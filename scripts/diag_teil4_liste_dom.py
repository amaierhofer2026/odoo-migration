"""Diagnose Teil 4: Suchleiste und Aktionsmenue der Rechnungsliste (VM)."""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env

env = lade_env()
URL = "https://k001959vsx.ipax.at"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def rufe(pfad, prm):
    req = urllib.request.Request(URL + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                             "params": prm}).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(op.open(req, timeout=180).read().decode())


rufe("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                   "password": env["ODOO18_PWD"]})
sid = next(c.value for c in jar if c.name == "session_id")

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ["TEMP"], "pw_teil4_diag_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1300})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": "k001959vsx.ipax.at", "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    s.goto(URL + "/odoo/action-354")
    s.wait_for_selector(".o_list_view, .o_list_renderer", timeout=90000)
    s.wait_for_timeout(5000)
    print("Knopfleiste der Suche:")
    for e in s.evaluate("""() => [...document.querySelectorAll('.o_control_panel button, .o_cp_searchview button')]
        .filter(e => e.getClientRects().length)
        .map(e => ({text: e.innerText.trim().slice(0,30), klasse: e.className.slice(0,60)}))"""):
        print("   ", e)
    print("\nZeilen auswaehlen ...")
    kb = s.query_selector(".o_list_view thead input[type=checkbox], .o_list_renderer thead input[type=checkbox]")
    print("   Kopf-Checkbox:", bool(kb))
    if kb:
        kb.click()
        s.wait_for_timeout(2500)
    print("\nAktionsmenue-Knoepfe:")
    for e in s.evaluate("""() => [...document.querySelectorAll('.o_cp_action_menus button, .o_control_panel .o_cp_action_menus button')]
        .filter(e => e.getClientRects().length)
        .map(e => ({text: e.innerText.trim().slice(0,30), klasse: e.className.slice(0,70)}))"""):
        print("   ", e)
    for el in s.query_selector_all("button"):
        if el.is_visible() and (el.inner_text() or "").strip().startswith("Aktionen"):
            el.click()
            break
    s.wait_for_timeout(2500)
    print("\nMenue-Eintraege (erste Ebene):")
    for e in s.evaluate("""() => [...document.querySelectorAll('.o-dropdown--menu .dropdown-item, .o-dropdown--menu .o_menu_item, .dropdown-menu > *')]
        .filter(e => e.getClientRects().length)
        .map(e => e.innerText.replace(/\\s+/g,' ').trim().slice(0,60))"""):
        print("   ", e)
    print("\nAnzahl Eintraege:", s.evaluate("""() => document.querySelectorAll('.o-dropdown--menu .dropdown-item, .o-dropdown--menu .o_menu_item').length"""))
    s.screenshot(path=os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "teil4", "diag_liste.png"), full_page=True)
    ctx.close()
