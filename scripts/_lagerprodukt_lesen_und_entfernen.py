"""Liest die Reiter des Test-Lagerprodukts und entfernt es anschliessend sauber."""
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


tmpls = kw("product.template", "search_read", [[["name", "like", "TEST-ABNAHME"]], ["id", "name", "is_storable"]])
print("Testprodukte:", tmpls)

JS = """() => {
  const sichtbar = (e) => !!e.getClientRects().length;
  return {
    reiter: [...document.querySelectorAll('.o_notebook .nav-link')].filter(sichtbar).map(e => (e.textContent||'').trim()),
    labels: [...document.querySelectorAll('.o_form_sheet label.o_form_label')].filter(sichtbar).map(e => (e.textContent||'').trim()).filter(t => t),
  };
}"""

if tmpls:
    from playwright.sync_api import sync_playwright  # noqa: E402
    with sync_playwright() as pw:
        ktx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ["TEMP"], "pw_lp2_%s" % os.getpid()),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
        ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        s = ktx.pages[0] if ktx.pages else ktx.new_page()
        s.goto("%s/web#id=%s&model=product.template&view_type=form" % (url, tmpls[0]["id"]))
        s.wait_for_timeout(9000)
        d = s.evaluate(JS)
        print("### LAGERPRODUKT %s (lagerfuehrung=%s) Reiter: %s" % (tmpls[0]["name"], tmpls[0]["is_storable"], d["reiter"]))
        print("   Beschriftungen: %s" % sorted(set(d["labels"]))[:30])
        s.screenshot(path=r"C:/Users/anna.maierhofer/Desktop/Odoo18-Abnahme-Session122/rechnung/produkt_lager_test_%s.png" % instanz,
                     full_page=True)
        ktx.close()

for t in tmpls:
    varianten = kw("product.product", "search_read", [[["product_tmpl_id", "=", t["id"]]], ["id"]])
    for v in varianten:
        try:
            kw("product.product", "unlink", [[v["id"]]])
        except Exception as fehler:
            print("Variante %s nicht entfernbar: %s" % (v["id"], str(fehler)[:120]))
    try:
        kw("product.template", "unlink", [[t["id"]]])
        print("Testprodukt %s entfernt" % t["id"])
    except Exception as fehler:
        print("Testprodukt %s nicht entfernbar: %s" % (t["id"], str(fehler)[:150]))

print("Kontrolle TEST-ABNAHME-Produkte:", kw("product.template", "search_count", [[["name", "like", "TEST-ABNAHME"]]]),
      "| Produkte gesamt:", kw("product.template", "search_count", [[]]))
