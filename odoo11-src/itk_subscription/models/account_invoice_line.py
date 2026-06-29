# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    subscription_id = fields.Many2one('sale.subscription')
