"""Verifiziert die Session-89-Punkte (10, 13, 15, 16, 22, 26 + Textkorrekturen) lokal und auf der VM.

Read-only: nur search_read / fields_get / get_views.
Aufruf:  python scripts/verify_s89_de.py
"""
import http.cookiejar
import json
import os
import urllib.request
import xml.etree.ElementTree as ET

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URLS = {"lokal": "http://localhost:8069", "vm": "https://k001959vsx.ipax.at"}


def lade_env():
    env = {}
    with open(os.path.join(BASIS, ".env"), encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                k, v = zeile.split("=", 1)
                env[k.strip()] = v.strip()
    return env


ENV = lade_env()

FELDER = [
    ("10", "Titel vorangestellt", "res.partner", "title_put_in_front", "Titel vorangestellt"),
    ("10", "Titel nachgestellt", "res.partner", "title_put_in_back", "Titel nachgestellt"),
    ("13", "Projekte", "res.partner", "project_ids", "Projekte"),
    ("13", "Aufgaben", "res.partner", "task_ids", "Aufgaben"),
    ("13", "Smart-Button Aufgaben", "res.partner", "task_count", "# Aufgaben"),
    ("15", "SLA-Frist", "helpdesk.ticket", "sla_deadline", "SLA-Frist"),
    ("15", "SLA erfuellt", "helpdesk.ticket", "sla_fits", "SLA erfüllt"),
    ("15", "Team-SLA", "helpdesk.ticket", "team_sla", "Team-SLA"),
    ("15", "Ticket-SLA", "helpdesk.ticket", "ticket_sla_ids", "Ticket-SLA"),
    ("15", "Gueltige SLAs", "helpdesk.ticket", "sla_ids", "Gültige SLAs"),
    ("16", "Zeiterfassung erlauben", "helpdesk.ticket", "allow_timesheet", "Zeiterfassung erlauben"),
    ("16", "Letzte Zeiterfassung", "helpdesk.ticket", "last_timesheet_activity", "Letzte Zeiterfassung"),
    ("16", "Geplante Stunden", "helpdesk.ticket", "planned_hours", "Geplante Stunden"),
    ("16", "Fortschritt", "helpdesk.ticket", "progress", "Fortschritt"),
    ("16", "Reststunden", "helpdesk.ticket", "remaining_hours", "Reststunden"),
    ("16", "Zeitsteuerung anzeigen", "helpdesk.ticket", "show_time_control", "Zeitsteuerung anzeigen"),
    ("16", "Zeiterfassung", "helpdesk.ticket", "timesheet_ids", "Zeiterfassung"),
    ("16", "Gesamtstunden", "helpdesk.ticket", "total_hours", "Gesamtstunden"),
]

# Bewusst NICHT geaenderte Begriffe (Gegenprobe: muessen englisch/identisch bleiben)
UNVERAENDERT = [
    ("Kontakte", "res.partner", "status_of_community", "Status of Community"),
    ("Kontakte", "res.partner", "member_of_city_alliance", "Member of City Alliance"),
    ("Kontakte", "res.partner", "asset_partner", "Asset Partner"),
    ("Kontakte", "res.partner", "community_magnitude", "Magnitude"),
    ("Kontakte", "res.partner", "reseller", "Reseller"),
]

BUTTONS = [
    ("15", "helpdesk.ticket", "form", "SLA setzen"),
    ("16", "helpdesk.ticket", "form", "Arbeit starten"),
    ("16", "helpdesk.ticket", "form", "Arbeit stoppen"),
    ("16", "helpdesk.ticket", "form", "Arbeit fortsetzen"),
    ("Korrektur", "sale.subscription", "form", "Erneuerungsangebot"),
    ("Korrektur", "sale.subscription", "form", "Abo-Auftrag abbrechen"),
    ("Korrektur", "sale.subscription", "form", "Abo-Auftrag schließen"),
]


def texte(arch, tag):
    out = []
    for el in ET.fromstring(arch).iter(tag):
        t = (el.text or "").strip() or (el.get("string") or "").strip()
        if t:
            out.append(t)
    return out


def pruefe(label, url):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def call(pfad, params):
        req = urllib.request.Request(url + pfad, data=json.dumps(
            {"jsonrpc": "2.0", "method": "call", "params": params}).encode(),
            headers={"Content-Type": "application/json"})
        with op.open(req, timeout=120) as r:
            d = json.loads(r.read().decode())
        if "error" in d:
            raise RuntimeError(str(d["error"])[:160])
        return d["result"]

    call("/web/session/authenticate", {"db": ENV["ODOO18_DB"], "login": ENV["ODOO18_USER"],
                                       "password": ENV["ODOO18_PWD"]})

    def kw(model, method, args, context=None):
        return call("/web/dataset/call_kw", {"model": model, "method": method, "args": args,
                                             "kwargs": {"context": context} if context else {}})

    print("=" * 100)
    print("INSTANZ %s - %s" % (label.upper(), url))
    print("=" * 100)
    ok = fehler = 0

    print("-- Feldbeschriftungen (de_DE) --")
    cache = {}
    for punkt, beschreibung, modell, feld, soll in FELDER:
        if modell not in cache:
            cache[modell] = kw(modell, "fields_get", [[], ["string"]], {"lang": "de_DE"})
        ist = cache[modell].get(feld, {}).get("string")
        gut = ist == soll
        ok, fehler = (ok + 1, fehler) if gut else (ok, fehler + 1)
        print("   %-9s %-26s %-26s -> %-28s %s"
              % (punkt, beschreibung, feld, ist, "OK" if gut else "FEHLER (soll %r)" % soll))

    print("-- Buttons / sichtbare Texte (de_DE) --")
    between = {}
    for punkt, modell, ansicht, soll in BUTTONS:
        if (modell, ansicht) not in between:
            between[(modell, ansicht)] = kw(modell, "get_views", [[[False, ansicht]]],
                                            {"lang": "de_DE"})["views"][ansicht]["arch"]
        gefunden = soll in between[(modell, ansicht)]
        ok, fehler = (ok + 1, fehler) if gefunden else (ok, fehler + 1)
        print("   %-9s %-20s -> %-30s %s"
              % (punkt, modell, soll, "OK" if gefunden else "FEHLER (nicht gefunden)"))

    print("-- Textkorrekturen (keine Altfehler mehr) --")
    abo = between[("sale.subscription", "form")]
    for falsch in ("Erneuerungsabgebot", "Aboauftrag"):
        gut = falsch not in abo
        ok, fehler = (ok + 1, fehler) if gut else (ok, fehler + 1)
        print("   %-28s -> %s" % ("kein %r mehr" % falsch, "OK" if gut else "FEHLER"))

    print("-- Kategorie (Punkt 26, Daten) --")
    neu = kw("helpdesk.ticket.category", "search_read", [[["name", "=", "Anonymisierungsportal"]], ["name"]],
             {"lang": "de_DE"})
    alt = kw("helpdesk.ticket.category", "search_count", [[["name", "like", "Anynom"]]], {"lang": "de_DE"})
    gut = len(neu) >= 1 and alt == 0
    ok, fehler = (ok + 1, fehler) if gut else (ok, fehler + 1)
    print("   'Anonymisierungsportal' gefunden: %d | alte Schreibweise: %d  %s"
          % (len(neu), alt, "OK" if gut else "FEHLER"))

    print("-- Gegenprobe: bewusst unveraenderte Begriffe --")
    for bereich, modell, feld, soll in UNVERAENDERT:
        if modell not in cache:
            cache[modell] = kw(modell, "fields_get", [[], ["string"]], {"lang": "de_DE"})
        ist = cache[modell].get(feld, {}).get("string")
        gut = ist == soll
        ok, fehler = (ok + 1, fehler) if gut else (ok, fehler + 1)
        print("   %-28s %-30s %s" % (beschreibung if False else feld, ist, "OK (unveraendert)" if gut else "FEHLER"))

    print("-- Gegenprobe: Punkt 22 (Helpdesk bleibt) und Punkt 14 (Team bleibt) --")
    menue = kw("ir.ui.menu", "search_read",
               [[["id", "=", kw("ir.model.data", "search_read",
                                [[["module", "=", "helpdesk_mgmt"], ["name", "=", "helpdesk_ticket_main_menu"]],
                                 ["res_id"]])[0]["res_id"]]], ["name"]], {"lang": "de_DE"})
    ist = menue[0]["name"] if menue else None
    gut = ist == "Helpdesk"
    ok, fehler = (ok + 1, fehler) if gut else (ok, fehler + 1)
    print("   Wurzelmenue Helpdesk            %-30s %s" % (ist, "OK (unveraendert)" if gut else "FEHLER"))
    team = cache["helpdesk.ticket"].get("team_id", {}).get("string")
    gut = team == "Team"
    ok, fehler = (ok + 1, fehler) if gut else (ok, fehler + 1)
    print("   Feld Team                       %-30s %s" % (team, "OK (unveraendert)" if gut else "FEHLER"))

    print("-- Kundenspezifische Bezeichnungen --")
    kv = kw("ir.ui.menu", "search_count", [[["name", "ilike", "Kundenverwaltung"]]], {"lang": "en_US"})
    ok, fehler = (ok + 1, fehler) if kv >= 1 else (ok, fehler + 1)
    print("   'Kundenverwaltung' (Quelltext)  Treffer: %-3d %s" % (kv, "OK" if kv >= 1 else "FEHLER"))

    print("\n   ERGEBNIS %s: %d OK, %d FEHLER\n" % (label.upper(), ok, fehler))
    return fehler


if __name__ == "__main__":
    gesamt = 0
    for label in ("lokal", "vm"):
        try:
            gesamt += pruefe(label, URLS[label])
        except Exception as ex:
            print("INSTANZ %s nicht erreichbar: %s\n" % (label.upper(), str(ex)[:150]))
            gesamt += 1
    print("Summe Fehler: %d" % gesamt)
