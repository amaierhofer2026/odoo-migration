"""Abonnement: sichtbare Beschriftungen auf den Odoo-11-Wortlaut setzen (Uebersetzungen).

Aendert gezielt einzelne msgstr-Zeilen in den ITK-Uebersetzungsdateien und kompiliert die .mo.

Aufruf: python scripts/abo_labels_setzen.py [--pruefen]
"""
import argparse
import io
import os
import re
import sys

import polib

REPO = r"C:/Odoo-Test"
DATEIEN = [
    os.path.join(REPO, "addons/itk_subscription/i18n/de.po"),
    os.path.join(REPO, "addons/itk_translation/i18n/de_itk_subscription.po"),
]

# msgid -> Odoo-11-Wortlaut (sichtbar)
ZUORDNUNG = {
    "Cancel Subscription": "Aboauftrag abbrechen",
    "Close Subscription": "Aboauftrag schließen",
    "Contract Ending on": "Vertragsende am",
    "Generate Invoice manually": "Generate Invoice manually",
    "Total": "Gesamtbetrag",
}


def bearbeite(pfad, pruefen):
    if not os.path.exists(pfad):
        print("  fehlt: %s" % pfad)
        return 0, 0
    po = polib.pofile(pfad)
    geaendert = 0
    for eintrag in po:
        ziel = ZUORDNUNG.get(eintrag.msgid)
        if ziel is None or eintrag.msgstr == ziel:
            continue
        if "field_sale_subscription__recurring_amount_total" in eintrag.comment and eintrag.msgid == "Total":
            pass  # genau dieser Feldeintrag ist gemeint
        print("  %s: %r -> %r" % (os.path.basename(pfad), eintrag.msgstr, ziel))
        eintrag.msgstr = ziel
        geaendert += 1
    if geaendert and not pruefen:
        po.save(pfad)
        po.save_as_mofile(pfad[:-3] + ".mo")
        print("  gespeichert: %s + .mo" % os.path.basename(pfad))
    return geaendert, 1


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--pruefen", action="store_true")
    args = a.parse_args()
    gesamt = 0
    for pfad in DATEIEN:
        anzahl, vorhanden = bearbeite(pfad, args.pruefen)
        gesamt += anzahl
    print("\nErgebnis: %d Aenderungen%s" % (gesamt, " (Pruefmodus)" if args.pruefen else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
