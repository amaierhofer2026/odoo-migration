"""R1 Mengeneinheiten: Zuordnung Odoo 11 -> Odoo 18 technisch vorbereiten (nur Odoo 18 aendern).

Odoo 11 wird ausschliesslich gelesen. In Odoo 18 werden ausschliesslich Mengeneinheiten und die
Dezimalgenauigkeit "Product Unit of Measure" angepasst - keine Auftraege, keine Produkte, keine
Datenmigration, keine bestehende Odoo-18-Funktion wird entfernt.

Schritte je Instanz (lokal / vm):
  1. Dezimalgenauigkeit "Product Unit of Measure": Odoo 11 fuehrt 3 Nachkommastellen (0,001),
     Odoo 18 fuehrt 2 (0,01) -> auf 3 setzen (erforderlich, siehe Nachweis 0,125-Mengen).
  2. Rundung der vorhandenen Einheiten "Einheit(en)" und "ITK Einheit" auf 0,001 setzen
     (Odoo 11 fuehrt beide mit 0,001; Odoo 18 nach der Umstellung ebenfalls).
  3. Fehlende, in Odoo 11 tatsaechlich verwendete Einheiten anlegen (GB und die
     "<Zahl> Gemeinden"-Sonderwerte) mit den Odoo-11-Eigenschaften.

Aufruf:
    python scripts/apply_verkauf_r1_mengeneinheiten.py --instanz lokal [--trocken]
    python scripts/apply_verkauf_r1_mengeneinheiten.py --instanz vm
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}

GENAUIGKEIT = "Product Unit of Measure"
GENAUIGKEIT_ZIEL = 3
RUNDUNG_HAUPT = 0.001
RUNDUNG_SONST = 0.01


def o11_einheiten() -> list[dict]:
    """Alle in Odoo 11 tatsaechlich verwendeten Mengeneinheiten (Auftragszeilen und Produkte)."""
    k = o11()
    einheiten = k.kw("product.uom", "search_read",
                     [[], ["name", "uom_type", "rounding", "factor", "category_id"]],
                     context=SP, order="name")
    benutzt = []
    for u in einheiten:
        zeilen = k.kw("sale.order.line", "search_count", [[("product_uom", "=", u["id"])]])
        produkte = k.kw("product.template", "search_count", [[("uom_id", "=", u["id"])]])
        if zeilen or produkte:
            u["zeilen"] = zeilen
            u["produkte"] = produkte
            u["kategorie"] = u["category_id"][1] if u["category_id"] else ""
            benutzt.append(u)
    return benutzt


# Einheiten, die in Odoo 18 eine eigene Kategorie brauchen: In Odoo 11 war "GB" die
# Referenzeinheit der Kategorie "Volumen"; in Odoo 18 ist das "L". "GB" ist fachlich keine
# Volumeneinheit, deshalb eigene Kategorie "Datenmenge".
EIGENE_KATEGORIE = {"GB": "Datenmenge"}


def kategorien(k18) -> dict[str, int]:
    return {c["name"]: c["id"] for c in
            k18.kw("uom.category", "search_read", [[], ["name"]], context=SP)}


def zielkategorie(k18, u: dict, anlegen: bool = True) -> int:
    """Kategorie in Odoo 18; eigene Kategorie wird angelegt, sonst auf 'Einheit' ausgewichen."""
    vorhanden = kategorien(k18)
    if u["name"] in EIGENE_KATEGORIE:
        name = EIGENE_KATEGORIE[u["name"]]
        if name in vorhanden:
            return vorhanden[name]
        if not anlegen:
            return -1
        neu = k18.kw("uom.category", "create", [{"name": name}], context=SP)
        return neu[0] if isinstance(neu, list) else neu
    name = u["kategorie"]
    if name in vorhanden:
        return vorhanden[name]
    if "Einheit" in vorhanden:
        return vorhanden["Einheit"]
    if not anlegen:
        return -1
    neu = k18.kw("uom.category", "create", [{"name": name}], context=SP)
    return neu[0] if isinstance(neu, list) else neu


def anlegewerte(k18, u: dict, kid: int) -> dict:
    """Anlagewerte so, dass die Odoo-18-Regel 'Referenzeinheit hat Faktor 1' eingehalten wird.

    Fuehrt die Zielkategorie bereits eine Referenzeinheit, wird die neue Einheit als
    'bigger' mit Faktor 1.0 gefuehrt - genauso wie Odoo 18 es bei 'ITK Einheit' macht.
    """
    belegung = k18.kw("uom.uom", "search_read",
                      [[("category_id", "=", kid), ("uom_type", "=", "reference")], ["name"]],
                      context=SP)
    typ = u["uom_type"]
    faktor = u["factor"] or 1.0
    hinweis = ""
    if typ == "reference" and belegung:
        typ, faktor = "bigger", 1.0
        hinweis = ("Kategorie fuehrt bereits die Referenzeinheit %s -> neue Einheit als "
                   "'bigger' mit Faktor 1.0 (wie Odoo 18 bei 'ITK Einheit')"
                   % belegung[0]["name"])
    return {"name": u["name"], "category_id": kid, "uom_type": typ, "factor": faktor,
            "rounding": u["rounding"] or RUNDUNG_SONST, "active": True, "hinweis": hinweis}


def snap(k) -> list[dict]:
    return k.kw("uom.uom", "search_read", [[], ["name", "rounding", "factor", "uom_type",
                                               "category_id", "active"]], context=SP, order="id")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--trocken", action="store_true")
    a = p.parse_args()

    print("R1 Mengeneinheiten - Vorbereitung (%s)%s" % (a.instanz, " [Trockenlauf]" if a.trocken else ""))
    benutzt = o11_einheiten()
    print("Odoo 11: %d tatsaechlich verwendete Mengeneinheiten" % len(benutzt))
    for u in sorted(benutzt, key=lambda x: -x["zeilen"]):
        print("   %-22s Rundung %-7s Typ %-10s Zeilen %-5s Produkte %s"
              % (u["name"], u["rounding"], u["uom_type"], u["zeilen"], u["produkte"]))

    k18 = o18(a.instanz)
    vorher_units = snap(k18)
    vorher_prec = k18.kw("decimal.precision", "search_read", [[("name", "=", GENAUIGKEIT)],
                                                              ["digits"]], context=SP)[0]

    print()
    print("Odoo 18 (%s) vorher: %d Einheiten, Genauigkeit %s = %s"
          % (a.instanz, len(vorher_units), GENAUIGKEIT, vorher_prec["digits"]))
    namen18 = {u["name"]: u for u in vorher_units}
    vorhandene_namen = set(namen18)
    fehlend = []
    ziele = []
    for u in sorted(benutzt, key=lambda x: -x["zeilen"]):
        if u["name"] in vorhandene_namen:
            ziele.append({"o11_name": u["name"], "o11_rundung": u["rounding"],
                          "o18_id": namen18[u["name"]]["id"], "o18_rundung": namen18[u["name"]]["rounding"],
                          "massnahme": "vorhanden", "zeilen": u["zeilen"], "produkte": u["produkte"]})
        else:
            fehlend.append(u)
            ziele.append({"o11_name": u["name"], "o11_rundung": u["rounding"], "o18_id": None,
                          "o18_rundung": None, "massnahme": "anlegen", "zeilen": u["zeilen"],
                          "produkte": u["produkte"]})

    # doppelte Namen in Odoo 11 (z. B. "13 Gemeinden" zweimal) auf eine Odoo-18-Einheit abbilden
    gesehen = {}
    fehlend_eindeutig = []
    for u in fehlend:
        if u["name"] in gesehen:
            gesehen[u["name"]]["zeilen_summe"] = gesehen[u["name"]]["zeilen_summe"] + u["zeilen"]
            continue
        kopie = dict(u)
        kopie["zeilen_summe"] = u["zeilen"]
        gesehen[u["name"]] = kopie
        fehlend_eindeutig.append(kopie)

    print()
    print("Anzulegen in Odoo 18 (%d):" % len(fehlend_eindeutig))
    kat18 = kategorien(k18)
    for u in fehlend_eindeutig:
        ziel = EIGENE_KATEGORIE.get(u["name"], u["kategorie"])
        if ziel not in kat18:
            # Odoo-11-Kategorie ohne Entsprechung (z. B. "Unsorted/Imported Units") -> "Einheit",
            # ausser die Einheit braucht eine eigene Kategorie (GB -> "Datenmenge")
            ziel = ziel if u["name"] in EIGENE_KATEGORIE else "Einheit"
        print("   %-22s Kategorie Odoo 11 %-26s -> Odoo 18 %-12s%s | Rundung %s | Zeilen %d"
              % (u["name"], u["kategorie"], ziel,
                 " (neu)" if ziel not in kat18 else "",
                 u["rounding"], u["zeilen_summe"]))
    print()
    print("Rundung anzupassen (vorhandene Einheiten mit Odoo-11-Rundung 0,001):")
    for z in ziele:
        if z["massnahme"] == "vorhanden" and z["o11_rundung"] < z["o18_rundung"]:
            print("   %-22s Odoo 18 Rundung %s -> %s (Odoo 11 fuehrt %s)"
                  % (z["o11_name"], z["o18_rundung"], z["o11_rundung"], z["o11_rundung"]))

    if a.trocken:
        print()
        print("Trockenlauf: nichts geaendert.")
        return 0

    geaendert = []
    # 1. Dezimalgenauigkeit
    if vorher_prec["digits"] != GENAUIGKEIT_ZIEL:
        k18.kw("decimal.precision", "write", [[vorher_prec["id"]], {"digits": GENAUIGKEIT_ZIEL}],
               context=SP)
        geaendert.append("Dezimalgenauigkeit %s: %s -> %s"
                         % (GENAUIGKEIT, vorher_prec["digits"], GENAUIGKEIT_ZIEL))

    # 1b. Vorhandene Einheiten mit eigener Kategorie richtig einhaengen (z. B. GB)
    for u in benutzt:
        if u["name"] not in EIGENE_KATEGORIE:
            continue
        vorhanden = kategorien(k18)
        zielname = EIGENE_KATEGORIE[u["name"]]
        ist = k18.kw("uom.uom", "search_read", [[("name", "=", u["name"])],
                                                ["category_id", "uom_type", "factor"]], context=SP)
        if not ist:
            continue
        eintrag = ist[0]
        kid = vorhanden.get(zielname)
        if kid is None:
            neu_kat = k18.kw("uom.category", "create", [{"name": zielname}], context=SP)
            kid = neu_kat[0] if isinstance(neu_kat, list) else neu_kat
        if eintrag["category_id"] and eintrag["category_id"][0] != kid:
            k18.kw("uom.uom", "write", [[eintrag["id"]], {"category_id": kid,
                                                          "uom_type": "reference",
                                                          "factor": 1.0}], context=SP)
            geaendert.append("Einheit %s in Kategorie %s verschoben (Typ reference, Faktor 1.0)"
                             % (u["name"], zielname))

    # 2. Rundung vorhandener Haupteinheiten
    for z in ziele:
        if z["massnahme"] == "vorhanden" and z["o11_rundung"] < z["o18_rundung"]:
            k18.kw("uom.uom", "write", [[z["o18_id"]], {"rounding": z["o11_rundung"]}], context=SP)
            geaendert.append("Rundung %s: %s -> %s" % (z["o11_name"], z["o18_rundung"],
                                                       z["o11_rundung"]))

    # 3. Fehlende Einheiten anlegen
    for u in fehlend_eindeutig:
        kid = zielkategorie(k18, u)
        werte = anlegewerte(k18, u, kid)
        hinweis = werte.pop("hinweis")
        neu = k18.kw("uom.uom", "create", [werte], context=SP)
        uid = neu[0] if isinstance(neu, list) else neu
        kname = [c["name"] for c in k18.kw("uom.category", "search_read",
                                           [[("id", "=", kid)], ["name"]], context=SP)]
        geaendert.append("Einheit angelegt: %s (id %s, Kategorie %s, Typ %s, Faktor %s)%s"
                         % (u["name"], uid, kname[0] if kname else kid, werte["uom_type"],
                            werte["factor"], " - " + hinweis if hinweis else ""))
        for z in ziele:
            if z["o11_name"] == u["name"] and z["o18_id"] is None:
                z["o18_id"] = uid

    nachher_units = snap(k18)
    nachher_prec = k18.kw("decimal.precision", "search_read", [[("name", "=", GENAUIGKEIT)],
                                                               ["digits"]], context=SP)[0]

    print()
    print("Aenderungen in Odoo 18 (%s):" % a.instanz)
    for g in geaendert:
        print("   %s" % g)
    print()
    print("Kontrolle:")
    print("   Genauigkeit %s = %s" % (GENAUIGKEIT, nachher_prec["digits"]))
    unveraendert = True
    vorher_map = {u["id"]: u for u in vorher_units}
    for u in nachher_units:
        alt = vorher_map.get(u["id"])
        absichtlich = ("Einheit(en)", "ITK Einheit") + tuple(EIGENE_KATEGORIE)
        if alt and alt != u and u["name"] not in absichtlich:
            unveraendert = False
            print("   HINWEIS: bestehende Einheit geaendert: %s" % u["name"])
    print("   Andere bestehende Einheiten unveraendert: %s" % unveraendert)
    print("   Einheiten gesamt: %d -> %d" % (len(vorher_units), len(nachher_units)))
    for z in ziele:
        print("   %-22s -> Odoo-18-Einheit id %-5s (%s)"
              % (z["o11_name"], z["o18_id"], z["massnahme"]))

    pfad = os.path.join(REPO, "docs", "_verkauf_r1_mengeneinheiten_%s.json" % a.instanz)
    with open(pfad, "w", encoding="utf-8") as fh:
        json.dump({"instanz": a.instanz, "genauigkeit_vorher": vorher_prec["digits"],
                   "genauigkeit_nachher": nachher_prec["digits"], "aenderungen": geaendert,
                   "zuordnung": ziele}, fh, ensure_ascii=False, indent=1)
    print("   Rohdaten: %s" % pfad)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
