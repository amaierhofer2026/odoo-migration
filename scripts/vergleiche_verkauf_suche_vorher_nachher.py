"""Vorher/Nachher-Vergleich der Suchansichten (Filter, Gruppierungen, Suchfelder).

Vergleicht den Stand vor der Ergaenzung (docs/_verkauf_teil3_suche_vorher.json) mit dem aktuellen
Stand (docs/_verkauf_teil3_suche.json): jeder vorher vorhandene Filter, jede Gruppierung und jedes
Suchfeld muss weiterhin vorhanden sein; Ergaenzungen werden ausgewiesen.

Aufruf:
    python scripts/vergleiche_verkauf_suche_vorher_nachher.py
"""
from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VORHER = os.path.join(REPO, "docs", "_verkauf_teil3_suche_vorher.json")
NACHHER = os.path.join(REPO, "docs", "_verkauf_teil3_suche.json")


def menge(daten: dict, schluessel: str) -> dict:
    """Je Aktion: Filter, Gruppierungen und Suchfelder als Mengen."""
    ergebnis = {}
    for a in daten[schluessel]["aktionen"]:
        if not a["menues"]:
            continue
        ergebnis[a["id"]] = {
            "name": a["name"],
            "filter": {(f["name"] or f["string"], f["string"]) for f in a["filter"]},
            "gruppen": {(g["context"] or "") for g in a["gruppen"]},
            "felder": {f["name"] for f in a["felder"]},
            "kontext": a["context"],
        }
    return ergebnis


def main() -> int:
    if not os.path.exists(VORHER):
        print("Vorher-Datei fehlt: %s" % VORHER)
        return 2
    dateien = (json.load(open(VORHER, encoding="utf-8")), json.load(open(NACHHER, encoding="utf-8")))
    fehlend = 0
    for schluessel, bezeichnung in (("o18", "Odoo 18 lokal"), ("vm", "Odoo 18 VM")):
        vorher = menge(dateien[0], schluessel)
        nachher = menge(dateien[1], schluessel)
        print("=== %s: Vorher/Nachher-Vergleich der Suchansichten (je Menueaktion) ===\n" % bezeichnung)
        for aktion_id, alt in sorted(vorher.items()):
            neu = nachher.get(aktion_id)
            print("Aktion %s '%s'" % (aktion_id, alt["name"]))
            if not neu:
                print("   FEHLT NACHHER COMPLETELY")
                fehlend += 1
                continue
            for art in ("filter", "gruppen", "felder"):
                weg = alt[art] - neu[art]
                dazu = neu[art] - alt[art]
                if weg:
                    fehlend += len(weg)
                    print("   ENTFERNT (%s): %s" % (art, sorted(weg)))
                if dazu:
                    print("   ergaenzt (%s): %s" % (art, sorted(str(x) for x in dazu)))
                if not weg and not dazu:
                    print("   %s unveraendert (%d)" % (art, len(neu[art])))
            if alt["kontext"] != neu["kontext"]:
                print("   Kontext geaendert: %s -> %s" % (alt["kontext"], neu["kontext"]))
            print()
    if fehlend:
        print("ERGEBNIS: %d Entfernung(en) gefunden - das darf nicht passieren." % fehlend)
    else:
        print("ERGEBNIS: keine Odoo-18-Funktion entfernt, nur Ergaenzungen.")
    return 1 if fehlend else 0


if __name__ == "__main__":
    raise SystemExit(main())
