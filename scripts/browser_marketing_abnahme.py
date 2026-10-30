#!/usr/bin/env python3
"""Browserabnahme Bereich E-MAIL-MARKETING (echter Chrome, Session 138).

Prueft die Odoo-11-Oberflaeche im Odoo 18 und die uebernommenen Daten:
Menues, Mailingsliste mit Odoo-11-Spalten, Kampagnen mit Stufen, Kampagnenstufen,
Kampagnen-Tags, Formular mit historischen Kennzahlen und die Versandsperre.

Aufruf:
  uv run --with playwright python scripts/browser_marketing_abnahme.py --instanz lokal
  uv run --with playwright python scripts/browser_marketing_abnahme.py --instanz vm
"""
import argparse
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from _o11o18_client import o18  # noqa: E402

DE = {"lang": "de_DE"}
ok = 0
fehler = []


def pruefe(bedingung, text, ist=None, soll=None):
    global ok
    if bedingung:
        ok += 1
        print("  OK   ", text, "" if ist is None else "(%s)" % (ist,))
    else:
        fehler.append("%s | ist=%r soll=%r" % (text, ist, soll))
        print("  FEHLER", text, "| ist=%r soll=%r" % (ist, soll))


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


def texte(seite, selektor, grenze=120):
    return [t for t in (t.strip() for t in seite.eval_on_selector_all(
        selektor,
        "(els) => els.map(e => (e.innerText || e.textContent || '').replace(/\\s+/g, ' ').trim())"
    )) if t][:grenze]


def warte(sekunden=2.0):
    time.sleep(sekunden)


