"""Read-only: vollstaendige Beschriftungspruefung des Bereichs Abrechnung (Odoo 11 gegen Odoo 18).

Prueft NICHT nur die dokumentierten 155 Feldpaare, sondern ALLE Felder der Modelle, die in den
Menuepunkten der Abrechnung (Odoo 11 bzw. Odoo 18) tatsaechlich vorkommen:

1. Je Modellpaar (Odoo 11 -> Odoo 18) werden die sichtbaren Feldbeschriftungen in de_DE gelesen.
2. Gleichnamige Felder werden verglichen (gleich / anders).
3. Umbenannte Felder werden ueber die Zuordnungstabelle verglichen.
4. Felder, die es nur auf einer Seite gibt, werden getrennt ausgewiesen.
5. Zusaetzlich: Felder, deren deutsche Beschriftung mit der englischen Quelle identisch ist
   (also keine deutsche Uebersetzung hat) - Liste zur Bewertung.

Odoo 11 wird ausschliesslich gelesen. Aufruf:
    python scripts/pruefe_abrechnung_beschriftungen_vollstaendig.py [--instanz lokal|vm]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

ZIEL = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session131", "beschriftungen")

# Modellpaare im Bereich Abrechnung (Odoo 11 -> Odoo 18). None = kein Gegenstueck.
PAARE = {
    "account.invoice": "account.move",
    "account.invoice.line": "account.move.line",
    "account.payment": "account.payment",
    "account.journal": "account.journal",
    "account.tax": "account.tax",
    "account.fiscal.position": "account.fiscal.position",
    "account.payment.term": "account.payment.term",
    "account.cash.rounding": "account.cash.rounding",
    "account.analytic.account": "account.analytic.account",
    "account.analytic.tag": None,
    "account.bank.statement.line": "account.bank.statement.line",
    "res.currency": "res.currency",
    "res.partner": "res.partner",
    "res.config.settings": "res.config.settings",
    "product.template": "product.template",
    "product.category": "product.category",
    "product.pricelist": "product.pricelist",
    "product.pricelist.item": "product.pricelist.item",
    "account.invoice.report": "account.invoice.report",
    "account.tax.report": None,
    "account.print.journal": None,
    "account.aged.trial.balance": None,
    "account.financial.report": None,
    "payment.acquirer": "payment.provider",
    "itk_valorisierung.valorisierung": "itk_valorisierung.valorisierung",
    "itk_projectcategory.projectcategory": "itk_projectcategory.projectcategory",
    "mail.message": "mail.message",
    "account.analytic.plan": None,
    "account.analytic.distribution.model": None,
    "account.account": "account.account",
}

# Umbenannte Felder (Odoo 11 -> Odoo 18), damit Beschriftungen vergleichbar bleiben.
UMBENANNT = {
    "account.invoice": {"date_invoice": "invoice_date", "date_due": "invoice_date_due",
                        "number": "name", "reference": "ref", "origin": "invoice_origin",
                        "comment": "narration", "type": "move_type", "user_id": "invoice_user_id",
                        "payment_term_id": "invoice_payment_term_id", "residual": "amount_residual",
                        "sent": "is_move_sent", "reconciled": "has_reconciled_entries",
                        "amount_total_company_signed": "amount_total_in_currency_signed",
                        "incoterms_id": "invoice_incoterm_id",
                        "cash_rounding_id": "invoice_cash_rounding_id",
                        "move_name": "name"},
    "account.invoice.line": {"invoice_id": "move_id", "uom_id": "product_uom_id",
                             "invoice_line_tax_ids": "tax_ids",
                             "account_analytic_id": "analytic_distribution"},
    "account.payment": {"payment_method_id": "payment_method_line_id"},
    "payment.acquirer": {"payment_icon_ids": "image_128"},
}

# Bewusst abweichende, dokumentierte Beschriftungen (aus docs/o11-o18-abrechnung-labelmapping.md).
BEWUSST = {
    ("account.invoice", "reference"), ("account.invoice", "payment_reference"),
    ("product.template", "product_type_id"), ("product.template", "website_message_ids"),
    ("product.template", "activity_state"), ("product.template", "activity_summary"),
    ("product.template", "activity_user_id"), ("product.template", "message_follower_ids"),
    ("product.template", "message_is_follower"), ("product.template", "message_partner_ids"),
    ("product.template", "rating_ids"), ("product.template", "write_uid"),
    ("product.template", "write_date"), ("product.template", "service_tracking"),
    ("product.template", "cost_currency_id"), ("product.template", "purchase_line_warn_msg"),
    ("product.template", "lst_price"),
}


def beschriftungen(k, modell):
    try:
        felder = k.kw(modell, "fields_get", [[], ["string", "type"]], context={"lang": "de_DE"})
    except Exception as fehler:
        return {"fehler": "fields_get fehlgeschlagen: %s" % str(fehler)[:140]}
    try:
        felder_en = k.kw(modell, "fields_get", [[], ["string"]], context={"lang": "en_US"})
    except Exception as fehler:
        felder_en = {}
    return {name: {"string": d.get("string", ""), "typ": d.get("type", ""),
                   "string_en": felder_en.get(name, {}).get("string", "")}
            for name, d in felder.items()}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    args = ap.parse_args()
    os.makedirs(ZIEL, exist_ok=True)

    k11, k18 = o11(), o18(args.instanz)
    ergebnis = {"gleich": [], "anders": [], "nur_o11": [], "nur_o18": [], "englisch_identisch": [],
                "bewusst_abweichend": [], "fehler": []}

    for m11, m18 in PAARE.items():
        print("### %s -> %s" % (m11, m18), flush=True)
        b11 = beschriftungen(k11, m11)
        if "fehler" in b11:
            ergebnis["fehler"].append({"modell": m11, "meldung": b11["fehler"]})
            print("   FEHLER:", b11["fehler"])
            continue
        if m18 is None:
            for name, d in b11.items():
                if d["typ"] in ("one2many", "many2many", "many2one") and name.endswith("_ids"):
                    continue
                if name in ("id", "__last_update", "display_name"):
                    continue
                ergebnis["nur_o11"].append({"modell": m11, "feld": name, "o11": d["string"]})
            continue
        b18 = beschriftungen(k18, m18)
        if "fehler" in b18:
            ergebnis["fehler"].append({"modell": m18, "meldung": b18["fehler"]})
            print("   FEHLER:", b18["fehler"])
            continue
        zuordnung = UMBENANNT.get(m11, {})
        for name, d in b11.items():
            if name in ("id", "__last_update", "display_name"):
                continue
            ziel = zuordnung.get(name, name)
            if ziel in b18:
                e = {"modell_o11": m11, "modell_o18": m18, "feld_o11": name, "feld_o18": ziel,
                     "o11": d["string"], "o18": b18[ziel]["string"]}
                if d["string"] == b18[ziel]["string"]:
                    ergebnis["gleich"].append(e)
                elif (m11, name) in BEWUSST:
                    ergebnis["bewusst_abweichend"].append(e)
                else:
                    ergebnis["anders"].append(e)
            else:
                ergebnis["nur_o11"].append({"modell": m11, "feld": name, "o11": d["string"]})
        umgekehrt = set(zuordnung.values())
        for name, d in b18.items():
            if name in ("id", "__last_update", "display_name"):
                continue
            if name not in umgekehrt and name not in b11:
                ergebnis["nur_o18"].append({"modell": m18, "feld": name, "o18": d["string"],
                                            "englisch": d["string"] == d["string_en"]})
        for name, d in b18.items():
            if d["string"] and d["string"] == d["string_en"] and name not in ("id", "__last_update"):
                ergebnis["englisch_identisch"].append({"modell": m18, "feld": name, "string": d["string"]})

    for schluessel, titel in (("anders", "ABWEICHENDE BESCHRIFTUNG (Odoo 11 gegen Odoo 18)"),):
        print("\n=== %s: %d ===" % (titel, len(ergebnis[schluessel])))
        for e in ergebnis[schluessel]:
            print("   %-28s %-28s O11=%-32s O18=%s" % (e["modell_o11"], e["feld_o18"], e["o11"], e["o18"]))
    print("\n=== Fehler: %d ===" % len(ergebnis["fehler"]))
    for e in ergebnis["fehler"]:
        print("   ", e)
    print("\nZusammenfassung: %d gleich, %d anders, %d bewusst abweichend, %d nur O11, %d nur O18, "
          "%d deutsch=englisch" % (len(ergebnis["gleich"]), len(ergebnis["anders"]),
                                   len(ergebnis["bewusst_abweichend"]), len(ergebnis["nur_o11"]),
                                   len(ergebnis["nur_o18"]), len(ergebnis["englisch_identisch"])))

    p = os.path.join(ZIEL, "beschriftungen_%s.json" % args.instanz)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1, default=str)
    print("Rohdaten: %s" % p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
