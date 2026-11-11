#!/usr/bin/env python3
"""Verkauf: reproduzierbares Migrationsskript Odoo 11 -> Odoo 18.

Rekonstruktion des fuer den Bereich Verkauf dokumentierten Weges (Sessions 120-124,
Doku `docs/o11-o18-verkauf-migrationscheck*.md`). Das Skript ist Teil des
ITK-Migrationsprojekts und wurde unter Freigabe von Anna Maierhofer erstellt.

WICHTIGER BEFUND (Trockenlauf 12.11.2026): Die Auftragsdaten wurden bisher NICHT
migriert. Odoo 11 hat 2.514 Auftraege, Odoo 18 enthaelt nur Abnahme-/Testauftraege.
Der Schreibpfad ist deshalb vorbereitet, aber NICHT ausgefuehrt; ein produktiver
Lauf braucht eine neue Freigabe.

Aufruf (Trockenlauf ist Standard und schreibt nichts):
    python scripts/migration/verkauf_migration.py --instanz lokal
    python scripts/migration/verkauf_migration.py --instanz vm

Schreiblauf nur mit Freigabe:
    python scripts/migration/verkauf_migration.py --instanz lokal \
        --ausfuehren --ich-habe-freigabe --grenze 50

Quelle: Odoo 11 Prod (`ITK_V1_a`) - ausschliesslich lesend.
Ziel:   Odoo 18 (`odoo18_test` lokal oder VM).

Erkennung (fachlicher Schluessel): Auftragsname (`name`). Odoo-11-IDs werden nicht als
Bruecke benutzt. Zeilen werden ueber Produkt (`default_code`, sonst Name) und Menge
zugeordnet; Kunden ueber die Odoo-11-Partner-id nur zur Anzeige, im Ziel ueber den Namen.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402


class Schreibschutz:
    """Bricht jeden Schreibaufruf im Trockenlauf ab."""

    SCHREIBEND = {"create", "write", "unlink", "copy"}

    def __init__(self, client_, schreiben: bool):
        self._client = client_
        self._schreiben = schreiben

    def kw(self, modell, methode, args, **kwargs):
        if not self._schreiben and methode in self.SCHREIBEND:
            raise RuntimeError("Schreibaufruf im Trockenlauf: %s.%s" % (modell, methode))
        return self._client.kw(modell, methode, args, **kwargs)


def lade_o11(cl) -> dict:
    auftraege = cl.kw("sale.order", "search_read", [[]],
                      fields=["id", "name", "state", "partner_id", "date_order",
                              "amount_untaxed", "amount_total", "currency_id"],
                      order="id", limit=6000)
    zeilen = cl.kw("sale.order.line", "search_read", [[]],
                   fields=["order_id", "product_id", "name", "product_uom_qty",
                           "price_unit", "price_subtotal"],
                   order="id", limit=20000)
    return {"auftraege": auftraege, "zeilen": zeilen}


def lade_o18(cl) -> dict:
    return {
        "namen": {r["name"]: r["id"] for r in
                  cl.kw("sale.order", "search_read", [[], ["name"]], limit=6000)},
        "produkte": {r["default_code"]: r["id"] for r in
                     cl.kw("product.product", "search_read", [[["default_code", "!=", False]],
                                                              ["id", "default_code"]], limit=6000)},
        "partner": {r["name"]: r["id"] for r in
                    cl.kw("res.partner", "search_read", [[], ["id", "name"]], limit=8000)},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    ap.add_argument("--grenze", type=int, default=0, help="nur die ersten N Auftraege bearbeiten")
    ap.add_argument("--mapping", help="Zuordnung Odoo-11-Auftrag -> Odoo-18-id als JSON")
    args = ap.parse_args()

    if args.ausfuehren and not args.ich_have_freigabe:
        print("ABBRUCH: Schreiblauf nur mit --ich-habe-freigabe (Freigabe von Anna).")
        return 2

    o11cl = client.o11()
    ziel = Schreibschutz(client.o18(args.instanz), args.ausfuehren)

    print("=== Verkauf-Migration %s | %s ===" % (
        args.instanz, "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF (schreibt nichts)"))
    o11 = lade_o11(o11cl)
    o18 = lade_o18(ziel)
    auftraege = o11["auftraege"][:args.grenze] if args.grenze else o11["auftraege"]
    zeilen_je_auftrag = {}
    for z in o11["zeilen"]:
        if z["order_id"]:
            zeilen_je_auftrag.setdefault(z["order_id"][0], []).append(z)

    erkannt, fehlend, partner_fehlt, produkt_fehlt, zeilen_summe = [], [], [], [], 0
    mapping = []
    for a in auftraege:
        ziel_id = o18["namen"].get(a["name"])
        if ziel_id:
            erkannt.append(a["name"])
            mapping.append({"o11_id": a["id"], "o11_name": a["name"], "o18_order_id": ziel_id,
                            "state": a["state"], "zeilen": len(zeilen_je_auftrag.get(a["id"], []))})
            continue
        fehlend.append(a["name"])
        partner_name = (a["partner_id"] or [0, ""])[1]
        if partner_name and partner_name not in o18["partner"]:
            partner_fehlt.append(a["name"])
        for z in zeilen_je_auftrag.get(a["id"], []):
            zeilen_summe += 1
            code = (z["product_id"] or [0, ""])[1]
            if code and code not in o18["produkte"]:
                produkt_fehlt.append(a["name"])
                break
        if args.ausfuehren:
            # Schreibpfad ist bewusst NICHT implementiert, solange die Stammdaten
            # (Kunden/Produkte) nicht vollstaendig zugeordnet sind - sonst entstehen
            # Auftraege ohne belastbare Zeilen. Ein Teilimport waere fachlich falsch.
            raise RuntimeError(
                "Schreibpfad gesperrt: erst Stammdatenzuordnung (Kunden/Produkte) pruefen "
                "und von Anna freigeben lassen. Betroffener Auftrag: %s" % a["name"])

    breite = "{:<26}{:>10}"
    print(breite.format("Objekt", "Anzahl"))
    print("-" * 36)
    for k, v in (("Auftraege Odoo 11 (gelesen)", len(auftraege)),
                 ("davon in Odoo 18 erkannt", len(erkannt)),
                 ("fehlend (nicht migriert)", len(fehlend)),
                 ("davon Kunde fehlt", len(partner_fehlt)),
                 ("davon Produkt fehlt", len(produkt_fehlt)),
                 ("Zeilen der fehlenden Auftraege", zeilen_summe),
                 ("angelegt", 0 if not args.ausfuehren else 0),
                 ("aktualisiert", 0),
                 ("uebersprungen (bereits vorhanden)", len(erkannt)),
                 ("nicht zuordenbar", len(partner_fehlt) + len(produkt_fehlt)),
                 ("Fehler", 0)):
        print(breite.format(k, v))

    if fehlend:
        print("\nBEFUND: %d von %d Auftraegen fehlen in Odoo 18 - die Auftragsdaten sind "
              "noch nicht migriert (Stand 12.11.2026)." % (len(fehlend), len(auftraege)))
        print("Beispiele fehlend (max. 5):", ", ".join(fehlend[:5]))
    if args.mapping:
        with open(args.mapping, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(mapping, fh, ensure_ascii=False, indent=1)
        print("Mapping geschrieben:", args.mapping, "(%d erkannte Auftraege)" % len(mapping))
    print("Modus:", "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
