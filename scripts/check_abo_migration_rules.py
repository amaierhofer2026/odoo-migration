"""Verifikation der Abo-Migrationsregeln auf der VM (Session 118, Teil 8, Version 2).

Klaert zwei Fragen abschliessend:
  1. Wo wirkt qty_multiplication_factor? (Abo-Zeile, wiederkehrender Preis, Rechnungszeile)
  2. Was passiert beim Rechnungslauf mit recurring_next_date (doppelte Rechnungen?)

Aufruf: python scripts/check_abo_migration_rules.py
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://k001959vsx.ipax.at"
FAELLE = [(1, 1000), (2, 500), (1, 250), (3, 100)]


def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            w[k.strip()] = v.strip()
    return w


def client():
    env = lade_env(os.path.join(REPO, ".env"))
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(URL + "/web/session/authenticate",
                                 data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
                                     "db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                     "password": env["ODOO18_PWD"]}}).encode(),
                                 headers={"Content-Type": "application/json"})
    with op.open(req, timeout=120) as f:
        f.read()

    def kw(modell, methode, args, **kwargs):
        r = urllib.request.Request(URL + "/web/dataset/call_kw",
                                   data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
                                       "model": modell, "method": methode, "args": args,
                                       "kwargs": kwargs}}).encode(),
                                   headers={"Content-Type": "application/json"})
        with op.open(r, timeout=600) as f:
            a = json.loads(f.read().decode())
        if "error" in a:
            raise RuntimeError(json.dumps(a["error"].get("data", {}).get("message", ""))[:280])
        return a.get("result")

    return kw


def main() -> int:
    kw = client()
    partner = kw("res.partner", "search_read", [[["name", "=", "Test Firma"]], ["id"]], limit=1)[0]["id"]
    prod = kw("product.product", "search_read", [[["sale_ok", "=", True]], ["id", "name", "uom_id"]], limit=1)[0]
    kurs = kw("product.pricelist", "search_read", [[["currency_id.name", "=", "EUR"]], ["id"]], limit=1)[0]["id"]
    vorlage = kw("sale.subscription.template", "search_read", [[], ["id"]], limit=1)[0]
    basis = {"partner_id": partner, "pricelist_id": kurs, "template_id": vorlage["id"],
             "recurring_rule_type": "monthly", "recurring_interval": 1, "date_start": "2026-08-01",
             "user_id": False, "recurring_next_date": "2026-09-21"}

    print("### 1) Abo-Zeile: Wirkung des Multiplikationsfaktors ###")
    abos = []
    for menge, faktor in FAELLE:
        werte = dict(basis)
        werte["name"] = "TEST Faktor %s-%s" % (menge, faktor)
        abo = kw("sale.subscription", "create", [werte])
        kw("sale.subscription.line", "create", [{
            "analytic_account_id": abo, "product_id": prod["id"], "name": "Testzeile",
            "quantity": menge, "price_unit": 65.0, "uom_id": prod["uom_id"][0],
            "qty_multiplication_factor": faktor}])
        kw("sale.subscription", "write", [[abo], {"state": "open"}])
        z = kw("sale.subscription.line", "search_read", [[["analytic_account_id", "=", abo]],
                                                        ["quantity", "price_unit", "price_subtotal", "qty_multiplication_factor"]])[0]
        kopf = kw("sale.subscription", "read", [[abo], ["recurring_total"]])[0]
        abos.append((abo, menge, faktor, z, kopf["recurring_total"]))
        print("   Abo %-4s Menge %-5s Faktor %-5s -> Zeile quantity=%-5s subtotal=%-9s | Abo wiederkehrend %-9s | Menge*Preis = %.2f"
              % (abo, menge, faktor, z["quantity"], z["price_subtotal"], kopf["recurring_total"], menge * 65.0))

    print("\n### 2) Rechnungslauf ###")
    crons = kw("ir.cron", "search_read", [[["model_id.model", "like", "sale.subscription"]],
                                          ["name", "active", "interval_number", "interval_type", "nextcall"]])
    for c in crons:
        print("   Cron %-52s aktiv=%s alle %s %s" % (c["name"][:52], c["active"], c["interval_number"], c["interval_type"]))
    cid = [c["id"] for c in crons if "invoice" in c["name"].lower()][0]
    print("   verwendeter Cron: %s" % cid)
    for lauf in (1, 2):
        kw("ir.cron", "method_direct_trigger", [[cid]])
        stand = []
        for abo, menge, faktor, _, _ in abos:
            n = kw("sale.subscription", "read", [[abo], ["invoice_count", "recurring_next_date"]])[0]
            stand.append((abo, n["invoice_count"], n["recurring_next_date"]))
        print("   Lauf %s -> %s" % (lauf, stand))
    print("\n### 3) Rechnungszeilen je Faktorfall ###")
    for abo, menge, faktor, _, _ in abos:
        for m in kw("account.move", "search_read", [[["invoice_line_ids.analytic_account_id", "=", abo]],
                                                   ["name", "state", "amount_total", "currency_id", "invoice_date", "invoice_line_ids"]]):
            print("   Rechnung %-12s %-8s %-9s %s | %s" % (m["name"], m["state"], m["amount_total"], m["currency_id"][1], m["invoice_date"]))
            for z in kw("account.move.line", "search_read", [[["move_id", "=", m["id"]]],
                                                             ["product_id", "name", "quantity", "price_unit", "price_subtotal"]]):
                print("      Zeile: %-22s Menge %-8s Preis %-8s Summe %-9s | %s"
                      % ((z["product_id"][1] if z["product_id"] else "-")[:22], z["quantity"], z["price_unit"],
                         z["price_subtotal"], (z["name"] or "")[:40]))
        print("   (Abo %s: Menge %s, Faktor %s)" % (abo, menge, faktor))
    return 0


if __name__ == "__main__":
    sys.exit(main())
