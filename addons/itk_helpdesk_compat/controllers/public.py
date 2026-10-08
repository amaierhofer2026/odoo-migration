"""Oeffentliches Ticket-Formular (ohne Anmeldung) - Entsprechung zum
Odoo-11-Website-Formular "Website (Public)".

Schutz gegen Spam (serverseitig):
1. Honigtopf-Feld "website_url" (muss leer bleiben),
2. Rate-Limit je IP und insgesamt je Stunde (Modell itk.helpdesk.public.submission),
3. reCAPTCHA, sobald in den Einstellungen ein Schluessel hinterlegt ist
   (Odoo-Modul google_recaptcha; ohne Schluessel ist die Pruefung inaktiv,
   genau wie in Odoo 11, wo das Formular reCAPTCHA-Schluessel besass).
"""
from __future__ import annotations

import base64
import logging

import werkzeug

from odoo import http
from odoo.http import request
from odoo.tools import plaintext2html

_logger = logging.getLogger(__name__)

KANAL = "itk_helpdesk_compat.helpdesk_ticket_channel_website_public"


class ITKHelpdeskPublic(http.Controller):

    # ---------------- Hilfsfunktionen ----------------

    @staticmethod
    def _zahl(key, standard):
        wert = request.env["ir.config_parameter"].sudo().get_param(key, standard)
        try:
            return int(wert or standard)
        except (TypeError, ValueError):
            return int(standard)

    def _kategorien(self):
        Kat = request.env["helpdesk.ticket.category"].sudo()
        alle = Kat.with_context(active_test=True).search([
            ("active", "=", True), ("show_in_portal", "=", True),
        ], order="sequence, id")
        return alle.filtered(lambda k: not k.parent_id), alle.filtered(lambda k: k.parent_id)

    def _team(self):
        team_id = self._zahl("itk_helpdesk.public_team_id", 0)
        if team_id:
            team = request.env["helpdesk.ticket.team"].sudo().browse(team_id).exists()
            if team:
                return team
        return request.env["helpdesk.ticket.team"].sudo().search(
            [("active", "=", True)], order="sequence, id", limit=1)

    def _startstufe(self, team):
        if team:
            stufen = team._get_applicable_stages()
            if stufen:
                return stufen[:1]
        return request.env["helpdesk.ticket.stage"].sudo().search(
            [("active", "=", True)], order="sequence, id", limit=1)

    def _ist_gesperrt(self, ip):
        """Rate-Limit: je IP und insgesamt je Stunde."""
        Submission = request.env["itk.helpdesk.public.submission"].sudo()
        grenze_ip = self._zahl("itk_helpdesk.public_rate_limit", 5)
        grenze_gesamt = self._zahl("itk_helpdesk.public_global_limit", 60)
        domain_ip = [("ip", "=", ip), ("blocked", "=", False),
                     ("create_date", ">=", fields_now_minus(hours=1))]
        if Submission.search_count(domain_ip) >= grenze_ip:
            Submission.create({"ip": ip, "blocked": True})
            return True
        domain_gesamt = [("blocked", "=", False),
                         ("create_date", ">=", fields_now_minus(hours=1))]
        return Submission.search_count(domain_gesamt) >= grenze_gesamt

    def _vorlage_werte(self, **kw):
        haupt, unter = self._kategorien()
        Felder = request.env["itk.helpdesk.subcategory.field"].sudo()
        dyn_felder = {}
        for fdef in Felder.search([("show_in_portal", "=", True)], order="sequence, id"):
            dyn_felder.setdefault(fdef.sub_category_id.id, []).append(fdef)
        return {
            "hauptkategorien": haupt,
            "unterkategorien": unter,
            "dyn_felder": dyn_felder,
            "kategorie_id": kw.get("category_id"),
            "unterkategorie_id": kw.get("sub_category_id"),
            "betreff": kw.get("subject") or "",
            "name": kw.get("contact_name") or "",
            "email": kw.get("contact_email") or "",
            "beschreibung": kw.get("description") or "",
            "fehler": kw.get("fehler") or "",
            "erfolg": bool(kw.get("erfolg")),
            "ticket_nummer": kw.get("ticket_nummer") or "",
            "recaptcha_public_key": request.env["ir.config_parameter"].sudo().get_param(
                "recaptcha_public_key", ""),
            "max_upload_size": request.env["ir.http"].get_max_file_upload_size()
            if hasattr(request.env["ir.http"], "get_max_file_upload_size")
            else request.env["ir.http"].session_info().get("max_file_upload_size", 0),
        }

    # ---------------- Routen ----------------

    @http.route(["/support/ticket/new"], type="http", auth="public", website=True,
                sitemap=False, csrf=False)
    def itk_public_form(self, **kw):
        return request.render("itk_helpdesk_compat.public_ticket_form", self._vorlage_werte(**kw))

    @http.route(["/support/ticket/submit"], type="http", auth="public", website=True,
                csrf=True)
    def itk_public_submit(self, **kw):
        ip = request.httprequest.remote_addr or "0.0.0.0"

        # 1. Honigtopf: gefuellt = Bot
        if (kw.get("website_url") or "").strip():
            _logger.info("Helpdesk-Spamschutz: Honigtopf gefuellt (%s)", ip)
            return request.render("itk_helpdesk_compat.public_ticket_form",
                                  self._vorlage_werte(erfolg=True))

        # 2. Pflichtfelder
        fehler = ""
        if not (kw.get("subject") or "").strip():
            fehler = "Bitte einen Betreff angeben."
        elif not (kw.get("description") or "").strip():
            fehler = "Bitte eine Beschreibung angeben."
        elif not (kw.get("contact_email") or "").strip():
            fehler = "Bitte eine E-Mail-Adresse angeben."

        # 3. reCAPTCHA (inaktiv ohne hinterlegten Schluessel)
        if not fehler:
            try:
                if not request.env["ir.http"]._verify_request_recaptcha_token(
                        "itk_helpdesk_public_ticket"):
                    fehler = "Die Spam-Pruefung ist fehlgeschlagen. Bitte erneut versuchen."
            except Exception as exc:  # noqa: BLE001
                _logger.info("Helpdesk-Spamschutz: reCAPTCHA abgelehnt (%s)", exc)
                fehler = "Die Spam-Pruefung ist fehlgeschlagen. Bitte erneut versuchen."

        # 4. Rate-Limit
        if not fehler and self._ist_gesperrt(ip):
            _logger.warning("Helpdesk-Spamschutz: Rate-Limit fuer %s", ip)
            fehler = ("Es wurden zu viele Anfragen in kurzer Zeit gestellt. "
                      "Bitte spaeter erneut versuchen oder den Support direkt kontaktieren.")

        if fehler:
            werte = self._vorlage_werte(**kw)
            werte["fehler"] = fehler
            return request.render("itk_helpdesk_compat.public_ticket_form", werte)

        ticket = self._erzeuge_ticket(ip, **kw)
        request.env["itk.helpdesk.public.submission"].sudo().create({
            "ip": ip,
            "email": (kw.get("contact_email") or "").strip(),
            "ticket_id": ticket.id,
        })
        self._raeume_auf()
        return request.render("itk_helpdesk_compat.public_ticket_form",
                              dict(self._vorlage_werte(), erfolg=True,
                                   ticket_nummer=ticket.number))

    # ---------------- Ticketanlage ----------------

    def _erzeuge_ticket(self, ip, **kw):
        Kat = request.env["helpdesk.ticket.category"].sudo()
        kategorie = Kat.browse(int(kw.get("category_id") or 0)).exists()
        unterkategorie = Kat.browse(int(kw.get("sub_category_id") or 0)).exists()
        if unterkategorie and unterkategorie.parent_id != kategorie:
            unterkategorie = Kat.browse()
        email = (kw.get("contact_email") or "").strip()
        name = (kw.get("contact_name") or "").strip()
        team = self._team()
        stufe = self._startstufe(team)
        kunde = request.env["res.partner"].sudo().search(
            [("email", "=ilike", email)], limit=2)
        vals = {
            "name": (kw.get("subject") or "").strip()[:120],
            "description": plaintext2html((kw.get("description") or "").strip()),
            "category_id": kategorie.id,
            "sub_category_id": unterkategorie.id,
            "channel_id": request.env.ref(KANAL, raise_if_not_found=False).id,
            "company_id": (kategorie.company_id or request.env.company).id,
            "partner_name": name or (kunde[:1].name if len(kunde) == 1 else ""),
            "partner_email": email,
            "user_id": False,
        }
        if len(kunde) == 1:
            vals["partner_id"] = kunde.id
        if team:
            vals["team_id"] = team.id
            if team.user_id:
                vals["user_id"] = team.user_id.id
        if stufe:
            vals["stage_id"] = stufe.id
        ticket = request.env["helpdesk.ticket"].sudo().with_context(
            itk_kanal="website_public").create(vals)

        # Zusatzfelder der Unterkategorie
        if ticket.sub_category_id:
            Feld = request.env["itk.helpdesk.subcategory.field"].sudo()
            Wert = request.env["itk.helpdesk.subcategory.field.value"].sudo()
            for fdef in Feld.search([
                ("sub_category_id", "=", ticket.sub_category_id.id),
                ("show_in_portal", "=", True),
            ], order="sequence, id"):
                wert = kw.get("dyn_field_%s" % fdef.id)
                if wert in (None, ""):
                    continue
                wert_vals = {"ticket_id": ticket.id, "field_id": fdef.id}
                if fdef.field_type == "integer":
                    try:
                        wert_vals["value_integer"] = int(wert)
                    except ValueError:
                        continue
                elif fdef.field_type == "float":
                    try:
                        wert_vals["value_float"] = float(wert)
                    except ValueError:
                        continue
                elif fdef.field_type == "date":
                    wert_vals["value_date"] = wert
                elif fdef.field_type == "boolean":
                    wert_vals["value_boolean"] = wert in ("on", "1", "true", "True")
                elif fdef.field_type == "text":
                    wert_vals["value_text"] = wert
                elif fdef.field_type == "selection":
                    wert_vals["value_selection"] = wert
                else:
                    wert_vals["value_char"] = wert
                Wert.create(wert_vals)

        # Anhang
        datei = request.httprequest.files.get("attachment")
        if datei and datei.filename:
            request.env["ir.attachment"].sudo().create({
                "name": datei.filename,
                "datas": base64.b64encode(datei.read()),
                "res_model": "helpdesk.ticket",
                "res_id": ticket.id,
            })

        # Kunde als Abonnent, damit er Antworten erhaelt
        if ticket.partner_id:
            ticket.message_subscribe(partner_ids=ticket.partner_id.ids)
        elif email:
            ticket.message_subscribe(partner_ids=request.env["res.partner"].sudo().search(
                [("email", "=ilike", email)], limit=1).ids)
        return ticket

    def _raeume_auf(self):
        request.env["itk.helpdesk.public.submission"].sudo().search([
            ("create_date", "<", fields_now_minus(days=7)),
        ]).unlink()


def fields_now_minus(hours=0, days=0):
    from datetime import datetime, timedelta
    return datetime.now() - timedelta(hours=hours, days=days)
