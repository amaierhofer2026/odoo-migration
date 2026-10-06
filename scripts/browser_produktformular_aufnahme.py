"""Produktformular im Browser aufnehmen (Reiter, Felder, Screenshots) - ohne Pruefung.

Fuer Vorher-/Nachher-Bilder. Aufruf:
    python scripts/browser_produktformular_aufnahme.py lokal|vm <zielordner>
"""
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AKTION = 382


def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            w[k.strip()] = v.strip().strip('"')
    return w


inst = sys.argv[1]
ziel = sys.argv[2]
os.makedirs(ziel, exist_ok=True)
env = lade_env(os.path.join(REPO, ".env"))
url = "http://localhost:8069" if inst != "vm" else "https://k001959vsx.ipax.at"
domain = "localhost" if inst != "vm" else "k001959vsx.ipax.at"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(url + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
            "db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
            "password": env["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"}))
sid = next(c.value for c in jar if c.name == "session_id")


def rpc(model, method, args, kwargs=None):
    kw = dict(kwargs or {})
    kw.setdefault("context", {"lang": "de_DE"})
    p = {"model": model, "method": method, "args": args, "kwargs": kw}
    r = json.loads(op.open(urllib.request.Request(
        url + "/web/dataset/call_kw", data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                        "params": p}).encode(),
        headers={"Content-Type": "application/json"})).read())
    if "error" in r:
        raise RuntimeError(str(r["error"])[:300])
    return r["result"]


ids = rpc("product.template", "search", [[["type", "=", "consu"], ["sale_ok", "=", True]]])
p = rpc("product.template", "read", [ids[:1], ["id", "name"]])[0]
print("Instanz:", inst, "| Produkt:", p)

TABS = """() => [...document.querySelectorAll('.o_notebook .o_notebook_headers .nav-link, .o_notebook > ul.nav .nav-link')]
    .filter(a => a.offsetParent).map(a => a.innerText.replace(/\\s+/g,' ').trim())"""
LABELS = """() => [...document.querySelectorAll('.o_notebook .tab-pane')]
    .filter(x => !x.className.includes('d-none') && x.offsetParent)
    .flatMap(x => [...x.querySelectorAll('label.o_form_label')])
    .filter(l => l.offsetParent && l.innerText.trim())
    .map(l => l.innerText.replace(/\\s+/g,' ').trim())"""

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_prodauf_%s" % inst),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()
    seite.goto("%s/odoo/action-%d" % (url, AKTION))
    seite.wait_for_selector(".o_list_view, .o_form_view", timeout=90000)
    seite.wait_for_timeout(5000)
    spalten = seite.evaluate("""() => [...document.querySelectorAll('.o_list_view thead th')]
        .filter(e => e.offsetParent).map(e => e.innerText.replace(/\\s+/g,' ').trim()).filter(t => t)""")
    print("Listenspalten:", spalten)
    print("Zeilen:", seite.evaluate("""() => document.querySelectorAll('.o_list_view tbody tr.o_data_row').length"""))
    print("Pager:", seite.evaluate("""() => { const e = document.querySelector('.o_pager'); return e ? e.innerText.replace(/\\s+/g,' ') : '-'; }"""))
    print("Suchleiste:", seite.evaluate("""() => [...document.querySelectorAll('.o_searchview .o_searchview_facet')]
        .map(e => e.innerText.replace(/\\s+/g,' ').trim())"""))
    seite.screenshot(path=os.path.join(ziel, "00_liste_verkaufbare_produkte.png"), full_page=True)
    seite.goto("%s/odoo/action-%d/%s" % (url, AKTION, p["id"]))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(6000)
    reiter = seite.evaluate(TABS)
    print("Reiter:", reiter)
    seite.screenshot(path=os.path.join(ziel, "01_reiter_gesamt.png"), full_page=True)
    for r in reiter:
        k = seite.query_selector(".o_notebook .nav-link:has-text('%s')" % r.replace('"', ""))
        if k is None:
            continue
        k.click()
        seite.wait_for_timeout(1500)
        print("--- %s: %s" % (r, seite.evaluate(LABELS)))
        seite.screenshot(path=os.path.join(ziel, "reiter_%s.png" % r.replace(" ", "_").replace("&", "und")),
                         full_page=True)
    print("Ordner:", ziel)
    ctx.close()
