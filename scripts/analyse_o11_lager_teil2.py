"""Read-only-Tiefenpruefung Odoo 11: Lagerbelege, Produktart-Werte, Originalarchs.

Session 119, Teil 14. Ergaenzt scripts/analyse_o11_lager.py. Ausschliesslich lesend.

Aufruf: python scripts/analyse_o11_lager_teil2.py
"""
from __future__ import annotations

import collections
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            w[k.strip()] = v.strip()
    return w


def client():
    env = lade_env(os.path.join(REPO, ".env"))
    url, db = "https://portal.it-kommunal.at", "ITK_V1_a"
    user, pwd = "anna.maierhofer@it-kommunal.at", env["ODOO11_PWD"]
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rufe(pfad, params):
        r = urllib.request.Request(url + pfad,
                                   data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode(),
                                   headers={"Content-Type": "application/json"})
        with op.open(r, timeout=600) as f:
            return json.loads(f.read().decode())

    rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})

    def kw(model, methode, args, **kwargs):
        o = rufe("/web/dataset/call_kw", {"model": model, "method": methode, "args": args, "kwargs": kwargs})
        if "error" in o:
            return {"__fehler__": str(o["error"].get("data", {}).get("message", o["error"].get("message")))[:150]}
        return o.get("result")

    return kw


def g(kw, model, feld, dom=None, **k):
    r = kw(model, "read_group", [dom or [], [feld], [feld]], **k)
    if isinstance(r, list):
        return [(x.get(feld), x.get(feld + "_count", x.get("__count"))) for x in r]
    return r


def main() -> int:
    kw = client()
    sprache = {"lang": "de_DE"}

    print("=== 1. Zustaende der Lagerbelege in Odoo 11 ===")
    for model, feld in (("stock.move", "state"), ("stock.move.line", "state"), ("stock.picking", "state"),
                        ("stock.picking", "picking_type_id")):
        print("   %-18s %-18s %s" % (model, feld, g(kw, model, feld)))
    print("   sale.order Zustaende: %s" % g(kw, "sale.order", "state"))

    print("\n=== 2. Herkunft der Lagerbelege (Stichprobe) ===")
    p = kw("stock.picking", "search_read", [[], ["id", "name", "origin", "state", "picking_type_id", "scheduled_date"]], limit=10)
    for x in (p if isinstance(p, list) else []):
        print("   %-12s origin=%-14s state=%-10s typ=%-22s %s" % (x["name"], x.get("origin"), x["state"],
              (x["picking_type_id"][1] if x.get("picking_type_id") else "-")[:22], x.get("scheduled_date")))
    print("   Zustaende der stock.move nach picking_type:")
    m = kw("stock.move", "search_read", [[], ["id", "state", "origin", "picking_type_id", "location_id", "location_dest_id"]], limit=8)
    for x in (m if isinstance(m, list) else []):
        print("   move %-6s state=%-10s origin=%-14s typ=%-20s %s -> %s" % (x["id"], x["state"], x.get("origin"),
              (x["picking_type_id"][1] if x.get("picking_type_id") else "-")[:20],
              (x["location_id"][1] if x.get("location_id") else "-")[:18],
              (x["location_dest_id"][1] if x.get("location_dest_id") else "-")[:18]))

    print("\n=== 3. Produktart (type) - echte Auswahlwerte und Verteilung ===")
    for model in ("product.template", "product.product"):
        f = kw(model, "fields_get", [["type"], ["string", "type", "selection", "store"]], context=sprache)
        print("   %s.type = %s" % (model, json.dumps(f.get("type", {}), ensure_ascii=False)[:300]))
    print("   Verteilung product.template.type: %s" % g(kw, "product.template", "type"))
    print("   Verteilung product.product.type : %s" % g(kw, "product.product", "type"))
    print("   Verteilung product.template.product_type_id (Status): %s" % g(kw, "product.template", "product_type_id"))
    print("   Verteilung product.template.categ_id: %s" % g(kw, "product.template", "categ_id"))
    print("   Verteilung product.template.uom_id: %s" % g(kw, "product.template", "uom_id"))
    print("   is_multi_factor_product True/False: %s" % g(kw, "product.template", "is_multi_factor_product"))
    print("   recurring_invoice: %s" % g(kw, "product.template", "recurring_invoice"))

    print("\n=== 4. Lagerbezogene Einstellungen an Produkten ===")
    for feld in ("route_ids", "tracking", "property_stock_inventory", "property_stock_production", "sale_delay"):
        n = kw("product.template", "search_count", [[(feld, "!=", False)]])
        print("   product.template mit %-26s != leer: %s" % (feld, n))

    print("\n=== 5. Originalarch: Odoo-11-Liste des Menuepunkts 'Abonnement Produkte' (Aktion 514) ===")
    akt = kw("ir.actions.act_window", "read", [[514], ["id", "name", "res_model", "view_mode", "domain", "context", "search_view_id"]])
    print("   Aktion: %s" % json.dumps(akt[0] if isinstance(akt, list) else akt, ensure_ascii=False)[:600])
    fvg = kw("product.template", "fields_view_get", [False, "tree", "list"], context=sprache)
    if isinstance(fvg, dict) and fvg.get("arch"):
        print("   TREES-ARCH:\n%s" % fvg["arch"])
    else:
        print("   %s" % str(fvg)[:200])
    fvf = kw("product.template", "fields_view_get", [False, "form", "form"], context=sprache)
    if isinstance(fvf, dict) and fvf.get("arch"):
        print("\n   FORM-ARCH (nur Lager-/Faktor-relevante Zeilen):")
        for zeile in fvf["arch"].splitlines():
            if any(w in zeile for w in ("qty_available", "virtual_available", "is_multi_factor", "to_multiply", "type",
                                        "product_type_id", "categ_id", "uom_id", "list_price", "standard_price",
                                        "default_code", "name=", "recurring_invoice")):
                print("      %s" % zeile.strip()[:160])

    print("\n=== 6. Originalarch: Suchansicht Odoo 11 (product.template.search) ===")
    fvs = kw("product.template", "fields_view_get", [False, "search", "search"], context=sprache)
    if isinstance(fvs, dict) and fvs.get("arch"):
        print(fvs["arch"])
    else:
        print("   %s" % str(fvs)[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