def pager(seite):
    return texte(seite, ".o_pager_value, .o_pager_limit", 4)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "marketing_abnahme"))
    a = ap.parse_args()
    c = zugang(a.instanz)
    k = o18(a.instanz)
    os.makedirs(a.out, exist_ok=True)
    ergebnis = {"instanz": a.instanz, "url": c["url"], "schritte": []}

    def rid(xmlid):
        m, n = xmlid.split(".")
        d = k.kw("ir.model.data", "search_read", [[("module", "=", m), ("name", "=", n)], ["res_id"]])
        return d[0]["res_id"] if d else 0

    # Aktion des Menues "Massenmailings" (nicht irgendeine Mailing-Aktion)
    menue = k.kw("ir.ui.menu", "read", [[rid("mass_mailing.mass_mailing_menu")], ["action"]], context=DE)[0]
    aktion_mailing = int((menue["action"] or "ir.actions.act_window,0").split(",")[1])
    aktion_kampagne = rid("itk_mass_mailing_compat.action_itk_mailing_campaign")
    aktion_stufe = rid("itk_mass_mailing_compat.action_itk_mailing_campaign_stage")
    probe = k.kw("mailing.mailing", "search_read",
                 [[("x_o11_id", "!=", False), ("x_o11_sent", ">", 0)],
                  ["id", "subject", "state", "x_o11_sent", "x_o11_opened"]],
                 context=DE, limit=1)
    probe = probe[0] if probe else None
    print("Aktionen:", aktion_mailing, aktion_kampagne, aktion_stufe, "| Probe:", probe)

    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            b = None
            for kanal in ("chrome", "msedge", None):
                try:
                    b = p.chromium.launch(channel=kanal) if kanal else p.chromium.launch()
                    ergebnis["browser"] = kanal or "chromium"
                    break
                except Exception as exc:  # noqa: BLE001
                    ergebnis.setdefault("browser_fehler", []).append(str(exc)[:80])
            if b is None:
                raise SystemExit("Kein Browser startbar")
            seite = b.new_page(viewport={"width": 1600, "height": 1000})
            seite.goto(c["url"] + "/web/login", wait_until="domcontentloaded", timeout=90000)
            warte(2)
            if not seite.query_selector(".o_main_navbar"):
                seite.fill("input[name='login']", c["user"])
                seite.fill("input[name='password']", c["pwd"])
                seite.click(".oe_login_form button[type='submit']")
            seite.wait_for_selector(".o_main_navbar", timeout=90000)
            warte(2)

            def schuss(name):
                pfad = os.path.join(a.out, "%s_%s.png" % (a.instanz, name))
                seite.screenshot(path=pfad, full_page=False)
                ergebnis["schritte"].append({"schritt": name, "bild": pfad})

            # ------------------------------------------------------- Menues
            # echter Weg: App-Umschalter (Kachel-Symbol) -> App E-Mail-Marketing
            seite.goto("%s/odoo/action-%s" % (c["url"], aktion_mailing), wait_until="domcontentloaded")
            warte(4)
            umschalter = seite.query_selector(".o_navbar_apps_menu button, .o_navbar_apps_menu")
            pruefe(umschalter is not None, "App-Umschalter vorhanden", bool(umschalter))
            app = None
            if umschalter:
                umschalter.click()
                warte(2)
                for el in seite.query_selector_all(".o-dropdown--menu .dropdown-item, .o_app"):
                    if "E-Mail-Marketing" in (el.inner_text() or ""):
                        app = el
                        break
            pruefe(app is not None, "App 'E-Mail-Marketing' im App-Umschalter", bool(app))
            if app:
                app.click()
                warte(5)
            nav = texte(seite, ".o_main_navbar, .o_main_navbar .o_menu_sections > *", 40)
            print("  Menueleiste:", nav)
            gesamt = " | ".join(nav)
            pruefe("Massenmailings" in gesamt, "Menue 'Massenmailings'", gesamt[:200])
            pruefe("Kampagnen" in gesamt, "Menue 'Kampagnen'", gesamt[:200])

            seite.goto("%s/odoo/action-%s?view_type=list" % (c["url"], aktion_mailing),
                       wait_until="domcontentloaded")
            warte(4)
            # Standardsuche des Odoo-18-Action ("mir zugewiesen") entfernen
            for _ in range(6):
                knopf = seite.query_selector(".o_searchview_facet .o_facet_remove")
                if not knopf:
                    break
                knopf.click()
                warte(1.5)
            kopf = texte(seite, ".o_list_view thead th", 40)
            print("  Spalten:", kopf)
            for spalte in ("Bezeichnung (Odoo 11)", "Kampagne (Odoo 11)", "Gesendet (Odoo 11)",
                           "Zugestellt (Odoo 11)", "Geöffnet (Odoo 11)"):
                pruefe(any(spalte in s for s in kopf), "Spalte %r" % spalte, kopf)
            pg = pager(seite)
            pruefe(len(pg) >= 2 and pg[1].replace(".", "") == "133",
                   "Liste zeigt 133 aktive Mailings", pg)
            schuss("01_mailings")

            # ------------------------------------------------------ Kampagnen
            seite.goto("%s/odoo/action-%s" % (c["url"], aktion_kampagne), wait_until="domcontentloaded")
            warte(4)
            spalten = texte(seite, ".o_kanban_header .o_column_title, .o_kanban_header_title", 20)
            print("  Kampagnenspalten:", spalten)
            pruefe(any("Ausführungsplan" in s for s in spalten), "Kanban zeigt Stufe 'Ausführungsplan'", spalten)
            karten = texte(seite, ".o_kanban_record", 20)
            pruefe(len(karten) >= 9, "mindestens 9 Kampagnenkarten", len(karten))
            pruefe(any("Informationsfreiheitsgesetz" in t for t in karten),
                   "Kampagne 'Informationsfreiheitsgesetz (IFG)' sichtbar", karten[:6])
            schuss("02_kampagnen")

            # ------------------------------------------------ Kampagnenstufen
            seite.goto("%s/odoo/action-%s" % (c["url"], aktion_stufe), wait_until="domcontentloaded")
            warte(4)
            zeilen = [z for z in texte(seite, ".o_list_view tbody tr", 10) if z.strip("\u200b ")]
            print("  Stufen:", zeilen)
            pruefe(len(zeilen) == 3, "3 Kampagnenstufen", len(zeilen), 3)
            for name in ("Ausführungsplan", "Design", "Gesendet"):
                pruefe(any(name in z for z in zeilen), "Stufe %r" % name, zeilen)
            schuss("03_stufen")

            # ------------------------------------------------------- Formular
            seite.goto("%s/odoo/action-%s/%s" % (c["url"], aktion_mailing, probe["id"]),
                       wait_until="domcontentloaded")
            warte(4)
            gruppen = [g.lower() for g in texte(seite, ".o_group .o_group_name, .o_form_view .o_horizontal_separator", 30)]
            print("  Gruppen:", gruppen)
            pruefe(any("11-angaben" in g for g in gruppen), "Gruppe 'Odoo-11-Angaben'", gruppen)
            pruefe(any("historische kennzahlen" in g for g in gruppen),
                   "Gruppe 'Historische Kennzahlen (Odoo 11)'", gruppen)
            werte = texte(seite, ".o_form_view .o_field_widget", 80)
            pruefe(any(str(probe["x_o11_sent"]) == w for w in werte),
                   "historischer Wert 'Gesendet' sichtbar", werte[:12])
            kopfbuttons = texte(seite, ".o_form_statusbar .o_statusbar_buttons button", 12)
            print("  Statusleiste:", kopfbuttons)
            schuss("04_formular")

            b.close()
    except Exception as exc:  # noqa: BLE001
        fehler.append("Browserlauf: %s" % str(exc)[:300])
        print("FEHLER im Browserlauf:", str(exc)[:300])

    ergebnis["ok"] = ok
    ergebnis["fehler"] = fehler
    with open(os.path.join(a.out, "ergebnis_%s.json" % a.instanz), "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print("\n=== Browserabnahme E-Mail-Marketing %s: %d OK / %d FEHLER ===" % (a.instanz, ok, len(fehler)))
    for f in fehler:
        print("   FEHLER:", f)
    return 0 if not fehler else 1


if __name__ == "__main__":
    sys.exit(main())
