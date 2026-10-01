"""Feldweiser Formularabgleich Bereich Abrechnung (Odoo 11 gegen Odoo 18).

Erhebt aus den wirksamen Ansichten beide Systeme:
- Formular: Seiten (Reiter), Gruppen (Ueberschriften), Felder mit Bezeichnung in Reihenfolge, Buttons
- Liste: Spalten mit Bezeichnung in Reihenfolge (inkl. optional/invisible)
- Suche: Filter, Gruppierungen, Suchfelder
und stellt die Bezeichnungen gegenueber: welche Odoo-11-Bezeichnung fehlt in Odoo 18.

Odoo 11 wird ausschliesslich gelesen.
Aufruf: python scripts/abgleiche_abrechnung_formulare.py
"""
from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

PAARE = [
    ("account.invoice", "account.move", "Rechnung/Gutschrift (Kopf und Reiter)", "form"),
    ("account.invoice.line", "account.move.line", "Rechnungszeilen (Spalten)", "tree/list"),
    ("account.payment", "account.payment", "Zahlung", "form"),
    ("account.payment", "account.payment", "Zahlungsliste (Spalten)", "tree/list"),
    ("res.partner", "res.partner", "Kunde/Lieferant", "form"),
    ("product.product", "product.product", "Produkt", "form"),
    ("account.payment.term", "account.payment.term", "Zahlungsbedingungen", "form"),
    ("account.journal", "account.journal", "Journale", "form"),
    ("account.tax", "account.tax", "Steuern", "form"),
    ("account.fiscal.position", "account.fiscal.position", "Steuerzuordnung", "form"),
    ("res.partner.bank", "res.partner.bank", "Bankkonten", "form"),
    ("account.analytic.account", "account.analytic.account", "Kostenstellen", "form"),
    ("account.analytic.plan", "account.analytic.plan", "Kostenstellenplaene", "form"),
]


def arch(k, modell, typ, alt):
    try:
        if alt:
            return k.kw(modell, "fields_view_get", [[], typ], context={"lang": "de_DE"}).get("arch") or ""
        gv = k.kw(modell, "get_views", [[[False, typ]]], context={"lang": "de_DE"})
        for _vid, d in ((gv or {}).get("views") or {}).items():
            return d.get("arch") or ""
    except Exception as fehler:
        return ""
    return ""


def erhebe(a, liste=False):
    """Seiten/Gruppen/Felder in Reihenfolge plus Buttons."""
    seiten, gruppen, felder, buttons, spalten = [], [], [], [], []
    if not a:
        return {"seiten": seiten, "gruppen": gruppen, "felder": felder, "buttons": buttons,
                "spalten": spalten}
    try:
        w = ET.fromstring(a)
    except ET.ParseError:
        return {"seiten": seiten, "gruppen": gruppen, "felder": felder, "buttons": buttons,
                "spalten": spalten}
    for e in w.iter():
        t = e.tag.split("}")[-1]
        if t == "field" and e.get("name"):
            text = e.get("string") or e.get("name")
            felder.append(text)
            if liste:
                spalten.append(text)
        elif t == "page" and e.get("string"):
            seiten.append(e.get("string"))
        elif t == "group" and e.get("string"):
            gruppen.append(e.get("string"))
        elif t == "button":
            txt = (e.get("string") or "".join(e.itertext())).strip().split("\n")[0]
            if txt:
                buttons.append(txt)
    return {"seiten": seiten, "gruppen": gruppen, "felder": sorted(set(felder)),
            "buttons": sorted(set(buttons)), "spalten": spalten}


CACHE = {}


def bezeichnungen(k, modell, schluessel):
    """Feldname -> sichtbare Bezeichnung (de_DE) des Modells."""
    if (schluessel, modell) in CACHE:
        return CACHE[(schluessel, modell)]
    try:
        f = k.kw(modell, "fields_get", [[], ["string"]], context={"lang": "de_DE"})
        CACHE[(schluessel, modell)] = {n: (d.get("string") or n) for n, d in f.items()}
    except Exception:
        CACHE[(schluessel, modell)] = {}
    return CACHE[(schluessel, modell)]


def main() -> int:
    k11, k18 = o11(), o18("lokal")
    for m11, m18, titel, art in PAARE:
        liste = art == "tree/list"
        typ11 = "tree" if liste else art
        typ18 = "list" if liste else art
        a = erhebe(arch(k11, m11, typ11, True), liste)
        b = erhebe(arch(k18, m18, typ18, False), liste)
        # Bezeichnungen aufloesen (Feldname -> sichtbare Bezeichnung des Modells)
        def aufloesen(k, modell, schluessel, daten):
            texte = bezeichnungen(k, modell, schluessel)
            daten["felder"] = sorted({texte.get(f, f) for f in daten["felder"]})
            daten["spalten"] = [texte.get(f, f) for f in daten["spalten"]]
            return daten
        n11 = m11 if m11 != "account.invoice.line" else "account.invoice.line"
        n18 = m18 if m18 != "account.move.line" else "account.move.line"
        a = aufloesen(k11, n11, "o11", a)
        b = aufloesen(k18, n18, "o18", b)
        fehlend = [f for f in a["felder"] if f not in b["felder"]]
        zusatz = [f for f in b["felder"] if f not in a["felder"]]
        print("\n==================== %s ====================" % titel)
        print("   O11 Reiter  : %s" % a["seiten"])
        print("   O18 Reiter  : %s" % b["seiten"])
        print("   O11 Gruppen : %s" % a["gruppen"])
        print("   O18 Gruppen : %s" % b["gruppen"])
        print("   O11 Buttons : %s" % a["buttons"][:14])
        print("   O18 Buttons : %s" % b["buttons"][:14])
        if liste:
            print("   O11 Spalten : %s" % a["spalten"])
            print("   O18 Spalten : %s" % b["spalten"][:24])
        print("   >>> in Odoo 11 sichtbar, in Odoo 18 NICHT vorhanden (%d):" % len(fehlend))
        for f in fehlend:
            print("        - %s" % f)
        print("   Odoo-18-Zusatz (%d, bleibt): %s" % (len(zusatz), zusatz[:14]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
