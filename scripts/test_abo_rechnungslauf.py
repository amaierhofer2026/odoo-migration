"""Nachweis: automatische Rechnungserzeugung aus einem Abo (Session 118, Teil 9).

Legt ein realistisches Testabo an (Vorlage, EUR-Preisliste, Kunde, Abo-Zeile, Produkt),
setzt recurring_next_date auf einen Testtermin und fuehrt den Cronjob
"Sale Subscription: generate recurring invoices and payments" aus.

Geprueft wird: genau eine Rechnung, invoice_count, Weiterschreibung von recurring_next_date,
kein Duplikat beim zweiten Lauf, Rechnung in EUR, Verknuepfung Abo <-> Rechnung.

Aufruf: python scripts/test_abo_rechnungslauf.py --instanz lokal|vm
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
FELDER_RECHNUNG = ["name", "state", "move_type", "amount_untaxed", "amount_tax", "amount_total",
                   "currency_id", "invoice_date", "invoice_origin"]


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


def suche(kw, modell, domain, felder, limit=1):
    return kw(modell, "search_read", [domain, felder], limit=limit)


def abo_lesen(kw, abo, felder):
    return kw("sale.subscription", "read", [[abo], felder])[0]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="vm")
    a = p.parse_args()
    url = "http://localhost:8069" if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    kw = client(url)
    print("Instanz: %s (%s)" % (a.instanz, url))
    ok = fehler = 0

    def pruefe(bed, txt):
        nonlocal ok, fehler
        if bed:
            ok += 1
            print("  OK   %s" % txt)
        else:
            fehler += 1
            print("  FEHL %s" % txt)

    alt = kw("sale.subscription", "search", [[["name", "=", NAME]]])
    if alt:
        kw("sale.subscription", "unlink", [alt])
    partner = suche(kw, "res.partner", [["customer_rank", ">", 0]], ["id", "name"])
    partner_id = partner[0]["id"]
    kurs = suche(kw, "product.pricelist", [["currency_id.name", "=", "EUR"], ["active", "=", True]], ["id", "name"])[0]
    prod = suche(kw, "product.product", [["sale_ok", "=", True]], ["id", "name", "uom_id"])[0]
    vorlage = suche(kw, "sale.subscription.template", [["payment_mandatory", "=", False]],
                    ["id", "name", "payment_mandatory"])[0]
    termin = "2026-09-21"
    werte = {"name": NAME, "partner_id": partner_id, "pricelist_id": kurs["id"], "template_id": vorlage["id"],
             "recurring_rule_type": "monthly", "recurring_interval": 1, "date_start": "2026-08-01",
             "recurring_next_date": termin, "user_id": False}
    abo = kw("sale.subscription", "create", [werte])
    kw("sale.subscription.line", "create", [{"analytic_account_id": abo, "product_id": prod["id"],
                                             "name": "Abonnement Test", "quantity": 1, "price_unit": 65.0,
                                             "uom_id": prod["uom_id"][0], "qty_multiplication_factor": 1}])
    kw("sale.subscription", "set_open", [[abo]])
    d = abo_lesen(kw, abo, ["name", "code", "state", "recurring_next_date", "recurring_total", "pricelist_id"])
    print("\nTestabo %s (%s): Status %s | Preisliste %s | wiederkehrend %s | naechste Rechnung %s"
          % (abo, d["code"], d["state"], d["pricelist_id"][1], d["recurring_total"], d["recurring_next_date"]))
    print("   Vorlage: %s (Zahlungspflicht %s) | Kunde: %s | Produkt: %s"
          % (vorlage["name"], vorlage["payment_mandatory"], partner[0]["name"], prod["name"][:30]))
    pruefe(d["state"] == "open", "Abo Status = Laufend")
    pruefe("EUR" in d["pricelist_id"][1], "EUR-Preisliste hinterlegt")
    pruefe(abs(d["recurring_total"] - 65.0) < 0.01, "Abo-Zeile mit Produkt und Betrag vorhanden (65,00)")

    cron = suche(kw, "ir.cron", [["name", "like", "generate recurring invoices"], ["active", "=", True]],
                 ["id", "name", "interval_number", "interval_type"])
    if not cron:
        print("  FEHL Cronjob nicht gefunden")
        return 1
    cid = cron[0]["id"]
    print("   Cronjob: %s (id %s, alle %s %s)" % (cron[0]["name"], cid, cron[0]["interval_number"], cron[0]["interval_type"]))
    kw("ir.cron", "method_direct_trigger", [[cid]])
    d1 = abo_lesen(kw, abo, ["invoice_count", "recurring_next_date"])
    print("\nNach dem ersten Lauf: Rechnungen %s | naechste Rechnung %s" % (d1["invoice_count"], d1["recurring_next_date"]))
    pruefe(d1["invoice_count"] == 1, "genau eine Rechnung erzeugt")
    pruefe(d1["recurring_next_date"] > termin,
           "recurring_next_date weitergeschrieben (%s -> %s)" % (termin, d1["recurring_next_date"]))

    kw("ir.cron", "method_direct_trigger", [[cid]])
    d2 = abo_lesen(kw, abo, ["invoice_count", "recurring_next_date"])
    print("Nach dem zweiten Lauf: Rechnungen %s | naechste Rechnung %s" % (d2["invoice_count"], d2["recurring_next_date"]))
    pruefe(d2["invoice_count"] == 1, "kein Duplikat beim zweiten Lauf")
    pruefe(d2["recurring_next_date"] == d1["recurring_next_date"], "Termin bleibt nach dem zweiten Lauf unveraendert")

    rechnungen = suche(kw, "account.move", [["invoice_origin", "=", d["code"]]], FELDER_RECHNUNG, limit=5)
    pruefe(len(rechnungen) == 1, "genau eine Rechnung ueber die Abo-Verknuepfung gefunden (invoice_origin = Abo-Code)")
    for r in rechnungen:
        print("   Rechnung %s | %s | %s %s | Datum %s | Herkunft %s"
              % (r["name"], r["state"], r["amount_total"], r["currency_id"][1], r["invoice_date"], r["invoice_origin"]))
        pruefe(r["currency_id"][1] == "EUR", "Rechnung laeuft in EUR")
        pruefe(r["move_type"] == "out_invoice", "Beleg ist eine Kundenrechnung (move_type out_invoice)")
        pruefe(abs(r["amount_untaxed"] - 65.0) < 0.01,
               "Nettobetrag = wiederkehrender Abo-Preis (65,00), Ist: %s" % r["amount_untaxed"])
        pruefe(r["amount_total"] > r["amount_untaxed"],
               "Bruttobetrag inkl. Steuer korrekt (%s netto + %s Steuer = %s)"
               % (r["amount_untaxed"], r["amount_tax"], r["amount_total"]))
        pruefe(r["invoice_origin"] == d["code"], "Verknuepfung Abo <-> Rechnung ueber den Abo-Code vorhanden")
    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
