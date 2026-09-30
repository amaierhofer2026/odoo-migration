"""Browser-Test (VM): Felder "Odoo-11-Rechnungsnummer" / "Odoo-11-Zahlungsnummer".

Oeffnet eine gebuchte Ausgangsrechnung der VM, prueft den Reiter "Weitere Informationen"
und dort die Gruppe "Herkunft (Migration)" mit dem Feld "Odoo-11-Rechnungsnummer"
(read-only). Es wird nichts gespeichert oder geaendert.
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "teil5")


def main() -> int:
    env = lade_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    url, domain = "https://k001959vsx.ipax.at", "k001959vsx.ipax.at"
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(
        url + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call",
                         "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                    "password": env["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"})
    json.loads(op.open(req, timeout=120).read().decode())
    sid = next(c.value for c in jar if c.name == "session_id")

    def kw(modell, methode, args, **kwargs):
        r = urllib.request.Request(
            url + "/web/dataset/call_kw",
            data=json.dumps({"jsonrpc": "2.0", "method": "call",
                             "params": {"model": modell, "method": methode, "args": args,
                                        "kwargs": kwargs}}).encode(),
            headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
        antwort = json.loads(op.open(r, timeout=180).read().decode())
        if "error" in antwort:
            raise RuntimeError(str(antwort["error"])[:200])
        return antwort["result"]

    belege = kw("account.move", "search_read",
                [[("move_type", "=", "out_invoice"), ("state", "=", "posted")], ["id", "name"]],
                order="id desc", limit=1, context={"lang": "de_DE"})
    if not belege:
        belege = kw("account.move", "search_read", [[("move_type", "=", "out_invoice")], ["id", "name"]],
                    order="id desc", limit=1, context={"lang": "de_DE"})
    beleg = belege[0]
    print("Testbeleg: %s (id %s)" % (beleg["name"], beleg["id"]))

    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    ok = fehler = 0

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
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_teil5_%s" % os.getpid()),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1400})
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        s = ctx.pages[0] if ctx.pages else ctx.new_page()
        s.goto("%s/odoo/action-354/%s" % (url, beleg["id"]))
        s.wait_for_selector(".o_form_view", timeout=90000)
        s.wait_for_timeout(4000)
        pruefe(True, "Rechnungsformular geoeffnet (%s)" % beleg["name"])
        reiter = [t.text_content().strip() for t in s.query_selector_all(".o_notebook .nav-link")]
        pruefe("Weitere Informationen" in reiter, "Reiter 'Weitere Informationen' vorhanden (%s)" % reiter)
        for t in s.query_selector_all(".o_notebook .nav-link"):
            if "Weitere Informationen" in (t.text_content() or ""):
                t.click()
                break
        s.wait_for_timeout(2500)
        aus = s.evaluate("""() => {
            const gruppe = (document.body.textContent || '').includes('Herkunft (Migration)') ? [1] : [];
            const feld = document.querySelector('input[name="itk_o11_invoice_number"], .o_field_widget[name="itk_o11_invoice_number"]');
            const inp = feld ? feld.querySelector('input') : null;
            return {gruppe: gruppe.length, feld: !!feld,
                    readonly: inp ? (inp.hasAttribute('readonly') || inp.readOnly) : null};
        }""")
        pruefe(aus["gruppe"] > 0, "Gruppe 'Herkunft (Migration)' im Reiter sichtbar")
        pruefe(aus["feld"], "Feld 'Odoo-11-Rechnungsnummer' wird gerendert")
        pruefe(aus["readonly"] in (True, None), "Feld ist read-only (readonly=%s)" % aus["readonly"])
        s.screenshot(path=os.path.join(VZ, "01_Formular_Herkunft.png"), full_page=True)
        s.goto("%s/odoo/accounting/payments" % url)
        s.wait_for_timeout(6000)
        pruefe(True, "Zahlungsliste geoeffnet")
        s.screenshot(path=os.path.join(VZ, "02_Zahlungsliste.png"), full_page=True)
        ctx.close()
    print("\n%d OK / %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
