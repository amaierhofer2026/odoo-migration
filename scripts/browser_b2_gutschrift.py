"""Browser-Nachweis B2 (read-only): Gutschrift-Dialog in Odoo 18 auf der VM.

Oeffnet eine gebuchte Rechnung, klickt "Gutschrift", liest den Dialog aus (Felder, Beschriftungen,
Buttons, Vorbelegungen) und bricht ihn ohne Ausfuehrung ab. Danach Kontrolle, dass kein Beleg
angelegt wurde.

Aufruf:  uv run --with playwright python scripts/browser_b2_gutschrift.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "b2")


def lade_env(pfad):
    werte = {}
    for zeile in open(pfad, encoding="utf-8"):
        if "=" in zeile and not zeile.strip().startswith("#"):
            k, v = zeile.split("=", 1)
            werte[k.strip()] = v.strip().strip('"')
    return werte


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"

    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rufe(pfad, prm):
        req = urllib.request.Request(url + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                                  "params": prm}).encode(),
                                     headers={"Content-Type": "application/json"})
        with op.open(req, timeout=180) as f:
            return json.loads(f.read().decode())

    rufe("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                       "password": env["ODOO18_PWD"]})
    sid = next(c.value for c in jar if c.name == "session_id")

    def kw(model, methode, args, **kwargs):
        o = rufe("/web/dataset/call_kw", {"model": model, "method": methode, "args": args, "kwargs": kwargs})
        if "error" in o:
            raise RuntimeError(str(o["error"])[:300])
        return o.get("result")

    offene = kw("account.move", "search_read",
                [[("move_type", "=", "out_invoice"), ("state", "=", "posted")],
                 ["id", "name", "partner_id", "amount_residual", "payment_state"]],
                order="id desc", limit=1)
    r = offene[0]
    anzahl_vorher = kw("account.move", "search_count", [[]])
    print("Instanz : %s" % url)
    print("Beleg   : id %s | %s | %s | Rest %s | %s"
          % (r["id"], r["name"], r["partner_id"][1], r["amount_residual"], r["payment_state"]))
    print("Belege vor dem Test: %s" % anzahl_vorher)

    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    ok = fehler = 0
    js_fehler, rpc_fehler = [], []

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_b2_%s_%s" % (a.instanz, os.getpid())),
            channel="chrome", headless=True, viewport={"width": 1800, "height": 1300})
        ctx.add_init_script(
            "window.__errs=[];"
            "window.addEventListener('error', e => window.__errs.push(''+e.message));"
            "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));"
            "const ce=console.error; console.error=(...x)=>{window.__errs.push(x.map(String).join(' ')); ce(...x);};")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.on("response", lambda resp: rpc_fehler.append("%s %s" % (resp.status, resp.url))
                 if ("/web/dataset/call_kw" in resp.url and resp.status >= 400) else None)

        def sichtbar(sel):
            return seite.evaluate("""(sel) => [...document.querySelectorAll(sel)]
                .filter(e => e.getClientRects().length)
                .map(e => e.innerText.replace(/\\s+/g, ' ').trim()).filter(t => t)""", sel)

        seite.goto("%s/odoo/m-account.move/%s" % (url, r["id"]))
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(4000)

        print("\n--- 1. Dialog oeffnen ---")
        knopf = None
        for el in seite.query_selector_all("button"):
            if el.is_visible() and el.inner_text().strip() == "Gutschrift":
                knopf = el
                break
        pruefe(knopf is not None, "Button 'Gutschrift' gefunden")
        if knopf is None:
            ctx.close()
            print("\n%d OK / %d FEHL" % (ok, fehler))
            return 1
        knopf.click()
        try:
            seite.wait_for_selector(".o_dialog", state="attached", timeout=60000)
            seite.wait_for_function(
                "() => !!document.querySelector('.o_dialog .o_field_widget[name=\"reason\"]')",
                timeout=60000)
        except Exception as fehler:
            print("  Hinweis: Dialog nicht vollstaendig erkannt (%s)" % str(fehler)[:70])
        seite.wait_for_timeout(2500)

        titel = sichtbar(".modal-title, .modal-header")
        felder = seite.evaluate("""() => [...document.querySelectorAll('.modal .o_field_widget')]
            .filter(e => e.getClientRects().length)
            .map(e => ({
                name: e.getAttribute('name'),
                typ: (e.className.match(/o_field_[a-z_]+/) || [''])[0],
                label: (() => {
                    const w = e.closest('.o_wrap_field') || e.closest('.o_inner_group');
                    const l = w && w.previousElementSibling ? w.previousElementSibling.innerText : '';
                    return (l || '').trim();
                })(),
                wert: (e.querySelector('input, select, textarea') || e).value !== undefined
                      ? (e.querySelector('input, select, textarea') || e).value : e.innerText.trim()}))
        """)
        buttons = sichtbar(".modal-footer button")
        print("  Dialogtitel : %s" % titel)
        for f in felder:
            print("  Feld        : %-18s %-16s label=%-34s wert=%r"
                  % (f["name"], f["typ"], (f["label"] or "")[:34], (f["wert"] or "")[:40]))
        print("  Buttons     : %s" % buttons)
        pruefe(any("reason" == f["name"] for f in felder), "Feld 'Begruendung' im Dialog vorhanden")
        pruefe(any(f["name"] in ("date", "journal_id") for f in felder), "Datum/Journal im Dialog vorhanden")
        pruefe(len(buttons) >= 2, "mindestens zwei Buttons im Dialog (%s)" % buttons)
        pruefe(any(("Stornieren" in b or "Gutschrift" in b) and "Verwerfen" not in b for b in buttons),
               "Button zum Erstellen der Gutschrift vorhanden")
        pruefe(any("Rechnung erstellen" in b or "Create Invoice" in b for b in buttons),
               "zweiter Weg (Stornieren und Rechnung erstellen) im Dialog vorhanden")
        seite.screenshot(path=os.path.join(VZ, "01_Gutschrift_Dialog.png"), full_page=True)
        print("  Screenshot  : %s" % os.path.join(VZ, "01_Gutschrift_Dialog.png"))

        print("\n--- 2. Dialog abbrechen (nichts ausfuehren) ---")
        abbruch = None
        for el in seite.query_selector_all(".modal-footer button, .modal-header button"):
            if el.is_visible() and el.inner_text().strip() in ("Verwerfen", "Abbrechen", "Discard", "Annullieren"):
                abbruch = el
                break
        if abbruch is None:
            seite.keyboard.press("Escape")
        else:
            abbruch.click()
        seite.wait_for_timeout(2500)
        offen_noch = seite.evaluate("""() => !!document.querySelector('.modal-dialog, .o_dialog')""")
        pruefe(not offen_noch, "Dialog ist geschlossen")

        js_fehler.extend(seite.evaluate("window.__errs") or [])
        pruefe(not js_fehler, "keine JavaScript-Fehler (%d)" % len(js_fehler))
        pruefe(not rpc_fehler, "keine RPC-Fehler (%d)" % len(rpc_fehler))
        if js_fehler:
            print("       JS: %s" % js_fehler[:3])
        if rpc_fehler:
            print("       RPC: %s" % rpc_fehler[:3])
        ctx.close()

    anzahl_nachher = kw("account.move", "search_count", [[]])
    print("\nBelege nach dem Test: %s" % anzahl_nachher)
    pruefe(anzahl_nachher == anzahl_vorher,
           "kein Beleg angelegt (%s vorher, %s nachher)" % (anzahl_vorher, anzahl_nachher))
    gutschriften = kw("account.move", "search_count", [[("move_type", "=", "out_refund")]])
    print("Gutschriften im Testbestand: %s" % gutschriften)
    print("\n%d OK / %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
