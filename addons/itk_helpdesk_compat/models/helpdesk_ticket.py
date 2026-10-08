from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Kanaele nach Odoo 11 (siehe data/helpdesk_channels.xml)
KANAL_MANUAL = "itk_helpdesk_compat.helpdesk_ticket_channel_manual"
KANAL_WEBSITE_PUBLIC = "itk_helpdesk_compat.helpdesk_ticket_channel_website_public"
KANAL_WEBSITE_USER = "itk_helpdesk_compat.helpdesk_ticket_channel_website_user"

KANAL_JE_HERKUNFT = {
    "manual": KANAL_MANUAL,
    "website_public": KANAL_WEBSITE_PUBLIC,
    "website_user": KANAL_WEBSITE_USER,
}


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    # ---- Felder nach Odoo 11 (website_support) ----
    sub_category_id = fields.Many2one(
        comodel_name="helpdesk.ticket.category",
        string="Unterkategorie",
        domain="[('parent_id', '=', category_id)]",
    )
    priority_id = fields.Many2one(
        comodel_name="itk.helpdesk.priority",
        string="Priorität",
    )
    dynamic_field_value_ids = fields.One2many(
        comodel_name="itk.helpdesk.subcategory.field.value",
        inverse_name="ticket_id",
        string="Extra Details",
        copy=False,
    )
    close_comment = fields.Text(
        string="Kommentar bei Abschluss",
    )
    closed_by_id = fields.Many2one(
        comodel_name="res.users",
        string="Geschlossen von",
        readonly=True,
        copy=False,
        help="Benutzer, der das Ticket abgeschlossen hat (Odoo 11: Geschlossen von).",
    )
    support_comment = fields.Text(
        string="Partner Kommentar",
        readonly=True,
    )
    # Odoo 11 verlangte keine Beschreibung am Ticket
    description = fields.Html(required=False, sanitize_style=True)

    # ---- Kanal automatisch aus dem Entstehungsweg ----

    @api.model
    def _itk_kanal(self, schluessel):
        """Liefert den Kanal-Datensatz zu einem Herkunftsschluessel."""
        xmlid = KANAL_JE_HERKUNFT.get(schluessel or "manual", KANAL_MANUAL)
        return self.env.ref(xmlid, raise_if_not_found=False)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "channel_id" in fields_list and not res.get("channel_id"):
            kanal = self._itk_kanal(self.env.context.get("itk_kanal") or "manual")
            if kanal:
                res["channel_id"] = kanal.id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("channel_id") and not self.env.context.get("fetchmail_cron_running"):
                kanal = self._itk_kanal(self.env.context.get("itk_kanal") or "manual")
                if kanal:
                    vals["channel_id"] = kanal.id
        return super().create(vals_list)

    # ---- Ticket-Aktionen ----

    def action_close_ticket(self):
        """Ticket schliessen: Status auf 'Geschlossen/Behoben', Abschlusszeitpunkt setzen."""
        closed_stage = self.env["helpdesk.ticket.stage"].search([
            ("name", "=", "Geschlossen/Behoben"),
        ], limit=1)
        if not closed_stage:
            raise UserError(_(
                "Kein Status 'Geschlossen/Behoben' gefunden. "
                "Bitte im Menü 'Status' anlegen."
            ))
        for ticket in self:
            ticket.write({
                "stage_id": closed_stage.id,
                "closed_date": fields.Datetime.now(),
                "closed_by_id": self.env.user.id,
            })

    def action_reply_ticket(self):
        """Antwort an den Kunden schreiben (Mail-Verfassen-Fenster)."""
        self.ensure_one()
        ctx = {
            "default_model": "helpdesk.ticket",
            "default_res_ids": [self.id],
            "default_composition_mode": "comment",
            "default_use_template": False,
        }
        if self.partner_id:
            ctx["default_partner_ids"] = [self.partner_id.id]
        if self.partner_email:
            ctx["default_email_to"] = self.partner_email
        return {
            "type": "ir.actions.act_window",
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "view_id": self.env.ref("mail.email_compose_message_wizard_form").id,
            "target": "new",
            "context": ctx,
        }

    # ---- Onchange ----

    @api.onchange("category_id")
    def _onchange_category_id(self):
        if self.category_id:
            if self.sub_category_id and self.sub_category_id.parent_id != self.category_id:
                self.sub_category_id = False
                self.dynamic_field_value_ids = [(5, 0, 0)]

    @api.onchange("sub_category_id")
    def _onchange_sub_category_id(self):
        if not self.sub_category_id:
            self.dynamic_field_value_ids = [(5, 0, 0)]
            return
        field_defs = self.env["itk.helpdesk.subcategory.field"].search([
            ("sub_category_id", "=", self.sub_category_id.id),
        ], order="sequence, id")
        self.dynamic_field_value_ids = [(5, 0, 0)]
        for fdef in field_defs:
            self.dynamic_field_value_ids = [(0, 0, {
                "field_id": fdef.id,
            })]

    # ---- Portal helpers ----

    def _get_dynamic_field_values_for_portal(self):
        self.ensure_one()
        if not self.sub_category_id:
            return []
        result = []
        field_defs = self.env["itk.helpdesk.subcategory.field"].search([
            ("sub_category_id", "=", self.sub_category_id.id),
            ("show_in_portal", "=", True),
        ], order="sequence, id")
        value_map = {v.field_id.id: v for v in self.dynamic_field_value_ids}
        for fdef in field_defs:
            val_rec = value_map.get(fdef.id)
            result.append({
                "field_def": fdef,
                "value": val_rec.get_value() if val_rec else "",
            })
        return result
