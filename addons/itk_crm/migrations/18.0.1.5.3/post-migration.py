"""Post-Migration 18.0.1.5.3: sichtbarer App-/Menue-Name "Kundenverwaltung" (Session 114).

Menue 143 (crm.crm_menu_root) hat noupdate=0: bei einem crm-Modul-Upgrade wird die
Quelle zurueckgesetzt, waehrend die alte de_DE-Uebersetzung "CRM" in der Datenbank
stehen bleibt. Deshalb laeuft hier (und kuenftig bei jedem itk_crm-Upgrade) das
komplette idempotente Struktur-Setup - insbesondere _setup_crm_menus() mit dem
sichtbaren App-Namen "Kundenverwaltung".

Es werden ausschliesslich Menue-/Strukturbezeichnungen in Odoo 18 gesetzt.
Odoo 11 Prod ist und bleibt read-only (kein Schreibzugriff).
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.itk_crm import setup_runtime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("itk_crm post-migration 18.0.1.5.3: App-/Menue-Namen Kundenverwaltung")
    setup_runtime.setup_all(env)
