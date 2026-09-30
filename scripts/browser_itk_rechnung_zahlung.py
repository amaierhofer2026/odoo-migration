"""Browser-Test (VM): Bericht "ITK-Rechnung mit Zahlung" im echten Browser.

Oeffnet die Rechnungsliste, liest das Drucken-Menue aus, waehlt "ITK-Rechnung mit Zahlung" und
prueft, dass ein PDF erzeugt wird. Es wird nichts gespeichert.
"""
from __future__ import annotations
import argparse, http.cookiejar, json, os, urllib.request
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session122", "teil6")

def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1); w[k.strip()] = v.strip().strip('"')
    return w

def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    jar = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    def rufe(pfad, prm):
        req = urllib.request.Request(url + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": prm}).encode(), headers={"Content-Type": "application/json"})
        with op.open(req, timeout=180) as f: return json.loads(f.read().decode())
    rufe("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]})
    sid = next(c.value for c in jar if c.name == "session_id")
    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    ok = fehler = 0
    def pruefe(b, t):
        nonlocal ok, fehler
        if b: ok += 1; print("  OK   %s" % t)
        else: fehler += 1; print("  FEHL %s" % t)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_itk_rep_%s_%s" % (a.instanz, os.getpid())),
            channel="chrome", headless=True, viewport={"width": 1800, "height": 1300}, accept_downloads=True)
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        s = ctx.pages[0] if ctx.pages else ctx.new_page()
        s.goto("%s/odoo/action-354" % url); s.wait_for_selector(".o_list_view, .o_list_renderer", timeout=90000); s.wait_for_timeout(5000)
        kb = s.query_selector(".o_list_view thead input[type=checkbox], .o_list_renderer thead input[type=checkbox]")
        if kb: kb.click(); s.wait_for_timeout(2500)
        knopf = None
        for el in s.query_selector_all("button"):
            if el.is_visible() and (el.inner_text() or "").strip().startswith("Herunterladen"):
                knopf = el; break
        pruefe(knopf is not None, "Menue 'Herunterladen' gefunden")
        if knopf:
            knopf.click(); s.wait_for_timeout(2500)
            eintraege = s.evaluate("""() => [...document.querySelectorAll('.o-dropdown--menu .dropdown-item, .dropdown-menu .dropdown-item')]
                .filter(e => e.getClientRects().length).map(e => e.innerText.trim())""")
            print("    Berichte: %s" % eintraege)
            pruefe(any("ITK-Rechnung mit Zahlung" in e for e in eintraege), "Bericht 'ITK-Rechnung mit Zahlung' im Menue")
            ziel = None
            for el in s.query_selector_all(".dropdown-item"):
                if el.is_visible() and "ITK-Rechnung mit Zahlung" in (el.inner_text() or ""):
                    ziel = el; break
            pruefe(ziel is not None, "Bericht anklickbar")
            if ziel:
                try:
                    with s.expect_download(timeout=45000) as dl:
                        ziel.click()
                    datei = dl.value
                    print("    Download: %s" % datei.suggested_filename)
                    pruefe(datei.suggested_filename.lower().endswith(".pdf"), "PDF erzeugt (%s)" % datei.suggested_filename)
                except Exception as e:
                    pruefe(False, "PDF-Download (%s)" % str(e)[:80])
            s.screenshot(path=os.path.join(VZ, "01_Drucken_Menue.png"), full_page=True)
        ctx.close()
    print("\n%d OK / %d FEHL" % (ok, fehler))
    return 1 if fehler else 0

if __name__ == "__main__":
    raise SystemExit(main())
