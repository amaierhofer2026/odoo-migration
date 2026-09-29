"""Bestandsaufnahme Verkauf, Teil 4: Druckberichte in Odoo 11 und Odoo 18.

Liest in Odoo 11 Prod (ausschliesslich lesend), Odoo 18 lokal und Odoo 18 VM:
  - alle Report-Aktionen (ir.actions.report) zu sale.order / sale.order.line
  - Bindung an das Drucken-Menue (binding_type/binding_model_id)
  - Reportname, Vorlage, Papierformat, Anhangsspeicherung
  - die QWeb-Vorlagen (Feldbezuege: Kunde, Positionen, Betraege, Steuern, Status)
  - vorhandene gespeicherte PDF-Anhaenge je Vorlage (Nutzungsspur)

Ergebnis: docs/_verkauf_teil4_druckberichte.json (gitignoriert)

Aufruf:
    python scripts/analyse_verkauf_teil4_druckberichte.py
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}

# Felder, deren Vorkommen in der Vorlage fachlich geprueft wird
FELD_MUSTER = {
    "partner": [r"partner_id", r"partner_shipping_id", r"partner_invoice_id", r"commercial_partner"],
    "adresse": [r"\.street", r"\.city", r"\.zip", r"\.country_id", r"\.vat", r"\.phone", r"\.email"],
    "positionen": [r"order_line", r"product_id", r"name\b", r"product_uom", r"product_uom_qty"],
    "preise": [r"price_unit", r"price_subtotal", r"price_total", r"discount", r"tax_id", r"taxes"],
    "summen": [r"amount_untaxed", r"amount_tax", r"amount_total", r"amount_%"],
    "status": [r"\bstate\b", r"confirmation_date", r"date_order", r"validity_date", r"require_payment"],
    "kopf_fuss": [r"company_id", r"user_id", r"internal_note", r"note", r"payment_term_id", r"incoterm"],
    "kanaele": [r"team_id", r"source_id", r"campaign_id", r"medium_id"],
}


def musterbefunde(arch: str) -> dict:
    arch = arch or ""
    treffer = {}
    for gruppe, muster in FELD_MUSTER.items():
        gefunden = sorted({m for m in muster if re.search(m, arch)})
        treffer[gruppe] = gefunden
    return treffer


def erhebe(client, ist18: bool) -> dict:
    daten = {"reports": [], "vorlagen": [], "anhaenge": [], "knoepfe": []}
    reports = client.kw("ir.actions.report", "search_read",
                        [[("model", "=", "sale.order")],
                         ["id", "name", "report_name", "report_type", "binding_model_id",
                          "binding_type", "print_report_name", "attachment", "attachment_use",
                          "paperformat_id", "groups_id", "multi"]], context=SP)
    for r in reports:
        r = dict(r)
        r["binding_model_id"] = r["binding_model_id"][1] if r["binding_model_id"] else None
        r["paperformat_id"] = r["paperformat_id"][1] if r["paperformat_id"] else None
        daten["reports"].append(r)

    for r in reports:
        vorlagen = client.kw("ir.ui.view", "search_read",
                             [[("type", "=", "qweb"), ("key", "=", r["report_name"])],
                              ["id", "name", "key", "arch_db", "priority", "mode"]], context=SP)
        if not vorlagen:
            vorlagen = client.kw("ir.ui.view", "search_read",
                                 [[("type", "=", "qweb"),
                                   ("name", "ilike", r["report_name"].replace(".", " "))],
                                  ["id", "name", "key", "arch_db", "priority", "mode"]], context=SP)
        for v in vorlagen:
            v = dict(v)
            arch = v.pop("arch_db") or ""
            v["report_name"] = r["report_name"]
            v["report_titel"] = r["name"]
            v["arch_zeichen"] = len(arch)
            v["felder"] = musterbefunde(arch)
            v["papierformat_zeilen"] = re.findall(r'format="([A-Za-z0-9_.]+)"', arch)[:5]
            v["extern_layout"] = bool(re.search(r"external_layout|web\.external_layout", arch))
            daten["vorlagen"].append(v)

    # Nutzungsspur: gespeicherte PDF-Anhaenge zu Verkaufsauftraegen
    anhaenge = client.kw("ir.attachment", "search_read",
                         [[("res_model", "=", "sale.order")], ["id", "name", "mimetype", "res_id"]],
                         context=SP)
    zaehler = {}
    for a in anhaenge:
        schluessel = a["name"].split(".")[0][:60]
        zaehler[schluessel] = zaehler.get(schluessel, 0) + 1
    daten["anhaenge"] = sorted(zaehler.items(), key=lambda x: -x[1])[:15]

    # Druckknoepfe am Auftrag (Formularansicht) - welcher Report ist verdrahtet
    form = client.kw("ir.ui.view", "search_read",
                     [[("model", "=", "sale.order"), ("type", "=", "form")],
                      ["id", "name", "arch_db", "priority"]], context=SP)
    for f in form:
        arch = f.get("arch_db") or ""
        for treffer in re.findall(r'<button[^>]*(?:print_quotation|report)[^>]*>', arch):
            daten["knoepfe"].append({"ansicht": f["name"], "knopf": treffer[:200]})
        for treffer in re.findall(r'name="([^"]*report[^"]*)"', arch):
            daten["knoepfe"].append({"ansicht": f["name"], "ref": treffer})
    return daten


def main() -> int:
    ergebnis = {}
    for name, client in (("o11", o11()), ("o18lokal", o18("lokal")), ("o18vm", o18("vm"))):
        ist18 = name != "o11"
        print("erhebe %s ..." % name)
        ergebnis[name] = erhebe(client, ist18)
        for r in ergebnis[name]["reports"]:
            print("   %-42s %-38s %s" % (r["name"][:42], r["report_name"], r["report_type"]))
        print("   Vorlagen: %d, gespeicherte PDFs: %d" % (len(ergebnis[name]["vorlagen"]),
                                                         len(ergebnis[name]["anhaenge"])))

    ziel = os.path.join(REPO, "docs", "_verkauf_teil4_druckberichte.json")
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print("\nRohdaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
