"""Read-only: XML-IDs fuer Menues/Aktionen/Ansichten des Bereichs Personal (Odoo 18 lokal).
Aufruf: python scripts/hr_xmlids.py [lokal|vm]"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

MODELLE = ["ir.ui.menu", "ir.actions.act_window", "ir.ui.view", "ir.model.access", "ir.rule"]


def haupt():
    instanz = sys.argv[1] if len(sys.argv) > 1 else "lokal"
    k = o18(instanz)
    for modell in MODELLE:
        ids = []
        if modell == "ir.ui.menu":
            ids = k.kw("ir.ui.menu", "search", [[("id", "<", 700)]])
        elif modell == "ir.actions.act_window":
            ids = k.kw("ir.actions.act_window", "search",
                       [[("res_model", "in", ["hr.employee", "hr.employee.public", "hr.department",
                                             "hr.job"])]])
        elif modell == "ir.ui.view":
            ids = k.kw("ir.ui.view", "search",
                       [[("model", "in", ["hr.employee", "hr.department", "hr.job"])]])
        elif modell == "ir.model.access":
            ids = k.kw("ir.model.access", "search", [[("name", "ilike", "hr.employee")]])
        else:
            ids = k.kw("ir.rule", "search", [[("name", "ilike", "Employee")]])
        if not ids:
            continue
        daten = k.kw("ir.model.data", "search_read",
                     [[("model", "=", modell), ("res_id", "in", ids)]],
                     fields=["module", "name", "res_id", "model"], order="res_id")
        if daten:
            print("=== %s ===" % modell)
            for d in daten:
                print("  %-4s %-22s %s.%s" % (d["res_id"], modell.replace("ir.", ""),
                                              d["module"], d["name"]))


if __name__ == "__main__":
    haupt()
