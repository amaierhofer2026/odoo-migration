"""Prueft (read-only): welche Felder waren im Odoo-11-Reiter 'Abrechnung' wirklich sichtbar,
und aus welcher Ansicht stammt die Odoo-18-Gruppe 'internal_notes'."""
from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vergleich_abo_produktformular as V  # noqa: E402

SP = {"lang": "de_DE"}
ZIEL = os.environ.get("TEMP", ".").replace("\\", "/") + "/aboform"
arch11 = open(ZIEL + "/o11_form_arch.xml", encoding="utf-8").read()

print("=== Odoo 11, Seite 'Abrechnung': Feld, Anzeige-Attribut, Modifier ===")
i, j = arch11.find('<page string="Abrechnung"'), arch11.find('<page string="Notizen"')
stueck = arch11[i:j]
for m in re.finditer(r'<field name="([^"]+)"([^>]*)>', stueck):
    name, rest = m.group(1), m.group(2)
    inv = re.search(r'invisible="([^"]*)"', rest)
    attrs = re.search(r"attrs=\"([^\"]*)\"", rest)
    print("   %-44s invisible=%-10s attrs=%s" % (name, inv.group(1) if inv else "-",
                                                 (attrs.group(1)[:70] if attrs else "-")))
print("\n   sichtbar (weder invisible=1 noch attrs-invisible) fuer ein Dienstleistungsprodukt:")
for m in re.finditer(r'<field name="([^"]+)"([^>]*)>', stueck):
    name, rest = m.group(1), m.group(2)
    inv = (re.search(r'invisible="([^"]*)"', rest) or [None, "-"])[1]
    attrs = (re.search(r"attrs=\"([^\"]*)\"", rest) or [None, ""])[1]
    versteckt = inv in ("1", "True", "true") or "invisible" in attrs
    if not versteckt:
        print("      %s" % name)

print("\n=== Odoo 18: Quelle der Gruppe internal_notes ===")
k18 = V.client("lokal")
v = k18("ir.ui.view", "search_read",
        [[["model", "=", "product.template"], ["type", "=", "form"], ["arch_db", "ilike", "internal_notes"]],
         ["id", "name", "priority", "inherit_id", "mode"]], context=SP, limit=0)
for x in v or []:
    md = k18("ir.model.data", "search_read", [[["model", "=", "ir.ui.view"], ["res_id", "=", x["id"]]], ["module", "name"]], context=SP)
    print("   id=%-6s %-46s prio=%-4s modus=%-10s inherit=%s  xml_id=%s" % (
        x["id"], (x["name"] or "")[:46], x["priority"], x.get("mode") or "-", x["inherit_id"], md))

print("\n=== Odoo 18: Rohstelle der Gruppe (Quelltext, englisch) ===")
for x in v or []:
    a = k18("ir.ui.view", "read", [[x["id"]], ["arch_db"]], context=SP)[0]["arch_db"]
    for m in re.finditer(r'<group name="internal_notes"[^>]*>', a):
        print("   Ansicht %s: %s" % (x["id"], m.group(0)))

print("\n=== Odoo 18: Ansichten, die das Produktformular erweitern (Basiskette) ===")
b = k18("ir.ui.view", "search_read",
        [[["model", "=", "product.template"], ["type", "=", "form"], ["mode", "=", "primary"]],
         ["id", "name", "priority", "xml_id"]], context=SP, limit=0)
for x in b or []:
    print("   id=%-6s %-46s xml_id=%s" % (x["id"], (x["name"] or "")[:46], x.get("xml_id")))
