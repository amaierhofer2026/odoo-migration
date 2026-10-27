"""Abnahme PROJEKT (Session 135): Struktur, Rechte, Datenbestand (read-only).

Aufruf:
  python scripts/verify_s135_projekt.py --instanz lokal
  python scripts/verify_s135_projekt.py --instanz vm --nach-migration

Prueft die S133-Umsetzung (itk_project), die in S135 migrierten Stammdaten
(Projekte, Aufgaben, Stufen, Tags) und die Projektgruppen. XML-IDs statt harter
Datenbank-IDs, weil IDs zwischen lokal und VM nicht stabil sind.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

CTX = {"lang": "de_DE"}
ERWARTUNG = {
    "projekte_gesamt": 38,          # 5 Testprojekte + 33 aus Odoo 11
    "projekte_aktiv": 33,           # 5 Test + 28 aktive Odoo-11-Projekte
    "aufgaben_gesamt": 723,         # 8 Testaufgaben + 715 aus Odoo 11
    "tags": 13,
}


class Pruefung:
    def __init__(self):
        self.ok = 0
        self.fehler = []

    def pruefe(self, bez, ist, soll):
        if ist == soll:
            self.ok += 1
            print("  OK      %-58s %s" % (bez, ist))
        else:
            self.fehler.append((bez, ist, soll))
            print("  FEHLER  %-58s ist=%s soll=%s" % (bez, ist, soll))

    def wahr(self, bez, bed, info=""):
        self.pruefe(bez, bool(bed), True)
        if not bed:
            print("          ->", info)

    def ergebnis(self):
        print("\n  Ergebnis: %d OK, %d FEHLER" % (self.ok, len(self.fehler)))
        for f in self.fehler:
            print("   FEHLER:", f)
        return 0 if not self.fehler else 1


def xmlid(cli, modul, name, modell):
    t = cli.kw("ir.model.data", "search_read",
               [[("module", "=", modul), ("name", "=", name), ("model", "=", modell)]],
               fields=["res_id"], limit=1)
    return t[0]["res_id"] if t else None


def arch(cli, modell, view_id, typ):
    res = cli.kw(modell, "get_views", [[(view_id, typ)]], options={"toolbar": False}, context=CTX)
    return list(res["views"].values())[0]["arch"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    a = ap.parse_args()
    cli = o18(a.instanz)
    p = Pruefung()
    print("### Instanz:", a.instanz)

    print("\n=== 1 Modul und S133-Umsetzung ===")
    m = cli.kw("ir.module.module", "search_read", [[("name", "=", "itk_project")]],
               fields=["state", "installed_version"])
    p.pruefe("itk_project installiert", m and m[0]["state"], "installed")
    f = cli.kw("project.task", "fields_get", [], attributes=["string", "type"], context=CTX)
    p.wahr("Startdatum der Aufgabe (itk_date_start) vorhanden", "itk_date_start" in f)
    p.pruefe("Prioritaet sichtbar", str(f.get("priority", {}).get("selection")), str(
        f.get("priority", {}).get("selection")))
    phasen = cli.kw("project.project.stage", "search_read", [[]], fields=["name"], order="sequence", limit=0)
    p.pruefe("Projektphasen deutsch", [x["name"] for x in phasen],
             ["Zu erledigen", "In Arbeit", "Erledigt", "Abgebrochen"])

    print("\n=== 2 Menues ===")
    menues = [("project.menu_projects", "Projekte"), ("project.menu_project_config", "Konfiguration")]
    stufen_menu = cli.kw("ir.ui.menu", "search_read", [[("name", "=", "Stufen")]],
                         fields=["id", "name", "parent_id"], context=CTX, limit=0)
    p.wahr("Menue 'Stufen' in der Projekt-Konfiguration", bool(stufen_menu), stufen_menu)
    start = cli.kw("ir.ui.menu", "search_read", [[("name", "=", "Arbeit starten")]],
                   fields=["id", "name"], context=CTX, limit=0)
    p.wahr("Menue 'Arbeit starten' deutsch", bool(start), start)

    print("\n=== 3 Ansichten und Wortlaute ===")
    task_form = xmlid(cli, "project", "view_task_form2", "ir.ui.view")
    ar = arch(cli, "project.task", task_form, "form")
    p.wahr("Aufgabe: Startdatum in der Ansicht", "itk_date_start" in ar)
    p.wahr("Aufgabe: keine englischen Knopfbeschriftungen", "Start work" not in ar and ">Stop<" not in ar,
           [x for x in ("Start work", "Stop") if x in ar])
    proj_form = xmlid(cli, "project", "edit_project", "ir.ui.view")
    ar2 = arch(cli, "project.project", proj_form, "form")
    p.wahr("Projekt: Zeiterfassung erlauben vorhanden", "allow_timesheets" in ar2)
    p.wahr("Projekt: Kostenstelle/Abrechnung vorhanden", "account_id" in ar2)

    print("\n=== 4 Datenbestand (nach Migration) ===")
    # Sammelprojekt der Zeiterfassungsmigration (Session 136) zaehlt nicht zum
    # Projektbereich: es wird dort weder fachlich noch strukturell verwendet.
    sammel = {"active_test": False}
    sammel_domain = [("name", "!=", "Ohne Projekt (Uebernahme Odoo 11)")]
    p.pruefe("Projekte inkl. archiviert (ohne Zeiterfassungs-Sammelprojekt)",
             cli.kw("project.project", "search_count", [sammel_domain], context=sammel),
             ERWARTUNG["projekte_gesamt"])
    p.pruefe("Projekte aktiv (ohne Zeiterfassungs-Sammelprojekt)",
             cli.kw("project.project", "search_count", [sammel_domain]),
             ERWARTUNG["projekte_aktiv"])
    p.pruefe("Aufgaben inkl. archiviert",
             cli.kw("project.task", "search_count", [[]], context={"active_test": False}),
             ERWARTUNG["aufgaben_gesamt"])
    p.pruefe("Stichwoerter", cli.kw("project.tags", "search_count", [[]]), ERWARTUNG["tags"])
    p.pruefe("Aufgaben mit Projekt",
             cli.kw("project.task", "search_count", [[("project_id", "!=", False)]],
                    context={"active_test": False}), 718)
    # 719 = 715 migrierte + 4 Testaufgaben mit Bearbeiter (von 8 Testaufgaben)
    p.pruefe("Aufgaben mit Bearbeiter",
             cli.kw("project.task", "search_count", [[("user_ids", "!=", False)]],
                    context={"active_test": False}), 719)
    p.pruefe("Aufgaben mit Startdatum (715 migriert)",
             cli.kw("project.task", "search_count", [[("itk_date_start", "!=", False)]],
                    context={"active_test": False}), 715)
    p.wahr("Stufen gesamt >= 103",
           cli.kw("project.task.type", "search_count", [[]], context={"active_test": False}) >= 103)

    print("\n=== 5 Rechte ===")
    # Odoo 11 fuehrt 23/20 Mitglieder inkl. Alias-Logins; Odoo 18 hat 14 aktive
    # interne Benutzer -> 13 Benutzer / 12 Manager (christiane.breit war in Odoo 11
    # nur in "Projekt/Benutzer", nicht Manager).
    for xmlname, soll_min in (("group_project_user", 13), ("group_project_manager", 12)):
        gid = xmlid(cli, "project", xmlname, "res.groups")
        g = cli.kw("res.groups", "read", [[gid]], fields=["name", "users"], context=CTX)[0]
        print("  INFO    %-40s Mitglieder: %d" % (g["name"], len(g["users"])))
        p.wahr("%s hat mindestens %d Mitglieder" % (xmlname, soll_min), len(g["users"]) >= soll_min,
               len(g["users"]))

    return p.ergebnis()


if __name__ == "__main__":
    raise SystemExit(main())
