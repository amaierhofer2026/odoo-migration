"""Kompatibilitaetsschicht Odoo 11 -> Odoo 18 (Session 118, Teil 9).

Odoo 11                         Odoo 18
get_fiscal_position(partner_id) -> _get_fiscal_position(partner)
map_tax(taxes, product, partner)-> map_tax(...) mit abweichender Signatur

Betroffen ist die automatische Rechnungserzeugung der Abos: ohne diese Bruecken bricht der
Cronjob 'generate recurring invoices and payments' mit einem AttributeError ab und rollt die
erzeugte Rechnung wieder zurueck - es entsteht keine Rechnung.
"""
from odoo import models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    def get_fiscal_position(self, partner_id, delivery_id=None):
        """Odoo-11-Signatur auf die Odoo-18-Methode abbilden."""
        partner = (self.env['res.partner'].browse(partner_id)
                   if isinstance(partner_id, int) else partner_id)
        return self._get_fiscal_position(partner)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def message_post_with_view(self, views, **kwargs):
        """Odoo 11: message_post_with_view - Odoo 18: message_post_with_source.

        In Odoo 18 heisst der Parameter fuer die Vorlagenwerte 'render_values' (Odoo 11: 'values').
        """
        if hasattr(self, 'message_post_with_source'):
            if 'values' in kwargs:
                kwargs['render_values'] = kwargs.pop('values')
            return self.message_post_with_source(views, **kwargs)
        return super().message_post_with_view(views, **kwargs)
