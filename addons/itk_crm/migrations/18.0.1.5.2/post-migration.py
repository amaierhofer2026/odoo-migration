"""Post-Migration 18.0.1.5.2: CRM-Stufen und Vertriebskanaele aus Odoo 11 (Session 114).

Odoo fuehrt post_init_hook nur bei Neuinstallation aus. Damit die Anpassungen
auch nach Restore + Modul-Upgrade automatisch wiederhergestellt werden, laeuft
das idempotente Setup hier als Post-Migration:

- CRM-Stufen: fehlende Stufe "Angebot ausgesendet" (Odoo 11, 2 Chancen) und die
  Odoo-11-Reihenfolge (New, Angebotsphase, On-Hold, Angebot ausgesendet,
  Positive Rueckmeldung, Won, Verloren, Zur Verrechnung bereit, Verrechnet)
- Vertriebskanaele: nur die in Odoo 11 tatsaechlich verwendeten Teams
  (Vertriebskanaele (Intern), Interne Weitergabe, Persoenlicher Kontakt, Webinar,
  Telefon, Newsletter, Webseite/Website) als Stammdaten vorbereiten
- Verkaufschancen werden NICHT zugeordnet (keine Datenmigration)
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.itk_crm import setup_runtime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("itk_crm post-migration 18.0.1.5.2: CRM-Stufen und Teams (Upgrade/Restore)")
    setup_runtime._setup_stage_labels(env)
    setup_runtime._setup_crm_teams(env)
