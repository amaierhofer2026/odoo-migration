
from odoo import models, fields, api



class SaleOrder(models.Model):
    """Adds
        - administrative_contact,
        - technical_contact
        """
    _inherit = 'sale.order'

    administrative_contact_id = fields.Many2one('res.partner', string='Verwaltungskontakt', )
    technical_contact_id = fields.Many2one('res.partner', string='Technischer Kontakt', )
    product_category_id = fields.Many2one('product.category', string='Produktkategorie', )
    final_customer_id = fields.Many2one('res.partner', string='Endkunde', )
    sale_contact_id = fields.Many2one('res.partner', string='Verkaufskontakt', )

    @api.onchange('partner_id')
    def _partner_id_changed(self):
        self.final_customer_id = self.partner_id

    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        return
