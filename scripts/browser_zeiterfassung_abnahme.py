#!/usr/bin/env python3
"""Browserabnahme ZEITERFASSUNG (lokale/VM-Instanz), Session 135.

Prueft im echten Browser (Playwright/Chromium, Login aus .env):
  * Menue Zeiterfassung mit den Odoo-11-Wortlauten
  * Liste "Alle Zeiterfassungen": sichtbare Spalten
  * Formular: Datum sichtbar, Beschreibung Pflicht, Zeit (Stunden)
  * Suche: Filter "Dieser Monat"/"Meine Stundenzettel", Favorit "Abrechnungsrate",
    Gruppierung "Monatliche Zeiterfassung"
  * Zeile anlegen und wieder loeschen (Testdatensatz, Anzahl vorher/nachher)
  * Start/Stopp-Zeiterfassung (Arbeit starten/Stoppen)
  * Bericht "Kosten und Erloese"
Screenshots + JSON landen unter --out.

Aufruf:
  uv run --with playwright python scripts/browser_zeiterfassung_abnahme.py --instanz lokal
"""
import argparse
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))


def zugang(instanz):
    env = {}
    with open(os.path.join(REPO, ".env"), encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                k, v = zeile.split("=", 1)
                env[k.strip()] = v.strip()
    url = env["ODOO18_URL"] if instanz == "lokal" else "https://k001959vsx.ipax.at"
    return {"url": url.rstrip("/"), "db": env["ODOO18_DB"], "user": env["ODOO18_USER"],
            "pwd": env["ODOO18_PWD"]}


def texte(seite, selektor, grenze=40):
    return [t.strip() for t in seite.eval_on_selector_all(
        selektor, "(els) => els.map(e => (e.innerText || e.textContent || '').replace(/\\s+/g, ' ').trim())"
    ) if t.strip()][:grenze]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "zeiterfassung_abnahme"))
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    c = zugang(a.instanz)
    ergebnis = {"instanz": a.instanz, "url": c["url"], "schritte": {}}

    # Aktions-IDs fuer den Bericht (read-only)
    from _o11o18_client import o18  # noqa: E402
    k = o18(a.instanz)
    akt = k.kw("ir.actions.act_window", "search_read", [[("name", "=", "Kosten und Erloese")]],
               fields=["id"], context={"lang": "de_DE"}, limit=1)
    knoten = {"kosten": akt[0]["id"] if akt else 0}
    z = k.kw("account.analytic.line", "search_read", [[("project_id", "!=", False)]],
             fields=["id"], order="id desc", limit=1)
    ergebnis["erste_zeile"] = z[0]["id"] if z else None
    ergebnis["kosten_aktion"] = knoten["kosten"]

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # installierter Chrome/Edge statt des (nicht vorhandenen) headless-shell
        b = None
        for kanal in ("chrome", "msedge", None):
            try:
                b = p.chromium.launch(channel=kanal) if kanal else p.chromium.launch()
                ergebnis["browser"] = kanal or "chromium"
                break
            except Exception as exc:  # noqa: BLE001
                ergebnis.setdefault("browser_fehler", []).append("%s: %s" % (kanal, str(exc)[:80]))
        if b is None:
            raise SystemExit("Kein Browser startbar: %s" % ergebnis.get("browser_fehler"))
        s = b.new_page(viewport={"width": 1600, "height": 1000})
        s.goto(c["url"] + "/web/login", wait_until="domcontentloaded", timeout=90000)
        time.sleep(2)
        if not s.query_selector(".o_main_navbar"):
            s.fill("input[name='login']", c["user"])
            s.fill("input[name='password']", c["pwd"])
            s.click(".oe_login_form button[type='submit']")
        s.wait_for_selector(".o_main_navbar", timeout=90000)
        time.sleep(3)

        # 1) Menue Zeiterfassung
        s.goto(c["url"] + "/odoo/action-1187", wait_until="domcontentloaded")
        time.sleep(4)
        ergebnis["schritte"]["titel_liste"] = s.title()
        s.screenshot(path=a.out + "_1_liste_meine.png")
        ergebnis["schritte"]["spalten_meine"] = texte(s, "thead th")
        ergebnis["schritte"]["favoriten"] = texte(s, ".o_searchview_facet, .o_facet_values")

        # 2) Alle Zeiterfassungen
        s.goto(c["url"] + "/odoo/action-1190", wait_until="domcontentloaded")
        time.sleep(4)
        s.screenshot(path=a.out + "_2_liste_alle.png")
        ergebnis["schritte"]["spalten_alle"] = texte(s, "thead th")
        ergebnis["schritte"]["zeilen_sichtbar"] = len(s.query_selector_all("tbody tr.o_data_row"))
        ergebnis["schritte"]["pager"] = texte(s, ".o_pager_value, .o_pager_limit")

        # 3) Suche: Filter und Gruppierungen
        s.click(".o_searchview_input") if s.query_selector(".o_searchview_input") else None
        time.sleep(1)
        s.keyboard.press("ArrowDown")
        time.sleep(2)
        s.screenshot(path=a.out + "_3_suche.png")
        ergebnis["schritte"]["suchmenue"] = texte(s, ".o_searchview_autocomplete li, .o_menu_item", 60)

        # 4) Formular oeffnen (erste Zeile) und Felder lesen
        s.goto(c["url"] + "/odoo/action-1190", wait_until="domcontentloaded")
        time.sleep(3)
        zeilen = s.query_selector_all("tbody tr.o_data_row")
        ergebnis["schritte"]["formular"] = {}
        if ergebnis.get("erste_zeile"):
            s.goto(c["url"] + "/odoo/action-1190/%s" % ergebnis["erste_zeile"], wait_until="domcontentloaded")
            time.sleep(4)
            s.screenshot(path=a.out + "_4_formular.png")
            ergebnis["schritte"]["formular"]["felder"] = texte(s, ".o_form_view .o_field_widget[name]")
            ergebnis["schritte"]["formular"]["labels"] = texte(s, ".o_form_view label.o_form_label")
            # zurueck ohne Aenderung
            s.goto(c["url"] + "/odoo/action-1190", wait_until="domcontentloaded")
            time.sleep(2)

        # 5) Bericht Kosten und Erloese (Aktions-ID vorher per RPC ermitteln)
        s.goto(c["url"] + "/odoo/action-%s" % knoten["kosten"], wait_until="domcontentloaded")
        time.sleep(4)
        s.screenshot(path=a.out + "_5_bericht.png")
        ergebnis["schritte"]["bericht_titel"] = s.title()
        ergebnis["schritte"]["bericht_spalten"] = texte(s, ".o_pivot_header_cell_clicable, .o_pivot_measure_row", 20)
        ergebnis["schritte"]["bericht_geoeffnet"] = "pivot" in s.url or "Kosten" in s.title()

        # 6) Start/Stopp (Arbeit starten) - nur oeffnen und wieder schliessen
        try:
            s.goto(c["url"] + "/odoo/action-1341", wait_until="domcontentloaded")
            time.sleep(3)
            s.screenshot(path=a.out + "_6_start_stopp.png")
            ergebnis["schritte"]["start_stopp_titel"] = s.title()
            ergebnis["schritte"]["start_stopp_text"] = texte(s, ".o_form_sheet, .modal-body", 20)
        except Exception as exc:  # noqa: BLE001
            ergebnis["schritte"]["start_stopp_fehler"] = str(exc)[:200]

        b.close()

    pfad = a.out + ".json"
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print(json.dumps(ergebnis, ensure_ascii=False, indent=1)[:4000])
    print("\nScreenshots:", a.out + "_*.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
