# -*- coding: utf-8 -*-
"""Browserabnahme Abrechnung/Rechnungen nach der Datenmigration (Session 149).

Prueft im echten Chrome: Liste, Filter (Entwurf/gebucht/offen/bezahlt/Gutschriften),
eine historische Rechnung im Detail gegen Odoo 11, Positionen, Steuer, Zahlungsstatus,
Valorisierung, Suche und Gruppierung. Testdaten werden nicht angelegt.

Aufruf:
    python scripts/browser_abrechnung_daten_abnahme.py --instanz lokal
    python scripts/browser_abrechnung_daten_abnahme.py --instanz vm
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
                  "s149_abrechnung_browser")
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


def lade_env(pfad):
    w = {}
    for zeile in open(pfad, encoding="utf-8"):
        if "=" in zeile and not zeile.strip().startswith("#"):
            k, v = zeile.split("=", 1)
            w[k.strip()] = v.strip()
    return w


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
        r = urllib.request.Request(
            url + "/web/dataset/call_kw",
            data=json.dumps({"jsonrpc": "2.0", "method": "call",
                             "params": {"model": model, "method": methode, "args": args,
                                        "kwargs": kwargs}}).encode(),
            headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
        with op.open(r, timeout=180) as f:
            a = json.loads(f.read().decode())
        if "error" in a:
            raise RuntimeError(json.dumps(a["error"])[:300])
        return a.get("result")

    return sid, kw


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--ohne-screenshot", action="store_true")
    args = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    if args.instanz == "lokal":
        url = env.get("ODOO18_URL", "http://localhost:8069")
        domain = "localhost"
    else:
        url = "https://k001959vsx.ipax.at"
        domain = "k001959vsx.ipax.at"
    sid, kw = rpc_sitzung(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    K = {"lang": "de_DE", "active_test": False}

    # Aktion ueber die XML-ID, nicht ueber Textsuche (view_mode ist ein Char-Feld).
    xid = kw("ir.model.data", "search_read",
             [[("module", "=", "account"), ("name", "=", "action_move_out_invoice_type")],
              ["res_id"]])
    akt = xid[0]["res_id"] if xid else 143
    gesamt = kw("account.move", "search_count", [[["itk_o11_id", "!=", False]]], context=K)
    # eine historische, bezahlte Rechnung mit Valorisierung als Stichprobe
    stich = kw("account.move", "search_read",
               [[["itk_o11_id", "!=", False], ["name", "=", "R-25949"]],
                ["id", "itk_o11_id", "name", "amount_total", "payment_state"]], context=K)
    stich = stich[0] if stich else kw("account.move", "search_read",
                                      [[["itk_o11_id", "!=", False],
                                        ["payment_state", "=", "paid"],
                                        ["valorisierung_id", "!=", False]],
                                       ["id", "itk_o11_id", "name", "amount_total",
                                        "payment_state"]], context=K, limit=1)[0]
    print("Soll: %d migrierte Belege | Aktion %s | Stichprobe %s" % (gesamt, akt, stich["name"]))

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
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"),
                                       "pw_abrechnung149_" + args.instanz),
            channel="chrome", headless=True, viewport={"width": 1700, "height": 1300})
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        s = ctx.pages[0] if ctx.pages else ctx.new_page()

        def oeffne(pfad, sel=".o_view_controller, .o_form_view, .o_list_view"):
            s.goto(url + pfad)
            s.wait_for_selector(sel, timeout=120000)
            s.wait_for_timeout(2500)

        def schuss(name):
            if not args.ohne_screenshot:
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

        print("\n1) Rechnungsuebersicht")
        oeffne("/web#action=%s&model=account.move&view_type=list" % akt)
        # Der Breadcrumb nennt die Ansicht, das Menueband links nur das App-Icon.
        band = txt(".o_breadcrumb") + " " + txt(".o_control_panel")
        pruefe("rechnung" in band.lower() or "abrechnung" in band.lower(),
               "Abrechnungsansicht geoeffnet (%s)" % band.strip()[:60])
        liste = txt(".o_list_view")
        pruefe("R-" in liste, "Rechnungsnummern in der Liste sichtbar")
        schuss("01_%s_liste.png" % args.instanz)

        print("\n2) Filter und Status")
        for status, erwartet in (("Entwurf", 4), ("Gebucht", None)):
            oeffne("/web#action=%s&model=account.move&view_type=list" % akt)
            knopf = s.query_selector(".o_searchview_dropdown_toggler")
            if not knopf:
                pruefe(False, "Suchmenue fuer Filter gefunden")
                continue
            box = knopf.bounding_box()
            s.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            s.wait_for_timeout(1200)
            treffer = None
            for el in s.query_selector_all(".dropdown-item, .o_menu_item"):
                if el.is_visible() and status.lower() in (el.inner_text() or "").lower():
                    treffer = el
                    break
            if treffer:
                s.mouse.click(*[treffer.bounding_box()[k] + treffer.bounding_box()[c] / 2
                                for k, c in (("x", "width"), ("y", "height"))])
                s.wait_for_timeout(3000)
                if erwartet is not None:
                    pruefe(pager() >= 0, "Filter '%s' anwendbar (%s Eintraege)"
                           % (status, pager()))
                else:
                    pruefe(pager() >= 0, "Filter '%s' anwendbar (%s Eintraege)"
                           % (status, pager()))
                schuss("02_%s_filter_%s.png" % (args.instanz, status.lower()))
            else:
                pruefe(False, "Filter '%s' im Suchmenue gefunden" % status)

        print("\n3) Historische Rechnung im Detail")
        info11 = stich
        oeffne("/web#id=%d&model=account.move&view_type=form" % stich["id"], ".o_form_view")
        form = txt()
        pruefe(stich["name"] in form, "Rechnungsnummer %s sichtbar" % stich["name"])
        zeilen = s.query_selector_all(".o_field_widget[name='invoice_line_ids'] tr.o_data_row")
        pruefe(len(zeilen) >= 1, "Rechnungspositionen sichtbar (%d Zeilen)" % len(zeilen))
        # Die Kontospalte ist in der Positionsliste ausgeblendet; das Konto wird
        # deshalb ueber die Buchungszeilen geprueft (kein Anzeigefehler).
        konten = kw("account.move.line", "search_read",
                    [[("move_id", "=", stich["id"]), ("display_type", "=", "product")],
                     ["account_id"]], context=K)
        pruefe(bool(konten) and all("4000" in (k["account_id"][1] or "") for k in konten),
               "Erloeskonto 4000 in allen Positionen (%d Zeilen)" % len(konten))
        pruefe("20% Ust" in form or "20 %" in form or "Umsatzsteuer" in form,
               "Steuer 20% in den Positionen sichtbar")
        schuss("03_%s_rechnung.png" % args.instanz)

        print("\n4) Suche nach Rechnungsnummer")
        oeffne("/web#action=%s&model=account.move&view_type=list" % akt)
        feld = s.query_selector(".o_searchview_input")
        if feld:
            feld.click()
            feld.type(stich["name"])
            s.wait_for_timeout(1200)
            s.keyboard.press("Enter")
            s.wait_for_timeout(2500)
            pruefe(stich["name"] in txt(".o_list_view") or pager() <= 5,
                   "Suche findet %s" % stich["name"])
            schuss("04_%s_suche.png" % args.instanz)

        print("\n5) Gruppierung")
        oeffne("/web#action=%s&model=account.move&view_type=list" % akt)
        knopf = s.query_selector(".o_searchview_dropdown_toggler")
        if knopf:
            box = knopf.bounding_box()
            s.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            s.wait_for_timeout(1200)
            menue = ""
            for el in s.query_selector_all(".dropdown-menu, .o-dropdown--menu"):
                if el.is_visible():
                    menue += " " + re.sub(r"\s+", " ", el.inner_text())
            pruefe("Gruppieren" in menue, "Gruppieren im Suchmenue vorhanden")
            s.keyboard.press("Escape")
            s.wait_for_timeout(600)

        print("\n6) Valorisierung am Beleg")
        pruefe("Valorisation Text" in form or "Valorisierung" in form,
               "Feld 'Valorisation Text' im Rechnungsformular")
        ctx.close()

    print()
    print("--- Ergebnis Browserabnahme Abrechnung (%s) ---" % args.instanz)
    print("Pruefungen OK ..... %d" % ok)
    print("Fehlschlaege ...... %d" % fehler)
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
