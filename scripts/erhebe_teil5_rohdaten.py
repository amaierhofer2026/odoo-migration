"""Teil 5: Rohdaten fuer Stammdaten- und Zuordnungsvorbereitung (read-only).

Liest aus Odoo 11 die tatsaechlich verwendeten Konten, Steuern, Valorisierungstexte und
Zahlungsnummern und aus Odoo 18 die vorhandenen Gegenstuecke. Ergebnis als JSON im Temp-Ordner,
damit Generator-Skripte darauf aufbauen koennen. Odoo 11 wird nur gelesen.

Aufruf:  python scripts/erhebe_teil5_rohdaten.py
"""
from __future__ import annotations

import collections
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18


def main() -> int:
    lade_env()
    k11, k18 = o11(), o18("lokal")
    daten = {}

    print("=== Valorisierungstexte ===")
    def vorlagen_felder(k, modell):
        try:
            f = k.kw(modell, "fields_get", [[], ["string"]], context={"lang": "de_DE"})
        except Exception:
            return None
        return [x for x in ("id", "name", "code", "description") if x in f]

    modell11 = modell18 = "itk_valorisierung.valorisierung"
    for kandidat in ("itk_valorisierung.valorisierung", "itk.valorisierung", "valorisierung"):
        if vorlagen_felder(k18, kandidat):
            modell18 = kandidat
            break
    f11 = vorlagen_felder(k11, modell11) or ["id", "name"]
    f18 = vorlagen_felder(k18, modell18) or ["id", "name"]
    print("   Modelle: O11 %s (%s) | O18 %s (%s)" % (modell11, f11, modell18, f18))
    v11 = k11.kw(modell11, "search_read", [[], f11], order="id", context={"lang": "de_DE"})
    v18 = k18.kw(modell18, "search_read", [[], f18], order="id", context={"lang": "de_DE"})
    daten["valorisierung_o11"] = v11
    daten["valorisierung_o18"] = v18
    print("   Odoo 11: %d | Odoo 18: %d" % (len(v11), len(v18)))
    for v in v11:
        print("      id=%-4s %s" % (v["id"], v["name"]))
    for v in v18:
        print("   O18 id=%-4s %s" % (v["id"], v["name"]))
    daten["valorisierung_modell"] = modell18

    print("\n=== Verwendete Konten (Odoo 11) ===")
    zeilen = k11.kw("account.move.line", "read_group",
                    [[("account_id", "!=", False)], ["account_id", "debit", "credit"], ["account_id"]],
                    lazy=False, context={"lang": "de_DE"})
    konten = []
    for z in zeilen:
        if not z.get("account_id"):
            continue
        kid = z["account_id"][0]
        daten_konto = k11.kw("account.account", "read", [[kid], ["id", "code", "name", "user_type_id",
                                                                  "internal_type", "reconcile"]],
                             context={"lang": "de_DE"})[0]
        konten.append({"id": kid, "code": daten_konto["code"], "name": daten_konto["name"],
                       "typ": (daten_konto.get("user_type_id") or ["", ""])[1],
                       "internal": daten_konto.get("internal_type"),
                       "buchungen": z.get("__count", z.get("account_id_count")),
                       "soll": z.get("debit", 0), "haben": z.get("credit", 0)})
    konten.sort(key=lambda x: str(x["code"]))
    daten["konten_o11"] = konten
    print("   verwendete Konten in Odoo 11: %d" % len(konten))

    print("\n=== Verwendete Steuern (Odoo 11) ===")
    steuern = []
    for t in k11.kw("account.tax", "search_read",
                    [[], ["id", "name", "description", "amount", "amount_type", "type_tax_use",
                          "price_include", "active"]], order="id", context={"lang": "de_DE"}):
        steuern.append(t)
    daten["steuern_o11"] = steuern
    verbrauch = collections.Counter()
    for l in k11.kw("account.invoice.line", "search_read",
                    [[("invoice_line_tax_ids", "!=", False)], ["invoice_line_tax_ids"]], order="id"):
        for st in (l.get("invoice_line_tax_ids") or []):
            verbrauch[st] += 1
    for l in k11.kw("account.invoice", "search_read",
                    [[("tax_line_ids", "!=", False)], ["tax_line_ids"]], order="id", limit=2000):
        pass
    daten["steuern_nutzung_o11"] = verbrauch
    print("   Steuern Odoo 11: %d, davon in Verwendung: %d" % (len(steuern), len(verbrauch)))

    print("\n=== Steuern Odoo 18 ===")
    daten["steuern_o18"] = k18.kw("account.tax", "search_read",
                                  [[], ["id", "name", "description", "amount", "amount_type", "type_tax_use",
                                        "price_include", "active"]], order="id", context={"lang": "de_DE"})
    print("   Steuern Odoo 18: %d" % len(daten["steuern_o18"]))

    print("\n=== Konten Odoo 18 (Kontenrahmen) ===")
    k18konten = k18.kw("account.account", "search_read",
                       [[], ["id", "code", "name", "account_type"]], order="code", context={"lang": "de_DE"})
    daten["konten_o18"] = k18konten
    print("   Konten Odoo 18: %d" % len(k18konten))

    print("\n=== Zahlungsnummern Odoo 11 ===")
    muster = collections.Counter()
    for z in k11.kw("account.payment", "search_read", [[], ["id", "name", "payment_date"]], order="id", limit=5000):
        name = z["name"] or ""
        teile = name.split("/")
        muster["/".join([teile[0], "JJJJ", "NNNN" if len(teile) > 2 and len(teile[2]) == 4 else "NNNNN"]
                         if len(teile) > 2 else "?")] += 1
    daten["zahlungsnummern_o11"] = dict(muster)
    print("   Muster: %s" % dict(muster))
    print("   erstes/letztes Beispiel: %s / %s"
          % (k11.kw("account.payment", "search_read", [[], ["name"]], order="id", limit=1)[0]["name"],
             k11.kw("account.payment", "search_read", [[], ["name"]], order="id desc", limit=1)[0]["name"]))

    ziel = os.path.join(tempfile.gettempdir(), "teil5_rohdaten.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, default=str)
    print("\nRohdaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
