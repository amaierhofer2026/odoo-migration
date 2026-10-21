"""Read-only: Zugriffsrechte PERSONAL je Instanz (ir.model.access + ir.rule + Gruppen der Menues).
Aufruf: python scripts/hr_rechte.py o11|lokal|vm"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
MODELLE = ["hr.employee", "hr.employee.public", "hr.department", "hr.job",
           "hr.employee.category", "hr.leave", "hr.holidays", "hr.attendance"]


def haupt():
    instanz = sys.argv[1] if len(sys.argv) > 1 else "lokal"
    k = o11() if instanz == "o11" else o18(instanz)
    ids = []
    for m in MODELLE:
        try:
            ids += k.kw("ir.model", "search", [[("model", "=", m)]], context=CTX)
        except Exception:  # noqa: BLE001
            pass
    print("=== %s: ir.model.access fuer %s ===" % (instanz, ", ".join(MODELLE)))
    acc = k.kw("ir.model.access", "search_read", [[("model_id", "in", ids)]],
               fields=["name", "model_id", "group_id", "perm_read", "perm_write", "perm_create",
                       "perm_unlink"], context=CTX)
    for a in sorted(acc, key=lambda x: (str(x["model_id"]), str(x["group_id"]))):
        print("  %-34s %-20s grp=%-34s r=%s w=%s c=%s u=%s" % (
            str(a["name"])[:34], str(a["model_id"])[:20], str(a["group_id"])[:34],
            a["perm_read"], a["perm_write"], a["perm_create"], a["perm_unlink"]))
    print("\n=== %s: ir.rule ===" % instanz)
    rul = k.kw("ir.rule", "search_read", [[("model_id", "in", ids)]],
               fields=["name", "model_id", "groups", "domain_force", "active"], context=CTX)
    for r in rul:
        print("  %-44s %-20s grp=%-24s dom=%s" % (str(r["name"])[:44], str(r["model_id"])[:20],
                                                  str(r.get("groups"))[:24],
                                                  str(r["domain_force"]).replace("\n", " ")[:100]))
    print("\n=== %s: Gruppen der Personal-Menues ===" % instanz)
    for name in ("Personal", "Mitarbeiter", "Abteilungen", "Verzeichnis"):
        try:
            men = k.kw("ir.ui.menu", "search_read", [[("name", "=", name)]],
                       fields=["id", "name", "complete_name", "groups_id", "action"], context=CTX)
            for m in men:
                print("  %-40s grp=%s act=%s" % (m["complete_name"], m["groups_id"], m["action"]))
        except Exception as exc:  # noqa: BLE001
            print("  %s: %s" % (name, str(exc)[:60]))


if __name__ == "__main__":
    haupt()
