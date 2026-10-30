#!/usr/bin/env python3
"""Browserabnahme Bereich EVENTS (echter Chrome, Session 138).

Prueft die Odoo-11-Oberflaeche im Odoo 18 und die uebernommenen
Veranstaltungsdaten: Menues, Liste mit Spalten, Suche/Filter/Gruppierung,
Formular mit Status, Kategorie, Online-Event, Mindestzahl, Odoo-11-Angaben,
Anlasskategorien und Berichtswesen.

Aufruf:
  uv run --with playwright python scripts/browser_events_abnahme.py --instanz lokal
  uv run --with playwright python scripts/browser_events_abnahme.py --instanz vm
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


def filter_setzen(seite, text, bereich=".o_dropdown_menu .dropdown-item, .o_menu_item"):
    try:
        s = seite.query_selector(".o_searchview_dropdown_toggler")
        if s:
            s.click()
            warte(1.5)
        for el in seite.query_selector_all(bereich):
            try:
                if (el.inner_text() or "").strip() == text:
                    el.click()
                    warte(3)
                    return True
            except Exception:  # noqa: BLE001
                continue
        seite.keyboard.press("Escape")
    except Exception:  # noqa: BLE001
        pass
    return False


def facet_entfernen(seite, alle=True):
    for _ in range(20):
        knopf = seite.query_selector(".o_searchview_facet .o_facet_remove")
        if not knopf:
            return
        knopf.click()
        warte(1.2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "events_abnahme"))
    a = ap.parse_args()
    c = zugang(a.instanz)
    k = o18(a.instanz)
    os.makedirs(a.out, exist_ok=True)
    ergebnis = {"instanz": a.instanz, "url": c["url"], "schritte": []}

    def rid(xmlid):
        m, n = xmlid.split(".")
        d = k.kw("ir.model.data", "search_read", [[("module", "=", m), ("name", "=", n)], ["res_id"]])
        return d[0]["res_id"] if d else 0

    aktion_event = rid("event.action_event_view")
    aktion_typ = rid("event.action_event_type")
    aktion_report = rid("itk_events_compat.action_event_report_itk_events")
    probe = k.kw("event.event", "search_read",
                 [[("x_o11_id", "=", 1)], ["id", "name", "x_o11_id", "x_o11_state", "x_o11_registrations",
                                           "date_begin", "x_o11_organizer_id"]],
                 context={"lang": "de_DE", "active_test": False})
    probe = probe[0] if probe else None
    print("Aktionen:", aktion_event, aktion_typ, aktion_report, "| Probe:", probe)

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
                return pfad

            # ---------------------------------------------------------- Menue
            seite.goto("%s/odoo/action-%s" % (c["url"], aktion_event), wait_until="domcontentloaded")
            warte(4)
            nav = texte(seite, ".o_main_navbar .o_menu_sections > *", 40)
            print("  Menueleiste:", nav)
            pruefe(any("Events" in n for n in nav), "App-Menue zeigt 'Events'", nav)
            pruefe(any("Berichtswesen" in n for n in nav), "Menue 'Berichtswesen' sichtbar", nav)
            pruefe(any("Konfiguration" in n for n in nav), "Menue 'Konfiguration' sichtbar", nav)

            # Kanban (Odoo-11-Standardansicht der Aktion) mit den Odoo-11-Statusspalten
            spalten = texte(seite, ".o_kanban_header .o_column_title, .o_kanban_header_title", 20)
            print("  Kanbanspalten:", spalten)
            pruefe(any("Bestätigt" in s for s in spalten), "Kanban zeigt Statusspalte 'Bestätigt'", spalten)
            pruefe(any("Erledigt" in s for s in spalten), "Kanban zeigt Statusspalte 'Erledigt'", spalten)
            schuss("01_kanban")

            # ---------------------------------------------------------- Liste
            umschalter = seite.query_selector(".o_switch_view.o_list")
            pruefe(umschalter is not None, "Listenumschalter vorhanden", bool(umschalter))
            if umschalter:
                umschalter.click()
                warte(3)
            kopf = texte(seite, ".o_list_view thead th", 40)
            print("  Spalten:", kopf)
            for spalte in ("Veranstaltungsname", "Kategorie", "Startdatum", "Enddatum",
                           "Reservierungen", "Max. Teilnehmeranzahl", "Mindestzahl an Teilnehmern",
                           "Verantwortlich", "Status"):
                pruefe(any(spalte in s for s in kopf), "Spalte %r vorhanden" % spalte, kopf)
            pg = pager(seite)
            pruefe(len(pg) >= 2 and pg[1].replace(".", "") == "121",
                   "Liste zeigt 121 aktive Veranstaltungen", pg)

            # ---------------------------------------------------------- Filter
            # 1) Filterangebot im Suchmenue sichtbar (Odoo-11-Statusfilter)
            seite.goto("%s/odoo/action-%s" % (c["url"], aktion_event), wait_until="domcontentloaded")
            warte(4)
            if seite.query_selector(".o_switch_view.o_list"):
                seite.click(".o_switch_view.o_list")
                warte(3)
            toggler = seite.query_selector(".o_searchview_dropdown_toggler")
            pruefe(toggler is not None, "Suchmenue-Aufklapper vorhanden", bool(toggler))
            if toggler:
                toggler.click()
                warte(2)
                for el in seite.query_selector_all(".o_searchview_dropdown_toggler, .o_menu_toggle, .dropdown-toggle"):
                    if (el.inner_text() or "").strip().startswith("Filter"):
                        el.click()
                        warte(2)
                        break
                angebot = texte(seite, ".o_dropdown_menu .dropdown-item, .o_menu_item", 60)
                print("  Filterangebot:", angebot[:25])
                for name in ("Nicht bestätigt", "Bestätigt", "Erledigt", "Abgebrochen"):
                    pruefe(any(name == a or a.startswith(name) for a in angebot),
                           "Filter %r im Suchmenue" % name, angebot[:25])
                schuss("02_filterangebot")
                seite.keyboard.press("Escape")
                warte(1)

            # 2) Ein Filter wird wirklich angewendet (Gegenprobe am Zaehler)
            seite.goto("%s/odoo/action-%s" % (c["url"], aktion_event), wait_until="domcontentloaded")
            warte(4)
            if seite.query_selector(".o_switch_view.o_list"):
                seite.click(".o_switch_view.o_list")
                warte(3)
            if filter_setzen(seite, "Abgebrochen"):
                pg = pager(seite)
                pruefe(len(pg) >= 2 and pg[1].replace(".", "") == "15",
                       "Filter 'Abgebrochen' ergibt 15", pg)
                schuss("02_filter_abgebrochen")
            else:
                pruefe(False, "Filter 'Abgebrochen' anwendbar")
            facet_entfernen(seite)

            # Gruppierung nach Status
            if filter_setzen(seite, "Status", bereich=".o_group_by_menu .dropdown-item, .o_dropdown_menu .dropdown-item"):
                inhalt = texte(seite, ".o_list_view .o_group_header", 20)
                pruefe(any("Bestätigt" in t for t in inhalt), "Gruppierung nach Status liefert Gruppen", inhalt[:5])
                schuss("03_gruppierung")
                facet_entfernen(seite)

            # ---------------------------------------------------------- Formular
            seite.goto("%s/odoo/action-%s/%s" % (c["url"], aktion_event, probe["id"]),
                       wait_until="domcontentloaded")
            warte(4)
            labels = texte(seite, ".o_form_view .o_form_label, .o_form_view .o_group label", 80)
            print("  Formularlabels:", labels[:30])
            for lab in ("Kategorie", "Online-Event", "Mindestzahl an Teilnehmern",
                        "Max. Teilnehmeranzahl"):
                pruefe(any(lab == x or x.startswith(lab) for x in labels), "Formularlabel %r" % lab, labels[:20])
            statusbar = texte(seite, ".o_statusbar_status .o_arrow_button", 12)
            pruefe(any("Bestätigt" in s for s in statusbar), "Statusleiste zeigt 'Bestätigt'", statusbar)
            reiter = texte(seite, ".o_notebook .nav-link", 20)
            pruefe(any("Odoo-11-Angaben" in r for r in reiter), "Reiter 'Odoo-11-Angaben' vorhanden", reiter)
            schuss("04_formular")

            if any("Odoo-11-Angaben" in r for r in reiter):
                for el in seite.query_selector_all(".o_notebook .nav-link"):
                    if "Odoo-11-Angaben" in (el.inner_text() or ""):
                        el.click()
                        warte(2)
                        break
                werte = texte(seite, ".o_notebook .tab-pane.active .o_field_widget, .o_notebook .tab-pane.active input", 40)
                print("  Odoo-11-Werte:", werte[:12])
                pruefe(any(str(probe["x_o11_id"]) == w for w in werte),
                       "Odoo-11-ID im Formular sichtbar", werte[:12])
                pruefe(any(str(probe["x_o11_registrations"]) == w for w in werte),
                       "Anzahl Anmeldungen (Odoo 11) sichtbar", werte[:12])
                schuss("05_odoo11_angaben")

            # ---------------------------------------------------------- Kategorien
            seite.goto("%s/odoo/action-%s" % (c["url"], aktion_typ), wait_until="domcontentloaded")
            warte(4)
            zeilen = texte(seite, ".o_list_view tbody tr", 20)
            print("  Anlasskategorien:", zeilen)
            pruefe(len(zeilen) == 2, "2 Anlasskategorien", len(zeilen), 2)
            pruefe(any("Online" in z for z in zeilen), "Kategorie 'Online'", zeilen)
            kopf = texte(seite, ".o_list_view thead th", 10)
            pruefe(any("Anlasskategorie" in s for s in kopf), "Spalte heisst 'Anlasskategorie'", kopf)
            schuss("06_anlasskategorien")

            # ---------------------------------------------------------- Berichtswesen
            seite.goto("%s/odoo/action-%s" % (c["url"], aktion_report), wait_until="domcontentloaded")
            warte(4)
            pivot = seite.query_selector(".o_pivot")
            pruefe(pivot is not None, "Pivot Veranstaltungen rendert", bool(pivot))
            inhalt = texte(seite, ".o_pivot table tr, .o_pivot th", 30)
            print("  Pivot:", inhalt[:10])
            schuss("07_berichtswesen")

            b.close()
    except Exception as exc:  # noqa: BLE001
        fehler.append("Browserlauf: %s" % str(exc)[:300])
        print("FEHLER im Browserlauf:", str(exc)[:300])

    ergebnis["ok"] = ok
    ergebnis["fehler"] = fehler
    with open(os.path.join(a.out, "ergebnis_%s.json" % a.instanz), "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print("\n=== Browserabnahme %s: %d OK / %d FEHLER ===" % (a.instanz, ok, len(fehler)))
    for f in fehler:
        print("   FEHLER:", f)
    return 0 if not fehler else 1


if __name__ == "__main__":
    sys.exit(main())
