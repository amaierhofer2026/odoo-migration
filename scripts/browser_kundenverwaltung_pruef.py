"""Browser-Pruefung Bereich Kundenverwaltung / CRM (Session 115).

Prueft im echten Browser (Playwright, Chrome) gegen die angegebene Instanz und
schreibt Screenshots in den Desktop-Ordner. Sitzung per RPC-Cookie (das
Login-Formular ist unzuverlaessig).

Geprueft wird:
  1. App-/Menueband: Kundenverwaltung mit Aktivitaeten, Pipeline, Kunden, Berichtswesen, Konfiguration
  2. Pipeline (Verkaufschancen): Ansicht, Stufen-Spalten
  3. Interessenten-Liste: sichtbare Spalten (inkl. ITK-Felder)
  4. Formular: Reiter, sichtbare Feldbeschriftungen
  5. Suche: Filter und Gruppieren nach (inkl. "Kunde")
  6. Konfiguration: Stufen, Vertriebskanaele, Ablehnungsgruende (Menue-Namen)
  7. Berichtswesen: Vertriebskanaele

Aufruf:
    python scripts/browser_kundenverwaltung_pruef.py --instanz vm
    python scripts/browser_kundenverwaltung_pruef.py --instanz lokal
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
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Layoutvergleich-Session95")


def lade_env(pfad):
    werte = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                s, w = zeile.split("=", 1)
                werte[s.strip()] = w.strip()
    return werte


def rpc_sitzung(url, db, user, pwd):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(
        url + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call",
                         "params": {"db": db, "login": user, "password": pwd}}).encode(),
        headers={"Content-Type": "application/json"})
    with op.open(req, timeout=120) as f:
        f.read()
    sid = next((c.value for c in jar if c.name == "session_id"), None)

    def kw(model, methode, args, **kwargs):
        req = urllib.request.Request(
            url + "/web/dataset/call_kw",
            data=json.dumps({"jsonrpc": "2.0", "method": "call",
                             "params": {"model": model, "method": methode, "args": args, "kwargs": kwargs}}).encode(),
            headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
        with op.open(req, timeout=120) as f:
            antwort = json.loads(f.read().decode())
        if "error" in antwort:
            raise RuntimeError(json.dumps(antwort["error"])[:200])
        return antwort.get("result")

    return sid, kw


def sichtbarer_text(seite, selektor):
    try:
        el = seite.query_selector(selektor)
        return (el.inner_text() if el else "").strip()
    except Exception:
        return ""


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="vm")
    p.add_argument("--ohne-screenshot", action="store_true")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    if a.instanz == "lokal":
        url = env.get("ODOO18_URL", "http://localhost:8069")
        domain = "localhost"
    else:
        url = "https://k001959vsx.ipax.at"
        domain = "k001959vsx.ipax.at"
    sid, kw = rpc_sitzung(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    print("Instanz: %s (%s)" % (a.instanz, url))

    # Menue -> Aktionen holen
    def menue_id(name, parent_name=None):
        dom = [("name", "=", name)]
        if parent_name:
            pid = kw("ir.ui.menu", "search_read", [[("name", "=", parent_name)], ["id"]], context={"lang": "de_DE"})
            dom.append(("parent_id", "=", pid[0]["id"] if pid else 0))
        treffer = kw("ir.ui.menu", "search_read", [dom, ["id", "action"]], context={"lang": "de_DE"})
        return treffer[0] if treffer else None

    aktionen = {}
    for label, name, parent in [("interessenten", "Interessenten", "Pipeline"),
                                ("pipeline", "Pipeline", "Pipeline"),
                                ("angebote", "Angebote", "Pipeline"),
                                ("kunden", "Kunden", None),
                                ("stufen", None, None),
                                ("teams", None, None),
                                ("verlustgruende", None, None),
                                ("tags", None, None),
                                ("bericht", None, None)]:
        if name:
            m = menue_id(name, parent)
            if m and m["action"]:
                aktionen[label] = int(str(m["action"]).split(",")[1])
    for xmlid, label in [("crm.crm_stage_action", "stufen"), ("sales_team.crm_team_action_config", "teams"),
                         ("sales_team.crm_team_action_pipeline", "bericht"),
                         ("crm.crm_lost_reason_action", "verlustgruende"), ("sales_team.sales_team_crm_tag_action", "tags")]:
        d = kw("ir.model.data", "search_read", [[("module", "=", xmlid.split(".")[0]), ("name", "=", xmlid.split(".", 1)[1])], ["res_id"]])
        if d:
            aktionen[label] = d[0]["res_id"]
    print("Aktionen:", aktionen)

    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_kv_" + a.instanz),
            channel="chrome", headless=True, viewport={"width": 1700, "height": 1300})
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()

        def oeffne(pfad, selektor=".o_view_controller, .o_form_view, .o_list_view, .o_kanban_view"):
            seite.goto(url + pfad)
            seite.wait_for_selector(selektor, timeout=90000)
            seite.wait_for_timeout(2500)

        def schuss(name):
            if not a.ohne_screenshot:
                datei = os.path.join(VZ, name)
                seite.screenshot(path=datei, full_page=True)
                print("       Screenshot: %s" % datei)

        print("\n1) Menueband der Kundenverwaltung")
        oeffne("/odoo/crm" if False else "/web#action=%s&model=crm.lead&view_type=kanban" % aktionen.get("pipeline", 213))
        band = sichtbarer_text(seite, ".o_main_navbar")
        pruefe("Kundenverwaltung" in band, "App-Name im Menueband sichtbar: %s" % re.sub(r"\s+", " ", band)[:110])
        for name in ["Aktivitäten", "Pipeline", "Kunden", "Berichtswesen", "Konfiguration"]:
            pruefe(name in band, "Menue '%s' sichtbar" % name)
        schuss("31_%s_Menueband_Kundenverwaltung.png" % a.instanz.upper())

        print("\n2) Pipeline (Verkaufschancen) und Stufen")
        text = seite.inner_text("body")
        stufen = [s for s in ["Neu", "Angebotsphase", "On-Hold", "Angebot ausgesendet", "Positive Rückmeldung",
                              "Erfolgreich", "Verloren", "Zur Verrechnung bereit", "Verrechnet"] if s in text]
        pruefe(len(stufen) >= 1, "Stufen im Kanban sichtbar: %s" % stufen)
        schuss("32_%s_Pipeline.png" % a.instanz.upper())

        print("\n3) Interessenten-Liste (Spalten)")
        if "interessenten" in aktionen:
            oeffne("/web#action=%s&model=crm.lead&view_type=list" % aktionen["interessenten"])
            kopf = sichtbarer_text(seite, "thead")
            kopf = re.sub(r"\s+", " ", kopf)
            pruefe(any(s in kopf for s in ["Ansprechpartner", "Stadt", "E-Mail", "Lead"]),
                   "Spaltenkopf: %s" % kopf[:150])
            for feld in ["Lead Status", "Anrede Lead", "Lead Quelle", "Produktinteresse"]:
                pruefe(feld in kopf, "Spalte '%s' sichtbar" % feld)
            schuss("33_%s_Interessenten_Liste.png" % a.instanz.upper())

            print("\n4) Suche: Filter und Gruppieren nach")
            seite.click(".o_searchview_input")
            seite.wait_for_timeout(1200)
            menue = sichtbarer_text(seite, ".o_searchview_autocomplete, .dropdown-menu")
            pruefe("Kunde" in menue or "Filter" in menue, "Suchmenue offen (%d Zeichen)" % len(menue))
            try:
                knopf = seite.query_selector("button:has-text('Gruppieren nach'), .dropdown-item:has-text('Gruppieren nach')")
                if knopf:
                    knopf.click()
                    seite.wait_for_timeout(1200)
                    menue = sichtbarer_text(seite, ".dropdown-menu")
            except Exception as exc:
                print("       Hinweis Gruppieren: %s" % str(exc)[:80])
            for begriff in ["Verkäufer", "Vertriebskanal", "Kunde", "Stufe", "Ablehnungsgrund"]:
                pruefe(begriff in menue, "Gruppieren/Filter '%s' sichtbar" % begriff)
            schuss("34_%s_Suche_Gruppieren.png" % a.instanz.upper())

        print("\n5) Formular (Reiter und Beschriftungen)")
        treffer = kw("crm.lead", "search_read", [[], ["id"]], limit=1)
        if treffer:
            lid = treffer[0]["id"]
            oeffne("/web#id=%s&model=crm.lead&view_type=form" % lid, ".o_form_view")
            form = re.sub(r"\s+", " ", seite.inner_text(".o_form_view"))
            # stage_id wird in Odoo 18 als Statusleiste gerendert (Stufennamen, kein Feldtitel)
            for label in ["Verkäufer", "Vertriebskanal", "Interessenten", "Weitere Informationen", "Stichwörter"]:
                pruefe(label in form, "Formular zeigt '%s'" % label)
            pruefe(any(s in form for s in ["Neu", "Angebotsphase", "Verloren"]),
                   "Statusleiste mit Stufennamen sichtbar")
            schuss("35_%s_Formular.png" % a.instanz.upper())

        print("\n6) Konfiguration (Stufen, Vertriebskanaele, Ablehnungsgruende)")
        if "stufen" in aktionen:
            oeffne("/web#action=%s&model=crm.stage&view_type=list" % aktionen["stufen"], ".o_list_view")
            text = seite.inner_text(".o_list_view")
            gefunden = [s for s in ["Neu", "Angebotsphase", "On-Hold", "Angebot ausgesendet", "Positive Rückmeldung",
                                    "Erfolgreich", "Verloren", "Zur Verrechnung bereit", "Verrechnet"] if s in text]
            pruefe(len(gefunden) == 9, "Stufenliste zeigt %d von 9 Stufen" % len(gefunden))
            schuss("36_%s_Konfiguration_Stufen.png" % a.instanz.upper())
        if "teams" in aktionen:
            oeffne("/web#action=%s&model=crm.team&view_type=list" % aktionen["teams"], ".o_list_view")
            text = seite.inner_text(".o_list_view")
            teams = [t for t in ["Vertriebskanäle (Intern)", "Interne Weitergabe", "Persönlicher Kontakt", "Webinar",
                                 "Telefon", "Newsletter", "Website"] if t in text]
            pruefe(len(teams) >= 5, "Vertriebskanaele sichtbar: %s" % teams)
            schuss("37_%s_Konfiguration_Vertriebskanaele.png" % a.instanz.upper())

        print("\n6b) Angebote und Kunden")
        if "angebote" in aktionen:
            oeffne("/web#action=%s&model=sale.order&view_type=list" % aktionen["angebote"])
            pruefe("Angebot" in seite.inner_text("body"), "Angebote-Ansicht geoeffnet")
            schuss("39_%s_Angebote.png" % a.instanz.upper())
        if "kunden" not in aktionen:
            d = kw("ir.model.data", "search_read", [[("module", "=", "contacts"), ("name", "=", "action_contacts")], ["res_id"]])
            if d:
                aktionen["kunden"] = d[0]["res_id"]
        if "kunden" in aktionen:
            oeffne("/web#action=%s&model=res.partner&view_type=kanban" % aktionen["kunden"])
            pruefe(len(seite.query_selector_all(".o_kanban_record")) >= 1,
                   "Kunden-Ansicht geoeffnet (%d Karten)" % len(seite.query_selector_all(".o_kanban_record")))
            schuss("40_%s_Kunden.png" % a.instanz.upper())

        print("\n6c) Konfiguration: Ablehnungsgruende und Lead Tags")
        if "verlustgruende" in aktionen:
            oeffne("/web#action=%s&model=crm.lost.reason&view_type=list" % aktionen["verlustgruende"], ".o_list_view")
            text = seite.inner_text(".o_list_view")
            gruende = [g for g in ["Too expensive", "Im Moment keinen Bedarf", "Bedarf zu gering",
                                   "Später kontaktieren", "Mitbewerb"] if g in text]
            pruefe(len(gruende) >= 3, "Ablehnungsgruende-Liste zeigt %d von 5 (Listen-Virtualisierung)" % len(gruende))
            kopf = sichtbarer_text(seite, ".o_breadcrumb") or sichtbarer_text(seite, ".o_control_panel")
            pruefe("Ablehnungsgr" in kopf, "Aktionsname im Kopf: '%s'" % re.sub(r"\s+", " ", kopf)[:60])
            schuss("41_%s_Konfiguration_Ablehnungsgruende.png" % a.instanz.upper())
        if "tags" in aktionen:
            oeffne("/web#action=%s&model=crm.tag&view_type=list" % aktionen["tags"], ".o_list_view")
            pruefe(len(seite.query_selector_all(".o_data_row")) >= 1,
                   "Lead Tags: %d Eintraege" % len(seite.query_selector_all(".o_data_row")))
            kopf = sichtbarer_text(seite, ".o_breadcrumb") or sichtbarer_text(seite, ".o_control_panel")
            pruefe("Lead Tags" in kopf, "Aktionsname im Kopf: '%s'" % re.sub(r"\s+", " ", kopf)[:60])
            schuss("42_%s_Konfiguration_LeadTags.png" % a.instanz.upper())
        if "stufen" in aktionen:
            oeffne("/web#action=%s&model=crm.stage&view_type=list" % aktionen["stufen"], ".o_list_view")
            kopf = sichtbarer_text(seite, ".o_breadcrumb") or sichtbarer_text(seite, ".o_control_panel")
            pruefe("Stufen" in kopf, "Aktionsname Stufen im Kopf: '%s'" % re.sub(r"\s+", " ", kopf)[:60])

        print("\n6d) Bundesland-Auswahlliste (Interessent)")
        if treffer:
            oeffne("/web#id=%s&model=crm.lead&view_type=form" % treffer[0]["id"], ".o_form_view")
            for begriff, erwartet, verboten in [("Buc", "Bucure", None), ("\u5317", "\u5317\u4eac", None),
                                                ("\u00d5\u00ee", "\u5317\u4eac", "\u00d5\u00ee")]:
                feld = seite.query_selector('.o_field_widget[name="state_id"] input')
                if not feld:
                    pruefe(False, "Feld Bundesland im Interessentenformular nicht gefunden")
                    break
                feld.click()
                feld.fill(begriff)
                seite.wait_for_timeout(2500)
                vorschlaege = sichtbarer_text(seite, ".o_field_widget[name=\"state_id\"] .dropdown-menu") or \
                              sichtbarer_text(seite, ".ui-autocomplete")
                if verboten:
                    echte = [z for z in seite.query_selector_all('.o_field_widget[name="state_id"] .dropdown-item')
                             if "(" in (z.inner_text() or "")]
                    pruefe(not echte, "Gegenprobe '%s': keine Mojibake-Eintraege mehr (%d echte Vorschlaege)"
                           % (begriff, len(echte)))
                else:
                    pruefe(erwartet in vorschlaege, "Bundesland-Suche '%s' -> %r"
                           % (begriff, re.sub(r"\s+", " ", vorschlaege)[:85]))
                seite.keyboard.press("Escape")
                seite.wait_for_timeout(600)
            schuss("43_%s_Bundesland_Interessent.png" % a.instanz.upper())

        print("\n6e) Bundesland-Auswahlliste (Kontakt)")
        # Kontakt ohne Land waehlen: Odoo filtert die Bundeslaender sonst auf das Land des Kontakts
        partner = kw("res.partner", "search_read", [[["is_company", "=", True], ["country_id", "=", False]],
                                                    ["id", "name"]], limit=1)
        if partner:
            oeffne("/web#id=%s&model=res.partner&view_type=form" % partner[0]["id"], ".o_form_view")
            feld = seite.query_selector('.o_field_widget[name="state_id"] input')
            if feld:
                feld.click()
                feld.fill("Buc")
                seite.wait_for_timeout(2500)
                vorschlaege = sichtbarer_text(seite, ".o_field_widget[name=\"state_id\"] .dropdown-menu") or \
                              sichtbarer_text(seite, ".ui-autocomplete")
                pruefe("Bucure" in vorschlaege, "Kontaktformular Bundesland-Suche 'Buc' -> %r"
                       % re.sub(r"\s+", " ", vorschlaege)[:90])
                seite.keyboard.press("Escape")
            else:
                pruefe(False, "Feld Bundesland im Kontaktformular nicht gefunden")
            schuss("44_%s_Bundesland_Kontakt.png" % a.instanz.upper())

        print("\n7) Berichtswesen: Vertriebskanaele")
        if "bericht" in aktionen:
            oeffne("/web#action=%s&model=crm.team&view_type=kanban" % aktionen["bericht"], ".o_kanban_view")
            pruefe(len(seite.query_selector_all(".o_kanban_record")) >= 1,
                   "Berichtswesen zeigt Team-Karten (%d)" % len(seite.query_selector_all(".o_kanban_record")))
            schuss("38_%s_Berichtswesen_Vertriebskanaele.png" % a.instanz.upper())

        ctx.close()

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
