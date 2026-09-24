"""Zusatzproben zum Produktformular (read-only), Teil 2.

- Konten der Produktkategorien in Odoo 11 und Odoo 18 lesen (Odoo 17+ speichert
  unternehmensabhaengige Felder nicht mehr in ir.property, sondern am Datensatz)
- Felddefinition von property_account_income_id in Odoo 18
- Routen der Produkte in Odoo 11 (Standardroute oder Einzelpflege?)
- Umfeld des Wortes "Notizen" im Odoo-18-Formular
- Preislistenpositionen in Odoo 11
"""
from __future__ import annotations

import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vergleich_abo_produktformular_felder as F  # noqa: E402

SP = {"lang": "de_DE"}
ZIEL = os.environ.get("TEMP", ".").replace("\\", "/") + "/aboform"

k11, k18 = F.client("o11"), F.client("lokal")

print("=== Produktkategorien und Konten ===")
for name, kw in (("o11", k11), ("o18", k18)):
    felder = [f for f in ("property_account_income_categ_id", "property_account_expense_categ_id",
                          "property_account_income_id", "property_account_expense_id")
              if isinstance(kw("product.category", "fields_get", [[f], ["string"]], context=SP), dict)
              and "string" in (kw("product.category", "fields_get", [[f], ["string"]], context=SP) or {})]
    print("  %s: lesbare Kontofelder an product.category: %s" % (name, felder))
    kat = kw("product.category", "search_read", [[], ["id", "name"] + felder], context=SP)
    if not isinstance(kat, list):
        print("     Lesefehler: %s" % str(kat)[:150])
        continue
    for f in felder:
        belegt = [(k["id"], k["name"], k[f]) for k in kat if k.get(f)]
        print("     %-38s %d von %d Kategorien belegt  %s" % (f, len(belegt), len(kat), belegt[:4]))

print("\n=== Felddefinition property_account_income_id in Odoo 18 (product.template) ===")
d = k18("product.template", "fields_get", [["property_account_income_id", "property_account_expense_id"],
                                           ["string", "type", "relation", "company_dependent", "store", "readonly"]], context=SP)
print("  %s" % d)

print("\n=== Odoo 18: kommt property_account_income_id in irgendeiner Ansicht vor? ===")
v = k18("ir.ui.view", "search_read", [[["arch_db", "ilike", "property_account_income_id"]], ["id", "name", "model", "type"]],
        context=SP, limit=20)
if isinstance(v, list):
    for x in v:
        print("  %-6s %-52s %-24s %s" % (x["id"], (x["name"] or "")[:52], x["model"], x["type"]))
    if not v:
        print("  (keine Ansicht)")
else:
    print("  %s" % str(v)[:150])

print("\n=== Odoo 11: Routen an den Produkten ===")
prod = k11("product.template", "search_read", [[], ["id", "name", "route_ids"]], context=SP, limit=0)
if isinstance(prod, list):
    zaehler = collections.Counter(tuple(sorted(p["route_ids"])) for p in prod)
    routen = {r["id"]: r["name"] for r in k11("stock.location.route", "search_read", [[], ["id", "name"]], context=SP)}
    print("  Produkte: %d | verschiedene Routenkombinationen: %d" % (len(prod), len(zaehler)))
    for kombi, n in zaehler.most_common(6):
        print("     %5d Produkte: %s" % (n, [routen.get(r, r) for r in kombi]))

print("\n=== Odoo 11: Preislistenpositionen ===")
print("  product.pricelist.item gesamt: %s | Produkte mit Positionen: %d" %
      (k11("product.pricelist.item", "search_count", [[]], context=SP),
       sum(1 for p in prod if p["route_ids"]) if isinstance(prod, list) else -1))
pr = k11("product.pricelist.item", "search_read", [[], ["id", "product_tmpl_id"]], context=SP, limit=0)
if isinstance(pr, list):
    print("  betroffene Produkte (verschieden): %d" % len({x["product_tmpl_id"][0] for x in pr if x.get("product_tmpl_id")}))

print("\n=== Umfeld des Wortes 'Notizen' im Odoo-18-Formular ===")
arch18 = open(ZIEL + "/o18_form_arch.xml", encoding="utf-8").read()
for m in re.finditer("Notizen", arch18):
    print("  ...%s..." % arch18[max(0, m.start() - 160):m.start() + 60].replace("\n", " "))
print("\n=== Odoo 18: <chatter/> und Anhangsfelder im Formular ===")
for m in re.finditer(r"<chatter[^>]*", arch18):
    print("  %s" % m.group(0))
arch11 = open(ZIEL + "/o11_form_arch.xml", encoding="utf-8").read()
print("  Odoo 11 <chatter>: %d" % len(re.findall("<chatter", arch11)))
