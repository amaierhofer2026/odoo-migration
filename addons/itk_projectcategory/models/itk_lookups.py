# -*- coding: utf-8 -*-

from odoo import fields, models


class ProjectCategory(models.Model):
    _name = 'itk_projectcategory.projectcategory'
    _description = 'Project Category'
    _order = "seq asc"
    code = fields.Char(string="Code", )
    name = fields.Char(string="Name", )
    seq = fields.Integer(string="Sequence", required=False, )