"""Abnahme des Zahlungsformulars: Smart Button (0/1/mehrere Rechnungen) und Statuskette.

Aufruf: python scripts/_zahlung_abnahme.py vm|lokal
Legt Testdaten an, prueft im echten Browser, raeumt danach alles wieder weg.
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
             "params": {"model": model, "method": method, "args": args,
                        "kwargs": {"context": context or CTX}}}
    req = urllib.request.Request(url + "/web/dataset/call_kw", data=json.dumps(daten).encode(),
                                 headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
    antwort = json.loads(op.open(req, timeout=180).read().decode())
    if "error" in antwort:
        raise RuntimeError(str(antwort["error"])[:300])
    return antwort["result"]


def erstes(model, dom, felder):
    treffer = kw(model, "search_read", [dom, felder])
    return treffer[0] if treffer else None


partner = erstes("res.partner", [["customer_rank", ">", 0]], ["id", "name"])
steuer = erstes("account.tax", [["type_tax_use", "=", "sale"]], ["id", "name"])
journal = erstes("account.journal", [["type", "=", "bank"]], ["id", "name"])

# --- Zustaende vorher merken
vorher = {m: kw(m, "search_count", [[]]) for m in ("account.payment", "account.move")}
print("Bestand vorher:", vorher)


def rechnung(betrag, ref):
    rid = kw("account.move", "create", [{
        "move_type": "out_invoice", "partner_id": partner["id"], "invoice_date": "2026-10-02", "ref": ref,
        "invoice_line_ids": [(0, 0, {"name": "Testzeile", "quantity": 1.0, "price_unit": betrag,
                                     "tax_ids": [(6, 0, [steuer["id"]] if steuer else [])]})]}])
    kw("account.move", "action_post", [[rid]])
    return rid


r1 = rechnung(100.0, "TEST-ABNAHME-A")
r2 = rechnung(50.0, "TEST-ABNAHME-B")
kontext = dict(CTX, active_model="account.move", active_ids=[r1, r2])
assistent = kw("account.payment.register", "create", [{"journal_id": journal["id"], "payment_date": "2026-10-02"}],
               context=kontext)
kw("account.payment.register", "action_create_payments", [[assistent]], context=kontext)
mehrfach = kw("account.payment", "search_read",
              [[["memo", "like", "TEST-ABNAHME"]], ["id", "state", "is_reconciled", "reconciled_invoice_ids", "amount"]])
print("Zahlung mit mehreren Rechnungen:", mehrfach)
z_mehrfach = mehrfach[0]["id"] if mehrfach else None

entwurf = kw("account.payment", "create", [{
    "payment_type": "inbound", "partner_type": "customer", "partner_id": partner["id"], "amount": 10.0,
    "journal_id": journal["id"], "date": "2026-10-02", "memo": "TEST-ABNAHME-ENTWURF"}])
gebucht = kw("account.payment", "create", [{
    "payment_type": "inbound", "partner_type": "customer", "partner_id": partner["id"], "amount": 20.0,
    "journal_id": journal["id"], "date": "2026-10-02", "memo": "TEST-ABNAHME-GEBUCHT"}])
kw("account.payment", "action_post", [[gebucht]])
abgebrochen = kw("account.payment", "create", [{
    "payment_type": "inbound", "partner_type": "customer", "partner_id": partner["id"], "amount": 30.0,
    "journal_id": journal["id"], "date": "2026-10-02", "memo": "TEST-ABNAHME-ABGEBROCHEN"}])
kw("account.payment", "action_post", [[abgebrochen]])
kw("account.payment", "action_cancel", [[abgebrochen]])
print("Testzahlungen: mehrfach=%s entwurf=%s gebucht=%s abgebrochen=%s" % (
    z_mehrfach, entwurf, gebucht, abgebrochen))

JS_ZUSTAND = """
() => {
  const sichtbar = (e) => !!e.getClientRects().length;
  const status = [...document.querySelectorAll('.o_form_statusbar button')].filter(sichtbar)
      .map(e => ({text: (e.textContent || '').trim(), aktiv: e.classList.contains('btn-primary')}));
  const smart = [...document.querySelectorAll('.oe_stat_button')].filter(sichtbar).map(e => (e.textContent || '').trim());
  const o18 = [...document.querySelectorAll('.o_field_widget[name=state]')].map(e => (e.textContent || '').trim());
  return {status: status, smart: smart, odoo18_state: o18};
}
"""
JS_LISTE = """
() => {
  const zeilen = [...document.querySelectorAll('.o_data_row')].map(r => (r.textContent || '').trim().slice(0, 40));
  const titel = (document.querySelector('.o_breadcrumb, .o_control_panel') || {}).textContent || '';
  return {anzahl: zeilen.length, zeilen: zeilen, titel: titel.slice(0, 80)};
}
"""

from playwright.sync_api import sync_playwright  # noqa: E402

ergebnis = {}
with sync_playwright() as pw:
    ktx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ["TEMP"], "pw_abn_%s" % os.getpid()),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
    ktx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    s = ktx.pages[0] if ktx.pages else ktx.new_page()

    vz = r"C:/Users/anna.maierhofer/Desktop/Odoo18-Abnahme-Session122/rechnung"

    def oeffne(pid, name):
        s.goto("%s/web#id=%s&model=account.payment&view_type=form" % (url, pid))
        s.wait_for_selector(".o_form_view", timeout=120000)
        s.wait_for_timeout(3500)
        z = s.evaluate(JS_ZUSTAND)
        print("   %-22s Statuskette=%s O18=%s Smart=%s" % (name, z["status"], z["odoo18_state"], z["smart"]))
        s.screenshot(path="%s/zahlung_%s_%s.png" % (vz, name, instanz), full_page=True)
        return z

    print("--- Entwurf (ohne Rechnungsbezug) ---")
    ergebnis["entwurf"] = oeffne(entwurf, "entwurf")

    print("--- Gebucht (in_process, ohne Abstimmung) ---")
    ergebnis["gebucht"] = oeffne(gebucht, "gebucht")

    print("--- Abgebrochen ---")
    ergebnis["abgebrochen"] = oeffne(abgebrochen, "abgebrochen")

    if z_mehrfach:
        print("--- Zahlung mit mehreren Rechnungen + Smart-Button-Test ---")
        ergebnis["mehrfach"] = oeffne(z_mehrfach, "mehrere")
        try:
            s.locator(".oe_stat_button").first.click()
            s.wait_for_timeout(6000)
            liste = s.evaluate(JS_LISTE)
            print("   Smart Button geoeffnet: %s" % liste)
            ergebnis["liste"] = liste
            s.screenshot(path="%s/zahlung_smartbutton_liste_%s.png" % (vz, instanz), full_page=True)
        except Exception as fehler:
            print("   Smart-Button-Klick fehlgeschlagen:", str(fehler)[:120])
            ergebnis["liste"] = {"fehler": str(fehler)[:120]}
    ktx.close()

# --- Aufraeumen
for pid in [entwurf, gebucht, abgebrochen, z_mehrfach]:
    if not pid:
        continue
    try:
        kw("account.payment", "action_draft", [[pid]])
    except Exception:
        pass
    try:
        kw("account.payment", "unlink", [[pid]])
    except Exception as fehler:
        print("Zahlung %s nicht entfernbar: %s" % (pid, str(fehler)[:120]))
for rid in (r1, r2):
    try:
        kw("account.move", "button_draft", [[rid]])
    except Exception:
        pass
    try:
        kw("account.move", "unlink", [[rid]])
    except Exception as fehler:
        print("Rechnung %s nicht entfernbar: %s" % (rid, str(fehler)[:120]))

nachher = {m: kw(m, "search_count", [[]]) for m in ("account.payment", "account.move")}
print("Bestand nachher:", nachher)
print("Testdaten uebrig:", kw("account.payment", "search_count", [[["memo", "like", "TEST-ABNAHME"]]]),
      kw("account.move", "search_count", [[["ref", "like", "TEST-ABNAHME"]]]))
json.dump(ergebnis, open(r"C:/Odoo-Test/docs/_zahlung_abnahme_%s.json" % instanz, "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
