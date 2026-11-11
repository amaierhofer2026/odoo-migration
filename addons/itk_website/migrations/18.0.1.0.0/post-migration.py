"""Post-Migration 18.0.1.0.0: Menue-Bezeichnungen erneut setzen.

Laeuft nach jedem Upgrade/Restore, weil die Bezeichnungen Moduldaten mit
noupdate=0 sind und ein Upgrade des Moduls `website` die Quelle zuruecksetzt.
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.itk_website import setup_runtime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("itk_website post-migration 18.0.1.0.0")
    setup_runtime.setup_all(env)
