# -*- coding: utf-8 -*-
"""Preislisten: Migrationsskript Odoo 11 -> Odoo 18.

Teil des ITK-Migrationsprojekts, erstellt unter Freigabe von Anna Maierhofer (11.11.2026).
Quelle: Odoo 11 Prod `ITK_V1_a` - ausschliesslich lesend. Ziel: Odoo 18.

Umfang:
- product.pricelist: 50 Preislisten
- product.pricelist.item: 1.876 Regeln (1.473 Produktvorlage, 268 Variante,
  107 Kategorie, 28 global; compute_price: 473 fixed, 1.397 formula, 6 percentage)

Nicht uebernommen, weil Odoo 18 die Felder nicht mehr fuehrt:
- `code` (0 belegt), `selectable` (0 belegt), `discount_policy` (in Odoo 18 am Auftrag),
  `website_id` (website_sale wird nicht migriert).

Idempotenz: `itk_o11_id` auf Preisliste und Regel (Modul itk_migration_keys).

Aufruf (Trockenlauf ist Standard und schreibt nichts):
    python scripts/migration/preislisten_migration.py --instanz lokal
    python scripts/migration/preislisten_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

BATCH = 100


class Schreibschutz:
    SCHREIBEND = {"create", "write", "unlink", "copy"}

    def __init__(self, client_, schreiben: bool):
        self._client = client_
        self._schreiben = schreiben

    def kw(self, modell, methode, args, **kwargs):
        if not self._schreiben and methode in SCHREIBEND_NAMEN:
            raise RuntimeError("Schreibaufruf im Trockenlauf: %s.%s" % (modell, methode))
        return self._client.kw(modell, methode, args, **kwargs)


SCHREIBEND_NAMEN = {"create", "write", "unlink", "copy"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    ap.add_argument("--grenze", type=int, default=0)
    ap.add_argument("--mapping")
    args = ap.parse_args()

    if args.ausfuehren and not args.ich_habe_freigabe:
        print("ABBRUCH: Schreiblauf nur mit --ich-habe-freigabe (Freigabe von Anna).")
        return 2

    o11 = client.o11()
    ziel = Schreibschutz(client.o18(args.instanz), args.ausfuehren)
    print("=== Preislisten-Migration %s | %s ===" % (
        args.instanz, "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF (schreibt nichts)"))

    listen = o11.kw("product.pricelist", "search_read", [[]],
                    fields=["id", "name", "currency_id", "active"], order="id", limit=500)
    if args.grenze:
        listen = listen[:args.grenze]
    items = o11.kw("product.pricelist.item", "search_read", [[]],
                   fields=["id", "pricelist_id", "applied_on", "product_tmpl_id", "product_id",
                           "categ_id", "min_quantity", "compute_price", "fixed_price",
                           "percent_price", "base", "price_discount", "price_round",
                           "price_surcharge", "date_start", "date_end",
                           "base_pricelist_id"],
                   order="id", limit=5000)

    stat = {"gelesen": len(listen), "neu": 0, "da": 0, "items": len(items),
            "item_neu": 0, "item_da": 0, "item_ohne_liste": 0, "item_ohne_bezug": 0,
            "item_ohne_waehrung": 0, "uebersprungen": 0, "fehler": 0}
    mapping = {"preislisten": [], "regeln": []}

    # Bestand
    pl_bestand = {r["itk_o11_id"]: r["id"] for r in
                  ziel.kw("product.pricelist", "search_read",
                          [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=500,
                          context={"active_test": False})}
    item_bestand = {r["itk_o11_id"]: r["id"] for r in
                    ziel.kw("product.pricelist.item", "search_read",
                            [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=5000,
                            context={"active_test": False})}
    tmpl_map = {r["itk_o11_id"]: r["id"] for r in
                ziel.kw("product.template", "search_read",
                        [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=5000,
                        context={"active_test": False})}
    var_map = {r["itk_o11_id"]: r["id"] for r in
               ziel.kw("product.product", "search_read",
                       [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=5000,
                       context={"active_test": False})}
    kat_map = {r["itk_o11_id"]: r["id"] for r in
               ziel.kw("product.category", "search_read",
                       [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=500,
                       context={"active_test": False})}
    waehrungen = {w["name"]: w["id"] for w in
                  ziel.kw("res.currency", "search_read", [[], ["id", "name"]], limit=200)}
    whg_std = waehrungen.get("EUR") or next(iter(waehrungen.values()))

    # 1) Preislisten
    for pl in listen:
        if pl["id"] in pl_bestand:
            stat["da"] += 1
            mapping["preislisten"].append({"o11_id": pl["id"], "o18_id": pl_bestand[pl["id"]]})
            continue
        vals = {"name": pl["name"], "itk_o11_id": pl["id"], "active": pl["active"],
                "currency_id": waehrungen.get((pl["currency_id"] or [0, "EUR"])[1], whg_std)}
        try:
            if args.ausfuehren:
                pid = ziel.kw("product.pricelist", "create", [vals])
                pid = pid[0] if isinstance(pid, list) else pid
            else:
                pid = -pl["id"]
            pl_bestand[pl["id"]] = pid
            stat["neu"] += 1
            mapping["preislisten"].append({"o11_id": pl["id"], "o18_id": pid})
        except Exception as e:
            stat["fehler"] += 1
            print("  FEHLER Preisliste o11_id %s: %s" % (pl["id"], str(e)[-200:]))

    # 2) Regeln
    neu = [i for i in items if i["id"] not in item_bestand]
    stat["item_da"] = len(items) - len(neu)
    for j in range(0, len(neu), BATCH):
        block = neu[j:j + BATCH]
        vals_list = []
        for it in block:
            liste = it["pricelist_id"] and it["pricelist_id"][0]
            if not liste or liste not in pl_bestand:
                stat["item_ohne_liste"] += 1
                continue
            vals = {"pricelist_id": pl_bestand[liste], "itk_o11_id": it["id"],
                    "applied_on": it["applied_on"] or "3_global",
                    "min_quantity": it["min_quantity"] or 0,
                    "compute_price": it["compute_price"] or "fixed",
                    "base": it["base"] or "list_price"}
            if it["compute_price"] == "fixed":
                vals["fixed_price"] = it["fixed_price"] or 0.0
            elif it["compute_price"] == "percentage":
                vals["percent_price"] = it["percent_price"] or 0.0
            else:
                vals["price_discount"] = it["price_discount"] if it["price_discount"] is not None else -1
                vals["price_round"] = it["price_round"] or 0.0
                vals["price_surcharge"] = it["price_surcharge"] or 0.0
            if it["base"] == "pricelist" and it["base_pricelist_id"]:
                basis = it["base_pricelist_id"][0]
                if basis in pl_bestand:
                    vals["base_pricelist_id"] = pl_bestand[basis]
                else:
                    stat["item_ohne_bezug"] += 1
                    continue
            if it["date_start"]:
                vals["date_start"] = it["date_start"]
            if it["date_end"]:
                vals["date_end"] = it["date_end"]
            bezug = False
            if it["product_tmpl_id"] and it["product_tmpl_id"][0] in tmpl_map:
                vals["applied_on"] = "1_product"
                vals["product_tmpl_id"] = tmpl_map[it["product_tmpl_id"][0]]
                bezug = True
            elif it["product_id"] and it["product_id"][0] in var_map:
                vals["applied_on"] = "0_product_variant"
                vals["product_id"] = var_map[it["product_id"][0]]
                bezug = True
            elif it["categ_id"] and it["categ_id"][0] in kat_map:
                vals["applied_on"] = "2_product_category"
                vals["categ_id"] = kat_map[it["categ_id"][0]]
                bezug = True
            elif it["applied_on"] == "3_global":
                bezug = True
            if not bezug:
                stat["item_ohne_bezug"] += 1
                continue
            vals_list.append(vals)
        try:
            if args.ausfuehren and vals_list:
                ids = ziel.kw("product.pricelist.item", "create", [vals_list])
                if not isinstance(ids, list):
                    ids = [ids]
            else:
                ids = [-v["itk_o11_id"] for v in vals_list]
            for v, nid in zip(vals_list, ids):
                item_bestand[v["itk_o11_id"]] = nid
                stat["item_neu"] += 1
                mapping["regeln"].append({"o11_id": v["itk_o11_id"], "o18_id": nid})
        except Exception as e:
            stat["fehler"] += 1
            print("  FEHLER Regel-Block ab o11_id %s: %s"
                  % (block[0]["id"], str(e)[-300:]))

    breite = "{:<36}{:>10}"
    print(breite.format("Objekt", "Anzahl"))
    print("-" * 46)
    for k, v in (("Preislisten gelesen", stat["gelesen"]),
                 ("davon neu angelegt", stat["neu"]),
                 ("davon bereits vorhanden", stat["da"]),
                 ("Regeln gelesen", stat["items"]),
                 ("davon neu angelegt", stat["item_neu"]),
                 ("davon bereits vorhanden", stat["item_da"]),
                 ("Regel ohne Preisliste", stat["item_ohne_liste"]),
                 ("Regel ohne Produktbezug", stat["item_ohne_bezug"]),
                 ("uebersprungen (unveraendert)", stat["uebersprungen"]),
                 ("nicht zuordenbar", stat["item_ohne_liste"] + stat["item_ohne_bezug"]),
                 ("Fehler", stat["fehler"])):
        print(breite.format(k, v))
    if not args.ausfuehren:
        print("Hinweis: 'neu angelegt' = Anzahl der Datensaetze, die geschrieben WUERDEN.")
    if args.mapping:
        with open(args.mapping, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(mapping, fh, ensure_ascii=False)
        print("Mapping geschrieben (nur IDs):", args.mapping)
    print("Modus:", "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
