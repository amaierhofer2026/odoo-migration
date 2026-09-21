
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
    # Odoo 11 fuehrt das Bestaetigungsdatum getrennt vom Bestelldatum (date_order). Odoo 18 hat kein
    # solches Feld: _prepare_confirmation_values() ueberschreibt date_order beim Bestaetigen mit dem
    # aktuellen Zeitpunkt. Fuer die Migration wird das Odoo-11-Feld "Bestaetigung am" deshalb 1:1
    # uebernommen (Session 117).
    confirmation_date = fields.Datetime(string='Bestätigung am', readonly=True, copy=False)

    @api.onchange('partner_id')
    def _partner_id_changed(self):
        self.final_customer_id = self.partner_id

    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        return


    def _prepare_confirmation_values(self):
        """Bestaetigungszeitpunkt mitschreiben (wie Odoo 11 confirmation_date)."""
        werte = super()._prepare_confirmation_values()
        if not self.confirmation_date:
            werte['confirmation_date'] = fields.Datetime.now()
        return werte
