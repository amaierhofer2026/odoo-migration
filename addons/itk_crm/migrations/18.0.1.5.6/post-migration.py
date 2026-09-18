"""Post-Migration 18.0.1.5.6: Loeschrecht auf crm.lead fuer die ITK-Gruppe "Manager (edit)".

Ergaenzt in security/ir.model.access.csv: die ITK-Gruppe "Manager (edit)"
(itk_crm.itk_group_manager, in Odoo 18 bereits vorhanden) erhaelt genau ein
zusaetzliches Recht - das Loeschen von Verkaufschancen/Interessenten. Lesen,
Schreiben und Anlegen kommen in Odoo 18 ueber die Verkaufsrollen; in Odoo 11
hatte die Gruppe "Manager (edit)" diese Rechte ebenfalls (R/W/C/D).

Keine Benutzerzuordnung, keine Datenmigration. Odoo 11 Prod bleibt read-only.
Zusaetzlich laeuft das idempotente Struktur-Setup erneut (u. a. die sichtbaren
Odoo-11-Bezeichnungen).
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.itk_crm import setup_runtime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("itk_crm post-migration 18.0.1.5.6: Loeschrecht crm.lead fuer Manager (edit)")
    setup_runtime.setup_all(env)
