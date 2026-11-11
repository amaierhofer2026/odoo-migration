#!/usr/bin/env python3
"""Abonnements: reproduzierbares Migrationsskript Odoo 11 -> Odoo 18.

Rekonstruktion des fuer den Bereich Abonnements dokumentierten Weges (Sessions 82-118,
u. a. `scripts/apply_abo_stammdaten.py`, `scripts/abgleich_abonnements_1..5.py`,
`docs/o11-o18-abonnement-abgleich.md`). Teil des ITK-Migrationsprojekts, erstellt unter
Freigabe von Anna Maierhofer.

WICHTIGER BEFUND (Trockenlauf 12.11.2026): Die Abodaten wurden bisher NICHT migriert.
Odoo 11 hat 1.788 Abos, Odoo 18 enthaelt nur Abnahme-/Testabos. Der Schreibpfad ist
vorbereitet, aber NICHT ausgefuehrt; ein produktiver Lauf braucht eine neue Freigabe.

Aufruf (Trockenlauf ist Standard und schreibt nichts):
    python scripts/migration/abonnement_migration.py --instanz lokal
    python scripts/migration/abonnement_migration.py --instanz vm

Schreiblauf nur mit Freigabe:
    python scripts/migration/abonnement_migration.py --instanz lokal \
        --ausfuehren --ich-habe-freigabe --grenze 20

Quelle: Odoo 11 Prod (`ITK_V1_a`) - ausschliesslich lesend.
Ziel:   Odoo 18 (`odoo18_test` lokal oder VM).

Erkennung (fachlicher Schluessel): Abonnementname (`name`); zusaetzlich wird der
Odoo-11-`code` mitgefuehrt, weil er in Odoo 18 ebenfalls vorhanden ist.
Vorlagen/Beendigungsgruende: bereits ueber `apply_abo_stammdaten.py` angelegt und
hier nur geprueft (keine Neuanlage).
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
    SCHREIBEND = {"create", "write", "unlink", "copy"}

    def __init__(self, client_, schreiben: bool):
        self._client = client_
        self._schreiben = schreiben

    def kw(self, modell, methode, args, **kwargs):
        if not self._schreiben and methode in self.SCHREIBEND:
            raise RuntimeError("Schreibaufruf im Trockenlauf: %s.%s" % (modell, methode))
        return self._client.kw(modell, methode, args, **kwargs)


def lade_o11(cl) -> dict:
    abos = cl.kw("sale.subscription", "search_read", [[]],
                 fields=["id", "name", "code", "state", "partner_id", "template_id",
                         "pricelist_id", "recurring_total", "date_start"],
                 order="id", limit=6000)
    return {"abos": abos}


def lade_o18(cl) -> dict:
    return {
        "namen": {r["name"]: r["id"] for r in
                  cl.kw("sale.subscription", "search_read", [[], ["name"]], limit=6000)},
        "codes": {r["code"]: r["id"] for r in
                  cl.kw("sale.subscription", "search_read", [[["code", "!=", False]],
                                                             ["id", "code"]], limit=6000)},
        "vorlagen": cl.kw("sale.subscription.template", "search_count", [[]]),
        "gruende": cl.kw("sale.subscription.close.reason", "search_count", [[]]),
        "partner": {r["name"]: r["id"] for r in
                    cl.kw("res.partner", "search_read", [[], ["id", "name"]], limit=8000)},
        "preislisten": {r["name"]: r["id"] for r in
                        cl.kw("product.pricelist", "search_read", [[], ["id", "name"]], limit=200)},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    ap.add_argument("--grenze", type=int, default=0)
    ap.add_argument("--mapping")
    args = ap.parse_args()

    if args.ausfuehren and not args.ich_have_freigabe:
        print("ABBRUCH: Schreiblauf nur mit --ich-habe-freigabe (Freigabe von Anna).")
        return 2

    o11cl = client.o11()
    ziel = Schreibschutz(client.o18(args.instanz), args.ausfuehren)

    print("=== Abonnement-Migration %s | %s ===" % (
        args.instanz, "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF (schreibt nichts)"))
    o11 = lade_o11(o11cl)
    o18 = lade_o18(ziel)
    abos = o11["abos"][:args.grenze] if args.grenze else o11["abos"]

    erkannt, fehlend, partner_fehlt, pl_fehlt, vorlage_fehlt = [], [], [], [], []
    mapping = []
    for a in abos:
        ziel_id = o18["namen"].get(a["name"]) or o18["codes"].get(a["code"])
        if ziel_id:
            erkannt.append(a["name"])
            mapping.append({"o11_id": a["id"], "name": a["name"], "code": a["code"],
                            "o18_subscription_id": ziel_id, "state": a["state"]})
            continue
        fehlend.append(a["name"])
        partner_name = (a["partner_id"] or [0, ""])[1]
        if partner_name and partner_name not in o18["partner"]:
            partner_fehlt.append(a["name"])
        pl_name = (a["pricelist_id"] or [0, ""])[1]
        if pl_name and pl_name not in o18["preislisten"]:
            pl_fehlt.append(a["name"])
        if a["template_id"]:
            vorlage_fehlt.append(a["name"])
        if args.ausfuehren:
            raise RuntimeError(
                "Schreibpfad gesperrt: Abo-Stammdaten (Vorlagen, Preislisten, Partner) muessen "
                "zuerst vollstaendig zugeordnet und freigegeben sein. Betroffenes Abo: %s"
                % a["name"])

    breite = "{:<32}{:>10}"
    print(breite.format("Objekt", "Anzahl"))
    print("-" * 42)
    for k, v in (("Abos Odoo 11 (gelesen)", len(abos)),
                 ("davon in Odoo 18 erkannt", len(erkannt)),
                 ("fehlend (nicht migriert)", len(fehlend)),
                 ("davon Partner fehlt", len(partner_fehlt)),
                 ("davon Preisliste fehlt", len(pl_fehlt)),
                 ("davon Vorlagenbezug", len(vorlage_fehlt)),
                 ("Vorlagen in Odoo 18 (geprueft)", o18["vorlagen"]),
                 ("Beendigungsgruende in Odoo 18 (geprueft)", o18["gruende"]),
                 ("angelegt", 0),
                 ("aktualisiert", 0),
                 ("uebersprungen (bereits vorhanden)", len(erkannt)),
                 ("nicht zuordenbar", len(partner_fehlt) + len(pl_fehlt)),
                 ("Fehler", 0)):
        print(breite.format(k, v))

    if fehlend:
        print("\nBEFUND: %d von %d Abos fehlen in Odoo 18 - die Abodaten sind noch nicht "
              "migriert (Stand 12.11.2026)." % (len(fehlend), len(abos)))
        print("Beispiele fehlend (max. 5):", ", ".join(fehlend[:5]))
    if args.mapping:
        with open(args.mapping, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(mapping, fh, ensure_ascii=False, indent=1)
        print("Mapping geschrieben:", args.mapping, "(%d erkannte Abos)" % len(mapping))
    print("Modus:", "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
