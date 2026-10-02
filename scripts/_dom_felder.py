"""DOM-Analyse des VM-Formulars: sichtbare Eingabefelder, Texte 'oder'/'in' und ihre Herkunft.

Aufruf: python scripts/_dom_felder.py vm <beleg_id> [modell]
Ausgabe je Fund: Feldname (technisch), Widget-Klasse, Elternkette, Position im Formular.
Zusaetzlich: Zaehlung sichtbarer Eingabefelder zwischen Kopfbereich und Reiterleiste.
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
modell = sys.argv[3] if len(sys.argv) > 3 else "account.move"

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
  const feldname = (e) => {
    const f = e.closest('[name]');
    return f ? f.getAttribute('name') : null;
  };
  const kette = (e, n) => {
    const aus = [];
    let p = e;
    for (let i = 0; i < n && p; i++) {
      aus.push(p.tagName.toLowerCase() + (p.getAttribute && p.getAttribute('name') ? '[' + p.getAttribute('name') + ']' : '')
        + (p.className ? '.' + String(p.className).split(' ').slice(0, 2).join('.') : ''));
      p = p.parentElement;
    }
    return aus;
  };
  const eingaben = [];
  for (const e of document.querySelectorAll('input, select, textarea')) {
    if (!sichtbar(e)) continue;
    if (e.closest('.o_notebook')) continue;               // Zeilen/Tabs getrennt
    if (e.closest('.o_searchview, .o_cp_searchview, .o_control_panel')) continue;
    eingaben.push({
      tag: e.tagName.toLowerCase(), typ: e.getAttribute('type') || '',
      klasse: String(e.className).slice(0, 50), wert: (e.value || '').slice(0, 30),
      feld: feldname(e), kette: kette(e, 4),
    });
  }
  const texte = [];
  for (const e of document.querySelectorAll('*')) {
    if (e.children.length) continue;
    const t = (e.textContent || '').trim();
    if (t !== 'oder' && t !== 'in' && t !== 'oder:') continue;
    if (!sichtbar(e)) continue;
    texte.push({text: t, kette: kette(e, 5), feld: feldname(e)});
  }
  const sheet = document.querySelector('.o_form_sheet');
  const reiter = document.querySelector('.o_notebook');
  let abstand = null;
  if (sheet && reiter) abstand = reiter.getBoundingClientRect().top - sheet.getBoundingClientRect().top;
  return {eingaben: eingaben, texte: texte, abstand_reiter: abstand};
}
"""

from playwright.sync_api import sync_playwright  # noqa: E402

with sync_playwright() as pw:
    ktx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_felder_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
    ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ktx.pages[0] if ktx.pages else ktx.new_page()
    s.goto("%s/web#id=%s&model=%s&view_type=form" % (url, beleg_id, modell))
    s.wait_for_selector(".o_form_view", timeout=120000)
    s.wait_for_timeout(4000)
    name = sys.argv[4] if len(sys.argv) > 4 else "formular"
    vz = r"C:/Users/anna.maierhofer/Desktop/Odoo18-Abnahme-Session122/rechnung"
    pfad = vz + "/" + name + ".png"
    s.screenshot(path=pfad, full_page=True)
    d = s.evaluate(JS)
    print("SCREENSHOT:", pfad)
    print("SICHTBARE EINGABEFELDER ausserhalb der Reiter:", len(d["eingaben"]))
    for e in d["eingaben"]:
        print("  <%s type=%s class=%s wert=%r> feld=%s" % (e["tag"], e["typ"], e["klasse"], e["wert"], e["feld"]))
        print("     Kette: %s" % " < ".join(e["kette"]))
    print("TEXTE 'oder'/'in':", len(d["texte"]))
    for t in d["texte"]:
        print("  %r feld=%s" % (t["text"], t["feld"]))
        print("     Kette: %s" % " < ".join(t["kette"]))
    print("Abstand Blatt->Reiter: %s px" % d["abstand_reiter"])
    ktx.close()
