#!/usr/bin/env python3
"""Browserabnahme Massenbearbeitung Odoo 18: jede Aktion oeffnen, anwenden, zuruecknehmen.

Je Aktion:
  1. Listenansicht oeffnen, Datensaetze markieren (Vorgabe: erste zwei Zeilen)
  2. Menue "Aktion" -> Aktion, Dialog pruefen (Titel, Optionen, Zaehlanzeige, Feldtyp)
  3. Modus "Setzen"/"Hinzufuegen" waehlen, Wert eintragen, "Anwenden"
  4. per RPC pruefen, welche Felder sich geaendert haben (Soll: nur das Zielfeld)
  5. Ausgangswerte zurueckschreiben und nachpruefen

Es werden keine Datensaetze geloescht und keine Stammdaten angelegt. Fuer die
Lead-Aktionen werden zwei Test-Leads angelegt und am Ende wieder entfernt.

Aufruf:
  uv run --with playwright python scripts/browser_massenbearbeitung_abnahme.py --instanz lokal
  uv run --with playwright python scripts/browser_massenbearbeitung_abnahme.py --instanz vm
Ergebnis: docs/_massenbearbeitung_browser_<instanz>.json
"""
from __future__ import annotations

import argparse
import datetime
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
KONTAKTE = "/odoo/action-141?view_type=list"
ANGEBOTE = "/odoo/action-431?view_type=list"
ABOS = "/odoo/action-1105?view_type=list"
ABOBUCHUNGEN = "/odoo/action-1109?view_type=list"
RECHNUNGEN = "/odoo/action-354?view_type=list"
PRODUKTE = "/odoo/action-296?view_type=list"
LEADS = "/odoo/action-210?view_type=list"

