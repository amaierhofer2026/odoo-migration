##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    number = fields.Integer(compute='_compute_number', store=True)

    @api.depends('sequence', 'order_id')
    def _compute_number(self):
        for purchase in self.mapped('order_id'):
            number = 1
            for line in purchase.order_line:
                line.number = number
                number += 1
