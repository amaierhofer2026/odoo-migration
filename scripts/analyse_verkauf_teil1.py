"""Read-only Bestandsaufnahme Verkauf Teil 1: Module und Nutzungszahlen.

Aufruf:
    python scripts/analyse_verkauf_teil1.py

Odoo 11 Prod (portal.it-kommunal.at, DB ITK_V1_a) wird ausschliesslich lesend verwendet.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

VERKAUF_MODULE = ["sale", "sale_management", "sale_stock", "sale_timesheet", "sale_subscription",
                  "sales_team", "account", "product", "crm", "report", "sale_order_line_number",
                  "itk_sale_management", "itk_saleorder_lines", "itk_crm", "itk_multifactor",
                  "itk_product", "merge_sale_order", "sale_merge_draft_invoice", "mass_editing",
                  "server_action_mass_edit", "account_invoice_line_number", "itk_reports"]

MODELLE = [
    ("sale.order", []),
    ("sale.order.line", []),
    ("sale.report", []),
    ("product.pricelist", []),
    ("product.pricelist.item", []),
    ("product.template", []),
    ("product.product", []),
    ("crm.team", []),
    ("account.payment.term", []),
    ("account.tax", []),
    ("res.partner", [["customer_rank", ">", 0]] if False else [["active", "=", True]]),
    ("sale.layout.category", []),
    ("crm.claim", []),
    ("report.all.channels.sales", []),
    ("sale.subscription", []),
    ("account.move", [["type", "=", "out_invoice"]]),
    ("account.fiscal.position", []),
]


def module(k) -> dict:
    try:
        daten = k.kw("ir.module.module", "search_read",
                     [[["name", "in", VERKAUF_MODULE]],
                      ["name", "shortdesc", "state", "latest_version", "author", "license"]],
                     context={"lang": "de_DE"})
    except Exception as fehler:
        print("  (Modulabfrage nicht moeglich: %s)" % str(fehler)[:120])
        return {}
    return {d["name"]: d for d in daten}


def main() -> int:
    for name, client in (("ODOO 11 PROD (read-only)", o11()), ("ODOO 18 LOKAL", o18("lokal"))):
        print("\n================ %s ================" % name)
        mods = module(client)
        print("--- Module ---")
        for m in VERKAUF_MODULE:
            d = mods.get(m)
            if d:
                print("  %-28s %-8s %-14s %s" % (d["name"], d["state"], d.get("latest_version") or "-",
                                                 d["shortdesc"]))
            else:
                print("  %-28s nicht vorhanden" % m)
        print("--- Nutzungszahlen ---")
        for modell, domain in MODELLE:
            try:
                n = client.kw(modell, "search_count", [domain])
                print("  %-30s %d" % (modell, n))
            except Exception as fehler:
                print("  %-30s FEHLER %s" % (modell, str(fehler)[:90]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
