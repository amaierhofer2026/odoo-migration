from odoo import fields, models


class ITKHelpdeskSubcategoryField(models.Model):
    _name = "itk.helpdesk.subcategory.field"
    _description = "Helpdesk Subcategory Dynamic Field"
    _order = "sequence, id"

    name = fields.Char(string="Buchungstext", required=True, translate=True)
    sub_category_id = fields.Many2one(
        comodel_name="helpdesk.ticket.category",
        string="Unterkategorie",
        required=True,
        ondelete="cascade",
        domain="[('parent_id', '!=', False)]",
    )
    field_type = fields.Selection(
        selection=[
            ("char", "Textfeld"),
            ("text", "Mehrzeiliges Textfeld"),
            ("integer", "Zahl (ganzzahlig)"),
            ("float", "Zahl (Dezimal)"),
            ("date", "Datum"),
            ("boolean", "Ja/Nein"),
            ("selection", "Auswahlfeld"),
        ],
        string="Typ",
        default="char",
        required=True,
    )
    selection_options = fields.Text(
        string="Auswahloptionen",
        help="Eine Option pro Zeile",
    )
    required = fields.Boolean(string="Pflichtfeld")
    help_text = fields.Char(string="Hilfetext")
    show_in_portal = fields.Boolean(string="Im Portal anzeigen", default=True)
    show_in_internal = fields.Boolean(string="Im Backend anzeigen", default=True)
    sequence = fields.Integer(string="Reihenfolge", default=10)
