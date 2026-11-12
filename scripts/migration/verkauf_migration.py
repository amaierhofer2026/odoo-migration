# -*- coding: utf-8 -*-
"""Verkauf: Migrationsskript Odoo 11 -> Odoo 18 (vollstaendiger Beleglauf).

Teil des ITK-Migrationsprojekts, erstellt unter Freigabe von Anna Maierhofer (11.11.2026).
Quelle: Odoo 11 Prod `ITK_V1_a` - ausschliesslich lesend. Ziel: Odoo 18.

Umfang: 2.514 Auftraege (`sale.order`) mit 4.076 Zeilen (`sale.order.line`).

Voraussetzungen: kontakte_migration.py, produkte_migration.py, preislisten_migration.py
und das Modul `itk_migration_keys` (Feld `itk_o11_id`).

Idempotenz: `itk_o11_id` auf `sale.order`. Auftragsnummern aus Odoo 11 bleiben erhalten.

Statusabbildung: draft -> draft, sent -> sent, sale -> sale, done -> sale (Odoo 18 kennt
kein "done"; der Fakturierungsstand steht an den Rechnungen), cancel -> cancel.

Datenschutz: Konsole, Mapping und Doku enthalten nur IDs, Nummern, Betraege, Zaehlwerte.

Aufruf (Trockenlauf ist Standard und schreibt nichts):
    python scripts/migration/verkauf_migration.py --instanz lokal
    python scripts/migration/verkauf_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe
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
SONDERFALL = ("eu", "rc", "intra", "reverse", "oss", "import", "export")


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
                    help="Odoo-18-Testauftraege ohne itk_o11_id samt Zeilen entfernen")
    args = ap.parse_args()

    if args.ausfuehren and not args.ich_habe_freigabe:
        print("ABBRUCH: Schreiblauf nur mit --ich-habe-freigabe (Freigabe von Anna).")
        return 2

    o11 = client.o11()
    ziel = Schreibschutz(client.o18(args.instanz), args.ausfuehren)
    print("=== Verkauf-Migration %s | %s ===" % (
        args.instanz, "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF (schreibt nichts)"))

    felder = ["id", "name", "state", "partner_id", "pricelist_id", "date_order",
              "client_order_ref", "note", "origin", "payment_term_id"]
    auftraege = o11.kw("sale.order", "search_read", [[]], fields=felder, order="id", limit=6000,
                       context={"active_test": False})
    if args.grenze:
        auftraege = auftraege[:args.grenze]
    zeilen = o11.kw("sale.order.line", "search_read", [[]],
                    fields=["id", "order_id", "product_id", "name", "product_uom_qty",
                            "price_unit", "discount", "price_subtotal", "taxes_id",
                            "product_uom", "sequence"],
                    order="id", limit=20000, context={"active_test": False})

    stat = {"gelesen": len(auftraege), "neu": 0, "da": 0, "zeilen": len(zeilen),
            "zeilen_neu": 0, "ohne_partner": 0, "ohne_produkt": 0,
            "fehler": 0, "testdaten": 0}
    mapping = []

    pl_map = {r["itk_o11_id"]: r["id"] for r in
              ziel.kw("product.pricelist", "search_read",
                      [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=500,
                      context={"active_test": False})}
    part_map = {r["itk_o11_id"]: r["id"] for r in
                ziel.kw("res.partner", "search_read",
                        [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=20000,
                        context={"active_test": False})}
    var_map = {r["itk_o11_id"]: r["id"] for r in
               ziel.kw("product.product", "search_read",
                       [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=5000,
                       context={"active_test": False})}
    # Zeilen-Einheit nur setzen, wenn sie zur Kategorie der Produkteinheit passt
    # (Odoo 18 verlangt gleiche Kategorie, Odoo 11 nicht).
    uom_rows = ziel.kw("uom.uom", "search_read",
                       [[], ["id", "name", "category_id"]], limit=500,
                       context={"active_test": False})
    uom_map = {r["name"]: r["id"] for r in uom_rows}
    uom_kat = {r["name"]: (r["category_id"] or [0])[0] for r in uom_rows}
    var_uom_kat = {}
    for v in ziel.kw("product.product", "search_read",
                     [[["itk_o11_id", "!=", False]], ["id", "uom_id"]], limit=5000,
                     context={"active_test": False}):
        var_uom_kat[v["id"]] = (v["uom_id"] or [0])[0]
    uom_kat_je_id = {r["id"]: (r["category_id"] or [0])[0] for r in uom_rows}
    bestand = {r["itk_o11_id"]: r["id"] for r in
               ziel.kw("sale.order", "search_read",
                       [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], limit=6000,
                       context={"active_test": False})}

    zeilen_je_auftrag = {}
    for z in zeilen:
        if z["order_id"]:
            zeilen_je_auftrag.setdefault(z["order_id"][0], []).append(z)

    # 0) Testauftraege des Zielsystems gemeinsam mit ihren Zeilen entfernen
    if args.testdaten_bereinigen:
        demo = ziel.kw("sale.order", "search_read",
                       [[["itk_o11_id", "=", 0]], ["id", "name"]], limit=500,
                       context={"active_test": False})
        for d in demo:
            if args.ausfuehren:
                try:
                    # Odoo 18 verweigert das Loeschen bestaetigter Auftraege: erst stornieren
                    try:
                        ziel.kw("sale.order", "action_cancel", [[d["id"]]])
                    except Exception:
                        pass
                    ziel.kw("sale.order", "unlink", [[d["id"]]])
                    stat["testdaten"] += 1
                except Exception as e:
                    stat["fehler"] += 1
                    print("  FEHLER Testauftrag %s: %s" % (d["id"], str(e)[-200:]))
            else:
                stat["testdaten"] += 1

    status_map = {"draft": "draft", "sent": "sent", "sale": "sale", "done": "sale",
                  "cancel": "cancel"}

    neu = [a for a in auftraege if a["id"] not in bestand]
    stat["da"] = len(auftraege) - len(neu)
    for i in range(0, len(neu), BATCH):
        block = neu[i:i + BATCH]
        for a in block:
            pid = a["partner_id"] and a["partner_id"][0]
            if not pid or pid not in part_map:
                stat["ohne_partner"] += 1
                print("  NICHT ZUORDENBAR Auftrag o11_id %s: Kunde fehlt" % a["id"])
                continue
            vals = {"partner_id": part_map[pid], "itk_o11_id": a["id"],
                    "client_order_ref": a["client_order_ref"] or False,
                    "note": a["note"] or False, "origin": a["origin"] or False,
                    "date_order": a["date_order"],
                    "state": status_map.get(a["state"], "draft")}
            if a["pricelist_id"] and a["pricelist_id"][0] in pl_map:
                vals["pricelist_id"] = pl_map[a["pricelist_id"][0]]
            order_zeilen = []
            for z in zeilen_je_auftrag.get(a["id"], []):
                prod = z["product_id"] and z["product_id"][0]
                if not prod or prod not in var_map:
                    stat["ohne_produkt"] += 1
                    continue
                zvals = {"product_id": var_map[prod],
                         "name": z["name"] or "",
                         "product_uom_qty": z["product_uom_qty"],
                         "price_unit": z["price_unit"],
                         "discount": z["discount"] or 0.0,
                         "sequence": z["sequence"] or 10}
                ziel_uom_name = (z["product_uom"] or [0, ""])[1]
                ziel_uom = uom_map.get(ziel_uom_name)
                if ziel_uom:
                    produkt_kat = var_uom_kat.get(var_map[prod])
                    if uom_kat_je_id.get(ziel_uom) == produkt_kat:
                        zvals["product_uom"] = ziel_uom
                order_zeilen.append(zvals)
            vals["order_line"] = [(0, 0, z) for z in order_zeilen]
            if args.ausfuehren:
                try:
                    neu_id = ziel.kw("sale.order", "create", [vals])
                    neu_id = neu_id[0] if isinstance(neu_id, list) else neu_id
                    # Odoo-11-Auftragsnummer beibehalten
                    ziel.kw("sale.order", "write", [[neu_id], {"name": a["name"]}])
                    bestand[a["id"]] = neu_id
                    stat["neu"] += 1
                    stat["zeilen_neu"] += len(order_zeilen)
                    mapping.append({"o11_id": a["id"], "o11_name": a["name"],
                                    "o18_id": neu_id, "state": a["state"],
                                    "zeilen": len(order_zeilen)})
                except Exception as e:
                    stat["fehler"] += 1
                    print("  FEHLER Auftrag o11_id %s: %s" % (a["id"], str(e)[-260:]))
            else:
                stat["neu"] += 1
                stat["zeilen_neu"] += len(order_zeilen)
                mapping.append({"o11_id": a["id"], "o11_name": a["name"],
                                "o18_id": -a["id"], "state": a["state"],
                                "zeilen": len(order_zeilen)})

    breite = "{:<40}{:>10}"
    print(breite.format("Objekt", "Anzahl"))
    print("-" * 50)
    for k, v in (("Auftraege gelesen", stat["gelesen"]),
                 ("davon neu angelegt", stat["neu"]),
                 ("davon bereits vorhanden", stat["da"]),
                 ("Zeilen gelesen", stat["zeilen"]),
                 ("Zeilen neu angelegt", stat["zeilen_neu"]),
                 ("Auftraege ohne zuordenbaren Kunden", stat["ohne_partner"]),
                 ("Zeilen ohne zuordenbares Produkt", stat["ohne_produkt"]),
                 ("Testauftraege bereinigt", stat["testdaten"]),
                 ("nicht zuordenbar", stat["ohne_partner"] + stat["ohne_produkt"]),
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
