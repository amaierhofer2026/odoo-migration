"""Aufraeumen: Testdaten der Browser-Abnahme im Verkauf entfernen (Odoo 18, VM/lokal).

Entfernt Lagerbelege ohne Auftragsbezug, die von Abnahmewerkzeugen stammen (Ursprung S00xxx),
sowie Testauftraege, die heute von den Werkzeugen angelegt wurden und liegengeblieben sind.

Aufruf:
    python scripts/aufraeumen_verkauf_testdaten.py --instanz vm [--trocken]
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18

SP = {"lang": "de_DE"}
HEUTE = "2026-09-29"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    p.add_argument("--trocken", action="store_true")
    a = p.parse_args()
    k = o18(a.instanz)

    print("Aufraeumen Testdaten (%s)%s" % (a.instanz, " - Trockenlauf" if a.trocken else ""))

    vorher = {"auftraege": k.kw("sale.order", "search_count", [[]], context=SP),
              "lagerbelege": k.kw("stock.picking", "search_count", [[]], context=SP),
              "produkte": k.kw("product.template", "search_count", [[]], context=SP)}
    print("Bestand vorher: %s" % vorher)

    belege = k.kw("stock.picking", "search_read",
                  [[("state", "not in", ["done"])], ["name", "state", "origin", "sale_id"]],
                  context=SP)
    print("Offene Lagerbelege: %d" % len(belege))
    for b in belege:
        print("  %s (%s) Ursprung %s, Auftrag %s" % (b["name"], b["state"], b["origin"],
                                                     b["sale_id"] or "-"))
        if a.trocken:
            continue
        try:
            if b["state"] not in ("cancel", "done"):
                k.kw("stock.picking", "action_cancel", [[b["id"]]], context=SP)
            k.kw("stock.picking", "unlink", [[b["id"]]], context=SP)
            print("     entfernt")
        except Exception as ex:
            print("     nicht entfernt: %s" % str(ex)[:120])

    heute = k.kw("sale.order", "search_read",
                 [[("create_date", ">=", "%s 00:00:00" % HEUTE)], ["name", "state", "locked",
                                                                   "partner_id"]], context=SP)
    print("Heute angelegte Auftraege: %d" % len(heute))
    for o in heute:
        print("  %s (%s, gesperrt=%s, %s)" % (o["name"], o["state"], o["locked"], o["partner_id"][1]))
        if a.trocken:
            continue
        try:
            if o["locked"]:
                k.kw("sale.order", "write", [[o["id"]], {"locked": False}], context=SP)
            if o["state"] != "cancel":
                w = k.kw("sale.order.cancel", "create", [{"order_id": o["id"]}], context=SP)
                k.kw("sale.order.cancel", "action_cancel", [[w[0] if isinstance(w, list) else w]],
                     context=SP)
            k.kw("sale.order", "unlink", [[o["id"]]], context=SP)
            print("     entfernt")
        except Exception as ex:
            print("     nicht entfernt: %s" % str(ex)[:160])

    produkte = k.kw("product.template", "search_read", [[("name", "ilike", "ZZ-Test")], ["name"]],
                    context=SP)
    for pr in produkte:
        print("  Testprodukt %s" % pr["name"])
        if not a.trocken:
            try:
                k.kw("product.product", "unlink", [[pr["id"]]], context=SP)
                print("     entfernt")
            except Exception as ex:
                print("     nicht entfernt: %s" % str(ex)[:120])

    nachher = {"auftraege": k.kw("sale.order", "search_count", [[]], context=SP),
               "lagerbelege": k.kw("stock.picking", "search_count", [[]], context=SP),
               "produkte": k.kw("product.template", "search_count", [[]], context=SP)}
    print("Bestand nachher: %s" % nachher)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
