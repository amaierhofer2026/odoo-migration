from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    # Odoo 11 fuehrt das Studio-Feld x_homeoffice (Boolean, 116 von 196 Zeilen
    # belegt). Odoo 18 kennt kein Homeoffice-Merkmal an der Anwesenheit.
    x_homeoffice = fields.Boolean(string="Home-Office", default=False)
