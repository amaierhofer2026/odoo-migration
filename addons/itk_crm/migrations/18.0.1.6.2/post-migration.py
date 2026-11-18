"""Post-Migration 18.0.1.6.2: ITK-Felder im Formular auch fuer Verkaufschancen.

Odoo 11 zeigt x_lead_status, x_Produktinteresse und x_Lead_Quelle im Formular
von Interessenten UND Verkaufschancen. Die Odoo-18-Ansicht
crm.lead.form.inherit.itk blendete die Gruppe fuer Verkaufschancen aus
(invisible="type == 'opportunity'"). Die Einschraenkung ist entfernt.

Die Ansicht ist Moduldaten mit noupdate=1, deshalb korrigiert der Setup-Lauf die
gespeicherte Fassung. Idempotent. Odoo 11 Prod bleibt read-only.
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.itk_crm import setup_runtime

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("itk_crm post-migration 18.0.1.6.2: Lead Classification in beiden Formularen")
    setup_runtime.setup_all(env)
