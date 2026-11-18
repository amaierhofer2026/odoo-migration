# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class ResPartnerCategory(models.Model):
    _inherit = "res.partner.category"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class ProductTemplate(models.Model):
    _inherit = "product.template"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class ProductProduct(models.Model):
    _inherit = "product.product"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class ProductCategory(models.Model):
    _inherit = "product.category"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class SaleOrder(models.Model):
    _inherit = "sale.order"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


# --- CRM (Session 145) ------------------------------------------------------
# Anker auf CRM-Stammdaten und -Vorgaengen. crm.tag wird auch vom Verkauf
# verwendet (sale.order.tag_ids); der Anker macht beide Migrationen idempotent.


class CrmLead(models.Model):
    _inherit = "crm.lead"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class CrmStage(models.Model):
    _inherit = "crm.stage"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class CrmTeam(models.Model):
    _inherit = "crm.team"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class CrmTag(models.Model):
    _inherit = "crm.tag"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class CrmLostReason(models.Model):
    _inherit = "crm.lost.reason"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class UtmSource(models.Model):
    _inherit = "utm.source"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class UtmCampaign(models.Model):
    _inherit = "utm.campaign"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class UtmMedium(models.Model):
    _inherit = "utm.medium"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class MailActivityType(models.Model):
    _inherit = "mail.activity.type"
    itk_o11_id = fields.Integer(string="Odoo-11-ID", index=True, copy=False)


class MailMessage(models.Model):
    """Anker fuer die Chatter-Migration (nur fachliche Nachrichten)."""
    _inherit = "mail.message"
    itk_o11_msg_id = fields.Integer(string="Odoo-11-Nachrichten-ID", index=True, copy=False)


class IrAttachment(models.Model):
    """Anker fuer die Anhang-Migration."""
    _inherit = "ir.attachment"
    itk_o11_att_id = fields.Integer(string="Odoo-11-Anhang-ID", index=True, copy=False)


class MailActivity(models.Model):
    """Anker fuer die Aktivitaetsmigration."""
    _inherit = "mail.activity"
    itk_o11_activity_id = fields.Integer(string="Odoo-11-Aktivitaets-ID", index=True,
                                         copy=False)
