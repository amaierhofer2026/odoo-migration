"""Browser-Abnahme Teil 5: Lieferanbindung des Verkaufs (Odoo 18, echter Browser).

Ablauf:
  1. Testdaten per RPC anlegen (Lagerartikel + Verkaufsauftrag, bestaetigt -> Lieferung)
  2. im Browser: Auftragsformular oeffnen, Knopf "Lieferungen" (Smart Button) pruefen
  3. Knopf anklicken -> Lieferliste mit dem Lagerbeleg, Beleg oeffnen
  4. Formular "Weitere Informationen": Lager und Lieferpolitik sichtbar
  5. Testdaten wieder bereinigen und Bestandszahlen pruefen
  6. JavaScript- und RPC-Fehler

Aufruf:
    uv run --with playwright python scripts/browser_verkauf_lieferung.py --instanz vm
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_verkauf_menue import lade_env, rpc_client, REPO

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session121", "lieferung")
SP = {"lang": "de_DE"}
PRODUKT = "ZZ-Test Lagerartikel Browser (bitte loeschen)"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    a = p.parse_args()

    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    vorher = {"auftraege": kw("sale.order", "search_count", [[]], context=SP),
              "lagerbelege": kw("stock.picking", "search_count", [[]], context=SP),
              "produkte": kw("product.template", "search_count", [[]], context=SP)}
    print("Instanz: %s (%s)" % (a.instanz, url))
    print("Bestand vorher: %s" % vorher)

    partner = kw("res.partner", "search_read", [[("name", "=", "Test Firma")], ["name"]], context=SP,
                 limit=1)
    if not partner:
        partner = kw("res.partner", "search_read", [[("customer_rank", ">", 0)], ["name"]], context=SP,
                     limit=1)
    produkt_id = kw("product.product", "create", [{
        "name": PRODUKT, "type": "consu", "is_storable": True, "list_price": 10.0,
        "sale_ok": True, "purchase_ok": False}], context=SP)
    auftrag_id = kw("sale.order", "create", [{
        "partner_id": partner[0]["id"],
        "order_line": [(0, 0, {"product_id": produkt_id, "product_uom_qty": 2.0,
                               "price_unit": 10.0, "name": PRODUKT})]}], context=SP)
    kw("sale.order", "action_confirm", [[auftrag_id]], context=SP)
    auftrag = kw("sale.order", "read", [[auftrag_id], ["name", "state", "delivery_count",
                                                      "picking_ids", "warehouse_id",
                                                      "picking_policy"]], context=SP)[0]
    picking_id = auftrag["picking_ids"][0] if auftrag["picking_ids"] else None
    picking = kw("stock.picking", "read", [[picking_id], ["name", "state", "origin"]], context=SP)[0] \
        if picking_id else None
    print("Testauftrag %s (Status %s, Lieferungen %d), Lagerbeleg %s"
          % (auftrag["name"], auftrag["state"], auftrag["delivery_count"],
             picking["name"] if picking else "-"))

    from playwright.sync_api import sync_playwright
    os.makedirs(VZ, exist_ok=True)
    js_fehler, rpc_fehler = [], []
    try:
        with sync_playwright() as pw:
            ctx = pw.chromium.launch_persistent_context(
                user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_verkauf_lief_%s" % a.instanz),
                channel="chrome", headless=True, viewport={"width": 1900, "height": 1400})
            ctx.add_init_script(
                "window.__errs=[];"
                "window.addEventListener('error', e => window.__errs.push(''+e.message));"
                "window.addEventListener('unhandledrejection', e => window.__errs.push(''+e.reason));")
            ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
            seite = ctx.pages[0] if ctx.pages else ctx.new_page()
            seite.on("response", lambda r: rpc_fehler.append("%s %s" % (r.status, r.url))
                     if ("/web/dataset/call_kw" in r.url and r.status >= 400) else None)

            print("\n--- 1. Auftragsformular mit Lieferungen ---")
            seite.goto("%s/odoo/sales/%d" % (url, auftrag_id))
            seite.wait_for_selector(".o_form_view", timeout=90000)
            seite.wait_for_timeout(5000)
            knoepfe = seite.eval_on_selector_all(
                ".o_form_statusbar button, .oe_button_box button, .o_control_panel button",
                "els => els.filter(e => e.offsetParent).map(e => (e.innerText||'').replace(/\\s+/g,' ').trim())")
            print("       Knoepfe: %s" % str([k for k in knoepfe if k])[:300])
            pruefe(any("Lieferung" in (k or "") for k in knoepfe), "Smart Button 'Lieferungen' im Formular")
            seite.screenshot(path=os.path.join(VZ, "01_Auftrag_Lieferungen_%s.png" % a.instanz), full_page=True)

            print("\n--- 2. Weitere Informationen: Lager und Lieferpolitik ---")
            reiter = seite.query_selector("a:has-text('Weitere Informationen')")
            if reiter:
                reiter.click()
                seite.wait_for_timeout(2500)
            formtext = re.sub(r"\s+", " ", seite.eval_on_selector(".o_form_sheet", "e => e ? e.innerText : ''"))
            pruefe("Lieferpolitik" in formtext or "Bereitstellen" in formtext or "Sobald wie möglich" in formtext,
                   "Lieferpolitik im Formular sichtbar")
            pruefe(any(w in formtext for w in ("Lager", "IT-Kommunal GmbH")), "Lagerfeld im Formular")
            seite.screenshot(path=os.path.join(VZ, "02_Auftrag_Weitere_Informationen_%s.png" % a.instanz), full_page=True)

            print("\n--- 3. Lieferliste/Lieferbeleg ueber den Smart Button ---")
            ziel = seite.query_selector(".oe_button_box button:has-text('Lieferung')") \
                or seite.query_selector("button:has-text('Lieferung')")
            pruefe(ziel is not None, "Smart Button anklickbar")
            if ziel:
                ziel.click()
                seite.wait_for_timeout(6000)
                liste = re.sub(r"\s+", " ", seite.eval_on_selector("body", "e => e.innerText"))
                pruefe(picking["name"] in liste if picking else False,
                       "Ansicht zeigt den Lagerbeleg %s" % (picking["name"] if picking else "-"))
                pruefe(auftrag["name"] in liste, "Bezug zum Auftrag %s sichtbar" % auftrag["name"])
                pruefe("Lieferadresse" in liste or "Vorgangsart" in liste, "Lieferbeleg-Formular geladen")
                pruefe(PRODUKT in liste or "ZZ-Test" in liste, "Position des Belegs sichtbar")
                pruefe("Bereit" in liste or "Bestätigt" in liste or "Zugewiesen" in liste,
                       "Status des Belegs sichtbar")
                seite.screenshot(path=os.path.join(VZ, "03_Lieferbeleg_%s.png" % a.instanz), full_page=True)

                print("\n--- 4. Lieferbeleg gegenpruefen (Formular oder Liste) ---")
                kopf = re.sub(r"\s+", " ", seite.eval_on_selector(".o_breadcrumb, .o_control_panel",
                                                                  "e => e ? e.innerText : ''"))
                if picking["name"] in kopf:
                    pruefe(True, "Lieferbeleg %s geoeffnet (Einzeltreffer oeffnet direkt das Formular)"
                           % picking["name"])
                    felder = re.sub(r"\s+", " ", seite.eval_on_selector(".o_form_sheet",
                                                                        "e => e ? e.innerText : ''"))
                    pruefe("Referenzbeleg" in felder, "Referenzbeleg im Lieferbeleg vorhanden")
                    seite.screenshot(path=os.path.join(VZ, "04_Lieferbeleg_Formular_%s.png" % a.instanz), full_page=True)
                else:
                    zeile = seite.query_selector(".o_data_row:has-text('%s')" % picking["name"]) if picking else None
                    pruefe(zeile is not None, "Lieferzeile in der Liste vorhanden")
                    if zeile:
                        zeile.click()
                        seite.wait_for_timeout(5000)
                        beleg = re.sub(r"\s+", " ", seite.eval_on_selector(".o_form_view", "e => e ? e.innerText : ''"))
                        pruefe(picking["name"] in beleg and "Referenzbeleg" in beleg,
                               "Lieferbeleg %s geoeffnet" % picking["name"])
                        seite.screenshot(path=os.path.join(VZ, "04_Lieferbeleg_Formular_%s.png" % a.instanz), full_page=True)

            js_fehler[:] = seite.evaluate("() => window.__errs") or []
            ctx.close()
    finally:
        print("\n--- 5. Testdaten bereinigen ---")
        try:
            if picking_id:
                kw("stock.picking", "action_cancel", [[picking_id]], context=SP)
            daten = kw("sale.order", "read", [[auftrag_id], ["state", "locked"]], context=SP)[0]
            if daten["state"] == "sale":
                if daten["locked"]:
                    kw("sale.order", "write", [[auftrag_id], {"locked": False}], context=SP)
                wiz = kw("sale.order.cancel", "create", [{"order_id": auftrag_id}], context=SP)
                kw("sale.order.cancel", "action_cancel", [[wiz]], context=SP)
            kw("sale.order", "unlink", [[auftrag_id]], context=SP)
            if picking_id:
                kw("stock.picking", "unlink", [[picking_id]], context=SP)
            kw("product.product", "unlink", [[produkt_id]], context=SP)
            print("  Auftrag, Lagerbeleg und Testprodukt entfernt")
        except Exception as ex:
            print("  Bereinigung: %s" % str(ex)[:200])

    nachher = {"auftraege": kw("sale.order", "search_count", [[]], context=SP),
               "lagerbelege": kw("stock.picking", "search_count", [[]], context=SP),
               "produkte": kw("product.template", "search_count", [[]], context=SP),
               "testprodukte": kw("product.template", "search_count", [[("name", "=", PRODUKT)]], context=SP)}
    print("\nBestand nachher: %s" % nachher)
    pruefe(nachher["auftraege"] == vorher["auftraege"], "Auftragsbestand unveraendert (%d)" % nachher["auftraege"])
    pruefe(nachher["produkte"] == vorher["produkte"], "Produktbestand unveraendert (%d)" % nachher["produkte"])
    pruefe(nachher["testprodukte"] == 0, "Testprodukt entfernt")

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    print("JavaScript-Fehler: %d %s" % (len(js_fehler), js_fehler[:3]))
    print("RPC-Fehler: %d %s" % (len(rpc_fehler), rpc_fehler[:3]))
    print("Screenshots: %s" % VZ)
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
