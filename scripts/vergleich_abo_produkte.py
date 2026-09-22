"""Bestandsaufnahme Abonnement Produkte: Odoo 11 gegen Odoo 18 (Session 118, Teil 14).

Liest je Instanz die Aktion, Listenansicht, Suchansicht und Formularansicht des Menuepunkts
"Abonnement Produkte" sowie die Felddefinitionen der verwendeten Spalten und die tatsaechliche
Nutzung der Produktdaten.

Aufruf: python scripts/vergleich_abo_produkte.py --instanz o11|vm|lokal
"""
from __future__ import annotations

import argparse
import collections
import http.cookiejar
import json
import os
import re
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


def client(instanz):
    env = lade_env(os.path.join(REPO, ".env"))
    if instanz == "o11":
        url, db = "https://portal.it-kommunal.at", "ITK_V1_a"
        user, pwd = "anna.maierhofer@it-kommunal.at", env["ODOO11_PWD"]
    elif instanz == "vm":
        url, db = "https://k001959vsx.ipax.at", env["ODOO18_DB"]
        user, pwd = env["ODOO18_USER"], env["ODOO18_PWD"]
    else:
        url, db = "http://localhost:8069", env["ODOO18_DB"]
        user, pwd = env["ODOO18_USER"], env["ODOO18_PWD"]
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rufe(pfad, params):
        r = urllib.request.Request(url + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode(),
                                   headers={"Content-Type": "application/json"})
        with op.open(r, timeout=600) as f:
            return json.loads(f.read().decode())

    rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})

    def kw(model, methode, args, **kwargs):
        o = rufe("/web/dataset/call_kw", {"model": model, "method": methode, "args": args, "kwargs": kwargs})
        if "error" in o:
            return {"__fehler__": str(o["error"].get("data", {}).get("message", o["error"].get("message")))[:120]}
        return o.get("result")

    return kw


