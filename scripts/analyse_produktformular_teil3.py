"""Teil 3: Wo landen die Kontofelder in Odoo 18, und was steht in 'Interne Notizen'?"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vergleich_abo_produktformular_felder as F  # noqa: E402

SP = {"lang": "de_DE"}
ZIEL = os.environ.get("TEMP", ".").replace("\\", "/") + "/aboform"
k18 = F.client("lokal")
k11 = F.client("o11")

print("=== Odoo 18: Ansicht, die property_account_income_id nennt ===")
v = k18("ir.ui.view", "read", [[1024], ["id", "name", "model", "type", "inherit_id", "priority", "active", "arch_db", "xml_id"]], context=SP)
if isinstance(v, list) and v:
    x = v[0]
    print("  id=%s name=%s modell=%s typ=%s prio=%s aktiv=%s inherit=%s" % (
        x["id"], x["name"], x["model"], x["type"], x["priority"], x["active"], x["inherit_id"]))
    arch = x.get("arch_db") or ""
    for m in re.finditer("property_account_income_id", arch):
        print("  ...%s..." % arch[max(0, m.start() - 300):m.start() + 120].replace("\n", " "))

print("\n=== Odoo 18: alle Ansichten mit Kontofeldern am Produkt (aktiv) ===")
v2 = k18("ir.ui.view", "search_read",
         [[["model", "in", ["product.template", "product.product"]], ["active", "=", True],
           ["arch_db", "ilike", "property_account"]], ["id", "name", "type", "priority", "inherit_id"]], context=SP)
for x in v2 or []:
    print("  %-6s %-52s %-6s prio=%-4s inherit=%s" % (x["id"], (x["name"] or "")[:52], x["type"], x["priority"], x["inherit_id"]))

print("\n=== Odoo 18: Gruppe 'Interne Notizen' im gerenderten Formular ===")
arch18 = open(ZIEL + "/o18_form_arch.xml", encoding="utf-8").read()
m = re.search(r'<group name="internal_notes".{0,900}', arch18, re.S)
print("  %s" % (m.group(0).replace("\n", " ")[:900] if m else "(nicht gefunden)"))

print("\n=== Odoo 18: Seiteninhalt Allgemeine Informationen, Gruppen und Feldreihenfolge ===")
m = re.search(r'<page name="general_information".*?</page>', arch18, re.S)
if m:
    stueck = m.group(0)
    for g in re.finditer(r'<group[^>]*>', stueck):
        print("  %s" % g.group(0).replace("\n", " ")[:150])
    print("  Felder in Reihenfolge: %s" % re.findall(r'<field name="([^"]+)"', stueck))

print("\n=== Odoo 11: Gruppen der Seite 'Abrechnung' und 'Notizen' ===")
arch11 = open(ZIEL + "/o11_form_arch.xml", encoding="utf-8").read()
for seite in ("invoicing", "notes"):
    m = re.search(r'<page name="%s".*?</page>' % seite, arch11, re.S)
    if m:
        for g in re.finditer(r'<group[^>]*>', m.group(0)):
            print("  [%s] %s" % (seite, g.group(0).replace("\n", " ")[:140]))
        print("  [%s] Felder: %s" % (seite, re.findall(r'<field name="([^"]+)"', m.group(0))))

print("\n=== Odoo 11/18: Reiter 'Lager' - Sichtbarkeitsbedingung ===")
for name, arch in (("o11", arch11), ("o18", arch18)):
    m = re.search(r'<page[^>]*name="inventory"[^>]*>', arch)
    print("  %s: %s" % (name, m.group(0).replace("\n", " ") if m else "(keine Seite)"))
    m2 = re.search(r'<page[^>]*name="variants"[^>]*>', arch)
    print("  %s Varianten: %s" % (name, m2.group(0).replace("\n", " ") if m2 else "(keine)"))
