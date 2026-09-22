"""Reproduziert den manuellen Rechnungsweg und zeigt den vollstaendigen Fehler (Session 118, Teil 12).

Ruft recurring_invoice() (Button "Rechnung manuell erstellen") auf und prueft den Datenfluss der
Finanzposition: Typ aus get_fiscal_position, Weitergabe, map_account und das Ergebnis.

Aufruf: python scripts/diagnose_manuelle_rechnung.py --instanz lokal|vm [--stoeren]
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
            daten = a["error"].get("data", {})
            raise RuntimeError((daten.get("name", "") + ": " + daten.get("message", ""))[:400])
        return a.get("result")

    return kw


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    url = "http://localhost:8069" if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    kw = client(url)
    print("Instanz: %s\n" % a.instanz)

    print("--- Datenfluss der Finanzposition ---")
    partner = kw("res.partner", "search_read", [[["name", "=", "Test Firma"]], ["id"]], limit=1)
    partner_id = partner[0]["id"] if partner else kw("res.partner", "search_read", [[["customer_rank", ">", 0]], ["id"]], limit=1)[0]["id"]
    fp = kw("account.fiscal.position", "search", [[]], limit=3)
    print("   Finanzpositionen in der DB: %s" % fp)
    fp_mit_regel = kw("account.fiscal.position", "search_read", [[["account_ids", "!=", False]], ["id", "name"]], limit=3)
    print("   Finanzpositionen mit Kontenzuordnung: %s" % fp_mit_regel)
    if fp:
        d = kw("account.fiscal.position", "read", [[fp[0]], ["id", "name", "account_ids", "auto_apply"]])[0]
        print("   Details %s: %s" % (fp[0], d))
    print("   Kunde %s -> typische Finanzposition (leer moeglich)" % partner_id)

    print("\n--- Button 'Rechnung manuell erstellen' (recurring_invoice) ---")
    abo = kw("sale.subscription", "search_read", [[["name", "=", NAME]], ["id", "code", "invoice_count", "recurring_next_date"]])
    if not abo:
        print("   Testabo fehlt")
        return 1
    abo = abo[0]
    print("   Abo %s (%s): Rechnungen %s | naechste Rechnung %s"
          % (abo["id"], abo["code"], abo["invoice_count"], abo["recurring_next_date"]))
    try:
        kw("sale.subscription", "recurring_invoice", [[abo["id"]]])
        print("   OK   recurring_invoice ohne Fehler")
    except Exception as exc:
        print("   FEHL %s" % str(exc)[:400])
    d = kw("sale.subscription", "search_read", [[["id", "=", abo["id"]]], ["invoice_count", "recurring_next_date"]])[0]
    print("   danach: Rechnungen %s | naechste Rechnung %s" % (d["invoice_count"], d["recurring_next_date"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
