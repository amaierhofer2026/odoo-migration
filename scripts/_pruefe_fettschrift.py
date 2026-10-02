"""Pruft im echten Browser, welche Beschriftungen fett sind und ob das an required liegt."""
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
pid = int(sys.argv[2]) if len(sys.argv) > 2 else 8

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(url + "/web/session/authenticate", data=json.dumps({
    "jsonrpc": "2.0", "method": "call",
    "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]}}).encode(),
    headers={"Content-Type": "application/json"}), timeout=60)
sid = next(c.value for c in jar if c.name == "session_id")

JS = """
() => {
  const aus = [];
  for (const lab of document.querySelectorAll('.o_form_sheet label.o_form_label')) {
    if (!lab.getClientRects().length) continue;
    const text = (lab.textContent || '').trim();
    if (!text) continue;
    const feld = lab.getAttribute('for');
    const wrap = lab.closest('.o_wrap_field') || lab.closest('.o_cell');
    const cs = getComputedStyle(lab);
    aus.push({label: text, for: feld,
              klassen: String(lab.className),
              fett: cs.fontWeight,
              pflicht_marker: !!(wrap && wrap.querySelector('.o_required_modifier, [required], .o_field_widget.o_required_modifier'))});
  }
  return aus;
}
"""

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    ktx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ["TEMP"], "pw_fett_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
    ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ktx.pages[0] if ktx.pages else ktx.new_page()
    s.goto("%s/web#id=%s&model=account.payment&view_type=form" % (url, pid))
    s.wait_for_selector(".o_form_view", timeout=120000)
    s.wait_for_timeout(4000)
    for e in s.evaluate(JS):
        print("%-26s for=%-24s fett=%-6s pflicht=%s klassen=%s" % (
            e["label"][:26], str(e["for"])[:24], e["fett"], e["pflicht_marker"], e["klassen"][:60]))
    ktx.close()
