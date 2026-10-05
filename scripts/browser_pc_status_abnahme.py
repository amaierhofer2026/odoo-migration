"""Browser-Abnahme: Project-Category-Spalte und Odoo-11-Statuskette (Odoo 18).

Prueft im echten Browser gegen lokale Instanz oder Test-VM:
  1. Ausgangsrechnungsliste: Spalte "Project Category" an der Position nach dem Status,
     mit echtem Wert aus der Datenbank.
  2. Kunden-Gutschriften: dieselbe Spalte in der eigenen Kundenliste.
  3. Rechnungsformular: Odoo-11-Statuskette fuer Entwurf, Offen, Teilzahlung, Bezahlt,
     Abgebrochen und Gutschrift; die Odoo-18-Statusleiste bleibt erhalten.
  4. Keine Odoo-18-Spalten oder -Funktionen entfernt.
Es wird nichts gespeichert.

Aufruf:
    uv run --with playwright python scripts/browser_pc_status_abnahme.py --instanz lokal
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKER = "TEST-PC-"
# Sichtbare Spalten der Kundenliste in Odoo 11 (Teil 4 dokumentiert) = Odoo-18-Bestand
ERWARTET_SPALTEN = ["Nummer", "Kunde", "Rechnungsdatum", "Fälligkeit", "Referenzbeleg",
                    "Referenz", "Exklusive Steuern", "Total", "Zu Bezahlen", "Status"]
ERWARTETE_KETTE = {"TEST-PC-1-entwurf": ("Entwurf", "Entwurf"),
                   "TEST-PC-2-offen": ("Offen", "Gebucht"),
                   "TEST-PC-3-teilzahlung": ("Offen", "Gebucht"),
                   "TEST-PC-4-bezahlt": ("Bezahlt", "Gebucht"),
                   "TEST-PC-5-abgebrochen": ("Abgebrochen", "Abgebrochen"),
                   "TEST-PC-6-gutschrift": ("Gutgeschrieben (Odoo 18)", "Gebucht")}
KETTE_STUFEN = ["Entwurf", "Offen", "Bezahlt", "Abgebrochen"]


def lade_env(pfad):
    werte = {}
    for zeile in open(pfad, encoding="utf-8"):
        if "=" in zeile and not zeile.strip().startswith("#"):
            k, v = zeile.split("=", 1)
            werte[k.strip()] = v.strip().strip('"')
    return werte


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="lokal")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session124",
                      "pc_und_statuskette", a.instanz)
    os.makedirs(VZ, exist_ok=True)

    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rufe(pfad, prm):
        req = urllib.request.Request(url + pfad, data=json.dumps(
            {"jsonrpc": "2.0", "method": "call", "params": prm}).encode(),
            headers={"Content-Type": "application/json"})
        with op.open(req, timeout=180) as f:
            return json.loads(f.read().decode())

    rufe("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                       "password": env["ODOO18_PWD"]})
    sid = next(c.value for c in jar if c.name == "session_id")

    def kw(model, methode, args, **kwargs):
        o = rufe("/web/dataset/call_kw", {"model": model, "method": methode,
                                          "args": args, "kwargs": kwargs})
        if "error" in o:
            raise RuntimeError(str(o["error"])[:300])
        return o.get("result")

    CTX = {"lang": "de_DE"}
    belege = kw("account.move", "search_read",
                [[["ref", "like", MARKER]],
                 ["id", "name", "ref", "state", "payment_state", "move_type"]], context=CTX)
    gutschrift = kw("account.move", "search_read",
                    [[["move_type", "=", "out_refund"], ["ref", "like", "Stornierung"]],
                     ["id", "name", "ref", "projectcategory_id"]], context=CTX, limit=1)
    print("Instanz: %s | Testbelege: %d | Kunden-Gutschrift: %s"
          % (url, len(belege), gutschrift))

    from playwright.sync_api import sync_playwright
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
                                       "pw_pc_%s_%s" % (a.instanz, os.getpid())),
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

        def liste_lesen(pfad, name):
            seite.goto("%s/odoo/%s" % (url, pfad))
            seite.wait_for_selector(".o_list_view, .o_list_renderer", timeout=90000)
            seite.wait_for_timeout(4000)
            daten = seite.evaluate("""() => {
                const kopf = document.querySelector('.o_list_renderer thead tr, .o_list_view thead tr');
                const ths = kopf ? [...kopf.querySelectorAll('th')].map(th => ({
                    i: th.cellIndex, t: th.innerText.replace(/\\s+/g, ' ').trim()})) : [];
                const zeilen = [...document.querySelectorAll('.o_data_row')].map(tr => ({
                    text: tr.innerText.replace(/\\s+/g, ' ').trim(),
                    zellen: [...tr.querySelectorAll('td')].reduce((a, td) => {
                        a[td.cellIndex] = td.innerText.replace(/\\s+/g, ' ').trim(); return a; }, {})}));
                return {ths, zeilen};
            }""")
            print("\n--- %s ---" % name)
            print("    Spalten: %s" % [t["t"] for t in daten["ths"]])
            return daten

        # ---------- 1. Ausgangsrechnungen ----------
        d1 = liste_lesen("action-354", "1. Ausgangsrechnungsliste")
        kopf1 = [t["t"] for t in d1["ths"]]
        pruefe("Project Category" in kopf1, "Spalte 'Project Category' in der Ausgangsrechnungsliste")
        if "Project Category" in kopf1:
            idx = [t for t in d1["ths"] if t["t"] == "Project Category"][0]["i"]
            status_idx = [t for t in d1["ths"] if t["t"] == "Status"][0]["i"]
            pruefe(idx == status_idx + 1, "Project Category steht direkt hinter dem Status "
                                          "(Status Zelle %s, Project Category Zelle %s)" % (status_idx, idx))
            zeile = next((z for z in d1["zeilen"] if "RE/2026/0003" in z["text"]), None)
            pruefe(zeile is not None, "Testrechnung RE/2026/0003 in der Liste gefunden")
            if zeile:
                wert = zeile["zellen"].get(str(idx), "")
                print("    Zeile: %s" % zeile["text"][:220])
                pruefe("BUNDESLAND SONDERVERTRAG" in wert,
                       "Project-Category-Wert in der Zeile: '%s'" % wert)
        for w in ERWARTET_SPALTEN:
            pruefe(any(w == k for k in kopf1), "Spalte '%s' weiterhin sichtbar" % w)
        seite.screenshot(path=os.path.join(VZ, "01_Ausgangsrechnungen.png"), full_page=True)

        # ---------- 2. Kunden-Gutschriften ----------
        d2 = liste_lesen("action-355", "2. Kunden-Gutschriften")
        kopf2 = [t["t"] for t in d2["ths"]]
        pruefe("Project Category" in kopf2, "Spalte 'Project Category' in den Kunden-Gutschriften")
        if "Project Category" in kopf2 and gutschrift:
            idx = [t for t in d2["ths"] if t["t"] == "Project Category"][0]["i"]
            zeile = next((z for z in d2["zeilen"] if gutschrift[0]["name"] in z["text"]), None)
            pruefe(zeile is not None, "Gutschrift %s in der Liste gefunden" % gutschrift[0]["name"])
            if zeile:
                wert = zeile["zellen"].get(str(idx), "")
                pruefe("BUNDESLAND SONDERVERTRAG" in wert,
                       "Project-Category-Wert in der Gutschriftzeile: '%s'" % wert)
        seite.screenshot(path=os.path.join(VZ, "02_Kunden_Gutschriften.png"), full_page=True)

        # ---------- 3. Statuskette im Formular ----------
        print("\n--- 3. Odoo-11-Statuskette im Rechnungsformular ---")

        def form_oeffnen(suchtext):
            seite.goto("%s/odoo/action-354" % url)
            seite.wait_for_selector(".o_data_row", timeout=90000)
            seite.wait_for_timeout(3000)
            zeile = seite.locator(".o_data_row", has_text=suchtext).first
            zeile.locator("td").nth(1).click()
            seite.wait_for_selector(".o_form_view", timeout=60000)
            seite.wait_for_timeout(3500)

        for ref, (erwartet, o18_erwartet) in ERWARTETE_KETTE.items():
            form_oeffnen(ref)
            # Reiter "Andere Informationen" oeffnen (Odoo rendert die Reiterinhalte erst beim Oeffnen)
            seite.locator(".o_notebook a.nav-link", has_text="Andere Informationen").first.click()
            seite.wait_for_timeout(2000)
            daten = seite.evaluate("""() => {
                const feld = document.querySelector("div[name='itk_o11_status']");
                const aktiv = feld ? [...feld.querySelectorAll('button')]
                    .filter(b => b.classList.contains('btn-primary') || b.classList.contains('o_arrow_button_current'))
                    .map(b => b.innerText.replace(/\\s+/g,' ').trim()) : [];
                const o18 = document.querySelector("div[name='state']");
                const pcfeld = document.querySelector("div[name='projectcategory_id']");
                const eingabe = pcfeld ? pcfeld.querySelector('input') : null;
                return {
                    kette_ganz: feld ? feld.innerText.replace(/\\s+/g,' ').trim() : null,
                    kette_aktiv: aktiv,
                    o18_status: o18 ? o18.innerText.replace(/\\s+/g,' ').trim() : null,
                    statusleisten: document.querySelectorAll('.o_statusbar_status').length,
                    pc_wert: eingabe ? eingabe.value : (pcfeld ? pcfeld.innerText.replace(/\\s+/g,' ').trim() : null)};
            }""")
            print("    %-22s Kette aktiv='%s' | ganz='%s' | O18-Status='%s' | Statusleisten=%s"
                  % (ref, daten["kette_aktiv"], daten["kette_ganz"], daten["o18_status"],
                     daten["statusleisten"]))
            print("       Project Category im Formular: '%s'" % daten["pc_wert"])
            pruefe(daten["kette_ganz"] is not None, "%s: Odoo-11-Statuskette im Formular sichtbar" % ref)
            pruefe(daten["kette_aktiv"] == [erwartet],
                   "%s: Kette zeigt '%s' (erwartet '%s')" % (ref, daten["kette_aktiv"], erwartet))
            for stufe in KETTE_STUFEN:
                pruefe(stufe in (daten["kette_ganz"] or ""),
                       "%s: Kettenstufe '%s' in der Statusleiste" % (ref, stufe))
            pruefe(o18_erwartet == (daten["o18_status"] or "").strip(),
                   "%s: Odoo-18-Status bleibt sichtbar als 'Status (Odoo 18)' = '%s'"
                   % (ref, daten["o18_status"]))
            pruefe(daten["statusleisten"] == 1,
                   "%s: nur die Odoo-11-Statusleiste gerendert (%d Statusleisten)"
                   % (ref, daten["statusleisten"]))
            pruefe("BUNDESLAND SONDERVERTRAG" in (daten["pc_wert"] or ""),
                   "%s: Project Category im Formular mit echtem Wert ('%s')" % (ref, daten["pc_wert"]))
            seite.screenshot(path=os.path.join(VZ, "03_%s.png" % ref), full_page=True)

        # ---------- 4. Odoo-18-Zusatzfunktionen ----------
        print("\n--- 4. Odoo-18-Zusatzfunktionen ---")
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
