"""Nachweis des Sonderfalls R-24832 (Zeilensteuer ohne Steuerbuchung in Odoo 11).

Teil A (read-only, Odoo 11): wendet die Sonderfall-Regel auf ALLE Odoo-11-Belege mit
steuerbehafteten Zeilen an und weist nach, dass genau ein Beleg die drei Bedingungen erfuellt
(alle uebrigen Belege erhalten ihre Steuer wie bisher).

Teil B (Vergleich): stellt den migrierten Beleg in Odoo 18 gegen Odoo 11 und prueft, dass
Gesamtbetrag, Restbetrag, Zahlungsstatus und Buchungszeilen unveraendert sind und KEINE
Steuerbuchung erzeugt wurde.

Aufruf: python scripts/pruefe_sonderfall_r24832.py --instanz lokal|vm [--beleg R-24832]
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}


def teil_a(k, nummer):
    print("=== Teil A: Sonderfall-Regel gegen alle Odoo-11-Belege mit Zeilensteuer ===")
    zeilen = k.kw("account.invoice.line", "search_read", [[("invoice_line_tax_ids", "!=", False)],
                                                          ["invoice_id"]], context=CTX, limit=0)
    beleg_ids = sorted({z["invoice_id"][0] for z in zeilen if z["invoice_id"]})
    print("   Belege mit steuerbehafteten Zeilen: %d" % len(beleg_ids))
    treffer = []
    geprueft = 0
    for i in range(0, len(beleg_ids), 200):
        teil = beleg_ids[i:i + 200]
        for b in k.kw("account.invoice", "read",
                      [teil, ["number", "type", "state", "amount_tax", "tax_line_ids",
                              "invoice_line_ids"]], context=CTX):
            geprueft += 1
            if abs(b["amount_tax"] or 0.0) > 0.005:
                continue
            if b["tax_line_ids"]:
                continue
            z = k.kw("account.invoice.line", "search_count",
                     [[("invoice_id", "=", b["id"]), ("invoice_line_tax_ids", "!=", False)]],
                     context=CTX)
            if z:
                treffer.append((b["number"], b["type"], b["state"], b["amount_tax"]))
    print("   geprueft: %d Belege" % geprueft)
    print("   Sonderfall-Kandidaten (Zeilensteuer, amount_tax = 0, keine Steuerbuchungszeile): %d"
          % len(treffer))
    for t in treffer:
        print("      %s | %s | %s | amount_tax=%.2f" % t)
    ok = len(treffer) == 1 and treffer[0][0] == nummer
    print("   %s Regel greift ausschliesslich bei %s (%d von %d Belegen behalten ihre Steuer)"
          % ("OK  " if ok else "FEHL", nummer, geprueft - len(treffer), geprueft))
    return ok, geprueft, len(treffer)


def teil_b(k11, z, nummer):
    print("\n=== Teil B: migrierter Beleg in Odoo 18 gegen Odoo 11 ===")
    q11 = k11.kw("account.invoice", "search_read", [[("number", "=", nummer)],
                 ["id", "number", "type", "state", "amount_untaxed", "amount_tax", "amount_total",
                  "residual", "partner_id", "move_id"]], context=CTX, limit=1)
    if not q11:
        print("   FEHL Beleg %s in Odoo 11 nicht gefunden" % nummer)
        return False
    b11 = q11[0]
    ids = z.kw("account.move", "search", [[("itk_o11_invoice_number", "=", nummer)]], context=CTX)
    if not ids:
        print("   FEHL Beleg %s ist in Odoo 18 nicht vorhanden (nicht migriert?)" % nummer)
        return False
    b18 = z.kw("account.move", "read", [ids, ["name", "move_type", "state", "amount_untaxed",
                                             "amount_tax", "amount_total", "amount_residual",
                                             "payment_state"]], context=CTX)[0]
    print("   Odoo 11: %s %s ohne=%.2f Steuer=%.2f total=%.2f Rest=%.2f"
          % (b11["number"], b11["state"], b11["amount_untaxed"], b11["amount_tax"],
             b11["amount_total"], b11["residual"]))
    print("   Odoo 18: %s %s ohne=%.2f Steuer=%.2f total=%.2f Rest=%.2f Zahlung=%s"
          % (b18["name"], b18["state"], b18["amount_untaxed"], b18["amount_tax"],
             b18["amount_total"], b18["amount_residual"], b18["payment_state"]))
    ok = True
    for feld11, feld18, bez in (("amount_untaxed", "amount_untaxed", "Nettobetrag"),
                                ("amount_total", "amount_total", "Gesamtbetrag"),
                                ("residual", "amount_residual", "Restbetrag")):
        gleich = abs((b11[feld11] or 0) - (b18[feld18] or 0)) < 0.005
        ok = ok and gleich
        print("   %s %-12s Odoo 11 %.2f = Odoo 18 %.2f" % ("OK  " if gleich else "FEHL", bez,
                                                            b11[feld11] or 0, b18[feld18] or 0))
    steuer_null = abs(b18["amount_tax"] or 0) < 0.005
    ok = ok and steuer_null
    print("   %s Steuer in Odoo 18 = %.2f (erwartet 0,00, keine Nachberechnung)"
          % ("OK  " if steuer_null else "FEHL", b18["amount_tax"] or 0))
    zustand = {"paid": "paid", "open": "not_paid", "draft": "draft"}.get(b11["state"], b11["state"])
    ok_zustand = (zustand == b18["payment_state"]) or (b11["state"] == "draft" and b18["state"] == "draft")
    ok = ok and ok_zustand
    print("   %s Zahlungsstatus Odoo 11 %s gegen Odoo 18 %s"
          % ("OK  " if ok_zustand else "FEHL", b11["state"], b18["payment_state"]))

    zeilen11 = k11.kw("account.move.line", "search_read", [[("move_id", "=", b11["move_id"][0])],
                      ["account_id", "debit", "credit", "tax_line_id"]], context=CTX, limit=0)
    zeilen18 = z.kw("account.move.line", "search_read", [[("move_id", "=", ids[0])],
                    ["account_id", "debit", "credit", "tax_line_id"]], context=CTX, limit=0)
    print("   Buchungszeilen Odoo 11: %d | Odoo 18: %d" % (len(zeilen11), len(zeilen18)))
    for zeile in zeilen11:
        print("      O11 %-32s Soll=%-9.2f Haben=%-9.2f Steuerzeile=%s"
              % (zeile["account_id"][1][:32], zeile["debit"], zeile["credit"],
                 zeile["tax_line_id"][1] if zeile["tax_line_id"] else "-"))
    for zeile in zeilen18:
        print("      O18 %-32s Soll=%-9.2f Haben=%-9.2f Steuerzeile=%s"
              % (zeile["account_id"][1][:32], zeile["debit"], zeile["credit"],
                 zeile["tax_line_id"][1] if zeile["tax_line_id"] else "-"))
    steuerzeilen18 = [x for x in zeilen18 if x["tax_line_id"]]
    ok = ok and not steuerzeilen18
    print("   %s Steuerbuchungszeilen in Odoo 18: %d (erwartet 0)"
          % ("OK  " if not steuerzeilen18 else "FEHL", len(steuerzeilen18)))
    zeilensteuer18 = z.kw("account.move.line", "search_count",
                          [[("move_id", "=", ids[0]), ("tax_ids", "!=", False)]], context=CTX)
    ok = ok and zeilensteuer18 == 0
    print("   %s Belegzeilen mit Steuer in Odoo 18: %d (erwartet 0)"
          % ("OK  " if zeilensteuer18 == 0 else "FEHL", zeilensteuer18))
    return ok


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--beleg", default="R-24832")
    a = p.parse_args()
    k11 = o11()
    z = o18(a.instanz)
    ok_a, geprueft, treffer = teil_a(k11, a.beleg)
    ok_b = teil_b(k11, z, a.beleg)
    print("\nErgebnis: Teil A %s | Teil B %s" % ("OK" if ok_a else "FEHL", "OK" if ok_b else "FEHL"))
    return 0 if (ok_a and ok_b) else 1


if __name__ == "__main__":
    raise SystemExit(main())
