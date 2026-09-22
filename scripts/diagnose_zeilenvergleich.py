"""Feldweiser Vergleich: ITK-Rechnungszeile gegen manuell erzeugte Zeile (Session 118, Teil 10).

Erzeugt eine Vergleichsrechnung mit identischen Werten, liest beide Zeilen vollstaendig aus und
gibt nur die abweichenden Felder aus.

Aufruf: python scripts/diagnose_zeilenvergleich.py --instanz lokal|vm
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


def kurz(wert):
    s = str(wert)
    return s[:60]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    url = "http://localhost:8069" if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    kw = client(url)
    print("Instanz: %s\n" % a.instanz)

    abo = kw("sale.subscription", "search_read", [[["name", "=", NAME]], ["id", "code"]])[0]
    move = kw("account.move", "search_read", [[["invoice_origin", "=", abo["code"]]], ["id"]])[0]["id"]
    zeile_itk = kw("account.move.line", "search_read", [[["move_id", "=", move], ["display_type", "=", "product"]],
                                                       ["id"]])[0]["id"]
    felder = [f for f, d in kw("account.move.line", "fields_get", [[], ["type"]]).items()
              if d["type"] in ("float", "monetary", "integer", "char", "boolean", "date", "datetime", "selection")]
    felder = [f for f in felder if f not in ("id", "__last_update", "create_date", "write_date")]

    partner = kw("res.partner", "search_read", [[["customer_rank", ">", 0]], ["id"]], limit=1)[0]["id"]
    prod = kw("product.product", "search_read", [[["sale_ok", "=", True]], ["id"]], limit=1)[0]["id"]
    vergleich = kw("account.move", "create", [{"move_type": "out_invoice", "partner_id": partner,
                                               "invoice_line_ids": [(0, 0, {"product_id": prod, "name": "Vergleich",
                                                                            "quantity": 1.0, "price_unit": 65.0})]}])
    zeile_man = kw("account.move.line", "search_read", [[["move_id", "=", vergleich], ["display_type", "=", "product"]],
                                                        ["id"]])[0]["id"]
    d_itk = kw("account.move.line", "read", [[zeile_itk], felder])[0]
    d_man = kw("account.move.line", "read", [[zeile_man], felder])[0]
    print("Vergleich ITK-Zeile %s (Rechnung %s) gegen manuelle Zeile %s (Rechnung %s)\n"
          % (zeile_itk, move, zeile_man, vergleich))
    print("--- Abweichende Felder ---")
    for f in sorted(felder):
        if d_itk.get(f) != d_man.get(f):
            print("   %-28s ITK: %-34s manuell: %s" % (f, kurz(d_itk.get(f)), kurz(d_man.get(f))))
    print("\n--- Betragsfelder im Direktvergleich ---")
    for f in ["quantity", "price_unit", "discount", "price_subtotal", "price_total", "balance", "amount_currency",
              "debit", "credit", "tax_ids", "account_id", "analytic_distribution", "product_uom_id", "currency_id"]:
        print("   %-24s ITK %-28s manuell %s" % (f, kurz(d_itk.get(f)), kurz(d_man.get(f))))
    try:
        kw("account.move", "unlink", [[vergleich]])
        print("\nVergleichsrechnung geloescht")
    except Exception as exc:
        print("\nVergleichsrechnung blieb bestehen: %s" % str(exc)[:100])
    return 0


if __name__ == "__main__":
    sys.exit(main())
