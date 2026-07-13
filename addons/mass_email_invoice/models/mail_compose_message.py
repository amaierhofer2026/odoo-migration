from odoo import fields, models, api


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def send_mail(self, auto_commit=False):
        context = self._context
        if context.get('mass_mark_invoice_as_sent') and \
                context.get('default_model') == 'account.move':
            account_move = self.env['account.move']
            invoice_ids = context.get('active_ids')
            invoices = account_move.browse(invoice_ids)
            invoices.is_move_sent = True
        return super().send_mail(auto_commit=auto_commit)
