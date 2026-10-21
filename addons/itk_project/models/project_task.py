from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    # Odoo 11 fuehrte auf der Aufgabe ein Startdatum (date_start, Datum/Uhrzeit);
    # es war auf allen 598 Aufgaben gesetzt. Odoo 18 hat kein solches Feld.
    # Geprueft und dokumentiert in docs/o11-o18-projekt-vergleich.md (Abschnitt 3/8).
    itk_date_start = fields.Datetime(
        string="Startdatum",
        help="Startdatum der Aufgabe. Entspricht dem Odoo-11-Feld 'Starting Date'.",
    )

    # Prioritaet: die technischen Werte von Odoo 18 (0/1) bleiben unveraendert,
    # nur die sichtbaren Bezeichnungen folgen der Odoo-11-Fachlogik
    # (Odoo 11: Niedrig / Normal; Odoo 18 standardmaessig Niedrig / Hoch).
    priority = fields.Selection(
        selection=[("0", "Niedrig"), ("1", "Normal")],
        string="Priorität",
        default="0",
    )
