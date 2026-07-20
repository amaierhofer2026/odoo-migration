"""Portal controller overrides for ITK helpdesk compatibility."""

from odoo import http
from odoo.http import request


class ITKHelpdeskPortal(http.Controller):

    def _get_dynamic_field_values(self, sub_category_id, ticket=None):
        if not sub_category_id:
            return []
        sub_category = request.env["helpdesk.ticket.category"].browse(int(sub_category_id))
        if not sub_category.exists():
            return []
        field_defs = request.env["itk.helpdesk.subcategory.field"].search([
            ("sub_category_id", "=", sub_category.id),
            ("show_in_portal", "=", True),
        ], order="sequence, id")
        result = []
        for fdef in field_defs:
            value = ""
            if ticket:
                existing = request.env["itk.helpdesk.subcategory.field.value"].search([
                    ("ticket_id", "=", ticket.id), ("field_id", "=", fdef.id),
                ], limit=1)
                if existing:
                    value = existing.get_value()
            result.append({"field_def": fdef, "value": value or ""})
        return result

    @http.route("/new/ticket", type="http", auth="user", website=True)
    def create_new_ticket(self, **kw):
        values = self._get_create_new_ticket_values(**kw)
        return request.render("helpdesk_mgmt.portal_create_ticket", values)

    def _get_create_new_ticket_values(self, **kw):
        session_info = request.env["ir.http"].session_info()
        company = request.env.company
        category_model = request.env["helpdesk.ticket.category"]
        domain = [("active", "=", True), ("show_in_portal", "=", True)]
        all_categories = (
            category_model.with_company(company.id).search(domain)
            if company.helpdesk_mgmt_portal_select_category else category_model
        )
        main_categories = all_categories.filtered(lambda c: not c.parent_id)
        subcategories = all_categories.filtered(lambda c: c.parent_id)
        sub_category_id = kw.get("sub_category_id")
        dynamic_field_values = self._get_dynamic_field_values(sub_category_id)
        teams = (
            request.env["helpdesk.ticket.team"].with_company(company.id)
            .search([("active", "=", True), ("show_in_portal", "=", True)])
            if company.helpdesk_mgmt_portal_select_team else False
        )
        return {
            "categories": all_categories,
            "main_categories": main_categories,
            "subcategories": subcategories,
            "category_id": kw.get("category_id"),
            "sub_category_id": sub_category_id,
            "dynamic_field_values": dynamic_field_values,
            "teams": teams,
            "email": request.env.user.email,
            "name": request.env.user.name,
            "ticket_team_id_required": company.helpdesk_mgmt_portal_team_id_required,
            "ticket_category_id_required": company.helpdesk_mgmt_portal_category_id_required,
            "max_upload_size": session_info["max_file_upload_size"],
        }

    @http.route("/submitted/ticket", type="http", auth="user", website=True, csrf=True)
    def submit_ticket(self, **kw):
        import base64, werkzeug
        from odoo.tools import plaintext2html

        category = request.env["helpdesk.ticket.category"].browse(int(kw.get("category") or 0))
        company = category.company_id or request.env.company
        vals = {
            "company_id": company.id,
            "category_id": category.id,
            "description": plaintext2html(kw.get("description")),
            "name": kw.get("subject"),
            "attachment_ids": False,
            "channel_id": request.env.ref("helpdesk_mgmt.helpdesk_ticket_channel_web", False).id,
            "partner_id": request.env.user.partner_id.id,
            "partner_name": request.env.user.partner_id.name,
            "partner_email": request.env.user.partner_id.email,
            "user_id": False,
        }
        if kw.get("sub_category_id"):
            vals["sub_category_id"] = int(kw["sub_category_id"])
        if company.helpdesk_mgmt_portal_select_team and kw.get("team"):
            team = request.env["helpdesk.ticket.team"].sudo().search([
                ("id", "=", int(kw.get("team"))), ("show_in_portal", "=", True),
            ])
            vals["team_id"] = team.id
        team = request.env["helpdesk.ticket.team"].browse(vals.get("team_id", 0))
        vals["stage_id"] = team._get_applicable_stages()[:1].id

        new_ticket = request.env["helpdesk.ticket"].sudo().create(vals)
        new_ticket.message_subscribe(partner_ids=request.env.user.partner_id.ids)

        if new_ticket.sub_category_id:
            field_defs = request.env["itk.helpdesk.subcategory.field"].search([
                ("sub_category_id", "=", new_ticket.sub_category_id.id),
                ("show_in_portal", "=", True),
            ])
            for fdef in field_defs:
                field_key = f"dyn_field_{fdef.id}"
                if field_key in kw:
                    raw_value = kw[field_key]
                    value_vals = {"ticket_id": new_ticket.id, "field_id": fdef.id}
                    if fdef.field_type == "integer":
                        try: value_vals["value_integer"] = int(raw_value) if raw_value else 0
                        except ValueError: value_vals["value_integer"] = 0
                    elif fdef.field_type == "float":
                        try: value_vals["value_float"] = float(raw_value) if raw_value else 0.0
                        except ValueError: value_vals["value_float"] = 0.0
                    elif fdef.field_type == "date":
                        value_vals["value_date"] = raw_value or False
                    elif fdef.field_type == "boolean":
                        value_vals["value_boolean"] = raw_value == "on"
                    else:
                        field_map = {"char": "value_char", "text": "value_text", "selection": "value_selection"}
                        value_vals[field_map.get(fdef.field_type, "value_char")] = raw_value or ""
                    request.env["itk.helpdesk.subcategory.field.value"].sudo().create(value_vals)

        if kw.get("attachment"):
            for c_file in request.httprequest.files.getlist("attachment"):
                data = c_file.read()
                if c_file.filename:
                    request.env["ir.attachment"].sudo().create({
                        "name": c_file.filename, "datas": base64.b64encode(data),
                        "res_model": "helpdesk.ticket", "res_id": new_ticket.id,
                    })
        return werkzeug.utils.redirect(f"/my/ticket/{new_ticket.id}")
