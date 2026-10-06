"""Browser-Abnahme Teil 2 - Reiter "Verkauf" (Auftrag 06.10.2026, Punkte 1 bis 5).

1. item_ids haelt keine eigenen Daten (One2many-Relation, Daten nur in product.pricelist.item)
2. Bestehender Datensatz mit Preislistenregel im Bearbeitungsmodus: Preis, Mindestbestellmenge,
   Startdatum, Enddatum, Speichern und Verwerfen (Werte werden immer wieder zurueckgestellt)
3. Produkt mit Abonnementvorlage: verknuepfte Vorlage oeffnen
4. Smart Button "Regeln Preislisten" und Preiskalkulation zeigen dieselben Datensaetze
5. Gruppentitel deutsch ("Zusatz- und Querverkauf"), optional_product_ids unveraendert

Aufruf: uv run --with playwright python scripts/browser_verkauf_reiter_abnahme2.py lokal|vm
"""
from __future__ import annotations

import datetime as dt
import http.cookiejar
import json
import os
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

INST = sys.argv[1] if len(sys.argv) > 1 else "lokal"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "http://localhost:8069" if INST == "lokal" else "https://k001959vsx.ipax.at"
DOMAIN = "localhost" if INST == "lokal" else "k001959vsx.ipax.at"
VZ = os.path.expanduser("~") + "/Desktop/Odoo18-Abnahme-Session126/verkauf_reiter2/" + INST
os.makedirs(VZ, exist_ok=True)
AKTION = 382
ERGEBNISSE = []

umg = {}
for zeile in open(os.path.join(REPO, ".env"), encoding="utf-8"):
    if "=" in zeile and not zeile.strip().startswith("#"):
        s, w = zeile.split("=", 1)
        umg[s.strip()] = w.strip()
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
CTX = {"lang": "de_DE"}
REGEL_FELDER = ["pricelist_id", "compute_price", "base", "applied_on", "fixed_price", "min_quantity",
                "date_start", "date_end", "price_discount", "percent_price", "company_id",
                "currency_id", "product_tmpl_id"]


def rpc(model, method, args, kwargs=None):
    nutzlast = {"jsonrpc": "2.0", "method": "call", "params": {
        "model": model, "method": method, "args": args, "kwargs": kwargs or {}}}
    with op.open(urllib.request.Request(URL + "/web/dataset/call_kw",
                 data=json.dumps(nutzlast).encode(),
                 headers={"Content-Type": "application/json"})) as a:
        d = json.loads(a.read().decode())
    if "error" in d:
        raise RuntimeError(str(d["error"])[:400])
    return d["result"]


def lese(ids, felder=REGEL_FELDER):
    return rpc("product.pricelist.item", "read", [ids, felder], {"context": CTX})


def anzahl(domain=None):
    return rpc("product.pricelist.item", "search_count", [domain or []], {"context": CTX})


def pruefe(ok, text):
    ERGEBNISSE.append((bool(ok), text))
    print("  %s  %s" % ("OK  " if ok else "FEHL", text))


def lokal_datum(wert):
    """UTC-Zeitstempel aus Odoo in das lokale Datum (Europe/Vienna) umrechnen."""
    if not wert:
        return None
    d = dt.datetime.strptime(str(wert), "%Y-%m-%d %H:%M:%S")
    for stunden in (1, 2):
        kandidat = (d + dt.timedelta(hours=stunden)).date().isoformat()
        if kandidat in ("2026-01-01", "2026-12-31"):
            return kandidat
    return d.date().isoformat()


op.open(urllib.request.Request(URL + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
            "db": umg["ODOO18_DB"], "login": umg["ODOO18_USER"],
            "password": umg["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"}))
SID = next(c.value for c in jar if c.name == "session_id")

# ---------------------------------------------------------------- Punkt 1: keine eigenen Daten
print("=== 1. item_ids haelt keine eigenen Daten ===")
felder_item = rpc("product.template", "fields_get", [["item_ids"],
                  ["type", "relation", "relation_field", "string", "readonly"]], {"context": CTX})["item_ids"]
