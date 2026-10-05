"""A/B-Nachweis im Browser: Pflichtfeld "Partner" im Rechnungsformular.

Phase A: Ansicht MIT required="1" (alter Stand) -> Speichern ohne Partner erwartet die Meldung
Phase B: Ansicht OHNE required="1" (neuer Stand) -> Speichern ohne Partner muss gelingen

Die Ansicht wird nur voruebergehend im Arbeitsspeicher der DB geschrieben (ueber die ORM, Sprache en_US)
und am Ende auf den Auslieferungsstand des Moduls zurueckgesetzt.

Aufruf: python scripts/browser_pflichtfeld_ab.py lokal 132
"""
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def view_id():
    r = rpc("ir.ui.view", "search_read",
            [[["name", "=", "account.move.form.itk.o11.kopfbereich"]], ["id"]])
    if not r:
        raise SystemExit("ABBRUCH: Ansicht account.move.form.itk.o11.kopfbereich nicht gefunden")
    return r[0]["id"]


ALT = '<field name="partner_id" nolabel="1" readonly="state != \'draft\'"/>'
MIT = '<field name="partner_id" nolabel="1" required="1" readonly="state != \'draft\'"/>'


def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            w[k.strip()] = v.strip().strip('"')
    return w


env = lade_env(os.path.join(REPO, ".env"))
inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
tid = sys.argv[2] if len(sys.argv) > 2 else "132"
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


def rpc(model, method, args, kwargs=None, ctx=None):
    kw = dict(kwargs or {})
    kw["context"] = ctx or {"lang": "de_DE"}
    p = {"model": model, "method": method, "args": args, "kwargs": kw}
    r = json.loads(op.open(urllib.request.Request(
        url + "/web/dataset/call_kw", data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                        "params": p}).encode(),
        headers={"Content-Type": "application/json"})).read())
    if "error" in r:
        raise RuntimeError(str(r["error"])[:400])
    return r["result"]


def arch_lesen():
    return rpc("ir.ui.view", "read", [[VIEW_ID], ["arch_db"]], ctx={"lang": "en_US"})[0]["arch_db"]


def arch_schreiben(arch):
    rpc("ir.ui.view", "write", [[VIEW_ID], {"arch_db": arch}], ctx={"lang": "en_US"})


from playwright.sync_api import sync_playwright  # noqa: E402

MELD = """() => [...document.querySelectorAll('.o_notification, .o_dialog, .modal')]
    .map(e => (e.innerText||'').replace(/\\s+/g,' ').trim()).filter(t => t)"""

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session126",
                  "pflichtfeld_partner", inst)
os.makedirs(VZ, exist_ok=True)

VIEW_ID = view_id()
start = arch_lesen()
print("Ansicht %s, Laenge %s Zeichen, required im Knoten: %s"
      % (VIEW_ID, len(start),
         "ja" if "nolabel=\"1\" required=\"1\" readonly" in start else "nein"))


def mit_required(arch):
    if 'nolabel="1" required="1" readonly' in arch:
        return arch
    if arch.count(ALT) != 1:
        raise SystemExit("ABBRUCH: Ankerknoten nicht eindeutig (%d)" % arch.count(ALT))
    return arch.replace(ALT, MIT)


def ohne_required(arch):
    return arch.replace(MIT, ALT)


ergebnis = {}


def phase(name, arch, wert, screenshot):
    arch_schreiben(arch)
    rpc("account.move", "write", [[int(tid)], {"partner_id": False}])
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_ab_%s_%s" % (inst, name)),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1300})
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.goto("%s/odoo/customer-invoices/%s" % (url, tid))
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(5000)
        vorher = seite.evaluate("""() => {
            const i = document.querySelector("div[name='partner_id'] input");
            const l = [...document.querySelectorAll('label')].find(x => x.innerText.trim() === 'Kunde');
            return {partner: i ? i.value : 'FELD-FEHLT',
                    labelKlasse: l ? l.className : 'kein Label',
                    labelGewicht: l ? getComputedStyle(l).fontWeight : '-',
                    pflichtKlasse: (document.querySelector("div[name='partner_id']") || {}).className};}""")
        feld = seite.locator("div[name='sale_order_benefit_period'] textarea").first
        feld.click()
        feld.fill(wert)
        seite.wait_for_timeout(1500)
        seite.evaluate("() => document.querySelector('button.o_form_button_save').click()")
        meldungen = []
        for _ in range(12):
            seite.wait_for_timeout(2000)
            meldungen = seite.evaluate(MELD) or meldungen
            stand = rpc("account.move", "read", [[int(tid)],
                                                 ["sale_order_benefit_period", "partner_id", "state"]])[0]
            if stand["sale_order_benefit_period"] == wert:
                break
        seite.screenshot(path=os.path.join(VZ, screenshot), full_page=True)
        ctx.close()
    ergebnis[name] = {"meldungen": meldungen, "stand": stand, "vorher": vorher}
    print("\n--- Phase %s ---" % name)
    print("   Formular  :", vorher)
    print("   Meldungen :", meldungen if meldungen else "keine")
    print("   Datensatz :", stand)


try:
    phase("A_mit_required", mit_required(start), "TEST-PF-126-A", "A_mit_required.png")
    phase("B_ohne_required", ohne_required(start), "TEST-PF-126-B", "B_ohne_required.png")
finally:
    sauber = ohne_required(arch_lesen())
    arch_schreiben(sauber)
    print("\nAnsicht zurueckgesetzt (ohne required):",
          "nolabel=\"1\" required=\"1\"" not in arch_lesen())

a, b = ergebnis["A_mit_required"], ergebnis["B_ohne_required"]
print("\n=== Ergebnis ===")
print("A (alt, required): Meldung 'Ungueltige Felder' =",
      any("Ungültige Felder" in m for m in a["meldungen"]),
      "| Wert gespeichert =", a["stand"]["sale_order_benefit_period"] == "TEST-PF-126-A")
print("B (neu, ohne)    : Meldung 'Ungueltige Felder' =",
      any("Ungültige Felder" in m for m in b["meldungen"]),
      "| Wert gespeichert =", b["stand"]["sale_order_benefit_period"] == "TEST-PF-126-B")
print("Screenshots:", VZ)
