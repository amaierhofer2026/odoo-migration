from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    itk_o11_payment_number = fields.Char(
        string="Odoo-11-Zahlungsnummer",
        copy=False,
        index=True,
        tracking=True,
        help="Ursprüngliche Zahlungsnummer aus Odoo 11 (z. B. CUST.IN/2026/1061). Nur zur "
             "historischen Nachvollziehbarkeit; die laufende Odoo-18-Nummer steht im Feld Nummer.",
    )
