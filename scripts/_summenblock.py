"""Liest im echten Browser den Summenblock unter den Rechnungszeilen aus.

Aufruf: python scripts/_summenblock.py vm|lokal <beleg_id> [screenshot_name]

Gibt die sichtbaren Beschriftungen und Betraege des Summenblocks aus (Reihenfolge wie im UI)
sowie die Zeile "Faelliger Betrag". Aendert nichts.
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
  const zeilen = [];
  const sichtbar = (e) => !!e.getClientRects().length;
  // Summenblock: Zeilen mit Beschriftung + Betrag
  for (const tr of document.querySelectorAll('.o_form_sheet table tr')) {
    const lab = tr.querySelector('label');
    const wert = tr.querySelector('.o_list_monetary, span[name]');
    if (!lab || !sichtbar(lab)) continue;
    const text = (lab.textContent || '').trim();
    if (!text) continue;
    zeilen.push({label: text, betrag: wert ? (wert.textContent || '').trim() : '',
                 titel: lab.getAttribute('title') || ''});
  }
  // Zeilen im Fussbereich (z.B. Faelliger Betrag, Bezahlt am ...)
  const fuss = [];
  for (const el of document.querySelectorAll('.o_form_sheet .oe_subtotal_footer, .o_form_sheet div')) {
    const t = (el.textContent || '').trim();
    if (!t || t.length > 60) continue;
    if (/^(Faelliger Betrag|Fälliger Betrag|Bezahlt am|Zu zahlen)/.test(t) && sichtbar(el)) {
      fuss.push(t);
    }
  }
  return {zeilen: zeilen, fuss: [...new Set(fuss)]};
}
"""

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    ktx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_summe_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
    ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ktx.pages[0] if ktx.pages else ktx.new_page()
    s.goto("%s/web#id=%s&model=account.move&view_type=form" % (url, beleg_id))
    s.wait_for_selector(".o_form_view", timeout=120000)
    s.wait_for_timeout(4000)
    d = s.evaluate(JS)
    print("SUMMENBLOCK Beleg %s (%s):" % (beleg_id, url))
    for z in d["zeilen"]:
        print("   %-18s %-14s %s" % (z["label"], z["betrag"], ("[Titel: %s]" % z["titel"]) if z["titel"] else ""))
    print("   Fusszeilen:", d["fuss"])
    if name:
        vz = r"C:/Users/anna.maierhofer/Desktop/Odoo18-Abnahme-Session122/rechnung"
        pfad = vz + "/" + name + ".png"
        s.screenshot(path=pfad, full_page=True)
        print("   SCREENSHOT:", pfad)
    ktx.close()
