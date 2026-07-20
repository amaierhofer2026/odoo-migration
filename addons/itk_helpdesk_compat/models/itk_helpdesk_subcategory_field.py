from odoo import fields, models


class ITKHelpdeskSubcategoryField(models.Model):
    _name = "itk.helpdesk.subcategory.field"
    _description = "Helpdesk Subcategory Dynamic Field"
    _order = "sequence, id"

    name = fields.Char(string="Label", required=True, translate=True)
    sub_category_id = fields.Many2one(
        comodel_name="helpdesk.ticket.category",
        string="Subcategory",
        required=True,
        ondelete="cascade",
        domain="[('parent_id', '!=', False)]",
    )
    field_type = fields.Selection(
        selection=[("char", "Text"), ("text", "Multiline Text")],
        string="Field Type",
        default="char",
        required=True,
    )
    required = fields.Boolean(string="Required")
    show_in_portal = fields.Boolean(string="Show in Portal", default=True)
    show_in_internal = fields.Boolean(string="Show in Internal Ticket", default=True)
    sequence = fields.Integer(default=10)
