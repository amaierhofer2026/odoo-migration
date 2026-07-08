from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        return self.env.ref('itk_reports.action_report_itk_saleorders').report_action(self)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def print_quotation(self):
        self.write({'state': "sent"})
        return self.env.ref('itk_reports.action_report_itk_purchasequotations').report_action(self)


class AccountMove(models.Model):
    _inherit = "account.move"

    def invoice_print(self):
        self.ensure_one()
        return self.env.ref('itk_reports.action_report_itk_invoices').report_action(self)
