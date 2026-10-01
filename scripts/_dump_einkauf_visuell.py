"""Visuelle Abnahme: Eingangsrechnungen und Lieferanten-Gutschriften (echter Browser)."""
import http.cookiejar, json, os, sys, urllib.request
sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import lade_env
instanz = sys.argv[1] if len(sys.argv) > 1 else "lokal"
url, domain = (("https://k001959vsx.ipax.at", "k001959vsx.ipax.at") if instanz == "vm" else ("http://localhost:8069", "localhost"))
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
vz = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "belege")
os.makedirs(vz, exist_ok=True)
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(user_data_dir=os.path.join(os.environ.get("TEMP","/tmp"), "pw_ek_%s_%s" % (instanz, os.getpid())), channel="chrome", headless=True, viewport={"width":1900,"height":1400}, locale="de-DE")
    ctx.add_cookies([{"name":"session_id","value":sid,"domain":domain,"path":"/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    def texte(sel):
        return s.evaluate("""(q) => [...document.querySelectorAll(q)].filter(e => e.getClientRects().length).map(e => (e.textContent||'').trim()).filter(t => t)""", sel)
    for wunsch in ("Eingangsrechnungen", "Lieferanten-Gutschriften"):
        menues = kw("ir.ui.menu","search_read",[[("name","=",wunsch),("action","!=",False)],["name","complete_name","action"]], context={"lang":"de_DE"})
        aid = None
        for m in menues:
            kandidat = int(m["action"].split(",")[1])
            modell = kw("ir.actions.act_window","read",[[kandidat],["res_model"]])[0]["res_model"]
            if modell == "account.move":
                aid = kandidat; print("%s: Menue %s Aktion %s" % (wunsch, m["complete_name"], aid)); break
        if not aid: print("%s: kein Menue gefunden" % wunsch); continue
        s.goto("%s/odoo/action-%s" % (url, aid)); s.wait_for_timeout(7000)
        spalten = texte(".o_list_renderer thead th, .o_list_view thead th")
        print("   Listen-Spalten:", spalten)
        ids = kw("account.move", "search", [[("move_type", "=", "in_invoice" if wunsch == "Eingangsrechnungen" else "in_refund")]], limit=1) or kw("account.move", "search", [[]], limit=1)
        if ids:
            s.goto("%s/web#id=%s&model=account.move&view_type=form" % (url, ids[0]))
            s.wait_for_selector(".o_form_view", timeout=90000); s.wait_for_timeout(4000)
            print("   Reiter:", s.evaluate("""() => [...document.querySelectorAll('.o_notebook .nav-link')].map(e => e.textContent.trim())"""))
            print("   sichtbare Felder:", sorted(set(texte(".o_inner_group label, .o_group label, .o_form_label")))[:22])
            print("   Buttons:", sorted(set(texte(".o_form_statusbar button, .o_control_panel button")))[:12])
            print("   Zeilen-Spalten:", texte(".o_field_x2many_list thead th"))
        s.screenshot(path=os.path.join(vz, "%s_%s.png" % (wunsch.replace("-","_"), instanz)), full_page=True)
        print("   SCREENSHOT:", os.path.join(vz, "%s_%s.png" % (wunsch.replace("-","_"), instanz)))
    ctx.close()
