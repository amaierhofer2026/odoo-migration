#!/usr/bin/env python3
"""Rechtepruefung Massenbearbeitung (Odoo 18).

Legt einen Testbenutzer ohne Einstellungsrechte an, prueft im echten Browser
Aktionsmenue und Dialog und per RPC die Konfigurationsrechte, und entfernt den
Benutzer danach wieder.

Aufruf: uv run --with playwright python scripts/rechte_massenbearbeitung.py --instanz lokal
"""
from __future__ import annotations

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
from _o11o18_client import lade_env, o18  # noqa: E402

DE = {"lang": "de_DE"}
LOGIN = "s140_massentest"
PASSWORT = "S140-test-2026"


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
        daten = json.loads(r.read().decode())
    if daten.get("error"):
        raise RuntimeError(daten["error"])
    return next(c.value for c in jar if c.name == "session_id")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    a = ap.parse_args()
    env = lade_env()
    url = (env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal"
           else "https://k001959vsx.ipax.at").rstrip("/")
    domain = url.split("//")[1].split(":")[0]
    moment = o18(a.instanz)

    ok_zahl = [0]
    fehler = []

    def pruefe(bedingung, text, ist=None):
        if bedingung:
            ok_zahl[0] += 1
            print("  OK    %s%s" % (text, "" if ist is None else "  (%s)" % (ist,)))
        else:
            fehler.append("%s | ist=%r" % (text, ist))
            print("  FEHL  %s | ist=%r" % (text, ist))

    # Testbenutzer
    alt = moment.kw("res.users", "search", [[("login", "=", LOGIN)]])
    if alt:
        moment.kw("res.users", "unlink", [alt])
    def gid(xmlid):
        m, n = xmlid.split(".")
        return moment.kw("ir.model.data", "search_read",
                         [[("module", "=", m), ("name", "=", n)], ["res_id"]])[0]["res_id"]

    # interner Benutzer ohne Einstellungsrechte, aber mit Kontaktpflege (darf Kontakte schreiben)
    gruppen = [gid("base.group_user"), gid("base.group_partner_manager")]
    benutzer = moment.kw("res.users", "create", [[{
        "name": "S140 Massentest",
        "login": LOGIN,
        "password": PASSWORT,
        "groups_id": [(6, 0, gruppen)],
    }]])
    print("Testbenutzer angelegt:", benutzer)

    try:
        sid = sitzung(url, env["ODOO18_DB"], LOGIN, PASSWORT)
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome")
            ctx = b.new_context(viewport={"width": 1500, "height": 950})
            ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
            seite = ctx.new_page()
            seite.goto(url + "/odoo/action-141?view_type=list", wait_until="domcontentloaded",
                       timeout=120000)
            seite.wait_for_selector(".o_list_view", timeout=120000)
            time.sleep(4)
            markiert = seite.evaluate(
                """() => {
                    const zeilen = [...document.querySelectorAll('.o_data_row')];
                    let n = 0;
                    for (let i = 0; i < 2 && i < zeilen.length; i++) {
                        const kasten = zeilen[i].querySelector('input[type=checkbox]');
                        if (kasten && !kasten.checked) { kasten.click(); n += 1; }
                    }
                    return [...document.querySelectorAll(
                        '.o_data_row .o_list_record_selector input[type=checkbox]')]
                        .filter(k => k.checked).length;
                }""")
            time.sleep(1.5)
            print("  markierte Zeilen:", markiert)
            menue = []
            for el in seite.query_selector_all(".o_control_panel button, .o_control_panel .dropdown-toggle"):
                if (el.inner_text() or "").strip().startswith("Aktion") and el.is_visible():
                    el.click()
                    break
            time.sleep(2)
            menue = [e.inner_text().strip() for e in
                     seite.query_selector_all(".o-dropdown--menu .dropdown-item") if e.is_visible()]
            print("  Aktionsmenue (Testbenutzer):", menue)
            pruefe("Tag-Zuweisung" in menue, "Aktion im Menue sichtbar (ohne Einstellungsrechte)")
            pruefe("Massenbearbeitung Kontakte" not in menue, "Dublette nicht mehr im Menue")

            geoeffnet = False
            for el in seite.query_selector_all(".o-dropdown--menu .dropdown-item"):
                if el.is_visible() and el.inner_text().strip() == "Tag-Zuweisung":
                    el.click()
                    geoeffnet = True
                    break
            if geoeffnet:
                try:
                    seite.wait_for_selector(".o_dialog .o_form_view", timeout=30000)
                except Exception:  # noqa: BLE001
                    geoeffnet = False
            pruefe(geoeffnet, "Dialog fuer Testbenutzer bedienbar")
            if not geoeffnet:
                seite.screenshot(path=os.path.join(os.environ.get("TEMP", "."),
                                                   "rechte_%s_kein_dialog.png" % a.instanz))
                b.close()
                raise SystemExit(1)
            time.sleep(2)
            dialog = seite.query_selector(".o_dialog")
            optionen = [o.inner_text().strip() for o in
                        dialog.query_selector_all(".o_field_widget[name^='selection__'] option")
                        if o.inner_text().strip()]
            pruefe("Nicht ändern" in optionen, "Dialog bedienbar (Optionen)", optionen)
            hinweis = ""
            for el in dialog.query_selector_all(".alert, p"):
                if "ausgewählten" in (el.inner_text() or ""):
                    hinweis = el.inner_text().strip()
            pruefe(str(markiert) in hinweis,
                   "Zaehlanzeige nennt %d markierte Datensaetze" % markiert, hinweis)
            pruefe(markiert >= 1, "mindestens eine Zeile markiert", markiert)
            bild = os.path.join(os.environ.get("TEMP", "."), "rechte_%s.png" % a.instanz)
            seite.screenshot(path=bild)
            for el in dialog.query_selector_all("button"):
                if (el.inner_text() or "").strip() in ("Abbrechen", "Cancel"):
                    el.click()
                    break
            time.sleep(1)

            # Konfiguration darf nicht erreichbar sein (Aktions-ID je Instanz aufloesen)
            xmlid = moment.kw("ir.model.data", "search_read",
                              [[("module", "=", "itk_massenbearbeitung"),
                                ("name", "=", "action_itk_massenbearbeitung")], ["res_id"]])
            aktion_id = xmlid[0]["res_id"] if xmlid else 0
            pruefe(bool(aktion_id), "Menueaktion Massenverarbeitung gefunden", aktion_id)
            seite.goto(url + "/odoo/action-%s" % aktion_id, wait_until="domcontentloaded",
                       timeout=90000)
            time.sleep(4)
            inhalt = seite.inner_text("body")
            pruefe("Zugriff" in inhalt or "Access" in inhalt or "nicht erlaubt" in inhalt
                   or seite.query_selector(".o_list_view") is None,
                   "Konfigurationsliste fuer Testbenutzer gesperrt",
                   (inhalt or "")[:120].replace("\n", " "))
            b.close()

        # RPC-Rechte
        test = o18(a.instanz)
        # als Testbenutzer anmelden
        test = type(moment)("https://k001959vsx.ipax.at" if a.instanz == "vm"
                            else env.get("ODOO18_URL", "http://localhost:8069"),
                            env["ODOO18_DB"], LOGIN, PASSWORT)
        try:
            test.kw("ir.actions.server", "write", [[1304], {"name": "Zuweisung Preisliste NÖ"}])
            pruefe(False, "Schreiben auf Server-Aktion fuer Testbenutzer verweigert", "erlaubt")
        except Exception as exc:  # noqa: BLE001
            pruefe("Access" in str(exc) or "Zugriff" in str(exc) or "nicht erlaubt" in str(exc),
                   "Schreiben auf Server-Aktion fuer Testbenutzer verweigert", str(exc)[:80])
        try:
            anzahl = test.kw("mass.editing.wizard", "search_count", [[]])
            pruefe(True, "Assistent fuer Testbenutzer lesbar", anzahl)
        except Exception as exc:  # noqa: BLE001
            pruefe(False, "Assistent fuer Testbenutzer lesbar", str(exc)[:80])
    finally:
        # res.users legt beim Anlegen einen Kontakt an; der bleibt beim Loeschen des
        # Benutzers bestehen und muss mit entfernt werden (keine Testreste).
        partner = moment.kw("res.users", "read", [[benutzer[0]], ["partner_id"]])[0]["partner_id"]
        moment.kw("res.users", "unlink", [benutzer])
        if partner:
            moment.kw("res.partner", "unlink", [[partner[0]]])
            pruefe(moment.kw("res.partner", "search_count", [[("id", "=", partner[0])]]) == 0,
                   "Testkontakt des Benutzers entfernt", partner[0])
        pruefe(moment.kw("res.users", "search_count", [[("login", "=", LOGIN)]]) == 0,
               "Testbenutzer entfernt")

    print("\n=== Ergebnis: %d OK / %d FEHL ===" % (ok_zahl[0], len(fehler)))
    for f in fehler:
        print("  FEHL:", f)
    return 0 if not fehler else 1


if __name__ == "__main__":
    sys.exit(main())
