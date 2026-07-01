from odoo import models, fields


class SaleOrderLine(models.Model):
    """Adds
        - partner_id (res.partner)
        - salesperson_id (res.users)
    """
    _inherit = 'sale.order.line'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
    )
    salesperson_id = fields.Many2one(
        comodel_name='res.users',
        string='Salesperson',
    )