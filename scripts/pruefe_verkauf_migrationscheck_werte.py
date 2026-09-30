"""Gezielte Wert- und Zuordnungspruefung zum Migrations-Check Verkauf (nur lesend).

Beantwortet die Fragen, die fuer die Werteerhaltung entscheidend sind:
  1. Welche in Odoo 11 belegten Felder werden in Odoo 18 berechnet (Wert nicht uebernehmbar)?
  2. Auswahlwerte (state, invoice_status, picking_policy) Odoo 11 gegen Odoo 18 - Schluesselgleichheit
  3. Mengeneinheiten: Odoo-11-Werte (product.uom) und Entsprechung in Odoo 18 (uom.uom)
  4. route_id, analytic_account_id, company_id, date_order: Vorkommen und Belegung
  5. Wo stehen die Felder des Odoo-11-Reiters "Weitere Informationen" im Odoo-18-Formular?
  6. Waehrungs- und Betragsfelder (Werteerhalt bei Betraegen)

Aufruf:
    python scripts/pruefe_verkauf_migrationscheck_werte.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}


def feldinfo(k, modell: str, felder: list[str]) -> dict:
    fg = k.kw(modell, "fields_get", [felder, ["string", "type", "relation", "selection", "store"]],
              context=SP)
    return fg


def main() -> int:
    k11, k18 = o11(), o18("lokal")
    print("Gezielte Wert- und Zuordnungspruefung (nur lesend)")

    # 1. Auswahlwerte im Vergleich
    print()
    print("--- 1. Auswahlwerte ---")
    for modell, feld in (("sale.order", "state"), ("sale.order", "invoice_status"),
                         ("sale.order", "picking_policy"), ("sale.order.line", "state"),
                         ("sale.order.line", "display_type")):
        try:
            s11 = feldinfo(k11, modell, [feld]).get(feld, {}).get("selection") or []
        except Exception:
            s11 = []
        try:
            s18 = feldinfo(k18, modell, [feld]).get(feld, {}).get("selection") or []
        except Exception:
            s18 = []
        k11s = [a for a, _ in s11]
        k18s = [a for a, _ in s18]
        print("  %s.%s" % (modell, feld))
        print("     O11 Schluessel: %s" % k11s)
        print("     O18 Schluessel: %s" % k18s)
        print("     nur O11: %s | nur O18: %s" % (sorted(set(k11s) - set(k18s)),
                                                  sorted(set(k18s) - set(k11s))))

    # 2. Belegung und Zustandsverteilung
    print()
    print("--- 2. Zustandsverteilung Odoo 11 (read-only) ---")
    for feld in ("state", "invoice_status"):
        g = k11.kw("sale.order", "read_group", [[], [feld], [feld]], context=SP)
        print("  sale.order.%s: %s" % (feld, {str(x[feld]): x.get(feld + "_count") for x in g}))

    # 3. Mengeneinheiten
    print()
    print("--- 3. Mengeneinheiten ---")
    uoms11 = k11.kw("product.uom", "search_read", [[], ["name", "uom_type", "rounding"]],
                    context=SP)
    benutzt = k11.kw("sale.order.line", "read_group", [[], ["product_uom"], ["product_uom"]],
                     context=SP, limit=20)
    print("  Odoo 11 Einheiten insgesamt: %d" % len(uoms11))
    print("  in Auftragszeilen verwendet:")
    for b in benutzt:
        zahl = b.get("product_uom_count") or b.get("__count")
        print("     %-32s %s Zeilen" % (b["product_uom"][1] if b.get("product_uom") else "-", zahl))
    fgu = k18.kw("uom.uom", "fields_get", [[], ["string", "type"]], context=SP)
    felder18 = [f for f in ("name", "uom_type", "factor", "factor_inv", "rounding",
                            "relative_factor", "category_id") if f in fgu]
    uoms18 = k18.kw("uom.uom", "search_read", [[], felder18], context=SP)
    print("  Odoo 18 Einheiten insgesamt: %d" % len(uoms18))
    print("  Odoo-11-Einheiten im Bestand:")
    for u in sorted(uoms11, key=lambda x: x["name"]):
        anzahl = k11.kw("sale.order.line", "search_count", [[("product_uom", "=", u["id"])]])
        if anzahl:
            print("     %-28s uom_type=%-8s Rundung=%s | %d Auftragszeilen"
                  % (u["name"], u.get("uom_type"), u.get("rounding"), anzahl))
    namen11 = {u["name"] for u in uoms11}
    namen18 = {u["name"] for u in uoms18}
    print("  Namen nur in Odoo 11: %s" % sorted(namen11 - namen18)[:10])
    print("  Namen nur in Odoo 18: %s" % sorted(namen18 - namen11)[:10])
    print("  Namen in beiden: %d" % len(namen11 & namen18))

    # 4. Einzelfelder
    print()
    print("--- 4. Einzelfelder ---")
    for modell, felder in (("sale.order", ["route_id", "route_ids", "analytic_account_id",
                                           "company_id", "date_order", "confirmation_date",
                                           "currency_id", "pricelist_id", "payment_term_id",
                                           "warehouse_id", "picking_policy", "incoterm",
                                           "note", "locked", "tag_ids"]),
                           ("sale.order.line", ["route_id", "product_uom", "price_reduce",
                                                "price_reduce_taxexcl", "price_reduce_taxinc",
                                                "price_subtotal", "price_total", "discount",
                                                "tax_id", "qty_delivered", "invoice_lines",
                                                "layout_category_id", "currency_id",
                                                "product_packaging_id"])):
        f11 = feldinfo(k11, modell, felder)
        f18 = feldinfo(k18, modell, felder)
        for f in felder:
            i11, i18 = f11.get(f), f18.get(f)
            belegt = None
            if i11 and i11.get("store"):
                try:
                    if i11.get("type") in ("integer", "float", "monetary"):
                        belegt = k11.kw(modell, "search_count", [[(f, "!=", 0)]])
                    elif i11.get("type") == "boolean":
                        belegt = k11.kw(modell, "search_count", [[(f, "=", True)]])
                    else:
                        belegt = k11.kw(modell, "search_count", [[(f, "!=", False)]])
                except Exception:
                    belegt = "?"
            print("  %-22s %-22s O11: %-28s O18: %-28s belegt O11: %s"
                  % (modell, f,
                     ("%s/%s%s" % (i11["type"], i11.get("relation") or "-",
                                   "" if i11.get("store") else " (nicht gespeichert)")) if i11 else "FEHLT",
                     ("%s/%s%s" % (i18["type"], i18.get("relation") or "-",
                                   "" if i18.get("store") else " (nicht gespeichert)")) if i18 else "FEHLT",
                     belegt))

    # 5. Wo stehen die Felder des Reiters "Weitere Informationen" in Odoo 18?
    print()
    print("--- 5. Felder des Odoo-11-Reiters 'Weitere Informationen' in Odoo 18 ---")
    with open(os.path.join(REPO, "docs", "_verkauf_migrationscheck_aufbau.json"),
              encoding="utf-8") as fh:
        aufbau = json.load(fh)
    felder_o11 = []
    for s in aufbau["weitere_informationen"]["o11"]:
        for f in s:
            felder_o11.append((f["feld"], f["gruppe"]))
    o18_alle = {}
    for s in aufbau["sale.order"]["reiter_o18"]:
        for f in s["felder"]:
            o18_alle[f] = s["seite"]
    o11_alle = {}
    for s in aufbau["sale.order"]["reiter_o11"]:
        for f in s["felder"]:
            o11_alle[f] = s["seite"]
    o18_weitere = {}
    for s in aufbau["weitere_informationen"]["o18"]:
        for f in s:
            o18_weitere[f["feld"]] = f["gruppe"]
    fehlend = []
    for name, gruppe11 in felder_o11:
        ziel = name
        seite = o18_alle.get(ziel)
        gruppe18 = o18_weitere.get(ziel)
        print("  %-30s O11-Gruppe %-22s -> O18: %s | Gruppe %s"
              % (name, gruppe11, seite or "NICHT im Formular", gruppe18 or "-"))
        if seite is None:
            fehlend.append((name, gruppe11))
    print()
    print("  Im Odoo-18-Formular NICHT vorhanden: %s"
          % [(n, g) for n, g in fehlend])

    print()
    print("--- 6. Weitere Felder des Odoo-11-Formulars ausserhalb des Reiters ---")
    for name, seite in sorted(o11_alle.items()):
        if seite in ("Auftragszeilen", "Weitere Informationen"):
            continue
        ziel = o18_alle.get(name)
        print("  %-30s O11: %-20s O18: %s" % (name, seite, ziel or "NICHT im Formular"))

    print()
    print("--- 7. Firmen und Waehrungen (Wertebereich) ---")
    g = k11.kw("sale.order", "read_group", [[], ["company_id"], ["company_id"]], context=SP)
    print("  Auftraege je Firma Odoo 11: %s"
          % {str(x["company_id"][1]): x.get("company_id_count") for x in g if x.get("company_id")})
    g2 = k11.kw("sale.order", "read_group", [[], ["currency_id"], ["currency_id"]], context=SP)
    print("  Auftraege je Waehrung Odoo 11: %s"
          % {str(x["currency_id"][1]): x.get("currency_id_count") for x in g2 if x.get("currency_id")})
    print("  Firmen Odoo 18: %s"
          % [c["name"] for c in k18.kw("res.company", "search_read", [[], ["name"]], context=SP)])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
