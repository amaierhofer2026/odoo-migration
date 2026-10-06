"""Abnahme Session 126: Partnerpflicht im Rechnungsformular nach dem Aufraeumen.

Prueft am echten Bildschirm (Auftrag Anna, 05.10.2026):
  0. Vorbedingung: kein Rechnungs-/Gutschriftenentwurf ohne Partner vorhanden
  1. Menue Abrechnung > Verkauf > Eingaenge oeffnet ohne Meldung
  2. Menue Abrechnung > Einkauf > Eingaenge oeffnet ohne Meldung
  3. gueltiger Beleg (mit Partner): oeffnen und Tab-Wechsel ohne Meldung
  4. gueltiger Beleg: Aenderung + Menuewechsel -> automatisches Speichern ohne Meldung,
     Aenderung ist gespeichert
  5. neuer Beleg ohne Partner: Speichern wird verhindert, kein Datensatz
  6. Partner setzen -> Speichern gelingt, Partner korrekt
  7. Testdaten entfernt, Bestand unveraendert, weiterhin kein Entwurf ohne Partner

Aufruf: python scripts/browser_abrechnung_partnerpflicht_abnahme.py lokal|vm
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
url = "http://localhost:8069" if inst != "vm" else "https://k001959vsx.ipax.at"
domain = "localhost" if inst != "vm" else "k001959vsx.ipax.at"
MARKER = "TEST-PP-126"

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


TYPEN = ["out_invoice", "out_refund", "in_invoice", "in_refund", "out_receipt", "in_receipt"]
OHNE = [["partner_id", "=", False], ["move_type", "in", TYPEN]]
kunde = rpc("res.partner", "search_read", [[["customer_rank", ">", 0]], ["id", "name"]], {"limit": 1})[0]
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

ok, fehl = [], []


def pruefe(bedingung, text):
    (ok if bedingung else fehl).append(text)
    print(("  OK   " if bedingung else "  FEHL ") + text)


def meldungen(seite, sekunden=7):
    gesammelt = []
    for _ in range(int(sekunden / 0.3)):
        for x in seite.evaluate(MELD):
            if x not in gesammelt:
                gesammelt.append(x)
        if gesammelt:
            break
        seite.wait_for_timeout(300)
    return gesammelt


VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session126",
                  "partnerpflicht_nach_aufraeumen", inst)
os.makedirs(VZ, exist_ok=True)

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_ppn_%s" % inst),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1300})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()

    print("0. Vorbedingung")
    offen = rpc("account.move", "search_read", [OHNE, ["id", "move_type"]])
    pruefe(len(offen) == 0, "kein Entwurf ohne Partner vorhanden (%s)" % (offen,))

    print("1./2. Menues Eingaenge")
    for abschnitt in ("Verkauf", "Einkauf"):
        seite.goto("%s/odoo/action-354" % url)
        seite.wait_for_selector(".o_list_view", timeout=90000)
        seite.wait_for_timeout(3500)
        a = seite.locator(".o_menu_sections > li > a, .o_menu_sections button") \
                 .filter(has_text=abschnitt).first
        a.click()
        seite.wait_for_timeout(1500)
        p = seite.locator(".o-dropdown--menu .dropdown-item").filter(has_text="Eingänge").first
        p.click()
        seite.wait_for_timeout(5000)
        mm = seite.evaluate(MELD)
        pruefe(not mm, "Abrechnung > %s > Eingänge ohne Meldung (%s)"
               % (abschnitt, mm if mm else "keine"))
        seite.screenshot(path=os.path.join(VZ, "01_%s_eingaenge.png" % abschnitt.lower()),
                         full_page=True)

    # gueltiger Beleg = erster Entwurf mit Partner
    gueltig = rpc("account.move", "search_read",
                  [[["move_type", "=", "out_invoice"], ["partner_id", "!=", False],
                    ["state", "=", "draft"]], ["id", "partner_id"]], {"limit": 1})[0]
    print("3. gueltiger Beleg %s" % gueltig["id"])
    seite.goto("%s/odoo/customer-invoices/%s" % (url, gueltig["id"]))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(4000)
    pruefe(not seite.evaluate(MELD), "gueltiger Beleg oeffnet ohne Meldung")
    seite.evaluate(VERSTECKEN)
    m3 = meldungen(seite, 5)
    pruefe(not m3, "Tab-Wechsel beim gueltigen Beleg ohne Meldung (%s)" % (m3 if m3 else "keine"))
    seite.evaluate(ZEIGEN)
    seite.screenshot(path=os.path.join(VZ, "02_gueltiger_beleg.png"), full_page=True)

    # eigener Testbeleg MIT Partner fuer Aenderung + Menuewechsel
    print("4. Aenderung + Menuewechsel (eigener Testbeleg mit Partner)")
    journal = rpc("account.journal", "search_read", [[["type", "=", "sale"]], ["id"]])[0]["id"]
    tid = rpc("account.move", "create", [{
        "move_type": "out_invoice", "partner_id": kunde["id"], "journal_id": journal,
        "ref": MARKER, "invoice_line_ids": [(0, 0, {"name": MARKER + " Zeile", "quantity": 1.0,
                                                    "price_unit": 5.0, "tax_ids": [(6, 0, [])]})]}])
    seite.goto("%s/odoo/customer-invoices/%s" % (url, tid))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(4000)
    feld = seite.locator("div[name='sale_order_benefit_period'] textarea").first
    feld.click()
    feld.fill("TEST-PP-126-geaendert")
    seite.wait_for_timeout(1200)
    a = seite.locator(".o_menu_sections > li > a, .o_menu_sections button").filter(has_text="Verkauf").first
    a.click()
    seite.wait_for_timeout(1500)
    seite.locator(".o-dropdown--menu .dropdown-item").filter(has_text="Ausgangsrechnungen").first.click()
    m4 = meldungen(seite, 8)
    pruefe(not m4, "Menuewechsel bei geaendertem gueltigem Beleg ohne Meldung (%s)"
           % (m4 if m4 else "keine"))
    d4 = rpc("account.move", "read", [[tid], ["sale_order_benefit_period", "partner_id"]])[0]
    pruefe(d4["sale_order_benefit_period"] == "TEST-PP-126-geaendert",
           "Aenderung wurde automatisch gespeichert (%s)" % d4["sale_order_benefit_period"])
    seite.screenshot(path=os.path.join(VZ, "03_menuewechsel_gueltig.png"), full_page=True)
    rpc("account.move", "unlink", [[tid]])
    print("   Testbeleg %s wieder entfernt" % tid)

    print("5. neuer Beleg ohne Partner")
    seite.goto("%s/odoo/action-354" % url)
    seite.wait_for_selector(".o_list_view", timeout=90000)
    seite.wait_for_timeout(3500)
    seite.locator("button").filter(has_text="Neu").first.click()
    seite.wait_for_selector(".o_form_view", timeout=60000)
    seite.wait_for_timeout(4000)
    f = seite.locator("div[name='sale_order_benefit_period'] textarea").first
    f.click()
    f.fill(MARKER + "-ohne-Partner")
    seite.wait_for_timeout(1000)
    seite.evaluate("() => document.querySelector('button.o_form_button_save').click()")
    m5 = meldungen(seite, 8)
    pruefe(any("Ungültige Felder" in x for x in m5), "Speichern ohne Partner verhindert (%s)" % (m5,))
    pruefe(rpc("account.move", "search_count", [[]]) == bestand_vor,
           "kein Datensatz angelegt (Bestand %s = %s)"
           % (rpc("account.move", "search_count", [[]]), bestand_vor))
    seite.screenshot(path=os.path.join(VZ, "04_neu_ohne_partner.png"), full_page=True)
    seite.evaluate(VERSTECKEN)
    meldungen(seite, 3)
    seite.evaluate(ZEIGEN)

    print("6. Partner setzen und speichern")
    pf = seite.locator("div[name='partner_id'] input").first
    pf.click()
    pf.fill(kunde["name"][:10])
    seite.wait_for_timeout(2500)
    v = seite.locator(".dropdown-item").filter(has_text=kunde["name"][:10]).first
    pruefe(v.count() > 0, "Vorschlagsliste oeffnet sich")
    if v.count():
        v.click()
        seite.wait_for_timeout(1500)
    seite.evaluate("() => document.querySelector('button.o_form_button_save').click()")
    neu_id = None
    for _ in range(14):
        seite.wait_for_timeout(1500)
        if seite.evaluate(MELD):
            break
        u = seite.evaluate("() => location.href")
        if "customer-invoices/" in u:
            kandidat = u.rstrip("/").split("/")[-1]
            if kandidat.isdigit():
                neu_id = int(kandidat)
                break
    pruefe(neu_id is not None, "Beleg mit Partner angelegt (id %s)" % neu_id)
    if neu_id:
        d = rpc("account.move", "read", [[neu_id], ["partner_id", "state"]])[0]
        pruefe(d["partner_id"] and d["partner_id"][0] == kunde["id"],
               "Partner korrekt zugeordnet: %s" % (d["partner_id"],))
        seite.screenshot(path=os.path.join(VZ, "05_mit_partner.png"), full_page=True)
        rpc("account.move", "unlink", [[neu_id]])
        print("   Testbeleg %s wieder entfernt" % neu_id)

    print("7. Abschluss")
    pruefe(rpc("account.move", "search_count", [[]]) == bestand_vor,
           "Bestand unveraendert (%s = %s)" % (rpc("account.move", "search_count", [[]]), bestand_vor))
    pruefe(len(rpc("account.move", "search_read", [OHNE, ["id"]])) == 0,
           "weiterhin kein Entwurf ohne Partner")
    ctx.close()

print("\n=== Ergebnis %s: %d OK / %d FEHL ===" % (inst, len(ok), len(fehl)))
for f in fehl:
    print("  FEHL:", f)
print("Screenshots:", VZ)
