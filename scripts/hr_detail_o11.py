"""Read-only Detailerhebung PERSONAL Odoo 11: Mitarbeiterdetails, Benutzer, Tags, Arbeitsplaene
mit Zeiten, Urlaubsantraege/Anwesenheiten je Mitarbeiter und Jahr.
Schreibt JSON nach %LOCALAPPDATA%\\Temp\\hr_erhebung\\o11_detail_*.json."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11  # noqa: E402

ZIEL = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Temp", "hr_erhebung")
CTX = {"lang": "de_DE"}


def sichere(name, daten):
    os.makedirs(ZIEL, exist_ok=True)
    pfad = os.path.join(ZIEL, name)
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, default=str)
    print("  -> %s (%d Bytes)" % (pfad, os.path.getsize(pfad)))


FELDER = ["id", "name", "firstname", "lastname", "active", "gender", "marital", "birthday",
          "country_id", "identification_id", "passport_id", "visa_no", "permit_no", "visa_expire",
          "sinid", "ssnid", "bank_account_id", "address_id", "address_home_id", "work_email",
          "work_phone", "mobile_phone", "work_location", "notes", "barcode", "pin",
          "department_id", "job_id", "parent_id", "coach_id", "user_id", "company_id",
          "resource_calendar_id", "category_ids", "timesheet_cost", "create_date"]


def haupt():
    k = o11()
    print("Mitarbeiterdetails ...")
    ids = k.kw("hr.employee", "search", [[]], context=dict(CTX, active_test=False), order="id")
    ma = k.kw("hr.employee", "read", [ids, FELDER], context=dict(CTX, active_test=False))
    sichere("o11_detail_mitarbeiter.json", ma)

    print("Benutzer ...")
    ben = k.kw("res.users", "search_read", [[]], fields=["id", "login", "name", "active", "share"],
               context=dict(CTX, active_test=False), order="id")
    sichere("o11_detail_benutzer.json", ben)

    print("Tags (hr.employee.category) ...")
    tags = k.kw("hr.employee.category", "search_read", [[]], fields=["id", "name", "color"],
                context=dict(CTX, active_test=False))
    for t in tags:
        t["mitarbeiter"] = k.kw("hr.employee", "search_count",
                                [[("category_ids", "in", [t["id"]])]],
                                context=dict(CTX, active_test=False))
    sichere("o11_detail_tags.json", tags)

    print("Arbeitsplaene + Zeiten ...")
    kal = k.kw("resource.calendar", "search_read", [[]],
               fields=["id", "name", "hours_per_day", "tz", "company_id", "full_time_required_hours"],
               context=CTX)
    zeiten = k.kw("resource.calendar.attendance", "search_read", [[]],
                  fields=["id", "name", "calendar_id", "dayofweek", "hour_from", "hour_to",
                          "day_period"], context=CTX, order="calendar_id,dayofweek,hour_from")
    sichere("o11_detail_kalender.json", {"kalender": kal, "zeiten": zeiten})

    print("Urlaubsantraege (hr.holidays) ...")
    urlaub = k.kw("hr.holidays", "search_read", [[]],
                  fields=["id", "name", "employee_id", "holiday_status_id", "date_from", "date_to",
                          "number_of_days_temp", "number_of_days", "state", "type", "holiday_type",
                          "department_id", "create_date"],
                  context=dict(CTX, active_test=False), order="id")
    sichere("o11_detail_urlaub.json", urlaub)

    print("Anwesenheiten (hr.attendance) ...")
    anw = k.kw("hr.attendance", "search_read", [[]],
               fields=["id", "employee_id", "check_in", "check_out", "worked_hours"],
               context=CTX, order="id")
    sichere("o11_detail_anwesenheit.json", anw)

    print("Zeiterfassung mit Mitarbeiterbezug ...")
    print("  analytic.line gesamt:", k.kw("account.analytic.line", "search_count", [[]]))
    print("  analytic.line mit employee_id:",
          k.kw("account.analytic.line", "search_count", [[("employee_id", "!=", False)]]))


if __name__ == "__main__":
    haupt()
