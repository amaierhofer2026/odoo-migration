"""Browser-Abnahme Session 126: Pflichtfeld "Partner" im Rechnungsformular.

Prueft am echten Bildschirm:
  1. Testbeleg (Entwurf ohne Partner) oeffnet ohne Meldung
  2. Aenderung speichern -> kein "Ungueltige Felder: Partner", Wert wirklich gespeichert
  3. Kunde setzen und speichern -> Partner korrekt zugeordnet
  4. Menue Verkauf > Eingaenge und Einkauf > Eingaenge oeffnen ohne Meldung
  5. Neu-Anlegen moeglich; Odoo-18-Zusatzfunktionen (Reiter, Statusleiste) vorhanden

Aufruf: python scripts/browser_pflichtfeld_abnahme.py lokal|vm <testbeleg-id>
"""
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            w[k.strip()] = v.strip().strip('"')
    return w


env = lade_env(os.path.join(REPO, ".env"))
inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
tid = int(sys.argv[2]) if len(sys.argv) > 2 else 0
url = "http://localhost:8069" if inst != "vm" else "https://k001959vsx.ipax.at"
domain = "localhost" if inst != "vm" else "k001959vsx.ipax.at"

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(url + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
            "db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
            "password": env["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"}))
sid = next(c.value for c in jar if c.name == "session_id")


def rpc(model, method, args, kwargs=None):
    kw = dict(kwargs or {})
    kw.setdefault("context", {"lang": "de_DE"})
    p = {"model": model, "method": method, "args": args, "kwargs": kw}
    r = json.loads(op.open(urllib.request.Request(
        url + "/web/dataset/call_kw", data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                        "params": p}).encode(),
        headers={"Content-Type": "application/json"})).read())
    if "error" in r:
        raise RuntimeError(str(r["error"])[:300])
    return r["result"]


kunden = rpc("res.partner", "search_read", [[["customer_rank", ">", 0]], ["name"]], {"limit": 1})
KUNDE_NAME = kunden[0]["name"] if kunden else "Test Firma"

from playwright.sync_api import sync_playwright  # noqa: E402

MELD = """() => [...document.querySelectorAll('.o_notification, .o_dialog, .modal')]
    .map(e => (e.innerText||'').replace(/\\s+/g,' ').trim()).filter(t => t)"""

ok, fehl, notizen = [], [], []


def pruefe(bedingung, text):
    (ok if bedingung else fehl).append(text)
    print(("  OK   " if bedingung else "  FEHL ") + text)


def speichern_und_pruefen(seite, erwartet, beschreibung):
    seite.evaluate("() => document.querySelector('button.o_form_button_save').click()")
    meldungen, stand = [], None
    for _ in range(12):
        seite.wait_for_timeout(2000)
        meldungen = seite.evaluate(MELD) or meldungen
        stand = rpc("account.move", "read", [[tid], ["sale_order_benefit_period", "partner_id"]])[0]
        if erwartet(stand):
            break
    pruefe("Ungültige Felder" not in " ".join(meldungen),
           "%s: keine Meldung 'Ungültige Felder' (%s)" % (beschreibung, meldungen if meldungen else "keine"))
    return stand, meldungen


VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session126",
                  "pflichtfeld_partner", inst)
