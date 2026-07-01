
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    valorisierung_id = fields.Many2one('itk_valorisierung.valorisierung', string="Valorisation Text")