# Feldtypen: selection = native Auswahlliste, m2o/m2m = Autocomplete, sonst Eingabefeld
AKTIONEN = [
    {"id": 1304, "name": "Zuweisung Preisliste NÖ", "url": KONTAKTE, "model": "res.partner",
     "feld": "property_product_pricelist", "typ": "m2o", "wert": "Preisliste 2026 + Valorisierung",
     "modus": "Setzen", "nur_schreibnachweis": True},
    {"id": 1305, "name": "Zuweisung zu Preisliste", "url": ANGEBOTE, "model": "sale.order",
     "feld": "pricelist_id", "typ": "m2o", "wert": "Preisliste 2026 + Valorisierung",
     "modus": "Setzen", "vorher_leeren": True,
     "zeilen_zustaende": ["Angebot", "Angebot gesendet"]},
    {"id": 1306, "name": "Recurring Total", "url": ABOBUCHUNGEN, "model": "sale.subscription.line",
     "feld": "quantity", "typ": "float", "wert": "2", "alternativen": ["3"], "modus": "Setzen"},
    {"id": 1307, "name": "Angebot zu Auftrag", "url": ANGEBOTE, "model": "sale.order",
     "feld": "state", "typ": "selection", "wert": "Verkaufsauftrag", "modus": "Setzen",
     "nebenpruefung": "sale_order", "zeilen_zustaende": ["Angebot", "Angebot gesendet"],
     "folgefelder": ["invoice_status"]},
    {"id": 1308, "name": "Status Kunde", "url": KONTAKTE, "model": "res.partner",
     "feld": "status_of_partner_id", "typ": "m2o", "wert": "Bestandskunde",
     "alternativen": ["Kein Kunde", "Ehemaliger Kunde"], "modus": "Setzen"},
    {"id": 1309, "name": "Zahlungsbedingungen setzen", "url": ANGEBOTE, "model": "sale.order",
     "feld": "payment_term_id", "typ": "m2o", "wert": "15 Tage",
     "alternativen": ["21 Tage", "30 Tage"], "modus": "Setzen",
     "zeilen_zustaende": ["Angebot", "Angebot gesendet"]},
    {"id": 1310, "name": "Startdatum des nächsten Leistungszeitraumes", "url": ABOS,
     "model": "sale.subscription", "feld": "recurring_next_date", "typ": "date",
     "wert": "01.12.2026", "alternativen": ["15.12.2026"], "modus": "Setzen"},
    {"id": 1311, "name": "Abo-Status ändern", "url": ABOS, "model": "sale.subscription",
     "feld": "state", "typ": "selection", "wert": "Zu erneuern",
     "alternativen": ["Abgeschlossen", "Neu"], "modus": "Setzen"},
    {"id": 1312, "name": "Produktkategorie zuweisen", "url": PRODUKTE, "model": "product.product",
     "feld": "categ_id", "typ": "m2o", "wert": "Expenses",
     "alternativen": ["Events", "All", "Saleable"], "modus": "Setzen",
     "pruefe_feld_direkt": True},
    {"id": 1313, "name": "Valorisierungstext ändern", "url": RECHNUNGEN, "model": "account.move",
     "feld": "valorisierung_id", "typ": "m2o", "wert": "VAL-OK",
     "alternativen": ["VALORISIERUNGSHINWEIS 2023"], "modus": "Setzen",
     "zeilen_zustaende": ["Entwurf"], "folgefelder": ["is_manually_modified"]},
    {"id": 1314, "name": "Zahlungsbedingungen setzen Abrechnung", "url": RECHNUNGEN,
     "model": "account.move", "feld": "invoice_payment_term_id", "typ": "m2o", "wert": "15 Tage",
     "alternativen": ["21 Tage", "30 Tage"], "modus": "Setzen",
     "zeilen_zustaende": ["Entwurf"],
     "folgefelder": ["is_manually_modified", "invoice_date_due"]},
    {"id": 1315, "name": "Rechnungsdatum Abrechnung", "url": RECHNUNGEN, "model": "account.move",
     "feld": "invoice_date", "typ": "date", "wert": "01.12.2026",
     "alternativen": ["15.12.2026"], "modus": "Setzen",
     "zeilen_zustaende": ["Entwurf"],
     "folgefelder": ["is_manually_modified", "date", "invoice_date_due"]},
    {"id": 1316, "name": "Datum der nächsten Rechnung", "url": ABOS, "model": "sale.subscription",
     "feld": "recurring_next_date", "typ": "date", "wert": "01.12.2026",
     "alternativen": ["15.12.2026"], "modus": "Setzen"},
    {"id": 1317, "name": "Leistungszeitraum setzen", "url": RECHNUNGEN, "model": "account.move",
     "feld": "sale_order_benefit_period", "typ": "text", "wert": "Test S140",
     "alternativen": ["Test S140b"], "modus": "Setzen",
     "zeilen_zustaende": ["Entwurf"], "folgefelder": ["is_manually_modified"]},
    {"id": 1318, "name": "Projektkategorie setzen", "url": RECHNUNGEN, "model": "account.move",
     "feld": "projectcategory_id", "typ": "m2o", "wert": "amtsweg.gv.at - BUNDESLAND STANDARD",
     "alternativen": ["amtsweg.gv.at - DSGVO-Verarbeitungsverzeichnis"], "modus": "Setzen",
     "zeilen_zustaende": ["Entwurf"], "folgefelder": ["is_manually_modified"]},
    {"id": 1319, "name": "Tag-Zuweisung", "url": KONTAKTE, "model": "res.partner",
     "feld": "category_id", "typ": "m2m", "wert": "AFS",
     "alternativen": ["Aktionen", "FSW", "Communex", "Datenschutzbeauftragter"],
     "modus": "Hinzufügen"},
    {"id": 1320, "name": "Produktinteresse setzen", "url": LEADS, "model": "crm.lead",
     "feld": "x_Produktinteresse", "typ": "selection", "wert": "IFG",
     "alternativen": ["Gemeindecloud", "Hinweisportal"], "modus": "Setzen",
     "lead_filter": "TEST S140"},
    {"id": 1321, "name": "Lead Quelle setzen", "url": LEADS, "model": "crm.lead",
     "feld": "x_Lead_Quelle", "typ": "selection", "wert": "Recherchierte Adressen April 2025",
     "alternativen": ["ITK & VÖWG Webinar (2025-06-24)"], "modus": "Setzen",
     "lead_filter": "TEST S140"},
    {"id": 1322, "name": "Interessent Stichwort setzen", "url": LEADS, "model": "crm.lead",
     "feld": "tag_ids", "typ": "m2m", "wert": "TEST S140", "modus": "Hinzufügen",
     "lead_filter": "TEST S140"},
    {"id": 1323, "name": "Interessent Lead Status setzen", "url": LEADS, "model": "crm.lead",
     "feld": "x_lead_status", "typ": "selection", "wert": "Lead kontaktiert",
     "alternativen": ["Lead aufbereitet", "On-Hold"], "modus": "Setzen",
     "lead_filter": "TEST S140"},
]

