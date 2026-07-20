from . import models

def post_init_hook(env):
    """Create ITK stages after module installation."""
    Stage = env["helpdesk.ticket.stage"]
    all_existing = Stage.with_context(active_test=False).search([])
    if all_existing:
        all_existing.write({"active": False})
    ITK_STAGES = [
        {"name": "Offen", "sequence": 10, "fold": False, "closed": False, "unattended": True},
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
