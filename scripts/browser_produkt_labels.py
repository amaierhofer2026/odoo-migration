"""Browser-Pruefung der Produkt-Beschriftungen auf der VM.

Aufruf: python scripts/browser_produkt_labels.py vm|local
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
VZ = r"C:/Users/anna.maierhofer/Desktop/Odoo18-Abnahme-Session122/produkte"
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


produkt = kw("product.template", "search", [[("sale_ok", "=", True)]], limit=1)
pid = produkt[0]
print("Produkt id=%s" % pid)

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_prod_%s_%s" % (instanz, os.getpid())),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()

    def texte(sel):
        return s.evaluate("""(q) => [...document.querySelectorAll(q)].filter(e => e.getClientRects().length)
            .map(e => (e.textContent||'').trim()).filter(t => t)""", sel)

    # Liste der verkaufbaren Produkte
    s.goto("%s/odoo/action-382" % url)
    s.wait_for_selector(".o_list_renderer, .o_kanban_renderer", timeout=120000)
    s.wait_for_timeout(4000)
    spalten = s.evaluate("""() => [...document.querySelectorAll('thead th')].map(e => e.textContent.trim()).filter(t => t)""")
    print("LISTE Spalten:", spalten)
    suche = texte(".o_searchview_input_container, .o_searchview")
    print("Suchleiste:", suche)
    bild = os.path.join(VZ, "produkt_liste_%s.png" % instanz)
    s.screenshot(path=bild)
    print("Screenshot:", bild)

    # Formular oeffnen
    s.goto("%s/web#id=%s&model=product.template&view_type=form" % (url, pid))
    s.wait_for_selector(".o_form_view", timeout=90000)
    s.wait_for_timeout(5000)
    labels = texte(".o_inner_group label, .o_group label, .o_form_label")
    reiter = s.evaluate("""() => [...document.querySelectorAll('.o_notebook .nav-link')].map(e => e.textContent.trim())""")
    print("FORMULAR Labels:", sorted(set(labels)))
    print("FORMULAR Reiter:", reiter)
    bild = os.path.join(VZ, "produkt_formular_%s.png" % instanz)
    s.screenshot(path=bild)
    print("Screenshot:", bild)

    # Filter der Produktsuche oeffnen
    try:
        s.goto("%s/odoo/action-382" % url)
        s.wait_for_selector(".o_list_renderer, .o_kanban_renderer", timeout=60000)
        s.wait_for_timeout(3000)
        s.click(".o_searchview_dropdown_toggler, .o_cp_searchview .dropdown-toggle")
        s.wait_for_timeout(2500)
        filtertexte = texte(".o_filter_menu .dropdown-item, .o_menu_item")
        print("FILTER/Gruppierungen:", sorted(set(filtertexte))[:20])
        bild = os.path.join(VZ, "produkt_filter_%s.png" % instanz)
        s.screenshot(path=bild)
        print("Screenshot:", bild)
    except Exception as f:
        print("Filtermenue nicht lesbar:", str(f)[:120])
    ctx.close()
