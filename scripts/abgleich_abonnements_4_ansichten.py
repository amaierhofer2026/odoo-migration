"""Abonnement-Neuabgleich (Schritt 4): Aufbau der Ansichten Odoo 11 gegen Odoo 18.

Aufruf: python scripts/abgleich_abonnements_4_ansichten.py
Nur lesend. Gibt je Ansicht die sichtbaren Felder in Reihenfolge aus.
"""
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
k11, k18 = o11(), o18("vm")


def ansichten(client, modell, bezeichnung):
    print("=== %s: Ansichten fuer %s ===" % (bezeichnung, modell))
    views = client.kw("ir.ui.view", "search_read",
                      [[["model", "=", modell], ["type", "in", ("form", "tree", "search")]],
                       ["name", "type", "arch"]], context=CTX)
    for view in sorted(views, key=lambda v: (v["type"], v["name"])):
        arch = view["arch"]
        if not arch:
            continue
        try:
            wurzel = ET.fromstring(arch)
        except ET.ParseError:
            print("  [%s] %s: nicht lesbar" % (view["type"], view["name"]))
            continue
        print("  [%s] %s" % (view["type"], view["name"]))
        reihen = []
        for element in wurzel.iter():
            if element.tag in ("field", "button", "label"):
                name = element.get("name") or element.get("string") or ""
                sichtbar = element.get("invisible") not in ("1", "True", "true")
                text = element.get("string") or ""
                if name:
                    reihen.append("%s%s%s" % (name, ("(%s)" % text) if text else "",
                                              "" if sichtbar else "[aus]"))
            elif element.tag == "page":
                reihen.append("REITER:%s" % (element.get("string") or ""))
        print("      " + " | ".join(reihen[:60]))
    print()


for modell in ("sale.subscription", "sale.subscription.line", "sale.subscription.template"):
    ansichten(k11, modell, "Odoo 11")
    ansichten(k18, modell, "Odoo 18")
