"""Automatischer Bezeichnungs- und Feldmapping-Check fuer den Bereich Abrechnung.

Verbindliche Regel (Anna, 30.09.2026): Hat ein Feld in Odoo 18 fachlich dieselbe Bedeutung wie
ein Feld aus Odoo 11, soll die sichtbare deutsche Bezeichnung in Odoo 18 genauso heissen wie in
Odoo 11. Die internen Odoo-18-Feldnamen bleiben unveraendert.

Das Skript vergleicht je Feldpaar die sichtbare Bezeichnung (fields_get, lang=de_DE) und
schreibt die Mapping-Tabelle
  Odoo-11-Feld -> Odoo-18-Zielfeld -> Odoo-11-Bezeichnung -> Odoo-18-Bezeichnung -> Abweichung
nach docs/o11-o18-abrechnung-labelmapping.md.

Aufruf:
    python scripts/check_abrechnung_labels.py                 # lokal und VM
    python scripts/check_abrechnung_labels.py --instanz lokal  # nur lokal
    python scripts/check_abrechnung_labels.py --nur-abweichungen
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18

# (Odoo-11-Modell, Odoo-11-Feld, Odoo-18-Modell, Odoo-18-Feld, Anmerkung)
MAPPING = [
    # --- Rechnungskopf (account.invoice -> account.move) ---
    ("account.invoice", "partner_id", "account.move", "partner_id", "Kunde"),
    ("account.invoice", "commercial_partner_id", "account.move", "commercial_partner_id", "gewerbliche Einheit"),
    ("account.invoice", "date_invoice", "account.move", "invoice_date", "umbenannt"),
    ("account.invoice", "date_due", "account.move", "invoice_date_due", "umbenannt"),
    ("account.invoice", "date", "account.move", "date", "Buchungsdatum"),
    ("account.invoice", "number", "account.move", "name", "umbenannt (Belegnummer)"),
    ("account.invoice", "reference", "account.move", "ref", "umbenannt, in Odoo 11 ungenutzt"),
    ("account.invoice", "origin", "account.move", "invoice_origin", "umbenannt"),
    ("account.invoice", "comment", "account.move", "narration", "umbenannt"),
    ("account.invoice", "state", "account.move", "state", "Zustand"),
    ("account.invoice", "type", "account.move", "move_type", "umbenannt"),
    ("account.invoice", "company_id", "account.move", "company_id", ""),
    ("account.invoice", "currency_id", "account.move", "currency_id", ""),
    ("account.invoice", "journal_id", "account.move", "journal_id", ""),
    ("account.invoice", "user_id", "account.move", "invoice_user_id", "Verkaeufer"),
    ("account.invoice", "team_id", "account.move", "team_id", "Vertriebskanal"),
    ("account.invoice", "payment_term_id", "account.move", "invoice_payment_term_id", "umbenannt"),
    ("account.invoice", "fiscal_position_id", "account.move", "fiscal_position_id", "Steuerzuordnung"),
    ("account.invoice", "partner_bank_id", "account.move", "partner_bank_id", ""),
    ("account.invoice", "amount_untaxed", "account.move", "amount_untaxed", ""),
    ("account.invoice", "amount_tax", "account.move", "amount_tax", ""),
    ("account.invoice", "amount_total", "account.move", "amount_total", ""),
    ("account.invoice", "amount_untaxed_signed", "account.move", "amount_untaxed_signed", ""),
    ("account.invoice", "amount_total_signed", "account.move", "amount_total_signed", ""),
    ("account.invoice", "amount_total_company_signed", "account.move", "amount_total_in_currency_signed", "umbenannt"),
    ("account.invoice", "residual", "account.move", "amount_residual", "umbenannt"),
    ("account.invoice", "payment_reference", "account.move", "payment_reference", ""),
    ("account.invoice", "notice", "account.move", "notice", "ITK-Feld"),
    ("account.invoice", "projectcategory_id", "account.move", "projectcategory_id", "ITK-Feld"),
    ("account.invoice", "valorisierung_id", "account.move", "valorisierung_id", "ITK-Feld"),
    ("account.invoice", "sent", "account.move", "is_move_sent", "umbenannt"),
    ("account.invoice", "reconciled", "account.move", "has_reconciled_entries", "umbenannt"),
    ("account.invoice", "payment_move_line_ids", "account.move", "matched_payment_ids", "anderes Modell"),
    ("account.invoice", "incoterms_id", "account.move", "invoice_incoterm_id", "umbenannt"),
    ("account.invoice", "cash_rounding_id", "account.move", "invoice_cash_rounding_id", "umbenannt"),
    ("account.invoice", "invoice_line_ids", "account.move", "invoice_line_ids", ""),
    ("account.invoice", "move_name", "account.move", "name", "aufgegangen in name"),
    # --- Rechnungszeile (account.invoice.line -> account.move.line) ---
    ("account.invoice.line", "invoice_id", "account.move.line", "move_id", "umbenannt"),
    ("account.invoice.line", "name", "account.move.line", "name", "Beschreibung"),
    ("account.invoice.line", "quantity", "account.move.line", "quantity", ""),
    ("account.invoice.line", "price_unit", "account.move.line", "price_unit", ""),
    ("account.invoice.line", "discount", "account.move.line", "discount", ""),
    ("account.invoice.line", "price_subtotal", "account.move.line", "price_subtotal", ""),
    ("account.invoice.line", "price_total", "account.move.line", "price_total", ""),
    ("account.invoice.line", "product_id", "account.move.line", "product_id", ""),
    ("account.invoice.line", "uom_id", "account.move.line", "product_uom_id", "umbenannt"),
    ("account.invoice.line", "account_id", "account.move.line", "account_id", ""),
    ("account.invoice.line", "invoice_line_tax_ids", "account.move.line", "tax_ids", "umbenannt"),
    ("account.invoice.line", "purchase_line_id", "account.move.line", "purchase_line_id", ""),
    ("account.invoice.line", "sequence", "account.move.line", "sequence", ""),
    ("account.invoice.line", "company_currency_id", "account.move.line", "company_currency_id", ""),
    ("account.invoice.line", "currency_id", "account.move.line", "currency_id", ""),
    ("account.invoice.line", "partner_id", "account.move.line", "partner_id", ""),
    ("account.invoice.line", "company_id", "account.move.line", "company_id", ""),
    ("account.invoice.line", "projectcategory_id", "account.move.line", "projectcategory_id", "ITK-Feld"),
    ("account.invoice.line", "valorisierung_id", "account.move.line", "valorisierung_id", "ITK-Feld"),
    ("account.invoice.line", "account_analytic_id", "account.move.line", "analytic_distribution", "anderes Modell"),
    # --- Produkte (verkaufbare/einkaufbare Produkte) ---
    ("product.template", "barcode", "product.template", "barcode", ""),
    ("product.product", "barcode", "product.product", "barcode", ""),
    ("product.template", "categ_id", "product.template", "categ_id", ""),
    ("product.product", "categ_id", "product.product", "categ_id", ""),
    ("product.template", "cost_method", "product.template", "cost_method", ""),
    ("product.product", "cost_method", "product.product", "cost_method", ""),
    ("product.template", "description_picking", "product.template", "description_picking", ""),
    ("product.product", "description_picking", "product.product", "description_picking", ""),
    ("product.template", "expense_policy", "product.template", "expense_policy", ""),
    ("product.product", "expense_policy", "product.product", "expense_policy", ""),
    ("product.template", "invoice_policy", "product.template", "invoice_policy", ""),
    ("product.product", "invoice_policy", "product.product", "invoice_policy", ""),
    ("product.template", "is_multi_factor_product", "product.template", "is_multi_factor_product", ""),
    ("product.product", "is_multi_factor_product", "product.product", "is_multi_factor_product", ""),
    ("product.template", "nbr_reordering_rules", "product.template", "nbr_reordering_rules", ""),
    ("product.product", "nbr_reordering_rules", "product.product", "nbr_reordering_rules", ""),
    ("product.template", "orderpoint_ids", "product.template", "orderpoint_ids", ""),
    ("product.product", "orderpoint_ids", "product.product", "orderpoint_ids", ""),
    ("product.template", "outgoing_qty", "product.template", "outgoing_qty", ""),
    ("product.product", "outgoing_qty", "product.product", "outgoing_qty", ""),
    ("product.template", "packaging_ids", "product.template", "packaging_ids", ""),
    ("product.product", "packaging_ids", "product.product", "packaging_ids", ""),
    ("product.template", "partner_ref", "product.template", "partner_ref", ""),
    ("product.product", "partner_ref", "product.product", "partner_ref", ""),
    ("product.template", "product_type_id", "product.template", "product_type_id", ""),
    ("product.product", "product_type_id", "product.product", "product_type_id", ""),
    ("product.template", "product_variant_count", "product.template", "product_variant_count", ""),
    ("product.product", "product_variant_count", "product.product", "product_variant_count", ""),
    ("product.template", "property_account_income_id", "product.template", "property_account_income_id", ""),
    ("product.product", "property_account_income_id", "product.product", "property_account_income_id", ""),
    ("product.template", "property_stock_inventory", "product.template", "property_stock_inventory", ""),
    ("product.product", "property_stock_inventory", "product.product", "property_stock_inventory", ""),
    ("product.template", "property_stock_production", "product.template", "property_stock_production", ""),
    ("product.product", "property_stock_production", "product.product", "property_stock_production", ""),
    ("product.template", "purchase_line_warn", "product.template", "purchase_line_warn", ""),
    ("product.product", "purchase_line_warn", "product.product", "purchase_line_warn", ""),
    ("product.template", "purchase_ok", "product.template", "purchase_ok", ""),
    ("product.product", "purchase_ok", "product.product", "purchase_ok", ""),
    ("product.template", "qty_available", "product.template", "qty_available", ""),
    ("product.product", "qty_available", "product.product", "qty_available", ""),
    ("product.template", "sale_delay", "product.template", "sale_delay", ""),
    ("product.product", "sale_delay", "product.product", "sale_delay", ""),
    ("product.template", "sale_line_warn", "product.template", "sale_line_warn", ""),
    ("product.product", "sale_line_warn", "product.product", "sale_line_warn", ""),
    ("product.template", "sale_line_warn_msg", "product.template", "sale_line_warn_msg", ""),
    ("product.product", "sale_line_warn_msg", "product.product", "sale_line_warn_msg", ""),
    ("product.template", "sale_ok", "product.template", "sale_ok", ""),
    ("product.product", "sale_ok", "product.product", "sale_ok", ""),
    ("product.template", "sales_count", "product.template", "sales_count", ""),
    ("product.product", "sales_count", "product.product", "sales_count", ""),
    ("product.template", "sequence", "product.template", "sequence", ""),
    ("product.product", "sequence", "product.product", "sequence", ""),
    ("product.template", "service_type", "product.template", "service_type", ""),
    ("product.product", "service_type", "product.product", "service_type", ""),
    ("product.template", "supplier_taxes_id", "product.template", "supplier_taxes_id", ""),
    ("product.product", "supplier_taxes_id", "product.product", "supplier_taxes_id", ""),
    ("product.template", "taxes_id", "product.template", "taxes_id", ""),
    ("product.product", "taxes_id", "product.product", "taxes_id", ""),
    ("product.template", "uom_id", "product.template", "uom_id", ""),
    ("product.product", "uom_id", "product.product", "uom_id", ""),
    ("product.template", "uom_po_id", "product.template", "uom_po_id", ""),
    ("product.product", "uom_po_id", "product.product", "uom_po_id", ""),
    ("product.template", "valuation", "product.template", "valuation", ""),
    ("product.product", "valuation", "product.product", "valuation", ""),
    ("product.template", "warehouse_id", "product.template", "warehouse_id", ""),
    ("product.product", "warehouse_id", "product.product", "warehouse_id", ""),
    ("product.template", "lst_price", "product.template", "lst_price", ""),
    ("product.product", "lst_price", "product.product", "lst_price", ""),
    ("product.template", "is_product_variant", "product.template", "is_product_variant", ""),
    ("product.product", "is_product_variant", "product.product", "is_product_variant", ""),
    ("product.template", "virtual_available", "product.template", "virtual_available", ""),
    ("product.product", "virtual_available", "product.product", "virtual_available", ""),
    ("product.template", "website_message_ids", "product.template", "website_message_ids", ""),
    ("product.product", "website_message_ids", "product.product", "website_message_ids", ""),
    ("product.template", "activity_state", "product.template", "activity_state", "bewusst abweichend"),
    ("product.product", "activity_state", "product.product", "activity_state", "bewusst abweichend"),
    ("product.template", "activity_summary", "product.template", "activity_summary", "bewusst abweichend"),
    ("product.product", "activity_summary", "product.product", "activity_summary", "bewusst abweichend"),
    ("product.template", "activity_user_id", "product.template", "activity_user_id", "bewusst abweichend"),
    ("product.product", "activity_user_id", "product.product", "activity_user_id", "bewusst abweichend"),
    ("product.template", "message_follower_ids", "product.template", "message_follower_ids", "bewusst abweichend"),
    ("product.product", "message_follower_ids", "product.product", "message_follower_ids", "bewusst abweichend"),
    ("product.template", "message_is_follower", "product.template", "message_is_follower", "bewusst abweichend"),
    ("product.product", "message_is_follower", "product.product", "message_is_follower", "bewusst abweichend"),
    ("product.template", "message_partner_ids", "product.template", "message_partner_ids", "bewusst abweichend"),
    ("product.product", "message_partner_ids", "product.product", "message_partner_ids", "bewusst abweichend"),
    ("product.template", "website_message_ids", "product.template", "website_message_ids", "bewusst abweichend"),
    ("product.product", "website_message_ids", "product.product", "website_message_ids", "bewusst abweichend"),
    ("product.template", "rating_ids", "product.template", "rating_ids", "bewusst abweichend"),
    ("product.product", "rating_ids", "product.product", "rating_ids", "bewusst abweichend"),
    ("product.template", "write_date", "product.template", "write_date", "bewusst abweichend"),
    ("product.product", "write_date", "product.product", "write_date", "bewusst abweichend"),
    ("product.template", "write_uid", "product.template", "write_uid", "bewusst abweichend"),
    ("product.product", "write_uid", "product.product", "write_uid", "bewusst abweichend"),
    ("product.template", "service_tracking", "product.template", "service_tracking", "bewusst abweichend"),
    ("product.product", "service_tracking", "product.product", "service_tracking", "bewusst abweichend"),
    ("product.template", "cost_currency_id", "product.template", "cost_currency_id", "bewusst abweichend"),
    ("product.product", "cost_currency_id", "product.product", "cost_currency_id", "bewusst abweichend"),
    ("product.template", "purchase_line_warn_msg", "product.template", "purchase_line_warn_msg", "bewusst abweichend"),
    ("product.product", "purchase_line_warn_msg", "product.product", "purchase_line_warn_msg", "bewusst abweichend"),
]


# Bewusst begruendete Abweichungen (keine 1:1-Zuordnung, mit Anna abgestimmt 30.09.2026)
BEGRUENDET = {
    ("account.move", "ref"): "Odoo-11-Feld reference war nie belegt (0 Belege); Odoo 18 nutzt ref fuer Stornierungstexte",
    ("account.move", "payment_reference"): "in Odoo 11 nicht vorhanden (Odoo-18-Zusatzfeld)",
    ("account.move", "name"): "Odoo-11-Feld name = Begruendung/Beschreibung, nicht die Belegnummer (Regel in Teil 5)",
    # Produkte
    ("product.template", "activity_state"): "Odoo-11-Beschriftung 'Bundesland' ist falsch (Aktivitaetsstatus)",
    ("product.product", "activity_state"): "Odoo-11-Beschriftung 'Bundesland' ist falsch (Aktivitaetsstatus)",
    ("product.template", "activity_summary"): "Standard-Aktivitaetsfeld (Chatter)",
    ("product.product", "activity_summary"): "Standard-Aktivitaetsfeld (Chatter)",
    ("product.template", "activity_user_id"): "Standard-Aktivitaetsfeld (Chatter)",
    ("product.product", "activity_user_id"): "Standard-Aktivitaetsfeld (Chatter)",
    ("product.template", "message_follower_ids"): "Standard-Chatterfeld (mail)",
    ("product.product", "message_follower_ids"): "Standard-Chatterfeld (mail)",
    ("product.template", "message_is_follower"): "Standard-Chatterfeld (mail)",
    ("product.product", "message_is_follower"): "Standard-Chatterfeld (mail)",
    ("product.template", "message_partner_ids"): "Standard-Chatterfeld (mail)",
    ("product.product", "message_partner_ids"): "Standard-Chatterfeld (mail)",
    ("product.template", "website_message_ids"): "Standard-Chatterfeld (website)",
    ("product.product", "website_message_ids"): "Standard-Chatterfeld (website)",
    ("product.template", "rating_ids"): "technisches Bewertungsfeld",
    ("product.product", "rating_ids"): "technisches Bewertungsfeld",
    ("product.template", "write_date"): "technisches Feld",
    ("product.product", "write_date"): "technisches Feld",
    ("product.template", "write_uid"): "technisches Feld",
    ("product.product", "write_uid"): "technisches Feld",
    ("product.template", "service_tracking"): "Odoo-18-Feld hat andere Auswahl/Bedeutung (Aufgabe/Projekt)",
    ("product.product", "service_tracking"): "Odoo-18-Feld hat andere Auswahl/Bedeutung (Aufgabe/Projekt)",
    ("product.template", "cost_currency_id"): "Odoo-11-Beschriftung ist ein englischer Rest ('Cost Currency')",
    ("product.product", "cost_currency_id"): "Odoo-11-Beschriftung ist ein englischer Rest ('Cost Currency')",
    ("product.template", "purchase_line_warn_msg"): "Odoo-11-Text enthaelt Schreibfehler ('Bachricht')",
    ("product.product", "purchase_line_warn_msg"): "Odoo-11-Text enthaelt Schreibfehler ('Bachricht')",
}


def labels(k, modell, felder):
    daten = k.kw(modell, "fields_get", [felder, ["string"]], context={"lang": "de_DE"})
    return {f: (daten.get(f, {}) or {}).get("string") for f in felder}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm", "beide"], default="beide")
    p.add_argument("--nur-abweichungen", action="store_true")
    a = p.parse_args()
    lade_env()

    instanzen = {"lokal": o18("lokal"), "vm": o18("vm")}
    if a.instanz != "beide":
        instanzen = {a.instanz: instanzen[a.instanz]}
    k11 = o11()

    felder11 = {}
    for m, f in {(x[0], x[1]) for x in MAPPING}:
        felder11.setdefault(m, []).append(f)
    beschriftung11 = {m: labels(k11, m, sorted(set(fs))) for m, fs in felder11.items()}

    beschriftung18 = {}
    for name, k in instanzen.items():
        felder18 = {}
        for m, f in {(x[2], x[3]) for x in MAPPING}:
            felder18.setdefault(m, []).append(f)
        beschriftung18[name] = {m: labels(k, m, sorted(set(fs))) for m, fs in felder18.items()}

    abweichungen = {name: [] for name in instanzen}
    zeilen = []
    for m11, f11, m18, f18, anmerkung in MAPPING:
        l11 = beschriftung11.get(m11, {}).get(f11) or "-"
        for name in instanzen:
            l18 = beschriftung18[name].get(m18, {}).get(f18)
            if l18 is None:
                zustand = "FELD FEHLT"
            elif l18 == l11:
                zustand = "gleich"
            elif (m18, f18) in BEGRUENDET:
                zustand = "begruendet abweichend"
            else:
                zustand = "ABWEICHUNG"
                abweichungen[name].append((m11, f11, l11, m18, f18, l18))
            zeilen.append((name, m11, f11, l11, m18, f18, l18 or "-", zustand, anmerkung))
            if name == "lokal":
                print("   %-34s %-30s %-14s | O18 %-32s %-28s %s"
                      % ("%s.%s" % (m11, f11), "", l11, "%s.%s" % (m18, f18), "", zustand))

    print("\n=== Zusammenfassung ===")
    for name in instanzen:
        print("   %-6s: %d Feldpaare, %d Abweichungen"
              % (name, len({(z[1], z[2]) for z in zeilen if z[0] == name}), len(abweichungen[name])))
    for name, liste in abweichungen.items():
        if not liste:
            continue
        print("\n=== Abweichungen %s ===" % name)
        for eintrag in liste:
            print("   %-38s Odoo 11: %-28s -> Odoo 18: %s" % ("%s.%s" % (eintrag[0], eintrag[1]),
                                                              eintrag[2], eintrag[5]))

    ziel = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "docs", "o11-o18-abrechnung-labelmapping.md")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# Label- und Feldmapping Abrechnung (Odoo 11 -> Odoo 18)\n\n")
        fh.write("Erzeugt von `scripts/check_abrechnung_labels.py` (Stand 30.09.2026, Session 122).\n")
        fh.write("Regel: sichtbare Bezeichnung wie Odoo 11, technischer Feldname bleibt Odoo 18.\n\n")
        fh.write("| Odoo-11-Feld | Odoo-11-Bezeichnung | Odoo-18-Zielfeld | Odoo-18-Bezeichnung | Zustand | Anmerkung |\n")
        fh.write("| --- | --- | --- | --- | --- | --- |\n")
        for z in zeilen:
            if z[0] != "lokal":
                continue
            fh.write("| `%s.%s` | %s | `%s.%s` | %s | %s | %s |\n"
                     % (z[1], z[2], z[3], z[4], z[5], z[6], z[7], z[8]))
    print("\nMapping-Tabelle geschrieben: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
