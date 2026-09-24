"""Zeigt die Odoo-11-Seite 'Abrechnung' im Rohzustand (aus dem gesicherten Arch)."""
import os
import re

ZIEL = os.environ.get("TEMP", ".").replace("\\", "/") + "/aboform"
arch = open(ZIEL + "/o11_form_arch.xml", encoding="utf-8").read()
i = arch.find('<page string="Abrechnung"')
j = arch.find('<page string="Notizen"')
print(arch[i:j])
print("\n=== Seite 'Bilder' ===")
k = arch.find('<page string="Bilder"')
print(arch[k:k + 1400])
