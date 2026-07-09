##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    number = fields.Integer(compute='_compute_number', store=True)

    @api.depends('sequence', 'move_id.line_ids', 'move_id.line_ids.sequence',
                 'move_id.line_ids.display_type')
    def _compute_number(self):
        for move in self.mapped('move_id'):
            number = 1
            product_lines = move.line_ids.filtered(
                lambda l: l.display_type == 'product')
            for line in product_lines.sorted(lambda l: l.sequence):
                line.number = number
                number += 1
