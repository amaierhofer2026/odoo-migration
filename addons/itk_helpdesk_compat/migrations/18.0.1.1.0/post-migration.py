"""Upgrade auf 18.0.1.1.0 (Helpdesk-Abgleich mit Odoo 11)."""


def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})

    # 1. Hilfeseiten-Platzhalter entfernen.
    #    Odoo 11 hatte "Help Groups"/"Help Pages" (0 Datensaetze, nie genutzt);
    #    Odoo 18 hat keinen Standard-Ersatz. Ein Menue ohne Funktion ist ein
    #    Dummy-Nachbau und wird deshalb entfernt.
    for xmlid in ("itk_helpdesk_compat.menu_helpdesk_config_help",
                  "itk_helpdesk_compat.action_help_page_placeholder"):
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec:
            rec.unlink()

    # 2. Ticketnummer wie in Odoo 11: fortlaufend, ohne Praefix, lueckenlos.
    seq = env.ref("helpdesk_mgmt.helpdesk_ticket_sequence", raise_if_not_found=False)
    if seq:
        seq.write({
            "prefix": "",
            "padding": 0,
            "implementation": "no_gap",
            "name": "Support-Ticket-Nummer (wie Odoo 11)",
        })
