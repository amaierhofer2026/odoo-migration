"""Prueft die Umsetzung des Unterbereichs Abonnement Produkte (Session 118/119, Teil 14).

Prueft read-only:
  - Modulstatus und Versionen (itk_subscription, itk_product, itk_multifactor)
  - Produktliste: Spalten und Beschriftungen (Interne Kategorie, Status, Einheit)
  - Produktliste: Bestandsmenge/Geplante Bestandsmenge bewusst NICHT vorhanden
    (in Odoo 11 nie benutzt - siehe docs/o11-o18-vergleich-abo-teil14.md)
  - Suchansicht: Filter und Gruppierungen
  - Produktformular: to_multiply_by_factor entfernt, is_multi_factor_product vorhanden

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

# Odoo-11-Liste des Menuepunkts "Abonnement Produkte" (Aktion 514):
#   sequence, default_code, name, is_multi_factor_product, list_price, standard_price,
#   product_type_id (Status), categ_id, [type], qty_available, virtual_available, uom_id, active
ERWARTET_SPALTEN = ["default_code", "name", "is_multi_factor_product", "list_price", "standard_price",
                    "product_type_id", "categ_id", "uom_id", "product_tag_ids", "type"]
OHNE_STOCK = ["qty_available", "virtual_available"]
ERWARTET_FILTER = ["filter_recurring", "filter_multi_factor", "filter_abo_aktiv"]
ERWARTET_GRUPPEN = ["categ_id", "product_type_id", "type", "is_multi_factor_product"]
ERWARTETE_MODULE = {"itk_subscription": None, "itk_product": None, "itk_multifactor": None}


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

    print("\n--- Module ---")
    for name in ERWARTETE_MODULE:
        treffer = kw("ir.module.module", "search_read",
                     [[["name", "=", name]], ["name", "state", "installed_version", "latest_version"]])
        if treffer:
            m = treffer[0]
            print("   %-18s %-10s installiert=%s latest=%s" % (name, m["state"], m["installed_version"], m["latest_version"]))
            pruefe(m["state"] == "installed", "%s installiert (kein Fehlerzustand)" % name)
        else:
            pruefe(False, "%s gefunden" % name)

    print("\n--- Produktliste ---")
    arch = kw("product.template", "get_views", [[[False, "list"]]], context={"lang": "de_DE"})["views"]["list"]["arch"]
    spalten = re.findall(r"<field name=\"([^\"]+)\"", arch)
    print("   Spalten: %s" % spalten)
    for feld in ERWARTET_SPALTEN:
        pruefe(feld in spalten, "Spalte vorhanden: %s" % feld)
    for feld in OHNE_STOCK:
        pruefe(feld not in spalten, "Spalte bewusst nicht vorhanden (kein Lager): %s" % feld)
    pruefe(len(spalten) == len(set(spalten)), "keine Spalte doppelt")
    beschriftungen = dict(re.findall(r"<field name=\"([^\"]+)\"[^>]*string=\"([^\"]*)\"", arch))
    print("   Beschriftungen: %s" % beschriftungen)
    pruefe(beschriftungen.get("categ_id") == "Interne Kategorie", "categ_id heisst 'Interne Kategorie'")
    pruefe(beschriftungen.get("product_type_id") == "Status", "product_type_id heisst 'Status'")
    pruefe(beschriftungen.get("uom_id") == "Einheit", "uom_id heisst 'Einheit'")
    for feld in ("is_multi_factor_product", "categ_id"):
        pruefe(bool(re.search(r"<field name=\"%s\"[^>]*optional=\"show\"" % feld, arch)),
               "Spalte in der Spaltenauswahl sichtbar (optional show): %s" % feld)

    print("\n--- Suchansicht ---")
    suche = kw("product.template", "get_views", [[[False, "search"]]], context={"lang": "de_DE"})["views"]["search"]["arch"]
    filter_namen = re.findall(r"<filter[^>]*name=\"([^\"]+)\"", suche)
    gruppen = re.findall(r"group_by'\s*:\s*'(\w+)'", suche)
    print("   Filter: %s" % filter_namen)
    print("   Gruppierungen: %s" % gruppen)
    for f in ERWARTET_FILTER:
        pruefe(f in filter_namen, "Filter vorhanden: %s" % f)
    for g in ERWARTET_GRUPPEN:
        pruefe(g in gruppen, "Gruppierung vorhanden: %s" % g)
    pruefe("filter_products" in filter_namen or "categ_id" in filter_namen, "bestehende Odoo-18-Filter erhalten")
    pruefe(not any(f.startswith("filter_c") for f in filter_namen), "keine nachgebauten Odoo-11-Service-Type-Filter")

    print("\n--- Produktformular ---")
    form = kw("product.template", "get_views", [[[False, "form"]]], context={"lang": "de_DE"})["views"]["form"]["arch"]
    pruefe("to_multiply_by_factor" not in form, "to_multiply_by_factor ist aus dem Formular entfernt")
    pruefe("is_multi_factor_product" in form, "is_multi_factor_product ist im Formular vorhanden")
    pruefe("product_type_id" in form, "product_type_id (Status) ist im Formular vorhanden")

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
