"""Korrigiert fehlerhaft dargestellte Sonderzeichen in den Steuerbezeichnungen (Odoo 18).

Befund 08.10.2026 (Auftrag Anna): In Abrechnung > Konfiguration > Finanzen > Steuern zeigen die
Beschreibungen statt "§" die Zeichenfolge "T°" (Datenbank: U+252C U+00BA, das ist der UTF-8-Code
des Paragrafzeichens C2 A7, faelschlich als CP437/CP850 gelesen). Herkunft: der Kontenrahmen-Import
aus l10n_at; die Quelldatei selbst ist korrekt UTF-8
(`l10n_at/data/template/account.tax-at.csv`, dort steht C2 A7 = "§").

Dieses Werkzeug korrigiert ausschliesslich die Felder `name` und `description` der Steuern und
laesst Steuerlogik, Konten, Saetze, Gruppen, Sequenzen und Verknuepfungen unveraendert. Es schreibt
beide Sprachen (en_US = Quelle, de_DE = Uebersetzung) und ist wiederholbar.

Aufruf:
    python scripts/korrigiere_steuerbeschreibungen.py --instanz lokal|vm [--pruefen]
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o18  # noqa: E402

ZIEL_DB = "odoo18_test"

# Bekannte Fehldarstellungen in den Steuerbeschreibungen und ihre Reparatur.
# 1. Paragrafzeichen (UTF-8 C2 A7), in der Oberflaeche als "T°" sichtbar.
FEHLER = {
    "\u252c\u00ba": "\u00a7",   # C2 A7 als CP437/CP850 gelesen (Befund, "T°" in der Oberflaeche)
    "\u00c2\u00a7": "\u00a7",   # C2 A7 als Latin-1 gelesen ("Â§")
    "\u00c3\u00a7": "\u00a7",   # C2 A7 doppelt kodiert
}
# NICHT korrigiert wird die Schreibweise "&gt;=" in zwei Beschreibungen: das Feld
# account.tax.description ist in Odoo 18 ein HTML-Feld (type=html, sanitize=True). Der Sanitizer
# speichert ">" als "&gt;" und zeigt es in HTML-Kontexten korrekt als ">" an - das ist der
# korrekte Speicherzustand, kein Darstellungsfehler. Ein Schreibversuch mit ">" wird vom
# Sanitizer sofort wieder in "&gt;" gewandelt (am 08.10.2026 geprueft, Ergebnis unveraendert).
# Alle uebersetzbaren Textfelder der Steuer (geprueft am 08.10.2026: name, description,
# invoice_label = "Bezeichnung auf Rechnungen").
FELDER = ("name", "description", "invoice_label")
SPRACHEN = (("en_US", "Quelle (englisch)"), ("de_DE", "Uebersetzung (deutsch)"))


def korrigiere(k, pruefen):
    gesamt = {"geprueft": 0, "geaendert": 0, "felder": 0, "vorkommen": 0}
    # Auch archivierte Steuern (active = False) beruecksichtigen: sie sind in der Liste sichtbar
    # (Befund 08.10.2026: die archivierte Steuer id 6 "0% Ust L 1e" trug den Fehler noch).
    ids = k.kw("account.tax", "search", [[("active", "in", [True, False])]], context={"lang": "de_DE"})
    for sprache, bezeichnung in SPRACHEN:
        ctx = {"lang": sprache}
        daten = k.kw("account.tax", "read", [ids, list(FELDER)], context=ctx)
        for t in daten:
            gesamt["geprueft"] += 1
            neu = {}
            anzahl = 0
            for feld in FELDER:
                alt = t.get(feld) or ""
                wert = alt
                for falsch, richtig in FEHLER.items():
                    if falsch in wert:
                        anzahl += wert.count(falsch)
                        wert = wert.replace(falsch, richtig)
                if wert != alt:
                    neu[feld] = wert
            if not neu:
                continue
            gesamt["geaendert"] += 1
            gesamt["felder"] += len(neu)
            gesamt["vorkommen"] += anzahl
            print("  %-8s id=%-4s %-14s %d Stelle(n)" % (sprache, t["id"], t["name"][:14], anzahl))
            for feld, wert in neu.items():
                alt = t.get(feld) or ""
                print("      %-11s vorher: %r" % (feld, alt[:110]))
                print("      %-11s nachher: %r" % ("", wert[:110]))
            if not pruefen:
                k.kw("account.tax", "write", [[t["id"]], neu], context=ctx)
    print("\nSprache %s: %d Datensaetze geprueft, %d geaendert, %d Felder, %d fehlerhafte Stellen"
          % (bezeichnung, gesamt["geprueft"], gesamt["geaendert"], gesamt["felder"],
             gesamt["vorkommen"]))
    return gesamt


def restpruefung(k):
    rest = 0
    for sprache, _ in SPRACHEN:
        for t in k.kw("account.tax", "search_read", [[("active", "in", [True, False])],
                                                    ["id"] + list(FELDER)],
                      context={"lang": sprache}, limit=0):
            for feld in FELDER:
                wert = t.get(feld) or ""
                for falsch in FEHLER:
                    rest += wert.count(falsch)
    return rest


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--pruefen", action="store_true", help="nur pruefen, nichts schreiben")
    a = p.parse_args()
    env = lade_env()
    if env.get("ODOO18_DB") != ZIEL_DB:
        raise SystemExit("ABBRUCH: Ziel-DB ist %r, erlaubt ist nur %r." % (env.get("ODOO18_DB"), ZIEL_DB))
    k = o18(a.instanz)
    print("Ziel: %s (%s) %s" % (a.instanz, ZIEL_DB, "(Pruefmodus)" if a.pruefen else ""))
    vorher = restpruefung(k)
    print("Fehlerhafte Stellen vorher: %d" % vorher)
    korrigiere(k, a.pruefen)
    nachher = restpruefung(k)
    print("Fehlerhafte Stellen nachher: %d" % nachher)
    return 0 if nachher == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
