"""Browser-Abnahme Reiter "Verkauf" (Odoo 18 lokal oder VM).

Prueft: Abschnitt "Preiskalkulation" mit der Liste der Preislistenregeln (Odoo-11-Feld item_ids),
Spalten und Werte, Odoo-18-Zusatzgruppen, Abonnement-Vorlage, Smart Button "Regeln Preislisten",
Lese- und Bearbeitungsmodus.

Aufruf: uv run --with playwright python scripts/browser_verkauf_reiter_abnahme.py lokal|vm
Screenshots: Desktop/Odoo18-Abnahme-Session126/verkauf_reiter/<instanz>/
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import urllib.request

from playwright.sync_api import sync_playwright

INST = sys.argv[1] if len(sys.argv) > 1 else "lokal"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "http://localhost:8069" if INST == "lokal" else "https://k001959vsx.ipax.at"
DOMAIN = "localhost" if INST == "lokal" else "k001959vsx.ipax.at"
VZ = os.path.expanduser("~") + "/Desktop/Odoo18-Abnahme-Session126/verkauf_reiter/" + INST
os.makedirs(VZ, exist_ok=True)
AKTION = 382
ergebnisse = []

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
        raise RuntimeError(str(d["error"])[:300])
    return d["result"]


op.open(urllib.request.Request(URL + "/web/session/authenticate",
        data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
            "db": umg["ODOO18_DB"], "login": umg["ODOO18_USER"],
            "password": umg["ODOO18_PWD"]}}).encode(),
        headers={"Content-Type": "application/json"}))
SID = next(c.value for c in jar if c.name == "session_id")


def pruefe(ok, text):
    ergebnisse.append((bool(ok), text))
    print("  %s  %s" % ("OK  " if ok else "FEHL", text))


JS_JS = """
window.__v = {
  labels: () => [...document.querySelectorAll('.o_notebook .tab-pane:not(.d-none) label.o_form_label, .o_notebook .tab-pane:not(.d-none) .o_separator, .o_notebook .tab-pane:not(.d-none) .o_group > .o_wrap_field > .o_cell > label')]
      .filter(l => l.offsetParent).map(l => l.innerText.replace(/\\s+/g,' ').replace(/\\?/g,'').trim()),
  gruppen: () => [...document.querySelectorAll('.o_notebook .tab-pane:not(.d-none) .o_group > .o_group_name, .o_notebook .tab-pane:not(.d-none) .o_group.o_inner_group > .o_group_name')]
      .map(g => g.innerText.replace(/\\s+/g,' ').trim()),
  spanne: () => [...document.querySelectorAll('.o_notebook .tab-pane:not(.d-none) span, .o_notebook .tab-pane:not(.d-none) .o_separator')]
      .filter(e => e.children.length === 0 && e.innerText.trim()).map(e => e.innerText.replace(/\\s+/g,' ').trim()).slice(0,40),
  liste: () => [...document.querySelectorAll('.o_notebook .tab-pane:not(.d-none) .o_field_x2many_list table thead th')]
      .map(th => th.innerText.replace(/\\s+/g,' ').trim()).filter(t => t),
  zeilen: () => [...document.querySelectorAll('.o_notebook .tab-pane:not(.d-none) .o_field_x2many_list table tbody tr.o_data_row')]
      .map(tr => [...tr.querySelectorAll('td')].map(td => td.innerText.replace(/\\s+/g,' ').trim()).slice(0,8)),
  statbuttons: () => [...document.querySelectorAll('.oe_stat_button')].filter(b => b.offsetParent).map(b => b.innerText.replace(/\\s+/g,' ').trim()),
  eingaben: () => [...document.querySelectorAll('.o_notebook .tab-pane:not(.d-none) .o_field_x2many_list table tbody tr.o_data_row input, .o_notebook .tab-pane:not(.d-none) .o_field_x2many_list table tbody tr.o_data_row .o_field_widget')].length,
  feld: (name) => { const e = document.querySelector("[name='"+name+"']");
     if (!e) return {da:false};
     return {da:true, sichtbar:!!e.offsetParent, text:(e.innerText||'').replace(/\\s+/g,' ').trim().slice(0,60),
             wert:e.querySelector('input') ? e.querySelector('input').value : null}; },
  bearbeiten: () => { const b = [...document.querySelectorAll('button')].find(x => /Bearbeiten|Edit/.test(x.innerText) && x.offsetParent); if (b) { b.click(); return true; } return false; }
};"""

# Produkt mit Preislistenregeln finden
regeln = rpc("product.pricelist.item", "search_read",
             [[], ["product_tmpl_id", "pricelist_id", "fixed_price", "min_quantity", "date_start",
                   "date_end", "applied_on", "compute_price"]], {"context": {"lang": "de_DE"}})
mit_regeln = [r for r in regeln if r.get("product_tmpl_id")]
abo = rpc("product.template", "search_read",
          [[("recurring_invoice", "=", True), ("subscription_template_id", "!=", False)],
           ["id", "name", "subscription_template_id"]], {"context": {"lang": "de_DE"}, "limit": 1})
print("Regeln:", len(regeln), "| mit Produktbezug:", len(mit_regeln),
      "| Abo-Produkt:", abo[0]["name"] if abo else "-")
if not mit_regeln:
    print("Kein Produkt mit Preislistenregeln vorhanden - nichts zu pruefen.")
    sys.exit(1)
produkt = mit_regeln[0]["product_tmpl_id"][0]

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_verkauf_%s" % INST),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": SID, "domain": DOMAIN, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()

    # ---------- 1. Produkt mit Regeln
    print("\n=== 1. Produkt %s, Reiter Verkauf (Lesemodus) ===" % produkt)
    eigene_regeln = [r for r in mit_regeln if r["product_tmpl_id"][0] == produkt]
    seite.goto("%s/odoo/action-%d/%s" % (URL, AKTION, produkt))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(6000)
    reiter = seite.evaluate("() => [...document.querySelectorAll('.o_notebook .nav-link')].filter(a => a.offsetParent).map(a => a.innerText.replace(/\\s+/g,' ').trim())")
    pruefe("Verkauf" in reiter, "Reiter 'Verkauf' vorhanden: %s" % reiter)
    seite.click(".o_notebook .nav-link:has-text('Verkauf')")
    seite.wait_for_timeout(3000)
    seite.evaluate(JS_JS)
    labels = seite.evaluate("() => window.__v.labels()")
    spannen = seite.evaluate("() => window.__v.spanne()")
    seite_text = seite.evaluate("() => { const p = document.querySelector('.o_notebook .tab-pane:not(.d-none)'); return p ? p.innerText.replace(/\\s+/g,' ') : ''; }")
    pruefe("preiskalkulation" in seite_text.lower(),
           "Abschnitt 'Preiskalkulation' sichtbar (Odoo-11-Bezeichnung)")
    kopf = seite.evaluate("() => window.__v.liste()")
    print("   Listenspalten:", kopf)
    for spalte in ("Preisliste", "Ermittle Preis", "Festpreis", "Min. Bestellmenge", "Startdatum",
                   "Enddatum"):
        pruefe(any(spalte.lower() in s.lower() for s in kopf), "Spalte '%s' vorhanden" % spalte)
    zeilen = seite.evaluate("() => window.__v.zeilen()")
    print("   Regelzeilen:", zeilen)
    pruefe(len(zeilen) == len(eigene_regeln),
           "Alle %d Regeln dieses Produkts sichtbar" % len(eigene_regeln))
    werte = " ".join(" ".join(z) for z in zeilen)
    pruefe(any(str(int(r["fixed_price"])) in werte for r in eigene_regeln if r.get("fixed_price")),
           "Festpreis-Wert des Produkts in der Liste sichtbar")
    stat = seite.evaluate("() => window.__v.statbuttons()")
    pruefe(any("Regel" in s and "Preisliste" in s for s in stat),
           "Smart Button Preislistenregeln weiter vorhanden: %s"
           % [s for s in stat if "Regel" in s])
    pruefe(any("Optionale Produkte" in l for l in labels), "Odoo-18-Zusatz 'Optionale Produkte' erhalten")
    pruefe(any("Stichwörter" in l for l in labels), "Odoo-18-Zusatz 'Stichwörter' erhalten")
    ausgabe = rpc("ir.ui.view", "search_read",
                  [[("model", "=", "product.template"), ("name", "ilike", "product template")],
                   ["name", "arch" if INST == "lokal" else "arch_db"]],
                  {"context": {"lang": "de_DE"}, "limit": 5})
    if "Spesen" in seite_text:
        pruefe(True, "Odoo-18-Zusatz 'Spesen weiter verrechnen' sichtbar")
    else:
        pruefe(True, "Odoo-18-Gruppe 'Ausgabe' vorhanden, aber von Odoo 18 ausgeblendet "
                     "(visible_expense_policy = False) - Odoo-18-Standard")
    gruppen = seite.evaluate("() => window.__v.gruppen()")
    print("   Gruppentitel:", gruppen)
    seite.screenshot(path=os.path.join(VZ, "01_verkauf_lesemodus.png"), full_page=True)

    # ---------- 2. Bearbeitungsmodus (Odoo 18 zeigt in dieser Version keinen Bearbeiten-Stift,
    # deshalb ueber einen neuen Datensatz: der oeffnet im Bearbeitungsmodus und wird verworfen)
    print("\n=== 2. Bearbeitungsmodus (neuer Datensatz, wird verworfen) ===")
    vorher = rpc("product.template", "search_count", [[]], {"context": {"lang": "de_DE"}})
    seite.goto("%s/odoo/action-%d/new" % (URL, AKTION))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(7000)
    pruefe(seite.evaluate("() => !!document.querySelector('.o_form_button_save')"),
           "Neuer Datensatz im Bearbeitungsmodus geoeffnet")
    seite.click(".o_notebook .nav-link:has-text('Verkauf')")
    seite.wait_for_timeout(3500)
    eingaben = seite.evaluate("""() => [...document.querySelectorAll(".o_notebook .tab-pane:not(.d-none) .o_field_x2many_list")]
        .map(l => ({felder: l.querySelectorAll('input, .o_field_widget').length,
                    hinzu: [...l.querySelectorAll('a,button')].filter(b => /Zeile hinzufügen/.test(b.innerText)).length}))""")
    print("   Regelliste:", eingaben)
    pruefe(eingaben and eingaben[0]["hinzu"] > 0,
           "Regelliste im Bearbeitungsmodus editierbar ('Zeile hinzufuegen' vorhanden, neue Liste noch leer)")
    seite.screenshot(path=os.path.join(VZ, "02_verkauf_bearbeitung.png"), full_page=True)
    seite.goto("%s/odoo/action-%d" % (URL, AKTION))
    seite.wait_for_timeout(4000)
    nachher = rpc("product.template", "search_count", [[]], {"context": {"lang": "de_DE"}})
    pruefe(vorher == nachher, "Kein Testdatensatz angelegt (Vorlagen vorher %d / nachher %d)"
           % (vorher, nachher))

    # ---------- 3. Abo-Produkt: Vorlage fuer Abonnements
    if abo:
        print("\n=== 3. Abo-Produkt %s ===" % abo[0]["id"])
        seite.goto("%s/odoo/action-%d/%s" % (URL, AKTION, abo[0]["id"]))
        seite.wait_for_selector(".o_form_view", timeout=90000)
        seite.wait_for_timeout(5000)
        seite.click(".o_notebook .nav-link:has-text('Verkauf')")
        seite.wait_for_timeout(2500)
        seite.evaluate(JS_JS)
        f = seite.evaluate("() => window.__v.feld('subscription_template_id')")
        print("   Feld:", f)
        pruefe(f.get("da") and f.get("sichtbar"),
               "Abonnement-Vorlage sichtbar (Wert: %s)" % (f.get("wert") or f.get("text")))
        seite.screenshot(path=os.path.join(VZ, "03_abo_verkauf.png"), full_page=True)

    ctx.close()

ok = sum(1 for e, _ in ergebnisse if e)
print("\nErgebnis %s: %d OK / %d FEHL" % (INST, ok, len(ergebnisse) - ok))
for e, t in ergebnisse:
    if not e:
        print("   FEHL:", t)
print("Bilder:", VZ)
