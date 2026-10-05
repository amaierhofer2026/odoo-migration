"""Read-only: Spalten der Rechnungszeilen in Odoo 11 (account.invoice.line) messen."""
import re
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11  # noqa: E402

k = o11()

# Ansichten mit Bezug auf Rechnungszeilen
views = k.kw("ir.ui.view", "search_read",
             [[["model", "=", "account.invoice.line"]],
              ["id", "name", "type", "mode", "priority", "inherit_id", "arch_db"]])
print("Ansichten account.invoice.line:", len(views))
for v in views:
    arch = v.get("arch_db") or ""
    felder = re.findall(r"<field name=\"([^\"]+)\"", arch)
    print("\n=== id %s | %s | typ=%s mode=%s prio=%s inherits=%s"
          % (v["id"], v["name"], v["type"], v["mode"], v["priority"], v["inherit_id"]))
    print("    Felder:", felder)
    if v["type"] == "tree":
        print(arch)
