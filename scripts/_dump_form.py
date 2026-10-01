"""Schnelldiagnose: sichtbare Feldbezeichnungen eines Formulars (Modell + Datensatz)."""
import http.cookiejar, json, os, sys, urllib.request
sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import lade_env
modell = sys.argv[1]; basis = sys.argv[2]; url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8069"
domain = "k001959vsx.ipax.at" if "k001959" in url else "localhost"
env = lade_env(r"C:/Odoo-Test/.env")
jar = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def rpc(pfad, prm):
    r = urllib.request.Request(url + pfad, data=json.dumps({"jsonrpc":"2.0","method":"call","params":prm}).encode(), headers={"Content-Type":"application/json"})
    return json.loads(op.open(r, timeout=180).read().decode())
rpc("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]})
sid = next(c.value for c in jar if c.name == "session_id")
def kw(m, meth, args, **kwargs):
    o = rpc("/web/dataset/call_kw", {"model": m, "method": meth, "args": args, "kwargs": kwargs})
    if "error" in o: raise RuntimeError(str(o["error"])[:200])
    return o["result"]
ids = kw(modell, "search", [[]], limit=1)
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(user_data_dir=os.path.join(os.environ.get("TEMP","/tmp"), "pw_df_%s" % os.getpid()), channel="chrome", headless=True, viewport={"width":1900,"height":1400}, locale="de-DE")
    ctx.add_cookies([{"name":"session_id","value":sid,"domain":domain,"path":"/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    s.goto("%s/web#id=%s&model=%s&view_type=form" % (url, ids[0], modell))
    s.wait_for_selector(".o_form_view", timeout=120000); s.wait_for_timeout(4000)
    def texte(sel):
        return s.evaluate("""(q) => [...document.querySelectorAll(q)].filter(e => e.getClientRects().length)
            .map(e => (e.textContent||'').trim()).filter(t => t)""", sel)
    print("REITER:", texte(".o_notebook .nav-link"))
    print("FELDER:", sorted(set(texte(".o_inner_group label, .o_group label, .o_form_label"))))
    print("BUTTONS:", sorted(set(texte(".o_form_statusbar button, .o_control_panel button")))[:16])
    ctx.close()
