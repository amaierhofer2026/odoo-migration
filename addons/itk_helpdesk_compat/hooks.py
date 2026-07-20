"""Post-install hooks for itk_helpdesk_compat."""

import logging

_logger = logging.getLogger(__name__)

ITK_STAGES = [
    {"name": "Offen", "sequence": 10, "fold": False, "closed": False, "unattended": True,
     "mail_template_xmlid": "itk_helpdesk_compat.mail_template_new_ticket_itk"},
    {"name": "in Bearbeitung", "sequence": 20, "fold": False, "closed": False, "unattended": False},
    {"name": "on Hold", "sequence": 30, "fold": True, "closed": False, "unattended": False},
    {"name": "Geschlossen/Behoben", "sequence": 40, "fold": False, "closed": True, "unattended": False},
    {"name": "an Partner weitergeleitet", "sequence": 50, "fold": False, "closed": False, "unattended": False},
    {"name": "Verrechnung mit Kunde geklärt", "sequence": 60, "fold": True, "closed": True, "unattended": False},
]


def _create_itk_stages(env):
    Stage = env["helpdesk.ticket.stage"]
    all_existing = Stage.with_context(active_test=False).search([])
    if all_existing:
        all_existing.write({"active": False})
        _logger.info("Deactivated %d existing stages", len(all_existing))
    mail_template = env.ref("itk_helpdesk_compat.mail_template_new_ticket_itk", raise_if_not_found=False)
    for stage_data in ITK_STAGES:
        vals = dict(stage_data)
        xmlid = vals.pop("mail_template_xmlid", None)
        if xmlid and mail_template:
            vals["mail_template_id"] = mail_template.id
        existing = Stage.with_context(active_test=False).search([("name", "=", vals["name"])], limit=1)
        if existing:
            existing.write(vals)
            existing.write({"active": True})
            _logger.info("Updated stage: %s", vals["name"])
        else:
            Stage.create(vals)
            _logger.info("Created stage: %s", vals["name"])


def post_init_hook(env):
    _create_itk_stages(env)
