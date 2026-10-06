"""Temporaeres Lager-Testprodukt in der Odoo-18-Testinstanz (Auftrag Anna 05.10.2026).

Nur Odoo 18 (lokal oder VM). Odoo 11 wird nie beruehrt.

Aufrufe:
  python scripts/lagerprodukt_test.py lokal zaehlen
  python scripts/lagerprodukt_test.py lokal anlegen
  python scripts/lagerprodukt_test.py lokal produktart Plattform   # Konsistenzprobe
  python scripts/lagerprodukt_test.py lokal produktart leeren
  python scripts/lagerprodukt_test.py lokal menge 5                # Inventuranpassung
  python scripts/lagerprodukt_test.py lokal aufraeumen             # alles wieder entfernen
  python scripts/lagerprodukt_test.py lokal pruefen                # Restkontrolle

Die erzeugten Datensatz-IDs werden in %LOCALAPPDATA%\\Temp\\lager_test.json protokolliert.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

CTX = {"lang": "de_DE"}
CODE = "ZZ-TEST-LAGER"
NAME = "ZZ-TEST Lagerprodukt (temporaer)"
PROTO = os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "Temp", "lager_test.json")
MODELLE = ("product.template", "product.product", "stock.quant", "stock.move", "stock.move.line",
           "stock.picking", "account.move", "stock.lot", "account.move.line")


def lade_proto():
    if os.path.exists(PROTO):
        with open(PROTO, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def speichere_proto(d):
    with open(PROTO, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)


def zaehlen(k, inst, still=False):
    aus = {}
    for m in MODELLE:
        try:
            aus[m] = k.kw(m, "search_count", [[]], context=CTX)
        except RuntimeError:
            aus[m] = None
    aus["filter_Bestandsaufloesung"] = k.kw(
        "product.template", "search_count", [[("qty_available", "<=", 0),
                                              ("is_storable", "=", True)]], context=CTX)
    aus["filter_Lagerverwaltung"] = k.kw(
        "product.template", "search_count", [[("is_storable", "=", True)]], context=CTX)
    aus["filter_Gueter"] = k.kw(
        "product.template", "search_count", [[("type", "=", "consu")]], context=CTX)
    if not still:
        print("Bestand %s:" % inst)
        for m, n in aus.items():
            print("   %-28s %s" % (m, n))
    return aus


def lege_an(k, inst):
    vorhanden = k.kw("product.template", "search", [[("default_code", "=", CODE)]], context=CTX)
    if vorhanden:
        print("Testprodukt existiert schon:", vorhanden)
        return vorhanden[0]
    tid = k.kw("product.template", "create", [{
        "name": NAME, "default_code": CODE, "type": "consu", "is_storable": True,
        "sale_ok": True, "purchase_ok": True, "list_price": 12.0, "standard_price": 7.0,
    }], context=CTX)
    print("Testprodukt angelegt: product.template", tid, "| type=consu, is_storable=True,",
          "product_type_id leer")
    p = lade_proto()
    p.setdefault(inst, {})["template"] = tid
    speichere_proto(p)
    return tid


def daten(k, tid):
    d = k.kw("product.template", "read",
             [[tid], ["id", "name", "default_code", "type", "is_storable", "product_type_id",
                      "sale_ok", "purchase_ok", "qty_available", "responsible_id"]],
             context=CTX)[0]
    print("Testprodukt:", json.dumps(d, ensure_ascii=False, default=str))
    return d


def produktart(k, inst, was):
    tid = lade_proto()[inst]["template"]
    if was == "leeren":
        k.kw("product.template", "write", [[tid], {"product_type_id": False}], context=CTX)
        print("Produktart geleert")
        return
    treffer = k.kw("itk_product.product_type", "search", [[("name", "=", was)]], context=CTX)
    if not treffer:
        print("Produktart nicht gefunden:", was)
        return
    k.kw("product.template", "write", [[tid], {"product_type_id": treffer[0]}], context=CTX)
    print("Produktart gesetzt:", was, "(ID %s)" % treffer[0])


def menge(k, inst, anzahl):
    tid = lade_proto()[inst]["template"]
    variante = k.kw("product.template", "read", [[tid], ["product_variant_id"]],
                    context=CTX)[0]["product_variant_id"][0]
    lager = k.kw("stock.location", "search", [[("usage", "=", "internal")]], context=CTX)[0]
    print("Ziellager (intern):", lager, k.kw("stock.location", "read", [[lager], ["complete_name"]],
                                             context=CTX)[0]["complete_name"])
    ctx = dict(CTX, inventory_mode=True)
    vorhanden = k.kw("stock.quant", "search",
                     [[("product_id", "=", variante), ("location_id", "=", lager)]], context=ctx)
    if vorhanden:
        qid = vorhanden[0]
        k.kw("stock.quant", "write", [[qid], {"inventory_quantity": anzahl}], context=ctx)
    else:
        qid = k.kw("stock.quant", "create", [{"product_id": variante, "location_id": lager,
                                              "inventory_quantity": anzahl}], context=ctx)
    k.kw("stock.quant", "action_apply_inventory", [[qid]], context=ctx)
    p = lade_proto()
    p.setdefault(inst, {}).setdefault("quants", [])
    if qid not in p[inst]["quants"]:
        p[inst]["quants"].append(qid)
    p[inst]["variante"] = variante
    speichere_proto(p)
    print("Inventuranpassung gebucht: Menge %s (quant %s, Variante %s)" % (anzahl, qid, variante))
    daten(k, tid)


def aufraeumen(k, inst):
    p = lade_proto()
    d = p.get(inst) or {}
    tid = d.get("template")
    if not tid:
        print("Nichts zu bereinigen (kein Protokolleintrag).")
        return
    variante = d.get("variante")
    if not variante:
        v = k.kw("product.template", "read", [[tid], ["product_variant_id"]], context=CTX)
        variante = v[0]["product_variant_id"][0] if v and v[0].get("product_variant_id") else None
    ctx = dict(CTX, inventory_mode=True)
    # 1. Mengen zuruecksetzen/loeschen
    if variante:
        quants = k.kw("stock.quant", "search",
                      [[("product_id", "=", variante)]], context=ctx)
        if quants:
            try:
                k.kw("stock.quant", "unlink", [quants], context=ctx)
                print("Quants geloescht:", quants)
            except RuntimeError as e:
                print("Quants nicht loeschbar:", str(e)[:120])
        # 2. Lagerbewegungen
        for modell in ("stock.move.line", "stock.move"):
            ids = k.kw(modell, "search", [[("product_id", "=", variante)]], context=ctx)
            if ids:
                try:
                    k.kw(modell, "unlink", [ids], context=ctx)
                    print("%s geloescht: %s" % (modell, ids))
                except RuntimeError as e:
                    print("%s nicht loeschbar: %s" % (modell, str(e)[:150]))
    # 3. Produkt loeschen
    try:
        k.kw("product.template", "unlink", [[tid]], context=CTX)
        print("Testprodukt geloescht: product.template", tid)
    except RuntimeError as e:
        print("Testprodukt nicht loeschbar:", str(e)[:200])
    p.pop(inst, None)
    speichere_proto(p)


if __name__ == "__main__":
    inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
    befehl = sys.argv[2] if len(sys.argv) > 2 else "zaehlen"
    k = o18(inst)
    if befehl == "zaehlen":
        zaehlen(k, inst)
    elif befehl == "anlegen":
        lege_an(k, inst)
        daten(k, lade_proto()[inst]["template"])
    elif befehl == "produktart":
        produktart(k, inst, sys.argv[3])
        daten(k, lade_proto()[inst]["template"])
    elif befehl == "menge":
        menge(k, inst, float(sys.argv[3]))
    elif befehl == "aufraeumen":
        aufraeumen(k, inst)
        zaehlen(k, inst)
    elif befehl == "pruefen":
        rest = k.kw("product.template", "search", [[("default_code", "=", CODE)]], context=CTX)
        print("Rest-Testprodukte:", rest)
        zaehlen(k, inst)
    else:
        print(__doc__)
