"""Prueft die Umsetzung des Unterbereichs Abonnement Produkte (Session 118, Teil 14).

Prueft read-only:
  - Modulstatus und Version
  - Produktliste: Spalten und Beschriftungen (Interne Kategorie, Bestandsmenge, geplante Bestandsmenge)
  - Suchansicht: Filter und Gruppierungen
  - Beschriftungen der Spaltenfelder (Status, Mit Faktor multiplizieren, Interne Kategorie)

Aufruf: python scripts/verify_abo_produkte.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ERWARTET_SPALTEN = ["default_code", "name", "is_multi_factor_product", "list_price", "standard_price",
                    "product_type_id", "categ_id", "qty_available", "virtual_available", "uom_id",
                    "product_tag_ids", "type"]
ERWARTET_FILTER = ["filter_recurring", "filter_multi_factor"]
ERWARTET_GRUPPEN = ["categ_id", "product_type_id", "type", "is_multi_factor_product"]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    env = {}
    for z in open(os.path.join(REPO, ".env"), encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            env[k.strip()] = v.strip()
    url = "http://localhost:8069" if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rpc(pfad, prm):
        r = urllib.request.Request(url + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": prm}).encode(),
                                   headers={"Content-Type": "application/json"})
        with op.open(r, timeout=300) as f:
            return json.loads(f.read().decode())

    rpc("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]})

    def kw(m, me, args, **K):
        o = rpc("/web/dataset/call_kw", {"model": m, "method": me, "args": args, "kwargs": K})
        if "error" in o:
            raise RuntimeError(str(o["error"].get("data", {}).get("message"))[:200])
        return o["result"]

    print("Instanz: %s (%s)" % (a.instanz, url))
    ok = fehler = 0

    def pruefe(bed, txt):
        nonlocal ok, fehler
        if bed:
            ok += 1
            print("  OK   %s" % txt)
        else:
            fehler += 1
            print("  FEHL %s" % txt)

    modul = kw("ir.module.module", "search_read", [[["name", "=", "itk_subscription"]], ["state", "latest_version"]])[0]
    print("\nModul: %s %s" % (modul["state"], modul["latest_version"]))
    pruefe(modul["state"] == "installed", "Modul installiert (kein Fehlerzustand)")

    print("\n--- Produktliste ---")
    arch = kw("product.template", "get_views", [[[False, "list"]]], context={"lang": "de_DE"})["views"]["list"]["arch"]
    spalten = re.findall(r"<field name=\"([^\"]+)\"", arch)
    print("   Spalten: %s" % spalten)
    for feld in ERWARTET_SPALTEN:
        pruefe(feld in spalten, "Spalte vorhanden: %s" % feld)
    beschriftungen = dict(re.findall(r"<field name=\"([^\"]+)\"[^>]*string=\"([^\"]*)\"", arch))
    print("   Beschriftungen: %s" % beschriftungen)
    pruefe(beschriftungen.get("categ_id") == "Interne Kategorie", "categ_id heisst 'Interne Kategorie'")
    pruefe(beschriftungen.get("qty_available") == "Bestandsmenge", "qty_available heisst 'Bestandsmenge'")
    pruefe(beschriftungen.get("virtual_available") == "Geplante Bestandsmenge",
           "virtual_available heisst 'Geplante Bestandsmenge'")
    pruefe("optional=\"show\"" in arch or "optional='show'" in arch, "Spalten sind sichtbar geschaltet (optional show)")

    print("\n--- Suchansicht ---")
    suche = kw("product.template", "get_views", [[[False, "search"]]], context={"lang": "de_DE"})["views"]["search"]["arch"]
    filter_namen = re.findall(r"<filter[^>]*name=\"([^\"]+)\"", suche)
    gruppen = re.findall(r"group_by': '(\w+)'", suche)
    print("   Filter: %s" % filter_namen)
    print("   Gruppierungen: %s" % gruppen)
    for f in ERWARTET_FILTER:
        pruefe(f in filter_namen, "Filter vorhanden: %s" % f)
    for g in ERWARTET_GRUPPEN:
        pruefe(g in gruppen, "Gruppierung vorhanden: %s" % g)
    pruefe("filter_products" in filter_namen or "categ_id" in filter_namen, "bestehende Odoo-18-Filter erhalten")

    print("\n--- Feldbeschriftungen ---")
    felder = kw("product.template", "fields_get", [["is_multi_factor_product", "to_multiply_by_factor", "product_type_id"],
                                                   ["string", "type"]], context={"lang": "de_DE"})
    for f, d in felder.items():
        print("   %-26s %-40s %s" % (f, d.get("string"), d.get("type")))
    pruefe("Mit Faktor" in felder.get("is_multi_factor_product", {}).get("string", ""),
           "is_multi_factor_product traegt die Faktor-Beschriftung")

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
