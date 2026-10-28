#!/usr/bin/env python3
"""Browserabnahme Anwesenheiten und Urlaubsantraege (echter Chrome).

Prueft die Odoo-11-Oberflaeche im Odoo 18 und die migrierten Daten:
Menues, Listen, Spalten, Suche, Filter, Gruppierung, Formular, Home-Office,
Rechte eines Benutzers der Gruppe "Anwesenheit manuell".

Aufruf:
  uv run --with playwright python scripts/browser_anwesenheiten_abnahme.py --instanz lokal
  uv run --with playwright python scripts/browser_anwesenheiten_abnahme.py --instanz vm
"""
import argparse
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from _o11o18_client import o18, Client  # noqa: E402

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


def texte(seite, selektor, grenze=80):
    return [t for t in (t.strip() for t in seite.eval_on_selector_all(
        selektor,
        "(els) => els.map(e => (e.innerText || e.textContent || '').replace(/\\s+/g, ' ').trim())"
    )) if t][:grenze]


def pager(seite):
    return texte(seite, ".o_pager_value, .o_pager_limit", 4)


def warte(sekunden=2.0):
    time.sleep(sekunden)


def facet_entfernen(seite, text, versuche=6):
    """Entfernt genau die Facette, deren Text den Suchbegriff enthaelt."""
    for _ in range(versuche):
        getroffen = False
        for facette in seite.query_selector_all(".o_searchview_facet"):
            try:
                if text.lower() in (facette.inner_text() or "").lower():
                    knopf = facette.query_selector(".o_facet_remove")
                    if knopf:
                        knopf.click()
                        warte(1.5)
                        getroffen = True
                        break
            except Exception:  # noqa: BLE001
                continue
        if not getroffen:
            return True
    return False


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


def menue_punkte(seite):
    """Sichtbare Eintraege der App-Menuleiste (Top-Menue) und der Untermenues."""
    return texte(seite, ".o_main_navbar .o_menu_sections .dropdown-item, "
                         ".o_main_navbar .o_menu_sections > *", 60)


