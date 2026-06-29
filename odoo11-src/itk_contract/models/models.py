# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ItkAccountAnalyticAccount(models.Model):
    _name = 'account.analytic.account'
    _inherit = ['account.analytic.account']
    minimum_contract_period = fields.Boolean('Minimum Contract Period')
