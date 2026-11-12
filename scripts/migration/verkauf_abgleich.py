# -*- coding: utf-8 -*-
"""Abgleich Verkauf/Abonnements Odoo 11 <-> Odoo 18 (read-only Nachweis).

Teil des ITK-Migrationsprojekts. Schreibt nichts, weder in Odoo 11 noch in Odoo 18.

Prueft je Auftrag und je Abo:
- Anzahl der Zeilen
- Mengen, Einzelpreise, Rabatte je Zeile (Toleranz 0,0001)
- Steuern der Zeilen (Satzvergleich, weil die Steuer-IDs systembedingt abweichen)
- Kopfsumme Odoo 11 gegen Zeilensumme Odoo 18 (Abweichungen werden ausgewiesen,
  ohne sie zu korrigieren - in Odoo 18 gilt die Berechnung aus den Zeilen)

Ausgabe: Zaehlwerte und - auf Wunsch - eine CSV mit den abweichenden Belegen
(ausserhalb des Repositories ablegen). Keine Personendaten.

Aufruf:
    python scripts/migration/verkauf_abgleich.py --instanz lokal
    python scripts/migration/verkauf_abgleich.py --instanz vm --csv %LOCALAPPDATA%/Temp/abgleich.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

TOLERANZ = 0.0001


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--csv")
    args = ap.parse_args()

    o11 = client.o11()
    o18 = client.o18(args.instanz)

    # ---------- Verkauf ----------
    auftraege11 = o11.kw("sale.order", "search_read",
                         [[], ["id", "name", "state", "amount_untaxed", "order_line"]],
                         limit=6000, context={"active_test": False})
    ids11 = {a["id"]: a for a in auftraege11}

    alle_zeilen11 = o11.kw("sale.order.line", "search_read", [[]],
                           fields=["id", "order_id", "product_id", "product_uom_qty",
                                   "price_unit", "discount", "price_subtotal", "tax_id"],
                           limit=20000, context={"active_test": False})
    zeilen11 = {}
    for z in alle_zeilen11:
        if z["order_id"]:
            zeilen11.setdefault(z["order_id"][0], []).append(z)

    auftraege18 = o18.kw("sale.order", "search_read",
                         [[["itk_o11_id", "!=", False]],
                          ["id", "itk_o11_id", "name", "amount_untaxed", "order_line"]],
                         limit=6000, context={"active_test": False})
    alle_zeilen18 = {}
    ids_zeilen = [i for a in auftraege18 for i in a["order_line"]]
    for i in range(0, len(ids_zeilen), 500):
        for z in o18.kw("sale.order.line", "read",
                        [ids_zeilen[i:i + 500],
                         ["order_id", "product_id", "product_uom_qty", "price_unit",
                          "discount", "price_subtotal", "tax_id"]]):
            alle_zeilen18.setdefault(z["order_id"][0], []).append(z)

    # Steuersaetze je System (Vergleich ueber Satz, nicht ueber IDs)
    satz11 = {t["id"]: round(t["amount"] or 0, 2) for t in
              o11.kw("account.tax", "search_read", [[], ["id", "amount"]], limit=600,
                     context={"active_test": False})}
    satz18 = {t["id"]: round(t["amount"] or 0, 2) for t in
              o18.kw("account.tax", "search_read", [[], ["id", "amount"]], limit=600,
                     context={"active_test": False})}
    stat = {"steuer_abweichend": 0, "auftraege11": len(auftraege11), "auftraege18": len(auftraege18),
            "zeilen11": len(alle_zeilen11), "zeilen18": sum(len(v) for v in alle_zeilen18.values()),
            "zeilen_abweichend": 0, "anzahl_abweichend": 0, "summe_abweichend": 0,
            "summe11": 0.0, "summe18": 0.0, "ohne_zeilen": 0}
    abweichungen = []

    for a in auftraege18:
        o11a = ids11.get(a["itk_o11_id"])
        if not o11a:
            continue
        stat["summe11"] += o11a["amount_untaxed"] or 0
        stat["summe18"] += a["amount_untaxed"] or 0
        z11 = zeilen11.get(o11a["id"], [])
        z18 = alle_zeilen18.get(a["id"], [])
        if not z11:
            stat["ohne_zeilen"] += 1
        if len(z11) != len(z18):
            stat["anzahl_abweichend"] += 1
            abweichungen.append([a["name"], "zeilenanzahl", len(z11), len(z18)])
        # Zeilen ueber Menge+Preis+Steuer zuordnen (Reihenfolge kann abweichen)
        rest = list(z18)
        for zi in z11:
            treffer = None
            for zk in rest:
                if (abs((zk["product_uom_qty"] or 0) - (zi["product_uom_qty"] or 0)) < TOLERANZ
                        and abs((zk["price_unit"] or 0) - (zi["price_unit"] or 0)) < TOLERANZ
                        and abs((zk["discount"] or 0) - (zi["discount"] or 0)) < TOLERANZ):
                    treffer = zk
                    break
            if treffer:
                soll = sorted(satz11.get(t, -1) for t in (zi.get("tax_id") or []))
                ist = sorted(satz18.get(t, -1) for t in (treffer.get("tax_id") or []))
                if soll != ist:
                    stat["steuer_abweichend"] += 1
                    abweichungen.append([a["name"], "steuer", soll, ist])
            if not treffer:
                stat["zeilen_abweichend"] += 1
                abweichungen.append([a["name"], "zeile", zi["product_uom_qty"],
                                     zi["price_unit"], zi["discount"]])
            else:
                rest.remove(treffer)
        if abs((o11a["amount_untaxed"] or 0) - (a["amount_untaxed"] or 0)) > 0.01:
            stat["summe_abweichend"] += 1
            abweichungen.append([a["name"], "kopfsumme", o11a["amount_untaxed"],
                                 a["amount_untaxed"]])

    # ---------- Abonnements ----------
    abos11 = o11.kw("sale.subscription", "search_read",
                    [[], ["id", "name", "recurring_total", "recurring_invoice_line_ids"]],
                    limit=6000, context={"active_test": False})
    abos18 = o18.kw("sale.subscription", "search_read",
                    [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id", "name"]],
                    limit=6000, context={"active_test": False})
    stat["abos11"] = len(abos11)
    stat["abos18"] = len(abos18)

    breite = "{:<46}{:>10}"
    print("=== Abgleich %s (read-only) ===" % args.instanz)
    print(breite.format("Auftraege Odoo 11", stat["auftraege11"]))
    print(breite.format("Auftraege Odoo 18 (migriert)", stat["auftraege18"]))
    print(breite.format("Auftragszeilen Odoo 11", stat["zeilen11"]))
    print(breite.format("Auftragszeilen Odoo 18", stat["zeilen18"]))
    print(breite.format("Zeilen mit Abweichung Menge/Preis/Rabatt", stat["zeilen_abweichend"]))
    print(breite.format("Zeilen mit abweichendem Steuersatz", stat["steuer_abweichend"]))
    print(breite.format("Auftraege mit abweichender Zeilenzahl", stat["anzahl_abweichend"]))
    print(breite.format("Auftraege ohne Zeilen", stat["ohne_zeilen"]))
    print(breite.format("Auftraege mit abweichender Kopfsumme", stat["summe_abweichend"]))
    print(breite.format("Summe Kopfwerte Odoo 11", round(stat["summe11"], 2)))
    print(breite.format("Summe Kopfwerte Odoo 18", round(stat["summe18"], 2)))
    print(breite.format("Differenz", round(stat["summe18"] - stat["summe11"], 2)))
    print(breite.format("Abos Odoo 11", stat["abos11"]))
    print(breite.format("Abos Odoo 18 (migriert)", stat["abos18"]))

    if args.csv:
        with open(args.csv, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(["beleg", "art", "wert_odoo11", "wert_odoo18", "hinweis"])
            for a in abweichungen:
                w.writerow(list(a) + ["Kopfwert in Odoo 11 inkonsistent" if a[1] == "kopfsumme" else ""])
        print("\nCSV geschrieben:", args.csv, "->", len(abweichungen), "Zeilen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
