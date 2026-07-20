from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ITKHelpdeskSubcategoryFieldValue(models.Model):
    _name = "itk.helpdesk.subcategory.field.value"
    _description = "Helpdesk Subcategory Dynamic Field Value"
    _rec_name = "field_id"

    ticket_id = fields.Many2one(
        comodel_name="helpdesk.ticket",
        string="Ticket",
        required=True,
        ondelete="cascade",
        index=True,
    )
    field_id = fields.Many2one(
        comodel_name="itk.helpdesk.subcategory.field",
        string="Feld",
        required=True,
        ondelete="cascade",
    )
    field_type = fields.Selection(related="field_id.field_type", string="Feldtyp")
    sub_category_id = fields.Many2one(
        related="field_id.sub_category_id",
        string="Unterkategorie",
        store=True,
    )
    value_char = fields.Char(string="Wert (Text)")
    value_text = fields.Text(string="Wert (Mehrzeilig)")
    value_integer = fields.Integer(string="Wert (Ganzzahl)")
    value_float = fields.Float(string="Wert (Dezimal)")
    value_date = fields.Date(string="Wert (Datum)")
    value_boolean = fields.Boolean(string="Wert (Ja/Nein)")
    value_selection = fields.Char(string="Wert (Auswahl)")
    value_display = fields.Char(string="Wert", compute="_compute_value_display")

    @api.depends(
        "field_type", "value_char", "value_text", "value_integer",
        "value_float", "value_date", "value_boolean", "value_selection",
    )
    def _compute_value_display(self):
        for rec in self:
            type_map = {
                "char": rec.value_char,
                "text": rec.value_text,
                "integer": str(rec.value_integer) if rec.value_integer is not None else "",
                "float": str(rec.value_float) if rec.value_float is not None else "",
                "date": str(rec.value_date) if rec.value_date else "",
                "boolean": "Ja" if rec.value_boolean else "Nein",
                "selection": rec.value_selection or "",
            }
            rec.value_display = type_map.get(rec.field_type, "") or ""

    @api.constrains("ticket_id", "field_id")
    def _check_unique_field_per_ticket(self):
        for rec in self:
            existing = self.search([
                ("ticket_id", "=", rec.ticket_id.id),
                ("field_id", "=", rec.field_id.id),
                ("id", "!=", rec.id),
            ])
            if existing:
                raise ValidationError(_(
                    "Das Feld '%s' ist diesem Ticket bereits zugewiesen.",
                    rec.field_id.name,
                ))

    def get_value(self):
        self.ensure_one()
        type_map = {
            "char": self.value_char,
            "text": self.value_text,
            "integer": self.value_integer,
            "float": self.value_float,
            "date": self.value_date,
            "boolean": self.value_boolean,
            "selection": self.value_selection,
        }
        return type_map.get(self.field_type)

    def set_value(self, value):
        self.ensure_one()
        field_name = {
            "char": "value_char",
            "text": "value_text",
            "integer": "value_integer",
            "float": "value_float",
            "date": "value_date",
            "boolean": "value_boolean",
            "selection": "value_selection",
        }.get(self.field_type, "value_char")
        self.write({field_name: value})
