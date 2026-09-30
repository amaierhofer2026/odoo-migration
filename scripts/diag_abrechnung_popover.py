"""Diagnose: DOM des Berichtswesen-Popovers auf der VM (read-only)."""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o18

env = lade_env()
url = "https://k001959vsx.ipax.at"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
req = urllib.request.Request(url + "/web/session/authenticate",
                            data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                             "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                                        "password": env["ODOO18_PWD"]}}).encode(),
                            headers={"Content-Type": "application/json"})
op.open(req).read()
sid = next(c.value for c in jar if c.name == "session_id")

from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ["TEMP"], "pw_diag_abrechnung"),
        channel="chrome", headless=True, viewport={"width": 1800, "height": 1300})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": "k001959vsx.ipax.at", "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()
    seite.goto(url + "/web#menu_id=193")
    seite.wait_for_selector(".o_main_navbar", timeout=90000)
    seite.wait_for_timeout(4000)
    kn = seite.query_selector_all(".o_main_navbar .o_menu_sections button, .o_main_navbar .o_menu_sections a")
    for k in kn:
        if k.inner_text().strip() == "Berichtswesen":
            k.click()
            break
    seite.wait_for_timeout(1500)
    print("--- Popover-Struktur ---")
    print(seite.evaluate("""() => {
        const boxen = [...document.querySelectorAll('.o-dropdown--menu.dropdown-menu')]
            .filter(e => e.getClientRects().length);
        const box = boxen[boxen.length - 1];
        if (!box) return 'kein Popover';
        return [...box.querySelectorAll('*')].filter(e => e.children.length === 0)
            .map(e => e.className + ' :: ' + e.innerText.trim()).join('\\n');
    }""")[:3000])
    print("\n--- Alle Elemente mit 'Audit'/'Pruefpfad' im Text (ganze Seite) ---")
    print(seite.evaluate("""() => [...document.querySelectorAll('*')]
        .filter(e => e.children.length === 0 && /Prüfpfad|Audit/.test(e.innerText || ''))
        .map(e => e.tagName + '.' + e.className + ' :: ' + e.innerText.trim()).slice(0, 10)"""))
    ctx.close()
