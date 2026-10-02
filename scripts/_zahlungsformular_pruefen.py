"""Prueft das Zahlungsformular im echten Browser: sichtbare Beschriftungen, Felder, Status, Smart Buttons.

Aufruf: python scripts/_zahlungsformular_pruefen.py vm|lokal <payment_id> [screenshot_name]
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
pid = int(sys.argv[2]) if len(sys.argv) > 2 else 8
name = sys.argv[3] if len(sys.argv) > 3 else None

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(url + "/web/session/authenticate", data=json.dumps({
    "jsonrpc": "2.0", "method": "call",
    "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]}}).encode(),
    headers={"Content-Type": "application/json"}), timeout=120)
sid = next(c.value for c in jar if c.name == "session_id")

JS = """
() => {
  const sichtbar = (e) => !!e.getClientRects().length;
  const felder = [];
  for (const w of document.querySelectorAll('.o_form_sheet .o_field_widget[name]')) {
    if (!sichtbar(w)) continue;
    const inp = w.querySelector('input, select, textarea');
    felder.push({feld: w.getAttribute('name'),
                 wert: inp ? (inp.value || '').slice(0, 24) : (w.textContent || '').trim().slice(0, 24)});
  }
  const labels = [...document.querySelectorAll('.o_form_sheet label.o_form_label')]
      .filter(sichtbar).map(e => (e.textContent || '').trim()).filter(t => t);
  const status = [...document.querySelectorAll('.o_form_statusbar .o_statusbar_status button, .o_arrow_button')]
      .filter(sichtbar).map(e => (e.textContent || '').trim());
  const knoepfe = [...document.querySelectorAll('.o_form_statusbar button, .o_control_panel .btn, .o_cp_buttons .btn')]
      .filter(sichtbar).map(e => (e.textContent || '').trim()).filter(t => t);
  const smart = [...document.querySelectorAll('.oe_stat_button')].filter(sichtbar).map(e => (e.textContent || '').trim());
  return {felder: felder, labels: labels, status: status, knoepfe: knoepfe, smart: smart};
}
"""

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    ktx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_zahl_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
    ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ktx.pages[0] if ktx.pages else ktx.new_page()
    s.goto("%s/web#id=%s&model=account.payment&view_type=form" % (url, pid))
    s.wait_for_selector(".o_form_view", timeout=120000)
    s.wait_for_timeout(4000)
    d = s.evaluate(JS)
    print("ZAHLUNGSFORMULAR id %s (%s)" % (pid, url))
    print("  Statusleiste:", d["status"])
    print("  Knoepfe:     ", d["knoepfe"])
    print("  SmartButtons:", d["smart"])
    print("  Beschriftungen:", d["labels"])
    print("  Felder (technisch = Wert):")
    for f in d["felder"]:
        print("     %-32s %s" % (f["feld"], f["wert"]))
    if name:
        vz = r"C:/Users/anna.maierhofer/Desktop/Odoo18-Abnahme-Session122/rechnung"
        pfad = vz + "/" + name + ".png"
        s.screenshot(path=pfad, full_page=True)
        print("  SCREENSHOT:", pfad)
    ktx.close()
