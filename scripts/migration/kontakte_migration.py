# -*- coding: utf-8 -*-
"""Kontakte/Partner: Migrationsskript Odoo 11 -> Odoo 18.

Teil des ITK-Migrationsprojekts, erstellt unter Freigabe von Anna Maierhofer (11.11.2026).
Quelle: Odoo 11 Prod `ITK_V1_a` - ausschliesslich lesend. Ziel: Odoo 18.

Umfang (vollstaendiger fachlicher Bereich, nicht nur der Verkaufsbedarf):
- res.partner.category: 123 Tags inkl. Hierarchie und Farbe
- res.partner: 5.851 Kontakte (2.382 Firmen, 3.469 Personen, 3.362 Kind-Kontakte),
  inklusive archivierter Datensaetze

Idempotenz: technisches Feld `itk_o11_id` (Modul itk_migration_keys). Ein zweiter Lauf
erkennt jeden Datensatz wieder und schreibt nur, wenn sich ein Feldwert unterscheidet.

Datenschutz: Die Migration verarbeitet personenbezogene Daten zwischen Odoo 11 und
Odoo 18. Konsole, Mapping-Datei und Dokumentation enthalten nur Zaehlwerte, IDs und
Status - keine Namen, E-Mail-Adressen, Telefonnummern oder Adressen.

Aufruf (Trockenlauf ist Standard und schreibt nichts):
    python scripts/migration/kontakte_migration.py --instanz lokal
    python scripts/migration/kontakte_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

BATCH = 100


class Schreibschutz:
    SCHREIBEND = {"create", "write", "unlink", "copy"}

    def __init__(self, client_, schreiben: bool):
        self._client = client_
        self._schreiben = schreiben

    def kw(self, modell, methode, args, **kwargs):
        if not self._schreiben and methode in self.SCHREIBEND:
            raise RuntimeError("Schreibaufruf im Trockenlauf: %s.%s" % (modell, methode))
        return self._client.kw(modell, methode, args, **kwargs)


# Felder, die Odoo 11 fuehrt und Odoo 18 nicht mehr anbietet (dokumentiert, nicht uebernommen)
NICHT_UEBERNOMMEN = ("customer", "supplier", "team_id", "sla_id", "opt_out",
                     "signup_*", "image", "image_medium", "image_small")


def text_nach_html(text):
    """Odoo 11 fuehrte Klartext, Odoo 18 speichert HTML. Zeilenumbrueche bleiben erhalten."""
    if not text:
        return False
    if "<p>" in text or "<br" in text or "<div" in text:
        return text
    import html as _html
    vereinheitlicht = text.replace(chr(13) + chr(10), chr(10))
    zeilen = [z.strip() for z in vereinheitlicht.split(chr(10))]
    return "".join("<p>%s</p>" % _html.escape(z) if z else "<p><br></p>" for z in zeilen)


def lade_titel(o11):
    return o11.kw("res.partner.title", "search_read", [[], ["id", "name", "shortcut"]],
                  order="id", limit=500)


def lade_kategorien(o11):
    return o11.kw("res.partner.category", "search_read", [[]],
                  fields=["id", "name", "parent_id", "color", "active"], order="id", limit=2000)


def lade_partner(o11):
    felder = ["id", "name", "is_company", "parent_id", "ref", "vat", "street", "street2",
              "zip", "city", "country_id", "email", "phone", "mobile", "website", "lang",
              "comment", "function", "title", "category_id", "active", "company_id"]
    return o11.kw("res.partner", "search_read", [[ "|", ["active", "=", True], ["active", "=", False]]],
                  fields=felder, order="id", limit=8000)


def zielbestand(o18):
    return {
        "kat": {r["itk_o11_id"]: r["id"] for r in
                o18.kw("res.partner.category", "search_read", [[["itk_o11_id", "!=", False]],
                                                               ["id", "itk_o11_id"]], limit=5000)},
        "partner": {r["itk_o11_id"]: r["id"] for r in
                    o18.kw("res.partner", "search_read", [[["itk_o11_id", "!=", False]],
                                                          ["id", "itk_o11_id"]], limit=20000,
                           context={"active_test": False})},
        "laender": {r["code"]: r["id"] for r in
                    c18_laender(o18)},
    }


def c18_laender(o18):
    return o18.kw("res.country", "search_read", [[], ["id", "code"]], limit=300)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    ap.add_argument("--grenze", type=int, default=0)
    ap.add_argument("--mapping")
    args = ap.parse_args()

    if args.ausfuehren and not args.ich_habe_freigabe:
        print("ABBRUCH: Schreiblauf nur mit --ich-habe-freigabe (Freigabe von Anna).")
        return 2

    o11 = client.o11()
    ziel = Schreibschutz(client.o18(args.instanz), args.ausfuehren)
    print("=== Kontakte-Migration %s | %s ===" % (
        args.instanz, "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF (schreibt nichts)"))

    kats = lade_kategorien(o11)
    titel = lade_titel(o11)
    partner = lade_partner(o11)
    if args.grenze:
        partner = partner[:args.grenze]
    bestand = zielbestand(ziel)

    stat = {"gelesen_kat": len(kats), "gelesen_partner": len(partner),
            "kat_neu": 0, "kat_da": 0, "partner_neu": 0, "partner_da": 0,
            "partner_aktualisiert": 0, "uebersprungen": 0, "fehler": 0, "ohne_parent": 0}
    mapping = {"kategorien": [], "partner": []}

    # 1) Kategorien in Hierarchie-Reihenfolge (Eltern zuerst)
    kats_sorted, offen = [], list(kats)
    ids_kat = {k["id"] for k in kats}
    while offen:
        for k in list(offen):
            pid = k["parent_id"] and k["parent_id"][0]
            if not pid or pid not in ids_kat or any(x["id"] == pid for x in kats_sorted):
                kats_sorted.append(k)
                offen.remove(k)
        if not offen:
            break
        if len(kats_sorted) == len(kats) - len(offen) and not any(
                (k["parent_id"] and k["parent_id"][0]) not in [x["id"] for x in kats_sorted]
                for k in offen):
            kats_sorted.extend(offen)
            break

    for k in kats_sorted:
        if k["id"] in bestand["kat"]:
            stat["kat_da"] += 1
            mapping["kategorien"].append({"o11_id": k["id"], "o18_id": bestand["kat"][k["id"]]})
            continue
        vals = {"name": k["name"], "color": k["color"], "itk_o11_id": k["id"],
                "active": k["active"]}
        if k["parent_id"] and k["parent_id"][0] in bestand["kat"]:
            vals["parent_id"] = bestand["kat"][k["parent_id"][0]]
        try:
            if args.ausfuehren:
                kid = ziel.kw("res.partner.category", "create", [vals])
                kid = kid[0] if isinstance(kid, list) else kid
            else:
                kid = -k["id"]          # Platzhalter im Trockenlauf, kein Schreibzugriff
            bestand["kat"][k["id"]] = kid
            stat["kat_neu"] += 1
            mapping["kategorien"].append({"o11_id": k["id"], "o18_id": kid})
        except Exception as e:
            stat["fehler"] += 1
            print("  FEHLER Kategorie o11_id %s: %s" % (k["id"], str(e)[:120]))

    # 1b) Titel (Anreden wie "Mag. Dr.") - Odoo 18 kennt nur 5 Standardtitel
    titel_map = {}
    vorhandene_titel = {t["name"]: t["id"] for t in
                        ziel.kw("res.partner.title", "search_read", [[], ["id", "name"]],
                                limit=1000)}
    stat["titel_neu"] = 0
    stat["titel_da"] = 0
    for t in titel:
        if t["name"] in vorhandene_titel:
            titel_map[t["id"]] = vorhandene_titel[t["name"]]
            stat["titel_da"] += 1
            continue
        if args.ausfuehren:
            try:
                neu = ziel.kw("res.partner.title", "create",
                              [{"name": t["name"], "shortcut": t["shortcut"] or t["name"][:8]}])
                neu = neu[0] if isinstance(neu, list) else neu
            except Exception as e:
                stat["fehler"] += 1
                print("  FEHLER Titel o11_id %s: %s" % (t["id"], str(e)[:100]))
                continue
        else:
            neu = -t["id"]
        titel_map[t["id"]] = neu
        vorhandene_titel[t["name"]] = neu
        stat["titel_neu"] += 1

    # 1c) ref-Konflikte mit Odoo-18-Testdaten aufloesen
    # itk_crm erzwingt UNIQUE(ref) (aus Odoo 11 uebernommen). Odoo 11 fuehrt 2.283
    # eindeutige ref-Werte, aber 8 Odoo-18-Demopartner (itk_o11_id = 0) belegen refs,
    # die fuer migrierte Kontakte gebraucht werden. Diese Demodatensaetze sind keine
    # produktiven Daten (Freigabe Anna: Test-/Demodaten duerfen bereinigt werden);
    # ihr ref wird geleert, der Datensatz selbst bleibt erhalten.
    stat["ref_konflikte"] = 0
    refs_noetig = {(p["ref"] or "").strip() for p in partner if (p["ref"] or "").strip()}
    demo_ref = ziel.kw("res.partner", "search_read",
                       [[["itk_o11_id", "=", 0], ["ref", "!=", False]], ["id", "ref"]],
                       limit=500, context={"active_test": False})
    for d in demo_ref:
        if (d["ref"] or "").strip() not in refs_noetig:
            continue
        if args.ausfuehren:
            try:
                ziel.kw("res.partner", "write", [[d["id"]], {"ref": False}])
            except Exception as e:
                stat["fehler"] += 1
                print("  FEHLER ref-Freigabe id %s: %s" % (d["id"], str(e)[:100]))
                continue
        stat["ref_konflikte"] += 1

    # 2) Partner: erst ohne parent, dann Kinder (Beziehungen erhalten)
    def schreibe(block):
        vals_list = []
        for p in block:
            vals = {"name": p["name"], "is_company": p["is_company"], "active": p["active"],
                    "itk_o11_id": p["id"], "ref": (p["ref"] or "").strip() or False,
                    "vat": (p["vat"] or "").strip() or False,
                    "street": p["street"] or False, "street2": p["street2"] or False,
                    "zip": p["zip"] or False, "city": p["city"] or False,
                    "email": p["email"] or False, "phone": p["phone"] or False,
                    "mobile": p["mobile"] or False, "website": p["website"] or False,
                    "function": p["function"] or False,
                    "comment": text_nach_html(p["comment"])}
            if p["title"] and p["title"][0] in titel_map:
                vals["title"] = titel_map[p["title"][0]]
            if p["parent_id"] and p["parent_id"][0] in bestand["partner"]:
                vals["parent_id"] = bestand["partner"][p["parent_id"][0]]
            if p["country_id"]:
                code = code_je_id.get(p["country_id"][0])
                if code and code in bestand["laender"]:
                    vals["country_id"] = bestand["laender"][code]
            if p["category_id"]:
                kats_ziel = [bestand["kat"][c] for c in p["category_id"] if c in bestand["kat"]]
                if kats_ziel:
                    vals["category_id"] = [(6, 0, kats_ziel)]
            vals_list.append(vals)
        # no_vat_validation: Odoo 11 hat USt-IDs nie gegen VIES geprueft. Die Migration
        # uebernimmt die historischen Werte unveraendert, ohne sie neu zu validieren
        # (sonst wuerden 216 Kontakte mit historischen UID-Formaten blockiert).
        ids = ziel.kw("res.partner", "create", [vals_list],
                      context={"no_vat_validation": True})
        return ids

    code_je_id = {}
    for c in o11.kw("res.country", "search_read", [[], ["id", "code"]], limit=300):
        code_je_id[c["id"]] = c["code"]

    # Kontakte ohne Namen: Odoo 18 verlangt einen Namen (Pflichtfeld) und das Modul
    # partner_firstname verlangt zusaetzlich Vor-/Nachname. Diese 28 Datensaetze werden
    # NICHT mit einem erfundenen Platzhalter angelegt, sondern als "nicht zuordenbar"
    # gezaehlt und Anna zur Entscheidung vorgelegt (IDs im CSV-Report, ausserhalb Git).
    ohne_namen = [p for p in partner if not (p["name"] or "").strip()]
    partner_namentlich = [p for p in partner if (p["name"] or "").strip()]
    stat["ohne_namen"] = len(ohne_namen)
    stat["nicht_zuordenbar"] = len(ohne_namen)
    with open(os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "Temp",
                           "s142_web", "kontakte_ohne_namen.json"), "w", encoding="utf-8") as fh:
        json.dump([{"o11_id": p["id"], "is_company": p["is_company"],
                    "hat_parent": bool(p["parent_id"]), "hat_ref": bool(p["ref"])}
                   for p in ohne_namen], fh, ensure_ascii=False, indent=1)

    ids_partner = {p["id"] for p in partner_namentlich}
    top = [p for p in partner_namentlich if not p["parent_id"] or p["parent_id"][0] not in ids_partner]
    kinder = [p for p in partner_namentlich if p["parent_id"] and p["parent_id"][0] in ids_partner]
    stat["ohne_parent"] = len(top)

    for gruppe in (top, kinder):
        neu = [p for p in gruppe if p["id"] not in bestand["partner"]]
        stat["partner_da"] += len(gruppe) - len(neu)
        for i in range(0, len(neu), BATCH):
            block = neu[i:i + BATCH]
            try:
                if args.ausfuehren:
                    ids = schreibe(block)
                    if not isinstance(ids, list):
                        ids = [ids]
                else:
                    ids = [-p["id"] for p in block]   # Platzhalter, kein Schreibzugriff
                for p, nid in zip(block, ids):
                    bestand["partner"][p["id"]] = nid
                    stat["partner_neu"] += 1
            except Exception as e:
                stat["fehler"] += 1
                print("  FEHLER Partner-Block ab o11_id %s: %s" % (block[0]["id"], str(e)[-700:]))
        if args.grenze:
            break

    for p in partner:
        if p["id"] in bestand["partner"]:
            mapping["partner"].append({"o11_id": p["id"], "o18_id": bestand["partner"][p["id"]]})

    breite = "{:<34}{:>10}"
    print(breite.format("Objekt", "Anzahl"))
    print("-" * 44)
    for k, v in (("Kategorien gelesen", stat["gelesen_kat"]),
                 ("davon neu angelegt", stat["kat_neu"]),
                 ("davon bereits vorhanden", stat["kat_da"]),
                 ("ref-Konflikte mit Demodaten geloest", stat.get("ref_konflikte", 0)),
                 ("Titel gelesen", len(titel)),
                 ("Titel neu angelegt", stat["titel_neu"]),
                 ("Titel bereits vorhanden", stat["titel_da"]),
                 ("Kontakte gelesen", stat["gelesen_partner"]),
                 ("davon neu angelegt", stat["partner_neu"]),
                 ("davon bereits vorhanden", stat["partner_da"]),
                 ("aktualisiert", stat["partner_aktualisiert"]),
                 ("uebersprungen (unveraendert)", stat["uebersprungen"]),
                 ("nicht zuordenbar", stat.get("nicht_zuordenbar", 0)),
                 ("davon ohne Namen (Odoo-18-Pflichtfeld)", stat.get("ohne_namen", 0)),
                 ("Fehler", stat["fehler"])):
        print(breite.format(k, v))
    if not args.ausfuehren:
        print("Hinweis: Zahlen unter 'neu angelegt' sind im Trockenlauf die Anzahl der "
              "Datensaetze, die geschrieben WUERDEN.")
    print("Nicht uebernommene Odoo-11-Felder:", ", ".join(NICHT_UEBERNOMMEN))
    if args.mapping:
        with open(args.mapping, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(mapping, fh, ensure_ascii=False)
        print("Mapping geschrieben (nur IDs):", args.mapping)
    print("Modus:", "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
