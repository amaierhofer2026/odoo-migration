"""Read-only Restmessungen Abrechnung: Menues je Modell (full_list), Volumen je Jahr.

Aufruf:  python scripts/analyse_abrechnung_details6.py
Odoo 11 Prod wird ausschliesslich lesend verwendet.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18

CTX = {"lang": "de_DE", "ir.ui.menu.full_list": True}


def lies(k, modell, domain, felder, order=None):
    try:
        return k.kw(modell, "search_read", [domain, felder], order=order, context=CTX)
    except Exception as fehler:
        print("      (Lesefehler %s: %s)" % (modell, str(fehler)[:60].replace("\n", " ")))
        return []


def z(k, modell, domain):
    try:
        return k.kw(modell, "search_count", [domain])
    except Exception as fehler:
        return "FEHLER(%s)" % str(fehler)[:40].replace("\n", " ")


def pfad(k, menu, nach_id, tiefe=0):
    teile = [menu["name"]]
    pid = menu["parent_id"][0] if menu["parent_id"] else False
    while pid and pid in nach_id:
        teile.insert(0, nach_id[pid]["name"])
        pid = nach_id[pid]["parent_id"][0] if nach_id[pid]["parent_id"] else False
    return " / ".join(teile)


def main() -> int:
    lade_env()
    k11 = o11()
    k18 = o18("lokal")

    print("=== 1) Menues je Zielmodell (nur Odoo 11, full_list) ===")
    alle = lies(k11, "ir.ui.menu", [], ["id", "name", "parent_id", "action"])
    nach_id = {m["id"]: m for m in alle}
    for modell in ("account.invoice", "account.payment", "account.move", "account.move.line",
                   "account.analytic.line", "account.analytic.account", "account.journal",
                   "account.account", "account.tax", "account.payment.term", "account.fiscal.position",
                   "account.invoice.report", "account.financial.report", "account.tax.report",
                   "account.print.journal", "account.aged.trial.balance", "account.report.partner.ledger",
                   "account.report.general.ledger", "account.balance.report", "accounting.report",
                   "account.analytic.tag", "tax.adjustments.wizard", "payment.acquirer",
                   "account.bank.statement", "account.bank.statement.line", "itk_valorisierung.valorisierung"):
        for ak in lies(k11, "ir.actions.act_window", [("res_model", "=", modell)], ["id", "name"]):
            for m in [x for x in alle if x["action"] == "ir.actions.act_window,%s" % ak["id"]]:
                print("   %-30s %s" % (modell, pfad(k11, m, nach_id)))

    print("\n=== 2) Volumen Odoo 11 nach Jahr ===")
    for jahr in range(2019, 2027):
        print("   %s: Rechnungen %-6s Zahlungen %-6s Buchungen %s" % (
            jahr,
            z(k11, "account.invoice", [("date_invoice", ">=", "%s-01-01" % jahr),
                                      ("date_invoice", "<=", "%s-12-31" % jahr)]),
            z(k11, "account.payment", [("payment_date", ">=", "%s-01-01" % jahr),
                                      ("payment_date", "<=", "%s-12-31" % jahr)]),
            z(k11, "account.move", [("date", ">=", "%s-01-01" % jahr),
                                   ("date", "<=", "%s-12-31" % jahr)])))

    print("\n=== 3) Beziehungen und Stammdaten (O11) ===")
    print("   verschiedene Kunden auf Rechnungen: %s" % z(k11, "res.partner", [("customer_rank", ">", 0)]))
    print("   Rechnungen mit Ursprung (origin):   %s" % z(k11, "account.invoice", [("origin", "!=", False)]))
    print("   Zahlungen mit Rechnungsbezug:       %s"
          % z(k11, "account.payment", [("invoice_ids", "!=", False)]))
    print("   Abstimmungen (partial/full):        %s / %s"
          % (z(k11, "account.partial.reconcile", []), z(k11, "account.full.reconcile", [])))
    for r in lies(k11, "account.invoice", [("origin", "!=", False)], ["origin"], order="id")[:8]:
        print("      Ursprung-Beispiel: %s" % r["origin"])
    print("   Zahlungen je Journal:")
    for j in lies(k11, "account.journal", [], ["id", "name", "code"], order="id"):
        print("      %-28s %s" % (j["name"][:28], z(k11, "account.payment", [("journal_id", "=", j["id"])])))

    print("\n=== 4) Gegenprobe Odoo 18: gibt es die O11-Berichtsmenues irgendwo? ===")
    for modell in ("account.tax.report", "account.print.journal", "account.aged.trial.balance",
                   "account.financial.report", "account.report.partner.ledger",
                   "account.report.general.ledger", "account.balance.report", "accounting.report",
                   "tax.adjustments.wizard", "payment.icon"):
        print("   %-32s O18: %s" % (modell, z(k18, modell, [])))
    print("   O18 Menues mit 'Kontoauszug'/'Partnerbericht'/'Bilanz'/'Saldo':")
    for m in lies(k18, "ir.ui.menu", [], ["id", "name", "parent_id", "action"]):
        if any(w in m["name"] for w in ("Kontoauszug", "Partnerbericht", "Bilanz", "Saldo", "Steuerbericht")):
            print("      id=%-5s %-28s action=%s" % (m["id"], m["name"], m["action"] or "-"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
