"""Read-only: Benutzer und Mitarbeiterdetails in Odoo 18 (lokal/vm) fuer den Abgleich.
Aufruf: python scripts/hr_detail_o18.py lokal|vm"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

ZIEL = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Temp", "hr_erhebung")
CTX = {"lang": "de_DE"}
FELDER = ["id", "name", "firstname", "lastname", "active", "gender", "marital", "birthday",
          "country_id", "identification_id", "passport_id", "visa_no", "permit_no", "visa_expire",
          "sinid", "ssnid", "bank_account_id", "work_contact_id", "work_email", "work_phone",
          "mobile_phone", "work_location_id", "work_location_name", "notes", "additional_note",
          "barcode", "pin", "department_id", "job_id", "parent_id", "coach_id", "user_id",
          "company_id", "resource_calendar_id", "category_ids", "hourly_cost", "employee_type",
          "create_date", "private_street", "private_city", "private_zip", "private_country_id",
          "private_email", "private_phone", "job_title", "tz", "lang"]


def sichere(name, daten):
    os.makedirs(ZIEL, exist_ok=True)
    pfad = os.path.join(ZIEL, name)
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, default=str)
    print("  -> %s (%d Bytes)" % (pfad, os.path.getsize(pfad)))


def haupt():
    instanz = sys.argv[1] if len(sys.argv) > 1 else "lokal"
    k = o18(instanz)
    ids = k.kw("hr.employee", "search", [[]], context=dict(CTX, active_test=False), order="id")
    ma = k.kw("hr.employee", "read", [ids, FELDER], context=dict(CTX, active_test=False))
    sichere("%s_detail_mitarbeiter.json" % instanz, ma)
    ben = k.kw("res.users", "search_read", [[]], fields=["id", "login", "name", "active", "share"],
               context=dict(CTX, active_test=False), order="id")
    sichere("%s_detail_benutzer.json" % instanz, ben)
    kal = k.kw("resource.calendar", "search_read", [[]],
               fields=["id", "name", "hours_per_day", "tz", "company_id", "full_time_required_hours"],
               context=CTX)
    zeiten = k.kw("resource.calendar.attendance", "search_read", [[]],
                  fields=["id", "name", "calendar_id", "dayofweek", "hour_from", "hour_to",
                          "day_period"], context=CTX, order="calendar_id,dayofweek,hour_from")
    sichere("%s_detail_kalender.json" % instanz, {"kalender": kal, "zeiten": zeiten})
    print("  Urlaub:", k.kw("hr.leave", "search_count", [[]]),
          " Anwesenheit:", k.kw("hr.attendance", "search_count", [[]]),
          " Zeiterfassung:", k.kw("account.analytic.line", "search_count", [[]]))


if __name__ == "__main__":
    haupt()
