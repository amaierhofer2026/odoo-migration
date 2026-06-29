from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    subscription_id = fields.Many2one('sale.subscription')
