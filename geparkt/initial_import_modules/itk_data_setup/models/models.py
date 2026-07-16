# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class itk_data_setup(models.Model):
#     _name = 'itk_data_setup.itk_data_setup'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100

# class ProjectCategory(models.Model):
#     _name = 'itk_data_setup.projectcategory'
#     _description = 'Project Category'
#     _order = "seq asc"
#     code = fields.Char(string="Code", )
#     name = fields.Char(string="Name", )
#     seq = fields.Integer(string="Sequence", required=False, )