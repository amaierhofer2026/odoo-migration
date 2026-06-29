# -*- coding: utf-8 -*-

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


    product_type_id = fields.Many2one('itk_product.product_type', string='Product-Type')
    # is_multi_factor_product = fields.Boolean(string="To multiply by Factor(thsd)", default=False)


class ProductType(models.Model):
    _name = 'itk_product.product_type'
    _description = 'Product-Type'
    _order = "seq asc"
    code = fields.Char(string="Code", )
    name = fields.Char(string="Name", )
    seq = fields.Integer(string="Sequence", required=False, )