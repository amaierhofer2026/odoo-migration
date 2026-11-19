# -*- coding: utf-8 -*-
"""Valorisierung: Rechte-Altbestand bereinigen (Session 148).

Entfernt Access-Regeln auf ``itk_valorisierung.valorisierung``, die **keiner Gruppe**
zugeordnet sind und **keine Modul-XML-ID** besitzen. Solche Regeln entstehen nicht aus
dem Repository (die CSV fuehrt nur die zwei Gruppenregeln), sondern sind Altbestand aus
einer frueheren Einrichtung - und sie hebeln jede Gruppenregel aus, weil Odoo Rechte
verknuepft (ODER).

Trockenlauf ist Standard; geschrieben wird nur mit ``--ausfuehren --ich-habe-freigabe``.
Das Skript ist idempotent: ein zweiter Lauf findet nichts mehr zu tun.

Aufruf:
    python scripts/migration/valorisierung_rechte_bereinigen.py --instanz vm
    python scripts/migration/valorisierung_rechte_bereinigen.py --instanz vm \\
        --ausfuehren --ich-habe-freigabe
"""
from __future__ import annotations

import argparse
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

CTX = {"lang": "de_DE"}
MODELL = "itk_valorisierung.valorisierung"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    args = ap.parse_args()
    if args.ausfuehren and not args.ich_habe_freigabe:
        print("ABBRUCH: Schreiblauf nur mit --ich-habe-freigabe (Freigabe von Anna).")
        return 2

    o18 = client.o18(args.instanz)
    print("=== Rechtebereinigung Valorisierung (%s) | %s ==="
          % (args.instanz, "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF"))

    regeln = o18.kw("ir.model.access", "search_read",
                    [[["model_id.model", "=", MODELL]],
                     ["id", "name", "group_id", "perm_read", "perm_write", "perm_create",
                      "perm_unlink"]], context=CTX, order="id")
    xmlids = {}
    for x in o18.kw("ir.model.data", "search_read",
                    [[["model", "=", "ir.model.access"]], ["res_id", "module", "name"]],
                    limit=100000):
        xmlids[x["res_id"]] = "%s.%s" % (x["module"], x["name"])

    verdacht, behalten = [], []
    for r in regeln:
        ohne_gruppe = not r["group_id"]
        ohne_xmlid = r["id"] not in xmlids
        (verdacht if (ohne_gruppe and ohne_xmlid) else behalten).append(r)

    print("\nBestehende Regeln: %d" % len(regeln))
    for r in behalten:
        print("  bleibt : %3d  %-45s Gruppe %-28s R/W/C/D %d%d%d%d  %s"
              % (r["id"], r["name"], (r["group_id"][1] if r["group_id"] else "-"),
                 r["perm_read"], r["perm_write"], r["perm_create"], r["perm_unlink"],
                 xmlids.get(r["id"], "(ohne XML-ID, aber mit Gruppe)")))
    for r in verdacht:
        print("  entfernen: %3d  %-42s ohne Gruppe, ohne XML-ID, R/W/C/D %d%d%d%d"
              % (r["id"], r["name"], r["perm_read"], r["perm_write"], r["perm_create"],
                 r["perm_unlink"]))

    if not verdacht:
        print("\nNichts zu tun - keine Regel ohne Gruppe und XML-ID vorhanden.")
    elif args.ausfuehren:
        o18.kw("ir.model.access", "unlink", [[r["id"] for r in verdacht]])
        print("\n%d Regel(n) entfernt." % len(verdacht))

    pruefen = o18.kw("ir.model.access", "search_read",
                     [[["model_id.model", "=", MODELL]],
                      ["id", "name", "group_id", "perm_read", "perm_write", "perm_create",
                       "perm_unlink"]], context=CTX, order="id")
    print("\nRegeln danach: %d" % len(pruefen))
    for r in pruefen:
        print("  %3d  %-45s Gruppe %-28s R/W/C/D %d%d%d%d"
              % (r["id"], r["name"], (r["group_id"][1] if r["group_id"] else "-"),
                 r["perm_read"], r["perm_write"], r["perm_create"], r["perm_unlink"]))
    offen = [r for r in pruefen if not r["group_id"]]
    print("\nErgebnis: %d Regel(n) ohne Gruppe verbleiben (Soll: 0)" % len(offen))
    return 0 if (not offen and not verdacht) or args.ausfuehren else 1


if __name__ == "__main__":
    sys.exit(main())
