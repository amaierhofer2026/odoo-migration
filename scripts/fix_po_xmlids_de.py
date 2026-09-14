#!/usr/bin/env python3
"""Repariert die XML-ID-Referenzen in i18n/de.po der Migrations-Module.

Hintergrund (Session 87):
  Die i18n/de.po-Dateien der aus Odoo 11 migrierten Module verweisen auf
  automatisch erzeugte XML-IDs im Odoo-11-Schema:

      model:ir.model.fields,field_description:itk_subscription.field_sale_subscription_partner_id
      #: selection:sale.subscription,minimum_contract_period_unit:0

  Odoo 18 erzeugt diese IDs aber mit DOPPELTEM Unterstrich bzw. anders:

      itk_subscription.field_sale_subscription__partner_id
      itk_subscription.selection__sale_subscription__state__draft

  Der PO-Import joint ueber ir_model_data - nicht passende Eintraege werden
  stillschweigend ignoriert (odoo/tools/translate.py: TranslationImporter.save).
  Ausserdem kennt der PoFileReader in Odoo 18 die alte Occurrence-Form
  "selection:model,field:index" nicht mehr (nur "model:"/"model_terms:"/"code:").

Dieses Skript
  * liest die PO-Dateien,
  * prueft jede Referenz gegen die echte Datenbank (VM oder lokal),
  * ersetzt veraltete Feld-Referenzen durch die tatsaechliche Odoo-18-XML-ID,
  * wandelt "selection:model,feld:index"-Referenzen in gueltige
    ir.model.fields.selection-Referenzen um,
  * laesst alles andere unveraendert und meldet, was nicht aufloesbar war.

Idempotent: bereits korrekte Referenzen bleiben unveraendert.

Aufruf:
    python scripts/fix_po_xmlids_de.py [--instanz vm|lokal] [--dry-run]
Credentials kommen aus der lokalen .env (gitignored) - ODOO18_*.
"""
import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDONS = os.path.join(BASIS, "addons")
ENV_PATH = os.path.join(BASIS, ".env")

URLS = {"vm": "https://k001959vsx.ipax.at", "lokal": "http://localhost:8069"}
# Module, die nicht aus dem Odoo-11-Bestand stammen bzw. unangetastet bleiben
AUSGENOMMEN = set()

# In Odoo 18 umbenannte Modelle (O11-Slug -> O18-Slug), laengste Praefixe zuerst
MODELL_UMBENENNUNGEN = [
    ("account_invoice_line", "account_move_line"),
    ("account_invoice", "account_move"),
    ("hr_holidays_status", "hr_leave_type"),
    ("hr_holidays", "hr_leave"),
    ("sale_subscription_line", "sale_subscription_line"),
]

OCC_RE = re.compile(r"^(#:\s*)(.*)$")
XMLID_RE = re.compile(r"^(model|model_terms|code|selection):([^:]+):(.+)$")


def lade_env(pfad=ENV_PATH):
    env = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            zeile = zeile.strip()
            if zeile and not zeile.startswith("#") and "=" in zeile:
                k, v = zeile.split("=", 1)
                env[k.strip()] = v.strip()
    return env


