"""Rechte im Bereich Urlaubsantraege/Anwesenheiten auf den Odoo-11-Stand bringen.

Odoo 11 fuehrt vier Gruppen, die Odoo 18 nicht 1:1 kennt:

  Odoo 11                                     Odoo 18
  Gruppe 34 "Anwesenheit manuell"      ->     itk_hr_leave_compat.group_itk_anwesenheit_manuell
  Gruppe 32 "Aufsicht"                 ->     hr_attendance.group_hr_attendance_manager
  Gruppe 79 "Personalsachbearbeiter"   ->     hr_holidays.group_hr_holidays_user
  Gruppe 80 "Manager"                  ->     hr_holidays.group_hr_holidays_manager

Zuordnung der Benutzer ausschliesslich ueber den Login (nicht ueber IDs).
Odoo 11 wird nur gelesen.

Aufruf:
    python scripts/anwesenheiten_rechte.py --instanz lokal|vm [--setzen]
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

DE = {"lang": "de_DE"}
ZUORDNUNG = [
    (34, "itk_hr_leave_compat.group_itk_anwesenheit_manuell", "Anwesenheit manuell"),
    (32, "hr_attendance.group_hr_attendance_manager", "Anwesenheiten / Administrator"),
    (79, "hr_holidays.group_hr_holidays_user", "Abwesenheiten / Sachbearbeiter"),
    (80, "hr_holidays.group_hr_holidays_manager", "Abwesenheiten / Administrator"),
]


def rec_id(k, xmlid):
    modul, name = xmlid.split(".")
    d = k.kw("ir.model.data", "search_read", [[("module", "=", modul), ("name", "=", name)],
                                             ["res_id"]], context=DE)
    return d[0]["res_id"] if d else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    ap.add_argument("--setzen", action="store_true")
    a = ap.parse_args()
    k11 = o11()
    k18 = o18(a.instanz)
    ctx = dict(DE, active_test=False)

    u11 = k11.kw("res.users", "search_read", [[], ["id", "login", "name", "groups_id"]],
                 context=ctx, order="id")
    u18 = k18.kw("res.users", "search_read", [[], ["id", "login", "name", "groups_id", "share"]],
                 context=ctx, order="id")
    nach_login = {u["login"].strip().lower(): u for u in u18}
    offen = []
    print("Instanz %s - %s" % (a.instanz, "SCHREIBEN" if a.setzen else "TROCKENLAUF"))
    print("  Odoo 11: %d Benutzer | Odoo 18: %d Benutzer" % (len(u11), len(u18)))

    for o11_gid, xmlid, bezeichnung in ZUORDNUNG:
        ziel_gid = rec_id(k18, xmlid)
        if not ziel_gid:
            print("  Gruppe %s nicht gefunden" % xmlid)
            offen.append(xmlid)
            continue
        soll = [u for u in u11 if o11_gid in u["groups_id"]]
        fehlt, vorhanden, ohne_login = [], [], []
        for u in soll:
            z = nach_login.get(u["login"].strip().lower())
            if not z:
                ohne_login.append(u["login"])
                continue
            if z["share"]:
                ohne_login.append("%s (Portalbenutzer in Odoo 18)" % u["login"])
                continue
            if ziel_gid in z["groups_id"]:
                vorhanden.append(z["login"])
            else:
                fehlt.append(z)
        print("\n  Odoo-11-Gruppe %d -> %s (%s)" % (o11_gid, xmlid, bezeichnung))
        print("    Mitglieder Odoo 11: %d | in Odoo 18 schon vorhanden: %d | zu setzen: %d | ohne Gegenstueck: %d"
              % (len(soll), len(vorhanden), len(fehlt), len(ohne_login)))
        if fehlt:
            print("    zu setzen: %s" % ", ".join(sorted(z["login"] for z in fehlt)))
        if ohne_login:
            print("    ohne Odoo-18-Benutzer: %s" % ", ".join(sorted(ohne_login)[:12]))
        if a.setzen and fehlt:
            k18.kw("res.users", "write", [[z["id"] for z in fehlt],
                                          {"groups_id": [(4, ziel_gid)]}])
            nach = k18.kw("res.groups", "read", [[ziel_gid], ["users"]], context=DE)[0]["users"]
            print("    -> Gruppe hat jetzt %d Benutzer" % len(nach))

    # Gegenprobe: niemand ohne Odoo-11-Vorbild in der neuen Gruppe
    ziel_gid = rec_id(k18, "itk_hr_leave_compat.group_itk_anwesenheit_manuell")
    if ziel_gid:
        mitglieder = k18.kw("res.users", "search_read", [[("groups_id", "in", [ziel_gid])],
                                                         ["login"]], context=DE)
        soll_logins = {u["login"].strip().lower() for u in u11 if 34 in u["groups_id"]}
        fremd = [m["login"] for m in mitglieder if m["login"].strip().lower() not in soll_logins]
        print("\n  Mitglieder 'Anwesenheit manuell': %d" % len(mitglieder))
        if fremd:
            print("    NICHT aus Odoo 11: %s" % fremd)
            offen.append("fremde Mitglieder")

    print("\n=== Ergebnis:", "0 offen" if not offen else "%d offen" % len(offen), "===")
    return 0 if not offen else 1


if __name__ == "__main__":
    sys.exit(main())
