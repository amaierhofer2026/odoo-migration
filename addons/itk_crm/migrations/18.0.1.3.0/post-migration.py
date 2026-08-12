"""Post-Migration 18.0.1.3.0: ITK-CRM-Struktur nach Upgrade/Restore wiederherstellen.

Odoo fuehrt post_init_hook nur bei Neuinstallation aus. Damit die O11-kompatible
CRM-Struktur (Kundenverwaltung: Stages, Menüs, App-Name, Custom-Felder, Lost
Reasons, Automated Action, Aktivitäten, Vertriebskanäle) auch nach einem
Restore + Modul-Upgrade automatisch zurueckkommt, laeuft das idempotente
Setup hier als Post-Migration (alle Funktionen sind mehrfach ausfuehrbar).
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.itk_crm import setup_runtime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("itk_crm post-migration 18.0.1.3.0: Struktur-Setup (Upgrade/Restore)")
    setup_runtime.setup_all(env)
