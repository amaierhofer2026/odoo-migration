from odoo import models, api, _
from odoo.exceptions import UserError


class SaleSubscriptionLineMultifactorUpdate(models.TransientModel):
    """
    This wizard will update the Multifactor from EWZ in all the selected salesubscriptionlines
    """

    _name = "sale.subscriptionline.multifactor.update.confirm"
    _description = "Update the selected SaleSubscriptionlines for the Multifactor from EWZ"


    def salesubscriptionline_update_multifactor(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['sale.subscription.line'].browse(active_ids):
            if record.product_id.is_multi_factor_product == False:
                raise UserError(_("Selected entry(ies) cannot be updated as they are no products with Mulitplicationfactor by Thousand."))
            record.set_product_uom_qty_with_multiplication_factor()
        return {'type': 'ir.actions.act_window_close'}