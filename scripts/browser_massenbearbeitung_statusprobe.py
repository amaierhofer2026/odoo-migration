#!/usr/bin/env python3
"""Prueft, ob die Statusfelder im Massenbearbeitungs-Dialog bedienbar sind.

Oeffnet "Angebot zu Auftrag" (sale.order.state, in Odoo 18 readonly=True) und
"Abo-Status aendern" (sale.subscription.state), stellt die Auswahl auf "Setzen",
liest die sichtbaren Auswahlwerte und beendet den Dialog mit "Abbrechen".
Es wird nichts gespeichert.

Aufruf: uv run --with playwright python scripts/browser_massenbearbeitung_statusprobe.py --instanz lokal
"""
import argparse
import http.cookiejar
import json
import os
import ssl
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from _o11o18_client import lade_env  # noqa: E402


def sitzung(url, db, user, pwd):
    jar = http.cookiejar.CookieJar()
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar),
                                     urllib.request.HTTPSHandler(context=ctx))
    req = urllib.request.Request(
        url + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call",
                         "params": {"db": db, "login": user, "password": pwd}}).encode(),
        headers={"Content-Type": "application/json"})
    with op.open(req, timeout=120) as r:
        json.loads(r.read().decode())
    return next(c.value for c in jar if c.name == "session_id")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "mass_probe"))
    a = ap.parse_args()
    env = lade_env()
    url = (env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal"
           else "https://k001959vsx.ipax.at").rstrip("/")
    domain = url.split("//")[1].split(":")[0]
    os.makedirs(a.out, exist_ok=True)
    sid = sitzung(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        ctx = b.new_context(viewport={"width": 1500, "height": 1000})
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.new_page()

        def probe(pfad, aktion, name):
            seite.goto(url + pfad, wait_until="domcontentloaded", timeout=120000)
            seite.wait_for_selector(".o_list_view", timeout=120000)
            time.sleep(3)
            boxen = seite.query_selector_all(".o_list_view thead input[type=checkbox]")
            if boxen:
                boxen[0].click()
                time.sleep(1.5)
            for el in seite.query_selector_all(".o_control_panel button, .o_control_panel .dropdown-toggle"):
                if (el.inner_text() or "").strip().startswith("Aktion") and el.is_visible():
                    el.click()
                    break
            time.sleep(2)
            for el in seite.query_selector_all(".o-dropdown--menu .dropdown-item"):
                if el.is_visible() and el.inner_text().strip() == aktion:
                    el.click()
                    break
            else:
                print("  FEHLER: Aktion %r nicht gefunden" % aktion)
                return
            seite.wait_for_selector(".o_dialog .o_form_view", timeout=60000)
            time.sleep(2)
            d = seite.query_selector(".o_dialog")
            # Auswahl auf "Setzen" stellen
            sel = d.query_selector(".o_field_widget[name^='selection__'] input, .o_field_widget[name^='selection__']")
            if sel:
                try:
                    sel.click()
                    time.sleep(1.5)
                    # Tastatur: zweite Option ("Setzen") waehlen
                    seite.keyboard.press("ArrowDown")
                    time.sleep(0.5)
                    seite.keyboard.press("Enter")
                    time.sleep(1.5)
                    print("  Auswahl per Tastatur gesetzt")
                    # Wertfeld anklicken: oeffnet es eine Auswahlliste?
                    for cand in d.query_selector_all(".o_field_widget[name]"):
                        if (cand.get_attribute("name") or "") == "state":
                            cand.click()
                            break
                    time.sleep(1.5)
                    offen = seite.evaluate("""() => document.querySelectorAll('.dropdown-menu .dropdown-item, .o_select_menu_item').length""")
                    print("  Auswahlpunkte im geoeffneten Wertfeld:", offen)
                except Exception as exc:  # noqa: BLE001
                    print("  Auswahl nicht bedienbar:", str(exc)[:80])
            time.sleep(2)
            feld = None
            for cand in d.query_selector_all(".o_field_widget[name]"):
                nm = cand.get_attribute("name") or ""
                if not nm.startswith("selection__") and nm not in ("operation_description_info", "message",
                                                                   "selected_item_qty", "remaining_item_qty",
                                                                   "operation_description_warning",
                                                                   "operation_description_danger"):
                    feld = cand
            info = {"aktion": aktion, "feld_element": feld.get_attribute("name") if feld else None,
                    "feld_sichtbar": bool(feld and feld.is_visible()),
                    "readonly_klasse": ("oe_read_only" in (feld.get_attribute("class") or "")) if feld else None,
                    "text": (feld.inner_text() or "").strip()[:120] if feld else None,
                    "hinweise": [(e.inner_text() or "").strip() for e in d.query_selector_all(".alert")],
                    "bild": os.path.join(a.out, "%s_%s_setzen.png" % (a.instanz, name))}
            seite.screenshot(path=info["bild"], full_page=False)
            print("  %s: %s" % (aktion, json.dumps(info, ensure_ascii=False)))
            for el in d.query_selector_all("button"):
                if (el.inner_text() or "").strip() in ("Abbrechen", "Cancel", "Schließen", "Close"):
                    el.click()
                    break
            time.sleep(1.5)

        probe("/odoo/action-431?view_type=list", "Angebot zu Auftrag", "angebot")
        probe("/odoo/action-1105?view_type=list", "Abo-Status ändern", "abo")
        b.close()


if __name__ == "__main__":
    main()
