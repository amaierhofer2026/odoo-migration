from odoo import fields, models


class ITKHelpdeskPriority(models.Model):
    _name = "itk.helpdesk.priority"
    _description = "Helpdesk Priority"
    _order = "sequence, id"

    name = fields.Char(string="Priorität Name", required=True, translate=True)
    sequence = fields.Integer(string="Nummernfolge", default=10)
    color = fields.Char(string="Farbe", default="#FFFFFF")
    active = fields.Boolean(string="Aktiv", default=True)
