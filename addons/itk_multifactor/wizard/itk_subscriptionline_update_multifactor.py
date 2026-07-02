from odoo import models, _
from odoo.exceptions import UserError


class SaleSubscriptionLineMultifactorUpdate(models.TransientModel):
    _name = "sale.subscriptionline.multifactor.update.confirm"
    _description = "Update the selected SaleSubscriptionlines for the Multifactor from EWZ"

    def salesubscriptionline_update_multifactor(self):
        active_ids = self.env.context.get('active_ids', [])
        for record in self.env['sale.subscription.line'].browse(active_ids):
            if not record.product_id.is_multi_factor_product:
                raise UserError(_(
                    "Selected entry(ies) cannot be updated as they are no products "
                    "with Multiplicationfactor by Thousand."
                ))
            record.set_product_uom_qty_with_multiplication_factor()
        return {'type': 'ir.actions.act_window_close'}
