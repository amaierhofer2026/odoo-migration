"""Teil 5: Funktionspruefung der Lager-/Lieferanbindung des Verkaufs (Odoo 18).

Legt einen Testdatensatz an (Lagerprodukt + Verkaufsauftrag), prueft die Lieferfunktion und
raeumt anschliessend alles wieder weg:

  1. Lagerprodukt anlegen (is_storable)
  2. Verkaufsauftrag mit einer Position anlegen und bestaetigen
  3. pruefen: warehouse_id, picking_policy, delivery_count, picking_ids, Lieferung mit
     Position und Verkaufsbezug
  4. aufraeumen: Lieferung stornieren, Auftrag stornieren und loeschen, Produkt loeschen
  5. Bestandszahlen vorher/nachher

Aufruf:
    python scripts/pruefe_verkauf_lieferung.py --instanz vm
    python scripts/pruefe_verkauf_lieferung.py --instanz lokal
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}
PRODUKT = "ZZ-Test Lagerartikel Session 121 (bitte loeschen)"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    a = p.parse_args()
    k = o18(a.instanz)
    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    print("Pruefung Lieferanbindung Verkauf (%s)" % a.instanz)
    zustand = {
        "auftraege": k.kw("sale.order", "search_count", [[]], context=SP),
        "lagerbelege": k.kw("stock.picking", "search_count", [[]], context=SP),
        "produkte": k.kw("product.template", "search_count", [[]], context=SP),
    }
    print("  Bestand vorher: %s" % zustand)

    print("\n--- 1. Felder der Lageranbindung ---")
    for feld in ("warehouse_id", "picking_policy", "picking_ids", "delivery_count",
                 "procurement_group_id"):
        treffer = k.kw("ir.model.fields", "search_count",
                       [[("model", "=", "sale.order"), ("name", "=", feld)]], context=SP)
        pruefe(bool(treffer), "Feld sale.order.%s vorhanden" % feld)
    for feld in ("move_ids", "qty_delivered"):
        treffer = k.kw("ir.model.fields", "search_count",
                       [[("model", "=", "sale.order.line"), ("name", "=", feld)]], context=SP)
        pruefe(bool(treffer), "Feld sale.order.line.%s vorhanden" % feld)
    lager = k.kw("ir.model.fields", "search_count", [[("model", "=", "stock.picking")]], context=SP)
    pruefe(lager > 0, "Modell stock.picking vorhanden (%d Felder)" % lager)

    partner = k.kw("res.partner", "search", [[("name", "=", "Test Firma")]], context=SP, limit=1)
    if not partner:
        partner = k.kw("res.partner", "search", [[("customer_rank", ">", 0)]], context=SP, limit=1)
    pruefe(bool(partner), "Testkunde gefunden")
    if not partner:
        return 1

    produkte_vorher = k.kw("product.template", "search_count", [[("name", "=", PRODUKT)]], context=SP)
    auftraege_vorher = k.kw("sale.order", "search_count", [[("partner_id", "=", partner[0])]], context=SP)
    print("  Testprodukt vorher vorhanden: %d, Auftraege des Testkunden: %d" % (produkte_vorher, auftraege_vorher))

    produkt = auftrag = picking = None
    try:
        print("\n--- 2. Testdaten anlegen ---")
        produkt_id = k.kw("product.product", "create", [{
            "name": PRODUKT, "type": "consu", "is_storable": True, "list_price": 10.0,
            "sale_ok": True, "purchase_ok": False,
        }], context=SP)
        produkt = k.kw("product.product", "read", [[produkt_id], ["name", "is_storable", "type"]], context=SP)[0]
        print("  Produkt: %s (is_storable=%s)" % (produkt["name"], produkt["is_storable"]))
        pruefe(produkt["is_storable"] is True, "Produkt ist lagermassig (is_storable)")

        auftrag_id = k.kw("sale.order", "create", [{
            "partner_id": partner[0],
            "order_line": [(0, 0, {"product_id": produkt_id, "product_uom_qty": 2.0,
                                   "price_unit": 10.0, "name": PRODUKT})],
        }], context=SP)
        auftrag = k.kw("sale.order", "read", [[auftrag_id], ["name", "state", "warehouse_id",
                                                            "picking_policy", "locked"]], context=SP)[0]
        print("  Auftrag %s angelegt (%s)" % (auftrag["name"], auftrag["state"]))
        pruefe(auftrag["state"] == "draft", "Auftrag ist im Entwurf")

        k.kw("sale.order", "action_confirm", [[auftrag_id]], context=SP)
        auftrag = k.kw("sale.order", "read", [[auftrag_id], ["name", "state", "warehouse_id",
                                                            "picking_policy", "delivery_count",
                                                            "picking_ids", "locked"]], context=SP)[0]
        print("  Nach Bestaetigung: Status %s, Lager %s, Lieferpolitik %s, Lieferungen %s, gesperrt %s"
              % (auftrag["state"], auftrag["warehouse_id"], auftrag["picking_policy"],
                 auftrag["delivery_count"], auftrag["locked"]))

        print("\n--- 3. Pruefungen der Lieferfunktion ---")
        pruefe(auftrag["state"] == "sale", "Auftrag ist bestaetigt")
        pruefe(bool(auftrag["warehouse_id"]), "Auftrag hat ein Lager (%s)"
               % (auftrag["warehouse_id"][1] if auftrag["warehouse_id"] else "-"))
        pruefe(auftrag["picking_policy"] in ("direct", "one"), "Lieferpolitik gesetzt (%s)"
               % auftrag["picking_policy"])
        pruefe(auftrag["delivery_count"] == 1, "Lieferungen am Auftrag: %d" % auftrag["delivery_count"])
        pruefe(len(auftrag["picking_ids"]) == 1, "picking_ids enthaelt einen Lagerbeleg")

        if auftrag["picking_ids"]:
            picking_id = auftrag["picking_ids"][0]
            picking = k.kw("stock.picking", "read",
                           [[picking_id], ["name", "state", "partner_id", "picking_type_id",
                                           "scheduled_date", "origin", "move_ids", "sale_id"]],
                           context=SP)[0]
            print("  Lagerbeleg %s (%s), Typ %s, Ursprung %s"
                  % (picking["name"], picking["state"], picking["picking_type_id"][1] if picking["picking_type_id"] else "-", picking["origin"]))
            pruefe(picking["state"] not in ("cancel", "done"), "Lagerbeleg ist offen (%s)" % picking["state"])
            pruefe(bool(picking["move_ids"]), "Lagerbeleg hat Bewegungen (%d)" % len(picking["move_ids"]))
            pruefe(bool(picking.get("sale_id")) and picking["sale_id"][0] == auftrag_id,
                   "Lagerbeleg ist mit dem Auftrag verknuepft (%s)" % (picking["sale_id"] or "-"))
            if picking["move_ids"]:
                bewegung = k.kw("stock.move", "read",
                                [[picking["move_ids"][0]], ["product_id", "product_uom_qty",
                                                            "sale_line_id", "state"]], context=SP)[0]
                print("  Bewegung: %s x %s, Auftragsposition %s, Status %s"
                      % (bewegung["product_uom_qty"], bewegung["product_id"][1],
                         bewegung["sale_line_id"] or "-", bewegung["state"]))
                pruefe(bewegung["product_id"][0] == produkt_id, "Bewegung betrifft das Testprodukt")
                pruefe(bewegung["product_uom_qty"] == 2.0, "Menge der Bewegung ist 2,00")
                pruefe(bool(bewegung["sale_line_id"]), "Bewegung ist mit der Auftragsposition verknuepft")
    finally:
        print("\n--- 4. Aufraeumen der Testdaten ---")
        try:
            if picking:
                k.kw("stock.picking", "action_cancel", [[picking["id"]]], context=SP)
                print("  Lagerbeleg %s storniert" % picking["name"])
        except Exception as ex:
            print("  Lagerbeleg-Storno: %s" % str(ex)[:120])
        try:
            if auftrag:
                a_daten = k.kw("sale.order", "read", [[auftrag["id"]], ["name", "state", "locked"]], context=SP)[0]
                if a_daten["state"] == "sale":
                    if a_daten["locked"]:
                        k.kw("sale.order", "write", [[auftrag["id"]], {"locked": False}], context=SP)
                    wiz = k.kw("sale.order.cancel", "create", [{"order_id": auftrag["id"]}], context=SP)
                    k.kw("sale.order.cancel", "action_cancel", [[wiz]], context=SP)
                    print("  Auftrag %s storniert" % a_daten["name"])
        except Exception as ex:
            print("  Auftragsstorno: %s" % str(ex)[:160])
        try:
            if auftrag:
                k.kw("sale.order", "unlink", [[auftrag["id"]]], context=SP)
                print("  Auftrag %s geloescht" % auftrag["name"])
        except Exception as ex:
            print("  Auftrag loeschen: %s" % str(ex)[:160])
        try:
            if picking:
                k.kw("stock.picking", "unlink", [[picking["id"]]], context=SP)
                print("  Lagerbeleg %s geloescht" % picking["name"])
        except Exception as ex:
            print("  Lagerbeleg loeschen: %s" % str(ex)[:160])
        try:
            if produkt:
                k.kw("product.product", "unlink", [[produkt["id"]]], context=SP)
                print("  Produkt %s geloescht" % produkt["name"])
        except Exception as ex:
            print("  Produkt loeschen: %s" % str(ex)[:160])

    print("\n--- 5. Bestand nach dem Aufraeumen ---")
    nachher = {
        "auftraege": k.kw("sale.order", "search_count", [[]], context=SP),
        "lagerbelege": k.kw("stock.picking", "search_count", [[]], context=SP),
        "produkte": k.kw("product.template", "search_count", [[]], context=SP),
        "testprodukte": k.kw("product.template", "search_count", [[("name", "=", PRODUKT)]], context=SP),
    }
    print("  Bestand nachher: %s" % nachher)
    pruefe(nachher["auftraege"] == zustand["auftraege"], "Auftragsbestand unveraendert (%d)"
           % nachher["auftraege"])
    pruefe(nachher["produkte"] == zustand["produkte"], "Produktbestand unveraendert (%d)"
           % nachher["produkte"])
    pruefe(nachher["lagerbelege"] == zustand["lagerbelege"], "Lagerbelegbestand unveraendert (%d)"
           % nachher["lagerbelege"])
    pruefe(nachher["testprodukte"] == 0, "Testprodukt restlos entfernt")

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
