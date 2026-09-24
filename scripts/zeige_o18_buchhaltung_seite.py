"""Inhalt der Odoo-18-Seite 'Buchhaltung' (account.product_template_form_view) im Rohzustand."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vergleich_abo_produktformular as V  # noqa: E402

SP = {"lang": "de_DE"}
k = V.client("lokal")
v = k("ir.ui.view", "read", [[1024], ["arch_db"]], context=SP)
arch = v[0]["arch_db"]
i = arch.find('name="invoicing"')
print("=== Roharch der Seite (ab name=\"invoicing\", 3000 Zeichen) ===")
print(arch[max(0, i - 200):i + 3000])
