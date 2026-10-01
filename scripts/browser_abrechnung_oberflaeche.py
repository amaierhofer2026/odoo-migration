"""Browser-Abnahme Bereich Abrechnung (Oberflaechenangleichung, Odoo 11 gegen Odoo 18).

Prueft im echten Browser:
 1. App-Bezeichnung "Abrechnung" und die Untermenues (Odoo-11-Wortlaut, auch in Untermenues).
 2. Filter der Rechnungsliste: Odoo-11-Filter vorhanden, Odoo-18-Zusatzfilter erhalten.
 3. Gruppierungen der Rechnungsliste (Auswahlliste der benutzerdefinierten Gruppe).

Aufruf: uv run --with playwright python scripts/browser_abrechnung_oberflaeche.py --instanz lokal|vm
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

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "oberflaeche")

O11_FILTER = ["Entwurf", "Offen", "Bezahlt", "Überfällig", "Meine Rechnungen",
              "Meine Aktivitäten", "Verspätete Aktivitäten", "Heutige Aktivitäten",
              "Anstehende Aktivitäten"]
O18_ZUSATZ = ["Gebucht", "Abgebrochen", "Nicht gesendet", "Ausgangsrechnungen", "Gutschriften",
              "Zu prüfen", "Peppol bereit", "Zu zahlen", "In Zahlung"]
O11_GRUPPEN = ["Partner", "Verkäufer", "Status", "Rechnungsdatum", "Fälligkeit"]
O11_MENUES = ["Verkauf", "Einkauf", "Berichtswesen", "Konfiguration"]
O11_UNTERMENUES = ["Kunden-Gutschriften", "Lieferanten-Gutschriften", "Verkaufbare Produkte",
                   "Einkaufbare Produkte", "Ausgangsrechnungen", "Eingangsrechnungen", "Zahlungen"]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    env = lade_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    if a.instanz == "vm":
        url, domain = "https://k001959vsx.ipax.at", "k001959vsx.ipax.at"
    else:
        url, domain = "http://localhost:8069", "localhost"

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
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_ui2_%s_%s" % (a.instanz, os.getpid())),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        s = ctx.pages[0] if ctx.pages else ctx.new_page()
        s.goto("%s/odoo/action-354" % url)
        s.wait_for_selector(".o_list_renderer", timeout=120000)
        s.wait_for_timeout(6000)

        abschnitte = s.evaluate("""() => [...document.querySelectorAll('.o_menu_sections button, .o_menu_sections a')]
            .map(e => (e.textContent || '').trim()).filter(t => t && t.length < 40)""")
        print("    Menueabschnitte: %s" % abschnitte)
        for name in O11_MENUES:
            pruefe(name in abschnitte, "App-Abschnitt '%s' sichtbar" % name)

        untermenue = []
        for abschnitt in O11_MENUES[:2]:
            try:
                s.click(".o_menu_sections button:has-text('%s')" % abschnitt)
                s.wait_for_timeout(2000)
                untermenue += s.evaluate("""() => [...document.querySelectorAll('.dropdown-item, .dropdown-menu a')]
                    .filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim())""")
                s.keyboard.press("Escape")
                s.wait_for_timeout(800)
            except Exception as fehler_text:
                print("    Hinweis: %s -> %s" % (abschnitt, str(fehler_text)[:60]))
        print("    Untermenues: %s" % untermenue[:20])
        for name in O11_UNTERMENUES:
            pruefe(any(name.lower() == u.lower() for u in untermenue), "Untermenue '%s' sichtbar" % name)
        s.screenshot(path=os.path.join(VZ, "01_Menue_Abrechnung.png"), full_page=True)

        # Filterliste
        s.click(".o_searchview_dropdown_toggler")
        s.wait_for_timeout(2500)
        labels = s.evaluate("""() => [...document.querySelectorAll('.o_dropdown_menu .dropdown-item, .o_dropdown_container .dropdown-item, .o_searchview_dropdown .dropdown-item')]
            .filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim())""")
        # Untermenues gezielt aufklappen (Aktivitaeten, Gruppieren nach)
        for unter in ("Meine Aktivitäten", "Gruppieren nach"):
            try:
                s.hover(".o_control_panel .dropdown-item:has-text('%s')" % unter)
                s.wait_for_timeout(1800)
                labels += s.evaluate("""() => [...document.querySelectorAll('.dropdown-item')]
                    .filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim())""")
            except Exception as hinweis:
                print("    Hinweis %s: %s" % (unter, str(hinweis)[:60]))
        labels = sorted(set(labels))
        print("    Filterliste (%d): %s" % (len(labels), labels[:40]))
        s.screenshot(path=os.path.join(VZ, "02_Filter.png"), full_page=True)
        for name in O11_FILTER:
            pruefe(any(name.lower() == l.lower() for l in labels), "Odoo-11-Filter '%s' vorhanden" % name)
        for name in O18_ZUSATZ:
            pruefe(any(name.lower() == l.lower() for l in labels), "Odoo-18-Zusatzfilter '%s' erhalten" % name)

        # Gruppierungen aus der Auswahlliste der benutzerdefinierten Gruppe
        gruppen = [l for l in labels if l]
        print("    Gruppierungen (%d): %s" % (len(gruppen), sorted(set(gruppen))[:25]))
        for name in O11_GRUPPEN:
            pruefe(any(name.lower() == g.lower() for g in gruppen), "Odoo-11-Gruppierung '%s' vorhanden" % name)
        s.keyboard.press("Escape")
        s.wait_for_timeout(1000)
        s.screenshot(path=os.path.join(VZ, "03_Liste.png"), full_page=True)
        ctx.close()

    print("\n%d OK / %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
