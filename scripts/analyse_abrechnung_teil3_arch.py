"""Read-only Analyse Abrechnung Teil 3: Formulare, Reiter, Buttons, Smart Buttons.

Vergleicht die Rechnungsformulare (Odoo 11: account.invoice, Odoo 18: account.move) ueber den
View-Arch: Reiter (page), Gruppen, Kopf-/Fussbuttons, Smart Buttons, Statusleiste.

Aufruf:  python scripts/analyse_abrechnung_teil3_arch.py [--json]
Odoo 11 Prod wird ausschliesslich lesend verwendet.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18


def arch(k, modell, typ="form"):
    """View-Arch holen - Odoo 18 ueber get_views, Odoo 11 ueber fields_view_get."""
    ctx = {"lang": "de_DE"}
    try:
        d = k.kw(modell, "get_views", [[[False, typ]]], context=ctx)
        return d["views"][typ]["arch"]
    except Exception:
        d = k.kw(modell, "fields_view_get", [[], typ], context=ctx)
        return d["arch"]


def texte(el, attr="string"):
    return el.get(attr) or ""


def analysiere(a, system):
    """Seiten, Gruppen, Buttons, Smart Buttons und Statusleiste aus dem Arch."""
    ergebnis = {"seiten": [], "gruppen": [], "kopf_buttons": [], "zeilen_buttons": [],
                "smart_buttons": [], "statusleiste": [], "felder_anzahl": 0}
    try:
        wurzel = ET.fromstring(a)
    except ET.ParseError as fehler:
        ergebnis["fehler"] = str(fehler)[:120]
        return ergebnis
    ergebnis["felder_anzahl"] = len(wurzel.findall(".//field"))

    for seite in wurzel.findall(".//page"):
        name = seite.get("name") or ""
        label = texte(seite)
        untergruppen = [texte(g) for g in seite.findall(".//group") if texte(g)]
        ergebnis["seiten"].append({"name": name, "string": label, "gruppen": untergruppen})
        for g in seite.findall(".//group"):
            if texte(g):
                ergebnis["gruppen"].append(texte(g))

    # Statusleiste: erstes field mit widget=statusbar
    for f in wurzel.findall(".//field"):
        if f.get("widget") == "statusbar":
            ergebnis["statusleiste"].append(f.get("name"))

    # Buttons: Kopfbereich (header) gegen Rest unterscheiden
    for header in wurzel.findall(".//header"):
        for b in header.findall(".//button"):
            ergebnis["kopf_buttons"].append({
                "name": b.get("name"), "string": texte(b), "typ": b.get("type"),
                "states": b.get("states"), "attrs": (b.get("attrs") or "")[:200],
                "modifiers": (b.get("modifiers") or "")[:200],
                "invisible": (b.get("invisible") or "")[:200],
                "class": b.get("class") or ""})
    for b in wurzel.findall(".//button"):
        if b.get("class") and ("oe_stat_button" in b.get("class") or "oe_stat" in b.get("class")):
            ergebnis["smart_buttons"].append({"name": b.get("name"), "string": texte(b),
                                              "typ": b.get("type")})
        elif not b.get("class") or "oe_stat" not in (b.get("class") or ""):
            pass

    # alle Buttons ausserhalb des Headers (Zeilenbuttons u. a.)
    header_buttons = wurzel.findall(".//header//button")
    for b in wurzel.findall(".//button"):
        if b in header_buttons:
            continue
        if "oe_stat_button" in (b.get("class") or ""):
            continue
        ergebnis["zeilen_buttons"].append({"name": b.get("name"), "string": texte(b),
                                           "typ": b.get("type"),
                                           "attrs": (b.get("attrs") or "")[:160]})

    # Stat-Buttons im Odoo-11-Arch sind divs mit class oe_stat_button
    for d in wurzel.findall(".//div"):
        if "oe_stat_button" in (d.get("class") or ""):
            b = d.find(".//button")
            ergebnis["smart_buttons"].append({
                "name": (b.get("name") if b is not None else None),
                "string": texte(d) or (texte(b) if b is not None else ""),
                "typ": (b.get("type") if b is not None else "div")})
    return ergebnis


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    lade_env()
    k11 = o11()
    k18 = o18("lokal")
    aus = {}
    for schluessel, k, modell in (("o11", k11, "account.invoice"), ("o18", k18, "account.move")):
        roh = arch(k, modell)
        d = analysiere(roh, schluessel)
        aus[schluessel] = d
        print("\n================ %s (%s) ================" % (schluessel.upper(), modell))
        print("Felder im Formular: %d | Reiter: %d | Kopf-Buttons: %d | Zeilen-Buttons: %d | "
              "Smart Buttons: %d" % (d["felder_anzahl"], len(d["seiten"]), len(d["kopf_buttons"]),
                                     len(d["zeilen_buttons"]), len(d["smart_buttons"])))
        print("Statusleiste: %s" % d["statusleiste"])
        print("-- Reiter --")
        for s in d["seiten"]:
            print("   %-24s '%s' | Gruppen: %s" % (s["name"], s["string"], s["gruppen"]))
        print("-- Kopf-Buttons --")
        for b in d["kopf_buttons"]:
            print("   %-34s '%s' typ=%s states=%s %s"
                  % (b["name"], b["string"], b["typ"], b["states"] or "-",
                     ("attrs=" + b["attrs"]) if b["attrs"] else ""))
        print("-- Smart Buttons --")
        for b in d["smart_buttons"]:
            print("   %-34s '%s' (%s)" % (b["name"], b["string"], b["typ"]))
        print("-- uebrige Buttons --")
        for b in d["zeilen_buttons"]:
            print("   %-34s '%s' typ=%s %s" % (b["name"], b["string"], b["typ"],
                                               ("attrs=" + b["attrs"]) if b["attrs"] else ""))

    if a.json:
        ziel = os.path.join(tempfile.gettempdir(), "abrechnung_teil3_arch.json")
        with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(aus, fh, ensure_ascii=False, indent=1, sort_keys=True)
        print("\nRohdaten (nicht im Repo): %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
