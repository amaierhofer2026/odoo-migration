"""Prueflauf Verkauf Teil 3, Schritt 3: Statuswerte und Statusuebergaenge.

Prueft in Odoo 11 (nur lesend), Odoo 18 lokal und Odoo 18 VM:
  - Auswahlwerte des Feldes state
  - Statusleiste (statusbar_visible)
  - Zustand ohne Datensaetze, Zustand done nur in Odoo 11, locked nur in Odoo 18
  - Buttons je Zustand (Sichtbarkeit aus dem Arch ausgewertet)
  - die dokumentierten Uebergaenge (draft->sale, draft->cancel, sale->cancel, cancel->draft,
    sale sperren/entsperren, sent->sale)

Aufruf:
    python scripts/verify_s121_verkauf_teil3_status.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18
from analyse_verkauf_teil3_formulare import formular_arch
from analyse_verkauf_teil3_status import button_eintraege
from sichtbarkeit_bedingungen import sichtbar, sichtbar_mit_werten

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}

ERWARTUNG = {
    "o11": {
        "auswahl": ["draft", "sent", "sale", "done", "cancel"],
        "statusleiste": "draft,sent,sale",
        "hat_locked": False,
        "hat_done": True,
        "uebergaenge": [
            ("draft", "action_confirm", True), ("draft", "action_cancel", True),
            ("draft", "action_draft", False), ("sent", "action_confirm", True),
            ("sent", "action_cancel", True), ("sale", "action_cancel", True),
            ("sale", "action_done", True), ("sale", "action_unlock", False),
            ("done", "action_unlock", True), ("done", "action_cancel", False),
            ("cancel", "action_draft", True), ("cancel", "action_confirm", False),
        ],
    },
    "o18": {
        "auswahl": ["draft", "sent", "sale", "cancel"],
        "statusleiste": "draft,sent,sale",
        "hat_locked": True,
        "hat_done": False,
        "uebergaenge": [
            ("draft", "action_confirm", True), ("draft", "action_cancel", True),
            ("draft", "action_draft", False), ("draft", "action_lock", False),
            ("sent", "action_confirm", True), ("sent", "action_cancel", True),
            ("sale", "action_cancel", True), ("sale", "action_lock", True),
            ("sale", "action_unlock", False), ("sale", "action_draft", False),
            ("cancel", "action_draft", True), ("cancel", "action_confirm", False),
            ("cancel", "action_cancel", False),
        ],
    },
}
WERTE = ["name", "state", "locked", "invoice_status", "invoice_count", "picking_ids",
         "authorized_transaction_ids", "id"]


def main() -> int:
    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    print("Prueflauf Verkauf Teil 3, Schritt 3 (Statuswechsel)")
    print("Odoo 11 Prod wird ausschliesslich lesend gelesen.\n")

    for schluessel, client, ist18, name in (("o11", o11(), False, "Odoo 11 Prod"),
                                            ("o18", o18("lokal"), True, "Odoo 18 lokal"),
                                            ("vm", o18("vm"), True, "Odoo 18 VM")):
        erwartet = ERWARTUNG["o11" if not ist18 else "o18"]
        print("--- %s ---" % name)
        felder = client.kw("sale.order", "fields_get", [[], ["type"]], context=SP)
        fg = client.kw("sale.order", "fields_get", [["state"], ["selection"]], context=SP)
        auswahl = [s[0] for s in fg["state"]["selection"]]
        pruefe(auswahl == erwartet["auswahl"], "Zustandswerte %s" % auswahl)
        pruefe(("locked" in felder) == erwartet["hat_locked"],
               "Feld locked vorhanden: %s" % ("locked" in felder))
        pruefe(("done" in auswahl) == erwartet["hat_done"], "Zustand done vorhanden: %s" % ("done" in auswahl))
        arch = formular_arch(client, "sale.order", ist18)
        import re
        treffer = re.search(r'statusbar_visible="([^"]+)"', arch)
        leiste = treffer.group(1) if treffer else "-"
        pruefe(leiste == erwartet["statusleiste"], "Statusleiste %s" % leiste)
        zaehlung = {g["state"]: g["state_count"]
                    for g in client.kw("sale.order", "read_group", [[], ["state"], ["state"]], context=SP)}
        gesamt = client.kw("sale.order", "search_count", [[]], context=SP)
        pruefe(sum(zaehlung.values()) == gesamt,
               "Summe der Zustaende %d = Anzahl Auftraege %d" % (sum(zaehlung.values()), gesamt))
        vorhanden = [f for f in WERTE if f in felder]
        kandidat = client.kw("sale.order", "search_read", [[("state", "=", "draft")], vorhanden], context=SP)
        kandidat = kandidat or client.kw("sale.order", "search_read", [[], vorhanden], context=SP)[:1]
        werte_basis = kandidat[0] if kandidat else {}
        knoepfe = button_eintraege(arch, ist18)
        for zustand, methode, erwartetete_sichtbarkeit in erwartet["uebergaenge"]:
            treffer_knoepfe = [b for b in knoepfe if b["name"] == methode]
            sichtbar_liste = []
            for b in treffer_knoepfe:
                ergebnis = sichtbar(b["bedingung"], zustand)
                if ergebnis is True:
                    sichtbar_liste.append(True)
                elif isinstance(ergebnis, str):
                    mit = sichtbar_mit_werten(b["bedingung"], zustand, dict(werte_basis, state=zustand))
                    sichtbar_liste.append(mit is True)
            ist = any(sichtbar_liste)
            pruefe(ist == erwartetete_sichtbarkeit,
                   "Zustand %-7s: %s %s" % (zustand, methode,
                                           "sichtbar" if erwartetete_sichtbarkeit else "nicht sichtbar"))
        print()

    print("Odoo 11 Prod wurde ausschliesslich lesend verwendet.")
    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
