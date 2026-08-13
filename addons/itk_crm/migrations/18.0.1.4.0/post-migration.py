"""Post-Migration 18.0.1.4.0: B (Neue Aktivitaet via Wizard) + C (Aktivitaetstypen).

Odoo fuehrt post_init_hook nur bei Neuinstallation aus. Damit die in
18.0.1.4.0 eingefuehrten Aenderungen auch nach Restore + Modul-Upgrade
automatisch zurueckkommen, laeuft das idempotente Setup hier als
Post-Migration:
- B: Menue 'Neue Aktivitaet' (Wizard mail.activity.schedule) — setup_runtime
- C: RPC-Duplikat-Typen 24/25/26 entfernen + de_DE-Slots sicherstellen —
  setup_runtime._setup_activity_types
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.itk_crm import setup_runtime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("itk_crm post-migration 18.0.1.4.0: B+C Setup (Upgrade/Restore)")
    setup_runtime.setup_all(env)
