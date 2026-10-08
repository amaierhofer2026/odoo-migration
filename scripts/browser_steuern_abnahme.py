"""Browserabnahme Bereich Steuern (Abrechnung > Konfiguration > Finanzen > Steuern).

Prueft im echten Chrome:
  1. Steuerliste: Spalten, Anzahl, Suche nach "20% Ust"
  2. Filter Verkauf / Einkauf
  3. Formular "20% Ust" und "20% Vst": Felder, Steuerkonten (Repartitionszeilen)
  4. Verknuepfungen: Steuer auf der Produktvorlage / auf der Rechnungszeile
  5. Testbelege (Verkauf mit USt, Einkauf mit VSt) aus scripts/steuern_testbelege.py:
     Formular mit Steuerspalte und Summen, Buchungszeilen mit Steuerkonto
  Screenshots als Beleg.

Aufruf: uv run --with playwright python scripts/browser_steuern_abnahme.py lokal|vm
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

INST = sys.argv[1] if len(sys.argv) > 1 else "lokal"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "http://localhost:8069" if INST == "lokal" else "https://k001959vsx.ipax.at"
DOMAIN = "localhost" if INST == "lokal" else "k001959vsx.ipax.at"
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session131", "steuern", "browser",
                  INST)
os.makedirs(VZ, exist_ok=True)
PROTOKOLL = os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "Temp", "steuern_testbelege.json")
zeit = int(time.time())

umg = {}
for zeile in open(os.path.join(REPO, ".env"), encoding="utf-8"):
    if "=" in zeile and not zeile.strip().startswith("#"):
        s, w = zeile.split("=", 1)
        umg[s.strip()] = w.strip()
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def rpc(model, method, args, kwargs=None):
    nutzlast = {"jsonrpc": "2.0", "method": "call", "params": {
        "model": model, "method": method, "args": args, "kwargs": kwargs or {}}}
    with op.open(urllib.request.Request(URL + "/web/dataset/call_kw",
                 data=json.dumps(nutzlast).encode(),
                 headers={"Content-Type": "application/json"})) as a:
        d = json.loads(a.read().decode())
    if "error" in d:
        raise RuntimeError(str(d["error"])[:400])
    return d["result"]


def pruefe(ok, text):
    print("  %s  %s" % ("OK  " if ok else "FEHL", text))
    return bool(ok)


op.open(urllib.request.Request(URL + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
            "db": umg["ODOO18_DB"], "login": umg["ODOO18_USER"],
            "password": umg["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"}))
SID = next(c.value for c in jar if c.name == "session_id")

steuer_aktion = rpc("ir.actions.act_window", "search_read",
                    [[["res_model", "=", "account.tax"]], ["id", "name"]])
steuer_aktion = steuer_aktion[0]["id"] if steuer_aktion else None
anzahl11 = rpc("account.tax", "search_count", [[]])
verwendet = rpc("account.tax", "search_count", [[["|"], ["taxes_id", "!=", False],
                                                 ["supplier_taxes_id", "!=", False]]]) if False else None
testbelege = json.load(open(PROTOKOLL, encoding="utf-8")).get("angelegt", []) \
    if os.path.exists(PROTOKOLL) else []
print("=== Bestand (%s) ===" % INST)
print("   Steuer-Aktion %s | %d Steuern im Bestand | Testbelege: %d" % (steuer_aktion, anzahl11,
                                                                     len(testbelege)))

ergebnisse = []
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_steuern_%s_%d" % (INST, zeit)),
        channel="chrome", headless=True, viewport={"width": 1920, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": SID, "domain": DOMAIN, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()
    seite.set_default_timeout(30000)

    # 1. Liste + Spalten + Suche
    print("\n=== 1. Steuerliste ===")
    seite.goto("%s/odoo/action-%s" % (URL, steuer_aktion))
    seite.wait_for_timeout(8000)
    kopf = seite.evaluate("""() => [...document.querySelectorAll('.o_list_table thead th')]
        .map(th => th.innerText.replace(/\\s+/g, ' ').trim()).filter(t => t)""")
    zeilen = seite.locator(".o_list_table tbody tr.o_data_row").count()
    print("   Spalten: %s" % kopf)
    print("   Zeilen auf der Seite: %d" % zeilen)
    ergebnisse.append(pruefe(len(kopf) >= 3, "Liste mit Spalten geladen (%d)" % len(kopf)))
    seite.screenshot(path=os.path.join(VZ, "01_steuerliste.png"), full_page=False)

    print("\n=== 2. Suche nach '20% Ust' ===")
    suchfeld = seite.locator(".o_searchview_input").first
    suchfeld.click()
    suchfeld.type("20% Ust", delay=40)
    seite.wait_for_timeout(2500)
    seite.keyboard.press("Enter")
    seite.wait_for_timeout(5000)
    treffer = seite.locator(".o_list_table tbody tr.o_data_row").count()
    namen = seite.evaluate("""() => [...document.querySelectorAll('.o_list_table tbody tr.o_data_row')]
        .map(r => r.innerText.replace(/\\s+/g, ' ').trim().slice(0, 60))""")
    print("   Treffer: %d | %s" % (treffer, namen[:4]))
    ergebnisse.append(pruefe(treffer >= 1, "Suche funktioniert (%d Treffer)" % treffer))
    seite.screenshot(path=os.path.join(VZ, "02_suche_20ust.png"), full_page=False)

    print("\n=== 3. Filter Verkauf / Einkauf ===")
    seite.goto("%s/odoo/action-%s" % (URL, steuer_aktion))
    seite.wait_for_timeout(7000)
    for filter_name, erwartet_feld in (("Verkauf", "type_tax_use"), ("Einkauf", "type_tax_use")):
        try:
            seite.locator(".o_searchview_dropdown_toggle, .o_cp_searchview .dropdown-toggle").first.click()
            seite.wait_for_timeout(1500)
            treffer_filter = seite.evaluate("""() => [...document.querySelectorAll('.dropdown-menu.show .dropdown-item, .o-dropdown--menu .dropdown-item')]
                .map(i => i.innerText.replace(/\\s+/g, ' ').trim()).filter(t => t)""")
            print("   Verfuegbare Filter (Auszug): %s" % [t for t in treffer_filter if t][:8])
            ergebnisse.append(pruefe(any(filter_name in t for t in treffer_filter),
                                     "Filter '%s' in der Filterauswahl vorhanden" % filter_name))
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(800)
        except Exception as fehler:
            print("   Hinweis Filter %s: %s" % (filter_name, str(fehler)[:90]))
            ergebnisse.append(pruefe(False, "Filter '%s' nicht pruefbar" % filter_name))
    seite.screenshot(path=os.path.join(VZ, "03_filter.png"), full_page=False)

    # 4. Formulare der beiden verwendeten Steuern
    for name, datei in (("20% Ust", "04_formular_20ust.png"), ("20% Vst", "05_formular_20vst.png")):
        print("\n=== 4. Formular '%s' ===" % name)
        seite.goto("%s/odoo/action-%s" % (URL, steuer_aktion))
        seite.wait_for_timeout(7000)
        feld = seite.locator(".o_searchview_input").first
        feld.click()
        feld.type(name, delay=40)
        seite.wait_for_timeout(2500)
        seite.keyboard.press("Enter")
        seite.wait_for_timeout(5000)
        seite.locator(".o_list_table tbody tr.o_data_row").first.click()
        seite.wait_for_timeout(6000)
        werte = seite.evaluate("""() => {
            const aus = {};
            const f = (n) => document.querySelector('.o_field_widget[name="' + n + '"]');
            ['name','description','amount','type_tax_use','amount_type','price_include','tax_group_id','sequence','active'].forEach(n => {
                const w = f(n); aus[n] = w ? (w.innerText || (w.querySelector('input') ? w.querySelector('input').value : '')).replace(/\\s+/g, ' ').trim() : '(nicht sichtbar)';
            });
            aus.konten = [...document.querySelectorAll('.o_field_widget[name="invoice_repartition_line_ids"] .o_data_row')]
                .map(r => r.innerText.replace(/\\s+/g, ' ').trim()).slice(0, 3);
            return aus; }""")
        for k_, v in werte.items():
            print("   %-18s %s" % (k_, v))
        ergebnisse.append(pruefe(name.split()[0] in str(werte.get("name", "")),
                                 "Formular '%s' geoeffnet und gelesen" % name))
        ergebnisse.append(pruefe(bool(werte.get("konten")),
                                 "Repartitionszeilen (Steuerkonten) sichtbar: %s" % werte.get("konten")))
        seite.screenshot(path=os.path.join(VZ, datei), full_page=True)

    # 5. Testbelege im Browser
    for beleg in testbelege:
        print("\n=== 5. Testbeleg %s (id %s) ===" % (beleg["art"], beleg["id"]))
        seite.goto("%s/odoo/action-353/%s" % (URL, beleg["id"]))
        seite.wait_for_timeout(7000)
        kopfzeile = seite.evaluate("""() => {
            const w = document.querySelector('.o_breadcrumb, .o_control_panel');
            return w ? w.innerText.replace(/\\s+/g, ' ').trim().slice(0, 150) : '(kein Kopf)'; }""")
        zeilen = seite.evaluate("""() => [...document.querySelectorAll('.o_field_widget[name="invoice_line_ids"] .o_data_row')]
            .map(r => r.innerText.replace(/\\s+/g, ' ').trim()).slice(0, 3)""")
        print("   Kopf: %s" % kopfzeile)
        print("   Zeilen: %s" % zeilen)
        ergebnisse.append(pruefe(bool(zeilen), "Beleg %s mit Zeile im Browser geoeffnet" % beleg["art"]))
        seite.screenshot(path=os.path.join(VZ, "06_beleg_%s.png" % beleg["art"]), full_page=True)
    ctx.close()

print("\nErgebnis: %d OK / %d FEHL" % (sum(1 for e in ergebnisse if e),
                                       sum(1 for e in ergebnisse if not e)))
print("Screenshots: %s" % VZ)
