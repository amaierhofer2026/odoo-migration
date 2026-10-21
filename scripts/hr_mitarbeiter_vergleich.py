"""Read-only Vergleich der Mitarbeiterstaemme Odoo 11 vs Odoo 18 (lok) - Namen, Abteilung, Stelle,
Benutzer, Firma, Arbeits-E-Mail. Keine Schreibzugriffe."""
from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}


def namen_wert(v):
    return v[1] if isinstance(v, (list, tuple)) else v


def liste(k, label):
    felder = ["id", "name", "active", "department_id", "job_id", "user_id", "company_id",
              "work_email", "identification_id", "parent_id", "coach_id", "resource_calendar_id"]
    da = k.kw("hr.employee", "search_read", [[]], fields=felder,
              context=dict(CTX, active_test=False), order="id")
    print("=== %s: %d Mitarbeiter (inkl. archiviert) ===" % (label, len(da)))
    for d in da:
        print("  %4s %-34s act=%-5s abt=%-22s stelle=%-26s benutzer=%-22s firma=%-14s mail=%s" % (
            d["id"], (d["name"] or "")[:34], d["active"],
            str(namen_wert(d.get("department_id")))[:22],
            str(namen_wert(d.get("job_id")))[:26],
            str(namen_wert(d.get("user_id")))[:22],
            str(namen_wert(d.get("company_id")))[:14],
            d.get("work_email") or "-"))
    return da


def haupt():
    k11 = o11()
    k18 = o18("lokal")
    e11 = liste(k11, "ODOO 11 PROD")
    e18 = liste(k18, "ODOO 18 LOKAL")

    s11 = {(e["name"] or "").strip() for e in e11}
    s18 = {(e["name"] or "").strip() for e in e18}
    print("\n=== NAMENSVERGLEICH ===")
    print("nur in O11 (%d): %s" % (len(s11 - s18), sorted(s11 - s18)))
    print("nur in O18 (%d): %s" % (len(s18 - s11), sorted(s18 - s11)))
    print("in beiden   (%d)" % len(s11 & s18))

    for k, label in ((k11, "O11"), (k18, "O18")):
        print("\n=== HR-MODELLE %s ===" % label)
        for m in ("hr.holidays", "hr.holidays.status", "hr.leave", "hr.leave.type",
                  "hr.contract", "hr.timesheet", "account.analytic.line", "hr.attendance"):
            try:
                print("  %-24s %s" % (m, k.kw(m, "search_count", [[]])))
            except Exception as exc:  # noqa: BLE001
                print("  %-24s FEHLT" % m)


if __name__ == "__main__":
    haupt()
