from odoo import fields, models


class HelpdeskTicketCategory(models.Model):
    _inherit = "helpdesk.ticket.category"

    user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="helpdesk_category_user_rel",
        column1="category_id",
        column2="user_id",
        string="Assigned Users",
        help="Users responsible for this category. "
        "When a ticket is assigned to this category, all these users "
        "will be added as followers to receive email notifications.",
        tracking=True,
    )
