#!/usr/bin/env python3
"""Browser-Probe Massenbearbeitung Odoo 18 (Ist-Stand, nur oeffnen und abbrechen).

Oeffnet echte Listenansichten, das Aktionsmenue und die Massenbearbeitungs-Dialoge,
liest die sichtbaren deutschen Beschriftungen und beendet jeden Dialog mit "Abbrechen".
Es wird kein Datensatz geschrieben (kein Klick auf "Anwenden").

Aufruf:
  uv run --with playwright python scripts/browser_massenbearbeitung_probe.py --instanz lokal
  uv run --with playwright python scripts/browser_massenbearbeitung_probe.py --instanz vm
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

TITEL = []


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
        raise SystemExit("Login fehlgeschlagen: %s" % daten["error"])
    return next(c.value for c in jar if c.name == "session_id")


def sichtbar(seite, selektor):
    ergebnis = []
    for e in seite.query_selector_all(selektor):
        if e.is_visible():
            t = (e.inner_text() or "").strip().replace("\n", " ")
            if t:
                ergebnis.append(t)
    return ergebnis


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
    ergebnis = {"instanz": a.instanz, "url": url, "dialoge": []}

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = None
        for kanal in ("chrome", "msedge", None):
            try:
                b = p.chromium.launch(channel=kanal) if kanal else p.chromium.launch()
                ergebnis["browser"] = kanal or "chromium"
                break
            except Exception:  # noqa: BLE001
                continue
        ctx = b.new_context(viewport={"width": 1600, "height": 1100})
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.new_page()

        def schuss(name):
            pfad = os.path.join(a.out, "%s_%s.png" % (a.instanz, name))
            seite.screenshot(path=pfad, full_page=False)
            return pfad

        def liste(url_pfad, titel):
            seite.goto(url + url_pfad, wait_until="domcontentloaded", timeout=120000)
            seite.wait_for_selector(".o_list_view", timeout=120000)
            time.sleep(3)
            print("\n=== %s (%s) ===" % (titel, url_pfad))

        def aktionen():
            """Zeilen markieren, Aktionsmenue oeffnen, Eintraege zurueckgeben."""
            boxen = seite.query_selector_all(".o_list_view thead .o_list_record_selector input,"
                                            " .o_list_view thead input[type=checkbox]")
            if boxen:
                boxen[0].click()
                time.sleep(1.5)
            knopf = None
            for el in seite.query_selector_all(".o_control_panel button, .o_control_panel .dropdown-toggle"):
                txt = (el.inner_text() or "").strip()
                if txt.startswith("Aktion") and el.is_visible():
                    knopf = el
                    break
            if knopf is None:
                return []
            knopf.click()
            time.sleep(2)
            eintraege = sichtbar(seite, ".o-dropdown--menu .dropdown-item")
            return eintraege

        def dialog(name, treffer):
            for el in seite.query_selector_all(".o-dropdown--menu .dropdown-item"):
                if el.is_visible() and treffer.lower() in (el.inner_text() or "").lower():
                    el.click()
                    break
            else:
                print("  FEHLER: Aktion %r nicht im Menue" % treffer)
                return None
            seite.wait_for_selector(".o_dialog .o_form_view", timeout=60000)
            time.sleep(2.5)
            d = seite.query_selector(".o_dialog")
            labels = sichtbar(d, "label, .o_field_widget[name^='selection__']")
            hinweise = sichtbar(d, "p, .alert")
            optionen = []
            for sel in d.query_selector_all(".o_field_widget[name^='selection__']"):
                optionen.append(sel.inner_text().strip().replace("\n", " "))
            titel = d.query_selector(".modal-title")
            daten = {"aktion": treffer, "titel": titel.inner_text().strip() if titel else None,
                     "labels": labels, "hinweise": hinweise, "optionen": optionen,
                     "feldwidgets": [e.get_attribute("name") for e in
                                     d.query_selector_all(".o_field_widget[name]")]}
            daten["bild"] = schuss("dialog_%s" % name)
            ergebnis["dialoge"].append(daten)
            print("  Dialog:", daten["titel"])
            print("    Felder:  ", daten["feldwidgets"])
            print("    Labels:  ", labels)
            print("    Auswahl: ", optionen)
            print("    Hinweise:", hinweise)
            # abbrechen, nichts speichern
            for el in d.query_selector_all("button"):
                if (el.inner_text() or "").strip() in ("Abbrechen", "Cancel", "Schließen", "Close"):
                    el.click()
                    break
            time.sleep(1.5)
            return daten

        liste("/odoo/action-141?view_type=list", "Kontakte")
        akte = aktionen()
        print("  Aktionsmenue Kontakte:", akte)
        ergebnis["aktionen_kontakte"] = akte
        ergebnis["bild_menu_kontakte"] = schuss("menue_kontakte")
        dialog("tag", "Tag-Zuweisung")
        akte = aktionen()
        dialog("preisliste", "Zuweisung Preisliste")
        akte = aktionen()
        dialog("statuskunde", "Status Kunde")

        liste("/odoo/action-354?view_type=list", "Ausgangsrechnungen")
        akte = aktionen()
        print("  Aktionsmenue Rechnungen:", akte)
        ergebnis["aktionen_rechnungen"] = akte
        ergebnis["bild_menu_rechnungen"] = schuss("menue_rechnungen")
        dialog("rechnungsdatum", "Rechnungsdatum Abrechnung")

        liste("/odoo/action-210?view_type=list", "Leads")
        akte = aktionen()
        print("  Aktionsmenue Leads:", akte)
        ergebnis["aktionen_leads"] = akte
        dialog("leadstatus", "Interessent Lead Status")

        liste("/odoo/action-431?view_type=list", "Angebote")
        akte = aktionen()
        print("  Aktionsmenue Angebote:", akte)
        ergebnis["aktionen_angebote"] = akte
        dialog("angebotzuauftrag", "Angebot zu Auftrag")

        liste("/odoo/action-1105?view_type=list", "Abonnements")
        akte = aktionen()
        print("  Aktionsmenue Abonnements:", akte)
        ergebnis["aktionen_abos"] = akte
        dialog("abostatus", "Abo-Status ändern")

        b.close()

    ziel = os.path.join(a.out, "probe_%s.json" % a.instanz)
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print("\nJSON:", ziel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
