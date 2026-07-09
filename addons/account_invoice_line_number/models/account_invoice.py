##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    number = fields.Integer(compute='_compute_number', store=True)

    @api.depends('sequence', 'display_type',
                 'move_id.invoice_line_ids',
                 'move_id.invoice_line_ids.sequence',
                 'move_id.invoice_line_ids.display_type')
    def _compute_number(self):
        for move in self.mapped('move_id'):
            # invoice_line_ids ist das im Formular gebundene One2many und im onchange
            # vollstaendig befuellt; self deckt die gerade angelegte Zeile ab, die dort
            # evtl. noch nicht enthalten ist. Nur echte Produktzeilen werden nummeriert.
            lines = (move.invoice_line_ids | self).filtered(
                lambda l: l.move_id == move and l.display_type == 'product')
            number = 1
            for line in lines.sorted(lambda l: l.sequence):
                line.number = number
                number += 1
