"""Diagnose: laedt das Zahlungsformular, zeigt Seiteninhalt und JS-Fehler."""
import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import lade_env  # noqa: E402

env = lade_env(r"C:/Odoo-Test/.env")
url = "https://k001959vsx.ipax.at" if sys.argv[1:2] == ["vm"] else "http://localhost:8069"
domain = "k001959vsx.ipax.at" if "k001959" in url else "localhost"
pid = sys.argv[2] if len(sys.argv) > 2 else "8"

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(url + "/web/session/authenticate", data=json.dumps({
    "jsonrpc": "2.0", "method": "call",
    "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]}}).encode(),
    headers={"Content-Type": "application/json"}), timeout=60)
sid = next(c.value for c in jar if c.name == "session_id")

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    ktx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ["TEMP"], "pw_diag_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
    ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ktx.pages[0] if ktx.pages else ktx.new_page()
    s.on("pageerror", lambda e: print("JS-FEHLER:", str(e)[:250]))
    s.goto("%s/web#id=%s&model=account.payment&view_type=form" % (url, pid))
    s.wait_for_timeout(15000)
    try:
        s.get_by_text("Technische Details ansehen").click(timeout=5000)
        s.wait_for_timeout(2500)
    except Exception as f:
        print("Details-Knopf nicht gefunden:", str(f)[:80])
    print("DIALOG:", s.evaluate("() => { const m = document.querySelector('.modal-body, .o_error_dialog'); return m ? (m.innerText || '').slice(-1200) : 'kein Dialog'; }"))
    pfad = r"C:/Users/anna.maierhofer/Desktop/Odoo18-Abnahme-Session122/rechnung/zahlung_diagnose.png"
    s.screenshot(path=pfad)
    print("SCREENSHOT:", pfad)
    ktx.close()
