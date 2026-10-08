"""Upgrade auf 18.0.1.1.1.

Das Modul importierte bisher das Paket `controllers` nicht; die
Portal-Anpassungen waren dadurch nie aktiv. Nach dem Import der Controller
werden hier die Benachrichtigungen fuer oeffentliche Tickets ergaenzt:
die Vorlage "Neues Ticket bei IT-Kommunal" muss auch dann senden, wenn
kein Kontakt verknuepft ist (Odoo 11: "Website (Public)").
"""


def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})

    vorlage = env["mail.template"].search(
        [("name", "=", "Neues Ticket bei IT-Kommunal")], limit=1)
    if vorlage:
        vorlage.write({
            "email_to": "{{ object.partner_id.email or object.partner_email }}",
            "email_from": "{{ object.team_id.email or user.company_id.email "
                          "or 'office@it-kommunal.at' }}",
        })

    # Stufe "Offen" traegt die Willkommens-Vorlage (wie Odoo 11:
    # Status 1 "Open" mit Mail-Vorlage "Neues Ticket bei IT-Kommunal").
    stufe = env["helpdesk.ticket.stage"].search([("name", "=", "Offen")], limit=1)
    if stufe and vorlage and not stufe.mail_template_id:
        stufe.mail_template_id = vorlage.id
