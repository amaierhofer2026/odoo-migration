"""Sonde: DOM des ersten Produktformular-Reiters (Sichtbarkeit einzelner Felder).

Aufruf: python scripts/_sonde_produktformular_dom.py lokal|vm [produkt_id]
"""
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            w[k.strip()] = v.strip().strip('"')
    return w


inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
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
    r = json.loads(op.open(urllib.request.Request(
        url + "/web/dataset/call_kw", data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                        "params": {"model": model, "method": method,
                                                                   "args": args, "kwargs": kw}}).encode(),
        headers={"Content-Type": "application/json"})).read())
    if "error" in r:
        raise RuntimeError(str(r["error"])[:300])
    return r["result"]


pid = int(sys.argv[2]) if len(sys.argv) > 2 else rpc(
    "product.template", "search", [[["type", "=", "consu"], ["sale_ok", "=", True]]])[0]
print("Instanz:", inst, "| Produkt:", rpc("product.template", "read", [[pid], ["name", "type", "product_variant_count"]]))

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_sonde_dom_%s" % inst),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    p = ctx.pages[0] if ctx.pages else ctx.new_page()
    p.goto("%s/odoo/action-382/%s" % (url, pid))
    p.wait_for_selector(".o_form_view", timeout=90000)
    p.wait_for_timeout(6000)
    felder = p.evaluate("""() => {
        const pane = [...document.querySelectorAll('.o_notebook .tab-pane')].find(x => x.offsetParent);
        return [...pane.querySelectorAll('[name]')].map(e => ({
            tag: e.tagName, name: e.getAttribute('name'), cls: e.className.slice(0,50),
            sichtbar: !!e.offsetParent, h: Math.round(e.getBoundingClientRect().height)}));}""")
    print("Felder im ersten Reiter (DOM):")
    for f in felder:
        print("   ", f)
    for name in ("categ_id", "default_code", "barcode"):
        print(name, ":", p.evaluate("""(n) => { const e = document.querySelector("[name='"+n+"']");
            if (!e) return 'NICHT IM DOM';
            const s = getComputedStyle(e);
            return {klasse: e.className, sichtbar: !!e.offsetParent, display: s.display,
                    html: e.outerHTML.replace(/\\s+/g,' ').slice(0,300)}; }""", name))
    ctx.close()
