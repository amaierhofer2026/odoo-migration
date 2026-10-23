"""Datenmigration PROJEKT: Odoo 11 (Produktion, read-only) -> Odoo 18.

Standard ist der TROCKENLAUF (keine Schreibzugriffe). Schreiben nur mit
    --ausfuehren --ich-habe-freigabe

Reihenfolge: Stufen (project.task.type) -> Stichwoerter (project.tags) ->
Projekte (project.project) -> Aufgaben (project.task) -> Rechte der Projektgruppen.

Regeln (Anna):
  * Odoo 11 ausschliesslich lesen; Ziel nur die Testdatenbank (odo18_test).
  * Zuordnung ueber fachliche Schluessel (Name, Name+Projekt, Arbeits-E-Mail),
    nie ueber Datenbank-IDs; bei Mehrdeutigkeit Abbruch mit Klartext.
  * Historische/archivierte Datensaetze werden mit uebernommen (active=False).
  * Keine Zeiterfassungszeilen - die bleiben gesperrt.
  * Protokoll ausserhalb des Repos (%LOCALAPPDATA%\\Temp\\projekt_migration\\).
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
PROTO = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Temp", "projekt_migration")

# Odoo-11-kanban_state -> Odoo-18-state (Status der Aufgabe)
STATE_MAP = {"done": "1_done", "blocked": "04_waiting_normal", "normal": None}


class Blocker(Exception):
    pass


def norm(w):
    return " ".join((w or "").split()).lower()


class Migration:
    def __init__(self, instanz, schreiben):
        self.k11 = o11()
        self.k18 = o18(instanz)
        self.instanz = instanz
        self.schreiben = schreiben
        self.stat = Counter()
        self.blocker = []
        self.hinweise = []
        self.plan = {"stufen": [], "tags": [], "projekte": [], "aufgaben": []}
        self.map = {"stufen": {}, "tags": {}, "projekte": {}, "kalender": {}}

    # ------------------------------------------------------------------ lesen
    def lesen(self):
        k11, k18 = self.k11, self.k18
        self.st11 = k11.kw("project.task.type", "search_read", [[]],
                           fields=["id", "name", "sequence", "fold", "project_ids", "legend_priority"],
                           context={"active_test": False}, order="sequence,id", limit=0)
        self.tg11 = k11.kw("project.tags", "search_read", [[]], fields=["id", "name", "color"], limit=0)
        self.pr11 = k11.kw("project.project", "search_read", [[]],
                           fields=["id", "name", "partner_id", "user_id", "privacy_visibility",
                                   "label_tasks", "allow_timesheets", "active", "color",
                                   "description", "type_ids", "resource_calendar_id",
                                   "analytic_account_id"],
                           context={"active_test": False}, order="id", limit=0)
        self.au11 = k11.kw("project.task", "search_read", [[]],
                           fields=["id", "name", "project_id", "stage_id", "user_id", "active",
                                   "date_deadline", "planned_hours", "description", "date_start",
                                   "kanban_state", "priority", "tag_ids", "parent_id", "partner_id",
                                   "sequence"],
                           context={"active_test": False}, order="project_id,id", limit=0)
        self.st18 = k18.kw("project.task.type", "search_read", [[]],
                           fields=["id", "name", "project_ids"], context={"active_test": False}, limit=0)
        self.tg18 = k18.kw("project.tags", "search_read", [[]], fields=["id", "name"], limit=0)
        self.pr18 = k18.kw("project.project", "search_read", [[]],
                           fields=["id", "name", "active"], context={"active_test": False}, limit=0)
        self.au18 = k18.kw("project.task", "search_read", [[]],
                           fields=["id", "name", "project_id"], context={"active_test": False}, limit=0)
        self.ma11 = k11.kw("hr.employee", "search_read", [[]],
                           fields=["id", "name", "work_email", "user_id", "active"],
                           context={"active_test": False}, limit=0)
        self.ma18 = k18.kw("hr.employee", "search_read", [[]],
                           fields=["id", "name", "work_email", "user_id", "active"],
                           context={"active_test": False}, limit=0)
        self.us18 = k18.kw("res.users", "search_read", [[]], fields=["id", "login", "name"],
                           context={"active_test": False}, limit=0)
        uids = sorted({m["user_id"][0] for m in self.ma11 if m["user_id"]})
        self.users11 = {u["id"]: u for u in k11.kw("res.users", "read", [uids],
                                                  fields=["login", "name", "email"])} if uids else {}
        self.kal11 = k11.kw("resource.calendar", "search_read", [[]], fields=["id", "name"],
                            context={"active_test": False}, limit=0)
        f18 = k18.kw("resource.calendar", "fields_get", [], attributes=["string"])
        self.kal18 = k18.kw("resource.calendar", "search_read", [[]],
                            fields=[x for x in ("id", "name", "active") if x in f18],
                            context={"active_test": False}, limit=0)
        try:
            self.pa18 = k18.kw("res.partner", "search_read", [[("is_company", "=", True)]],
                               fields=["id", "name"], limit=0)
            self.pa18_ids = {x["id"] for x in self.pa18}
        except Exception:  # noqa: BLE001
            self.pa18 = []
            self.pa18_ids = set()
        print("  Odoo 11: %d Stufen, %d Tags, %d Projekte, %d Aufgaben, %d Kalender"
              % (len(self.st11), len(self.tg11), len(self.pr11), len(self.au11), len(self.kal11)))
        print("  Odoo 18: %d Stufen, %d Tags, %d Projekte, %d Aufgaben, %d Kalender"
              % (len(self.st18), len(self.tg18), len(self.pr18), len(self.au18), len(self.kal18)))

    def user_da(self, login):
        return any(norm(u["login"]) == norm(login) for u in self.us18)

    # --------------------------------------------------------------- planen
    def planen(self):
        # Kalender (Arbeitszeit) ueber Namen
        k18 = defaultdict(list)
        for x in self.kal18:
            k18[norm(x["name"])].append(x)
        for x in self.kal11:
            treffer = k18.get(norm(x["name"]), [])
            if len(treffer) > 1:
                self.blocker.append("Arbeitszeit '%s': %d gleichnamige in Odoo 18" % (x["name"], len(treffer)))
            elif treffer:
                self.map["kalender"][x["id"]] = treffer[0]["id"]

        # Projekt-Zuordnung zuerst (Stufen haengen daran)
        p18 = defaultdict(list)
        for x in self.pr18:
            p18[norm(x["name"])].append(x)
        for x in self.pr11:
            treffer = p18.get(norm(x["name"]), [])
            if len(treffer) > 1:
                self.blocker.append("Projekt '%s': %d gleichnamige in Odoo 18" % (x["name"], len(treffer)))
                continue
            partner = None
            if x["partner_id"]:
                pt = [y for y in self.pa18 if norm(y["name"]) == norm(x["partner_id"][1])]
                if len(pt) == 1:
                    partner = pt[0]["id"]
                elif not pt:
                    self.hinweise.append("Projekt '%s': Kunde '%s' fehlt in Odoo 18"
                                         % (x["name"], x["partner_id"][1]))
            self.plan["projekte"].append({
                "o11_id": x["id"], "o18_id": treffer[0]["id"] if treffer else None,
                "name": x["name"], "aktiv": x["active"], "kunde": partner,
                "manager11": x["user_id"][0] if x["user_id"] else None,
                "sichtbarkeit": x["privacy_visibility"], "label_tasks": x["label_tasks"],
                "farbe": x["color"], "kalender": self.map["kalender"].get(
                    x["resource_calendar_id"][0] if x["resource_calendar_id"] else None),
                "stufen11": x["type_ids"],
                "zeiterfassung": x["allow_timesheets"],
            })

        # Stufen: Name + Projektbezug; Odoo 18 fuehrt Stufen projektgebunden
        st18_key = defaultdict(list)
        for s in self.st18:
            for pid in (s["project_ids"] or [0]):
                st18_key[(norm(s["name"]), pid)].append(s)
        for s in self.st11:
            projekte11 = s["project_ids"] or []
            projekte18 = [self.plan["projekte"][i]["o18_id"] for i, p in enumerate(self.plan["projekte"])
                          if p["o11_id"] in projekte11]
            if len(projekte11) != len(projekte18):
                self.blocker.append("Stufe '%s': Projektbezug nicht vollstaendig zugeordnet" % s["name"])
                continue
            treffer = []
            for pid in (projekte18 or [0]):
                treffer.extend(st18_key.get((norm(s["name"]), pid), []))
            self.plan["stufen"].append({
                "o11_id": s["id"], "name": s["name"], "sequence": s["sequence"],
                "fold": s["fold"], "projekte11": projekte11, "projekte18": projekte18,
                "o18_id": treffer[0]["id"] if treffer else None,
            })

        # Tags ueber Namen
        t18 = defaultdict(list)
        for t in self.tg18:
            t18[norm(t["name"])].append(t)
        for t in self.tg11:
            treffer = t18.get(norm(t["name"]), [])
            self.plan["tags"].append({"o11_id": t["id"], "name": t["name"], "farbe": t["color"],
                                      "o18_id": treffer[0]["id"] if treffer else None})

        # Mitarbeiter -> Benutzer (fuer Projektmanager / Zugewiesen an)
        ma18_mail = {norm(m["work_email"]): m for m in self.ma18 if m["work_email"]}
        ma18_name = defaultdict(list)
        for m in self.ma18:
            ma18_name[norm(m["name"])].append(m)
        self.ma_map, self.user_map = {}, {}
        self.user_plan = []
        for m in self.ma11:
            ziel = ma18_mail.get(norm(m["work_email"]))
            if not ziel:
                treffer = ma18_name.get(norm(m["name"]), [])
                if len(treffer) == 1:
                    ziel = treffer[0]
            if not ziel:
                self.blocker.append("Mitarbeiter '%s' fehlt in Odoo 18" % m["name"])
                continue
            self.ma_map[m["id"]] = ziel["id"]
            if ziel["user_id"] and m["user_id"]:
                self.user_map[m["user_id"][0]] = ziel["user_id"][0]
            elif m["user_id"]:
                # Odoo-11-Benutzer vorhanden, in Odoo 18 fehlt das Konto:
                # als inaktiven Benutzer anlegen, damit die Zuweisung erhalten bleibt
                u11 = self.users11.get(m["user_id"][0])
                if u11 and not self.user_da(u11["login"]):
                    self.user_plan.append({"login": u11["login"], "name": u11["name"],
                                           "email": u11.get("email") or u11["login"],
                                           "mitarbeiter11": m["id"], "o11_user_id": m["user_id"][0],
                                           "o18_id": None})
                # Platzhalter: Konto wird beim Schreiben angelegt, Zuweisung bleibt erhalten
                self.user_map[m["user_id"][0]] = "NEU:%s" % u11["login"]

        # Aufgaben
        a18 = defaultdict(list)
        for a in self.au18:
            a18[(a["project_id"][0] if a["project_id"] else 0, norm(a["name"]))].append(a)
        projekt_map = {p["o11_id"]: p["o18_id"] for p in self.plan["projekte"]}
        stufen_map = {s["o11_id"]: s["o18_id"] for s in self.plan["stufen"]}
        for a in self.au11:
            pid11 = a["project_id"][0] if a["project_id"] else None
            if pid11 and pid11 not in projekt_map:
                self.blocker.append("Aufgabe '%s': Projekt nicht geplant" % a["name"])
                continue
            pid18 = projekt_map.get(pid11)
            treffer = a18.get((pid18 or 0, norm(a["name"])), [])
            user18 = self.user_map.get(a["user_id"][0]) if a["user_id"] else None
            if a["user_id"] and not user18:
                self.hinweise.append("Aufgabe '%s': Bearbeiter '%s' ohne Odoo-18-Benutzer"
                                     % (a["name"], a["user_id"][1]))
            stufe = stufen_map.get(a["stage_id"][0]) if a["stage_id"] else None
            self.plan["aufgaben"].append({
                "o11_id": a["id"], "name": a["name"], "o18_id": treffer[0]["id"] if treffer else None,
                "projekt11": pid11, "projekt18": pid18, "stufe11": a["stage_id"][0] if a["stage_id"] else None,
                "stufe18": stufe, "user18": user18, "aktiv": a["active"],
                "frist": a["date_deadline"], "geplant": a["planned_hours"],
                "start": a["date_start"], "kanban_state": a["kanban_state"],
                "beschreibung": a["description"], "tags11": a["tag_ids"],
                "partner": a["partner_id"][0] if a["partner_id"] else None,
                "sequence": a["sequence"],
            })

        self.stat["stufen_neu"] = sum(1 for s in self.plan["stufen"] if not s["o18_id"])
        self.stat["tags_neu"] = sum(1 for t in self.plan["tags"] if not t["o18_id"])
        self.stat["projekte_neu"] = sum(1 for p in self.plan["projekte"] if not p["o18_id"])
        self.stat["aufgaben_neu"] = sum(1 for a in self.plan["aufgaben"] if not a["o18_id"])
        self.stat["projekte"] = len(self.plan["projekte"])
        self.stat["projekte_archiviert"] = sum(1 for p in self.plan["projekte"] if not p["aktiv"])
        self.stat["aufgaben"] = len(self.plan["aufgaben"])
        self.stat["aufgaben_archiviert"] = sum(1 for p in self.plan["aufgaben"] if not p["aktiv"])
        self.stat["aufgaben_ohne_projekt"] = sum(1 for a in self.plan["aufgaben"] if not a["projekt11"])
        self.stat["aufgaben_mit_stufe11"] = sum(1 for a in self.plan["aufgaben"] if a["stufe11"])
        self.stat["benutzer_neu"] = len(self.user_plan)
        self.stat["aufgaben_mit_start"] = sum(1 for a in self.plan["aufgaben"] if a["start"])
        self.stat["aufgaben_mit_zeit"] = sum(1 for a in self.plan["aufgaben"] if a["geplant"])
        self.stat["aufgaben_mit_tags"] = sum(1 for a in self.plan["aufgaben"] if a["tags11"])
        self.stat["kanban_abnorm"] = sum(1 for a in self.plan["aufgaben"]
                                         if a["kanban_state"] in ("done", "blocked"))

    # --------------------------------------------------------------- bericht
    def bericht(self):
        print("\n=== Plan ===")
        for k in ("projekte", "projekte_archiviert", "projekte_neu", "aufgaben", "aufgaben_archiviert",
                  "aufgaben_neu", "aufgaben_ohne_projekt", "aufgaben_mit_stufe11", "aufgaben_mit_start",
                  "benutzer_neu",
                  "aufgaben_mit_zeit", "aufgaben_mit_tags", "stufen_neu", "tags_neu", "kanban_abnorm"):
            print("  %-24s %s" % (k, self.stat.get(k)))
        if self.user_plan:
            print("\n  Benutzer anzulegen (inaktiv): %d %s"
                  % (len(self.user_plan), [u["login"] for u in self.user_plan]))
        if self.hinweise:
            print("\n=== Hinweise (%d, erste 12) ===" % len(self.hinweise))
            for h in self.hinweise[:12]:
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
            json.dump({"statistik": dict(self.stat), "blocker": self.blocker,
                       "hinweise": self.hinweise, "plan": self.plan}, fh,
                      ensure_ascii=False, default=str)
        print("  Protokoll:", pfad)

    # -------------------------------------------------------------- schreiben
    def schreiben_lokal(self):
        if self.blocker:
            raise Blocker("Abbruch: %d Blocker offen" % len(self.blocker))
        k18 = self.k18
        # 0) fehlende Benutzerkonten (inaktiv) anlegen
        for u in self.user_plan:
            gid = k18.kw("ir.model.data", "search_read",
                         [[("module", "=", "base"), ("name", "=", "group_user")]],
                         fields=["res_id"], limit=1)
            # Odoo 18 verweigert das Anlegen mit active=False ("Aktion nicht fuer einen
            # archivierten Benutzer ausfuehrbar") -> aktiv anlegen, danach archivieren.
            vals = {"login": u["login"], "name": u["name"], "email": u["email"],
                    "share": False,
                    "groups_id": [(6, 0, [gid[0]["res_id"]])] if gid else []}
            try:
                neu = k18.kw("res.users", "create", [vals])
                neu_id = neu[0] if isinstance(neu, list) else neu
                k18.kw("res.users", "write", [[neu_id], {"active": False}])
                u["o18_id"] = neu_id
                self.stat["benutzer_angelegt"] += 1
                self.user_map[u["o11_user_id"]] = u["o18_id"]
            except Exception as exc:  # noqa: BLE001
                self.blocker.append("Benutzer '%s' nicht anlegbar: %s" % (u["login"], str(exc)[-200:]))
        if self.blocker:
            for b in self.blocker:
                print("   ! Benutzer:", b)
            raise Blocker("Benutzer konnten nicht angelegt werden - Abbruch vor Stammdaten")
        # 1) Stufen
        for s in self.plan["stufen"]:
            if s["o18_id"]:
                continue
            neu = k18.kw("project.task.type", "create", [{
                "name": s["name"], "sequence": s["sequence"], "fold": bool(s["fold"]),
                "project_ids": [(6, 0, [p for p in s["projekte18"] if p])],
            }])
            s["o18_id"] = neu[0] if isinstance(neu, list) else neu
            self.stat["stufen_angelegt"] += 1
        # 2) Tags
        for t in self.plan["tags"]:
            if t["o18_id"]:
                continue
            neu = k18.kw("project.tags", "create", [{"name": t["name"], "color": t["farbe"]}])
            t["o18_id"] = neu[0] if isinstance(neu, list) else neu
            self.stat["tags_angelegt"] += 1
        # 3) Projekte
        for p in self.plan["projekte"]:
            if p["o18_id"]:
                continue
            vals = {
                "name": p["name"],
                "privacy_visibility": p["sichtbarkeit"],
                "allow_timesheets": bool(p["zeiterfassung"]),
                "label_tasks": p["label_tasks"] or "Tasks",
                "color": p["farbe"] or 0,
            }
            if p["kunde"]:
                vals["partner_id"] = p["kunde"]
            if p["manager11"] and self.user_map.get(p["manager11"]):
                vals["user_id"] = self.user_map[p["manager11"]]
            if p["kalender"]:
                vals["resource_calendar_id"] = p["kalender"]
            if p["stufen11"]:
                stufen = [self.map_stufe(i) for i in p["stufen11"]]
                vals["type_ids"] = [(6, 0, [x for x in stufen if x])]
            neu = k18.kw("project.project", "create", [vals])
            p["o18_id"] = neu[0] if isinstance(neu, list) else neu
            self.stat["projekte_angelegt"] += 1
            if not p["aktiv"]:
                k18.kw("project.project", "write", [[p["o18_id"]], {"active": False}])
                self.stat["projekte_archiviert_gesetzt"] += 1
        # Projektzuordnung nach dem Anlegen neu aufbauen (o18_id ist jetzt bekannt)
        self.projekt_runtime = {p["o11_id"]: p["o18_id"] for p in self.plan["projekte"]}
        # 4) Aufgaben
        for a in self.plan["aufgaben"]:
            if a["o18_id"]:
                continue
            vals = {
                "name": a["name"],
                "project_id": self.projekt_runtime.get(a["projekt11"]) or False,
                "priority": "0",
                "sequence": a["sequence"] or 0,
            }
            if a["stufe18"]:
                vals["stage_id"] = a["stufe18"]
            if isinstance(a["user18"], int):
                vals["user_ids"] = [(6, 0, [a["user18"]])]
            if a["frist"]:
                vals["date_deadline"] = str(a["frist"])[:10] + " 00:00:00"
            if a["geplant"]:
                vals["allocated_hours"] = a["geplant"]
            if a["start"]:
                vals["itk_date_start"] = str(a["start"])[:10] + " 00:00:00"
            if a["beschreibung"]:
                vals["description"] = a["beschreibung"]
            if a["tags11"]:
                tags = [self.map_tag(i) for i in a["tags11"]]
                vals["tag_ids"] = [(6, 0, [x for x in tags if x])]
            if a["partner"] and a["partner"] in self.pa18_ids:
                vals["partner_id"] = a["partner"]
            ziel_state = STATE_MAP.get(a["kanban_state"])
            if ziel_state:
                vals["state"] = ziel_state
            neu = k18.kw("project.task", "create", [vals])
            a["o18_id"] = neu[0] if isinstance(neu, list) else neu
            self.stat["aufgaben_angelegt"] += 1
            if not a["aktiv"]:
                k18.kw("project.task", "write", [[a["o18_id"]], {"active": False}])
                self.stat["aufgaben_archiviert_gesetzt"] += 1
        print("  angelegt: %s" % dict((k, v) for k, v in self.stat.items() if k.endswith("_angelegt")))

    def map_stufe(self, o11_id):
        for s in self.plan["stufen"]:
            if s["o11_id"] == o11_id:
                return s["o18_id"]
        return None

    def map_tag(self, o11_id):
        for t in self.plan["tags"]:
            if t["o11_id"] == o11_id:
                return t["o18_id"]
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    ap.add_argument("--plan-schreiben", action="store_true")
    a = ap.parse_args()

    env = lade_env()
    if a.ausfuehren and not a.ich_habe_freigabe:
        print("STOPP: --ausfuehren nur zusammen mit --ich-habe-freigabe")
        return 2
    if a.ausfuehren and not env["ODOO18_DB"].endswith("odoo18_test"):
        print("STOPP: Ziel-DB ist nicht die Testdatenbank:", env["ODOO18_DB"])
        return 2

    m = Migration(a.instanz, a.ausfuehren)
    print("### Projekt-Migration, Instanz:", a.instanz,
          " Modus:", "SCHREIBEN" if a.ausfuehren else "Trockenlauf")
    m.lesen()
    m.planen()
    m.bericht()
    if a.plan_schreiben:
        m.protokoll()
    if a.ausfuehren:
        m.schreiben_lokal()
        m.protokoll()
    else:
        print("\nTrockenlauf - keine Aenderung geschrieben.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
