"""Verkauf: Stammdaten in Odoo 18 korrigieren (Session 121).

Entscheidung von Anna (24.09.2026): Die Zahlungsbedingung "14 Tage" muss fachlich 14 Tage ab
Rechnungsdatum bedeuten. In Odoo 18 war die Zeile mit nb_days = 0 (Zahlung sofort) angelegt.
"Sofortige Zahlung" und "30 Tage" bleiben unveraendert.

Idempotent: schreibt nur, wenn der Ist-Wert abweicht; liest danach zurueck.
Aufruf (lokal und VM, beide Instanzen muessen gleich sein):
    python scripts/apply_verkauf_stammdaten.py --instanz lokal
    python scripts/apply_verkauf_stammdaten.py --instanz vm
    python scripts/apply_verkauf_stammdaten.py --instanz vm --pruefen    (nur lesen)
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18

SP = {"lang": "de_DE"}

# Sollwerte je Zahlungsbedingung: Name -> Liste der Zeilen-Sollwerte
SOLL = {
    "14 Tage": [{"nb_days": 14, "value": "percent", "value_amount": 100.0,
                 "delay_type": "days_after"}],
    # nur Kontrolle, es wird nichts geschrieben:
    "Sofortige Zahlung": [{"nb_days": 0, "value": "percent", "value_amount": 100.0,
                           "delay_type": "days_after"}],
    "30 Tage": [{"nb_days": 30, "value": "percent", "value_amount": 100.0,
                 "delay_type": "days_after"}],
}
SCHREIBEN = {"14 Tage"}


def zeilen(k, term_id):
    return k.kw("account.payment.term.line", "search_read",
                [[["payment_id", "=", term_id]], ["value", "value_amount", "nb_days", "delay_type"]],
                context=SP)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--pruefen", action="store_true")
    a = p.parse_args()

    k = o18(a.instanz)
    print("Instanz: %s" % a.instanz)
    ok = fehler = 0
    for name, soll in SOLL.items():
        termine = k.kw("account.payment.term", "search_read", [[["name", "=", name]], ["id", "name"]],
                       context=SP)
        if not termine:
            print("  FEHL Zahlungsbedingung '%s' nicht gefunden" % name)
            fehler += 1
            continue
        tid = termine[0]["id"]
        ist = zeilen(k, tid)
        soll_zeile = soll[0]
        abweichung = []
        for feld in ("nb_days", "value", "value_amount", "delay_type"):
            ist_wert, soll_wert = ist[0][feld], soll_zeile[feld]
            if isinstance(soll_wert, float):
                gleich = abs(float(ist_wert) - soll_wert) < 1e-6
            else:
                gleich = ist_wert == soll_wert
            if not gleich:
                abweichung.append("%s: %s statt %s" % (feld, ist_wert, soll_wert))
        if not abweichung:
            print("  OK   %-20s (id %s) unveraendert: nb_days=%s, %s, %s"
                  % (name, tid, ist[0]["nb_days"], ist[0]["value"], ist[0]["delay_type"]))
            ok += 1
            continue
        if name not in SCHREIBEN:
            print("  FEHL %-20s (id %s) weicht ab (%s), darf aber nicht geaendert werden"
                  % (name, tid, abweichung))
            fehler += 1
            continue
        print("  ->   %-20s (id %s) korrigieren: %s" % (name, tid, abweichung))
        if a.pruefen:
            fehler += 1
            print("       (Pruefmodus: nicht geschrieben)")
            continue
        k.kw("account.payment.term.line", "write", [[ist[0]["id"]], {"nb_days": soll_zeile["nb_days"]}],
             context=SP)
        nachher = zeilen(k, tid)
        if nachher[0]["nb_days"] == soll_zeile["nb_days"]:
            print("  OK   %-20s gesetzt: nb_days=%s (vorher %s)"
                  % (name, nachher[0]["nb_days"], ist[0]["nb_days"]))
            ok += 1
        else:
            print("  FEHL %-20s konnte nicht gesetzt werden (Ist %s)"
                  % (name, nachher[0]["nb_days"]))
            fehler += 1

    print("\nErgebnis: %d OK / %d FEHL%s" % (ok, fehler, " (Pruefmodus)" if a.pruefen else ""))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
