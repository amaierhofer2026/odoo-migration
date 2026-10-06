"""Randfaelle der Produktmigration in Odoo 11 klaeren (read-only).

Vorlage 300 "Test Produkt 2" (Attributzeilen, aber nur eine Variante) und Vorlage 263
(keine Variante) auf Verwendung in Belegen und Stammdaten pruefen; Odoo-18-Bestand
gegenueberstellen.

Aufruf: python scripts/pruefe_o11_produkt_randfaelle.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

k = o11()
CTX = {"lang": "de_DE"}
VORLAGEN = (263, 300)

print("=== Odoo 11: Verwendung der Randfall-Vorlagen ===")
for tpl in VORLAGEN:
    t = k.kw("product.template", "read", [[tpl], ["name", "type", "active", "sale_ok",
                                                  "purchase_ok"]], context=CTX)[0]
    print("\nVorlage %s: %s (Typ %s, aktiv %s, Verkauf %s, Einkauf %s)"
          % (tpl, t["name"], t["type"], t["active"], t["sale_ok"], t["purchase_ok"]))
    var = k.kw("product.product", "search", [[["product_tmpl_id", "=", tpl]]], context=CTX)
    print("   Varianten: %s" % var)
    for modell, feld in (("account.move.line", "product_id"), ("sale.order.line", "product_id"),
                         ("purchase.order.line", "product_id"),
                         ("sale.subscription.line", "product_id"), ("stock.move", "product_id"),
                         ("product.supplierinfo", "product_tmpl_id"),
                         ("product.pricelist.item", "product_tmpl_id")):
        try:
            if modell == "product.supplierinfo":
                n = k.kw(modell, "search_count", [[[feld, "=", tpl]]], context=CTX)
                hinweis = ""
            elif var:
                n = k.kw(modell, "search_count", [[[feld, "in", var]]], context=CTX)
                hinweis = ""
            else:
                n = 0
                hinweis = " (Vorlage ohne Variante: Belegzeilen koennen sie nicht fuehren)"
            print("   %-24s %s: %d%s" % (modell, feld, n, hinweis))
        except Exception as e:
            print("   %-24s Fehler: %s" % (modell, str(e)[:70]))

print("\n=== Odoo 18: Bestand der beiden Instanzen ===")
for inst in ("lokal", "vm"):
    k18 = o18(inst)
    print("%s: product.template %d | product.product %d | product.attribute %d | "
          "product.attribute.value %d | product.image-Modell vorhanden: %s"
          % (inst, k18.kw("product.template", "search_count", [[]], context=CTX),
             k18.kw("product.product", "search_count", [[]], context=CTX),
             k18.kw("product.attribute", "search_count", [[]], context=CTX),
             k18.kw("product.attribute.value", "search_count", [[]], context=CTX),
             bool(k18.kw("ir.model", "search_count", [[["model", "=", "product.image"]]],
                         context=CTX))))
    ids = k18.kw("product.template", "search", [[["id", "in", list(VORLAGEN)]]], context=CTX)
    if ids:
        print("   Vorlagen mit denselben IDs in Odoo 18:",
              k18.kw("product.template", "read", [ids, ["id", "name", "type"]], context=CTX))
    print("   Vorlagen ohne Variante:",
          len([t for t in k18.kw("product.template", "search", [[]], context=CTX)
               if not k18.kw("product.product", "search_count", [[["product_tmpl_id", "=", t]]],
                             context=CTX)]))
