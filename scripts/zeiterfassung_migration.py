"""Datenmigration ZEITERFASSUNG: Odoo 11 (Produktion, read-only) -> Odoo 18.

Stand 27.10.2026 (Session 136). Das Modul Projekt ist abgenommen; der Schreiblauf
ist freigegeben, die Sicherung `--projekt-abgeschlossen` bleibt bestehen.

Aufruf:
    python scripts/zeiterfassung_migration.py --instanz lokal
    python scripts/zeiterfassung_migration.py --instanz lokal --plan-schreiben
    python scripts/zeiterfassung_migration.py --instanz lokal --grenze 20 --ausfuehren \\
        --ich-habe-freigabe --projekt-abgeschlossen            # Pilotlauf
    python scripts/zeiterfassung_migration.py --instanz lokal --ausfuehren \\
        --ich-habe-freigabe --projekt-abgeschlossen            # Volllauf (idempotent)

Regeln (Anna, 22.10.2026 und 27.10.2026):
  * Odoo 11 ausschliesslich lesen, Bestand bei jedem Lauf NEU erheben.
  * Ziel nur die Testdatenbank (ODOO18_DB endet auf odoo18_test).
  * Zuordnung ueber fachliche Schluessel (E-Mail/Name, Projektname, Aufgabentitel,
    Stufe/Stichwort), nie ueber Datenbank-IDs; bei Mehrdeutigkeit Abbruch.
  * Vollstaendige Historie: Zeilen archivierter Mitarbeiter, archivierte Projekte
    und Aufgaben, Zeilen ohne Projekt, historische Ticketnummern.
  * Zeilen ohne Projekt -> Sammelprojekt "Ohne Projekt (Uebernahme Odoo 11)".
  * Zeilen ohne Projekt, aber mit Odoo-11-Aufgabe: Odoo 18 verweigert Zeiterfassung
    auf privaten Aufgaben ("Fuer eine private Aufgabe koennen keine Zeiterfassungen
    erstellt werden", am 27.10.2026 belegt - auch mit gesetztem Projekt). Diese
    Zeilen gehen ebenfalls ins Sammelprojekt; die Odoo-11-Aufgabe bleibt als
    Referenz erhalten (`ref` = "O11-Aufgabe <Name>").
  * Kostenstelle (Odoo 11 `account_id`) projektloser Zeilen bleibt als Referenz
    erhalten (`ref` = "O11-Kostenstelle <Name>").
  * Support-Tickets: KEINE neuen Helpdesk-Tickets; Ticketnummer als `ref`
    ("O11-Ticket <Nummer>"). Mehrere Referenzen werden mit " | " verbunden.
  * Startzeit historischer Zeilen: 00:00 des Odoo-11-Datums; Endzeit leer.
  * Beschreibung: Text unveraendert, Rand-Leerzeichen werden entfernt (Odoo 18 fuehrt
    keine; bei 298 Abwesenheitszeilen waere eine spaetere Rückschreibung technisch
    gesperrt).
  * `non_billable_project` -> `non_billable`. Den Abrechnungstyp berechnet Odoo 18
    selbst (alle Odoo-11-Zeilen sind nicht abrechenbar; Pruefung im Verifikations-
    skript).
  * Abwesenheitsbezug: Kandidaten des Mitarbeiters mit gleichem Beginndatum
    (Odoo-11-Konvention `str(date_from)[:10]`, wie im uebernommenen Abwesenheits-
    bestand) und Status "validate"; bei mehreren Treffern zusaetzlich gleiche
    Tagesanzahl. Abgelehnte/offene Antraege sind keine gebuchten Abwesenheiten und
    scheiden aus (klaert die vier mehrdeutigen Zeilen zu Odoo-11-Abwesenheit 147).
  * Archivierte Mitarbeiter werden fuer den Import kurz aktiviert und danach
    wieder exakt so archiviert wie vorher.
  * Protokoll ausserhalb des Repos (%LOCALAPPDATA%\\Temp\\zeiterfassung_migration\\).

Idempotenz: vorhandene Zeilen werden ueber den Fingerabdruck (Datum, Mitarbeiter,
Projekt, Aufgabe, Dauer, Beschreibung, Referenz) als Multimenge verrechnet; ein
zweiter Lauf legt 0 Zeilen neu an.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
SCHREIB_CTX = {"lang": "de_DE", "tracking_disable": True, "mail_create_nolog": True,
               "mail_notrack": True, "no_reset_password": True}
PROTO = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Temp", "zeiterfassung_migration")
SAMMELPROJEKT = "Ohne Projekt (Uebernahme Odoo 11)"
INVOICE_MAP = {
    "billable_time": "billable_time",
    "billable_fixed": "billable_fixed",
    "non_billable": "non_billable",
    # Odoo 18 kennt "Keine Aufgabe gefunden" (non_billable_project) nicht mehr
    "non_billable_project": "non_billable",
    False: "non_billable",
    None: "non_billable",
}
ZEILEN_STATS = ("zeilen", "zeilen_neu", "zeilen_vorhanden", "zeilen_ohne_projekt",
                "zeilen_private_aufgabe", "zeilen_ticket_ref", "zeilen_kostenstelle_ref",
                "zeilen_abwesenheit", "abwesenheit_zugeordnet", "abwesenheit_ohne_treffer",
                "stunden", "stunden_neu", "zeilen_archivierter_mitarbeiter")


class Blocker(Exception):
    pass


def norm(wert):
    return " ".join((wert or "").split()).lower()


def sql_date(wert):
    """Odoo-11-Datum (datetime oder date) als reines Datum."""
    return str(wert)[:10]


class Migration:
    def __init__(self, instanz: str, schreiben: bool, grenze: int = 0, stapel: int = 200):
        self.k11 = o11()
        self.k18 = o18(instanz)
        self.instanz = instanz
        self.schreiben = schreiben
        self.grenze = grenze
        self.stapel = stapel
        self.statistik = Counter()
        self.blocker = []
        self.hinweise = []
        self.plan = {"stufen": [], "tags": [], "projekte": [], "aufgaben": [],
                     "benutzer": [], "zeilen": []}
        self.neu = 0
        self.uebersprungen = 0
        self.mapping = {}          # o11_id -> o18_id
        self.aktiviert = []        # Mitarbeiter, die kurz aktiviert wurden
        self.archiviert18 = []     # Odoo-18-Mitarbeiter, die archiviert sind und Zeilen haben
        self.abw_status = Counter()
        self.sammel_neu = False

    # ------------------------------------------------------------------ lesen
    def lese_o11(self):
        k = self.k11
        self.stufen11 = k.kw("project.task.type", "search_read", [[]],
                             fields=["id", "name", "sequence", "fold", "project_ids",
                                     "legend_priority"], context={"active_test": False}, limit=0)
        f_tags = k.kw("project.tags", "fields_get", [], attributes=["string"])
        self.tags11 = k.kw("project.tags", "search_read", [[]], fields=["id", "name", "color"],
                           limit=0) if "name" in f_tags else []
        self.projekte11 = k.kw("project.project", "search_read", [[]],
                               fields=["id", "name", "partner_id", "user_id", "privacy_visibility",
                                       "label_tasks", "allow_timesheets", "active", "color",
                                       "description", "date_start", "date"],
                               context={"active_test": False}, order="id", limit=0)
        self.aufgaben11 = k.kw("project.task", "search_read", [[]],
                               fields=["id", "name", "project_id", "stage_id", "user_id", "active",
                                       "date_deadline", "planned_hours", "description", "date_start",
                                       "kanban_state", "priority", "tag_ids", "parent_id",
                                       "partner_id"],
                               context={"active_test": False}, order="id", limit=0)
        self.zeilen11 = k.kw("account.analytic.line", "search_read", [[]],
                             fields=["id", "date", "name", "unit_amount", "employee_id", "user_id",
                                     "project_id", "task_id", "account_id", "holiday_id",
                                     "support_ticket_id", "timesheet_invoice_type", "product_uom_id",
                                     "amount", "ref"],
                             order="date,id", limit=0)
        self.ma11 = k.kw("hr.employee", "search_read", [[]],
                         fields=["id", "name", "work_email", "user_id", "active", "job_id"],
                         context={"active_test": False}, order="id", limit=0)
        tids = sorted({z["support_ticket_id"][0] for z in self.zeilen11 if z["support_ticket_id"]})
        self.tickets11 = {t["id"]: t for t in k.kw("website.support.ticket", "read", [tids],
                                                   fields=["ticket_number", "subject",
                                                           "create_date"])} if tids else {}
        hids = sorted({z["holiday_id"][0] for z in self.zeilen11 if z["holiday_id"]})
        self.holidays11 = {h["id"]: h for h in k.kw("hr.holidays", "read", [hids],
                                                    fields=["employee_id", "date_from", "date_to",
                                                            "holiday_status_id", "state",
                                                            "number_of_days_temp"])} if hids else {}
        uids = sorted({m["user_id"][0] for m in self.ma11 if m["user_id"]})
        self.users11 = {u["id"]: u for u in k.kw("res.users", "read", [uids],
                                                 fields=["login", "name", "active", "email"])}
        print("  Odoo 11: %d Stufen, %d Tags, %d Projekte, %d Aufgaben, %d Zeilen, %d MA, %d Tickets"
              % (len(self.stufen11), len(self.tags11), len(self.projekte11), len(self.aufgaben11),
                 len(self.zeilen11), len(self.ma11), len(self.tickets11)))

    def lese_o18(self):
        k = self.k18
        self.projekte18 = k.kw("project.project", "search_read", [[]],
                               fields=["id", "name", "account_id", "allow_timesheets", "active"],
                               context={"active_test": False}, limit=0)
        self.aufgaben18 = k.kw("project.task", "search_read", [[]],
                               fields=["id", "name", "project_id", "active"],
                               context={"active_test": False}, limit=0)
        self.stufen18 = k.kw("project.task.type", "search_read", [[]], fields=["id", "name"],
                             context={"active_test": False}, limit=0)
        self.tags18 = k.kw("project.tags", "search_read", [[]], fields=["id", "name"], limit=0)
        self.ma18 = k.kw("hr.employee", "search_read", [[]],
                         fields=["id", "name", "work_email", "user_id", "active"],
                         context={"active_test": False}, limit=0)
        self.users18 = k.kw("res.users", "search_read", [[]],
                            fields=["id", "login", "name", "active"],
                            context={"active_test": False}, limit=0)
        self.partner18 = k.kw("res.partner", "search_read", [[("is_company", "=", True)]],
                              fields=["id", "name"], limit=0)
        self.leaves18 = k.kw("hr.leave", "search_read", [[]],
                             fields=["employee_id", "date_from", "date_to", "state",
                                     "number_of_days"],
                             context={"active_test": False}, limit=0)
        self.zeilen18 = k.kw("account.analytic.line", "search_read", [[]],
                             fields=["date", "name", "unit_amount", "employee_id", "task_id",
                                     "project_id", "ref"], limit=0)
        uom = k.kw("uom.uom", "search_read", [[("name", "in", ["Hours", "Hour(s)"])]],
                   fields=["id", "name"], limit=1)
        self.uom_stunde = uom[0]["id"] if uom else False
        firma = k.kw("res.company", "search_read", [[]], fields=["id"], limit=1)
        self.firma = firma[0]["id"] if firma else 1
        self.active_ma18 = {m["id"]: bool(m["active"]) for m in self.ma18}
        print("  Odoo 18: %d Projekte, %d Aufgaben, %d Stufen, %d Tags, %d MA, %d Benutzer, "
              "%d Zeilen, %d Abwesenheiten"
              % (len(self.projekte18), len(self.aufgaben18), len(self.stufen18), len(self.tags18),
                 len(self.ma18), len(self.users18), len(self.zeilen18), len(self.leaves18)))

    # -------------------------------------------------------------- zuordnen
    def baue_plan(self):
        p18 = defaultdict(list)
        for p in self.projekte18:
            p18[norm(p["name"])].append(p)
        for p in self.projekte11:
            treffer = p18.get(norm(p["name"]), [])
            if len(treffer) > 1:
                self.blocker.append("Projekt '%s': %d gleichnamige in Odoo 18"
                                    % (p["name"], len(treffer)))
                continue
            kunde = None
            if p["partner_id"]:
                kt = [x for x in self.partner18 if norm(x["name"]) == norm(p["partner_id"][1])]
                if len(kt) == 1:
                    kunde = kt[0]["id"]
                elif not kt:
                    self.hinweise.append("Projekt '%s': Kunde '%s' fehlt in Odoo 18 "
                                         "(Partner-Migration offen)" % (p["name"],
                                                                        p["partner_id"][1]))
            if treffer and bool(treffer[0]["active"]) != bool(p["active"]):
                self.hinweise.append("Projekt '%s': Archivstatus O11=%s / O18=%s"
                                     % (p["name"], p["active"], treffer[0]["active"]))
            self.plan["projekte"].append({
                "o11_id": p["id"], "name": p["name"],
                "o18_id": treffer[0]["id"] if treffer else None,
                "konto18": (treffer[0]["account_id"] or [None])[0] if treffer else None,
                "aktiv": p["active"], "kunde": kunde, "sichtbarkeit": p["privacy_visibility"],
                "label_tasks": p["label_tasks"], "zeiterfassung": p["allow_timesheets"],
                "fuehrer": (p["user_id"][1] if p["user_id"] else None),
            })
        # Sammelprojekt fuer Zeilen ohne Projekt
        treffer_sammel = [x for x in self.plan["projekte"] if norm(x["name"]) == norm(SAMMELPROJEKT)]
        if treffer_sammel:
            self.plan["sammelprojekt"] = treffer_sammel[0]
        else:
            vorhanden = p18.get(norm(SAMMELPROJEKT), [])
            self.plan["sammelprojekt"] = {
                "o11_id": None, "name": SAMMELPROJEKT,
                "o18_id": vorhanden[0]["id"] if vorhanden else None,
                "konto18": (vorhanden[0]["account_id"] or [None])[0] if vorhanden else None,
                "aktiv": True, "kunde": None, "sichtbarkeit": "employees",
                "label_tasks": "Tasks", "zeiterfassung": True, "fuehrer": None,
            }
            self.plan["projekte"].append(self.plan["sammelprojekt"])

        # Stufen und Tags ueber Namen
        s18 = defaultdict(list)
        for s in self.stufen18:
            s18[norm(s["name"])].append(s)
        for s in self.stufen11:
            self.plan["stufen"].append({"o11_id": s["id"], "name": s["name"],
                                        "o18_id": s18[norm(s["name"])][0]["id"]
                                        if s18.get(norm(s["name"])) else None})
        t18 = defaultdict(list)
        for t in self.tags18:
            t18[norm(t["name"])].append(t)
        for t in self.tags11:
            self.plan["tags"].append({"o11_id": t["id"], "name": t["name"],
                                      "o18_id": t18[norm(t["name"])][0]["id"]
                                      if t18.get(norm(t["name"])) else None})

        # Aufgaben: Name innerhalb des Projekts eindeutig. Projektlose Aufgaben sind
        # in Odoo 18 private Aufgaben und nur ueber Name + Archivstatus zuordenbar.
        a18 = defaultdict(list)
        a18_privat = defaultdict(list)
        for a in self.aufgaben18:
            if a["project_id"]:
                a18[(a["project_id"][0], norm(a["name"]))].append(a)
            else:
                a18_privat[(norm(a["name"]), bool(a["active"]))].append(a)
        projekt_map = {p["o11_id"]: p["o18_id"] for p in self.plan["projekte"]}

        def gruppe(a):
            """Schluessel, unter dem gleiche Aufgaben zusammengefasst werden."""
            pid11 = a["project_id"][0] if a["project_id"] else None
            pid18 = projekt_map.get(pid11) if pid11 else None
            if pid11:
                return ("projekt", pid18, norm(a["name"]))
            return ("privat", norm(a["name"]), bool(a["active"]))

        # Doppelaufgaben: gleiche Position in der nach IDs sortierten Odoo-11-Gruppe
        # entspricht der gleichen Position in Odoo 18 (Reihenfolge der Migration).
        gruppen11 = defaultdict(list)
        for a in sorted(self.aufgaben11, key=lambda x: x["id"]):
            gruppen11[gruppe(a)].append(a)
        for a in self.aufgaben11:
            pid11 = a["project_id"][0] if a["project_id"] else None
            pid18 = projekt_map.get(pid11) if pid11 else None
            if pid11:
                treffer = a18.get((pid18, norm(a["name"])), []) if pid18 else []
            else:
                treffer = a18_privat.get((norm(a["name"]), bool(a["active"])), [])
            if len(treffer) > 1:
                ziel = None
                eigene = gruppen11[gruppe(a)]
                # 1. Wahl: exakt gleicher Name (unterscheidet z. B. Leerzeichen am Anfang)
                exakt = [x for x in treffer if x["name"] == a["name"]]
                if len(exakt) == 1:
                    ziel, grund = exakt[0], "exakter Name"
                elif len(eigene) == len(treffer):
                    sortiert = sorted(treffer, key=lambda x: x["id"])
                    position = [x["id"] for x in eigene].index(a["id"])
                    ziel, grund = sortiert[position], "Reihenfolge der IDs"
                if ziel is None:
                    self.blocker.append("Aufgabe '%s' (O11 %s): %d gleichnamige in Odoo 18, "
                                        "keine eindeutige Zuordnung"
                                        % (a["name"], a["id"], len(treffer)))
                    continue
                self.hinweise.append("Aufgabe '%s' kommt %d-mal vor (Projekt '%s'): O11 %s -> "
                                     "O18 %s ueber %s"
                                     % (a["name"], len(treffer),
                                        (a["project_id"] or [None, "(privat)"])[1],
                                        a["id"], ziel["id"], grund))
                treffer = [ziel]
            self.plan["aufgaben"].append({
                "o11_id": a["id"], "name": a["name"], "projekt11": pid11,
                "projekt18": pid18, "privat11": not pid11,
                "o18_id": treffer[0]["id"] if treffer else None,
                "aktiv": a["active"], "stufe": (a["stage_id"][1] if a["stage_id"] else None),
                "zugewiesen": (a["user_id"][1] if a["user_id"] else None),
                "frist": a["date_deadline"], "geplant": a["planned_hours"],
                "start": a["date_start"], "prioritaet": a["priority"],
            })

        # Mitarbeiter: Arbeits-E-Mail, sonst Name
        m18_mail = {norm(m["work_email"]): m for m in self.ma18 if m["work_email"]}
        m18_name = defaultdict(list)
        for m in self.ma18:
            m18_name[norm(m["name"])].append(m)
        self.ma_map = {}
        for m in self.ma11:
            ziel = m18_mail.get(norm(m["work_email"]))
            if not ziel:
                treffer = m18_name.get(norm(m["name"]), [])
                if len(treffer) == 1:
                    ziel = treffer[0]
                elif len(treffer) > 1:
                    self.blocker.append("Mitarbeiter '%s': %d gleichnamige in Odoo 18"
                                        % (m["name"], len(treffer)))
                    continue
            if not ziel:
                self.blocker.append("Mitarbeiter '%s' fehlt in Odoo 18" % m["name"])
                continue
            self.ma_map[m["id"]] = ziel["id"]
            if bool(ziel["active"]) != bool(m["active"]):
                self.hinweise.append("Mitarbeiter '%s': aktiv O11=%s / O18=%s"
                                     % (m["name"], m["active"], ziel["active"]))

        # Benutzer: fehlende Konten fuer historische user_id
        u18_login = {norm(u["login"]): u for u in self.users18}
        ma18_by_id = {m["id"]: m for m in self.ma18}
        self.user_map = {}
        self.user11_map = {}
        for m in self.ma11:
            if not m["user_id"]:
                continue
            u11 = self.users11.get(m["user_id"][0])
            if not u11:
                continue
            ziel_ma = ma18_by_id.get(self.ma_map.get(m["id"]))
            vorhanden = None
            if ziel_ma and ziel_ma["user_id"]:
                vorhanden = {"id": ziel_ma["user_id"][0]}
            if not vorhanden:
                vorhanden = u18_login.get(norm(u11["login"]))
            self.user_map[m["id"]] = {"login": u11["login"], "name": u11["name"],
                                      "o18_id": vorhanden["id"] if vorhanden else None,
                                      "aktiv": u11["active"]}
            if vorhanden:
                self.user11_map[u11["id"]] = vorhanden["id"]
            else:
                self.plan["benutzer"].append({"login": u11["login"], "name": u11["name"],
                                              "mitarbeiter11": m["id"]})

    # ------------------------------------------------------------- abwesenheit
    def loese_abwesenheit(self, hid11):
        """Liefert (holiday18_id | False, Begruendung)."""
        h11 = self.holidays11.get(hid11)
        if not h11 or not h11["employee_id"]:
            return False, "Odoo-11-Abwesenheit fehlt"
        ma = self.ma_map.get(h11["employee_id"][0])
        if not ma:
            return False, "Mitarbeiter der Abwesenheit nicht zugeordnet"
        beginn = str(h11["date_from"])[:10]
        tage11 = h11.get("number_of_days_temp")
        kandidaten = [x for x in self.leaves18
                      if (x["employee_id"] or [0])[0] == ma
                      and str(x["date_from"])[:10] == beginn]
        gebucht = [x for x in kandidaten if x["state"] == "validate"]
        if len(gebucht) == 1:
            return gebucht[0]["id"], "eindeutig, Status gebucht"
        if len(gebucht) > 1:
            gleich = [x for x in gebucht
                      if abs((x["number_of_days"] or 0) - (tage11 or 0)) < 0.001]
            if len(gleich) == 1:
                return gleich[0]["id"], "eindeutig, gebucht und gleiche Tagesanzahl"
            return None, "mehrdeutig: %d gebuchte Abwesenheiten am %s (%s)" % (
                len(gebucht), beginn,
                ", ".join("#%s %s Tage" % (x["id"], x["number_of_days"]) for x in gebucht))
        if kandidaten:
            return False, "kein gebuchter Antrag, nur Status %s" % ", ".join(
                sorted({x["state"] for x in kandidaten}))
        return False, "keine Abwesenheit am %s in Odoo 18" % beginn

    # ---------------------------------------------------------------- zeilen
    def plane_zeilen(self):
        for schluessel in ZEILEN_STATS:
            self.statistik.pop(schluessel, None)
        self.abw_status = Counter()
        self.plan["zeilen"] = []
        projekt_konto = {p["o11_id"]: p["o18_id"] for p in self.plan["projekte"]}
        aufgabe_map = {a["o11_id"]: a["o18_id"] for a in self.plan["aufgaben"]}
        privat_map = {a["o11_id"]: a["name"] for a in self.plan["aufgaben"] if a["privat11"]}
        aufgabe_projekt = {a["o11_id"]: a["projekt11"] for a in self.plan["aufgaben"]}
        offen = defaultdict(list)
        for z in self.zeilen18:
            schluessel = self.fingerabdruck(
                sql_date(z["date"]), (z["employee_id"] or [0])[0],
                (z["project_id"] or [0])[0], (z["task_id"] or [0])[0],
                z["unit_amount"], z["name"], z["ref"] or "")
            offen[schluessel].append(z)
        sammel = self.plan.get("sammelprojekt") or {}
        mapping = {}
        for z in self.zeilen11:
            if z["project_id"]:
                if z["project_id"][0] not in projekt_konto:
                    self.blocker.append("Zeile %s: Projekt '%s' nicht geplant"
                                        % (z["id"], z["project_id"][1]))
                    continue
                pid = projekt_konto.get(z["project_id"][0])
            else:
                pid = sammel.get("o18_id")     # Zeilen ohne Projekt -> Sammelprojekt
            if z["task_id"] and z["task_id"][0] not in aufgabe_map:
                self.blocker.append("Zeile %s: Aufgabe '%s' nicht geplant"
                                    % (z["id"], z["task_id"][1]))
                continue
            tid = aufgabe_map.get(z["task_id"][0]) if z["task_id"] else None
            ma = self.ma_map.get(z["employee_id"][0]) if z["employee_id"] else None
            if z["employee_id"] and ma is None:
                self.blocker.append("Zeile %s: Mitarbeiter '%s' nicht zugeordnet"
                                    % (z["id"], z["employee_id"][1]))
                continue
            refs = []
            if z["support_ticket_id"]:
                t = self.tickets11.get(z["support_ticket_id"][0])
                if t and t.get("ticket_number"):
                    refs.append("O11-Ticket %s" % t["ticket_number"])
                else:
                    self.hinweise.append("Zeile %s: Ticket %s ohne Nummer"
                                         % (z["id"], z["support_ticket_id"][0]))
            if z["task_id"] and z["task_id"][0] in privat_map:
                refs.append("O11-Aufgabe %s" % privat_map[z["task_id"][0]])
                tid = None      # private Aufgabe: Odoo 18 verweigert Zeiterfassung
            elif (z["task_id"] and z["project_id"]
                  and aufgabe_projekt.get(z["task_id"][0]) not in (None, z["project_id"][0])):
                # Odoo 11 erlaubt eine Aufgabe aus einem anderen Projekt; Odoo 18
                # setzt die Aufgabe beim Anlegen zurueck. Projekt bleibt wie in
                # Odoo 11, der Aufgabentitel bleibt als Referenz erhalten.
                refs.append("O11-Aufgabe %s" % z["task_id"][1])
                tid = None
            if not z["project_id"] and z["account_id"]:
                refs.append("O11-Kostenstelle %s" % z["account_id"][1])
            ref = " | ".join(refs) or False
            holiday = False
            hatte_abw = bool(z["holiday_id"])
            if hatte_abw:
                holiday, grund = self.loese_abwesenheit(z["holiday_id"][0])
                self.abw_status[grund.split(",")[0].split(":")[0]] += 1
                if holiday is None:
                    self.blocker.append("Zeile %s (Datum %s, '%s'): Abwesenheit O11 %s - %s"
                                        % (z["id"], sql_date(z["date"]), (z["name"] or "")[:40],
                                           z["holiday_id"][0], grund))
                    continue
            fp = self.fingerabdruck(sql_date(z["date"]), ma or 0, pid or 0, tid or 0,
                                    z["unit_amount"], z["name"], ref or "")
            kandidaten = offen.get(fp) or []
            bereits = kandidaten.pop(0) if kandidaten else None
            if bereits:
                mapping[z["id"]] = bereits["id"]
            self.plan["zeilen"].append({
                "o11_id": z["id"], "date": sql_date(z["date"]),
                "date_time": "%s 00:00:00" % sql_date(z["date"]), "name": z["name"],
                "unit_amount": z["unit_amount"], "employee18": ma, "project18": pid,
                "task18": tid, "ref": ref, "holiday18": holiday,
                "user11": (z["user_id"] or [0])[0],
                "invoice_type11": z["timesheet_invoice_type"],
                "ohne_projekt": not z["project_id"],
                "privat_aufgabe": bool(z["task_id"] and z["task_id"][0] in privat_map),
                "hatte_abwesenheit": hatte_abw,
                "bereits_vorhanden": bool(bereits),
            })
        self.mapping = mapping
        p = self.plan
        self.statistik["zeilen"] = len(p["zeilen"])
        self.statistik["zeilen_neu"] = sum(1 for z in p["zeilen"] if not z["bereits_vorhanden"])
        self.statistik["zeilen_vorhanden"] = (self.statistik["zeilen"]
                                             - self.statistik["zeilen_neu"])
        self.statistik["zeilen_ohne_projekt"] = sum(1 for z in p["zeilen"] if z["ohne_projekt"])
        self.statistik["zeilen_private_aufgabe"] = sum(1 for z in p["zeilen"]
                                                       if z["privat_aufgabe"])
        self.statistik["zeilen_ticket_ref"] = sum(1 for z in p["zeilen"]
                                                  if z["ref"] and "O11-Ticket" in z["ref"])
        self.statistik["zeilen_kostenstelle_ref"] = sum(
            1 for z in p["zeilen"] if z["ref"] and "O11-Kostenstelle" in z["ref"])
        self.statistik["zeilen_abwesenheit"] = sum(1 for z in self.zeilen11 if z["holiday_id"])
        self.statistik["abwesenheit_zugeordnet"] = sum(1 for z in p["zeilen"] if z["holiday18"])
        self.statistik["abwesenheit_ohne_treffer"] = sum(
            1 for z in p["zeilen"] if z["hatte_abwesenheit"] and not z["holiday18"])
        self.statistik["stunden"] = round(sum(z["unit_amount"] or 0 for z in self.zeilen11), 2)
        self.statistik["stunden_neu"] = round(sum(z["unit_amount"] or 0 for z in p["zeilen"]
                                                  if not z["bereits_vorhanden"]), 2)
        self.statistik["projekte_neu"] = sum(1 for x in p["projekte"] if not x["o18_id"])
        self.statistik["aufgaben_neu"] = sum(1 for x in p["aufgaben"] if not x["o18_id"])
        self.statistik["stufen_neu"] = sum(1 for x in p["stufen"] if not x["o18_id"])
        self.statistik["tags_neu"] = sum(1 for x in p["tags"] if not x["o18_id"])
        self.statistik["benutzer_neu"] = len(p["benutzer"])
        self.archiviert18 = sorted({z["employee18"] for z in p["zeilen"]
                                    if z["employee18"] and not z["bereits_vorhanden"]
                                    and not self.active_ma18.get(z["employee18"], True)})
        self.statistik["zeilen_archivierter_mitarbeiter"] = sum(
            1 for z in p["zeilen"] if z["employee18"] in set(self.archiviert18))

    @staticmethod
    def fingerabdruck(date, ma, pid, tid, menge, name, ref):
        return (str(date), ma or 0, pid or 0, tid or 0, round(menge or 0, 6),
                norm(name), ref or "")

    def bericht(self):
        print("\n=== Plan ===")
        for k in ("projekte_neu", "aufgaben_neu", "stufen_neu", "tags_neu", "benutzer_neu",
                  "zeilen", "zeilen_neu", "zeilen_vorhanden", "zeilen_ohne_projekt",
                  "zeilen_private_aufgabe", "zeilen_ticket_ref", "zeilen_kostenstelle_ref",
                  "zeilen_abwesenheit", "abwesenheit_zugeordnet", "abwesenheit_ohne_treffer",
                  "stunden", "stunden_neu", "zeilen_archivierter_mitarbeiter"):
            print("  %-34s %s" % (k, self.statistik.get(k)))
        print("\n  Projekte bereits vorhanden: %d / neu: %d"
              % (len(self.plan["projekte"]) - self.statistik["projekte_neu"],
                 self.statistik["projekte_neu"]))
        print("  Aufgaben bereits vorhanden: %d / neu: %d"
              % (len(self.plan["aufgaben"]) - self.statistik["aufgaben_neu"],
                 self.statistik["aufgaben_neu"]))
        print("  Benutzer anzulegen (inaktiv): %d %s"
              % (len(self.plan["benutzer"]), [b["login"] for b in self.plan["benutzer"]]))
        print("  Mitarbeiter kurz zu aktivieren: %d %s"
              % (len(self.archiviert18),
                 [m["name"] for m in self.ma18 if m["id"] in set(self.archiviert18)]))
        if self.abw_status:
            print("  Abwesenheitszuordnung: %s" % dict(self.abw_status))
        if self.hinweise:
            print("\n=== Hinweise (%d) ===" % len(self.hinweise))
            for h in self.hinweise[:20]:
                print("   -", h)
        if self.blocker:
            print("\n=== Blocker (%d) ===" % len(self.blocker))
            for b in self.blocker[:30]:
                print("   !", b)
        else:
            print("\n  Keine Blocker.")

    def protokoll(self, name="plan"):
        os.makedirs(PROTO, exist_ok=True)
        pfad = os.path.join(PROTO, "%s_%s.json" % (name, self.instanz))
        daten = {"statistik": dict(self.statistik), "blocker": self.blocker,
                 "hinweise": self.hinweise, "mapping": self.mapping,
                 "aktiviert": self.aktiviert, "plan": self.plan}
        with open(pfad, "w", encoding="utf-8") as fh:
            json.dump(daten, fh, ensure_ascii=False, default=str)
        print("  Protokoll:", pfad)
        return pfad

    # --------------------------------------------------------------- schreiben
    def schreibe(self):
        if self.blocker:
            raise Blocker("%d Blocker offen - kein Schreibzugriff." % len(self.blocker))
        k = self.k18
        sammel = self.plan["sammelprojekt"]
        if not sammel.get("o18_id"):
            vals = {"name": SAMMELPROJEKT, "allow_timesheets": True, "allow_billable": False,
                    "privacy_visibility": "employees", "company_id": self.firma}
            neu = k.kw("project.project", "create", [vals], context=SCHREIB_CTX)
            sammel["o18_id"] = neu
            selbst = k.kw("project.project", "read", [neu], fields=["account_id"])[0]
            sammel["konto18"] = (selbst["account_id"] or [None])[0]
            self.sammel_neu = True
            print("  Sammelprojekt angelegt: #%s (Konto %s)"
                  % (sammel["o18_id"], sammel["konto18"]))
            # Plan neu rechnen, damit die projektlosen Zeilen die neue ID bekommen
            self.plan["zeilen"] = []
            self.plane_zeilen()

        projekt_konto = {p["o18_id"]: p["konto18"] for p in self.plan["projekte"] if p["o18_id"]}
        for b in self.plan["benutzer"]:
            neu = k.kw("res.users", "create", [{"login": b["login"], "name": b["name"],
                                                "active": True, "share": False}],
                       context=SCHREIB_CTX)
            k.kw("res.users", "write", [[neu], {"active": False}], context=SCHREIB_CTX)
            print("  Benutzer inaktiv angelegt: %s (#%s)" % (b["login"], neu))
            for mid, info in self.user_map.items():
                if info["login"] == b["login"]:
                    info["o18_id"] = neu

        ma_by_id = {m["id"]: m for m in self.ma18}
        zeilen = [z for z in self.plan["zeilen"] if not z["bereits_vorhanden"]]
        if self.grenze:
            zeilen = zeilen[:self.grenze]
        print("  Zu schreiben: %d Zeilen (Stapel %d), uebersprungen: %d"
              % (len(zeilen), self.stapel, self.statistik["zeilen_vorhanden"]))
        try:
            for mid in self.archiviert18:
                k.kw("hr.employee", "write", [[mid], {"active": True}], context=SCHREIB_CTX)
                self.aktiviert.append(mid)
            if self.aktiviert:
                print("  Kurz aktiviert: %s" % [ma_by_id[m]["name"] for m in self.aktiviert])
            for start in range(0, len(zeilen), self.stapel):
                block = zeilen[start:start + self.stapel]
                vals_list = [self.werte(z, projekt_konto) for z in block]
                try:
                    ids = k.kw("account.analytic.line", "create", [vals_list],
                               context=SCHREIB_CTX)
                except Exception as fehler:
                    raise Blocker("Stapel ab Zeile %d (O11 %s .. %s) fehlgeschlagen: %s"
                                  % (start, block[0]["o11_id"], block[-1]["o11_id"],
                                     str(fehler)[-400:]))
                for z, neu_id in zip(block, ids):
                    self.mapping[z["o11_id"]] = neu_id
                self.neu += len(ids)
                print("    %5d / %5d geschrieben (O11 %s .. %s)"
                      % (min(start + self.stapel, len(zeilen)), len(zeilen),
                         block[0]["o11_id"], block[-1]["o11_id"]))
        finally:
            for mid in self.aktiviert:
                k.kw("hr.employee", "write", [[mid], {"active": False}], context=SCHREIB_CTX)
            if self.aktiviert:
                print("  Wieder archiviert: %s" % [ma_by_id[m]["name"] for m in self.aktiviert])
        self.uebersprungen = self.statistik["zeilen_vorhanden"]
        print("\n  Neu geschrieben: %d / uebersprungen (bereits vorhanden): %d"
              % (self.neu, self.uebersprungen))

    def repariere_beschreibung(self):
        """Setzt bereits geschriebene Beschreibungen exakt auf den Odoo-11-Wortlaut.

        Notwendig, weil der erste Lauf Rand-Leerzeichen entfernt hatte (665 Zeilen).
        Es wird ausschliesslich das Feld `name` geschrieben, nichts geloescht.
        """
        k = self.k18
        ids = [oid for oid in (self.mapping.get(z["o11_id"]) for z in self.plan["zeilen"]) if oid]
        gefunden = {}
        for i in range(0, len(ids), 500):
            for r in k.kw("account.analytic.line", "read", [ids[i:i + 500]],
                          fields=["id", "name"]):
                gefunden[r["id"]] = r["name"]
        gruppen = defaultdict(list)
        for z in self.plan["zeilen"]:
            oid = self.mapping.get(z["o11_id"])
            if not oid or oid not in gefunden:
                continue
            soll = z["name"] if (z["name"] or "").strip() else "/"
            if gefunden[oid] != soll:
                gruppen[soll].append(oid)
        anzahl = sum(len(v) for v in gruppen.values())
        print("  Beschreibungen abweichend: %d in %d Gruppen" % (anzahl, len(gruppen)))
        for soll, liste in gruppen.items():
            k.kw("account.analytic.line", "write", [liste, {"name": soll}],
                 context=SCHREIB_CTX)
        # Nachkontrolle
        rest = 0
        for i in range(0, len(ids), 500):
            for r in k.kw("account.analytic.line", "read", [ids[i:i + 500]],
                          fields=["id", "name"]):
                gefunden[r["id"]] = r["name"]
        for z in self.plan["zeilen"]:
            oid = self.mapping.get(z["o11_id"])
            if oid and oid in gefunden and gefunden[oid] != (z["name"] if (z["name"] or "").strip()
                                                            else "/"):
                rest += 1
        print("  Nachkontrolle: %d Zeilen weiterhin abweichend" % rest)
        return anzahl

    def werte(self, z, projekt_konto):
        vals = {
            # Beschreibung: Odoo 18 fuehrt keine Rand-Leerzeichen. 665 Odoo-11-Zeilen
            # hatten solche (" (1/1)", "neues Formular erstellt "); der Text selbst
            # bleibt unveraendert. Bei 298 dieser Zeilen ist eine exakte Rückschreibung
            # technisch gesperrt (Odoo 18 verweigert Writes auf Zeiterfassungen mit
            # Abwesenheitsbezug) - deshalb wird einheitlich getrimmt.
            "name": (z["name"] or "").strip() or "/",
            "date": z["date"],
            "unit_amount": z["unit_amount"] or 0.0,
            "employee_id": z["employee18"],
            "project_id": z["project18"],
            "date_time": z["date_time"],
            "company_id": self.firma,
        }
        if self.uom_stunde:
            vals["product_uom_id"] = self.uom_stunde
        if z["task18"]:
            vals["task_id"] = z["task18"]
        konto = projekt_konto.get(z["project18"])
        if konto:
            vals["account_id"] = konto
        if z["ref"]:
            vals["ref"] = z["ref"]
        if z["holiday18"]:
            vals["holiday_id"] = z["holiday18"]
        # Benutzer: Odoo-11-Benutzer der Zeile, sonst der Benutzer des Mitarbeiters
        user18 = self.user11_map.get(z.get("user11"))
        if not user18:
            mid11 = next((m for m, m18 in self.ma_map.items() if m18 == z["employee18"]), None)
            user18 = (self.user_map.get(mid11) or {}).get("o18_id")
        if user18:
            vals["user_id"] = user18
        return vals


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    ap.add_argument("--projekt-abgeschlossen", action="store_true")
    ap.add_argument("--plan-schreiben", action="store_true")
    ap.add_argument("--grenze", type=int, default=0, help="nur die ersten N neuen Zeilen schreiben")
    ap.add_argument("--stapel", type=int, default=200)
    ap.add_argument("--reparatur-beschreibung", action="store_true",
                    help="nur abweichende Beschreibungen exakt auf Odoo 11 zuruecksetzen")
    a = ap.parse_args()

    env = lade_env()
    if a.ausfuehren and not a.ich_habe_freigabe:
        print("STOPP: --ausfuehren nur zusammen mit --ich-habe-freigabe")
        return 2
    if a.ausfuehren and not a.projekt_abgeschlossen:
        print("STOPP: Migration gesperrt - Modul Projekt ist noch nicht abgenommen.")
        return 3
    if (a.ausfuehren or a.reparatur_beschreibung) and not env["ODOO18_DB"].endswith("odoo18_test"):
        print("STOPP: Ziel-DB ist nicht die Testdatenbank:", env["ODOO18_DB"])
        return 2
    if a.reparatur_beschreibung and not a.ich_habe_freigabe:
        print("STOPP: --reparatur-beschreibung nur zusammen mit --ich-habe-freigabe")
        return 2

    m = Migration(a.instanz, a.ausfuehren, grenze=a.grenze, stapel=a.stapel)
    print("### Zeiterfassung-Migration, Instanz:", a.instanz,
          " Modus:", "SCHREIBEN" if a.ausfuehren else "Trockenlauf")
    m.lese_o11()
    m.lese_o18()
    m.baue_plan()
    m.plane_zeilen()
    m.bericht()
    if a.plan_schreiben:
        m.protokoll("plan")
    if a.reparatur_beschreibung:
        m.repariere_beschreibung()
        m.protokoll("ergebnis")
        print("\nReparatur beendet.")
        return 0
    if a.ausfuehren:
        try:
            m.schreibe()
        except Blocker as fehler:
            print("\nABBRUCH:", fehler)
            m.protokoll("abbruch")
            return 4
        m.protokoll("ergebnis")
        print("\nSchreiblauf beendet.")
    else:
        print("\nTrockenlauf - keine Aenderung geschrieben.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
