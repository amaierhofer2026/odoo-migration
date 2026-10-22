"""Abnahme Zeiterfassung: Struktur, Wortlaute, Menues, Favoriten (read-only).

Aufruf:
  python scripts/verify_s135_zeiterfassung.py --instanz lokal
  python scripts/verify_s135_zeiterfassung.py --instanz vm

Prueft die in itk_timesheet umgesetzten Punkte und (mit --nach-migration) den
migrierten Datenbestand. Es werden ausschliesslich lesende RPC-Aufrufe gemacht.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

CTX = {"lang": "de_DE"}


class Pruefung:
    def __init__(self):
        self.ok = 0
        self.fehler = []
        self.hinweise = []

    def pruefe(self, bez, ist, soll):
        if ist == soll:
            self.ok += 1
            print("  OK      %-58s %s" % (bez, ist))
        else:
            self.fehler.append((bez, ist, soll))
            print("  FEHLER  %-58s ist=%s soll=%s" % (bez, ist, soll))

    def pruefe_wahr(self, bez, bedingung, wert=""):
        self.pruefe(bez, bool(bedingung), True)
        if not bedingung:
            self.hinweise.append("%s (%s)" % (bez, wert))

    def ergebnis(self):
        print("\n  Ergebnis: %d OK, %d FEHLER" % (self.ok, len(self.fehler)))
        for f in self.fehler:
            print("   FEHLER:", f)
        return 0 if not self.fehler else 1


XMLIDS = {
    "liste_meine": ("hr_timesheet", "hr_timesheet_line_tree"),
    "liste_alle": ("hr_timesheet", "timesheet_view_tree_user"),
    "form_meine": ("hr_timesheet", "hr_timesheet_line_form"),
    "form_alle": ("hr_timesheet", "timesheet_view_form_user"),
    "suche": ("hr_timesheet", "hr_timesheet_line_search"),
    "suche_meine": ("hr_timesheet", "hr_timesheet_line_my_timesheet_search"),
    "menue_meine": ("hr_timesheet", "timesheet_menu_activity_mine"),
    "menue_rate": ("sale_timesheet", "menu_timesheet_billing_analysis"),
    "menue_anwesenheit": ("hr_timesheet_attendance", "menu_hr_timesheet_attendance_report"),
    "menue_berichte": ("hr_timesheet", "menu_timesheets_reports"),
    "aktion_meine": ("hr_timesheet", "act_hr_timesheet_line"),
}


def aufloesen(cli):
    """XML-IDs -> Datenbank-IDs. IDs sind zwischen lokal und VM NICHT stabil."""
    ids = {}
    for key, (modul, name) in XMLIDS.items():
        treffer = cli.kw("ir.model.data", "search_read",
                         [[("module", "=", modul), ("name", "=", name)]],
                         fields=["res_id"], limit=1)
        ids[key] = treffer[0]["res_id"] if treffer else None
    return ids


def arch(cli, modell, view_id, typ):
    res = cli.kw(modell, "get_views", [[(view_id, typ)]], options={"toolbar": False}, context=CTX)
    return list(res["views"].values())[0]["arch"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--nach-migration", action="store_true")
    a = ap.parse_args()
    cli = o18(a.instanz)
    p = Pruefung()
    print("### Instanz:", a.instanz)
    xid = aufloesen(cli)
    print("  XML-IDs:", xid)

    print("\n=== 1 Modul ===")
    m = cli.kw("ir.module.module", "search_read", [[("name", "=", "itk_timesheet")]],
               fields=["name", "state", "installed_version"])
    p.pruefe("itk_timesheet installiert", m and m[0]["state"], "installed")
    p.pruefe("itk_timesheet Version", m[0]["installed_version"] if m else "-", "18.0.1.0.3")

    print("\n=== 2 Liste 'Meine Stundenzettel' (2657) ===")
    ar = arch(cli, "account.analytic.line", xid["liste_meine"], "list")
    p.pruefe_wahr("Spaltenlabel Zeit (Stunden)", 'string="Zeit (Stunden)"' in ar, ar[:200])
    p.pruefe_wahr("Spaltensumme Gesamtdauer", 'sum="Gesamtdauer"' in ar)
    p.pruefe_wahr("Beschreibung Pflicht", 'name="name"' in ar and 'required="1"' in ar)
    p.pruefe_wahr("Datums-Spalte sichtbar", '<field name="date"' in ar and 'column_invisible="1"' not in ar.split('<field name="date"')[1][:80])
    p.pruefe_wahr("Startzeit standardmaessig ausgeblendet",
                  'optional="hide"' in ar.split('<field name="date_time"')[1][:120])

    print("\n=== 3 Liste 'Alle Zeiterfassungen' (2659) ===")
    ar = arch(cli, "account.analytic.line", xid["liste_alle"], "list")
    p.pruefe_wahr("Spaltenlabel Zeit (Stunden)", 'string="Zeit (Stunden)"' in ar)
    p.pruefe_wahr("Spaltensumme Gesamtdauer", 'sum="Gesamtdauer"' in ar)
    # Mitarbeiter muss als Spalte sichtbar sein (Odoo 11), nicht optional versteckt
    stueck = ar.split('<field name="employee_id"')[1].split("/>")[0] if '<field name="employee_id"' in ar else ""
    p.pruefe_wahr("Mitarbeiter-Spalte sichtbar",
                  'column_invisible="0"' in stueck and 'optional="hide"' not in stueck
                  and 'required="1"' in stueck, stueck)

    print("\n=== 4 Formulare (2667 eigene, 2668 alle) ===")
    for vid in (xid["form_meine"], xid["form_alle"]):
        ar = arch(cli, "account.analytic.line", vid, "form")
        p.pruefe_wahr("%s: Datum sichtbar" % vid,
                      'invisible="0" string="Datum"' in ar or 'string="Datum"' in ar, ar[:200])
        p.pruefe_wahr("%s: Zeit (Stunden)" % vid, 'string="Zeit (Stunden)"' in ar)
        p.pruefe_wahr("%s: Beschreibung Pflicht" % vid, 'required="1"' in ar)

    print("\n=== 5 Suche ===")
    ar = arch(cli, "account.analytic.line", xid["suche"], "search")
    for wort in ["Meine Stundenzettel", "Abrechenbare Stunden", "Projekte mit Festpreis",
                 "Nicht abrechenbare Stunden", "Monatliche Zeiterfassung", "Dieser Monat", "Mit Ticket"]:
        p.pruefe_wahr("Suchfilter/Wortlaut: %s" % wort, wort in ar)
    p.pruefe_wahr("Filter 'Dieser Monat' mit Datumsdomain",
                  "date_this_month" in ar and "context_today" in ar)
    ar2 = arch(cli, "account.analytic.line", xid["suche_meine"], "search")
    p.pruefe_wahr("Eigene Suche: Dieser Monat", "Dieser Monat" in ar2)
    p.pruefe_wahr("Eigene Suche: Monatliche Zeiterfassung", "Monatliche Zeiterfassung" in ar2)

    print("\n=== 6 Menues ===")
    menues = {"menue_meine": "Meine Stundenzettel", "menue_rate": "Nach Abrechnungsrate",
              "menue_anwesenheit": "Anwesenheit"}
    gelesen = cli.kw("ir.ui.menu", "read",
                     [[xid[k] for k in menues if xid[k]]],
                     fields=["name"], context=CTX)
    ist = {x["id"]: x["name"] for x in gelesen}
    for key, soll in menues.items():
        p.pruefe("Menue %s (%s)" % (key, xid[key]), ist.get(xid[key]), soll)
    akt_name = cli.kw("ir.actions.act_window", "read", [[xid["aktion_meine"]]],
                      fields=["name"], context=CTX)[0]["name"]
    p.pruefe("Aktion 'Meine Stundenzettel'", akt_name, "Meine Stundenzettel")
    menu_xids = cli.kw("ir.model.data", "search_read",
                       [[("module", "=", "itk_timesheet"), ("model", "=", "ir.ui.menu")]],
                       fields=["name", "res_id"], limit=0)
    p.pruefe_wahr("Menue 'Kosten und Erloese' vorhanden", bool(menu_xids), menu_xids)
    if menu_xids:
        nm = cli.kw("ir.ui.menu", "read", [[x["res_id"] for x in menu_xids]],
                    fields=["name", "parent_id"], context=CTX)
        p.pruefe("Menue Kosten und Erloese heisst", nm[0]["name"], "Kosten und Erloese")
        p.pruefe("Menue haengt unter Berichtswesen", nm[0]["parent_id"][0], xid["menue_berichte"])

    print("\n=== 7 Bericht Kosten und Erloese ===")
    akt = cli.kw("ir.actions.act_window", "search_read",
                 [[("name", "=", "Kosten und Erloese")]],
                 fields=["name", "res_model", "view_mode", "domain"], context=CTX, limit=0)
    p.pruefe_wahr("Aktion vorhanden", bool(akt), akt)
    if akt:
        p.pruefe("Aktion Modell", akt[0]["res_model"], "timesheets.analysis.report")
        p.pruefe("Aktion Ansichten", akt[0]["view_mode"], "pivot,list")

    print("\n=== 8 Favorit Abrechnungsrate ===")
    f = cli.kw("ir.filters", "search_read", [[("model_id", "=", "account.analytic.line"),
                                             ("name", "=", "Abrechnungsrate")]],
              fields=["name", "domain", "context", "is_default"], limit=0)
    p.pruefe_wahr("Favorit vorhanden", bool(f), f)
    if f:
        p.pruefe("Favorit ist Standard", bool(f[0]["is_default"]), True)
        p.pruefe_wahr("Favorit Spaltengruppierung Monat",
                      "date:month" in str(f[0]["context"]), f[0]["context"])

    print("\n=== 9 Odoo-18-Zusatzfunktionen erhalten ===")
    start = cli.kw("ir.model.data", "search_read",
                   [[("module", "=", "project_timesheet_time_control"),
                     ("name", "=", "hr_timesheet_switch_menu")]], fields=["res_id"], limit=1)
    if start:
        nm = cli.kw("ir.ui.menu", "read", [[start[0]["res_id"]]], fields=["name"], context=CTX)
        p.pruefe("Menue 'Arbeit starten'", nm[0]["name"], "Arbeit starten")
    a1187 = cli.kw("ir.actions.act_window", "read", [[xid["aktion_meine"]]], fields=["view_mode"])[0]
    for vw in ("list", "form", "kanban", "pivot", "graph"):
        p.pruefe_wahr("Aktion 1187 bietet %s" % vw, vw in a1187["view_mode"])

    print("\n=== 10 Gruppen (Rechte) ===")
    g = cli.kw("res.groups", "read", [[607, 608]], fields=["name", "users"], context=CTX)
    for x in g:
        print("  INFO    %-42s Mitglieder: %d" % (x["name"], len(x["users"])))
    p.pruefe_wahr("Gruppe 'nur eigene' vorhanden", any(x["id"] == 607 for x in g))
    p.pruefe_wahr("Gruppe 'alle' vorhanden", any(x["id"] == 608 for x in g))
    mitglieder = {x["id"]: set(x["users"]) for x in g}
    # Odoo-11-Konzept: alle aktiven internen Benutzer duerfen eigene Zeiten erfassen
    aktiv = cli.kw("res.users", "search_read", [[("share", "=", False), ("active", "=", True)]],
                   fields=["id", "login"], limit=0)
    aktiv = [u for u in aktiv if u["login"] not in ("__system__", "default", "public", "portaltemplate")]
    # Ausnahme: christiane.breit war in Odoo 11 NICHT in der Zeiterfassungsgruppe
    AUSNAHME_607 = {"christiane.breit@it-kommunal.at"}
    fehlt = [u["login"] for u in aktiv
             if u["id"] not in mitglieder.get(607, set())
             and (u["login"] or "").lower() not in {x.lower() for x in AUSNAHME_607}]
    p.pruefe_wahr("alle aktiven internen Benutzer in Gruppe 607", not fehlt, fehlt)
    p.pruefe_wahr("Gruppe 608 nur fuer Projektmanager-Kreis (<= 12)",
                  len(mitglieder.get(608, set())) <= 12, len(mitglieder.get(608, set())))
    p.pruefe_wahr("Gruppe 608 ist Teilmenge von 607",
                  mitglieder.get(608, set()) <= mitglieder.get(607, set()) | mitglieder.get(608, set()))

    if a.nach_migration:
        print("\n=== 11 Datenbestand ===")
        md = "account.analytic.line"
        p.pruefe("Zeilen gesamt", cli.kw(md, "search_count", [[]]), 12885 + 19)
        p.pruefe("Zeilen mit Projekt", cli.kw(md, "search_count", [[("project_id", "!=", False)]]),
                 12885 + 19 - 282)
        p.pruefe("Zeilen mit Aufgabe", cli.kw(md, "search_count", [[("task_id", "!=", False)]]),
                 12744 + 19)
        p.pruefe("Projekte", cli.kw("project.project", "search_count", [[]]), 5 + 33 + 1)
        p.pruefe("Aufgaben", cli.kw("project.task", "search_count", [[]]), 8 + 714)

    return p.ergebnis()


if __name__ == "__main__":
    raise SystemExit(main())
