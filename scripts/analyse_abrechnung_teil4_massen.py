"""Read-only Teil 4: Massenbearbeitung und Massenaktionen der Rechnung (Odoo 11 gegen Odoo 18).

Aufruf:  python scripts/analyse_abrechnung_teil4_massen.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18


def main() -> int:
    lade_env()
    k11, k18 = o11(), o18("lokal")

    print("=== Odoo 11: Massenbearbeitungsobjekte auf der Rechnung (mass.object) ===")
    treffer = []
    for m in k11.kw("mass.object", "search_read",
                    [[("model_id.model", "=", "account.invoice")],
                     ["id", "name", "field_ids", "model_id"]], order="id", context={"lang": "de_DE"}):
        namen = []
        for fid in m["field_ids"]:
            f = k11.kw("ir.model.fields", "read", [[fid], ["name", "field_description"]])[0]
            namen.append(m.get("name") and "%s (%s)" % (f["name"], f["field_description"]) or f["name"])
        print("   id=%-4s %-40s -> %s" % (m["id"], m["name"][:40], namen))
        treffer.append(m["name"])
    if not treffer:
        print("   keine Massenbearbeitungsobjekte auf account.invoice")

    print("\n=== Odoo 18: Server-Aktionen auf account.move ===")
    for a in k18.kw("ir.actions.server", "search_read",
                    [[("model_id.model", "=", "account.move")],
                     ["id", "name", "state", "binding_model_id", "create_date"]],
                    order="id", context={"lang": "de_DE"}):
        print("   id=%-5s %-42s typ=%-10s angelegt=%s"
              % (a["id"], a["name"][:42], a["state"], (a["create_date"] or "")[:10]))

    print("\n=== Gegenueberstellung der Massenbearbeitung ===")
    massen = [a for a in k18.kw("ir.actions.server", "search_read",
                                [[("model_id.model", "=", "account.move"), ("state", "=", "mass_edit")],
                                 ["id", "name"]], order="id", context={"lang": "de_DE"})]
    print("   Odoo 11: %d Massenobjekte | Odoo 18: %d Massenbearbeitungs-Aktionen"
          % (len(treffer), len(massen)))
    for a in massen:
        print("      %s" % a["name"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
