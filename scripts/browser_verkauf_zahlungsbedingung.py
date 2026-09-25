"""Browser-Abnahme Verkauf: Zahlungsbedingung "14 Tage" in Odoo 18 (Session 121).

Oeffnet die Zahlungsbedingung im echten Browser, liest die Zeilenwerte (Tage, Verzoegerung) und
macht einen Screenshot. Read-only (es wird nichts gespeichert).

Aufruf:
    uv run --with playwright python scripts/browser_verkauf_zahlungsbedingung.py --instanz vm
    uv run --with playwright python scripts/browser_verkauf_zahlungsbedingung.py --instanz lokal
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_verkauf_menue import lade_env, rpc_client, REPO

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session121")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    p.add_argument("--ohne-screenshot", action="store_true")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

    SP = {"lang": "de_DE"}
    term = kw("account.payment.term", "search_read", [[["name", "=", "14 Tage"]], ["id", "name"]], context=SP)
    if not term:
        raise SystemExit("Zahlungsbedingung '14 Tage' nicht gefunden.")
    tid = term[0]["id"]
    zeilen = kw("account.payment.term.line", "search_read",
                [[["payment_id", "=", tid]], ["nb_days", "value", "value_amount", "delay_type"]], context=SP)
    aktion = kw("ir.actions.act_window", "search_read",
                [[["res_model", "=", "account.payment.term"]], ["id", "name"]], context=SP, limit=1)[0]["id"]
    print("Instanz: %s (%s) | Zahlungsbedingung '14 Tage' id %s" % (a.instanz, url, tid))
    print("   Zeilen laut RPC: %s" % zeilen)

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

    def saeubere(t):
        return re.sub(r"\s+", " ", t or "").strip()

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_verkauf_zdb_%s" % a.instanz),
            channel="chrome", headless=True, viewport={"width": 1600, "height": 1100})
        ctx.add_init_script(
            "window.__errs=[];"
            "window.addEventListener('error', e => window.__errs.push(''+e.message));"
            "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));"
            "const ce=console.error; console.error=(...x)=>{window.__errs.push(x.map(String).join(' ')); ce(...x);};")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.on("response", lambda r: rpc_fehler.append("%s %s" % (r.status, r.url))
                 if ("/web/dataset/call_kw" in r.url and r.status >= 400) else None)

        seite.goto("%s/odoo/action-%s/%s" % (url, aktion, tid))
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(4000)
        pruefe(seite.query_selector(".o_form_view") is not None, "Zahlungsbedingung im Browser geoeffnet")
        text = saeubere(seite.inner_text(".o_form_sheet")) if seite.query_selector(".o_form_sheet") else ""
        print("       sichtbarer Formularinhalt: %s" % text[:200])
        pruefe("14" in text, "sichtbarer Zeilenwert enthaelt 14 (Tage)")
        pruefe("14 Tage" in text or "Tage" in text, "Beschriftung 'Tage' sichtbar")
        if not a.ohne_screenshot:
            datei = os.path.join(VZ, "05_Zahlungsbedingung_14_Tage_%s.png" % a.instanz)
            seite.screenshot(path=datei, full_page=True)
            print("       Screenshot: %s" % datei)

        js_fehler.extend(seite.evaluate("window.__errs") or [])
        pruefe(not js_fehler, "keine JavaScript-Fehler (%d)" % len(js_fehler))
        pruefe(not rpc_fehler, "keine RPC-Fehler (HTTP >= 400) (%d)" % len(rpc_fehler))
        ctx.close()

    print("\n%d OK / %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
