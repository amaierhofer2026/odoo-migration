"""B3 Zahlung: echter Browser-Test auf der VM (Zahlung registrieren, Testdaten).

Ablauf: offene Testrechnung oeffnen, Knopf "Zahlen" klicken, Dialogfelder auslesen, Zahlung
bestaetigen, Ergebnis pruefen. Es entstehen Testdaten in der Testdatenbank (eine Zahlung),
keine Migration, keine Produktivdaten.

Aufruf:  uv run --with playwright python scripts/browser_b3_zahlung.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "b3")


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
    p.add_argument("--rechnung", type=int, default=0)
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

    if a.rechnung:
        offen = kw("account.move", "search_read",
                   [[("id", "=", a.rechnung)], ["id", "name", "amount_total", "partner_id", "state"]],
                   order="id", limit=1)
    else:
        offen = kw("account.move", "search_read",
                   [[("move_type", "=", "out_invoice"), ("state", "=", "posted"),
                     ("payment_state", "!=", "paid")], ["id", "name", "amount_total", "partner_id"]],
                   order="id", limit=1)
    if not offen:
        print("Keine offene gebuchte Ausgangsrechnung auf %s gefunden." % a.instanz)
        return 1
    r = offen[0]
    zahlungen_vorher = kw("account.payment", "search_count", [[]])
    print("Instanz  : %s" % url)
    print("Rechnung : id %s | %s | %s | %s" % (r["id"], r["name"], r["partner_id"][1], r["amount_total"]))
    print("Zahlungen vorher: %s" % zahlungen_vorher)

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
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"),
                                       "pw_b3_%s_%s" % (a.instanz, os.getpid())),
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

        if kw("account.move", "read", [[r["id"]], ["state"]])[0]["state"] == "draft":
            print("\n--- 0. Entwurf buchen ---")
            buchen = None
            for el in seite.query_selector_all("button"):
                if el.is_visible() and el.inner_text().strip() in ("Bestaetigen", "Bestätigen", "Buchen"):
                    buchen = el
                    break
            pruefe(buchen is not None, "Knopf zum Buchen vorhanden")
            if buchen is not None:
                print("  Knopf       : %s" % buchen.inner_text().strip())
                buchen.click()
                seite.wait_for_timeout(6000)
            pruefe(kw("account.move", "read", [[r["id"]], ["state"]])[0]["state"] == "posted",
                   "Rechnung ist gebucht")
            seite.reload()
            seite.wait_for_selector(".o_form_view", timeout=60000)
            seite.wait_for_timeout(3000)

        print("\n--- 1. Rechnung und Knopf 'Zahlen' ---")
        buttons = sichtbar(".o_statusbar_buttons button, .o_form_statusbar button.btn")
        print("  Kopf-Buttons: %s" % buttons)
        pruefe(any("Zahlen" in b for b in buttons), "Knopf 'Zahlen' sichtbar")
        knopf = None
        for el in seite.query_selector_all("button"):
            if el.is_visible() and el.inner_text().strip() == "Zahlen":
                knopf = el
                break
        pruefe(knopf is not None, "Knopf 'Zahlen' gefunden")

        print("\n--- 2. Dialog der Zahlung ---")
        knopf.click()
        try:
            seite.wait_for_function(
                "() => !!document.querySelector('.o_dialog .o_field_widget[name=\"amount\"]')",
                timeout=60000)
        except Exception as f:
            print("  Hinweis: Dialog nicht erkannt (%s)" % str(f)[:70])
        seite.wait_for_timeout(2500)
        titel = sichtbar(".o_dialog .modal-title, .o_dialog .o_dialog_title")
        felder = seite.evaluate("""() => [...document.querySelectorAll('.o_dialog .o_field_widget')]
            .filter(e => e.getClientRects().length)
            .map(e => ({name: e.getAttribute('name'),
                        wert: (e.querySelector('input, select, textarea') || {value: ''}).value || e.innerText.trim()}))""")
        dialog_buttons = sichtbar(".o_dialog .modal-footer button, .o_dialog footer button")
        print("  Titel       : %s" % titel)
        for f in felder:
            print("  Feld        : %-24s wert=%r" % (f["name"], (f["wert"] or "")[:40]))
        print("  Buttons     : %s" % dialog_buttons)
        pruefe(any(f["name"] == "journal_id" for f in felder), "Journal im Dialog")
        pruefe(any(f["name"] == "payment_method_line_id" for f in felder), "Zahlungsmethode im Dialog")
        pruefe(any(f["name"] == "amount" for f in felder), "Betrag im Dialog")
        pruefe(any(f["name"] == "communication" for f in felder), "Vermerk im Dialog")
        seite.screenshot(path=os.path.join(VZ, "01_Zahlung_Dialog.png"), full_page=True)
        print("  Screenshot  : %s" % os.path.join(VZ, "01_Zahlung_Dialog.png"))

        print("\n--- 3. Zahlung bestaetigen ---")
        primaer = None
        for el in seite.query_selector_all(".o_dialog .modal-footer button, .o_dialog footer button"):
            if el.is_visible() and "btn-primary" in (el.get_attribute("class") or ""):
                primaer = el
                break
        pruefe(primaer is not None, "Bestaetigungsknopf gefunden")
        if primaer is not None:
            print("  Knopf       : %s" % primaer.inner_text().strip())
            primaer.click()
            seite.wait_for_timeout(6000)
        offen_noch = seite.evaluate("() => !!document.querySelector('.o_dialog')")
        pruefe(not offen_noch, "Dialog ist geschlossen")
        zustand = seite.evaluate("""() => {
            const s = document.querySelector('.o_statusbar_status .o_arrow_button_current');
            const kopf = document.querySelector('.o_form_view .o_form_statusbar');
            const box = document.querySelector('.o_field_statinfo, .oe_button_box, .o_button_box');
            const zahl = document.querySelector('.o_payment_label');
            return {status: s ? s.innerText.trim() : '',
                    badge: (kopf ? kopf.innerText : '').replace(/\s+/g, ' ').trim(),
                    box: (box ? box.innerText : '').replace(/\s+/g, ' ').trim(),
                    zahlung: zahl ? zahl.innerText.replace(/\s+/g, ' ').trim() : ''};
        }""")
        print("  Anzeige     : Status=%s | Zahlungsanzeige=%s | Smart =%s"
              % (zustand["status"], zustand["zahlung"][:40], zustand["box"][:50]))
        pruefe("Bezahlt" in zustand["zahlung"], "Rechnung zeigt 'Bezahlt' (%s)" % zustand["zahlung"][:30])
        pruefe("Zahlungen" in zustand["box"], "Smart Button 'Zahlungen' sichtbar")
        seite.screenshot(path=os.path.join(VZ, "02_Zahlung_gebucht.png"), full_page=True)

        js_fehler.extend(seite.evaluate("window.__errs") or [])
        pruefe(not js_fehler, "keine JavaScript-Fehler (%d)" % len(js_fehler))
        pruefe(not rpc_fehler, "keine RPC-Fehler (%d)" % len(rpc_fehler))
        if js_fehler:
            print("       JS: %s" % js_fehler[:3])
        if rpc_fehler:
            print("       RPC: %s" % rpc_fehler[:3])
        ctx.close()

    print("\n--- 4. Gegenprobe ueber die Datenbank ---")
    zahlungen_nachher = kw("account.payment", "search_count", [[]])
    rechnung = kw("account.move", "read", [[r["id"]], ["name", "payment_state", "amount_residual"]])[0]
    print("  Zahlungen nachher: %s" % zahlungen_nachher)
    print("  Rechnung         : %s" % rechnung)
    pruefe(zahlungen_nachher == zahlungen_vorher + 1, "genau eine Zahlung entstanden")
    pruefe(rechnung["payment_state"] == "paid" and abs(rechnung["amount_residual"]) < 0.001,
           "Rechnung ist bezahlt (Rest 0)")
    for z in kw("account.payment", "search_read", [[("reconciled_invoice_ids", "in", [r["id"]])],
               ["name", "amount", "memo", "date", "state", "payment_method_line_id", "journal_id"]],
               order="id desc", limit=1):
        print("  Zahlung          : %s" % z)

    print("\n%d OK / %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
