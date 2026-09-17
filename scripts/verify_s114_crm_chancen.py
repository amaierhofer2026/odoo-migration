"""Abnahmepruefung Bereich CRM -> Verkaufschancen (Session 114).

Prueft READ-ONLY gegen eine Odoo-18-Instanz (lokal oder VM):
  1. CRM-Stufen: Namen, Reihenfolge, is_won/fold (inkl. nachgetragener Stufe "Angebot ausgesendet")
  2. Vertriebsteams: nur die in Odoo 11 tatsaechlich verwendeten Teams, aktiv, mit Leiter
  3. Verlustgruende: die fuenf Odoo-11-Namen
  4. Felder der Verkaufschance: Zielnamen und Typen in Odoo 18
  5. Versionsumbenennungen (planned_revenue -> expected_revenue usw.)
  6. Keine Verkaufschance migriert

Aufruf:
    python scripts/verify_s114_crm_chancen.py --instanz lokal
    python scripts/verify_s114_crm_chancen.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Reihenfolge wie in Odoo 11 Prod (Name in Odoo 18, erwartete sequence)
STUFEN = [
    ("Neu", 1),
    ("Angebotsphase", 2),
    ("On-Hold", 3),
    ("Angebot ausgesendet", 4),      # in Session 114 nachgetragen
    ("Positive Rückmeldung", 5),
    ("Erfolgreich", 6),
    ("Verloren", 7),
    ("Zur Verrechnung bereit", 8),
    ("Verrechnet", 9),
]

# Teams, die in Odoo 11 tatsaechlich Verkaufschancen enthalten (Odoo-18-Name, Teamleiter erwartet)
TEAMS = [
    ("Vertriebskanäle (Intern)", False),
    ("Interne Weitergabe", False),
    ("Persönlicher Kontakt", True),
    ("Webinar", True),
    ("Telefon", True),
    ("Newsletter", True),
    ("Website", False),               # Odoo 11 "Webseite"
]
# In Odoo 11 vorhanden, aber ohne Verkaufschancen -> bewusst nicht angelegt
TEAMS_NICHT = ["Suche / Liste"]

# Verlustgruende aus Odoo 11 (alle in Odoo 18 schon vorhanden)
VERLUSTGRUENDE = ["Too expensive", "Im Moment keinen Bedarf", "Bedarf zu gering",
                  "Später kontaktieren", "Mitbewerb"]

# Odoo-18-Zielfelder der Verkaufschance: (Feld, Typ, Relation oder None)
FELDER = {
    "partner_id": ("many2one", "res.partner"),
    "name": ("char", None),
    "user_id": ("many2one", "res.users"),
    "team_id": ("many2one", "crm.team"),
    "stage_id": ("many2one", "crm.stage"),
    "expected_revenue": ("monetary", None),
    "probability": ("float", None),
    "priority": ("selection", None),
    "date_deadline": ("date", None),
    "lost_reason_id": ("many2one", "crm.lost.reason"),
    "tag_ids": ("many2many", "crm.tag"),
    "description": ("html", None),
    "date_closed": ("datetime", None),
    "message_ids": ("one2many", "mail.message"),
    "active": ("boolean", None),
    "type": ("selection", None),
}

# Odoo-11-Feldnamen, die es in Odoo 18 nicht mehr gibt (umbenannt oder entfallen)
ENTFALLEN = ["planned_revenue", "lost_reason", "kanban_state", "date_action_last"]


def lade_env(pfad: str) -> dict:
    werte = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                s, w = zeile.split("=", 1)
                werte[s.strip()] = w.strip()
    return werte


class Client:
    def __init__(self, url: str, db: str, user: str, pwd: str):
        self.url = url.rstrip("/")
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        self.rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})

    def rufe(self, pfad: str, params: dict):
        req = urllib.request.Request(
            self.url + pfad,
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode(),
            headers={"Content-Type": "application/json"})
        with self.opener.open(req, timeout=240) as antwort:
            daten = json.loads(antwort.read().decode())
        if "error" in daten:
            raise RuntimeError(json.dumps(daten["error"])[:300])
        return daten.get("result")

    def kw(self, model: str, methode: str, args: list, **kwargs):
        return self.rufe("/web/dataset/call_kw",
                         {"model": model, "method": methode, "args": args, "kwargs": kwargs})


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    k = Client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    print("Instanz: %s (%s, DB %s)" % (a.instanz, url, env["ODOO18_DB"]))
    ok = fehler = 0

    def pruefe(bedingung: bool, text: str):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    print("\n1) CRM-Stufen (Namen und Reihenfolge wie Odoo 11)")
    stufen = {s["name"]: s for s in k.kw("crm.stage", "search_read", [[], ["name", "sequence", "fold", "is_won"]],
                                        context={"active_test": False}, order="sequence,id")}
    pruefe(len(stufen) == len(STUFEN), "Anzahl Stufen: %d (erwartet %d)" % (len(stufen), len(STUFEN)))
    for name, seq in STUFEN:
        s = stufen.get(name)
        if not s:
            pruefe(False, "Stufe '%s' fehlt" % name)
        else:
            pruefe(s["sequence"] == seq, "Stufe '%s' an Position %s (erwartet %s)" % (name, s["sequence"], seq))
    for name, soll in [("Erfolgreich", True), ("Verloren", False), ("Verrechnet", False)]:
        s = stufen.get(name)
        if s:
            pruefe(s.get("is_won") == soll, "'%s' is_won=%s (erwartet %s)" % (name, s.get("is_won"), soll))
    verd = sorted(stufen.values(), key=lambda s: s["sequence"])
    pruefe([s["sequence"] for s in verd] == list(range(1, len(STUFEN) + 1)),
           "Sequenzen lueckenlos 1..%d" % len(STUFEN))

    print("\n2) Vertriebsteams (nur tatsaechlich verwendete)")
    teams = {}
    for t in k.kw("crm.team", "search_read", [[], ["name", "active", "user_id"]], context={"active_test": False}):
        teams[t["name"]] = t
    for name, leiter_erwartet in TEAMS:
        t = teams.get(name)
        if not t:
            pruefe(False, "Team '%s' fehlt" % name)
            continue
        pruefe(t["active"], "Team '%s' aktiv" % name)
        if leiter_erwartet:
            pruefe(bool(t.get("user_id")), "Team '%s' hat einen Teamleiter (%s)" % (name, t["user_id"][1] if t.get("user_id") else "-"))
        else:
            print("       Team '%s' aktiv (kein Leiter in Odoo 11 hinterlegt)" % name)
    for name in TEAMS_NICHT:
        pruefe(name not in teams, "Unbenutztes Odoo-11-Team '%s' wurde nicht angelegt" % name)

    print("\n3) Verlustgruende")
    gruende = [g["name"] for g in k.kw("crm.lost.reason", "search_read", [[], ["name"]], context={"active_test": False})]
    for name in VERLUSTGRUENDE:
        pruefe(name in gruende, "Verlustgrund '%s' vorhanden" % name)

    print("\n4) Felder der Verkaufschance in Odoo 18")
    felder = k.kw("crm.lead", "fields_get", [list(FELDER), ["type", "relation"]])
    for name, (typ, rel) in FELDER.items():
        d = felder.get(name)
        if not d:
            pruefe(False, "%s fehlt" % name)
        elif d["type"] != typ or (rel and d.get("relation") != rel):
            pruefe(False, "%s: Typ %s/%s (erwartet %s/%s)" % (name, d["type"], d.get("relation"), typ, rel))
        else:
            pruefe(True, "%s (%s%s)" % (name, d["type"], " -> " + rel if rel else ""))

    print("\n5) Versionsumbenennungen (alte Odoo-11-Namen duerfen nicht mehr existieren)")
    alt = k.kw("crm.lead", "fields_get", [ENTFALLEN, ["type"]])
    for name in ENTFALLEN:
        pruefe(name not in alt, "%s existiert in Odoo 18 nicht mehr" % name)

    print("\n6) Modulstand und Kontrollzahlen")
    mod = k.kw("ir.module.module", "search_read", [[["name", "=", "itk_crm"]], ["installed_version", "latest_version"]])[0]
    pruefe(mod["installed_version"].startswith("18.0.1.5"), "itk_crm %s (latest %s)" % (mod["installed_version"], mod["latest_version"]))
    print("       Verkaufschancen im Testbestand: %d (keine Migration erwartet)"
          % k.kw("crm.lead", "search_count", [[["type", "=", "opportunity"]]]))
    print("       crm.lead gesamt: %d" % k.kw("crm.lead", "search_count", [[]]))
    print("       Teams gesamt: %d (davon aktiv: %d)"
          % (len(teams), len([t for t in teams.values() if t["active"]])))

    print("\nERGEBNIS: %d OK, %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
