from odoo import fields, models, api


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def get_mail_values(self, res_ids):
        """Override to populate partner_ids for account.move mass mailing."""
        res = super().get_mail_values(res_ids)
        if self.model == 'account.move':
            moves = self.env['account.move'].browse(res_ids)
            for move in moves:
                if res.get(move.id) and move.partner_id:
                    res[move.id]['partner_ids'] = [move.partner_id.id]
                    if not res[move.id].get('email_to'):
                        res[move.id]['email_to'] = move.partner_id.email or ''
        return res

    def send_mail(self, auto_commit=False):
        context = self._context
        if context.get('mass_mark_invoice_as_sent') and \
                context.get('default_model') == 'account.move':
            invoices = self.env['account.move'].browse(
                context.get('active_ids', []))
            invoices.is_move_sent = True
        return super().send_mail(auto_commit=auto_commit)
