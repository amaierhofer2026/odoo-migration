# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        return self.env.ref('itk_reports.action_report_itk_saleorders').report_action(self)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def print_quotation(self):
        self.write({'state': "sent"})
        return self.env.ref('itk_reports.action_report_itk_purchasequotations').report_action(self)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def invoice_print(self):
        self.ensure_one()
        self.sent = True
        if self.user_has_groups('account.group_account_invoice'):
            return self.env.ref('itk_reports.action_report_itk_invoices').report_action(self)
        else:
            return self.env.ref('itk_reports.account_invoices_with_payment').report_action(self)