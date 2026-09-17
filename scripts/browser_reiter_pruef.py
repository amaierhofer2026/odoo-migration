"""Einen Formular-Reiter im echten Browser pruefen (Sichtbarkeit, Spalten, Buttons).

Ergaenzt `browser_feldbreite.py` (das einzelne Felder vermisst). Beantwortet die Fragen
der Arbeitsregel "vorhanden != erledigt": Ist der Reiter sichtbar? Welche Felder stehen
drin? Welche Spaltenkoepfe? Gibt es Buttons? Wie viele Zeilen sind sichtbar?

Aufruf:
    uv run --with playwright python scripts/browser_reiter_pruef.py [URL] [KONTAKT-ID] [REITER] [BILDDATEI]

Beispiele:
    uv run --with playwright python scripts/browser_reiter_pruef.py http://localhost:8069 72 "Support Ticket" 20_lokal.png
    uv run --with playwright python scripts/browser_reiter_pruef.py https://k001959vsx.ipax.at 72 "Support Ticket" 20_vm.png

Hinweis: Odoo (17+) cached Ansichten im Browserprofil; das Profil wird vor jedem Lauf
geloescht, damit wirklich die aktuelle Ansicht geprueft wird.
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import shutil
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BILDER = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Layoutvergleich-Session95")


def lade_env(pfad: str) -> dict:
    werte = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                s, w = zeile.split("=", 1)
                werte[s.strip()] = w.strip()
    return werte


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8069"
    kontakt = sys.argv[2] if len(sys.argv) > 2 else "72"
    reiter = sys.argv[3] if len(sys.argv) > 3 else "Support Ticket"
    bild = sys.argv[4] if len(sys.argv) > 4 else "20_Reiter_Pruefung.png"
    marke = "lokal" if "localhost" in url else "VM"
    env = lade_env(os.path.join(REPO, ".env"))

    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(url.rstrip("/") + "/web/session/authenticate",
                                 data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                  "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                                             "password": env["ODOO18_PWD"]}}).encode(),
                                 headers={"Content-Type": "application/json"})
    with op.open(req, timeout=120) as f:
        json.loads(f.read().decode())
    sid = next(c.value for c in jar if c.name == "session_id")

    from playwright.sync_api import sync_playwright

    profil = os.path.join(os.environ["TEMP"], "pw_reiter_%s_%s" % (marke, reiter.replace(" ", "")))
    shutil.rmtree(profil, ignore_errors=True)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(user_data_dir=profil, channel="chrome", headless=True,
                                                    viewport={"width": 1600, "height": 1200})
        ctx.add_cookies([{"name": "session_id", "value": sid, "path": "/",
                          "domain": "localhost" if "localhost" in url else url.split("//")[1].split("/")[0]}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.goto(url.rstrip("/") + "/odoo/contacts/%s" % kontakt, wait_until="domcontentloaded", timeout=120000)
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(5000)
        gefunden = False
        for t in seite.query_selector_all(".nav-link"):
            if reiter.lower() in t.inner_text().lower():
                t.click()
                gefunden = True
                break
        seite.wait_for_timeout(4000)
        daten = seite.evaluate("""() => {
            const p = document.querySelector('.tab-pane.active');
            if (!p) return {fehler: 'kein aktiver Reiter'};
            return {
                reiter: (p.getAttribute('name') || '') + ' | ' + (p.innerText || '').replace(/\\n+/g, ' | ').trim().slice(0, 300),
                tabellenkoepfe: [...p.querySelectorAll('table thead th')].map(e => e.innerText.trim()).filter(t => t),
                felder: [...new Set([...p.querySelectorAll('[name]')].map(e => e.getAttribute('name')))],
                buttons: [...p.querySelectorAll('button')].map(e => (e.innerText || e.title || '').trim()).filter(t => t),
                sichtbareZeilen: p.querySelectorAll('table tbody tr').length,
            };
        }""")
        print("Instanz: %s | Kontakt: %s | Reiter gesucht: %s" % (marke, kontakt, reiter))
        print("Reiter gefunden:", gefunden)
        print(json.dumps(daten, ensure_ascii=False, indent=1)[:1600])
        print("Reiterleiste:", [t.inner_text().strip() for t in seite.query_selector_all(".nav-link")])
        pfad = os.path.join(BILDER, bild)
        seite.screenshot(path=pfad, full_page=True)
        print("Screenshot:", pfad)
        ctx.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
