"""Post-Migration 18.0.1.5.0: Aktivitaetstyp-Entscheidung (Typ 2 kanonisch).

Odoo fuehrt post_init_hook nur bei Neuinstallation aus. Damit die
Entscheidung vom 14.08.2026 auch nach Restore + Modul-Upgrade automatisch
wiederhergestellt wird, laeuft das idempotente Setup hier als Post-Migration:
- Typ 2 (mail.mail_activity_data_call) ist kanonisch, de_DE-Name 'Anrufen'
- Legacy-Typ 21 (itk_crm.mail_activity_type_anrufen) wird entfernt, falls er
  aus einem Altdump wieder existiert (Referenzen -> Typ 2)
- delay_count und alle Standardwerte von Typ 2 bleiben unangetastet
- setup_runtime._setup_activity_types (idempotent)
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.itk_crm import setup_runtime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("itk_crm post-migration 18.0.1.5.0: Aktivitaetstyp-Entscheidung (Upgrade/Restore)")
    setup_runtime.setup_all(env)
