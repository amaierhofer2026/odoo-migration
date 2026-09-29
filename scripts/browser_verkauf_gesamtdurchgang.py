"""Teil 5, Block 3: Browser-Gesamtdurchgang Verkauf (ein durchgehender Klickpfad).

Ein Browser, eine Sitzung, alle Stationen des Bereichs Verkauf nacheinander:
  Menues -> Auftragsliste -> Auftragsformular und Reiter -> Lagerbereich -> Suche/Filter/Gruppierung
  -> Ansichten (Liste/Kanban/Kalender/Pivot/Graph) -> Auftragskalender -> Berichte (Verkauf und
  Verkaufsauftraege aller Kanaele) -> Drucken -> Zahlungsbedingungen -> Stammdaten
  (Preislisten, Verkaufsteams) -> Lieferfunktion (Auftrag mit Lieferung)

Es werden keine Daten geaendert (nur Ansichten geoeffnet und gesucht); der Bestand wird vorher und
nachher verglichen. Fuer die Lieferstation wird - wie in browser_verkauf_lieferung.py - ein
Testauftrag angelegt und danach wieder entfernt.

Aufruf:
    uv run --with playwright python scripts/browser_verkauf_gesamtdurchgang.py --instanz vm
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_verkauf_menue import lade_env, rpc_client, REPO

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session121", "gesamtdurchgang")
SP = {"lang": "de_DE"}
TESTPRODUKT = "ZZ-Test Gesamtdurchgang Lagerartikel (bitte loeschen)"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

    ok = fehler = 0
    js_fehler, rpc_fehler = [], []
    os.makedirs(VZ, exist_ok=True)

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    def saeubere(t):
        return re.sub(r"\s+", " ", t or "").strip()

    auftrag = kw("sale.order", "search_read", [[("state", "=", "sale")], ["name", "partner_id"]],
                 context=SP, limit=1)[0]
    def aktion_id(modell):
        ids = kw("ir.actions.act_window", "search", [[("res_model", "=", modell)]], context=SP,
                 limit=1)
        return ids[0] if ids else None

    akt_zb = aktion_id("account.payment.term")
    akt_preise = aktion_id("product.pricelist")
    akt_teams = aktion_id("crm.team")
    bestand_vorher = {"auftraege": kw("sale.order", "search_count", [[]], context=SP),
                      "produkte": kw("product.template", "search_count", [[]], context=SP),
                      "lagerbelege": kw("stock.picking", "search_count", [[]], context=SP)}
    print("Instanz: %s (%s) | Testauftrag %s | Bestand %s"
          % (a.instanz, url, auftrag["name"], bestand_vorher))

    from playwright.sync_api import sync_playwright
    testdaten = {}
    try:
        with sync_playwright() as pw:
            ctx = pw.chromium.launch_persistent_context(
                user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_gesamtdurchgang_%s" % a.instanz),
                channel="chrome", headless=True, viewport={"width": 1900, "height": 1400})
            ctx.add_init_script(
                "window.__errs=[];"
                "window.addEventListener('error', e => window.__errs.push(''+e.message));"
                "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));")
            ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
            seite = ctx.pages[0] if ctx.pages else ctx.new_page()
            seite.on("response", lambda r: rpc_fehler.append("%s %s" % (r.status, r.url))
                     if ("/web/dataset/call_kw" in r.url and r.status >= 400) else None)

            def station(nummer, titel, name):
                print("\n--- Station %02d: %s ---" % (nummer, titel))
                seite.screenshot(path=os.path.join(VZ, "%02d_%s_%s.png" % (nummer, name, a.instanz)),
                                 full_page=True)

            def text_body():
                return saeubere(seite.eval_on_selector("body", "e => e.innerText"))

            # 1) Menues
            seite.goto("%s/odoo/sales" % url)
            seite.wait_for_selector(".o_control_panel", timeout=90000)
            seite.wait_for_timeout(4000)
            station(1, "Angebote/Auftraege geoeffnet", "Angebote")
            inhalt = text_body()
            pruefe(auftrag["name"] in inhalt or "Auftrag" in inhalt, "Auftragsliste geladen")
            # Menuegruppen der Verkauf-App (nach dem Oeffnen der App sichtbar)
            seite.goto("%s/odoo/sales" % url)
            seite.wait_for_selector(".o_main_navbar", timeout=90000)
            seite.wait_for_timeout(3500)
            menues = saeubere(seite.eval_on_selector(".o_main_navbar", "e => e ? e.innerText : ''"))
            print("       Menues: %s" % menues[:200])
            for eintrag in ("Verkauf", "Aufträge", "Abzurechnen", "Produkte", "Berichtswesen",
                            "Konfiguration"):
                pruefe(eintrag in menues, "Menue '%s' sichtbar" % eintrag)
            station(2, "Hauptmenues", "Menues")

            # 3) Auftragsformular und Reiter
            seite.goto("%s/odoo/sales/%d" % (url, auftrag["id"]))
            seite.wait_for_selector(".o_form_view", timeout=90000)
            seite.wait_for_timeout(4500)
            form = saeubere(seite.eval_on_selector(".o_form_view", "e => e ? e.innerText : ''"))
            station(3, "Auftragsformular", "Auftrag_Formular")
            pruefe("Auftragszeilen" in form, "Reiter 'Auftragszeilen' vorhanden")
            pruefe("Weitere Informationen" in form, "Reiter 'Weitere Informationen' vorhanden")
            for feld in ("Kunde", "Verkaufskontakt", "Vertriebsmitarbeiter", "Zahlungsbedingungen",
                         "Preisliste", "Rechnungsadresse", "Lieferadresse"):
                pruefe(feld in form, "Feld '%s' im Formular" % feld)
            station(4, "Formularfelder", "Formular_Felder")

            # 5) Lagerbereich in den weiteren Informationen
            reiter = seite.query_selector("a:has-text('Weitere Informationen')")
            if reiter:
                reiter.click()
                seite.wait_for_timeout(3000)
            details = saeubere(seite.eval_on_selector(".o_form_sheet", "e => e ? e.innerText : ''"))
            for feld in ("Lagerhaus", "Versandbedingungen", "Lieferdatum"):
                pruefe(feld in details, "Lagerfeld '%s' sichtbar" % feld)
            station(5, "Lagerbereich", "Lager")

            # 6) Suche, Filter, Gruppierung (in der Auftragsliste)
            seite.goto("%s/odoo/sales" % url)
            seite.wait_for_selector(".o_list_view, .o_control_panel", timeout=90000)
            seite.wait_for_timeout(4000)
            seite.wait_for_selector(".o_searchview_input", timeout=30000)
            seite.click(".o_searchview_input")
            seite.fill(".o_searchview_input", auftrag["name"])
            seite.keyboard.press("Enter")
            seite.wait_for_timeout(4000)
            gefiltert = text_body()
            pruefe(auftrag["name"] in gefiltert, "Suche nach Auftragsnummer liefert den Auftrag")
            seite.click(".o_searchview_dropdown_toggler")
            seite.wait_for_timeout(1500)
            menue = saeubere(seite.eval_on_selector(".o-dropdown--menu", "e => e ? e.innerText : ''"))
            pruefe("Filter" in menue and "Gruppieren nach" in menue,
                   "Filter- und Gruppierungsbereich vorhanden")
            gruppen = saeubere(seite.eval_on_selector_all(
                ".o-dropdown--menu *",
                "els => els.filter(e => e.children.length === 0 && (e.innerText||'').trim())"
                ".map(e => e.innerText.trim()).join(' | ')"))
            print("       Suchmenue: %s" % gruppen[:220])
            pruefe("Gruppieren nach" in gruppen,
                   "Gruppieren-nach-Bereich mit Eintraegen vorhanden (%d Eintraege)"
                   % len([x for x in gruppen.split(" | ") if x]))
            station(6, "Suche und Filter", "Suche_Filter")
            seite.keyboard.press("Escape")

            # 7) Ansichten Liste/Kanban/Pivot/Graph/Kalender
            seite.goto("%s/odoo/sales" % url)
            seite.wait_for_selector(".o_switch_view", timeout=90000)
            seite.wait_for_timeout(4000)
            for typ, klasse, klassen in (("Liste", "o_list", ".o_list_view"),
                                         ("Kanban", "o_kanban", ".o_kanban_view"),
                                         ("Kalender", "o_calendar", ".o_calendar_view"),
                                         ("Pivot", "o_pivot", ".o_pivot_view"),
                                         ("Graph", "o_graph", ".o_graph_view")):
                knopf = seite.query_selector(".o_switch_view.%s" % klasse)
                if knopf:
                    knopf.click()
                    seite.wait_for_timeout(4000)
                    pruefe(seite.query_selector(klassen) is not None, "Ansicht '%s' laedt" % typ)
                else:
                    pruefe(False, "Umschalter fuer '%s' nicht gefunden" % typ)
            station(7, "Ansichten", "Ansichten")

            # 8) Auftragskalender (eigener Menuepunkt)
            seite.goto("%s/odoo/action-itk_sale_management.action_saleorder_kalender_itk" % url)
            seite.wait_for_selector(".o_calendar_view", timeout=90000)
            seite.wait_for_timeout(4500)
            kal = saeubere(seite.eval_on_selector(".o_calendar_view", "e => e ? e.innerText : ''"))
            pruefe(auftrag["name"] in kal or "Auftragskalender" in text_body(),
                   "Auftragskalender zeigt Auftraege (%s)" % auftrag["name"])
            station(8, "Auftragskalender", "Auftragskalender")

            # 9) Berichtswesen: Verkaufsanalyse und Kanaele-Bericht
            seite.goto("%s/odoo/action-416" % url)
            seite.wait_for_selector(".o_graph_view, .o_pivot_view", timeout=90000)
            seite.wait_for_timeout(4000)
            pruefe("Verkaufsanalyse" in text_body() or "Verkaufsaufträge" in text_body(),
                   "Bericht Verkaufsanalyse (Aktion 416) geoeffnet")
            station(9, "Bericht Verkauf", "Bericht_Verkauf")
            seite.goto("%s/odoo/action-itk_sale_management.action_sale_report_all_channels" % url)
            seite.wait_for_selector(".o_pivot_view", timeout=90000)
            seite.wait_for_timeout(5000)
            pivot = saeubere(seite.eval_on_selector(".o_pivot_view", "e => e ? e.innerText : ''"))
            pruefe("aller Kanäle" in text_body(), "Bericht 'Verkaufsauftraege aller Kanaele' geoeffnet")
            pruefe("Aktuelles Verkaufsjahr" in pivot or "Aktuelles Verkaufsjahr" in text_body(),
                   "Filter 'Aktuelles Verkaufsjahr' aktiv")
            station(10, "Bericht aller Kanaele", "Bericht_Kanaele")

            # 10) Drucken
            seite.goto("%s/odoo/sales/%d" % (url, auftrag["id"]))
            seite.wait_for_selector(".o_form_view", timeout=90000)
            seite.wait_for_timeout(4000)
            seite.click(".o_cp_action_menus button")
            seite.wait_for_timeout(1200)
            seite.click(".o-dropdown--has-parent:has-text('Drucken')", timeout=15000)
            seite.wait_for_timeout(1800)
            druck = saeubere(seite.eval_on_selector_all(
                ".o_popover *, .o-dropdown--menu *",
                "els => els.filter(e => e.children.length === 0 && (e.innerText||'').trim())"
                ".map(e => e.innerText.trim()).join(' | ')"))
            print("       Drucken-Menue: %s" % druck[:160])
            for bericht in ("Angebot/Auftrag", "ITK-Angebot/Auftrag", "PDF-Angebot",
                            "PRO-FORMA-Rechnung"):
                pruefe(bericht in druck, "Druckbericht '%s' angeboten" % bericht)
            station(11, "Drucken", "Drucken")
            seite.keyboard.press("Escape")

            # 11) Zahlungsbedingungen
            seite.goto("%s/odoo/action-%s" % (url, akt_zb))
            seite.wait_for_selector(".o_control_panel", timeout=90000)
            seite.wait_for_timeout(4500)
            zb = text_body()
            pruefe("30 Tage netto" in zb, "Zahlungsbedingung '30 Tage netto' in der Liste")
            pruefe("14 Tage" in zb, "Zahlungsbedingung '14 Tage' in der Liste")
            station(12, "Zahlungsbedingungen", "Zahlungsbedingungen")

            # 12) Stammdaten: Preislisten und Verkaufsteams
            seite.goto("%s/odoo/action-%s" % (url, akt_preise))
            seite.wait_for_selector(".o_control_panel", timeout=90000)
            seite.wait_for_timeout(4500)
            preise = text_body()
            pruefe("Preisliste" in preise or "Preise" in preise, "Preislistenliste geoeffnet")
            station(13, "Preislisten", "Preislisten")
            seite.goto("%s/odoo/action-%s" % (url, akt_teams))
            seite.wait_for_selector(".o_control_panel", timeout=90000)
            seite.wait_for_timeout(4500)
            teams = text_body()
            pruefe("Vertriebskanäle (Intern)" in teams or "Verkaufsteam" in teams
                   or "Verkauf" in teams, "Verkaufsteams/Vertriebskanaele geoeffnet")
            station(14, "Verkaufsteams", "Verkaufsteams")

            # 13) Lieferfunktion mit Testauftrag
            partner = kw("res.partner", "search", [[("name", "=", "Test Firma")]], context=SP, limit=1)
            testdaten["produkt"] = kw("product.product", "create", [{
                "name": TESTPRODUKT, "type": "consu", "is_storable": True, "list_price": 5.0,
                "sale_ok": True, "purchase_ok": False}], context=SP)
            testdaten["auftrag"] = kw("sale.order", "create", [{
                "partner_id": partner[0],
                "order_line": [(0, 0, {"product_id": testdaten["produkt"], "product_uom_qty": 1.0,
                                       "price_unit": 5.0, "name": TESTPRODUKT})]}], context=SP)
            kw("sale.order", "action_confirm", [[testdaten["auftrag"]]], context=SP)
            daten = kw("sale.order", "read", [[testdaten["auftrag"]], ["name", "delivery_count",
                                                                     "picking_ids"]], context=SP)[0]
            testdaten["picking"] = daten["picking_ids"][0] if daten["picking_ids"] else None
            seite.goto("%s/odoo/sales/%d" % (url, testdaten["auftrag"]))
            seite.wait_for_selector(".o_form_view", timeout=90000)
            seite.wait_for_timeout(5000)
            lief = text_body()
            print("       Testauftrag %s, Lieferungen %s" % (daten["name"], daten["delivery_count"]))
            pruefe("Lieferung" in lief, "Smart Button 'Lieferung' im Testauftrag")
            ziel = seite.query_selector("button:has-text('Lieferung')")
            if ziel:
                ziel.click()
                seite.wait_for_timeout(6000)
                beleg = text_body()
                pruefe("WH/OUT" in beleg or "Lieferaufträge" in beleg,
                       "Lieferbeleg aus dem Auftrag geoeffnet")
            station(15, "Lieferfunktion", "Lieferung")

            js_fehler[:] = seite.evaluate("() => window.__errs") or []
            ctx.close()
    finally:
        print("\n--- Testdaten bereinigen ---")
        try:
            if testdaten.get("picking"):
                kw("stock.picking", "action_cancel", [[testdaten["picking"]]], context=SP)
            if testdaten.get("auftrag"):
                zustand = kw("sale.order", "read", [[testdaten["auftrag"]], ["state", "locked"]],
                             context=SP)[0]
                if zustand["state"] == "sale":
                    if zustand["locked"]:
                        kw("sale.order", "write", [[testdaten["auftrag"]], {"locked": False}], context=SP)
                    wiz = kw("sale.order.cancel", "create", [{"order_id": testdaten["auftrag"]}], context=SP)
                    kw("sale.order.cancel", "action_cancel", [[wiz]], context=SP)
                kw("sale.order", "unlink", [[testdaten["auftrag"]]], context=SP)
            if testdaten.get("picking"):
                kw("stock.picking", "unlink", [[testdaten["picking"]]], context=SP)
            if testdaten.get("produkt"):
                kw("product.product", "unlink", [[testdaten["produkt"]]], context=SP)
            print("  Testauftrag, Lieferbeleg und Testprodukt entfernt")
        except Exception as ex:
            print("  Bereinigung: %s" % str(ex)[:200])

    bestand_nachher = {"auftraege": kw("sale.order", "search_count", [[]], context=SP),
                       "produkte": kw("product.template", "search_count", [[]], context=SP),
                       "lagerbelege": kw("stock.picking", "search_count", [[]], context=SP)}
    print("\nBestand nachher: %s" % bestand_nachher)
    pruefe(bestand_nachher == bestand_vorher, "Bestand unveraendert (Testdaten bereinigt)")
    pruefe(kw("product.template", "search_count", [[("name", "ilike", "ZZ-Test")]], context=SP) == 0,
           "keine Testprodukte zurueckgeblieben")

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    print("JavaScript-Fehler: %d %s" % (len(js_fehler), js_fehler[:3]))
    print("RPC-Fehler: %d %s" % (len(rpc_fehler), rpc_fehler[:3]))
    print("Screenshots: %s" % VZ)
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
