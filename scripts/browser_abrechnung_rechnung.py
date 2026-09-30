"""Browser-Spotcheck Abrechnung Teil 3: gebuchte Rechnung auf der VM (read-only).

Prueft im echten Browser: Reiter, Statusleiste, Kopf-Buttons, Smart Buttons, Drucken-Knopf
(PDF-Download) und das Drucken-Menue im Aktionsmenue. Es wird nichts gespeichert.

Aufruf:  uv run --with playwright python scripts/browser_abrechnung_rechnung.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "teil3")


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
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

    kandidaten = kw("account.move", "search_read",
                    [[("move_type", "=", "out_invoice"), ("state", "=", "posted")],
                     ["id", "name", "partner_id", "amount_total", "payment_state", "payment_count"]],
                    order="id desc", limit=1)
    r = kandidaten[0]
    print("Instanz: %s (%s)" % (a.instanz, url))
    print("Beleg  : id %s | %s | %s | %s | %s | Zahlungen %s"
          % (r["id"], r["name"], r["partner_id"][1], r["amount_total"], r["payment_state"],
             r["payment_count"]))

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
                                       "pw_abrechnung_rechnung_%s_%s" % (a.instanz, os.getpid())),
            channel="chrome", headless=True, viewport={"width": 1800, "height": 1400},
            accept_downloads=True)
        ctx.add_init_script(
            "window.__errs=[];"
            "window.addEventListener('error', e => window.__errs.push(''+e.message));"
            "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));"
            "const ce=console.error; console.error=(...x)=>{window.__errs.push(x.map(String).join(' ')); ce(...x);};")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.on("response", lambda resp: rpc_fehler.append("%s %s" % (resp.status, resp.url))
                 if ("/web/dataset/call_kw" in resp.url and resp.status >= 400) else None)

        def sichtbare(sel):
            return seite.evaluate("""(sel) => [...document.querySelectorAll(sel)]
                .filter(e => e.getClientRects().length)
                .map(e => e.innerText.replace(/\\s+/g, ' ').trim()).filter(t => t)""", sel)

        seite.goto("%s/odoo/m-account.move/%s" % (url, r["id"]))
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(4000)

        reiter = seite.evaluate("""() => [...document.querySelectorAll('.o_notebook .nav-link, .o_notebook .nav-item a')]
            .map(e => e.innerText.trim()).filter(t => t)""")
        buttons = sichtbare(".o_statusbar_buttons button, .o_form_statusbar button.btn")
        smart = sichtbare(".oe_stat_button")
        status = seite.evaluate("""() => {
            const akt = document.querySelector('.o_statusbar_status .o_arrow_button_current');
            return akt ? akt.innerText.trim() : '';
        }""")

        print("\n--- 1. Formular der gebuchten Rechnung ---")
        print("  Reiter        : %s" % reiter)
        print("  Status        : %s" % status)
        print("  Kopf-Buttons  : %s" % buttons)
        print("  Smart Buttons : %s" % smart)
        pruefe(any(r.startswith("Rechnungszeilen") for r in reiter), "Reiter 'Rechnungszeilen' sichtbar")
        pruefe(any("Weitere Informationen" in r for r in reiter), "Reiter 'Weitere Informationen' sichtbar")
        pruefe("Gebucht" in status, "Statusleiste zeigt 'Gebucht'")
        pruefe(any("Senden" in b for b in buttons), "Button 'Senden' sichtbar")
        pruefe(any("Drucken" in b for b in buttons), "Button 'Drucken' sichtbar")
        pruefe(any("Gutschrift" in b for b in buttons), "Button 'Gutschrift' sichtbar")
        pruefe(any("Auf Entwurf zurücksetzen" in b for b in buttons),
               "Button 'Auf Entwurf zurücksetzen' sichtbar")
        pruefe(any("Zahlungen" in s for s in smart),
               "Smart Button mit Zahlungen sichtbar (%s)" % smart)
        seite.screenshot(path=os.path.join(VZ, "01_Rechnung_gebucht.png"), full_page=True)
        print("       Screenshot: %s" % os.path.join(VZ, "01_Rechnung_gebucht.png"))

        print("\n--- 2. Knopf 'Drucken' (PDF) ---")
        try:
            with seite.expect_download(timeout=25000) as dl:
                for el in seite.query_selector_all("button"):
                    if el.is_visible() and el.inner_text().strip() == "Drucken":
                        el.click()
                        break
            datei = dl.value
            print("  Download      : %s" % datei.suggested_filename)
            pruefe(datei.suggested_filename.lower().endswith(".pdf"),
                   "Klick auf 'Drucken' erzeugt ein PDF (%s)" % datei.suggested_filename)
        except Exception as fehler:
            pruefe(False, "Klick auf 'Drucken' hat kein PDF erzeugt (%s)" % str(fehler)[:80])
            seite.keyboard.press("Escape")

        print("\n--- 3. Drucken-Menue im Aktionsmenue ---")
        geoeffnet = False
        for sel in (".o_cp_action_menus button", ".o_control_panel .o_cp_action_menus button",
                    "button[data-menu='action']"):
            kn = seite.query_selector_all(sel)
            if kn:
                kn[0].click()
                seite.wait_for_timeout(2000)
                geoeffnet = True
                break
        if geoeffnet:
            eintraege = sichtbare(".o-dropdown--menu .dropdown-item, .dropdown-menu .dropdown-item")
            print("  Aktionsmenue  : %s" % eintraege)
            druck = None
            for el in seite.query_selector_all(".dropdown-item, .o_menu_item"):
                if el.is_visible() and el.inner_text().strip().startswith("Drucken"):
                    druck = el
                    break
            if druck:
                druck.click()
                seite.wait_for_timeout(2000)
                berichte = sichtbare(".o-dropdown--menu .dropdown-item, .dropdown-menu .dropdown-item")
                print("  Drucken-Menue : %s" % berichte)
                pruefe(bool(berichte), "Drucken-Menue listet Berichte (%d)" % len(berichte))
                seite.screenshot(path=os.path.join(VZ, "02_Drucken_Menue.png"), full_page=True)
                print("       Screenshot: %s" % os.path.join(VZ, "02_Drucken_Menue.png"))
            else:
                print("  (kein Drucken-Menue im Aktionsmenue gefunden)")
            seite.keyboard.press("Escape")
        else:
            print("  (Aktionsmenue nicht gefunden)")

        print("\n--- 4. Reiter 'Weitere Informationen' ---")
        for el in seite.query_selector_all(".o_notebook .nav-link"):
            if el.inner_text().strip().startswith("Weitere Informationen"):
                el.click()
                seite.wait_for_timeout(1800)
                break
        gruppen = seite.evaluate("""() => {
            const namen = [...document.querySelectorAll('.o_group_name, .o_inner_group > .o_group_name, .o_wrap_label')]
                .filter(e => e.getClientRects().length)
                .map(e => e.innerText.replace(/\\s+/g, ' ').trim()).filter(t => t);
            return [...new Set(namen)];
        }""")
        print("  Gruppen       : %s" % gruppen)
        pruefe(bool(gruppen), "Gruppen im Reiter 'Weitere Informationen' sichtbar (%d)" % len(gruppen))
        seite.screenshot(path=os.path.join(VZ, "03_Weitere_Informationen.png"), full_page=True)

        print("\n--- 5. Fehlerzaehler ---")
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
