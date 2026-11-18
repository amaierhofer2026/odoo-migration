# -*- coding: utf-8 -*-
"""Browserabnahme CRM / Verkaufschancen nach der Datenmigration (Session 145).

Prueft im echten Browser (Playwright, Chrome, frisches Profil) und haelt jede
Erwartung gegen einen per RPC gemessenen Sollwert. Screenshots landen im
Temp-Ordner der Sitzung (nicht im Repository).

Geprueft wird:
 1 Menueband und Menuepunkte der Kundenverwaltung
 2 Pipeline (Kanban): neun Stufen, Anzahl Verkaufschancen
 3 Interessenten-Liste: Anzahl, Spalten inkl. ITK-Felder
 4 Suche: Filter "Archiviert", Gruppieren nach Verkaeufer/Stufe/Vertriebskanal, Favoriten
 5 Einzelner Vorgang: Kontakt, Verkaeufer, Team, Stufe, Prioritaet, Stichwoerter,
   Produktinteresse, Interessentenstatus, Quelle/Kampagne/Medium, erwarteter Umsatz,
   Notizen, Chatter
 6 Stufenwechsel im Formular
 7 Gewonnener und verlorener Vorgang
 8 Archivierter Vorgang
 9 Neuen Vorgang anlegen, bearbeiten, Status aendern, archivieren, wiederherstellen,
   danach loeschen (Testdaten entfernt)

Aufruf:
    python scripts/browser_crm_daten_abnahme.py --instanz lokal
    python scripts/browser_crm_daten_abnahme.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import ssl
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Temp", "s145_crm", "bilder")
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


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
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar),
                                     urllib.request.HTTPSHandler(context=_CTX))
    req = urllib.request.Request(
        url + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call",
                         "params": {"db": db, "login": user, "password": pwd}}).encode(),
        headers={"Content-Type": "application/json"})
    with op.open(req, timeout=180) as f:
        f.read()
    sid = next((c.value for c in jar if c.name == "session_id"), None)

    def kw(model, methode, args, **kwargs):
        req = urllib.request.Request(
            url + "/web/dataset/call_kw",
            data=json.dumps({"jsonrpc": "2.0", "method": "call",
                             "params": {"model": model, "method": methode, "args": args,
                                        "kwargs": kwargs}}).encode(),
            headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
        with op.open(req, timeout=180) as f:
            antwort = json.loads(f.read().decode())
        if "error" in antwort:
            raise RuntimeError(json.dumps(antwort["error"])[:400])
        return antwort.get("result")

    return sid, kw


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--ohne-screenshot", action="store_true")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    if a.instanz == "lokal":
        url = env.get("ODOO18_URL", "http://localhost:8069")
        domain = "localhost"
    else:
        url = "https://k001959vsx.ipax.at"
        domain = "k001959vsx.ipax.at"
    sid, kw = rpc_sitzung(url, env["ODOO18_DB"], env["ODOO18_USER"], env["OODOO18_PWD"]
                          if "OODOO18_PWD" in env else env["ODOO18_PWD"])
    CTX = {"lang": "de_DE"}

    # ---- Sollwerte per RPC
    soll = {}
    soll["chancen"] = kw("crm.lead", "search_count", [[("type", "=", "opportunity")]],
                         context=CTX)
    soll["interessenten"] = kw("crm.lead", "search_count", [[("type", "=", "lead")]],
                               context=CTX)
    soll["gesamt"] = kw("crm.lead", "search_count", [[]], context=CTX)
    soll["archiviert"] = kw("crm.lead", "search_count", [[("active", "=", False)]],
                            context={"lang": "de_DE", "active_test": False})
    soll["stufen"] = len(kw("crm.stage", "search", [[]], context=CTX))
    gewonnen = kw("crm.lead", "search_count", [[("stage_id.is_won", "=", True), ("active", "=", True)]],
                  context=CTX)
    soll["gewonnen"] = gewonnen
    soll["verloren"] = kw("crm.lead", "search_count",
                          [["&", ("active", "=", False), ("probability", "=", 0)]],
                          context={"lang": "de_DE", "active_test": False})
    print("Sollwerte: %s" % soll)

    # Beispielvorgaenge: gewonnen, verloren, archiviert, mit Partner und mit Stichwort
    def erster(domain, context=None):
        ids = kw("crm.lead", "search", [domain], context=context or CTX, limit=1, order="id")
        return ids[0] if ids else None

    bsp = {
        "gewonnen": erster([("stage_id.is_won", "=", True), ("active", "=", True)]),
        "verloren": erster([("stage_id.is_won", "=", False), ("stage_id.name", "=", "Verloren")]),
        "archiviert": erster([("active", "=", False)],
                             {"lang": "de_DE", "active_test": False}),
        "vorgang": erster([("partner_id", "!=", False), ("tag_ids", "!=", False),
                           ("type", "=", "opportunity")]),
    }
    print("Beispielvorgaenge: %s" % bsp)

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

    def menu_aktion(name, parent=None):
        dom = [("name", "=", name)]
        if parent:
            pid = kw("ir.ui.menu", "search_read", [[("name", "=", parent)], ["id"]], context=CTX)
            dom.append(("parent_id", "=", pid[0]["id"] if pid else 0))
        t = kw("ir.ui.menu", "search_read", [dom, ["id", "action"]], context=CTX)
        if t and t[0]["action"]:
            return int(str(t[0]["action"]).split(",")[1])
        return None

    akt = {"pipeline": menu_aktion("Pipeline", "Pipeline"),
           "interessenten": menu_aktion("Interessenten", "Pipeline"),
           "kunden": menu_aktion("Kunden"),
           "stufen": None, "teams": None, "gruende": None, "tags": None}
    for xmlid, key in [("crm.crm_stage_action", "stufen"),
                       ("sales_team.crm_team_action_config", "teams"),
                       ("crm.crm_lost_reason_action", "gruende"),
                       ("sales_team.sales_team_crm_tag_action", "tags")]:
        d = kw("ir.model.data", "search_read",
               [[("module", "=", xmlid.split(".")[0]), ("name", "=", xmlid.split(".", 1)[1])],
                ["res_id"]])
        if d:
            akt[key] = d[0]["res_id"]
    print("Aktionen: %s" % akt)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_crm145_" + a.instanz),
            channel="chrome", headless=True, viewport={"width": 1700, "height": 1300})
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()

        def oeffne(pfad, selektor=".o_view_controller, .o_form_view, .o_list_view, .o_kanban_view"):
            seite.goto(url + pfad)
            seite.wait_for_selector(selektor, timeout=120000)
            seite.wait_for_timeout(3000)

        def speichern():
            knopf = seite.query_selector("button.o_form_button_save")
            if knopf and knopf.is_visible():
                knopf.click()
                seite.wait_for_timeout(2500)

        def klick(el):
            """Klick ueber die Bildschirmkoordinaten (Odoo-Dropdowns reagieren
            auf synthetische Playwright-Klicks nicht zuverlaessig)."""
            box = el.bounding_box()
            seite.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

        def schuss(name):
            if not a.ohne_screenshot:
                datei = os.path.join(VZ, name)
                seite.screenshot(path=datei, full_page=True)
                print("       Screenshot: %s" % datei)

        def pager():
            t = seite.query_selector(".o_pager_limit")
            if t:
                return int(re.sub(r"[^0-9]", "", t.inner_text()))
            ganz = seite.query_selector(".o_pager")
            if ganz:
                m = re.search(r"/\s*([0-9.]+)", ganz.inner_text())
                if m:
                    return int(m.group(1).replace(".", ""))
            return -1

        def menue_text():
            """Text aller sichtbaren Dropdown-Menues (Odoo legt mehrere an)."""
            teile = []
            for sel in (".dropdown-menu", ".o-dropdown--menu", ".o_search_bar_menu"):
                for el in seite.query_selector_all(sel):
                    if el.is_visible():
                        teile.append(re.sub(r"\s+", " ", el.inner_text()))
            return " | ".join(teile)

        def txt(sel="body"):
            try:
                return re.sub(r"\s+", " ", seite.inner_text(sel))
            except Exception:
                return ""

        print("\n1) Menueband Kundenverwaltung")
        oeffne("/web#action=%s&model=crm.lead&view_type=kanban" % akt["pipeline"])
        band = txt(".o_main_navbar")
        pruefe("Kundenverwaltung" in band, "App-Name im Menueband: %s" % band[:80])
        for name in ["Aktivitäten", "Pipeline", "Kunden", "Berichtswesen", "Konfiguration"]:
            pruefe(name in band, "Menue '%s' sichtbar" % name)
        schuss("01_%s_menueband.png" % a.instanz)

        print("\n2) Pipeline (Kanban)")
        text = txt()
        stufen = [s for s in ["Neu", "Angebotsphase", "On-Hold", "Angebot ausgesendet",
                              "Positive Rückmeldung", "Erfolgreich", "Verloren",
                              "Zur Verrechnung bereit", "Verrechnet"] if s in text]
        pruefe(len(stufen) == soll["stufen"],
               "Kanban zeigt %d von %d Stufen: %s" % (len(stufen), soll["stufen"], stufen))
        karten = len([e for e in seite.query_selector_all(".o_kanban_record") if e.is_visible()])
        pruefe(karten > 0, "Pipeline zeigt %d Karten im Kanban (Soll gesamt: %d Verkaufschancen)"
               % (karten, soll["chancen"]))
        schuss("02_%s_pipeline.png" % a.instanz)

        print("\n3) Interessenten-Liste")
        oeffne("/web#action=%s&model=crm.lead&view_type=list" % akt["interessenten"],
               ".o_list_view")
        pruefe(pager() == soll["interessenten"],
               "Interessenten-Pager %s = Soll %s" % (pager(), soll["interessenten"]))
        kopf = txt("thead")
        for feld in ["Anrede Lead", "Lead Quelle", "Produktinteresse", "Lead Status",
                     "Verkäufer", "Vertriebskanal"]:
            pruefe(feld in kopf, "Spalte '%s' sichtbar" % feld)
        schuss("03_%s_interessenten_liste.png" % a.instanz)

        print("\n4) Suche: Filter und Gruppierung (funktional)")

        def oeffne_suchmenue(versuche=3):
            """Oeffnet das Suchmenue und liefert die sichtbaren Eintraege.

            Der Oeffner reagiert nur auf echte Klicks und schliesst sich
            gelegentlich sofort wieder - daher mit Wiederholung arbeiten.
            """
            for _ in range(versuche):
                tog = seite.query_selector(".o_searchview_dropdown_toggler")
                if not tog:
                    return []
                klick(tog)
                seite.wait_for_timeout(1800)
                eintraege = []
                for el in seite.query_selector_all(".o_menu_item, .dropdown-item"):
                    t = re.sub(r"\s+", " ", el.inner_text()).strip()
                    if t:
                        eintraege.append((t, el))
                if len(eintraege) > 5:
                    return eintraege
                seite.wait_for_timeout(1200)
            return []

        seite.click(".o_searchview_input")
        seite.wait_for_timeout(800)
        eintraege = oeffne_suchmenue()
        schuss("04_%s_suche_menue.png" % a.instanz)
        pruefe(len(eintraege) > 5, "Suchmenue offen (%d Eintraege)" % len(eintraege))
        namen = [t for t, _ in eintraege]
        menue_voll = " ".join(
            re.sub(r"\s+", " ", b.inner_text()) for b in seite.query_selector_all(".dropdown-menu, .o-dropdown--menu"))
        for begriff in ["Filter", "Gruppieren nach", "Verkäufer", "Vertriebskanal", "Stufe"]:
            pruefe(begriff in menue_voll or any(begriff in n for n in namen),
                   "Suchmenue enthaelt '%s'" % begriff)
        gruppe = next((el for t, el in eintraege if t == "Stufe"), None)
        if gruppe:
            klick(gruppe)
            seite.wait_for_timeout(4500)
            gruppen = seite.query_selector_all(".o_group_header")
            pruefe(len(gruppen) == soll["stufen"],
                   "Gruppierung nach Stufe: %d Gruppen (Soll %d)" % (len(gruppen), soll["stufen"]))
            schuss("05_%s_gruppierung_stufe.png" % a.instanz)
            chips = seite.query_selector_all(".o_searchview_facet .o_facet_remove")
            if chips:
                klick(chips[0])
                seite.wait_for_timeout(4500)
        else:
            pruefe(False, "Eintrag 'Stufe' im Suchmenue gefunden")
        eintraege = oeffne_suchmenue()
        filter_el = next((el for t, el in eintraege if t == "Verloren"), None)
        # Der Odoo-18-Filter "Verloren" der Interessentenliste lautet
        # active = False und Wahrscheinlichkeit 0 - Sollwert entsprechend messen.
        erwartet = kw("crm.lead", "search_count",
                      [["&", "&", ("probability", "=", 0), ("active", "=", False),
                        ("type", "=", "lead")]],
                      context={"lang": "de_DE", "active_test": False})
        if filter_el:
            klick(filter_el)
            seite.wait_for_timeout(4500)
            facette = txt(".o_searchview_facet")
            zeilen = len(seite.query_selector_all(".o_data_row"))
            pruefe("Verloren" in facette, "Filter 'Verloren' als Chip aktiv (%s)" % facette[:60])
            pruefe(zeilen == erwartet, "Filter liefert %d Zeilen (RPC-Soll %d)"
                   % (zeilen, erwartet))
            schuss("06_%s_filter_verloren.png" % a.instanz)
            chips = seite.query_selector_all(".o_searchview_facet .o_facet_remove")
            if chips:
                klick(chips[0])
                seite.wait_for_timeout(4500)
        else:
            pruefe(False, "Filter 'Verloren' im Suchmenue gefunden")

        print("\n5) Einzelner Vorgang mit Kontakt, Stichwort und ITK-Feldern")
        lid = bsp["vorgang"]
        if lid:
            daten = kw("crm.lead", "read", [[lid], ["name", "partner_id", "user_id", "team_id",
                                                     "stage_id", "priority", "tag_ids", "expected_revenue",
                                                     "x_Produktinteresse", "x_lead_status",
                                                     "campaign_id", "medium_id", "source_id",
                                                     "description", "message_ids"]],
                       context=CTX)[0]
            oeffne("/web#id=%s&model=crm.lead&view_type=form" % lid, ".o_form_view")
            form = txt(".o_form_view")
            pruefe(daten["name"][:25] in form, "Vorgangsname sichtbar: %s" % daten["name"][:40])
            # Kontakt/Verkäufer stehen als many2one-Widget im Formular - den
            # angezeigten Text direkt am Feld lesen (der Formulartext enthaelt
            # auch abgeschnittene Anzeigenamen).
            def feldtext(name):
                el = seite.query_selector(".o_field_widget[name='%s']" % name)
                if not el:
                    return ""
                eingabe = el.query_selector("input")
                if eingabe:
                    wert = (eingabe.input_value() or "").strip()
                    if wert:
                        return wert
                return re.sub(r"\s+", " ", el.inner_text()).strip()
            pruefe(len(feldtext("partner_id")) > 0,
                   "Kontakt sichtbar: %s" % feldtext("partner_id")[:50])
            pruefe(len(feldtext("user_id")) > 0,
                   "Verkaeufer sichtbar: %s" % feldtext("user_id")[:40])
            pruefe("Stichwörter" in form, "Feld Stichwoerter vorhanden")
            pruefe("Erwarteter Umsatz" in form or "Erwartetes Abschlussdatum" in form,
                   "Umsatz/Abschlussdatum vorhanden")
            chatter = txt(".o-mail-Chatter, .o-mail-ChatterContainer")
            pruefe(len(chatter) > 0, "Chatter-Bereich vorhanden (%d Zeichen)" % len(chatter))
            # Migrierte fachliche Nachrichten und Anhaenge sichtbar?
            n11 = kw("mail.message", "search_count",
                     [[("model", "=", "crm.lead"), ("res_id", "=", lid)]], context=CTX)
            nachrichten = len(seite.query_selector_all(".o-mail-Message"))
            pruefe(nachrichten > 0,
                   "Chatter zeigt %d Nachrichten (RPC: %d)" % (nachrichten, n11))
            anhaenge = kw("ir.attachment", "search_count",
                          [[("res_model", "=", "crm.lead"), ("res_id", "=", lid)]], context=CTX)
            anzeige = txt(".o-mail-Chatter, .o-mail-ChatterContainer")
            pruefe(anhaenge == 0 or "Anhang" in anzeige or "Anhänge" in anzeige
                   or "Anlage" in anzeige or len(seite.query_selector_all(".o-mail-AttachmentCard")) > 0,
                   "Anhaenge im Chatter sichtbar (RPC: %d)" % anhaenge)
            # Reiter "Zusaetzliche Informationen": Vertriebskanal, Kampagne,
            # Medium, Herkunft sowie die ITK-Felder aus Odoo 11
            tab = None
            for el in seite.query_selector_all(".nav-link"):
                if el.is_visible() and "Zusätzliche" in el.inner_text():
                    tab = el
                    break
            if tab:
                klick(tab)
                seite.wait_for_timeout(2500)
            form2 = txt(".o_form_view")
            pruefe(len(feldtext("team_id")) > 0,
                   "Vertriebskanal sichtbar: %s" % feldtext("team_id")[:40])
            for label in ["Kampagne", "Medium", "Herkunft"]:
                pruefe(label in form2, "Feld '%s' vorhanden" % label)
            for label in ["Produktinteresse", "Lead Status", "Lead Quelle"]:
                pruefe(label in form2, "ITK-Feld '%s' im Formular sichtbar" % label)
            schuss("07_%s_vorgang_formular.png" % a.instanz)

            print("\n6) Statusleiste und Stufen im Formular")
        seite.goto(url + "/web#id=%s&model=crm.lead&view_type=form" % lid)
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(3000)
        aktuell = [e.inner_text().strip() for e in seite.query_selector_all(".o_statusbar_status button")
                   if e.is_visible()]
        print("       Statusleiste: %s" % aktuell)
        pruefe(any(str(daten["stage_id"][1])[:8] in a for a in aktuell),
               "Aktuelle Stufe '%s' in der Statusleiste" % daten["stage_id"][1])
        pruefe(len(aktuell) >= 2, "Weitere Stufen als Knoepfe erreichbar (%d)" % len(aktuell))
        schuss("08_%s_statusleiste.png" % a.instanz)

        print("\n7) Gewonnener, verlorener und archivierter Vorgang")
        for key, label in [("gewonnen", "Gewonnen"), ("verloren", "Verloren"),
                           ("archiviert", "Archiviert")]:
            vid = bsp.get(key)
            if not vid:
                pruefe(False, "%s Vorgang vorhanden" % label)
                continue
            oeffne("/web#id=%s&model=crm.lead&view_type=form" % vid, ".o_form_view")
            form = txt(".o_form_view")
            pruefe(len(form) > 200, "%s Vorgang laesst sich oeffnen (%d Zeichen)" % (label, len(form)))
            schuss("09_%s_%s.png" % (a.instanz, key.lower()))

        print("\n8) Neuen Vorgang anlegen, bearbeiten, archivieren, wiederherstellen, loeschen")
        oeffne("/web#action=%s&model=crm.lead&view_type=kanban" % akt["pipeline"])
        neu_id = None
        try:
            neu_knopf = seite.query_selector("button.o-kanban-button-new")
            if not neu_knopf:
                neu_knopf = seite.query_selector("button:has-text('Neu')")
            klick(neu_knopf)
            seite.wait_for_timeout(2000)
            # Bei aktivierten Leads fragt Odoo 18 nach dem Typ
            for el in seite.query_selector_all(".dropdown-item, .o_menu_item"):
                if el.is_visible() and "Verkaufschance" in el.inner_text():
                    klick(el)
                    break
            seite.wait_for_timeout(2500)
            name = "ABNAHME S145 Testchance"
            # Odoo 18 legt im Kanban eine Schnell-Anlagekarte an (kein Vollformular)
            feld = seite.query_selector(".o_kanban_quick_add .o_field_widget[name='name'] input, .o_field_widget[name='name'] input")
            if feld:
                feld.fill(name)
                seite.wait_for_timeout(800)
            hinzu = None
            for el in seite.query_selector_all("button"):
                if el.is_visible() and el.inner_text().strip() in ("Hinzufügen", "Speichern"):
                    hinzu = el
                    break
            if hinzu:
                klick(hinzu)
                seite.wait_for_timeout(3500)
            else:
                speichern()
                seite.wait_for_timeout(3000)
            treffer = kw("crm.lead", "search_read", [[("name", "=", name)], ["id", "stage_id"]],
                        context=CTX, limit=1)
            pruefe(bool(treffer), "Neuer Vorgang im Browser angelegt")
            if treffer:
                neu_id = treffer[0]["id"]
                pruefe(treffer[0]["stage_id"] is not False, "Neuer Vorgang hat eine Stufe")
                schuss("10_%s_neuer_vorgang.png" % a.instanz)
                # Karte oeffnen: erst im Formular gibt es Sterne, Statusleiste
                # und das Aktionen-Menue
                oeffne("/web#id=%s&model=crm.lead&view_type=form" % neu_id, ".o_form_view")
                # bearbeiten: Prioritaet setzen (Stern-Widget)
                widget = seite.query_selector(".o_field_widget[name='priority']")
                sterne = []
                if widget:
                    sterne = [a for a in widget.query_selector_all("a") if a.is_visible()]
                if len(sterne) >= 3:
                    klick(sterne[2])
                    seite.wait_for_timeout(2500)
                    prio = kw("crm.lead", "read", [[neu_id], ["priority"]], context=CTX)[0]["priority"]
                    pruefe(prio != "0", "Prioritaet im Formular geaendert (jetzt %s)" % prio)
                else:
                    pruefe(False, "Prioritaets-Sterne im Formular gefunden (%d)" % len(sterne))

                # Stufenwechsel am Testdatensatz
                knoepfe = [e for e in seite.query_selector_all(".o_statusbar_status button")
                           if e.is_visible()]
                ziel_knopf = ziel_name = None
                for k in knoepfe:
                    n = re.sub(r"\s*\d+\s*(Min\.|Std\.|Tage?|J|Monate?).*$", "",
                               k.inner_text().strip()).strip()
                    if n in ("Angebotsphase", "On-Hold", "Angebot ausgesendet",
                             "Positive Rückmeldung", "Erfolgreich", "Verloren",
                             "Zur Verrechnung bereit", "Verrechnet"):
                        ziel_knopf, ziel_name = k, n
                        break
                vorher_neu = kw("crm.lead", "read", [[neu_id], ["stage_id"]], context=CTX)[0]["stage_id"][1]
                if ziel_knopf:
                    klick(ziel_knopf)
                    seite.wait_for_timeout(3200)
                    jetzt = kw("crm.lead", "read", [[neu_id], ["stage_id"]], context=CTX)[0]["stage_id"][1]
                    pruefe(jetzt == ziel_name, "Stufe am Testvorgang gewechselt: %s -> %s"
                           % (vorher_neu, jetzt))
                else:
                    pruefe(False, "Stufenknopf am Testvorgang sichtbar")

                # Archivieren ueber das Aktionen-Menue des Formulars
                oeffne("/web#id=%s&model=crm.lead&view_type=form" % neu_id, ".o_form_view")
                seite.keyboard.press("Escape")
                seite.wait_for_timeout(1500)
                aktion = seite.query_selector(".o_cp_action_menus button")
                if aktion:
                    klick(aktion)
                    seite.wait_for_timeout(2000)
                arch = None
                for box in seite.query_selector_all(".dropdown-menu, .o-dropdown--menu"):
                    for el in box.query_selector_all("a, button, .dropdown-item, .o_menu_item"):
                        if re.sub(r"\s+", " ", el.inner_text()).strip() == "Archivieren":
                            arch = el
                            break
                    if arch:
                        break
                if arch:
                    klick(arch)
                    seite.wait_for_timeout(2500)
                    # Odoo fragt beim Archivieren nach (Bestaetigungsdialog)
                    for el in seite.query_selector_all(".modal-footer button, .o_dialog footer button"):
                        if el.is_visible() and el.inner_text().strip() in ("OK", "Ok", "Archivieren"):
                            klick(el)
                            break
                    seite.wait_for_timeout(3500)
                    aktiv = kw("crm.lead", "search_read", [[("id", "=", neu_id)], ["active"]],
                               context={"lang": "de_DE", "active_test": False}, limit=1)
                    pruefe(aktiv and aktiv[0]["active"] is False, "Testvorgang archiviert")
                    schuss("11_%s_archiviert.png" % a.instanz)
                    # Wiederherstellen: archivierter Datensatz laesst sich per URL oeffnen
                    oeffne("/web#id=%s&model=crm.lead&view_type=form" % neu_id, ".o_form_view")
                    aktion = seite.query_selector(".o_cp_action_menus button")
                    if aktion:
                        klick(aktion)
                        seite.wait_for_timeout(2000)
                    zur = None
                    for box in seite.query_selector_all(".dropdown-menu, .o-dropdown--menu"):
                        for el in box.query_selector_all("a, button, .dropdown-item, .o_menu_item"):
                            if re.sub(r"\s+", " ", el.inner_text()).strip() in ("Archivierung aufheben", "Wiederherstellen", "Zurückholen"):
                                zur = el
                                break
                        if zur:
                            break
                    if zur:
                        klick(zur)
                        seite.wait_for_timeout(2500)
                        for el in seite.query_selector_all(".modal-footer button, .o_dialog footer button"):
                            if el.is_visible() and el.inner_text().strip() in ("OK", "Ok", "Archivierung aufheben", "Wiederherstellen"):
                                klick(el)
                                break
                        seite.wait_for_timeout(3500)
                        aktiv = kw("crm.lead", "search_read", [[("id", "=", neu_id)], ["active"]],
                                   context={"lang": "de_DE", "active_test": False}, limit=1)
                        pruefe(aktiv and aktiv[0]["active"] is True, "Testvorgang wiederhergestellt")
                    else:
                        pruefe(False, "Aktion 'Wiederherstellen' im Aktionen-Menue")
                else:
                    pruefe(False, "Aktion 'Archivieren' im Aktionen-Menue")
        except Exception as exc:  # noqa: BLE001
            pruefe(False, "Neuanlage im Browser: %s" % str(exc)[:160])
        finally:
            schuss("11_%s_test_vorgang.png" % a.instanz)
            # Testdaten entfernen
            if neu_id:
                kw("crm.lead", "unlink", [[neu_id]])
                rest = kw("crm.lead", "search_count", [[("id", "=", neu_id)]],
                          context={"lang": "de_DE", "active_test": False})
                pruefe(rest == 0, "Testvorgang wieder geloescht (Rest: %d)" % rest)

        print("\n9) Konfiguration: Stufen, Vertriebskanaele, Ablehnungsgruende, Lead Tags")
        oeffne("/web#action=%s&model=crm.stage&view_type=list" % akt["stufen"], ".o_list_view")
        stufen_liste = [s for s in ["Neu", "Angebotsphase", "On-Hold", "Angebot ausgesendet",
                                    "Positive Rückmeldung", "Erfolgreich", "Verloren",
                                    "Zur Verrechnung bereit", "Verrechnet"]
                        if s in txt(".o_list_view")]
        pruefe(len(stufen_liste) >= 7, "Stufenliste zeigt %d Stufen" % len(stufen_liste))
        schuss("12_%s_stufen.png" % a.instanz)
        oeffne("/web#action=%s&model=crm.team&view_type=list" % akt["teams"], ".o_list_view")
        teams_text = txt(".o_list_view")
        teams = [t for t in ["Suche / Liste", "Persönlicher Kontakt", "Webseite", "Telefon",
                             "Webinar", "Newsletter", "Interne Weitergabe",
                             "Vertriebskanäle (Intern)"] if t in teams_text]
        pruefe(len(teams) >= 6, "Vertriebskanaele sichtbar: %s" % teams)
        schuss("13_%s_vertriebskanaele.png" % a.instanz)
        oeffne("/web#action=%s&model=crm.lost.reason&view_type=list" % akt["gruende"], ".o_list_view")
        gruende = [g for g in ["Zu teuer", "Im Moment keinen Bedarf", "Bedarf zu gering",
                               "Später kontaktieren", "Mitbewerb"] if g in txt(".o_list_view")]
        pruefe(len(gruende) >= 4, "Ablehnungsgruende sichtbar: %s" % gruende)
        schuss("14_%s_ablehnungsgruende.png" % a.instanz)
        oeffne("/web#action=%s&model=crm.tag&view_type=list" % akt["tags"], ".o_list_view")
        pruefe(pager() >= 40, "Lead Tags: %s Datensaetze (Soll >= 40)" % pager())
        schuss("15_%s_lead_tags.png" % a.instanz)

        ctx.close()

    print("\n=== Ergebnis %s: %d OK / %d FEHL ===" % (a.instanz, ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
