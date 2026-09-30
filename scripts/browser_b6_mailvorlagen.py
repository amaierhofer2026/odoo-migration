"""B6 Mailvorlagen: Browser-Test auf der VM (read-only, kein Versand).

Prueft im echten Browser:
 1. Die beiden ITK-Rechnungsvorlagen sind in der Vorlagenliste sichtbar.
 2. Im Massenversand-Dialog der Rechnung ist die ITK-Vorlage auswaehlbar; Auswahl und Text
    werden angezeigt.

Der Dialog wird nur geoeffnet und verworfen, es wird nichts versendet und nichts gespeichert.

Aufruf:  uv run --with playwright python scripts/browser_b6_mailvorlagen.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "b6")
NAMEN = ["Rechnungsstellung: Allgemeine Rechnung",
         "Rechnungsstellung: Ihr Abonnement für help-amtsweg.gv.at"]


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

    beleg = kw("account.move", "search_read",
               [[("move_type", "=", "out_invoice"), ("state", "=", "posted")],
                ["id", "name"]], order="id desc", limit=1)[0]
    zahlungen = kw("mail.mail", "search_count", [[]])
    print("Instanz: %s" % url)
    print("Beleg  : %s %s | mail.mail vorher: %s" % (beleg["id"], beleg["name"], zahlungen))

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
                                       "pw_b6_%s_%s" % (a.instanz, os.getpid())),
            channel="chrome", headless=True, viewport={"width": 1800, "height": 1300})
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

        print("\n--- 1. Vorlagenliste (E-Mail-Vorlagen) ---")
        seite.goto("%s/odoo/action-133?view_type=list" % url)
        seite.wait_for_timeout(6000)
        liste = sichtbar(".o_list_view .o_data_row")
        print("    erste Zeilen: %s" % liste[:4])
        gefunden = [n for n in NAMEN if any(n[:38] in z for z in liste)]
        pruefe(len(gefunden) == 2, "beide ITK-Vorlagen in der Liste sichtbar (%d von 2)" % len(gefunden))
        seite.screenshot(path=os.path.join(VZ, "01_Vorlagenliste.png"), full_page=True)

        print("\n--- 2. Massenversand-Dialog der Rechnung ---")
        seite.goto("%s/odoo/m-account.move/%s" % (url, beleg["id"]))
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(4000)
        menue = None
        for el in seite.query_selector_all(".o_cp_action_menus button, .o_control_panel .o_cp_action_menus button"):
            if el.is_visible():
                menue = el
                break
        pruefe(menue is not None, "Aktionsmenue gefunden")
        if menue is not None:
            menue.click()
            seite.wait_for_timeout(2000)
            eintraege = sichtbar(".o-dropdown--menu .dropdown-item, .dropdown-menu .dropdown-item")
            print("    Eintraege: %s" % eintraege)
            ziel = None
            for el in seite.query_selector_all(".dropdown-item"):
                if el.is_visible() and "Massenversand" in (el.inner_text() or ""):
                    ziel = el
                    break
            pruefe(ziel is not None, "Eintrag 'Massenversand Rechnungen per Email' vorhanden")
            if ziel is not None:
                ziel.click()
                seite.wait_for_timeout(6000)
                feld = seite.query_selector(".o_dialog .o_field_widget[name='template_id']")
                pruefe(feld is not None, "Vorlagenfeld im Dialog vorhanden")
                optionen = []
                if feld is not None:
                    knopf = feld.query_selector("button") or feld
                    knopf.click()
                    seite.wait_for_timeout(2500)
                    optionen = seite.evaluate("""() => [...document.querySelectorAll(
                        '.o-autocomplete--dropdown-item, .dropdown-menu .dropdown-item')]
                        .filter(e => e.getClientRects().length).map(e => e.innerText.trim())""")
                print("    Vorlagen im Dialog: %s" % optionen)
                treffer = [n for n in NAMEN if n in optionen]
                pruefe(len(treffer) == 2,
                       "beide ITK-Vorlagen im Dialog auswaehlbar (%d von 2)" % len(treffer))
                # ITK-Vorlage waehlen und Wirkung im Dialog pruefen
                gewaehlt = False
                for el in seite.query_selector_all(".o-autocomplete--dropdown-item, .dropdown-menu .dropdown-item"):
                    if el.is_visible() and (el.inner_text() or "").strip() == NAMEN[0]:
                        el.click()
                        gewaehlt = True
                        break
                pruefe(gewaehlt, "ITK-Vorlage 'Allgemeine Rechnung' angeklickt")
                seite.wait_for_timeout(4000)
                betreff = seite.evaluate("""() => {
                    const f = document.querySelector('.o_dialog .o_field_widget[name="subject"] input');
                    return f ? f.value : '';
                }""")
                print("    Betreff im Dialog: %s" % betreff)
                pruefe("Rechnung (Ref" in (betreff or ""),
                       "Betreff aus der ITK-Vorlage uebernommen (Rendern je Empfaenger beim Senden)")
                seite.screenshot(path=os.path.join(VZ, "02_Massenversand_Dialog.png"), full_page=True)
                print("    Screenshot: %s" % os.path.join(VZ, "02_Massenversand_Dialog.png"))
                for el in seite.query_selector_all(".o_dialog button, .modal button"):
                    if el.is_visible() and (el.inner_text() or "").strip() in ("Verwerfen", "Abbrechen", "Discard"):
                        el.click()
                        break
                seite.wait_for_timeout(2500)

        js_fehler.extend(seite.evaluate("window.__errs") or [])
        pruefe(not js_fehler, "keine JavaScript-Fehler (%d)" % len(js_fehler))
        pruefe(not rpc_fehler, "keine RPC-Fehler (%d)" % len(rpc_fehler))
        if js_fehler:
            print("       JS: %s" % js_fehler[:3])
        if rpc_fehler:
            print("       RPC: %s" % rpc_fehler[:3])
        ctx.close()

    nachher = kw("mail.mail", "search_count", [[]])
    print("\nmail.mail nachher: %s (vorher %s)" % (nachher, zahlungen))
    pruefe(nachher == zahlungen, "kein Versand ausgeloest (unveraendert)")
    print("\n%d OK / %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
