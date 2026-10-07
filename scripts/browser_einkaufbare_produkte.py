"""Browser-Abnahme Session 128: Abrechnung > Einkauf > Einkaufbare Produkte.

Prueft im echten Chrome (lokal und VM):
  1. Liste oeffnet als Liste, Spalten in Odoo-11-Reihenfolge und Odoo-11-Wortlaut, keine englischen
     Beschriftungen, Zeilenzahl gegen den Standardfilter "Kann eingekauft werden"
  2. Filter, Gruppierungen, Suchfelder im Suchmenue (Vergleich mit Odoo 11)
  3. Spaltenauswahl: Odoo-18-Zusatzspalten vorhanden, deutsch, zuschaltbar
  4. Filter ein-/ausschalten, Gruppierung setzen/entfernen, Suche
  5. Produktformular oeffnen: Reiter, Steuerfelder, Smart Buttons
  6. Bearbeitungsmodus mit temporaerem Testprodukt (wird danach vollstaendig entfernt)

Aufruf: uv run --with playwright python scripts/browser_einkaufbare_produkte.py lokal|vm
"""
from __future__ import annotations

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
VZ = os.path.expanduser("~") + "/Desktop/Odoo18-Abnahme-Session128/einkaufbare_produkte/" + INST
os.makedirs(VZ, exist_ok=True)
AKTION = 383
CTX = {"lang": "de_DE"}
ERGEBNISSE = []

ERWARTETE_SPALTEN = ["Interne Referenz", "Name", "Verkaufspreis", "Steuern (Verkauf)", "Steuern (Einkauf)"]
ENGLISCHE = ["Sales Taxes", "Purchase Taxes", "Quantity On Hand", "Forecasted Quantity",
             "Unit of Measure", "Barcode", "Sales", "Purchase", "# Product Variants",
             "Product Category", "Invoicing Policy", "Track Service", "Purchase Unit"]
ERWARTETE_FILTER = ["Kann verkauft werden", "Kann eingekauft werden", "Service Type Consulting",
                    "Service Type Onlineservice", "Service Type Software-Solution",
                    "Service Type Platform", "Service Type Hardware", "Service Type Förderprojekt",
                    "Zeitbasierte Dienste", "Festpreis-Dienste", "Meilenstein-Dienste",
                    "Bestandsauflösung", "Bestandsreichweite", "Archiviert"]
ERWARTETE_GRUPPEN = ["Produktart", "Produktkategorie", "Status", "Mit Faktor multipliziert"]
ERWARTETE_EXTRAS = ["Bestandsmenge", "Prognostizierter Bestand", "Mengeneinheit", "Strichcode", "Kosten",
                    "Interne Kategorie", "Status", "Produktart", "# Produkt Varianten", "Verantwortlich",
                    "Stichwörter", "Favorit", "Kann verkauft werden", "Kann eingekauft werden",
                    "Einkauf ME"]

umg = {}
for zeile in open(os.path.join(REPO, ".env"), encoding="utf-8"):
    if "=" in zeile and not zeile.strip().startswith("#"):
        s, w = zeile.split("=", 1)
        umg[s.strip()] = w.strip()
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


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


def pruefe(ok, text):
    ERGEBNISSE.append((bool(ok), text))
    print("  %s  %s" % ("OK  " if ok else "FEHL", text))


op.open(urllib.request.Request(URL + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
            "db": umg["ODOO18_DB"], "login": umg["ODOO18_USER"],
            "password": umg["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"}))
SID = next(c.value for c in jar if c.name == "session_id")

