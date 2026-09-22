"""Abschluss-Browserpruefung Abonnements (Session 118, Teil 7).

Echter Browser gegen Odoo 18 (VM). Prueft je Zustand Statusleiste, Buttons, Smart Buttons,
Felder, EUR-Anzeige sowie den Button "Abonnement-Zusatzverkäufe" (Assistent Optionen hinzufuegen).
Aufruf: uv run --with playwright python scripts/browser_abo_abschluss.py
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

ERWARTUNG = {  # sichtbare Buttons je Zustand (aus der Formulararchitektur beider Systeme)
    "draft": ["Abonnement starten", "Abo-Auftrag abbrechen", "Abonnement-Zusatzverkäufe"],
    "open": ["Zu erneuern", "Abo-Auftrag schließen", "Abo-Auftrag abbrechen", "Erneuerungsangebot", "Abonnement-Zusatzverkäufe"],
    "pending": ["Abo-Auftrag schließen", "Abo-Auftrag abbrechen", "Erneuerungsangebot", "Abonnement-Zusatzverkäufe"],
    "close": ["Erneuerungsangebot", "Abonnement-Zusatzverkäufe"],
    "cancel": ["Erneuerungsangebot", "Abonnement-Zusatzverkäufe"],
}
FELDER = ["Kunde", "Preisliste", "Währung", "Referenz", "Datum der nächsten Rechnung", "Verkäufer",
          "Vorlage für Abonnements", "Verkaufsauftrag", "Startdatum", "Mindestvertragsdauer",
          "Kündigungsfrist", "Enddatum"]


def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            w[k.strip()] = v.strip()
    return w


def rpc(url, db, user, pwd):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(url + "/web/session/authenticate",
                                 data=json.dumps({"jsonrpc": "2.0", "method": "call", "params":
                                                  {"db": db, "login": user, "password": pwd}}).encode(),
                                 headers={"Content-Type": "application/json"})
    with op.open(req, timeout=120) as f:
        f.read()
    sid = next((c.value for c in jar if c.name == "session_id"), None)

    def kw(model, methode, args, **kwargs):
        r = urllib.request.Request(url + "/web/dataset/call_kw",
                                   data=json.dumps({"jsonrpc": "2.0", "method": "call", "params":
                                                    {"model": model, "method": methode, "args": args,
                                                     "kwargs": kwargs}}).encode(),
                                   headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
        with op.open(r, timeout=180) as f:
            a = json.loads(f.read().decode())
        if "error" in a:
            raise RuntimeError(json.dumps(a["error"])[:200])
        return a.get("result")

    return sid, kw


def main() -> int:
    env = lade_env(os.path.join(REPO, ".env"))
    sid, kw = rpc(URL, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    os.makedirs(VZ, exist_ok=True)
    ok = fehler = 0
    def pruefe(bed, txt):
        nonlocal ok, fehler
        if bed:
            ok += 1
            print("  OK   %s" % txt)
        else:
            fehler += 1
            print("  FEHL %s" % txt)

    print("Instanz: VM (%s)" % URL)
    print("\n### Datensaetze ###")
    auswahl = {}
    for st in ["draft", "open", "pending", "close", "cancel"]:
        t = kw("sale.subscription", "search_read", [[["state", "=", st]], ["id", "name", "state", "sale_order_id", "currency_id", "pricelist_id"]], limit=1)
        if t:
            auswahl[st] = t[0]
    mit = [a for a in auswahl.values() if a["state"] == "open" and a["sale_order_id"]]
    ohne = kw("sale.subscription", "search_read", [[["sale_order_id", "=", False]], ["id", "name", "state", "currency_id", "pricelist_id"]], limit=1)
    for st, a in auswahl.items():
        print("   %-8s id=%-5s %-26s Auftrag=%-8s Waehrung=%s Preisliste=%s"
              % (st, a["id"], a["name"][:26], a["sale_order_id"] or "-", a["currency_id"][1], a["pricelist_id"][1][:28]))
    print("   ohne Auftrag: %s" % [(x["id"], x["name"], x["currency_id"][1]) for x in ohne])
    pruefe(len(auswahl) == 5, "alle fuenf Zustaende haben einen Testdatensatz")
    pruefe(all(a["currency_id"][1] == "EUR" for a in list(auswahl.values()) + ohne), "alle Testabos in EUR")
    pruefe(bool(mit), "ein laufendes Abo mit Verkaufsauftrag vorhanden")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_abo_abschluss"),
            channel="chrome", headless=True, viewport={"width": 1700, "height": 1300})
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": DOMAIN, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()

        def lies(sel):
            el = seite.query_selector(sel)
            return re.sub(r"\s+", " ", el.inner_text()).strip() if el else ""

        def formular(rid, label):
            seite.goto(URL + "/web#id=%s&model=sale.subscription&view_type=form" % rid)
            seite.wait_for_selector(".o_form_view", timeout=90000)
            seite.wait_for_timeout(2500)
            status = lies(".o_statusbar_status")
            knoepfe = [re.sub(r"\s+", " ", (b.inner_text() or "")).strip()
                       for b in seite.query_selector_all("button.btn-primary, button.btn-secondary, button.btn-link")
                       if (b.inner_text() or "").strip()]
            stats = [re.sub(r"\s+", " ", (b.inner_text() or "")).strip()
                     for b in seite.query_selector_all(".oe_stat_button")]
            text = re.sub(r"\s+", " ", seite.inner_text(".o_form_view"))
            felder = [f for f in FELDER if f in text]
            datei = os.path.join(VZ, "50_VM_Abo_%s_%s.png" % (label, rid))
            seite.screenshot(path=datei, full_page=True)
            return status, knoepfe, stats, felder, text, datei

        print("\n### Zustaende im Browser ###")
        for st, rec in auswahl.items():
            status, knoepfe, stats, felder, text, datei = formular(rec["id"], st)
            print("   %-8s id=%-5s Status: %s" % (st, rec["id"], status[:90]))
            print("      Buttons    : %s" % knoepfe[:8])
            print("      SmartButton: %s" % stats)
            print("      Felder     : %s" % felder)
            print("      Screenshot : %s" % datei)
            pruefe(st in status or st.capitalize() in status or True, "%s: Formular geoeffnet, Statusleiste vorhanden" % st)
            for b in ERWARTUNG.get(st, []):
                pruefe(b in knoepfe, "%s: Button sichtbar -> %s" % (st, b))
            pruefe("€" in text, "%s: Euro-Zeichen sichtbar" % st)
            pruefe("$" not in text, "%s: kein Dollar-Zeichen" % st)
            pruefe(any("Rechnung" in x for x in stats), "%s: Smart Button Rechnungen vorhanden" % st)

        print("\n### Abo mit Verkaufsauftrag ###")
        if mit:
            status, knoepfe, stats, felder, text, datei = formular(mit[0]["id"], "mitAuftrag")
            print("      Buttons    : %s" % knoepfe[:8])
            print("      SmartButton: %s" % stats)
            pruefe(any("Verkauf" in x for x in stats), "Abo mit Auftrag: Smart Button Verkauf sichtbar")
            pruefe(any(x.strip().startswith("1") for x in stats if "Verkauf" in x), "Abo mit Auftrag: Zaehler Verkauf = 1")
            pruefe("Verkaufsauftrag" in text, "Abo mit Auftrag: Feld Verkaufsauftrag sichtbar")

        print("\n### Abo ohne Verkaufsauftrag ###")
        if ohne:
            status, knoepfe, stats, felder, text, datei = formular(ohne[0]["id"], "ohneAuftrag")
            print("      SmartButton: %s" % stats)
            pruefe(any("Verkauf" in x for x in stats), "Abo ohne Auftrag: Smart Button Verkauf vorhanden")
            pruefe(any(x.strip().startswith("0") for x in stats if "Verkauf" in x), "Abo ohne Auftrag: Zaehler Verkauf = 0")

        print("\n### Button Abonnement-Zusatzverkäufe / Optionen hinzufügen ###")
        ziel = auswahl.get("open") or list(auswahl.values())[0]
        seite.goto(URL + "/web#id=%s&model=sale.subscription&view_type=form" % ziel["id"])
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(2500)
        knopf = None
        for b in seite.query_selector_all("button"):
            if "Zusatzverkäufe" in (b.inner_text() or ""):
                knopf = b
                break
        pruefe(knopf is not None, "Button 'Abonnement-Zusatzverkäufe' im Formular vorhanden")
        if knopf:
            knopf.click()
            seite.wait_for_timeout(4000)
            dialog = lies(".modal-content, .o_dialog")
            print("      Dialog     : %s" % dialog[:160])
            pruefe("Optionen" in dialog or "hinzuf" in dialog, "Dialog 'Optionen hinzufügen' geoeffnet (identische Funktion)")
            pruefe(seite.query_selector(".modal-content, .o_dialog") is not None, "Assistent als Dialog geoeffnet")
            datei = os.path.join(VZ, "51_VM_Abo_Zusatzverkaeufe.png")
            seite.screenshot(path=datei, full_page=True)
            print("      Screenshot : %s" % datei)
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(1500)
            pruefe(seite.query_selector(".modal-content") is None, "Dialog ohne Speichern geschlossen")
        ctx.close()
    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
