# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class itk_third_party_setup(models.Model):
#     _name = 'itk_third_party_setup.itk_third_party_setup'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100