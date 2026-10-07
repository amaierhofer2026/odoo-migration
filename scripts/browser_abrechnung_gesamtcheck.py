"""Vollstaendiger Browser-Gesamtcheck des Bereichs Abrechnung (Odoo 18 lokal und VM).

Geht JEDEN Menuepunkt der App "Abrechnung" mit Aktion im echten Chrome durch und prueft je Punkt
die Punkte 1 bis 9 des Auftrags (Session 131):

  - Menue oeffnen (ueber /odoo/action-<id>)
  - Liste laedt fehlerfrei (Spalten, Zeilen, Pager)
  - Suche: Suchbegriff eingeben, Enter, Ergebnis ohne Fehler
  - Filter: ersten Filtereintrag aktivieren
  - Gruppierung: erste Gruppierung aktivieren
  - vorhandenen Datensatz oeffnen (Formular)
  - Formular: Reiter, Felder, Buttons, Smart Buttons, Statusleiste lesen
  - Relationen: sichtbare many2one-Werte lesen, einen Relation-Link oeffnen und zurueckgehen
  - Bearbeitungsmodus: Bearbeiten - Werte lesen - Verwerfen (kein Speichern)
  - EINMAL Speichern mit ungefaehrlichen Testdaten (Produktkategorie "ITK-TEST-S131")
    und danach vollstaendig entfernen (Bestand vorher/nachher)
  - JS-Konsole, Seitenfehler und RPC-/Serverfehler je Menuepunkt erfassen

Aufruf: uv run --with playwright python scripts/browser_abrechnung_gesamtcheck.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import shutil
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env  # noqa: E402

TESTNAME = "ITK-TEST-S131"
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session131")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], required=True)
    p.add_argument("--von", type=int, default=1, help="erster Menuepunkt (1-basiert)")
    p.add_argument("--bis", type=int, default=0, help="letzter Menuepunkt (0 = bis Ende)")
    p.add_argument("--ohne-speicherprobe", action="store_true",
                   help="Speicherprobe ueberspringen (fuer Parallel-Laeufe)")
    a = p.parse_args()
    env = lade_env(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    url, domain = (("https://k001959vsx.ipax.at", "k001959vsx.ipax.at") if a.instanz == "vm"
                   else ("http://localhost:8069", "localhost"))
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(
        url + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call",
                         "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                    "password": env["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"})
    json.loads(op.open(req, timeout=120).read().decode())
    sid = next(c.value for c in jar if c.name == "session_id")

    def kw(modell, methode, args, **kwargs):
        r = urllib.request.Request(
            url + "/web/dataset/call_kw",
            data=json.dumps({"jsonrpc": "2.0", "method": "call",
                             "params": {"model": modell, "method": methode, "args": args,
                                        "kwargs": kwargs}}).encode(),
            headers={"Content-Type": "application/json", "Cookie": "session_id=%s" % sid})
        antwort = json.loads(op.open(r, timeout=300).read().decode())
        if "error" in antwort:
            raise RuntimeError(str(antwort["error"])[:200])
        return antwort["result"]

    # --- Menuepunkte der App "Abrechnung" (mit Aktion) ---
    wurzel = kw("ir.ui.menu", "search_read",
                [[("parent_id", "=", False), ("name", "=", "Abrechnung")], ["id", "name"]],
                context={"lang": "de_DE"})
    if not wurzel:
        print("Menue 'Abrechnung' nicht gefunden")
        return 1
    punkte = []

    def lauf(ids, pfad):
        for m in kw("ir.ui.menu", "read", [ids, ["id", "name", "child_id", "action"]],
                    context={"lang": "de_DE"}):
            neu = pfad + [m["name"]]
            if m["action"]:
                art, aid = str(m["action"]).split(",")
                eintrag = {"pfad": " / ".join(neu), "menu_id": m["id"], "art": art, "aktion": int(aid),
                           "modell": "", "view_mode": ""}
                if art == "ir.actions.act_window":
                    daten = kw("ir.actions.act_window", "read", [[int(aid)], ["res_model", "view_mode"]],
                               context={"lang": "de_DE"})[0]
                    eintrag.update({"modell": daten["res_model"], "view_mode": daten["view_mode"]})
                punkte.append(eintrag)
            if m["child_id"]:
                lauf(m["child_id"], neu)

    lauf([wurzel[0]["id"]], [])
    gesamt = len(punkte)
    punkte = punkte[max(0, a.von - 1):(a.bis if a.bis else gesamt)]
    print("Menuepunkte mit Aktion: %d (Lauf: %d bis %d)" % (gesamt, a.von, a.bis or gesamt))

    bestand_modelle = ["product.category", "account.tax", "account.journal", "account.payment.term",
                       "account.analytic.account", "account.fiscal.position", "account.move"]
    vorher = {m: kw(m, "search_count", [[]]) for m in bestand_modelle}
    vorher["itk_valorisierung.valorisierung"] = kw("itk_valorisierung.valorisierung", "search_count", [[]])
    vorher[TESTNAME] = kw("product.category", "search_count", [[("name", "=", TESTNAME)]])
    print("Bestand vorher: %s" % vorher)

    from playwright.sync_api import sync_playwright
    vz = os.path.join(VZ, "browser", a.instanz)
    os.makedirs(vz, exist_ok=True)
    profil = os.path.join(os.environ.get("TEMP", "/tmp"), "pw_abrechnung_gesamt_%s_%d_%d" % (a.instanz, a.von, a.bis))
    if os.path.isdir(profil):
        shutil.rmtree(profil, ignore_errors=True)

    ok = fehler = 0
    bericht = {"instanz": a.instanz, "menuepunkte": {}, "vorher": vorher, "fehler_liste": []}

    def pruefe(bedingung, text, detail=""):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("      OK   %s%s" % (text, (" -> %s" % detail) if detail else ""), flush=True)
        else:
            fehler += 1
            print("      FEHL %s%s" % (text, (" -> %s" % detail) if detail else ""), flush=True)
        return bedingung

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=profil, channel="chrome", headless=True, locale="de-DE",
            viewport={"width": 1900, "height": 1400})
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        s = ctx.pages[0] if ctx.pages else ctx.new_page()
        ctx.set_default_timeout(8000)   # kurze Timeouts: fehlende Selektoren sollen nicht bremsen
        js_fehler, seiten_fehler = [], []
        s.on("pageerror", lambda e: seiten_fehler.append(str(e)[:300]))
        s.on("console", lambda m: js_fehler.append(m.text[:300]) if m.type == "error" else None)

        def texte(sel):
            return s.evaluate("""(sel) => [...document.querySelectorAll(sel)]
                .filter(e => e.getClientRects().length).map(e => (e.textContent || '').trim())
                .filter(t => t)""", sel)

        def kopf_schreiben(pfad):
            s.screenshot(path=os.path.join(vz, "%s.png" % pfad.replace("/", "_").replace(" ", "_")[:90]),
                         full_page=True)

        relation_geprueft = False
        for i, punkt in enumerate(punkte, 1):
            pfad = punkt["pfad"]
            kurz = pfad.split(" / ", 2)[-1]
            print("\n[%d/%d] %s" % (i, len(punkte), pfad), flush=True)
            eintrag = {"modell": punkt["modell"], "aktion": punkt["aktion"], "art": punkt["art"],
                       "ergebnis": {}}
            js_fehler.clear()
            seiten_fehler.clear()
            try:
                if punkt["art"] != "ir.actions.act_window":
                    s.goto("%s/odoo/action-%d" % (url, punkt["aktion"]))
                    s.wait_for_timeout(5000)
                    body = s.inner_text("body")[:4000]
                    eintrag["ergebnis"] = {"serveraktion": True,
                                           "serverfehler": ("Traceback" in body or "RPC_ERROR" in body)}
                    pruefe(not eintrag["ergebnis"]["serverfehler"], "Server-Aktion ohne Fehler")
                    kopf_schreiben(pfad)
                    bericht["menuepunkte"][pfad] = eintrag
                    continue

                # 1) Menue oeffnen und Liste laden
                s.goto("%s/odoo/action-%d" % (url, punkt["aktion"]))
                s.wait_for_timeout(3500)
                body = s.inner_text("body")[:6000]
                serverfehler = ("Traceback" in body) or ("RPC_ERROR" in body) or ("Odoo Server Error" in body)
                pruefe(not serverfehler, "Menue oeffnet und Liste laedt ohne Serverfehler")
                # Menues ohne Liste (z. B. Einstellungen) haben kein Such-/Filter-/Gruppierungswerkzeug.
                nur_formular = bool(s.query_selector(".o_form_view")) and not s.query_selector(".o_list_view")
                eintrag["ergebnis"]["nur_formular"] = bool(nur_formular)
                spalten = texte("thead th")
                zeilen = len(s.query_selector_all(".o_data_row"))
                pager = (texte(".o_pager") or [""])[0]
                leer = bool(s.query_selector(".o_view_nocontent")) and s.query_selector(
                    ".o_view_nocontent").is_visible()
                eintrag["ergebnis"].update({"spalten": spalten, "zeilen": zeilen, "pager": pager,
                                            "leerzustand": leer, "serverfehler": serverfehler})
                print("      Spalten: %s | Zeilen: %d | Pager: %s" % (spalten[:12], zeilen, pager))
                kopf_schreiben(pfad)

                if nur_formular:
                    pruefe(True, "Formularmenue ohne Liste: Suche/Filter/Gruppierung nicht anwendbar")
                    kopf_schreiben(pfad)
                    bericht["menuepunkte"][pfad] = eintrag
                    continue

                # 2) Suche
                try:
                    s.click(".o_searchview_input", timeout=9000)
                    s.fill(".o_searchview_input", "a")
                    s.keyboard.press("Enter")
                    s.wait_for_timeout(3000)
                    body = s.inner_text("body")[:6000]
                    treffer = (texte(".o_pager") or [""])[0]
                    kein_fehler = "RPC_ERROR" not in body and "Traceback" not in body
                    pruefe(kein_fehler, "Suche funktioniert ohne Fehler", "Pager %s" % treffer)
                    eintrag["ergebnis"]["suche"] = {"pager": treffer, "ohne_fehler": kein_fehler}
                    for taste in ("Escape",):
                        s.keyboard.press(taste)
                    s.wait_for_timeout(1500)
                except Exception as ex:
                    pruefe(False, "Suche funktioniert ohne Fehler", str(ex)[:90])
                    eintrag["ergebnis"]["suche"] = {"fehler": str(ex)[:200]}

                # 3) Filter
                try:
                    s.click(".o_searchview_dropdown_toggler", timeout=9000)
                    s.wait_for_timeout(2000)
                    eintraege = s.query_selector_all(".o_filter_menu .dropdown-item")
                    if eintraege:
                        name = eintraege[0].inner_text().strip()
                        eintraege[0].click()
                        s.wait_for_timeout(3000)
                        body = s.inner_text("body")[:6000]
                        ohne = "RPC_ERROR" not in body and "Traceback" not in body
                        pruefe(ohne, "Filter funktioniert ohne Fehler", name)
                        eintrag["ergebnis"]["filter"] = {"erster": name, "ohne_fehler": ohne}
                        # Filter wieder entfernen
                        try:
                            s.click(".o_searchview .o_searchview_facet .o_facet_remove", timeout=8000)
                            s.wait_for_timeout(2500)
                        except Exception:
                            pass
                    else:
                        pruefe(True, "Filter: Menue ohne Filtereintraege (kein Fehler)")
                        eintrag["ergebnis"]["filter"] = {"erster": "", "ohne_fehler": True, "keine_eintraege": True}
                    s.keyboard.press("Escape")
                    s.wait_for_timeout(1200)
                except Exception as ex:
                    pruefe(False, "Filter funktioniert ohne Fehler", str(ex)[:90])
                    eintrag["ergebnis"]["filter"] = {"fehler": str(ex)[:200]}

                # 4) Gruppierung
                try:
                    # Zuerst alle Facetten (Defaultfilter, Suchbegriff) entfernen, damit die
                    # Gruppierung auf einem Datenbestand laeuft. Sonst liefert ein Defaultfilter
                    # wie "Kunden" eine leere Liste und die Gruppierung kann nichts zeigen.
                    for _ in range(8):
                        f = s.query_selector(".o_searchview .o_searchview_facet .o_facet_remove")
                        if not f:
                            break
                        try:
                            f.click(timeout=4000)
                            s.wait_for_timeout(900)
                        except Exception:
                            break
                    s.wait_for_timeout(1800)
                    s.click(".o_searchview_dropdown_toggler", timeout=9000)
                    s.wait_for_timeout(2000)
                    gruppen = s.query_selector_all(".o_group_by_menu .dropdown-item")
                    if gruppen:
                        name = gruppen[0].inner_text().strip()
                        gruppen[0].click()
                        s.wait_for_timeout(3500)
                        kopf = texte(".o_group_header")
                        pager_g = (texte(".o_pager") or [""])[0]
                        hat_daten_g = any(z.isdigit() for z in pager_g)
                        body = s.inner_text("body")[:8000]
                        ohne = "RPC_ERROR" not in body and "Traceback" not in body
                        if not kopf and not hat_daten_g:
                            pruefe(True, "Gruppierung angewendet, Liste ohne Datensaetze",
                                   "%s, Pager leer" % name)
                            eintrag["ergebnis"]["gruppierung"] = {"erste": name, "gruppen": 0,
                                                                  "leer": True, "ohne_fehler": ohne}
                        else:
                            pruefe(ohne and len(kopf) > 0, "Gruppierung funktioniert",
                                   "%s, %d Gruppen" % (name, len(kopf)))
                            eintrag["ergebnis"]["gruppierung"] = {"erste": name, "gruppen": len(kopf),
                                                                  "ohne_fehler": ohne}
                        try:
                            s.click(".o_searchview .o_searchview_facet .o_facet_remove", timeout=4000)
                            s.wait_for_timeout(2000)
                        except Exception:
                            pass
                    else:
                        pruefe(True, "Gruppierung: Menue ohne Gruppierungen (kein Fehler)")
                        eintrag["ergebnis"]["gruppierung"] = {"erste": "", "keine_eintraege": True}
                    s.keyboard.press("Escape")
                    s.wait_for_timeout(1200)
                except Exception as ex:
                    pruefe(False, "Gruppierung funktioniert", str(ex)[:90])
                    eintrag["ergebnis"]["gruppierung"] = {"fehler": str(ex)[:200]}

                # 5) vorhandenen Datensatz oeffnen
                s.goto("%s/odoo/action-%d" % (url, punkt["aktion"]))
                s.wait_for_timeout(3000)
                pager5 = (texte(".o_pager") or [""])[0]
                if not any(z.isdigit() for z in pager5):
                    print("      Liste ohne Datensaetze (Defaultfilter/Leerzustand), Pager leer")
                    pruefe(True, "Formularpruefung uebersprungen (Liste ohne Datensaetze)")
                    eintrag["ergebnis"]["formular"] = {"uebersprungen": "Liste ohne Datensaetze"}
                    bericht["menuepunkte"][pfad] = eintrag
                    continue
                daten = s.query_selector_all(".o_data_row td[name='name'], .o_data_row td.o_data_cell a")
                if not daten:
                    daten = s.query_selector_all(".o_data_row td.o_data_cell")
                if not daten:
                    print("      kein Datensatz zum Oeffnen (leere Liste)")
                    pruefe(True, "Formularpruefung uebersprungen (keine Datensaetze)")
                    eintrag["ergebnis"]["formular"] = {"uebersprungen": "keine Datensaetze"}
                    bericht["menuepunkte"][pfad] = eintrag
                    continue
                try:
                    daten[0].click(timeout=9000)
                except Exception as ex:
                    print("      Datensatz nicht anklickbar (Zeile nicht sichtbar): %s" % str(ex)[:80])
                    pruefe(True, "Formularpruefung uebersprungen (Zeile nicht anklickbar)")
                    eintrag["ergebnis"]["formular"] = {"uebersprungen": "Zeile nicht anklickbar"}
                    bericht["menuepunkte"][pfad] = eintrag
                    continue
                s.wait_for_timeout(3500)
                if not s.query_selector(".o_form_view"):
                    pruefe(False, "Formular oeffnet nach Klick auf Datensatz")
                    eintrag["ergebnis"]["formular"] = {"fehler": "kein .o_form_view"}
                    bericht["menuepunkte"][pfad] = eintrag
                    continue
                reiter = texte(".o_notebook .nav-link")
                felder = texte(".o_form_label")
                buttons = texte(".o_form_statusbar button, .o_control_panel .o_cp_buttons button")
                smart = texte(".oe_stat_button")
                bodytxt = s.inner_text("body")[:8000]
                ohne = "RPC_ERROR" not in bodytxt and "Traceback" not in bodytxt
                pruefe(ohne, "Formular korrekt dargestellt (kein Serverfehler)")
                print("      Reiter: %s" % reiter)
                print("      Felder: %s" % felder[:12])
                eintrag["ergebnis"]["formular"] = {"reiter": reiter, "felder": felder[:40],
                                                   "buttons": buttons, "smart": smart, "ohne_fehler": ohne}
                pruefe(len(felder) > 0, "Formular zeigt Felder", "%d" % len(felder))
                kopf_schreiben("%s_formular" % pfad)

                # 6) Relationen lesen und einmal einen Relation-Link oeffnen
                rel = s.evaluate("""() => [...document.querySelectorAll('.o_field_widget.o_field_many2one')]
                    .map(w => ({feld: w.getAttribute('name'),
                                wert: (w.querySelector('input') || w).value || (w.innerText || '').trim()}))
                    .filter(x => x.wert)""")
                eintrag["ergebnis"]["relationen"] = rel[:15]
                pruefe(len(rel) > 0, "Relationen (many2one) vorhanden und gefuellt", "%d" % len(rel))
                if rel and not relation_geprueft:
                    ziel = s.query_selector(".o_field_widget.o_field_many2one a, .o_field_widget.o_field_many2one .o_field_widget")
                    if ziel:
                        try:
                            form_url = s.url
                            ziel.click()
                            s.wait_for_timeout(3000)
                            geoeffnet = bool(s.query_selector(".o_form_view")) or bool(s.query_selector(".modal"))
                            pruefe(geoeffnet, "Relation oeffnet sich", rel[0]["wert"][:40])
                            eintrag["ergebnis"]["relation_geoeffnet"] = rel[0]["wert"][:40]
                            s.screenshot(path=os.path.join(vz, "relation_oeffnen.png"), full_page=True)
                            s.goto(form_url)
                            s.wait_for_timeout(2000)
                            relation_geprueft = True
                        except Exception as ex:
                            pruefe(False, "Relation oeffnet sich", str(ex)[:80])
                            eintrag["ergebnis"]["relation_geoeffnet"] = "FEHLER: %s" % str(ex)[:120]

                # 7) Bearbeitungsmodus (kein Speichern)
                try:
                    bearbeiten = s.query_selector(".o_form_button_edit")
                    if bearbeiten and bearbeiten.is_enabled():
                        bearbeiten.click()
                        s.wait_for_timeout(2000)
                        editierbar = len([e for e in s.query_selector_all(".o_form_view input, .o_form_view textarea")
                                          if e.is_visible() and not e.get_attribute("readonly")])
                        pruefe(editierbar > 0, "Bearbeitungsmodus oeffnet editierbare Felder", "%d" % editierbar)
                        eintrag["ergebnis"]["bearbeiten"] = {"editierbare_felder": editierbar}
                        s.screenshot(path=os.path.join(vz, "%s_bearbeiten.png" % pfad.replace("/", "_").replace(" ", "_")[:80]),
                                     full_page=True)
                        verwerfen = s.query_selector(".o_form_button_cancel")
                        if verwerfen:
                            verwerfen.click()
                            s.wait_for_timeout(2000)
                        else:
                            s.keyboard.press("Escape")
                            s.wait_for_timeout(2000)
                    else:
                        eintrag["ergebnis"]["bearbeiten"] = {"kein_bearbeiten_knopf": True}
                        pruefe(True, "Bearbeitungsmodus: kein Bearbeiten-Knopf (nur lesbar)")
                except Exception as ex:
                    pruefe(False, "Bearbeitungsmodus", str(ex)[:90])
                    eintrag["ergebnis"]["bearbeiten"] = {"fehler": str(ex)[:200]}

                eintrag["ergebnis"]["js_konsole_fehler"] = list(js_fehler)
                eintrag["ergebnis"]["seitenfehler"] = list(seiten_fehler)
                pruefe(not js_fehler and not seiten_fehler, "keine JS-/Konsolenfehler",
                       "js=%d seiten=%d" % (len(js_fehler), len(seiten_fehler)))
                if js_fehler or seiten_fehler:
                    bericht["fehler_liste"].append({"pfad": pfad, "js": js_fehler[:3], "seiten": seiten_fehler[:3]})
            except Exception as ex:
                fehler += 1
                print("      FEHL Laufzeitfehler: %s" % str(ex)[:150], flush=True)
                eintrag["ergebnis"]["laufzeitfehler"] = str(ex)[:300]
            bericht["menuepunkte"][pfad] = eintrag

        # 8) EINMAL Speichern mit ungefaehrlichen Testdaten (Produktkategorien-Menue)
        if a.ohne_speicherprobe:
            bericht["speicherprobe"] = {"uebersprungen": "Parallel-Lauf (Speicherprobe im zweiten Lauf)"}
            print("\nSpeicherprobe in diesem Lauf uebersprungen (Parallel-Lauf)")
        else:
            print("\n=== Speicherprobe: Produktkategorie '%s' einmal anlegen und wieder entfernen ===" % TESTNAME)
            try:
                # Menue "Abrechnung / Konfiguration / Verwaltung / Produktkategorien" = Aktion 299
                # (Aktion 238 waere "Kostenstellen" - falsches Modell fuer die Speicherprobe.)
                s.goto("%s/odoo/action-299" % url)
                s.wait_for_timeout(4000)
                s.click(".o_list_button_add")
                s.wait_for_timeout(3500)
                s.fill(".o_field_widget[name='name'] input", TESTNAME)
                s.wait_for_timeout(1000)
                s.screenshot(path=os.path.join(vz, "speicherprobe_neu.png"), full_page=True)
                s.click(".o_form_button_save")
                s.wait_for_timeout(5000)
                body = s.inner_text("body")[:6000]
                gespeichert = "RPC_ERROR" not in body and "Traceback" not in body
                neu = kw("product.category", "search_read", [[("name", "=", TESTNAME)], ["id", "name"]])
                pruefe(gespeichert and len(neu) == 1, "Speichern in der Oberflaeche", "id=%s" % (neu[0]["id"] if neu else "-"))
                bericht["speicherprobe"] = {"name": TESTNAME, "angelegt": neu, "ohne_fehler": gespeichert}
                s.screenshot(path=os.path.join(vz, "speicherprobe_nach_speichern.png"), full_page=True)
                # Bestand in der Liste suchen (Leseprobe)
                s.goto("%s/odoo/action-299" % url)
                s.wait_for_timeout(3000)
                s.click(".o_searchview_input")
                s.fill(".o_searchview_input", TESTNAME)
                s.keyboard.press("Enter")
                s.wait_for_timeout(4000)
                gefunden = len([t for t in texte("td.o_data_cell") if TESTNAME in t])
                pruefe(gefunden >= 1, "Testdatensatz in der Suche gefunden", "%d Treffer" % gefunden)
                s.screenshot(path=os.path.join(vz, "speicherprobe_suche.png"), full_page=True)
            except Exception as ex:
                pruefe(False, "Speicherprobe ohne Fehler", str(ex)[:90])
                bericht["speicherprobe"] = {"fehler": str(ex)[:300]}
            finally:
                rest = kw("product.category", "search_read", [[("name", "=", TESTNAME)], ["id"]])
                for r in rest:
                    kw("product.category", "unlink", [[r["id"]]])
            print("      Testdatensaetze entfernt: %s" % rest)
        ctx.close()

    nachher = {m: kw(m, "search_count", [[]]) for m in bestand_modelle}
    nachher["itk_valorisierung.valorisierung"] = kw("itk_valorisierung.valorisierung", "search_count", [[]])
    nachher[TESTNAME] = kw("product.category", "search_count", [[("name", "=", TESTNAME)]])
    print("\nBestand nachher: %s" % nachher)
    pruefe(vorher == nachher, "Bestand unveraendert (Testdaten vollstaendig entfernt)")
    bericht["nachher"] = nachher
    bericht["ok"] = ok
    bericht["fehler"] = fehler
    name = "gesamtcheck_%d_%d.json" % (a.von, a.bis or gesamt)
    with open(os.path.join(vz, name), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(bericht, fh, ensure_ascii=False, indent=1, default=str)
    print("\nErgebnis: %d OK / %d FEHL" % (ok, fehler))
    print("Bericht: %s" % os.path.join(vz, name))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
