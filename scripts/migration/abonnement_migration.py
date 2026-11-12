# -*- coding: utf-8 -*-
"""Abonnements: Migrationsskript Odoo 11 -> Odoo 18 (vollstaendiger Beleglauf).

Teil des ITK-Migrationsprojekts, erstellt unter Freigabe von Anna Maierhofer (11.11.2026).
Quelle: Odoo 11 Prod `ITK_V1_a` - ausschliesslich lesend. Ziel: Odoo 18.

Umfang: 1.788 Abonnements (`sale.subscription`). In Odoo 11 haengen die Abozeilen am
analytischen Konto; die Produkt-/Mengenangaben werden daher aus den Abo-Zeilen
(`sale.subscription.line`) ueber das analytische Konto des Abos gelesen.

Voraussetzungen: kontakte_migration.py, produkte_migration.py, preislisten_migration.py,
Abostammdaten (`apply_abo_stammdaten.py`) und Modul `itk_migration_keys`.

Idempotenz: `itk_o11_id` auf `sale.subscription`.

Datenschutz: Nur IDs, Nummern, Betraege und Zaehlwerte in Konsole, Mapping und Doku.

Aufruf:
    python scripts/migration/abonnement_migration.py --instanz lokal
    python scripts/migration/abonnement_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

BATCH = 25


class Schreibschutz:
    SCHREIBEND = {"create", "write", "unlink", "copy"}

    def __init__(self, client_, schreiben: bool):
        self._client = client_
        self._schreiben = schreiben

    def kw(self, modell, methode, args, **kwargs):
        if not self._schreiben and methode in self.SCHREIBEND:
            raise RuntimeError("Schreibaufruf im Trockenlauf: %s.%s" % (modell, methode))
        return self._client.kw(modell, methode, args, **kwargs)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    ap.add_argument("--grenze", type=int, default=0)
    ap.add_argument("--mapping")
    ap.add_argument("--testdaten-bereinigen", action="store_true",
                    help="Odoo-18-Testabos ohne itk_o11_id entfernen")
    args = ap.parse_args()

    if args.ausfuehren and not args.ich_habe_freigabe:
        print("ABBRUCH: Schreiblauf nur mit --ich-habe-freigabe (Freigabe von Anna).")
        return 2

    o11 = client.o11()
    ziel = Schreibschutz(client.o18(args.instanz), args.ausfuehren)
    print("=== Abonnement-Migration %s | %s ===" % (
        args.instanz, "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF (schreibt nichts)"))

    felder = ["id", "name", "code", "state", "partner_id", "pricelist_id", "template_id",
              "date_start", "recurring_total", "recurring_invoice_line_ids", "user_id"]
    abos = o11.kw("sale.subscription", "search_read", [[]], fields=felder, order="id",
                  limit=6000, context={"active_test": False})
    if args.grenze:
        abos = abos[:args.grenze]

    stat = {"gelesen": len(abos), "neu": 0, "da": 0, "ohne_partner": 0,
            "ohne_vorlage": 0, "zeilen_neu": 0, "zeilen_ohne_produkt": 0,
            "fehler": 0, "testdaten": 0}
    mapping = []

    part_map = {r["itk_o11_id"]: r["id"] for r in
                ziel.kw("res.partner", "search_read",
                        [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=20000,
                        context={"active_test": False})}
    pl_map = {r["itk_o11_id"]: r["id"] for r in
              ziel.kw("product.pricelist", "search_read",
                      [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=500,
                      context={"active_test": False})}
    vorlagen = {r["name"]: r["id"] for r in
                ziel.kw("sale.subscription.template", "search_read",
                        [[], ["id", "name"]], limit=200,
                        context={"active_test": False})}
    var_map = {r["itk_o11_id"]: r["id"] for r in
               ziel.kw("product.product", "search_read",
                       [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=5000,
                       context={"active_test": False})}
    bestand = {r["itk_o11_id"]: r["id"] for r in
               ziel.kw("sale.subscription", "search_read",
                       [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=6000,
                       context={"active_test": False})}

    # Abozeilen: in Odoo 11 haengen sie ueber recurring_invoice_line_ids am Abo
    # (das analytische Konto ist bei den Abos selbst nicht gesetzt).
    zeilen11 = o11.kw("sale.subscription.line", "search_read", [[]],
                      fields=["id", "analytic_account_id", "product_id", "name", "quantity",
                              "price_unit", "uom_id"], order="id", limit=20000,
                      context={"active_test": False})
    zeilen_je_id = {z["id"]: z for z in zeilen11}
    # Vorlagen ueber die Odoo-11-ID aufloesen (display_name traegt ein Praefix)
    uom_map = {r["name"]: r["id"] for r in
               ziel.kw("uom.uom", "search_read", [[], ["id", "name"]], limit=500,
                       context={"active_test": False})}
    uom_std = uom_map.get("Units") or uom_map.get("Unit(s)") or next(iter(uom_map.values()))
    vorlagen11 = {t["id"]: t["name"] for t in
                  o11.kw("sale.subscription.template", "search_read", [[], ["id", "name"]],
                         limit=200, context={"active_test": False})}

    if args.testdaten_bereinigen:
        demo = ziel.kw("sale.subscription", "search_read",
                       [[["itk_o11_id", "=", 0]], ["id", "name"]], limit=500,
                       context={"active_test": False})
        for d in demo:
            if args.ausfuehren:
                try:
                    ziel.kw("sale.subscription", "unlink", [[d["id"]]])
                    stat["testdaten"] += 1
                except Exception as e:
                    stat["fehler"] += 1
                    print("  FEHLER Testabo %s: %s" % (d["id"], str(e)[-180:]))
            else:
                stat["testdaten"] += 1

    status_map = {"draft": "draft", "open": "open", "close": "close", "cancel": "cancel",
                  "pending": "draft", "to_renew": "open"}

    neu = [a for a in abos if a["id"] not in bestand]
    stat["da"] = len(abos) - len(neu)
    for i in range(0, len(neu), BATCH):
        for a in neu[i:i + BATCH]:
            pid = a["partner_id"] and a["partner_id"][0]
            if not pid or pid not in part_map:
                stat["ohne_partner"] += 1
                print("  NICHT ZUORDENBAR Abo o11_id %s: Kunde fehlt" % a["id"])
                continue
            vals = {"partner_id": part_map[pid], "itk_o11_id": a["id"],
                    "code": a["code"] or False,
                    "date_start": (a["date_start"] or False),
                    "state": status_map.get(a["state"], "draft")}
            if a["pricelist_id"] and a["pricelist_id"][0] in pl_map:
                vals["pricelist_id"] = pl_map[a["pricelist_id"][0]]
            if a["template_id"]:
                tname = vorlagen11.get(a["template_id"][0])
                if tname and tname in vorlagen:
                    vals["template_id"] = vorlagen[tname]
                else:
                    stat["ohne_vorlage"] += 1
            order_zeilen = []
            for zid in (a["recurring_invoice_line_ids"] or []):
                z = zeilen_je_id.get(zid)
                if not z:
                    continue
                prod = z["product_id"] and z["product_id"][0]
                if not prod or prod not in var_map:
                    stat["zeilen_ohne_produkt"] += 1
                    continue
                uom_name = (z.get("uom_id") or [0, ""])[1]
                order_zeilen.append((0, 0, {
                    "product_id": var_map[prod],
                    "name": z["name"] or "",
                    "quantity": z["quantity"] or 1.0,
                    "price_unit": z["price_unit"] or 0.0,
                    "uom_id": uom_map.get(uom_name, uom_std),
                }))
            vals["recurring_invoice_line_ids"] = order_zeilen
            if args.ausfuehren:
                try:
                    neu_id = ziel.kw("sale.subscription", "create", [vals])
                    neu_id = neu_id[0] if isinstance(neu_id, list) else neu_id
                    ziel.kw("sale.subscription", "write", [[neu_id], {"name": a["name"]}])
                    bestand[a["id"]] = neu_id
                    stat["neu"] += 1
                    stat["zeilen_neu"] += len(order_zeilen)
                    mapping.append({"o11_id": a["id"], "o11_name": a["name"],
                                    "o18_id": neu_id, "state": a["state"],
                                    "zeilen": len(order_zeilen)})
                except Exception as e:
                    stat["fehler"] += 1
                    print("  FEHLER Abo o11_id %s: %s" % (a["id"], str(e)[-260:]))
            else:
                stat["neu"] += 1
                stat["zeilen_neu"] += len(order_zeilen)
                mapping.append({"o11_id": a["id"], "o11_name": a["name"],
                                "o18_id": -a["id"], "state": a["state"],
                                "zeilen": len(order_zeilen)})

    breite = "{:<40}{:>10}"
    print(breite.format("Objekt", "Anzahl"))
    print("-" * 50)
    for k, v in (("Abos gelesen", stat["gelesen"]),
                 ("davon neu angelegt", stat["neu"]),
                 ("davon bereits vorhanden", stat["da"]),
                 ("Abozeilen neu angelegt", stat["zeilen_neu"]),
                 ("Abos ohne zuordenbaren Kunden", stat["ohne_partner"]),
                 ("Abos ohne Vorlagenzuordnung", stat["ohne_vorlage"]),
                 ("Zeilen ohne zuordenbares Produkt", stat["zeilen_ohne_produkt"]),
                 ("Testabos bereinigt", stat["testdaten"]),
                 ("nicht zuordenbar", stat["ohne_partner"]),
                 ("Fehler", stat["fehler"])):
        print(breite.format(k, v))
    if not args.ausfuehren:
        print("Hinweis: 'neu angelegt' = Anzahl, die geschrieben WUERDE.")
    if args.mapping:
        with open(args.mapping, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(mapping, fh, ensure_ascii=False)
        print("Mapping geschrieben (nur IDs und Nummern):", args.mapping)
    print("Modus:", "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
