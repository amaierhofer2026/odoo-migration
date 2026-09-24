"""Prueft, welcher Eintrag aus get_views in Odoo 18 der vollstaendig zusammengefuehrte Arch ist."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vergleich_abo_produktformular as V  # noqa: E402

SP = {"lang": "de_DE"}
ZIEL = os.environ.get("TEMP", ".").replace("\\", "/") + "/aboform"
k18 = V.client("lokal")

e = k18("product.template", "get_views", [[[False, "form"]]], context=SP)
print("Schluessel der Antwort: %s" % sorted(e.keys()))
print("main_view_id: %s" % e.get("main_view_id"))
for vid, v in e["views"].items():
    arch = v.get("arch") or ""
    print("  view %-6s %-46s len=%-6d Buchhaltung=%-5s Abo-Vorlage=%-5s is_multi=%-5s" % (
        vid, (v.get("name") or v.get("xml_id") or "")[:46], len(arch),
        'name="invoicing"' in arch, "subscription_template_id" in arch, "is_multi_factor_product" in arch))

letzter = list(e["views"].values())[-1]
arch = letzter.get("arch") or ""
with open(ZIEL + "/o18_form_arch_final.xml", "w", encoding="utf-8") as f:
    f.write(arch)
print("\nletzter Eintrag gespeichert: %d Zeichen -> %s/o18_form_arch_final.xml" % (len(arch), ZIEL))
seiten = V.__dict__.get("re") and None
import re  # noqa: E402
print("Seiten im letzten Eintrag: %s" % re.findall(r'<page[^>]*string="([^"]+)"', arch))
print("Kontofelder im letzten Eintrag: %s" % re.findall(r'property_account\w*', arch))
