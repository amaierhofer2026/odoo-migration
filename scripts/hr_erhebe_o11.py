"""Read-only Erhebung PERSONAL (Odoo 11 Prod) - Felder, Ansichten, Menues, Aktionen, Rechte.
Schreibt JSON nach %LOCALAPPDATA%\\Temp\\hr_erhebung\\o11_*.json. Keine Schreibzugriffe."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

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


def ansichten(k, modell, ist_o11=True):
    felder_liste = ["id", "name", "type", "priority", "mode", "active", "inherit_id", "model",
                    "arch_db" if ist_o11 else "arch"]
    return k.kw("ir.ui.view", "search_read", [[("model", "=", modell)]], fields=felder_liste,
                context=CTX, order="priority,id")


def menues(k, wurzel_name_re):
    wurzeln = k.kw("ir.ui.menu", "search_read", [[("name", "ilike", wurzel_name_re)]],
                   fields=["id", "name", "parent_id", "sequence", "action", "complete_name"],
                   context=CTX)
    ergebnis = []
    for w in wurzeln:
        ergebnis.append(dict(w, kinder=k.kw("ir.ui.menu", "search_read",
                                            [[("parent_id", "child_of", w["id"])]],
                                            fields=["id", "name", "parent_id", "sequence", "action",
                                                    "complete_name"], context=CTX, order="sequence,id")))
    return ergebnis


def haupt():
    k = o11()
    print("Felder hr.employee ...")
    sichere("o11_felder_hr_employee.json", felder(k, "hr.employee"))
    print("Felder hr.employee.public ...")
    try:
        sichere("o11_felder_hr_employee_public.json", felder(k, "hr.employee.public"))
    except Exception as exc:  # noqa: BLE001
        print("  kein hr.employee.public: %s" % str(exc)[:80])
    print("Ansichten hr.employee ...")
    sichere("o11_views_hr_employee.json", ansichten(k, "hr.employee"))
    print("Ansichten hr.department / hr.job ...")
    sichere("o11_views_hr_department.json", ansichten(k, "hr.department"))
    sichere("o11_views_hr_job.json", ansichten(k, "hr.job"))
    print("Menues Personal ...")
    sichere("o11_menues.json", menues(k, "Personal"))
    print("Menues Mitarbeiter ...")
    sichere("o11_menues_mitarbeiter.json", menues(k, "Mitarbeiter"))
    print("Aktionen ...")
    akt = k.kw("ir.actions.act_window", "search_read",
               [[("res_model", "in", ["hr.employee", "hr.department", "hr.job", "hr.holidays",
                                     "hr.attendance", "hr.contract"])]],
               fields=["id", "name", "res_model", "view_mode", "domain", "context", "help"],
               context=CTX, order="res_model,id")
    sichere("o11_aktionen.json", akt)
    print("Stammdaten ...")
    stamm = {
        "departments": k.kw("hr.department", "search_read", [[]],
                            fields=["id", "name", "parent_id", "manager_id", "complete_name", "active"],
                            context=CTX, order="id"),
        "jobs": k.kw("hr.job", "search_read", [[]],
                     fields=["id", "name", "department_id", "expected_employees", "no_of_employee",
                             "description", "requirements", "active"], context=CTX, order="id"),
        "calendars": k.kw("resource.calendar", "search_read", [[]],
                          fields=["id", "name", "hours_per_day", "tz", "company_id"],
                          context=CTX, order="id"),
        "leave_types": k.kw("hr.holidays.status", "search_read", [[]],
                            fields=["id", "name", "limit", "leaves_taken", "remaining_leaves",
                                    "color_name", "active"], context=CTX, order="id"),
        "companies": k.kw("res.company", "search_read", [[]],
                          fields=["id", "name", "parent_id"], context=CTX),
    }
    sichere("o11_stammdaten.json", stamm)
    print("Rechte ...")
    rechte = {
        "access": k.kw("ir.model.access", "search_read",
                       [[("model_id", "in", ["hr.employee", "hr.employee.public", "hr.department",
                                             "hr.job", "hr.holidays", "hr.attendance"])]],
                       fields=["id", "name", "model_id", "group_id", "perm_read", "perm_write",
                               "perm_create", "perm_unlink"], context=CTX),
        "rules": k.kw("ir.rule", "search_read",
                      [[("model_id", "in", ["hr.employee", "hr.department", "hr.holidays",
                                            "hr.attendance"])]],
                      fields=["id", "name", "model_id", "groups", "domain_force", "perm_read",
                              "perm_write", "perm_create", "perm_unlink", "active"], context=CTX),
        "gruppen": k.kw("res.groups", "search_read",
                        [[("name", "ilike", "Mitarbeiter")]], fields=["id", "name", "category_id"],
                        context=CTX),
    }
    sichere("o11_rechte.json", rechte)


if __name__ == "__main__":
    haupt()
