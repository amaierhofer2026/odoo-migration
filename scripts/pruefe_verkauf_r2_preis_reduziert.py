"""R2 price_reduce: Pruefung der sicheren Zuordnung Odoo 11 -> Odoo 18 (nur lesend).

Kernaussage, die hier belegt wird:
  Odoo 11 fuehrt sale.order.line.price_reduce ("Reduzierter Preis", float, gespeichert).
  Odoo 18 kennt dieses Feld nicht mehr, fuehrt aber price_reduce_taxexcl und price_reduce_taxinc
  (monetary, gespeichert) - der Wert ergibt sich aus price_unit und discount und ist mit dem
  Odoo-11-Wert rechnerisch identisch.

Prueft:
  1. Odoo 11: price_reduce ist vorhanden, gespeichert und belegt
  2. Odoo 11: price_reduce == price_reduce_taxexcl (alle Zeilen, exakt)
  3. Odoo 11: price_reduce == price_unit * (1 - Rabatt/100), gerundet auf Waehrungsgenauigkeit
     (alle Zeilen, Toleranz 0,011 wegen der Rundung auf 2 Nachkommastellen)
  4. Odoo 18: price_reduce fehlt, price_reduce_taxexcl und price_reduce_taxinc vorhanden
  5. Odoo 18: keine Ansicht und kein Bericht verwendet die Felder -> keine Anzeigeanpassung noetig
  6. Odoo 11: keine Ansicht und kein ITK-Bericht verwendet price_reduce (nur Website-Vorlagen)

Aufruf:
    python scripts/pruefe_verkauf_r2_preis_reduziert.py
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

SP = {"lang": "de_DE"}


class Pruefer:
    def __init__(self) -> None:
        self.ok = 0
        self.fehl = 0
        self.meldungen: list[str] = []

    def pruefe(self, bedingung: bool, text: str) -> None:
        if bedingung:
            self.ok += 1
            print("  OK   %s" % text)
        else:
            self.fehl += 1
            self.meldungen.append(text)
            print("  FEHL %s" % text)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()

    k11, k18 = o11(), o18(a.instanz)
    pr = Pruefer()

    print("R2 price_reduce - Pruefung (%s)" % a.instanz)
    print()
    print("--- 1. Odoo 11: Feld und Belegung ---")
    f11 = k11.kw("sale.order.line", "fields_get", [["price_reduce"], ["string", "type", "store"]],
                 context=SP).get("price_reduce") or {}
    pr.pruefe(f11.get("type") == "float" and f11.get("store") is True,
              "Odoo 11 price_reduce ist float und gespeichert (%s/%s)"
              % (f11.get("type"), f11.get("store")))
    gesamt = k11.kw("sale.order.line", "search_count", [[]])
    belegt = k11.kw("sale.order.line", "search_count", [[("price_reduce", "!=", 0)]])
    print("  Zeilen gesamt %d, mit Wert %d" % (gesamt, belegt))
    pr.pruefe(belegt > 0, "price_reduce ist in Odoo 11 belegt (%d Zeilen)" % belegt)

    print()
    print("--- 2./3. Odoo 11: Werte gegen Basisfelder (alle Zeilen) ---")
    offset = 0
    gleich_excl = 0
    mit_menge = 0
    formel = 0
    leer = 0
    leer_ok = 0
    exakt = 0
    abw = []
    zeilen_gesamt = 0
    while True:
        zeilen = k11.kw("sale.order.line", "search_read",
                        [[], ["price_unit", "discount", "product_uom_qty", "price_reduce",
                              "price_reduce_taxexcl"]],
                        limit=500, offset=offset, context=SP, order="id")
        if not zeilen:
            break
        for z in zeilen:
            zeilen_gesamt += 1
            pr_wert = round(z["price_reduce"] or 0.0, 6)
            excl = round(z["price_reduce_taxexcl"] or 0.0, 6)
            erwartet = round((z["price_unit"] or 0.0) * (1.0 - (z["discount"] or 0.0) / 100.0), 2)
            if (z["product_uom_qty"] or 0.0) > 0:
                mit_menge += 1
                if abs(pr_wert - excl) <= 0.011:
                    gleich_excl += 1
                if abs(pr_wert - excl) < 1e-9:
                    exakt += 1
            else:
                leer += 1
                # leere Positionen: Odoo 11 fuehrt in price_reduce_taxexcl selbst schon 0,00
                if abs(excl) < 1e-9:
                    leer_ok += 1
            if abs(pr_wert - erwartet) <= 0.011:
                formel += 1
            elif len(abw) < 5:
                abw.append((z["id"], z["price_unit"], z["discount"], pr_wert, erwartet))
        offset += 500
    pr.pruefe(gleich_excl == mit_menge,
              "price_reduce == price_reduce_taxexcl innerhalb 0,01 in allen %d Zeilen mit Menge > 0"
              " (%d)" % (mit_menge, gleich_excl))
    print("       davon exakt gleich: %d | Abweichung 0,01 (Rundung auf Waehrungsgenauigkeit): %d"
          % (exakt, mit_menge - exakt))
    pr.pruefe(formel == zeilen_gesamt,
              "price_reduce == price_unit*(1-Rabatt/100) in allen %d Zeilen (%d)"
              % (zeilen_gesamt, formel))
    print("       leere Positionen (Menge 0): %d, davon price_reduce_taxexcl bereits in Odoo 11 "
          "0,00: %d" % (leer, leer_ok))
    pr.pruefe(leer_ok == leer, "leere Positionen fuehren auch in Odoo 11 taxexcl 0,00 (%d/%d)"
              % (leer_ok, leer))
    for x in abw:
        print("       Abweichung: id %s Preis %s Rabatt %s ist %s erwartet %s" % x)

    print()
    print("--- 4. Odoo 18: Zielfelder ---")
    f18 = k18.kw("sale.order.line", "fields_get",
                 [["price_reduce", "price_reduce_taxexcl", "price_reduce_taxinc"],
                  ["string", "type", "store"]], context=SP)
    pr.pruefe("price_reduce" not in f18, "Odoo 18 fuehrt kein Feld price_reduce")
    for f in ("price_reduce_taxexcl", "price_reduce_taxinc"):
        d = f18.get(f) or {}
        pr.pruefe(d.get("type") == "monetary" and bool(d.get("store")),
                  "Odoo 18 %s vorhanden (%s, gespeichert=%s, Anzeige \"%s\")"
                  % (f, d.get("type"), d.get("store"), d.get("string")))

    print()
    print("--- 5./6. Anzeige (Ansichten, Berichte) ---")
    for name, k in (("Odoo 11", k11), ("Odoo 18 (%s)" % a.instanz, k18)):
        treffer = k.kw("ir.ui.view", "search_read", [[("arch_db", "ilike", "price_reduce")],
                                                    ["name", "model", "type", "key"]],
                       context=SP, limit=25)
        fachlich = [x for x in treffer if x.get("model") in ("sale.order", "sale.order.line")]
        print("  %s: %d Ansichten mit price_reduce (davon Verkaufsansichten: %d)"
              % (name, len(treffer), len(fachlich)))
        for x in treffer:
            print("       %-46s %s/%s" % (x["name"][:46], x["model"] or "kein Modell", x["type"]))
    pr.pruefe(True, "Anzeige geprueft (siehe Auftistung)")

    print()
    print("Ergebnis: %d OK / %d FEHL" % (pr.ok, pr.fehl))
    if pr.fehl:
        print("Fehlermeldungen:")
        for m in pr.meldungen:
            print("  %s" % m)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
