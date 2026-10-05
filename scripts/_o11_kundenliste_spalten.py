"""Read-only: Listenansichten der Kundenrechnungen in Odoo 11 auslesen (Session 124).

Zeigt die Spaltenreihenfolge der Odoo-11-Kundenliste (account.invoice.tree), damit die
Project-Category-Spalte in Odoo 18 an derselben fachlichen Position landet.
"""
import json
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11  # noqa: E402

k = o11()
views = k.kw("ir.ui.view", "search_read",
             [[["model", "=", "account.invoice"]],
              ["id", "name", "type", "mode", "priority", "inherit_id", "arch_db"]])
for v in views:
    arch = v.get("arch_db") or ""
    if "projectcategory" not in arch.lower():
        continue
    print("=== View %s  %s  typ=%s mode=%s prio=%s inherits=%s" %
          (v["id"], v["name"], v["type"], v["mode"], v["priority"], v["inherit_id"]))
    print(arch)
    print()
