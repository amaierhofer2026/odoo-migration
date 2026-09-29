"""Diagnose: Fehler beim Klick auf den Smart Button "Lieferungen" (Odoo 18).

Legt kurzlebige Testdaten an, oeffnet den Auftrag im Browser, klickt den Smart Button und
liest den Fehlerdialog samt technischen Details aus. Raeumt anschliessend auf.

Aufruf:
    uv run --with playwright python scripts/diag_verkauf_lieferung_fehler.py --instanz vm
"""
from __future__ import annotations

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from browser_verkauf_menue import lade_env, rpc_client, REPO

SP = {"lang": "de_DE"}
PRODUKT = "ZZ-Test Lagerartikel Diagnose (bitte loeschen)"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = "https://k001959vsx.ipax.at" if a.instanz == "vm" else "http://localhost:8069"
    domain = "k001959vsx.ipax.at" if a.instanz == "vm" else "localhost"
    sid, kw = rpc_client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])

    partner = kw("res.partner", "search", [[("name", "=", "Test Firma")]], context=SP, limit=1)
    produkt_id = kw("product.product", "create", [{
        "name": PRODUKT, "type": "consu", "is_storable": True, "list_price": 10.0,
        "sale_ok": True, "purchase_ok": False}], context=SP)
    auftrag_id = kw("sale.order", "create", [{
        "partner_id": partner[0],
        "order_line": [(0, 0, {"product_id": produkt_id, "product_uom_qty": 1.0,
                               "price_unit": 10.0, "name": PRODUKT})]}], context=SP)
    kw("sale.order", "action_confirm", [[auftrag_id]], context=SP)
    auftrag = kw("sale.order", "read", [[auftrag_id], ["name", "picking_ids"]], context=SP)[0]
    print("Testauftrag %s, Lagerbelege %s" % (auftrag["name"], auftrag["picking_ids"]))

    from playwright.sync_api import sync_playwright
    konsole = []
    try:
        with sync_playwright() as pw:
            ctx = pw.chromium.launch_persistent_context(
                user_data_dir=os.path.join(os.environ.get("TEMP", "/tmp"), "pw_diag_lief_%s" % a.instanz),
                channel="chrome", headless=True, viewport={"width": 1900, "height": 1400})
            ctx.add_cookies([{"name": "session_id", "value": sid, "domain": domain, "path": "/"}])
            seite = ctx.pages[0] if ctx.pages else ctx.new_page()
            seite.on("console", lambda m: konsole.append("%s: %s" % (m.type, m.text[:200])))
            anfragen = []
            seite.on("response", lambda r: anfragen.append("%s %s" % (r.status, r.url))
                     if r.status >= 400 else None)
            seite.goto("%s/odoo/sales/%d" % (url, auftrag_id))
            seite.wait_for_selector(".o_form_view", timeout=90000)
            seite.wait_for_timeout(5000)
            print("\n=== Klick auf 'Lieferung' ===")
            seite.click("button:has-text('Lieferung')", timeout=20000)
            seite.wait_for_timeout(7000)
            fehlerdialog = seite.query_selector(".o_error_dialog, .modal-dialog")
            if fehlerdialog:
                print("Dialogtext:", re.sub(r"\s+", " ", fehlerdialog.inner_text())[:600])
                try:
                    seite.click(".o_error_dialog button:has-text('Technische Details')", timeout=8000)
                    seite.wait_for_timeout(2500)
                    details = seite.eval_on_selector(".o_error_dialog, .modal-dialog", "e => e.innerText")
                    print("\n=== Technische Details ===")
                    print(re.sub(r"\n{3,}", "\n", details)[:2500])
                except Exception as ex:
                    print("Details nicht lesbar: %s" % str(ex)[:150])
            else:
                inhalt = re.sub(r"\s+", " ", seite.eval_on_selector("body", "e => e.innerText"))
                print("Kein Dialog. Seiteninhalt:", inhalt[:400])
            print("\n=== Fehlerhafte Anfragen ===")
            for x in anfragen[:10]:
                print("  ", x)
            print("\n=== Konsole (letzte 12) ===")
            for x in konsole[-12:]:
                print("  ", x)
            ctx.close()
    finally:
        try:
            if auftrag["picking_ids"]:
                kw("stock.picking", "action_cancel", [[auftrag["picking_ids"][0]]], context=SP)
            daten = kw("sale.order", "read", [[auftrag_id], ["state", "locked"]], context=SP)[0]
            if daten["state"] == "sale":
                if daten["locked"]:
                    kw("sale.order", "write", [[auftrag_id], {"locked": False}], context=SP)
                wiz = kw("sale.order.cancel", "create", [{"order_id": auftrag_id}], context=SP)
                kw("sale.order.cancel", "action_cancel", [[wiz]], context=SP)
            kw("sale.order", "unlink", [[auftrag_id]], context=SP)
            if auftrag["picking_ids"]:
                kw("stock.picking", "unlink", [[auftrag["picking_ids"][0]]], context=SP)
            kw("product.product", "unlink", [[produkt_id]], context=SP)
            print("\nTestdaten entfernt.")
        except Exception as ex:
            print("\nBereinigung: %s" % str(ex)[:200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
