"""Teil 5: Vollstaendigkeitscheck der Konten- und Steuerzuordnung (Odoo 11 read-only).

Prueft ohne Lese-Limit:
 1. Konten: alle Buchungszeilen je Odoo-11-Konto, Summe gegen die Gesamtzahl der Zeilen.
 2. Steuern: alle Buchungszeilen mit Steuerzuordnung, alle Steuerzeilen, alle Rechnungszeilen
    mit Steuer und alle Rechnungsteuerzeilen - je verwendete Steuer mit Anzahl.

Aufruf:  python scripts/pruefe_teil5_abdeckung.py
"""
from __future__ import annotations

import collections
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11

STAPEL = 2000


def blaettern(k, modell, domain, felder, reihenfolge="id"):
    """Liest alle Treffer in Stapeln (RPC-Limit umgangen)."""
    ids = k.kw(modell, "search", [domain], order=reihenfolge)
    daten = []
    for i in range(0, len(ids), STAPEL):
        daten.extend(k.kw(modell, "read", [ids[i:i + STAPEL], felder]))
    return daten


def main() -> int:
    k = o11()
    ergebnis = {}

    # ---------- 1. Konten ----------
    gesamt_zeilen = k.kw("account.move.line", "search_count", [[]])
    gruppen = k.kw("account.move.line", "read_group",
                   [[], ["account_id", "debit", "credit"], ["account_id"]], lazy=False,
                   orderby="account_id_count desc")
    konten = []
    summe = 0
    for g in gruppen:
        if not g.get("account_id"):
            continue
        kid = g["account_id"][0]
        info = k.kw("account.account", "read", [[kid], ["code", "name", "internal_type"]],
                    context={"lang": "de_DE"})[0]
        anzahl = g.get("account_id_count") or 0
        summe += anzahl
        konten.append({"id": kid, "code": info["code"], "name": info["name"],
                       "zeilen": anzahl, "soll": g["debit"], "haben": g["credit"]})
    ergebnis["konten"] = konten
    ergebnis["zeilen_gesamt"] = gesamt_zeilen
    ergebnis["zeilen_summe_gruppen"] = summe
    print("=== 1. Konten-Abdeckung (Odoo 11) ===")
    print("Buchungszeilen gesamt: %d | Summe der Kontengruppen: %d | Abdeckung: %s"
          % (gesamt_zeilen, summe, "100%" if summe == gesamt_zeilen else "UNVOLLSTAENDIG"))
    for x in konten:
        print("   %-8s %-52s Zeilen=%-6s Soll=%14.2f Haben=%14.2f"
              % (x["code"], (x["name"] or "")[:52], x["zeilen"], x["soll"], x["haben"]))
    ohne_konto = k.kw("account.move.line", "search_count", [[("account_id", "=", False)]])
    ergebnis["zeilen_ohne_konto"] = ohne_konto
    print("Buchungszeilen ohne Konto: %d" % ohne_konto)

    # Umfang der Zeilen nach Belegart dokumentieren
    umfang = {}
    for g in k.kw("account.move.line", "read_group", [[], ["move_id"], ["move_id"]], lazy=False, limit=0) or []:
        pass
    for g in k.kw("account.move.line", "read_group", [[], ["journal_id"], ["journal_id"]], lazy=False,
                  orderby="journal_id_count desc"):
        if g.get("journal_id"):
            umfang[g["journal_id"][1]] = g.get("journal_id_count")
    ergebnis["zeilen_je_journal"] = umfang
    print("Zeilen je Journal: %s" % umfang)

    # ---------- 2. Steuern ----------
    print("\n=== 2. Steuer-Abdeckung (Odoo 11) ===")
    # 2a Buchungszeilen mit Steuerzuordnung (tax_ids)
    zeilen_tax = blaettern(k, "account.move.line", [("tax_ids", "!=", False)], ["tax_ids"])
    z_tax = collections.Counter()
    for z in zeilen_tax:
        for t in (z.get("tax_ids") or []):
            z_tax[t] += 1
    # 2b Steuerzeilen (tax_line_id) der Buchungen
    zeilen_taxline = blaettern(k, "account.move.line", [("tax_line_id", "!=", False)], ["tax_line_id"])
    z_taxline = collections.Counter()
    for z in zeilen_taxline:
        if z.get("tax_line_id"):
            z_taxline[z["tax_line_id"][0]] += 1
    # 2c Rechnungszeilen mit Steuer
    zeilen_inv = blaettern(k, "account.invoice.line", [("invoice_line_tax_ids", "!=", False)],
                           ["invoice_line_tax_ids"])
    z_inv = collections.Counter()
    for z in zeilen_inv:
        for t in (z.get("invoice_line_tax_ids") or []):
            z_inv[t] += 1
    rechnungszeilen_gesamt = k.kw("account.invoice.line", "search_count", [[]])
    # 2d Rechnungsteuerzeilen (account.invoice.tax)
    taxzeilen = blaettern(k, "account.invoice.tax", [], ["tax_id", "amount", "base"])
    z_itax = collections.Counter()
    for z in taxzeilen:
        if z.get("tax_id"):
            z_itax[z["tax_id"][0]] += 1

    alle = collections.Counter()
    for c in (z_tax, z_taxline, z_inv, z_itax):
        alle.update(c)
    alle_tax_ids = set(z_tax) | set(z_taxline) | set(z_inv) | set(z_itax)
    ergebnis["steuern"] = {str(t): {"buchungszeilen_tax_ids": z_tax.get(t, 0),
                                    "steuerzeilen_tax_line_id": z_taxline.get(t, 0),
                                    "rechnungszeilen": z_inv.get(t, 0),
                                    "rechnungsteuerzeilen": z_itax.get(t, 0)}
                           for t in sorted(alle_tax_ids)}
    ergebnis["rechnungszeilen_gesamt"] = rechnungszeilen_gesamt
    ergebnis["rechnungszeilen_mit_steuer"] = len(zeilen_inv)
    for tid in sorted(alle_tax_ids):
        t = k.kw("account.tax", "read", [[tid], ["name", "amount", "amount_type", "type_tax_use",
                                                 "price_include", "active"]], context={"lang": "de_DE"})[0]
        print("   id=%-4s %-40s Satz=%-6s %-8s %-6s | Buchungszeilen(tax_ids)=%-5s Steuerzeilen=%-5s "
              "Rechnungszeilen=%-5s Rechnungsteuerzeilen=%-4s"
              % (t["id"], (t["name"] or "")[:40], t["amount"], t["amount_type"], t["type_tax_use"],
                 z_tax.get(tid, 0), z_taxline.get(tid, 0), z_inv.get(tid, 0), z_itax.get(tid, 0)))
    print("Rechnungszeilen gesamt: %d | davon mit Steuer: %d" % (rechnungszeilen_gesamt, len(zeilen_inv)))

    ziel = os.path.join(tempfile.gettempdir(), "teil5_abdeckung.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1, default=str)
    print("\nErgebnis: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
