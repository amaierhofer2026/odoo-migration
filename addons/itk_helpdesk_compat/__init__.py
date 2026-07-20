from . import models

def post_init_hook(env):
    """Create ITK stages and mail template after module installation."""

    # --- Mail Template ---
    MailTemplate = env["mail.template"]
    existing_tpl = MailTemplate.search([("name", "=", "Neues Ticket bei IT-Kommunal")], limit=1)
    if not existing_tpl:
        tpl = MailTemplate.create({
            "name": "Neues Ticket bei IT-Kommunal",
            "model_id": env.ref("helpdesk_mgmt.model_helpdesk_ticket").id,
            "subject": "Neues Ticket: {{ object.name }}",
            "email_from": "{{ object.team_id.email or user.company_id.email }}",
            "email_to": "{{ object.partner_id.email }}",
            "auto_delete": True,
            "lang": "{{ object.partner_id.lang }}",
            "body_html": """<div style="font-family:Arial,sans-serif;max-width:600px">
<h2 style="color:#875A7B">Ihr Ticket wurde erstellt</h2>
<p>Guten Tag ${object.partner_id.name},</p>
<p>vielen Dank für Ihre Anfrage. Wir haben ein Ticket erstellt:</p>
<table style="width:100%;border-collapse:collapse">
<tr><td style="padding:8px;border:1px solid #ddd;background:#f9f9f9;font-weight:bold">Ticket</td><td style="padding:8px;border:1px solid #ddd">${object.name}</td></tr>
<tr><td style="padding:8px;border:1px solid #ddd;background:#f9f9f9;font-weight:bold">Kategorie</td><td style="padding:8px;border:1px solid #ddd">${object.category_id.name or ''}</td></tr>
</table>
<p>Wir kümmern uns schnellstmöglich darum.</p>
<p>Ihr IT-Kommunal Team</p></div>""",
        })
        mail_template = tpl
    else:
        mail_template = existing_tpl

    # --- Stages ---
    Stage = env["helpdesk.ticket.stage"]
    all_existing = Stage.with_context(active_test=False).search([])
    if all_existing:
        all_existing.write({"active": False})
    ITK_STAGES = [
        {"name": "Offen", "sequence": 10, "fold": False, "closed": False, "unattended": True,
         "mail_template_id": mail_template.id},
        {"name": "in Bearbeitung", "sequence": 20, "fold": False, "closed": False, "unattended": False},
        {"name": "on Hold", "sequence": 30, "fold": True, "closed": False, "unattended": False},
        {"name": "Geschlossen/Behoben", "sequence": 40, "fold": False, "closed": True, "unattended": False},
        {"name": "an Partner weitergeleitet", "sequence": 50, "fold": False, "closed": False, "unattended": False},
        {"name": "Verrechnung mit Kunde geklärt", "sequence": 60, "fold": True, "closed": True, "unattended": False},
    ]
    for stage_data in ITK_STAGES:
        existing = Stage.with_context(active_test=False).search([("name", "=", stage_data["name"])], limit=1)
        if existing:
            existing.write(stage_data)
            existing.write({"active": True})
        else:
            Stage.create(stage_data)
