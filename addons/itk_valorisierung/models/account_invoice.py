# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    valorisierung_id = fields.Many2one('itk_valorisierung.valorisierung', string="Valorisation Text")
