"""Reproduziert den Fehler mit einer Finanzposition MIT Kontenzuordnung (Session 118, Teil 12).

Setzt auf dem Testabo voruebergehend einen Partner mit der Finanzposition "Drittstaaten"
(Kontenzuordnung vorhanden), ruft map_account direkt und danach recurring_invoice auf,
und stellt den Ausgangszustand wieder her.

Aufruf: python scripts/repro_fiscal_position.py --instanz lokal|vm
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
            d = a["error"].get("data", {})
            raise RuntimeError((d.get("name", "") + ": " + d.get("message", ""))[:500])
        return a.get("result")

    return kw


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    url = "http://localhost:8069" if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    kw = client(url)
    print("Instanz: %s\n" % a.instanz)

    print("--- Finanzpositionen mit Kontenzuordnung ---")
    for fp in kw("account.fiscal.position", "search_read", [[["account_map", "!=", False]], ["id", "name", "auto_apply"]], limit=5):
        print("   %s %s auto_apply=%s" % (fp["id"], fp["name"], fp["auto_apply"]))
    ziel = kw("account.fiscal.position", "search_read", [[["account_map", "!=", False]], ["id", "name"]], limit=1)
    if not ziel:
        print("   keine Finanzposition mit Kontenzuordnung vorhanden - Fehler nicht reproduzierbar")
        return 0
    fp_id = ziel[0]["id"]
    print("   verwendet: %s %s" % (fp_id, ziel[0]["name"]))

    print("\n--- map_account direkt ---")
    konto = kw("account.account", "search_read", [[["account_type", "=", "income"]], ["id", "code"]], limit=1)[0]
    print("   Testkonto %s %s" % (konto["id"], konto["code"]))
    for variante, argument in [("ID (int)", konto["id"]), ("Recordset (Odoo 18 erwartet das)", [konto["id"]])]:
        try:
            ergebnis = kw("account.fiscal.position", "map_account", [[fp_id], argument])
            print("   %-38s -> %s" % (variante, ergebnis))
        except Exception as exc:
            print("   %-38s -> FEHLER: %s" % (variante, str(exc)[:200]))

    print("\n--- recurring_invoice mit Partner an der Finanzposition ---")
    abo = kw("sale.subscription", "search_read", [[["name", "=", NAME]], ["id", "code", "partner_id", "invoice_count"]])[0]
    partner_id = abo["partner_id"][0]
    alt = kw("res.partner", "read", [[partner_id], ["property_account_position_id"]])[0]["property_account_position_id"]
    print("   Abo %s, Kunde %s, bisherige Finanzposition: %s" % (abo["id"], abo["partner_id"][1], alt))
    kw("res.partner", "write", [[partner_id], {"property_account_position_id": fp_id}])
    try:
        kw("sale.subscription", "recurring_invoice", [[abo["id"]]])
        print("   OK   recurring_invoice ohne Fehler")
    except Exception as exc:
        print("   FEHL recurring_invoice: %s" % str(exc)[:300])
    d = kw("sale.subscription", "read", [[abo["id"]], ["invoice_count", "recurring_next_date"]])[0]
    print("   danach: Rechnungen %s | naechste Rechnung %s" % (d["invoice_count"], d["recurring_next_date"]))
    kw("res.partner", "write", [[partner_id], {"property_account_position_id": alt[0] if alt else False}])
    print("   Finanzposition des Kunden wiederhergestellt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
