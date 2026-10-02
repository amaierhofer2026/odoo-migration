"""Browserpruefung der Konfigurationsformulare (lokal und VM).

Aufruf: python scripts/_konfiguration_pruefen.py vm|lokal
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
        raise RuntimeError(str(antwort["error"])[:200])
    return antwort["result"]


ziele = []
for modell, dom, name in (
        ("account.tax", [["type_tax_use", "=", "sale"]], "Steuern"),
        ("account.journal", [["type", "=", "bank"]], "Journale"),
        ("res.currency", [["name", "=", "EUR"]], "Waehrungen"),
        ("product.category", [], "Produktkategorien"),
        ("account.payment.term", [], "Zahlungsbedingungen"),
        ("account.analytic.account", [], "Kostenstellen"),
        ("account.fiscal.position", [], "Steuerzuordnung"),
):
    satz = kw(modell, "search_read", [dom, ["id", "display_name"]])[:1]
    if satz:
        ziele.append((modell, satz[0]["id"], name, satz[0]["display_name"]))
    else:
        print("%s: kein Datensatz gefunden" % name)

JS = """
() => {
  const sichtbar = (e) => !!e.getClientRects().length;
  return {
    reiter: [...document.querySelectorAll('.o_notebook .nav-link')].filter(sichtbar).map(e => (e.textContent||'').trim()),
    labels: [...document.querySelectorAll('.o_form_sheet label.o_form_label')].filter(sichtbar).map(e => (e.textContent||'').trim()).filter(t => t),
    buttons: [...document.querySelectorAll('.o_form_statusbar button, .o_cp_buttons .btn')].filter(sichtbar).map(e => (e.textContent||'').trim()).filter(t => t),
    smart: [...document.querySelectorAll('.oe_stat_button')].filter(sichtbar).map(e => (e.textContent||'').trim()),
  };
}
"""

from playwright.sync_api import sync_playwright  # noqa: E402

vz = r"C:/Users/anna.maierhofer/Desktop/Odoo18-Abnahme-Session122/rechnung"
with sync_playwright() as pw:
    ktx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ["TEMP"], "pw_konf_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
    ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ktx.pages[0] if ktx.pages else ktx.new_page()
    for modell, rec, name, bez in ziele:
        s.goto("%s/web#id=%s&model=%s&view_type=form" % (url, rec, modell))
        s.wait_for_timeout(8000)
        d = s.evaluate(JS)
        print("### %s: %s (id %s)" % (name, bez, rec))
        print("   Reiter: %s" % d["reiter"])
        print("   Beschriftungen: %s" % sorted(set(d["labels"]))[:24])
        if d["smart"]:
            print("   Smart: %s" % d["smart"][:6])
        s.screenshot(path="%s/konf_%s_%s.png" % (vz, name.lower().replace(" ", "_").replace("ä", "ae"), instanz),
                     full_page=True)
    ktx.close()
