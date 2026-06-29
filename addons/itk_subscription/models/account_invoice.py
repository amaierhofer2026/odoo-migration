from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sale_order_confirmation_date = fields.Date(string='Saleorder Confirmation Date', help="")
    sale_order_benefit_period = fields.Text(string='Benefit Period')
    notice = fields.Text(string='Invoice Note')