NEBENPRUEFUNG = {
    "sale.order": ["stock.picking:sale_id"],
}

ok_zahl = 0
fehler = []


def pruefe(bedingung, text, ist=None, soll=None):
    global ok_zahl
    if bedingung:
        ok_zahl += 1
        print("    OK    %s%s" % (text, "" if ist is None else "  (%s)" % (ist,)))
    else:
        fehler.append("%s | ist=%r soll=%r" % (text, ist, soll))
        print("    FEHL  %s | ist=%r soll=%r" % (text, ist, soll))


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


_FELD_CACHE = {}


def alle_felder(k, model):
    """Stored-Felder fuer den Schnappschuss (one2many ausgenommen) plus Menge der berechneten."""
    if model not in _FELD_CACHE:
        f = k.kw(model, "fields_get", [[], ["type", "store", "compute"]]) or {}
        stored = sorted(n for n, d in f.items()
                        if d.get("store") and d.get("type") != "one2many")
        berechnet = {n for n, d in f.items() if d.get("compute")}
        _FELD_CACHE[model] = (stored, berechnet)
    return _FELD_CACHE[model]


def schnappschuss(k, model, ids):
    felder, _berechnet = alle_felder(k, model)
    daten = {d["id"]: d for d in k.kw(model, "read", [ids, felder], context=DE) or []}
    return daten


