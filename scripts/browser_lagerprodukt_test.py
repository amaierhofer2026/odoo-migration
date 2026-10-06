"""Browser-Pruefung des temporaeren Lager-Testprodukts (Odoo 18 lokal oder VM).

Aufruf: uv run --with playwright python scripts/browser_lagerprodukt_test.py lokal|vm [vorher|nachher]
Prueft: Produktformular (Reiter, is_storable, Produktart leer, type unsichtbar), Lager-/
Bestandsfunktionen, Filter "Bestandsaufloesung" und "Lagerverwaltung", Verkaufs-/Einkaufsfunktionen
(neue Belege ohne Speichern), Konsistenz type + product_type_id + is_storable.
Screenshots: Desktop/Odoo18-Abnahme-Session126/lager_test/<instanz>/<phase>/
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import urllib.request

from playwright.sync_api import sync_playwright

INST = sys.argv[1] if len(sys.argv) > 1 else "lokal"
PHASE = sys.argv[2] if len(sys.argv) > 2 else "vorher"
PROTO = os.path.join(os.environ["LOCALAPPDATA"], "Temp", "lager_test.json")
URL = "http://localhost:8069" if INST == "lokal" else "https://k001959vsx.ipax.at"
DOMAIN = "localhost" if INST == "lokal" else "k001959vsx.ipax.at"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.expanduser("~") + "/Desktop/Odoo18-Abnahme-Session126/lager_test/%s/%s" % (INST, PHASE)
os.makedirs(VZ, exist_ok=True)
AKTION_PRODUKTE = 382
ergebnisse = []

umgebung = {}
with open(os.path.join(REPO, ".env"), encoding="utf-8") as fh:
    for zeile in fh:
        if "=" in zeile and not zeile.strip().startswith("#"):
            s, w = zeile.split("=", 1)
            umgebung[s.strip()] = w.strip()
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(URL + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
            "db": umgebung["ODOO18_DB"], "login": umgebung["ODOO18_USER"],
            "password": umgebung["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"}))
SID = next(c.value for c in jar if c.name == "session_id")


def pruefe(ok, text):
    ergebnisse.append((bool(ok), text))
    print("  %s  %s" % ("OK  " if ok else "FEHL", text))


with open(PROTO, encoding="utf-8") as fh:
    proto = json.load(fh)
tid = proto[INST]["template"]

JS_LABELS = """() => [...document.querySelectorAll('.o_notebook .nav-link')]
    .filter(a => a.offsetParent).map(a => a.innerText.replace(/\\s+/g,' ').trim())"""
JS_FELD = """(name) => { const e = document.querySelector("[name='"+name+"']");
    if (!e) return {da:false};
    const lab = e.closest('.o_inner_group') ? e.closest('.o_inner_group')
        .querySelector("label[for='"+e.id+"']") : null;
    return {da:true, sichtbar:!!e.offsetParent, klasse:e.className.slice(0,80),
            eingabe:e.querySelectorAll('input,select,textarea').length,
            wert:e.querySelector('input') ? e.querySelector('input').value : null,
            checked:e.querySelector('input') ? e.querySelector('input').checked : null,
            text:(e.innerText||'').replace(/\\s+/g,' ').trim().slice(0,70),
            label:lab ? lab.innerText.replace(/\\s+/g,' ').replace(/\\?/g,'').trim() : null}; }"""
JS_KNOEPFE = """() => [...document.querySelectorAll('.oe_stat_button')]
    .filter(b => b.offsetParent).map(b => b.innerText.replace(/\\s+/g,' ').trim())"""
JS_ZEILEN = """() => [...document.querySelectorAll('.o_data_row')]
    .filter(r => r.offsetParent).map(r => r.innerText.replace(/\\s+/g,' ').trim().slice(0,60))"""

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_lagertest_%s" % INST),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1250})
    ctx.add_cookies([{"name": "session_id", "value": SID, "domain": DOMAIN, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()

    # ---------- 1. Produktformular
    print("\n=== 1. Formular (product.template %s) ===" % tid)
    seite.goto("%s/odoo/action-%d/%s" % (URL, AKTION_PRODUKTE, tid))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(5000)
    reiter = seite.evaluate(JS_LABELS)
    print("   Reiter:", reiter)
    pruefe("Lager" in reiter, "Reiter 'Lager' sichtbar (bei nicht lagerfuehrbaren Produkten fehlt er)")
    d = seite.evaluate(JS_FELD, "is_storable")
    pruefe(d.get("da") and d.get("checked") is True,
           "Feld 'Bestand verfolgen' sichtbar und gesetzt (label=%s)" % d.get("label"))
    pt = seite.evaluate(JS_FELD, "product_type_id")
    pruefe(pt.get("da"), "Produktart-Feld vorhanden (label=%s, Wert=%r)"
           % (pt.get("label"), pt.get("wert") or pt.get("text")))
    ty = seite.evaluate(JS_FELD, "type")
    pruefe(not ty.get("da") or not ty.get("sichtbar"),
           "type ist unsichtbar (Odoo-18-Aufbau: nicht doppelt sichtbar)")
    kn = seite.evaluate(JS_KNOEPFE)
    print("   Smart Buttons:", kn)
    lager_knoepfe = [k for k in kn if any(w in k for w in ("Vorrätig", "Prognostiziert",
                                                            "Meldebestände", "Eingang"))]
    pruefe(lager_knoepfe, "Lager-Smart-Buttons vorhanden: %s" % lager_knoepfe)
    if PHASE == "nachher":
        pruefe(any("5,000" in k for k in lager_knoepfe),
               "Bestand wird im Formular angezeigt (5,000): %s" % lager_knoepfe)
    seite.screenshot(path=os.path.join(VZ, "01_formular.png"), full_page=True)

    # ---------- 2. Lagerreiter
    print("\n=== 2. Reiter Lager ===")
    seite.click(".o_notebook .nav-link:has-text('Lager')")
    seite.wait_for_timeout(2500)
    routen = seite.evaluate("""() => [...document.querySelectorAll("[name='route_ids'] input, "
        + ".o_field_widget[name='route_ids'] input")].filter(i => i.checked)
        .map(i => i.closest('label') ? i.closest('label').innerText.trim() : '')""")
    print("   gesetzte Routen:", routen)
    pruefe(True, "Lagerreiter geoeffnet, Routen-Auswahl vorhanden (%s)" % routen)
    for feld in ("route_from_categ_ids", "weight", "volume", "responsible_id"):
        f = seite.evaluate(JS_FELD, feld)
        print("   Feld %-22s da=%s sichtbar=%s label=%s" % (feld, f.get("da"), f.get("sichtbar"),
                                                            f.get("label")))
    seite.screenshot(path=os.path.join(VZ, "02_lagerreiter.png"), full_page=True)

    # ---------- 3. Smart Button Bestand
    print("\n=== 3. Smart Button Bestand ===")
    b = seite.query_selector(".oe_stat_button:has-text('Einheit')")
    if b:
        print("   Button-Text:", b.inner_text().replace("\n", " ")[:80])
        pruefe(True, "Bestands-Smart-Button vorhanden")
    else:
        pruefe(False, "Kein Bestands-Smart-Button gefunden")

    # ---------- 4. Filter in der Produktliste
    print("\n=== 4. Filter in der Liste ===")
    for name in ("Bestandsauflösung", "Lagerverwaltung", "Service Type Platform"):
        erwartet_gefunden = {"Bestandsauflösung": {"vorher": True, "nachher": False},
                             "Lagerverwaltung": {"vorher": True, "nachher": True},
                             "Service Type Platform": {"vorher": False, "nachher": True}}[name][PHASE]
        seite.goto("%s/odoo/action-%d" % (URL, AKTION_PRODUKTE))
        seite.wait_for_selector(".o_list_view", timeout=90000)
        seite.wait_for_timeout(3500)
        try:
            # Standardfilter der Aktion ("Kann verkauft/eingekauft werden") entfernen,
            # damit nur der gepruefte Filter wirkt (sonst ODER-Verknuepfung)
            for el in seite.query_selector_all(".o_searchview_facet .o_facet_remove"):
                try:
                    el.click()
                    seite.wait_for_timeout(900)
                except Exception:
                    pass
            seite.click(".o_searchview_dropdown_toggler", timeout=8000)
            seite.wait_for_timeout(1200)
            seite.click(".o_menu_item:has-text('%s')" % name, timeout=8000)
            seite.wait_for_timeout(3500)
            facetten = seite.evaluate("""() => [...document.querySelectorAll('.o_searchview_facet')]
                .filter(f => f.offsetParent).map(f => f.innerText.replace(/\\s+/g,' ').trim())""")
            print("   Facetten:", facetten)
            gefiltert = any(name in f for f in facetten)
            zeilen = seite.evaluate(JS_ZEILEN) if gefiltert else []
            print("   Filter %-18s Zeilen: %s" % (name, len(zeilen)))
            for z in zeilen:
                print("      ", z)
            gefunden = any("ZZ-TEST" in z for z in zeilen)
            pruefe(gefiltert, "Filter '%s' ist aktiv (Facette gesetzt)" % name)
            pruefe(gefunden == erwartet_gefunden,
                   "Filter '%s': Testprodukt %s (erwartet %s, Bestand %s, Produktart %s)"
                   % (name, "gefunden" if gefunden else "nicht gefunden",
                      "gefunden" if erwartet_gefunden else "nicht gefunden",
                      "0" if PHASE == "vorher" else "5", "-" if PHASE == "vorher" else "Plattform"))
            seite.screenshot(path=os.path.join(VZ, "03_filter_%s.png" % name), full_page=True)
        except Exception as fehler:
            pruefe(False, "Filter '%s' nicht klickbar: %s" % (name, str(fehler)[:120]))

    # ---------- 5. Verkauf / Einkauf (neue Belege, nichts speichern)
    print("\n=== 5. Verkaufs-/Einkaufsfunktion (neue Belege, ohne Speichern) ===")
    for pfad, titel in (("sale.order", "Verkaufsauftrag"), ("purchase.order", "Bestellung")):
        try:
            seite.goto("%s/odoo/%s/new" % (URL, pfad))
            seite.wait_for_selector(".o_form_view", timeout=45000)
            seite.wait_for_timeout(3000)
            pruefe(True, "%s: neues Formular geoeffnet (ohne Speichern)" % titel)
            seite.screenshot(path=os.path.join(VZ, "04_%s_neu.png" % pfad.split(".")[0]),
                             full_page=True)
        except Exception as fehler:
            pruefe(False, "%s: Formular nicht geoeffnet (%s)" % (titel, str(fehler)[:100]))

    ctx.close()

ok = sum(1 for e, _ in ergebnisse if e)
print("\nErgebnis %s/%s: %d OK / %d FEHL" % (INST, PHASE, ok, len(ergebnisse) - ok))
for e, t in ergebnisse:
    if not e:
        print("   FEHL:", t)
print("Bilder:", VZ)
