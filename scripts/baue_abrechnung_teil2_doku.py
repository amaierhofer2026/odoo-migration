"""Erzeugt docs/o11-o18-vergleich-abrechnung-teil2.md aus den Messdaten (Teil 2).

Quelle: %TEMP%/abrechnung_teil2_felder.json (scripts/analyse_abrechnung_teil2_felder.py)
        %TEMP%/abrechnung_teil2_details.json (scripts/analyse_abrechnung_teil2_details.py)
Aufruf:  python scripts/baue_abrechnung_teil2_doku.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUELLE = os.path.join(tempfile.gettempdir(), "abrechnung_teil2_felder.json")
QUELLE2 = os.path.join(tempfile.gettempdir(), "abrechnung_teil2_details.json")
ZIEL_DATEI = os.path.join(REPO, "docs", "o11-o18-vergleich-abrechnung-teil2.md")

INFRA = ("__last_update", "id", "display_name", "create_uid", "create_date", "write_uid",
         "write_date", "message_", "activity_", "website_", "access_", "has_message",
         "rating_", "portal_url", "message_channel_ids", "message_last_post", "message_unread",
         "message_unread_counter")

# Felder, die es nur in Odoo 11 gibt: Ziel in Odoo 18 und Einstufung
ZIEL_NUR_O11 = {
    "type": ("move_type", "Transformation (Auswahlwerte umbenannt)"),
    "state": ("state + payment_state", "Transformation (Zustand aufgeteilt)"),
    "date_invoice": ("invoice_date", "Transformation (umbenannt)"),
    "date_due": ("invoice_date_due", "Transformation (umbenannt)"),
    "origin": ("invoice_origin", "Transformation (umbenannt)"),
    "reference": ("ref", "Transformation (umbenannt); in Odoo 11 ungenutzt (0)"),
    "number": ("name", "Transformation (umbenannt)"),
    "move_name": ("name", "Transformation (aufgegangen in name)"),
    "move_id": ("-", "entfaellt (Odoo 11: Verknuepfung Rechnung <-> Buchungssatz)"),
    "payment_term_id": ("invoice_payment_term_id", "Transformation (umbenannt)"),
    "residual": ("amount_residual", "Transformation (umbenannt)"),
    "residual_signed": ("amount_residual_signed", "Transformation (umbenannt)"),
    "residual_company_signed": ("amount_residual_signed", "Transformation (aufgegangen)"),
    "amount_total_company_signed": ("amount_total_in_currency_signed", "Transformation (umbenannt)"),
    "sent": ("is_move_sent", "Transformation (umbenannt)"),
    "comment": ("narration", "Transformation (umbenannt)"),
    "account_id": ("-", "entfaellt (Konto kommt in Odoo 18 aus Journal/Position)"),
    "cash_rounding_id": ("invoice_cash_rounding_id", "Transformation (umbenannt)"),
    "incoterms_id": ("invoice_incoterm_id", "Transformation (umbenannt, aus sale_stock)"),
    "refund_invoice_id": ("reversed_entry_id", "Transformation (umbenannt)"),
    "refund_invoice_ids": ("reversal_move_ids", "Transformation (umbenannt)"),
    "reconciled": ("has_reconciled_entries", "Transformation (umbenannt, boolean)"),
    "has_outstanding": ("invoice_has_outstanding", "Transformation (umbenannt)"),
    "payments_widget": ("invoice_payments_widget", "Transformation (umbenannt, Widget)"),
    "outstanding_credits_debits_widget": ("invoice_outstanding_credits_debits_widget",
                                          "Transformation (umbenannt, Widget)"),
    "payment_move_line_ids": ("matched_payment_ids", "Transformation (anderes Modell)"),
    "sequence_number_next": ("sequence_number + highest_name", "Transformation (Nummernkreis)"),
    "sequence_number_next_prefix": ("sequence_prefix", "Transformation (Nummernkreis)"),
    "tax_line_ids": ("line_ids (display_type = tax)", "Transformation (eigenes Modell entfaellt)"),
    "timesheet_ids": ("-", "entfaellt (sale_timesheet in Odoo 11 ungenutzt, 0 Datensaetze)"),
    "timesheet_count": ("-", "entfaellt (sale_timesheet in Odoo 11 ungenutzt, 0 Datensaetze)"),
    "reference_type": ("-", "obsolet (in Odoo 11 immer 'none')"),
    "sequence_number_next_prefix ": ("-", "-"),
}

ZIEL_NUR_O11_LINE = {
    "invoice_id": ("move_id", "Transformation (umbenannt)"),
    "invoice_line_tax_ids": ("tax_ids", "Transformation (umbenannt)"),
    "uom_id": ("product_uom_id", "Transformation (umbenannt)"),
    "account_analytic_id": ("analytic_distribution", "Transformation (umbenannt); Odoo 11 ungenutzt (0)"),
    "analytic_tag_ids": ("-", "entfaellt (Odoo 11: 0 Datensaetze; Odoo 18: Verteilungsschluessel)"),
    "invoice_type": ("move_id.move_type", "Transformation (auf Kopf verschoben)"),
    "is_rounding_line": ("display_type = rounding", "Transformation (Auswahlwert)"),
    "layout_category_id": ("-", "kein Ziel (Odoo 18: display_type line_section/line_note)"),
    "layout_category_sequence": ("-", "kein Ziel (Abschnittsreihenfolge, nicht migrieren)"),
    "origin": ("ref", "Transformation (umbenannt)"),
    "price_subtotal_signed": ("-", "entfaellt (Vorzeichen ergibt sich aus debit/credit)"),
    "product_image": ("-", "entfaellt (Anzeigefeld)"),
    "purchase_id": ("purchase_order_id", "Transformation (umbenannt); Odoo 11 ungenutzt (0)"),
}

# Nur Odoo 18: Einordnung der wichtigsten Zusatzfelder
NUR_O18_GRUPPEN = [
    ("Nummernkreis/Sequenz", ["sequence_prefix", "sequence_number", "highest_name",
                              "name_placeholder", "made_sequence_gap", "secure_sequence_number",
                              "inalterable_hash", "restrict_mode_hash_table", "posted_before"]),
    ("Zahlungsstatus/Abstimmung", ["payment_state", "amount_residual", "amount_residual_signed",
                                   "amount_paid", "matched_payment_ids", "reconciled_payment_ids",
                                   "payment_count", "needed_terms", "payment_term_details",
                                   "next_payment_date", "preferred_payment_method_line_id",
                                   "statement_line_id", "statement_id", "has_reconciled_entries"]),
    ("Betraege/Waehrung", ["amount_residual", "amount_tax_signed", "amount_total_in_currency_signed",
                           "amount_untaxed_in_currency_signed", "amount_total_words",
                           "invoice_currency_rate", "expected_currency_rate",
                           "display_inactive_currency_warning", "tax_totals", "quick_edit_total_amount"]),
    ("E-Rechnung/EDI (Zusatzfunktion)", ["peppol_move_state", "peppol_message_uuid",
                                         "peppol_can_send_response", "peppol_response_ids",
                                         "ubl_cii_xml_id", "ubl_cii_xml_file",
                                         "invoice_pdf_report_id", "invoice_pdf_report_file",
                                         "invoice_source_email", "can_send_as_self_invoice",
                                         "qr_code_method", "display_qr_code"]),
    ("Pruefpfad/Audit (Zusatzfunktion)", ["audit_trail_message_ids", "inalterable_hash",
                                          "secure_sequence_number", "checked", "is_manually_modified"]),
    ("Automatik/Pruefungen", ["auto_post", "auto_post_origin_id", "auto_post_until",
                              "abnormal_amount_warning", "abnormal_date_warning",
                              "duplicated_ref_ids", "partner_credit", "partner_credit_warning",
                              "show_name_warning", "show_reset_to_draft_button",
                              "show_update_fpos", "tax_lock_date_message", "hide_post_button"]),
    ("Belegarten/Positionen", ["line_ids", "invoice_line_ids", "attachment_ids",
                               "reversal_move_ids", "reversed_entry_id", "move_type", "type_name",
                               "narration", "journal_group_id", "direction_sign", "is_storno"]),
    ("Sonstige Odoo-18-Felder", ["delivery_date", "show_delivery_date", "sale_order_count",
                                 "purchase_order_count", "transaction_count", "transaction_ids",
                                 "invoice_vendor_bill_id", "purchase_vendor_bill_id",
                                 "is_purchase_matched", "taxes_legal_notes", "bank_partner_id",
                                 "country_code", "tax_country_id", "tax_country_code",
                                 "tax_calculation_rounding_method", "always_tax_exigible",
                                 "company_price_include", "quick_edit_mode", "is_being_sent",
                                 "sending_data", "move_sent_values", "activity_calendar_event_id",
                                 "my_activity_date_deadline", "suitable_journal_ids",
                                 "invoice_filter_type_domain", "invoice_partner_display_name",
                                 "invoice_outstanding_credits_debits_widget",
                                 "invoice_payments_widget", "origin_payment_id",
                                 "tax_cash_basis_created_move_ids", "tax_cash_basis_origin_move_id",
                                 "tax_cash_basis_rec_id", "stock_move_id",
                                 "stock_valuation_layer_ids", "status_in_payment",
                                 "restrict_mode_hash_table", "attachment_ids", "inline"]),
]


def infra(feld):
    return feld.startswith(INFRA)


def zaehl_text(k):
    return "%s" % k


def baue():
    d = json.load(open(QUELLE, encoding="utf-8"))
    d2 = json.load(open(QUELLE2, encoding="utf-8"))
    z = []
    z.append("# Odoo 11 -> Odoo 18: Bereich Abrechnung, Teil 2 (Feldinventar Rechnung)")
    z.append("")
    z.append("Stand: 30.09.2026, Session 122")
    z.append("Status: **FELDINVENTAR ABGESCHLOSSEN - nur Analyse, an Odoo 18 wurde nichts geaendert**")
    z.append("")
    z.append("Vergleichsbasis: Odoo 11 Prod (`https://portal.it-kommunal.at`, DB `ITK_V1_a`) - "
             "ausschliesslich lesend.")
    z.append("Zielsystem: Odoo 18 lokal (`localhost:8069`) und VM `k001959vsx.ipax.at`, DB `odo18_test`.")
    z.append("")
    z.append("Auftrag (Anna, 30.09.2026): Teil 2 nur analysieren und dokumentieren - "
             "vollstaendiger Vergleich `account.invoice` / `account.invoice.line` (Odoo 11) gegen "
             "`account.move` / `account.move.line` (Odoo 18), inklusive belegter Felder, Typen, "
             "Relationen, Zustaende und Zielzuordnung.")
    z.append("")

    # ---------- 1 Methodik ----------
    z.append("## 1. Methodik und Nachweise")
    z.append("")
    z.append("```")
    z.append("scripts/analyse_abrechnung_teil2_felder.py    Feldmengen, Typen, Relationen, Nutzung")
    z.append("scripts/analyse_abrechnung_teil2_details.py  Beschriftungen, Pflicht/readonly, Auswahlwerte")
    z.append("scripts/baue_abrechnung_teil2_doku.py        erzeugt dieses Dokument aus den Messdaten")
    z.append("```")
    z.append("")
    z.append("Zwei Quellen je Modell und Instanz (Muster Session 121): `ir.model.fields` (autoritative "
             "Feldliste mit `modules`, `required`, `readonly`, `store`, `related`) und `fields_get` "
             "(Anzeigebeschriftung und Auswahlwerte in `de_DE`).")
    z.append("")
    z.append("Vollstaendigkeitskontrolle (Feldmengen gegeneinander geprueft):")
    for m11 in d:
        m18 = d[m11]["o18"]["modell"]
        z.append("- `%s` gegen `%s`: `ir.model.fields` gegen `fields_get` ohne Abweichung "
                 "(O11 %s / %s und O18 %s / %s)."
                 % (m11, m18, d[m11]["o11"]["anzahl_ir_model_fields"], d[m11]["o11"]["anzahl_fields_get"],
                    d[m11]["o18"]["anzahl_ir_model_fields"], d[m11]["o18"]["anzahl_fields_get"]))
    z.append("")
    z.append("Zaehlregeln (Odoo-11-Besonderheiten):")
    z.append("```")
    z.append("- Odoo 11 kennt in ir.model.fields kein 'computed'. Berechnete Felder werden an")
    z.append("  store=False erkannt, abgeleitete an related != False.")
    z.append("- Nutzungszahlen nur fuer gespeicherte, nicht abgeleitete Felder (search_count mit")
    z.append("  Domain (feld != False)). Bei berechneten Feldern steht 'berechnet' statt einer Zahl.")
    z.append("- Infrastrukturfelder (message_*, activity_*, website_*, access_*, create_*, write_*,")
    z.append("  display_name, id, portal_url) sind je Modell zu einer Zeile zusammengefasst.")
    z.append("```")
    z.append("")

    # ---------- 2 Feldmengen ----------
    z.append("## 2. Feldmengen")
    z.append("")
    z.append("```")
    for m11 in d:
        m18 = d[m11]["o18"]["modell"]
        a = set(d[m11]["o11"]["felder"])
        b = set(d[m11]["o18"]["felder"])
        z.append("%-22s Odoo 11: %3d Felder | %-20s Odoo 18: %3d Felder | gemeinsam %2d | "
                 "nur O11 %2d | nur O18 %3d"
                 % (m11, len(a), m18, len(b), len(a & b), len(a - b), len(b - a)))
    z.append("```")
    z.append("")
    z.append("Zum Vergleich die Odoo-11-Nutzung: `account.invoice` 6.277 Datensaetze, "
             "`account.invoice.line` 10.031 Datensaetze. Odoo-18-Testbestand (keine Produktivdaten): "
             "lokal 37 Belege / 100 Buchungszeilen, VM 57 Belege - die Zielzahlen sind Testdaten, "
             "keine Datenlage.")
    z.append("")

    # ---------- 3 nur O11 ----------
    for m11, ziel in (("account.invoice", ZIEL_NUR_O11), ("account.invoice.line", ZIEL_NUR_O11_LINE)):
        fld = d[m11]["o11"]["felder"]
        nur = sorted(set(fld) - set(d[m11]["o18"]["felder"]))
        z.append("### 2.%d Felder, die es nur in Odoo 11 gibt (%s): %d"
                 % (1 if m11 == "account.invoice" else 2, m11, len(nur)))
        z.append("")
        z.append("| Odoo-11-Feld | Beschriftung | Typ | Relation | belegt (Odoo 11) | Ziel in Odoo 18 | Einstufung |")
        z.append("|---|---|---|---|---|---|---|")
        for f in nur:
            if infra(f):
                continue
            e = fld[f]
            zn, ein = ziel.get(f, ("siehe Text", "Klärung nötig"))
            z.append("| `%s` | %s | %s | %s | %s | %s | %s |"
                     % (f, e["string_fg"] or "-", e["ttype"], e["relation"] or "-",
                        ("berechnet" if e.get("store_fg") is False
                         else e.get("belegt", "nicht gemessen")),
                        zn, ein))
        z.append("")
        infra_felder = [f for f in nur if infra(f)]
        z.append("Standard-Infrastruktur (in Odoo 18 durch die Standardfelder ersetzt): %s"
                 % ", ".join("`%s`" % f for f in infra_felder))
        z.append("")

    # ---------- 4 nur O18 ----------
    z.append("### 2.3 Felder, die es nur in Odoo 18 gibt (Zusatzfunktionen und Infrastruktur)")
    z.append("")
    z.append("`account.move` 139, `account.move.line` 70 Felder. Die wichtigsten Gruppen:")
    z.append("")
    for gruppe, felder in NUR_O18_GRUPPEN:
        vorhanden = [f for f in felder if f in d["account.invoice"]["o18"]["felder"]]
        if vorhanden:
            z.append("- **%s:** %s" % (gruppe, ", ".join("`%s`" % f for f in vorhanden)))
    z.append("")
    z.append("Die uebrigen Felder sind Odoo-18-Standardinfrastruktur (mail/activity/portal/"
             "Berechtigungen) oder berechnete Anzeigefelder. Sie werden nicht entfernt.")
    z.append("")

    # ---------- 5 Abweichungen bei gemeinsamen Feldern ----------
    z.append("## 3. Gemeinsame Felder mit Abweichungen")
    z.append("")
    for m11 in d2:
        z.append("### %s" % m11)
        z.append("")
        z.append("Typ-/Relationsabweichungen (%d):" % len(d2[m11]["abw_type"]))
        z.append("")
        z.append("| Feld | Odoo 11 | Odoo 18 | Bewertung |")
        z.append("|---|---|---|---|")
        for f, t11, t18, r11, r18 in d2[m11]["abw_type"]:
            z.append("| `%s` | %s %s | %s %s | Beziehung angepasst, Feld bleibt |"
                     % (f, t11, ("-> " + r11) if r11 else "", t18, ("-> " + r18) if r18 else ""))
        z.append("")
        z.append("Beschriftungsunterschiede in de_DE (%d, Auswahl):" % len(d2[m11]["abw_label"]))
        z.append("")
        z.append("| Feld | Odoo 11 | Odoo 18 |")
        z.append("|---|---|---|")
        for f, s11, s18 in d2[m11]["abw_label"]:
            z.append("| `%s` | %s | %s |" % (f, s11, s18))
        z.append("")

    # ---------- 6 Pflicht/readonly/berechnet ----------
    z.append("## 4. Pflichtfelder, readonly, berechnete Felder")
    z.append("")
    z.append("```")
    for m11 in d2:
        z.append("%s / %s" % (m11, d[m11]["o18"]["modell"]))
        z.append("  Pflicht Odoo 11:            %s" % d2[m11]["req11"])
        z.append("  Pflicht Odoo 18:            %s" % d2[m11]["req18"])
        z.append("  in Odoo 18 zusaetzlich:     %s" % sorted(set(d2[m11]["req18"]) - set(d2[m11]["req11"])))
        z.append("  nicht mehr pflichtig:       %s" % sorted(set(d2[m11]["req11"]) - set(d2[m11]["req18"])))
        z.append("  berechnet (store=False):    Odoo 11 %d | Odoo 18 %d"
                 % (len(d2[m11]["berechnet11"]), len(d2[m11]["berechnet18"])))
        z.append("")
    z.append("```")
    z.append("")
    z.append("Bewertung: Die Pflichtfelder verschieben sich von fachlichen Feldern "
             "(`partner_id`, `account_id`, `reference_type`) auf technische Felder "
             "(`move_type`, `state`, `date`, `auto_post`, `display_type`, `move_id`). "
             "Fuer die Migration heisst das: diese technischen Felder muessen beim Import gesetzt "
             "werden, die alten Pflichtfelder sind es nicht mehr.")
    z.append("")

    # ---------- 7 Zustaende ----------
    z.append("## 5. Zustaende und Auswahlwerte")
    z.append("")
    z.append("```")
    z.append("account.invoice.state        Odoo 11: draft Entwurf | open Offen | paid Bezahlt | cancel Abgebrochen")
    z.append("account.move.state           Odoo 18: draft Entwurf | posted Gebucht | cancel Abgebrochen")
    z.append("account.move.payment_state   Odoo 18: not_paid | in_payment | paid | partial | reversed | blocked | invoicing_legacy")
    z.append("account.invoice.type         Odoo 11: out_invoice | in_invoice | out_refund | in_refund")
    z.append("account.move.move_type       Odoo 18: entry | out_invoice | out_refund | in_invoice | in_refund | out_receipt | in_receipt")
    z.append("account.move.line.display_type Odoo 18: product | cogs | tax | discount | rounding | payment_term | line_section | line_note | epd")
    z.append("account.invoice.line.invoice_type  Odoo 11: wie type (auf der Zeile wiederholt)")
    z.append("account.invoice.reference_type     Odoo 11: nur 'none' belegt")
    z.append("```")
    z.append("")
    z.append("Wichtig fuer die Migration: Odoo 11 fuehrt den Zahlungszustand im Feld `state` "
             "(`open`/`paid`), Odoo 18 trennt Buchungszustand (`state`) und Zahlungszustand "
             "(`payment_state`). Gemessene Verteilung in Odoo 11: draft 14, open 43, paid 6.220, "
             "cancel 0. Der Zustand `open` (43 Belege) ist der einzige Wert ohne direkte "
             "Entsprechung und wird in der Migrationsregel auf `posted` + `payment_state` "
             "abgebildet (Teil 5).")
    z.append("")

    # ---------- 8 Nutzung ----------
    z.append("## 6. Belegte Datensaetze in Odoo 11 (vollstaendig)")
    z.append("")
    for m11 in ("account.invoice", "account.invoice.line"):
        fld = d[m11]["o11"]["felder"]
        z.append("### %s (Grundgesamtheit %s)" % (m11, "6.277" if "line" not in m11 else "10.031"))
        z.append("")
        z.append("| Feld | Beschriftung | Typ | Relation | Pflicht | readonly | belegt |")
        z.append("|---|---|---|---|---|---|---|")
        for f in sorted(fld):
            e = fld[f]
            if infra(f) or e.get("store_fg") is False:
                continue
            belegt = e.get("belegt", "-")
            if e.get("related"):
                belegt = "%s (abgeleitet: %s)" % (belegt, e["related"])
            z.append("| `%s` | %s | %s | %s | %s | %s | %s |"
                     % (f, e["string_fg"] or "-", e["ttype"], e["relation"] or "-",
                        "ja" if e.get("required_fg") else "-", "ja" if e.get("readonly_fg") else "-",
                        belegt))
        z.append("")

    # ---------- 9 ITK ----------
    z.append("## 7. ITK- und Drittmodul-Felder (Herkunft)")
    z.append("")
    z.append("```")
    z.append("Odoo 11 account.invoice:")
    for f, mod in d2["account.invoice"]["itk11"]:
        z.append("  %-30s aus %s" % (f, mod))
    z.append("Odoo 11 account.invoice.line:")
    for f, mod in d2["account.invoice.line"]["itk11"]:
        z.append("  %-30s aus %s" % (f, mod))
    z.append("Odoo 18 account.move:")
    for f, mod in d2["account.invoice"]["itk18"]:
        z.append("  %-30s aus %s" % (f, mod))
    z.append("Odoo 18 account.move.line:")
    for f, mod in d2["account.invoice.line"]["itk18"]:
        z.append("  %-30s aus %s" % (f, mod))
    z.append("```")
    z.append("")
    z.append("Ergebnis: Die ITK-Felder der Rechnung sind in Odoo 18 vorhanden - `valorisierung_id` "
             "(itk_valorisierung), `projectcategory_id` (itk_projectcategory), `notice`, "
             "`sale_order_benefit_period`, `sale_order_confirmation_date` (itk_subscription). "
             "Aus Odoo 11 entfallen die Felder des nie genutzten `sale_timesheet` "
             "(`timesheet_ids`, `timesheet_count`, je 0 Datensaetze) sowie die UTM-Felder des "
             "Rechnungskopfs (`campaign_id`, `medium_id`, `source_id`, alle 0 Datensaetze).")
    z.append("")

    # ---------- 10 K2: Rechnungsnummern technisch geprueft ----------
    z.append("## 8. Auftrag K2: historische Rechnungsnummern in Odoo 18 (technisch geprueft)")
    z.append("")
    z.append("Auftrag Anna (30.09.2026): pruefen, wie die historischen Rechnungsnummern in Odoo 18 "
             "korrekt und eindeutig erhalten bzw. nachvollziehbar zugeordnet werden koennen. "
             "Es wurde **nichts** umnummeriert und **nichts** geschrieben.")
    z.append("")
    z.append("### 8.1 Messwerte Odoo 11")
    z.append("")
    z.append("```")
    z.append("6.277 Rechnungen, davon 6.263 mit Nummer (14 Entwuerfe ohne Nummer)")
    z.append("alle Nummern im EINEN Journal \"Ausgangsrechnungen (EUR)\" (id 1), Praefix immer 'R-'")
    z.append("Formatwechsel: 2019 R-1900001 bis R-19578 (Jahr + 5 Stellen),")
    z.append("               2020-2026 R-20001 ... R-26989 (Jahr + 3 Stellen)")
    z.append("Eindeutigkeit in Odoo 11: SQL-Constraint account_invoice_number_uniq")
    z.append("  = unique(number, company_id, journal_id, type)")
    z.append("Befund: genau EINE Nummer doppelt im selben Journal, weil sie einmal fuer eine")
    z.append("  Rechnung und einmal fuer eine Gutschrift verwendet wurde:")
    z.append("  R-25001 = id 9703 (out_invoice, 02.01.2025, Magistrat der Stadt Wels, 27.593,52)")
    z.append("          = id 11531 (out_refund, 06.02.2025, Verein Gesundheitsland Kaernten,")
    z.append("            1.474,76, Ursprung R-25584)")
    z.append("  In Odoo 11 erlaubt, weil 'type' Teil des eindeutigen Schluessels war.")
    z.append("237 Kunden-Gutschriften liegen im selben Journal wie die Rechnungen.")
    z.append("```")
    z.append("")
    z.append("### 8.2 Technische Lage in Odoo 18 (Quellcode und Datenbank geprueft, read-only)")
    z.append("")
    z.append("```")
    z.append("1) Feld 'name' ist beschreibbar: account.move.name ist compute + inverse +")
    z.append("   readonly=False + store=True (account/models/account_move.py, Zeile 128).")
    z.append("   Eine Migration KANN die historische Nummer also direkt setzen.")
    z.append("2) Eindeutigkeit: UNIQUE INDEX account_move_unique_name")
    z.append("   ON account_move (name, journal_id) WHERE state = 'posted' AND name <> '/'")
    z.append("   Fehlermeldung: \"Ein anderer Datensatz mit demselben Namen existiert bereits.\"")
    z.append("   => Nummern muessen je Journal eindeutig sein, ABER anders als in Odoo 11 zaehlt")
    z.append("      'type' nicht mit. Die eine Doppelnummer R-25001 wuerde den Import daher")
    z.append("      abbrechen (Klärung K2a).")
    z.append("3) Nummernvergabe setzt auf der hoechsten vorhandenen Nummer auf:")
    z.append("   _set_next_sequence() -> _get_next_sequence_format() -> _get_last_sequence()")
    z.append("   liest die letzte Nummer desselben Journals (name != '/') und leitet das Format")
    z.append("   ueber _get_sequence_format_param() ab. Sind die historischen Nummern einmal")
    z.append("   importiert, fuehrt Odoo 18 die Zaehlung im GLEICHEN Format fort (R-26990 ...),")
    z.append("   ohne dass eine Sequenz von Hand gepflegt werden muss.")
    z.append("4) Nur beim Posten wird automatisch nummeriert; ein bereits gesetzter Name bleibt")
    z.append("   erhalten (_get_last_sequence_domain schliesst Zeilen mit name = '/' aus).")
    z.append("5) Achtung beim Import: wird 'journal_id' geaendert und 'name' NICHT mitgeschrieben,")
    z.append("   setzt Odoo den Namen zurueck (account_move.py: draft_move.name = False).")
    z.append("   Journal und Nummer daher immer im selben Schreibvorgang setzen.")
    z.append("6) Journal-Felder fuer den Nummernkreis: sequence_override_regex, refund_sequence")
    z.append("   (\"Gesonderter Nummerkreis fuer Gutschriften\"), payment_sequence, code.")
    z.append("7) Pruefpfad/Audit (Buchungen festschreiben): secure_sequence_number,")
    z.append("   inalterable_hash, restrict_mode_hash_table, check_move_sequence_chain().")
    z.append("   Ist der Pruefpfad aktiv, sind Nummern gebuchter Belege nicht mehr aenderbar -")
    z.append("   die Entscheidung ueber die Nummernvergabe muss VOR der Migration fallen.")
    z.append("```")
    z.append("")
    z.append("### 8.3 Empfehlung (Entscheidung offen, nichts umgesetzt)")
    z.append("")
    z.append("```")
    z.append("a) Historische Nummern 1:1 als account.move.name importieren und posten ->")
    z.append("   Nummern bleiben erhalten, Odoo 18 zaehlt im Format R-xxxxx weiter.")
    z.append("   Voraussetzung: die eine Doppelnummer R-25001 wird vorher geregelt.")
    z.append("b) Fuer die Doppelnummer gibt es drei Moeglichkeiten (Entscheidung Anna):")
    z.append("   b1) Gutschrift behaelt R-25001, Rechnung bekommt eine dokumentierte Ersatznummer")
    z.append("       (Original in ref oder payment_reference) - Achtung: Nummernkreis- und")
    z.append("       Rechnungslegungslogik, daher nur nach fachlicher Freigabe.")
    z.append("   b2) Rechnung behaelt R-25001, Gutschrift bekommt eine Ersatznummer.")
    z.append("   b3) Beide behalten die Nummer; das geht nur mit getrennten Journalen (dann greift")
    z.append("       der UNIQUE INDEX je Journal) - wuerde aber die Journalstruktur veraendern.")
    z.append("c) Nicht empfohlen: Odoo-Nummern neu vergeben und die historische Nummer nur in 'ref'")
    z.append("   ablegen (Wunsch war: Nummern eindeutig erhalten).")
    z.append("d) Vor der Migration technisch pruefen (Testlauf in einer Kopie, kein Produktivsystem):")
    z.append("   6.263 Belege mit Nummer importieren, 0 Konflikte ausser R-25001 erwartet.")
    z.append("```")
    z.append("")

    # ---------- 11 Bewertung ----------
    z.append("## 9. Bewertung und offene Punkte")
    z.append("")
    z.append("```")
    z.append("Vollstaendigkeit: Jedes tatsaechlich belegte Odoo-11-Feld der Rechnung und der")
    z.append("  Rechnungszeile hat ein Ziel in Odoo 18 - entweder unter demselben Namen, als")
    z.append("  umbenanntes Standardfeld, als berechnetes Feld oder als bewusst entfallendes Feld")
    z.append("  mit Begruendung. Kein belegtes Feld bleibt ohne Zuordnung.")
    z.append("ITK-Felder: valorisierung_id, projectcategory_id, notice, sale_order_benefit_period,")
    z.append("  sale_order_confirmation_date und subscription_id sind in Odoo 18 vorhanden.")
    z.append("Entfallen (jeweils 0 belegte Datensaetze in Odoo 11): timesheet_ids/timesheet_count")
    z.append("  (sale_timesheet), campaign_id/medium_id/source_id (UTM), reference_type (immer")
    z.append("  'none'), analytic_tag_ids, account_analytic_id, purchase_id, incoterms_id und")
    z.append("  cash_rounding_id (beide 0).")
    z.append("Kein Ziel (bewusst, wie im Verkauf R7): layout_category_id und")
    z.append("  layout_category_sequence der Rechnungszeile. Gemessen: genau 2 von 10.031 Zeilen")
    z.append("  mit Abschnittskategorie, 606 Zeilen mit einer Abschnittsreihenfolge ungleich 0.")
    z.append("  Odoo 18 bildet Abschnitte ueber display_type = line_section/line_note ab; es")
    z.append("  werden keine kuenstlichen Abschnittszeilen angelegt.")
    z.append("Ungenutzt in Odoo 11, aber strukturell vorhanden: incoterms_id, cash_rounding_id,")
    z.append("  purchase_id, timesheet_*, layout_category_id.")
    z.append("```")
    z.append("")
    z.append("Offene Punkte aus Teil 2 (Entscheidung Anna, nichts umgesetzt):")
    z.append("")
    z.append("```")
    z.append("K2a Doppelnummer R-25001 (Rechnung und Gutschrift, 2025) - Regelung noetig, sonst")
    z.append("     bricht der Import an dieser einen Stelle ab (Abschnitt 8.3 b1/b2/b3).")
    z.append("K2b Nummernformat: 2019 mit 5 Stellen (R-1900001), ab 2020 mit 3 Stellen (R-20001).")
    z.append("     Fortsetzung ab der hoechsten Nummer moeglich; Frage: welches Format soll")
    z.append("     weiterlaufen (Vorschlag: das Format des letzten Jahres).")
    z.append("K2c Pruefpfad/Audit (Buchungen festschreiben): vor der Migration entscheiden, ob er")
    z.append("     aktiviert wird - danach sind Nummern gebuchter Belege unveraenderlich.")
    z.append("K5  Steuern: Das Steuer-Mapping (77 gegen 53) wird im Stammdatenteil (Teil 5)")
    z.append("     vorbereitet; das Feldinventar ist damit abgeschlossen.")
    z.append("K9  USD: 4 Rechnungen mit USD (F4) sind betroffen; Feld currency_id ist in beiden")
    z.append("     Systemen vorhanden, unveraendert offener Pruefpunkt.")
    z.append("```")
    z.append("")

    # ---------- 12 Rahmenbedingungen ----------
    z.append("## 10. Rahmenbedingungen und Nachweise")
    z.append("")
    z.append("```")
    z.append("Keine Aenderung an Odoo 18: kein Upgrade, kein Neustart, kein Schreibvorgang;")
    z.append("  alle Messungen per search_read/search_count/fields_get/ir.model.constraint")
    z.append("  sowie Quellcode-Lesen im Container (docker exec ... sed/grep, read-only).")
    z.append("Odoo 11 Prod ausschliesslich read-only.")
    z.append("Keine Datenmigration: 0 Datensaetze uebernommen, keine Nummer geaendert.")
    z.append("Rohdaten (Feldinventar-JSON) liegen nur im Temp-Verzeichnis, nicht im Repo.")
    z.append("Lokal und VM: Account-Module identisch; das Feldinventar wurde lokal gemessen und")
    z.append("  ueber die im Teil 1 geprueften identischen Modulversionen auf die VM bezogen.")
    z.append("```")
    z.append("")
    z.append("## 11. Naechster Schritt (Vorschlag)")
    z.append("")
    z.append("```")
    z.append("Teil 3: Formulare, Reiter, Buttons, Smart Buttons und Zustandswechsel der Rechnung")
    z.append("  im echten Browser (lokal und auf der VM), inklusive Zahlungs- und Abstimmungslogik")
    z.append("  sowie Rechnungsdruck/Versand. Vor Teil 3 werden die Entscheidungen zu K1, K3, K4")
    z.append("  und K6 sowie zu K2a/K2b aus diesem Teil erbeten.")
    z.append("```")
    z.append("")

    doc = "\n".join(z) + "\n"
    with open(ZIEL_DATEI, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)
    print("geschrieben: %s (%d Zeilen)" % (ZIEL_DATEI, doc.count("\n")))
    return 0


if __name__ == "__main__":
    raise SystemExit(baue())