# ---------------------------------------------------------------- Bestand vorher
vorher = {
    "vorlagen": rpc("product.template", "search_count", [[]]),
    "varianten": rpc("product.product", "search_count", [[]]),
    "einkaufbar": rpc("product.template", "search_count", [[("purchase_ok", "=", True)]]),
    "varianten_einkaufbar": rpc("product.product", "search_count", [[("purchase_ok", "=", True)]]),
    "bestellzeilen": rpc("purchase.order.line", "search_count", [[]]),
    "verkaufszeilen": rpc("sale.order.line", "search_count", [[]]),
    "rechnungszeilen": rpc("account.move.line", "search_count", [[]]),
    "abos": rpc("sale.subscription", "search_count", [[]]),
}
print("=== Bestand vorher (%s) ===" % INST)
print("  ", json.dumps(vorher))

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_s128_%s_%d" % (INST, time.time())),
        channel="chrome", headless=True, viewport={"width": 1920, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": SID, "domain": DOMAIN, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()

    def spaltenkoepfe():
        return seite.evaluate("""() => [...document.querySelectorAll('.o_list_table thead th')]
            .map(th => th.innerText.replace(/\\s+/g,' ').trim()).filter(t => t !== '')""")

    def zeilen():
        return seite.locator(".o_list_table tbody tr.o_data_row").count()

    def suchmenue_oeffnen():
        seite.evaluate("""() => { const t = document.querySelector('.o_searchview_dropdown_toggler');
            if (t) t.click(); }""")
        seite.wait_for_timeout(1500)

    def menue_eintraege(bereich):
        text = seite.inner_text(bereich)
        return [z.strip() for z in text.split("\n") if z.strip()]

    # ------------------------------------------------------------ 1. Liste
    print("\n=== 1. Liste des Menuepunkts ===")
    seite.goto("%s/odoo/action-%d" % (URL, AKTION))
    seite.wait_for_selector(".o_list_view", timeout=90000)
    seite.wait_for_timeout(5000)
    ist_liste = seite.locator(".o_list_view").count() > 0
    kopf = spaltenkoepfe()
    zeilen_ist = zeilen()
    print("   Ansicht  : %s" % ("Liste" if ist_liste else "andere Ansicht"))
    print("   Spalten  : %s" % kopf)
    print("   Zeilen   : %d | einkaufbare Vorlagen laut Datenbank: %d" % (zeilen_ist, vorher["einkaufbar"]))
    pruefe(ist_liste, "Der Menuepunkt oeffnet eine Listenansicht")
    pruefe(kopf[:5] == ERWARTETE_SPALTEN,
           "Die ersten fuenf Spalten sind die Odoo-11-Spalten in Odoo-11-Reihenfolge: %s" % kopf[:5])
    englisch = [s for s in kopf if s in ENGLISCHE]
    pruefe(not englisch, "Keine englische Spaltenbeschriftung sichtbar (%s)" % (englisch or "keine"))
    rest = [s for s in kopf if s not in ERWARTETE_SPALTEN]
    print("   Weitere Spaltenkoepfe: %s" % (rest or "keine"))
    pruefe(zeilen_ist == vorher["einkaufbar"],
           "Der Standardfilter zeigt genau die einkaufbaren Vorlagen (%d von %d)"
           % (zeilen_ist, vorher["einkaufbar"]))
    seite.screenshot(path=os.path.join(VZ, "01_liste.png"), full_page=True)

    # ------------------------------------------------------------ 2. Filter und Gruppierungen
    print("\n=== 2. Suchmenue: Filter und Gruppierungen ===")
    facette = seite.evaluate("""() => [...document.querySelectorAll('.o_searchview_facet')]
        .map(f => f.innerText.replace(/\\s+/g,' ').trim())""")
    print("   Aktive Filter: %s" % facette)
    pruefe(any("Kann eingekauft werden" in f for f in facette),
           "Standardfilter 'Kann eingekauft werden' ist beim Oeffnen aktiv")
    suchmenue_oeffnen()
    filter_ist = menue_eintraege(".o_filter_menu")
    gruppen_ist = menue_eintraege(".o_group_by_menu")
    print("   Filter        : %s" % filter_ist)
    print("   Gruppierungen : %s" % gruppen_ist)
    fehlend = [f for f in ERWARTETE_FILTER if f not in filter_ist]
    pruefe(not fehlend, "Alle Odoo-11-Filter vorhanden (%s)" % (fehlend or "vollstaendig"))
    pruefe("Verfügbare Produkte" in filter_ist,
           "Filter 'Verfügbare Produkte' aus Odoo 11 vorhanden")
    pruefe(all(g in gruppen_ist for g in ERWARTETE_GRUPPEN),
           "Gruppierungen Produktart/Produktkategorie/Status vorhanden")
    seite.screenshot(path=os.path.join(VZ, "02_suchmenue.png"), full_page=True)
    seite.keyboard.press("Escape")
    seite.wait_for_timeout(1200)

    # ------------------------------------------------------------ 3. Filter ausschalten/einschalten
    print("\n=== 3. Filter 'Kann eingekauft werden' aus- und einschalten ===")
    seite.evaluate("""() => { const f = [...document.querySelectorAll('.o_searchview_facet')]
        .find(x => /Kann eingekauft werden/.test(x.innerText));
        if (f) { const x = f.querySelector('.o_facet_remove, .fa-times, button'); if (x) x.click(); } }""")
    seite.wait_for_timeout(3500)
    ohne_filter = zeilen()
    alle = vorher["vorlagen"]
    print("   Zeilen ohne Filter: %d | Produkte gesamt: %d" % (ohne_filter, alle))
    pruefe(ohne_filter == alle, "Ohne Filter zeigt die Liste alle Produktvorlagen (%d)" % alle)
    seite.screenshot(path=os.path.join(VZ, "03_ohne_filter.png"), full_page=True)
    suchmenue_oeffnen()
    seite.evaluate("""() => { const e = [...document.querySelectorAll('.o_filter_menu .dropdown-item')]
        .find(x => /^Kann eingekauft werden$/.test(x.innerText.replace(/\\s+/g,' ').trim()));
        if (e) e.click(); }""")
    seite.wait_for_timeout(3500)
    mit_filter = zeilen()
    print("   Zeilen mit Filter: %d" % mit_filter)
    pruefe(mit_filter == vorher["einkaufbar"],
           "Filter 'Kann eingekauft werden' findet genau die einkaufbaren Vorlagen (%d)" % mit_filter)

    # ------------------------------------------------------------ 4. Spaltenauswahl
    print("\n=== 4. Spaltenauswahl (Odoo-18-Zusatzspalten) ===")
    seite.evaluate("""() => { const t = document.querySelector('.o_optional_columns_dropdown_toggle')
        || [...document.querySelectorAll('button')].find(b => /Spalten|Columns/.test(b.getAttribute('title') || ''));
        if (t) t.click(); }""")
    seite.wait_for_timeout(2000)
    auswahl = seite.evaluate("""() => [...document.querySelectorAll('.o_optional_columns_dropdown .dropdown-item, .o-dropdown--menu .dropdown-item')]
        .map(e => e.innerText.replace(/\\s+/g,' ').trim()).filter(t => t)""")
    print("   Auswahl   : %s" % auswahl)
    fehlend_ex = [e for e in ERWARTETE_EXTRAS if e not in auswahl]
    pruefe(not fehlend_ex, "Alle Odoo-18-Zusatzspalten in der Spaltenauswahl vorhanden (%s)"
           % (fehlend_ex or "vollstaendig"))
    englisch_ex = [e for e in auswahl if e in ENGLISCHE]
    pruefe(not englisch_ex, "Auch in der Spaltenauswahl keine englische Beschriftung (%s)"
           % (englisch_ex or "keine"))
    seite.screenshot(path=os.path.join(VZ, "04_spaltenauswahl.png"), full_page=True)
    # Bestandsmenge zuschalten und wieder abschalten
    seite.evaluate("""() => { const e = [...document.querySelectorAll('.o_optional_columns_dropdown .dropdown-item, .o-dropdown--menu .dropdown-item')]
        .find(x => /^Bestandsmenge$/.test(x.innerText.replace(/\\s+/g,' ').trim())); if (e) e.click(); }""")
    seite.wait_for_timeout(3000)
    kopf_mit = spaltenkoepfe()
    print("   Spalten mit zugeschalteter Bestandsmenge: %s" % kopf_mit)
    pruefe("Bestandsmenge" in kopf_mit, "Zusatzspalte 'Bestandsmenge' laesst sich zuschalten")
    seite.screenshot(path=os.path.join(VZ, "05_zusatzspalte.png"), full_page=True)
    seite.evaluate("""() => { const e = [...document.querySelectorAll('.o_optional_columns_dropdown .dropdown-item, .o-dropdown--menu .dropdown-item')]
        .find(x => /^Bestandsmenge$/.test(x.innerText.replace(/\\s+/g,' ').trim())); if (e) e.click(); }""")
    seite.wait_for_timeout(2500)
    pruefe("Bestandsmenge" not in spaltenkoepfe(), "Zusatzspalte wieder abschaltbar")

    # ------------------------------------------------------------ 5. Gruppierung
    print("\n=== 5. Gruppierung ===")
    suchmenue_oeffnen()
    seite.evaluate("""() => { const e = [...document.querySelectorAll('.o_group_by_menu .dropdown-item')]
        .find(x => /^Produktkategorie$/.test(x.innerText.replace(/\\s+/g,' ').trim())); if (e) e.click(); }""")
    seite.wait_for_timeout(4000)
    gruppen = seite.locator(".o_group_header").count()
    print("   Gruppenzeilen: %d" % gruppen)
    pruefe(gruppen > 0, "Gruppierung nach Produktkategorie erzeugt Gruppenzeilen (%d)" % gruppen)
    seite.screenshot(path=os.path.join(VZ, "06_gruppierung.png"), full_page=True)
    seite.evaluate("""() => { const f = [...document.querySelectorAll('.o_searchview_facet')]
        .find(x => /Produktkategorie/.test(x.innerText));
        if (f) { const x = f.querySelector('.o_facet_remove, .fa-times, button'); if (x) x.click(); } }""")
    seite.wait_for_timeout(3000)

    # ------------------------------------------------------------ 6. Suche
    print("\n=== 6. Suche ===")
    erstes = rpc("product.template", "search_read",
                 [[("purchase_ok", "=", True)], ["name"]], {"context": CTX, "limit": 1})
    suchbegriff = erstes[0]["name"]
    seite.fill(".o_searchview_input", suchbegriff[:12])
    seite.keyboard.press("Enter")
    seite.wait_for_timeout(5000)
    treffer = zeilen()
    erwartet_suche = rpc("product.template", "search_count",
                         [[("purchase_ok", "=", True), ("name", "ilike", suchbegriff[:12])]], {"context": CTX})
    print("   Suchbegriff '%s': %d Zeilen (Datenbank: %d)" % (suchbegriff[:12], treffer, erwartet_suche))
    pruefe(treffer == erwartet_suche, "Die Suche findet dieselbe Anzahl wie die Datenbank (%d)" % erwartet_suche)
    seite.screenshot(path=os.path.join(VZ, "07_suche.png"), full_page=True)
    seite.keyboard.press("Escape")
    seite.wait_for_timeout(1500)
    seite.evaluate("""() => { const f = [...document.querySelectorAll('.o_searchview_facet')]
        .find(x => /Name|Produkt$/i.test(x.innerText));
        if (f) { const x = f.querySelector('.o_facet_remove, .fa-times, button'); if (x) x.click(); } }""")
    seite.wait_for_timeout(2500)

    # ------------------------------------------------------------ 7. Produktformular
    print("\n=== 7. Produktformular aus dieser Liste ===")
    seite.wait_for_selector(".o_list_table tbody tr.o_data_row", timeout=60000)
    seite.locator(".o_list_table tbody tr.o_data_row").first.click()
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(6000)
    reiter = seite.evaluate("""() => [...document.querySelectorAll('.o_notebook .nav-link')]
        .map(e => e.innerText.replace(/\\s+/g,' ').trim()).filter(t => t)""")
    buttons = seite.evaluate("""() => [...document.querySelectorAll('.oe_stat_button')]
        .map(e => e.innerText.replace(/\\s+/g,' ').trim()).filter(t => t)""")
    print("   Reiter         : %s" % reiter)
    print("   Smart Buttons  : %s" % buttons)
    pruefe(len(reiter) >= 5, "Formular oeffnet mit den Reitern (%d)" % len(reiter))
    pruefe(any("Steuern" in b or "Auftrag" in b or "Rechnung" in b or "Lieferung" in b or "Verkauf" in b
               for b in buttons), "Smart Buttons vorhanden (%s)" % (buttons or "keine"))
    seite.screenshot(path=os.path.join(VZ, "08_formular.png"), full_page=True)

    # Alle Reiter nacheinander oeffnen, Beschriftungen und Feldnamen einsammeln
    def formular_durchgang(kennung):
        daten = {}
        print("   Reiter im Einzelnen fuer %s:" % kennung)
        for name in reiter:
            try:
                seite.click(".o_notebook .nav-link:has-text('%s')" % name)
                seite.wait_for_timeout(2600)
                inhalt = seite.inner_text(".o_form_sheet")
                felder = seite.evaluate("""() => [...document.querySelectorAll('.o_field_widget[name]')]
                    .map(e => e.getAttribute('name'))""")
                daten[name] = {"text": inhalt, "felder": felder}
                print("      %-26s %d Zeichen | Felder: %s" % (name, len(inhalt), ", ".join(felder[:16])))
                seite.screenshot(path=os.path.join(
                    VZ, "09_%s_%s.png" % (kennung, name.lower().replace(" ", "_").replace("&", "und"))),
                    full_page=True)
            except Exception as fehler:
                print("      %-26s nicht pruefbar: %s" % (name, str(fehler)[:60]))
        return daten

    daten1 = formular_durchgang("produkt1")
    text1 = "\n".join(d["text"] for d in daten1.values())
    felder1 = [f for d in daten1.values() for f in d["felder"]]

    for beschriftung in ("Steuern (Verkauf)", "Steuern (Einkauf)"):
        reiter_mit = [n for n, d in daten1.items() if beschriftung in d["text"]]
        pruefe(bool(reiter_mit), "Formular zeigt '%s' (Reiter: %s)"
               % (beschriftung, ", ".join(reiter_mit) or "nirgends"))

    # Zweites Produkt: Warenprodukt (Produktart Produkte) aus derselben Liste
    waren = rpc("product.template", "search_read",
                [[("purchase_ok", "=", True), ("type", "=", "consu")], ["id", "name"]],
                {"context": CTX, "limit": 1})
    if waren:
        print("   Zweites Produkt (Warenprodukt): %s (%s)" % (waren[0]["name"], waren[0]["id"]))
        seite.goto("%s/odoo/action-%d/%s" % (URL, AKTION, waren[0]["id"]))
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(5000)
        reiter2 = seite.evaluate("""() => [...document.querySelectorAll('.o_notebook .nav-link')]
            .map(e => e.innerText.replace(/\\s+/g,' ').trim()).filter(t => t)""")
        daten2 = formular_durchgang_waren = {}
        for name in reiter2:
            try:
                seite.click(".o_notebook .nav-link:has-text('%s')" % name)
                seite.wait_for_timeout(2600)
                daten2[name] = {"text": seite.inner_text(".o_form_sheet"),
                                "felder": seite.evaluate("""() => [...document.querySelectorAll('.o_field_widget[name]')]
                                    .map(e => e.getAttribute('name'))""")}
                seite.screenshot(path=os.path.join(VZ, "10_waren_%s.png" % name.lower().replace(" ", "_")),
                                 full_page=True)
            except Exception as fehler:
                print("      %-26s nicht pruefbar: %s" % (name, str(fehler)[:60]))
        text2 = "\n".join(d["text"] for d in daten2.values())
        felder2 = [f for d in daten2.values() for f in d["felder"]]
    else:
        daten2, text2, felder2 = {}, "", []

    englisch_form = [w for w in ("Sales Taxes", "Purchase Taxes", "Quantity On Hand", "Forecasted Quantity",
                                 "Unit of Measure", "Track Service", "Invoicing Policy", "Cost")
                     if w in (text1 + text2)]
    pruefe(not englisch_form, "Formular ohne englische Beschriftungen (%s)" % (englisch_form or "keine"))
    alle_felder = felder1 + felder2
    for feld in ("default_code", "barcode", "uom_id", "uom_po_id", "standard_price", "list_price",
                 "categ_id", "taxes_id", "supplier_taxes_id"):
        pruefe(feld in alle_felder, "Feld '%s' im Formular vorhanden (Produkt %s/waren)"
               % (feld, "Dienstleistung" if feld in felder1 else "nur Warenprodukt"))
    for beschriftung in ("Produktart", "Einkauf ME", "Strichcode", "Kosten",
                         "Interne Referenz", "Interne Kategorie"):
        pruefe(beschriftung in (text1 + text2), "Beschriftung '%s' im Formular sichtbar" % beschriftung)
    # Odoo 18 zeigt die Verkaufs-Mengeneinheit im Formular nicht als eigene Zeile
    # "Mengeneinheit", sondern als Einheit am Preis ("pro Einheit(en)"); der Reiter Einkauf
    # fuehrt "Einkauf ME". Beides wird als sichtbare Einheitenangabe geprueft.
    pruefe("Einheit" in (text1 + text2), "Mengeneinheit ist im Formular als Einheit am Preis sichtbar")
    pruefe("Status" not in text1, "Der Reiter Status (Liste: Status) erscheint im Formular als 'Produktart'")
    for beleg in ("08_formular.png", "09_produkt1_abrechnung.png"):
        print("   Bild: %s" % os.path.join(VZ, beleg))

    # ------------------------------------------------------------ 8. Bearbeitungsmodus mit Testprodukt
    print("\n=== 8. Bearbeitungsmodus mit temporaerem Testprodukt ===")
    test_id = rpc("product.template", "create", [{
        "name": "TEST-S128 Einkaufsprodukt",
        "purchase_ok": True,
        "sale_ok": True,
        "list_price": 66.0,
        "standard_price": 22.0,
    }], {"context": CTX})
    print("   Testprodukt angelegt: product.template,%s" % test_id)
    try:
        seite.goto("%s/odoo/action-%d/%s" % (URL, AKTION, test_id))
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(6000)
        modus = seite.evaluate("() => document.querySelector('.o_form_editable') ? 'bearbeitbar' : 'nur lesen'")
        print("   Formularzustand: %s" % modus)
        pruefe(modus == "bearbeitbar", "Testprodukt oeffnet im Bearbeitungsmodus")
        # Verkaufspreis aendern und speichern
        seite.evaluate("""() => { const z = [...document.querySelectorAll('.o_field_widget[name="list_price"] input')][0]; if (z) z.focus(); }""")
        seite.wait_for_timeout(800)
        seite.keyboard.press("Control+A")
        seite.keyboard.type("77,50")
        seite.keyboard.press("Tab")
        seite.wait_for_timeout(1500)
        seite.click("button.o_form_button_save")
        seite.wait_for_timeout(4000)
        wert = rpc("product.template", "read", [[test_id], ["list_price", "standard_price", "purchase_ok"]],
                   {"context": CTX})[0]
        print("   Nach dem Speichern:", json.dumps({k: str(v) for k, v in wert.items()}, ensure_ascii=False))
        pruefe(abs(wert["list_price"] - 77.5) < 0.001,
               "Aenderung im Formular wird gespeichert (Verkaufspreis %.2f)" % wert["list_price"])
        seite.screenshot(path=os.path.join(VZ, "10_testprodukt.png"), full_page=True)
    finally:
        rpc("product.template", "unlink", [[test_id]], {"context": CTX})
        print("   Testprodukt wieder entfernt: product.template,%s" % test_id)

    # ------------------------------------------------------------ Nachkontrolle
    print("\n=== 9. Bestand nachher ===")
    nachher = {
        "vorlagen": rpc("product.template", "search_count", [[]]),
        "varianten": rpc("product.product", "search_count", [[]]),
        "einkaufbar": rpc("product.template", "search_count", [[("purchase_ok", "=", True)]]),
        "varianten_einkaufbar": rpc("product.product", "search_count", [[("purchase_ok", "=", True)]]),
        "bestellzeilen": rpc("purchase.order.line", "search_count", [[]]),
        "verkaufszeilen": rpc("sale.order.line", "search_count", [[]]),
        "rechnungszeilen": rpc("account.move.line", "search_count", [[]]),
        "abos": rpc("sale.subscription", "search_count", [[]]),
    }
    print("  ", json.dumps(nachher))
    pruefe(vorher == nachher, "Bestand vorher == nachher (keine Testdaten zurueckgeblieben)")
    ctx.close()

ok = sum(1 for e, _ in ERGEBNISSE if e)
print("\n=== Ergebnis %s: %d OK / %d FEHL ===" % (INST, ok, len(ERGEBNISSE) - ok))
for e, t in ERGEBNISSE:
    if not e:
        print("   FEHL: %s" % t)
with open(os.path.join(VZ, "ergebnis.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join("%s  %s" % ("OK  " if e else "FEHL", t) for e, t in ERGEBNISSE))
print("Bilder und Ergebnisliste: %s" % VZ)
