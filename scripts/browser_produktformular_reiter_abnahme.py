"""Browser-Abnahme Produktformular (Reiter und Felder gegen Odoo 11).

Oeffnet ein echtes Produkt (Ware) ueber den Menuepunkt Abrechnung > Verkauf >
Verkaufbare Produkte (Aktion 382), liest Reiter, Gruppentitel und sichtbare
Feldbeschriftungen aus dem DOM, prueft sie gegen den Odoo-11-Aufbau und legt je
Reiter einen Screenshot ab.

Aufruf: python scripts/browser_produktformular_reiter_abnahme.py lokal|vm [ordner]
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
ordner = sys.argv[2] if len(sys.argv) > 2 else ""
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
    p = {"model": model, "method": method, "args": args, "kwargs": kw}
    r = json.loads(op.open(urllib.request.Request(
        url + "/web/dataset/call_kw", data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                        "params": p}).encode(),
        headers={"Content-Type": "application/json"})).read())
    if "error" in r:
        raise RuntimeError(str(r["error"])[:300])
    return r["result"]


def norm(t):
    return (t or "").replace("\u00a0", " ").strip()


ids = rpc("product.template", "search", [[["type", "=", "consu"], ["sale_ok", "=", True]]])
produkt = rpc("product.template", "read", [ids[:1], ["id", "name", "type", "sale_ok", "purchase_ok"]])[0]
print("Instanz:", inst, "| Produkt:", produkt)

TABS = """() => [...document.querySelectorAll('.o_notebook .o_notebook_headers .nav-link, .o_notebook > ul.nav .nav-link')]
    .filter(a => a.offsetParent).map(a => a.innerText.replace(/\\s+/g,' ').trim())"""

LABELS = """() => [...document.querySelectorAll('.o_notebook .tab-pane')]
    .filter(p => !p.className.includes('d-none') && p.offsetParent)
    .flatMap(p => [...p.querySelectorAll('label.o_form_label')])
    .filter(l => l.offsetParent && l.innerText.trim())
    .map(l => { const z = l.closest('.o_wrap_field') || l.parentElement;
                const f = z ? z.querySelector('[name]') : null;
                return l.innerText.replace(/\\s+/g,' ').replace(/\\?/g,'').trim() + '|' +
                       (f ? f.getAttribute('name') : '?'); })"""

TITEL = """(gesucht) => gesucht.filter(t => [...document.querySelectorAll('.o_notebook *, .o_form_sheet *')]
    .some(e => !e.children.length && e.offsetParent &&
               (e.innerText || '').replace(/\\s+/g,' ').trim().toUpperCase() === t.toUpperCase()))"""

from playwright.sync_api import sync_playwright  # noqa: E402

ok, fehl = [], []


def pruefe(bedingung, text):
    (ok if bedingung else fehl).append(text)
    print(("  OK   " if bedingung else "  FEHL ") + text)


VZ = ordner or os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session126",
                            "produktformular", inst)
os.makedirs(VZ, exist_ok=True)

O11_REITER = ["Allgemeine Informationen", "Attribute & Varianten", "Verkauf", "Einkauf",
              "Lager", "Abrechnung", "Notizen"]

GRUPPEN = {
    "Abrechnung": ["Forderungen", "Verbindlichkeiten", "Abrechnung", "Eingangsrechnung"],
    "Notizen": ["Description for Internal", "Beschreibung für Kunden", "Beschreibung für Lieferanten",
                "Beschreibung für Auslieferungsaufträge", "Beschreibung für Wareneingang",
                "Beschreibung für interne Transfers", "Warnung beim Verkauf des Produktes",
                "Warnung beim Einkauf dieses Produktes"],
}

with sync_playwright() as pw:
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_prodform_%s" % inst),
        channel="chrome", headless=True, viewport={"width": 1900, "height": 1400})
    ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
    seite = ctx.pages[0] if ctx.pages else ctx.new_page()
    seite.goto("%s/odoo/action-%d/%s" % (url, AKTION, produkt["id"]))
    seite.wait_for_selector(".o_form_view", timeout=90000)
    seite.wait_for_timeout(6000)

    reiter = seite.evaluate(TABS)
    print("\nReiter im Formular:", reiter)
    pruefe(reiter == O11_REITER,
           "Reiterfolge wie Odoo 11 (mit Odoo-18-Zusatz 'Attribute & Varianten'): %s" % reiter)

    inhalt = {}
    titel_je_reiter = {}
    for r in reiter:
        knopf = seite.query_selector(".o_notebook .nav-link:has-text('%s')" % r.replace('"', ""))
        if knopf is None:
            continue
        knopf.click()
        seite.wait_for_timeout(1500)
        inhalt[r] = seite.evaluate(LABELS)
        titel_je_reiter[r] = seite.evaluate(TITEL, GRUPPEN.get(r, []))
        seite.screenshot(path=os.path.join(VZ, "reiter_%s.png" % r.replace(" ", "_").replace("&", "und")))
        print("\n--- Reiter %s ---" % r)
        print("   Felder:", [x.split("|")[0] for x in inhalt[r]])
        if titel_je_reiter[r]:
            print("   Gruppen:", titel_je_reiter[r])

    # ---------- 1. Reiter Allgemeine Informationen ----------
    l1 = [x.split("|")[0] for x in inhalt.get("Allgemeine Informationen", [])]
    for feld in ("Interne Kategorie", "Interne Referenz", "Strichcode"):
        pruefe(feld in l1, "Erster Reiter zeigt '%s'" % feld)
    pruefe(l1.index("Interne Kategorie") < l1.index("Verkaufspreis") if "Verkaufspreis" in l1 else True,
           "Kategorie/Referenz/Strichcode stehen vor dem Verkaufspreis (erste Gruppe, Odoo 11)")
    pruefe("Fakturierungsregel" not in l1, "Fakturierungsregel steht NICHT mehr im ersten Reiter (Odoo 11: Abrechnung)")

    # ---------- Reiter Abrechnung ----------
    la = [x.split("|")[0] for x in inhalt.get("Abrechnung", [])]
    for feld in ("Steuern (Verkauf)", "Steuern (Einkauf)", "Fakturierungsregel", "Kontrollrichtlinie"):
        pruefe(feld in la, "Reiter Abrechnung zeigt '%s'" % feld)
    gt = titel_je_reiter.get("Abrechnung", [])
    pruefe(sorted(gt) == sorted(GRUPPEN["Abrechnung"]),
           "Reiter Abrechnung: Odoo-11-Gruppen Forderungen/Verbindlichkeiten/Abrechnung/Eingangsrechnung %s" % gt)

    # ---------- Reiter Notizen ----------
    ln = [x.split("|")[0] for x in inhalt.get("Notizen", [])]
    for feld in ("Beschreibung", "Verkaufsbeschreibung", "Einkaufsbeschreibung",
                 "Beschreibung auf Lieferaufträgen", "Beschreibung auf Wareneingängen",
                 "Beschreibung der Kommisionierung", "Auftragsposition", "Bestellposition"):
        pruefe(feld in ln, "Reiter Notizen zeigt '%s'" % feld)
    warnung = rpc("product.template", "read", [[produkt["id"]], ["sale_line_warn"]])[0]
    if warnung["sale_line_warn"] != "no-message":
        pruefe("Mitteilung für Auftragszeile" in ln, "Reiter Notizen zeigt 'Mitteilung für Auftragszeile'")
    else:
        pruefe("Mitteilung für Auftragszeile" not in ln,
               "Reiter Notizen: 'Mitteilung für Auftragszeile' ist bei Warnung 'Keine Nachricht' "
               "unsichtbar (Odoo-11-Bedingung; Feld im Arch mit Odoo-11-Beschriftung vorhanden)")
    gt = titel_je_reiter.get("Notizen", [])
    pruefe(sorted(gt) == sorted(GRUPPEN["Notizen"]),
           "Reiter Notizen: alle acht Odoo-11-Gruppen vorhanden (%d/8) %s" % (len(gt), gt))
    pruefe(not any(x in gt for x in ("Angebotsbeschreibung", "Einkaufsbeschreibung")),
           "Reiter Notizen: keine Odoo-18-Gruppentitel mehr")

    # ---------- Arch: kein Feld doppelt, alle Odoo-11-Felder vorhanden ----------
    arch = rpc("product.template", "get_views", [[[False, "form"]]])["views"]["form"]["arch"]
    for feld in ("taxes_id", "supplier_taxes_id", "invoice_policy", "purchase_method",
                 "description", "description_sale", "description_purchase", "description_pickingout",
                 "description_pickingin", "description_picking", "sale_line_warn", "sale_line_warn_msg",
                 "purchase_line_warn", "purchase_line_warn_msg", "categ_id", "default_code"):
        anz = arch.count('<field name="%s"' % feld)
        pruefe(anz == 1, "Arch: Feld %s genau einmal im Formular (%d)" % (feld, anz))
    # barcode: 1x im Formular, 1x als optionale Spalte in einer eingebetteten Liste
    pruefe(arch.count('<field name="barcode"') == 2 and '<field name="barcode" optional="hide"/>' in arch,
           "Arch: Feld barcode 1x im Formular + 1x als Listenspalte")
    pruefe(all(x in arch for x in ('string="Notizen"', 'string="Abrechnung"')),
           "Arch: Reiter Notizen und Abrechnung vorhanden")

    # ---------- nicht mehr benutzte Odoo-18-Huellen ----------
    lv = [x.split("|")[0] for x in inhalt.get("Verkauf", [])]
    le = [x.split("|")[0] for x in inhalt.get("Einkauf", [])]
    pruefe("Kontrollrichtlinie" not in le, "Reiter Einkauf: Kontrollrichtlinie entfernt (Odoo 11: Abrechnung)")
    pruefe("Einkaufsbeschreibung" not in le, "Reiter Einkauf: Einkaufsbeschreibung entfernt (Odoo 11: Notizen)")
    pruefe("Auftragsposition" not in lv, "Reiter Verkauf: Auftragsposition entfernt (Odoo 11: Notizen)")
    pruefe("Verkaufsbeschreibung" not in lv, "Reiter Verkauf: Verkaufsbeschreibung entfernt (Odoo 11: Notizen)")
    ll = [x.split("|")[0] for x in inhalt.get("Lager", [])]
    pruefe(not any("Beschreibung" in x for x in ll),
           "Reiter Lager: Beschreibungsfelder entfernt (Odoo 11: Notizen)")
    pruefe(ll, "Reiter Lager: Inhalte %s" % ll)

    print("\nErgebnis:", len(ok), "OK /", len(fehl), "FEHL")
    for f in fehl:
        print("   FEHL:", f)
    print("Screenshots:", VZ)
    ctx.close()
