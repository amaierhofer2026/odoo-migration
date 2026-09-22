"""Diagnose: Welche Werte liefert itk_subscription an account.move? (Session 118, Teil 10)

Ruft die Vorbereitungsmethode des Abo-Moduls direkt auf, zeigt die erzeugten Werte und legt
die Rechnung mit genau diesen Werten an, um Zeile und Summen zu vergleichen.

Aufruf: python scripts/diagnose_abo_prepare_invoice.py --instanz lokal|vm
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
    abo = kw("sale.subscription", "search", [[["name", "=", NAME]]])
    if not abo:
        print("Testabo fehlt")
        return 1
    abo_id = abo[0]
    print("--- Werte aus itk_subscription (Abo %s) ---" % abo_id)
    werte = kw("sale.subscription", "_prepare_invoice", [[abo_id]])
    for schluessel in sorted(werte):
        if schluessel == "invoice_line_ids":
            print("   %s:" % schluessel)
            for kommando, _id, zeile in werte[schluessel]:
                for feld in sorted(zeile):
                    print("      %-24s %s" % (feld, zeile[feld]))
        else:
            print("   %-24s %s" % (schluessel, werte[schluessel]))

    print("\n--- Rechnung mit genau diesen Werten anlegen ---")
    neu = kw("account.move", "create", [werte])
    d = kw("account.move", "read", [[neu], ["name", "state", "amount_untaxed", "amount_tax", "amount_total", "currency_id"]])[0]
    print("   Rechnung %s (%s): untaxed %s | tax %s | total %s %s"
          % (d["name"], d["state"], d["amount_untaxed"], d["amount_tax"], d["amount_total"], d["currency_id"][1]))
    for lz in kw("account.move.line", "search_read",
                 [[["move_id", "=", neu]], ["display_type", "name", "quantity", "price_unit", "discount",
                                            "price_subtotal", "price_total", "tax_ids", "analytic_distribution",
                                            "currency_id"]], limit=8):
        print("      Zeile %-10s Menge %-6s Preis %-8s Rabatt %-5s subtotal %-8s total %-8s Steuern %s Kurs-Cur %s"
              % (lz["display_type"] or "product", lz["quantity"], lz["price_unit"], lz["discount"],
                 lz["price_subtotal"], lz["price_total"], lz["tax_ids"], lz["currency_id"]))
    try:
        kw("account.move", "unlink", [[neu]])
        print("   Testrechnung geloescht")
    except Exception as exc:
        print("   Testrechnung blieb bestehen: %s" % str(exc)[:120])
    return 0


if __name__ == "__main__":
    sys.exit(main())
