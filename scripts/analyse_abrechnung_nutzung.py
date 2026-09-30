"""Read-only Nutzungszahlen Abrechnung: Odoo 11 Prod gegen Odoo 18 (lokal/VM).

Aufruf:  python scripts/analyse_abrechnung_nutzung.py [--instanz lokal|vm]
Odoo 11 Prod wird ausschliesslich lesend verwendet (nur search_count/read/read_group).

Domain-Form: durchgaengig FLACH (Liste von Tupeln) - args = [domain, felder].
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18


def z(k, modell, domain):
    """search_count mit flacher Domain."""
    try:
        return k.kw(modell, "search_count", [domain])
    except Exception as fehler:
        return "FEHLER(%s)" % str(fehler)[:40].replace("\n", " ")


def lies(k, modell, domain, felder, order=None):
    try:
        return k.kw(modell, "search_read", [domain, felder], order=order,
                    context={"lang": "de_DE"})
    except Exception as fehler:
        print("      (Lesefehler %s: %s)" % (modell, str(fehler)[:60].replace("\n", " ")))
        return []


def verteilung(k, modell, feld, werte):
    return [(w, z(k, modell, [(feld, "=", w)])) for w in werte]


def zeige(titel):
    print("\n---- %s ----" % titel)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    a = p.parse_args()
    lade_env()
    k11 = o11()
    k18 = o18(a.instanz)

    # ================= ODOO 11 =================
    zeige("O11: Rechnungen account.invoice nach Typ")
    for t, n in verteilung(k11, "account.invoice", "type",
                           ["out_invoice", "in_invoice", "out_refund", "in_refund"]):
        print("  %-12s %s" % (t, n))
    zeige("O11: Rechnungen nach Zustand / Zahlungsstatus")
    for t, n in verteilung(k11, "account.invoice", "state",
                           ["draft", "open", "in_payment", "paid", "cancel"]):
        print("  state %-12s %s" % (t, n))
    for t, n in verteilung(k11, "account.invoice", "payment_state",
                           ["not_paid", "partial", "paid", "in_payment"]):
        print("  payment_state %-12s %s" % (t, n))
    print("  Restbetrag > 0:            %s" % z(k11, "account.invoice", [("residual", ">", 0)]))
    print("  mit Steuerposition:        %s"
          % z(k11, "account.invoice", [("fiscal_position_id", "!=", False)]))
    print("  Zeilen mit Kostenstelle:   %s"
          % z(k11, "account.invoice.line", [("account_analytic_id", "!=", False)]))
    print("  Zeilen mit Vorlage(itk_valorisierung-Feldname?): siehe Modulpruefung")
    r = lies(k11, "account.invoice", [("date_invoice", "!=", False)], ["date_invoice"],
             order="date_invoice asc")
    if r:
        print("  aelteste Rechnung:         %s" % r[0]["date_invoice"])
    r = lies(k11, "account.invoice", [("date_invoice", "!=", False)], ["date_invoice"],
             order="date_invoice desc")
    if r:
        print("  juengste Rechnung:         %s" % r[0]["date_invoice"])

    zeige("O11: Zahlungen account.payment")
    for t, n in verteilung(k11, "account.payment", "payment_type", ["inbound", "outbound"]):
        print("  %-10s %s" % (t, n))
    for t, n in verteilung(k11, "account.payment", "state",
                           ["draft", "posted", "sent", "reconciled", "cancelled"]):
        print("  %-12s %s" % (t, n))
    print("  mit Rechnungsbezug:  %s"
          % z(k11, "account.payment", [("reconciled_invoice_ids", "!=", False)]))
    r = lies(k11, "account.payment", [("payment_date", "!=", False)], ["payment_date"],
             order="payment_date asc")
    if r:
        print("  aelteste Zahlung:    %s" % r[0]["payment_date"])

    zeige("O11: Journale (account.journal)")
    for j in lies(k11, "account.journal", [], ["id", "name", "code", "type", "active"], order="type,code"):
        print("  id=%-3s %-10s %-30s %-10s aktiv=%s"
              % (j["id"], j["code"], j["name"][:30], j["type"], j["active"]))

    zeige("O11: Buchungen account.move je Journal (Grundgesamtheit %s)"
          % z(k11, "account.move", []))
    for j in lies(k11, "account.journal", [], ["id", "code", "type", "name"], order="type,code"):
        print("  %-10s %-10s %-30s %s" % (j["code"], j["type"], j["name"][:30],
                                         z(k11, "account.move", [("journal_id", "=", j["id"])])))
    for t, n in verteilung(k11, "account.move", "state", ["draft", "posted", "cancel"]):
        print("  state %-10s %s" % (t, n))

    zeige("O11: Kostenrechnung / Analytik")
    print("  Buchungen gesamt:         %s" % z(k11, "account.analytic.line", []))
    for j in lies(k11, "account.analytic.journal", [], ["id", "name", "code", "type"], order="code"):
        print("  Journal %-4s %-24s %-8s %s" % (j["id"], j["name"][:24], j["type"],
                                               z(k11, "account.analytic.line",
                                                 [("journal_id", "=", j["id"])])))
    print("  Kostenstellen (account.analytic.account), gesamt %s:"
          % z(k11, "account.analytic.account", []))
    for aa in lies(k11, "account.analytic.account", [], ["id", "name", "code", "account_type"],
                   order="code"):
        print("     id=%-3s %-16s %-22s %s" % (aa["id"], aa.get("code") or "-",
                                              aa.get("account_type") or "-", aa["name"][:50]))

    zeige("O11: Steuern")
    print("  gesamt %s | aktiv %s" % (z(k11, "account.tax", []),
                                      z(k11, "account.tax", [("active", "=", True)])))
    for w, n in verteilung(k11, "account.tax", "type_tax_use", ["sale", "purchase", "none"]):
        print("  %-10s %s" % (w, n))
    print("  Positionen mit Steuer: %s"
          % z(k11, "account.invoice.line", [("invoice_line_tax_ids", "!=", False)]))

    zeige("O11: Valorisierungstexte (itk_valorisierung)")
    for v in lies(k11, "itk_valorisierung.valorisierung", [], ["id", "name"], order="id"):
        print("  id=%-3s %s" % (v["id"], v["name"][:70]))

    zeige("O11: Zahlungsbedingungen")
    for t in lies(k11, "account.payment.term", [], ["id", "name", "active"], order="id"):
        print("  id=%-3s aktiv=%-6s %s" % (t["id"], t["active"], t["name"]))
        for ln in lies(k11, "account.payment.term.line", [("payment_term_id", "=", t["id"])],
                       ["id", "value", "days", "option"], order="id"):
            print("       Zeile value=%s days=%s option=%s"
                  % (ln["value"], ln["days"], ln["option"]))

    zeige("O11: Waehrungen und Preise")
    print("  Waehrungen: %s" % [(c["id"], c["name"], c["active"])
                               for c in lies(k11, "res.currency", [], ["id", "name", "active"])])

    # ================= ODOO 18 =================
    K = "O18(%s)" % a.instanz
    zeige("%s: Rechnungen account.move nach move_type" % K)
    for t, n in verteilung(k18, "account.move", "move_type",
                           ["entry", "out_invoice", "out_refund", "in_invoice", "in_refund",
                            "out_receipt", "in_receipt"]):
        print("  %-12s %s" % (t, n))
    for t, n in verteilung(k18, "account.move", "state", ["draft", "posted", "cancel"]):
        print("  state %-10s %s" % (t, n))
    print("  mit Steuerposition:        %s"
          % z(k18, "account.move", [("fiscal_position_id", "!=", False)]))
    print("  Zeilen mit Kostenstelle:   %s"
          % z(k18, "account.move.line", [("analytic_distribution", "!=", False)]))

    zeige("%s: Zahlungen account.payment" % K)
    for t, n in verteilung(k18, "account.payment", "payment_type", ["inbound", "outbound"]):
        print("  %-10s %s" % (t, n))
    for t, n in verteilung(k18, "account.payment", "state",
                           ["draft", "in_process", "paid", "canceled", "rejected"]):
        print("  %-12s %s" % (t, n))

    zeige("%s: Journale" % K)
    for j in lies(k18, "account.journal", [], ["id", "name", "code", "type", "active"], order="type,code"):
        print("  id=%-3s %-10s %-30s %-10s aktiv=%s"
              % (j["id"], j["code"], j["name"][:30], j["type"], j["active"]))

    zeige("%s: Kostenrechnung" % K)
    print("  Plaene: %s" % [p["name"] for p in lies(k18, "account.analytic.plan", [], ["name"])])
    for aa in lies(k18, "account.analytic.account", [], ["id", "name", "code", "plan_id"], order="code"):
        print("  id=%-3s %-16s %-30s plan=%s" % (aa["id"], aa.get("code") or "-",
                                                 aa["name"][:30], aa.get("plan_id")))
    print("  Buchungen: %s" % z(k18, "account.analytic.line", []))

    zeige("%s: Steuern, Zahlungsbedingungen, Waehrungen, Valorisierung" % K)
    print("  Steuern gesamt %s | aktiv %s" % (z(k18, "account.tax", []),
                                              z(k18, "account.tax", [("active", "=", True)])))
    for w, n in verteilung(k18, "account.tax", "type_tax_use", ["sale", "purchase", "none"]):
        print("  %-10s %s" % (w, n))
    for t in lies(k18, "account.payment.term", [], ["id", "name", "active"], order="id"):
        print("  Zahlungsbedingung id=%-3s aktiv=%-6s %s" % (t["id"], t["active"], t["name"]))
    print("  Waehrungen: %s" % [(c["id"], c["name"], c["active"])
                               for c in lies(k18, "res.currency", [], ["id", "name", "active"])])
    print("  Valorisierungen: %s" % [(v["id"], v["name"][:60])
                                     for v in lies(k18, "itk_valorisierung.valorisierung", [],
                                                   ["id", "name"])])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
