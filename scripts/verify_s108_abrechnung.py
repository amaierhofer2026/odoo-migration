"""Abnahmepruefung Bereich Kontakte -> Kontaktformular -> Abrechnung (Session 108).

Prueft READ-ONLY gegen eine Odoo-18-Instanz (lokal oder VM):
  1. Sind alle abrechnungsrelevanten Felder vorhanden (Name, Typ, Relation)?
  2. Zeigt der gerenderte Arch des Reiters "Abrechnung" die erwarteten Felder?
  3. In welche Reiter wurden die Odoo-11-Felder in Odoo 18 verschoben?
  4. Sind die abrechnungsrelevanten Stammdaten vorhanden?
  5. Enthaelt peppol_eas die oesterreichische VOKZ-Kennung 9915?

Aufruf:
    python scripts/verify_s108_abrechnung.py --instanz lokal
    python scripts/verify_s108_abrechnung.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (Feld, erwarteter Typ, erwartete Relation oder None)
FELDER = [
    ("property_payment_term_id", "many2one", "account.payment.term"),
    ("property_supplier_payment_term_id", "many2one", "account.payment.term"),
    ("property_account_position_id", "many2one", "account.fiscal.position"),
    ("property_account_receivable_id", "many2one", "account.account"),
    ("property_account_payable_id", "many2one", "account.account"),
    ("bank_ids", "one2many", "res.partner.bank"),
    ("invoice_sending_method", "selection", None),
    ("invoice_edi_format", "selection", None),
    ("invoice_edi_format_store", "char", None),
    ("invoice_template_pdf_report_id", "many2one", "ir.actions.report"),
    ("peppol_eas", "selection", None),
    ("peppol_endpoint", "char", None),
    ("peppol_verification_state", "selection", None),
    ("autopost_bills", "selection", None),
    ("credit", "monetary", None),
    ("credit_limit", "float", None),
    ("use_partner_credit_limit", "boolean", None),
    ("trust", "selection", None),
]

# Felder, die in Odoo 18 nicht mehr existieren (Odoo-11-Bestand)
ENTFALLEN = ["property_stock_customer", "property_stock_supplier"]

# Felder, die im gerenderten Arch des Reiters "Abrechnung" vorkommen sollen
ARCH_FELDER = ["bank_ids", "invoice_sending_method", "invoice_edi_format", "peppol_eas", "peppol_endpoint",
               "autopost_bills"]

# Odoo-11-Reiter -> erwarteter Odoo-18-Reiter (verschobene Felder)
VERSCHOBEN = {
    "property_payment_term_id": "Verkauf & Einkauf",
    "property_supplier_payment_term_id": "Verkauf & Einkauf",
    "property_account_position_id": "Verkauf & Einkauf",
    "bank_ids": "Abrechnung",
    "property_account_receivable_id": None,   # in Odoo 18 nicht im Formular (Standardwerte der Buchhaltung)
    "property_account_payable_id": None,
}


def lade_env(pfad: str) -> dict:
    werte = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                s, w = zeile.split("=", 1)
                werte[s.strip()] = w.strip()
    return werte


class Client:
    def __init__(self, url: str, db: str, user: str, pwd: str):
        self.url = url.rstrip("/")
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        self.rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})

    def rufe(self, pfad: str, params: dict):
        req = urllib.request.Request(
            self.url + pfad,
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode(),
            headers={"Content-Type": "application/json"})
        with self.opener.open(req, timeout=240) as antwort:
            daten = json.loads(antwort.read().decode())
        if "error" in daten:
            raise RuntimeError(json.dumps(daten["error"])[:300])
        return daten.get("result")

    def kw(self, model: str, methode: str, args: list, **kwargs):
        return self.rufe("/web/dataset/call_kw",
                         {"model": model, "method": methode, "args": args, "kwargs": kwargs})


def reiter(arch: str, feld: str) -> str:
    """Reiter-Tag, in dem das Feld steht (attributreihenfolge-tolerant)."""
    for m in re.finditer(r'<field\b[^>]*name="%s"[^>]*/?>' % feld, arch):
        seiten = re.findall(r'<page\b[^>]*>', arch[:m.start()])
        return seiten[-1] if seiten else "?"
    return "nicht im Formular"


# Reiter werden in Odoo teils ueber name, teils ueber string adressiert
REITER_MUSTER = {
    "Verkauf & Einkauf": ("sales_purchases", "Verkauf &amp; Einkauf", "Verkauf & Einkauf"),
    "Abrechnung": ("accounting", "Abrechnung"),
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    k = Client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    print("Instanz: %s (%s, DB %s)" % (a.instanz, url, env["ODOO18_DB"]))
    ok = fehler = 0

    def pruefe(bedingung: bool, text: str):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    print("\n1) Felder in Odoo 18 (Name, Typ, Relation)")
    felder = k.kw("res.partner", "fields_get", [[f for f, _, _ in FELDER], ["type", "relation"]])
    for name, typ, rel in FELDER:
        d = felder.get(name)
        if not d:
            pruefe(False, "%s fehlt" % name)
        elif d["type"] != typ or (rel and d.get("relation") != rel):
            pruefe(False, "%s: Typ %s/%s (erwartet %s/%s)" % (name, d["type"], d.get("relation"), typ, rel))
        else:
            pruefe(True, "%s (%s%s)" % (name, d["type"], " -> " + rel if rel else ""))

    print("\n2) Entfallene Odoo-11-Felder")
    alt = k.kw("res.partner", "fields_get", [ENTFALLEN, ["type"]])
    for name in ENTFALLEN:
        pruefe(name not in alt, "%s existiert in Odoo 18 nicht mehr" % name)

    print("\n3) Gerenderter Arch des Reiters 'Abrechnung'")
    arch = k.kw("res.partner", "get_views", [[[False, "form"]]], context={"lang": "de_DE"})["views"]["form"]["arch"]
    i = arch.find('name="accounting"')
    pruefe(i > 0, "Reiter 'accounting' im Arch gefunden")
    j = arch.find("<page", i + 10)
    seg = arch[i:(j if j > 0 else i + 8000)]
    for f in ARCH_FELDER:
        pruefe(('name="%s"' % f) in seg, "Feld %s im Reiter Abrechnung" % f)
    for f in ["bank_ids", "allow_out_payment", "acc_holder_name"]:
        d = k.kw("res.partner.bank", "fields_get", [[f], ["type"]]) if f != "bank_ids" else {"bank_ids": {"type": "one2many"}}
        pruefe(bool(d.get(f)), "Bankfeld %s vorhanden" % f)

    print("\n4) Verschobene Felder (Odoo 11 -> Odoo 18)")
    for feld, erwartet in VERSCHOBEN.items():
        tag = reiter(arch, feld)
        if erwartet is None:
            pruefe(tag == "nicht im Formular",
                   "%s: in Odoo 18 nicht im Formular (erwartet), gefunden: %s" % (feld, tag))
        else:
            treffer = any(m in tag for m in REITER_MUSTER[erwartet])
            pruefe(treffer, "%s steht in Odoo 18 im Reiter '%s' (gefunden: %s)" % (feld, erwartet, tag[:70]))

    print("\n5) Abrechnungsrelevante Stammdaten")
    for modell, mindest, label in [("account.payment.term", 4, "Zahlungsbedingungen"),
                                   ("account.fiscal.position", 1, "Steuerpositionen"),
                                   ("account.account", 10, "Konten")]:
        n = k.kw(modell, "search_count", [[]])
        pruefe(n >= mindest, "%s: %d" % (label, n))
    namen = [t["name"] for t in k.kw("account.payment.term", "search_read", [[], ["name"]])]
    pruefe("14 Tage" in namen, "Zahlungsbedingung '14 Tage' (Odoo-11-Hauptwert) vorhanden")
    for typ, label in [("asset_receivable", "Debitorenkonten"), ("liability_payable", "Kreditorenkonten")]:
        n = k.kw("account.account", "search_count", [[["account_type", "=", typ]]])
        pruefe(n >= 1, "%s in Odoo 18 vorhanden: %d" % (label, n))

    print("\n6) VOKZ (oesterreichische Peppol-Kennung)")
    sel = k.kw("res.partner", "fields_get", [["peppol_eas"], ["selection"]], context={"lang": "de_DE"})["peppol_eas"]["selection"]
    vokz = [s for s in sel if s[0] == "9915"]
    pruefe(bool(vokz), "peppol_eas 9915 vorhanden: %s" % (vokz[0][1] if vokz else "-"))
    n = k.kw("res.partner", "search_count", [[["peppol_eas", "=", "9915"]]])
    print("       Hinweis: Kontakte mit VOKZ-Kennung (9915) im Testbestand: %d" % n)
    n = k.kw("ir.module.module", "search_count", [[["name", "in", ["account_peppol", "account_edi_ubl_cii"]], ["state", "=", "installed"]]])
    pruefe(n >= 1, "Peppol-/EDI-Module installiert: %d" % n)

    print("\n7) Kontrollzahlen")
    print("       Kontakte gesamt: %d" % k.kw("res.partner", "search_count", [[]]))
    print("       Bankverbindungen: %d" % k.kw("res.partner.bank", "search_count", [[]]))

    print("\nERGEBNIS: %d OK, %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
