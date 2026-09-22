"""Browser-Klick-Test des manuellen Rechnungsbuttons auf der VM (Session 118, Teil 12).

Oeffnet ein Abo im echten Browser, klickt den Rechnungs-Button "Rechnung manuell erstellen"
(direkt oder ueber das Aktionsmenue) und prueft: kein RPC-/Serverfehler, genau eine neue Rechnung.

Aufruf: uv run --with playwright python scripts/browser_abo_manuell_klick.py
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Layoutvergleich-Session95")
URL, DOMAIN = "https://k001959vsx.ipax.at", "k001959vsx.ipax.at"
NAME = "TEST Rechnungslauf Nachweis"


def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            w[k.strip()] = v.strip()
    return w


def rpc():
    env = lade_env(os.path.join(REPO, ".env"))
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(URL + "/web/session/authenticate",
                                 data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
                                     "db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                     "password": env["ODOO18_PWD"]}}).encode(),
                                 headers={"Content-Type": "application/json"})
    with op.open(req, timeout=120) as f:
        f.read()
    sid = next((c.value for c in jar if c.name == "session_id"), None)

    def kw(modell, methode, args, **kwargs):
        r = urllib.request.Request(URL + "/web/dataset/call_kw",
                                   data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
                                       "model": modell, "method": methode, "args": args,
                                       "kwargs": kwargs}}).encode(),
                                   headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
        with op.open(r, timeout=300) as f:
            a = json.loads(f.read().decode())
        if "error" in a:
            d = a["error"].get("data", {})
            raise RuntimeError((d.get("name", "") + ": " + d.get("message", ""))[:200])
        return a.get("result")

    return sid, kw


def main() -> int:
    sid, kw = rpc()
    abo = kw("sale.subscription", "search_read", [[["name", "=", NAME]], ["id", "code", "invoice_count", "partner_id"]])[0]
    print("Abo %s (%s) | Rechnungen vorher: %s" % (abo["id"], abo["code"], abo["invoice_count"]))
    ok = fehler = 0

    def pruefe(bed, txt):
        nonlocal ok, fehler
        if bed:
            ok += 1
            print("  OK   %s" % txt)
        else:
            fehler += 1
            print("  FEHL %s" % txt)

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_abo_manuell"),
            channel="chrome", headless=True, viewport={"width": 1700, "height": 1300})
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": DOMAIN, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.goto(URL + "/web#id=%s&model=sale.subscription&view_type=form" % abo["id"])
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(3000)
        print("   sichtbare Buttons: %s" % [re.sub(r"\s+", " ", (b.inner_text() or "")).strip()
                                            for b in seite.query_selector_all("button.btn-primary, button.btn-secondary, button.btn-link")
                                            if (b.inner_text() or "").strip()][:9])

        knopf = None
        for b in seite.query_selector_all("button, .dropdown-item, a"):
            if "Rechnung manuell" in (b.inner_text() or ""):
                knopf = b
                break
        if not knopf:
            print("   Button nicht direkt sichtbar - Aktionsmenue oeffnen")
            for b in seite.query_selector_all("button"):
                if (b.inner_text() or "").strip() in ("...", "Aktion", "Aktionen"):
                    b.click()
                    seite.wait_for_timeout(2000)
                    break
            for b in seite.query_selector_all(".dropdown-item, .o_menu_item, a, button"):
                if "Rechnung manuell" in (b.inner_text() or ""):
                    knopf = b
                    break
        pruefe(knopf is not None, "Eintrag 'Rechnung manuell erstellen' im Browser gefunden")
        if not knopf:
            seite.screenshot(path=os.path.join(VZ, "53_VM_Abo_Rechnung_manuell_NICHT_GEFUNDEN.png"), full_page=True)
            ctx.close()
            print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
            return 1

        knopf.click()
        seite.wait_for_timeout(10000)
        text = re.sub(r"\s+", " ", seite.inner_text("body"))
        datei = os.path.join(VZ, "53_VM_Abo_Rechnung_manuell.png")
        seite.screenshot(path=datei, full_page=True)
        print("   Screenshot: %s" % datei)
        pruefe("RPC_ERROR" not in text and "Traceback" not in text and "ProgrammingError" not in text
               and "error" not in text.lower()[:400], "kein RPC-/Serverfehler nach dem Klick")
        pruefe("Rechnung" in text or "Entwurf" in text or "Rechnung manuell" in text,
               "Browser zeigt nach dem Klick eine Rechnungsansicht")
        ctx.close()

    danach = kw("sale.subscription", "read", [[abo["id"]], ["invoice_count"]])[0]["invoice_count"]
    print("   Rechnungen nachher: %s" % danach)
    pruefe(danach == abo["invoice_count"] + 1,
           "genau eine neue Rechnung durch den Klick (%s -> %s)" % (abo["invoice_count"], danach))
    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
