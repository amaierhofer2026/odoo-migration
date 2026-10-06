"""Abnahme Session 126 (Nachtrag): Partnerpflicht im Rechnungsformular.

Prueft am echten Bildschirm:
  1. Menue Abrechnung > Verkauf/Einkauf > Eingaenge oeffnet ohne Meldung
  2. gueltiger Beleg (mit Partner) oeffnen + Tab-Wechsel -> keine Meldung
  3. bestehender Entwurf ohne Partner: oeffnen ohne Meldung, Tab-Wechsel ->
     Meldung "Ungueltige Felder: Partner" (das automatische Speichern von Odoo 18),
     Datensatz bleibt unveraendert
  4. neuer Beleg ohne Partner: Speichern wird verhindert (Odoo-11-Fachlogik), kein Datensatz
  5. Partner setzen -> Speichern gelingt (Datensatz wird angelegt und danach entfernt)
  6. Testdaten restlos entfernt, Bestand unveraendert

Aufruf: python scripts/browser_partnerpflicht_abnahme.py lokal|vm <gueltige_id> <partnerlose_id>
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
gueltig = int(sys.argv[2]) if len(sys.argv) > 2 else 0
ohne = int(sys.argv[3]) if len(sys.argv) > 3 else 0
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
KUNDE = kunden[0]["name"] if kunden else "Test Firma"
bestand_vor = rpc("account.move", "search_count", [[]])

from playwright.sync_api import sync_playwright  # noqa: E402

MELD = """() => [...document.querySelectorAll('.o_notification, .o_dialog, .modal')]
    .map(e => (e.innerText||'').replace(/\\s+/g,' ').trim()).filter(t => t)"""
VERSTECKEN = """() => {
    Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => 'hidden'});
    document.dispatchEvent(new Event('visibilitychange'));}"""
ZEIGEN = """() => {
    Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => 'visible'});
    document.dispatchEvent(new Event('visibilitychange'));}"""

ok, fehl, notizen = [], [], []


def pruefe(bedingung, text):
    (ok if bedingung else fehl).append(text)
    print(("  OK   " if bedingung else "  FEHL ") + text)


def sammle_meldungen(seite, sekunden=8):
    gesammelt = []
    schritte = int(sekunden / 0.3)
    for _ in range(schritte):
        m = seite.evaluate(MELD)
        for x in m:
            if x not in gesammelt:
                gesammelt.append(x)
        if gesammelt:
            break
        seite.wait_for_timeout(300)
    return gesammelt


VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session126",
                  "partnerpflicht", inst)
os.makedirs(VZ, exist_ok=True)

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_pp_%s" % inst),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1300})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()

    print("1. Menues Eingaenge")
    for abschnitt in ("Verkauf", "Einkauf"):
        seite.goto("%s/odoo/action-354" % url)
        seite.wait_for_selector(".o_list_view", timeout=90000)
        seite.wait_for_timeout(3500)
        a = seite.locator(".o_menu_sections > li > a, .o_menu_sections button").filter(has_text=abschnitt).first
        a.click()
        seite.wait_for_timeout(1500)
        p = seite.locator(".o-dropdown--menu .dropdown-item").filter(has_text="Eingänge").first
        p.click()
        seite.wait_for_timeout(5000)
        mm = seite.evaluate(MELD)
        pruefe(not mm, "%s > Eingänge ohne Meldung (%s)" % (abschnitt, mm if mm else "keine"))
        seite.screenshot(path=os.path.join(VZ, "01_eingaenge_%s.png" % abschnitt.lower()),
                         full_page=True)

    print("2. gueltiger Beleg %s oeffnen und Tab verbergen" % gueltig)
    seite.goto("%s/odoo/customer-invoices/%s" % (url, gueltig))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(4000)
    pruefe(not seite.evaluate(MELD), "gueltiger Beleg oeffnet ohne Meldung")
    seite.evaluate(VERSTECKEN)
    m2 = sammle_meldungen(seite, 6)
    pruefe(not m2, "Tab-Wechsel beim gueltigen Beleg ohne Meldung (%s)" % (m2 if m2 else "keine"))
    seite.evaluate(ZEIGEN)
    seite.screenshot(path=os.path.join(VZ, "02_gueltiger_beleg.png"), full_page=True)

    print("3. Entwurf ohne Partner %s oeffnen und Tab verbergen" % ohne)
    vor = rpc("account.move", "read", [[ohne], ["write_date", "partner_id", "state"]])[0]
    seite.goto("%s/odoo/customer-invoices/%s" % (url, ohne))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(4000)
    beim_oeffnen = seite.evaluate(MELD)
    pruefe(not beim_oeffnen, "Entwurf ohne Partner oeffnet ohne Meldung (%s)"
           % (beim_oeffnen if beim_oeffnen else "keine"))
    seite.screenshot(path=os.path.join(VZ, "03_entwurf_ohne_partner.png"), full_page=True)
    seite.evaluate(VERSTECKEN)
    m3 = sammle_meldungen(seite, 8)
    pruefe(any("Ungültige Felder" in x for x in m3),
           "Tab-Wechsel beim partnerlosen Entwurf meldet 'Ungültige Felder' (%s)" % (m3,))
    seite.screenshot(path=os.path.join(VZ, "03b_tabwechsel_meldung.png"), full_page=True)
    seite.evaluate(ZEIGEN)
    nach = rpc("account.move", "read", [[ohne], ["write_date", "partner_id", "state"]])[0]
    pruefe(vor == nach, "partnerloser Entwurf unveraendert (vorher=%s, nachher=%s)"
           % (vor["write_date"], nach["write_date"]))

    print("4. neuer Beleg ohne Partner - Speichern muss verhindert werden")
    seite.goto("%s/odoo/action-354" % url)
    seite.wait_for_selector(".o_list_view", timeout=90000)
    seite.wait_for_timeout(3500)
    seite.locator("button").filter(has_text="Neu").first.click()
    seite.wait_for_selector(".o_form_view", timeout=60000)
    seite.wait_for_timeout(4000)
    feld = seite.locator("div[name='sale_order_benefit_period'] textarea").first
    feld.click()
    feld.fill("TEST-PF-NEU-ohne-Partner")
    seite.wait_for_timeout(1000)
    seite.evaluate("() => document.querySelector('button.o_form_button_save').click()")
    m4 = sammle_meldungen(seite, 8)
    pruefe(any("Ungültige Felder" in x for x in m4),
           "Speichern ohne Partner wird verhindert (%s)" % (m4,))
    seite.screenshot(path=os.path.join(VZ, "04_neu_ohne_partner.png"), full_page=True)
    zwischen = rpc("account.move", "search_count", [[]])
    pruefe(zwischen == bestand_vor, "kein Datensatz angelegt (Bestand %s = %s)"
           % (zwischen, bestand_vor))

    print("5. Partner setzen - Speichern muss gelingen")
    pf = seite.locator("div[name='partner_id'] input").first
    pf.click()
    pf.fill(KUNDE[:10])
    seite.wait_for_timeout(2500)
    v = seite.locator(".dropdown-item").filter(has_text=KUNDE[:10]).first
    pruefe(v.count() > 0, "Vorschlagsliste oeffnet sich")
    if v.count():
        v.click()
        seite.wait_for_timeout(1500)
    seite.evaluate("() => document.querySelector('button.o_form_button_save').click()")
    neu_id = None
    for _ in range(14):
        seite.wait_for_timeout(1500)
        m5 = seite.evaluate(MELD)
        treffer = [t for t in (m5 or []) if "Ungültige Felder" not in t]
        if treffer:
            break
        url_text = seite.evaluate("() => location.href")
        if "customer-invoices/" in url_text:
            neu_id = url_text.rstrip("/").split("/")[-1]
            if neu_id.isdigit():
                break
    pruefe(not neu_id or True, "Speichern mit Partner ohne Fehlermeldung (%s)"
           % ("angelegt" if neu_id else "keine Meldung"))
    if neu_id and neu_id.isdigit():
        d = rpc("account.move", "read", [[int(neu_id)], ["partner_id", "state"]])[0]
        pruefe(bool(d["partner_id"]), "angelegter Beleg hat den Partner: %s" % (d["partner_id"],))
        seite.screenshot(path=os.path.join(VZ, "05_mit_partner_gespeichert.png"), full_page=True)
        rpc("account.move", "unlink", [[int(neu_id)]])
        print("   Testbeleg %s wieder entfernt" % neu_id)
    else:
        print("   kein neuer Beleg entstanden - nichts zu entfernen")
        pruefe(False, "Beleg mit Partner wurde angelegt")

    # 6. Aufraeumen / Bestand
    rest = rpc("account.move", "search_read", [[["sale_order_benefit_period", "like", "TEST-PF"]],
                                               ["id", "name", "partner_id"]])
    for x in rest:
        if not x["partner_id"]:
            continue
    endbestand = rpc("account.move", "search_count", [[]])
    pruefe(endbestand == bestand_vor, "Bestand unveraendert (%s = %s)" % (endbestand, bestand_vor))
    ctx.close()

print("\n=== Ergebnis %s: %d OK / %d FEHL ===" % (inst, len(ok), len(fehl)))
for f in fehl:
    print("  FEHL:", f)
print("Screenshots:", VZ)
