"""Read-only: Buttons und Reiter der Rechnungsformulare mit ihren Bedingungen auflisten.

Aufruf:  python scripts/analyse_abrechnung_teil3_details.py
"""
from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18


def arch(k, modell):
    try:
        d = k.kw(modell, "get_views", [[[False, "form"]]], context={"lang": "de_DE"})
        return d["views"]["form"]["arch"]
    except Exception:
        return k.kw(modell, "fields_view_get", [[], "form"], context={"lang": "de_DE"})["arch"]


def wurzel(text):
    return ET.fromstring(text.replace("&nbsp;", " ").replace("&", "&amp;").replace("&amp;amp;", "&amp;"))


def bedingung(el):
    teile = []
    for schluessel in ("invisible", "states", "attrs", "modifiers", "readonly", "groups", "class"):
        wert = el.get(schluessel)
        if wert:
            teile.append("%s=%s" % (schluessel, wert.replace("\n", " ")[:110]))
    return " | ".join(teile)


def main() -> int:
    lade_env()
    for name, k, modell in (("O11", o11(), "account.invoice"), ("O18", o18("lokal"), "account.move")):
        w = wurzel(arch(k, modell))
        print("\n================ %s %s (Formular) ================" % (name, modell))
        print("-- Reiter --")
        for seite in w.findall(".//page"):
            print("   %-22s %s" % (seite.get("name") or "", seite.get("string") or ""))
        print("-- Kopf-Buttons (Statusleiste) --")
        for b in w.findall(".//header//button"):
            print("   %-34s typ=%-8s ziel=%-28s %s"
                  % (b.get("name") or "", b.get("type") or "", (b.get("name") if b.get("type") != "object" else b.get("name")),
                     (b.get("string") or "")[:38]))
            print("        %s" % bedingung(b))
        print("-- Buttons ausserhalb des Kopfes --")
        for b in [x for x in w.findall(".//button") if x not in w.findall(".//header//button")]:
            kls = b.get("class") or ""
            art = "Smart Button" if "oe_stat_button" in kls else "Button"
            print("   %-6s %-32s typ=%-8s %-28s %s" % (art, b.get("name") or "", b.get("type") or "",
                                                       (b.get("name") if b.get("type") != "object" else b.get("name")),
                                                       (b.get("string") or "")[:34]))
            print("        %s" % bedingung(b))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