class DB:
    def __init__(self, url, env):
        jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        self.url = url
        self.db = env["ODOO18_DB"]
        self.pwd = env["ODOO18_PWD"]
        self.uid = self._call("common", "authenticate",
                              [self.db, env["ODOO18_USER"], self.pwd, {}])

    def _call(self, service, method, args, kwargs=None):
        payload = {"jsonrpc": "2.0", "method": "call",
                   "params": {"service": service, "method": method, "args": args,
                              "kwargs": kwargs or {}}, "id": 1}
        req = urllib.request.Request(self.url + "/jsonrpc", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with self.op.open(req, timeout=180) as r:
            out = json.loads(r.read().decode())
        if "error" in out:
            d = out["error"].get("data", {})
            raise RuntimeError("%s | %s" % (d.get("name"), d.get("message")))
        return out["result"]

    def kw(self, model, method, args=None, kwargs=None):
        return self._call("object", "execute_kw",
                          [self.db, self.uid, self.pwd, model, method, args or [], kwargs or {}])


def hole_imd(db, modul):
    """{model: {name: res_id}} aller XML-IDs des Moduls."""
    raus = {}
    rows = db.kw("ir.model.data", "search_read", [[["module", "=", modul]]],
                 {"fields": ["model", "name", "res_id"],
                  "context": {"active_test": False}})
    for r in rows:
        raus.setdefault(r["model"], {})[r["name"]] = r["res_id"]
    return raus


def baue_mappings(db, modul, imd):
    """Liefert (feld_map, sel_map):
       feld_map: {alter_name: neuer_name} fuer ir.model.fields (O11 -> O18)
       sel_map : {(model, feld, englischer_label): xmlid_name}
    """
    feld_map = {}
    for name in imd.get("ir.model.fields", {}):
        if "__" in name:
            alt = name.replace("__", "_", 1)
            feld_map.setdefault(alt, name)

    # Feld-ID -> (model, technischer Feldname), damit Selection-Saetze
    # eindeutig zugeordnet werden koennen (field_id liefert sonst nur den Anzeigenamen).
    id_zu_feld = {}
    feld_ids = list(imd.get("ir.model.fields", {}).values())
    for stueck in [feld_ids[i:i + 400] for i in range(0, len(feld_ids), 400)]:
        for r in db.kw("ir.model.fields", "read", [stueck], {"fields": ["model", "name"]}):
            id_zu_feld[r["id"]] = (r["model"], r["name"])

    sel_map = {}
    sel_imd = imd.get("ir.model.fields.selection", {})
    if sel_imd:
        umkehr = {v: k for k, v in sel_imd.items()}
        resids = list(sel_imd.values())
        for stueck in [resids[i:i + 400] for i in range(0, len(resids), 400)]:
            rows = db.kw("ir.model.fields.selection", "read", [stueck],
                         {"fields": ["field_id", "value", "name"],
                          "context": {"lang": "en_US"}})
            for r in rows:
                if not r["field_id"]:
                    continue
                ziel = id_zu_feld.get(r["field_id"][0])
                if not ziel:
                    continue
                modellname, feldname = ziel
                sel_map[(modellname, feldname, r["name"])] = umkehr.get(r["id"])
    return feld_map, sel_map


def modell_des_feldes(db, modul, feld_xmlid_alt):
    """Findet (model, field) zum alten Namen ueber ir.model.fields des Moduls."""
    return None


def verarbeite_datei(pfad, modul, db, dry_run=False):
    imd = hole_imd(db, modul)
    feld_map, sel_map = baue_mappings(db, modul, imd)

    rohtext = open(pfad, "rb").read().decode("utf-8")
    crlf = "\r\n" in rohtext
    zeilen = rohtext.replace("\r\n", "\n").split("\n")

    # Kontext fur selection-Referenzen: das jeweils zugehoerige msgid
    # (englischer Ausgangstext) steht in der Zeile nach den Referenzen.
    aenderungen = []
    nicht_aufloesbar = []
    aktuelle_refs = []
    for i, zeile in enumerate(zeilen):
        m = OCC_RE.match(zeile)
        if m:
            aktuelle_refs.append((i, m.group(1), m.group(2)))
            continue
        if zeile.startswith('msgid "'):
            msgid = zeile[len('msgid "'):].rstrip('"')
            for idx, praefix, inhalt in aktuelle_refs:
                teile = inhalt.split()
                neu = []
                for t in teile:
                    mm = XMLID_RE.match(t)
                    if not mm:
                        neu.append(t)
                        continue
                    art, modell, xmlid = mm.groups()
                    if art == "selection":
                        # selection:model,feld:index  ->  gueltige Selection-Referenz
                        modellname, _, feldname = modell.partition(",")
                        treffer = sel_map.get((modellname, feldname, msgid))
                        if treffer:
                            neu.append("model:ir.model.fields.selection,name:%s.%s"
                                       % (modul, treffer))
                            aenderungen.append(("selection", modul,
                                                "%s.%s=%s" % (modellname, feldname, msgid),
                                                xmlid, treffer, msgid))
                        else:
                            nicht_aufloesbar.append(("selection", modul,
                                                     "%s.%s=%s" % (modellname, feldname, msgid),
                                                     xmlid, msgid))
                            neu.append(t)
                        continue
                    if art == "code":
                        neu.append(t)
                        continue
                    # ir.ui.view.arch_db ist in Odoo 18 ein translate=callable-Feld
                    # (xml_translate) -> Referenz muss "model_terms:" heissen.
                    if art == "model" and modell == "ir.ui.view,arch_db":
                        neu.append("model_terms:" + modell + ":" + xmlid)
                        aenderungen.append(("model_terms", modul, modell, xmlid, "arch_db", msgid))
                        continue
                    kurz = xmlid.split(".", 1)
                    if len(kurz) != 2:
                        neu.append(t)
                        continue
                    mod, name = kurz
                    if name.startswith("field_") and "__" not in name:
                        ziel = feld_map.get(name)
                        if not ziel:
                            # O11-Modell umbenannt? (account.invoice.line -> account.move.line)
                            for alt, neumodell in MODELL_UMBENENNUNGEN:
                                praefix_alt = "field_%s_" % alt
                                praefix_neu = "field_%s_" % neumodell
                                if name.startswith(praefix_alt):
                                    kandidat = praefix_neu + name[len(praefix_alt):]
                                    if feld_map.get(kandidat):
                                        ziel = feld_map[kandidat]
                                        break
                        if ziel:
                            neu.append("%s:%s:%s.%s" % (art, modell, mod, ziel))
                            aenderungen.append(("field", modul, name, xmlid, ziel, msgid))
                            continue
                        nicht_aufloesbar.append(("field", modul, name, xmlid, msgid))
                    elif name.startswith("model_"):
                        # ir.model-Referenz: Modell evtl. umbenannt
                        if name not in imd.get("ir.model", {}):
                            for alt, neumodell in MODELL_UMBENENNUNGEN:
                                if name == "model_" + alt:
                                    kandidat = "model_" + neumodell
                                    if kandidat in imd.get("ir.model", {}):
                                        neu.append("%s:%s:%s.%s" % (art, modell, mod, kandidat))
                                        aenderungen.append(("model", modul, name, xmlid,
                                                            kandidat, msgid))
                                        break
                            else:
                                nicht_aufloesbar.append(("model", modul, name, xmlid, msgid))
                    neu.append(t)
                if neu != teile:
                    zeilen[idx] = praefix + " ".join(neu)
            aktuelle_refs = []
    if aenderungen and not dry_run:
        text = "\n".join(zeilen)
        if crlf:
            text = text.replace("\n", "\r\n")
        open(pfad, "wb").write(text.encode("utf-8"))
    return aenderungen, nicht_aufloesbar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal", choices=sorted(URLS))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--nur", default=None, help="nur dieses Modul bearbeiten")
    args = ap.parse_args()

    env = lade_env()
    db = DB(URLS[args.instanz], env)
    print("Instanz: %s (uid %s)  %s" % (args.instanz, db.uid,
                                        "(DRY-RUN)" if args.dry_run else ""))

    gesamt_a, gesamt_n = 0, 0
    for modul in sorted(os.listdir(ADDONS)):
        if args.nur and modul != args.nur:
            continue
        if modul in AUSGENOMMEN:
            continue
        i18n_dir = os.path.join(ADDONS, modul, "i18n")
        if not os.path.isdir(i18n_dir):
            continue
        # WICHTIG: Odoo mischt beim Import die .pot-Referenzen in die .po
        # (polib merge, odoo/tools/translate.py PoFileReader.__init__). Falsche
        # Referenzen im .pot ueberschreiben also die korrekten aus der .po.
        dateien = []
        po = os.path.join(i18n_dir, "de.po")
        if os.path.isfile(po):
            dateien.append(po)
        dateien += sorted(os.path.join(i18n_dir, f) for f in os.listdir(i18n_dir)
                          if f.endswith(".pot"))
        if not dateien:
            continue
        a, n = [], []
        for datei in dateien:
            ta, tn = verarbeite_datei(datei, modul, db, dry_run=args.dry_run)
            a += ta
            n += tn
        if not a and not n:
            continue
        gesamt_a += len(a)
        gesamt_n += len(n)
        print("\n%-32s korrigiert: %-4d nicht aufloesbar: %d" % (modul, len(a), len(n)))
        for eintrag in a[:6]:
            print("    %-9s %s -> %s" % (eintrag[0], eintrag[2][:52], str(eintrag[4])[:52]))
        if len(a) > 6:
            print("    ... und %d weitere" % (len(a) - 6))
        for eintrag in n[:5]:
            print("    OFFEN %-9s %s (msgid %r)" % (eintrag[0], eintrag[2][:44], eintrag[-1][:40]))
        if len(n) > 5:
            print("    ... und %d weitere offene" % (len(n) - 5))

    print("\n=== Summe: %d Referenzen korrigiert, %d nicht aufloesbar ==="
          % (gesamt_a, gesamt_n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
