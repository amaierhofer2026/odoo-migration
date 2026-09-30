"""Read-only Detailpruefung Abrechnung Teil 5: Berichts-/Zahlungsmodelle beider Systeme.

Aufruf:  python scripts/analyse_abrechnung_details5.py [--instanz lokal|vm]
Odoo 11 Prod wird ausschliesslich lesend verwendet.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18

MODELLE_O11 = [
    "accounting.report", "account.balance.report", "account.report.general.ledger",
    "account.report.partner.ledger", "account.financial.report", "account.print.journal",
    "account.aged.trial.balance", "account.tax.report", "tax.adjustments.wizard",
    "payment.token", "payment.icon", "account.bank.statement.import", "account.bank.statement",
    "account.journal.group", "account.tax.group", "account.secure.entries.wizard",
    "account.invoice.line.report", "account.invoice.refund", "account.change.lock.date",
    "account.move.reversal", "account.payment.register", "account.automatic.reconcile",
    "account.reconcile.model", "account.account.type", "account.analytic.tag",
]
MODELLE_O18 = [
    "account.report", "account.report.line", "account.report.column", "account.report.expression",
    "account.financial.report", "account.print.journal", "account.aged.trial.balance",
    "account.tax.report", "tax.adjustments.wizard", "payment.token", "payment.icon",
    "account.bank.statement", "account.journal.group", "account.tax.group",
    "account.secure.entries.wizard", "account.invoice.line.report", "account.move.reversal",
    "account.payment.register", "account.reconcile.model", "account.account.type",
    "account.analytic.tag", "account.account.tag", "account.account.report",
]


def z(k, modell, domain=None):
    try:
        return k.kw(modell, "search_count", [domain or []])
    except Exception as fehler:
        kurz = str(fehler)
        if "404" in kurz:
            return "MODELL FEHLT"
        return "FEHLER(%s)" % kurz[:36].replace("\n", " ")


def lies(k, modell, domain, felder, order=None):
    try:
        return k.kw(modell, "search_read", [domain, felder], order=order,
                    context={"lang": "de_DE", "ir.ui.menu.full_list": True})
    except Exception:
        return []


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    a = p.parse_args()
    lade_env()
    k11 = o11()
    k18 = o18(a.instanz)

    print("=== Berichts- und Zahlungsmodelle: O11 (Name) | O18 (Name) ===")
    for n in zip(MODELLE_O11, MODELLE_O18 + ["-"] * len(MODELLE_O11)):
        print("   %-32s O11: %-14s | %-34s O18: %s"
              % (n[0], z(k11, n[0]), n[1], z(k18, n[1]) if n[1] != "-" else "-"))

    print("\n=== O11: Finanzberichte (account.financial.report) ===")
    for r in lies(k11, "account.financial.report", [], ["id", "name", "type", "sequence"], order="sequence"):
        print("   id=%-3s %-8s %s" % (r["id"], r["type"], r["name"][:60]))

    print("\n=== O11: Business-Intelligence-Knoten und Bankbeleg-Menues ===")
    for mid in (273, 176, 177):
        m = lies(k11, "ir.ui.menu", [("id", "=", mid)], ["id", "name", "parent_id", "action"])
        print("   Menue %s: %s" % (mid, m))

    print("\n=== O18: Kontoauszugs-/Partnerberichte (Community-Besetzung) ===")
    for ak in lies(k18, "ir.actions.act_window", [], ["id", "name", "res_model"], order="id"):
        if ak["res_model"] in ("account.bank.statement.line", "account.report", "account.move.line"):
            menues = lies(k18, "ir.ui.menu", [("action", "=", "ir.actions.act_window,%s" % ak["id"])],
                          ["id", "name", "parent_id"])
            for m in menues:
                print("   %-24s %-40s Menue %s (%s)" % (ak["res_model"], ak["name"][:40],
                                                        m["name"], m["id"]))
    print("   O18 Menues mit leerem Berichtswesen-Zweig:")
    for m in lies(k18, "ir.ui.menu", [], ["id", "name", "parent_id", "action"], order="id"):
        if m["name"] in ("Kontoauszugsberichte", "Partnerberichte", "Verwaltung", "Berichtswesen",
                         "Berichtswesen ", "Business Intelligence", "Deutsche Belege",
                         "Allgemeine Bankbelege", "Erinnerung", "Erzeuge Buchungen"):
            print("      id=%-5s %-26s parent=%s action=%s"
                  % (m["id"], m["name"], m["parent_id"], m["action"] or "-"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
