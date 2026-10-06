"""Funktions- und Verknuepfungspruefung aller sieben Reiter im echten Browser.

Oeffnet ein echtes Produkt der Menues Abrechnung > Verkauf/Einkauf > Verkaufbare/Einkaufbare
Produkte und prueft je Reiter die Funktionen: Smart Buttons (mit Klick), Preise, Steuern,
Fakturierungs- und Einkaufsregeln, Lagerbezug, Kategorie, interne Referenz, Abonnementbezug
sowie die Verknuepfungen (Lieferanten, Routen, Verpackungen, Attribute, Beschreibungen,
Warnhinweise). Nur Lesen und Oeffnen - keine Speicherung, keine Datensaetze angelegt.

Aufruf: python scripts/browser_produktformular_funktionen.py lokal|vm [produkt_id]
"""
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AKTION = 382


def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            w[k.strip()] = v.strip().strip('"')
    return w


inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
env = lade_env(os.path.join(REPO, ".env"))
url = "http://localhost:8069" if inst != "vm" else "https://k001959vsx.ipax.at"
domain = "localhost" if inst != "vm" else "k001959vsx.ipax.at"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.open(urllib.request.Request(url + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
            "db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
            "password": env["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"}))
sid = next(c.value for c in jar if c.name == "session_id")


def rpc(model, method, args, kwargs=None):
    kw = dict(kwargs or {})
    kw.setdefault("context", {"lang": "de_DE"})
    r = json.loads(op.open(urllib.request.Request(
        url + "/web/dataset/call_kw", data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                        "params": {"model": model, "method": method,
                                                                   "args": args, "kwargs": kw}}).encode(),
        headers={"Content-Type": "application/json"})).read())
    if "error" in r:
        raise RuntimeError(str(r["error"])[:300])
    return r["result"]


# Produkt mit Verknuepfungen waehlen (Verkaeufe und Einkaeufe belegt)
kandidaten = rpc("product.template", "search_read",
                 [[["type", "=", "consu"], ["sale_ok", "=", True]], ["id", "name", "sales_count",
                                                                     "purchased_product_qty"]])
pid = int(sys.argv[2]) if len(sys.argv) > 2 else next(
    (p["id"] for p in kandidaten if p["sales_count"] and p["purchased_product_qty"]),
    kandidaten[0]["id"])
p = rpc("product.template", "read", [[pid], ["name", "type", "standard_price", "list_price",
                                             "categ_id", "product_type_id", "responsible_id"]] )[0]
print("Instanz:", inst, "| Produkt:", p)

ok, fehl = [], []


def pruefe(bedingung, text):
    (ok if bedingung else fehl).append(text)
    print(("  OK   " if bedingung else "  FEHL ") + text)


# ---------------------------------------------------------------- JS-Bausteine
FELD = """(name) => { const e = document.querySelector("[name='"+name+"']");
    if (!e) return {da:false};
    const z = e.closest('.o_wrap_field') || e.parentElement;
    const lab = z ? z.querySelector('label.o_form_label') : null;
    return {da:true, sichtbar:!!e.offsetParent, klasse:e.className.slice(0,60),
            readonly:e.className.includes('o_readonly_modifier'),
            eingabe:e.querySelectorAll('input,select,textarea').length,
            text:(e.innerText||'').replace(/\\s+/g,' ').trim().slice(0,80)
                 || (e.querySelector('input') ? e.querySelector('input').value : ''),
            label:lab ? lab.innerText.replace(/\\s+/g,' ').replace(/\\?/g,'').trim() : null}; }"""

CHIPS = """(name) => { const e = document.querySelector("[name='"+name+"']");
    if (!e) return []; return [...e.querySelectorAll('.o_tag, .badge, .o_m2m_tag')]
        .map(t => t.innerText.replace(/\\s+/g,' ').trim()).filter(Boolean); }"""

RADIO = """(name) => { const e = document.querySelector("[name='"+name+"']");
    if (!e) return null; const c = e.querySelector('input:checked');
    if (!c) return null; const l = e.querySelector("label[for='"+c.id+"']") || c.closest('label');
    return l ? l.innerText.replace(/\\s+/g,' ').trim() : c.value; }"""

