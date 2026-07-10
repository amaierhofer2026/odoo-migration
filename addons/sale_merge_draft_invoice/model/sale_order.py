from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _create_invoices(self, grouped=False, final=False):
        """Merge with existing draft invoices when context flag is set."""
        if self.env.context.get('merge_draft_invoice'):
            return self._create_invoices_merged(grouped=grouped, final=final)
        return super()._create_invoices(grouped=grouped, final=final)

    def _create_invoices_merged(self, grouped=False, final=False):
        """Create invoices, merging with existing draft invoices per partner."""
        AccountMove = self.env['account.move']
        partners = self.mapped('partner_invoice_id') or self.mapped('partner_id')

        for partner in partners:
            partner_orders = self.filtered(
                lambda o: (o.partner_invoice_id or o.partner_id) == partner)

            # Look for existing draft invoice for this partner
            draft_inv = AccountMove.search([
                ('state', '=', 'draft'),
                ('move_type', '=', 'out_invoice'),
                ('partner_id', '=', partner.id),
                ('invoice_line_ids.sale_line_ids', '!=', False),
            ], limit=1)

            if draft_inv:
                # Add invoice lines to existing draft invoice
                for order in partner_orders:
                    order._create_invoices_from_order(draft_inv)
                if final:
                    draft_inv.action_post()
            else:
                # Create new invoices normally for these orders
                partner_orders._create_invoices(grouped=grouped, final=final)

        # Find newly created invoices to return
        return self.env['account.move'].search([
            ('invoice_line_ids.sale_line_ids.order_id', 'in', self.ids),
            ('state', 'in', ['draft', 'posted']),
        ])

    def _create_invoices_from_order(self, invoice):
        """Add this order's lines to an existing draft invoice."""
        invoice_line_vals = []
        for line in self.order_line:
            invoice_line_vals.append((0, 0, line._prepare_invoice_line()))
        if invoice_line_vals:
            invoice.write({'invoice_line_ids': invoice_line_vals})
