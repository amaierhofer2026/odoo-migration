"""Browserabnahme der Steuerbeschreibungen (Sonderzeichen) im echten Chrome.

Prueft Liste und Formular der Steuern auf die beanstandeten Sonderzeichen:
  * In der Liste und im Formular darf kein "T°"/"┬º" mehr erscheinen,
  * das Paragrafzeichen muss als "§" sichtbar sein (Beispiele Anna: UST_019 Grundstuecksumsaetze,
    UST_016 Kleinunternehmer),
  * die Beschreibung darf sich nicht in der Darstellung unterscheiden.
Screenshots als Beleg.

Aufruf: uv run --with playwright python scripts/browser_steuern_beschreibungen.py lokal|vm
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
KAPUTT = ("\u252c", "\u00ba", "T\u00b0", "\u00c2\u00a7", "\ufffd")
# (Formularsuche ueber den Steuernamen; die Klammer nennt den erwarteten Beschreibungstext)
BEISPIELE = (("0% Ust R E", "UST_019 Grundstücksumsätze"), ("0% Ust S B", "UST_016 Kleinunternehmer"),
            ("20% Vst EU T", "VST_061 entrichtete"), ("20% RC C S", "RC 20% § 19 Abs. 1a"))
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
aktion = rpc("ir.actions.act_window", "search", [[["res_model", "=", "account.tax"]]])[0]

ergebnisse = []
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_steuertext_%s_%d" % (INST, zeit)),
        channel="chrome", headless=True, viewport={"width": 1920, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": SID, "domain": DOMAIN, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()
    seite.set_default_timeout(30000)

    print("=== 1. Liste: sichtbare Beschreibungen ===")
    seite.goto("%s/odoo/action-%s" % (URL, aktion))
    seite.wait_for_timeout(8000)
    kopf = seite.evaluate("""() => [...document.querySelectorAll('.o_list_table thead th')]
        .map(th => th.innerText.replace(/\\s+/g, ' ').trim()).filter(t => t)""")
    sichtbar = seite.evaluate("""() => [...document.querySelectorAll('.o_list_table tbody tr.o_data_row')]
        .map(r => r.innerText.replace(/\\s+/g, ' ').trim())""")
    kaputt = [(z, [hex(ord(k[0])) for k in KAPUTT if k in z]) for z in sichtbar
              if any(k in z for k in KAPUTT)]
    print("   Spalten: %s" % kopf)
    print("   Zeilen auf der Seite: %d | davon mit kaputtem Zeichen: %d" % (len(sichtbar), len(kaputt)))
    for z in sichtbar[:3]:
        print("      %s" % z[:120])
    for z, m in kaputt[:5]:
        print("      VERDACHT %s | %r" % (m, z[:110]))
    ergebnisse.append(pruefe(not kaputt, "Liste ohne fehlerhafte Sonderzeichen"))
    seite.screenshot(path=os.path.join(VZ, "01_steuerliste.png"), full_page=False)

    for muster, kennung in BEISPIELE:
        print("\n=== 2. Formular: Suche '%s' (erwartet %s in der Beschreibung) ===" % (muster, kennung))
        seite.goto("%s/odoo/action-%s" % (URL, aktion))
        seite.wait_for_timeout(7000)
        feld = seite.locator(".o_searchview_input").first
        feld.click()
        feld.type(muster, delay=40)
        seite.wait_for_timeout(2500)
        seite.keyboard.press("Enter")
        seite.wait_for_timeout(5000)
        n = seite.locator(".o_list_table tbody tr.o_data_row").count()
        if not n:
            ergebnisse.append(pruefe(False, "Steuer '%s' nicht gefunden" % muster))
            continue
        # Genau die Zeile oeffnen, deren Text den erwarteten Beschreibungstext enthaelt
        # (die Freitextsuche kann mehrere Treffer liefern).
        zeilen = seite.locator(".o_list_table tbody tr.o_data_row")
        treffer_idx = None
        for i in range(n):
            t = (zeilen.nth(i).inner_text() or "").replace("\n", " ")
            if kennung.split()[0] in t:
                treffer_idx = i
                break
        if treffer_idx is None:
            ergebnisse.append(pruefe(False, "Steuer mit '%s' in der Liste nicht gefunden" % kennung))
            continue
        zeilen.nth(treffer_idx).click()
        seite.wait_for_timeout(6000)
        # Beschreibung und "Bezeichnung auf Rechnungen" liegen im Reiter "Erweiterte Optionen"
        try:
            seite.locator(".o_form_view .nav-link", has_text="Erweiterte Optionen").first.click()
            seite.wait_for_timeout(2500)
        except Exception as fehler:
            print("   Hinweis Reiter: %s" % str(fehler)[:80])
        texte = seite.evaluate("""() => {
            const aus = {};
            ['description', 'invoice_label'].forEach(n => {
                const w = document.querySelector('.o_field_widget[name="' + n + '"]');
                if (!w) { aus[n] = '(nicht sichtbar)'; return; }
                const i = w.querySelector('input, textarea');
                aus[n] = ((i && i.value) || w.innerText || '').replace(/\\s+/g, ' ').trim();
            });
            return aus; }""")
        print("   Beschreibung    : %r" % texte["description"][:140])
        print("   Bezeichnung auf Rechnungen: %r" % texte["invoice_label"][:100])
        zusammen = "%s %s" % (texte["description"], texte["invoice_label"])
        gut = (kennung.split()[0] in zusammen) and ("\u00a7" in zusammen) \
            and not any(k in zusammen for k in KAPUTT)
        ergebnisse.append(pruefe(gut, "Formular zeigt '%s' und '§', kein fehlerhaftes Zeichen"
                                 % kennung))
        seite.screenshot(path=os.path.join(VZ, "02_formular_%s.png" % muster), full_page=False)
    ctx.close()

print("\nErgebnis: %d OK / %d FEHL" % (sum(1 for e in ergebnisse if e),
                                       sum(1 for e in ergebnisse if not e)))
print("Screenshots: %s" % VZ)
