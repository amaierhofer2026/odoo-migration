"""Browser-Pruefung der Reiterbeschriftung im Abo-Formular (Session 118, Teil 13).

Oeffnet das Abo-Formular auf zwei Wegen im echten Browser und prueft, dass der erste Reiter
"Wiederkehrende Buchungen" heisst:
  Weg 1: normales Abonnement (Menue Abonnements -> Abonnements)
  Weg 2: Zu erneuernde Abonnements (eigener Menuepunkt)

Aufruf: uv run --with playwright python scripts/browser_abo_reiter.py
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
SOLL = "Wiederkehrende Buchungen"


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
            raise RuntimeError(str(a["error"].get("data", {}).get("message"))[:200])
        return a.get("result")

    return sid, kw


def main() -> int:
    sid, kw = rpc()
    ok = fehler = 0

    def pruefe(bed, txt):
        nonlocal ok, fehler
        if bed:
            ok += 1
            print("  OK   %s" % txt)
        else:
            fehler += 1
            print("  FEHL %s" % txt)

    # Menuepunkt "Zu erneuernde Abonnements" -> Aktion
    menus = kw("ir.ui.menu", "search_read", [[["name", "ilike", "erneuernde"]], ["id", "name", "action"]], context={"lang": "de_DE"})
    print("Menuepunkt gefunden: %s" % menus)
    referenz = menus[0]["action"] if menus and menus[0]["action"] else False
    aktion = int(str(referenz).split(",")[-1]) if referenz else False
    print("Aktion des Menuepunkts: %s" % aktion)
    ziel_pending = kw("sale.subscription", "search_read", [[["state", "=", "pending"]], ["id", "code"]], limit=1)
    ziel_normal = kw("sale.subscription", "search_read", [[["state", "=", "open"]], ["id", "code"]], limit=1)
    if not ziel_pending:
        ziel_pending = ziel_normal
    print("Testabos: normal %s | zu erneuern %s" % (ziel_normal, ziel_pending))

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_abo_reiter"),
            channel="chrome", headless=True, viewport={"width": 1700, "height": 1300})
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": DOMAIN, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()

        def reiter(bezeichnung, adresse, datei):
            print("\n--- %s ---" % bezeichnung)
            print("    Adresse: %s" % adresse)
            seite.goto(adresse)
            seite.wait_for_selector(".o_form_view", timeout=90000)
            seite.wait_for_timeout(3000)
            reiter_texte = [re.sub(r"\s+", " ", (a.inner_text() or "")).strip()
                            for a in seite.query_selector_all(".o_notebook .nav-link, .o_notebook a.nav-link")]
            print("    sichtbare Reiter: %s" % reiter_texte)
            pruefe(SOLL in reiter_texte, "%s: Reiter '%s' sichtbar" % (bezeichnung, SOLL))
            pruefe("Abonnement-Einträge" not in reiter_texte, "%s: alter Reitername nicht mehr sichtbar" % bezeichnung)
            seite.screenshot(path=os.path.join(VZ, datei), full_page=True)
            print("    Screenshot: %s" % os.path.join(VZ, datei))

        if ziel_normal:
            reiter("Weg 1: normales Abonnement", URL + "/web#id=%s&model=sale.subscription&view_type=form" % ziel_normal[0]["id"],
                   "54_VM_Abo_Reiter_normales_Abo.png")
        # Weg 2 ueber den Menuepunkt "Zu erneuernde Abonnements"
        adresse2 = (URL + "/odoo/action-%s" % aktion) if aktion else (URL + "/odoo/subscriptions")
        seite.goto(adresse2)
        seite.wait_for_timeout(6000)
        zeile = None
        for z in seite.query_selector_all("tr.o_data_row td.o_data_cell, tr.o_data_row a"):
            if (z.inner_text() or "").strip():
                zeile = z
                break
        if zeile:
            zeile.click()
            seite.wait_for_timeout(6000)
            reiter_texte = [re.sub(r"\s+", " ", (a.inner_text() or "")).strip()
                            for a in seite.query_selector_all(".o_notebook .nav-link, .o_notebook a.nav-link")]
            print("    Reiter: %s" % reiter_texte)
            pruefe(SOLL in reiter_texte, "Weg 2: Reiter '%s' sichtbar" % SOLL)
            seite.screenshot(path=os.path.join(VZ, "55_VM_Abo_Reiter_Zu_erneuern.png"), full_page=True)
            print("    Screenshot: %s" % os.path.join(VZ, "55_VM_Abo_Reiter_Zu_erneuern.png"))
        else:
            print("    Fallback: Formular des Abos aus der Zu-erneuern-Liste direkt oeffnen")
            reiter("Weg 2: Zu erneuernde Abonnements (Datensatz %s)" % ziel_pending[0]["id"],
                   URL + "/web#id=%s&model=sale.subscription&view_type=form" % ziel_pending[0]["id"],
                   "55_VM_Abo_Reiter_Zu_erneuern.png")
        ctx.close()
    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
