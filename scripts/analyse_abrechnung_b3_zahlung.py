"""Read-only B3: Zahlungsweg Odoo 11 gegen Odoo 18.

Aufruf:  python scripts/analyse_abrechnung_b3_zahlung.py
Odoo 11 Prod wird ausschliesslich lesend verwendet.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18

FELDER = ["name", "field_description", "ttype", "relation", "required", "readonly", "store"]


def felder(k, modell, nur=None):
    roh = k.kw("ir.model.fields", "search_read", [[("model", "=", modell)], FELDER], order="name")
    if nur:
        roh = [f for f in roh if any(m in f["name"] for m in nur)]
    return roh


def main() -> int:
    lade_env()
    k11, k18 = o11(), o18("lokal")

    print("=" * 78)
    print("1) Odoo 11: Zahlungsmodelle und ihre Felder")
    print("=" * 78)
    for modell in ("account.payment",):
        roh = felder(k11, modell)
        print("-- %s (%d Felder) --" % (modell, len(roh)))
        for f in roh:
            beschr = k11.kw(modell, "fields_get", [[f["name"]], ["string", "selection"]],
                            context={"lang": "de_DE"}).get(f["name"], {})
            zusatz = ""
            if beschr.get("selection"):
                zusatz = " | Auswahl: %s" % beschr["selection"]
            print("   %-30s %-12s %-34s req=%-5s%s"
                  % (f["name"], f["ttype"], (f["field_description"] or "")[:34], f["required"], zusatz))
    print("-- Assistent account.register.payments (Odoo 11, unbenutzt) --")
    for f in felder(k11, "account.register.payments"):
        print("   %-30s %-12s %s" % (f["name"], f["ttype"], f["field_description"]))

    print("\n" + "=" * 78)
    print("2) Odoo 11: tatsechliche Nutzung der 5.987 Zahlungen")
    print("=" * 78)
    zahlungen = k11.kw("account.payment", "search_count", [[]])
    print("   Zahlungen gesamt:                    %s" % zahlungen)
    for feld in ("payment_method_id", "journal_id", "communication", "payment_type", "partner_type",
                 "currency_id", "payment_date", "writeoff_account_id", "writeoff_label",
                 "payment_difference", "payment_difference_handling", "state", "payment_reference"):
        try:
            belegt = k11.kw("account.payment", "search_count", [[(feld, "!=", False)]])
            leer = k11.kw("account.payment", "search_count", [[(feld, "=", False)]])
            print("   %-32s belegt=%-6s leer=%s" % (feld, belegt, leer))
        except Exception as fehler:
            print("   %-32s nicht lesbar (%s)" % (feld, str(fehler)[:40]))
    print("-- Verteilung nach Zahlungsart und Journal --")
    for feld in ("payment_method_id", "journal_id", "payment_type", "partner_type", "state"):
        try:
            for g in k11.kw("account.payment", "read_group", [[], [feld], [feld]],
                            context={"lang": "de_DE"}, lazy=False):
                print("   %-18s %-32s %s" % (feld, (g.get(feld) or ["", ""])[1] if isinstance(g.get(feld), list) else g.get(feld), g.get("__count")))
        except Exception as fehler:
            print("   %-18s nicht lesbar (%s)" % (feld, str(fehler)[:40]))
    print("-- Zahlungsarten (account.payment.method) --")
    for m in k11.kw("account.payment.method", "search_read",
                    [[], ["id", "name", "code", "payment_type"]], order="id"):
        print("   id=%-4s %-28s code=%-10s typ=%s" % (m["id"], m["name"], m["code"], m["payment_type"]))
    print("-- Journale --")
    for j in k11.kw("account.journal", "search_read",
                    [[], ["id", "name", "code", "type", "inbound_payment_method_ids",
                          "outbound_payment_method_ids"]], order="id"):
        print("   id=%-4s %-30s %-8s %-12s ein=%s aus=%s"
              % (j["id"], j["name"][:30], j["code"], j["type"],
                 j["inbound_payment_method_ids"], j["outbound_payment_method_ids"]))
    print("-- Zahlungsbeispiele --")
    for z in k11.kw("account.payment", "search_read",
                    [[], ["id", "name", "payment_method_id", "journal_id", "payment_date",
                          "communication", "amount", "state", "invoice_ids"]], order="id", limit=5):
        print("   id=%-5s %-12s %-18s %-22s %s %s %s" % (z["id"], z["name"],
              (z["payment_method_id"] or ["", ""])[1], (z["journal_id"] or ["", ""])[1][:22],
              z["payment_date"], z["amount"], (z["communication"] or "")[:30]))

    print("\n" + "=" * 78)
    print("3) Odoo 18: Zahlungsweg")
    print("=" * 78)
    print("-- Assistent account.payment.register --")
    for f in felder(k18, "account.payment.register"):
        beschr = k18.kw("account.payment.register", "fields_get", [[f["name"]], ["string", "selection"]],
                        context={"lang": "de_DE"}).get(f["name"], {})
        zusatz = " | Auswahl: %s" % beschr["selection"] if beschr.get("selection") else ""
        print("   %-34s %-12s %-32s%s" % (f["name"], f["ttype"], (beschr.get("string") or "")[:32], zusatz))
    print("-- Zahlungsarten-Modell (account.payment.method + Zeilen) --")
    for m in k18.kw("account.payment.method", "search_read",
                    [[], ["id", "name", "code", "payment_type"]], order="id"):
        print("   id=%-4s %-28s code=%-10s typ=%s" % (m["id"], m["name"], m["code"], m["payment_type"]))
    for z in k18.kw("account.payment.method.line", "search_read",
                    [[], ["id", "name", "journal_id", "payment_method_id", "payment_type"]], order="id"):
        print("   Zeile id=%-4s %-24s Journal=%-24s typ=%s"
              % (z["id"], z["name"], (z["journal_id"] or ["", ""])[1], z["payment_type"]))
    print("-- Journale --")
    for j in k18.kw("account.journal", "search_read",
                    [[], ["id", "name", "code", "type", "inbound_payment_method_line_ids",
                          "outbound_payment_method_line_ids"]], order="id"):
        print("   id=%-4s %-26s %-8s %-12s ein=%s aus=%s"
              % (j["id"], j["name"][:26], j["code"], j["type"],
                 j["inbound_payment_method_line_ids"], j["outbound_payment_method_line_ids"]))
    print("-- Zahlungen im Testbestand --")
    for z in k18.kw("account.payment", "search_read",
                    [[], ["id", "name", "payment_method_line_id", "journal_id", "date",
                          "memo", "amount", "state", "partner_type", "payment_type"]], order="id"):
        print("   id=%-4s %-14s %-22s %-20s %s %s" % (z["id"], z["name"],
              (z["payment_method_line_id"] or ["", ""])[1], (z["journal_id"] or ["", ""])[1][:20],
              z["date"], z["amount"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
