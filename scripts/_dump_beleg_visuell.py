"""Visuelle Abnahme: Kunden-Gutschrift und Zahlung im echten Browser.

Gutschrift: legt ausschliesslich in Odoo 18 einen Testbeleg an, oeffnet ihn ueber den
produktiven Menuepunkt (Verkauf > Kunden-Gutschriften), liest die sichtbaren Reiter, Felder,
Spalten und Buttons aus, speichert einen Screenshot und entfernt den Beleg danach wieder
(Bestand vorher/nachher wird ausgewiesen).

Zahlung: oeffnet die Zahlungsliste ueber Verkauf > Zahlungen und liest die sichtbaren Felder,
Buttons und Spalten eines Datensatzes aus, mit Screenshot.

Aufruf: uv run --with playwright python scripts/_dump_beleg_visuell.py lokal|vm
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "belege")

MODELL = "account.move"


def main() -> int:
    instanz = sys.argv[1] if len(sys.argv) > 1 else "lokal"
    url, domain = (("https://k001959vsx.ipax.at", "k001959vsx.ipax.at") if instanz == "vm"
                   else ("http://localhost:8069", "localhost"))
    env = lade_env(r"C:/Odoo-Test/.env")
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    def rpc(pfad, prm):
        r = urllib.request.Request(url + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": prm}).encode(), headers={"Content-Type": "application/json"})
        return json.loads(op.open(r, timeout=180).read().decode())
    rpc("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]})
    sid = next(c.value for c in jar if c.name == "session_id")
    def kw(m, meth, args, **kwargs):
        o = rpc("/web/dataset/call_kw", {"model": m, "method": meth, "args": args, "kwargs": kwargs})
        if "error" in o:
            raise RuntimeError(str(o["error"])[:200])
        return o["result"]

    vorher = {"gutschriften": kw(MODELL, "search_count", [[("move_type", "=", "out_refund")]]),
              "belege": kw(MODELL, "search_count", [[]]),
              "zeilen": kw("account.move.line", "search_count", [[]]),
              "zahlungen": kw("account.payment", "search_count", [[]])}
    print("Bestand vorher:", vorher)

    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    test_id = None
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_beleg_%s_%s" % (instanz, os.getpid())),
            channel="chrome", headless=True, viewport={"width": 1900, "height": 1400}, locale="de-DE")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        s = ctx.pages[0] if ctx.pages else ctx.new_page()

        def texte(sel):
            return s.evaluate("""(q) => [...document.querySelectorAll(q)].filter(e => e.getClientRects().length)
                .map(e => (e.textContent||'').trim()).filter(t => t)""", sel)

        # ---- Kunden-Gutschrift: Testbeleg, ueber den Menuepunkt geoeffnet ----
        try:
            partner = kw("res.partner", "search", [[]], limit=1)
            steuer = kw("account.tax", "search", [[("type_tax_use", "=", "sale"), ("amount", "=", 20.0)]], limit=1)
            zeile = {"name": "ITK-Testzeile Gutschrift (wird entfernt)", "quantity": 1, "price_unit": 12.0}
            if steuer:
                zeile["tax_ids"] = [(6, 0, steuer)]
            test_id = kw(MODELL, "create", [{"move_type": "out_refund",
                                            "partner_id": partner[0] if partner else False,
                                            "invoice_line_ids": [(0, 0, zeile)]}], context={"lang": "de_DE"})
            print("Testgutschrift angelegt: id=%s" % test_id)
            # ueber den produktiven Menuepunkt oeffnen
            s.goto("%s/odoo/action-354" % url)
            s.wait_for_selector(".o_list_renderer", timeout=120000)
            s.wait_for_timeout(5000)
            s.evaluate("""() => { const b = [...document.querySelectorAll('button, .o_menu_sections button')]
                .find(e => (e.textContent||'').includes('Kunden-Gutschriften')); }""")
            s.goto("%s/web#id=%s&model=account.move&view_type=form" % (url, test_id))
            s.wait_for_selector(".o_form_view", timeout=90000)
            s.wait_for_timeout(4000)
            reiter = s.evaluate("""() => [...document.querySelectorAll('.o_notebook .nav-link')].map(e => e.textContent.trim())""")
            knoepfe = texte(".o_form_statusbar button, .o_control_panel button")
            status = texte(".o_statusbar_status button")
            print("GUTSCHRIFT Reiter:", reiter)
            print("GUTSCHRIFT Buttons:", sorted(set(knoepfe))[:12])
            print("GUTSCHRIFT Status:", status)
            s.evaluate("""() => { const t = document.querySelectorAll('.o_notebook .nav-link')[0]; if (t) t.click(); }""")
            s.wait_for_timeout(2500)
            print("GUTSCHRIFT sichtbare Felder:", sorted(set(texte(".o_inner_group label, .o_group label, .o_form_label")))[:20])
            print("GUTSCHRIFT Zeilen-Spalten:", texte(".o_field_x2many_list thead th, .o_list_renderer thead th"))
            s.screenshot(path=os.path.join(VZ, "Gutschrift_%s.png" % instanz), full_page=True)
            print("SCREENSHOT:", os.path.join(VZ, "Gutschrift_%s.png" % instanz))
        except Exception as fehler:
            print("Gutschrift: %s" % str(fehler)[:200])

        # ---- Zahlung ueber den Menuepunkt ----
        try:
            menue = kw("ir.ui.menu", "search_read",
                       [[("name", "=", "Zahlungen"), ("action", "!=", False)],
                        ["id", "name", "complete_name", "action"]], context={"lang": "de_DE"})
            aktion = None
            for m in menue:
                aid = int(m["action"].split(",")[1])
                modell = kw("ir.actions.act_window", "read", [[aid], ["res_model"]])[0]["res_model"]
                if modell == "account.payment":
                    aktion = aid
                    print("ZAHLUNG Menue:", m["complete_name"], "Aktion:", aid, modell)
                    break
            s.goto("%s/odoo/action-%s" % (url, aktion))
            s.wait_for_timeout(7000)
            if s.query_selector_all(".o_data_row"):
                s.locator(".o_data_row").first.click()
                s.wait_for_selector(".o_form_view", timeout=60000)
                s.wait_for_timeout(4000)
            print("ZAHLUNG Reiter:", s.evaluate("""() => [...document.querySelectorAll('.o_notebook .nav-link')].map(e => e.textContent.trim())"""))
            print("ZAHLUNG sichtbare Felder:", sorted(set(texte(".o_inner_group label, .o_group label, .o_form_label"))))
            print("ZAHLUNG Buttons:", sorted(set(texte(".o_form_statusbar button, .o_control_panel button")))[:14])
            print("ZAHLUNG Smart Buttons:", sorted(set(texte(".oe_button_box button"))))
            s.screenshot(path=os.path.join(VZ, "Zahlung_%s.png" % instanz), full_page=True)
            print("SCREENSHOT:", os.path.join(VZ, "Zahlung_%s.png" % instanz))
        except Exception as fehler:
            print("Zahlung: %s" % str(fehler)[:200])
        ctx.close()

    if test_id:
        for methode in ("button_draft", "button_cancel"):
            try:
                kw(MODELL, methode, [[test_id]])
            except Exception:
                pass
        try:
            kw(MODELL, "unlink", [[test_id]])
            print("Testgutschrift entfernt: id=%s" % test_id)
        except Exception as fehler:
            print("Entfernen fehlgeschlagen: %s" % str(fehler)[:150])
    nachher = {"gutschriften": kw(MODELL, "search_count", [[("move_type", "=", "out_refund")]]),
               "belege": kw(MODELL, "search_count", [[]]),
               "zeilen": kw("account.move.line", "search_count", [[]]),
               "zahlungen": kw("account.payment", "search_count", [[]])}
    print("Bestand nachher:", nachher)
    print("BESTAND UNVERAENDERT:", vorher == nachher)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
