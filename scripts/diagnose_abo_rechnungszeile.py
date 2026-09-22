"""Diagnose: warum hat die erzeugte Abo-Rechnung 0,00? (Session 118, Teil 10)

Liest read-only die Abo-Zeile vor der Rechnungserzeugung und die tatsaechlich erzeugte
Rechnungszeile aus, inklusive aller preisrelevanten Felder.

Aufruf: python scripts/diagnose_abo_rechnungszeile.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "TEST Rechnungslauf Nachweis"


def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            w[k.strip()] = v.strip()
    return w


def client(url):
    env = lade_env(os.path.join(REPO, ".env"))
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(url + "/web/session/authenticate",
                                 data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
                                     "db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                     "password": env["ODOO18_PWD"]}}).encode(),
                                 headers={"Content-Type": "application/json"})
    with op.open(req, timeout=120) as f:
        f.read()

    def kw(modell, methode, args, **kwargs):
        r = urllib.request.Request(url + "/web/dataset/call_kw",
                                   data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
                                       "model": modell, "method": methode, "args": args,
                                       "kwargs": kwargs}}).encode(),
                                   headers={"Content-Type": "application/json"})
        with op.open(r, timeout=600) as f:
            a = json.loads(f.read().decode())
        if "error" in a:
            meldung = a["error"].get("data", {}).get("message", a["error"].get("message", ""))
            raise RuntimeError(json.dumps(meldung)[:300])
        return a.get("result")

    return kw


def suche(kw, modell, domain, felder, limit=5):
    return kw(modell, "search_read", [domain, felder], limit=limit)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    url = "http://localhost:8069" if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    kw = client(url)
    print("Instanz: %s (%s)\n" % (a.instanz, url))

    abo = suche(kw, "sale.subscription", [["name", "=", NAME]],
                ["id", "name", "code", "state", "recurring_total", "recurring_monthly",
                 "recurring_invoice_line_ids", "pricelist_id", "recurring_next_date"])
    if not abo:
        print("Testabo nicht gefunden - bitte zuerst scripts/test_abo_rechnungslauf.py ausfuehren.")
        return 1
    abo = abo[0]
    print("ABO %s (%s) Status %s | wiederkehrend %s | Preisliste %s | naechste Rechnung %s"
          % (abo["id"], abo["code"], abo["state"], abo["recurring_total"],
             abo["pricelist_id"][1], abo["recurring_next_date"]))
    print("   recurring_invoice_line_ids: %s" % abo["recurring_invoice_line_ids"])

    print("\n--- Abo-Zeilen (alle preisrelevanten Felder) ---")
    felder = ["id", "name", "product_id", "quantity", "uom_id", "price_unit", "discount",
              "qty_multiplication_factor", "price_subtotal", "analytic_account_id"]
    for z in suche(kw, "sale.subscription.line", [["analytic_account_id", "=", abo["id"]]], felder, limit=10):
        print("   Zeile %s: %s" % (z["id"], z["name"]))
        for f in felder[2:]:
            print("      %-26s %s" % (f, z[f]))

    print("\n--- Erzeugte Rechnungen ---")
    rechnungen = suche(kw, "account.move", [["invoice_origin", "=", abo["code"]]],
                       ["id", "name", "state", "move_type", "amount_untaxed", "amount_tax", "amount_total",
                        "currency_id", "invoice_date", "invoice_line_ids"], limit=5)
    for r in rechnungen:
        print("   Rechnung %s (%s) %s | untaxed %s | tax %s | total %s %s | Datum %s"
              % (r["id"], r["name"], r["state"], r["amount_untaxed"], r["amount_tax"],
                 r["amount_total"], r["currency_id"][1], r["invoice_date"]))
        print("   Rechnungszeilen-IDs: %s" % r["invoice_line_ids"])
        for lz in suche(kw, "account.move.line", [["move_id", "=", r["id"]]],
                        ["id", "display_type", "name", "product_id", "quantity", "price_unit", "discount",
                         "price_subtotal", "price_total", "tax_ids", "account_id", "analytic_distribution"],
                        limit=10):
            print("      Zeile %s (%s): %s" % (lz["id"], lz["display_type"] or "produkt", (lz["name"] or "")[:44]))
            for f in ["product_id", "quantity", "price_unit", "discount", "price_subtotal", "price_total",
                      "tax_ids", "account_id", "analytic_distribution"]:
                print("         %-22s %s" % (f, lz[f]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
