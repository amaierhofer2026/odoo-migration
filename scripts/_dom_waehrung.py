"""Findet im echten Browser die DOM-Herkunft eines sichtbaren Elements (z.B. 'Waehrung').

Aufruf: python scripts/_dom_waehrung.py vm [beleg_id] [textmuster]
Nutzt dieselbe Anmeldung wie die uebrigen Abnahmeskripte (RPC + session_id-Cookie).
"""
import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import lade_env  # noqa: E402

env = lade_env(r"C:/Odoo-Test/.env")
url = "https://k001959vsx.ipax.at" if sys.argv[1:2] == ["vm"] else "http://localhost:8069"
domain = "k001959vsx.ipax.at" if "k001959" in url else "localhost"
beleg_id = int(sys.argv[2]) if len(sys.argv) > 2 else 46
muster = sys.argv[3] if len(sys.argv) > 3 else "hrung"

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
req = urllib.request.Request(url + "/web/session/authenticate", data=json.dumps({
    "jsonrpc": "2.0", "method": "call",
    "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]},
}).encode(), headers={"Content-Type": "application/json"})
json.loads(op.open(req, timeout=120).read().decode())
sid = next(c.value for c in jar if c.name == "session_id")

JS = """
(muster) => {
  const treffer = [];
  for (const el of document.querySelectorAll('*')) {
    if (el.children.length) continue;
    const txt = (el.textContent || '').trim();
    if (!txt || txt.includes(muster) === false) continue;
    if (!el.getClientRects().length) continue;
    const kette = [];
    let p = el;
    for (let i = 0; i < 6 && p; i++) {
      kette.push(p.tagName.toLowerCase()
        + (p.getAttribute && p.getAttribute('name') ? '[' + p.getAttribute('name') + ']' : '')
        + (p.className ? '.' + String(p.className).split(' ').slice(0, 2).join('.') : ''));
      p = p.parentElement;
    }
    const feld = el.closest('[name]');
    const gruppe = el.closest('.o_group, .o_inner_group, .o_inner_group');
    treffer.push({text: txt, kette: kette,
                  feld: feld ? feld.getAttribute('name') : null,
                  gruppe: gruppe ? (gruppe.getAttribute('name') || String(gruppe.className).slice(0, 60)) : null});
  }
  return treffer;
}
"""

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    ktx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_dom_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
    ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ktx.pages[0] if ktx.pages else ktx.new_page()
    s.goto("%s/web#id=%s&model=account.move&view_type=form" % (url, beleg_id))
    s.wait_for_selector(".o_form_view", timeout=120000)
    s.wait_for_timeout(4000)
    treffer = s.evaluate(JS, muster)
    print("TREFFER fuer Muster %r: %d" % (muster, len(treffer)))
    for t in treffer:
        print("  text=%r  feld=%s  gruppe=%s" % (t["text"], t["feld"], t["gruppe"]))
        for stufe in t["kette"]:
            print("     ^ %s" % stufe)
    ktx.close()
