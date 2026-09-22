"""Browser-Abnahme "Abonnement Produkte" auf der Odoo-18-VM (Session 119, Teil 14).

Oeffnet Abonnements -> Abonnement Produkte im echten Browser (Playwright + Chrome, headless)
und prueft mit echten Klicks: Listenansicht, Spalten, Spaltenauswahl, Suche, Filter,
Gruppierungen, Produktformular und EUR-Darstellung. JS- und RPC-Fehler werden mitgezaehlt.

Aufruf:
    uv run --with playwright python scripts/browser_abo_produkte.py --instanz vm
    uv run --with playwright python scripts/browser_abo_produkte.py --instanz lokal --ohne-screenshot
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session119")

ERWARTETE_SPALTEN = ["Interne Referenz", "Produktname", "Mit Faktor multiplizieren (pro 1.000)",
                     "Verkaufspreis", "Kosten", "Status", "Interne Kategorie", "Einheit"]
NICHT_ERWARTET = ["Bestandsmenge", "Geplante Bestandsmenge"]
ERWARTETE_FILTER = ["Mit Faktor multipliziert", "Aktive Abonnement Produkte", "Produkte",
                    "Abonnement Produkte", "Archiviert", "Dienstleistungen", "Güter", "Verkauf", "Einkauf"]
ERWARTETE_GRUPPEN = ["Produktart", "Produktkategorie", "Status", "Mit Faktor multipliziert"]


def lade_env(pfad):
    werte = {}
    for zeile in open(pfad, encoding="utf-8"):
        if "=" in zeile and not zeile.strip().startswith("#"):
            k, v = zeile.split("=", 1)
            werte[k.strip()] = v.strip()
    return werte


def rpc_client(url, db, user, pwd):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rufe(pfad, prm):
        req = urllib.request.Request(url + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": prm}).encode(),
                                     headers={"Content-Type": "application/json"})
        with op.open(req, timeout=180) as f:
            return json.loads(f.read().decode())

    rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})
    sid = next((c.value for c in jar if c.name == "session_id"), None)

    def kw(model, methode, args, **kwargs):
        o = rufe("/web/dataset/call_kw", {"model": model, "method": methode, "args": args, "kwargs": kwargs})
        if "error" in o:
            raise RuntimeError(str(o["error"].get("data", {}).get("message"))[:200])
        return o.get("result")

    return sid, kw


# Klickt einen Eintrag des Suchleisten-Menues an: bereich='filter' oder 'gruppe'
# (die Eintraege 'Mit Faktor multipliziert' existieren in beiden Abschnitten).
JS_KLICK = """(args) => {
    const [text, bereich] = args;
    const menu = document.querySelector('.o_search_bar_menu');
    if (!menu) return 'kein-menue';
    const kopf = [...menu.querySelectorAll('*')].find(e => e.children.length === 0 &&
        (e.innerText || '').trim() === 'Gruppieren nach');
    const eintraege = [...menu.querySelectorAll('li[role=option], .dropdown-item')];
    const treffer = eintraege.filter(i => {
        const t = (i.innerText || '').replace(/\\s+/g, ' ').trim();
        if (t !== text) return false;
        if (!kopf) return bereich === 'filter';
        const danach = !!(kopf.compareDocumentPosition(i) & Node.DOCUMENT_POSITION_FOLLOWING);
        return bereich === 'gruppe' ? danach : !danach;
    });
    if (!treffer.length) return 'nicht-gefunden';
    treffer[0].scrollIntoView();
    treffer[0].click();
    return 'geklickt';
}"""


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    p.add_argument("--ohne-screenshot", action="store_true")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

    treffer = kw("ir.model.data", "search_read",
                 [[("module", "=", "itk_subscription"), ("name", "=", "product_action_subscription")],
                  ["res_id"]], limit=1)
    if not treffer:
        menue = kw("ir.ui.menu", "search_read", [[("name", "ilike", "Abonnement Produkte")], ["id", "action"]], limit=1)
        treffer = [{"res_id": int(str(menue[0]["action"]).split(",")[1])}] if menue and menue[0]["action"] else []
    if not treffer:
        raise SystemExit("Aktion 'Abonnement Produkte' nicht gefunden - Abbruch.")
    aktion_id = treffer[0]["res_id"]
    such_view = kw("ir.actions.act_window", "read", [[aktion_id], ["search_view_id"]])[0]["search_view_id"]

    produkte = kw("product.template", "search_read",
                  [[("recurring_invoice", "=", True)], ["id", "name", "list_price"]], limit=5)
    if not produkte:
        produkte = kw("product.template", "search_read", [[], ["id", "name", "list_price"]], limit=5)
    if not produkte:
        raise SystemExit("Keine Produkte vorhanden - Abbruch.")
    produkt = produkte[0]
    suchbegriff = re.split(r"[\s/-]+", produkt["name"].strip())[0]

    print("Instanz      : %s (%s)" % (a.instanz, url))
    print("Aktion       : %s | Suchansicht: %s" % (aktion_id, such_view))
    print("Suchbegriff  : %s" % suchbegriff)
    print("Produkt (Form): id=%s %s" % (produkt["id"], produkt["name"]))

    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    ok = fehler = 0
    js_fehler, rpc_fehler = [], []

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    def saeubere(text):
        return re.sub(r"\s+", " ", text or "").strip()

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_abo_prod_%s_%s" % (a.instanz, os.getpid())),
            channel="chrome", headless=True, viewport={"width": 1800, "height": 1300})
        ctx.add_init_script(
            "window.__errs=[];"
            "window.addEventListener('error', e => window.__errs.push(''+e.message));"
            "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));"
            "const ce=console.error; console.error=(...x)=>{window.__errs.push(x.map(String).join(' ')); ce(...x);};")
        ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
        seite = ctx.pages[0] if ctx.pages else ctx.new_page()
        seite.on("response", lambda r: rpc_fehler.append("%s %s" % (r.status, r.url))
                 if ("/web/dataset/call_kw" in r.url and r.status >= 400) else None)

        def oeffne(pfad, selektor=".o_list_view"):
            seite.goto(url + pfad)
            seite.wait_for_selector(selektor, timeout=90000)
            seite.wait_for_timeout(3000)

        def schuss(name):
            if not a.ohne_screenshot:
                datei = os.path.join(VZ, name)
                seite.screenshot(path=datei, full_page=True)
                print("       Screenshot: %s" % datei)

        def menue_oeffnen():
            seite.click(".o_searchview_input")
            seite.wait_for_timeout(1500)
            return saeubere(seite.inner_text(".o_search_bar_menu")) if seite.query_selector(".o_search_bar_menu") else ""

        def facetten_entfernen():
            for _ in range(6):
                pfeil = seite.query_selector(".o_searchview_facet .o_facet_remove")
                if not pfeil:
                    break
                if not pfeil.is_visible():
                    break
                if not pfeil.is_enabled():
                    break
                pfeil.click()
                seite.wait_for_timeout(1500)

        print("\n1) Menuepunkt Abonnement Produkte -> Listenansicht")
        oeffne("/web#action=%s&model=product.template&view_type=list" % aktion_id)
        kopf = saeubere(seite.inner_text("thead"))
        print("       Spaltenkopf: %s" % kopf[:260])
        for spalte in ERWARTETE_SPALTEN:
            pruefe(spalte in kopf, "Spalte sichtbar: %s" % spalte)
        for spalte in NICHT_ERWARTET:
            pruefe(spalte not in kopf, "Spalte bewusst nicht vorhanden: %s" % spalte)
        inhalt = saeubere(seite.inner_text(".o_list_view"))
        pruefe("€" in inhalt, "Preise in EUR dargestellt (Euro-Zeichen in der Liste)")
        schuss("60_%s_Abo_Produkte_Liste.png" % a.instanz.upper())

        print("\n2) Spaltenauswahl")
        schalter = seite.query_selector(".o_optional_columns_dropdown_toggle")
        pruefe(schalter is not None, "Schalter der Spaltenauswahl vorhanden")
        if schalter:
            schalter.click()
            seite.wait_for_timeout(1500)
            menue = saeubere(seite.inner_text(".o-dropdown--menu") if seite.query_selector(".o-dropdown--menu")
                             else seite.inner_text("body"))
            for eintrag in ("Interne Kategorie", "Mit Faktor multiplizieren (pro 1.000)"):
                pruefe(eintrag in menue, "Spaltenauswahl bietet an: %s" % eintrag)
            schuss("61_%s_Abo_Produkte_Spaltenauswahl.png" % a.instanz.upper())
            eintrag = seite.query_selector(".o-dropdown--menu label:has-text('Interne Kategorie')") or \
                seite.query_selector(".o-dropdown--menu .dropdown-item:has-text('Interne Kategorie')")
            if eintrag:
                eintrag.click()
                seite.wait_for_timeout(2000)
                pruefe("Interne Kategorie" not in saeubere(seite.inner_text("thead")),
                       "Abwahl der Spalte wirkt (Kopfzeile ohne 'Interne Kategorie')")
            # Das Menue bleibt nach dem Abwaehlen offen - dann direkt wieder anwaehlen.
            if not seite.query_selector(".o-dropdown--menu"):
                schalter = seite.query_selector(".o_optional_columns_dropdown_toggle")
                if schalter:
                    schalter.click()
                    seite.wait_for_timeout(1500)
            eintrag = seite.query_selector(".o-dropdown--menu label:has-text('Interne Kategorie')") or \
                seite.query_selector(".o-dropdown--menu .dropdown-item:has-text('Interne Kategorie')")
            if eintrag:
                eintrag.click()
                seite.wait_for_timeout(2000)
            pruefe("Interne Kategorie" in saeubere(seite.inner_text("thead")),
                   "Wiederanwahl der Spalte wirkt (Kopfzeile wieder mit 'Interne Kategorie')")
            seite.keyboard.press("Escape")
            seite.wait_for_timeout(800)

        print("\n3) Suche")
        seite.click(".o_searchview_input")
        seite.fill(".o_searchview_input", suchbegriff)
        seite.keyboard.press("Enter")
        seite.wait_for_timeout(3000)
        facetten = saeubere(seite.inner_text(".o_searchview"))
        inhalt = saeubere(seite.inner_text(".o_list_view"))
        pruefe(suchbegriff.lower() in facetten.lower() or "Produkt" in facetten,
               "Suchbedingung gesetzt: %s" % facetten[:120])
        pruefe(produkt["name"].split()[0].lower() in inhalt.lower() or suchbegriff.lower() in inhalt.lower(),
               "Suche '%s' findet das Produkt in der Liste" % suchbegriff)
        schuss("62_%s_Abo_Produkte_Suche.png" % a.instanz.upper())
        facetten_entfernen()

        print("\n4) Filter")
        menue = menue_oeffnen()
        for f in ERWARTETE_FILTER:
            pruefe(f in menue, "Filter angeboten: %s" % f)
        schuss("63_%s_Abo_Produkte_Filter_Menue.png" % a.instanz.upper())
        ergebnis = seite.evaluate(JS_KLICK, ["Mit Faktor multipliziert", "filter"])
        pruefe(ergebnis == "geklickt", "Filter 'Mit Faktor multipliziert' angeklickt (%s)" % ergebnis)
        seite.wait_for_timeout(2500)
        facetten = saeubere(seite.inner_text(".o_searchview"))
        pruefe("Faktor" in facetten, "Filter wirkt als Bedingung in der Suchleiste: %s" % facetten[:120])
        pruefe("o_list_view" in seite.content() or seite.query_selector(".o_list_view") is not None,
               "Listenansicht bleibt fehlerfrei sichtbar (Filter ausgefuehrt)")
        schuss("64_%s_Abo_Produkte_Filter_Faktor.png" % a.instanz.upper())
        facetten_entfernen()

        print("\n5) Gruppierungen")
        menue = menue_oeffnen()
        for g in ERWARTETE_GRUPPEN:
            pruefe(g in menue, "Gruppierung angeboten: %s" % g)
        ergebnis = seite.evaluate(JS_KLICK, ["Status", "gruppe"])
        pruefe(ergebnis == "geklickt", "Gruppierung 'Status' angeklickt (%s)" % ergebnis)
        seite.wait_for_timeout(3000)
        liste = saeubere(seite.inner_text(".o_list_view"))
        pruefe(any(s in liste for s in ["Onlineservice", "Plattform", "Software", "Consulting", "Hardware", "Kein"]),
               "Gruppierung nach Status zeigt Gruppen (Auszug: %s)" % liste[:180])
        schuss("65_%s_Abo_Produkte_Gruppierung_Status.png" % a.instanz.upper())
        facetten_entfernen()

        print("\n6) Produktformular")
        oeffne("/web#id=%s&model=product.template&view_type=form" % produkt["id"], ".o_form_view")
        form = saeubere(seite.inner_text(".o_form_view"))
        # Hinweis: default_code heisst im Odoo-18-Formular 'Referenz' (Basismodul product,
        # string am View), in der Liste wie in Odoo 11 'Interne Referenz'. product_type_id
        # heisst im Formular 'Produkttyp' (Odoo 11: 'Product-Type'), in der Liste 'Status'.
        for label in ["Referenz", "Verkaufspreis", "Kosten", "Produkttyp", "Kategorie", "Einheit"]:
            pruefe(label in form, "Formular zeigt '%s'" % label)
        anzahl = form.count("Mit Faktor multiplizieren (pro 1.000)")
        pruefe(anzahl == 1, "Feld 'Mit Faktor multiplizieren (pro 1.000)' genau einmal (gefunden: %d)" % anzahl)
        pruefe("To multiply" not in form, "englische Restbeschriftung 'To multiply' nicht sichtbar")
        pruefe("€" in form, "Preise im Formular in EUR")
        schuss("66_%s_Abo_Produkte_Formular.png" % a.instanz.upper())

        print("\n7) Fehlerfreiheit")
        js_fehler.extend(seite.evaluate("window.__errs") or [])
        pruefe(not js_fehler, "keine JavaScript-Fehler (%d)" % len(js_fehler))
        for e in js_fehler[:5]:
            print("       JS : %s" % str(e)[:160])
        pruefe(not rpc_fehler, "keine RPC-Fehler (%d)" % len(rpc_fehler))
        for e in rpc_fehler[:5]:
            print("       RPC: %s" % str(e)[:160])
        ctx.close()

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
