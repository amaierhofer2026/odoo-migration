"""Read-only Detailpruefung Abrechnung Teil 3: Menuepfade O18, Ist-Versteuerung, Zahlungsarten.

Aufruf:  python scripts/analyse_abrechnung_details3.py [--instanz lokal|vm]
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


def pfad(k, menu):
    teile = [menu["name"]]
    pid = menu["parent_id"][0] if menu["parent_id"] else False
    while pid:
        eltern = lies(k, "ir.ui.menu", [("id", "=", pid)], ["name", "parent_id"])
        if not eltern:
            break
        teile.insert(0, eltern[0]["name"])
        pid = eltern[0]["parent_id"][0] if eltern[0]["parent_id"] else False
    return " / ".join(teile)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    a = p.parse_args()
    lade_env()
    k11 = o11()
    k18 = o18(a.instanz)

    print("=== 1) O18: Menuepfade der Kostenstellen-/Berichtsmenues ===")
    for ak in lies(k18, "ir.actions.act_window", [("res_model", "=", "account.analytic.line")],
                   ["id", "name", "context"], order="id"):
        for m in lies(k18, "ir.ui.menu", [("action", "=", "ir.actions.act_window,%s" % ak["id"])],
                      ["id", "name", "parent_id"], order="id"):
            print("   menue_id=%-5s %-52s ctx=%s" % (m["id"], pfad(k18, m), (ak["context"] or "-")[:60]))
    print("   O18 account.report-Datensaetze:")
    for r in lies(k18, "account.report", [], ["id", "name"], order="id"):
        print("      id=%-3s %s" % (r["id"], r["name"]))
    for ak in lies(k18, "ir.actions.act_window", [("res_model", "=", "account.report")],
                   ["id", "name"], order="id"):
        for m in lies(k18, "ir.ui.menu", [("action", "=", "ir.actions.act_window,%s" % ak["id"])],
                      ["id", "name", "parent_id"], order="id"):
            print("      Menue: %s (%s)" % (pfad(k18, m), ak["name"]))
    for ak in lies(k18, "ir.actions.client", [("name", "ilike", "%account%")], ["id", "name", "tag"]):
        print("      client action: %s (%s)" % (ak["name"], ak["tag"]))

    print("\n=== 2) Ist-Versteuerung (Cash Basis) ===")
    for name, k in (("O11", k11), ("O18", k18)):
        firma = lies(k, "res.company", [], ["id", "name", "tax_cash_basis_journal_id", "currency_id"],
                     order="id")
        for f in firma:
            print("   %s Firma %s: Cash-Basis-Journal=%s Waehrung=%s"
                  % (name, f["name"][:30], f.get("tax_cash_basis_journal_id"), f.get("currency_id")))
    print("   O11 Buchungen im Journal CABA: %s" % z(k11, "account.move", [("journal_id", "=", 5)]))
    print("   O18 Buchungen im Journal CABA: %s" % z(k18, "account.move", [("journal_id", "=", 5)]))

    print("\n=== 3) Zahlungsarten (payment_method_id) ===")
    for name, k, modell in (("O11", k11, "account.payment.method"), ("O18", k18, "account.payment.method.line")):
        for m in lies(k, modell, [], ["id", "name"], order="id")[:12]:
            print("   %s %-12s id=%-3s %s" % (name, modell, m["id"], m.get("name")))

    print("\n=== 4) Rechnungsnummern-Kreis und Nummernvergabe ===")
    for name, k, modell in (("O11", k11, "account.invoice"), ("O18", k18, "account.move")):
        r = lies(k, modell, [("number", "!=", False)], ["number"], order="number desc")
        print("   %s hoechste Nummer: %s" % (name, r[0]["number"] if r else "-"))
        r = lies(k, modell, [("number", "!=", False)], ["number"], order="number asc")
        print("   %s aelteste Nummer: %s" % (name, r[0]["number"] if r else "-"))

    print("\n=== 5) Zustands-/Feldunterschiede Rechnung (O11 vs O18) ===")
    for feld in ("state", "payment_state", "amount_residual", "residual", "type", "move_type",
                 "date_invoice", "invoice_date", "date_due", "invoice_date_due", "reference",
                 "name", "origin", "journal_id", "currency_id", "user_id", "invoice_user_id"):
        s11 = z(k11, "account.invoice", [(feld, "!=", False)])
        s18 = z(k18, "account.move", [(feld, "!=", False)])
        print("   %-20s O11: %-12s O18: %s" % (feld, s11, s18))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
