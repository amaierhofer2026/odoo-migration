from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    sale_merge_draft_invoice = fields.Boolean(
        string="Invoices",
    )
