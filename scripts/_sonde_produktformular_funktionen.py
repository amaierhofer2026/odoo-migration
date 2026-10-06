"""Sonde: DOM-Details fuer die Funktionspruefung (Smart Buttons, Radios, Notizen).

Aufruf: python scripts/_sonde_produktformular_funktionen.py lokal|vm [produkt_id]
"""
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            w[k.strip()] = v.strip().strip('"')
    return w


inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
env = lade_env(os.path.join(REPO, ".env"))
url = "http://localhost:8069" if inst != "vm" else "https://k001959vsx.ipax.at"
domain = "localhost" if inst != "vm" else "k001959vsx.ipax.at"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(url + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
            "db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
            "password": env["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"}))
sid = next(c.value for c in jar if c.name == "session_id")

pid = int(sys.argv[2]) if len(sys.argv) > 2 else 3

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_sonde_fun_%s" % inst),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1500})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    s.goto("%s/odoo/action-382/%s" % (url, pid))
    s.wait_for_selector(".o_form_view", timeout=90000)
    s.wait_for_timeout(6000)
    print("Smart Buttons:", s.evaluate("""() => [...document.querySelectorAll('.oe_stat_button, .o_stat_button')]
        .map(b => b.innerText.replace(/\\s+/g,' ').trim())"""))
    print("Kopfknopfbereich:", s.evaluate("""() => [...document.querySelectorAll('.o_form_statusbar button, .o_control_panel button')]
        .map(b => b.innerText.replace(/\\s+/g,' ').trim()).filter(Boolean)"""))
    s.query_selector(".o_notebook .nav-link:has-text('Abrechnung')").click()
    s.wait_for_timeout(1500)
    print("\ninvoice_policy:")
    print(s.evaluate("""() => [...document.querySelectorAll("[name='invoice_policy']")]
        .map(e => e.tagName + ' ' + e.className.slice(0,40) + ' :: ' +
                  (e.outerHTML||'').replace(/\\s+/g,' ').slice(0, 260))"""))
    print("purchase_method:", s.evaluate("""() => [...document.querySelectorAll("[name='purchase_method']")]
        .map(e => e.tagName + ' ' + e.className.slice(0,30) + ' :: ' +
                  (e.outerHTML||'').replace(/\\s+/g,' ').slice(0,200))"""))
    s.query_selector(".o_notebook .nav-link:has-text('Notizen')").click()
    s.wait_for_timeout(1500)
    print("\ndescription-Treffer:", s.evaluate("""() => [...document.querySelectorAll("[name='description']")]
        .map(e => e.tagName + ' ' + e.className.slice(0,50) + ' sichtbar=' + !!e.offsetParent +
                  ' :: ' + (e.outerHTML||'').replace(/\\s+/g,' ').slice(0, 200))"""))
    print("Gruppen im Reiter Notizen:", s.evaluate("""() => [...document.querySelectorAll('.o_group, .o_group_name')]
        .map(e => e.tagName + '.' + e.className.slice(0,26) + ' name=' + (e.getAttribute('name')||'-') +
                  ' text=' + (e.innerText||'').replace(/\\s+/g,' ').slice(0,30))"""))
    ctx.close()
