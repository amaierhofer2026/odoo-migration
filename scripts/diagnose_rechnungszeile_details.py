"""Diagnose der konkreten ITK-Rechnungszeile (Session 118, Teil 10).

Liest alle gespeicherten Betragsfelder der von itk_subscription erzeugten Rechnungszeile,
das Rechnungsjournal und prueft, ob eine erneute Berechnung (harmlose Schreiboperation)
den Betrag korrigiert.

Aufruf: python scripts/diagnose_rechnungszeile_details.py --instanz lokal|vm
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
            raise RuntimeError(json.dumps(meldung)[:400])
        return a.get("result")

    return kw


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    url = "http://localhost:8069" if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    kw = client(url)
    print("Instanz: %s\n" % a.instanz)
    abo = kw("sale.subscription", "search_read", [[["name", "=", NAME]], ["id", "code"]])[0]
    moves = kw("account.move", "search_read", [[["invoice_origin", "=", abo["code"]]],
                                              ["id", "name", "state", "journal_id", "currency_id",
                                               "amount_untaxed", "amount_tax", "amount_total",
                                               "date", "invoice_date", "company_id"]])
    for m in moves:
        print("Rechnung %s (%s) Status %s | Journal %s | Waehrung %s | Firma %s"
              % (m["id"], m["name"], m["state"], m["journal_id"], m["currency_id"], m["company_id"]))
        print("   Datum %s | Leistungsdatum %s | untaxed %s | tax %s | total %s"
              % (m["date"], m["invoice_date"], m["amount_untaxed"], m["amount_tax"], m["amount_total"]))
        for lz in kw("account.move.line", "search_read",
                     [[["move_id", "=", m["id"]]],
                      ["display_type", "quantity", "price_unit", "discount", "price_subtotal", "price_total",
                       "debit", "credit", "balance", "amount_currency", "currency_id", "tax_ids", "account_id",
                       "product_uom_id", "analytic_distribution"]], limit=5):
            print("   Zeile (%s):" % (lz["display_type"] or "product"))
            for feld in ["quantity", "price_unit", "discount", "price_subtotal", "price_total", "debit", "credit",
                         "balance", "amount_currency", "currency_id", "tax_ids", "account_id", "product_uom_id",
                         "analytic_distribution"]:
                print("      %-22s %s" % (feld, lz[feld]))
        print("\n   --- erneute Berechnung durch harmlose Schreiboperation ---")
        kw("account.move", "write", [[m["id"]], {"narration": "Diagnose Teil 10"}])
        d = kw("account.move", "read", [[m["id"]], ["amount_untaxed", "amount_tax", "amount_total"]])[0]
        print("      nach dem Schreiben: untaxed %s | tax %s | total %s"
              % (d["amount_untaxed"], d["amount_tax"], d["amount_total"]))
        for lz in kw("account.move.line", "search_read", [[["move_id", "=", m["id"]]],
                                                          ["price_subtotal", "price_total", "balance",
                                                           "amount_currency"]], limit=5):
            print("      Zeile: subtotal %s | total %s | balance %s | amount_currency %s"
                  % (lz["price_subtotal"], lz["price_total"], lz["balance"], lz["amount_currency"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
