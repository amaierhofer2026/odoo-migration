"""Post-Migration 18.0.1.5.7: Aktionsnamen der Konfiguration wie Odoo 11.

Setzt zusaetzlich die Aktionsnamen (Seitentitel) der Konfigurationslisten auf die
Odoo-11-Wortlaute: "Lead Tags" und "Ablehnungsgruende" (vorher "Stichwoerter",
"Verlustgruende"). Nur Oberflaeche. Odoo 11 Prod bleibt read-only.
"""
from odoo import SUPERUSER_ID, api

from odoo.addons.itk_crm import setup_runtime


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    setup_runtime.setup_all(env)
