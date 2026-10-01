"""Vollstaendiger Abnahme-Durchgang durch das Modul Abrechnung im echten Browser.

Aufruf: python scripts/browser_abrechnung_vollstaendig.py vm|local [max_menus]

Fuer jeden erreichbaren Menuepunkt mit Aktion:
  - Listenansicht: sichtbare Spalten
  - Suchleiste: Filter und Gruppierungen (Dropdown im Browser geoeffnet)
  - Kopfleiste: sichtbare Buttons und Smart Buttons
  - Formular des ersten Datensatzes: Reiter, sichtbare Beschriftungen
Ergebnis wird als JSON an docs/_abrechnung_durchgang.json angehaengt (fortsetzbar).
"""
import http.cookiejar
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import lade_env  # noqa: E402

instanz = sys.argv[1] if len(sys.argv) > 1 else "vm"
grenze = int(sys.argv[2]) if len(sys.argv) > 2 else 40
url = "https://k001959vsx.ipax.at" if instanz == "vm" else "http://localhost:8069"
domain = "k001959vsx.ipax.at" if "k001959" in url else "localhost"
env = lade_env(r"C:/Odoo-Test/.env")
ziel = r"C:/Odoo-Test/docs/_abrechnung_durchgang.json"

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(url + "/web/session/authenticate", data=json.dumps({
    "jsonrpc": "2.0", "method": "call",
    "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]}}).encode(),
    headers={"Content-Type": "application/json"}), timeout=120)
sid = next(c.value for c in jar if c.name == "session_id")


def kw(model, method, args, context=None):
    daten = {"jsonrpc": "2.0", "method": "call", "params": {
        "model": model, "method": method, "args": args, "kwargs": {"context": context or {"lang": "de_DE"}}}}
    req = urllib.request.Request(url + "/web/dataset/call_kw", data=json.dumps(daten).encode(),
                                 headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
    antwort = json.loads(op.open(req, timeout=180).read().decode())
    if "error" in antwort:
        raise RuntimeError(str(antwort["error"])[:200])
    return antwort["result"]


# Menuepunkte des Moduls Abrechnung (Wurzel ueber die Aktion des Moduls finden)
modul = kw("ir.module.module", "search_read", [[["name", "=", "account"]], ["id"]])[0]
wurzel = kw("ir.ui.menu", "search_read", [[["name", "in", ["Abrechnung", "Rechnungsstellung", "Invoicing"]]],
                                           ["id", "name", "complete_name"]])
print("Wurzelmenues:", wurzel)
alle = []
for w in wurzel:
    kinder = kw("ir.ui.menu", "search_read", [[["parent_id", "child_of", w["id"]]],
                                              ["id", "name", "complete_name", "action"]])
    alle.extend(kinder)
menues = [m for m in alle if m.get("action")]
print("Menuepunkte mit Aktion: %d" % len(menues))

ergebnis = []
if os.path.exists(ziel):
    ergebnis = json.load(open(ziel, encoding="utf-8"))
erledigt = {e["menu_id"] for e in ergebnis}

from playwright.sync_api import sync_playwright  # noqa: E402

JS_LISTE = """() => ({
  spalten: [...document.querySelectorAll('.o_list_renderer thead th')].map(e => (e.textContent || '').trim()).filter(t => t),
  buttons: [...document.querySelectorAll('.o_control_panel .btn, .o_cp_buttons .btn')].filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim()).filter(t => t),
})"""
JS_FILTER = """() => {
  const aus = {filter: [], gruppieren: []};
  for (const d of document.querySelectorAll('.o_dropdown_menu, .o_searchview_dropdown, .dropdown-menu')) {
    const text = (d.textContent || '');
    if (!d.getClientRects().length) continue;
    for (const it of d.querySelectorAll('.dropdown-item, .o_menu_item')) {
      const t = (it.textContent || '').trim();
      if (!t || t.length > 60) continue;
      (text.includes('Gruppieren') ? aus.gruppieren : aus.filter).push(t);
    }
  }
  return aus;
}"""
JS_FORM = """() => ({
  reiter: [...document.querySelectorAll('.o_notebook .nav-link')].map(e => (e.textContent || '').trim()),
  labels: [...document.querySelectorAll('.o_inner_group label, .o_group label, .o_form_label')].filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim()).filter(t => t),
  buttons: [...document.querySelectorAll('.o_form_statusbar .btn, .o_cp_buttons .btn')].filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim()).filter(t => t),
  smart: [...document.querySelectorAll('.oe_stat_button')].filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim()),
})"""

with sync_playwright() as pw:
    ktx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_durch_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
    ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ktx.pages[0] if ktx.pages else ktx.new_page()
    for m in menues[:grenze]:
        if m["id"] in erledigt:
            continue
        aktion = m["action"]
        # Odoo liefert "ir.actions.act_window,354" als String
        if isinstance(aktion, str) and "," in aktion:
            modell_aktion, aktion_id = aktion.split(",")[:2]
            if modell_aktion != "ir.actions.act_window":
                continue
        elif isinstance(aktion, list) and aktion[0] == "ir.actions.act_window":
            aktion_id = aktion[1]
        else:
            continue
        if not aktion_id:
            continue
        eintrag = {"menu_id": m["id"], "menu": m["complete_name"], "action_id": aktion_id}
        try:
            s.goto("%s/odoo/action-%s" % (url, aktion_id))
            s.wait_for_timeout(6000)
            zustand = s.evaluate(JS_LISTE)
            eintrag["spalten"] = zustand["spalten"]
            eintrag["buttons_liste"] = zustand["buttons"]
            # Suchleiste: Filter und Gruppierungen
            try:
                s.evaluate("""() => { const t = document.querySelector('.o_searchview_dropdown_toggler, .o_cp_searchview .dropdown-toggle');
                    if (t) t.click(); }""")
                s.wait_for_timeout(1500)
                eintrag["suche"] = s.evaluate(JS_FILTER)
                s.keyboard.press("Escape")
                s.wait_for_timeout(800)
            except Exception as f:
                eintrag["suche"] = {"fehler": str(f)[:80]}
            # erstes Formular
            try:
                if s.query_selector_all(".o_data_row"):
                    s.locator(".o_data_row").first.click()
                    s.wait_for_selector(".o_form_view", timeout=60000)
                    s.wait_for_timeout(3500)
                    form = s.evaluate(JS_FORM)
                    eintrag["form_reiter"] = form["reiter"]
                    eintrag["form_labels"] = sorted(set(form["labels"]))
                    eintrag["form_buttons"] = form["buttons"]
                    eintrag["smart_buttons"] = form["smart"]
            except Exception as f:
                eintrag["form_fehler"] = str(f)[:100]
            print("[%s] %s -> Spalten=%d Labels=%d" % (instanz, m["complete_name"], len(eintrag.get("spalten", [])), len(eintrag.get("form_labels", []))))
        except Exception as f:
            eintrag["fehler"] = str(f)[:160]
            print("[%s] %s FEHLER %s" % (instanz, m["complete_name"], str(f)[:80]))
        ergebnis.append(eintrag)
        json.dump(ergebnis, open(ziel, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ktx.close()
print("Ergebnis: %s Eintraege -> %s" % (len(ergebnis), ziel))
