"""Browser-Abnahme Bereich Verkauf Teil 1 (Session 121): sichtbare Menues.

Oeffnet die App "Verkauf" im echten Browser (Playwright + Chrome, headless), klickt die
Menuegruppen Auftraege, Abzurechnen, Produkte, Berichtswesen und Konfiguration und liest die
sichtbaren Menuepunkte. Zaehlt JS- und RPC-Fehler. Read-only (kein Schreiben in Odoo).

Aufruf:
    uv run --with playwright python scripts/browser_verkauf_menue.py --instanz vm
    uv run --with playwright python scripts/browser_verkauf_menue.py --instanz lokal
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session121")

ERWARTET = {
    "Aufträge": ["Alle Auftragszeilen", "Angebote", "Aufträge", "Verkaufsteams", "Kunden"],
    "Abzurechnen": ["Abzurechnende Aufträge", "Aufträge für Upselling"],
    "Produkte": ["Produkte", "Produktvarianten", "Preislisten"],
    "Berichtswesen": ["Verkauf", "Vertriebsmitarbeiter", "Produkte", "Kunden"],
    "Konfiguration": ["Einstellungen", "Verkaufsteams", "Angebotsvorlagen", "Kopf-/Fußzeilen",
                      "Stichwörter", "Attribute", "Produktkategorien", "Zahlungsanbieter",
                      "Zahlungsmethoden"],
}
# Odoo 11 hatte diese Untergruppe; in Odoo 18 erscheint sie im Menue nur als Abschnittstitel
# (nicht als klickbarer Eintrag). Deshalb wird sie im Text des geoeffneten Menues geprueft.
GRUPPENTEXT = {"Konfiguration": ["Verkaufsaufträge"]}
NICHT_ERWARTET = ["Verkaufsaufträge aller Kanäle", "Reportlayout Kategorien", "Reklamationen"]


def lade_env(pfad):
    werte = {}
    for zeile in open(pfad, encoding="utf-8"):
        if "=" in zeile and not zeile.strip().startswith("#"):
            k, v = zeile.split("=", 1)
            werte[k.strip()] = v.strip().strip('"')
    return werte


def rpc_client(url, db, user, pwd):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rufe(pfad, prm):
        req = urllib.request.Request(url + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                                  "params": prm}).encode(),
                                     headers={"Content-Type": "application/json"})
        with op.open(req, timeout=180) as f:
            return json.loads(f.read().decode())

    rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})
    sid = next((c.value for c in jar if c.name == "session_id"), None)

    def kw(model, methode, args, **kwargs):
        o = rufe("/web/dataset/call_kw", {"model": model, "method": methode, "args": args, "kwargs": kwargs})
        if "error" in o:
            raise RuntimeError(str(o["error"].get("data", {}).get("message"))[:200])
        return o.get("result")

    return sid, kw


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    p.add_argument("--ohne-screenshot", action="store_true")
    p.add_argument("--probe", action="store_true", help="nur DOM-Struktur ausgeben")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    kwurzel = kw("ir.ui.menu", "search_read",
                 [[("parent_id", "=", False), ("name", "=", "Verkauf")], ["id", "name"]],
                 context={"lang": "de_DE"})
    mid = kwurzel[0]["id"] if kwurzel else 255
    print("Instanz   : %s (%s), Wurzelmenue Verkauf id %s" % (a.instanz, url, mid))

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

    def saeubere(text):
        return re.sub(r"\s+", " ", text or "").strip()

    mit = sync_playwright() if True else None
    with mit as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_verkauf_%s_%s" % (a.instanz, os.getpid())),
            channel="chrome", headless=True, viewport={"width": 1800, "height": 1300})
        ctx.add_init_script(
            "window.__errs=[];"
            "window.addEventListener('error', e => window.__errs.push(''+e.message));"
            "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));"
            "const ce=console.error; console.error=(...x)=>{window.__errs.push(x.map(String).join(' ')); ce(...x);};")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.on("response", lambda r: rpc_fehler.append("%s %s" % (r.status, r.url))
                 if ("/web/dataset/call_kw" in r.url and r.status >= 400) else None)

        def schuss(name):
            if not a.ohne_screenshot:
                datei = os.path.join(VZ, name)
                seite.screenshot(path=datei, full_page=True)
                print("       Screenshot: %s" % datei)

        seite.goto("%s/web#menu_id=%s" % (url, mid))
        seite.wait_for_selector(".o_main_navbar", timeout=90000)
        seite.wait_for_timeout(4000)

        def abschnitte():
            return seite.eval_on_selector_all(
                ".o_main_navbar .o_menu_sections button, .o_main_navbar .o_menu_sections a",
                "els => els.map(e => e.innerText.trim()).filter(t => t)")

        def dropdown():
            """Sichtbare Eintraege des gerade geoeffneten Menue-Popovers (Odoo 18: o-dropdown--menu).

            Der Selektor muss ohne Praefix '.o_main_navbar' arbeiten: Odoo 18 haengt das Popover
            an das Ende des Body (Befund Session 121). Sichtbarkeit ueber getClientRects pruefen -
            offsetParent ist bei position:fixed-Elementen null und liefert falsche Ergebnisse.
            """
            return seite.evaluate("""() => {
                const boxen = [...document.querySelectorAll('.o-dropdown--menu.dropdown-menu')]
                    .filter(e => e.getClientRects().length);
                const box = boxen[boxen.length - 1];
                if (!box) return [];
                return [...box.querySelectorAll('.dropdown-item')]
                    .filter(e => e.getClientRects().length)
                    .map(e => e.innerText.trim()).filter(t => t);
            }""")

        def dropdown_text():
            """Gesamter Text des geoeffneten Menues (inkl. nicht klickbarer Abschnittstitel)."""
            return saeubere(seite.evaluate("""() => {
                const boxen = [...document.querySelectorAll('.o-dropdown--menu.dropdown-menu')]
                    .filter(e => e.getClientRects().length);
                const box = boxen[boxen.length - 1];
                return box ? box.innerText : '';
            }"""))

        app = saeubere(seite.inner_text(".o_main_navbar .o_menu_brand") if seite.query_selector(".o_main_navbar .o_menu_brand") else "")
        sichtbar = saeubere(seite.inner_text(".o_main_navbar"))
        print("\n--- 1. App und Menuegruppen ---")
        print("       Navbar: %s" % sichtbar[:200])
        pruefe("Verkauf" in app or "Verkauf" in sichtbar, "App 'Verkauf' geoeffnet (brand='%s')" % app)
        gr = abschnitte()
        print("       Menuegruppen: %s" % gr)
        for name in ERWARTET:
            pruefe(name in gr, "Menuegruppe '%s' sichtbar" % name)
        for name in NICHT_ERWARTET:
            pruefe(name not in sichtbar, "Menuepunkt '%s' nicht sichtbar (wie dokumentiert)" % name)
        schuss("01_App_Verkauf.png")

        if a.probe:
            print("\n       Probe: Dropdowns ohne Klick: %s" % dropdown())
            print("\n%d OK / %d FEHL" % (ok, fehler))
            return 1 if fehler else 0

        print("\n--- 2. Menuepunkte je Gruppe (echte Klicks) ---")
        eintraege = []
        for name, soll in ERWARTET.items():
            treffer = None
            for i, g in enumerate(gr):
                if g == name:
                    treffer = i
                    break
            if treffer is None:
                pruefe(False, "Gruppe '%s' nicht anklickbar" % name)
                continue
            knopf = seite.query_selector_all(".o_main_navbar .o_menu_sections button, .o_main_navbar .o_menu_sections a")
            knopf[treffer].click()
            seite.wait_for_timeout(1200)
            texte = dropdown()
            komplett = dropdown_text()
            eintraege.extend(texte)
            print("       %-16s -> %s" % (name, texte))
            pruefe(bool(texte), "Klick auf '%s' oeffnet das Menue (%d Eintraege)" % (name, len(texte)))
            for punkt in soll:
                pruefe(any(punkt.lower() in saeubere(t).lower() for t in texte),
                       "Menuepunkt '%s' unter '%s' sichtbar" % (punkt, name))
            for punkt in GRUPPENTEXT.get(name, []):
                pruefe(punkt.lower() in komplett.lower(),
                       "Menuegruppe '%s' im Menue '%s' vorhanden" % (punkt, name))
            schuss("02_Menue_%s.png" % re.sub(r"[^A-Za-z]", "", name)[:12])
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(600)

        print("\n--- 3. Gegenprobe und Fehlerzähler ---")
        alle = " | ".join(eintraege)
        for name in NICHT_ERWARTET:
            pruefe(name not in alle, "Menuepunkt '%s' in keiner Gruppe sichtbar" % name)
        js_fehler.extend(seite.evaluate("window.__errs") or [])
        pruefe(not js_fehler, "keine JavaScript-Fehler (%d)" % len(js_fehler))
        pruefe(not rpc_fehler, "keine RPC-Fehler (HTTP >= 400) (%d)" % len(rpc_fehler))
        if js_fehler:
            print("       JS: %s" % js_fehler[:3])
        if rpc_fehler:
            print("       RPC: %s" % rpc_fehler[:3])
        ctx.close()

    print("\n%d OK / %d FEHL" % (ok, fehler))
    print("Odoo wurde nur lesend verwendet (Browser-Aufrufe ohne Speichern).")
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
