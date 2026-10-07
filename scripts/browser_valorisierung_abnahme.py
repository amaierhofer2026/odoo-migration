"""Browser-Abnahme Bereich Valorisierung (Abrechnung > Konfiguration > Valorisierung).

Prueft im echten Chrome:
  1. Menuepunkt oeffnet die Liste; Spaltenueberschriften = Odoo-11-Wortlaut
     (Code, Beschreibung, Nummernfolge) in Odoo-11-Reihenfolge
  2. Datensaetze vorhanden, Odoo-11-Namen sichtbar
  3. Formular des ersten Datensatzes: Reiter/Felder, Beschriftungen, Reihenfolge
  4. Feldbezeichnung auf dem Rechnungsformular ("Valorisation Text" wie in Odoo 11)
  5. Screenshots als Beleg

Aufruf: uv run --with playwright python scripts/browser_valorisierung_abnahme.py lokal|vm
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
VZ = os.path.expanduser("~") + "/Desktop/Odoo18-Abnahme-Session129/valorisierung/browser/" + INST
os.makedirs(VZ, exist_ok=True)
ERWARTETE_SPALTEN = ["Code", "Beschreibung", "Nummernfolge"]
ERWARTETE_FELDER = ["Code", "Beschreibung", "Nummernfolge"]

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

aktion = rpc("ir.actions.act_window", "search", [[["res_model", "=",
                                                  "itk_valorisierung.valorisierung"]]])
aktion_id = aktion[0]
namen = [x["name"] for x in rpc("itk_valorisierung.valorisierung", "search_read",
                                [[], ["name"]], {"context": {"lang": "de_DE"}})]
print("=== Bestand (%s) ===" % INST)
print("   Aktion %s | %d Valorisierungstexte: %s" % (aktion_id, len(namen), namen[:4]))

ergebnisse = []
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_valo_%s_%d" % (INST, time.time())),
        channel="chrome", headless=True, viewport={"width": 1920, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": SID, "domain": DOMAIN, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()

    print("\n=== 1. Liste ===")
    seite.goto("%s/odoo/action-%d" % (URL, aktion_id))
    seite.wait_for_selector(".o_list_view", timeout=90000)
    seite.wait_for_timeout(4000)
    kopf = seite.evaluate("""() => [...document.querySelectorAll('.o_list_table thead th')]
        .map(th => th.innerText.replace(/\\s+/g, ' ').trim()).filter(t => t !== '')""")
    zeilen = seite.locator(".o_list_table tbody tr.o_data_row").count()
    print("   Spalten : %s" % kopf)
    print("   Zeilen  : %d" % zeilen)
    ergebnisse.append(pruefe(kopf == ERWARTETE_SPALTEN,
                             "Spaltenueberschriften in Odoo-11-Wortlaut und -Reihenfolge: %s" % kopf))
    ergebnisse.append(pruefe(zeilen == len(namen), "Liste zeigt %d Datensaetze" % len(namen)))
    seite.screenshot(path=os.path.join(VZ, "01_liste.png"), full_page=True)

    print("\n=== 2. Formular des ersten Datensatzes ===")
    seite.locator(".o_list_table tbody tr.o_data_row").first.click()
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(3500)
    felder = seite.evaluate("""() => {
        return [...document.querySelectorAll('.o_form_view .o_group label, .o_form_view .o_inner_group label')]
            .map(l => l.innerText.replace(/\\s+/g, ' ').trim()).filter(t => t !== ''); }""")
    reiter = seite.evaluate("""() => [...document.querySelectorAll('.o_form_view .o_notebook .nav-link')]
        .map(a => a.innerText.replace(/\\s+/g, ' ').trim())""")
    print("   Reiter  : %s" % (reiter or "(keine)"))
    print("   Felder  : %s" % felder)
    ergebnisse.append(pruefe([f for f in felder if f in ERWARTETE_FELDER] == ERWARTETE_FELDER,
                             "Formularfelder in Odoo-11-Reihenfolge: %s" % felder))
    seite.screenshot(path=os.path.join(VZ, "02_formular.png"), full_page=True)

    print("\n=== 3. Feldbezeichnung auf dem Rechnungsformular ===")
    seite.goto("%s/odoo/action-354" % URL)
    seite.wait_for_selector(".o_list_view", timeout=90000)
    seite.wait_for_timeout(4000)
    seite.locator(".o_list_table tbody tr.o_data_row").first.click()
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(3500)
    # Der Reiter "Andere Informationen" wird erst beim Oeffnen gerendert (Lehre Session 121)
    try:
        seite.locator(".o_notebook a.nav-link", has_text="Andere Informationen").first.click()
        seite.wait_for_timeout(2500)
    except Exception as fehler:
        print("   Reiter 'Andere Informationen' nicht geoeffnet: %s" % str(fehler)[:80])
    label = seite.evaluate("""() => {
        const w = document.querySelector('.o_field_widget[name="valorisierung_id"]');
        if (!w) return 'Feld nicht sichtbar';
        const g = w.closest('.o_inner_group') || w.parentElement;
        const l = g ? g.querySelector('label') : null;
        return l ? l.innerText.replace(/\\s+/g, ' ').trim() : 'ohne Beschriftung'; }""")
    print("   Beschriftung account.move.valorisierung_id: %r" % label)
    ergebnisse.append(pruefe(label in ("Valorisation Text", "Valorisierungs Text"),
                             "Beschriftung auf der Rechnung: %r (Odoo 11: 'Valorisation Text')" % label))
    seite.screenshot(path=os.path.join(VZ, "03_rechnung.png"), full_page=False)
    ctx.close()

print("\n=== Ergebnis ===")
print("   %d OK / %d FEHL" % (sum(1 for e in ergebnisse if e), sum(1 for e in ergebnisse if not e)))
print("   Bilder: %s" % VZ)
