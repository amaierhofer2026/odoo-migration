"""Schnelldiagnose: sichtbare Felder je Reiter des Odoo-18-Rechnungsformulars."""
import http.cookiejar, json, os, sys, urllib.request
sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import lade_env
env = lade_env(r"C:/Odoo-Test/.env")
url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8069"
domain = "k001959vsx.ipax.at" if "k001959" in url else "localhost"
jar = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
req = urllib.request.Request(url + "/web/session/authenticate", data=json.dumps({"jsonrpc":"2.0","method":"call","params":{"db":env["ODOO18_DB"],"login":env["ODOO18_USER"],"password":env["ODOO18_PWD"]}}).encode(), headers={"Content-Type":"application/json"})
json.loads(op.open(req, timeout=120).read().decode())
sid = next(c.value for c in jar if c.name == "session_id")
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(user_data_dir=os.path.join(os.environ.get("TEMP","/tmp"), "pw_dump_%s" % os.getpid()), channel="chrome", headless=True, viewport={"width":1900,"height":1400}, locale="de-DE")
    ctx.add_cookies([{"name":"session_id","value":sid,"domain":domain,"path":"/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()
    ids = None
    try:
        antwort = op.open(urllib.request.Request(url + "/web/dataset/call_kw",
            data=json.dumps({"jsonrpc":"2.0","method":"call","params":{"model":"account.move","method":"search_read",
                "args":[[["move_type","=","out_invoice"],["state","=","posted"]],["id","name"]],
                "kwargs":{"limit":1,"order":"id desc","context":{"lang":"de_DE"}}}}).encode(),
            headers={"Content-Type":"application/json","Cookie":"session_id=%s" % sid}), timeout=120)
        ids = json.loads(antwort.read().decode())["result"]
    except Exception as e:
        print("Hinweis Belegsuche:", str(e)[:80])
    if ids:
        print("BELEG:", ids[0]["name"], "id", ids[0]["id"])
        s.goto("%s/web#id=%s&model=account.move&view_type=form" % (url, ids[0]["id"]))
    else:
        s.goto("%s/odoo/action-354" % url); s.wait_for_selector(".o_list_renderer", timeout=120000); s.wait_for_timeout(5000)
        s.locator(".o_data_row").first.click()
    s.wait_for_selector(".o_form_view", timeout=90000); s.wait_for_timeout(4000)
    reiter = s.evaluate("""() => [...document.querySelectorAll('.o_notebook .nav-link')].map(e => e.textContent.trim())""")
    print("REITER:", reiter)
    for i, name in enumerate(reiter):
        s.evaluate("""(i) => { const t = document.querySelectorAll('.o_notebook .nav-link')[i]; if (t) t.click(); }""", i)
        s.wait_for_timeout(2500)
        felder = s.evaluate("""() => [...document.querySelectorAll('.o_inner_group label, .o_group label, .o_form_label')]
            .filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim()).filter(t => t)""")
        print("REITER %d '%s': %s" % (i, name, sorted(set(felder))))
    s.evaluate("""() => { const t = document.querySelectorAll('.o_notebook .nav-link')[0]; if (t) t.click(); }""")
    s.wait_for_timeout(2500)
    spalten = s.evaluate("""() => [...document.querySelectorAll('.o_field_x2many_list thead th, .o_list_renderer thead th')]
        .map(e => (e.textContent || '').trim()).filter(t => t)""")
    print("ZEILEN-SPALTEN:", spalten)
    vz = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "rechnung")
    os.makedirs(vz, exist_ok=True)
    datei = os.path.join(vz, "Rechnung_%s.png" % ("vm" if "k001959" in url else "lokal"))
    s.screenshot(path=datei, full_page=True)
    print("SCREENSHOT:", datei)
    ctx.close()
