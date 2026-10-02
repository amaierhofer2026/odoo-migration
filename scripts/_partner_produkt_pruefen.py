"""Browserpruefung Kunden/Lieferanten und Produkte (lokal und VM).

Aufruf: python scripts/_partner_produkt_pruefen.py vm|lokal
"""
import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import lade_env  # noqa: E402

env = lade_env(r"C:/Odoo-Test/.env")
instanz = sys.argv[1] if len(sys.argv) > 1 else "lokal"
url = "https://k001959vsx.ipax.at" if instanz == "vm" else "http://localhost:8069"
domain = "k001959vsx.ipax.at" if "k001959" in url else "localhost"
CTX = {"lang": "de_DE"}

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(url + "/web/session/authenticate", data=json.dumps({
    "jsonrpc": "2.0", "method": "call",
    "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]}}).encode(),
    headers={"Content-Type": "application/json"}), timeout=60)
sid = next(c.value for c in jar if c.name == "session_id")


def kw(model, method, args, context=None):
    daten = {"jsonrpc": "2.0", "method": "call",
             "params": {"model": model, "method": method, "args": args, "kwargs": {"context": context or CTX}}}
    req = urllib.request.Request(url + "/web/dataset/call_kw", data=json.dumps(daten).encode(),
                                 headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
    antwort = json.loads(op.open(req, timeout=180).read().decode())
    if "error" in antwort:
        raise RuntimeError(str(antwort["error"])[:250])
    return antwort["result"]


partner = kw("res.partner", "search_read", [[["customer_rank", ">", 0]], ["id", "name", "display_name"]])[:1]
produkt = kw("product.template", "search_read", [[["sale_ok", "=", True]], ["id", "name"]])[:1]
print("Partner:", partner)
print("Produkt:", produkt)

JS = """
() => {
  const sichtbar = (e) => !!e.getClientRects().length;
  return {
    reiter: [...document.querySelectorAll('.o_notebook .nav-link')].filter(sichtbar).map(e => (e.textContent||'').trim()),
    labels: [...document.querySelectorAll('.o_form_sheet label.o_form_label')].filter(sichtbar).map(e => (e.textContent||'').trim()).filter(t => t),
    smart: [...document.querySelectorAll('.oe_stat_button')].filter(sichtbar).map(e => (e.textContent||'').trim()),
    buttons: [...document.querySelectorAll('.o_form_statusbar button, .o_cp_buttons .btn')].filter(sichtbar).map(e => (e.textContent||'').trim()).filter(t => t),
  };
}
"""

from playwright.sync_api import sync_playwright  # noqa: E402

vz = r"C:/Users/anna.maierhofer/Desktop/Odoo18-Abnahme-Session122/rechnung"
with sync_playwright() as pw:
    ktx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ["TEMP"], "pw_pp2_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
    ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ktx.pages[0] if ktx.pages else ktx.new_page()
    for modell, rec, name in (("res.partner", partner[0]["id"] if partner else 1, "partner"),
                              ("product.template", produkt[0]["id"] if produkt else None, "produkt")):
        if not rec:
            continue
        s.goto("%s/web#id=%s&model=%s&view_type=form" % (url, rec, modell))
        s.wait_for_timeout(9000)
        d = s.evaluate(JS)
        print("### %s id %s (%s)" % (modell, rec, instanz))
        print("   Reiter:", d["reiter"])
        print("   Beschriftungen:", sorted(set(d["labels"]))[:26])
        print("   SmartButtons:", d["smart"][:12])
        s.screenshot(path="%s/%s_%s.png" % (vz, name, instanz), full_page=True)
    ktx.close()
