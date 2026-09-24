"""Schlussprobe: jedes Odoo-11-Formularfeld einzeln gegen Odoo 18 pruefen (read-only).

Frage je Feld: existiert das Feld im Odoo-18-Modell product.template?
Ausserdem: steht es im gerenderten Odoo-18-Formular?
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vergleich_abo_produktformular as V  # noqa: E402

SP = {"lang": "de_DE"}
ZIEL = os.environ.get("TEMP", ".").replace("\\", "/") + "/aboform"

FELDER = """weight volume responsible_id tracking sale_delay invoice_policy service_type service_policy
service_tracking project_id sale_line_warn sale_line_warn_msg purchase_line_warn purchase_line_warn_msg
purchase_method valuation cost_method property_cost_method property_valuation property_stock_production
property_stock_inventory property_stock_account_input property_stock_account_output property_account_income_id
property_account_expense_id property_account_creditor_price_difference item_ids website_url public_categ_ids
alternative_product_ids accessory_product_ids inventory_availability available_threshold custom_message
website_style_ids route_ids route_from_categ_ids description_pickingout description_pickingin description_picking
product_image_ids product_variant_id uom_po_id currency_id taxes_id supplier_taxes_id categ_id default_code
barcode is_multi_factor_product recurring_invoice subscription_template_id description description_sale
description_purchase attribute_line_ids sale_ok purchase_ok type product_type_id list_price standard_price
qty_available virtual_available outgoing_qty incoming_qty nbr_reordering_rules reordering_min_qty
reordering_max_qty sales_count purchase_count message_ids activity_ids message_follower_ids website_published
image_medium active company_id uom_id product_variant_count is_product_variant name""".split()

k11, k18 = V.client("o11"), V.client("lokal")
arch11 = open(ZIEL + "/o11_form_arch.xml", encoding="utf-8").read()
arch18 = open(ZIEL + "/o18_form_arch_final.xml", encoding="utf-8").read()

d11 = k11("product.template", "fields_get", [FELDER, ["string", "type", "relation"]], context=SP)
d18 = k18("product.template", "fields_get", [FELDER, ["string", "type", "relation"]], context=SP)
d11 = d11 if isinstance(d11, dict) else {}
d18 = d18 if isinstance(d18, dict) else {}

zeilen = []
print("%-44s %-6s %-6s %-32s %-32s" % ("Feld", "O11", "O18", "O11 String", "O18 String"))
for f in FELDER:
    a, b = f in d11, f in d18
    print("%-44s %-6s %-6s %-32s %-32s" % (
        f, "ja" if a else "-", "ja" if b else "NEIN",
        (d11.get(f, {}).get("string") or "")[:32], (d18.get(f, {}).get("string") or "")[:32]))
    z = "|".join([f, "ja" if a else "-", "ja" if b else "NEIN",
                  "imFormular" if ('name="%s"' % f) in arch11 else "-",
                  "imFormular" if ('name="%s"' % f) in arch18 else "-"])
    zeilen.append(z)

with open(ZIEL + "/schlussprobe.txt", "w", encoding="utf-8") as fh:
    fh.write("Feld|O11Modell|O18Modell|O11Formular|O18Formular\n" + "\n".join(zeilen) + "\n")
print("\n[gespeichert: %s/schlussprobe.txt]" % ZIEL)
