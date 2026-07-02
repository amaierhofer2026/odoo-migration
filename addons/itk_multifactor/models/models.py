from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    multi_factor = fields.Integer(
        string='Multiplication Factor/Thsd',
        tracking=True,
    )

    def _compute_populationthousandsfactor(self):
        self.ensure_one()
        if hasattr(self, 'population') and self.population:
            self.multi_factor = -(-self.population // 1000)
        elif not hasattr(self, 'population'):
            pass
        else:
            self.multi_factor = 1


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_multi_factor_product = fields.Boolean(
        string="To multiply by Factor(per 1000)",
        default=False,
    )


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_multiplication_factor = fields.Integer(
        string='Multiplication Factor/Thsd',
        tracking=True,
    )

    @api.onchange('product_id')
    def set_product_uom_qty_with_multiplication_factor(self):
        if self.product_id.is_multi_factor_product and self.order_id.partner_id:
            self.product_uom_qty = 1
            self.qty_multiplication_factor = self.order_id.partner_id.multi_factor
            self.product_uom_qty = self.product_uom_qty * self.qty_multiplication_factor
        elif self.product_id.is_multi_factor_product and not self.order_id.partner_id:
            self.product_uom_qty = 1
        else:
            self.product_uom_qty = 1


class SaleSubscriptionLine(models.Model):
    _inherit = 'sale.subscription.line'

    qty_multiplication_factor = fields.Integer(
        string='Multiplication Factor/Thsd',
        tracking=True,
        default=1,
    )

    def set_product_uom_qty_with_multiplication_factor(self):
        if self.product_id.is_multi_factor_product and self.partner_id:
            self.quantity = 1
            self.qty_multiplication_factor = self.partner_id.multi_factor
            self.quantity = self.quantity * self.qty_multiplication_factor
        elif self.product_id.is_multi_factor_product and not self.partner_id:
            self.product_uom_qty = 1
        else:
            self.product_uom_qty = 1
        return
