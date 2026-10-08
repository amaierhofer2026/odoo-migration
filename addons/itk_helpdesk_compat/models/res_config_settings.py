from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    itk_helpdesk_public_team_id = fields.Many2one(
        comodel_name="helpdesk.ticket.team",
        string="Helpdesk-Team für öffentliche Tickets",
        config_parameter="itk_helpdesk.public_team_id",
        help="Team, dem Tickets aus dem öffentlichen Formular zugeordnet werden.",
    )
    itk_helpdesk_public_rate_limit = fields.Integer(
        string="Öffentliche Eingaben je IP und Stunde",
        config_parameter="itk_helpdesk.public_rate_limit",
        default=5,
        help="Höchstzahl der Ticket-Eingaben je IP-Adresse innerhalb einer Stunde.",
    )
    itk_helpdesk_public_global_limit = fields.Integer(
        string="Öffentliche Eingaben insgesamt je Stunde",
        config_parameter="itk_helpdesk.public_global_limit",
        default=60,
        help="Gesamtschutz gegen verteilte Spam-Eingaben.",
    )