def unterscheide(vorher, nachher):
    unterschiede = []
    for rid, alt in vorher.items():
        neu = nachher.get(rid, {})
        for feld, wert in alt.items():
            if feld in ("write_date", "write_uid", "__last_update"):
                continue
            if neu.get(feld) != wert:
                unterschiede.append({"id": rid, "feld": feld, "alt": wert, "neu": neu.get(feld)})
    return unterschiede


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--nur", default=None, help="nur diese Aktions-ID pruefen")
    a = ap.parse_args()
    env = lade_env()
    url = (env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal"
           else "https://k001959vsx.ipax.at").rstrip("/")
    domain = url.split("//")[1].split(":")[0]
    k = o18(a.instanz)
    sid = sitzung(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    ergebnis = {"instanz": a.instanz, "stand": datetime.datetime.now().isoformat(timespec="seconds"),
                "aktionen": []}

    # Testdaten fuer die Lead-Aktionen: zwei temporaere Leads (werden entfernt)
    lead_ids = k.kw("crm.lead", "create", [[
        {"name": "TEST S140 Massenbearbeitung A", "type": "lead"},
        {"name": "TEST S140 Massenbearbeitung B", "type": "lead"},
    ]])
    pruefe(len(lead_ids) == 2, "Test-Leads angelegt (werden am Ende entfernt)", lead_ids)
    if not k.kw("crm.tag", "search", [[("name", "=", "TEST S140")]]):
        tag_id = k.kw("crm.tag", "create", [[{"name": "TEST S140"}]])[0]
    else:
        tag_id = k.kw("crm.tag", "search", [[("name", "=", "TEST S140")]])[0]

    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome")
            ctx = b.new_context(viewport={"width": 1600, "height": 1050})
            ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
            seite = ctx.new_page()
            netz = []
            seite.on("request", lambda r: netz.append({"url": r.url, "post": (r.post_data or "")[:1500]})
                     if "call_kw" in r.url else None)

            def liste_laden(pfad, filter_text=None):
                seite.goto(url + pfad, wait_until="domcontentloaded", timeout=120000)
                seite.wait_for_selector(".o_list_view", timeout=120000)
                time.sleep(3.5)
                if filter_text:
                    seite.fill(".o_searchview_input", filter_text)
                    seite.keyboard.press("Enter")
                    time.sleep(3)
                return seite.evaluate(
                    "() => [...document.querySelectorAll('.o_data_row')]"
                    ".map(r => (r.getAttribute('data-id') || '').replace('datapoint_', ''))")

            def markieren_indizes(indizes):
                anzahl = seite.evaluate("""(indizes) => {
                    const zeilen = [...document.querySelectorAll('.o_data_row')];
                    let n = 0;
                    for (const i of indizes) {
                        const kasten = zeilen[i] && zeilen[i].querySelector('input[type=checkbox]');
                        if (kasten && !kasten.checked) { kasten.click(); n += 1; }
                    }
                    return n;
                }""", indizes)
                time.sleep(1.5)
                return anzahl

            def aktionsmenue(aktion):
                for el in seite.query_selector_all(".o_control_panel button, .o_control_panel .dropdown-toggle"):
                    if (el.inner_text() or "").strip().startswith("Aktion") and el.is_visible():
                        el.click()
                        break
                time.sleep(2)
                eintraege = [e.inner_text().strip() for e in
                             seite.query_selector_all(".o-dropdown--menu .dropdown-item") if e.is_visible()]
                for el in seite.query_selector_all(".o-dropdown--menu .dropdown-item"):
                    if el.is_visible() and el.inner_text().strip() == aktion:
                        el.click()
                        return eintraege
                return eintraege

            for cfg in AKTIONEN:
                if a.nur and str(cfg["id"]) != str(a.nur):
                    continue
                print("\n--- %s (id %s, %s.%s)" % (cfg["name"], cfg["id"], cfg["model"], cfg["feld"]))
                eintrag = {"id": cfg["id"], "name": cfg["name"], "model": cfg["model"], "feld": cfg["feld"]}
                try:
                    liste_laden(cfg["url"], cfg.get("lead_filter")
                                or ("TEST S140" if cfg["model"] == "crm.lead" else None))
                    zellen = seite.evaluate(
                        "() => [...document.querySelectorAll('.o_data_row')]"
                        ".map(r => [...r.querySelectorAll('td')].map(td => (td.innerText || '').trim()))")
                    indizes = list(range(len(zellen)))
                    if cfg.get("zeilen_zustaende"):
                        indizes = [i for i in indizes
                                   if any(z in cfg["zeilen_zustaende"] for z in zellen[i])]
                    indizes = indizes[:2]
                    eintrag["zeilen"] = [" | ".join(zellen[i])[:120] for i in indizes]
                    pruefe(len(indizes) >= 1, "passende Zeilen in der Liste", len(indizes), ">=1")
                    if not indizes:
                        ergebnis["aktionen"].append(eintrag)
                        continue

                    markiert = markieren_indizes(indizes)
                    pruefe(markiert == len(indizes), "Zeilen markiert", markiert, len(indizes))
                    menue = aktionsmenue(cfg["name"])
                    eintrag["aktionsmenue"] = menue
                    pruefe(cfg["name"] in menue, "Aktion im Menue 'Aktion'", cfg["name"] in menue)
                    seite.wait_for_selector(".o_dialog .o_form_view", timeout=60000)
                    time.sleep(2)

                    # echte Datensatz-IDs aus dem Kontext des Dialogs (data-id im DOM ist nur eine Datapoint-Nummer)
                    ziel, _modell_ctx = aktive_ids(netz)
                    eintrag["datensaetze"] = ziel
                    pruefe(bool(ziel), "aktive Datensaetze aus dem Dialogkontext", ziel)
                    if not ziel:
                        ergebnis["aktionen"].append(eintrag)
                        continue

                    vorher_original = schnappschuss(k, cfg["model"], ziel)
                    if cfg.get("vorher_leeren"):
                        # Zielfeld vor der Probe leeren, damit die Aktion nachweisbar etwas setzt
                        k.kw(cfg["model"], "write", [ziel, {cfg["feld"]: False}])
                        time.sleep(1.5)
                    vorher = schnappschuss(k, cfg["model"], ziel)
                    schreib_vorher = {d["id"]: d["write_date"] for d in
                                      k.kw(cfg["model"], "read", [ziel, ["write_date"]])}
                    direkt_vorher = {d["id"]: d.get(cfg["feld"]) for d in
                                     k.kw(cfg["model"], "read", [ziel, [cfg["feld"]]], context=DE)}
                    if cfg.get("nur_zustand"):
                        ist = {v.get("state") for v in vorher.values()}
                        eintrag["zustand_vorher"] = sorted(ist)
                    cfg = dict(cfg)
                    cfg["wert"] = waehle_wert(k, cfg, ziel)
                    eintrag["wert"] = cfg["wert"]
                    neben_vorher = {}
                    for schluessel in NEBENPRUEFUNG.get(cfg["model"], []):
                        modell, feld = schluessel.split(":")
                        neben_vorher[modell] = k.kw(modell, "search_count",
                                                    [[(feld, "in", ziel)]])

                    dialog = seite.query_selector(".o_dialog")
                    titel = dialog.query_selector(".modal-title")
                    eintrag["titel"] = titel.inner_text().strip() if titel else None
                    pruefe(eintrag["titel"] == cfg["name"], "Dialogtitel", eintrag["titel"], cfg["name"])

                    auswahl = dialog.query_selector(".o_field_widget[name^='selection__'] select")
                    optionen = ([o.inner_text().strip() for o in
                                 auswahl.query_selector_all("option") if o.inner_text().strip()]
                                if auswahl else [])
                    eintrag["optionen"] = optionen
                    pruefe("Nicht ändern" in optionen, "Option 'Nicht ändern' vorhanden", optionen)
                    pruefe(cfg["modus"] in optionen, "Option '%s' vorhanden" % cfg["modus"], optionen)

                    hinweis = ""
                    for el in dialog.query_selector_all("p, .alert"):
                        t = (el.inner_text() or "").strip()
                        if "Behandlung" in t or "ausgewählten" in t:
                            hinweis = t
                    eintrag["hinweis"] = hinweis
                    pruefe(str(len(ziel)) in hinweis, "Zaehlanzeige nennt %d Datensaetze" % len(ziel), hinweis)

                    seite.select_option(
                        ".o_dialog .o_field_widget[name^='selection__'] select", label=cfg["modus"])
                    time.sleep(2)
                    eintrag.update(wert_setzen(seite, cfg))
                    pruefe(eintrag.get("wert_gesetzt", False), "Wert eingetragen",
                           eintrag.get("wert_anzeige"), cfg["wert"])
                    bild = os.path.join(os.environ.get("TEMP", "."), "mass_%s_%s.png"
                                        % (a.instanz, cfg["id"]))
                    seite.screenshot(path=bild)
                    eintrag["bild"] = bild

                    # anwenden
                    angeklickt = False
                    for el in dialog.query_selector_all("button"):
                        if (el.inner_text() or "").strip() == "Anwenden":
                            el.click()
                            angeklickt = True
                            break
                    pruefe(angeklickt, "Knopf 'Anwenden' vorhanden")
                    time.sleep(5)
                    eintrag["dialog_nach_anwenden"] = seite.query_selector(".o_dialog") is not None
                    eintrag["netz"] = [n for n in netz if "mass.editing.wizard" in n["url"]][-4:]
                    seite.screenshot(path=os.path.join(os.environ.get("TEMP", "."),
                                                       "mass_%s_%s_nach.png" % (a.instanz, cfg["id"])))
                    fehlerdialog = seite.query_selector(".o_dialog .o_error_dialog, .modal.show .o_error_dialog")
                    if fehlerdialog:
                        eintrag["fehler"] = (fehlerdialog.inner_text() or "").strip()[:300]
                        print("    HINWEIS  Fehlermeldung:", eintrag["fehler"])
                        for el in seite.query_selector_all(".o_dialog button, .modal button"):
                            if (el.inner_text() or "").strip() in ("Abbrechen", "Schließen", "Close", "OK"):
                                el.click()
                                break
                        time.sleep(2)
                    else:
                        try:
                            seite.wait_for_selector(".o_dialog", state="detached", timeout=30000)
                        except Exception:  # noqa: BLE001
                            pass
                        time.sleep(2)

                    nachher = schnappschuss(k, cfg["model"], ziel)
                    unterschiede = unterscheide(vorher, nachher)
                    eintrag["aenderungen"] = unterschiede
                    _felder, berechnet = alle_felder(k, cfg["model"])
                    erlaubt = {cfg["feld"]} | set(cfg.get("folgefelder", [])) | berechnet
                    nur_ziel = all(u["feld"] in erlaubt for u in unterschiede)
                    if not cfg.get("nur_schreibnachweis") and not cfg.get("pruefe_feld_direkt"):
                        pruefe(bool(unterschiede), "Feld wurde geschrieben", unterschiede)
                        pruefe(nur_ziel, "nur Zielfeld und berechnete Folgefelder geaendert",
                               sorted({u["feld"] for u in unterschiede}), sorted(erlaubt))
                    if cfg.get("pruefe_feld_direkt"):
                        direkt_nachher = {d["id"]: d.get(cfg["feld"]) for d in
                                          k.kw(cfg["model"], "read", [ziel, [cfg["feld"]]], context=DE)}
                        geaendert = [i for i in ziel
                                     if direkt_nachher.get(i) != direkt_vorher.get(i)]
                        pruefe(bool(geaendert), "Feld direkt geaendert (nicht gespeichertes Feld)",
                               {str(k2): v for k2, v in direkt_nachher.items()})
                    if cfg.get("nur_schreibnachweis"):
                        schreib_nachher = {d["id"]: d["write_date"] for d in
                                           k.kw(cfg["model"], "read", [ziel, ["write_date"]])}
                        geaendert = [i for i in ziel if schreib_nachher.get(i) != schreib_vorher.get(i)]
                        pruefe(bool(geaendert), "Schreibvorgang belegt (write_date)", geaendert)
                        werte = [str((nachher[i].get(cfg["feld"]) or "")) for i in ziel]
                        pruefe(all(cfg["wert"] in w or w in cfg["wert"] for w in werte),
                               "Zielfeld traegt den gesetzten Wert", werte, cfg["wert"])
                    for schluessel in NEBENPRUEFUNG.get(cfg["model"], []):
                        modell, feld = schluessel.split(":")
                        jetzt = k.kw(modell, "search_count", [[(feld, "in", ziel)]])
                        eintrag["nebenpruefung_" + modell] = [neben_vorher.get(modell), jetzt]
                        pruefe(jetzt == neben_vorher.get(modell), "%s unveraendert" % modell,
                               jetzt, neben_vorher.get(modell))

                    # zuruecknehmen
                    zurueck = 0
                    for rid, werte in rueckgabe_werte(k, cfg, vorher_original, nachher).items():
                        if werte:
                            k.kw(cfg["model"], "write", [[rid], werte])
                            zurueck += 1
                    if cfg.get("pruefe_feld_direkt"):
                        for rid in ziel:
                            alt = direkt_vorher.get(rid)
                            alt_id = alt[0] if isinstance(alt, (list, tuple)) else alt
                            if alt_id:
                                k.kw(cfg["model"], "write", [[rid], {cfg["feld"]: alt_id}])
                                zurueck += 1
                    nach_kontrolle = schnappschuss(k, cfg["model"], ziel)
                    rest = [u for u in unterscheide(vorher_original, nach_kontrolle)
                            if u["feld"] not in berechnet]
                    eintrag["ruecknahme"] = {"datensaetze": zurueck, "rest": rest}
                    pruefe(not rest, "Ausgangswerte wiederhergestellt", rest)
                except Exception as exc:  # noqa: BLE001
                    eintrag["ausnahme"] = str(exc)[:400]
                    fehler.append("%s: %s" % (cfg["name"], str(exc)[:160]))
                    print("    AUSNAHME:", str(exc)[:200])
                ergebnis["aktionen"].append(eintrag)

            b.close()
    finally:
        # Testdaten entfernen
        try:
            k.kw("crm.lead", "unlink", [lead_ids])
            pruefe(k.kw("crm.lead", "search_count", [[("id", "in", lead_ids)]]) == 0,
                   "Test-Leads entfernt", lead_ids)
        except Exception as exc:  # noqa: BLE001
            fehler.append("Test-Leads nicht entfernt: %s" % str(exc)[:160])
        try:
            k.kw("crm.tag", "unlink", [[tag_id]])
            pruefe(k.kw("crm.tag", "search_count", [[("id", "=", tag_id)]]) == 0,
                   "Test-Stichwort entfernt", tag_id)
        except Exception as exc:  # noqa: BLE001
            fehler.append("Test-Stichwort nicht entfernt: %s" % str(exc)[:160])

    ziel_datei = os.path.join(REPO, "docs", "_massenbearbeitung_browser_%s.json" % a.instanz)
    with open(ziel_datei, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print("\n=== Ergebnis: %d OK / %d FEHL ===" % (ok_zahl, len(fehler)))
    for f in fehler:
        print("  FEHL:", f)
    print("JSON:", ziel_datei)
    return 0 if not fehler else 1


def rueckgabe_werte(k, cfg, vorher_original, nachher):
    """Rueckgabewerte je Datensatz: Ziel ist immer der urspruengliche Zustand."""
    fdef = k.kw(cfg["model"], "fields_get", [[cfg["feld"]], ["type", "relation"]])[cfg["feld"]]
    typ = fdef.get("type")
    rel = fdef.get("relation")
    feld = cfg["feld"]
    _felder, berechnet = alle_felder(k, cfg["model"])
    werte = {}
    for rid, alt in vorher_original.items():
        neu = nachher.get(rid, {})
        altwert = alt.get(feld)
        if typ == "many2one":
            ziel = (altwert[0] if isinstance(altwert, (list, tuple)) else altwert) or False
            ist = neu.get(feld)
            ist = (ist[0] if isinstance(ist, (list, tuple)) else ist) or False
            if ziel != ist:
                werte.setdefault(rid, {})[feld] = ziel
        elif typ == "many2many":
            alt_ids = set(altwert or [])
            neu_ids = set(neu.get(feld) or [])
            befehle = [(3, i) for i in neu_ids - alt_ids] + [(4, i) for i in alt_ids - neu_ids]
            if befehle:
                werte.setdefault(rid, {})[feld] = befehle
        else:
            if altwert != neu.get(feld):
                werte.setdefault(rid, {})[feld] = altwert
    return werte


def aktive_ids(netz):
    """Datensatz-IDs aus dem Kontext des zuletzt geoeffneten Massenbearbeitungs-Dialogs."""
    for n in reversed(netz):
        if "mass.editing.wizard" in n["url"]:
            try:
                p = json.loads(n["post"])
                ctx = p.get("params", {}).get("kwargs", {}).get("context", {}) or {}
                if ctx.get("active_ids"):
                    return list(ctx["active_ids"]), ctx.get("active_model")
            except Exception:  # noqa: BLE001
                continue
    return [], None


def waehle_wert(k, cfg, ids):
    """Wert bestimmen, der sich vom Ist-Wert unterscheidet (sonst keine Aenderung nachweisbar)."""
    if cfg["typ"] not in ("m2o", "m2m"):
        return cfg["wert"]
    feld = cfg["feld"]
    fdef = k.kw(cfg["model"], "fields_get", [[feld], ["type", "relation"]])[feld]
    daten = k.kw(cfg["model"], "read", [ids, [feld]], context=DE) or []
    kandidaten = [cfg["wert"]] + cfg.get("alternativen", [])
    if cfg["typ"] == "m2m":
        # m2m liefert IDs; fuer den Vergleich Namen lesen
        ids_jetzt = {i for d in daten for i in (d.get(feld) or [])}
        namen = set()
        if ids_jetzt:
            namen = {x["name"] for x in
                     k.kw(fdef["relation"], "read", [list(ids_jetzt), ["name"]], context=DE)}
        for w in kandidaten:
            if w not in namen:
                return w
        return cfg["wert"]
    ist_ids = {d[feld][0] for d in daten if isinstance(d.get(feld), (list, tuple))}
    for w in kandidaten:
        treffer = k.kw(fdef.get("relation"), "name_search", [w, []], limit=5, context=DE)
        ids = [t[0] for t in (treffer or [])]
        if ids and ids[0] not in ist_ids:
            return w
    return cfg["wert"]


def wert_setzen(seite, cfg):
    """Wert im Dialog eintragen. Gibt Angaben fuer den Bericht zurueck."""
    info = {"wert_gesetzt": False, "wert_anzeige": None}
    feld = cfg["feld"]
    selektor = ".o_dialog .o_field_widget[name='%s']" % feld
    widget = seite.query_selector(selektor)
    if widget is None:
        info["fehler"] = "Wertfeld nicht im Dialog"
        return info
    tag = widget.evaluate("e => e.firstElementChild ? e.firstElementChild.tagName : ''")
    info["widget"] = tag
    if cfg["typ"] == "selection":
        select = widget.query_selector("select")
        if select:
            info["auswahlwerte"] = [o.inner_text().strip() for o in
                                    select.query_selector_all("option") if o.inner_text().strip()]
            seite.select_option(selektor + " select", label=cfg["wert"])
            time.sleep(1.5)
            info["wert_anzeige"] = seite.eval_on_selector(
                selektor + " select", "e => e.options[e.selectedIndex].text").strip()
    elif cfg["typ"] in ("m2o", "m2m"):
        eingabe = widget.query_selector("input")
        if eingabe is None:
            info["fehler"] = "kein Eingabefeld"
            return info
        eingabe.click()
        eingabe.type(cfg["wert"], delay=40)
        time.sleep(3)
        treffer = None
        try:
            # echter Mausklick auf den Vorschlag (OWL reagiert auf Pointer-Events)
            seite.locator(".o-autocomplete--dropdown-item, a.dropdown-item").filter(
                has_text=cfg["wert"]).first.click(timeout=10000)
            treffer = cfg["wert"]
        except Exception:  # noqa: BLE001
            treffer = seite.evaluate("""(wert) => {
                const links = [...document.querySelectorAll('a.dropdown-item, .o-autocomplete--dropdown-item')]
                    .filter(e => e.offsetParent !== null);
                let ziel = links.find(e => (e.innerText || '').trim() === wert) || links[0];
                if (ziel) {
                    const el = (ziel.tagName === 'A' ? ziel : ziel.querySelector('a') || ziel);
                    for (const typ of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
                        el.dispatchEvent(new MouseEvent(typ, {bubbles: true, cancelable: true, view: window}));
                    }
                    return (ziel.innerText || '').trim();
                }
                return null;
            }""", cfg["wert"])
        time.sleep(2)
        if cfg["typ"] == "m2m" and treffer:
            seite.keyboard.press("Tab")
            time.sleep(1)
        anzeige = (eingabe.input_value() or "").strip()
        if cfg["typ"] == "m2m":
            tags = [t.inner_text().strip() for t in
                    widget.query_selector_all(".o_tag, .o_badge, .badge") if t.inner_text().strip()]
            if tags:
                anzeige = ", ".join(tags)
        if not anzeige:
            anzeige = seite.inner_text(selektor).strip()[:120]
        info["wert_anzeige"] = anzeige
        info["treffer"] = treffer
    else:
        eingabe = widget.query_selector("input, textarea")
        if eingabe is None:
            info["fehler"] = "kein Eingabefeld"
            return info
        eingabe.click()
        eingabe.fill("")
        eingabe.type(cfg["wert"], delay=30)
        seite.keyboard.press("Tab")
        time.sleep(1.5)
        info["wert_anzeige"] = (eingabe.input_value() or "").strip()
    info["wert_gesetzt"] = bool(info.get("wert_anzeige"))
    info["widget_html"] = (widget.inner_html()[:300] if widget is not None else None)
    return info


if __name__ == "__main__":
    sys.exit(main())
