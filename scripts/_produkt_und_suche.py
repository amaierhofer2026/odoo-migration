"""Prueft (a) die Reiter eines Lagerprodukts im Browser und (b) Suchansichten der Buchhaltungsmodelle.

Aufruf: python scripts/_produkt_und_suche.py vm|lokal
"""
import http.cookiejar
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import lade_env  # noqa: E402

env = lade_env(r"C:/Odoo-Test/.env")
instanz = sys.argv[1] if len(sys.argv) > 1 else "vm"
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
        raise RuntimeError(str(antwort["error"])[:200])
    return antwort["result"]


# --- (b) Suchansichten (autoritativ aus der View, nicht aus dem Browser)
print("=== Suchansichten (Filter und Gruppierungen) ===")
for modell in ("account.move", "account.payment", "res.partner", "product.template",
               "account.tax", "account.journal", "account.payment.term", "account.analytic.account"):
    try:
        gv = kw(modell, "get_views", [[[False, "search"]]])
        arch = list((gv.get("views") or {}).values())[0]["arch"]
        w = ET.fromstring(arch)
        filter_ = [f.get("name") for f in w.iter("filter")]
        gruppen = [f.get("name") for f in w.iter("filter") if (f.get("context") or "").find("group_by") >= 0]
        felder = [f.get("name") for f in w.iter("field")]
        print("%-26s Filter=%d (davon Gruppierung=%d) Suchfelder=%s" % (
            modell, len(filter_), len(gruppen), felder[:8]))
        print("      Gruppierungen: %s" % gruppen[:12])
    except Exception as fehler:
        print("%-26s FEHLER %s" % (modell, str(fehler)[:90]))

# --- (a) Lagerprodukt im Browser
lager = kw("product.template", "search_read",
           [[["sale_ok", "=", True], ["is_storable", "=", True]], ["id", "name"]])[:1]
if not lager:
    lager = kw("product.template", "search_read", [[["is_storable", "=", True]], ["id", "name"]])[:1]
print("\nLagerprodukt:", lager)

if lager:
    from playwright.sync_api import sync_playwright  # noqa: E402
    JS = """() => {
      const sichtbar = (e) => !!e.getClientRects().length;
      return {
        reiter: [...document.querySelectorAll('.o_notebook .nav-link')].filter(sichtbar).map(e => (e.textContent||'').trim()),
        labels: [...document.querySelectorAll('.o_form_sheet label.o_form_label')].filter(sichtbar).map(e => (e.textContent||'').trim()).filter(t => t),
      };
    }"""
    vz = r"C:/Users/anna.maierhofer/Desktop/Odoo18-Abnahme-Session122/rechnung"
    with sync_playwright() as pw:
        ktx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ["TEMP"], "pw_lager_%s" % os.getpid()),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
        ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        s = ktx.pages[0] if ktx.pages else ktx.new_page()
        s.goto("%s/web#id=%s&model=product.template&view_type=form" % (url, lager[0]["id"]))
        s.wait_for_timeout(9000)
        d = s.evaluate(JS)
        print("### Lagerprodukt %s: Reiter=%s" % (lager[0]["name"], d["reiter"]))
        print("   Beschriftungen: %s" % sorted(set(d["labels"]))[:26])
        s.screenshot(path="%s/produkt_lager_%s.png" % (vz, instanz), full_page=True)
        ktx.close()
