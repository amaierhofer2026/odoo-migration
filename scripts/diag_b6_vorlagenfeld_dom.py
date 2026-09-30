"""Diagnose B6: Vorlagenfeld im Massenversand-Dialog der VM (DOM)."""
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
        user_data_dir=os.path.join(os.environ["TEMP"], "pw_b6_diag_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1800, "height": 1300})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": "k001959vsx.ipax.at", "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    s.goto(URL + "/odoo/m-account.move/46")
    s.wait_for_selector(".o_form_view", timeout=90000)
    s.wait_for_timeout(4000)
    for el in s.query_selector_all(".o_cp_action_menus button"):
        if el.is_visible():
            el.click()
            break
    s.wait_for_timeout(2000)
    for el in s.query_selector_all(".dropdown-item"):
        if el.is_visible() and "Massenversand" in (el.inner_text() or ""):
            el.click()
            break
    s.wait_for_timeout(6000)
    print("Dialogfelder:")
    for f in s.evaluate("""() => [...document.querySelectorAll('.o_dialog .o_field_widget')]
        .map(e => e.getAttribute('name') + ' | ' + (e.className.match(/o_field_[a-z_]+/) || [''])[0])"""):
        print("   ", f)
    print("\nDialogtext:", s.evaluate("() => (document.querySelector('.o_dialog')||{}).innerText ? document.querySelector('.o_dialog').innerText.replace(/\\s+/g,' ').slice(0,400) : 'kein Dialog'"))
    feld = s.query_selector(".o_dialog .o_field_widget[name='template_id']")
    print("\nVorlagenfeld vorhanden:", bool(feld))
    if feld:
        print("HTML:", (feld.inner_html() or "")[:300].replace("\n", " "))
        try:
            feld.click()
            s.wait_for_timeout(2500)
            print("Optionen:", s.evaluate("""() => [...document.querySelectorAll('.o-autocomplete--dropdown-item, .dropdown-menu .dropdown-item')]
                .filter(e => e.getClientRects().length).map(e => e.innerText.trim()).slice(0, 20)"""))
        except Exception as f:
            print("Klick fehlgeschlagen:", str(f)[:80])
    s.screenshot(path=os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "b6", "diag_dialog.png"), full_page=True)
    ctx.close()
