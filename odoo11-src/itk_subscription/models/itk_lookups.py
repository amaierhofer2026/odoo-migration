# -*- coding: utf-8 -*-

from odoo import fields, models

class NoticePeriod(models.Model):
    _name = 'itk_subscription.noticeperiod'
    _description = 'Notice Period'
    _order = "seq asc"
    code = fields.Char(string="Code", )
    name = fields.Char(string="Name", )
    seq = fields.Integer(string="Sequence", required=False, )