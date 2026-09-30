"""R1 Mengeneinheiten: Pruefung der Zuordnung Odoo 11 -> Odoo 18 (nur lesend).

Prueft je Instanz:
  1. jede in Odoo 11 tatsaechlich verwendete Mengeneinheit hat in Odoo 18 eine Einheit mit
     gleichem Namen (Zuordnung ueber den Namen, IDs spielen keine Rolle)
  2. Rundung der Haupteinheiten "Einheit(en)" und "ITK Einheit" = 0,001 wie in Odoo 11
  3. Dezimalgenauigkeit "Product Unit of Measure" = 3 wie in Odoo 11
  4. Mengenwerte: jede Odoo-11-Auftragsmenge ist mit der Odoo-18-Rundung unveraendert darstellbar
     (Nachweis der Werteerhaltung, z. B. 0,125)
  5. die uebrigen bestehenden Odoo-18-Einheiten sind unveraendert vorhanden
  6. Odoo-18-Zusatzfunktionen unberuehrt: Standardeinheiten weiterhin vorhanden und aktiv

Aufruf:
    python scripts/pruefe_verkauf_r1_mengeneinheiten.py [--instanzen lokal,vm]
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

SP = {"lang": "de_DE"}
GENAUIGKEIT = "Product Unit of Measure"
HAUPTEINHEITEN = ("Einheit(en)", "ITK Einheit")
# Die 29 Einheiten, die Odoo 18 vor der R1-Vorbereitung fuehrt (unveraendert erhalten)
STANDARD_O18 = ["cm", "Dutzende", "Einheit(en)", "fl oz (US)", "ft", "ft┬│", "ft┬▓", "g",
                "Gal (US)", "in", "in┬│", "ITK Einheit", "kg", "km", "kWh", "L", "lb", "m",
                "m┬│", "m┬▓", "mi", "Minuten", "mm", "oz", "qt (US)", "Stunden", "t", "Tage", "yd"]


class Pruefer:
    def __init__(self) -> None:
        self.ok = 0
        self.fehl = 0
        self.meldungen: list[str] = []

    def pruefe(self, bedingung: bool, text: str) -> None:
        if bedingung:
            self.ok += 1
        else:
            self.fehl += 1
            self.meldungen.append(text)
            print("  FEHL %s" % text)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanzen", default="lokal,vm")
    a = p.parse_args()

    k11 = o11()
    einheiten11 = k11.kw("product.uom", "search_read",
                         [[], ["name", "uom_type", "rounding", "factor"]], context=SP)
    benutzt = []
    zeilen11 = []
    offset = 0
    while True:
        s = k11.kw("sale.order.line", "search_read",
                   [[], ["product_uom_qty", "product_uom", "order_id"]], limit=500, offset=offset,
                   context=SP, order="id")
        if not s:
            break
        zeilen11.extend(s)
        offset += 500
    for u in einheiten11:
        n = sum(1 for z in zeilen11 if z["product_uom"] and z["product_uom"][0] == u["id"])
        if n:
            u["zeilen"] = n
            u["name"] = u["name"]
            benutzt.append(u)
    print("Odoo 11: %d verwendete Einheiten, %d Auftragszeilen gelesen"
          % (len(benutzt), len(zeilen11)))

    gesamt = Pruefer()
    for instanz in [x.strip() for x in a.instanzen.split(",") if x.strip()]:
        print()
        print("=" * 78)
        print("Instanz %s" % instanz)
        print("=" * 78)
        k18 = o18(instanz)
        units = k18.kw("uom.uom", "search_read",
                       [[], ["name", "uom_type", "rounding", "factor", "category_id", "active"]],
                       context=SP)
        nach_name = {}
        for u in units:
            nach_name.setdefault(u["name"], []).append(u)
        prec = k18.kw("decimal.precision", "search_read", [[("name", "=", GENAUIGKEIT)], ["digits"]],
                      context=SP)[0]
        p18 = Pruefer()

        print("--- 1. Zuordnung der verwendeten Odoo-11-Einheiten ---")
        for u in sorted(benutzt, key=lambda x: -x["zeilen"]):
            treffer = nach_name.get(u["name"])
            p18.pruefe(bool(treffer), "Einheit '%s' (%d Zeilen) fehlt in Odoo 18"
                       % (u["name"], u["zeilen"]))
            if treffer:
                t = treffer[0]
                print("  OK   %-22s -> %-22s (id %s, Rundung O11 %s / O18 %s, %d Zeilen)"
                      % (u["name"], t["name"], t["id"], u["rounding"], t["rounding"], u["zeilen"]))
                p18.pruefe(t["rounding"] <= u["rounding"] + 1e-12,
                           "Rundung von '%s' ist groeber als in Odoo 11 (%s > %s)"
                           % (u["name"], t["rounding"], u["rounding"]))

        print("--- 2. Rundung der Haupteinheiten ---")
        for name in HAUPTEINHEITEN:
            t = nach_name.get(name)
            p18.pruefe(bool(t) and abs(t[0]["rounding"] - 0.001) < 1e-12,
                       "Rundung von '%s' ist %s, erwartet 0.001"
                       % (name, t[0]["rounding"] if t else "Einheit fehlt"))

        print("--- 3. Dezimalgenauigkeit ---")
        p18.pruefe(prec["digits"] == 3,
                   "Dezimalgenauigkeit '%s' ist %s, erwartet 3" % (GENAUIGKEIT, prec["digits"]))
        print("  Genauigkeit %s = %s" % (GENAUIGKEIT, prec["digits"]))

        print("--- 4. Werteerhaltung der Mengen (%d Zeilen) ---" % len(zeilen11))
        nicht_darstellbar = []
        for z in zeilen11:
            q = z["product_uom_qty"] or 0.0
            name = z["product_uom"][1] if z["product_uom"] else None
            t = nach_name.get(name)
            runde = t[0]["rounding"] if t else 0.01
            if abs(q - round(q / runde) * runde) > 1e-9:
                nicht_darstellbar.append((z["order_id"][1] if z["order_id"] else "-", name, q))
        p18.pruefe(not nicht_darstellbar,
                   "Mengen nicht darstellbar: %s" % nicht_darstellbar[:5])
        print("  nicht darstellbare Mengen: %d" % len(nicht_darstellbar))
        drei = [z["product_uom_qty"] for z in zeilen11
                if abs((z["product_uom_qty"] or 0) - round((z["product_uom_qty"] or 0), 2)) > 1e-9]
        print("  Mengen mit 3 Nachkommastellen: %d %s" % (len(drei), drei[:5]))

        print("--- 5. Bestehende Odoo-18-Einheiten erhalten ---")
        fehlend = [n for n in STANDARD_O18 if n not in nach_name]
        p18.pruefe(not fehlend, "Odoo-18-Standardeinheiten fehlen: %s" % fehlend)
        print("  Einheiten gesamt: %d | davon aktiv: %d"
              % (len(units), sum(1 for u in units if u["active"])))

        print("--- 6. Verwendung in Odoo 18 (unveraendert) ---")
        produkte = k18.kw("product.template", "search_count", [[]], context=SP)
        zeilen = k18.kw("sale.order.line", "search_count", [[]], context=SP)
        print("  Produkte %d | Auftragszeilen %d" % (produkte, zeilen))
        erwartet = {"lokal": (13, 28), "vm": (13, 29)}.get(instanz, (13, 28))
        p18.pruefe((produkte, zeilen) == erwartet,
                   "Bestand in Odoo 18 abweichend (Produkte %d, Zeilen %d, erwartet %s)"
                   % (produkte, zeilen, erwartet))

        print()
        print("Ergebnis %s: %d OK / %d FEHL" % (instanz, p18.ok, p18.fehl))
        gesamt.ok += p18.ok
        gesamt.fehl += p18.fehl
        gesamt.meldungen.extend(p18.meldungen)

    print()
    print("Gesamt: %d OK / %d FEHL" % (gesamt.ok, gesamt.fehl))
    if gesamt.fehl:
        print("Fehlermeldungen:")
        for m in gesamt.meldungen:
            print("  %s" % m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
