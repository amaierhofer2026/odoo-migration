"""Gruppen der Buchhaltung in Odoo 18: Namen, Vererbung, Mitglieder."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vergleich_abo_produktformular as V  # noqa: E402

SP = {"lang": "de_DE"}
k = V.client("lokal")
g = k("res.groups", "read", [[35, 36, 37, 38, 39], ["id", "name", "full_name", "implied_ids", "users", "trans_implied_ids"]], context=SP)
for x in g or []:
    print("%-4s %-42s implied=%s users=%d" % (x["id"], x["full_name"] or x["name"], x["implied_ids"], len(x["users"])))
print()
for x in g or []:
    tr = x.get("trans_implied_ids")
    if tr:
        namen = k("res.groups", "read", [tr, ["full_name"]], context=SP)
        print("%-42s schliesst ein: %s" % (x["full_name"] or x["name"], [n["full_name"] for n in namen]))
