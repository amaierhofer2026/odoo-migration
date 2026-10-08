"""Upgrade auf 18.0.1.1.2: Absender der Ticket-Benachrichtigung korrigieren.

Die Vorlage "Neues Ticket bei IT-Kommunal" verwendete in email_from das Feld
team_id.email. helpdesk.ticket.team hat in Odoo 18 kein Feld email; beim
Anlegen/Speichern eines Tickets (Stufe "Offen" traegt die Vorlage) brach das
Rendern mit AttributeError ab. Korrekt sind team_id.alias_email bzw. der
Firmenwert.
"""


def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    vorlage = env["mail.template"].search(
        [("name", "=", "Neues Ticket bei IT-Kommunal")], limit=1)
    if vorlage:
        vorlage.write({
            "email_from": "{{ object.team_id.alias_email or object.company_id.email "
                          "or 'office@it-kommunal.at' }}",
            "email_to": "{{ object.partner_id.email or object.partner_email }}",
        })
