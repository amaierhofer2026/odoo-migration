"""Read-only Erhebung PERSONAL (Odoo 18, lokal/vm) - Felder, Ansichten, Menues, Aktionen, Rechte.
Aufruf: python scripts/hr_erhebe_o18.py lokal|vm
Schreibt JSON nach %LOCALAPPDATA%\\Temp\\hr_erhebung\\<instanz>_*.json."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

ZIEL = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Temp", "hr_erhebung")
CTX = {"lang": "de_DE"}


def sichere(name, daten):
    os.makedirs(ZIEL, exist_ok=True)
    pfad = os.path.join(ZIEL, name)
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, default=str)
    print("  -> %s (%d Bytes)" % (pfad, os.path.getsize(pfad)))


def felder(k, modell):
    return k.kw(modell, "fields_get", [[], ["string", "type", "relation", "required", "readonly",
                                            "store", "selection", "help", "searchable", "sortable",
                                            "depends", "digits", "size"]], context=CTX)


def haupt():
    instanz = sys.argv[1] if len(sys.argv) > 1 else "lokal"
    k = o18(instanz)
    print("Felder hr.employee ...")
    sichere("%s_felder_hr_employee.json" % instanz, felder(k, "hr.employee"))
    print("Felder hr.employee.public ...")
    sichere("%s_felder_hr_employee_public.json" % instanz, felder(k, "hr.employee.public"))
    for modell in ("hr.version", "hr.work.location"):
        try:
            print("Felder %s ..." % modell)
            sichere("%s_felder_%s.json" % (instanz, modell.replace(".", "_")), felder(k, modell))
        except Exception as exc:  # noqa: BLE001
            print("  %s nicht vorhanden: %s" % (modell, str(exc)[:80]))
    print("Stammdaten ...")
    stamm = {
        "departments": k.kw("hr.department", "search_read", [[]],
                            fields=["id", "name", "parent_id", "manager_id", "complete_name", "active"],
                            context=CTX, order="id"),
        "jobs": k.kw("hr.job", "search_read", [[]],
                     fields=["id", "name", "department_id", "expected_employees", "no_of_employee",
                             "description", "requirements", "active"], context=CTX, order="id"),
        "calendars": k.kw("resource.calendar", "search_read", [[]],
                          fields=["id", "name", "hours_per_day", "tz", "company_id", "active"],
                          context=dict(CTX, active_test=False), order="id"),
        "leave_types": k.kw("hr.leave.type", "search_read", [[]],
                            fields=["id", "name", "request_unit", "leave_validation_type",
                                    "requires_allocation", "active"], context=CTX, order="id"),
        "companies": k.kw("res.company", "search_read", [[]],
                          fields=["id", "name", "parent_id"], context=CTX),
        "tags": k.kw("hr.employee.category", "search_read", [[]], fields=["id", "name", "color"],
                     context=CTX),
        "work_locations": k.kw("hr.work.location", "search_read", [[]],
                               fields=["id", "name", "location_type", "address_id", "active"],
                               context=CTX),
    }
    sichere("%s_stammdaten.json" % instanz, stamm)
    print("Rechte ...")
    rechte = {
        "access": k.kw("ir.model.access", "search_read",
                       [[("model_id", "in", ["hr.employee", "hr.employee.public", "hr.department",
                                             "hr.job", "hr.leave", "hr.attendance"])]],
                       fields=["id", "name", "model_id", "group_id", "perm_read", "perm_write",
                               "perm_create", "perm_unlink"], context=CTX),
        "rules": k.kw("ir.rule", "search_read",
                      [[("model_id", "in", ["hr.employee", "hr.department", "hr.leave",
                                            "hr.attendance"])]],
                      fields=["id", "name", "model_id", "groups", "domain_force", "perm_read",
                              "perm_write", "perm_create", "perm_unlink", "active"], context=CTX),
        "gruppen_hr": k.kw("res.groups", "search_read",
                           [[("name", "ilike", "Mitarbeiter")]], fields=["id", "name", "category_id"],
                           context=CTX),
    }
    sichere("%s_rechte.json" % instanz, rechte)


if __name__ == "__main__":
    haupt()
