"""Alle Produkt-Listenansichten und Feldbeschriftungen rund um 'Einkaufbare Produkte' erheben.

Aufruf: python scripts/untersuche_einkaufbare_ansichten.py o11|lokal|vm [datei]
Nur lesend. Beantwortet: welche Listenansicht zeigt welches Menue, welche Spalten enthaelt sie,
wie heissen die Felder in de_DE, welche Ansichten tragen Steuer-Spalten.
"""
from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
k = o11() if inst == "o11" else o18(inst)
CTX = {"lang": "de_DE"}
LISTENTYP = "tree" if inst == "o11" else "list"

zeilen = []


def schreibe(text=""):
    zeilen.append(text)
    print(text)


FELDER = ["default_code", "name", "lst_price", "list_price", "taxes_id", "supplier_taxes_id",
          "qty_available", "virtual_available", "uom_id", "uom_po_id", "barcode", "categ_id",
          "standard_price", "product_type_id", "is_multi_factor_product", "sale_ok", "purchase_ok",
          "product_variant_count", "seller_ids", "type", "active", "is_favorite", "cost_currency_id",
          "currency_id", "responsible_id", "product_tag_ids", "description_purchase",
          "description_sale", "recurring_invoice", "invoice_policy", "service_type", "weight", "volume"]

schreibe("=== Instanz=%s ===" % inst)

# ------------------------------------------------------------------ 1. Feldbeschriftungen
for model in ("product.product", "product.template"):
    info = k.kw(model, "fields_get", [FELDER, ["string", "type", "relation"]], context=CTX)
    schreibe("\n--- Feldbeschriftungen de_DE: %s ---" % model)
    for feld in FELDER:
        i = info.get(feld)
        if not i:
            schreibe("  %-26s FELD FEHLT" % feld)
            continue
        schreibe("  %-26s %-34s %-12s %s" % (feld, i.get("string", "?")[:34], i.get("type", "?"),
                                             i.get("relation") or ""))

# ------------------------------------------------------------------ 2. Menues im Einkauf
schreibe("\n--- Menues mit 'Einkauf' im Pfad ---")
for m in k.kw("ir.ui.menu", "search_read",
              [[["complete_name", "ilike", "Einkauf"]], ["complete_name", "action", "sequence"]],
              context=CTX):
    schreibe("  %-52s action=%s" % (m["complete_name"], m["action"]))

# ------------------------------------------------------------------ 3. Listenansichten mit Spalten
schreibe("\n--- Listenansichten (%-4s) fuer product.product / product.template ---" % LISTENTYP)
vids = k.kw("ir.ui.view", "search_read",
            [[["model", "in", ["product.product", "product.template"]], ["type", "=", LISTENTYP]],
             ["name", "model", "priority", "mode", "inherit_id", "xml_id", "arch"]], context=CTX)
for v in sorted(vids, key=lambda x: x["id"]):
    arch = v["arch"] or ""
    spalten = re.findall(r'<field name="([^"]+)"', arch)
    if not spalten:
        continue
    treffer = [f for f in spalten if f in ("default_code", "name", "lst_price", "list_price",
                                           "taxes_id", "supplier_taxes_id", "qty_available",
                                           "virtual_available", "uom_id", "barcode", "standard_price")]
    if not treffer:
        continue
    schreibe("\n  id=%s %-44s mode=%-9s prio=%-3s xmlid=%s" % (
        v["id"], (v["name"] or "")[:44], v["mode"], v["priority"], v["xml_id"]))
    schreibe("      Spalten: %s" % ", ".join(spalten))

# ------------------------------------------------------------------ 4. Ansichten mit Steuerspalten
schreibe("\n--- Ansichten mit Steuerspalten (taxes_id / supplier_taxes_id) ---")
alle = k.kw("ir.ui.view", "search_read",
            [[["model", "in", ["product.product", "product.template"]]],
             ["name", "model", "type", "mode", "xml_id", "arch"]], context=CTX)
for v in alle:
    arch = v["arch"] or ""
    if "taxes_id" in arch and "<field" in arch:
        felder = re.findall(r'<field name="([^"]+)"', arch)
        if "taxes_id" in felder or "supplier_taxes_id" in felder:
            schreibe("  %-8s %-12s id=%-6s %-46s xmlid=%s" % (
                v["type"], v["mode"], v["id"], (v["name"] or "")[:46], v["xml_id"]))
            schreibe("           %s" % ", ".join(felder))

if len(sys.argv) > 2:
    with open(sys.argv[2], "w", encoding="utf-8") as fh:
        fh.write("\n".join(zeilen))
    print("\n[gespeichert: %s]" % sys.argv[2])
