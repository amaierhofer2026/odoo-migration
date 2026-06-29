##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    number = fields.Integer(compute='_compute_number', store=True)

    @api.depends('sequence', 'move_id.invoice_line_ids')
    def _compute_number(self):
        for move in self.mapped('move_id'):
            number = 1
            for line in move.invoice_line_ids:
                line.number = number
                number += 1
