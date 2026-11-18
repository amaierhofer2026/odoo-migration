"""Post-Migration 18.0.1.6.0: CRM-Struktur an Odoo 11 angleichen (Session 145).

Aenderungen gegenueber 18.0.1.5.10:
- Vertriebskanal "Suche / Liste" ergaenzt (633 Interessenten in Odoo 11).
- Odoo-18-Standardteam "Website" heisst sichtbar wieder "Webseite" (Odoo 11).
- use_leads wie Odoo 11 (alle Kanaele ausser "Webseite").
- Stufe "Verrechnet": is_won=True und nicht zugeklappt; "Verloren" nicht
  zugeklappt (Odoo 11 zeigte alle neun Stufen offen und zaehlte "Verrechnet"
  ueber die Wahrscheinlichkeit als gewonnen).
- Ablehnungsgruende mit Odoo-11-Wortlaut in Quelle, de_DE und en_US.
- Fuenf ITK-Aktivitaetstypen aus Odoo 11 (u. a. "zu Verloren").
- Menue Berichtswesen "Leads" heisst wieder "Interessenten".

Nur Oberflaeche und Stammdaten, keine Vorgangsdaten. Idempotent, laeuft bei
jedem itk_crm-Upgrade erneut ueber setup_all. Odoo 11 Prod bleibt read-only.
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.itk_crm import setup_runtime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("itk_crm post-migration 18.0.1.6.0: CRM-Struktur an Odoo 11 angleichen")
    setup_runtime.setup_all(env)
