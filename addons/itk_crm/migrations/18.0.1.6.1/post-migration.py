"""Post-Migration 18.0.1.6.1: Auswahlwerte der ITK-Felder auf crm.lead.

Die Felder x_Lead_Quelle, x_Produktinteresse und x_lead_status wurden bisher mit
dem Anzeigetext als technischem Schluessel gefuehrt ("Bereits Kunde" statt "kunde")
und hatten dadurch nur 11 statt 24 Lead-Quellen. Fuer die Datenmigration aus
Odoo 11 (Session 145) werden die Odoo-11-Schluessel wiederhergestellt - sichtbar
aendert sich nichts, die Auswahl bleibt dieselbe.

Idempotent ueber setup_runtime._setup_custom_fields. Odoo 11 Prod bleibt read-only.
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.itk_crm import setup_runtime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("itk_crm post-migration 18.0.1.6.1: Odoo-11-Schluessel der crm.lead-Auswahlfelder")
    setup_runtime.setup_all(env)
