"""Browser-Pruefung Abonnements: Zustaende, Buttons, Smart Buttons (Session 118, Teil 3).

Vergleicht das Abo-Formular im echten Browser. --instanz o11 liest Odoo 11 Prod
ausschliesslich lesend (nur Ansichten oeffnen), --instanz vm die Odoo-18-VM.

Aufruf:
    python scripts/browser_abo_pruef.py --instanz vm
    python scripts/browser_abo_pruef.py --instanz o11
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Layoutvergleich-Session95")


def lade_env(pfad):
    werte = {}
    for zeile in open(pfad, encoding="utf-8"):
        if "=" in zeile and not zeile.strip().startswith("#"):
            s, w = zeile.split("=", 1)
            werte[s.strip()] = w.strip()
    return werte


def rpc(url, db, user, pwd):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(url + "/web/session/authenticate",
                                 data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                  "params": {"db": db, "login": user, "password": pwd}}).encode(),
                                 headers={"Content-Type": "application/json"})
    with op.open(req, timeout=120) as f:
        f.read()
    sid = next((c.value for c in jar if c.name == "session_id"), None)

    def kw(model, methode, args, **kwargs):
        req = urllib.request.Request(url + "/web/dataset/call_kw",
                                     data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                      "params": {"model": model, "method": methode,
                                                                 "args": args, "kwargs": kwargs}}).encode(),
                                     headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
        with op.open(req, timeout=180) as f:
            antwort = json.loads(f.read().decode())
        if "error" in antwort:
            raise RuntimeError(json.dumps(antwort["error"])[:200])
        return antwort.get("result")

    return sid, kw


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "o11"], default="vm")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    if a.instanz == "vm":
        url, domain, db, user, pwd = "https://k001959vsx.ipax.at", "k001959vsx.ipax.at", env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"]
    else:
        url, domain, db, user, pwd = "https://portal.it-kommunal.at", "portal.it-kommunal.at", "ITK_V1_a", "anna.maierhofer@it-kommunal.at", "anma120126!"
    sid, kw = rpc(url, db, user, pwd)
    print("Instanz: %s (%s) - %s" % (a.instanz, url, "nur lesend" if a.instanz == "o11" else "Abnahme"))
    os.makedirs(VZ, exist_ok=True)

    # je Zustand einen Datensatz waehlen; zusaetzlich ein Abo ohne Verkaufsauftrag
    auswahl = {}
    for st in ["draft", "open", "pending", "close", "cancel"]:
        t = kw("sale.subscription", "search_read", [[["state", "=", st]], ["id", "name", "sale_order_id"]], limit=1)
        if t:
            auswahl[st] = t[0]
    ohne = kw("sale.subscription", "search_read", [[["sale_order_id", "=", False]], ["id", "name", "state"]], limit=1)
    print("Gefundene Zustaende:", {k: (v["id"], v["name"]) for k, v in auswahl.items()},
          "| ohne Auftrag:", [(x["id"], x["name"], x["state"]) for x in ohne])

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_abo_" + a.instanz),
            channel="chrome", headless=True, viewport={"width": 1700, "height": 1300})
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()

        def formular(sid_rec, label):
            seite.goto(url + "/web#id=%s&model=sale.subscription&view_type=form" % sid_rec)
            seite.wait_for_selector(".o_form_view", timeout=90000)
            seite.wait_for_timeout(2500)
            sichtbar = seite.query_selector(".o_statusbar_status")
            status = re.sub(r"\s+", " ", sichtbar.inner_text()).strip() if sichtbar else "-"
            knoepfe = [re.sub(r"\s+", " ", (b.inner_text() or "")).strip()
                       for b in seite.query_selector_all("button.btn-primary, button.btn-secondary, button.btn-link")
                       if (b.inner_text() or "").strip()]
            stats = [(re.sub(r"\s+", " ", (b.inner_text() or "")).strip())
                     for b in seite.query_selector_all(".oe_stat_button")]
            text = re.sub(r"\s+", " ", seite.inner_text(".o_form_view"))
            felder = [f for f in ["Kunde", "Preisliste", "Vorlage", "Verkaufsauftrag", "Startdatum",
                                  "Datum der nächsten Rechnung", "Enddatum", "Grund für die Beendigung",
                                  "Verkäufer", "Wiederkehrender Preis", "Kündigungsfrist", "Mindestvertragsdauer"]
                      if f in text]
            print("   %-12s id=%-5s Status: %s" % (label, sid_rec, status[:80]))
            print("      Buttons   : %s" % knoepfe[:8])
            print("      SmartButt : %s" % stats)
            print("      Felder    : %s" % felder)
            datei = os.path.join(VZ, "48_%s_Abo_%s_%s.png" % (a.instanz.upper(), label, sid_rec))
            seite.screenshot(path=datei, full_page=True)
            print("      Screenshot: %s" % datei)

        print("\n### Zustaende ###")
        for st, rec in auswahl.items():
            formular(rec["id"], st)
        if ohne:
            print("\n### Abo ohne Verkaufsauftrag ###")
            formular(ohne[0]["id"], "ohneAuftrag")
        ctx.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
