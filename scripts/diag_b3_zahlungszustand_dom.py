"""Diagnose: wie zeigt Odoo 18 den Zahlungszustand im Rechnungsformular (VM)?"""
from __future__ import annotations
import http.cookiejar, json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env
env = lade_env()
URL = "https://k001959vsx.ipax.at"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def rufe(p, prm):
    req = urllib.request.Request(URL+p, data=json.dumps({"jsonrpc":"2.0","method":"call","params":prm}).encode(),
                                 headers={"Content-Type":"application/json"})
    return json.loads(op.open(req, timeout=120).read().decode())
rufe("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]})
sid = next(c.value for c in jar if c.name == "session_id")
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(user_data_dir=os.path.join(os.environ["TEMP"], "pw_b3_diag_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1800, "height": 1300})
    ctx.add_cookies([{"name":"session_id","value":sid,"domain":"k001959vsx.ipax.at","path":"/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    s.goto(URL + "/odoo/m-account.move/41"); s.wait_for_selector(".o_form_view", timeout=90000); s.wait_for_timeout(5000)
    print("Elemente mit 'Bezahlt':")
    for e in s.evaluate("""() => [...document.querySelectorAll('*')]
        .filter(e => e.children.length === 0 && /Bezahlt|Teilweise|Zahlung/.test(e.innerText || ''))
        .slice(0, 12)
        .map(e => ({tag: e.tagName, klasse: e.className, text: e.innerText.trim().slice(0,40),
                    eltern: e.parentElement ? e.parentElement.className.slice(0,60) : ''}))"""):
        print("   ", e)
    print("\npayment_state-Elemente:")
    for e in s.evaluate("""() => [...document.querySelectorAll('[name="payment_state"], .o_field_widget[name="payment_state"]')]
        .map(e => ({tag: e.tagName, klasse: e.className, text: e.innerText.trim().slice(0,40),
                    kinder: e.children.length}))"""):
        print("   ", e)
    print("\nKopfbereich der Seite (Text):", s.evaluate("() => document.querySelector('.o_form_view').innerText.replace(/\n+/g,' | ').slice(0, 400)"))
    ctx.close()
