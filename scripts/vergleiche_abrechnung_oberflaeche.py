"""Bereich Abrechnung: vollstaendige Gegenueberstellung der sichtbaren Oberflaeche.

Liest aus Odoo 11 (read-only) und Odoo 18 die *wirksamen* Ansichten (Formular, Liste, Suche)
und extrahiert alle sichtbaren Bezeichnungen:
Felder, Reiter (Seiten), Gruppen, Buttons, Smart Buttons, Listenspalten (inkl. optional),
Filter, Gruppierungen, Suchfelder. Zusaetzlich der Menuebaum.

Ergebnis: JSON im Temp-Ordner und eine kompakte Gegenueberstellung auf der Konsole.

Aufruf: python scripts/vergleiche_abrechnung_oberflaeche.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

PAARE = [("account.invoice", "account.move", "Rechnung/Gutschrift"),
         ("account.payment", "account.payment", "Zahlung")]


def wirksame_ansicht(k, modell, typ, alt=False):
    """Liefert die wirksame Ansicht (arch) einer Ansichtsart."""
    try:
        if alt:
            fv = k.kw(modell, "fields_view_get", [[], typ], context={"lang": "de_DE"})
            return fv.get("arch") or ""
        gv = k.kw(modell, "get_views", [[[False, typ]]], context={"lang": "de_DE"})
        views = (gv or {}).get("views") or {}
        for _vid, daten in views.items():
            return daten.get("arch") or ""
    except Exception as fehler:
        print("      Hinweis %s %s: %s" % (modell, typ, str(fehler)[:90]))
    return ""


def auswerten(arch):
    ergebnis = {"felder": {}, "seiten": [], "gruppen": [], "buttons": [], "smart": [],
                "spalten": [], "filter": [], "gruppierungen": [], "suchfelder": []}
    if not arch:
        return ergebnis
    try:
        wurzel = ET.fromstring(arch)
    except ET.ParseError:
        return ergebnis
    for e in wurzel.iter():
        tag = e.tag.split("}")[-1]
        if tag == "field":
            name = e.get("name") or ""
            if name:
                ergebnis["felder"][name] = e.get("string") or ""
                if e.get("optional"):
                    ergebnis["spalten"].append((name, e.get("string") or "", e.get("optional")))
                if e.get("invisible") and "column" in (e.get("invisible") or ""):
                    ergebnis["spalten"].append((name, e.get("string") or "", "invisible-column"))
        elif tag == "page":
            if e.get("string"):
                ergebnis["seiten"].append(e.get("string"))
        elif tag == "group":
            if e.get("string"):
                ergebnis["gruppen"].append(e.get("string"))
        elif tag == "button":
            text = e.get("string") or ""
            if not text:
                text = "".join(e.itertext()).strip() or e.get("name") or ""
            if text:
                ergebnis["buttons"].append(text)
        elif tag == "filter":
            ergebnis["filter"].append({"name": e.get("name") or "", "string": e.get("string") or "",
                                       "domain": (e.get("domain") or "")[:120],
                                       "context": (e.get("context") or "")[:100]})
        elif tag == "groupby":
            ergebnis["gruppierungen"].append(e.get("string") or e.get("name") or "")
    # Smart Buttons: Buttons innerhalb von oe_button_box
    for box in wurzel.iter():
        if (box.get("class") or "").find("oe_button_box") >= 0:
            for b in box.iter():
                if b.tag.split("}")[-1] == "button":
                    ergebnis["smart"].append(b.get("string") or b.get("name") or "")
    return ergebnis


def sammle(k, modell, alt=False):
    return {"form": auswerten(wirksame_ansicht(k, modell, "form", alt)),
            "list": auswerten(wirksame_ansicht(k, modell, "tree", alt) or wirksame_ansicht(k, modell, "list", alt)),
            "search": auswerten(wirksame_ansicht(k, modell, "search", alt))}


def main() -> int:
    k11, k18 = o11(), o18("lokal")
    daten = {}
    for m11, m18, titel in PAARE:
        print("\n==================== %s (%s -> %s) ====================" % (titel, m11, m18))
        s11, s18 = sammle(k11, m11, True), sammle(k18, m18, False)
        daten[m11] = {"o11": s11, "o18": s18}
        for bereich in ("form", "list", "search"):
            a, b = s11[bereich], s18[bereich]
            print("\n-- %s --" % bereich)
            print("   O11 Reiter   : %s" % a["seiten"])
            print("   O18 Reiter   : %s" % b["seiten"])
            print("   O11 Gruppen  : %s" % a["gruppen"])
            print("   O18 Gruppen  : %s" % b["gruppen"])
            print("   O11 Buttons  : %s" % sorted(set(a["buttons"])))
            print("   O18 Buttons  : %s" % sorted(set(b["buttons"])))
            print("   O11 Smart    : %s" % sorted(set(a["smart"])))
            print("   O18 Smart    : %s" % sorted(set(b["smart"])))
            if bereich == "search":
                print("   O11 Filter   : %s" % sorted({f["name"] for f in a["filter"] if f["name"]}))
                print("   O18 Filter   : %s" % sorted({f["name"] for f in b["filter"] if f["name"]}))
                print("   O11 Gruppen  : %s" % sorted({f["name"] for f in a["filter"] if not f["domain"]}))
                print("   O18 Gruppierungen: %s" % sorted(set(b["gruppierungen"])))
                print("   O11 Suchfelder: %s" % sorted(a["suchfelder"].keys() if isinstance(a["suchfelder"], dict) else []))
                print("   O18 Suchfelder: %s" % sorted(a["suchfelder"].keys() if isinstance(b["suchfelder"], dict) else []))
            if bereich == "list":
                print("   O11 Spalten: %s" % [f for f in a["felder"].items()])
                print("   O18 Spalten: %s" % [f for f in b["felder"].items()])
                print("   O11 optionale Spalten: %s" % [s[1] or s[0] for s in a["spalten"]])
                print("   O18 optionale Spalten: %s" % [s[1] or s[0] for s in b["spalten"]])

    ziel = os.path.join(tempfile.gettempdir(), "abrechnung_oberflaeche.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, default=str)
    print("\nRohdaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
