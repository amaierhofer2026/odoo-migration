"""Abnahme Smart Button "Rechnungen": 2 verknuepfte Rechnungen, 1 Zahlung, Klick-Test.

Aufruf: python scripts/_smartbutton_abnahme.py vm|lokal
Legt Testdaten an, prueft im Browser (Anzeige + geoeffnete Liste), raeumt danach auf.
"""
import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import lade_env  # noqa: E402

env = lade_env(r"C:/Odoo-Test/.env")
instanz = sys.argv[1] if len(sys.argv) > 1 else "vm"
url = "https://k001959vsx.ipax.at" if instanz == "vm" else "http://localhost:8069"
domain = "k001959vsx.ipax.at" if "k001959" in url else "localhost"
CTX = {"lang": "de_DE"}

jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(url + "/web/session/authenticate", data=json.dumps({
    "jsonrpc": "2.0", "method": "call",
    "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]}}).encode(),
    headers={"Content-Type": "application/json"}), timeout=120)
sid = next(c.value for c in jar if c.name == "session_id")


def kw(model, method, args, context=None):
    daten = {"jsonrpc": "2.0", "method": "call",
             "params": {"model": model, "method": method, "args": args, "kwargs": {"context": context or CTX}}}
    req = urllib.request.Request(url + "/web/dataset/call_kw", data=json.dumps(daten).encode(),
                                 headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
    antwort = json.loads(op.open(req, timeout=180).read().decode())
    if "error" in antwort:
        raise RuntimeError(str(antwort["error"])[:250])
    return antwort["result"]


def erstes(model, dom, felder):
    treffer = kw(model, "search_read", [dom, felder])
    return treffer[0] if treffer else None


vorher = {"zahlungen": kw("account.payment", "search_count", [[]]), "belege": kw("account.move", "search_count", [[]])}
print("Bestand vorher:", vorher)

kunde = erstes("res.partner", [["customer_rank", ">", 0]], ["id", "name"])
lieferant = erstes("res.partner", [["supplier_rank", ">", 0]], ["id", "name"]) or kunde
steuer_verkauf = erstes("account.tax", [["type_tax_use", "=", "sale"]], ["id", "name"])
steuer_einkauf = erstes("account.tax", [["type_tax_use", "=", "purchase"]], ["id", "name"]) or steuer_verkauf
journal = erstes("account.journal", [["type", "=", "bank"]], ["id", "name"])


def beleg(art, partner, steuer, betrag, ref):
    bid = kw("account.move", "create", [{
        "move_type": art, "partner_id": partner["id"], "invoice_date": "2026-10-02", "ref": ref,
        "invoice_line_ids": [(0, 0, {"name": "Testzeile Smart Button", "quantity": 1.0, "price_unit": betrag,
                                     "tax_ids": [(6, 0, [steuer["id"]] if steuer else [])]})]}])
    kw("account.move", "action_post", [[bid]])
    return bid


def zahlung_fuer(ids):
    kontext = dict(CTX, active_model="account.move", active_ids=ids)
    assistent = kw("account.payment.register", "create", [{"journal_id": journal["id"], "payment_date": "2026-10-02", "group_payment": True}],
                   context=kontext)
    kw("account.payment.register", "action_create_payments", [[assistent]], context=kontext)
    treffer = kw("account.payment", "search_read",
                 [[["reconciled_invoice_ids", "in", ids], ["reconciled_bill_ids", "in", ids]],
                  ["id", "name", "amount", "state", "is_reconciled", "reconciled_invoice_ids", "reconciled_bill_ids"]])
    return treffer


k1 = beleg("out_invoice", kunde, steuer_verkauf, 100.0, "TEST-SB-A")
k2 = beleg("out_invoice", kunde, steuer_verkauf, 50.0, "TEST-SB-B")
kunde_zahlungen = zahlung_fuer([k1, k2])
print("Kundenzahlung mit 2 Rechnungen:", kunde_zahlungen)

l1 = beleg("in_invoice", lieferant, steuer_einkauf, 80.0, "TEST-SB-C")
l2 = beleg("in_invoice", lieferant, steuer_einkauf, 20.0, "TEST-SB-D")
liefer_zahlungen = zahlung_fuer([l1, l2])
print("Lieferantenzahlung mit 2 Belegen:", liefer_zahlungen)

JS = """
() => {
  const sichtbar = (e) => !!e.getClientRects().length;
  const smart = [...document.querySelectorAll('.oe_stat_button')].filter(sichtbar).map(e => (e.textContent || '').trim());
  const status = [...document.querySelectorAll('.o_form_statusbar button')].filter(sichtbar)
      .map(e => ({t: (e.textContent || '').trim(), aktiv: e.classList.contains('btn-primary') || e.classList.contains('o_arrow_button_current') || e.getAttribute('aria-current') === 'true'}));
  return {smart: smart, status: status};
}
"""
JS_LISTE = """
() => {
  const zeilen = [...document.querySelectorAll('.o_data_row')].map(r => (r.textContent || '').trim().slice(0, 50));
  return {anzahl: zeilen.length, zeilen: zeilen};
}
"""

from playwright.sync_api import sync_playwright  # noqa: E402

vz = r"C:/Users/anna.maierhofer/Desktop/Odoo18-Abnahme-Session122/rechnung"
bericht = {}
with sync_playwright() as pw:
    ktx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ["TEMP"], "pw_sb_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
    ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ktx.pages[0] if ktx.pages else ktx.new_page()
    for bezeichnung, liste in (("kunde", kunde_zahlungen), ("lieferant", liefer_zahlungen)):
        if not liste:
            print("%s: keine Zahlung erzeugt" % bezeichnung)
            continue
        pid = liste[0]["id"]
        s.goto("%s/web#id=%s&model=account.payment&view_type=form" % (url, pid))
        s.wait_for_selector(".o_form_view", timeout=120000)
        s.wait_for_timeout(3500)
        zustand = s.evaluate(JS)
        print("%s Zahlung id %s: SmartButtons=%s Statuskette=%s" % (bezeichnung, pid, zustand["smart"], zustand["status"]))
        s.screenshot(path="%s/smartbutton_%s_%s.png" % (vz, bezeichnung, instanz), full_page=True)
        try:
            s.locator(".oe_stat_button").first.click()
            s.wait_for_timeout(6000)
            liste_geoeffnet = s.evaluate(JS_LISTE)
            print("   geoeffnete Liste: %s" % liste_geoeffnet)
            bericht[bezeichnung] = {"zahlung": pid, "smart": zustand["smart"], "liste": liste_geoeffnet}
            s.screenshot(path="%s/smartbutton_%s_liste_%s.png" % (vz, bezeichnung, instanz), full_page=True)
        except Exception as fehler:
            print("   Klick fehlgeschlagen:", str(fehler)[:120])
    ktx.close()

# --- Aufraeumen
for z in kunde_zahlungen + liefer_zahlungen:
    for schritt in ("action_cancel", "action_draft", "unlink"):
        try:
            kw("account.payment", schritt, [[z["id"]]])
        except Exception:
            pass
for bid in (k1, k2, l1, l2):
    for schritt in ("button_draft", "unlink"):
        try:
            kw("account.move", schritt, [[bid]])
        except Exception:
            pass

nachher = {"zahlungen": kw("account.payment", "search_count", [[]]), "belege": kw("account.move", "search_count", [[]])}
print("Bestand nachher:", nachher)
print("Testbelege uebrig:", kw("account.move", "search_count", [[["ref", "like", "TEST-SB"]]]),
      "Testzahlungen uebrig:", kw("account.payment", "search_count", [[["memo", "like", "TEST-SB"]]]))
json.dump(bericht, open(r"C:/Odoo-Test/docs/_smartbutton_%s.json" % instanz, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
