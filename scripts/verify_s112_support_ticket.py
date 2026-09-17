"""Abnahmepruefung Bereich Kontakte -> Kontaktformular -> Support Ticket (Session 112).

Prueft READ-ONLY gegen eine Odoo-18-Instanz (lokal oder VM):
  1. Sind die ticketrelevanten Felder auf res.partner vorhanden?
  2. Zeigt der gerenderte Arch des Reiters "Support Ticket" die Ticketliste mit den erwarteten Spalten?
  3. Steht der Smart-Button "Support Tickets" im Formular und oeffnet die Ticketliste?
  4. Reihenfolge der Reiter (Gemeinde-Information, dann Support Ticket)?
  5. Sind Ticket-Stufen, Kategorien und Teams vorhanden?

Aufruf:
    python scripts/verify_s112_support_ticket.py --instanz lokal
    python scripts/verify_s112_support_ticket.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Feld -> (Typ, Relation)
FELDER = {
    "helpdesk_ticket_ids": ("one2many", "helpdesk.ticket"),
    "helpdesk_ticket_count": ("integer", None),
    "helpdesk_ticket_active_count": ("integer", None),
    "helpdesk_ticket_count_string": ("char", None),
}

# Spalten, die der Reiter zeigen soll (Feld -> Beschriftung)
SPALTEN = {
    "number": "Ticketnummer",
    "name": "Titel",
    "create_date": "Erstellt am",
    "stage_id": "Stufe",
    "team_id": "Team",
    "category_id": "Kategorie",
    "user_id": "Zugewiesener Benutzer",
}

# Felder, die es in Odoo 11 gab und in Odoo 18 bewusst nicht mehr gibt
ENTFALLEN = ["sla_id", "stp_ids"]

REITER_FOLGE_ENDE = ["Gemeinde-Information", "Support Ticket"]


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

    print("\n1) Felder in Odoo 18")
    felder = k.kw("res.partner", "fields_get", [list(FELDER), ["type", "relation"]])
    for name, (typ, rel) in FELDER.items():
        d = felder.get(name)
        if not d:
            pruefe(False, "%s fehlt" % name)
        elif d["type"] != typ or (rel and d.get("relation") != rel):
            pruefe(False, "%s: Typ %s/%s (erwartet %s/%s)" % (name, d["type"], d.get("relation"), typ, rel))
        else:
            pruefe(True, "%s (%s%s)" % (name, d["type"], " -> " + rel if rel else ""))

    print("\n2) Entfallene Odoo-11-Felder (website_support)")
    alt = k.kw("res.partner", "fields_get", [ENTFALLEN, ["type"]])
    for name in ENTFALLEN:
        pruefe(name not in alt, "%s existiert in Odoo 18 nicht mehr (Odoo 11: 0 Kontakte mit Wert)" % name)

    print("\n3) Gerenderter Arch des Reiters 'Support Ticket'")
    arch = k.kw("res.partner", "get_views", [[[False, "form"]]], context={"lang": "de_DE"})["views"]["form"]["arch"]
    i = arch.find('name="support_ticket"')
    pruefe(i > 0, "Reiter 'support_ticket' im Arch gefunden")
    j = arch.find("<page", i + 10)
    seg = arch[i:(j if j > 0 else i + 3000)]
    pruefe('name="helpdesk_ticket_ids"' in seg, "Ticketliste (helpdesk_ticket_ids) im Reiter")
    for feld, beschriftung in SPALTEN.items():
        m = re.search(r'<field\b[^>]*name="%s"[^>]*/?>' % feld, seg)
        pruefe(bool(m), "Spalte %s im Reiter" % feld)
        if m:
            pruefe('string="%s"' % beschriftung in m.group(0), "%s mit Beschriftung '%s'" % (feld, beschriftung))
    pruefe("readonly=\"1\"" in seg, "Reiterliste ist nur lesend")
    pruefe("Platzhalter" not in seg and "werden hier angezeigt" not in seg, "kein Platzhaltertext mehr im Reiter")

    print("\n4) Smart-Button und Reiter-Reihenfolge")
    m = re.search(r'<button\b[^>]*action_view_helpdesk_tickets[^>]*>.*?</button>', arch, re.S)
    pruefe(bool(m), "Smart-Button action_view_helpdesk_tickets vorhanden")
    if m:
        pruefe('string="Support Tickets"' in m.group(0), "Button-Beschriftung 'Support Tickets' (wie Odoo 11)")
    folge = [t for t in re.findall(r'<page\b[^>]*string="([^"]+)"', arch)]
    print("       Reiterfolge: %s" % folge)
    for name in REITER_FOLGE_ENDE:
        pruefe(name in folge, "Reiter '%s' vorhanden" % name)
    if all(n in folge for n in REITER_FOLGE_ENDE):
        pruefe(folge.index("Gemeinde-Information") < folge.index("Support Ticket"),
               "Support Ticket steht nach Gemeinde-Information")

    print("\n5) Ticket-Stammdaten in Odoo 18")
    for modell, mindest, label in [("helpdesk.ticket.stage", 6, "Stufen"),
                                   ("helpdesk.ticket.category", 1, "Kategorien"),
                                   ("helpdesk.ticket.team", 1, "Teams")]:
        n = k.kw(modell, "search_count", [[]])
        pruefe(n >= mindest, "%s: %d (mindestens %d erwartet)" % (label, n, mindest))
    stufen = [s["name"] for s in k.kw("helpdesk.ticket.stage", "search_read", [[], ["name"]], order="sequence")]
    print("       Odoo-18-Stufen: %s" % stufen)
    erwartet = ["in Bearbeitung", "on Hold", "Geschlossen/Behoben"]
    for s in erwartet:
        pruefe(any(s.lower() in x.lower() for x in stufen), "Stufe '%s' (wie Odoo-11-Status) vorhanden" % s)

    print("\n6) Kontrollzahlen")
    print("       Kontakte gesamt: %d" % k.kw("res.partner", "search_count", [[]]))
    print("       Tickets im Testbestand: %d" % k.kw("helpdesk.ticket", "search_count", [[]]))
    print("       Kontakte mit Tickets: %d (Testbestand)" % k.kw("res.partner", "search_count", [[["helpdesk_ticket_ids", "!=", False]]]))

    print("\nERGEBNIS: %d OK, %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
