"""Browser-Abnahme Zahlungsformular (Abrechnung > Verkauf/Einkauf > Zahlungen).

Aufruf: python scripts/browser_zahlungsformular_abnahme.py lokal|vm

Prueft am echten Bildschirm:
  1. sichtbare Beschriftungen im Odoo-11-Block = Odoo-11-Satz und -Reihenfolge
  2. technische Felder (Odoo-11-Zahlungsnummer, Status (Odoo 18)) stehen NICHT im Odoo-11-Block,
     sondern in eigener Gruppe darunter
  3. Statuskette mit Odoo-11-Werten, Rohstatus in der technischen Gruppe
  4. Pflichtfeld-Kennzeichnung wie Odoo 11 (Zahlungsbetrag, Zahlungsmethode)
  5. Beschriftungen einheitlich; heller nur readonly/leere Felder (Odoo-18-Standard)
  6. Smart Button "Rechnungen" erscheint nur bei verknuepften Rechnungen (wie Odoo 11)
  7. Lieferantenzahlung (Einkauf > Zahlungen): gleicher Aufbau, kein zweites Partnerfeld
  8. Testdaten entfernt, Bestand unveraendert
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
MARKER = "TEST-ZAHLUNG-126"
O11_LABELS = ["Zahlungsart", "Partnertyp", "Partner", "Zahlungsbetrag", "Zahlungsjournal",
              "Zahlungsmethode", "Zahlungsdatum", "Memo", "Zahlungstransaktion"]

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
        raise RuntimeError(str(r["error"])[:400])
    return r["result"]


def norm(t):
    return (t or "").replace("?", "").strip().upper()


LABELS = """() => [...document.querySelectorAll('.o_form_view label')]
    .filter(l => !l.className.includes('form-check-label'))
    .map(l => {
        const zeile = l.closest('.o_wrap_field') || l.parentElement;
        const feld = zeile ? zeile.querySelector('[name]') : null;
        const st = getComputedStyle(l);
        const sichtbar = feld ? !!(feld.offsetParent) : false;
        return {text: l.innerText.replace(/\\s+/g,' ').trim(), feld: feld ? feld.getAttribute('name') : null,
                sichtbar: sichtbar, gewicht: st.fontWeight, deckkraft: st.opacity};})
    .filter(x => x.sichtbar && x.text)"""

GRUPPENTITEL = """() => [...document.querySelectorAll('.o_form_view *')]
    .filter(e => e.children.length === 0 && /herkunft|status \\(odoo 18\\)/i.test(e.innerText || ''))
    .map(e => e.tagName + '.' + e.className + ' = ' + e.innerText.replace(/\\s+/g,' ').trim())"""

with open(os.path.join(os.environ.get("TEMP", "/tmp"), "_zahlergebnis.txt"), "w", encoding="utf-8"):
    pass

from playwright.sync_api import sync_playwright  # noqa: E402

ok, fehl = [], []


def pruefe(bedingung, text):
    (ok if bedingung else fehl).append(text)
    print(("  OK   " if bedingung else "  FEHL ") + text)


bestand_vor = rpc("account.payment", "search_count", [[]])
alle = rpc("account.payment", "search_read", [[], ["id", "name", "reconciled_invoices_count"]])
ohne = [x for x in alle if x["reconciled_invoices_count"] == 0][:1]
mit = [x for x in alle if x["reconciled_invoices_count"] > 0][:1]
# Auf der VM hat jede vorhandene Zahlung eine verknuepfte Rechnung -> Testzahlung ohne Rechnung
eigene_ohne = None
if not ohne:
    kunde = rpc("res.partner", "search_read", [[["customer_rank", ">", 0]], ["id", "name"]], {"limit": 1})[0]
    journal = rpc("account.journal", "search_read", [[["type", "=", "bank"]], ["id"]], {"limit": 1})[0]
    eigene_ohne = rpc("account.payment", "create", [{
        "payment_type": "inbound", "partner_type": "customer", "partner_id": kunde["id"],
        "journal_id": journal["id"], "amount": 12.0, "memo": MARKER, "date": "2026-10-05"}])
    ohne = [{"id": eigene_ohne, "name": "(Testzahlung)", "reconciled_invoices_count": 0}]
print("Instanz:", inst, "| Zahlungen:", bestand_vor, "| ohne Rechnung:", ohne, "| mit Rechnung:", mit)

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session126",
                  "zahlungsformular_abnahme", inst)
os.makedirs(VZ, exist_ok=True)

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_zfa_%s" % inst),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1300})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()

    # ---------- 1. bis 5. Kunden-Zahlung
    pid = ohne[0]["id"]
    seite.goto("%s/odoo/action-330/%s" % (url, pid))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(5000)
    labels = seite.evaluate(LABELS)
    texte = [x["text"] for x in labels]
    print("\n  Beschriftungen in Reihenfolge:", texte)
    pruefe([norm(t) for t in texte[:9]] == [norm(t) for t in O11_LABELS],
           "Odoo-11-Beschriftungen vollstaendig und in Odoo-11-Reihenfolge: %s" % texte[:9])
    pruefe("ODOO-11-ZAHLUNGSNUMMER" in [norm(t) for t in texte[9:]],
           "Odoo-11-Zahlungsnummer erscheint NACH dem Odoo-11-Block (technische Gruppe)")
    titel = seite.evaluate(GRUPPENTITEL)
    print("  Gruppentitel:", titel)
    pruefe(any("HERKUNFT" in norm(t) for t in titel) and any("STATUS (ODOO 18)" in norm(t) for t in titel),
           "technische Gruppen 'Herkunft (Migration)' und 'Status (Odoo 18)' vorhanden")
    pruefe(not any(x["feld"] in ("itk_o11_payment_number", "state") for x in labels[:9]),
           "keines der technischen Felder steht im Odoo-11-Block")

    pflicht = seite.evaluate("""() => ['amount','payment_method_line_id','payment_type','journal_id','date']
        .map(n => {const e = document.querySelector(\"div[name='\" + n + \"']\");
                   return {name: n, pflicht: e ? e.className.includes('o_required_modifier') : null};})""")
    print("  Pflichtfeld-Kennzeichnung:", pflicht)
    pruefe(all(x["pflicht"] for x in pflicht),
           "Zahlungsbetrag, Zahlungsmethode, Zahlungsart, Journal und Datum sind pflichtig (wie Odoo 11)")

    gewichte = {x["gewicht"] for x in labels}
    pruefe(gewichte == {"500"}, "Schriftgewicht aller Beschriftungen einheitlich (%s)" % gewichte)
    hell = sorted({x["feld"] for x in labels if x["deckkraft"] != "1"})
    print("  heller dargestellte Beschriftungen:", hell)
    pruefe(set(hell) <= {"payment_transaction_id", "itk_o11_payment_number", "state"},
           "heller nur readonly/leere Felder, Ursache = Odoo-18-Standard (o_form_label_readonly/-empty)")
    seite.screenshot(path=os.path.join(VZ, "01_kundenzahlung_%s.png" % pid), full_page=True)

    status = seite.evaluate("""() => ({
        kette: [...document.querySelectorAll('.o_statusbar_status button')]
            .map(b => b.innerText.replace(/\\s+/g,' ').trim()).filter(t => t && t !== '...'),
        roh: (document.querySelector(\"div[name='state']\") || {}).innerText || ''})""")
    print("  Statuskette:", status)
    pruefe(set(status["kette"]) >= {"Entwurf", "Gebucht", "Abgestimmt", "Abgebrochen"},
           "Odoo-11-Statuskette sichtbar")
    pruefe(bool(status["roh"].strip()), "Odoo-18-Rohstatus in der technischen Gruppe: %r" % status["roh"])

    # ---------- 6. Smart Button
    knoepfe_ohne = seite.evaluate("() => [...document.querySelectorAll('.oe_stat_button')].map(b => b.innerText.trim())")
    pruefe(not any("Rechnungen" in k for k in knoepfe_ohne),
           "ohne verknuepfte Rechnung kein Smart Button (wie Odoo 11): %s" % knoepfe_ohne)
    if mit:
        seite.goto("%s/odoo/action-330/%s" % (url, mit[0]["id"]))
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(4500)
        knoepfe = seite.evaluate("() => [...document.querySelectorAll('.oe_stat_button')].map(b => b.innerText.replace(/\\s+/g,' ').trim())")
        print("  Smart Buttons bei Zahlung %s: %s" % (mit[0]["id"], knoepfe))
        pruefe(any("Rechnungen" in k for k in knoepfe),
               "Smart Button 'Rechnungen' bei verknuepfter Rechnung sichtbar")
        seite.screenshot(path=os.path.join(VZ, "02_smartbutton.png"), full_page=True)

    # ---------- 7. Lieferantenzahlung
    lieferant = rpc("res.partner", "search_read", [[["supplier_rank", ">", 0]], ["id", "name"]], {"limit": 1})
    journal = rpc("account.journal", "search_read", [[["type", "=", "bank"]], ["id", "name"]], {"limit": 1})
    lid = None
    if lieferant and journal:
        lid = rpc("account.payment", "create", [{
            "payment_type": "outbound", "partner_type": "supplier", "partner_id": lieferant[0]["id"],
            "journal_id": journal[0]["id"], "amount": 10.0, "memo": MARKER, "date": "2026-10-05"}])
        seite.goto("%s/odoo/action-331/%s" % (url, lid))
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(5000)
        l2 = seite.evaluate(LABELS)
        t2 = [x["text"] for x in l2]
        print("\n  Lieferantenzahlung:", t2)
        pruefe([norm(t) for t in t2[:9]] == [norm(t) for t in O11_LABELS],
               "Lieferantenzahlung: gleiche Odoo-11-Beschriftungen")
        pruefe(sum(1 for x in l2 if x["feld"] == "partner_id") == 1,
               "Lieferantenzahlung: genau ein Partnerfeld (%d gefunden)"
               % sum(1 for x in l2 if x["feld"] == "partner_id"))
        pruefe(sum(1 for x in l2 if x["feld"] == "journal_id") == 1, "genau ein Journalfeld")
        pruefe(sum(1 for x in l2 if x["feld"] == "date") == 1, "genau ein Datumsfeld")
        pruefe(sum(1 for x in l2 if x["feld"] == "memo") == 1, "genau ein Memofeld")
        pruefe(any("ZAHLUNGSNUMMER" in norm(x["text"]) for x in l2),
               "Lieferantenzahlung: technische Gruppe vorhanden")
        seite.screenshot(path=os.path.join(VZ, "03_lieferantenzahlung.png"), full_page=True)
    else:
        pruefe(False, "Lieferant/Journal fuer den Test gefunden")

    # ---------- 8. Aufraeumen
    if lid:
        rpc("account.payment", "unlink", [[lid]])
        print("  Testzahlung %s entfernt" % lid)
    if eigene_ohne:
        rpc("account.payment", "unlink", [[eigene_ohne]])
        print("  Testzahlung ohne Rechnung %s entfernt" % eigene_ohne)
    rest = rpc("account.payment", "search_read", [[["memo", "like", MARKER]], ["id"]])
    pruefe(len(rest) == 0, "keine Testzahlung zurueckgeblieben")
    pruefe(rpc("account.payment", "search_count", [[]]) == bestand_vor,
           "Bestand unveraendert (%s = %s)" % (rpc("account.payment", "search_count", [[]]), bestand_vor))
    ctx.close()

print("\n=== Ergebnis %s: %d OK / %d FEHL ===" % (inst, len(ok), len(fehl)))
for f in fehl:
    print("  FEHL:", f)
print("Screenshots:", VZ)
