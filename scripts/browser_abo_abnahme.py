"""Browser-Abnahme Abonnement auf der VM: Liste und Formular mit Screenshots.

Aufruf: python scripts/browser_abo_abnahme.py vm|local
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


def kw(model, method, args, **kwargs):
    daten = {"jsonrpc": "2.0", "method": "call", "params": {
        "model": model, "method": method, "args": args,
        "kwargs": {"context": kwargs.get("context", {"lang": "de_DE"})}}}
    req = urllib.request.Request(url + "/web/dataset/call_kw", data=json.dumps(daten).encode(),
                                 headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
    antwort = json.loads(op.open(req, timeout=180).read().decode())
    if "error" in antwort:
        raise RuntimeError(str(antwort["error"])[:200])
    return antwort["result"]


abo = kw("sale.subscription", "search", [[("state", "=", "open")]], limit=1)
abo_id = abo[0] if abo else kw("sale.subscription", "search", [[]], limit=1)[0]
print("Abonnement id=%s" % abo_id)

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_abo_%s_%s" % (instanz, os.getpid())),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()

    def texte(sel):
        return s.evaluate("""(q) => [...document.querySelectorAll(q)].filter(e => e.getClientRects().length)
            .map(e => (e.textContent||'').trim()).filter(t => t)""", sel)

    # Liste
    s.goto("%s/odoo/action-1105" % url)
    s.wait_for_selector(".o_list_renderer", timeout=120000)
    s.wait_for_timeout(4000)
    spalten = s.evaluate("""() => [...document.querySelectorAll('thead th')].map(e => e.textContent.trim()).filter(t => t)""")
    print("LISTE Spalten:", spalten)
    pfad = os.path.join(VZ, "abo_liste_%s.png" % instanz)
    s.screenshot(path=pfad, full_page=False)
    print("Screenshot:", pfad)

    # Formular
    s.goto("%s/web#id=%s&model=sale.subscription&view_type=form" % (url, abo_id))
    s.wait_for_selector(".o_form_view", timeout=90000)
    s.wait_for_timeout(5000)
    knoepfe = texte(".o_form_statusbar button, .o_control_panel button")
    status = texte(".o_statusbar_status button")
    labels = texte(".o_inner_group label, .o_group label, .o_form_label")
    print("FORMULAR Buttons:", sorted(set(knoepfe)))
    print("FORMULAR Status:", status)
    print("FORMULAR Labels:", sorted(set(labels)))
    pfad = os.path.join(VZ, "abo_formular_%s.png" % instanz)
    s.screenshot(path=pfad, full_page=False)
    print("Screenshot:", pfad)

    # Reiter Wiederkehrende Buchungen
    s.evaluate("""() => { const t = [...document.querySelectorAll('.o_notebook .nav-link')]
        .find(e => (e.textContent||'').includes('Wiederkehrende')); if (t) t.click(); }""")
    s.wait_for_timeout(3500)
    zeilen_labels = texte(".o_field_x2many .o_list_table thead th")
    print("ZEILEN Spalten:", zeilen_labels)
    pfad = os.path.join(VZ, "abo_zeilen_%s.png" % instanz)
    s.screenshot(path=pfad, full_page=False)
    print("Screenshot:", pfad)
    ctx.close()
