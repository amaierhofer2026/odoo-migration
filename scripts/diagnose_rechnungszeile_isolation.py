"""Isolation: rechnet Odoo 18 auf dieser Instanz korrekt? (Session 118, Teil 10)

(a) liest eine bestehende, nicht von ITK erzeugte Rechnungszeile
(b) legt eine Testrechnung mit einer Zeile ueber die normale Odoo-API an und prueft die Summe
(c) legt dieselbe Zeile mit den von itk_subscription gesetzten Zusatzwerten an und prueft erneut
Danach wird die Testrechnung wieder geloescht.

Aufruf: python scripts/diagnose_rechnungszeile_isolation.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FELDER = ["id", "name", "quantity", "price_unit", "discount", "price_subtotal", "price_total",
          "currency_id", "tax_ids", "account_id", "analytic_distribution", "product_uom_id"]


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


def zeige(kw, titel, move_id):
    d = kw("account.move", "read", [[move_id], ["name", "state", "amount_untaxed", "amount_total", "currency_id"]])[0]
    print("   %s: Rechnung %s (%s) untaxed %s | total %s %s"
          % (titel, d["name"], d["state"], d["amount_untaxed"], d["amount_total"], d["currency_id"][1]))
    for lz in kw("account.move.line", "search_read", [[["move_id", "=", move_id]], FELDER], limit=10):
        print("      Zeile: Menge %-6s Preis %-8s Rabatt %-5s subtotal %-8s total %-8s Steuern %s"
              % (lz["quantity"], lz["price_unit"], lz["discount"], lz["price_subtotal"], lz["price_total"],
                 lz["tax_ids"]))
    return d


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    url = "http://localhost:8069" if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    kw = client(url)
    print("Instanz: %s\n" % a.instanz)

    print("--- (a) bestehende Rechnungszeilen anderer Herkunft ---")
    fremd = kw("account.move.line", "search_read",
               [[["display_type", "=", "product"], ["move_id.move_type", "=", "out_invoice"]],
                FELDER + ["move_id"]], limit=4)
    for lz in fremd:
        print("   %-12s Menge %-6s Preis %-8s Rabatt %-5s subtotal %-9s Steuern %s"
              % (lz["move_id"][1], lz["quantity"], lz["price_unit"], lz["discount"], lz["price_subtotal"], lz["tax_ids"]))

    partner = kw("res.partner", "search_read", [[["customer_rank", ">", 0]], ["id"]], limit=1)[0]["id"]
    prod = kw("product.product", "search_read", [[["sale_ok", "=", True]], ["id", "name", "uom_id", "taxes_id"]], limit=1)[0]
    print("\n   Testprodukt %s | UoM %s | Steuern %s" % (prod["name"][:28], prod["uom_id"], prod["taxes_id"]))

    print("\n--- (b) Testrechnung, Zeile nur mit Produkt/Menge/Preis ---")
    m1 = kw("account.move", "create", [{"move_type": "out_invoice", "partner_id": partner, "invoice_line_ids": [
        (0, 0, {"product_id": prod["id"], "name": "Isolation B", "quantity": 1.0, "price_unit": 65.0})]}])
    zeige(kw, "ohne Zusatzwerte", m1)

    print("\n--- (c) Testrechnung mit den Werten wie itk_subscription ---")
    spalte = kw("sale.subscription", "search_read", [[], ["id", "analytic_account_id"]], limit=1)
    zusatz = {"product_id": prod["id"], "name": "Isolation C", "quantity": 1.0, "price_unit": 65.0,
              "discount": 0.0, "product_uom_id": prod["uom_id"][0], "tax_ids": [(6, 0, prod["taxes_id"])],
              "analytic_distribution": {}, "subscription_id": spalte[0]["id"] if spalte else False}
    m2 = kw("account.move", "create", [{"move_type": "out_invoice", "partner_id": partner, "invoice_line_ids": [
        (0, 0, zusatz)]}])
    zeige(kw, "mit Zusatzwerten", m2)

    print("\n--- Aufraeumen ---")
    for m in (m1, m2):
        try:
            kw("account.move", "unlink", [[m]])
            print("   Testrechnung %s geloescht" % m)
        except Exception as exc:
            print("   Testrechnung %s konnte nicht geloescht werden: %s" % (m, str(exc)[:120]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
