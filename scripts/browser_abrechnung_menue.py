"""Browser-Spotcheck Bereich Abrechnung (Session 122): sichtbare Menues auf der VM.

Vorgehen: zuerst die fuer den Benutzer sichtbaren Menues per RPC lesen (OHNE
ir.ui.menu.full_list, also genau die Sichtbarkeit des angemeldeten Benutzers), dann dieselbe App
im echten Browser (Playwright + Chrome, headless) oeffnen, alle Menuegruppen anklicken und die
sichtbaren Menuepunkte auslesen. Verglichen wird RPC-Sichtbarkeit gegen Browser-Sichtbarkeit.
Read-only, kein Speichern. JavaScript- und RPC-Fehler werden mitgezaehlt.

Aufruf:
    uv run --with playwright python scripts/browser_abrechnung_menue.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122")
WURZEL = "Rechnungsstellung"
# Gegenprobe: in Odoo 11 vorhandene, in Odoo 18 nicht mehr vorhandene Berichte
NICHT_ERWARTET = ["Umsatzsteuerbericht", "Audit Journale", "alter Partner Saldo",
                  "Vorläufige Bilanz", "Gewinn und Verlust", "Partner-Kontoauszug",
                  "Umsätze nach Konten und Perioden"]
# Bekannte, dokumentierte Abweichung: Menue im Menuebaum vorhanden, aber vom Web-Client nicht
# ausgeliefert (Befund F57, 30.09.2026). Grund: Odoo-18-Client liefert einen reduzierten
# Menuebaum; der Pruefpfad haengt an der aktivierten Pruefpfad-Funktion. Kein Handlungsbedarf.
BEKANNTE_ABWEICHUNG = {
    "Prüfpfad": "Odoo-18-Zusatzfunktion, im Browser nicht sichtbar (Befund F57)",
}


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


def rpc_menues(kw):
    """Sichtbare Menues unter der App-Wurzel (ohne full_list = Benutzersicht)."""
    alle = kw("ir.ui.menu", "search_read", [[], ["name", "parent_id"]], context={"lang": "de_DE"})
    nach_id = {m["id"]: m for m in alle}
    wurzel = [m for m in alle if not m["parent_id"] and m["name"] == WURZEL]
    if not wurzel:
        return None, [], {}
    wid = wurzel[0]["id"]
    kinder = {}
    for m in alle:
        pid = m["parent_id"][0] if m["parent_id"] else False
        kinder.setdefault(pid, []).append(m)
    abschnitte, punkte = [], {}
    for a in kinder.get(wid, []):
        abschnitte.append(a["name"])
        namen = []
        stapel = [a]
        while stapel:
            k = stapel.pop(0)
            for kind in kinder.get(k["id"], []):
                namen.append(kind["name"])
                stapel.append(kind)
        punkte.setdefault(a["name"], []).extend(namen)
    return wid, abschnitte, punkte


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    p.add_argument("--ohne-screenshot", action="store_true")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    wid, abschnitte, punkte = rpc_menues(kw)
    print("Instanz   : %s (%s)" % (a.instanz, url))
    print("RPC-Sichtbarkeit: Wurzelmenue '%s' id %s" % (WURZEL, wid))
    print("  Abschnitte: %s" % abschnitte)
    for k, v in punkte.items():
        print("  %-24s %s" % (k, v))
    rpc_alle = [n for v in punkte.values() for n in v]

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

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"),
                                       "pw_abrechnung_%s_%s" % (a.instanz, os.getpid())),
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

        seite.goto("%s/web#menu_id=%s" % (url, wid))
        seite.wait_for_selector(".o_main_navbar", timeout=90000)
        seite.wait_for_timeout(4000)

        def knoepfe():
            return seite.query_selector_all(".o_main_navbar .o_menu_sections button, "
                                            ".o_main_navbar .o_menu_sections a")

        def dropdown():
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
            """Volltext des geoeffneten Popovers (enthaelt auch Abschnittstitel ohne Aktion)."""
            return saeubere(seite.evaluate("""() => {
                const boxen = [...document.querySelectorAll('.o-dropdown--menu.dropdown-menu')]
                    .filter(e => e.getClientRects().length);
                const box = boxen[boxen.length - 1];
                return box ? box.innerText : '';
            }"""))

        marke = saeubere(seite.inner_text(".o_main_navbar .o_menu_brand")
                         if seite.query_selector(".o_main_navbar .o_menu_brand") else "")
        sichtbar = saeubere(seite.inner_text(".o_main_navbar"))
        print("\n--- 1. App und Menuegruppen im Browser ---")
        print("       Navbar: %s" % sichtbar[:250])
        kn = knoepfe()
        web_abschnitte = [saeubere(k.inner_text()) for k in kn]
        print("       Menuegruppen (klickbar): %s" % web_abschnitte)
        pruefe(WURZEL in marke or WURZEL in sichtbar,
               "App '%s' im Browser geoeffnet (brand='%s')" % (WURZEL, marke))
        schuss("01_App_Rechnungsstellung.png")

        print("\n--- 2. Jede Menuegruppe anklicken und Eintraege auslesen ---")
        web_punkte = {}
        web_texte = []
        for i, name in enumerate(web_abschnitte):
            kn = knoepfe()
            if i >= len(kn):
                break
            kn[i].click()
            seite.wait_for_timeout(1200)
            texte = dropdown()
            volltext = dropdown_text()
            web_punkte.setdefault(name, [])
            web_punkte[name].extend(texte)
            web_texte.append(volltext)
            print("       %-24s -> %s" % (name, texte))
            if volltext:
                print("       %-24s    (Popover-Text: %s)" % ("", volltext[:180]))
            pruefe(bool(texte), "Klick auf '%s' oeffnet das Menue (%d Eintraege)" % (name, len(texte)))
            schuss("02_Menue_%s.png" % re.sub(r"[^A-Za-z]", "", name)[:14])
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(600)

        print("\n--- 3. Abgleich RPC-Sichtbarkeit gegen Browser ---")
        web_alle = [n for v in web_punkte.values() for n in v]
        web_text = " | ".join(web_abschnitte + web_alle + web_texte)
        fehlend = [n for n in rpc_alle if n not in web_text and n not in BEKANNTE_ABWEICHUNG]
        abweichung = [n for n in rpc_alle if n not in web_text and n in BEKANNTE_ABWEICHUNG]
        print("       RPC-sichtbare Menuepunkte: %d | im Browser gefunden: %d | dokumentierte Abweichung: %d"
              % (len(rpc_alle), len(rpc_alle) - len(fehlend) - len(abweichung), len(abweichung)))
        for n in abweichung:
            print("       HINWEIS '%s' im Browser nicht sichtbar: %s" % (n, BEKANNTE_ABWEICHUNG[n]))
        pruefe(not fehlend, "jeder laut RPC sichtbare Menuepunkt ist im Browser vorhanden "
                            "(ausser der dokumentierten Abweichung)")
        for n in fehlend:
            pruefe(False, "Menuepunkt '%s' fehlt im Browser" % n)

        print("\n--- 4. Gegenproben und Fehlerzaehler ---")
        for name in NICHT_ERWARTET:
            pruefe(name.lower() not in web_text.lower(),
                   "Odoo-11-Bericht '%s' nicht sichtbar (dokumentiert)" % name)
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
