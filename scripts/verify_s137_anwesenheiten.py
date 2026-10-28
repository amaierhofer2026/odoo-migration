"""Abnahme Anwesenheiten und Urlaubsantraege: Odoo 11 (read-only) gegen Odoo 18.

Prueft Struktur (Menues, Ansichten, Filter, Rechte) und Daten (Multimengen,
Status, Tagesanzahl, Beschreibung, Genehmiger, Homeoffice, Arbeitsstunden).

Aufruf:
    python scripts/verify_s137_anwesenheiten.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

DE = {"lang": "de_DE"}
EN = {"lang": "en_US"}

ok = 0
fehler = []


def pruefe(bedingung, text, ist=None, soll=None):
    global ok
    if bedingung:
        ok += 1
    else:
        fehler.append("%s%s%s" % (text,
                                  "" if ist is None else " | ist=%r" % (ist,),
                                  "" if soll is None else " | soll=%r" % (soll,)))


def nt(s):
    return " ".join((s or "").split())


def nn(s):
    return nt(s).lower()


def rec_id(k, xmlid):
    modul, name = xmlid.split(".")
    d = k.kw("ir.model.data", "search_read",
             [[("module", "=", modul), ("name", "=", name)], ["res_id"]], context=DE)
    return d[0]["res_id"] if d else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = ap.parse_args()
    k11 = o11()
    k18 = o18(a.instanz)
    ctx11 = dict(DE, active_test=False)
    ctx18 = dict(DE, active_test=False)

    print("=== Abnahme Anwesenheiten/Urlaubsantraege (%s) ===" % a.instanz)

    # ---------------------------------------------------------------- Struktur
    modul = k18.kw("ir.module.module", "search_read", [[("name", "=", "itk_hr_leave_compat")],
                   ["name", "state", "latest_version"]], context=DE)
    pruefe(bool(modul) and modul[0]["state"] == "installed",
           "Modul itk_hr_leave_compat installiert", modul and modul[0]["state"], "installed")
    if modul:
        print("  Modulstand itk_hr_leave_compat:", modul[0]["latest_version"])

    menues = [("hr_holidays.menu_hr_holidays_root", "Urlaubsanträge"),
              ("hr_holidays.menu_hr_holidays_my_leaves", "Mein Urlaubskonto"),
              ("hr_holidays.hr_leave_menu_my", "Urlaubsantrag"),
              ("hr_holidays.menu_open_allocation", "Urlaubsanspruch anfragen"),
              ("hr_holidays.menu_hr_holidays_management", "Zu bestätigender Urlaub"),
              ("hr_holidays.menu_open_department_leave_approve", "Urlaubsanträge"),
              ("hr_holidays.hr_holidays_menu_manager_approve_allocations", "Urlaubsanspruch"),
              ("hr_holidays.menu_hr_available_holidays_report_tree", "Urlaubdetails"),
              ("hr_attendance.menu_hr_attendance_view_attendances", "Anwesenheiten"),
              ("hr_attendance.menu_hr_attendance_reporting", "Anwesenheits-Analyse")]
    for xmlid, soll in menues:
        rid = rec_id(k18, xmlid)
        ist = k18.kw("ir.ui.menu", "read", [[rid], ["name"]], context=DE)[0]["name"] if rid else None
        pruefe(ist == soll, "Menue %s" % xmlid, ist, soll)

    # eigene Menues (Urlaubskonto/Berichte)
    for name, eltern in (("Auswertung Urlaubskonto", "hr_holidays.menu_hr_holidays_my_leaves"),
                         ("Urlaubsanträge", "hr_holidays.menu_hr_holidays_report"),
                         ("Urlaub nach Abteilung", "hr_holidays.menu_hr_holidays_report")):
        pid = rec_id(k18, eltern)
        treffer = k18.kw("ir.ui.menu", "search_read", [[("name", "=", name), ("parent_id", "=", pid)],
                                                        ["id", "action"]], context=DE)
        pruefe(bool(treffer), "Menue %s unter %s" % (name, eltern), bool(treffer), True)
        if treffer:
            pruefe(bool(treffer[0]["action"]),
                   "Menue %s hat eine Aktion" % name, treffer[0]["action"], "Aktion")

    # Ansichten: Spalten und Beschriftungen
    def arch(xmlid, typ):
        rid = rec_id(k18, xmlid)
        if not rid:
            return ""
        return k18.kw("ir.ui.view", "get_views", [[[rid, typ]]], context=DE)["views"][typ]["arch"]

    a_att = arch("hr_attendance.view_attendance_tree", "list")
    pruefe('name="x_homeoffice"' in a_att, "Liste Anwesenheiten: Spalte Home-Office")
    pruefe('string="Check In"' in a_att, "Liste Anwesenheiten: Spalte Check In")
    a_lv = arch("hr_holidays.hr_leave_view_tree", "list")
    pruefe('name="x_o11_number_of_days"' in a_lv, "Liste Abwesenheiten: Spalte Anzahl der Tage (Odoo 11)")
    pruefe('string="Abwesenheitstyp"' in a_lv, "Liste Abwesenheiten: Spalte Abwesenheitstyp")
    a_lvf = arch("hr_holidays.hr_leave_view_form", "form")
    pruefe('name="x_o11_number_of_days"' in a_lvf, "Formular Abwesenheit: Feld Anzahl der Tage (Odoo 11)")
    a_attf = arch("hr_attendance.hr_attendance_view_form", "form")
    pruefe('name="x_homeoffice"' in a_attf, "Formular Anwesenheit: Feld Home-Office")

    a_such = arch("hr_holidays.hr_leave_view_search_manager", "search")
    for text in ("Zur Genehmigung", "Aktive Typen", "Ungelesene Nachrichten", "Urlaube meiner Abteilung",
                 "Mein Teamurlaub", "Manager", "Prüfer", "Abteilung"):
        pruefe('string="%s"' % text in a_such, "Suchfilter/Gruppierung %r" % text)
    a_such_att = arch("hr_attendance.hr_attendance_view_filter", "search")
    pruefe('string="Home-Office"' in a_such_att, "Suchfilter Home-Office (Anwesenheiten)")

    # Rechte
    gid = rec_id(k18, "itk_hr_leave_compat.group_itk_anwesenheit_manuell")
    g = k18.kw("res.groups", "read", [[gid], ["name", "users"]] , context=DE)[0] if gid else None
    pruefe(bool(g), "Gruppe Anwesenheit manuell vorhanden", bool(g), True)
    if g:
        print("  Gruppe 'Anwesenheit manuell': %d Benutzer" % len(g["users"]))
        pruefe(len(g["users"]) > 0, "Gruppe Anwesenheit manuell hat Benutzer", len(g["users"]), ">0")
    rule = k18.kw("ir.rule", "search_read", [[("model_id.model", "=", "hr.attendance"),
                                              ("name", "ilike", "Anwesenheit manuell")],
                                             ["id", "domain_force", "perm_write"]], context=DE)
    pruefe(bool(rule) and rule[0]["perm_write"], "Datensatzregel eigene Anwesenheiten (Schreiben)",
           bool(rule), True)
    acc = k18.kw("ir.model.access", "search_read", [[("name", "ilike", "anwesenheit manuell")],
                                                    ["perm_read", "perm_write", "perm_create"]],
                 context=DE)
    pruefe(bool(acc) and acc[0]["perm_create"], "Zugriffsrecht eigene Anwesenheiten anlegen",
           bool(acc), True)

    # ------------------------------------------------------------------ Daten
    h11 = k11.kw("hr.holidays", "search_read",
                 [[], ["id", "name", "type", "employee_id", "holiday_status_id", "state",
                       "date_from", "date_to", "number_of_days_temp", "first_approver_id",
                       "second_approver_id"]], context=ctx11, order="id")
    s11 = {t["id"]: t for t in k11.kw("hr.holidays.status", "search_read",
                                      [[], ["id", "name"]], context=ctx11)}
    b11 = k11.kw("hr.employee", "search_read", [[], ["id", "name", "work_email"]], context=ctx11)
    at11 = k11.kw("hr.attendance", "search_read",
                  [[], ["id", "employee_id", "check_in", "check_out", "worked_hours", "x_homeoffice"]],
                  context=ctx11, order="check_in,id")

    b18 = k18.kw("hr.employee", "search_read", [[], ["id", "name", "work_email", "active"]],
                 context=ctx18)
    typ18 = {t["id"]: t for t in k18.kw("hr.leave.type", "search_read", [[], ["id", "name"]],
                                        context=ctx18)}
    l18 = k18.kw("hr.leave", "search_read",
                 [[], ["id", "employee_id", "holiday_status_id", "request_date_from", "request_date_to",
                       "number_of_days", "state", "private_name", "x_o11_number_of_days",
                       "first_approver_id", "second_approver_id"]], context=ctx18, order="id")
    al18 = k18.kw("hr.leave.allocation", "search_read",
                  [[], ["id", "employee_id", "holiday_status_id", "number_of_days", "state"]],
                  context=ctx18, order="id")
    at18 = k18.kw("hr.attendance", "search_read",
                  [[], ["id", "employee_id", "check_in", "check_out", "worked_hours", "x_homeoffice"]],
                  context=ctx18, order="check_in,id")

    # Zuordnung Mitarbeiter (E-Mail, dann Name)
    nach_email = {nn(e["work_email"]): e for e in b18 if e["work_email"]}
    nach_name = {nn(e["name"]): e for e in b18}
    ma = {}
    for e in b11:
        z = nach_email.get(nn(e["work_email"])) or nach_name.get(nn(e["name"]))
        if z:
            ma[e["id"]] = z
    pruefe(len(ma) == len(b11), "Mitarbeiterzuordnung vollstaendig", len(ma), len(b11))
    # Namen in Odoo 18 koennen anders geschrieben sein ("Miglar Daniel" statt
    # "Daniel Miglar") - fuer den Vergleich auf die Odoo-11-Schreibweise abbilden.
    b11_nach_id = {e["id"]: e["name"] for e in b11}
    rueck = {e["name"]: b11_nach_id[o11id] for o11id, e in ma.items() if o11id in b11_nach_id}

    def o11name(name18):
        return rueck.get(name18, name18)

    nach_typ = collections.defaultdict(list)
    for t in typ18.values():
        nach_typ[nt(t["name"])].append(t)
    ty = {}
    for tid, t in s11.items():
        treffer = nach_typ.get(nt(t["name"]))
        if treffer and len(treffer) == 1:
            ty[tid] = treffer[0]
    pruefe(len(ty) == len(s11), "Urlaubsarten zugeordnet", len(ty), len(s11))

    # Zaehlungen
    n_antraege11 = sum(1 for h in h11 if h["type"] == "remove")
    n_ansprueche11 = sum(1 for h in h11 if h["type"] == "add")
    print("  Odoo 11: %d Antraege, %d Ansprueche, %d Anwesenheiten, %d Mitarbeiter"
          % (n_antraege11, n_ansprueche11, len(at11), len(b11)))
    print("  Odoo 18: %d Antraege, %d Ansprueche, %d Anwesenheiten, %d Mitarbeiter"
          % (len(l18), len(al18), len(at18), len(b18)))
    pruefe(len(l18) == n_antraege11, "Anzahl Antraege", len(l18), n_antraege11)
    pruefe(len(al18) == n_ansprueche11 - 3, "Anzahl Ansprueche (3 nicht uebertragbar)", len(al18),
           n_ansprueche11 - 3)
    pruefe(len(at18) == len(at11), "Anzahl Anwesenheiten", len(at18), len(at11))

    # Antraege: Multimenge + Status + Felder
    k11 = collections.Counter()
    for h in h11:
        if h["type"] != "remove":
            continue
        k11[(h["employee_id"][1] if h["employee_id"] else "",
            nt(s11[h["holiday_status_id"][0]]["name"]),
            (h["date_from"] or "")[:10], (h["date_to"] or "")[:10], h["state"])] += 1
    k18c = collections.Counter()
    for r in l18:
        k18c[(o11name(r["employee_id"][1]) if r["employee_id"] else "",
              nt(typ18[r["holiday_status_id"][0]]["name"]),
              r["request_date_from"] or "", r["request_date_to"] or "", r["state"])] += 1
    fehlend = k11 - k18c
    zuviel = k18c - k11
    pruefe(not fehlend, "Antraege: keine fehlenden Datensaetze", sum(fehlend.values()), 0)
    pruefe(not zuviel, "Antraege: keine zusaetzlichen Datensaetze", sum(zuviel.values()), 0)
    if fehlend:
        for x in list(fehlend.items())[:10]:
            print("     fehlt:", x)
    if zuviel:
        for x in list(zuviel.items())[:10]:
            print("     zuviel:", x)

    # Status je Datensatz (Odoo 11 massgeblich)
    idx = {}
    for r in l18:
        idx.setdefault((o11name(r["employee_id"][1]) if r["employee_id"] else "",
                        nt(typ18[r["holiday_status_id"][0]]["name"]),
                        r["request_date_from"], r["request_date_to"]), []).append(r)
    status_falsch = []
    tage_falsch = []
    beschreibung_fehlt = []
    approver_fehlt = []
    for h in h11:
        if h["type"] != "remove":
            continue
        schluessel = (h["employee_id"][1] if h["employee_id"] else "",
                      nt(s11[h["holiday_status_id"][0]]["name"]),
                      (h["date_from"] or "")[:10], (h["date_to"] or "")[:10])
        kandidaten = idx.get(schluessel) or []
        if not kandidaten:
            continue
        r = kandidaten[0]
        if r["state"] != h["state"]:
            status_falsch.append((h["id"], r["id"], h["state"], r["state"]))
        if abs((r["x_o11_number_of_days"] or 0.0) - (h["number_of_days_temp"] or 0.0)) > 0.001:
            tage_falsch.append((h["id"], h["number_of_days_temp"], r["x_o11_number_of_days"]))
        if h["name"] and nt(h["name"]) != nt(r["private_name"]):
            beschreibung_fehlt.append((h["id"], h["name"], r["private_name"]))
        if h.get("first_approver_id"):
            soll = ma.get(h["first_approver_id"][0], {}).get("id")
            ist = r["first_approver_id"][0] if r["first_approver_id"] else False
            if soll and ist != soll:
                approver_fehlt.append((h["id"], soll, ist))
    pruefe(not status_falsch, "Status wie in Odoo 11", status_falsch[:5], [])
    pruefe(not tage_falsch, "Anzahl der Tage (Odoo 11) gespeichert", tage_falsch[:5], [])
    pruefe(not beschreibung_fehlt, "Beschreibung uebernommen", beschreibung_fehlt[:5], [])
    pruefe(not approver_fehlt, "Erste Genehmigung uebernommen", approver_fehlt[:5], [])

    # Ansprueche
    a11 = collections.Counter()
    for h in h11:
        if h["type"] != "add" or not h["employee_id"]:
            continue
        if (h["number_of_days_temp"] or 0.0) <= 0:
            continue
        a11[(h["employee_id"][1], nt(s11[h["holiday_status_id"][0]]["name"]),
             round(h["number_of_days_temp"], 2), h["state"])] += 1
    a18 = collections.Counter()
    for r in al18:
        a18[(o11name(r["employee_id"][1]), nt(typ18[r["holiday_status_id"][0]]["name"]),
             round(r["number_of_days"], 2), r["state"])] += 1
    pruefe(not (a11 - a18), "Ansprueche: keine fehlenden Datensaetze", sum((a11 - a18).values()), 0)
    pruefe(not (a18 - a11), "Ansprueche: keine zusaetzlichen Datensaetze", sum((a18 - a11).values()), 0)

    # Anwesenheiten: Zeitstempel, Dauer, Homeoffice
    b11c = collections.Counter((x["employee_id"][1] if x["employee_id"] else "", x["check_in"]) for x in at11)
    b18c = collections.Counter((o11name(x["employee_id"][1]) if x["employee_id"] else "", x["check_in"])
                               for x in at18)
    pruefe(not (b11c - b18c), "Anwesenheiten: keine fehlenden Zeilen", sum((b11c - b18c).values()), 0)
    pruefe(not (b18c - b11c), "Anwesenheiten: keine zusaetzlichen Zeilen", sum((b18c - b11c).values()), 0)
    idx_a = {}
    for x in at18:
        if x["employee_id"]:
            idx_a[(o11name(x["employee_id"][1]), x["check_in"])] = x
    dauer_falsch, homeoffice_falsch, checkout_falsch = [], [], []
    summe11 = summe18 = 0.0
    for x in at11:
        if not x["employee_id"]:
            continue
        y = idx_a.get((x["employee_id"][1], x["check_in"]))
        if not y:
            continue
        summe11 += x["worked_hours"] or 0.0
        summe18 += y["worked_hours"] or 0.0
        if (x["check_out"] or False) != (y["check_out"] or False):
            checkout_falsch.append((x["id"], x["check_out"], y["check_out"]))
        elif abs((x["worked_hours"] or 0.0) - (y["worked_hours"] or 0.0)) > 0.01:
            dauer_falsch.append((x["id"], round(x["worked_hours"] or 0, 3), round(y["worked_hours"] or 0, 3)))
        if bool(x["x_homeoffice"]) != bool(y["x_homeoffice"]):
            homeoffice_falsch.append((x["id"], x["x_homeoffice"], y["x_homeoffice"]))
    print("  Arbeitsstunden Odoo 11 = %.2f | Odoo 18 = %.2f" % (summe11, summe18))
    pruefe(not checkout_falsch, "Anwesenheiten: Abmeldezeiten", checkout_falsch[:5], [])
    pruefe(not dauer_falsch, "Anwesenheiten: Arbeitsstunden", dauer_falsch[:5], [])
    pruefe(not homeoffice_falsch, "Anwesenheiten: Home-Office", homeoffice_falsch[:5], [])
    pruefe(abs(summe11 - summe18) < 0.05, "Summe Arbeitsstunden", round(summe18, 2), round(summe11, 2))
    n_home = sum(1 for x in at18 if x["x_homeoffice"])
    pruefe(n_home == sum(1 for x in at11 if x["x_homeoffice"]),
           "Anzahl Home-Office-Zeilen", n_home, sum(1 for x in at11 if x["x_homeoffice"]))

    # Beziehungen
    ohne_mitarbeiter = [r["id"] for r in l18 if not r["employee_id"]]
    ohne_typ = [r["id"] for r in l18 if not r["holiday_status_id"]]
    pruefe(not ohne_mitarbeiter, "Antraege ohne Mitarbeiter", ohne_mitarbeiter, [])
    pruefe(not ohne_typ, "Antraege ohne Abwesenheitsart", ohne_typ, [])
    pruefe(not [r["id"] for r in al18 if not r["employee_id"]], "Ansprueche ohne Mitarbeiter")
    pruefe(not [x["id"] for x in at18 if not x["employee_id"]], "Anwesenheiten ohne Mitarbeiter")

    # Sonderfaelle
    n_null11 = sum(1 for h in h11 if h["type"] == "remove" and not (h["number_of_days_temp"] or 0))
    n_null18 = sum(1 for r in l18 if not (r["number_of_days"] or 0))
    print("  0-Tage-Antraege: Odoo 11 %d, Odoo 18 %d (Odoo 18 rechnet die Dauer selbst)"
          % (n_null11, n_null18))
    pruefe(n_null18 >= n_null11, "0-Tage-Antraege nicht verloren", n_null18, n_null11)

    archiviert = {o11name(e["name"]) for e in b18 if not e["active"]}
    antraege_arch = sum(1 for r in l18 if r["employee_id"][1] in archiviert)
    antraege_arch11 = sum(1 for h in h11 if h["type"] == "remove" and h["employee_id"]
                          and h["employee_id"][1] in archiviert)
    pruefe(antraege_arch == antraege_arch11, "Antraege ausgeschiedener Mitarbeiter",
           antraege_arch, antraege_arch11)

    koch = [r for r in l18 if r["employee_id"] and "Koch Katharina" in r["employee_id"][1]
            and r["request_date_from"] == "2021-06-01"]
    pruefe(bool(koch) and koch[0]["state"] == "validate",
           "Abwesenheit Koch Katharina 2021-06-01 gebucht", koch[0]["state"] if koch else None, "validate")

    neu711 = [r for r in l18 if r["employee_id"] and "Blagojevic" in r["employee_id"][1]
              and r["request_date_from"] == "2026-10-26"]
    pruefe(bool(neu711) and neu711[0]["state"] == "confirm",
           "Antrag Blagojevic 2026-10-26 vorhanden (Status Zu genehmigen)",
           neu711[0]["state"] if neu711 else None, "confirm")

    # keine Fremdarten (Testdaten)
    fremd = [r["id"] for r in l18 if nt(typ18[r["holiday_status_id"][0]]["name"])
             not in {nt(t["name"]) for t in s11.values()}]
    pruefe(not fremd, "keine Antraege mit Odoo-18-Testart", fremd, [])

    # Resturlaub je Mitarbeiter/Art (nur beratend, keine Abnahme)
    print("\n  Resturlaub (Ansprueche minus gebuchte Antraege) - Auszug:")
    saldo = collections.Counter()
    for r in al18:
        if r["state"] == "validate":
            saldo[(r["employee_id"][1], nt(typ18[r["holiday_status_id"][0]]["name"]))] += r["number_of_days"]
    for r in l18:
        if r["state"] == "validate":
            saldo[(r["employee_id"][1], nt(typ18[r["holiday_status_id"][0]]["name"]))] -= r["number_of_days"]
    for (emp, typ), wert in sorted(saldo.items()):
        if typ.startswith("gesetzlicher Jahresurlaub 2026"):
            print("     %-34s %-42s %7.2f" % (emp[:34], typ[:42], wert))

    print("\n=== Ergebnis: %d OK / %d FEHLER ===" % (ok, len(fehler)))
    for f in fehler:
        print("  FEHLER:", f)
    return 0 if not fehler else 1


if __name__ == "__main__":
    sys.exit(main())
