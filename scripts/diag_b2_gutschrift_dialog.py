"""Diagnose B2: Beschriftungen und Felder des Gutschrift-Dialogs (Odoo 18, VM/read-only)."""
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
    return json.loads(op.open(req, timeout=120).read().decode())


rufe("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                   "password": env["ODOO18_PWD"]})
sid = next(c.value for c in jar if c.name == "session_id")

from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ["TEMP"], "pw_b2_lab_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1600, "height": 1200})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": "k001959vsx.ipax.at", "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    s.goto(URL + "/odoo/m-account.move/28")
    s.wait_for_selector(".o_form_view", timeout=90000)
    s.wait_for_timeout(4000)
    for el in s.query_selector_all("button"):
        if el.is_visible() and el.inner_text().strip() == "Gutschrift":
            el.click()
            break
    s.wait_for_selector(".o_dialog", state="attached", timeout=60000)
    s.wait_for_timeout(3000)
    print("Dialog-Text:")
    print("  " + s.evaluate("() => document.querySelector('.o_dialog').innerText.replace(/\\n+/g, ' | ')"))
    print("\nLabels der Reihe nach:")
    for l in s.evaluate("""() => [...document.querySelectorAll('.o_dialog label')]
        .map(e => e.innerText.trim() + '  (for=' + (e.getAttribute('for') || '-') + ')')"""):
        print("   ", l)
    print("\nFelder im Dialog:")
    for f in s.evaluate("""() => [...document.querySelectorAll('.o_dialog .o_field_widget')]
        .map(e => e.getAttribute('name') + ' [' + (e.className.match(/o_field_[a-z_]+/) || [''])[0] + ']')"""):
        print("   ", f)
    s.keyboard.press("Escape")
    s.wait_for_timeout(1500)
    ctx.close()
