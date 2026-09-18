"""Post-Migration 18.0.1.5.5: sichtbare Bezeichnungen wie Odoo 11 (Session 115).

Setzt das idempotente Struktur-Setup erneut: Feldbeschreibungen (Stufe, Verkaeufer,
Vertriebskanal, Ablehnungsgrund, Erwartetes Abschlussdatum), Menue- und Aktionsnamen
(Lead Tags, Ablehnungsgruende, Stufen), App-Name Kundenverwaltung, Menuepunkt
Berichtswesen/Vertriebskanaele. Nur Oberflaeche, keine Modell-/Feldnamen.
Odoo 11 Prod bleibt read-only.
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.itk_crm import setup_runtime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("itk_crm post-migration 18.0.1.5.5: Bezeichnungen wie Odoo 11")
    setup_runtime.setup_all(env)
