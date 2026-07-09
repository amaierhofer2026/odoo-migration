##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _set_invoice_line_numbers(self):
        # Nummeriert die Produktpositionen einer Rechnung fortlaufend (1,2,3 ...).
        # Wird auf Move-Ebene ausgefuehrt, weil ein zeilenbasierter Compute bei
        # account.move die Geschwisterzeilen im onchange NICHT sieht.
        for move in self:
            number = 1
            for line in move.invoice_line_ids.sorted(lambda l: l.sequence):
                new_number = number if line.display_type == 'product' else 0
                if line.number != new_number:
                    line.number = new_number
                if line.display_type == 'product':
                    number += 1

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_number(self):
        # Live-Aktualisierung im Formular (Zeile hinzufuegen/umsortieren/loeschen).
        self._set_invoice_line_numbers()

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves._set_invoice_line_numbers()
        return moves

    def write(self, vals):
        res = super().write(vals)
        # Serverseitig erzeugte/geaenderte Rechnungen (z. B. aus Auftrag/Abo) neu nummerieren.
        # Nur Entwuerfe anfassen – gebuchte Buchungen duerfen nicht veraendert werden.
        if 'invoice_line_ids' in vals or 'line_ids' in vals:
            self.filtered(lambda m: m.state == 'draft')._set_invoice_line_numbers()
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    number = fields.Integer(store=True)
