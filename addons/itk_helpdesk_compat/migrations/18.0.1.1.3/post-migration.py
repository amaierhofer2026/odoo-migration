"""Upgrade auf 18.0.1.1.3: Benachrichtigungsvorlage auf Odoo-18-Syntax.

Die Vorlage "Neues Ticket bei IT-Kommunal" enthielt noch die Odoo-11-Syntax
${ object.feld }. Odoo 18 rendert Mailvorlagen mit {{ ... }} bzw. QWeb; die
Platzhalter wären im Kundenmail wörtlich erschienen.
"""

BODY = """<div style="font-family:Arial,Helvetica,sans-serif;max-width:600px">
  <h2 style="color:#875A7B">Ihr Ticket wurde erstellt</h2>
  <p>Guten Tag {{ object.partner_id.name or object.partner_name or '' }},</p>
  <p>vielen Dank für Ihre Anfrage. Wir haben ein Ticket mit folgenden Details erstellt:</p>
  <table style="width:100%;border-collapse:collapse">
    <tr>
      <td style="padding:8px;border:1px solid #ddd;background:#f9f9f9;font-weight:bold">Ticket</td>
      <td style="padding:8px;border:1px solid #ddd">{{ object.number }} - {{ object.name }}</td>
    </tr>
    <tr>
      <td style="padding:8px;border:1px solid #ddd;background:#f9f9f9;font-weight:bold">Kategorie</td>
      <td style="padding:8px;border:1px solid #ddd">{{ object.category_id.name or '' }}</td>
    </tr>
  </table>
  <p>Wir kümmern uns schnellstmöglich um Ihr Anliegen.</p>
  <p>Mit freundlichen Grüßen,<br/>Ihr IT-Kommunal Team</p>
</div>"""


def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    vorlage = env["mail.template"].search(
        [("name", "=", "Neues Ticket bei IT-Kommunal")], limit=1)
    if vorlage:
        vorlage.write({
            "subject": "Neues Ticket {{ object.number }}: {{ object.name }}",
            "body_html": BODY,
        })
