"""Nutzung der Produktformular-Felder in Odoo 11 (read-only).

Zaehlt je Feld, in wie vielen product.template-Datensaetzen ein Wert steht
(Bulk-Read des Feldes, Zaehlung in Python). Zusaetzlich: product.image,
Anhaenge am Produkt, Steuer-/Kontofelder.

Aufruf: python scripts/analyse_o11_produktfelder_nutzung.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11  # noqa: E402

FELDER = [
    # Allgemeine Informationen
    "name", "type", "product_type_id", "categ_id", "default_code", "barcode", "list_price",
    "is_multi_factor_product", "recurring_invoice", "subscription_template_id", "standard_price",
    "uom_id", "uom_po_id",
    # Verkauf
    "sale_ok", "sale_line_warn", "sale_line_warn_msg", "description_sale",
    # Einkauf
    "purchase_ok", "seller_ids", "purchase_method", "description_purchase",
    "purchase_line_warn", "purchase_line_warn_msg",
    # Lager
    "route_ids", "tracking", "weight", "volume", "responsible_id", "sale_delay",
    "description_picking", "description_pickingin", "description_pickingout",
    # Abrechnung
    "taxes_id", "supplier_taxes_id", "property_account_income_id",
    "property_account_expense_id", "property_account_creditor_price_difference",
    "invoice_policy", "service_type", "service_policy", "service_tracking", "project_id",
    # Notizen / Bilder
    "description", "product_image_ids", "sale_delay",
    # Sonstiges (Kontrollwerte)
    "active",
]

k = o11()
CTX = {"lang": "de_DE"}
ids = k.kw("product.template", "search", [[]], context=CTX)
print("product.template gesamt:", len(ids))
print("product.product  gesamt:", k.kw("product.product", "search_count", [[]], context=CTX))
try:
    print("product.image    gesamt:", k.kw("product.image", "search_count", [[]], context=CTX))
except Exception as e:
    print("product.image    Fehler:", str(e)[:80])
print()
print("%-46s %8s %8s %7s" % ("Feld", "belegt", "gesamt", "%"))
for f in FELDER:
    try:
        werte = k.kw("product.template", "read", [ids, [f]], context=CTX)
    except Exception as e:
        print("%-46s Fehler: %s" % (f, str(e)[:60]))
        continue
    belegt = 0
    for w in werte:
        v = w.get(f)
        if v not in (False, None, "", 0, 0.0, [], "no-message"):
            belegt += 1
    print("%-46s %8d %8d %6.1f%%" % (f, belegt, len(ids), 100.0 * belegt / max(len(ids), 1)))

# Anhaenge (Bilder/Dokumente) am Produkt
try:
    an = k.kw("ir.attachment", "search_read",
              [[["res_model", "=", "product.template"]], ["res_id", "mimetype"]], context=CTX)
    produkte = {a["res_id"] for a in an}
    bilder = [a for a in an if (a.get("mimetype") or "").startswith("image/")]
    print()
    print("Anhaenge an product.template:", len(an), "| davon Bilder:", len(bilder),
          "| Produkte mit Anhang:", len(produkte))
except Exception as e:
    print("Anhaenge Fehler:", str(e)[:100])
