"""Read-only: Odoo-11-Vererbungen, die Zeilen-Spalten ergaenzen (Sektion, Nummer)."""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11  # noqa: E402

k = o11()
for vid in (1044, 1270):
    treffer = k.kw("ir.ui.view", "search_read", [[["id", "=", vid]], ["id", "name", "priority", "arch_db"]])
    if not treffer:
        print("id %s nicht gefunden" % vid)
        continue
    v = treffer[0]
    print("=== id %s | %s | prio %s" % (v["id"], v["name"], v["priority"]))
    print(v["arch_db"])
    print()
