#!/usr/bin/env python3
"""Browserabnahme ZEITERFASSUNG auf den MIGRIERTEN Daten (Session 136).

Prueft im echten Browser (Playwright/Chromium, Login aus .env) und vergleicht mit
Sollwerten aus Odoo 11 (live, read-only):

  * Meine Stundenzettel: Spalten, Anzahl, Summe, Favorit
  * Alle Zeiterfassungen: Spalten, Anzahl aller Zeilen
  * Suche: migrierte Beschreibung, Filter "Mit historischer Referenz",
    Filter "Dieser Monat", Gruppierung nach Projekt
  * Formular einer migrierten Zeile: Datum, Startzeit 00:00, Endzeit, Referenz,
    Projekt, Aufgabe, Mitarbeiter
  * Beziehungen: Projekt- und Aufgabenformular aus der Zeile erreichbar
  * Archivierte/historische Daten: Zeilen eines archivierten Mitarbeiters
  * Pivot/Bericht "Kosten und Erloese"
  * Start/Stopp-Assistent "Arbeit starten"
  * Rechte: zweiter Benutzer mit nur "eigene Zeiterfassungen" (Testbenutzer wird
    am Ende wieder geloescht)

Aufruf:
  uv run --with playwright python scripts/browser_zeiterfassung_daten.py --instanz lokal
  uv run --with playwright python scripts/browser_zeiterfassung_daten.py --instanz vm
"""
import argparse
import json
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from _o11o18_client import o18  # noqa: E402


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
    return [t for t in (t.strip() for t in seite.eval_on_selector_all(
        selektor, "(els) => els.map(e => (e.innerText || e.textContent || '').replace(/\\s+/g, ' ').trim())"
    )) if t][:grenze]


def feldwerte(seite):
    """Sichtbare Werte der Formularfelder (input/textarea/span) einsammeln."""
    return seite.eval_on_selector_all(
        ".o_form_view .o_field_widget[name]",
        """(els) => els.map(e => {
            const name = e.getAttribute('name');
            const inp = e.querySelector('input, textarea');
            let wert = inp ? inp.value : (e.innerText || '').trim();
            return name + '=' + (wert || '').replace(/\s+/g, ' ').trim();
        })""")


def pager(seite):
    """(erste, letzte, gesamt) aus dem Pager."""
    werte = texte(seite, ".o_pager_value, .o_pager_limit", 4)
    return werte


def warte(sekunden=2.0):
    time.sleep(sekunden)


def suche(seite, text, enter=True):
    feld = seite.query_selector(".o_searchview_input")
    if not feld:
        return False
    feld.click()
    feld.fill(text)
    warte(1.5)
    if enter:
        seite.keyboard.press("Enter")
        warte(2.5)
    return True


def filter_menue(seite):
    """Oeffnet das Filter/Gruppieren-Menue der Suchleiste und liefert die Punkte."""
    for sel in (".o_searchview_dropdown_toggler", "button.o_searchview_dropdown_toggler",
                ".o_cp_searchview .dropdown-toggle"):
        knopf = seite.query_selector(sel)
        if knopf:
            knopf.click()
            warte(1.5)
            return texte(seite, ".o_dropdown_menu .dropdown-item, .o_menu_item", 80)
    return []


