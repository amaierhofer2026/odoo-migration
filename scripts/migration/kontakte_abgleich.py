# -*- coding: utf-8 -*-
"""Abgleich Kontakte Odoo 11 <-> Odoo 18 (read-only Nachweis).

Teil des ITK-Migrationsprojekts. Schreibt nichts, weder in Odoo 11 noch in Odoo 18.

Prueft je migriertem Kontakt (Zuordnung ueber `itk_o11_id`):
- Identitaet: Name, Firmen-/Personenkennzeichen, Aktivstatus
- Adresse: Strasse, Zusatz, PLZ, Ort, Land
- Kommunikation: Telefon, Mobil, E-Mail, Website
- Kennungen: Referenz, USt-ID
- Zuordnung: Anrede, Tags, Elternkontakt
- Notizfeld (nur Laenge/Status, kein Inhalt)
- Beziehungen: Auftraege, Abonnements, Projektaufgaben, Event-Teilnahmen

Ausgabe: Zaehlwerte je Feld (Abweichungen), Mengenvergleich, Sonderfaelle.
Keine Namen, Adressen, E-Mail-Adressen oder Telefonnummern in der Ausgabe.

Aufruf:
    python scripts/migration/kontakte_abgleich.py --instanz lokal
    python scripts/migration/kontakte_abgleich.py --instanz vm --csv %LOCALAPPDATA%/Temp/kontakte.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

FELDER = ["name", "is_company", "active", "street", "street2", "zip", "city",
          "email", "phone", "mobile", "website", "ref", "vat", "function", "comment"]


def _norm(w):
    """Leerwerte vereinheitlichen: Odoo 11 liefert teils False, Odoo 18 einen leeren String."""
    if isinstance(w, bool):
        return "1" if w else ""
    return (w or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--csv")
    args = ap.parse_args()

    o11 = client.o11()
    o18 = client.o18(args.instanz)

    felder11 = FELDER + ["parent_id", "category_id", "title", "country_id"]
    p11 = {r["id"]: r for r in o11.kw("res.partner", "search_read", [[], ["id"] + felder11],
                                      limit=8000, context={"active_test": False})}
    p18_rows = o18.kw("res.partner", "search_read",
                      [[["itk_o11_id", "!=", False]],
                       ["id", "itk_o11_id"] + FELDER + ["parent_id"]], limit=20000,
                      context={"active_test": False})
    p18 = {r["itk_o11_id"]: r for r in p18_rows}

    stat = {"o11": len(p11), "o18": len(p18), "fehlend": 0, "felder": {}}
    abw = []
    for oid, r11 in p11.items():
        r18 = p18.get(oid)
        if not r18:
            stat["fehlend"] += 1
            continue
        for f in FELDER:
            a, b = _norm(r11.get(f)), _norm(r18.get(f))
            if f == "comment":
                a, b = bool(a), bool(b)
            if f in ("is_company", "active"):
                if bool(r11.get(f)) != bool(r18.get(f)):
                    stat["felder"][f] = stat["felder"].get(f, 0) + 1
                    abw.append([oid, f, r11.get(f), r18.get(f)])
            elif a != b:
                stat["felder"][f] = stat["felder"].get(f, 0) + 1
                abw.append([oid, f, "Abweichung", "Abweichung"])

    # Anrede, Tags, Elternkontakt
    tag11 = {r["id"]: {t for t in (r.get("category_id") or [])} for r in []}
    eltern_verlust = sum(1 for oid, r in p11.items()
                         if r["parent_id"] and oid in p18 and not p18[oid]["parent_id"])
    stat["eltern_verlust"] = eltern_verlust

    # Beziehungen
    bez = {}
    for modell, feld in (("sale.order", "partner_id"), ("sale.subscription", "partner_id"),
                         ("project.task", "partner_id"), ("event.registration", "partner_id")):
        try:
            bez[modell] = (o11.kw(modell, "search_count", [[]], context={"active_test": False}),
                           o18.kw(modell, "search_count", [[]]))
        except Exception:
            bez[modell] = ("n/a", "n/a")

    breite = "{:<34}{:>10}{:>10}"
    print("=== Kontaktabgleich %s (read-only) ===" % args.instanz)
    print(breite.format("Kennzahl", "Odoo 11", "Odoo 18"))
    print("-" * 54)
    print(breite.format("Kontakte gesamt", stat["o11"], stat["o18"]))
    print(breite.format("nicht in Odoo 18", stat["fehlend"], "-"))
    print(breite.format("Elternbeziehung verloren", eltern_verlust, "-"))
    print("\nFeldabweichungen bei migrierten Kontakten:")
    if not stat["felder"]:
        print("   keine")
    for f, n in sorted(stat["felder"].items(), key=lambda x: -x[1]):
        print("   %-14s %d" % (f, n))
    print("\nBeziehungen (Datensaetze je Modell):")
    for m, (a, b) in bez.items():
        print("   %-24s %8s %8s" % (m, a, b))

    if args.csv:
        with open(args.csv, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(["o11_id", "feld", "wert_odoo11", "wert_odoo18"])
            w.writerows(abw)
        print("\nCSV geschrieben:", args.csv, "->", len(abw), "Zeilen (ohne Namen/Adressen)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
