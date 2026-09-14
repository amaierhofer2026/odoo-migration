"""Verifiziert die zehn deutschen Repo-Punkte (Session 88) auf lokaler Instanz und VM.

Read-only: ausschliesslich search_read / fields_get / get_views.
Aufruf:  python scripts/verify_s88_de.py
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

# (Punkt, Beschreibung, Modell, Feld/Objekt, erwarteter deutscher Text)
FELDER = [
    ("2", "Vorname", "res.partner", "firstname", "Vorname"),
    ("2", "Nachname", "res.partner", "lastname", "Nachname"),
    ("3", "Einwohnerzahl", "res.partner", "population", "Einwohnerzahl"),
    ("4", "Aktualisierung Einwohnerzahl", "res.partner", "population_update",
     "Einwohnerzahl aktualisiert am"),
    ("5", "Peppol-Endpunkt", "res.partner", "peppol_endpoint", "Peppol-Endpunkt"),
    ("17", "Anzahl Duplikate", "helpdesk.ticket", "duplicate_count", "Anzahl Duplikate"),
    ("17", "Duplikat von", "helpdesk.ticket", "duplicate_id", "Duplikat von"),
    ("17", "Duplikat-Tickets", "helpdesk.ticket", "duplicate_ids", "Duplikat-Tickets"),
    ("17", "Duplikat-Erkennung", "helpdesk.ticket", "duplicate_tracking_enabled",
     "Duplikat-Erkennung aktivieren."),
]

MENUES = [
    ("18", "itk_translation.menu_itk_toplevel", "ITK-Menü"),
    ("19", "itk_helpdesk_compat.menu_helpdesk_config_sla", "SLAs"),
    ("20", "itk_helpdesk_compat.menu_helpdesk_config_team", "Helpdesk-Gruppen"),
]

BUTTONS = [
    ("1", "sale.subscription", "form", "Rechnung manuell erstellen"),
    ("6", "res.partner", "form", "Karte"),
    ("6", "res.partner", "form", "Routenplaner"),
    ("17", "helpdesk.ticket", "form", "Als Duplikat markieren"),
]


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
            raise RuntimeError(str(d["error"])[:200])
        return d["result"]

    call("/web/session/authenticate", {"db": ENV["ODOO18_DB"], "login": ENV["ODOO18_USER"],
                                       "password": ENV["ODOO18_PWD"]})

    def kw(model, method, args, context=None):
        return call("/web/dataset/call_kw", {"model": model, "method": method, "args": args,
                                             "kwargs": {"context": context} if context else {}})

    print("=" * 96)
    print("INSTANZ %s - %s" % (label.upper(), url))
    print("=" * 96)
    ok, fehler = 0, 0

    print("-- Feldbeschriftungen (de_DE) --")
    cache = {}
    for punkt, beschreibung, modell, feld, soll in FELDER:
        if modell not in cache:
            cache[modell] = kw(modell, "fields_get", [[], ["string"]], {"lang": "de_DE"})
        ist = cache[modell].get(feld, {}).get("string")
        gut = ist == soll
        ok, fehler = (ok + 1, fehler) if gut else (ok, fehler + 1)
        print("   %-4s %-26s %-28s -> %-32s %s"
              % (punkt, beschreibung, feld, ist, "OK" if gut else "FEHLER (soll %r)" % soll))

    print("-- Menuebezeichnungen (de_DE) --")
    for punkt, xmlid, soll in MENUES:
        modul, name = xmlid.split(".", 1)
        daten = kw("ir.model.data", "search_read",
                   [[["module", "=", modul], ["name", "=", name]], ["res_id"]])
        ist = None
        if daten:
            saetze = kw("ir.ui.menu", "search_read", [[["id", "=", daten[0]["res_id"]]], ["name"]],
                        {"lang": "de_DE"})
            ist = saetze[0]["name"] if saetze else None
        gut = ist == soll
        ok, fehler = (ok + 1, fehler) if gut else (ok, fehler + 1)
        print("   %-4s %-34s -> %-26s %s"
              % (punkt, xmlid, ist, "OK" if gut else "FEHLER (soll %r)" % soll))

    print("-- Buttons im Formular (de_DE) --")
    for punkt, modell, ansicht, soll in BUTTONS:
        arch = kw(modell, "get_views", [[[False, ansicht]]], {"lang": "de_DE"})["views"][ansicht]["arch"]
        texte = []
        for el in ET.fromstring(arch).iter():
            if el.tag == "button":
                t = (el.text or "").strip() or (el.get("string") or "").strip()
                if t:
                    texte.append(t)
        gut = soll in texte
        ok, fehler = (ok + 1, fehler) if gut else (ok, fehler + 1)
        print("   %-4s %-20s -> %-26s %s"
              % (punkt, modell, soll, "OK" if gut else "FEHLER (nicht gefunden)"))

    print("-- Kundenspezifische Bezeichnungen unveraendert --")
    # Achtung: 'Kundenverwaltung' ist der QUELLTEXT des CRM-Wurzelmenues (crm.crm_menu_root);
    # die deutsche Uebersetzung dieses Core-Menues lautet 'CRM'. Der kundenspezifische
    # Begriff muss also im Quelltext (en_US) und im jsonb erhalten bleiben.
    treffer = kw("ir.ui.menu", "search_read", [[["name", "ilike", "Kundenverwaltung"]], ["name"]],
                 {"lang": "en_US"})
    roh = kw("ir.ui.menu", "search_read", [[["id", "in", [m["id"] for m in treffer]]], ["name"]],
             {"lang": "en_US"})
    gut = len(treffer) >= 1
    ok, fehler = (ok + 1, fehler) if gut else (ok, fehler + 1)
    print("   'Kundenverwaltung' (Quelltext/en_US)  Treffer: %-3d %s"
          % (len(treffer), "OK" if gut else "FEHLER"))

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
