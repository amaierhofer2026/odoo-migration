"""Post-Migration 18.0.1.5.4: Menue-Namen der Kundenverwaltung (Session 114).

Setzt erneut das idempotente Struktur-Setup: sichtbarer App-Name "Kundenverwaltung",
Konfigurationsgruppe "Interessenten und Chancen" (Odoo 11) statt "Pipeline".
Nur Menue-Bezeichnungen in Odoo 18; Odoo 11 Prod bleibt read-only.
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.itk_crm import setup_runtime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("itk_crm post-migration 18.0.1.5.4: Menue-Namen Kundenverwaltung")
    setup_runtime.setup_all(env)
