"""Datenmigration ZEITERFASSUNG: Odoo 11 (Produktion, read-only) -> Odoo 18.

STAND 22.10.2026: Die Migration ist VORBEREITET, aber GESPERRT. Der Schreiblauf
verlangt zusaetzlich `--projekt-abgeschlossen`, weil die Zeiterfassung an der
Projekt-/Aufgabenstruktur haengt und das Modul Projekt noch nicht abgenommen ist.

Aufruf:
    python scripts/zeiterfassung_migration.py --instanz lokal
    python scripts/zeiterfassung_migration.py --instanz lokal --plan-schreiben
    # spaeter, nach Projekt-Abnahme:
    python scripts/zeiterfassung_migration.py --instanz lokal --ausfuehren \
        --ich-habe-freigabe --projekt-abgeschlossen

Regeln (Anna, 22.10.2026):
  * Odoo 11 ausschliesslich lesen.
  * Ziel nur die Testdatenbank (ODOO18_DB endet auf odoo18_test).
  * Zuordnung ueber fachliche Schluessel (E-Mail/Name, Projektname, Aufgabentitel),
    nie ueber Datenbank-IDs; bei Mehrdeutigkeit Abbruch mit Klartext.
  * Vollstaendige Historie: auch Zeilen archivierter Mitarbeiter (1.605) und
    Zeilen ohne Projekt (282, Sammelprojekt "Ohne Projekt (Uebernahme Odoo 11)").
  * 11 fehlende Benutzerkonten werden als inaktive Benutzer angelegt, damit
    user_id erhalten bleibt.
  * Startzeit historischer Zeilen: 00:00 des Odoo-11-Datums.
  * Support-Ticket-Verweise: KEINE neuen Helpdesk-Tickets; die Odoo-11-Ticketnummer
    wird als historische Referenz in `ref` geschrieben ("O11-Ticket <Nummer>").
  * Protokoll ausserhalb des Repos (%LOCALAPPDATA%\\Temp\\zeiterfassung_migration\\).
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
PROTO = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Temp", "zeiterfassung_migration")
SAMMELPROJEKT = "Ohne Projekt (Uebernahme Odoo 11)"
INVOICE_MAP = {
    "billable_time": "billable_time",
    "billable_fixed": "billable_fixed",
    "non_billable": "non_billable",
    # Odoo 18 kennt "Keine Aufgabe gefunden" nicht mehr
    "non_billable_project": "non_billable",
    False: "non_billable",
    None: "non_billable",
}


class Blocker(Exception):
    pass


def norm(wert):
    return " ".join((wert or "").split()).lower()


class Migration:
    def __init__(self, instanz: str, schreiben: bool):
        self.k11 = o11()
        self.k18 = o18(instanz)
        self.instanz = instanz
        self.schreiben = schreiben
        self.statistik = Counter()
        self.blocker = []
        self.hinweise = []
        self.plan = {"stufen": [], "tags": [], "projekte": [], "aufgaben": [],
                     "benutzer": [], "zeilen": []}

    # ------------------------------------------------------------------ lesen
    def lese_o11(self):
        k = self.k11
        self.stufen11 = k.kw("project.task.type", "search_read", [[]],
                             fields=["id", "name", "sequence", "fold", "project_ids",
                                     "legend_priority"], context={"active_test": False}, limit=0)
        f_tags = k.kw("project.tags", "fields_get", [], attributes=["string"])
        self.tags11 = k.kw("project.tags", "search_read", [[]], fields=["id", "name", "color"],
                           limit=0) if "name" in f_tags else []
        f_pro = k.kw("project.project", "fields_get", [], attributes=["string"])
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
                                     "support_ticket_id", "timesheet_invoice_type", "product_uom_id"],
                             order="date,id", limit=0)
        self.ma11 = k.kw("hr.employee", "search_read", [[]],
                         fields=["id", "name", "work_email", "user_id", "active", "job_id"],
                         context={"active_test": False}, order="id", limit=0)
        # Ticketnummern der 295 Tickets
        tids = sorted({z["support_ticket_id"][0] for z in self.zeilen11 if z["support_ticket_id"]})
        self.tickets11 = {t["id"]: t for t in k.kw("website.support.ticket", "read", [tids],
                                                   fields=["ticket_number", "subject", "create_date"])}
        # Abwesenheiten (für holiday_id der 1.131 Zeilen) - Zuordnung ueber Mitarbeiter + Beginn
        hids = sorted({z["holiday_id"][0] for z in self.zeilen11 if z["holiday_id"]})
        self.holidays11 = {h["id"]: h for h in k.kw("hr.holidays", "read", [hids],
                                                    fields=["employee_id", "date_from", "date_to",
                                                            "holiday_status_id", "state"])} if hids else {}
        # Benutzer zu den Mitarbeitern (Login fuer spätere user_id)
        uids = sorted({m["user_id"][0] for m in self.ma11 if m["user_id"]})
        self.users11 = {u["id"]: u for u in k.kw("res.users", "read", [uids],
                                                 fields=["login", "name", "active", "email"])}
        print("  Odoo 11: %d Stufen, %d Tags, %d Projekte, %d Aufgaben, %d Zeilen, %d MA, %d Tickets"
              % (len(self.stufen11), len(self.tags11), len(self.projekte11), len(self.aufgaben11),
                 len(self.zeilen11), len(self.ma11), len(self.tickets11)))

    def lese_o18(self):
        k = self.k18
        self.projekte18 = k.kw("project.project", "search_read", [[]],
                               fields=["id", "name", "account_id", "allow_timesheets"],
                               context={"active_test": False}, limit=0)
        self.aufgaben18 = k.kw("project.task", "search_read", [[]],
                               fields=["id", "name", "project_id"],
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
                             fields=["employee_id", "date_from", "date_to", "state"],
                             context={"active_test": False}, limit=0)
        self.zeilen18 = k.kw("account.analytic.line", "search_read", [[]],
                             fields=["date", "name", "unit_amount", "employee_id", "task_id",
                                     "project_id", "ref"], limit=0)
        print("  Odoo 18: %d Projekte, %d Aufgaben, %d Stufen, %d Tags, %d MA, %d Benutzer, %d Zeilen"
              % (len(self.projekte18), len(self.aufgaben18), len(self.stufen18), len(self.tags18),
                 len(self.ma18), len(self.users18), len(self.zeilen18)))

    # -------------------------------------------------------------- zuordnen
    def baue_plan(self):
        # Projekt: Name muss eindeutig sein (Odoo 18 hat nur Testprojekte)
        p18 = defaultdict(list)
        for p in self.projekte18:
            p18[norm(p["name"])].append(p)
        for p in self.projekte11:
            treffer = p18.get(norm(p["name"]), [])
            if len(treffer) > 1:
                self.blocker.append("Projekt '%s': %d gleichnamige in Odoo 18" % (p["name"], len(treffer)))
                continue
            kunde = None
            if p["partner_id"]:
                kt = [x for x in self.partner18 if norm(x["name"]) == norm(p["partner_id"][1])]
                if len(kt) == 1:
                    kunde = kt[0]["id"]
                elif not kt:
                    self.hinweise.append("Projekt '%s': Kunde '%s' fehlt in Odoo 18 (Partner-Migration offen)"
                                         % (p["name"], p["partner_id"][1]))
            self.plan["projekte"].append({
                "o11_id": p["id"], "name": p["name"], "o18_id": treffer[0]["id"] if treffer else None,
                "aktiv": p["active"], "kunde": kunde, "sichtbarkeit": p["privacy_visibility"],
                "label_tasks": p["label_tasks"], "zeiterfassung": p["allow_timesheets"],
                "fuehrer": (p["user_id"][1] if p["user_id"] else None),
            })
        # Sammelprojekt fuer Zeilen ohne Projekt (Odoo 11: Kostenstellenbuchungen)
        treffer_sammel = [x for x in self.plan["projekte"] if norm(x["name"]) == norm(SAMMELPROJEKT)]
        if treffer_sammel:
            self.plan["sammelprojekt"] = treffer_sammel[0]
        else:
            vorhanden_sammel = p18.get(norm(SAMMELPROJEKT), [])
            self.plan["sammelprojekt"] = {
                "o11_id": None, "name": SAMMELPROJEKT,
                "o18_id": vorhanden_sammel[0]["id"] if vorhanden_sammel else None,
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
                                        "o18_id": s18.get(norm(s["name"]), [{}])[0].get("id")
                                        if s18.get(norm(s["name"])) else None})
        t18 = defaultdict(list)
        for t in self.tags18:
            t18[norm(t["name"])].append(t)
        for t in self.tags11:
            self.plan["tags"].append({"o11_id": t["id"], "name": t["name"],
                                      "o18_id": t18.get(norm(t["name"]), [{}])[0].get("id")
                                      if t18.get(norm(t["name"])) else None})

        # Aufgaben: Name innerhalb des Projekts eindeutig
        a18 = defaultdict(list)
        for a in self.aufgaben18:
            pid = a["project_id"][0] if a["project_id"] else 0
            a18[(pid, norm(a["name"]))].append(a)
        projekt_map = {p["o11_id"]: p["o18_id"] for p in self.plan["projekte"]}
        for a in self.aufgaben11:
            pid11 = a["project_id"][0] if a["project_id"] else None
            pid18 = projekt_map.get(pid11) if pid11 else None
            treffer = a18.get((pid18, norm(a["name"])), []) if pid18 else []
            self.plan["aufgaben"].append({
                "o11_id": a["id"], "name": a["name"], "projekt11": pid11,
                "projekt18": pid18, "o18_id": treffer[0]["id"] if treffer else None,
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
            quelle = "E-Mail"
            if not ziel:
                treffer = m18_name.get(norm(m["name"]), [])
                if len(treffer) == 1:
                    ziel, quelle = treffer[0], "Name"
                elif len(treffer) > 1:
                    self.blocker.append("Mitarbeiter '%s': %d gleichnamige in Odoo 18" % (m["name"], len(treffer)))
                    continue
            if not ziel:
                self.blocker.append("Mitarbeiter '%s' fehlt in Odoo 18" % m["name"])
                continue
            self.ma_map[m["id"]] = ziel["id"]
            if bool(ziel["active"]) != bool(m["active"]):
                self.hinweise.append("Mitarbeiter '%s': aktiv O11=%s / O18=%s"
                                     % (m["name"], m["active"], ziel["active"]))

        # Benutzer: 11 fehlende fuer historische user_id
        u18_login = {norm(u["login"]): u for u in self.users18}
        ma18_by_id = {m["id"]: m for m in self.ma18}
        self.user_map = {}
        for m in self.ma11:
            if not m["user_id"]:
                continue
            u11 = self.users11.get(m["user_id"][0])
            if not u11:
                continue
            # 1. Wahl: der Odoo-18-Mitarbeiter hat bereits ein Benutzerkonto
            ziel_ma = ma18_by_id.get(self.ma_map.get(m["id"]))
            vorhanden = None
            if ziel_ma and ziel_ma["user_id"]:
                vorhanden = {"id": ziel_ma["user_id"][0]}
            # 2. Wahl: gleicher Login
            if not vorhanden:
                vorhanden = u18_login.get(norm(u11["login"]))
            self.user_map[m["id"]] = {"login": u11["login"], "name": u11["name"],
                                      "o18_id": vorhanden["id"] if vorhanden else None,
                                      "aktiv": u11["active"]}
            if not vorhanden:
                self.plan["benutzer"].append({"login": u11["login"], "name": u11["name"],
                                              "mitarbeiter11": m["id"]})

    # ---------------------------------------------------------------- zeilen
    def plane_zeilen(self):
        projekt_map = {p["o11_id"]: p["o18_id"] for p in self.plan["projekte"]}
        aufgabe_map = {a["o11_id"]: a["o18_id"] for a in self.plan["aufgaben"]}
        vorhanden = Counter()
        for z in self.zeilen18:
            schluessel = (str(z["date"]), (z["employee_id"] or [0])[0],
                          (z["project_id"] or [0])[0], (z["task_id"] or [0])[0],
                          round(z["unit_amount"] or 0, 4), norm(z["name"]))
            vorhanden[schluessel] += 1
        for z in self.zeilen11:
            sammel = self.plan.get("sammelprojekt") or {}
            if z["project_id"]:
                if z["project_id"][0] not in projekt_map:
                    self.blocker.append("Zeile %s: Projekt '%s' nicht geplant"
                                        % (z["id"], z["project_id"][1]))
                    continue
                pid = projekt_map.get(z["project_id"][0])
            else:
                pid = sammel.get("o18_id")     # Zeilen ohne Projekt -> Sammelprojekt
            tid = aufgabe_map.get(z["task_id"][0]) if z["task_id"] else None
            ma = self.ma_map.get(z["employee_id"][0]) if z["employee_id"] else None
            if z["task_id"] and z["task_id"][0] not in aufgabe_map:
                self.blocker.append("Zeile %s: Aufgabe '%s' nicht geplant"
                                    % (z["id"], z["task_id"][1]))
                continue
            if z["employee_id"] and ma is None:
                self.blocker.append("Zeile %s: Mitarbeiter '%s' nicht zugeordnet" % (z["id"], z["employee_id"][1]))
                continue
            holiday = None
            if z["holiday_id"]:
                h11 = self.holidays11.get(z["holiday_id"][0])
                if h11 and h11["employee_id"]:
                    beginn = str(h11["date_from"])[:10]
                    treffer_h = [x for x in self.leaves18
                                 if (x["employee_id"] or [0])[0] == self.ma_map.get(h11["employee_id"][0])
                                 and str(x["date_from"])[:10] == beginn]
                    if len(treffer_h) == 1:
                        holiday = treffer_h[0]["id"]
                    elif len(treffer_h) > 1:
                        self.hinweise.append("Abwesenheit O11 %s: %d Treffer in Odoo 18"
                                             % (z["holiday_id"][0], len(treffer_h)))
                    else:
                        holiday = False
                        self.statistik["abwesenheit_ohne_treffer"] += 1
            ref = False
            if z["support_ticket_id"]:
                t = self.tickets11.get(z["support_ticket_id"][0])
                if t and t.get("ticket_number"):
                    ref = "O11-Ticket %s" % t["ticket_number"]
            schluessel = (str(z["date"]), ma or 0, pid or 0, tid or 0,
                          round(z["unit_amount"] or 0, 4), norm(z["name"]))
            self.plan["zeilen"].append({
                "o11_id": z["id"], "date": str(z["date"]),
                "date_time": "%s 00:00:00" % z["date"], "name": z["name"],
                "unit_amount": z["unit_amount"], "employee18": ma, "project18": pid,
                "task18": tid, "ref": ref, "holiday18": holiday,
                "invoice_type": INVOICE_MAP.get(z["timesheet_invoice_type"], "non_billable"),
                "ohne_projekt": not z["project_id"],
                "bereits_vorhanden": vorhanden.get(schluessel, 0) > 0,
            })
        # Statistik
        p = self.plan
        self.statistik["zeilen"] = len(p["zeilen"])
        self.statistik["zeilen_neu"] = sum(1 for z in p["zeilen"] if not z["bereits_vorhanden"])
        self.statistik["zeilen_ohne_projekt"] = sum(1 for z in p["zeilen"] if z["ohne_projekt"])
        self.statistik["projekte_gesamt_plan"] = len(p["projekte"])
        self.statistik["aufgaben_gesamt_plan"] = len(p["aufgaben"])
        self.statistik["zeilen_ticket_ref"] = sum(1 for z in p["zeilen"] if z["ref"])
        self.statistik["zeilen_abwesenheit"] = sum(1 for z in self.zeilen11 if z["holiday_id"])
        self.statistik["abwesenheit_zugeordnet"] = sum(1 for z in p["zeilen"] if z.get("holiday18"))
        self.statistik["abwesenheit_ohne_treffer"] = sum(
            1 for z in p["zeilen"] if z["holiday18"] is False)
        self.statistik["stunden"] = round(sum(z["unit_amount"] or 0 for z in self.zeilen11), 2)
        self.statistik["projekte_neu"] = sum(1 for x in p["projekte"] if not x["o18_id"])
        self.statistik["aufgaben_neu"] = sum(1 for x in p["aufgaben"] if not x["o18_id"])
        self.statistik["stufen_neu"] = sum(1 for x in p["stufen"] if not x["o18_id"])
        self.statistik["tags_neu"] = sum(1 for x in p["tags"] if not x["o18_id"])
        self.statistik["benutzer_neu"] = len(p["benutzer"])

    def bericht(self):
        print("\n=== Plan ===")
        for k in ("projekte_neu", "aufgaben_neu", "stufen_neu", "tags_neu", "benutzer_neu",
                  "zeilen", "zeilen_neu", "zeilen_ohne_projekt", "zeilen_ticket_ref",
                  "zeilen_abwesenheit", "abwesenheit_zugeordnet",
                  "abwesenheit_ohne_treffer", "stunden"):
            print("  %-24s %s" % (k, self.statistik.get(k)))
        print("\n  Projekte bereits vorhanden: %d / neu: %d"
              % (len(self.plan["projekte"]) - self.statistik["projekte_neu"], self.statistik["projekte_neu"]))
        print("  Aufgaben bereits vorhanden: %d / neu: %d"
              % (len(self.plan["aufgaben"]) - self.statistik["aufgaben_neu"], self.statistik["aufgaben_neu"]))
        print("  Benutzer anzulegen (inaktiv): %d %s"
              % (len(self.plan["benutzer"]), [b["login"] for b in self.plan["benutzer"]]))
        if self.hinweise:
            print("\n=== Hinweise (%d) ===" % len(self.hinweise))
            for h in self.hinweise[:15]:
                print("   -", h)
        if self.blocker:
            print("\n=== Blocker (%d) ===" % len(self.blocker))
            for b in self.blocker[:20]:
                print("   !", b)
        else:
            print("\n  Keine Blocker.")

    def protokoll(self):
        os.makedirs(PROTO, exist_ok=True)
        pfad = os.path.join(PROTO, "plan_%s.json" % self.instanz)
        with open(pfad, "w", encoding="utf-8") as fh:
            json.dump({"statistik": dict(self.statistik), "blocker": self.blocker,
                       "hinweise": self.hinweise, "plan": self.plan}, fh,
                      ensure_ascii=False, default=str)
        print("  Protokoll:", pfad)

    # --------------------------------------------------------------- schreiben
    def schreibe(self):
        raise Blocker("Schreiblauf ist gesperrt: Modul Projekt ist noch nicht abgenommen. "
                      "Freigabe ueber --projekt-abgeschlossen erst nach Projekt-Abnahme.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    ap.add_argument("--projekt-abgeschlossen", action="store_true")
    ap.add_argument("--plan-schreiben", action="store_true")
    a = ap.parse_args()

    env = lade_env()
    if a.ausfuehren and not a.ich_habe_freigabe:
        print("STOPP: --ausfuehren nur zusammen mit --ich-habe-freigabe")
        return 2
    if a.ausfuehren and not a.projekt_abgeschlossen:
        print("STOPP: Migration gesperrt - Modul Projekt ist noch nicht abgenommen.")
        print("       Schreiben erst mit --projekt-abgeschlossen (nach Projekt-Abnahme).")
        return 3
    if a.ausfuehren and not env["ODOO18_DB"].endswith("odoo18_test"):
        print("STOPP: Ziel-DB ist nicht die Testdatenbank:", env["ODOO18_DB"])
        return 2

    m = Migration(a.instanz, a.ausfuehren)
    print("### Zeiterfassung-Migration, Instanz:", a.instanz,
          " Modus:", "SCHREIBEN" if a.ausfuehren else "Trockenlauf")
    m.lese_o11()
    m.lese_o18()
    m.baue_plan()
    m.plane_zeilen()
    m.bericht()
    if a.plan_schreiben:
        m.protokoll()
    if a.ausfuehren:
        m.schreibe()
    else:
        print("\nTrockenlauf - keine Aenderung geschrieben.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
