#!/usr/bin/env python3
"""Read-only Zuordnungsbericht: Stammdaten-Abhaengigkeiten fuer Verkauf und Abonnements.

Teil des ITK-Migrationsprojekts (Odoo 11 -> Odoo 18). Schreibt NICHTS, weder in Odoo 11
noch in Odoo 18.

Zweck: Ermitteln, welche Kunden, Produkte, Preislisten, Vorlagen und sonstigen Relationen
die 2.514 Auftraege und 1.788 Abos aus Odoo 11 brauchen und welche davon in Odoo 18
bereits eindeutig vorhanden sind.

Datenschutz: In der Konsole und in der Doku erscheinen NUR Zaehlwerte, Odoo-IDs und
technische Schluessel (default_code, ref-Kennung, Steuernummer). Namen von Personen oder
Firmen werden nicht ausgegeben. Der optionale CSV-Report enthaelt ebenfalls keine Namen,
nur IDs und Status - und gehoert nicht ins Repository (Ziel ausserhalb des Repos waehlen).

Aufruf:
    python scripts/migration/verkauf_abo_stammdaten_abgleich.py --instanz lokal
    python scripts/migration/verkauf_abo_stammdaten_abgleich.py --instanz lokal \
        --csv "%LOCALAPPDATA%/Temp/stammdaten_abgleich.csv"
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402


class Schreibschutz:
    """Liest nur - jeder Schreibaufruf ist ein Programmierfehler."""

    def __init__(self, client_):
        self._client = client_

    def kw(self, modell, methode, args, **kwargs):
        if methode in ("create", "write", "unlink", "copy"):
            raise RuntimeError("Schreibaufruf in einem read-only Werkzeug: %s.%s"
                               % (modell, methode))
        return self._client.kw(modell, methode, args, **kwargs)


def _norm(s):
    return (s or "").strip().lower()


def lade_benoetigt(o11) -> dict:
    """Welche Relationen brauchen Auftraege und Abos aus Odoo 11?"""
    auftraege = o11.kw("sale.order", "search_read", [[]],
                       fields=["id", "partner_id", "pricelist_id", "state"], limit=6000)
    zeilen = o11.kw("sale.order.line", "search_read", [[]],
                    fields=["order_id", "product_id"], limit=20000)
    abos = o11.kw("sale.subscription", "search_read", [[]],
                  fields=["id", "partner_id", "pricelist_id", "template_id", "state"], limit=6000)
    # Abo-Zeilen: in Odoo 11 haengen sie am analytischen Konto, nicht am Abo
    abo_produkte = []
    try:
        abo_zeilen = o11.kw("sale.subscription.line", "search_read", [[]],
                            fields=["analytic_account_id", "product_id"], limit=20000)
        abo_produkte = abo_zeilen
    except Exception:
        abo_zeilen = []

    partner = set()
    for a in auftraege:
        if a["partner_id"]:
            partner.add(a["partner_id"][0])
    for a in abos:
        if a["partner_id"]:
            partner.add(a["partner_id"][0])
    produkte = {z["product_id"][0] for z in zeilen if z["product_id"]}
    produkte |= {z["product_id"][0] for z in abo_produkte if z.get("product_id")}
    preislisten = set()
    for a in auftraege:
        if a["pricelist_id"]:
            preislisten.add(a["pricelist_id"][0])
    for a in abos:
        if a["pricelist_id"]:
            preislisten.add(a["pricelist_id"][0])
    vorlagen = {a["template_id"][0] for a in abos if a["template_id"]}
    return {"auftraege": auftraege, "zeilen": zeilen, "abos": abos,
            "abo_zeilen": abo_zeilen, "partner": partner, "produkte": produkte,
            "preislisten": preislisten, "vorlagen": vorlagen}


def lade_o18(o18) -> dict:
    """Index fuer die eindeutige Zuordnung (nur eindeutige Schluessel)."""
    partner_ref, partner_vat, partner_mail, partner_name = {}, {}, {}, {}
    for p in o18.kw("res.partner", "search_read", [[]],
                    fields=["id", "ref", "vat", "email"], limit=20000):
        if p["ref"]:
            partner_ref.setdefault(_norm(p["ref"]), []).append(p["id"])
        if p["vat"]:
            partner_vat.setdefault(_norm(p["vat"]).replace(" ", ""), []).append(p["id"])
        if p["email"]:
            partner_mail.setdefault(_norm(p["email"]), []).append(p["id"])
    produkte_code, produkte_name = {}, {}
    for pr in o18.kw("product.product", "search_read", [[]],
                     fields=["id", "default_code", "name"], limit=20000):
        if pr["default_code"]:
            produkte_code.setdefault(_norm(pr["default_code"]), []).append(pr["id"])
    preislisten = {}
    for pl in o18.kw("product.pricelist", "search_read", [[]], fields=["id", "name"], limit=500):
        preislisten.setdefault(_norm(pl["name"]), []).append(pl["id"])
    vorlagen = {}
    try:
        for v in o18.kw("sale.subscription.template", "search_read", [[]],
                        fields=["id", "name"], limit=500):
            vorlagen.setdefault(_norm(v["name"]), []).append(v["id"])
    except Exception:
        pass
    return {"ref": partner_ref, "vat": partner_vat, "mail": partner_mail,
            "produkte_code": produkte_code, "preislisten": preislisten, "vorlagen": vorlagen}


def ordne_partner(ids, o11, index) -> dict:
    """Eindeutige Zuordnung je Partner: ref -> vat -> email. Kein Raten ueber Namen."""
    erg = {"eindeutig": [], "mehrdeutig": [], "fehlend": [], "ohne_schluessel": []}
    ids = sorted(ids)
    for i in range(0, len(ids), 200):
        block = ids[i:i + 200]
        for p in o11.kw("res.partner", "read", [block, ["id", "ref", "vat", "email", "is_company"]]):
            treffer = None
            for quelle, wert in (("ref", p["ref"]), ("vat", p["vat"]), ("email", p["email"])):
                if not wert:
                    continue
                schluessel = _norm(wert)
                if quelle == "vat":
                    schluessel = schluessel.replace(" ", "")
                feld = "mail" if quelle == "email" else quelle
                kandidaten = index[feld].get(schluessel, [])
                if len(kandidaten) == 1:
                    treffer = (quelle, kandidaten[0])
                    break
                if len(kandidaten) > 1:
                    erg["mehrdeutig"].append({"o11_id": p["id"], "schluessel": quelle,
                                              "anzahl": len(kandidaten)})
                    treffer = "mehrdeutig"
                    break
            if treffer is None:
                hat_schluessel = bool(p["ref"] or p["vat"] or p["email"])
                erg["ohne_schluessel" if not hat_schluessel else "fehlend"].append(
                    {"o11_id": p["id"], "is_company": p["is_company"],
                     "ref": bool(p["ref"]), "vat": bool(p["vat"]), "mail": bool(p["email"])})
            elif treffer != "mehrdeutig":
                erg["eindeutig"].append({"o11_id": p["id"], "o18_id": treffer[1],
                                         "schluessel": treffer[0]})
    return erg


def ordne_produkte(ids, o11, index) -> dict:
    erg = {"eindeutig": [], "mehrdeutig": [], "fehlend": []}
    ids = sorted(ids)
    for i in range(0, len(ids), 200):
        for p in o11.kw("product.product", "read", [ids[i:i + 200], ["id", "default_code"]]):
            code = _norm(p["default_code"])
            if not code:
                erg["fehlend"].append({"o11_id": p["id"], "grund": "ohne default_code"})
                continue
            kandidaten = index["produkte_code"].get(code, [])
            if len(kandidaten) == 1:
                erg["eindeutig"].append({"o11_id": p["id"], "o18_id": kandidaten[0],
                                         "code": p["default_code"]})
            elif len(kandidaten) > 1:
                erg["mehrdeutig"].append({"o11_id": p["id"], "code": p["default_code"],
                                          "anzahl": len(kandidaten)})
            else:
                erg["fehlend"].append({"o11_id": p["id"], "code": p["default_code"]})
    return erg


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--csv", help="Report ausserhalb des Repos ablegen")
    args = ap.parse_args()

    o11 = Schreibschutz(client.o11())
    o18 = Schreibschutz(client.o18(args.instanz))

    b = lade_benoetigt(o11)
    idx = lade_o18(o18)

    print("=== Stammdaten-Abgleich Verkauf/Abonnements (%s, read-only) ===" % args.instanz)
    print("Auftraege: %d | Zeilen: %d | Abos: %d | Abo-Zeilen: %d"
          % (len(b["auftraege"]), len(b["zeilen"]), len(b["abos"]), len(b["abo_zeilen"])))
    print("Benoetigt: %d Partner, %d Produkte, %d Preislisten, %d Abo-Vorlagen"
          % (len(b["partner"]), len(b["produkte"]), len(b["preislisten"]), len(b["vorlagen"])))

    partner = ordne_partner(b["partner"], o11, idx)
    produkte = ordne_produkte(b["produkte"], o11, idx)
    pl_eindeutig, pl_mehrdeutig, pl_fehlend = [], [], []
    for pl_id in sorted(b["preislisten"]):
        ohne = Schreibschutz(client.o11())
        rec = ohne.kw("product.pricelist", "read", [[pl_id], ["id", "name"]])[0]
        kandidaten = idx["preislisten"].get(_norm(rec["name"]), [])
        if len(kandidaten) == 1:
            pl_eindeutig.append({"o11_id": pl_id, "o18_id": kandidaten[0]})
        elif len(kandidaten) > 1:
            pl_mehrdeutig.append({"o11_id": pl_id, "anzahl": len(kandidaten)})
        else:
            pl_fehlend.append({"o11_id": pl_id})
    vor_eindeutig, vor_mehrdeutig, vor_fehlend = [], [], []
    if b["vorlagen"]:
        for rec in o11.kw("sale.subscription.template", "read",
                          [sorted(b["vorlagen"]), ["id", "name"]]):
            kandidaten = idx["vorlagen"].get(_norm(rec["name"]), [])
            if len(kandidaten) == 1:
                vor_eindeutig.append({"o11_id": rec["id"], "o18_id": kandidaten[0]})
            elif len(kandidaten) > 1:
                vor_mehrdeutig.append({"o11_id": rec["id"], "anzahl": len(kandidaten)})
            else:
                vor_fehlend.append({"o11_id": rec["id"]})

    print("\n%-24s%10s%12s%12s%12s" % ("Objekt", "benoetigt", "eindeutig", "mehrdeutig", "fehlend"))
    print("-" * 70)
    for name, d, g in (("Partner", partner, len(b["partner"])),
                       ("Produkte", produkte, len(b["produkte"]))):
        print("%-24s%10d%12d%12d%12d" % (name, g, len(d["eindeutig"]), len(d["mehrdeutig"]),
                                         len(d["fehlend"])))
    print("%-24s%10d%12d%12d%12d" % ("Preislisten", len(b["preislisten"]), len(pl_eindeutig),
                                     len(pl_mehrdeutig), len(pl_fehlend)))
    print("%-24s%10d%12d%12d%12d" % ("Abo-Vorlagen", len(b["vorlagen"]), len(vor_eindeutig),
                                     len(vor_mehrdeutig), len(vor_fehlend)))
    print("%-24s%10d" % ("Partner ohne jeden Schluessel", len(partner["ohne_schluessel"])))

    if partner["mehrdeutig"]:
        print("\nMehrdeutige Partner (Schluessel mehrfach in Odoo 18): %d" % len(partner["mehrdeutig"]))
        for m in partner["mehrdeutig"][:5]:
            print("   o11_id %s ueber %s -> %d Treffer" % (m["o11_id"], m["schluessel"], m["anzahl"]))
    if produkte["mehrdeutig"]:
        print("\nMehrdeutige Produkte: %d" % len(produkte["mehrdeutig"]))
        for m in produkte["mehrdeutig"][:5]:
            print("   o11_id %s code %s -> %d Treffer" % (m["o11_id"], m["code"], m["anzahl"]))

    if args.csv:
        zeilen = []
        for e in partner["eindeutig"]:
            zeilen.append(["partner", e["o11_id"], e["o18_id"], e["schluessel"], "eindeutig"])
        for e in partner["mehrdeutig"]:
            zeilen.append(["partner", e["o11_id"], "", e["schluessel"], "mehrdeutig:%d" % e["anzahl"]])
        for e in partner["fehlend"]:
            zeilen.append(["partner", e["o11_id"], "", "", "fehlt"])
        for e in partner["ohne_schluessel"]:
            zeilen.append(["partner", e["o11_id"], "", "", "ohne_schluessel"])
        for e in produkte["eindeutig"]:
            zeilen.append(["produkt", e["o11_id"], e["o18_id"], e.get("code", ""), "eindeutig"])
        for e in produkte["fehlend"]:
            zeilen.append(["produkt", e["o11_id"], "", e.get("code", ""), e.get("grund", "fehlt")])
        with open(args.csv, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(["objekt", "o11_id", "o18_id", "schluessel", "status"])
            w.writerows(zeilen)
        print("\nCSV geschrieben (ohne Namen):", args.csv, "->", len(zeilen), "Zeilen")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
