from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    itk_o11_invoice_number = fields.Char(
        string="Odoo-11-Rechnungsnummer",
        copy=False,
        index=True,
        tracking=True,
        help="Ursprüngliche Rechnungsnummer aus Odoo 11. Nur zur historischen Nachvollziehbarkeit "
             "(Entscheidung K2a); die laufende Odoo-18-Nummer steht im Feld Nummer.",
    )
