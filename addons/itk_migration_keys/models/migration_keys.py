# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class ResPartnerCategory(models.Model):
    _inherit = "res.partner.category"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class ProductTemplate(models.Model):
    _inherit = "product.template"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class ProductProduct(models.Model):
    _inherit = "product.product"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class ProductCategory(models.Model):
    _inherit = "product.category"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class SaleOrder(models.Model):
    _inherit = "sale.order"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)
