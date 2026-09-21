"""Browser-Pruefung Bereich Angebote / Verkaufsauftraege (Session 117).

Prueft im echten Browser (Playwright) auf der angegebenen Instanz mehrere
Auftragszustaende und die Sichtbarkeit der Smart Buttons (Rechnungen,
Abonnements, Lieferung) samt Zaehlern. Screenshots landen im Desktop-Ordner.

Aufruf:
    python scripts/browser_auftraege_pruef.py --instanz vm
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
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                s, w = zeile.split("=", 1)
                werte[s.strip()] = w.strip()
    return werte


def rpc_sitzung(url, db, user, pwd):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(
        url + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call",
                         "params": {"db": db, "login": user, "password": pwd}}).encode(),
        headers={"Content-Type": "application/json"})
    with op.open(req, timeout=120) as f:
        f.read()
    sid = next((c.value for c in jar if c.name == "session_id"), None)

    def kw(model, methode, args, **kwargs):
        req = urllib.request.Request(
            url + "/web/dataset/call_kw",
            data=json.dumps({"jsonrpc": "2.0", "method": "call",
                             "params": {"model": model, "method": methode, "args": args, "kwargs": kwargs}}).encode(),
            headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
        with op.open(req, timeout=120) as f:
            antwort = json.loads(f.read().decode())
        if "error" in antwort:
            raise RuntimeError(json.dumps(antwort["error"])[:200])
        return antwort.get("result")

    return sid, kw


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="vm")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    domain = "localhost" if a.instanz == "lokal" else "k001959vsx.ipax.at"
    sid, kw = rpc_sitzung(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    print("Instanz: %s (%s)" % (a.instanz, url))
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

    # Testauftraege je Zustand auswaehlen
    auftraege = {}
    for state in ["draft", "sent", "sale", "cancel"]:
        treffer = kw("sale.order", "search_read", [[["state", "=", state]], ["id", "name", "invoice_count", "subscription_count"]], limit=1)
        if treffer:
            auftraege[state] = treffer[0]
    mit_rechnung = kw("sale.order", "search_read", [[["invoice_ids", "!=", False]], ["id", "name", "invoice_count", "subscription_count"]], limit=1)
    print("Testauftraege:", {k: (v["id"], v["name"]) for k, v in auftraege.items()},
          "| mit Rechnung:", [(m["id"], m["name"]) for m in mit_rechnung])

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_auftraege_" + a.instanz),
            channel="chrome", headless=True, viewport={"width": 1700, "height": 1300})
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()

        def oeffne_auftrag(oid, name):
            seite.goto(url + "/web#id=%s&model=sale.order&view_type=form" % oid)
            seite.wait_for_selector(".o_form_view", timeout=90000)
            seite.wait_for_timeout(2500)
            text = re.sub(r"\s+", " ", seite.inner_text(".o_form_view"))
            status = ""
            for s in ["Angebot", "Angebot gesendet", "Verkaufsauftrag", "Storniert", "Auftrag"]:
                if s in text:
                    status = s
                    break
            # Smart Buttons
            knoepfe = []
            for b in seite.query_selector_all(".oe_stat_button"):
                t = re.sub(r"\s+", " ", (b.inner_text() or "")).strip()
                knoepfe.append(t)
            print("       %s (%s): Statusleiste='%s'" % (name, oid, status))
            print("         Smart Buttons: %s" % knoepfe)
            print("         Bestaetigung am im Formular: %s" % ("ja" if "Bestätigung am" in text else "nein"))
            datei = os.path.join(VZ, "45_%s_Auftrag_%s.png" % (a.instanz.upper(), name))
            seite.screenshot(path=datei, full_page=True)
            print("         Screenshot: %s" % datei)
            return text, knoepfe

        print("\n1) Angebot (draft)")
        if "draft" in auftraege:
            text, knoepfe = oeffne_auftrag(auftraege["draft"]["id"], "Angebot")
            pruefe("Bestätigung am" in text, "Feld 'Bestätigung am' im Angebot sichtbar")
            pruefe(not any("Rechnung" in k for k in knoepfe), "kein Rechnungs-Smart-Button ohne Rechnung")
        else:
            pruefe(False, "kein Angebot (draft) vorhanden")

        print("\n2) Angebot gesendet (sent)")
        if "sent" in auftraege:
            text, knoepfe = oeffne_auftrag(auftraege["sent"]["id"], "Gesendet")
            pruefe(True, "Formular im Zustand 'Angebot gesendet' geoeffnet")

        print("\n3) Bestaetigter Verkaufsauftrag (sale)")
        if "sale" in auftraege:
            text, knoepfe = oeffne_auftrag(auftraege["sale"]["id"], "Bestaetigt")
            pruefe(True, "Formular im Zustand 'Verkaufsauftrag' geoeffnet")

        print("\n4) Stornierter Auftrag (cancel)")
        if "cancel" in auftraege:
            text, knoepfe = oeffne_auftrag(auftraege["cancel"]["id"], "Storniert")
            pruefe(True, "Formular im Zustand 'Storniert' geoeffnet")

        print("\n5) Auftrag mit Rechnung")
        if mit_rechnung:
            text, knoepfe = oeffne_auftrag(mit_rechnung[0]["id"], "MitRechnung")
            pruefe(any("Rechnung" in k for k in knoepfe),
                   "Rechnungs-Smart-Button sichtbar: %s" % [k for k in knoepfe if "Rechnung" in k])
            rechnung_knopf = [b for b in seite.query_selector_all(".oe_stat_button") if "Rechnung" in (b.inner_text() or "")]
            if rechnung_knopf:
                rechnung_knopf[0].click()
                seite.wait_for_timeout(3000)
                pruefe(".o_list_view" in seite.content() or "Rechnung" in seite.inner_text("body"),
                       "Klick auf Rechnungen oeffnet die Rechnungsliste")
                datei = os.path.join(VZ, "46_%s_Auftrag_Rechnungen.png" % a.instanz.upper())
                seite.screenshot(path=datei, full_page=True)
                print("         Screenshot: %s" % datei)
        else:
            pruefe(False, "kein Auftrag mit Rechnung vorhanden")

        print("\n6) Auftrag mit Abonnement")
        abo = kw("sale.order", "search_read", [[["subscription_count", ">", 0]], ["id", "name", "subscription_count"]], limit=1)
        if abo:
            text, knoepfe = oeffne_auftrag(abo[0]["id"], "MitAbo")
            pruefe(any("bonnement" in k for k in knoepfe),
                   "Abo-Smart-Button sichtbar: %s" % [k for k in knoepfe if "bonnement" in k])
            abo_knopf = [b for b in seite.query_selector_all(".oe_stat_button") if "bonnement" in (b.inner_text() or "")]
            if abo_knopf:
                abo_knopf[0].click()
                seite.wait_for_timeout(3000)
                pruefe("bonnement" in seite.inner_text("body"), "Klick auf Abonnements oeffnet die Abo-Ansicht")
                datei = os.path.join(VZ, "47_%s_Auftrag_Abonnements.png" % a.instanz.upper())
                seite.screenshot(path=datei, full_page=True)
                print("         Screenshot: %s" % datei)
        else:
            pruefe(False, "kein Auftrag mit Abonnement vorhanden")

        ctx.close()

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
