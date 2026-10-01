"""Abrechnung: Konfigurationsmodelle und Assistenten Odoo 11 gegen Odoo 18.

Liest die wirksamen Ansichten (Formular, Liste, Suche) beider Systeme und gibt die sichtbaren
Bezeichnungen kompakt aus, damit eindeutige Unterschiede direkt angeglichen werden koennen.
Odoo 11 wird ausschliesslich gelesen.

Aufruf: python scripts/vergleiche_abrechnung_konfiguration.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

MODELLE = [
    ("account.tax", "account.tax", "Steuern"),
    ("account.journal", "account.journal", "Journale"),
    ("res.currency", "res.currency", "Waehrungen"),
    ("account.fiscal.position", "account.fiscal.position", "Steuerzuordnung"),
    ("account.payment.term", "account.payment.term", "Zahlungsbedingungen"),
    ("account.analytic.account", "account.analytic.account", "Kostenrechnung/Kostenstellen"),
    ("res.partner.bank", "res.partner.bank", "Bankkonten"),
    ("product.category", "product.category", "Verwaltung/Produktkategorien"),
    ("res.config.settings", "res.config.settings", "Einstellungen"),
]

ASSISTENTEN = [
    ("account.payment.register", "account.payment.register", "Zahlung erfassen"),
    ("account.invoice.refund", "account.move.reversal", "Gutschrift/Stornierung"),
    ("account.payment", "account.payment", "Zahlung"),
]


def arch(k, modell, typ, alt):
    try:
        if alt:
            fv = k.kw(modell, "fields_view_get", [[], typ], context={"lang": "de_DE"})
            return fv.get("arch") or ""
        gv = k.kw(modell, "get_views", [[[False, typ]]], context={"lang": "de_DE"})
        for _vid, d in ((gv or {}).get("views") or {}).items():
            return d.get("arch") or ""
    except Exception:
        return ""
    return ""


def sichtbar(a):
    ergebnis = {"felder": [], "seiten": [], "gruppen": [], "buttons": [], "filter": [],
                "gruppierungen": [], "suchfelder": [], "spalten": []}
    if not a:
        return ergebnis
    try:
        w = ET.fromstring(a)
    except ET.ParseError:
        return ergebnis
    for e in w.iter():
        t = e.tag.split("}")[-1]
        if t == "field" and e.get("name"):
            txt = e.get("string") or e.get("name")
            ergebnis["felder"].append(txt)
            if e.get("optional"):
                ergebnis["spalten"].append(txt + (" (optional)" if e.get("optional") == "hide" else ""))
        elif t == "page" and e.get("string"):
            ergebnis["seiten"].append(e.get("string"))
        elif t == "group" and e.get("string"):
            ergebnis["gruppen"].append(e.get("string"))
        elif t == "button":
            txt = e.get("string") or "".join(e.itertext()).strip()
            if txt:
                ergebnis["buttons"].append(txt.split("\n")[0].strip())
        elif t in ("filter", "groupby"):
            txt = e.get("string") or e.get("name") or ""
            if txt:
                (ergebnis["filter"] if e.get("domain") or e.get("context") is None else ergebnis["gruppierungen"]).append(txt)
    for s in ("felder", "seiten", "gruppen", "buttons", "filter", "gruppierungen", "spalten"):
        ergebnis[s] = sorted(set(ergebnis[s]))
    return ergebnis


def main() -> int:
    k11, k18 = o11(), o18("lokal")
    daten = {}
    for m11, m18, titel in MODELLE + ASSISTENTEN:
        print("\n==================== %s (%s -> %s) ====================" % (titel, m11, m18))
        for typ in ("form", "list", "search"):
            a = sichtbar(arch(k11, m11, "tree" if typ == "list" else typ, True))
            b = sichtbar(arch(k18, m18, "list" if typ == "list" else typ, False))
            if not any(a.values()) and not any(b.values()):
                continue
            daten["%s/%s" % (m18, typ)] = {"o11": a, "o18": b}
            print("  -- %s --" % typ)
            for schluessel in ("seiten", "gruppen", "buttons", "felder", "spalten", "filter", "gruppierungen"):
                if not a[schluessel] and not b[schluessel]:
                    continue
                print("     %-14s O11: %s" % (schluessel, a[schluessel][:18]))
                print("     %-14s O18: %s" % ("", b[schluessel][:18]))
    ziel = os.path.join(tempfile.gettempdir(), "abrechnung_konfiguration.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, default=str)
    print("\nRohdaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
