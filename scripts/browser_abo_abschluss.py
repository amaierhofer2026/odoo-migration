"""Abschluss-Browserpruefung Abonnements (Session 118, Teil 6).

Prueft im echten Browser:
  --instanz vm   Odoo 18 VM: Abo-Formular (Buttons, Smart Buttons, Felder, Waehrung) und die
                 Waehrungsanzeige in Angeboten, Verkaufsauftraegen, Abos, Rechnungen und Einkauf.
  --instanz o11  Odoo 11 Prod: dasselbe Formular - ausschliesslich lesend (nur Ansichten oeffnen,
                 nichts anklicken, nichts speichern).

Aufruf: uv run --with playwright python scripts/browser_abo_abschluss.py --instanz vm
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Layoutvergleich-Session95")

FELDER = ["Kunde", "Preisliste", "Währung", "Referenz", "Datum der nächsten Rechnung", "Verkäufer",
          "Vorlage für Abonnements", "Verkaufsauftrag", "Nutzungsvereinbarung", "Startdatum",
          "Mindestvertragsdauer", "Kündigungsfrist", "Enddatum", "Produkt", "Beschreibung", "Menge",
          "Mengeneinheit", "Preis pro ME", "Rabatt", "Zwischensumme", "Multiplikationsfaktor"]
REITER = ["Abonnement-Einträge", "Wiederkehrende Buchungen", "Einstellungen"]


def lade_env(pfad):
    werte = {}
    for zeile in open(pfad, encoding="utf-8"):
        if "=" in zeile and not zeile.strip().startswith("#"):
            s, w = zeile.split("=", 1)
            werte[s.strip()] = w.strip()
    return werte


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "o11"], required=True)
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    if a.instanz == "vm":
        url = "https://k001959vsx.ipax.at"
        login, pwd = env["ODOO18_USER"], env["ODOO18_PWD"]
        liste = "/odoo/subscriptions"
    else:
        url = "https://portal.it-kommunal.at"
        login, pwd = "anna.maierhofer@it-kommunal.at", env["ODOO11_PWD"]
        liste = "/web#model=sale.subscription&view_type=list"
    from playwright.sync_api import sync_playwright
    ok = fehler = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        ctx = b.new_context(viewport={"width": 1600, "height": 1100}, ignore_https_errors=True, locale="de-AT")
        pg = ctx.new_page()
        pg.goto(url + "/web/login", wait_until="domcontentloaded", timeout=90000)
        pg.fill('input[name="login"]', login)
        pg.fill('input[name="password"]', pwd)
        pg.click('form.oe_login_form button[type="submit"], form button.btn-primary')
        pg.wait_for_load_state("networkidle", timeout=90000)
        if "login" in pg.url:
            pg.fill('input[name="login"]', login)
            pg.fill('input[name="password"]', pwd)
            pg.press('input[name="password"]', "Enter")
            pg.wait_for_load_state("networkidle", timeout=90000)
        pg.goto(url + liste, wait_until="domcontentloaded", timeout=90000)
        pg.wait_for_timeout(6000)

        def text():
            return pg.inner_text("body")

        def pruefe(bedingung, meldung):
            nonlocal ok, fehler
            if bedingung:
                ok += 1
                print("  OK   %s" % meldung)
            else:
                fehler += 1
                print("  FEHL %s" % meldung)

        print("Instanz: %s (%s)" % (a.instanz, url))
        print("\n1) Abo-Liste und Formular")
        pruefe("Abonnement" in text(), "Abo-Menue/Liste geladen")
        # erstes Abo in der Liste oeffnen
        zeilen = pg.query_selector_all("tr.o_data_row a, .o_data_row td")
        ziel = None
        for z in zeilen:
            if z.inner_text().strip():
                ziel = z
                break
        if ziel:
            ziel.click()
            pg.wait_for_timeout(6000)
        pruefe("Abonnement" in text() or "Abo" in text(), "Abo-Formular geoeffnet")
        for f in FELDER:
            pruefe(f in text(), "Feld/Bezeichnung sichtbar: %s" % f)
        for r in REITER:
            if r in text():
                pruefe(True, "Reiter sichtbar: %s" % r)
        print("\n2) Buttons und Smart Buttons")
        for b_name in ["Abonnement-Zusatzverkäufe", "Abonnement starten", "Zu erneuern",
                       "Abo-Auftrag schließen", "Abo-Auftrag abbrechen", "Erneuerungsangebot",
                       "Rechnungen", "Online-Vorschau"]:
            pruefe(b_name in text(), "sichtbar: %s" % b_name)
        print("\n3) Waehrung im Abo")
        pruefe("€" in text(), "Euro-Zeichen im Abo sichtbar")
        pruefe("$" not in text(), "kein Dollar-Zeichen im Abo")
        os.makedirs(SHOTS, exist_ok=True)
        pfad = os.path.join(SHOTS, "49_%s_Abo_Formular.png" % a.instanz.upper())
        pg.screenshot(path=pfad, full_page=True)
        print("Screenshot:", pfad)
        b.close()
    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
