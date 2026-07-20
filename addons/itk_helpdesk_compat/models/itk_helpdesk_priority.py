from odoo import fields, models


class ITKHelpdeskPriority(models.Model):
    _name = "itk.helpdesk.priority"
    _description = "Helpdesk Priority"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    color = fields.Char(string="Color", default="#FFFFFF")
    active = fields.Boolean(default=True)