print("   fields_get:", felder_item)
pruefe(felder_item["type"] == "one2many" and felder_item["relation"] == "product.pricelist.item"
       and felder_item["relation_field"] == "product_tmpl_id",
       "item_ids ist eine One2many-Relation auf product.pricelist.item ueber product_tmpl_id "
       "(keine eigene Speicherung)")
regeln_start = rpc("product.pricelist.item", "search_read",
                   [[], ["id", "product_tmpl_id"]], {"context": CTX})
regel_ids_start = sorted(r["id"] for r in regeln_start)
pruefe(all(r["product_tmpl_id"] for r in regeln_start),
       "Jede Regel traegt product_tmpl_id (%d von %d)" % (len(regeln_start), len(regeln_start)))
regel = regeln_start[0]
regel_id, produkt = regel["id"], regel["product_tmpl_id"][0]
start = lese([regel_id])[0]
print("   Testregel %s an Produkt %s: %s" % (regel_id, produkt,
      json.dumps({k: start[k] for k in ("pricelist_id", "fixed_price", "min_quantity", "date_start",
                                        "date_end", "applied_on", "compute_price")}, ensure_ascii=False)))

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"),
                                   "pw_v2_%s_%d" % (INST, time.time())),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": SID, "domain": DOMAIN, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()

    def oeffne(produkt_id, reiter="Verkauf"):
        seite.goto("%s/odoo/action-%d/%s" % (URL, AKTION, produkt_id))
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(6000)
        if reiter:
            seite.click(".o_notebook .nav-link:has-text('%s')" % reiter)
            seite.wait_for_timeout(2500)

    def zelle(feld, wert):
        """Wert in die erste Datenzeile der Regelliste schreiben (deutsches Zahlenformat)."""
        zeile = seite.locator(".o_field_x2many_list tbody tr.o_data_row").first
        z = zeile.locator("td[name='%s']" % feld)
        z.click()
        seite.wait_for_timeout(900)
        seite.keyboard.press("Control+A")
        if wert == "":
            seite.keyboard.press("Delete")
        else:
            seite.keyboard.type(str(wert))
        seite.keyboard.press("Tab")
        seite.wait_for_timeout(1200)

    def zeilen_anzahl():
        return seite.locator(".o_field_x2many_list tbody tr.o_data_row").count()

    def speichern():
        seite.click("button.o_form_button_save")
        seite.wait_for_timeout(3500)
        # Schutz: falls beim Bearbeiten eine leere Zusatzzeile entstanden ist, entfernen
        for _ in range(3):
            if zeilen_anzahl() <= 1:
                break
            seite.locator(".o_field_x2many_list tbody tr.o_data_row").last.locator(
                "td.o_list_record_remove button, button.fa-trash-o, .o_list_record_remove").last.click()
            seite.wait_for_timeout(1200)
            seite.click("button.o_form_button_save")
            seite.wait_for_timeout(3000)
        return zeilen_anzahl()

    def verwerfen():
        seite.click("button.o_form_button_cancel")
        seite.wait_for_timeout(2000)
        for txt in ("Verwerfen", "OK"):
            k = seite.locator(".modal button:has-text('%s')" % txt)
            if k.count() and k.first.is_visible():
                k.first.click()
                seite.wait_for_timeout(1500)
                break
        seite.wait_for_timeout(1500)

    # -------------------------------------------------- Punkt 2: Bearbeitungsmodus, Speichern/Verwerfen
    print("\n=== 2. Bestehender Datensatz mit Regel: Bearbeitungsmodus, Speichern, Verwerfen ===")
    oeffne(produkt)
    modus = seite.evaluate("() => document.querySelector('.o_form_editable') ? 'bearbeitbar' : 'nur lesen'")
    zeilen = seite.evaluate("""() => { const tr = document.querySelector('.o_field_x2many_list tbody tr.o_data_row');
        return tr ? [...tr.querySelectorAll('td[name]')].map(td => td.getAttribute('name')) : []; }""")
    print("   Formularzustand:", modus, "| Zellen:", zeilen)
    pruefe(modus == "bearbeitbar", "Bestehender Datensatz im Bearbeitungsmodus bearbeitbar")
    pruefe(all(n in zeilen for n in ("fixed_price", "min_quantity", "date_start", "date_end")),
           "Zellen Preis, Mindestbestellmenge, Startdatum, Enddatum vorhanden")
    seite.screenshot(path=os.path.join(VZ, "01_bearbeitungsmodus.png"), full_page=True)

    # Verwerfen: Preis aendern, dann Aenderungen verwerfen
    zelle("fixed_price", "66,00")
    zwischen = lese([regel_id])[0]["fixed_price"]
    pruefe(abs(zwischen - start["fixed_price"]) < 0.001,
           "Formulaenderung noch nicht in der Datenbank (dort weiterhin %.2f)" % zwischen)
    verwerfen()
    nach_verwerfen = lese([regel_id])[0]
    pruefe(nach_verwerfen == start,
           "Verwerfen laesst den Datensatz unveraendert (Preis %.2f, Mindestbestellmenge %s)"
           % (nach_verwerfen["fixed_price"], nach_verwerfen["min_quantity"]))

    # Speichern: Preis, Mindestbestellmenge, Startdatum, Enddatum setzen und speichern
    oeffne(produkt)
    zelle("fixed_price", "66,00")
    zelle("min_quantity", "7")
    zelle("date_start", "01.01.2026")
    zelle("date_end", "31.12.2026")
    zeilen_nach_save = speichern()
    seite.screenshot(path=os.path.join(VZ, "02_gespeichert.png"), full_page=True)
    w = lese([regel_id])[0]
    print("   Nach dem Speichern:", json.dumps({k: str(w[k]) for k in
          ("fixed_price", "min_quantity", "date_start", "date_end")}, ensure_ascii=False))
    pruefe(abs(w["fixed_price"] - 66.0) < 0.001, "Speichern uebernimmt den Preis (66,00)")
    pruefe(w["min_quantity"] == 7.0, "Speichern uebernimmt die Mindestbestellmenge (7)")
    pruefe(lokal_datum(w["date_start"]) == "2026-01-01",
           "Speichern uebernimmt das Startdatum (01.01.2026, gespeichert %s)" % w["date_start"])
    pruefe(lokal_datum(w["date_end"]) == "2026-12-31",
           "Speichern uebernimmt das Enddatum (31.12.2026, gespeichert %s)" % w["date_end"])
    pruefe(zeilen_nach_save == 1, "Keine Zusatzzeile in der Regelliste entstanden")

    # Zurueckstellen auf den Ausgangszustand
    oeffne(produkt)
    zelle("fixed_price", ("%.2f" % start["fixed_price"]).replace(".", ","))
    zelle("min_quantity", "%g" % (start["min_quantity"] or 0))
    zelle("date_start", "")
    zelle("date_end", "")
    speichern()
    zurueck = lese([regel_id])[0]
    pruefe(zurueck == start,
           "Ausgangszustand wiederhergestellt (%s)" % json.dumps(
               {k: str(zurueck[k]) for k in ("fixed_price", "min_quantity", "date_start", "date_end")},
               ensure_ascii=False))

    # -------------------------------------------------- Punkt 4: Smart Button gegen Preiskalkulation
    print("\n=== 4. Smart Button gegen Preiskalkulation ===")
    oeffne(produkt, reiter=None)
    knopf = seite.evaluate("""() => { const b = [...document.querySelectorAll('.oe_stat_button')]
        .find(x => /Regel/.test(x.innerText)); return b ? b.innerText.replace(/\\s+/g,' ').trim() : null; }""")
    erwartet = anzahl([("product_tmpl_id", "=", produkt)])
    print("   Smart Button:", knopf, "| Regeln dieses Produkts:", erwartet)
    pruefe(knopf is not None and str(erwartet) in knopf, "Smart Button zaehlt die Regeln des Produkts")
    oeffne(produkt)
    sichtbar = zeilen_anzahl()
    texte = seite.evaluate("""() => [...document.querySelectorAll('.o_field_x2many_list tbody tr.o_data_row')]
        .map(tr => tr.innerText.replace(/\\s+/g,' ').trim())""")
    print("   Preiskalkulation zeigt:", sichtbar, "Zeile(n):", texte)
    pruefe(sichtbar == erwartet, "Preiskalkulation zeigt dieselbe Anzahl (%d)" % sichtbar)
    seite.evaluate("""() => { const b = [...document.querySelectorAll('.oe_stat_button')]
        .find(x => /Regel/.test(x.innerText)); if (b) b.click(); }""")
    seite.wait_for_timeout(8000)
    dom = seite.evaluate("""() => {
        const rows = [...document.querySelectorAll('.o_list_view tbody tr.o_data_row, .o_list_renderer tbody tr.o_data_row')];
        return {anzahl: rows.length,
                ids: rows.map(tr => tr.getAttribute('data-id')).filter(Boolean),
                text: rows.map(tr => tr.innerText.replace(/\\s+/g,' ').trim().slice(0,80)),
                url: location.href}; }""")
    print("   Smart-Button-Liste:", json.dumps(dom, ensure_ascii=False))
    ids_rpc = sorted(rpc("product.pricelist.item", "search", [[("product_tmpl_id", "=", produkt)]],
                         {"context": CTX}))
    pruefe(dom["anzahl"] == erwartet,
           "Smart-Button-Liste zeigt dieselbe Anzahl (%d)" % dom["anzahl"])
    werte_rpc = lese(ids_rpc)
    alle_da = all(any(("%.2f" % r["fixed_price"]).replace(".", ",") in t for t in dom["text"])
                  for r in werte_rpc)
    pruefe(alle_da and dom["anzahl"] == len(werte_rpc),
           "Smart-Button-Liste zeigt dieselben Datensaetze wie die Preiskalkulation "
           "(IDs %s, Werte %s)" % (ids_rpc, [t[:60] for t in dom["text"]]))
    seite.screenshot(path=os.path.join(VZ, "03_smartbutton_liste.png"), full_page=True)

    # Gegenprobe mit dem zweiten Produkt (andere Preislistenregel, anderer Preis)
    zweites = [r for r in regeln_start if r["product_tmpl_id"] and r["product_tmpl_id"][0] != produkt]
    if zweites:
        p2 = zweites[0]["product_tmpl_id"][0]
        ids2 = sorted(rpc("product.pricelist.item", "search", [[("product_tmpl_id", "=", p2)]],
                          {"context": CTX}))
        werte2 = lese(ids2)
        oeffne(p2)
        tab_zeilen2 = seite.evaluate("""() => [...document.querySelectorAll('.o_field_x2many_list tbody tr.o_data_row')]
            .map(tr => tr.innerText.replace(/\\s+/g,' ').trim())""")
        oeffne(p2, reiter=None)
        knopf2 = seite.evaluate("""() => { const b = [...document.querySelectorAll('.oe_stat_button')]
            .find(x => /Regel/.test(x.innerText)); return b ? b.innerText.replace(/\\s+/g,' ').trim() : null; }""")
        pruefe(len(tab_zeilen2) == len(werte2) and str(len(werte2)) in (knopf2 or ""),
               "Gegenprobe Produkt %s: Preiskalkulation %d Zeile(n), Smart Button '%s'"
               % (p2, len(tab_zeilen2), knopf2))
        pruefe(all(any(("%.2f" % r["fixed_price"]).replace(".", ",") in t for t in tab_zeilen2)
                   for r in werte2),
               "Gegenprobe: derselbe Regelwert in der Preiskalkulation (%s)"
               % [("%.2f" % r["fixed_price"]) for r in werte2])

    # -------------------------------------------------- Punkt 3: Abonnementvorlage oeffnen
    print("\n=== 3. Produkt mit Abonnementvorlage ===")
    abo = rpc("product.template", "search_read",
              [[("subscription_template_id", "!=", False)], ["id", "name", "subscription_template_id"]],
              {"context": CTX, "limit": 1})
    if abo:
        p_abo = abo[0]
        vorlage = rpc("sale.subscription.template", "read",
                      [[p_abo["subscription_template_id"][0]], ["name", "id"]], {"context": CTX})[0]
        print("   Produkt:", p_abo["name"], "| verknuepfte Vorlage:", vorlage)
        oeffne(p_abo["id"])
        feld = seite.evaluate("""() => { const e = document.querySelector("[name='subscription_template_id']");
            if (!e) return null;
            return {eingabe: e.querySelector('input') ? e.querySelector('input').value : null,
                    pfeil: !!e.querySelector('.o_external_button')}; }""")
        pruefe(feld and feld["eingabe"] == vorlage["name"],
               "Abonnementvorlage '%s' ist am Produkt verknuepft" % vorlage["name"])
        seite.evaluate("""() => { const l = document.querySelector("[name='subscription_template_id'] .o_external_button");
            if (l) l.click(); }""")
        seite.wait_for_timeout(7000)
        geoeffnet = seite.evaluate("""() => ({
            modal: !!document.querySelector('.modal'),
            formular_im_dialog: !!document.querySelector('.modal .o_form_view, .o_dialog .o_form_view'),
            dialog: !!document.querySelector('.o_dialog'),
            breadcrumb: (document.querySelector('.modal .o_breadcrumb') || document.querySelector('.o_breadcrumb') || {}).innerText || '',
            url: location.href,
            inhalt: (document.querySelector('.modal, .o_dialog') || document.body).innerText.replace(/\\s+/g,' ').slice(0, 200)})""")
        print("   Geoeffnet:", json.dumps(geoeffnet, ensure_ascii=False))
        geoeffnet_ok = (vorlage["name"] in json.dumps(geoeffnet, ensure_ascii=False)
                        and (geoeffnet["formular_im_dialog"] or geoeffnet["dialog"]
                             or "sale.subscription.template" in geoeffnet["url"]))
        pruefe(geoeffnet_ok,
               "Verknuepfte Abonnementvorlage wurde geoeffnet (Formular/Dialog mit '%s')"
               % vorlage["name"])
        seite.screenshot(path=os.path.join(VZ, "04_abo_vorlage.png"), full_page=True)
        seite.keyboard.press("Escape")
        seite.wait_for_timeout(2000)
        oeffne(p_abo["id"])
        angezeigt = seite.evaluate("""() => { const tr = document.querySelector('.o_notebook .tab-pane:not(.d-none) [name="subscription_template_id"]');
            return tr ? tr.innerText.replace(/\\s+/g,' ').trim() : ''; }""")
        pruefe(vorlage["name"] in angezeigt or feld["eingabe"] == vorlage["name"],
               "Verknuepfung bleibt nach dem Oeffnen erhalten")
    else:
        pruefe(False, "Kein Produkt mit Abonnementvorlage gefunden")

    # -------------------------------------------------- Punkt 5: deutsche Gruppenbeschriftung
    print("\n=== 5. Gruppenbeschriftung deutsch ===")
    oeffne(produkt)
    tabtext = seite.evaluate("""() => { const p = document.querySelector('.o_notebook .tab-pane:not(.d-none)');
        return p ? p.innerText.replace(/\\s+/g, ' ') : ''; }""")
    print("   Reitertext (Auszug):", tabtext[:220])
    pruefe("zusatz- und querverkauf" in tabtext.lower(), "Gruppentitel deutsch: 'Zusatz- und Querverkauf'")
    pruefe("upselling" not in tabtext.lower() and "cross-selling" not in tabtext.lower(),
           "Kein englischer Titel 'Upselling'/'Cross-Selling' mehr sichtbar")
    pruefe(seite.evaluate("() => !!document.querySelector(\"[name='optional_product_ids']\")"),
           "Feld 'Optionale Produkte' unveraendert vorhanden (Funktion unberuehrt)")
    pruefe(seite.evaluate("() => !!document.querySelector(\"[name='item_ids']\")"),
           "Abschnitt 'Preiskalkulation' mit item_ids vorhanden")
    seite.screenshot(path=os.path.join(VZ, "05_gruppentitel.png"), full_page=True)
    ctx.close()

# ---------------------------------------------------------------- Abschluss
regel_ids_ende = sorted(r["id"] for r in rpc("product.pricelist.item", "search_read",
                                             [[], ["id"]], {"context": CTX}))
pruefe(regel_ids_ende == regel_ids_start,
       "Abschluss: Regelbestand unveraendert (%s), keine Testdaten" % regel_ids_ende)
ende = lese([regel_id])[0]
pruefe(ende == start, "Abschluss: Testregel exakt im Ausgangszustand")
ok = sum(1 for e, _ in ERGEBNISSE if e)
print("\nErgebnis %s: %d OK / %d FEHL" % (INST, ok, len(ERGEBNISSE) - ok))
for e, t in ERGEBNISSE:
    if not e:
        print("   FEHL:", t)
print("Bilder:", VZ)
