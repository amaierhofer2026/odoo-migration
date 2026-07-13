from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _create_invoices(self, grouped=False, final=False, date=None):
        """Merge with existing draft invoices when context flag is set."""
        if self.env.context.get('merge_draft_invoice'):
            return self._create_invoices_merged(
                grouped=grouped, final=final, date=date)
        return super()._create_invoices(
            grouped=grouped, final=final, date=date)

    def _create_invoices_merged(self, grouped=False, final=False, date=None):
        """Create invoices, merging with existing draft invoices per partner."""
        AccountMove = self.env['account.move']
        partners = self.mapped('partner_invoice_id') or self.mapped('partner_id')
        result = AccountMove

        for partner in partners:
            partner_orders = self.filtered(
                lambda o: (o.partner_invoice_id or o.partner_id) == partner)

            draft_inv = AccountMove.search([
                ('state', '=', 'draft'),
                ('move_type', '=', 'out_invoice'),
                ('partner_id', '=', partner.id),
                ('invoice_line_ids.sale_line_ids', '!=', False),
            ], limit=1)

            if draft_inv:
                for order in partner_orders:
                    for line in order.order_line:
                        line_vals = line._prepare_invoice_line()
                        draft_inv.write({
                            'invoice_line_ids': [(0, 0, line_vals)],
                        })
                result |= draft_inv
            else:
                moves = partner_orders.with_context(
                    merge_draft_invoice=False
                )._create_invoices(
                    grouped=grouped, final=final, date=date)
                result |= moves

        return result
