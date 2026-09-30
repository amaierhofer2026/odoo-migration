"""Read-only Detailpruefung Abrechnung: Feldnamen, Menueziele, fehlende Berichte.

Aufruf:  python scripts/analyse_abrechnung_details.py [--instanz lokal|vm]
Odoo 11 Prod wird ausschliesslich lesend verwendet.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18


def fget(k, modell, felder=None):
    try:
        d = k.kw(modell, "fields_get", [felder or [], ["string", "type", "relation"]],
                 context={"lang": "de_DE"})
        return d
    except Exception as fehler:
        return {"_fehler": str(fehler)[:80]}


def lies(k, modell, domain, felder, order=None):
    try:
        return k.kw(modell, "search_read", [domain, felder], order=order,
                    context={"lang": "de_DE"})
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

    print("=== 1) Valorisierung: Felder und Verwendung ===")
    print("O11 itk_valorisierung.valorisierung: %s" % sorted(fget(k11, "itk_valorisierung.valorisierung")))
    for m in lies(k11, "ir.model.fields",
                  [("name", "like", "valoris")], ["model", "name", "field_description", "modules"],
                  order="model,name"):
        print("   O11 Feld: %-34s %-24s %s" % (m["model"], m["name"], m["field_description"]))
    print("O18 itk_valorisierung.valorisierung: %s" % sorted(fget(k18, "itk_valorisierung.valorisierung")))
    for m in lies(k18, "ir.model.fields",
                  [("name", "like", "valoris")], ["model", "name", "field_description"],
                  order="model,name"):
        print("   O18 Feld: %-34s %-24s %s" % (m["model"], m["name"], m["field_description"]))
    for feld in ("valorisation_id", "valorisierung_id", "valorisation_text"):
        print("   O11 Rechnungszeilen mit %-18s: %s"
              % (feld, z(k11, "account.invoice.line", [(feld, "!=", False)])))
        print("   O18 Positionen mit %-19s: %s"
              % (feld, z(k18, "account.move.line", [(feld, "!=", False)])))

    print("\n=== 2) Zahlungsbedingungen: Zeilenfelder O11 ===")
    print("O11 account.payment.term.line Felder: %s" % sorted(fget(k11, "account.payment.term.line")))
    for t in lies(k11, "account.payment.term", [], ["id", "name"], order="id"):
        zl = lies(k11, "account.payment.term.line", [("payment_term_id", "=", t["id"])],
                  ["id", "value", "days", "option"], order="id")
        print("   %s (id %s): %s" % (t["name"], t["id"],
                                     ", ".join("value=%s days=%s option=%s" % (l["value"], l["days"], l["option"])
                                               for l in zl) or "-"))
    print("O18 account.payment.term.line Felder: %s" % sorted(fget(k18, "account.payment.term.line")))
    for t in lies(k18, "account.payment.term", [], ["id", "name"], order="id"):
        zl = lies(k18, "account.payment.term.line", [("payment_term_id", "=", t["id"])],
                  ["id", "value", "value_amount", "nb_days", "delay_type"], order="id")
        print("   %s (id %s): %s" % (t["name"], t["id"],
                                     ", ".join("value=%s amount=%s nb_days=%s delay=%s"
                                               % (l["value"], l["value_amount"], l["nb_days"], l["delay_type"])
                                               for l in zl) or "-"))

    print("\n=== 3) Kostenstellen-Buchungen: Felder und Menueziele ===")
    print("O11 account.analytic.line Felder: %s" % sorted(fget(k11, "account.analytic.line")))
    print("O18 account.analytic.line Felder: %s" % sorted(fget(k18, "account.analytic.line")))

    print("\n=== 4) Menues und Aktionen je Zielmodell (beide Systeme, alle Wurzeln) ===")
    for name, k in (("O11", k11), ("O18", k18)):
        print("-- %s --" % name)
        for modell in ("account.invoice", "account.move", "account.payment", "account.analytic.line",
                       "account.tax.report", "account.print.journal", "account.aged.trial.balance",
                       "account.analytic.tag", "account.invoice.report", "itk_valorisierung.valorisierung",
                       "account.cash.rounding", "account.fiscal.position", "account.bank.statement"):
            aktionen = lies(k, "ir.actions.act_window", [("res_model", "=", modell)],
                            ["id", "name", "view_mode"], order="id")
            menues = []
            for ak in aktionen:
                menues += [m["name"] for m in lies(k, "ir.ui.menu",
                                                   [("action", "=", "ir.actions.act_window,%s" % ak["id"])],
                                                   ["name"], order="id")]
            print("   %-34s Aktionen: %-2s Menues: %s"
                  % (modell, len(aktionen), sorted(set(menues))))

    print("\n=== 5) Wizards/Berichte: Modelle vorhanden? ===")
    for modell in ("account.tax.report", "account.print.journal", "account.aged.trial.balance",
                   "account.tax.report.line", "account.report", "account.financial.report",
                   "account.aged.partner.balance", "account.partner.ledger"):
        s11 = z(k11, modell, [])
        s18 = z(k18, modell, [])
        print("   %-30s O11: %-12s O18: %s" % (modell, s11, s18))

    print("\n=== 6) Herkunft der O11-Berichtsmodelle (ir.model.modules) ===")
    for modell in ("account.tax.report", "account.print.journal", "account.aged.trial.balance",
                   "account.invoice.report", "itk_valorisierung.valorisierung"):
        d = lies(k11, "ir.model", [("model", "=", modell)], ["model", "modules"])
        print("   %-34s modules=%s" % (modell, d[0]["modules"] if d else "-"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
