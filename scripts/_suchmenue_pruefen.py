"""Liest im echten Browser die Filter- und Gruppierungsmenues einer Listenansicht.

Aufruf: python scripts/_suchmenue_pruefen.py vm|lokal [aktions_id] [bezeichnung]
"""
import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import lade_env  # noqa: E402

env = lade_env(r"C:/Odoo-Test/.env")
instanz = sys.argv[1] if len(sys.argv) > 1 else "vm"
url = "https://k001959vsx.ipax.at" if instanz == "vm" else "http://localhost:8069"
domain = "k001959vsx.ipax.at" if "k001959" in url else "localhost"
aktion = sys.argv[2] if len(sys.argv) > 2 else "330"
bez = sys.argv[3] if len(sys.argv) > 3 else "Zahlungen"

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(url + "/web/session/authenticate", data=json.dumps({
    "jsonrpc": "2.0", "method": "call",
    "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]}}).encode(),
    headers={"Content-Type": "application/json"}), timeout=60)
sid = next(c.value for c in jar if c.name == "session_id")

JS_OEFFNEN = """() => {
  const t = document.querySelector('.o_searchview_dropdown_toggler, .o_cp_searchview .dropdown-toggle, .o_searchview .dropdown-toggle');
  if (t) { t.click(); return true; } return false; }"""

JS_LESEN = """() => {
  const aus = [];
  for (const d of document.querySelectorAll('.dropdown-menu')) {
    if (!d.getClientRects().length) continue;
    const text = (d.innerText || '').replace(/\\s+/g, ' ').trim();
    aus.push(text.slice(0, 700));
  }
  return aus;
}"""

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    ktx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ["TEMP"], "pw_suche_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
    ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ktx.pages[0] if ktx.pages else ktx.new_page()
    s.goto("%s/odoo/action-%s" % (url, aktion))
    s.wait_for_timeout(9000)
    print("%s (Aktion %s, %s)" % (bez, aktion, instanz))
    try:
        print("   geoeffnet:", s.evaluate(JS_OEFFNEN))
        s.wait_for_timeout(2500)
        for block in s.evaluate(JS_LESEN):
            print("   MENUE: %s" % block)
    except Exception as fehler:
        print("   nicht lesbar: %s" % str(fehler)[:120])
    s.screenshot(path=r"C:/Users/anna.maierhofer/Desktop/Odoo18-Abnahme-Session122/rechnung/suchmenue_%s_%s.png"
                        % (bez.lower(), instanz), full_page=True)
    ktx.close()
