
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # Session 130: Beschriftung nach Odoo 11. Odoo 11 fuehrt account.invoice.valorisierung_id
    # mit der Quellbezeichnung "Valorisation Text"; auch in deutscher Anzeige zeigt Odoo 11
    # "Valorisation Text" (nachgemessen mit lang=de_DE). Die abweichende Bezeichnung
    # "Valorisierungstext" ist damit ersetzt.
    valorisierung_id = fields.Many2one('itk_valorisierung.valorisierung', string="Valorisation Text")
