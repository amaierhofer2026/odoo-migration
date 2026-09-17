"""Abnahmepruefung Bereich Kundenverwaltung / CRM (Session 115).

Prueft READ-ONLY gegen eine Odoo-18-Instanz (lokal oder VM):
  1. Sichtbarer App-/Menue-Name "Kundenverwaltung" (Quelle, de_DE, en_US)
  2. Hauptmenues und Untermenues in der Odoo-11-Reihenfolge
  3. Konfigurationsgruppe "Interessenten und Chancen", Menue "Vertriebskanaele"
  4. Zugriffsgruppen am Wurzelmenue
  5. ITK-Felder: in Liste der Interessenten und im Formular, NICHT in der Liste der Verkaufschancen
  6. Stammdaten: 9 Stufen, 7 Teams, 5 Verlustgruende
  7. Keine Datenmigration (0 Verkaufschancen)

Aufruf:
    python scripts/verify_s115_kundenverwaltung.py --instanz lokal
    python scripts/verify_s115_kundenverwaltung.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_MENUE = "crm.crm_menu_root"
ERWARTETE_HAUPTMENUES = ["Aktivitäten", "Pipeline", "Kunden", "Berichtswesen", "Konfiguration"]
ERWARTETE_PIPELINE = ["Pipeline", "Interessenten", "Angebote", "Teams"]
KONFIG_GRUPPE = "crm.menu_crm_config_lead"
KONFIG_GRUPPE_NAME = "Interessenten und Chancen"
KONFIG_KINDER = ["Stichwörter", "Verlustgründe"]
VERTRIEBSKANAELE = "crm.crm_team_config"
ITK_FELDER = ["x_Anrede_Lead", "x_Lead_Quelle", "x_Produktinteresse", "x_lead_status"]
STUFEN = ["Neu", "Angebotsphase", "On-Hold", "Angebot ausgesendet", "Positive Rückmeldung",
          "Erfolgreich", "Verloren", "Zur Verrechnung bereit", "Verrechnet"]
TEAMS = ["Vertriebskanäle (Intern)", "Interne Weitergabe", "Persönlicher Kontakt", "Webinar",
         "Telefon", "Newsletter", "Website"]
TEAM_NICHT = "Suche / Liste"
VERLUSTGRUENDE = ["Too expensive", "Im Moment keinen Bedarf", "Bedarf zu gering",
                  "Später kontaktieren", "Mitbewerb"]
ERWARTETE_GRUPPEN_XMLIDS = ["sales_team.group_sale_manager", "sales_team.group_sale_salesman"]
VERSION = "18.0.1.5.4"


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

    def menue(xmlid: str):
        treffer = k.kw("ir.model.data", "search_read",
                       [[["module", "=", xmlid.split(".")[0]], ["name", "=", xmlid.split(".", 1)[1]]], ["res_id"]])
        if not treffer:
            return None
        mid = treffer[0]["res_id"]
        return k.kw("ir.ui.menu", "read", [[mid], ["name", "parent_id", "sequence", "groups_id"]])

    print("\n1) Sichtbare App-/Menue-Namen (Wortlaut wie Odoo 11)")
    wurzel = menue(APP_MENUE)
    if not wurzel:
        pruefe(False, "Wurzelmenue %s nicht gefunden" % APP_MENUE)
        wurzel_id = None
    else:
        wurzel_id = wurzel[0]["parent_id"] and wurzel[0].get("id")
        mid = wurzel[0].get("id")
        quelle = k.kw("ir.ui.menu", "read", [[mid], ["name"]])[0]["name"]
        deutsch = k.kw("ir.ui.menu", "read", [[mid], ["name"]], context={"lang": "de_DE"})[0]["name"]
        englisch = k.kw("ir.ui.menu", "read", [[mid], ["name"]], context={"lang": "en_US"})[0]["name"]
        pruefe(deutsch == "Kundenverwaltung", "App-Name de_DE = '%s' (erwartet 'Kundenverwaltung')" % deutsch)
        pruefe(englisch == "Kundenverwaltung", "App-Name en_US = '%s'" % englisch)
        pruefe(quelle == "Kundenverwaltung", "App-Name Quelle = '%s'" % quelle)
        wurzel_id = mid
        gruppen = k.kw("ir.ui.menu", "read", [[mid], ["groups_id"]])[0]["groups_id"]
        xmlids = []
        for gid in gruppen:
            daten = k.kw("ir.model.data", "search_read", [[["model", "=", "res.groups"], ["res_id", "=", gid]], ["module", "name"]])
            xmlids += ["%s.%s" % (d["module"], d["name"]) for d in daten]
        fehlend = [x for x in ERWARTETE_GRUPPEN_XMLIDS if x not in xmlids]
        pruefe(not fehlend, "Zugriffsgruppen am Wurzelmenue: %s" % (xmlids or gruppen))
    kg = menue(KONFIG_GRUPPE)
    if kg:
        kid = kg[0]["id"]
        name = k.kw("ir.ui.menu", "read", [[kid], ["name"]], context={"lang": "de_DE"})[0]["name"]
        pruefe(name == KONFIG_GRUPPE_NAME, "Konfigurationsgruppe = '%s' (erwartet '%s')" % (name, KONFIG_GRUPPE_NAME))
        kinder = [x["name"] for x in k.kw("ir.ui.menu", "search_read",
                                          [[["parent_id", "=", kid]], ["name"]], context={"lang": "de_DE"}, order="sequence")]
        pruefe(all(w in kinder for w in KONFIG_KINDER),
               "Untermenues: %s" % kinder)
    else:
        pruefe(False, "Konfigurationsgruppe %s fehlt" % KONFIG_GRUPPE)
    vk = menue(VERTRIEBSKANAELE)
    if vk:
        n = k.kw("ir.ui.menu", "read", [[vk[0]["id"]], ["name"]], context={"lang": "de_DE"})[0]["name"]
        pruefe(n == "Vertriebskanäle", "Konfigurationsmenue = '%s' (erwartet 'Vertriebskanäle')" % n)

    print("\n2) Hauptmenues und Untermenues in der Odoo-11-Reihenfolge")
    if wurzel_id:
        haupt = k.kw("ir.ui.menu", "search_read", [[["parent_id", "=", wurzel_id]], ["name", "sequence"]],
                     context={"lang": "de_DE"}, order="sequence,id")
        namen = [m["name"] for m in haupt]
        pruefe(namen == ERWARTETE_HAUPTMENUES, "Hauptmenues: %s" % namen)
        pipeline = [m for m in haupt if m["name"] == "Pipeline"]
        if pipeline:
            kinder = [x["name"] for x in k.kw("ir.ui.menu", "search_read",
                                              [[["parent_id", "=", pipeline[0]["id"]]], ["name"]],
                                              context={"lang": "de_DE"}, order="sequence")]
            pruefe(kinder == ERWARTETE_PIPELINE, "Untermenues Pipeline: %s" % kinder)

    print("\n3) ITK-Felder an denselben Stellen wie in Odoo 11")
    for xid, soll in [("itk_crm.crm_lead_list_interessenten_inherit", True),
                      ("itk_crm.crm_lead_form_interessenten_inherit", True)]:
        treffer = k.kw("ir.model.data", "search_read",
                       [[["module", "=", "itk_crm"], ["name", "=", xid.split(".", 1)[1]]], ["res_id"]])
        if not treffer:
            pruefe(False, "View %s fehlt" % xid)
            continue
        vid = treffer[0]["res_id"]
        db_arch = k.kw("ir.ui.view", "read", [[vid], ["arch_db"]], context={"lang": "de_DE"})[0]["arch_db"]
        drin = [f for f in ITK_FELDER if f in db_arch]
        pruefe(len(drin) == len(ITK_FELDER), "%s enthaelt alle vier ITK-Felder (%d)" % (xid, len(drin)))
    liste_opp = k.kw("ir.ui.view", "search_read",
                     [[["model", "=", "crm.lead"], ["type", "=", "list"], ["name", "=", "crm.lead.list.opportunity"]], ["arch_db"]],
                     context={"lang": "de_DE"})
    if liste_opp:
        arch = liste_opp[0]["arch_db"] or ""
        pruefe(not any(f in arch for f in ITK_FELDER),
               "Liste der Verkaufschancen ohne ITK-Felder (wie Odoo 11)")

    print("\n4) Stammdaten (Session 114 vorbereitet)")
    stufen = {s["name"]: s for s in k.kw("crm.stage", "search_read", [[], ["name", "sequence"]],
                                         context={"active_test": False}, order="sequence,id")}
    pruefe(all(s in stufen for s in STUFEN), "9 Stufen wie Odoo 11 (%d gefunden)" % len(stufen))
    pruefe("Angebot ausgesendet" in stufen, "Stufe 'Angebot ausgesendet' vorhanden")
    teams = {t["name"]: t for t in k.kw("crm.team", "search_read", [[], ["name", "active"]],
                                        context={"active_test": False})}
    fehlend = [t for t in TEAMS if t not in teams or not teams[t]["active"]]
    pruefe(not fehlend, "7 Vertriebsteams vorhanden und aktiv%s" % (" (fehlt: %s)" % fehlend if fehlend else ""))
    pruefe(TEAM_NICHT not in teams, "Team '%s' bewusst nicht angelegt" % TEAM_NICHT)
    gr = [g["name"] for g in k.kw("crm.lost.reason", "search_read", [[], ["name", "active"]], context={"active_test": False})]
    pruefe(all(v in gr for v in VERLUSTGRUENDE), "5 Verlustgruende vorhanden")

    print("\n5) Keine Datenmigration")
    opp = k.kw("crm.lead", "search_count", [[["type", "=", "opportunity"]]])
    leads = k.kw("crm.lead", "search_count", [[["type", "=", "lead"]]])
    pruefe(opp == 0, "Verkaufschancen: %d (erwartet 0, Odoo 11 hat 359)" % opp)
    pruefe(leads <= 1, "Interessenten: %d (Odoo 11 hat 6.608, nur Testdatensatz erlaubt)" % leads)

    print("\n6) Modulversion")
    version = k.kw("ir.module.module", "search_read", [[["name", "=", "itk_crm"]], ["installed_version"]])[0]["installed_version"]
    pruefe(version == VERSION, "itk_crm %s (erwartet %s)" % (version, VERSION))

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
