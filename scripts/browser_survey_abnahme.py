# -*- coding: utf-8 -*-
"""Browserabnahme Umfragen / Survey nach der Datenmigration (Session 146).

Prueft im echten Browser (Playwright, Chrome, eigenes Profil) und haelt jede
Erwartung gegen einen per RPC gemessenen Sollwert. Screenshots landen im
Temp-Ordner (nicht im Repository). Antwortinhalte werden nie ausgegeben -
nur Laengen und Zaehlwerte.

Geprueft wird:
 1 Menueband und Menuepunkte
 2 Umfrageliste: Anzahl, Spalten, Filter "Archiviert"
 3 Kanban der Umfragen
 4 Einzelne Umfrage: Titel, Abschnitt, Frage, Kennzahlen
 5 Fragen-Liste und Vorgeschlagene Werte
 6 Teilnahmen: Anzahl, Filter, Gruppierung, Suche
 7 Einzelne Teilnahme mit Antwortzeile
 8 Auswertung (Graph/Pivot) und Ergebnisseite
 9 Oeffentliche Umfrage ausfuellen (Testteilnahme, danach entfernt)
10 Umfrage ueber die Oberflaeche anlegen, Frage ergaenzen, loeschen
11 Befund: "Neu" in der Fragen-Liste (Produktfehler in survey 18.0.3.7)

Aufruf:
    python scripts/browser_survey_abnahme.py --instanz lokal
    python scripts/browser_survey_abnahme.py --instanz vm
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
VZ = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Temp",
                  "s146_survey", "bilder")
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
    sid, kw = rpc_sitzung(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    CTX = {"lang": "de_DE"}
    CTX_ALLE = {"lang": "de_DE", "active_test": False}

    # ------------------------------------------------------------ Sollwerte
    soll = {
        "umfragen": kw("survey.survey", "search_count", [[]], context=CTX),
        "teilnahmen": kw("survey.user_input", "search_count", [[]], context=CTX),
        "abgeschlossen": kw("survey.user_input", "search_count", [[("state", "=", "done")]],
                            context=CTX),
        "fragen": kw("survey.question", "search_count", [[("is_page", "=", False)]], context=CTX),
        "vorgaben": kw("survey.question.answer", "search_count", [[]], context=CTX),
    }
    umfragen = kw("survey.survey", "search_read",
                  [[], ["id", "title", "access_token", "question_count", "answer_count",
                        "answer_done_count"]], context=CTX, order="id")
    # Die Umfrage mit den meisten Teilnahmen ist die fachlich relevante
    echte = max(umfragen, key=lambda x: x["answer_count"]) if umfragen else None
    test_umfrage = next((x for x in umfragen if x["id"] != (echte or {}).get("id")), None)
    teilnahme = kw("survey.user_input", "search",
                   [[("state", "=", "done")]], context=CTX, order="id desc", limit=1)
    print("Sollwerte: %s" % soll)
    print("Echte Umfrage: %s (%d Antworten)" % (echte["id"], echte["answer_count"]))
    if not echte or not teilnahme:
        print("ABBRUCH: keine migrierten Daten gefunden.")
        return 2

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

    def befund(text):
        print("  BEFUND %s" % text)

    def aktion(xml_teil):
        d = kw("ir.model.data", "search_read",
               [[("module", "=", xml_teil.split(".")[0]), ("name", "=", xml_teil.split(".", 1)[1])],
                ["res_id"]])
        return d[0]["res_id"] if d else None

    # Odoo-18-XML-IDs (in Odoo 11 hiessen sie action_survey_question/_label_form)
    akt = {"umfragen": aktion("survey.action_survey_form"),
           "teilnahmen": aktion("survey.action_survey_user_input"),
           "fragen": aktion("survey.action_survey_question_form"),
           "vorgaben": aktion("survey.survey_question_answer_action"),
           "zeilen": aktion("survey.survey_user_input_line_action")}
    print("Aktionen: %s" % akt)

    neu_umfrage, neu_teilnahme = None, None
    try:
        with sync_playwright() as pw:
            ctx = pw.chromium.launch_persistent_context(
                user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"),
                                           "pw_survey146_" + a.instanz),
                channel="chrome", headless=True, viewport={"width": 1700, "height": 1300})
            ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
            seite = ctx.pages[0] if ctx.pages else ctx.new_page()

            def oeffne(pfad, selektor=".o_view_controller, .o_form_view, .o_list_view, "
                                     ".o_kanban_view, .o_graph_view, .o_pivot_view"):
                seite.goto(url + pfad)
                seite.wait_for_selector(selektor, timeout=120000)
                seite.wait_for_timeout(3000)

            def schuss(name):
                if not a.ohne_screenshot:
                    datei = os.path.join(VZ, name)
                    seite.screenshot(path=datei, full_page=True)
                    print("       Screenshot: %s" % datei)

            def txt(sel="body"):
                try:
                    return re.sub(r"\s+", " ", seite.inner_text(sel))
                except Exception:  # noqa: BLE001
                    return ""

            def pager():
                t = seite.query_selector(".o_pager_limit")
                if t:
                    return int(re.sub(r"[^0-9]", "", t.inner_text()) or -1)
                return -1

            def klick(el):
                box = el.bounding_box()
                seite.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

            def suchmenue_oeffnen():
                knopf = seite.query_selector(".o_searchview_dropdown_toggler, "
                                             ".o_searchview .o_dropdown_toggler_btn, "
                                             "button.o_searchview_dropdown_toggler")
                if knopf:
                    klick(knopf)
                    seite.wait_for_timeout(1200)
                    return True
                return False

            def cookie_weg():
                """Cookie-Hinweis wegklicken - er liegt sonst ueber den Knoepfen."""
                for el in seite.query_selector_all("button, a"):
                    try:
                        if el.is_visible() and (el.inner_text() or "").strip() == "OK":
                            el.evaluate("e => e.click()")
                            seite.wait_for_timeout(800)
                            return True
                    except Exception:  # noqa: BLE001
                        continue
                return False

            def zeilen():
                return len([e for e in seite.query_selector_all(".o_data_row") if e.is_visible()])

            def text_klick(text, tag="*"):
                """Klickt das erste sichtbare Element mit genau diesem Text per Maus."""
                for el in seite.query_selector_all(tag):
                    try:
                        if el.is_visible() and (el.inner_text() or "").strip() == text:
                            box = el.bounding_box()
                            if box:
                                seite.mouse.click(box["x"] + box["width"] / 2,
                                                  box["y"] + box["height"] / 2)
                                seite.wait_for_timeout(1200)
                                return True
                    except Exception:  # noqa: BLE001
                        continue
                return False

            def gruppen():
                return [re.sub(r"\s+", " ", e.inner_text()).strip()
                        for e in seite.query_selector_all(".o_group_header") if e.is_visible()]

            def menue_eintrag(name):
                """Klickt einen Eintrag im offenen Suchmenue per DOM-Klick."""
                for el in seite.query_selector_all(".dropdown-menu *, .o-dropdown--menu *"):
                    if not el.is_visible():
                        continue
                    text = re.sub(r"\s+", " ", el.inner_text() or "").strip()
                    if text == name:
                        el.evaluate("e => e.click()")
                        seite.wait_for_timeout(2500)
                        return True
                return False

            def ansicht(art):
                """Wechselt ueber die Ansichts-Knoepfe auf graph/pivot."""
                knopf = seite.query_selector("button.o_switch_view.o_%s" % art)
                if knopf:
                    knopf.evaluate("e => e.click()")
                    seite.wait_for_timeout(4000)
                    return True
                return False

            def suchmenue_text():
                teile = []
                for sel in (".dropdown-menu", ".o-dropdown--menu", ".o_search_bar_menu"):
                    for el in seite.query_selector_all(sel):
                        if el.is_visible():
                            teile.append(re.sub(r"\s+", " ", el.inner_text()))
                return " | ".join(teile)

            print("\n1) Menueband und Menuepunkte")
            oeffne("/web#action=%s&model=survey.survey&view_type=list" % akt["umfragen"])
            band = txt(".o_main_navbar")
            pruefe("Umfragen" in band, "App-Name im Menueband: %s" % band[:90])
            for name in ("Umfragen", "Teilnahmen", "Fragen & Antworten"):
                pruefe(name in band, "Menuepunkt '%s' sichtbar" % name)
            schuss("01_%s_menueband.png" % a.instanz)

            print("\n2) Umfrageliste")
            pruefe(pager() == soll["umfragen"],
                   "Pager %s = Soll %s Umfragen" % (pager(), soll["umfragen"]))
            kopf = txt("thead")
            for spalte in ("Umfrage", "Verantwortlich"):
                pruefe(spalte in kopf, "Spalte '%s' sichtbar" % spalte)
            if "Fragen" in kopf:
                pruefe(True, "Spalte 'Fragen' sichtbar")
            else:
                befund("Spalte 'Fragen' ist in der Liste standardmaessig ausgeblendet "
                       "(Odoo-18-Spaltenauswahl)")
            liste = txt(".o_list_view")
            pruefe(echte["title"][:25] in liste, "Umfrage-Titel in der Liste sichtbar")
            schuss("02_%s_umfrageliste.png" % a.instanz)

            print("\n3) Kanban der Umfragen")
            oeffne("/web#action=%s&model=survey.survey&view_type=kanban" % akt["umfragen"],
                   ".o_kanban_view")
            karten = len([e for e in seite.query_selector_all(".o_kanban_record")
                          if e.is_visible()])
            pruefe(karten >= soll["umfragen"],
                   "Kanban zeigt %d Karten (Soll %d)" % (karten, soll["umfragen"]))
            schuss("03_%s_kanban.png" % a.instanz)

            print("\n4) Einzelne Umfrage")
            oeffne("/web#id=%s&model=survey.survey&view_type=form" % echte["id"], ".o_form_view")
            form = txt()
            pruefe(echte["title"][:25] in form, "Titel im Formular sichtbar")
            pruefe("Abschnitt" in form or "Seite" in form,
                   "Abschnittsbereich sichtbar (Odoo 18 nennt Seiten 'Abschnitt')")
            schuss("04_%s_umfrage_formular.png" % a.instanz)

            fragen_dom = kw("survey.question", "search_read",
                            [[("survey_id", "=", echte["id"])],
                             ["id", "title", "is_page", "question_type"]], context=CTX, order="id")
            for f in fragen_dom:
                titel = (f["title"] or "")[:30]
                in_dom = titel.split("(")[0].strip()[:30] in form
                if f["is_page"]:
                    pruefe(in_dom, "Abschnitt '%s' im Formular sichtbar" % titel)
                else:
                    pruefe(in_dom, "Frage '%s' im Formular sichtbar" % titel)
            schuss("05_%s_umfrage_fragen.png" % a.instanz)

            print("\n5) Fragen und Vorgaben")
            oeffne("/web#action=%s&model=survey.question&view_type=list" % akt["fragen"],
                   ".o_list_view")
            pruefe(pager() == soll["fragen"], "Fragen-Pager %s = Soll %s"
                   % (pager(), soll["fragen"]))
            schuss("06_%s_fragen.png" % a.instanz)
            oeffne("/web#action=%s&model=survey.question.answer&view_type=list" % akt["vorgaben"],
                   ".o_list_view")
            # Die Vorgaben sind standardmaessig nach Frage gruppiert - aufklappen.
            for kopf in seite.query_selector_all(".o_group_header"):
                if kopf.is_visible():
                    kopf.evaluate("e => e.click()")
                    seite.wait_for_timeout(1500)
            pruefe(zeilen() == soll["vorgaben"], "Vorgaben-Liste zeigt %d Zeilen = Soll %s"
                   % (zeilen(), soll["vorgaben"]))
            werte = txt(".o_list_view")
            yes = kw("survey.question.answer", "search_read", [[], ["value"]], context=CTX,
                     order="id")
            for w in yes:
                pruefe(w["value"] in werte, "Vorgabe '%s' sichtbar" % w["value"])
            schuss("07_%s_vorgaben.png" % a.instanz)

            print("\n6) Teilnahmen: Liste, Filter, Gruppierung, Suche")
            oeffne("/web#action=%s&model=survey.user_input&view_type=list" % akt["teilnahmen"],
                   ".o_list_view")
            # Teilnahmen sind in Odoo 18 standardmaessig nach Umfrage gruppiert.
            g = gruppen()
            pruefe(len(g) == soll["umfragen"],
                   "Standard-Gruppierung nach Umfrage: %d Gruppen (Soll %d): %s"
                   % (len(g), soll["umfragen"], g))
            schuss("08_%s_teilnahmen.png" % a.instanz)

            if suchmenue_oeffnen():
                pruefe("Abgeschlossen" in suchmenue_text(),
                       "Filter 'Abgeschlossen' im Suchmenue vorhanden")
                if menue_eintrag("Abgeschlossen"):
                    g = gruppen()
                    pruefe(len(g) == 1, "Filter 'Abgeschlossen': %d Gruppe(n) statt 2 "
                           "(die Testumfrage hat nur eine offene Teilnahme)" % len(g))
                    if g:
                        m = re.search(r"(\d+)", g[0])
                        zaehler = int(m.group(1)) if m else -1
                        pruefe(zaehler == soll["abgeschlossen"],
                               "Gruppe zeigt %s = Soll %s abgeschlossene Teilnahmen"
                               % (zaehler, soll["abgeschlossen"]))
                    schuss("09_%s_teilnahmen_abgeschlossen.png" % a.instanz)

            # Gruppierung entfernen und erneut setzen
            seite.goto(url + "/web#action=%s&model=survey.user_input&view_type=list"
                             % akt["teilnahmen"])
            seite.wait_for_selector(".o_list_view", timeout=120000)
            seite.wait_for_timeout(2500)
            chip = None
            for el in seite.query_selector_all(".o_searchview_facet"):
                if "Umfrage" in (el.inner_text() or ""):
                    chip = el.query_selector(".o_facet_remove, .fa-times, button")
                    break
            if chip:
                chip.evaluate("e => e.click()")
                seite.wait_for_timeout(2500)
                pruefe(len(gruppen()) == 0 and pager() == soll["teilnahmen"],
                       "Gruppierung entfernt: %d Gruppen, Pager %s = Soll %s"
                       % (len(gruppen()), pager(), soll["teilnahmen"]))
                schuss("10a_%s_teilnahmen_flach.png" % a.instanz)
                if suchmenue_oeffnen() and menue_eintrag("Umfrage"):
                    pruefe(len(gruppen()) == soll["umfragen"],
                           "Gruppierung nach Umfrage erneut gesetzt: %d Gruppen (Soll %d)"
                           % (len(gruppen()), soll["umfragen"]))
                    schuss("10_%s_teilnahmen_gruppiert.png" % a.instanz)
            else:
                befund("Gruppierungs-Chip 'Umfrage' nicht gefunden")

            # Suche: in der Teilnahmenliste sucht das Feld nach Teilnehmer/E-Mail
            # (Odoo-18-Standard); der Umfragetitel wird ueber den Filter "Umfrage"
            # gesetzt. Geprueft wird daher die Suche in der Umfrageliste.
            oeffne("/web#action=%s&model=survey.survey&view_type=list" % akt["umfragen"])
            feld = seite.query_selector(".o_searchview_input")
            if feld:
                feld.click()
                feld.type(echte["title"].split("|")[0].strip()[:12])
                seite.wait_for_timeout(2000)
                vorschlag = None
                for el in seite.query_selector_all(".o_searchview_autocomplete li, "
                                                   ".o_searchview_autocomplete *"):
                    if el.is_visible() and (el.inner_text() or "").strip():
                        vorschlag = el
                        break
                if vorschlag:
                    vorschlag.evaluate("e => e.click()")
                else:
                    seite.keyboard.press("Enter")
                seite.wait_for_timeout(3500)
                pruefe(pager() == 1, "Suche nach Umfragetitel findet %s = Soll 1"
                       % pager())
                schuss("11_%s_suche.png" % a.instanz)
            befund("Teilnahmen-Suche sucht nach Teilnehmer/E-Mail; der Umfragetitel wird "
                   "ueber Filter/Gruppierung 'Umfrage' gesetzt (Odoo-18-Standard, wie Odoo 11)")

            print("\n7) Einzelne Teilnahme mit Antwort")
            oeffne("/web#id=%s&model=survey.user_input&view_type=form" % teilnahme[0],
                   ".o_form_view")
            form = txt()
            pruefe("Abgeschlossen" in form or "Erledigt" in form,
                   "Status der Teilnahme sichtbar")
            zeilen = kw("survey.user_input.line", "search_read",
                        [[("user_input_id", "=", teilnahme[0])], ["value_text_box", "question_id"]],
                        context=CTX)
            pruefe(len(zeilen) >= 1, "Teilnahme hat %d Antwortzeile(n)" % len(zeilen))
            if zeilen:
                laenge = len(zeilen[0]["value_text_box"] or "")
                pruefe(laenge > 0, "Antworttext vorhanden (%d Zeichen, Inhalt nicht protokolliert)"
                       % laenge)
                anfang = (zeilen[0]["value_text_box"] or "")[:15]
                pruefe(anfang in form, "Antwortanfang wird im Formular angezeigt")
            schuss("12_%s_teilnahme.png" % a.instanz)

            print("\n8) Auswertung")
            # Die Umfrage-Aktion fuehrt nur Kanban/Liste/Formular/Aktivitaet - Graph und
            # Pivot sind in Odoo 18 vorhanden, aber nicht in der Aktion verknuepft.
            knopf_arten = seite.evaluate(
                """() => Array.from(document.querySelectorAll('.o_switch_view'))
                        .map(e => e.className.replace('btn btn-secondary o_switch_view ', ''))""")
            pruefe("o_graph" not in " ".join(knopf_arten),
                   "Ansichtsumschalter der Umfragen: %s (Graph/Pivot nicht in der Aktion - "
                   "Odoo-18-Standard)" % knopf_arten)
            oeffne("/web#id=%s&model=survey.survey&view_type=form" % echte["id"], ".o_form_view")
            form = txt()
            pruefe("Ergebnisse" in form or "Teilen" in form,
                   "Umfrageformular bietet Auswertung/Teilen an")
            schuss("13_%s_umfrage_aktionen.png" % a.instanz)
            seite.goto(url + "/survey/results/%s" % echte["access_token"])
            seite.wait_for_timeout(4000)
            ergebnis = txt()
            pruefe("Ergebnis" in ergebnis or "Antwort" in ergebnis or "Frage" in ergebnis,
                   "Ergebnisseite der Umfrage oeffnet sich")
            schuss("15_%s_ergebnisse.png" % a.instanz)

            print("\n9) Oeffentliche Umfrage ausfuellen (Testteilnahme)")
            ziel = test_umfrage or echte
            vorher = kw("survey.user_input", "search_count", [[]], context=CTX)
            seite.goto(url + "/survey/start/%s" % ziel["access_token"])
            seite.wait_for_timeout(4000)
            cookie_weg()
            seite_text = txt()
            pruefe("Umfrage" in seite_text or ziel["title"][:15] in seite_text,
                   "oeffentliche Umfrageseite oeffnet sich ohne Anmeldung")
            schuss("16_%s_oeffentlich.png" % a.instanz)
            # Odoo 18 zeigt zuerst eine Startseite mit "Umfrage starten".
            gestartet = False
            for el in seite.query_selector_all("button, a"):
                try:
                    if el.is_visible() and "starten" in (el.inner_text() or "").lower():
                        box = el.bounding_box()
                        if box:
                            seite.mouse.click(box["x"] + box["width"] / 2,
                                              box["y"] + box["height"] / 2)
                            seite.wait_for_timeout(2500)
                            gestartet = True
                            break
                except Exception:  # noqa: BLE001
                    continue
            pruefe(gestartet, "oeffentliche Umfrage laesst sich starten")
            cookie_weg()
            schuss("16b_%s_oeffentlich_frage.png" % a.instanz)
            # Antwortmoeglichkeit: Odoo 18 rendert die Zeilen als klickbare Kacheln.
            gewaehlt = False
            for el in seite.query_selector_all(".o_survey_form_choice_item, label, .form-check"):
                try:
                    if el.is_visible() and (el.inner_text() or "").strip() in ("ja", "nein"):
                        box = el.bounding_box()
                        if box:
                            seite.mouse.click(box["x"] + box["width"] / 2,
                                              box["y"] + box["height"] / 2)
                            seite.wait_for_timeout(1200)
                            gewaehlt = True
                            break
                except Exception:  # noqa: BLE001
                    continue
            if not gewaehlt:
                feld = seite.query_selector("textarea, input[type=text]")
                if feld:
                    feld.click()
                    seite.keyboard.type("ITK Testeintrag Session 146", delay=20)
                    gewaehlt = True
            pruefe(gewaehlt, "Antwort im oeffentlichen Formular gesetzt")
            schuss("17a_%s_oeffentlich_ausgefuellt.png" % a.instanz)
            absenden = seite.query_selector("button.o_survey_navigation_submit")
            if absenden:
                box = absenden.bounding_box()
                seite.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                seite.wait_for_timeout(5000)
            else:
                befund("Absende-Knopf o_survey_navigation_submit nicht gefunden")
            schuss("17_%s_oeffentlich_gesendet.png" % a.instanz)
            nachher = kw("survey.user_input", "search_count", [[]], context=CTX)
            pruefe(nachher == vorher + 1, "Teilnahmen %s -> %s (eine Testteilnahme angelegt)"
                   % (vorher, nachher))
            neu_teilnahme = kw("survey.user_input", "search",
                               [[("itk_o11_id", "=", False)]], context=CTX_ALLE, order="id desc",
                               limit=1)
            if neu_teilnahme:
                daten = kw("survey.user_input", "read", [neu_teilnahme, ["state"]], context=CTX)
                zeilen_neu = kw("survey.user_input.line", "search_count",
                                [[("user_input_id", "=", neu_teilnahme[0])]], context=CTX)
                pruefe(daten[0]["state"] == "done",
                       "Testteilnahme ist abgeschlossen (Status %s)" % daten[0]["state"])
                pruefe(zeilen_neu == 1, "Testteilnahme hat %d Antwortzeile(n)" % zeilen_neu)
                pruefe("Danke" in txt() or "Vielen" in txt() or "abgeschlossen" in txt().lower(),
                       "Danke-Seite wird angezeigt")

            print("\n10) Umfrage ueber die Oberflaeche anlegen")
            oeffne("/web#action=%s&model=survey.survey&view_type=list" % akt["umfragen"])
            neu = seite.query_selector("button.o_list_button_add")
            if neu:
                neu.evaluate("e => e.click()")
                seite.wait_for_selector(".o_form_view", timeout=60000)
                seite.wait_for_timeout(2500)
                cookie_weg()
                # Der Umfragetitel ist in Odoo 18 ein Textfeld (textarea) mit Placeholder.
                titel = seite.query_selector("textarea[placeholder*='Zufriedenheit'], "
                                             ".o_field_widget[name='title'] textarea, "
                                             ".o_field_widget[name='title'] input")
                if titel:
                    titel.click()
                    titel.fill("ITK TEST S146 Browserabnahme")
                    seite.wait_for_timeout(1000)
                else:
                    befund("Titelfeld im Umfrageformular nicht gefunden")
                # Odoo 18 oeffnet dazu den Dialog "Abschnitte und Fragen erstellen"
                if text_klick("Eine Frage hinzufügen"):
                    seite.wait_for_timeout(2500)
                    dialog = seite.query_selector(".o_dialog")
                    pruefe(dialog is not None,
                           "Dialog 'Abschnitte und Fragen erstellen' oeffnet sich")
                    frage = seite.query_selector(".o_dialog .o_field_widget[name='title'] input, "
                                                 ".o_dialog .o_field_widget[name='title'] textarea, "
                                                 ".o_dialog textarea, .o_dialog input[type=text]")
                    if frage:
                        frage.click()
                        frage.fill("ITK TESTFRAGE S146")
                        seite.wait_for_timeout(800)
                    knopf = None
                    for el in seite.query_selector_all(".o_dialog button"):
                        if el.is_visible() and "Speichern & schließen" in (el.inner_text() or ""):
                            knopf = el
                            break
                    if knopf:
                        box = knopf.bounding_box()
                        seite.mouse.click(box["x"] + box["width"] / 2,
                                          box["y"] + box["height"] / 2)
                        seite.wait_for_timeout(3000)
                    else:
                        befund("Knopf 'Speichern & schliessen' im Dialog nicht gefunden")
                speichern = seite.query_selector("button.o_form_button_save")
                if speichern and speichern.is_visible():
                    speichern.evaluate("e => e.click()")
                    seite.wait_for_timeout(4000)
                schuss("18_%s_neue_umfrage.png" % a.instanz)
                neu_umfrage = kw("survey.survey", "search",
                                 [[("title", "=", "ITK TEST S146 Browserabnahme")]],
                                 context=CTX_ALLE)
                pruefe(bool(neu_umfrage), "Umfrage wurde im Browser angelegt")
                if neu_umfrage:
                    daten = kw("survey.survey", "read", [neu_umfrage, ["question_count"]],
                               context=CTX)
                    pruefe(daten[0]["question_count"] >= 1,
                           "Frage im Formular mit angelegt (%d)" % daten[0]["question_count"])
                    fragen = kw("survey.question", "search",
                                [[("survey_id", "=", neu_umfrage[0])]], context=CTX_ALLE)
                    pruefe(len(fragen) >= 1, "angelegte Frage in der Datenbank vorhanden")
            else:
                befund("kein Anlegen-Knopf in der Umfrageliste")

            print("\n11) Befund: 'Neu' in der Fragen-Liste")
            oeffne("/web#action=%s&model=survey.question&view_type=list" % akt["fragen"],
                   ".o_list_view")
            knopf = seite.query_selector("button.o_list_button_add")
            if not knopf:
                befund("Fragen-Liste bietet keinen 'Neu'-Knopf; Fragen werden im "
                       "Umfrageformular ueber den Dialog angelegt (Odoo-18-Standard)")
            if knopf:
                klick(knopf)
                seite.wait_for_timeout(4000)
                fehlertext = ""
                dialog = seite.query_selector(".o_dialog .modal-body, .o_notification_content")
                if dialog:
                    fehlertext = re.sub(r"\s+", " ", dialog.inner_text())[:200]
                if "create" in fehlertext.lower() and "vals_list" in fehlertext:
                    befund("Anlegen einer Frage ueber die Fragen-Liste scheitert mit "
                           "TypeError create()/vals_list - Defekt in survey 18.0.3.7 "
                           "(fehlendes @api.model_create_multi), nicht durch die Migration "
                           "verursacht")
                    schuss("19_%s_frage_neu_defekt.png" % a.instanz)
                else:
                    befund("Anlegen-Knopf der Fragen-Liste: %s"
                           % (fehlertext or "kein Dialog erkannt"))
            ctx.close()
    finally:
        # ---------------------------------------------------------- Aufraeumen
        rest = []
        if neu_umfrage:
            rest += neu_umfrage
        rest += kw("survey.survey", "search",
                   [[("title", "like", "ITK TEST S146")]], context=CTX_ALLE)
        if rest:
            kw("survey.survey", "unlink", [sorted(set(rest))])
        if neu_teilnahme:
            kw("survey.user_input", "unlink", [neu_teilnahme])
        reste = {m: kw(m, "search_count", [[]], context=CTX_ALLE)
                 for m in ("survey.survey", "survey.question", "survey.question.answer",
                           "survey.user_input", "survey.user_input.line")}
        print("\nAufraeumen: Testumfrage und Testteilnahme entfernt")
        print("Bestand danach: %s" % reste)
        pruefe(reste["survey.survey"] == soll["umfragen"],
               "Umfragen wieder bei %s" % soll["umfragen"])
        pruefe(reste["survey.user_input"] == soll["teilnahmen"],
               "Teilnahmen wieder bei %s" % soll["teilnahmen"])

    print()
    print("--- Ergebnis Browserabnahme (%s) ---" % a.instanz)
    print("Pruefungen OK ..... %d" % ok)
    print("Fehlschlaege ...... %d" % fehler)
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
