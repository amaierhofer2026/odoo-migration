from odoo import fields, models


class HelpdeskTicketCategory(models.Model):
    _inherit = "helpdesk.ticket.category"

    field_ids = fields.One2many(
        comodel_name="itk.helpdesk.subcategory.field",
        inverse_name="sub_category_id",
        string="Zusätzliche Felder",
    )
