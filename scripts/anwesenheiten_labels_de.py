"""Deutsche Bezeichnungen im Bereich Urlaubsantraege/Anwesenheiten (Odoo-11-Wortlaut).

Das Modul itk_hr_leave_compat setzt die Basistexte der Menues und Aktionen; die
Oberflaeche liest aber den de_DE-Slot, der noch die Odoo-18-Bezeichnung enthaelt.
Dieses Skript schreibt die de_DE-Slots und prueft anschliessend die gerenderten
Ansichten (Spalten, Feldbeschriftungen, Filter) im Odoo-11-Wortlaut.

Aufruf:
    python scripts/anwesenheiten_labels_de.py --instanz lokal [--setzen]
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

DE = {"lang": "de_DE"}
EN = {"lang": "en_US"}

SLOTS = [
    ("ir.ui.menu", "hr_holidays.menu_hr_holidays_root", "Urlaubsanträge"),
    ("ir.ui.menu", "hr_holidays.menu_hr_holidays_my_leaves", "Mein Urlaubskonto"),
    ("ir.ui.menu", "hr_holidays.hr_leave_menu_my", "Urlaubsantrag"),
    ("ir.ui.menu", "hr_holidays.menu_open_allocation", "Urlaubsanspruch anfragen"),
    ("ir.ui.menu", "hr_holidays.menu_hr_holidays_management", "Zu bestätigender Urlaub"),
    ("ir.ui.menu", "hr_holidays.menu_open_department_leave_approve", "Urlaubsanträge"),
    ("ir.ui.menu", "hr_holidays.hr_holidays_menu_manager_approve_allocations", "Urlaubsanspruch"),
    ("ir.ui.menu", "hr_holidays.menu_hr_available_holidays_report_tree", "Urlaubdetails"),
    ("ir.ui.menu", "hr_attendance.menu_hr_attendance_view_attendances", "Anwesenheiten"),
    ("ir.ui.menu", "hr_attendance.menu_hr_attendance_reporting", "Anwesenheits-Analyse"),
    ("ir.actions.act_window", "hr_holidays.hr_leave_action_my", "Urlaubsantrag"),
    ("ir.actions.act_window", "hr_holidays.hr_leave_allocation_action_my", "Urlaubsanspruch anfragen"),
    ("ir.actions.act_window", "hr_holidays.hr_leave_action_action_approve_department", "Urlaubsanträge"),
    ("ir.actions.act_window", "hr_holidays.hr_leave_allocation_action_approve_department", "Urlaubsanspruch"),
    ("ir.actions.act_window", "hr_holidays.action_hr_available_holidays_report", "Urlaubdetails"),
    ("ir.actions.act_window", "hr_attendance.hr_attendance_reporting", "Anwesenheits-Analyse"),
]

ANSICHTEN = [
    ("hr.attendance", "hr_attendance.view_attendance_tree", "list", "check_in", "Check In"),
    ("hr.attendance", "hr_attendance.view_attendance_tree", "list", "check_out", "Check Out"),
    ("hr.attendance", "hr_attendance.view_attendance_tree", "list", "x_homeoffice", "Home-Office"),
    ("hr.attendance", "hr_attendance.hr_attendance_view_form", "form", "x_homeoffice", "Home-Office"),
    ("hr.leave", "hr_holidays.hr_leave_view_tree", "list", "x_o11_number_of_days", "Anzahl der Tage (Odoo 11)"),
    ("hr.leave", "hr_holidays.hr_leave_view_tree", "list", "holiday_status_id", "Abwesenheitstyp"),
    ("hr.leave", "hr_holidays.hr_leave_view_form", "form", "x_o11_number_of_days", "Anzahl der Tage (Odoo 11)"),
    ("hr.leave", "hr_holidays.hr_leave_view_form", "form", "holiday_status_id", "Abwesenheitstyp"),
]

FILTER = [
    ("hr.leave", "hr_holidays.hr_leave_view_search_manager", "search", "Zur Genehmigung"),
    ("hr.leave", "hr_holidays.hr_leave_view_search_manager", "search", "Aktive Typen"),
    ("hr.leave", "hr_holidays.hr_leave_view_search_manager", "search", "Urlaube meiner Abteilung"),
    ("hr.leave", "hr_holidays.hr_leave_view_search_manager", "search", "Mein Teamurlaub"),
    ("hr.leave", "hr_holidays.hr_leave_view_search_manager", "search", "Prüfer"),
    ("hr.attendance", "hr_attendance.hr_attendance_view_filter", "search", "Home-Office"),
]


def rec_id(k, xmlid):
    modul, name = xmlid.split(".")
    treffer = k.kw("ir.model.data", "search_read",
                   [[("module", "=", modul), ("name", "=", name)], ["res_id", "model"]], context=DE)
    return treffer[0] if treffer else None


def arch(k, xmlid, typ):
    d = rec_id(k, xmlid)
    if not d:
        return ""
    r = k.kw("ir.ui.view", "get_views", [[[d["res_id"], typ]]], context=DE)
    return r["views"].get(typ, {}).get("arch", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    ap.add_argument("--setzen", action="store_true")
    a = ap.parse_args()
    k = o18(a.instanz)
    offen = []

    print("=== de_DE-Slots Menues/Aktionen ===")
    for modell, xmlid, text in SLOTS:
        d = rec_id(k, xmlid)
        if not d:
            print("  %-58s XML-ID FEHLT" % xmlid)
            offen.append(xmlid)
            continue
        rid = d["res_id"]
        de = k.kw(modell, "read", [[rid], ["name"]], context=DE)[0]["name"]
        zustand = "OK" if de == text else "SETZEN"
        print("  %-56s de=%-26r %s" % (xmlid[-56:], de, zustand))
        if a.setzen and de != text:
            k.kw(modell, "write", [[rid], {"name": text}], context=DE)
            neu = k.kw(modell, "read", [[rid], ["name"]], context=DE)[0]["name"]
            print("        -> jetzt de=%r" % neu)
            if neu != text:
                offen.append(xmlid)
        elif de != text:
            offen.append(xmlid)

    print("\n=== Gerenderte Ansichten: Feldbeschriftungen ===")
    for modell, xmlid, typ, feld, soll in ANSICHTEN:
        a_text = arch(k, xmlid, typ)
        treffer = re.search(r"<field[^>]*name=\"%s\"[^>]*>" % re.escape(feld), a_text)
        if not treffer:
            print("  %-40s %-26s FELD NICHT IN DER ANSICHT" % (xmlid[-40:], feld))
            offen.append("%s.%s" % (xmlid, feld))
            continue
        knoten = treffer.group(0)
        m = re.search(r'string="([^"]*)"', knoten)
        ist = m.group(1) if m else ""
        ok = (ist == soll)
        if not ok and not ist:
            meta = k.kw(modell, "fields_get", [[feld], ["string"]], context=DE)[feld]["string"]
            ok = (meta == soll)
            ist = meta
        print("  %-40s %-26s = %-32r %s" % (xmlid[-40:], feld, ist, "OK" if ok else "ABWEICHUNG"))
        if not ok:
            offen.append("%s.%s" % (xmlid, feld))

    print("\n=== Gerenderte Suchansichten: Filter und Gruppierungen ===")
    for modell, xmlid, typ, text in FILTER:
        a_text = arch(k, xmlid, typ)
        ok = ('string="%s"' % text) in a_text
        print("  %-40s %-28s %s" % (xmlid[-40:], text, "OK" if ok else "FEHLT"))
        if not ok:
            offen.append("%s/%s" % (xmlid, text))

    print("\n=== Ergebnis:", "0 offen" if not offen else "%d offen" % len(offen), "===")
    for x in offen:
        print("   -", x)
    return 0 if not offen else 1


if __name__ == "__main__":
    sys.exit(main())
