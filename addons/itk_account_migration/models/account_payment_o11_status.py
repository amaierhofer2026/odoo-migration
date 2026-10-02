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
            ("paid_o18", "Bezahlt (Odoo 18)"),
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
        """Odoo-11-Kette aus den technischen Odoo-18-Werten ableiten.

        Wichtig: "Abgestimmt" wird NUR gezeigt, wenn die Zahlung in Odoo 18 tatsaechlich
        abgestimmt ist (is_reconciled). Ein technischer Zustand "paid" allein genuegt nicht -
        er kann auch ohne vollstaendige Abstimmung mit den Rechnungen vorkommen
        (z.B. nur mit einem Kontoauszug abgeglichen, is_matched ohne is_reconciled).
        Dieser Fall wird als eigener Odoo-18-Zusatzschritt gezeigt, damit nichts falsch
        als "Abgestimmt" erscheint.
        """
        for zahlung in self:
            if zahlung.state == "canceled":
                wert = "cancelled"          # Odoo 11: Abgebrochen
            elif zahlung.state == "rejected":
                wert = "rejected"           # Odoo-18-Zusatz: Abgelehnt
            elif zahlung.state == "draft":
                wert = "draft"              # Odoo 11: Entwurf
            elif zahlung.is_reconciled:
                wert = "reconciled"         # Odoo 11: Abgestimmt (echte Abstimmung)
            elif zahlung.state == "paid":
                wert = "paid_o18"           # Odoo-18-Zusatz: bezahlt, aber nicht abgestimmt
            else:
                wert = "posted"             # Odoo 11: Gebucht
            zahlung.itk_o11_status = wert
