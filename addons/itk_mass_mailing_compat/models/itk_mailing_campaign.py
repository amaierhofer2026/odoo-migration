from odoo import fields, models


class ItkMailingCampaignStage(models.Model):
    _name = "itk.mailing.campaign.stage"
    _description = "Mailingkampagnen-Stufe"
    _order = "sequence, id"

    name = fields.Char(string="Stufe", required=True, translate=True)
    sequence = fields.Integer(string="Reihenfolge", default=10)
    fold = fields.Boolean(string="Gefaltet", default=False)
    x_o11_id = fields.Integer(string="Odoo-11-ID", readonly=True, copy=False, index=True)


class ItkMailingTag(models.Model):
    _name = "itk.mailing.tag"
    _description = "Kampagnen-Tag"
    _order = "name"

    name = fields.Char(string="Tag", required=True)
    color = fields.Integer(string="Farbe", default=0)
    x_o11_id = fields.Integer(string="Odoo-11-ID", readonly=True, copy=False, index=True)


class ItkMailingCampaign(models.Model):
    _name = "itk.mailing.campaign"
    _description = "Mailingkampagne"
    _order = "name"

    name = fields.Char(string="Kampagne", required=True)
    active = fields.Boolean(string="Aktiv", default=True)
    user_id = fields.Many2one("res.users", string="Verantwortlich",
                              default=lambda self: self.env.user)
    stage_id = fields.Many2one("itk.mailing.campaign.stage", string="Stufe",
                               ondelete="restrict", index=True)
    tag_ids = fields.Many2many("itk.mailing.tag", "itk_campaign_tag_rel",
                               "campaign_id", "tag_id", string="Tags")
    company_id = fields.Many2one("res.company", string="Unternehmen",
                                 default=lambda self: self.env.company)

    mailing_ids = fields.One2many("mailing.mailing", "itk_campaign_id", string="Mailings")
    mailing_count = fields.Integer(string="Anzahl Mailings", compute="_compute_mailing_count")

    # Odoo-11-Referenz und historische Kennzahlen
    x_o11_id = fields.Integer(string="Odoo-11-ID", readonly=True, copy=False, index=True)
    x_o11_total_mailings = fields.Integer(string="Mailings (Odoo 11)", readonly=True)
    x_o11_sent = fields.Integer(string="Gesendet (Odoo 11)", readonly=True)
    x_o11_delivered = fields.Integer(string="Zugestellt (Odoo 11)", readonly=True)
    x_o11_opened = fields.Integer(string="Geöffnet (Odoo 11)", readonly=True)
    x_o11_replied = fields.Integer(string="Geantwortet (Odoo 11)", readonly=True)
    x_o11_bounced = fields.Integer(string="Bounces (Odoo 11)", readonly=True)
    x_o11_received_ratio = fields.Integer(string="Zustellquote (Odoo 11)", readonly=True)
    x_o11_opened_ratio = fields.Integer(string="Öffnungsquote (Odoo 11)", readonly=True)
    x_o11_replied_ratio = fields.Integer(string="Antwortquote (Odoo 11)", readonly=True)
    x_o11_clicks_ratio = fields.Integer(string="Klickquote (Odoo 11)", readonly=True)
    x_o11_sent_date = fields.Datetime(string="Sendedatum (Odoo 11)", readonly=True)
    x_o11_unique_ab_testing = fields.Boolean(string="A/B-Test (Odoo 11)", readonly=True)

    def _compute_mailing_count(self):
        for campaign in self:
            campaign.mailing_count = len(campaign.mailing_ids)
