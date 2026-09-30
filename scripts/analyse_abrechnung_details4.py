"""Read-only Detailpruefung Abrechnung Teil 4: Steuerbericht-Zugang O18, Feldnamen, Anhaenge.

Aufruf:  python scripts/analyse_abrechnung_details4.py [--instanz lokal|vm]
Odoo 11 Prod wird ausschliesslich lesend verwendet.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18


def lies(k, modell, domain, felder, order=None):
    try:
        return k.kw(modell, "search_read", [domain, felder], order=order, context={"lang": "de_DE"})
    except Exception as fehler:
        print("      (Lesefehler %s: %s)" % (modell, str(fehler)[:70].replace("\n", " ")))
        return []


def z(k, modell, domain):
    try:
        return k.kw(modell, "search_count", [domain])
    except Exception as fehler:
        return "FEHLER(%s)" % str(fehler)[:40].replace("\n", " ")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    a = p.parse_args()
    lade_env()
    k11 = o11()
    k18 = o18(a.instanz)

    print("=== 1) O18: Woher kommt account.report, wo ist der Steuerbericht? ===")
    for m in lies(k18, "ir.model", [("model", "=", "account.report")], ["model", "modules", "name"]):
        print("   ir.model: %s | modules=%s" % (m["model"], m["modules"]))
    for typ in ("ir.actions.client", "ir.actions.act_window", "ir.actions.server", "ir.actions.report"):
        felder = ["id", "name"] + (["tag"] if typ == "ir.actions.client" else [])
        for ak in lies(k18, typ, [], felder, order="id"):
            treffer = "account" in str(ak.get("tag") or "") or "report" in str(ak.get("name") or "").lower()
            if not treffer:
                continue
            menues = lies(k18, "ir.ui.menu", [("action", "=", "%s,%s" % (typ, ak["id"]))],
                          ["id", "name", "parent_id"], order="id")
            if menues:
                print("   %-20s %-40s Menues: %s" % (typ, ak["name"][:40],
                                                     [(m["id"], m["name"]) for m in menues]))
    print("   O18 Menues mit 'Steuer'/'Bericht' im Namen:")
    for m in lies(k18, "ir.ui.menu", [], ["id", "name", "parent_id", "action"], order="id"):
        if any(w in (m["name"] or "") for w in ("Steuer", "Bericht", "UVA", "Auswertung")):
            print("      id=%-5s %-46s action=%s" % (m["id"], m["name"], m["action"] or "-"))

    print("\n=== 2) Feldnamen Rechnung: O11 gegen O18 (Referenz/Ursprung/Zahlungsreferenz) ===")
    for feld11, feld18 in (("origin", "invoice_origin"), ("reference", "ref"),
                           ("payment_term_id", "invoice_payment_term_id"),
                           ("payment_move_id", "invoice_payments_widget"),
                           ("commercial_partner_id", "commercial_partner_id"),
                           ("partner_id", "partner_id"), ("residual", "amount_residual"),
                           ("date_invoice", "invoice_date"), ("date_due", "invoice_date_due"),
                           ("date", "date"), ("user_id", "invoice_user_id"),
                           ("sent", "is_move_sent"), ("number", "name"),
                           ("payment_reference", "payment_reference"),
                           ("account_id", "account_id"), ("move_name", "name")):
        print("   %-24s O11: %-12s | %-26s O18: %s"
              % (feld11, z(k11, "account.invoice", [(feld11, "!=", False)]),
                 feld18, z(k18, "account.move", [(feld18, "!=", False)])))

    print("\n=== 3) Rechnungszeilen: Feldnamen und Felder mit Werten ===")
    for feld11, feld18 in (("price_subtotal", "price_subtotal"), ("price_total", "price_total"),
                           ("invoice_line_tax_ids", "tax_ids"), ("account_analytic_id", "analytic_distribution"),
                           ("account_id", "account_id"), ("quantity", "quantity"),
                           ("price_unit", "price_unit"), ("discount", "discount"),
                           ("uom_id", "product_uom_id"), ("invoice_id", "move_id"),
                           ("valorisation_text", "valorisierung_id")):
        print("   %-24s O11: %-12s | %-26s O18: %s"
              % (feld11, z(k11, "account.invoice.line", [(feld11, "!=", False)]),
                 feld18, z(k18, "account.move.line", [(feld18, "!=", False)])))

    print("\n=== 4) Mailversand/Anhaenge zu Rechnungen (Nutzungsnachweis) ===")
    for name, k, modell in (("O11", k11, "account.invoice"), ("O18", k18, "account.move")):
        print("   %s Anhaenge (ir.attachment) zu %-14s %s" % (name, modell,
                                                              z(k, "ir.attachment", [("res_model", "=", modell)])))
        print("   %s Mails (mail.message) zu %-17s %s" % (name, modell,
                                                          z(k, "mail.message", [("model", "=", modell)])))
    print("   O11 Rechnungskontakte im Chatter: %s"
          % z(k11, "mail.message", [("model", "=", "account.invoice"), ("message_type", "=", "email")]))

    print("\n=== 5) Berichte/Druckvorlagen auf Rechnungen ===")
    for name, k, modell in (("O11", k11, "account.invoice"), ("O18", k18, "account.move")):
        for r in lies(k, "ir.actions.report", [("model", "=", modell)],
                      ["id", "name", "report_name", "report_type", "attachment", "binding_model_id"],
                      order="id"):
            print("   %s %-38s %-16s typ=%s bindung=%s" % (name, r["name"][:38], r["report_name"],
                                                           r["report_type"], r.get("binding_model_id")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