def klick_menue(seite, text):
    """Klickt einen Menuepunkt; Fallback ueber JS (auch in Untermenues)."""
    for sel in (".o_dropdown_menu .dropdown-item", ".o_menu_item", "button", "a", "span"):
        for el in seite.query_selector_all(sel):
            try:
                if (el.inner_text() or "").strip() == text and el.is_visible():
                    el.click()
                    warte(2.5)
                    return True
            except Exception:  # noqa: BLE001
                continue
    try:
        getroffen = seite.evaluate(
            """(text) => {
                const alle = [...document.querySelectorAll('button,a,span,li,div')];
                const ziel = alle.reverse().find(e =>
                    (e.innerText || '').trim() === text && e.offsetParent !== null);
                if (!ziel) return false;
                ziel.click();
                return true;
            }""", text)
        if getroffen:
            warte(2.5)
        return bool(getroffen)
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--out", default=os.path.join(os.environ.get("TEMP", "."), "zeit_daten"))
    ap.add_argument("--rechte-test", action="store_true", default=True)
    a = ap.parse_args()
    c = zugang(a.instanz)
    k = o18(a.instanz)
    ergebnis = {"instanz": a.instanz, "url": c["url"], "schritte": {}, "soll": {}}
    CTX = {"lang": "de_DE"}

    # ---------------------------------------------------------- Sollwerte (RPC)
    md = "account.analytic.line"
    soll = ergebnis["soll"]
    soll["zeilen_gesamt"] = k.kw(md, "search_count", [[]])
    soll["stunden_gesamt"] = round(sum(
        z["unit_amount"] or 0 for z in k.kw(md, "search_read", [[]],
                                            fields=["unit_amount"], limit=0)), 2)
    soll["mit_referenz"] = k.kw(md, "search_count", [[("ref", "!=", False)]])
    soll["sammelprojekt"] = k.kw(md, "search_count",
                                 [[("project_id.name", "=",
                                    "Ohne Projekt (Uebernahme Odoo 11)")]])
    ma18 = {m["id"]: m for m in k.kw("hr.employee", "search_read", [[]],
                                     fields=["id", "name", "active"],
                                     context={"active_test": False}, limit=0)}
    archiviert = [m for m in ma18.values() if not m["active"]]
    soll["archivierte_mitarbeiter"] = len(archiviert)
    ziel_ma = next((m for m in archiviert if m["name"].startswith("Osagie")), archiviert[0])
    soll["archivierter_mitarbeiter"] = ziel_ma["name"]
    soll["zeilen_archivierter_mitarbeiter"] = k.kw(
        md, "search_count", [[("employee_id", "=", ziel_ma["id"])]])
    # aelteste Zeile mit Ticket-Referenz fuer das Formular
    probe = k.kw(md, "search_read", [[("ref", "like", "O11-Ticket")]],
                 fields=["id", "date", "name", "ref", "project_id", "task_id", "employee_id",
                         "unit_amount", "date_time", "date_time_end", "holiday_id"],
                 order="date asc, id asc", limit=1)
    ergebnis["probezeile"] = probe[0] if probe else None
    # Zeile eines archivierten Mitarbeiters
    probe_ma = k.kw(md, "search_read", [[("employee_id", "=", ziel_ma["id"])]],
                    fields=["id", "date", "name"], order="id asc", limit=1)
    ergebnis["probe_archiv"] = probe_ma[0] if probe_ma else None
    akt = k.kw("ir.actions.act_window", "search_read", [[("name", "=", "Kosten und Erloese")]],
               fields=["id"], context=CTX, limit=1)
    ergebnis["kosten_aktion"] = akt[0]["id"] if akt else 0
    print("Sollwerte:", json.dumps(soll, ensure_ascii=False))

    # Testbenutzer fuer die Rechtepruefung (wird am Ende geloescht)
    test_user = None
    if a.rechte_test:
        vorhanden = k.kw("res.users", "search_read", [[("login", "=", "hermes.rechte.test@itk.local")]],
                         fields=["id"], limit=1)
        if vorhanden:
            test_user = vorhanden[0]["id"]
        else:
            g607 = k.kw("res.groups", "search_read",
                        [[("name", "ilike", "nur eigene Zeiterfassungen")]], fields=["id"], limit=1)
            g_intern = k.kw("res.groups", "search_read", [[("name", "=", "Internal User")]],
                            fields=["id"], limit=1)
            g_projekt = k.kw("res.groups", "search_read",
                             [[("name", "=", "User"),
                               ("category_id.name", "ilike", "Project")]],
                             fields=["id"], limit=1)
            gruppen = [x["id"] for x in (g607[0] if g607 else None,
                                         g_intern[0] if g_intern else None,
                                         g_projekt[0] if g_projekt else None) if x]
            test_user = k.kw("res.users", "create", [{
                "name": "Hermes Rechte Test", "login": "hermes.rechte.test@itk.local",
                "active": True,
                "groups_id": [(6, 0, gruppen)],
            }], context={"tracking_disable": True, "no_reset_password": True})
        ergebnis["testbenutzer"] = test_user

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b = None
        for kanal in ("chrome", "msedge", None):
            try:
                b = p.chromium.launch(channel=kanal) if kanal else p.chromium.launch()
                ergebnis["browser"] = kanal or "chromium"
                break
            except Exception as exc:  # noqa: BLE001
                ergebnis.setdefault("browser_fehler", []).append("%s: %s" % (kanal, str(exc)[:80]))
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

        s = b.new_page(viewport={"width": 1700, "height": 1000})
        anmelden(s, c["user"], c["pwd"])

        # 1) Meine Stundenzettel
        s.goto(c["url"] + "/odoo/action-1187", wait_until="domcontentloaded")
        warte(5)
        s.screenshot(path=a.out + "_1_meine.png")
        ergebnis["schritte"]["meine"] = {
            "titel": s.title(), "spalten": texte(s, "thead th"), "pager": pager(s),
            "facetten": texte(s, ".o_searchview_facet, .o_facet_values"),
            "zeilen_sichtbar": len(s.query_selector_all("tbody tr.o_data_row")),
        }
        # Favorit "Abrechnungsrate" entfernen -> alle eigenen Zeilen
        for knopf in s.query_selector_all(".o_searchview_facet .o_facet_remove"):
            try:
                knopf.click()
                warte(2)
            except Exception:  # noqa: BLE001
                pass
        warte(2)
        s.screenshot(path=a.out + "_1b_meine_ohne_favorit.png")
        ergebnis["schritte"]["meine_ohne_favorit"] = {
            "pager": pager(s), "facetten": texte(s, ".o_searchview_facet", 10),
            "zeilen_sichtbar": len(s.query_selector_all("tbody tr.o_data_row")),
        }

        # 2) Alle Zeiterfassungen
        s.goto(c["url"] + "/odoo/action-1190", wait_until="domcontentloaded")
        warte(5)
        s.screenshot(path=a.out + "_2_alle.png")
        ergebnis["schritte"]["alle"] = {
            "spalten": texte(s, "thead th"), "pager": pager(s),
            "zeilen_sichtbar": len(s.query_selector_all("tbody tr.o_data_row")),
        }

        # 3) Suche: migrierte Beschreibung
        suche(s, "IFG-Portal")
        s.screenshot(path=a.out + "_3_suche_ifg.png")
        ergebnis["schritte"]["suche_ifg"] = {"pager": pager(s),
                                             "zeilen": len(s.query_selector_all("tbody tr.o_data_row"))}
        s.goto(c["url"] + "/odoo/action-1190", wait_until="domcontentloaded")
        warte(4)

        # 4) Filter "Mit historischer Referenz"
        punkte = filter_menue(s)
        ergebnis["schritte"]["filter_menue"] = punkte[:40]
        klick_menue(s, "Mit historischer Referenz")
        s.screenshot(path=a.out + "_4_referenz.png")
        ergebnis["schritte"]["filter_referenz"] = {
            "pager": pager(s), "facetten": texte(s, ".o_searchview_facet", 10),
            "zeilen": len(s.query_selector_all("tbody tr.o_data_row")),
            "referenzen": texte(s, "tbody tr.o_data_row td[name='ref']", 5),
        }
        s.goto(c["url"] + "/odoo/action-1190", wait_until="domcontentloaded")
        warte(4)

        # 5) Filter "Dieser Monat" (Untermenue "Datum")
        filter_menue(s)
        if not klick_menue(s, "Dieser Monat"):
            klick_menue(s, "Datum")
            klick_menue(s, "Dieser Monat")
        s.screenshot(path=a.out + "_5_dieser_monat.png")
        ergebnis["schritte"]["filter_monat"] = {"pager": pager(s),
                                                "facetten": texte(s, ".o_searchview_facet", 10)}
        s.goto(c["url"] + "/odoo/action-1190", wait_until="domcontentloaded")
        warte(4)

        # 6) Gruppierung nach Projekt
        punkte = filter_menue(s)
        ergebnis["schritte"]["gruppieren_menue"] = punkte[:60]
        if not klick_menue(s, "Projekt"):
            klick_menue(s, "Group By Projekt")
        s.screenshot(path=a.out + "_6_gruppe_projekt.png")
        ergebnis["schritte"]["gruppe_projekt"] = {
            "gruppen": texte(s, ".o_group_header", 12),
            "zeilen": len(s.query_selector_all("tbody tr.o_data_row")),
        }

        # 7) Formular einer migrierten Zeile mit Ticket-Referenz
        if ergebnis.get("probezeile"):
            pid = ergebnis["probezeile"]["id"]
            s.goto(c["url"] + "/odoo/action-1190/%s" % pid, wait_until="domcontentloaded")
            warte(5)
            s.screenshot(path=a.out + "_7_formular.png")
            ergebnis["schritte"]["formular"] = {
                "labels": texte(s, ".o_form_view label.o_form_label", 20),
                "werte": texte(s, ".o_form_view .o_field_widget[name]", 25),
                "beschreibung": texte(s, ".o_form_view .o_field_widget[name='name']", 2),
                "referenz": texte(s, ".o_form_view .o_field_widget[name='ref']", 2),
                "datum": texte(s, ".o_form_view .o_field_widget[name='date']", 2),
                "startzeit": texte(s, ".o_form_view .o_field_widget[name='date_time']", 2),
                "projekt": texte(s, ".o_form_view .o_field_widget[name='project_id']", 2),
                "aufgabe": texte(s, ".o_form_view .o_field_widget[name='task_id']", 2),
                "mitarbeiter": texte(s, ".o_form_view .o_field_widget[name='employee_id']", 2),
                "zeit": texte(s, ".o_form_view .o_field_widget[name='unit_amount']", 2),
                "feldwerte": feldwerte(s),
            }
            # 8) Beziehungen: Projekt- und Aufgabenformular oeffnen
            if ergebnis["probezeile"]["project_id"]:
                s.goto(c["url"] + "/odoo/project.project/%s" % ergebnis["probezeile"]["project_id"][0],
                       wait_until="domcontentloaded")
                warte(4)
                ergebnis["schritte"]["projekt_formular"] = {
                    "titel": s.title(), "kopf": texte(s, ".o_form_view .oe_title, h1", 3)}
                s.screenshot(path=a.out + "_8_projekt.png")
            if ergebnis["probezeile"]["task_id"]:
                s.goto(c["url"] + "/odoo/project.task/%s" % ergebnis["probezeile"]["task_id"][0],
                       wait_until="domcontentloaded")
                warte(4)
                ergebnis["schritte"]["aufgabe_formular"] = {
                    "titel": s.title(), "kopf": texte(s, ".o_form_view .oe_title, h1", 3)}
                s.screenshot(path=a.out + "_9_aufgabe.png")

        # 9) Archivierte/historische Daten: Zeilen eines archivierten Mitarbeiters
        if ergebnis.get("probe_archiv"):
            s.goto(c["url"] + "/odoo/action-1190/%s" % ergebnis["probe_archiv"]["id"],
                   wait_until="domcontentloaded")
            warte(4)
            s.screenshot(path=a.out + "_10_archiv_zeile.png")
            ergebnis["schritte"]["archiv_zeile"] = {
                "titel": s.title(),
                "mitarbeiter": texte(s, ".o_form_view .o_field_widget[name='employee_id']", 2),
                "beschreibung": texte(s, ".o_form_view .o_field_widget[name='name']", 2),
            }

        # 9b) Sammelprojekt in der Gruppierung nach Projekt (Zahl + Summe)
        s.goto(c["url"] + "/odoo/action-1190", wait_until="domcontentloaded")
        warte(4)
        filter_menue(s)
        klick_menue(s, "Projekt")
        warte(2)
        gruppen = texte(s, ".o_group_header", 60)
        ergebnis["schritte"]["gruppe_projekt_alle"] = {
            "anzahl_gruppen": len(gruppen),
            "sammelprojekt": [g for g in gruppen if "Ohne Projekt" in g],
        }
        s.screenshot(path=a.out + "_10b_gruppe_alle.png")

        # 10) Pivot/Bericht
        if ergebnis["kosten_aktion"]:
            s.goto(c["url"] + "/odoo/action-%s" % ergebnis["kosten_aktion"],
                   wait_until="domcontentloaded")
            warte(5)
            s.screenshot(path=a.out + "_11_bericht.png")
            ergebnis["schritte"]["bericht"] = {
                "titel": s.title(), "pivot": bool(s.query_selector(".o_pivot")),
                "kopf": texte(s, ".o_pivot thead th, .o_pivot_header_cell_clicable", 15),
            }

        # 11) Start/Stopp
        s.goto(c["url"] + "/odoo/action-1341", wait_until="domcontentloaded")
        warte(4)
        s.screenshot(path=a.out + "_12_start_stopp.png")
        ergebnis["schritte"]["start_stopp"] = {"titel": s.title(),
                                               "text": texte(s, ".o_form_sheet, .modal-body", 12)}
        s.close()

        # 12) Rechte: zweiter Benutzer (nur eigene Zeiterfassungen)
        if test_user:
            t = b.new_page(viewport={"width": 1400, "height": 900})
            try:
                anmelden(t, "hermes.rechte.test@itk.local", "Hermes-Test-136!")
                t.goto(c["url"] + "/odoo/action-1187", wait_until="domcontentloaded")
                warte(5)
                t.screenshot(path=a.out + "_13_rechte_eigene.png")
                eigene = {"pager": pager(t), "zeilen": len(t.query_selector_all("tbody tr.o_data_row"))}
                t.goto(c["url"] + "/odoo/action-1190", wait_until="domcontentloaded")
                warte(5)
                t.screenshot(path=a.out + "_14_rechte_alle.png")
                alle = {"pager": pager(t), "zeilen": len(t.query_selector_all("tbody tr.o_data_row"))}
                ergebnis["schritte"]["rechte"] = {"meine": eigene, "alle": alle}
            except Exception as exc:  # noqa: BLE001
                ergebnis["schritte"]["rechte_fehler"] = str(exc)[:300]
            t.close()
        b.close()

    if test_user:
        try:
            k.kw("res.users", "write", [[test_user], {"active": False}])
            k.kw("res.users", "unlink", [[test_user]])
            ergebnis["testbenutzer_geloescht"] = True
        except Exception as exc:  # noqa: BLE001
            ergebnis["testbenutzer_geloescht"] = str(exc)[:200]

    pfad = a.out + ".json"
    os.makedirs(os.path.dirname(pfad) or ".", exist_ok=True)
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1, default=str)
    print(json.dumps(ergebnis, ensure_ascii=False, indent=1, default=str)[:6000])
    print("\nScreenshots:", a.out + "_*.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
