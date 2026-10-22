"""Read-only Sofortbefund Zeiterfassung (Odoo 11 gegen Odoo 18 lokal/VM).

Aufruf:
  python scripts/zeiterfassung_sofort.py --quelle o11
Nur lesende RPC-Aufrufe.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quelle", required=True, choices=["o11", "lokal", "vm"])
    a = ap.parse_args()
    cli = o11() if a.quelle == "o11" else o18(a.quelle)

    print("### Quelle:", a.quelle)

    mods = cli.kw("ir.module.module", "search_read",
                  [[("state", "=", "installed"),
                    ("name", "in", ["hr_timesheet", "hr_timesheet_attendance", "project",
                                    "project_timesheet_holidays", "project_timesheet_time_control",
                                    "sale_timesheet", "sale_project", "sale_timesheet_rounded",
                                    "hr_timesheet_sheet", "analytic", "hr", "project_todo",
                                    "timesheet_grid", "helpdesk_mgmt_timesheet",
                                    "website_support_analytic_timesheets",
                                    "itk_projectcategory"])]],
                  fields=["name", "state", "installed_version"], order="name", limit=0)
    print("\n=== Module installiert ===")
    for m in mods:
        print("  %-45s %s" % (m["name"], m["installed_version"] or "-"))

    print("\n=== account.analytic.line: Felder (Anzahl) ===")
    f = cli.kw("account.analytic.line", "fields_get", [],
               attributes=["string", "type", "required", "readonly", "relation"])
    print("  Felder:", len(f))
    for name in ["date", "name", "unit_amount", "employee_id", "user_id", "project_id",
                 "task_id", "account_id", "amount", "company_id", "product_uom_id",
                 "sheet_id", "timesheet_invoice_type", "timesheet_invoice_id", "holiday_id",
                 "so_line", "timer_start", "department_id", "partner_id", "stage_id"]:
        if name in f:
            fd = f[name]
            print("  %-24s %-38s %-12s %s%s%s" % (name, (fd.get("string") or "")[:38], fd.get("type"),
                                                  "PFLICHT " if fd.get("required") else "",
                                                  "readonly " if fd.get("readonly") else "",
                                                  ("->" + str(fd.get("relation"))) if fd.get("relation") else ""))
        else:
            print("  %-24s -- nicht vorhanden --" % name)

    n = cli.kw("account.analytic.line", "search_count", [[]])
    print("\n=== Bestand account.analytic.line:", n)
    if "task_id" in f:
        print("  mit Aufgabe:", cli.kw("account.analytic.line", "search_count", [[("task_id", "!=", False)]]))
    if "employee_id" in f:
        print("  mit Mitarbeiter:", cli.kw("account.analytic.line", "search_count", [[("employee_id", "!=", False)]]))
    print("  Projekte project.project:", cli.kw("project.project", "search_count", [[]]))
    print("  Aufgaben project.task:", cli.kw("project.task", "search_count", [[]]))
    print("  Mitarbeiter hr.employee:", cli.kw("hr.employee", "search_count", [[]]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
