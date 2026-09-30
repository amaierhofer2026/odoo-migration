"""Diagnose: DOM des Rechnungsformulars (VM) - Smart Buttons und Drucken-Menue."""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env

env = lade_env()
url = "https://k001959vsx.ipax.at"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def rufe(pfad, prm):
    req = urllib.request.Request(url + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                              "params": prm}).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(op.open(req, timeout=180).read().decode())


rufe("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                   "password": env["ODOO18_PWD"]})
sid = next(c.value for c in jar if c.name == "session_id")


def kw(model, methode, args, **kwargs):
    o = rufe("/web/dataset/call_kw", {"model": model, "method": methode, "args": args, "kwargs": kwargs})
    if "error" in o:
        raise RuntimeError(str(o["error"])[:200])
    return o.get("result")


belege = kw("account.move", "search_read",
            [[("move_type", "=", "out_invoice"), ("state", "=", "posted")],
             ["id", "name", "payment_count", "payment_state", "sale_order_count", "transaction_count"]],
            order="id desc", limit=3)
for b in belege:
    print(b)

from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ["TEMP"], "pw_diag_rechnung"),
        channel="chrome", headless=True, viewport={"width": 1800, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": "k001959vsx.ipax.at", "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()
    seite.goto("%s/odoo/m-account.move/%s" % (url, belege[0]["id"]))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(4000)
    print("\n--- alle oe_stat_button ---")
    print(seite.evaluate("""() => [...document.querySelectorAll('.oe_stat_button')].map(e => ({
        text: e.innerText.replace(/\\s+/g,' ').trim(), sichtbar: e.getClientRects().length > 0 }))"""))
    print("\n--- Button-Box Container ---")
    print(seite.evaluate("""() => [...document.querySelectorAll('.oe_button_box, [name="button_box"]')]
        .map(e => e.className + ' | sichtbar=' + (e.getClientRects().length>0) + ' | ' + e.innerText.replace(/\\s+/g,' ').trim().slice(0,120))"""))
    print("\n--- Klick auf Drucken ---")
    for el in seite.query_selector_all("button"):
        if el.is_visible() and el.inner_text().strip() == "Drucken":
            el.click()
            break
    seite.wait_for_timeout(3000)
    print("Dropdowns:", seite.evaluate("""() => [...document.querySelectorAll('.o-dropdown--menu, .dropdown-menu')]
        .filter(e => e.getClientRects().length).map(e => e.innerText.replace(/\\s+/g,' ').trim().slice(0,200))"""))
    print("Dialoge  :", seite.evaluate("""() => [...document.querySelectorAll('.modal, .o_dialog')]
        .filter(e => e.getClientRects().length).map(e => e.innerText.replace(/\\s+/g,' ').trim().slice(0,300))"""))
    print("Titel    :", seite.evaluate("""() => [...document.querySelectorAll('.modal-title, .o_dialog .modal-header')]
        .map(e => e.innerText.trim()).slice(0,3)"""))
    ctx.close()
