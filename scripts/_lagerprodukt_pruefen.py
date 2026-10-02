"""Prueft die Reiter eines Lagerprodukts (Testdatensatz, wird wieder entfernt).

Aufruf: python scripts/_lagerprodukt_pruefen.py vm|lokal
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


vorher = kw("product.template", "search_count", [[]])
neu = kw("product.template", "create", [{
    "name": "TEST-ABNAHME Lagerprodukt",
    "is_storable": True,
    "sale_ok": True,
    "purchase_ok": True,
    "list_price": 10.0,
}])
print("Testprodukt id %s (Bestand vorher %s, nachher %s)" % (
    neu, vorher, kw("product.template", "search_count", [[]])))

JS = """() => {
  const sichtbar = (e) => !!e.getClientRects().length;
  return {
    reiter: [...document.querySelectorAll('.o_notebook .nav-link')].filter(sichtbar).map(e => (e.textContent||'').trim()),
    labels: [...document.querySelectorAll('.o_form_sheet label.o_form_label')].filter(sichtbar).map(e => (e.textContent||'').trim()).filter(t => t),
  };
}"""

from playwright.sync_api import sync_playwright  # noqa: E402

vz = r"C:/Users/anna.maierhofer/Destkop" if False else r"C:/Users/anna.maierhofer/Desktop/Odoo18-Abnahme-Session122/rechnung"
try:
    with sync_playwright() as pw:
        ktx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ["TEMP"], "pw_lp_%s" % os.getpid()),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
        ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        s = ktx.pages[0] if ktx.pages else ktx.new_page()
        s.goto("%s/web#id=%s&model=product.template&view_type=form" % (url, neu))
        s.wait_for_timeout(9000)
        d = s.evaluate(JS)
        print("### Lagerprodukt Reiter (%s): %s" % (instanz, d["reiter"]))
        print("   Beschriftungen: %s" % sorted(set(d["labels"]))[:30])
        s.screenshot(path="%s/produkt_lager_test_%s.png" % (vz, instanz), full_page=True)
        ktx.close()
finally:
    werk = kw("product.product", "search_read", [[[["product_tmpl_id", "=", neu]], ["id"]]])
    for w in werk:
        try:
            kw("product.product", "unlink", [[w["id"]]])
        except Exception:
            pass
    try:
        kw("product.template", "unlink", [[neu]])
        print("Testprodukt entfernt")
    except Exception as fehler:
        print("Testprodukt nicht entfernbar:", str(fehler)[:150])
    print("Kontrolle: Testprodukt vorhanden =",
          kw("product.template", "search_count", [[["name", "like", "TEST-ABNAHME"]]]),
          "| Bestand jetzt:", kw("product.template", "search_count", [[]]))
