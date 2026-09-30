"""Read-only Detailpruefung Abrechnung Teil 2: Menuepfade, Aktionen, Verwendung.

Aufruf:  python scripts/analyse_abrechnung_details2.py [--instanz lokal|vm]
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
    """Menuepfad aus Namen aufbauen."""
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

    print("=== 1) Menuepfade je Berichtsmodell ===")
    for name, k in (("O11", k11), ("O18", k18)):
        print("-- %s --" % name)
        for modell in ("account.analytic.line", "account.invoice.report", "account.move",
                       "account.payment", "account.tax.report", "account.print.journal",
                       "account.aged.trial.balance", "itk_valorisierung.valorisierung"):
            for ak in lies(k, "ir.actions.act_window", [("res_model", "=", modell)],
                           ["id", "name", "domain", "context", "view_mode"], order="id"):
                menues = lies(k, "ir.ui.menu",
                              [("action", "=", "ir.actions.act_window,%s" % ak["id"])],
                              ["id", "name", "parent_id"], order="id")
                for m in menues:
                    print("   %-34s | %-46s | domain=%s ctx=%s"
                          % (modell, pfad(k, m), (ak["domain"] or "-")[:40], (ak["context"] or "-")[:60]))

    print("\n=== 2) O18 Enterprise-Kandidaten fuer die fehlenden O11-Berichte ===")
    for m in lies(k18, "ir.module.module",
                  [("name", "in", ["account_reports", "accountant", "account_asset",
                                   "account_followup", "account_batch_payment",
                                   "account_sepa", "enterprise", "account_peppol"])],
                  ["name", "shortdesc", "state", "author", "license", "installed_version"],
                  order="name"):
        print("   %-24s %-14s %-22s %s" % (m["name"], m["state"], m["author"], m["license"]))

    print("\n=== 3) Valorisierung: Verwendung ===")
    print("   O11 Rechnungen mit Valorisierungstext: %s  (von %s)"
          % (z(k11, "account.invoice", [("valorisierung_id", "!=", False)]),
             z(k11, "account.invoice", [])))
    for t, n in [(v["name"], z(k11, "account.invoice", [("valorisierung_id", "=", v["id"])]))
                 for v in lies(k11, "itk_valorisierung.valorisierung", [], ["id", "name"], order="id")]:
        print("      %-45s %s" % (t[:45], n))
    print("   O18 Rechnungen mit Valorisierungstext: %s  (von %s)"
          % (z(k18, "account.move", [("valorisierung_id", "!=", False)]),
             z(k18, "account.move", [])))

    print("\n=== 4) Zahlungsbedingungen: Zeilen (Feld payment_id) ===")
    for name, k, felder in (("O11", k11, ["value", "days", "option"]),
                            ("O18", k18, ["value", "value_amount", "nb_days", "delay_type"])):
        print("-- %s --" % name)
        for t in lies(k, "account.payment.term", [], ["id", "name"], order="id"):
            zl = lies(k, "account.payment.term.line", [("payment_id", "=", t["id"])],
                      ["id"] + felder, order="id")
            print("   %-42s %s" % (t["name"][:42],
                                   "; ".join(str({f: l.get(f) for f in felder}) for l in zl) or "-"))

    print("\n=== 5) Kostenstellenbuchungen: Woher kommen die Buchungen? ===")
    print("   O11 gesamt: %s" % z(k11, "account.analytic.line", []))
    print("     mit Projekt:      %s" % z(k11, "account.analytic.line", [("project_id", "!=", False)]))
    print("     mit Aufgabe:      %s" % z(k11, "account.analytic.line", [("task_id", "!=", False)]))
    print("     mit Auftragszeile:%s" % z(k11, "account.analytic.line", [("so_line", "!=", False)]))
    print("     mit Stundenzettelrechnung: %s"
          % z(k11, "account.analytic.line", [("timesheet_invoice_id", "!=", False)]))
    print("     Kostenstellen-Tags genutzt: %s"
          % z(k11, "account.analytic.line", [("tag_ids", "!=", False)]))
    print("   O11 Kostenstellen-Tags (Stammdaten): %s" % z(k11, "account.analytic.tag", []))

    print("\n=== 6) Nachweis der Nutzung der PDF-Berichte (Anhaenge/Protokolle) ===")
    for modell in ("account.print.journal", "account.aged.trial.balance", "account.tax.report"):
        print("   O11 Anhaenge zu %-28s %s" % (modell, z(k11, "ir.attachment",
                                                       [("res_model", "=", modell)])))
        print("   O18 Anhaenge zu %-28s %s" % (modell, z(k18, "ir.attachment",
                                                       [("res_model", "=", modell)])))

    print("\n=== 7) Zahlungen: Felder O11 gegen O18 ===")
    for feld in ("invoice_ids", "reconciled_invoice_ids", "reconciled_bill_ids", "payment_difference",
                 "partner_type", "destination_account_id", "payment_method_id", "journal_id"):
        print("   %-26s O11: %-12s O18: %s"
              % (feld, z(k11, "account.payment", [(feld, "!=", False)]),
                 z(k18, "account.payment", [(feld, "!=", False)])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
