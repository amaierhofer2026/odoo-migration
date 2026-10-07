"""Details fuer den Umbau der Produktliste: Ansichten 1023/4204, Aktions-XMLIDs, Belegung.

Aufruf: python scripts/pruefe_produktliste_details.py o11|lokal|vm
Nur lesend.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
k = o11() if inst == "o11" else o18(inst)
CTX = {"lang": "de_DE"}

print("=== Instanz=%s ===" % inst)

if inst != "o11":
    info = k.kw("ir.actions.act_window", "fields_get", [[], ["string", "type"]], context=CTX)
    print("ir.actions.act_window hat 'view_id': %s" % ("view_id" in info))

for mid in (225, 226, 382, 383):
    d = k.kw("ir.model.data", "search_read",
             [[["model", "=", "ir.actions.act_window"], ["res_id", "=", mid]],
              ["module", "name", "complete_name"]], context=CTX)
    if d:
        print("Aktion %s = %s" % (mid, d[0]["complete_name"]))

if inst != "o11":
    for vid in (860, 1023, 4204, 2204, 4400, 4267):
        try:
            v = k.kw("ir.ui.view", "read", [[vid], ["name", "mode", "inherit_id", "priority", "xml_id", "arch"]],
                    context=CTX)[0]
            print("\n### Ansicht %s  %s  mode=%s  inherit=%s  xmlid=%s" % (
                vid, v["name"], v["mode"], v["inherit_id"], v["xml_id"]))
            print(v["arch"])
        except Exception as e:
            print("\n### Ansicht %s: %s" % (vid, str(e)[:120]))

print("\n--- Belegung in %s ---" % inst)
modell = "product.product" if inst == "o11" else "product.template"
print("  Datensaetze: %d" % k.kw(modell, "search_count", [[]], context=CTX))
for feld in ("default_code", "name", "taxes_id", "supplier_taxes_id", "list_price", "lst_price",
             "standard_price", "purchase_ok", "sale_ok", "barcode", "uom_id", "uom_po_id",
             "categ_id", "type", "product_type_id", "attribute_line_ids", "attribute_value_ids",
             "seller_ids", "active"):
    try:
        if feld in ("seller_ids", "attribute_line_ids"):
            basis = "product.template" if feld == "attribute_line_ids" else modell
            anzahl = k.kw(basis, "search_count", [[[feld, "!=", False]]], context=CTX)
        else:
            anzahl = k.kw(modell, "search_count", [[[feld, "!=", False]]], context=CTX)
        print("  %-22s %s" % (feld, anzahl))
    except Exception as e:
        print("  %-22s Fehler: %s" % (feld, str(e)[:70]))

if inst == "o11":
    for modell2, dom in (("product.supplierinfo", []),
                         ("product.pricelist.item", []),
                         ("product.template", [[("purchase_ok", "=", 1)]]),
                         ("product.template", [[("purchase_ok", "=", 0)]]),
                         ("product.template", [[("taxes_id", "=", False)]]),
                         ("product.template", [[("supplier_taxes_id", "=", False)]])):
        try:
            print("  %-22s %s" % (modell2 + (" " + str(dom) if dom else ""),
                                  k.kw(modell2, "search_count", [dom], context=CTX)))
        except Exception as e:
            print("  %-22s Fehler: %s" % (modell2, str(e)[:60]))
