"""Read-only Analyse Abrechnung Teil 3: Zahlungs-/Abstimmungslogik, Druck und Versand.

Aufruf:  python scripts/analyse_abrechnung_teil3_prozesse.py
Odoo 11 Prod wird ausschliesslich lesend verwendet.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18

WIZARDS_O11 = ["account.invoice.send", "account.invoice.refund", "account.register.payments",
               "account.payment", "account.reconciliation.widget", "account.bank.statement",
               "account.bank.statement.line", "account.reconcile.model", "account.payment.term",
               "account.invoice.confirm", "account.automatic.reconcile"]
WIZARDS_O18 = ["account.move.send", "account.move.send.wizard", "account.move.reversal",
               "account.payment.register", "account.payment", "account.reconciliation.widget",
               "account.bank.statement", "account.bank.statement.line", "account.reconcile.model",
               "account.secure.entries.wizard", "account.move.send.batch.wizard"]


def z(k, modell, domain=None):
    try:
        return k.kw(modell, "search_count", [domain or []])
    except Exception as fehler:
        return "MODELL FEHLT" if "404" in str(fehler) else str(fehler)[:40]


def lies(k, modell, domain, felder, order=None):
    try:
        return k.kw(modell, "search_read", [domain, felder], order=order, context={"lang": "de_DE"})
    except Exception:
        return []


def main() -> int:
    lade_env()
    k11 = o11()
    k18 = o18("lokal")
    aus = {}

    print("=== 1) Wizards/Modelle fuer Zahlung, Abstimmung, Versand ===")
    for name, k, modelle in (("O11", k11, WIZARDS_O11), ("O18", k18, WIZARDS_O18)):
        print("-- %s --" % name)
        for m in modelle:
            print("   %-34s %s" % (m, z(k, m)))

    print("\n=== 2) Aktionen aus dem Odoo-11-Formular (178, 241) ===")
    for aid in (178, 241, 249, 250, 251, 252, 258, 262, 263, 264, 265, 266, 267, 269, 276):
        for ak in lies(k11, "ir.actions.act_window", [("id", "=", aid)],
                       ["id", "name", "res_model", "view_mode", "target", "domain", "context"]):
            print("   %-4s %-42s %-28s %s" % (ak["id"], ak["name"][:42], ak["res_model"],
                                              ak["view_mode"]))
        for ak in lies(k11, "ir.actions.act_window_close", [("id", "=", aid)], ["id", "name"]):
            print("   %-4s (act_window_close) %s" % (ak["id"], ak["name"]))
        for ak in lies(k11, "ir.actions.server", [("id", "=", aid)], ["id", "name", "model_name"]):
            print("   %-4s (server) %-36s %s" % (ak["id"], ak["name"], ak["model_name"]))
        for ak in lies(k11, "ir.actions.client", [("id", "=", aid)], ["id", "name", "tag"]):
            print("   %-4s (client) %-36s %s" % (ak["id"], ak["name"], ak["tag"]))

    print("\n=== 3) Mailvorlagen auf Rechnungen ===")
    for name, k, modell in (("O11", k11, "account.invoice"), ("O18", k18, "account.move")):
        vorlagen = lies(k, "mail.template", [("model", "=", modell)],
                        ["id", "name", "model", "email_from", "auto_delete"])
        print("   %s: %d Mailvorlagen auf %s" % (name, len(vorlagen), modell))
        for v in vorlagen:
            print("      id=%-4s %s" % (v["id"], v["name"]))

    print("\n=== 4) Zahlungs-/Abstimmungsnutzung in Odoo 11 ===")
    print("   Zahlungen gesamt:                 %s" % z(k11, "account.payment", []))
    print("   Zahlungen mit Rechnungsbezug:     %s"
          % z(k11, "account.payment", [("invoice_ids", "!=", False)]))
    print("   Rechnungen im Zustand offen:      %s" % z(k11, "account.invoice", [("state", "=", "open")]))
    print("   Teilabstimmungen:                 %s" % z(k11, "account.partial.reconcile", []))
    print("   Vollabstimmungen:                 %s" % z(k11, "account.full.reconcile", []))
    print("   Bankauszuege/-zeilen:             %s / %s"
          % (z(k11, "account.bank.statement", []), z(k11, "account.bank.statement.line", [])))
    print("   Abstimmungsmodelle:               %s" % z(k11, "account.reconcile.model", []))

    print("\n=== 5) Druckvorlagen (Reports) auf Rechnungen ===")
    for name, k, modell in (("O11", k11, "account.invoice"), ("O18", k18, "account.move")):
        for r in lies(k, "ir.actions.report", [("model", "=", modell)],
                      ["id", "name", "report_name", "report_type", "attachment",
                       "binding_model_id", "multi"], order="id"):
            print("   %s id=%-4s %-40s %-45s typ=%s" % (name, r["id"], r["name"][:40],
                                                       r["report_name"], r["report_type"]))

    print("\n=== 6) Zahlungs-Widgets und Felder im Odoo-11-Formular ===")
    a11 = k11.kw("account.invoice", "fields_view_get", [[], "form"], context={"lang": "de_DE"})["arch"]
    for feld in ("payments_widget", "outstanding_credits_debits_widget", "payment_move_line_ids",
                 "reference_type", "comment", "sent", "residual"):
        print("   %-34s im Arch: %s" % (feld, feld in a11))

    ziel = os.path.join(tempfile.gettempdir(), "abrechnung_teil3_prozesse.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(aus, fh, ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
