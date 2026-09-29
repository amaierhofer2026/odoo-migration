"""Verkauf: Stammdaten in Odoo 18 korrigieren (Session 121).

Entscheidung von Anna (24.09.2026): Die Zahlungsbedingung "14 Tage" muss fachlich 14 Tage ab
Rechnungsdatum bedeuten. In Odoo 18 war die Zeile mit nb_days = 0 (Zahlung sofort) angelegt.
"Sofortige Zahlung" und "30 Tage" bleiben unveraendert.

Ergaenzung (29.09.2026, Teil 5 Block 2/Stammdaten): Die in Odoo 11 verwendete Zahlungsbedingung
"30 Tage netto" (Odoo 11: eine Zeile "balance", 30 Tage, Option day_after_invoice_date,
Firmenbezug) fehlte in Odoo 18. Sie wird hier bei Bedarf angelegt; bestehende Zahlungsbedingungen
bleiben unveraendert, bestehende Auftraege und Kunden werden nicht beruehrt.

Idempotent: legt nur an, was fehlt; schreibt nur, wenn der Ist-Wert abweicht; liest danach zurueck.
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
    # Odoo-11-Bezeichnung; wird bei Bedarf angelegt (siehe ANLEGEN)
    # Odoo 18 kennt die Odoo-11-Auswahl "balance" nicht mehr; fachlich entspricht ihr
    # eine Zeile mit percent 100 %.
    "30 Tage netto": [{"nb_days": 30, "value": "percent", "value_amount": 100.0,
                       "delay_type": "days_after"}],
}
SCHREIBEN = {"14 Tage"}

# Zahlungsbedingungen, die in Odoo 18 fehlen, aber in Odoo 11 verwendet wurden (29.09.2026)
# Gegenstueck zur Odoo-11-Konfiguration: eine Zeile (in Odoo 11 "balance"/0 %, in Odoo 18
# entspricht das "percent"/100 %), 30 Tage ab Rechnungsdatum. Odoo 18 fuehrt die Felder als
# nb_days (statt days) und delay_type (statt option = day_after_invoice_date); die Bedingung
# bleibt ohne Firmenbezug, wie alle uebrigen Zahlungsbedingungen in Odoo 18.
ANLEGEN = {
    "30 Tage netto": {
        "note": "Zahlungsbedingungen: 30 Tage netto",
        "zeilen": [{"value": "percent", "value_amount": 100.0, "nb_days": 30,
                    "delay_type": "days_after"}],
    },
}


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

    # Fehlende Zahlungsbedingungen anlegen (Odoo-11-Bezeichnungen)
    for name, daten in ANLEGEN.items():
        vorhanden = k.kw("account.payment.term", "search_read", [[["name", "=", name]], ["id"]],
                         context=SP)
        if vorhanden:
            print("  OK   Zahlungsbedingung '%s' bereits vorhanden (id %s)"
                  % (name, vorhanden[0]["id"]))
            ok += 1
            continue
        if a.pruefen:
            print("  FEHL Zahlungsbedingung '%s' fehlt (Pruefmodus: nicht angelegt)" % name)
            fehler += 1
            continue
        new_id = k.kw("account.payment.term", "create", [{
            "name": name,
            "note": daten["note"],
            "line_ids": [(0, 0, dict(z)) for z in daten["zeilen"]],
        }], context=SP)
        neu = k.kw("account.payment.term", "read", [[new_id], ["name", "note", "active"]],
                   context=SP)[0]
        neu_zeilen = zeilen(k, new_id)
        stimmt = (neu["name"] == name and neu["active"]
                  and len(neu_zeilen) == len(daten["zeilen"]))
        print("  %s   '%s' angelegt (id %s): Zeilen %s, Hinweis '%s'"
              % ("OK " if stimmt else "FEHL", name, new_id,
                 [(z["value"], z["value_amount"], z["nb_days"], z["delay_type"]) for z in neu_zeilen],
                 neu["note"]))
        ok += 1 if stimmt else 0
        fehler += 0 if stimmt else 1

    for name, soll in SOLL.items():
        termine = k.kw("account.payment.term", "search_read", [[["name", "=", name]], ["id", "name"]],
                       context=SP)
        if not termine:
            if name in ANLEGEN:
                continue          # wurde oben bereits gemeldet (Pruefmodus: fehlt)
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
