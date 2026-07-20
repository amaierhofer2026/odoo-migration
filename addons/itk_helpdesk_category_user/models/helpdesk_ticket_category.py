from odoo import fields, models


class HelpdeskTicketCategory(models.Model):
    _inherit = "helpdesk.ticket.category"

    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Assigned User",
        help="Default assignee for tickets of this category. "
        "The user will be set as ticket assignee and follower "
        "when this category is selected and no assignee is set manually.",
        tracking=True,
        domain="[('share', '=', False)]",
    )
