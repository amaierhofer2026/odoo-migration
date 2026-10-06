"""Produktart: Verwendung je Belegmodell (read-only, Odoo 11 und Odoo 18).

Zeigt je Modul (Rechnungen, Verkaufsauftraege, Abonnements, Lagerbewegungen, Bestellungen),
welche Produktarten dort tatsaechlich vorkommen - Grundlage fuer die Frage, ob Funktionen,
Filter oder Module von der Produktart abhaengen.

Aufruf: python scripts/produktart_verwendung_je_modul.py [o11|lokal|vm]
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}


def verteilung(k, modell, feld, produkt_feld="product_id"):
    """Produkte eines Belegmodells auf type und product_type_id abbilden."""
    try:
        gruppen = k.kw(modell, "read_group", [[], [produkt_feld], [produkt_feld]], context=CTX)
    except RuntimeError as fehler:
        return {"fehler": str(fehler)[:150]}
    ids = [g[produkt_feld][0] for g in gruppen
           if isinstance(g.get(produkt_feld), (list, tuple)) and g[produkt_feld][0]]
    if not ids:
        return {"produkte": 0}
    paare = k.kw("product.product", "read", [ids, ["product_tmpl_id"]], context=CTX)
    tmpls = sorted({p["product_tmpl_id"][0] for p in paare if p.get("product_tmpl_id")})
    daten = k.kw("product.template", "read", [tmpls, ["type", "product_type_id"]], context=CTX)
    typ = {d["id"]: d.get("type") for d in daten}
    pt = {d["id"]: (d["product_type_id"][1] if d.get("product_type_id") else "(leer)")
          for d in daten}
    je_typ, je_pt, gesehen = {}, {}, set()
    for p in paare:
        t = p["product_tmpl_id"][0] if p.get("product_tmpl_id") else None
        if t in gesehen:
            continue
        gesehen.add(t)
        je_typ[typ.get(t) or "(leer)"] = je_typ.get(typ.get(t) or "(leer)", 0) + 1
        w = pt.get(t, "(leer)")
        je_pt[w] = je_pt.get(w, 0) + 1
    return {"produkte": len(gesehen),
            "je_type": dict(sorted(je_typ.items(), key=lambda x: -x[1])),
            "je_product_type_id": dict(sorted(je_pt.items(), key=lambda x: -x[1]))}


MODELLE_O11 = [("account.invoice.line", "product_id", "Kundenrechnungen (Zeilen)"),
               ("account.move.line", "product_id", "Buchungszeilen"),
               ("sale.order.line", "product_id", "Verkaufsauftraege (Zeilen)"),
               ("sale.subscription.line", "product_id", "Abonnements (Zeilen)"),
               ("stock.move", "product_id", "Lagerbewegungen"),
               ("purchase.order.line", "product_id", "Bestellungen (Zeilen)")]
MODELLE_O18 = [("account.move.line", "product_id", "Buchungszeilen/Rechnungen"),
               ("sale.order.line", "product_id", "Verkaufsauftraege (Zeilen)"),
               ("sale.subscription.line", "product_id", "Abonnements (Zeilen)"),
               ("stock.move", "product_id", "Lagerbewegungen"),
               ("purchase.order.line", "product_id", "Bestellungen (Zeilen)")]

if __name__ == "__main__":
    inst = sys.argv[1] if len(sys.argv) > 1 else "o11"
    k = o11() if inst == "o11" else o18(inst)
    aus = {}
    for modell, feld, titel in (MODELLE_O11 if inst == "o11" else MODELLE_O18):
        aus[titel] = {"modell": modell}
        aus[titel].update(verteilung(k, modell, feld))
    ziel = os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "Temp", "produktart",
                        "verwendung_%s.json" % inst)
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(aus, fh, ensure_ascii=False, indent=1)

    print("=== Verwendung je Modul: %s ===" % inst.upper())
    for titel, d in aus.items():
        print("\n%s (%s)" % (titel, d["modell"]))
        if "fehler" in d:
            print("   Fehler:", d["fehler"])
            continue
        print("   Produkte:", d.get("produkte"))
        print("   je Produktart (type):", d.get("je_type"))
        print("   je Product-Type (product_type_id):", d.get("je_product_type_id"))
    print("\ngespeichert:", ziel)
