"""Feldbreite im Kontaktformular messen (Browser, echte Darstellung).

Beantwortet die Frage "ist der Wert sichtbar oder abgeschnitten?" mit Zahlen
(clientWidth vs. scrollWidth) statt mit Augenmass. Gedacht fuer die Regel
"vorhanden != erledigt": sichtbar? richtige Position? vollstaendig lesbar?

Aufruf:
    uv run --with playwright python scripts/browser_feldbreite.py [URL] [KONTAKT-ID] [FELDNAME] [REITER-SUCHTEXT]

Beispiele:
    uv run --with playwright python scripts/browser_feldbreite.py http://localhost:8069 72 status_of_community Gemeinde
    uv run --with playwright python scripts/browser_feldbreite.py https://k001959vsx.ipax.at 72 status_of_community Gemeinde

Hinweis: Odoo (17+) cached Ansichten im Browserprofil. Dieses Werkzeug loescht das
Profil vor jedem Lauf, damit wirklich die aktuelle Ansicht gemessen wird.
"""
import http.cookiejar, json, os, sys, urllib.request

ZIEL = r"C:\Users\anna.maierhofer\Desktop\Odoo18-Layoutvergleich-Session95"
env = {}
for z in open(r"C:\Odoo-Test\.env", encoding="utf-8"):
    if "=" in z and not z.strip().startswith("#"):
        k, v = z.split("=", 1); env[k.strip()] = v.strip()
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8069"
KONTAKT = sys.argv[2] if len(sys.argv) > 2 else "72"
FELD = sys.argv[3] if len(sys.argv) > 3 else "status_of_community"
REITER = sys.argv[4] if len(sys.argv) > 4 else "Gemeinde"
MARKE = "lokal" if "localhost" in URL else "VM"

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
req = urllib.request.Request(URL + "/web/session/authenticate",
                             data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                              "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                                         "password": env["ODOO18_PWD"]}}).encode(),
                             headers={"Content-Type": "application/json"})
with op.open(req, timeout=120) as f:
    json.loads(f.read().decode())
sid = next(c.value for c in jar if c.name == "session_id")

from playwright.sync_api import sync_playwright

import shutil
PROFIL = os.path.join(os.environ["TEMP"], "pw_prof_s110m")
shutil.rmtree(PROFIL, ignore_errors=True)   # frisches Profil: Odoo-View-Cache im Browser vermeiden
with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=PROFIL, channel="chrome", headless=True,
        viewport={"width": 1600, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": "localhost" if "localhost" in URL else "k001959vsx.ipax.at", "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()
    seite.goto(URL + "/odoo/contacts/%s" % KONTAKT, wait_until="domcontentloaded", timeout=120000)
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(5000)
    for t in seite.query_selector_all(".nav-link"):
        if REITER in t.inner_text():
            t.click(); break
    seite.wait_for_timeout(4000)
    daten = seite.evaluate("""() => {
        const p = document.querySelector('.tab-pane.active');
        const feld = p && p.querySelector('[name="%FELD%"]');
        if (!feld) return {fehler: 'Feld nicht gefunden'};
        const zelle = feld.closest('td');
        const zeile = feld.closest('tr');
        const gruppe = feld.closest('.o_inner_group') || feld.closest('group') || feld.closest('table');
        const messe = (el) => el ? {w: el.offsetWidth, client: el.clientWidth} : null;
        const misch = (txt) => { const c = document.createElement('canvas').getContext('2d');
            c.font = window.getComputedStyle(feld.querySelector('input') || feld).font;
            return Math.ceil(c.measureText(txt).width); };
        const eingabe = feld.querySelector('input') || feld;
        return {
            marke: '%MARKE%',
            tabBreite: p.offsetWidth,
            gruppe: misch0(gruppe), zeile: messe(zeile), zelle: messe(zelle),
            eingabe: {client: eingabe.clientWidth, scroll: eingabe.scrollWidth, text: (eingabe.value || eingabe.innerText || '').trim()},
            bedarf: {Marktgemeinde: misch('Marktgemeinde'), Magistrat: misch('Magistrat'), Magistrat_der_Stadt: misch('Magistrat der Stadt'), Stadtgemeinde: misch('Stadtgemeinde'), Gemeinde: misch('Gemeinde')},
            colspan: feld.getAttribute('colspan'),
            gruppenBreiten: [...p.querySelectorAll('.o_inner_group, table.o_group')].map(e => e.offsetWidth),
        };
        function misch0(el) { return el ? {w: el.offsetWidth, colspan: el.getAttribute('colspan')} : null; }
    }""".replace("%MARKE%", MARKE).replace("%FELD%", FELD))
    print(json.dumps(daten, ensure_ascii=False, indent=1))
    pfad = os.path.join(ZIEL, "18_%s_GemeindeInfo_Messung.png" % MARKE)
    seite.screenshot(path=pfad, full_page=True)
    print("Screenshot:", pfad)
    ctx.close()
