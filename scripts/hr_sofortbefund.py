"""Read-only Sofortbefund PERSONAL: welche HR-Module sind in Odoo 11 und Odoo 18 installiert,
wie viele Mitarbeiter/Datensaetze gibt es. Keine Schreibzugriffe."""
from __future__ import annotations

import json
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from _o11o18_client import o11, o18  # noqa: E402

HR_MODULE = ["hr", "hr_contract", "hr_holidays", "hr_attendance", "hr_recruitment",
             "hr_timesheet", "hr_expense", "hr_payroll", "hr_org_chart", "hr_employee_firstname",
             "hr_holidays_public", "hr_gamification", "hr_skills", "hr_maintenance",
             "itk_*hr*", "partner_firstname", "resource"]

MODELS = ["hr.employee", "hr.department", "hr.job", "hr.contract", "hr.attendance",
          "hr.leave", "hr.leave.type", "hr.leave.allocation", "resource.resource",
          "resource.calendar", "hr.employee.public", "hr.work.location", "hr.version",
          "res.users", "res.partner"]


def modulstand(k, label):
    print("=== MODULE %s ===" % label)
    try:
        mods = k.kw("ir.module.module", "search_read",
                    [[("name", "like", "hr")], ["name", "state", "installed_version", "shortdesc"]],
                    context={"lang": "de_DE"})
        for m in sorted(mods, key=lambda x: x["name"]):
            if m["state"] in ("installed", "to upgrade", "to install"):
                print("  %-28s %-12s %s" % (m["name"], m["state"], m.get("installed_version") or ""))
        print("  (Summe hr-Module installiert: %d)" % sum(1 for m in mods if m["state"] == "installed"))
    except Exception as exc:  # noqa: BLE001
        print("  FEHLER %s" % exc)


def zaehlungen(k, label):
    print("=== ZAEHLUNGEN %s ===" % label)
    for modell in MODELS:
        try:
            aktiv = k.kw(modell, "search_count", [[]])
            gesamt = k.kw(modell, "search_count", [[]], context={"active_test": False})
            print("  %-24s aktiv=%-6s gesamt=%-6s" % (modell, aktiv, gesamt))
        except Exception as exc:  # noqa: BLE001
            print("  %-24s FEHLT/FEHLER: %s" % (modell, str(exc)[:90]))


def main():
    for label, fabrik in (("ODOO 11 PROD", o11), ("ODOO 18 LOKAL", lambda: o18("lokal"))):
        try:
            k = fabrik()
        except Exception as exc:  # noqa: BLE001
            print("=== %s: LOGIN FEHLGESCHLAGEN: %s" % (label, str(exc)[:300]))
            continue
        print("\n########## %s ##########" % label)
        modulstand(k, label)
        zaehlungen(k, label)


if __name__ == "__main__":
    main()
