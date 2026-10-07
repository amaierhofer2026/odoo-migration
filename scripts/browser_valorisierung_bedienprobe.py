"""Browser-Bedienprobe Bereich Valorisierung auf der VM (keine Speicherung, keine Testdaten).

1. Bestand der Valorisierungstexte vorher (Name, seq, write_date) aufnehmen
2. Rechnung oeffnen, Reiter "Andere Informationen", Feld "Valorisation Text" anklicken,
   Auswahlliste auslesen (Verwendbarkeit), danach Escape und Seite verlassen - ohne Speichern
3. Bestand nachher aufnehmen und vergleichen (Beleg und Valorisierungstexte unveraendert)

Aufruf: uv run --with playwright python scripts/browser_valorisierung_bedienprobe.py vm
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

INST = sys.argv[1] if len(sys.argv) > 1 else "vm"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "http://localhost:8069" if INST == "lokal" else "https://k001959vsx.ipax.at"
DOMAIN = "localhost" if INST == "lokal" else "k001959vsx.ipax.at"
VZ = os.path.expanduser("~") + "/Desktop/Odoo18-Abnahme-Session129/valorisierung/browser/" + INST
os.makedirs(VZ, exist_ok=True)

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


def bestand():
    texte = rpc("itk_valorisierung.valorisierung", "search_read",
                [[], ["name", "seq", "write_date"], ],
                {"context": {"lang": "de_DE"}, "order": "id"})
    belege = rpc("account.move", "search_read",
                 [[("valorisierung_id", "!=", False)], ["name", "state", "valorisierung_id", "write_date"]],
                 {"context": {"lang": "de_DE"}})
    return {"texte": [(t["name"], t["seq"], t["write_date"]) for t in texte], "belege": belege}


op.open(urllib.request.Request(URL + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
            "db": umg["ODOO18_DB"], "login": umg["ODOO18_USER"],
            "password": umg["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"}))
SID = next(c.value for c in jar if c.name == "session_id")

vorher = bestand()
print("=== Bestand vorher (%s) ===" % INST)
print("   Valorisierungstexte: %d" % len(vorher["texte"]))
for n, s, w in vorher["texte"]:
    print("      %-45s seq=%s write_date=%s" % (n, s, w))
print("   Belege mit Valorisierungstext: %d" % len(vorher["belege"]))
for b in vorher["belege"]:
    print("      %-28s %-8s %s write_date=%s" % (b["name"] or "(ohne Nummer)", b["state"],
                                                 b["valorisierung_id"], b["write_date"]))

ergebnisse = []
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ["TEMP"], "pw_bedien_%d" % time.time()),
        channel="chrome", headless=True, viewport={"width": 1920, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": SID, "domain": DOMAIN, "path": "/"}])
    s = ctx.pages[0] if ctx.pages else ctx.new_page()

    ziel = None
    for b in vorher["belege"]:
        if b["state"] == "draft":
            ziel = b
            break
    print("\n=== Bedienprobe am Beleg %s ===" % (ziel["name"] or "(Entwurf)"))
    s.goto("%s/odoo/action-354/%d" % (URL, ziel["id"]))
    s.wait_for_selector(".o_form_view", timeout=90000)
    s.wait_for_timeout(3500)
    for reiter in ("Andere Informationen", "Rechnungszeilen"):
        try:
            s.locator(".o_notebook a.nav-link", has_text=reiter).first.click()
            s.wait_for_timeout(1500)
            if s.locator('.o_field_widget[name="valorisierung_id"]').count():
                break
        except Exception:
            continue
    feld = s.locator('.o_field_widget[name="valorisierung_id"]').first
    sichtbar = feld.count() > 0
    ergebnisse.append(sichtbar)
    print("   %s  Feld im Formular sichtbar" % ("OK  " if sichtbar else "FEHL"))
    if sichtbar:
        s.screenshot(path=os.path.join(VZ, "04_rechnung_feld_sichtbar.png"), full_page=False)
        feld.click()
        s.wait_for_timeout(2500)
        auswahl = s.evaluate("""() => [...document.querySelectorAll('.o_field_many2one input, .o_field_many2one .dropdown-item, .o-autocomplete--dropdown-item')]
            .map(e => (e.value || e.innerText || '').replace(/\\s+/g, ' ').trim()).filter(t => t !== '')""")
        offen = s.evaluate("""() => document.querySelectorAll('.o_field_many2one .dropdown-menu, .o-autocomplete--dropdown-menu').length""")
        print("   Auswahlliste offen: %s | Eintraege: %s" % (bool(offen), auswahl[:12]))
        ergebnisse.append(bool(auswahl))
        print("   %s  Feld bedienbar (Auswahlliste gelesen)" % ("OK  " if auswahl else "FEHL"))
        s.screenshot(path=os.path.join(VZ, "05_rechnung_auswahlliste.png"), full_page=False)
        s.keyboard.press("Escape")
        s.wait_for_timeout(800)
    # Ohne Speichern verlassen
    s.goto("%s/odoo/action-354" % URL)
    s.wait_for_timeout(2500)
    ctx.close()

nachher = bestand()
print("\n=== Vergleich vorher/nachher ===")
gleich_texte = vorher["texte"] == nachher["texte"]
gleich_belege = [(b["name"], b["state"], b["write_date"]) for b in vorher["belege"]] == \
                [(b["name"], b["state"], b["write_date"]) for b in nachher["belege"]]
print("   %s  Valorisierungstexte unveraendert (%d)" % ("OK  " if gleich_texte else "FEHL", len(nachher["texte"])))
print("   %s  Belege unveraendert (write_date identisch, %d)" % ("OK  " if gleich_belege else "FEHL",
                                                                 len(nachher["belege"])))
ergebnisse += [gleich_texte, gleich_belege]
wert = [t[0] for t in nachher["texte"] if t[0] == "VAL-OK"]
print("   %s  VAL-OK vorhanden und unveraendert: %s" % ("OK  " if wert else "FEHL", wert))
ergebnisse.append(bool(wert))

print("\n=== Ergebnis (%s) ===" % INST)
print("   %d OK / %d FEHL" % (sum(1 for e in ergebnisse if e), sum(1 for e in ergebnisse if not e)))
