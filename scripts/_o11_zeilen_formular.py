"""Read-only: Rechnungszeilen-Spalten im Odoo-11-Formular (account.invoice.form) messen."""
import re
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11  # noqa: E402

k = o11()

# 1. Basisformular
basis = k.kw("ir.ui.view", "search_read",
             [[["name", "=", "account.invoice.form"], ["model", "=", "account.invoice"],
               ["type", "=", "form"]], ["id", "name", "arch_db"]])
if not basis:
    sys.exit("account.invoice.form nicht gefunden")
v = basis[0]
arch = v["arch_db"]
i = arch.find("invoice_line_ids")
start = arch.rfind("<", 0, arch.rfind("field", 0, i))
teil = arch[start:arch.find("</field>", i) + 8]
print("=== Odoo 11 account.invoice.form (id %s), invoice_line_ids:" % v["id"])
print(teil[:2500])
print("\nFelder im Zeilenblock:", re.findall(r"<field name=\"([^\"]+)\"", teil))

# 2. Alle Vererbungen des Formulars, die Zeilenfelder anfassen
kinder = k.kw("ir.ui.view", "search_read",
              [[["model", "=", "account.invoice"], ["type", "=", "form"],
                ["inherit_id", "!=", False]],
               ["id", "name", "priority", "inherit_id", "arch_db"]])
print("\n=== Vererbende Formularansichten: %d ===" % len(kinder))
for kind in kinder:
    a = kind["arch_db"] or ""
    if "invoice_line" not in a and "name" not in a:
        continue
    felder = re.findall(r"<field name=\"([^\"]+)\"", a)
    if not felder:
        continue
    print("  id %-5s prio %-4s %-40s Felder: %s" % (kind["id"], kind["priority"],
                                                    kind["name"][:40], felder))
