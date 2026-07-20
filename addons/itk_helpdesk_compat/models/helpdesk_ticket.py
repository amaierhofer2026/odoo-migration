import json

from odoo import _, api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    sub_category_id = fields.Many2one(
        comodel_name="helpdesk.ticket.category",
        string="Subcategory",
        domain="[('parent_id', '=', category_id)]",
    )
    priority_id = fields.Many2one(
        comodel_name="itk.helpdesk.priority",
        string="Priority",
    )
    dynamic_field_values = fields.Text(
        string="Dynamic Field Values",
        help="JSON blob storing values of subcategory dynamic fields",
    )

    @api.onchange("category_id")
    def _onchange_category_id(self):
        """Reset subcategory when category changes."""
        if self.category_id != self.sub_category_id.parent_id:
            self.sub_category_id = False
            self.dynamic_field_values = False

    def _get_subcategory_fields(self):
        """Return dynamic field definitions for the current subcategory."""
        self.ensure_one()
        if not self.sub_category_id:
            return self.env["itk.helpdesk.subcategory.field"]
        return self.env["itk.helpdesk.subcategory.field"].search(
            [("sub_category_id", "=", self.sub_category_id.id)]
        )

    def _get_dynamic_field_value(self, field_def):
        """Read a single dynamic field value from the JSON blob."""
        self.ensure_one()
        if not self.dynamic_field_values:
            return ""
        try:
            values = json.loads(self.dynamic_field_values)
        except (json.JSONDecodeError, TypeError):
            return ""
        return values.get(str(field_def.id), "")
