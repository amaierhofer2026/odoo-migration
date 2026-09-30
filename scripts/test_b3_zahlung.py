"""B3 Zahlung: Funktionstest des Odoo-18-Zahlungswegs (Assistent account.payment.register).

Aufruf:
  python scripts/test_b3_zahlung.py --instanz lokal                 # nur Vorbelegung lesen
  python scripts/test_b3_zahlung.py --instanz lokal --ausfuehren    # Zahlung wirklich anlegen

Der Test verwendet die gebuchte, offene Testrechnung (Standard: RE/2026/0001, id 1).
Er legt Testdaten in der Testdatenbank an (Zahlung), keine Produktivdaten, keine Migration.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o18

FELDER = ["journal_id", "payment_method_line_id", "amount", "communication", "payment_date",
          "payment_difference", "payment_difference_handling", "currency_id", "partner_id",
          "partner_type", "payment_type", "group_payment", "available_payment_method_line_ids",
          "show_payment_difference", "can_edit_wizard", "hide_writeoff_section",
          "available_journal_ids", "source_amount", "source_amount_currency", "writeoff_label"]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--ausfuehren", action="store_true")
    p.add_argument("--rechnung", type=int, default=0)
    a = p.parse_args()
    lade_env()
    k = o18(a.instanz)

    if a.rechnung:
        rid = a.rechnung
    else:
        treffer = k.kw("account.move", "search_read",
                       [[("move_type", "=", "out_invoice"), ("state", "=", "posted"),
                         ("payment_state", "!=", "paid")], ["id", "name"]], order="id", limit=1)
        if not treffer:
            print("Keine gebuchte offene Ausgangsrechnung gefunden.")
            return 1
        rid = treffer[0]["id"]
        print("Testrechnung: id %s %s" % (rid, treffer[0]["name"]))

    vorher = k.kw("account.move", "read", [[rid], ["name", "state", "payment_state", "amount_total",
                                                   "amount_residual"]])[0]
    print("Vorher: %s" % vorher)
    zaehler_vorher = {"account.payment": k.kw("account.payment", "search_count", [[]]),
                      "account.partial.reconcile": k.kw("account.partial.reconcile", "search_count", [[]])}

    ctx = {"active_model": "account.move", "active_ids": [rid], "active_id": rid,
           "lang": "de_DE", "tz": "Europe/Vienna"}
    kid = k.kw("account.payment.register", "create", [[{}]], context=ctx)
    kid = kid[0] if isinstance(kid, list) else kid
    werte = k.kw("account.payment.register", "read", [[kid], FELDER], context=ctx)[0]
    print("\nAssistent (id %s) Vorbelegung:" % kid)
    for feld in FELDER:
        print("   %-36s %s" % (feld, werte.get(feld)))
    if not a.ausfuehren:
        k.kw("account.payment.register", "unlink", [[kid]])
        print("\n(Assistent verworfen, nichts angelegt - --ausfuehren nicht gesetzt)")
        return 0

    print("\nZahlung anlegen ...")
    ergebnis = k.kw("account.payment.register", "action_create_payments", [[kid]], context=ctx)
    print("   Rueckgabe: %s" % ergebnis)
    nachher = k.kw("account.move", "read", [[rid], ["name", "state", "payment_state",
                                                    "amount_residual"]])[0]
    print("Nachher Rechnung: %s" % nachher)
    zaehler_nachher = {"account.payment": k.kw("account.payment", "search_count", [[]]),
                       "account.partial.reconcile": k.kw("account.partial.reconcile", "search_count", [[]])}
    print("Zaehler vorher/nachher: %s / %s" % (zaehler_vorher, zaehler_nachher))
    for z in k.kw("account.payment", "search_read", [[("reconciled_invoice_ids", "in", [rid])],
                  ["id", "name", "amount", "memo", "date", "state", "journal_id",
                   "payment_method_line_id", "partner_type", "payment_type", "payment_reference"]],
                  order="id desc", limit=3, context={"lang": "de_DE"}):
        print("   Zahlung: %s" % z)
    for m in k.kw("account.move.line", "search_read",
                  [[("move_id.move_type", "=", "entry"), ("partner_id", "=", vorher.get("partner_id"))],
                   ["id", "move_id", "account_id", "debit", "credit", "amount_residual"]],
                  order="id desc", limit=4, context={"lang": "de_DE"}):
        print("   Buchungszeile: %s" % m)
    for pr in k.kw("account.partial.reconcile", "search_read", [[], ["id", "debit_move_id",
                  "credit_move_id", "amount", "debit_amount_currency"]], order="id desc", limit=3):
        print("   Abstimmung: %s" % pr)
    ok = (nachher["payment_state"] == "paid" and abs(nachher["amount_residual"]) < 0.001
          and zaehler_nachher["account.payment"] == zaehler_vorher["account.payment"] + 1)
    print("\nERGEBNIS: %s" % ("OK - Rechnung ausgeglichen, Zahlung gebucht" if ok else "FEHL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