def ansicht(kw, modell, art, sprache):
    """Ansichtsarch je Odoo-Version lesen (Odoo 11: fields_view_get, Odoo 18: get_views)."""
    if art == "search":
        ergebnis = kw(modell, "fields_view_get", [False, "search"], context=sprache)
    else:
        ergebnis = kw(modell, "fields_view_get", [False, art], context=sprache)
    if isinstance(ergebnis, dict) and ergebnis.get("arch"):
        return ergebnis["arch"]
    ergebnis = kw(modell, "get_views", [[[False, art]]], context=sprache)
    if isinstance(ergebnis, dict) and "views" in ergebnis:
        for _n, v in ergebnis["views"].items():
            if v.get("arch"):
                return v["arch"]
    return ""

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["o11", "vm", "lokal"], default="o11")
    a = p.parse_args()
    kw = client(a.instanz)
    print("=== Instanz: %s ===" % a.instanz)
    sprache = {"lang": "de_DE"}

    print("\n--- Aktion/Menue 'Abonnement Produkte' ---")
    for akt in kw("ir.actions.act_window", "search_read",
                  [[["res_model", "=", "product.template"]], ["id", "name", "domain", "context", "view_mode", "res_id"]],
                  context=sprache, limit=6):
        print("   %s | %s | domain=%s | context=%s | views=%s" % (akt["id"], akt["name"], str(akt["domain"])[:60],
                                                                 str(akt["context"])[:60], akt["view_mode"]))

    print("\n--- Listenansicht: Spalten (Feldnamen in Reihenfolge) ---")
    for art in ("tree", "form"):
        inhalt = ansicht(kw, "product.template", art, sprache)
        print("   (%s) Felder: %s" % (art, re.findall(r'<field name="([^"]+)"', inhalt)[:60]))

    print("\n--- Suchansicht: Filter und Gruppierungen ---")
    inhalt = ansicht(kw, "product.template", "search", sprache)
    print("   FILTER :" + str(re.findall(r'<filter[^>]*?name="([^"]+)"[^>]*?string="([^"]*)"', inhalt)))
    print("   FILTER2:" + str(re.findall(r'<filter[^>]*?string="([^"]*)"[^>]*?name="([^"]+)"', inhalt)))
    print("   GROUPBY:" + str(re.findall(r'group_by[\'"]+(\w+)', inhalt)))
    print("   FELDER :" + str(re.findall(r'<field name="([^"]+)"', inhalt)))

    if a.instanz == "o11":
        print("\n--- Produktbestand Odoo 11 ---")
        print("   product.template gesamt: %s | aktiv: %s" % (
            kw("product.template", "search_count", [[]]), kw("product.template", "search_count", [[["active", "=", True]]])))
        print("   product.product: %s" % kw("product.product", "search_count", [[]]))
        print("   Varianten (template mit >1 Variante): %s" % kw("product.template", "search_count",
              [[["product_variant_count", ">", 1]]]))
        zeilen = kw("sale.subscription.line", "search_read", [[], ["product_id", "analytic_account_id"]])
        produkte = collections.Counter(z["product_id"][0] for z in zeilen if z["product_id"])
        print("   in Abos verwendete Produkte (verschiedene): %s" % len(produkte))
        infos = kw("product.product", "read", [[p for p, _ in produkte.most_common(12)],
                                              ["id", "default_code", "name", "categ_id", "uom_id", "type",
                                               "list_price", "standard_price", "qty_available", "virtual_available",
                                               "qty_multiplication_factor", "active", "taxes_id", "variant_count"]])
        for i in sorted(infos, key=lambda x: -produkte[x["id"]]):
            print("      %-5s %-14s %-38s Abos=%-4s Kat=%-22s ME=%-8s Preis=%-8s Kosten=%-8s Faktor=%-5s Lager=%-8s Geplant=%-8s aktiv=%s"
                  % (i["id"], i["default_code"] or "-", (i["name"] or "")[:38], produkte[i["id"]],
                     (i["categ_id"][1] if i["categ_id"] else "-")[:22], (i["uom_id"][1] if i["uom_id"] else "-")[:8],
                     i.get("list_price"), i.get("standard_price"), i.get("qty_multiplication_factor"), i.get("qty_available"),
                     i.get("virtual_available"), i["active"]))
        print("\n--- Felddefinitionen der Odoo-11-Spalten ---")
        felder = ["default_code", "name", "qty_multiplication_factor", "list_price", "standard_price", "state",
                  "categ_id", "qty_available", "virtual_available"]
        for f, d in kw("product.product", "fields_get", [felder, ["string", "type", "relation", "required", "readonly", "store", "compute"]], context=sprache).items():
            print("   %-26s %-22s %-12s rel=%-18s store=%-5s req=%s ro=%s" % (f, d.get("string"), d.get("type"),
                  str(d.get("relation")), d.get("store"), d.get("required"), d.get("readonly")))
        print("\n   Kategorien in Verwendung: %s" % kw("product.category", "search_read", [[], ["id", "name"]], limit=10))
        print("   Einheiten in Verwendung: %s" % kw("uom.uom", "search_read", [[], ["id", "name"]], limit=8))
    else:
        print("\n--- Felddefinitionen der Odoo-18-Spalten ---")
        felder = ["default_code", "name", "qty_multiplication_factor", "list_price", "standard_price", "state",
                  "categ_id", "qty_available", "virtual_available", "type", "uom_id", "product_variant_count"]
        ergebnis = kw("product.product", "fields_get", [felder, ["string", "type", "relation", "required", "readonly", "store", "compute"]], context=sprache)
        if isinstance(ergebnis, dict) and "__fehler__" not in ergebnis:
            for f, d in ergebnis.items():
                print("   %-26s %-24s %-12s rel=%-18s store=%-5s req=%s ro=%s" % (f, d.get("string"), d.get("type"),
                      str(d.get("relation")), d.get("store"), d.get("required"), d.get("readonly")))
        else:
            print("   %s" % ergebnis)
    return 0


if __name__ == "__main__":
    sys.exit(main())
