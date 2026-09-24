"""Teil 4: Modulzustaende Odoo 18 und Zeiterfassung in Odoo 11 (read-only)."""
from __future__ import annotations

import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vergleich_abo_produktformular as V  # noqa: E402

SP = {"lang": "de_DE"}
k11, k18 = V.client("o11"), V.client("lokal")

print("=== Modulzustaende Odoo 18 (lokal) ===")
module = k18("ir.module.module", "search_read",
             [[["name", "in", ["sale_project", "sale_timesheet", "project", "hr_timesheet", "website_sale",
                               "product", "stock", "stock_account", "sale_stock", "purchase_stock", "account",
                               "sale_management", "itk_product", "itk_multifactor", "account_analytic"]]],
              ["name", "state", "installed_version"]], context=SP)
for m in sorted(module or [], key=lambda x: x["name"]):
    print("   %-24s %-14s %s" % (m["name"], m["state"], m["installed_version"] or "-"))

print("\n=== Odoo 11: Dienstleistung mit Zeiterfassung ===")
pr = k11("product.template", "search_read", [[["service_type", "=", "timesheet"]], ["id", "name", "default_code"]], context=SP, limit=0)
print("   Produkte mit service_type='timesheet': %d" % len(pr or []))
for x in (pr or [])[:8]:
    print("      %-6s %-46s %s" % (x["id"], (x["name"] or "")[:46], x["default_code"] or "-"))
ids = [x["id"] for x in (pr or [])]
if ids:
    pp = k11("product.product", "search_read", [[["product_tmpl_id", "in", ids]], ["id"]], context=SP, limit=0)
    pids = [x["id"] for x in (pp or [])]
    print("   zugehoerige Varianten: %d" % len(pids))
    if pids:
        for modell, dom, feld in (("account.analytic.line", [["product_id", "in", pids]], "product_id"),
                                  ("sale.order.line", [["product_id", "in", pids]], "product_id")):
            n = k11(modell, "search_count", [dom], context=SP)
            print("   %-22s Zeilen mit diesen Produkten: %s" % (modell, n))
        n_ts = k11("sale.order.line", "search_count", [[["product_id", "in", pids], ["qty_delivered", ">", 0]]], context=SP)
        print("   sale.order.line mit qty_delivered > 0 (diese Produkte): %s" % n_ts)
print("   account.analytic.line gesamt in Odoo 11: %s" % k11("account.analytic.line", "search_count", [[]], context=SP))
print("   sale.order.line gesamt: %s | mit qty_delivered != 0: %s" % (
    k11("sale.order.line", "search_count", [[]], context=SP),
    k11("sale.order.line", "search_count", [[["qty_delivered", "!=", 0]]], context=SP)))

print("\n=== Odoo 11: Verteilung service_policy / expense_policy ===")
sp = k11("product.template", "search_read", [[], ["id", "service_policy"]], context=SP, limit=0)
print("   service_policy: %s" % collections.Counter(x.get("service_policy") for x in (sp or [])).most_common())
print("   expense_policy in Odoo 11 vorhanden: %s" % (isinstance(k11("product.template", "fields_get", [["expense_policy"], ["string"]], context=SP),
                                                                 dict) and "expense_policy" in k11("product.template", "fields_get", [["expense_policy"], ["string"]], context=SP)))
