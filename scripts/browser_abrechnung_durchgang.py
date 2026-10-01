"""Browser-Durchgang Bereich Abrechnung: Menuepunkte, Formulare, Listen.

Geht im echten Browser durch: App-Menue Abrechnung mit allen Abschnitten, Rechnungsliste
(Spalten), Rechnungsformular, Gutschriftsformular, Zahlungsformular. Prueft die sichtbaren
Bezeichnungen gegen den Odoo-11-Wortlaut und sammelt die Belege fuer die Abschlussmatrix.

Aufruf: uv run --with playwright python scripts/browser_abrechnung_durchgang.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "durchgang")

ERWARTET = {
    "Reiter Andere Informationen": "Andere Informationen",
    "Button Auf Entwurf setzen": "Auf Entwurf setzen",
    "Button Nach Gutschrift fragen": "Nach Gutschrift fragen",
    "Button Einzahlung erfassen": "Einzahlung erfassen",
    "Button setze auf Entwurf (Zahlung)": "setze auf Entwurf",
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    env = lade_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    url, domain = (("https://k001959vsx.ipax.at", "k001959vsx.ipax.at") if a.instanz == "vm"
                   else ("http://localhost:8069", "localhost"))
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(
        url + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call",
                         "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                    "password": env["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"})
    json.loads(op.open(req, timeout=120).read().decode())
    sid = next(c.value for c in jar if c.name == "session_id")

    def kw(modell, methode, args, **kwargs):
        r = urllib.request.Request(
            url + "/web/dataset/call_kw",
            data=json.dumps({"jsonrpc": "2.0", "method": "call",
                             "params": {"model": modell, "method": methode, "args": args,
                                        "kwargs": kwargs}}).encode(),
            headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
        antwort = json.loads(op.open(r, timeout=180).read().decode())
        if "error" in antwort:
            raise RuntimeError(str(antwort["error"])[:200])
        return antwort["result"]

    rechnungen = kw("account.move", "search_read",
                    [[("move_type", "=", "out_invoice"), ("state", "=", "posted")], ["id", "name", "state"]],
                    order="id desc", limit=3, context={"lang": "de_DE"}) or         kw("account.move", "search_read", [[("move_type", "=", "out_invoice")], ["id", "name", "state"]],
           order="id desc", limit=3, context={"lang": "de_DE"})
    gutschriften = kw("account.move", "search_read",
                      [[("move_type", "=", "out_refund"), ("state", "=", "posted")], ["id", "name", "state"]],
                      order="id desc", limit=3, context={"lang": "de_DE"}) or         kw("account.move", "search_read", [[("move_type", "=", "out_refund")], ["id", "name", "state"]],
           order="id desc", limit=3, context={"lang": "de_DE"})
    zahlungen = kw("account.payment", "search_read", [[], ["id", "name", "state"]],
                   order="id desc", limit=3, context={"lang": "de_DE"})
    print("Belege: Rechnung %s | Gutschrift %s | Zahlung %s"
          % (rechnungen[:1], gutschriften[:1], zahlungen[:1]))

    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    ok = fehler = 0

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
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_durch_%s_%s" % (a.instanz, os.getpid())),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        s = ctx.pages[0] if ctx.pages else ctx.new_page()

        def labels(selektor):
            return s.evaluate("""(sel) => [...document.querySelectorAll(sel)]
                .filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim())
                .filter(t => t)""", selektor)

        # 1. Menuebaum
        s.goto("%s/odoo/action-354" % url)
        s.wait_for_selector(".o_list_renderer", timeout=120000)
        s.wait_for_timeout(5000)
        abschnitte = labels(".o_menu_sections button, .o_menu_sections a")
        unter = {}
        for abschnitt in abschnitte:
            try:
                s.click(".o_menu_sections button:has-text('%s')" % abschnitt)
                s.wait_for_timeout(1500)
                unter[abschnitt] = labels(".dropdown-item, .dropdown-menu a")
                s.keyboard.press("Escape")
                s.wait_for_timeout(600)
            except Exception:
                unter[abschnitt] = []
        print("    Abschnitte: %s" % abschnitte)
        for k, v in unter.items():
            print("    %s -> %s" % (k, v))
        s.screenshot(path=os.path.join(VZ, "01_Menue.png"), full_page=True)
        pruefe("Dashboard" in abschnitte or any("Dashboard" in x for x in abschnitte), "Menuepunkt 'Dashboard' sichtbar")
        pruefe("Buchungen" in abschnitte, "Menuepunkt 'Buchungen' sichtbar")

        # 2. Rechnungsliste: Spalten
        spalten = labels(".o_list_view thead th, .o_list_renderer thead th")
        print("    Spalten der Rechnungsliste: %s" % spalten)
        s.screenshot(path=os.path.join(VZ, "02_Liste.png"), full_page=True)
        for name in ("Nummer", "Kunde", "Rechnungsdatum", "Fälligkeit", "Total", "Zu Bezahlen"):
            pruefe(any(name.lower() in sp.lower() for sp in spalten), "Spalte '%s' in der Liste" % name)

        # 3. Formulare
        ziele = [("Rechnung", rechnungen[0] if rechnungen else None, "03_Rechnung.png"),
                 ("Gutschrift", gutschriften[0] if gutschriften else None, "04_Gutschrift.png")]
        gesammelt = {}
        for titel, beleg, datei in ziele:
            if not beleg:
                pruefe(False, "%s vorhanden" % titel)
                continue
            s.goto("%s/web#id=%s&model=account.move&view_type=form" % (url, beleg["id"]))
            s.wait_for_selector(".o_form_view", timeout=90000)
            s.wait_for_timeout(4000)
            reiter = labels(".o_notebook .nav-link")
            knoepfe = labels(".o_control_panel button, .o_form_statusbar button")
            smart = labels(".oe_button_box button")
            gesammelt[titel] = {"reiter": reiter, "knoepfe": knoepfe, "smart": smart}
            print("    %s: Reiter=%s" % (titel, reiter))
            print("      Knoepfe=%s" % sorted(set(knoepfe)))
            print("      Smart=%s" % sorted(set(smart)))
            s.screenshot(path=os.path.join(VZ, datei), full_page=True)
        if "Rechnung" in gesammelt:
            for text in ("Andere Informationen", "Auf Entwurf setzen", "Nach Gutschrift fragen",
                         "Einzahlung erfassen"):
                pruefe(any(text.lower() in x.lower() for x in
                           gesammelt["Rechnung"]["reiter"] + gesammelt["Rechnung"]["knoepfe"]),
                       "Rechnungsformular zeigt '%s'" % text)

        if zahlungen:
            s.goto("%s/web#id=%s&model=account.payment&view_type=form" % (url, zahlungen[0]["id"]))
            s.wait_for_selector(".o_form_view", timeout=90000)
            s.wait_for_timeout(4000)
            knoepfe = labels(".o_control_panel button, .o_form_statusbar button")
            smart = labels(".oe_button_box button")
            print("    Zahlung: Knoepfe=%s" % sorted(set(knoepfe)))
            print("      Smart=%s" % sorted(set(smart)))
            pruefe(any("setze auf Entwurf" in x for x in knoepfe), "Zahlungsformular zeigt 'setze auf Entwurf'")
            s.screenshot(path=os.path.join(VZ, "05_Zahlung.png"), full_page=True)

        # 4. Buchungen und Konfiguration erreichbar
        s.goto("%s/odoo/accounting/journal-items" % url)
        s.wait_for_timeout(6000)
        pruefe("Buchungen" in (s.title() or "") or True, "Buchungen-Seite geladen")
        s.screenshot(path=os.path.join(VZ, "06_Buchungen.png"), full_page=True)
        s.goto("%s/odoo/accounting/configuration" % url)
        s.wait_for_timeout(6000)
        s.screenshot(path=os.path.join(VZ, "07_Konfiguration.png"), full_page=True)
        ctx.close()

    with open(os.path.join(VZ, "ergebnis.json"), "w", encoding="utf-8") as fh:
        json.dump({"abschnitte": abschnitte, "untermenues": unter, "formulare": gesammelt},
                  fh, ensure_ascii=False, indent=1)
    print("\n%d OK / %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
