from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Beschriftung des Feldes "Interne Referenz" wie in Odoo 11 Prod (Session 106).
    # Odoo 18 hat in der Basis-Ansicht ausdruecklich "Referenz" gesetzt; fachlich ist es
    # dasselbe Feld (res.partner.ref, char), die Bedeutung soll aber sofort eindeutig sein.
    # Damit gilt der Wortlaut auch in Suche, Filter und allen Ansichten ohne eigene Beschriftung.
    ref = fields.Char(string='Interne Referenz', index=True)

    is_customer = fields.Boolean(
        string='Ist ein Kunde',
        compute='_compute_is_customer',
        inverse='_inverse_is_customer',
    )

    is_supplier = fields.Boolean(
        string='Ist ein Lieferant',
        compute='_compute_is_supplier',
        inverse='_inverse_is_supplier',
    )

    @api.depends('customer_rank')
    def _compute_is_customer(self):
        for rec in self:
            rec.is_customer = rec.customer_rank > 0

    def _inverse_is_customer(self):
        for rec in self:
            if rec.is_customer:
                if rec.customer_rank <= 0:
                    rec.customer_rank = 1
            else:
                rec.customer_rank = 0

    @api.depends('supplier_rank')
    def _compute_is_supplier(self):
        for rec in self:
            rec.is_supplier = rec.supplier_rank > 0

    def _inverse_is_supplier(self):
        for rec in self:
            if rec.is_supplier:
                if rec.supplier_rank <= 0:
                    rec.supplier_rank = 1
            else:
                rec.supplier_rank = 0
