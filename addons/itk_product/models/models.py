from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # type = fields.Selection(selection_add=[('license', 'Lizenz')])
    type = fields.Selection(selection=[('consu', 'Verbrauchsgüter'),
                                       ('service', 'Service'),
                                       ('general', 'Allgemein'),
                                       ('onlineservice', 'Onlineservice'),
                                       ('sw', 'Software-Lösung'),
                                       ('consulting', 'Consulting'),
                                       ('platform', 'Plattform'),
                                       ('hw', 'Hardware'),
                                       ('project', 'Förderprojekt'),
                                       ])


    product_type_id = fields.Many2one('itk_product.product_type', string='Produkttyp')
    to_multiply_by_factor = fields.Boolean(string="Mit Faktor multiplizieren (pro 1.000)", default=False)

    # 24.09.2026 (Session 120, Teil 15): Odoo 11 hatte am Produkt ein Feld "Verantwortlich"
    # (responsible_id -> res.users). Odoo 17/18 hat es ersatzlos entfernt, in Odoo 11 ist es
    # aber auf allen 649 Produkten gepflegt (Administrator 394, Waiss Martina 252,
    # Breiteneder Lorenz 3). Es wird hier mit demselben Feldnamen und derselben Relation
    # neu angelegt, damit der Wert bei der Migration 1:1 uebernommen werden kann.
    responsible_id = fields.Many2one('res.users', string='Verantwortlich')


class ProductType(models.Model):
    _name = 'itk_product.product_type'
    _description = 'Product-Type'
    _order = "seq asc"
    code = fields.Char(string="Code", )
    name = fields.Char(string="Name", )
    seq = fields.Integer(string="Sequence", required=False, )