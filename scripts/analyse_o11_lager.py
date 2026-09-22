"""Read-only-Analyse: wurde das Lager-Modul (stock) in Odoo 11 fachlich verwendet?

Session 119, Teil 14 (Abonnement Produkte). Beantwortet die Frage, ob die Odoo-11-Spalten
qty_available (Bestandsmenge) und virtual_available (Geplante Bestandsmenge) fachlich
relevant waren oder ob sie nur Standardspalten ohne Nutzung sind.

Es wird ausschliesslich gelesen (search_count / search_read / fields_get / read).
Keine Schreiboperation.

Aufruf: python scripts/analyse_o11_lager.py
"""
from __future__ import annotations

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
        r = urllib.request.Request(
            url + pfad,
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with op.open(r, timeout=600) as f:
            return json.loads(f.read().decode())

    rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})

    def kw(model, methode, args, **kwargs):
        o = rufe("/web/dataset/call_kw", {"model": model, "method": methode, "args": args, "kwargs": kwargs})
        if "error" in o:
            return {"__fehler__": str(o["error"].get("data", {}).get("message", o["error"].get("message")))[:150]}
        return o.get("result")

    return kw


def main() -> int:
    kw = client()
    sprache = {"lang": "de_DE"}
    print("=== Odoo 11 (read-only): Lager-Nutzung ===")

    print("\n--- 1. Ist das Modul stock ueberhaupt installiert? ---")
    for name in ("stock", "sale_stock", "purchase_stock", "stock_account", "delivery", "sale_subscription", "itk_multifactor"):
        r = kw("ir.module.module", "search_read", [[["name", "=", name]], ["name", "state", "latest_version"]])
        if isinstance(r, list) and r:
            print("   %-18s state=%-12s version=%s" % (name, r[0]["state"], r[0].get("latest_version")))
        else:
            print("   %-18s nicht vorhanden / keine Auskunft: %s" % (name, str(r)[:60]))

    print("\n--- 2. Lager-Grunddaten (existieren Lagerorte/Lagerhaeuser?) ---")
    for modell, dom in (
        ("stock.warehouse", []),
        ("stock.location", []),
        ("stock.location", [("usage", "=", "internal")]),
        ("stock.location", [("usage", "=", "supplier")]),
        ("stock.location", [("usage", "=", "customer")]),
        ("stock.location", [("usage", "=", "inventory")]),
        ("stock.picking.type", []),
        ("stock.route", []),
        ("stock.warehouse.orderpoint", []),
        ("stock.warehouse.orderpoint", [("product_id", "!=", False)]),
    ):
        print("   %-30s %-42s -> %s" % (modell, str(dom)[:42], kw(modell, "search_count", [dom])))

    print("\n--- 3. Echte Lagerbewegungen ---")
    for modell, dom in (
        ("stock.move", []),
        ("stock.move", [("state", "=", "done")]),
        ("stock.move.line", []),
        ("stock.move.line", [("state", "=", "done")]),
        ("stock.picking", []),
        ("stock.picking", [("state", "=", "done")]),
        ("stock.quant", []),
        ("stock.quant", [("quantity", "!=", 0)]),
        ("stock.quant", [("location_id.usage", "=", "internal")]),
    ):
        print("   %-30s %-42s -> %s" % (modell, str(dom)[:42], kw(modell, "search_count", [dom])))

    print("\n--- 4. Produkte mit Bestand / geplantem Bestand ungleich 0 ---")
    for dom in (
        [],
        [("qty_available", "!=", 0)],
        [("qty_available", ">", 0)],
        [("qty_available", "<", 0)],
        [("virtual_available", "!=", 0)],
        [("virtual_available", ">", 0)],
        [("incoming_qty", "!=", 0)],
        [("outgoing_qty", "!=", 0)],
        [("type", "=", "product")],
        [("type", "=", "consu")],
        [("type", "=", "service")],
    ):
        print("   product.template %-44s -> %s" % (str(dom)[:44], kw("product.template", "search_count", [dom])))

    print("\n   Verteilung Bestandsmenge (alle Templates, Stichprobe 4.000):")
    zeilen = kw("product.template", "search_read", [[], ["id", "default_code", "name", "type", "qty_available",
                                                       "virtual_available", "categ_id", "uom_id"]], limit=4000)
    if isinstance(zeilen, list):
        nz = [z for z in zeilen if (z.get("qty_available") or 0) != 0]
        vz = [z for z in zeilen if (z.get("virtual_available") or 0) != 0]
        print("      gelesen=%s | mit Bestand<>0=%s | mit geplantem Bestand<>0=%s" % (len(zeilen), len(nz), len(vz)))
        for z in nz[:15]:
            print("      id=%-5s code=%-12s typ=%-8s Bestand=%-10s geplant=%-10s %s"
                  % (z["id"], z.get("default_code") or "-", z.get("type"), z.get("qty_available"),
                     z.get("virtual_available"), (z.get("name") or "")[:40]))
        for z in vz[:15]:
            if (z.get("qty_available") or 0) == 0:
                print("      (geplant) id=%-5s code=%-12s typ=%-8s geplant=%-10s %s"
                      % (z["id"], z.get("default_code") or "-", z.get("type"), z.get("virtual_available"),
                         (z.get("name") or "")[:40]))

    print("\n--- 5. Werden Lagerorte/Lagerhaeuser produktiv genutzt? ---")
    print("   Lagerhaeuser: %s" % str(kw("stock.warehouse", "search_read", [[], ["id", "name", "code"]], limit=10))[:300])
    print("   Bewegungen je Lagerort (Ziel, Top):")
    bewegungen = kw("stock.move.line", "search_read", [[["state", "=", "done"]], ["location_id", "location_dest_id", "product_id"]], limit=200)
    if isinstance(bewegungen, list) and bewegungen:
        import collections
        zaehler = collections.Counter()
        for b in bewegungen:
            zaehler[b["location_dest_id"][1] if b["location_dest_id"] else "-"] += 1
        for ort, n in zaehler.most_common(10):
            print("      %-40s %s" % (ort[:40], n))
    else:
        print("      %s" % str(bewegungen)[:150])

    print("\n--- 6. Lieferungen/Auftraege: wurde aus Auftraegen geliefert? ---")
    for modell, dom in (
        ("sale.order", []),
        ("sale.order", [("state", "=", "done")]),
        ("sale.order.line", [("qty_delivered", "!=", 0)]),
        ("sale.order.line", [("qty_delivered", "=", 0)]),
        ("sale.subscription.line", []),
    ):
        print("   %-30s %-42s -> %s" % (modell, str(dom)[:42], kw(modell, "search_count", [dom])))

    print("\n--- 7. Felddefinitionen Lager-Bezug ---")
    felder = ["qty_available", "virtual_available", "incoming_qty", "outgoing_qty", "type",
              "property_stock_production", "property_stock_inventory", "route_ids", "tracking",
              "valuation", "cost_method", "standard_price"]
    erg = kw("product.template", "fields_get", [felder, ["string", "type", "store", "readonly", "compute", "depends"]], context=sprache)
    if isinstance(erg, dict) and "__fehler__" not in erg:
        for f in felder:
            d = erg.get(f, {})
            print("   %-28s %-26s %-10s store=%-5s ro=%-5s compute=%s" % (f, d.get("string"), d.get("type"),
                  d.get("store"), d.get("readonly"), d.get("compute")))
    else:
        print("   %s" % str(erg)[:200])

    print("\n--- 8. Lager-Menues in Odoo 11 (werden sie angezeigt?) ---")
    menues = kw("ir.ui.menu", "search_read", [[["name", "ilike", "Lager"]], ["id", "name", "complete_name", "action"]], limit=15)
    if isinstance(menues, list):
        for m in menues:
            print("   %-5s %-60s %s" % (m["id"], (m.get("complete_name") or "")[:60], m.get("action")))

    print("\n--- 9. Abo-Produkte: Produktart-Verteilung der 209 in Abos genutzten Produkte ---")
    zeilen = kw("sale.subscription.line", "search_read", [[], ["product_id"]])
    if isinstance(zeilen, list):
        pids = sorted({z["product_id"][0] for z in zeilen if z.get("product_id")})
        print("   verschiedene Produkte in Abo-Zeilen: %s" % len(pids))
        import collections
        typen = collections.Counter()
        bestand = 0
        for i in range(0, len(pids), 200):
            teil = kw("product.product", "read", [pids[i:i + 200], ["id", "type", "qty_available", "virtual_available"]])
            for p in teil:
                typen[p.get("type")] += 1
                if (p.get("qty_available") or 0) != 0:
                    bestand += 1
        print("   Produktarten: %s" % dict(typen))
        print("   davon mit Bestand <> 0: %s" % bestand)
    return 0


if __name__ == "__main__":
    sys.exit(main())
