# -*- coding: utf-8 -*-

from odoo import models, fields, api



class SaleOrder(models.Model):
    """Adds
        - administrative_contact,
        - technical_contact
        """
    _inherit = 'sale.order'

    administrative_contact_id = fields.Many2one('res.partner', string='Administrative Contact', )
    technical_contact_id = fields.Many2one('res.partner', string='Technical Contact', )
    product_category_id = fields.Many2one('product.category', string='Product Category', )
    final_customer_id = fields.Many2one('res.partner', string='Final Customer', )
    sale_contact_id = fields.Many2one('res.partner', string='Sale Contact', )

    @api.onchange('partner_id')
    def _partner_id_changed(self):
        self.final_customer_id = self.partner_id

    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        return
