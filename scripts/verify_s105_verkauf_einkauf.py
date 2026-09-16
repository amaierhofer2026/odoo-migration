"""Abnahmepruefung Bereich Kontakte -> Kontaktformular -> Verkauf & Einkauf (Session 105).

Prueft READ-ONLY gegen eine Odoo-18-Instanz (lokal oder VM):
  1. Sind alle migrationsrelevanten Felder vorhanden (Name, Typ, Relation)?
  2. Funktioniert die Odoo-18-Logik Ist ein Kunde / Ist ein Lieferant (compute auf customer_rank/supplier_rank)?
  3. Sind die benoetigten Stammdaten vorhanden (Zahlungsbedingungen, Waehrungen, Branchen, Preislisten)?
  4. Enthaelt der gerenderte Arch des Tabs "Verkauf & Einkauf" die erwarteten Felder?

Aufruf:
    python scripts/verify_s105_verkauf_einkauf.py --instanz lokal
    python scripts/verify_s105_verkauf_einkauf.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (Feldname, erwarteter Typ in Odoo 18, erwartete Relation oder None)
FELDER = [
    ("ref", "char", None),
    ("user_id", "many2one", "res.users"),
    ("buyer_id", "many2one", "res.users"),
    ("industry_id", "many2one", "res.partner.industry"),
    ("website", "char", None),
    ("multi_factor", "integer", None),
    ("customer_rank", "integer", None),
    ("supplier_rank", "integer", None),
    ("is_customer", "boolean", None),
    ("is_supplier", "boolean", None),
    ("property_product_pricelist", "many2one", "product.pricelist"),
    ("property_payment_term_id", "many2one", "account.payment.term"),
    ("property_supplier_payment_term_id", "many2one", "account.payment.term"),
    ("property_inbound_payment_method_line_id", "many2one", "account.payment.method.line"),
    ("property_outbound_payment_method_line_id", "many2one", "account.payment.method.line"),
    ("property_purchase_currency_id", "many2one", "res.currency"),
    ("property_account_position_id", "many2one", "account.fiscal.position"),
    ("property_account_receivable_id", "many2one", "account.account"),
    ("property_account_payable_id", "many2one", "account.account"),
    ("bank_ids", "one2many", "res.partner.bank"),
    ("payment_token_count", "integer", None),
    ("company_registry", "char", None),
    ("global_location_number", "char", None),
]

# Felder, die in Odoo 18 bewusst nicht mehr auf dem Kontakt existieren
ENTFALLEN = ["customer", "supplier", "opt_out", "property_stock_customer", "property_stock_supplier",
             "property_payment_method_id"]

# Felder, die der gerenderte Arch des Tabs enthalten soll
ARCH_FELDER = ["user_id", "buyer_id", "ref", "industry_id", "property_product_pricelist",
               "property_payment_term_id", "property_supplier_payment_term_id",
               "property_inbound_payment_method_line_id", "property_outbound_payment_method_line_id",
               "property_purchase_currency_id", "property_account_position_id"]


def lade_env(pfad: str) -> dict:
    werte = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                schluessel, wert = zeile.split("=", 1)
                werte[schluessel.strip()] = wert.strip()
    return werte


class Client:
    def __init__(self, url: str, db: str, user: str, pwd: str):
        self.url = url.rstrip("/")
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})

    def rufe(self, pfad: str, params: dict):
        req = urllib.request.Request(
            self.url + pfad,
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with self.opener.open(req, timeout=240) as antwort:
            daten = json.loads(antwort.read().decode())
        if "error" in daten:
            raise RuntimeError(json.dumps(daten["error"])[:300])
        return daten.get("result")

    def kw(self, model: str, methode: str, args: list, **kwargs):
        return self.rufe("/web/dataset/call_kw",
                         {"model": model, "method": methode, "args": args, "kwargs": kwargs})


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    if a.instanz == "lokal":
        url = env.get("ODOO18_URL", "http://localhost:8069")
    else:
        url = "https://k001959vsx.ipax.at"
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
            pruefe(False, "%s hat Typ %s/%s (erwartet %s/%s)" % (name, d["type"], d.get("relation"), typ, rel))
        else:
            pruefe(True, "%s (%s%s)" % (name, d["type"], " -> " + rel if rel else ""))

    print("\n2) Bewusst entfallene Odoo-11-Felder")
    alt = k.kw("res.partner", "fields_get", [ENTFALLEN, ["type"]])
    for name in ENTFALLEN:
        pruefe(name not in alt, "%s existiert in Odoo 18 nicht mehr" % name)

    print("\n3) Odoo-18-Logik Ist ein Kunde / Ist ein Lieferant")
    kunden = k.kw("res.partner", "search_count", [[["customer_rank", ">", 0]]])
    probe = k.kw("res.partner", "search_read", [[["customer_rank", ">", 0]], ["name", "customer_rank", "is_customer"]], limit=1)
    pruefe(bool(probe), "Kontakte mit customer_rank > 0 vorhanden (%d)" % kunden)
    if probe:
        pruefe(probe[0]["is_customer"] is True,
               "is_customer spiegelt customer_rank (%s: rank=%s, is_customer=%s)"
               % (probe[0]["name"][:30], probe[0]["customer_rank"], probe[0]["is_customer"]))
    liefer = k.kw("res.partner", "search_count", [[["supplier_rank", ">", 0]]])
    print("       Hinweis: Kontakte mit supplier_rank > 0: %d" % liefer)

    print("\n4) Stammdaten in Odoo 18")
    for modell, mindest, label in [("account.payment.term", 4, "Zahlungsbedingungen"),
                                   ("res.currency", 2, "aktive Waehrungen"),
                                   ("res.partner.industry", 20, "Branchen"),
                                   ("account.payment.method.line", 1, "Zahlungsmethoden")]:
        n = k.kw(modell, "search_count", [[]])
        pruefe(n >= mindest, "%s: %d (mindestens %d erwartet)" % (label, n, mindest))
    namen = [t["name"] for t in k.kw("account.payment.term", "search_read", [[], ["name"]])]
    pruefe("14 Tage" in namen, "Zahlungsbedingung '14 Tage' vorhanden (Odoo-11-Hauptwert)")
    pl = k.kw("product.pricelist", "search_read", [[], ["name", "active", "currency_id"]], context={"active_test": False})
    aktive = [p for p in pl if p["active"]]
    pruefe(len(aktive) > 0, "aktive Preisliste vorhanden: %s" % ([(p["name"][:30], p["currency_id"][1]) for p in aktive] or "keine"))
    if not aktive:
        print("       GAP: alle Preislisten sind inaktiv (%s) - vor der Datenmigration klaeren"
              % [(p["name"][:30], p["currency_id"][1]) for p in pl])
    fp = k.kw("account.fiscal.position", "search_read", [[], ["name"]])
    pruefe(len(fp) > 0, "Steuerpositionen vorhanden: %d" % len(fp))

    print("\n5) Gerenderter Arch des Tabs 'Verkauf & Einkauf'")
    arch = k.kw("res.partner", "get_views", [[[False, "form"]]], context={"lang": "de_DE"})["views"]["form"]["arch"]
    i = arch.find('name="sales_purchases"')
    j = arch.find("<page", arch.find("<page", i) + 1)
    seg = arch[i:j] if i > 0 else ""
    pruefe(bool(seg), "Tab 'sales_purchases' im Arch gefunden")
    for f in ARCH_FELDER:
        pruefe('name="%s"' % f in seg, "Feld %s im Tab sichtbar" % f)

    print("\n6) Kontrollzahlen")
    print("       Kontakte gesamt: %d" % k.kw("res.partner", "search_count", [[]]))
    print("       Zeilen im Auftragstabellen-Kontext unveraendert (keine Datenaenderung durch dieses Skript)")

    print("\nERGEBNIS: %d OK, %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
