from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MailingMailing(models.Model):
    _inherit = "mailing.mailing"

    # ---------------------------------------------------------------- Odoo 11
    x_o11_id = fields.Integer(string="Odoo-11-ID", readonly=True, copy=False, index=True)
    x_o11_name = fields.Char(string="Bezeichnung (Odoo 11)", readonly=True, copy=False)
    x_o11_source = fields.Char(string="Quelle (Odoo 11)", readonly=True, copy=False,
                               help="utm.source-Name aus Odoo 11. In Odoo 18 tragen alle "
                                    "uebernommenen Mailings die Quelle 'Odoo 11'.")
    x_o11_schedule_date = fields.Datetime(
        string="Geplantes Sendedatum (Odoo 11)", readonly=True, copy=False,
        help="Historischer Planungstermin aus Odoo 11. Bewusst NICHT in "
             "schedule_date uebernommen, damit kein Versand ausgeloest wird.")
    itk_campaign_id = fields.Many2one(
        "itk.mailing.campaign", string="Kampagne (Odoo 11)",
        ondelete="set null", index=True)

    # Historische Kennzahlen aus Odoo 11. Odoo 18 berechnet seine eigenen
    # Kennzahlen aus mailing.trace; diese Felder bleiben unveraendert und
    # sind nur lesbar.
    x_o11_sent = fields.Integer(string="Gesendet (Odoo 11)", readonly=True)
    x_o11_delivered = fields.Integer(string="Zugestellt (Odoo 11)", readonly=True)
    x_o11_opened = fields.Integer(string="Geöffnet (Odoo 11)", readonly=True)
    x_o11_replied = fields.Integer(string="Geantwortet (Odoo 11)", readonly=True)
    x_o11_bounced = fields.Integer(string="Bounces (Odoo 11)", readonly=True)
    x_o11_failed = fields.Integer(string="Fehlgeschlagen (Odoo 11)", readonly=True)
    x_o11_total = fields.Integer(string="Empfänger gesamt (Odoo 11)", readonly=True)
    x_o11_contact_ab_pc = fields.Integer(string="A/B-Test Prozent (Odoo 11)", readonly=True)

    # ------------------------------------------------------- Versandsperre
    def _itk_historical_guard(self):
        """Historische Odoo-11-Mailings duerfen nie wieder versendet werden."""
        historisch = self.filtered(lambda m: m.x_o11_id)
        if historisch:
            raise UserError(_(
                "Historische Mailings aus Odoo 11 dürfen nicht erneut versendet werden: %s"
            ) % ", ".join(historisch.mapped("subject")))

    def action_send_mail(self, res_ids=None):
        self._itk_historical_guard()
        return super().action_send_mail(res_ids=res_ids)

    def action_put_in_queue(self):
        self._itk_historical_guard()
        return super().action_put_in_queue()

    def action_launch(self):
        self._itk_historical_guard()
        return super().action_launch()

    def action_schedule(self):
        self._itk_historical_guard()
        return super().action_schedule()

    def action_set_sending(self):
        self._itk_historical_guard()
        return super().action_set_sending()

    @api.model_create_multi
    def create(self, vals_list):
        # Beim Anlegen ueber die Migration darf kein Zustand gesetzt werden,
        # der einen Versand ausloest.
        for vals in vals_list:
            if vals.get("x_o11_id") and vals.get("state") in ("in_queue", "sending"):
                raise UserError(_("Historische Mailings dürfen nicht in die Warteschlange."))
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("state") in ("in_queue", "sending"):
            self._itk_historical_guard()
        return super().write(vals)
