"""Browser-Pruefung der drei uebrigen Abonnement-Menuepunkte auf der VM.

Aufruf: python scripts/browser_abo_menues.py vm|local
"""
import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import lade_env  # noqa: E402

instanz = sys.argv[1] if len(sys.argv) > 1 else "vm"
url = "https://k001959vsx.ipax.at" if instanz == "vm" else "http://localhost:8069"
domain = "k001959vsx.ipax.at" if instanz == "vm" else "localhost"
env = lade_env(r"C:/Odoo-Test/.env")
VZ = r"C:/Users/anna.maierhofer/Desktop/Odoo18-Abnahme-Session122/abonnement"
os.makedirs(VZ, exist_ok=True)

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(url + "/web/session/authenticate", data=json.dumps({
    "jsonrpc": "2.0", "method": "call",
    "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]}}).encode(),
    headers={"Content-Type": "application/json"}), timeout=120)
sid = next(c.value for c in jar if c.name == "session_id")

from playwright.sync_api import sync_playwright  # noqa: E402

SEITEN = [("Abonnement Produkte", "action-1102"), ("Zu erneuernde Abonnements", "action-1107"),
          ("Vorlagen fuer Abonnements", "action-1110")]

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_abom_%s_%s" % (instanz, os.getpid())),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1200}, locale="de-DE")
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    for titel, pfad in SEITEN:
        s.goto("%s/odoo/%s" % (url, pfad))
        try:
            s.wait_for_selector(".o_list_renderer, .o_kanban_renderer", timeout=90000)
        except Exception:
            print("%s: keine Liste geladen" % titel)
            continue
        s.wait_for_timeout(4000)
        spalten = s.evaluate("""() => [...document.querySelectorAll('thead th')].map(e => e.textContent.trim()).filter(t => t)""")
        gruppen = s.evaluate("""() => [...document.querySelectorAll('.o_group_header, .o_kanban_record')].slice(0,3)
            .map(e => (e.textContent||'').trim().slice(0,60))""")
        zaehler = s.evaluate("""() => { const e = document.querySelector('.o_pager_counter, .o_control_panel .o_pager'); return e ? e.textContent.trim() : ''; }""")
        print("%s | Spalten: %s | Pager: %s" % (titel, spalten, zaehler))
        print("     Zeilen/Karten: %s" % gruppen)
        bild = os.path.join(VZ, "abo_%s_%s.png" % (pfad.replace("action-", "aktion"), instanz))
        s.screenshot(path=bild)
        print("     Screenshot: %s" % bild)
    ctx.close()
