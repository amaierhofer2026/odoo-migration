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
KONFIG_KINDER = ["Lead Tags", "Ablehnungsgründe"]
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
VERSION = "18.0.1.5.7"


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

    print("\n7) Odoo-11-Bezeichnungen (nur Oberflaeche) und Gruppierung Kunde")
    LABELS = {"stage_id": "Stufe", "user_id": "Verkäufer", "team_id": "Vertriebskanal",
              "lost_reason_id": "Ablehnungsgrund", "date_deadline": "Erwartetes Abschlussdatum"}
    felder = k.kw("ir.model.fields", "search_read",
                  [[["model", "=", "crm.lead"], ["name", "in", list(LABELS)]], ["name", "field_description"]],
                  context={"lang": "de_DE"})
    ist = {f["name"]: f["field_description"] for f in felder}
    for feld, soll in LABELS.items():
        pruefe(ist.get(feld) == soll, "Label %s = '%s' (erwartet '%s')" % (feld, ist.get(feld), soll))
    MENUES = {"crm.menu_crm_lead_categ": "Lead Tags", "crm.menu_crm_lost_reason": "Ablehnungsgründe"}
    for xmlid, soll in MENUES.items():
        m = menue(xmlid)
        if m:
            name = k.kw("ir.ui.menu", "read", [[m[0]["id"]], ["name"]], context={"lang": "de_DE"})[0]["name"]
            pruefe(name == soll, "Menue %s = '%s' (erwartet '%s')" % (xmlid, name, soll))
        else:
            pruefe(False, "Menue %s fehlt" % xmlid)
    akt = k.kw("ir.model.data", "search_read", [[["module", "=", "crm"], ["name", "=", "crm_stage_action"]], ["res_id"]])
    if akt:
        an = k.kw("ir.actions.act_window", "read", [[akt[0]["res_id"]], ["name"]])[0]["name"]
        pruefe(an == "Stufen", "Aktion Phasen -> '%s' (erwartet 'Stufen')" % an)

    print("\n8) Menuepunkt Berichtswesen/Vertriebskanaele (wie Odoo 11)")
    rm = menue("itk_crm.menu_report_vertriebskanaele")
    if rm:
        mid = rm[0]["id"]
        name = k.kw("ir.ui.menu", "read", [[mid], ["name"]], context={"lang": "de_DE"})[0]["name"]
        eltern = k.kw("ir.ui.menu", "read", [[mid], ["parent_id"]])[0]["parent_id"]
        eltern_name = k.kw("ir.ui.menu", "read", [[eltern[0]], ["name"]], context={"lang": "de_DE"})[0]["name"] if eltern else ""
        pruefe(name == "Vertriebskanäle", "Menue heisst '%s'" % name)
        pruefe(eltern_name == "Berichtswesen", "haengt unter '%s'" % eltern_name)
    else:
        pruefe(False, "Menue Berichtswesen/Vertriebskanaele fehlt (Migration 18.0.1.5.5)")

    print("\n9) Gruppierung Kunde in beiden Suchansichten")
    for xid in ["crm.view_crm_case_opportunities_filter", "crm.view_crm_case_leads_filter"]:
        d = k.kw("ir.model.data", "search_read", [[["module", "=", xid.split(".")[0]], ["name", "=", xid.split(".", 1)[1]]], ["res_id"]])
        if not d:
            pruefe(False, "Suchansicht %s nicht gefunden" % xid)
            continue
        vid = d[0]["res_id"]
        kinder = k.kw("ir.ui.view", "search_read", [[["inherit_id", "=", vid], ["model", "=", "crm.lead"]], ["arch_db"]],
                      context={"lang": "de_DE"}, limit=20)
        arch = " ".join((v["arch_db"] or "") for v in kinder)
        pruefe("groupby_partner" in arch and "group_by" in arch.replace(" ", "") or "groupby_partner" in arch,
               "%s: Gruppierung Kunde ergaenzt" % xid)

    print("\n10) Berechtigungen (Loeschrecht aus Odoo 11, Gruppe Manager (edit))")
    regel = k.kw("ir.model.access", "search_read", [[["name", "=", "access_itk_crm_lead_manager"]],
                 ["group_id", "perm_read", "perm_write", "perm_create", "perm_unlink"]])
    if regel:
        r = regel[0]
        pruefe(r["perm_unlink"] == 1 and r["perm_read"] == 0 and r["perm_write"] == 0 and r["perm_create"] == 0,
               "Regel 'access_itk_crm_lead_manager': nur Loeschen (R%s W%s C%s D%s) fuer Gruppe '%s'"
               % (r["perm_read"], r["perm_write"], r["perm_create"], r["perm_unlink"],
                  r["group_id"][1] if r["group_id"] else "?"))
    else:
        pruefe(False, "Regel access_itk_crm_lead_manager fehlt")
    gruppe = k.kw("res.groups", "search_read", [[["name", "=", "Manager (edit)"]], ["name", "users", "implied_ids"]], context={"lang": "de_DE"})
    pruefe(bool(gruppe), "ITK-Gruppe 'Manager (edit)' vorhanden (Odoo-18-Gruppe, kein Nachbau)")
    if gruppe:
        benutzer = k.kw("res.users", "read", [gruppe[0]["users"], ["login"]]) if gruppe[0]["users"] else []
        pruefe(len(benutzer) <= 1, "der Gruppe sind noch keine Odoo-11-Benutzer zugeordnet (%s)" % [u["login"] for u in benutzer])

    print("\n11) Bundeslaender (res.country.state): beschaedigte Zeichen")
    import re as _re
    import unicodedata as _ud
    VERD = _re.compile("[\u2500-\u257f\u2580-\u259f\ufffd\u00a2\u00a3\u00a5\u00a9\u00ac\u00bb\u00bc\u00bd\u00d7]")
    MUSTER = ["\u00e2\u0080", "\u00c3\u201a", "\u00c2\u00a0", "\u00c3\u0192", "\u00e2\u20ac"]
    states = k.kw("res.country.state", "search_read", [[], ["id", "code", "name", "country_id"]],
                  context={"lang": "en_US"}, limit=4000)
    kaputt = [s for s in states
              if VERD.search(s["name"] or "") or any(m in (s["name"] or "") for m in MUSTER)
              or any(_ud.category(z) == "Cc" for z in (s["name"] or ""))]
    pruefe(not kaputt, "keine beschaedigten State-Namen (%d von %d geprueft)%s"
           % (len(states), len(states), "" if not kaputt else " - z. B. %r" % kaputt[0]["name"]))
    leer = [s for s in states if not (s["name"] or "").strip()]
    pruefe(not leer, "keine leeren State-Namen")
    kombis = {}
    for s in states:
        kombis.setdefault((s["country_id"][0] if s["country_id"] else 0, s["code"]), []).append(s["id"])
    dopp = {c: v for c, v in kombis.items() if len(v) > 1}
    pruefe(not dopp, "keine doppelten Land/Code-Kombinationen%s" % ("" if not dopp else " - %s" % list(dopp)[:3]))
    at = [s for s in states if s["country_id"] and s["country_id"][1] == "Austria"]
    AT_NAMEN = ["Burgenland", "Kärnten", "Niederösterreich", "Oberösterreich", "Salzburg",
                "Steiermark", "Tirol", "Vorarlberg", "Wien"]
    pruefe(len(at) == 9, "Oesterreich hat 9 Bundeslaender (%d)" % len(at))
    namen = sorted(s["name"] for s in at)
    pruefe(namen == sorted(AT_NAMEN), "Oesterreichs Bundeslaender namentlich korrekt: %s" % namen)
    at_id = k.kw("res.country", "search_read", [[["code", "=", "AT"]], ["id"]], context={"lang": "de_DE"})
    pruefe(bool(at_id), "Land Oesterreich (Code AT) vorhanden")
    gebraucht = k.kw("crm.lead", "search_count", [[["state_id", "!=", False]]])
    gebraucht_p = k.kw("res.partner", "search_count", [[["state_id", "!=", False]]])
    print("       (Kontrollzahl: crm.lead mit Bundesland %d, Kontakte mit Bundesland %d)" % (gebraucht, gebraucht_p))

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