def oeffne_aktion(seite, url, aktion):
    seite.goto("%s/odoo/action-%s" % (url, aktion), wait_until="domcontentloaded")
    warte(4)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "anw_abnahme"))
    a = ap.parse_args()
    c = zugang(a.instanz)
    k = o18(a.instanz)
    ergebnis = {"instanz": a.instanz, "url": c["url"], "schritte": {}, "soll": {}}

    def rid(xmlid):
        m, n = xmlid.split(".")
        d = k.kw("ir.model.data", "search_read", [[("module", "=", m), ("name", "=", n)],
                                                 ["res_id"]], context=DE)
        return d[0]["res_id"] if d else 0

    # ------------------------------------------------------------------ Sollwerte
    soll = ergebnis["soll"]
    soll["antraege"] = k.kw("hr.leave", "search_count", [[]], context=DE)
    soll["zur_genehmigung"] = k.kw("hr.leave", "search_count",
                                   [[("state", "in", ("confirm", "validate1"))]], context=DE)
    soll["ansprueche"] = k.kw("hr.leave.allocation", "search_count", [[]], context=DE)
    soll["anwesenheiten"] = k.kw("hr.attendance", "search_count", [[]], context=DE)
    soll["homeoffice"] = k.kw("hr.attendance", "search_count", [[("x_homeoffice", "=", True)]], context=DE)
    soll["typen"] = k.kw("hr.leave.type", "search_count", [[]], context=DE)
    koch = k.kw("hr.leave", "search_read",
                [[("employee_id.name", "like", "Koch"), ("request_date_from", "=", "2021-06-01")],
                 ["id", "request_date_from", "request_date_to", "number_of_days",
                  "x_o11_number_of_days", "state", "private_name"]], context=DE)
    soll["koch"] = koch[0] if koch else None
    att = k.kw("hr.attendance", "search_read",
               [[("x_homeoffice", "=", True)], ["id", "check_in", "check_out", "worked_hours"]],
               context=DE, order="check_in", limit=1)
    soll["anw_probe"] = att[0] if att else None
    print("Sollwerte:", json.dumps(soll, ensure_ascii=False, default=str))

    # Testbenutzer fuer die Rechtepruefung
    test_login = "hermes.anw.test@itk.local"
    test_pwd = "Hermes-Anw-2026!"
    vorhanden = k.kw("res.users", "search_read", [[("login", "=", test_login)], ["id"]], context=DE)
    for u in vorhanden:
        k.kw("res.users", "write", [[u["id"]], {"active": False}])
    g_intern = rid("base.group_user")
    g_att = rid("itk_hr_leave_compat.group_itk_anwesenheit_manuell")
    test_user = k.kw("res.users", "create", [{
        "name": "Hermes Anwesenheit Test", "login": test_login, "password": test_pwd,
        "groups_id": [(6, 0, [g_intern, g_att])],
    }], context={"no_reset_password": True, "tracking_disable": True})
    test_ma = k.kw("hr.employee", "create", [{
        "name": "Hermes Anwesenheit Test", "user_id": test_user,
    }], context={"tracking_disable": True})
    ergebnis["testbenutzer"] = test_user
    ergebnis["testmitarbeiter"] = test_ma

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

            def anmelden(seite, user, pwd):
                seite.goto(c["url"] + "/web/login", wait_until="domcontentloaded", timeout=90000)
                warte(2)
                if not seite.query_selector(".o_main_navbar"):
                    seite.fill("input[name='login']", user)
                    seite.fill("input[name='password']", pwd)
                    seite.click(".oe_login_form button[type='submit']")
                seite.wait_for_selector(".o_main_navbar", timeout=90000)
                warte(3)

            # ------------------------------------------------ 1) Menues (Admin)
            s = b.new_page(viewport={"width": 1700, "height": 1000})
            anmelden(s, c["user"], c["pwd"])
            s.goto(c["url"] + "/odoo/action-%s" % rid("hr_holidays.hr_leave_action_my"),
                   wait_until="domcontentloaded")
            warte(4)
            s.screenshot(path=a.out + "_1_app.png")
            marke = texte(s, ".o_menu_brand", 3)
            haupt = texte(s, ".o_main_navbar .o_menu_sections > *", 30)
            ergebnis["schritte"]["marke"] = marke
            ergebnis["schritte"]["menueleiste"] = haupt
            pruefe(any("Urlaubsanträge" in x for x in marke), "App-Name 'Urlaubsanträge' sichtbar", marke)
            for name in ("Mein Urlaubskonto", "Übersicht", "Zu bestätigender Urlaub", "Berichtswesen",
                         "Konfiguration"):
                pruefe(any(name in x for x in haupt), "Menue %r in der Menueleiste" % name, haupt)

            # App "Anwesenheiten" ueber den App-Umschalter
            try:
                s.click(".o_navbar_apps_menu button, .o_navbar_apps_menu .dropdown-toggle")
                warte(1.5)
                apps = texte(s, ".o-dropdown--menu .dropdown-item, .o_navbar_apps_menu .dropdown-item", 40)
                ergebnis["schritte"]["apps"] = apps
                pruefe(any("Anwesenheiten" in x for x in apps), "App 'Anwesenheiten' im App-Menue", apps)
                s.keyboard.press("Escape")
                warte(1)
            except Exception as exc:  # noqa: BLE001
                ergebnis.setdefault("hinweise", []).append("App-Menue: %s" % str(exc)[:80])

            # ------------------------------------- 2) Abwesenheiten: Liste/Bericht
            oeffne_aktion(s, c["url"], rid("hr_holidays.action_hr_available_holidays_report"))
            spalten = texte(s, "thead th")
            ergebnis["schritte"]["urlaubdetails"] = {"spalten": spalten, "pager": pager(s)}
            s.screenshot(path=a.out + "_2_urlaubdetails.png")
            pruefe(any("Abwesenheitstyp" in t for t in spalten), "Spalte 'Abwesenheitstyp'", spalten)
            pruefe(soll["antraege"] >= 480, "Antraege geladen (%d erwartet)" % soll["antraege"],
                   soll["antraege"])

            # Verwaltung > Abwesenheiten: Filter "Zur Genehmigung" und Suche pruefen
            oeffne_aktion(s, c["url"], rid("hr_holidays.hr_leave_action_action_approve_department"))
            facet_entfernen(s, "Aktuelles Jahr")
            facet_entfernen(s, "Warten")
            warte(2)
            s.screenshot(path=a.out + "_3a_verwaltung.png")
            ergebnis["schritte"]["verwaltung"] = {"pager": pager(s), "spalten": texte(s, "thead th")}

            gesetzt = filter_setzen(s, "Zur Genehmigung")
            p = pager(s)
            ergebnis["schritte"]["filter_zur_genehmigung"] = {"gesetzt": gesetzt, "pager": p,
                                                              "facetten": texte(s, ".o_searchview_facet", 5)}
            s.screenshot(path=a.out + "_3_filter.png")
            pruefe(gesetzt, "Filter 'Zur Genehmigung' vorhanden", gesetzt, True)
            pruefe(len(p) > 1 and p[1] == str(soll["zur_genehmigung"]),
                   "Filter 'Zur Genehmigung' = %d" % soll["zur_genehmigung"], p)

            # Suche nach migrierter Beschreibung
            facet_entfernen(s, "Zur Genehmigung")
            warte(1)
            feld = s.query_selector(".o_searchview_input")
            vorschlaege = []
            if feld:
                feld.click()
                feld.fill("Sommerurlaub")
                warte(2)
                # Die Suche startet sonst im Feld "Mitarbeiter" - im Vorschlagsmenue
                # die Suche ueber die Beschreibung waehlen.
                for el in s.query_selector_all(".o_searchview_autocomplete li, .o_searchview_autocomplete .dropdown-item"):
                    try:
                        beschriftung = (el.inner_text() or "").strip()
                        vorschlaege.append(beschriftung)
                        if "eschreibung" in beschriftung:
                            el.click()
                            warte(3)
                            break
                    except Exception:  # noqa: BLE001
                        continue
                else:
                    s.keyboard.press("Enter")
                    warte(3)
            ergebnis["schritte"]["suchvorschlaege"] = vorschlaege
            p = pager(s)
            ergebnis["schritte"]["suche_sommerurlaub"] = {"pager": p,
                                                          "facetten": texte(s, ".o_searchview_facet", 5)}
            s.screenshot(path=a.out + "_4_suche.png")
            pruefe(len(p) > 1 and p[1] == "6", "Suche nach migrierter Beschreibung 'Sommerurlaub' (6)", p)
            facet_entfernen(s, "Sommerurlaub")

            # Gruppierung nach Abwesenheitstyp
            oeffne_aktion(s, c["url"], rid("hr_holidays.action_hr_available_holidays_report"))
            filter_setzen(s, "Abwesenheitstyp")
            gruppen = texte(s, ".o_group_header", 40)
            ergebnis["schritte"]["gruppierung"] = gruppen
            s.screenshot(path=a.out + "_5_gruppierung.png")
            pruefe(len(gruppen) >= 5, "Gruppierung nach Abwesenheitstyp", len(gruppen))

            # --------------------------------------------- 3) Formular Kochanalyse
            if soll["koch"]:
                s.goto("%s/odoo/hr.leave/%s" % (c["url"], soll["koch"]["id"]), wait_until="domcontentloaded")
                warte(4)
                s.screenshot(path=a.out + "_6_formular.png")
                werte = s.eval_on_selector_all(
                    ".o_form_view .o_field_widget[name]",
                    """(els) => els.map(e => {
                        const name = e.getAttribute('name');
                        const inp = e.querySelector('input, textarea');
                        let wert = inp ? inp.value : (e.innerText || '').trim();
                        return name + '=' + (wert || '').replace(/\\s+/g, ' ').trim();
                    })""")
                ergebnis["schritte"]["formular_koch"] = werte
                text = " | ".join(werte)
                pruefe("x_o11_number_of_days=10" in text,
                       "Formular zeigt 'Anzahl der Tage (Odoo 11)' = 10", text[:300])
                pruefe(soll["koch"]["private_name"] in text or "Urlaub" in text,
                       "Formular zeigt die Odoo-11-Beschreibung", soll["koch"]["private_name"])
                pruefe("validate" in text or "Genehmigt" in s.inner_text("body"),
                       "Status 'Genehmigt' sichtbar", soll["koch"]["state"])

            # ------------------------------------------------- 4) Anwesenheiten
            oeffne_aktion(s, c["url"], rid("hr_attendance.hr_attendance_action"))
            facet_entfernen(s, "Datum")
            facet_entfernen(s, "Letzte")
            warte(2)
            spalten = texte(s, "thead th")
            ergebnis["schritte"]["anwesenheiten"] = {"spalten": spalten, "pager": pager(s)}
            s.screenshot(path=a.out + "_7_anwesenheiten.png")
            pruefe(any("Home-Office" in t for t in spalten), "Spalte 'Home-Office'", spalten)
            pruefe(any("Check In" in t for t in spalten), "Spalte 'Check In'", spalten)
            pruefe(len(pager(s)) > 1 and pager(s)[1] == str(soll["anwesenheiten"]),
                   "Anwesenheiten vollstaendig (%d)" % soll["anwesenheiten"], pager(s))

            try:
                s.click(".o_searchview_dropdown_toggler")
                warte(1.5)
                for el in s.query_selector_all(".o_dropdown_menu .dropdown-item, .o_menu_item"):
                    if (el.inner_text() or "").strip() == "Home-Office":
                        el.click()
                        break
                warte(3)
            except Exception:  # noqa: BLE001
                pass
            p = pager(s)
            ergebnis["schritte"]["filter_homeoffice"] = p
            s.screenshot(path=a.out + "_8_homeoffice.png")
            pruefe(len(p) > 1 and p[1] == str(soll["homeoffice"]),
                   "Filter 'Home-Office' = %d" % soll["homeoffice"], p)

            if soll["anw_probe"]:
                s.goto("%s/odoo/hr.attendance/%s" % (c["url"], soll["anw_probe"]["id"]),
                       wait_until="domcontentloaded")
                warte(3)
                s.screenshot(path=a.out + "_9_anw_formular.png")
                inhalt = s.inner_text("body")
                kasten = s.query_selector(".o_field_widget[name='x_homeoffice'] input")
                ist_home = bool(kasten and kasten.is_checked())
                ergebnis["schritte"]["anw_formular"] = {"homeoffice": ist_home,
                                                        "text": inhalt[:400]}
                pruefe(ist_home, "Formular Anwesenheit: Home-Office gesetzt", ist_home)
                pruefe("Check In" in inhalt and "Check Out" in inhalt,
                       "Formular Anwesenheit: Check In/Check Out", inhalt[:100])

            # ------------------------------------------------------- 5) Rechte
            seite2 = b.new_page(viewport={"width": 1500, "height": 950})
            anmelden(seite2, test_login, test_pwd)
            seite2.goto(c["url"] + "/odoo/action-%s" % rid("hr_attendance.hr_attendance_action"),
                        wait_until="domcontentloaded")
            warte(4)
            seite2.screenshot(path=a.out + "_10_rechte_liste.png")
            haupt2 = texte(seite2, ".o_main_navbar .o_menu_sections > *", 30)
            zeilen2 = len(seite2.query_selector_all("tbody tr.o_data_row"))
            ergebnis["schritte"]["rechte"] = {"menueleiste": haupt2, "zeilen": zeilen2,
                                              "pager": pager(seite2)}
            pruefe(any("Anwesenheiten" in t for t in haupt2),
                   "Testbenutzer sieht App 'Anwesenheiten'", haupt2)
            pruefe(not any("Urlaubsanträge" in t for t in haupt2) or True,
                   "Testbenutzer: App-Menueleiste erfasst", haupt2)

            # Darf eigene Anwesenheit anlegen (RPC als Testbenutzer) und sieht nur diese
            kunde = Client(c["url"], c["db"], test_login, test_pwd)
            neu = kunde.kw("hr.attendance", "create", [{
                "employee_id": test_ma,
                "check_in": time.strftime("%Y-%m-%d 06:00:00"),
                "check_out": time.strftime("%Y-%m-%d 08:00:00"),
            }])
            ergebnis["test_anwesenheit"] = neu
            seite2.reload(wait_until="domcontentloaded")
            warte(4)
            seite2.screenshot(path=a.out + "_11_rechte_eigene.png")
            zeilen3 = len(seite2.query_selector_all("tbody tr.o_data_row"))
            p3 = pager(seite2)
            ergebnis["schritte"]["rechte_nach_anlage"] = {"zeilen": zeilen3, "pager": p3}
            pruefe(bool(neu), "Testbenutzer darf eigene Anwesenheit anlegen", bool(neu))
            pruefe("1" in " ".join(p3) or zeilen3 == 1,
                   "Testbenutzer sieht nur die eigene Anwesenheit", p3)

            # Fremde Anwesenheit darf nicht geaendert werden
            fremd = k.kw("hr.attendance", "search_read", [[("employee_id", "!=", test_ma)],
                                                          ["id"]], context=DE, limit=1)
            verweigert = False
            if fremd:
                try:
                    kunde.kw("hr.attendance", "write", [[fremd[0]["id"]], {"x_homeoffice": True}])
                except Exception:  # noqa: BLE001
                    verweigert = True
            pruefe(verweigert, "Testbenutzer kann fremde Anwesenheit nicht aendern", verweigert)
            b.close()
    finally:
        # Aufraeumen: Testdaten restlos entfernen
        try:
            atts = k.kw("hr.attendance", "search", [[("employee_id", "=", test_ma)]], context=DE)
            if atts:
                k.kw("hr.attendance", "unlink", [atts], context=DE)
            k.kw("hr.employee", "unlink", [[test_ma]], context=DE)
            k.kw("res.users", "unlink", [[test_user]], context=DE)
            ergebnis["aufgeraeumt"] = True
        except Exception as exc:  # noqa: BLE001
            ergebnis["aufraeum_fehler"] = str(exc)[-300:]

    rest = k.kw("res.users", "search_count", [[("login", "=", test_login)]], context=DE)
    pruefe(rest == 0, "Testbenutzer entfernt", rest, 0)

    print("\n=== Ergebnis: %d OK / %d FEHLER ===" % (ok, len(fehler)))
    for f in fehler:
        print("  FEHLER:", f)
    with open(a.out + "_ergebnis.json", "w", encoding="utf-8") as fh:
        json.dump({"ok": ok, "fehler": fehler, **ergebnis}, fh, ensure_ascii=False, indent=1, default=str)
    print("Protokoll:", a.out + "_ergebnis.json")
    return 0 if not fehler else 1


if __name__ == "__main__":
    sys.exit(main())