os.makedirs(VZ, exist_ok=True)

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_pfab_%s" % inst),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1300})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()

    print("1. Testbeleg %s oeffnen" % tid)
    seite.goto("%s/odoo/customer-invoices/%s" % (url, tid))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(5000)
    pruefe(not seite.evaluate(MELD), "Testbeleg oeffnet ohne Meldung")
    zustand = seite.evaluate("""() => {
        const d = document.querySelector("div[name='partner_id']");
        const i = d ? d.querySelector('input') : null;
        return {wert: i ? i.value : 'FELD-FEHLT',
                klasse: d ? d.className : '-',
                rot: i ? getComputedStyle(i).borderBottomColor : '-'};}""")
    pruefe(zustand["wert"] == "", "Feld Kunde vorhanden und leer (gemessen: '%s')" % zustand["wert"])
    pruefe("o_required_modifier" not in zustand["klasse"],
           "Kunde ist kein Pflichtfeld mehr gekennzeichnet (%s)" % zustand["klasse"])
    seite.screenshot(path=os.path.join(VZ, "01_testbeleg_ohne_partner.png"), full_page=True)

    print("2. Aenderung speichern")
    feld = seite.locator("div[name='sale_order_benefit_period'] textarea").first
    feld.click()
    feld.fill("TEST-PF-126-Abnahme")
    seite.wait_for_timeout(1200)
    stand, _ = speichern_und_pruefen(seite, lambda s: s["sale_order_benefit_period"] == "TEST-PF-126-Abnahme",
                                     "Speichern ohne Partner")
    pruefe(stand["sale_order_benefit_period"] == "TEST-PF-126-Abnahme",
           "Wert wirklich gespeichert (Leistungszeitraum=%s, Partner=%s)"
           % (stand["sale_order_benefit_period"], stand["partner_id"]))
    seite.screenshot(path=os.path.join(VZ, "02_gespeichert_ohne_partner.png"), full_page=True)

    print("3. Kunde setzen: %s" % KUNDE_NAME)
    pf = seite.locator("div[name='partner_id'] input").first
    pf.click()
    pf.fill(KUNDE_NAME[:10])
    seite.wait_for_timeout(2500)
    vorschlag = seite.locator(".dropdown-item").filter(has_text=KUNDE_NAME[:10]).first
    pruefe(vorschlag.count() > 0, "Vorschlagsliste oeffnet sich")
    if vorschlag.count():
        vorschlag.click()
        seite.wait_for_timeout(1500)
    stand, m3 = speichern_und_pruefen(seite, lambda s: bool(s["partner_id"]), "Speichern mit Kunde")
    pruefe(bool(stand["partner_id"]), "Partner korrekt zugeordnet: %s" % (stand["partner_id"],))
    seite.screenshot(path=os.path.join(VZ, "03_mit_kunde.png"), full_page=True)

    print("4. Menues Verkauf/Einkauf > Eingaenge")
    for abschnitt_name in ("Verkauf", "Einkauf"):
        seite.goto("%s/odoo/action-354" % url)
        seite.wait_for_selector(".o_list_view", timeout=90000)
        seite.wait_for_timeout(4000)
        abschnitt = seite.locator(".o_menu_sections > li > a, .o_menu_sections button") \
                         .filter(has_text=abschnitt_name).first
        if not abschnitt.count():
            pruefe(False, "Abschnitt %s gefunden" % abschnitt_name)
            continue
        abschnitt.click()
        seite.wait_for_timeout(1500)
        punkt = seite.locator(".o-dropdown--menu .dropdown-item").filter(has_text="Eingänge").first
        if not punkt.count():
            pruefe(False, "%s > Eingänge gefunden" % abschnitt_name)
            continue
        punkt.click()
        seite.wait_for_timeout(6000)
        mm = seite.evaluate(MELD)
        pruefe(not mm, "%s > Eingänge oeffnet ohne Meldung (%s)" % (abschnitt_name, mm if mm else "keine"))
        seite.screenshot(path=os.path.join(VZ, "04_%s_eingaenge.png" % abschnitt_name.lower()),
                         full_page=True)

    print("5. Neu anlegen")
    seite.goto("%s/odoo/action-354" % url)
    seite.wait_for_selector(".o_list_view", timeout=90000)
    seite.wait_for_timeout(4000)
    neu = seite.locator("button").filter(has_text="Neu").first
    pruefe(neu.count() > 0, "Knopf Neu vorhanden")
    if neu.count():
        neu.click()
        seite.wait_for_selector(".o_form_view", timeout=60000)
        seite.wait_for_timeout(4000)
        pruefe(not seite.evaluate(MELD), "neuer Beleg oeffnet ohne Meldung")
        seite.screenshot(path=os.path.join(VZ, "05_neu.png"), full_page=True)
        reiter = seite.locator(".o_form_view .nav-link").all_inner_texts()
        pruefe(any("Andere Informationen" in r for r in reiter),
               "Reiter Andere Informationen vorhanden: %s" % reiter)
        pruefe(seite.locator(".o_form_statusbar, .o_statusbar_status").count() > 0,
               "Statusleiste vorhanden")
        seite.keyboard.press("Escape")
        seite.wait_for_timeout(2000)
    ctx.close()

print("\n=== Ergebnis %s: %d OK / %d FEHL ===" % (inst, len(ok), len(fehl)))
for f in fehl:
    print("  FEHL:", f)
for n in notizen:
    print("  Hinweis:", n)
print("Screenshots:", VZ)
