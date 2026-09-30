"""Teil 4: Browser-Abnahme der Rechnungsliste auf der VM (read-only).

Prueft im echten Browser: Listenspalten, Suchfilter und Gruppierungen sowie die
ITK-Massenaktionen im Aktionsmenue (inklusive Dialog der Massenbearbeitung).
Es wird nichts gespeichert.

Aufruf:  uv run --with playwright python scripts/browser_teil4_rechnungsliste.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "teil4")
ITK_AKTIONEN = ["Valorisierungstext ändern", "Zahlungsbedingungen setzen Abrechnung",
                "Rechnungsdatum Abrechnung", "Leistungszeitraum setzen", "Projektkategorie setzen"]
ERWARTETE_FILTER = ["Meine Rechnungen", "Zu zahlen", "Überfällig"]
ERWARTETE_GRUPPEN = ["Kunde", "Vertriebsmitarbeiter", "Verkaufsteam", "Status"]
ERWARTETE_SPALTEN = ["Rechnungsdatum", "Gesamt", "Status"]


def lade_env(pfad):
    werte = {}
    for zeile in open(pfad, encoding="utf-8"):
        if "=" in zeile and not zeile.strip().startswith("#"):
            k, v = zeile.split("=", 1)
            werte[k.strip()] = v.strip().strip('"')
    return werte


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"

    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rufe(pfad, prm):
        req = urllib.request.Request(url + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                                  "params": prm}).encode(),
                                     headers={"Content-Type": "application/json"})
        with op.open(req, timeout=180) as f:
            return json.loads(f.read().decode())

    rufe("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                       "password": env["ODOO18_PWD"]})
    sid = next(c.value for c in jar if c.name == "session_id")

    def kw(model, methode, args, **kwargs):
        o = rufe("/web/dataset/call_kw", {"model": model, "method": methode, "args": args, "kwargs": kwargs})
        if "error" in o:
            raise RuntimeError(str(o["error"])[:200])
        return o.get("result")

    anzahl = kw("account.move", "search_count", [[("move_type", "=", "out_invoice")]])
    print("Instanz: %s | Ausgangsrechnungen im Testbestand: %s" % (url, anzahl))

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

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"),
                                       "pw_teil4_%s_%s" % (a.instanz, os.getpid())),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1300})
        ctx.add_init_script(
            "window.__errs=[];"
            "window.addEventListener('error', e => window.__errs.push(''+e.message));"
            "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));"
            "const ce=console.error; console.error=(...x)=>{window.__errs.push(x.map(String).join(' ')); ce(...x);};")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.on("response", lambda resp: rpc_fehler.append("%s %s" % (resp.status, resp.url))
                 if ("/web/dataset/call_kw" in resp.url and resp.status >= 400) else None)

        def sichtbar(sel):
            return seite.evaluate("""(sel) => [...document.querySelectorAll(sel)]
                .filter(e => e.getClientRects().length)
                .map(e => e.innerText.replace(/\\s+/g, ' ').trim()).filter(t => t)""", sel)

        seite.goto("%s/odoo/action-354" % url)
        seite.wait_for_selector(".o_list_view, .o_list_renderer", timeout=90000)
        seite.wait_for_timeout(5000)

        print("\n--- 1. Listenspalten ---")
        spalten = seite.evaluate("""() => [...document.querySelectorAll('.o_list_view thead th, .o_list_renderer thead th')]
            .map(e => e.innerText.replace(/\\s+/g, ' ').trim()).filter(t => t)""")
        print("    %s" % spalten)
        for w in ERWARTETE_SPALTEN:
            pruefe(any(w in s for s in spalten), "Spalte '%s' vorhanden" % w)
        seite.screenshot(path=os.path.join(VZ, "01_Rechnungsliste.png"), full_page=True)

        print("\n--- 2. Suchfilter und Gruppierungen ---")
        gesammelt = []

        def menue_texte():
            return seite.evaluate("""() => [...document.querySelectorAll('.o-dropdown--menu *, .dropdown-menu *')]
                .filter(e => e.getClientRects().length && e.children.length === 0)
                .map(e => e.innerText.replace(/\\s+/g, ' ').trim()).filter(t => t)""")

        toggler = seite.query_selector(".o_searchview_dropdown_toggler")
        pruefe(toggler is not None, "Suchmenue-Knopf vorhanden")
        if toggler is not None:
            toggler.click()
            seite.wait_for_timeout(2000)
            gesammelt += menue_texte()
            for beschriftung in ("Filter", "Gruppieren nach"):
                for el in seite.query_selector_all(".o-dropdown--menu .dropdown-item, .o-dropdown--menu .o_menu_item"):
                    if (el.inner_text() or "").strip().startswith(beschriftung):
                        el.hover()
                        seite.wait_for_timeout(1200)
                        unter = menue_texte()
                        gesammelt += unter
                        print("    %s: %s" % (beschriftung, [t for t in unter if t not in ("Filter", "Gruppieren nach")][:16]))
                        break
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(800)
        print("    gesammelte Eintraege: %d" % len(gesammelt))
        for w in ERWARTETE_FILTER:
            pruefe(any(w == t or w in t for t in gesammelt), "Filter '%s' vorhanden" % w)
        for w in ERWARTETE_GRUPPEN:
            pruefe(any(w in t for t in gesammelt), "Gruppierung '%s' vorhanden" % w)

        print("\n--- 3. Aktionsmenue mit ITK-Massenaktionen ---")
        # alle Zeilen markieren
        kasten = seite.query_selector(".o_list_view thead input[type=checkbox], .o_list_renderer thead input[type=checkbox]")
        if kasten is not None:
            kasten.click()
            seite.wait_for_timeout(2000)
        menue = None
        for el in seite.query_selector_all("button"):
            if el.is_visible() and (el.inner_text() or "").strip().startswith("Aktionen"):
                menue = el
                break
        pruefe(menue is not None, "Aktionsmenue gefunden")
        gefunden = []
        if menue is not None:
            menue.click()
            seite.wait_for_timeout(2500)
            eintraege = sichtbar(".o-dropdown--menu .dropdown-item, .dropdown-menu .dropdown-item")
            print("    Aktionen: %s" % eintraege)
            gefunden = [w for w in ITK_AKTIONEN if any(w in e for e in eintraege)]
            pruefe(len(gefunden) >= 4,
                   "ITK-Massenaktionen im Menue vorhanden (%d von %d: %s)"
                   % (len(gefunden), len(ITK_AKTIONEN), gefunden))
            seite.screenshot(path=os.path.join(VZ, "02_Aktionsmenue.png"), full_page=True)

            print("\n--- 4. Massenbearbeitungs-Dialog ---")
            ziel = None
            for el in seite.query_selector_all(".dropdown-item"):
                if el.is_visible() and "Valorisierungstext" in (el.inner_text() or ""):
                    ziel = el
                    break
            if ziel is not None:
                ziel.click()
                seite.wait_for_timeout(5000)
                dialog = sichtbar(".o_dialog, .modal")
                print("    Dialog: %s" % (dialog[0][:160] if dialog else "keiner"))
                pruefe(bool(dialog), "Massenbearbeitungs-Dialog geoeffnet")
                felder = seite.evaluate("""() => [...document.querySelectorAll('.o_dialog .o_field_widget, .modal .o_field_widget')]
                    .map(e => e.getAttribute('name')).filter(t => t)""")
                print("    Felder: %s" % felder)
                pruefe(any("valorisierung" in (f or "") for f in felder),
                       "Feld Valorisierungstext im Dialog")
                seite.screenshot(path=os.path.join(VZ, "03_Massenbearbeitung.png"), full_page=True)
                for el in seite.query_selector_all(".o_dialog button, .modal button"):
                    if el.is_visible() and (el.inner_text() or "").strip() in ("Verwerfen", "Abbrechen", "Schliessen", "Discard"):
                        el.click()
                        break
                seite.wait_for_timeout(2500)
            else:
                pruefe(False, "Massenaktion 'Valorisierungstext ändern' im Menue gefunden")

        js_fehler.extend(seite.evaluate("window.__errs") or [])
        pruefe(not js_fehler, "keine JavaScript-Fehler (%d)" % len(js_fehler))
        pruefe(not rpc_fehler, "keine RPC-Fehler (%d)" % len(rpc_fehler))
        if js_fehler:
            print("       JS: %s" % js_fehler[:3])
        if rpc_fehler:
            print("       RPC: %s" % rpc_fehler[:3])
        ctx.close()

    print("\n%d OK / %d FEHL" % (ok, fehler))
    print("Screenshots: %s" % VZ)
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
