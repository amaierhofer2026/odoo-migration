# -*- coding: utf-8 -*-
"""Browserabnahme Valorisierung nach der Datenmigration (Session 148), echter Chrome.

Ergaenzt die Strukturabnahme aus Session 129 (``browser_valorisierung_abnahme.py``)
um die Datenpruefung: Beschreibungstexte, Suche, Filter/Gruppierung, Anlegen,
Bearbeiten, Loeschen und das Feld "Valorisation Text" im Rechnungsformular.
Testdaten werden anschliessend entfernt.

Aufruf:
    python scripts/browser_valorisierung_daten_abnahme.py --instanz lokal
    python scripts/browser_valorisierung_daten_abnahme.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import ssl
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Temp",
                  "s148_valorisierung")
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


def lade_env(pfad):
    werte = {}
    for zeile in open(pfad, encoding="utf-8"):
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
            raise RuntimeError(json.dumps(antwort["error"])[:300])
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

    MODELL = "itk_valorisierung.valorisierung"
    soll = kw(MODELL, "search_count", [[]], context=CTX)
    akt = kw("ir.model.data", "search_read",
             [[("module", "=", "itk_valorisierung"),
               ("name", "=", "menu_finance_configuration_valorisierung_action")],
              ["res_id"]])[0]["res_id"]
    rechnung = kw("account.move", "search_read",
                  [[["valorisierung_id", "!=", False]], ["id", "name"]], context=CTX, limit=1)
    print("Soll: %d Hinweise, Aktion %s, Rechnung mit Hinweis: %s"
          % (soll, akt, rechnung[0]["id"] if rechnung else None))

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

    neu_id = None
    try:
        with sync_playwright() as pw:
            ctx = pw.chromium.launch_persistent_context(
                user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"),
                                           "pw_valo148_" + a.instanz),
                channel="chrome", headless=True, viewport={"width": 1700, "height": 1300})
            ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
            s = ctx.pages[0] if ctx.pages else ctx.new_page()

            def oeffne(pfad, sel=".o_view_controller, .o_form_view, .o_list_view"):
                s.goto(url + pfad)
                s.wait_for_selector(sel, timeout=120000)
                s.wait_for_timeout(3000)

            def schuss(name):
                if not a.ohne_screenshot:
                    datei = os.path.join(VZ, name)
                    s.screenshot(path=datei, full_page=True)
                    print("       Screenshot: %s" % datei)

            def txt(sel="body"):
                try:
                    return re.sub(r"\s+", " ", s.inner_text(sel))
                except Exception:  # noqa: BLE001
                    return ""

            def pager():
                t = s.query_selector(".o_pager_limit")
                return int(re.sub(r"[^0-9]", "", t.inner_text()) or -1) if t else -1

            print("\n1) Menue und Liste")
            oeffne("/web#action=%s&model=%s&view_type=list" % (akt, MODELL))
            band = txt(".o_main_navbar")
            pruefe("Abrechnung" in band, "App 'Abrechnung' im Menueband")
            liste = txt(".o_list_view")
            pruefe(pager() == soll, "Liste zeigt %s = Soll %d Hinweise" % (pager(), soll))
            kopf = txt("thead")
            for spalte in ("Code", "Beschreibung", "Nummernfolge"):
                pruefe(spalte in kopf, "Spalte '%s' sichtbar" % spalte)
            pruefe("VALORISIERUNGSHINWEIS 2019" in liste, "Code des ersten Hinweises sichtbar")
            schuss("01_%s_liste.png" % a.instanz)

            print("\n2) Formular mit Text")
            satz = kw(MODELL, "search_read", [[["itk_o11_id", "!=", False]],
                                               ["id", "name", "description"]],
                      context=CTX, order="itk_o11_id", limit=1)[0]
            oeffne("/web#id=%d&model=%s&view_type=form" % (satz["id"], MODELL), ".o_form_view")
            form = txt()
            # Textareas liefern ihren Inhalt nicht ueber inner_text - Werte separat lesen.
            form += " " + " ".join(
                (el.input_value() or "")
                for el in s.query_selector_all("textarea")
                if el.is_visible())
            pruefe(satz["name"].strip() in form, "Code im Formular sichtbar")
            anfang = (satz["description"] or "")[:40]
            pruefe(anfang in form, "Beschreibungstext sichtbar (%d Zeichen)"
                   % len(satz["description"] or ""))
            pruefe("Beschreibung" in form and "Nummernfolge" in form,
                   "deutsche Feldbezeichnungen")
            schuss("02_%s_formular.png" % a.instanz)

            print("\n3) Suche")
            oeffne("/web#action=%s&model=%s&view_type=list" % (akt, MODELL))
            feld = s.query_selector(".o_searchview_input")
            if feld:
                feld.click()
                feld.type("2024")
                s.wait_for_timeout(1500)
                s.keyboard.press("Enter")
                s.wait_for_timeout(3000)
                erwartet = kw(MODELL, "search_count", [[["name", "ilike", "2024"]]], context=CTX)
                pruefe(pager() == erwartet, "Suche '2024' findet %s = Soll %d"
                       % (pager(), erwartet))
                schuss("03_%s_suche.png" % a.instanz)

            print("\n4) Filter und Gruppierung (Odoo-18-Standard)")
            knopf = s.query_selector(".o_searchview_dropdown_toggler")
            if knopf:
                box = knopf.bounding_box()
                s.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                s.wait_for_timeout(1500)
                menue = ""
                for el in s.query_selector_all(".dropdown-menu, .o-dropdown--menu"):
                    if el.is_visible():
                        menue += " " + re.sub(r"\s+", " ", el.inner_text())
                pruefe("Filter" in menue or "Gruppieren" in menue,
                       "Suchmenue mit Filter/Gruppieren vorhanden")
                s.keyboard.press("Escape")
                s.wait_for_timeout(800)

            print("\n5) Anlegen, bearbeiten, loeschen")
            oeffne("/web#action=%s&model=%s&view_type=list" % (akt, MODELL))
            add = s.query_selector("button.o_list_button_add")
            if add:
                add.evaluate("e => e.click()")
                s.wait_for_selector(".o_form_view", timeout=60000)
                s.wait_for_timeout(2000)
                name_feld = s.query_selector("div[name='name'] input, "
                                             ".o_field_widget[name='name'] input")
                if name_feld:
                    name_feld.click()
                    s.keyboard.type("ITK TEST S148 Valorisierung", delay=25)
                desc = s.query_selector("div[name='description'] textarea, textarea")
                if desc:
                    desc.click()
                    s.keyboard.type("Testtext Session 148", delay=15)
                sp = s.query_selector("button.o_form_button_save")
                if sp and sp.is_visible():
                    sp.evaluate("e => e.click()")
                    s.wait_for_timeout(3000)
                neu_id = kw(MODELL, "search", [[("name", "=", "ITK TEST S148 Valorisierung")]],
                            context={"lang": "de_DE", "active_test": False}, limit=1)
                pruefe(bool(neu_id), "Hinweis im Browser angelegt")
                if neu_id:
                    daten = kw(MODELL, "read", [neu_id, ["description", "seq"]], context=CTX)
                    pruefe("Testtext Session 148" in (daten[0]["description"] or ""),
                           "Beschreibung wurde gespeichert")
                    oeffne("/web#id=%d&model=%s&view_type=form" % (neu_id[0], MODELL),
                           ".o_form_view")
                    schuss("04_%s_neuer_satz.png" % a.instanz)
            else:
                pruefe(False, "Anlegen-Knopf in der Liste gefunden")

            print("\n6) Feld im Rechnungsformular")
            if rechnung:
                oeffne("/web#id=%d&model=account.move&view_type=form" % rechnung[0]["id"],
                       ".o_form_view")
                form = txt()
                treffer = [e for e in s.query_selector_all(".o_field_widget[name='valorisierung_id']")
                           if e.is_visible()]
                pruefe(bool(treffer) or "Valorisation Text" in form,
                       "Feld 'Valorisation Text' im Rechnungsformular vorhanden")
                schuss("05_%s_rechnung.png" % a.instanz)
            else:
                g = kw("account.move", "get_views", [[[False, "form"]], {}], context=CTX)
                pruefe("valorisierung_id" in g["views"]["form"]["arch"],
                       "Feld 'valorisierung_id' im Rechnungsformular-Arch")
            ctx.close()
    finally:
        if neu_id:
            kw(MODELL, "unlink", [neu_id])
        rest = kw(MODELL, "search", [[("name", "like", "ITK TEST S148")]],
                  context={"lang": "de_DE", "active_test": False})
        if rest:
            kw(MODELL, "unlink", [rest])
        nachher = kw(MODELL, "search_count", [[]],
                     context={"lang": "de_DE", "active_test": False})
        print("\nAufraeumen: Testsatz entfernt")
        print("Bestand: %d -> %d" % (soll, nachher))
        pruefe(nachher == soll, "Keine Testdaten zurueckgeblieben")

    print()
    print("--- Ergebnis Browserabnahme (%s) ---" % a.instanz)
    print("Pruefungen OK ..... %d" % ok)
    print("Fehlschlaege ...... %d" % fehler)
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
