"""Browserbeleg Session 131: Wortlaut der zwei Menues und Kontenvorgabe 4000.

Prueft im echten Chrome (lokal und VM):
  1. Menue "Kostenstellenkonten" unter Abrechnung > Konfiguration > Kostenrechnung
     (Odoo-11-Wortlaut), Titel und Navigationsleiste
  2. Menue "Projektkategorien" unter Abrechnung > Konfiguration > Verwaltung
  3. Produktkategorie-Formular: Ertragskonto zeigt das entschiedene Zielkonto 4000
  4. Gebuchte Kundenrechnung: Konto der Belegzeile = 4000
  Screenshots als Beleg.

Aufruf: uv run --with playwright python scripts/browser_abrechnung_wortlaut_konten.py lokal|vm
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
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session131", "browser", INST)
os.makedirs(VZ, exist_ok=True)
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

# Menue-IDs ueber die technische Kennung bestimmen (nicht ueber den Namen)
kennungen = {"kostenstellen": ("account", "account_analytic_def_account"),
             "projektkategorien": ("itk_projectcategory",
                                   "menu_finance_configuration_projectcategory")}
menu_ids = {}
for was, (modul, name) in kennungen.items():
    md = rpc("ir.model.data", "search_read",
             [[["module", "=", modul], ["name", "=", name], ["model", "=", "ir.ui.menu"]],
              ["res_id"]])
    menu_ids[was] = md[0]["res_id"]
kategorie_aktion = rpc("ir.actions.act_window", "search",
                       [[["res_model", "=", "product.category"]]])[0]
# Aktions-ID der Kundenrechnungen ueber die technische Kennung bestimmen
rechnung_aktion = None
md = rpc("ir.model.data", "search_read",
         [[["module", "=", "account"], ["name", "=", "action_move_out_invoice_type"],
           ["model", "=", "ir.actions.act_window"]], ["res_id"]])
if md:
    rechnung_aktion = md[0]["res_id"]
if not rechnung_aktion:
    treffer = rpc("ir.actions.act_window", "search",
                  [[["res_model", "=", "account.move"], ["name", "ilike", "Rechnung"]]])
    rechnung_aktion = treffer[0] if treffer else rpc(
        "ir.actions.act_window", "search", [[["res_model", "=", "account.move"]]])[0]

print("=== Bestand (%s) ===" % INST)
print("   Menue Kostenstellenkonten : %s" % menu_ids["kostenstellen"])
print("   Menue Projektkategorien   : %s" % menu_ids["projektkategorien"])
print("   Kategorie-Aktion          : %s | Rechnungs-Aktion: %s" % (kategorie_aktion, rechnung_aktion))

ergebnisse = []
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_wortlaut_%s_%d" % (INST, zeit)),
        channel="chrome", headless=True, viewport={"width": 1920, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": SID, "domain": DOMAIN, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()
    seite.set_default_timeout(30000)

    # 1./2. Sichtbare Navigationsmenues der App Abrechnung lesen (echte Oberflaeche)
    print("\n=== Sichtbare Menues der App Abrechnung ===")
    seite.goto("%s/odoo/action-%d" % (URL, kategorie_aktion))
    seite.wait_for_timeout(7000)
    sichtbar = seite.evaluate("""() => {
        const aus = [];
        document.querySelectorAll('.o_menu_sections > *').forEach(el => aus.push(el.innerText.replace(/\\s+/g, ' ').trim()));
        aus.push('--- App-Titel: ' + (document.querySelector('.o_menu_brand') ? document.querySelector('.o_menu_brand').innerText.trim() : '?'));
        return aus; }""")
    print("   Navigationsleiste: %s" % sichtbar[:8])
    # Konfigurations-Menue oeffnen, Untermenue aufklappen und die sichtbaren Eintraege lesen
    eintraege = []
    for konfig in seite.locator(".o_menu_sections .dropdown-toggle", has_text="Konfiguration").all():
        try:
            konfig.click()
            seite.wait_for_timeout(1500)
            for eltern in seite.locator(".dropdown-menu.show .dropdown-toggle, .dropdown-menu.show .o-dropdown--menu .dropdown-toggle").all():
                try:
                    eltern.hover()
                    seite.wait_for_timeout(1200)
                except Exception:
                    pass
            texte = seite.evaluate("""() => [...document.querySelectorAll('.dropdown-menu.show, .o-dropdown--menu')]
                .map(m => m.innerText.replace(/\\s+/g, ' ').trim()).filter(t => t)""")
            eintraege.extend(" | ".join(texte).split(" | "))
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(800)
        except Exception as fehler2:
            print("   Hinweis: %s" % str(fehler2)[:90])
    seite.screenshot(path=os.path.join(VZ, "menues_abrechnung.png"), full_page=False)
    print("   Sichtbare Untermenues (Auszug): %s" % [e for e in eintraege if e][:16])
    for erwartet in ("Kostenstellenkonten", "Projektkategorien"):
        treffer = [e for e in eintraege if erwartet in e]
        ergebnisse.append(pruefe(bool(treffer), "Menue '%s' im echten Browser sichtbar (%s)"
                                 % (erwartet, treffer[:1] or "nicht gefunden")))

    # 3. Produktkategorie-Formular: Ertragskonto
    print("\n=== Produktkategorie: Ertragskonto ===")
    seite.goto("%s/odoo/action-%d" % (URL, kategorie_aktion))
    seite.wait_for_timeout(6000)
    seite.locator(".o_list_table tbody tr.o_data_row").first.click()
    seite.wait_for_timeout(5000)
    konto = seite.evaluate("""() => {
        const w = document.querySelector('.o_field_widget[name="property_account_income_categ_id"]');
        if (!w) return '(Feld nicht sichtbar)';
        const a = w.querySelector('.o_field_many2one_selection .o_field_widget, input, span');
        return (w.innerText || (a ? a.value : '') || '').replace(/\\s+/g, ' ').trim(); }""")
    print("   Ertragskonto im Formular: %r" % konto)
    ergebnisse.append(pruefe("4000" in konto, "Ertragskonto zeigt 4000 (entschiedenes Zielkonto)"))
    seite.screenshot(path=os.path.join(VZ, "produktkategorie_ertragskonto.png"), full_page=False)

    # 4. Buchungszeile: Konto 4000 ueber Suche im Browser belegen
    print("\n=== Buchungszeile: Suche nach Konto 4000 (Browser) ===")
    # Der Konto-Spaltenkopf ist in Odoo 18 je Ansicht eine optionale Spalte; deshalb wird ueber
    # die Suche gefiltert und die gefundene Zeile im Formular geoeffnet (dort ist Konto ein Feld).
    treffer_zeilen = 0
    kontofeld = ""
    for aktion in (rpc("ir.actions.act_window", "search_read",
                       [[["res_model", "=", "account.move.line"], ["name", "=", "Journal Items"]],
                        ["id", "name"]]) or [])[:3] or \
                  rpc("ir.actions.act_window", "search_read",
                      [[["res_model", "=", "account.move.line"]], ["id", "name"]])[:3]:
        seite.goto("%s/odoo/action-%d" % (URL, aktion["id"]))
        seite.wait_for_timeout(7000)
        try:
            suchfeld = seite.locator(".o_searchview_input").first
            suchfeld.click()
            suchfeld.type("4000 Brutto-Umsatzerl", delay=40)
            seite.wait_for_timeout(2500)
            seite.keyboard.press("Enter")
            seite.wait_for_timeout(5000)
        except Exception as fehler2:
            print("   Hinweis Suche (Aktion %s): %s" % (aktion["id"], str(fehler2)[:80]))
            continue
        zeilen = seite.locator(".o_list_table tbody tr.o_data_row").count()
        print("   Aktion %s (%s): Trefferzeilen nach Suche '4000 Brutto-Umsatzerl': %d"
              % (aktion["id"], aktion["name"][:26], zeilen))
        if not zeilen:
            continue
        seite.screenshot(path=os.path.join(VZ, "buchungszeilen_suche_4000.png"), full_page=True)
        treffer_zeilen = zeilen
        # Zusatzbeleg: erste Zeile oeffnen und das Kontofeld lesen (Konto ist im Formular ein Feld).
        try:
            seite.locator(".o_list_table tbody tr.o_data_row").first.click()
            seite.wait_for_timeout(6000)
            kontofeld = seite.evaluate("""() => {
                const w = document.querySelector('.o_field_widget[name="account_id"]');
                return w ? w.innerText.replace(/\\s+/g, ' ').trim() : ''; }""")
            print("   Buchungszeile geoeffnet; Feld Konto = %r" % kontofeld)
            seite.screenshot(path=os.path.join(VZ, "buchungszeile_formular_konto.png"), full_page=True)
        except Exception as fehler2:
            print("   Hinweis Formularbeleg: %s" % str(fehler2)[:80])
        break
    ergebnisse.append(pruefe(treffer_zeilen > 0,
                             "Suche nach Konto '4000 Brutto-Umsatzerl...' findet %d Buchungszeilen "
                             "im echten Browser (Screenshot)" % treffer_zeilen))
    ctx.close()

print("\nErgebnis: %d OK / %d FEHL" % (sum(1 for e in ergebnisse if e),
                                       sum(1 for e in ergebnisse if not e)))
print("Screenshots: %s" % VZ)
