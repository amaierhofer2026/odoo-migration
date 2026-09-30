"""Gezielter Migrations-Check Verkauf: Formularaufbau und Spalten Odoo 11 vs Odoo 18.

NUR LESEND. Vergleicht die im Browser sichtbare Struktur:
  1. Reiter (Notebook-Seiten) des Auftragsformulars
  2. Aufbau je Reiter (Gruppen und Felder in Reihenfolge, mit Beschriftungen)
  3. alle Felder und Gruppen des Reiters "Weitere Informationen"
  4. sichtbare Spalten der Auftragszeilen-Tabelle im Formular
  5. Spalten der Auftragslisten im Menue Auftraege/Angebote

Grundlage: die zusammengesetzte Ansicht (inherits beruecksichtigt) von sale.order
bzw. sale.order.line.

Ausgabe: docs/_verkauf_migrationscheck_aufbau.json + Klartextbericht.

Aufruf:
    python scripts/analyse_verkauf_migrationscheck_aufbau.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}


def hole_arch(k, modell: str, ansichtstyp: str) -> str:
    """Zusammengesetzte Ansicht (inkl. geerbter Aenderungen) als XML-Text."""
    for methode in ("get_view", "fields_view_get"):
        try:
            if methode == "get_view":
                d = k.kw(modell, "get_view", [False, ansichtstyp], context=SP)
            else:
                d = k.kw(modell, "fields_view_get", [False, ansichtstyp], context=SP)
            if d and d.get("arch"):
                return d["arch"]
        except Exception:
            continue
    raise RuntimeError("Ansicht %s/%s nicht lesbar" % (modell, ansichtstyp))


def saeubere(xml_text: str) -> ET.Element:
    """XML-Text der Ansicht einlesen (Entities bleiben unveraendert, sie sind gueltiges XML)."""
    xml_text = re.sub(r"<\?xml[^>]*\?>", "", xml_text).strip()
    try:
        return ET.fromstring(xml_text)
    except ET.ParseError:
        # Notnagel: nur die Struktur-Elemente behalten, alle Attribute aus XML-Entities loesen
        import html
        entspannt = re.sub(r"<(/?)(\w[\w-]*)", r"<\1\2", xml_text)
        entspannt = entspannt.replace("&quot;", '"').replace("&amp;", "&") \
                             .replace("&gt;", ">").replace("&lt;", "<").replace("&apos;", "'")
        entspannt = html.unescape(entspannt)
        entspannt = re.sub(r'(attrs|modifiers)="[^"]*"', "", entspannt)
        return ET.fromstring(entspannt)


def felder_im_knoten(knoten: ET.Element, tiefe: int = 0) -> list[dict]:
    """Felder in Dokumentreihenfolge, mit Gruppe (naechster group-Vorfahre)."""
    ergebnis = []

    def lauf(e: ET.Element, gruppe: str | None, tiefe: int):
        name = e.tag
        if name == "field":
            ergebnis.append({
                "feld": e.get("name"),
                "beschriftung": e.get("string"),
                "widget": e.get("widget"),
                "readonly": e.get("readonly"),
                "invisible": e.get("invisible") or e.get("attrs"),
                "gruppe": gruppe,
                "tiefe": tiefe,
            })
        naechste_gruppe = gruppe
        if name == "group":
            naechste_gruppe = e.get("string") or e.get("name") or "(ohne Beschriftung)"
        for kind in list(e):
            lauf(kind, naechste_gruppe, tiefe + 1)

    lauf(knoten, None, tiefe)
    return ergebnis


def seiten(knoten: ET.Element) -> list[dict]:
    """Notebook-Seiten mit ihren Feldern in Reihenfolge."""
    ergebnis = []
    for nb in knoten.iter("notebook"):
        for seite in nb.findall("page"):
            felder = felder_im_knoten(seite)
            ergebnis.append({
                "seite": seite.get("string") or seite.get("name") or "(ohne Beschriftung)",
                "name": seite.get("name"),
                "felder": felder,
                "gruppen": sorted({f["gruppe"] for f in felder if f["gruppe"]}),
                "felder_namen": [f["feld"] for f in felder],
            })
    return ergebnis


def spalten(k, modell: str, ansicht: str = "list") -> list[str]:
    """Spalten der Standard-Listenansicht eines Modells (Dokumentreihenfolge)."""
    try:
        arch = hole_arch(k, modell, ansicht)
    except Exception:
        arch = hole_arch(k, modell, "tree")
    w = saeubere(arch)
    spalten_liste = []
    for feld in w.iter("field"):
        if feld.get("name") and feld.get("name") not in spalten_liste:
            spalten_liste.append(feld.get("name"))
    return spalten_liste


def main() -> int:
    print("Migrations-Check Formularaufbau Verkauf (nur lesend)")
    k11, k18l, k18v = o11(), o18("lokal"), o18("vm")

    ergebnis: dict = {}

    for modell in ("sale.order",):
        arch11 = hole_arch(k11, modell, "form")
        arch18 = hole_arch(k18l, modell, "form")
        w11, w18 = saeubere(arch11), saeubere(arch18)
        s11, s18 = seiten(w11), seiten(w18)
        ergebnis[modell] = {
            "reiter_o11": [{"seite": s["seite"], "felder": s["felder_namen"],
                            "gruppen": s["gruppen"]} for s in s11],
            "reiter_o18": [{"seite": s["seite"], "felder": s["felder_namen"],
                            "gruppen": s["gruppen"]} for s in s18],
        }
        print("=" * 78)
        print("Reiter des Formulars %s" % modell)
        print("Odoo 11 (%d): %s" % (len(s11), [s["seite"] for s in s11]))
        print("Odoo 18 (%d): %s" % (len(s18), [s["seite"] for s in s18]))
        for s in s11:
            print("  O11 %-28s Felder %d" % (s["seite"], len(s["felder_namen"])))
        for s in s18:
            print("  O18 %-28s Felder %d" % (s["seite"], len(s["felder_namen"])))

        # Reiter "Weitere Informationen" im Detail
        for label, liste in (("Odoo 11", s11), ("Odoo 18", s18)):
            for s in liste:
                if "weitere" in (s["seite"] or "").lower():
                    print()
                    print("--- %s: Reiter '%s' ---" % (label, s["seite"]))
                    for f in s["felder"]:
                        print("    %-32s %-40s Gruppe: %s"
                              % (f["feld"], f["beschriftung"] or "", f["gruppe"] or "-"))
        ergebnis["weitere_informationen"] = {
            "o11": [s["felder"] for s in s11 if "weitere" in (s["seite"] or "").lower()],
            "o18": [s["felder"] for s in s18 if "weitere" in (s["seite"] or "").lower()],
        }

    # Spalten der Auftragszeilen im Formular (o2m order_line) und der Liste
    print()
    print("=" * 78)
    print("Spalten der Auftragszeilen")
    for instanzname, k in (("Odoo 11", k11), ("Odoo 18 lokal", k18l), ("Odoo 18 VM", k18v)):
        zl = spalten(k, "sale.order.line")
        print("  %-14s %s" % (instanzname, zl))
    ergebnis["spalten_auftragszeilen"] = {
        "o11": spalten(k11, "sale.order.line"),
        "o18_lokal": spalten(k18l, "sale.order.line"),
        "o18_vm": spalten(k18v, "sale.order.line"),
    }

    print()
    print("Spalten der Auftragsliste")
    for instanzname, k in (("Odoo 11", k11), ("Odoo 18 lokal", k18l)):
        print("  %-14s %s" % (instanzname, spalten(k, "sale.order")))
    ergebnis["spalten_auftragsliste"] = {
        "o11": spalten(k11, "sale.order"),
        "o18_lokal": spalten(k18l, "sale.order"),
    }

    pfad = os.path.join(REPO, "docs", "_verkauf_migrationscheck_aufbau.json")
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print()
    print("Rohdaten: %s" % pfad)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
