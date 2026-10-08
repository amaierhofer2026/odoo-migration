from odoo import fields, models


class ITKHelpdeskPublicSubmission(models.Model):
    """Protokoll oeffentlicher Ticket-Eingaben (Spamschutz/Rate-Limit).

    Wird ausschliesslich serverseitig (sudo) geschrieben und gelesen.
    """

    _name = "itk.helpdesk.public.submission"
    _description = "Öffentliche Helpdesk-Eingabe (Spamschutz)"
    _order = "create_date desc"
    _rec_name = "ip"

    ip = fields.Char(string="IP-Adresse", required=True, index=True)
    email = fields.Char(string="E-Mail")
    ticket_id = fields.Many2one("helpdesk.ticket", string="Ticket", ondelete="set null")
    blocked = fields.Boolean(string="Blockiert", default=False)
