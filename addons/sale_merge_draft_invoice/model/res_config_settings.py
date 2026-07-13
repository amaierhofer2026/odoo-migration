from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _description = 'Sale Merge Draft Invoice Settings'

    sale_merge_draft_invoice = fields.Boolean(
        string="Invoices",
        related='company_id.sale_merge_draft_invoice',
        readonly=False,
    )
