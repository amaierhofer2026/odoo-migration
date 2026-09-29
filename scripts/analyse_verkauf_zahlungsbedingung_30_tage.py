"""Bestandsaufnahme Zahlungsbedingung "30 Tage netto" (Odoo 11 read-only vs. Odoo 18).

Liest in Odoo 11 Prod (ausschliesslich lesend):
  - die vollstaendige Konfiguration der Zahlungsbedingung "30 Tage netto" (Kopf und Zeilen)
  - die Nutzung: Auftraege mit dieser Bedingung, Kunden mit dieser Standardbedingung,
    Rechnungen/Abos mit Bezug
Vergleicht mit den in Odoo 18 vorhandenen Zahlungsbedingungen (lokal und VM).

Aufruf:
    python scripts/analyse_verkauf_zahlungsbedingung_30_tage.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}
NAME = "30 Tage netto"
KOPFFELDER = ["name", "note", "active", "company_id", "early_discount", "discount_percentage",
              "discount_days"]
ZEILENFELDER = ["value", "value_amount", "days", "day_of_the_month", "option", "sequence"]


def lese_bedingungen(client, ist18: bool) -> list:
    ids = client.kw("account.payment.term", "search", [[]], context=SP)
    ergebnis = []
    for pid in ids:
        try:
            kopf = client.kw("account.payment.term", "read",
                             [[pid], [f for f in KOPFFELDER if f != "early_discount" or ist18]],
                             context=SP)[0]
        except Exception:
            kopf = client.kw("account.payment.term", "read", [[pid], ["name", "note", "active"]],
                             context=SP)[0]
        zeilen = client.kw("account.payment.term.line", "search_read",
                           [[("payment_term_id", "=", pid)], ZEILENFELDER], context=SP)
        kopf["id"] = pid
        kopf["zeilen"] = sorted(zeilen, key=lambda z: z.get("sequence") or 0)
        ergebnis.append(kopf)
    return sorted(ergebnis, key=lambda x: (x.get("name") or "").lower())


def main() -> int:
    k11, k18, kvm = o11(), o18("lokal"), o18("vm")
    ergebnis = {}

    print("=== Odoo 11 Prod: Zahlungsbedingung '%s' (nur lesend) ===" % NAME)
    treffer = k11.kw("account.payment.term", "search_read",
                     [[("name", "=", NAME)],
                      ["name", "note", "active", "company_id", "id"]], context=SP)
    if not treffer:
        treffer = k11.kw("account.payment.term", "search_read",
                         [[("name", "ilike", "30 Tage")],
                          ["name", "note", "active", "company_id", "id"]], context=SP)
    print("  Treffer: %d" % len(treffer))
    for t in treffer:
        print("  id=%s name='%s' aktiv=%s Firma=%s" % (t["id"], t["name"], t["active"],
                                                       t["company_id"] or "-"))
        print("     Hinweis: %s" % ((t.get("note") or "-").replace("\n", " ")[:120]))
        zeilen = k11.kw("account.payment.term.line", "search_read",
                        [[("payment_term_id", "=", t["id"])], ZEILENFELDER], context=SP)
        for z in sorted(zeilen, key=lambda x: x.get("sequence") or 0):
            print("     Zeile: Wert %s/%s, Tage %s, Monatstag %s, Option %s"
                  % (z["value"], z["value_amount"], z["days"], z["day_of_the_month"], z["option"]))
    ergebnis["o11"] = treffer

    if treffer:
        pid = treffer[0]["id"]
        print("\n=== Odoo 11: Nutzung ===")
        nutzung = {}
        for modell, feld, titel in (("sale.order", "payment_term_id", "Verkaufsauftraege"),
                                    ("account.invoice", "payment_term_id", "Rechnungen"),
                                    ("res.partner", "property_payment_term_id", "Kunden (Standard)")):
            try:
                n = k11.kw(modell, "search_count", [[(feld, "=", pid)]], context=SP)
            except Exception as ex:
                n = "nicht messbar (%s)" % str(ex)[:60]
            nutzung[titel] = n
            print("  %-22s %s" % (titel, n))
        auftraege = k11.kw("sale.order", "search_read",
                           [[("payment_term_id", "=", pid)],
                            ["name", "state", "partner_id", "date_order", "amount_total"]], context=SP)
        print("  Betroffene Auftraege:")
        for a in auftraege:
            print("     %s | %s | %s | %s | %s" % (a["name"], a["state"], a["partner_id"][1],
                                                   (a["date_order"] or "")[:10], a["amount_total"]))
        partner = k11.kw("res.partner", "search_read",
                         [[("property_payment_term_id", "=", pid)], ["name"]], context=SP)
        print("  Kunden mit dieser Standardbedingung: %s" % [p["name"] for p in partner])
        ergebnis["nutzung"] = {"zaehler": nutzung, "auftraege": auftraege,
                               "kunden": [p["name"] for p in partner]}

    print("\n=== Odoo 18 vorhandene Zahlungsbedingungen ===")
    for name, k in (("lokal", k18), ("vm", kvm)):
        bed = lese_bedingungen(k, True)
        print("  %s: %d Bedingungen" % (name, len(bed)))
        for b in bed:
            zeilen = ", ".join("%s/%s Tage=%s Option=%s" % (z["value"], z["value_amount"],
                                                            z["days"], z["option"])
                               for z in b["zeilen"])
            print("     %-28s %s" % (b["name"][:28], zeilen or "keine Zeilen"))
        ergebnis["o18_" + name] = bed

    ziel = os.path.join(REPO, "docs", "_verkauf_zahlungsbedingung_30.json")
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1)
    print("\nRohdaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
