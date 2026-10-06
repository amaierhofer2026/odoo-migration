"""Bestand account.move je Zustand/Zahlungszustand/Belegart (Odoo 18, read-only)."""
import sys

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o18  # noqa: E402

k = o18(sys.argv[1] if len(sys.argv) > 1 else "lokal")
print("Instanz:", k.url)
gruppen = k.kw("account.move", "read_group",
               [[], ["id"], ["state", "payment_state", "move_type"]],
               context={"lang": "de_DE"}, lazy=False)
for g in gruppen:
    print("  %-10s %-16s %-12s %s" % (g["state"], g.get("payment_state"),
                                      g["move_type"], g["__count"]))
print("Gesamt:", k.kw("account.move", "search_count", [[]]))
