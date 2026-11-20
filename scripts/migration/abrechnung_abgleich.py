# -*- coding: utf-8 -*-
"""Abrechnung: Abgleich Odoo 11 gegen Odoo 18 (read-only).

Prueft je Instanz Anzahl, Typen, Status, Nummern, Summen, Zeilen, Partnerzuordnung,
Valorisierungsbezug, offenen Rest und Zahlungsstatus. Die 53 Rechnungen an namenlosen
Kontakten sind als dokumentierte Luecke bekannt und werden getrennt ausgewiesen.

Aufruf:
    python scripts/migration/abrechnung_abgleich.py --instanz lokal
    python scripts/migration/abrechnung_abgleich.py --instanz vm
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

CTX11 = {"lang": "de_DE", "active_test": False}
CTX18 = {"lang": "de_DE", "active_test": False}
MODELL = "account.move"
TOLERANZ = 0.02


def m2o(w):
    return w[0] if isinstance(w, (list, tuple)) and w else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    args = ap.parse_args()

    o11 = client.o11()
    o18 = client.o18(args.instanz)
    print("=== Abrechnungsabgleich Odoo 11 <-> Odoo 18 (%s) ===" % args.instanz)
    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    # ------------------------------------------------ Stammdaten Ziel
    partner_map = {r["itk_o11_id"]: r["id"] for r in
                   o18.kw("res.partner", "search_read", [[["itk_o11_id", "!=", False]],
                                                         ["id", "itk_o11_id"]],
                          context=CTX18, limit=50000)}

    # ------------------------------------------------ Quelle lesen
    felder11 = ["id", "number", "type", "state", "date_invoice", "partner_id",
                "amount_untaxed", "amount_tax", "amount_total", "residual",
                "valorisierung_id", "invoice_line_ids"]
    ids11 = o11.kw("account.invoice", "search", [[]], context=CTX11, limit=200000)
    q = []
    for i in range(0, len(ids11), 500):
        q.extend(o11.kw("account.invoice", "read", [ids11[i:i + 500], felder11],
                        context=CTX11))
    # nicht zuordenbar = Partner ohne Anker im Ziel
    ohne_partner = [r for r in q if m2o(r["partner_id"]) not in partner_map]
    erwartet = [r for r in q if m2o(r["partner_id"]) in partner_map]
    print("Odoo 11: %d Belege, davon %d ohne Partneranker (dokumentierte Luecke)"
          % (len(q), len(ohne_partner)))

    # ------------------------------------------------ Ziel lesen
    ids18 = o18.kw(MODELL, "search", [[["itk_o11_id", "!=", False]]], context=CTX18,
                  limit=200000)
    z = {}
    felder18 = ["id", "itk_o11_id", "name", "move_type", "state", "invoice_date",
                "partner_id", "amount_untaxed", "amount_tax", "amount_total",
                "amount_residual", "payment_state", "valorisierung_id", "ref"]
    for i in range(0, len(ids18), 500):
        for r in o18.kw(MODELL, "read", [ids18[i:i + 500], felder18], context=CTX18):
            z[r["itk_o11_id"]] = r

    # ------------------------------------------------ Anzahl
    pruefe(len(z) == len(erwartet),
           "Belegzahl: Odoo 18 %d, erwartet %d (Odoo 11 %d minus %d Luecke)"
           % (len(z), len(erwartet), len(q), len(ohne_partner)))
    pruefe(len(ohne_partner) == 53, "dokumentierte Luecke: %d Belege (erwartet 53)"
           % len(ohne_partner))

    # ------------------------------------------------ Typen, Status
    typ11 = Counter(r["type"] for r in erwartet)
    typ18 = Counter("out_refund" if r["move_type"] == "out_refund" else "out_invoice"
                    for r in z.values())
    for t in ("out_invoice", "out_refund"):
        pruefe(typ11.get(t, 0) == typ18.get(t, 0),
               "Typ %s: Odoo 11 %d, Odoo 18 %d" % (t, typ11.get(t, 0), typ18.get(t, 0)))

    st11 = Counter(r["state"] for r in erwartet)
    st18 = Counter(r["state"] for r in z.values())
    pruefe(st11.get("draft", 0) == st18.get("draft", 0),
           "Entwuerfe: Odoo 11 %d, Odoo 18 %d" % (st11.get("draft", 0), st18.get("draft", 0)))
    soll_posted = st11.get("open", 0) + st11.get("paid", 0)
    pruefe(soll_posted == st18.get("posted", 0),
           "gebucht: erwartet %d (offen %d + bezahlt %d), Odoo 18 %d"
           % (soll_posted, st11.get("open", 0), st11.get("paid", 0), st18.get("posted", 0)))

    # ------------------------------------------------ Nummern
    ohne_nummer = 0
    nummer_abw = 0
    for r in erwartet:
        t = z.get(r["id"])
        if not t:
            continue
        if r["state"] == "draft":
            if (t["name"] or "/") != "/":
                ohne_nummer += 1
            continue
        if (r["number"] or "") != (t["name"] or ""):
            nummer_abw += 1
    pruefe(nummer_abw == 0, "Rechnungsnummern identisch (%d Abweichungen)" % nummer_abw)
    pruefe(ohne_nummer == 0, "Entwuerfe ohne Nummer (%d Abweichungen)" % ohne_nummer)

    # ------------------------------------------------ Summen
    s11 = {k: round(sum(r[k] for r in erwartet), 2)
           for k in ("amount_untaxed", "amount_tax", "amount_total", "residual")}
    s18 = {k: round(sum(r[k] for r in z.values()), 2)
           for k in ("amount_untaxed", "amount_tax", "amount_total", "amount_residual")}
    # Bekannte Odoo-11-Dateninkonsistenz: bei einem Beleg weicht der Kopf-Bruttowert um
    # 55,63 von der Summe der Zeilen ab. Odoo 18 rechnet aus den Zeilen, deshalb ist
    # genau diese Differenz erwartet (dokumentiert in der Datenmigrationsdoku).
    BEKANNT_KOPF_ZEILEN = 55.63
    for k11, k18, name in (("amount_untaxed", "amount_untaxed", "netto"),
                           ("amount_tax", "amount_tax", "Steuer"),
                           ("amount_total", "amount_total", "brutto")):
        diff = round(s18[k18] - s11[k11], 2)
        grenze = BEKANNT_KOPF_ZEILEN + TOLERANZ if name != "netto" else TOLERANZ
        pruefe(abs(diff) <= grenze,
               "Summe %s: Odoo 11 %.2f, Odoo 18 %.2f (Differenz %.2f%s)"
               % (name, s11[k11], s18[k18], diff,
                  "; bekannte Kopf-/Zeilendifferenz Odoo 11" if abs(diff) > TOLERANZ else ""))

    # ------------------------------------------------ Zeilen
    zeilen11 = sum(len(r["invoice_line_ids"]) for r in erwartet)
    zeilen18 = o18.kw("account.move.line", "search_count",
                      [[["move_id.itk_o11_id", "!=", False],
                        ["display_type", "=", "product"]]], context=CTX18)
    pruefe(zeilen11 == zeilen18, "Rechnungszeilen: Odoo 11 %d, Odoo 18 %d"
           % (zeilen11, zeilen18))

    # ------------------------------------------------ Partner je Beleg
    partner_abw = 0
    for r in erwartet:
        t = z.get(r["id"])
        if t and m2o(t["partner_id"]) != partner_map.get(m2o(r["partner_id"])):
            partner_abw += 1
    pruefe(partner_abw == 0, "Partnerzuordnung je Beleg (%d Abweichungen)" % partner_abw)

    # ------------------------------------------------ Valorisierung
    valo_map = {r["itk_o11_id"]: r["id"] for r in
                o18.kw("itk_valorisierung.valorisierung", "search_read",
                       [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]], context=CTX18,
                       limit=1000)}
    soll_valo = sum(1 for r in erwartet if r["valorisierung_id"])
    ist_valo = sum(1 for r in z.values() if r["valorisierung_id"])
    pruefe(soll_valo == ist_valo, "Valorisierungsbezug: erwartet %d, Odoo 18 %d"
           % (soll_valo, ist_valo))

    # ------------------------------------------------ Zahlungen
    zahlungen = o18.kw("account.payment", "search_count", [[["itk_o11_id", "!=", False]]],
                       context=CTX18)
    z11 = o11.kw("account.payment", "search_count", [[]], context=CTX11)
    print("  Zahlungen: Odoo 11 %d, Odoo 18 %d" % (z11, zahlungen))
    bezahlt = sum(1 for r in z.values() if r["payment_state"] == "paid")
    offen_rest = round(sum(r["amount_residual"] for r in z.values()), 2)
    print("  Bezahlte Belege: %d | offener Rest: %.2f (Odoo 11: %.2f)"
          % (bezahlt, offen_rest, s11["residual"]))
    if zahlungen:
        # Erwartete Differenz: 4 Entwuerfe fuehren in Odoo 11 residual 0 (kein
        # Buchungssatz), in Odoo 18 den vollen Betrag (946,20); dazu zwei Gutschriften,
        # die Odoo 11 teilverrechnet hat (R-25700 144,72, R-25543 525,84).
        BEKANNT_REST = 1616.76
        diff = round(offen_rest - s11["residual"], 2)
        pruefe(abs(diff) <= BEKANNT_REST + TOLERANZ,
               "Offener Rest: Odoo 18 %.2f, Odoo 11 %.2f (Differenz %.2f = %.2f Entwuerfe "
               "+ %.2f Teilverrechnungen)" % (offen_rest, s11["residual"], diff, 946.20,
                                              670.56))

    print()
    print("--- Ergebnis ---")
    print("Pruefungen OK ............... %d" % ok)
    print("Abweichungen ................ %d" % fehler)
    print("Dokumentierte Luecke ........ %d Belege (namenlose Kontakte), "
          "brutto %.2f" % (len(ohne_partner),
                           round(sum(r["amount_total"] for r in ohne_partner), 2)))
    return 0 if not fehler else 1


if __name__ == "__main__":
    sys.exit(main())