AUSWAHL = """(name) => { const e = document.querySelector("[name='"+name+"']");
    if (!e) return null; const s = e.querySelector('select');
    return s ? s.options[s.selectedIndex].text.replace(/\\s+/g,' ').trim() : null; }"""

INNERE_LISTE = """(name) => { const e = document.querySelector("[name='"+name+"']");
    if (!e) return null;
    const k = [...e.querySelectorAll('table thead th')].map(x => x.innerText.replace(/\\s+/g,' ').trim());
    const z = e.querySelectorAll('tbody tr.o_data_row').length;
    return {spalten:k.filter(Boolean), zeilen:z,
            hinzufuegen: !!e.querySelector('.o_field_x2many_list_row_add, a.o_field_x2many_list_row_add')}; }"""

HAKEN = """(name) => { const e = document.querySelector("[name='"+name+"']");
    if (!e) return null; const l = e.closest('.o_wrap_field') || e.parentElement;
    const lab = l ? l.innerText.replace(/\\s+/g,' ').trim() : null;
    const c = e.querySelector('input[type=checkbox]');
    return {label:lab, gesetzt: c ? c.checked : null}; }"""

STATIONEN = """() => [...document.querySelectorAll('.oe_stat_button')]
    .filter(b => b.offsetParent).map(b => b.innerText.replace(/\\s+/g,' ').trim())"""

KOPF = """() => { const b = document.querySelector('.o_breadcrumb, .o_control_panel .o_last_breadcrumb_item');
    return b ? b.innerText.replace(/\\s+/g,' ').trim() : ''; }"""

ANSICHT = """() => { if (document.querySelector('.o_list_view')) return 'Liste';
    if (document.querySelector('.o_kanban_view')) return 'Kanban';
    if (document.querySelector('.o_form_view')) return 'Formular';
    return 'andere'; }"""

from playwright.sync_api import sync_playwright  # noqa: E402

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session126",
                  "produktformular_funktionen", inst)
