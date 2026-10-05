# -*- coding: utf-8 -*-
"""Odoo-11-Prozesskette fuer Rechnungen sichtbar machen.

Odoo 11 fuehrte die Rechnung durch die Statuswerte
    Entwurf -> Offen -> Bezahlt -> Abgebrochen
Odoo 18 kennt technisch state (draft/posted/cancel) und payment_state
(not_paid/in_payment/partial/paid/reversed/blocked/invoicing_legacy).

Dieses Feld bildet die Odoo-11-Anzeige ab, ohne die Odoo-18-Logik zu veraendern: es ist ein
berechnetes Anzeigefeld (readonly, nicht gespeichert). Die technischen Werte bleiben unveraendert
und werden zusaetzlich im Feld "Zahlungsstatus" angezeigt.

Fachliches Mapping (Entscheidung Session 123, 05.10.2026):
    draft                                  -> Entwurf
    cancel                                 -> Abgebrochen
    posted + not_paid/partial/in_payment/  -> Offen
             blocked/invoicing_legacy
    posted + paid                          -> Bezahlt
    posted + reversed                      -> Gutgeschrieben (bewusster Odoo-18-Zusatz,
                                              fachlich gleichwertig zu "Bezahlt" bei Rest 0)
"""
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    itk_o11_status = fields.Selection(
        selection=[
            ("draft", "Entwurf"),
            ("open", "Offen"),
            ("paid", "Bezahlt"),
            ("cancelled", "Abgebrochen"),
            ("reversed", "Gutgeschrieben (Odoo 18)"),
        ],
        string="Status",
        compute="_compute_itk_o11_status",
        store=False,
        help="Odoo-11-Prozesskette, abgeleitet aus Status und Zahlungsstatus von Odoo 18 "
             "(nur Anzeige; die Odoo-18-Werte bleiben unveraendert).",
    )

    @api.depends("state", "payment_state")
    def _compute_itk_o11_status(self):
        for move in self:
            if move.state == "cancel":
                move.itk_o11_status = "cancelled"
            elif move.state == "draft":
                move.itk_o11_status = "draft"
            elif move.payment_state == "paid":
                move.itk_o11_status = "paid"
            elif move.payment_state == "reversed":
                # vollstaendig gutgeschrieben: in Odoo 11 "Bezahlt", hier bewusst eigener Wert
                move.itk_o11_status = "reversed"
            else:
                # not_paid, partial, in_payment, blocked, invoicing_legacy
                move.itk_o11_status = "open"
