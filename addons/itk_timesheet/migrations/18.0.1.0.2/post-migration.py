"""Post-Migration 18.0.1.0.2: Menue-Wortlaute der Zeiterfassung (Odoo-11-Wortlaut).

Odoo fuehrt post_init_hook nur bei Neuinstallation aus. Damit die Wortlaute auch
nach Modul-Upgrade oder Restore wiederhergestellt werden, laeuft dasselbe
idempotente Setup hier erneut.
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.itk_timesheet import setup_runtime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("itk_timesheet post-migration 18.0.1.0.2: Menue-Wortlaute")
    setup_runtime.setup_all(env)
