from odoo import fields, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    # In Odoo 11 gespeicherte Tagesanzahl (Feld number_of_days_temp). Odoo 18
    # berechnet die Dauer aus Zeitraum und Arbeitsplan neu und laesst das Feld
    # nicht schreiben - der Odoo-11-Wert bleibt damit als historischer Beleg
    # erhalten.
    x_o11_number_of_days = fields.Float(
        string="Anzahl der Tage (Odoo 11)",
        readonly=True,
        copy=False,
        help="Tagesanzahl wie in Odoo 11 gespeichert. Dient dem Abgleich mit dem "
             "Produktivsystem; die Dauer in Odoo 18 wird aus Zeitraum und "
             "Arbeitsplan berechnet.",
    )
