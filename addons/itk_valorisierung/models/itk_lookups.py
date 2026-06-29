# -*- coding: utf-8 -*-

from odoo import fields, models


class Valorisierung(models.Model):
    _name = 'itk_valorisierung.valorisierung'
    _description = 'Valorisierung'
    _order = "seq asc"
    name = fields.Char(string="Code", )
    description = fields.Text(string="Description", )
    seq = fields.Integer(string="Sequence", required=False, )