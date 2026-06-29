# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    sale_order_confirmation_date = fields.Date(string='Saleorder Confirmation Date', help="")
    sale_order_benefit_period = fields.Text(string='Benefit Period')      # Leistungszeitraum für Abo
    notice = fields.Text(string='Invoice Note')