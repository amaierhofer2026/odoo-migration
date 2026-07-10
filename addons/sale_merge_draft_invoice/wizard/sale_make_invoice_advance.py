from odoo import api, fields, models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    _description = "Sale Advance Payment Inv (Merge Draft)"

    @api.model
    def _get_default_merge_draft_invoice(self):
        if self.env.user.company_id.sale_merge_draft_invoice:
            return True

    merge_draft_invoice = fields.Boolean(
        string='Merge with draft invoices',
        default=_get_default_merge_draft_invoice,
        help=_('Activate this option in order to merge the resulting '
               'invoice with existing draft invoices or deactivate it if you '
               'wish a separate invoice for this sale order.')
    )

    def create_invoices(self):
        rec = self.with_context(merge_draft_invoice=True) if \
            self.merge_draft_invoice else self
        return super(SaleAdvancePaymentInv, rec).create_invoices()
