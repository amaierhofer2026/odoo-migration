from odoo import models, api, fields, _
from odoo.exceptions import UserError

class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    # @api.onchange('pricelist_id')
    def onchange_pricelist_id_from_wizard(self, plist_id):
        self.pricelist_id = plist_id
        subscription_lines = self.recurring_invoice_line_ids
        for line in subscription_lines:
            line.onchange_product_quantity()  # calls calculation of prices and looks for adequate pricelist
        self._compute_recurring_total()


class SaleSubscriptionSetPricelist(models.TransientModel):
    """
    This wizard will update the Pricelist in selected Subscriptions
    """
    _name = "sale.subscription.set.pricelist.confirm"
    _description = "Set new Pricelist to the selected Subscriptions"

    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True)

    @api.multi
    def subscription_set_pricelist(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['sale.subscription'].browse(active_ids):
            if record.state == 'close' or record.state == 'cancel':
                raise UserError("One or more selected subscriptions cannot be updated as they are closed or cancelled!")
            record.onchange_pricelist_id_from_wizard(self.pricelist_id)
        return {'type': 'ir.actions.act_window_close'}
