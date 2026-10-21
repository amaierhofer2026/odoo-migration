"""Read-only Detailabfragen PERSONAL: Aktionen, Gruppen, Abteilungs-/Stellenansichten.
Aufruf: python scripts/hr_aktionen.py o11|lokal|vm"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}


def haupt():
    instanz = sys.argv[1] if len(sys.argv) > 1 else "lokal"
    ist_o11 = instanz == "o11"
    k = o11() if ist_o11 else o18(instanz)
    print("=== Aktionen Personal (act_window) ===")
    akt = k.kw("ir.actions.act_window", "search_read",
               [[("res_model", "in", ["hr.employee", "hr.employee.public", "hr.department",
                                     "hr.job", "hr.holidays", "hr.leave", "hr.attendance"])]],
               fields=["id", "name", "res_model", "view_mode", "domain", "context"],
               context=CTX, order="res_model,id")
    for a in akt:
        print("  %-4s %-38s %-20s mode=%-16s dom=%s ctx=%s" % (
            a["id"], str(a["name"])[:38], a["res_model"], a["view_mode"],
            str(a["domain"])[:40], str(a["context"])[:50]))
    print("\n=== Gruppen Personal ===")
    grp = k.kw("res.groups", "search_read",
               [[("name", "ilike", "Personal")]], fields=["id", "name", "category_id"], context=CTX)
    for g in grp:
        print("  %s %s %s" % (g["id"], g["name"], g["category_id"]))
    if ist_o11:
        for gid in (13, 14, 32, 34, 79):
            try:
                g = k.kw("res.groups", "read", [[gid], ["name", "category_id"]], context=CTX)
                print("  Gruppe %s: %s" % (gid, g))
            except Exception as exc:  # noqa: BLE001
                print("  Gruppe %s: %s" % (gid, str(exc)[:60]))
    print("\n=== Ansichten hr.department / hr.job (Typen) ===")
    for modell in ("hr.department", "hr.job"):
        v = k.kw("ir.ui.view", "search_read", [[("model", "=", modell)]],
                 fields=["id", "name", "type", "priority", "mode"], context=CTX)
        for x in v:
            print("  %-20s %-4s %-8s prio=%-4s %s" % (modell, x["id"], x["type"], x["priority"], x["name"]))


if __name__ == "__main__":
    haupt()
