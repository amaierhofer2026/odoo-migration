from odoo import api, fields, models


class EventEvent(models.Model):
    _inherit = "event.event"

    # Odoo-11-Referenzfelder. Sie tragen ausschliesslich technische Kennungen
    # und Zaehlwerte, keine personenbezogenen Daten. Zweck: Idempotenz der
    # Migration und spaetere Nachverknuepfung nach der Kontaktmigration.
    x_o11_id = fields.Integer(
        string="Odoo-11-ID",
        readonly=True,
        copy=False,
        index=True,
        help="Datensatz-ID der Veranstaltung in Odoo 11 (nur Referenz).",
    )
    x_o11_state = fields.Char(
        string="Status (Odoo 11)",
        readonly=True,
        copy=False,
        help="Statuswert der Veranstaltung in Odoo 11: draft, confirm, done, cancel.",
    )
    x_o11_registrations = fields.Integer(
        string="Anmeldungen (Odoo 11)",
        readonly=True,
        copy=False,
        help="Anzahl der Anmeldungen in Odoo 11. Die Teilnehmer selbst werden "
             "erst mit der Kontakt- und Personendatenmigration uebernommen.",
    )
    x_o11_organizer_id = fields.Integer(
        string="Veranstalter (Odoo-11-Kontakt-ID)",
        readonly=True,
        copy=False,
        help="res.partner-ID des Veranstalters in Odoo 11. Der Kontakt selbst "
             "wird nicht uebernommen; das Feld dient der spaeteren "
             "Nachverknuepfung.",
    )
    x_o11_address_id = fields.Integer(
        string="Ort (Odoo-11-Kontakt-ID)",
        readonly=True,
        copy=False,
        help="res.partner-ID des Veranstaltungsortes in Odoo 11. Der Kontakt "
             "selbst wird nicht uebernommen; das Feld dient der spaeteren "
             "Nachverknuepfung.",
    )

    # Odoo 11 fuehrt an der Veranstaltung "Online Event" (is_online, 120 von
    # 122 Datensaetzen) und "Mindestzahl an Teilnehmern" (seats_min, 114
    # Datensaetze). Beide Felder gibt es in Odoo 18 nicht.
    x_is_online = fields.Boolean(
        string="Online-Event",
        default=False,
        help="Odoo-11-Kennzeichen is_online. Odoo 18 leitet 'Online' aus dem "
             "fehlenden Veranstaltungsort ab; das Kennzeichen bleibt als "
             "eigenes Feld erhalten.",
    )
    x_seats_min = fields.Integer(
        string="Mindestzahl an Teilnehmern",
        default=0,
        help="Odoo-11-Feld seats_min (informative Mindestteilnehmerzahl).",
    )

    @api.model
    def _gc_mark_events_done(self):
        """Uebernommene Odoo-11-Veranstaltungen behalten ihren Status.

        Odoo 18 setzt bei jedem Autovacuum-Lauf jede Veranstaltung, deren
        Enddatum vorbei ist, in die Phase "Erledigt" (Kernmethode
        _gc_mark_events_done). Damit wuerde der aus Odoo 11 uebernommene
        Status historischer Veranstaltungen (100 x "Bestaetigt") sofort
        ueberschrieben. Veranstaltungen mit Odoo-11-Referenz bleiben deshalb
        unangetastet; in Odoo 18 neu angelegte Veranstaltungen werden
        weiterhin automatisch auf "Erledigt" gesetzt.
        """
        abgelaufen = self.search([
            ("date_end", "<", fields.Datetime.now()),
            ("stage_id.pipe_end", "=", False),
            ("x_o11_id", "=", False),
        ])
        if abgelaufen:
            abgelaufen.action_set_done()
