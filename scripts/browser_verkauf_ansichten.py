"""Browser-Abnahme Verkauf Teil 4, Schritt 1: Liste, Kanban, Pivot, Graph, Kalender (Odoo 18).

Prueft im echten Browser die Angebotsliste (Menue Verkauf/Auftraege/Angebote):
  - Listenansicht mit den Odoo-11-Spalten inklusive "Bestelldatum"
  - Spaltenauswahl (optionale Spalten) enthaelt "Bestelldatum"
  - Umschalten auf Kanban, Pivot, Graph und Kalender
  - Kalender: Odoo-18-Aktivitaetenkalender ist vorhanden

Aufruf:
    uv run --with playwright python scripts/browser_verkauf_ansichten.py --instanz lokal
    uv run --with playwright python scripts/browser_verkauf_ansichten.py --instanz vm
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_verkauf_menue import lade_env, rpc_client, REPO

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session121")
SP = {"lang": "de_DE"}
SPALTEN_O11 = ["Auftrag", "Nummer", "Bestelldatum", "Kunde", "Rechnungsadresse", "Verkaufskontakt",
               "Verkäufer", "Vertriebsmitarbeiter", "Total Net", "Währung", "Rechnungsstellung",
               "Status", "Zustand"]
# (Name, Klasse der Umschaltflaeche in Odoo 18, Klasse des Ansichtscontainers)
ANSICHTEN = [("Liste", "o_list", "o_list_view"), ("Kanban", "o_kanban", "o_kanban_view"),
             ("Pivot", "o_pivot", "o_pivot_view"), ("Graph", "o_graph", "o_graph_view"),
             ("Kalender", "o_calendar", "o_calendar_view")]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    p.add_argument("--ohne-screenshot", action="store_true")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    print("Instanz: %s (%s)" % (a.instanz, url))

    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    ok = fehler = 0
    js_fehler, rpc_fehler = [], []

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    def saeubere(t):
        return re.sub(r"\s+", " ", t or "").strip()

    def schuss(seite, name):
        if not a.ohne_screenshot:
            datei = os.path.join(VZ, name)
            seite.screenshot(path=datei, full_page=True)
            print("       Screenshot: %s" % datei)

    def kopfzeilen(seite):
        return seite.evaluate(
            "() => [...document.querySelectorAll('.o_list_view thead th')]"
            ".map(e => (e.innerText || '').trim()).filter(Boolean)")

    def ansicht_wechseln(seite, klasse):
        knopf = seite.query_selector(".o_switch_view.%s" % klasse)
        if not knopf:
            return False
        knopf.click()
        seite.wait_for_timeout(3500)
        return True

    def sichtbar(seite, selektor):
        return bool(seite.evaluate(
            "(s) => [...document.querySelectorAll(s)].some(e => e.getClientRects().length)", selektor))

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_verkauf_ansichten_%s" % a.instanz),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1400})
        ctx.add_init_script(
            "window.__errs=[];"
            "window.addEventListener('error', e => window.__errs.push(''+e.message));"
            "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));"
            "const ce=console.error; console.error=(...x)=>{window.__errs.push(x.map(String).join(' ')); ce(...x);};")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.on("response", lambda r: rpc_fehler.append("%s %s" % (r.status, r.url))
                 if ("/web/dataset/call_kw" in r.url and r.status >= 400) else None)

        print("\n--- 1. Angebotsliste: Spalten ---")
        seite.goto("%s/odoo/action-430" % url)
        seite.wait_for_selector(".o_list_view", timeout=90000)
        seite.wait_for_timeout(4000)
        spalten = kopfzeilen(seite)
        print("       Kopfzeilen: %s" % ", ".join(spalten))
        pruefe("Bestelldatum" in spalten,
               "Spalte 'Bestelldatum' ist in der Liste sichtbar (Odoo 11: Bestelldatum)")
        for spalte in ("Nummer", "Kunde", "Nettobetrag"):
            pruefe(spalte in spalten, "Spalte '%s' vorhanden" % spalte)
        pruefe(len(spalten) >= 8, "Liste zeigt %d Spalten" % len(spalten))
        schuss(seite, "22_Liste_Bestelldatum_%s.png" % a.instanz)

        print("\n--- 2. Spaltenauswahl (optionale Spalten) ---")
        knopf = seite.query_selector(".o_optional_columns_dropdown_toggle")
        if knopf:
            knopf.click()
            seite.wait_for_timeout(1500)
            auswahl = saeubere(seite.evaluate("""() => {
                const d = [...document.querySelectorAll('.o-dropdown--menu, .dropdown-menu')]
                    .filter(e => e.getClientRects().length);
                return d.length ? d[d.length-1].innerText : '';
            }"""))
            print("       Auswahl: %s" % auswahl[:200])
            pruefe("Bestelldatum" in auswahl, "Spaltenauswahl enthaelt 'Bestelldatum'")
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(800)
        else:
            pruefe(False, "Spaltenauswahl nicht gefunden")

        print("\n--- 3. Ansichten umschalten ---")
        for name, schalter, klasse in ANSICHTEN[1:]:
            if ansicht_wechseln(seite, schalter):
                da = sichtbar(seite, ".%s" % klasse)
                pruefe(da, "Ansicht '%s' geoeffnet (%s)" % (name, klasse))
                if name == "Kalender":
                    inhalt = saeubere(seite.eval_on_selector(".o_calendar_view", "e => e ? e.innerText : ''"))
                    print("       Kalenderinhalt (Auszug): %s" % inhalt[:120])
                    schuss(seite, "26_Kalender_%s.png" % a.instanz)
                elif name == "Graph":
                    schuss(seite, "25_Graph_%s.png" % a.instanz)
                elif name == "Pivot":
                    schuss(seite, "24_Pivot_%s.png" % a.instanz)
                else:
                    schuss(seite, "23_Kanban_%s.png" % a.instanz)
            else:
                pruefe(False, "Ansicht '%s' nicht umschaltbar" % name)

        print("\n--- 4. Zurueck zur Liste ---")
        if ansicht_wechseln(seite, "o_list"):
            pruefe(sichtbar(seite, ".o_list_view"), "Liste wieder geoeffnet")
        else:
            pruefe(False, "Zurueck zur Liste nicht moeglich")

        js_fehler[:] = seite.evaluate("() => window.__errs") or []
        ctx.close()

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    print("JavaScript-Fehler: %d %s" % (len(js_fehler), js_fehler[:3]))
    print("RPC-Fehler: %d %s" % (len(rpc_fehler), rpc_fehler[:3]))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