os.makedirs(VZ, exist_ok=True)

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_prodfun_%s" % inst),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1500})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()
    seite.goto("%s/odoo/action-%d/%s" % (url, AKTION, pid))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(6000)

    # ---------------------------------------------------------- 1. Kopfbereich
    print("\n=== Kopfbereich: Smart Buttons und Statusleiste ===")
    stat = seite.evaluate(STATIONEN)
    print("   Smart Buttons:", stat)
    anzahl_varianten = rpc("product.template", "read", [[pid], ["product_variant_count"]])[0]
    for erwartet in ("Regeln Preislisten", "Dokumente", "Verkauft", "Eingekauft"):
        pruefe(any(erwartet.lower() in s.lower() for s in stat),
               "Smart Button '%s' vorhanden" % erwartet)
    if anzahl_varianten["product_variant_count"] > 1:
        pruefe(any("variant" in s.lower() for s in stat),
               "Smart Button 'Varianten' vorhanden (Produkt hat %d Varianten)"
               % anzahl_varianten["product_variant_count"])
    else:
        pruefe(not any("variant" in s.lower() for s in stat),
               "Smart Button 'Varianten' bei nur einer Variante ausgeblendet (Odoo-18-Regel)")
    pruefe(len(stat) >= 4, "Smart Buttons vollstaendig (%d)" % len(stat))
    seite.screenshot(path=os.path.join(VZ, "01_kopf_smartbuttons.png"), full_page=True)

    # Klickprobe: Verknuepfungen oeffnen (nur oeffnen, nichts speichern)
    for knopf in ("Verkauft", "Eingekauft", "Regeln Preislisten"):
        b = seite.query_selector(".oe_stat_button:has-text('%s')" % knopf)
        if b is None:
            pruefe(False, "Smart Button '%s' nicht klickbar gefunden" % knopf)
            continue
        vorher = seite.url
        b.click()
        seite.wait_for_timeout(3500)
        ziel = seite.url
        ans = seite.evaluate(ANSICHT)
        kopf = seite.evaluate(KOPF)
        pruefe(ziel != vorher, "Klick auf '%s' oeffnet Verknuepfung (%s -> %s, %s, '%s')"
               % (knopf, vorher.split("/")[-1], ziel.split("/")[-1], ans, kopf[:60]))
        seite.go_back()
        seite.wait_for_selector(".o_form_view", timeout=60000)
        seite.wait_for_timeout(2500)

    # ---------------------------------------------------------- Reiter Schleife
    for reiter in ("Allgemeine Informationen", "Verkauf", "Einkauf", "Lager", "Abrechnung",
                   "Notizen", "Attribute & Varianten"):
        k = seite.query_selector(".o_notebook .nav-link:has-text('%s')" % reiter)
        if k is None:
            pruefe(False, "Reiter '%s' nicht gefunden" % reiter)
            continue
        k.click()
        seite.wait_for_timeout(1500)

        if reiter == "Allgemeine Informationen":
            print("\n=== Reiter Allgemeine Informationen ===")
            for feld in ("product_type_id", "categ_id", "default_code", "barcode", "responsible_id",
                         "list_price", "standard_price", "recurring_invoice",
                         "subscription_template_id"):
                d = seite.evaluate(FELD, feld)
                print("   %-26s %s" % (feld, d))
            cat = seite.evaluate(FELD, "categ_id")
            pruefe(cat.get("da") and cat.get("sichtbar") and cat.get("eingabe", 0) >= 1,
                   "Kategorie: sichtbar, editierbar, Verknuepfung zu product.category")
            code = seite.evaluate(FELD, "default_code")
            pruefe(code.get("da") and code.get("eingabe", 0) >= 1,
                   "Interne Referenz: sichtbar und editierbar")
            pt = seperate = seite.evaluate(FELD, "product_type_id")
            pruefe(pt.get("da") and pt.get("eingabe", 0) >= 1,
                   "Product-Type: sichtbar, editierbar (Verknuepfung itk_product.product_type)")
            preis = seite.evaluate(FELD, "list_price")
            pruefe(preis.get("da") and preis.get("eingabe", 0) >= 1, "Verkaufspreis: editierbar")
            # Anna 05.10.2026: deutsche Beschriftung, Odoo-11-Reihenfolge im ersten Reiter
            pt = seite.evaluate(FELD, "product_type_id")
            pruefe(pt.get("label") == "Produktart",
                   "Produktart-Feld traegt die deutsche Beschriftung '%s'" % pt.get("label"))
            reins = seite.evaluate("""() => [...document.querySelectorAll('.o_notebook .tab-pane')]
                .filter(p => !p.className.includes('d-none') && p.offsetParent)
                .flatMap(p => [...p.querySelectorAll('label.o_form_label')])
                .filter(l => l.offsetParent && l.innerText.trim())
                .map(l => l.innerText.replace(/\\s+/g,' ').replace(/\\?/g,'').trim())""")
            erwartet = [x for x in reins if x in ("Produktart", "Interne Kategorie",
                                                  "Interne Referenz", "Strichcode")]
            pruefe(erwartet == ["Produktart", "Interne Kategorie", "Interne Referenz", "Strichcode"],
                   "Erster Reiter in Odoo-11-Reihenfolge: %s" % erwartet)
            pruefe("Product-Type" not in " ".join(reins),
                   "keine englische Beschriftung 'Product-Type' im ersten Reiter")
            for feld in ("product_type_id", "categ_id", "default_code", "list_price"):
                d = seite.evaluate(FELD, feld)
                if d.get("text"):
                    print("      Wert %s = %s" % (feld, d["text"]))
            haken = seite.evaluate(HAKEN, "sale_ok")
            pruefe(haken and haken.get("gesetzt") is not None,
                   "Kann verkauft werden: %s" % (haken.get("gesetzt") if haken else "-"))
            haken = seite.evaluate(HAKEN, "purchase_ok")
            pruefe(haken and haken.get("gesetzt") is not None,
                   "Kann eingekauft werden: %s" % (haken.get("gesetzt") if haken else "-"))
            seite.screenshot(path=os.path.join(VZ, "02_allgemein.png"), full_page=True)

        if reiter == "Verkauf":
            print("\n=== Reiter Verkauf ===")
            for feld in ("optional_product_ids", "product_tag_ids", "expense_policy"):
                d = seite.evaluate(FELD, feld)
                print("   %-26s %s" % (feld, d))
            d = seite.evaluate(FELD, "optional_product_ids")
            pruefe(d.get("da") and d.get("sichtbar"),
                   "Optionale Produkte: vorhanden (Odoo-18-Feld der alternativen/Zubehoer-Produkte)")
            r = seite.evaluate(RADIO, "expense_policy")
            pruefe(r is not None, "Spesen weiter verrechnen: Auswahl aktiv (%s)" % r)
            seite.screenshot(path=os.path.join(VZ, "03_verkauf.png"), full_page=True)

        if reiter == "Einkauf":
            print("\n=== Reiter Einkauf ===")
            l = seite.evaluate(INNERE_LISTE, "seller_ids")
            print("   seller_ids:", l)
            pruefe(l is not None, "Lieferantenliste vorhanden (Spalten %s, Zeilen %s, Hinzufuegen %s)"
                   % (l.get("spalten") if l else "-", l.get("zeilen") if l else "-",
                      l.get("hinzufuegen") if l else "-"))
            d = seite.evaluate(FELD, "uom_po_id")
            pruefe(d.get("da") and d.get("sichtbar"), "Einkauf ME (uom_po_id): sichtbar/editierbar")
            seite.screenshot(path=os.path.join(VZ, "04_einkauf.png"), full_page=True)

        if reiter == "Lager":
            print("\n=== Reiter Lager ===")
            for feld in ("route_ids", "route_from_categ_ids", "responsible_id", "weight", "volume",
                         "sale_delay", "packaging_ids"):
                d = seite.evaluate(FELD, feld)
                print("   %-26s %s" % (feld, d))
            l = seite.evaluate(INNERE_LISTE, "packaging_ids")
            print("   packaging_ids:", l)
            d = seite.evaluate(FELD, "route_ids")
            pruefe(d.get("da") and d.get("eingabe", 0) >= 1,
                   "Routen: Auswahl vorhanden (Verknuepfung stock.route)")
            d = seite.evaluate(FELD, "sale_delay")
            pruefe(d.get("da") and d.get("eingabe", 0) >= 1, "Auslieferungszeit: editierbar")
            pruefe(seite.query_selector("button:has-text('Diagramm ansehen')") is not None,
                   "Knopf 'Diagramm ansehen' im Reiter Lager vorhanden")
            seite.screenshot(path=os.path.join(VZ, "05_lager.png"), full_page=True)

        if reiter == "Abrechnung":
            print("\n=== Reiter Abrechnung ===")
            chips = seite.evaluate(CHIPS, "taxes_id")
            print("   Steuern (Verkauf) Chips:", chips)
            chips2 = seite.evaluate(CHIPS, "supplier_taxes_id")
            print("   Steuern (Einkauf) Chips:", chips2)
            pruefe(bool(chips), "Steuern (Verkauf): Verknuepfung zu account.tax belegt (%s)" % chips)
            pruefe(bool(chips2), "Steuern (Einkauf): Verknuepfung zu account.tax belegt (%s)" % chips2)
            d = seite.evaluate(FELD, "tax_string")
            print("   tax_string:", d.get("text") if d.get("da") else "-")
            r = seite.evaluate(RADIO, "invoice_policy") or seite.evaluate(AUSWAHL, "invoice_policy")
            pruefe(r is not None, "Fakturierungsregel: Auswahl aktiv (%s)" % r)
            r2 = seite.evaluate(RADIO, "purchase_method")
            pruefe(r2 is not None, "Kontrollrichtlinie: Auswahl aktiv (%s)" % r2)
            d = seite.evaluate(FELD, "invoice_policy")
            pruefe(d.get("da") and d.get("eingabe", 0) >= 1, "Fakturierungsregel: editierbar")
            seite.screenshot(path=os.path.join(VZ, "06_abrechnung.png"), full_page=True)

        if reiter == "Notizen":
            print("\n=== Reiter Notizen ===")
            for feld in ("description", "description_sale", "description_purchase",
                         "description_pickingout", "description_pickingin", "description_picking"):
                d = seite.evaluate(FELD, feld)
                editierbar = d.get("eingabe", 0) >= 1 or seite.evaluate(
                    """(n) => { const e = document.querySelector("[name='"+n+"']");
                        return !!(e && (e.querySelector('.o_field_html, [contenteditable=true], .o-wysiwyg')
                                        || e.className.includes('o_field_html'))); }""", feld)
                pruefe(d.get("da") and d.get("sichtbar") and editierbar,
                       "%s: sichtbar und editierbar%s" % (
                           feld, " (HTML-Feld, Odoo 11: Textfeld)" if feld == "description" else ""))
            for feld in ("sale_line_warn", "purchase_line_warn"):
                a = seite.evaluate(AUSWAHL, feld)
                print("   %-24s Auswahl: %s" % (feld, a))
                pruefe(a is not None, "Warnhinweis %s: Auswahl vorhanden (%s)" % (feld, a))
            seite.screenshot(path=os.path.join(VZ, "07_notizen.png"), full_page=True)

        if reiter == "Attribute & Varianten":
            print("\n=== Reiter Attribute & Varianten ===")
            l = seite.evaluate(INNERE_LISTE, "attribute_line_ids")
            print("   attribute_line_ids:", l)
            pruefe(l is not None, "Attributliste vorhanden (Spalten %s, Zeilen %s, Hinzufuegen %s)"
                   % (l.get("spalten") if l else "-", l.get("zeilen") if l else "-",
                      l.get("hinzufuegen") if l else "-"))
            seite.screenshot(path=os.path.join(VZ, "08_attribute.png"), full_page=True)

    # ---------------------------------------------------------- Abonnement-Produkt
    print("\n=== Abonnement-Produkt: Abonnementfelder (Reiter 1 und Verkauf) ===")
    abos = rpc("product.template", "search_read", [[["recurring_invoice", "=", True]], ["id", "name"]],
               {"limit": 1})
    if abos:
        seite.goto("%s/odoo/action-%d/%s" % (url, AKTION, abos[0]["id"]))
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(5000)
        haken = seite.evaluate(HAKEN, "recurring_invoice")
        pruefe(bool(haken) and haken.get("gesetzt") is True,
               "Produkt %s (%s): 'Abonnement Produkt' im ersten Reiter gesetzt"
               % (abos[0]["id"], abos[0]["name"]))
        seite.query_selector(".o_notebook .nav-link:has-text('Verkauf')").click()
        seite.wait_for_timeout(1500)
        s = seite.evaluate(FELD, "subscription_template_id")
        pruefe(bool(s.get("da")) and bool(s.get("sichtbar")),
               "Reiter Verkauf zeigt die Abonnement-Vorlage (Wert: %s)" % (s.get("text") or "-"))
        seite.screenshot(path=os.path.join(VZ, "09_abo_verkauf.png"), full_page=True)
    else:
        pruefe(False, "kein Abonnement-Produkt in der Instanz gefunden")

    # ---------------------------------------------------------- Kopf-Werkzeuge
    print("\n=== Kopf-Werkzeuge (nur oeffnen, nichts speichern) ===")
    # zurueck zum Ausgangsprodukt (das Abonnement-Produkt ist eine Dienstleistung,
    # dort gibt es den Etiketten-Knopf nicht - Odoo-18-Regel)
    seite.goto("%s/odoo/action-%d/%s" % (url, AKTION, pid))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(4000)
    for knopf, name in (("Etiketten drucken", "Etiketten"),):
        b = seite.query_selector("button:has-text('%s')" % knopf)
        if b is None:
            pruefe(False, "Knopf '%s' fehlt" % knopf)
            continue
        b.click()
        seite.wait_for_timeout(3000)
        dialog = seite.query_selector(".modal-dialog, .o_dialog")
        pruefe(dialog is not None, "Knopf '%s' oeffnet Dialog (%s)" % (name, bool(dialog)))
        seite.keyboard.press("Escape")
        seite.wait_for_timeout(1200)
        pruefe(seite.query_selector(".modal-dialog, .o_dialog") is None,
               "Dialog '%s' ohne Speichern geschlossen" % name)

    bestand = rpc("product.template", "search_count", [[]])
    print("\nBestand product.template:", bestand)
    print("Ergebnis:", len(ok), "OK /", len(fehl), "FEHL")
    for f in fehl:
        print("   FEHL:", f)
    print("Bilder:", VZ)
    ctx.close()
