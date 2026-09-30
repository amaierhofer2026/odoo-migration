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
]


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
