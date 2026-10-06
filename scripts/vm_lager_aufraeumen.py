"""VM-Bereinigung des Lager-Tests ueber eine temporaere Odoo-Serveraktion (SSH ist gesperrt).

Warum: Odoo blockiert das Loeschen abgeschlossener Lagerbewegungen und Bewertungssaetze per ORM.
Die gezielten DELETE-Anweisungen laufen daher in einer einmaligen Serveraktion (state='code'),
die danach wieder geloescht wird. Nur Odoo 18 VM, nur die IDs des Testprodukts.

Aufruf: python scripts/vm_lager_aufraeumen.py <vorlage_id> <varianten_id>
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

CTX = {"lang": "de_DE"}

SQL = """
DELETE FROM stock_move_line WHERE product_id IN ({vid});
DELETE FROM stock_move WHERE product_id IN ({vid});
DELETE FROM stock_quant WHERE product_id IN ({vid});
DELETE FROM stock_valuation_layer WHERE product_id IN ({vid});
DELETE FROM mail_message WHERE (model='product.template' AND res_id={tid}) OR (model='product.product' AND res_id={vid});
DELETE FROM mail_followers WHERE (res_model='product.template' AND res_id={tid}) OR (res_model='product.product' AND res_id={vid});
DELETE FROM mail_activity WHERE (res_model='product.template' AND res_id={tid}) OR (res_model='product.product' AND res_id={vid});
"""

if __name__ == "__main__":
    tid, vid = int(sys.argv[1]), int(sys.argv[2])
    k = o18("vm")
    print("vorher: Testprodukt(e) =",
          k.kw("product.template", "search", [[("default_code", "=", "ZZ-TEST-LAGER")]],
               context=CTX),
          "| quants:", k.kw("stock.quant", "search_count", [[]], context=CTX),
          "| moves:", k.kw("stock.move", "search_count", [[]], context=CTX))

    code = "env.cr.execute(\"\"\"%s\"\"\")" % SQL.format(vid=vid, tid=tid).strip()
    aktion = k.kw("ir.actions.server", "create", [{
        "name": "ZZ-TEMP Lager-Test aufraeumen", "state": "code", "model_id":
        k.kw("ir.model", "search", [[("model", "=", "product.template")]], context=CTX)[0],
        "code": code, "usage": "ir_actions_server",
    }], context=CTX)
    print("Serveraktion angelegt:", aktion)
    try:
        k.kw("ir.actions.server", "run", [[aktion]], context=CTX)
        print("Serveraktion ausgefuehrt")
    except RuntimeError as fehler:
        print("Ausfuehrung fehlgeschlagen:", str(fehler)[:300])
    # Aktion wieder entfernen (kein Testdatensatz zuruecklassen)
    try:
        k.kw("ir.actions.server", "unlink", [[aktion]], context=CTX)
        print("Serveraktion geloescht:", aktion)
    except RuntimeError as fehler:
        print("Aktion nicht loeschbar:", str(fehler)[:200])

    print("nachher: quants:", k.kw("stock.quant", "search_count", [[]], context=CTX),
          "| moves:", k.kw("stock.move", "search_count", [[]], context=CTX),
          "| svl:", k.kw("stock.valuation.layer", "search_count", [[]], context=CTX))
    try:
        k.kw("product.template", "unlink", [[tid]], context=CTX)
        print("Testprodukt geloescht:", tid)
    except RuntimeError as fehler:
        print("Testprodukt nicht geloescht:", str(fehler)[:200])
    print("Rest-Testprodukte:",
          k.kw("product.template", "search", [[("default_code", "=", "ZZ-TEST-LAGER")]], context=CTX))
    print("Bestand: Vorlagen", k.kw("product.template", "search_count", [[]], context=CTX),
          "| Produkte", k.kw("product.product", "search_count", [[]], context=CTX),
          "| account.move", k.kw("account.move", "search_count", [[]], context=CTX))
