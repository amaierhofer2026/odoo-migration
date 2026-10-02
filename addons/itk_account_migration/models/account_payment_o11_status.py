# -*- coding: utf-8 -*-
"""Odoo-11-Prozesskette fuer Zahlungen sichtbar machen.

Odoo 11 fuehrte die Zahlung durch die Statuswerte
    Entwurf -> Gebucht -> Abgestimmt -> Abgebrochen
Odoo 18 kennt stattdessen die technischen Werte
    draft / in_process / paid / canceled / rejected
und fuehrt die Abstimmung als eigenes Merkmal (is_reconciled, is_matched).

Dieses Feld bildet die Odoo-11-Prozesskette ab, ohne die Odoo-18-Logik zu veraendern:
es ist ein berechnetes Anzeigefeld (readonly), die technischen Werte bleiben unveraendert
und werden zusaetzlich als "Status (Odoo 18)" angezeigt.
"""
from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    itk_o11_status = fields.Selection(
        selection=[
            ("draft", "Entwurf"),
            ("posted", "Gebucht"),
            ("reconciled", "Abgestimmt"),
            ("cancelled", "Abgebrochen"),
            ("rejected", "Abgelehnt (Odoo 18)"),
        ],
        string="Status",
        compute="_compute_itk_o11_status",
        store=False,
        help="Odoo-11-Prozesskette, abgeleitet aus Status und Abstimmung von Odoo 18 "
             "(nur Anzeige; die Odoo-18-Werte bleiben unveraendert).",
    )

    @api.depends("state", "is_reconciled", "is_matched")
    def _compute_itk_o11_status(self):
        for zahlung in self:
            if zahlung.state == "canceled":
                wert = "cancelled"
            elif zahlung.state == "rejected":
                wert = "rejected"
            elif zahlung.state == "draft":
                wert = "draft"
            elif zahlung.state == "paid" or zahlung.is_reconciled or zahlung.is_matched:
                wert = "reconciled"
            else:
                wert = "posted"
            zahlung.itk_o11_status = wert
