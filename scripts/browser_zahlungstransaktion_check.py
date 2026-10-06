"""Pruefung "Zahlungstransaktion" (payment_transaction_id) im Zahlungsformular.

Aufruf: python scripts/browser_zahlungstransaktion_check.py lokal|vm

Prueft am echten Bildschirm und per RPC:
  1. Feld sichtbar? Beschriftung?
  2. bedienbar (Eingabe/Auswahl) oder readonly? DOM-Klassen und Eingabefelder
  3. Modell-Readonly laut fields_get
  4. Belegung: payment_transaction_id, payment_token_id, use_electronic_payment_method
  5. Bestand: payment.transaction, payment.token, payment.provider
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


pid = rpc("account.payment", "search", [[]])[0]
daten = rpc("account.payment", "read", [[pid], ["name", "payment_transaction_id", "payment_token_id",
                                               "use_electronic_payment_method", "payment_method_code",
                                               "payment_method_line_id", "state"]])[0]
print("Instanz:", inst, "| Zahlung:", pid)
for k, v in daten.items():
    print("   %-32s %s" % (k, v))
print("   payment.transaction gesamt      :", rpc("payment.transaction", "search_count", [[]]))
print("   payment.token gesamt            :", rpc("payment.token", "search_count", [[]]))
print("   payment.provider gesamt         :", rpc("payment.provider", "search_count", [[]]))
f = rpc("account.payment", "fields_get", [["payment_transaction_id"], ["string", "type", "relation", "readonly"]])
print("   Felddefinition (Odoo 18)        :", f)

from playwright.sync_api import sync_playwright  # noqa: E402

DOM = """() => {
    const d = document.querySelector("div[name='payment_transaction_id']");
    if (!d) return {da: false};
    const lab = (d.closest('.o_wrap_field') || d.parentElement).querySelector('label');
    const st = lab ? getComputedStyle(lab) : null;
    return {da: true,
            beschriftung: lab ? lab.innerText.replace(/\\s+/g,' ').trim() : '-',
            klassen: d.className,
            readonlyKennzeichen: d.className.includes('o_readonly_modifier'),
            eingabefelder: d.querySelectorAll('input, select, textarea').length,
            wert: (d.innerText || '').replace(/\\s+/g,' ').trim(),
            sichtbar: !!(d.offsetParent),
            labelDeckkraft: st ? st.opacity : '-',
            labelKlasse: lab ? lab.className : '-'};}"""

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_tx_%s" % inst),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1300})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()
    seite.goto("%s/odoo/action-330/%s" % (url, pid))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(5000)
    print("\n--- DOM: Feld Zahlungstransaktion ---")
    print("   ", seite.evaluate(DOM))
    vz = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session126",
                      "zahlungstransaktion", inst)
    os.makedirs(vz, exist_ok=True)
    seite.screenshot(path=os.path.join(vz, "zahlungstransaktion_%s.png" % pid), full_page=True)
    print("Screenshot:", os.path.join(vz, "zahlungstransaktion_%s.png" % pid))
    ctx.close()
