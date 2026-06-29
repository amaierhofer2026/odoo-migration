# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    projectcategory_id = fields.Many2one('itk_projectcategory.projectcategory', string="Project Category")
