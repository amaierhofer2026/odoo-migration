"""Read-only Belegsammlung zur Kontenfrage 8400/3400 (Odoo 11 gegen Odoo 18).

Erhebt je System:
  - die Konten 8400/3400 bzw. 1161/839 (Code, Name, Kontotyp, Abstimmung, Steuern)
  - Konten des Zielkontenrahmens (Kandidaten) mit Typ und tatsaechlicher Verwendung
  - Steuern, die auf diese Konten verweisen
  - ir.property-Eintraege zu den Konto-Vorgabefeldern von product.category
  - sichtbare Bezeichnungen mit "Projektkategor" und "Kostenstellenkonten"
Keine Schreiboperation.

Aufruf: python scripts/erhebe_konterverwendung_8400_3400.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
ZIEL = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session131", "konten")


def konten(k, modell_account, codes):
    vorhanden = k.kw(modell_account, "fields_get", [[], ["type"]], context=CTX)
    felder = [f for f in ("code", "name", "user_type_id", "reconcile", "active") if f in vorhanden]
    gefunden = k.kw(modell_account, "search_read", [[("code", "in", codes)], felder], context=CTX, limit=0)
    ergebnis = []
    for a in gefunden:
        typ = a["user_type_id"][1] if a.get("user_type_id") else "-"
        nutzung = k.kw("account.move.line", "search_count", [[("account_id", "=", a["id"])]], context=CTX)
        ergebnis.append({"id": a["id"], "code": a["code"], "name": a["name"], "typ": typ,
                         "abstimmbar": a.get("reconcile"), "aktiv": a.get("active"),
                         "belegzeilen_mit_diesem_konto": nutzung})
    return ergebnis


def steuern_auf_konto(k, kontoid):
    """Steuern, die auf ein Konto verweisen (Odoo 11: account_id/refund_account_id)."""
    fg = k.kw("account.tax", "fields_get", [[], ["type", "relation", "string"]], context=CTX)
    kontofelder = [f for f, d in fg.items()
                   if d.get("type") == "many2one" and d.get("relation") == "account.account"]
    treffer = []
    for feld in kontofelder:
        for t in k.kw("account.tax", "search_read", [[(feld, "=", kontoid)], ["name", "description",
                                                                              "amount", "type_tax_use"]],
                      context=CTX, limit=0):
            treffer.append({"feld": feld, "steuer": t["name"], "beschreibung": t.get("description"),
                            "satz": t["amount"], "verwendung": t["type_tax_use"]})
    return {"felder_geprueft": kontofelder, "treffer": treffer}


def property_vorgaben(k, modell, felder):
    feld_ids = k.kw("ir.model.fields", "search", [[("model", "=", modell), ("name", "in", felder)]],
                    context=CTX)
    if not feld_ids:
        return {"hinweis": "keine property-Felder gefunden"}
    daten = k.kw("ir.property", "search_read",
                 [[("fields_id", "in", feld_ids)], ["name", "res_id", "value_reference", "company_id"]],
                 context=CTX, limit=0)
    return [{"feld": d["name"], "res_id": d["res_id"] or "(global/Firmenvorgabe)",
             "wert": d["value_reference"], "firma": d["company_id"]} for d in daten]


def bezeichnungen(k, suchbegriffe):
    treffer = {}
    for begriff in suchbegriffe:
        m = k.kw("ir.ui.menu", "search_read", [[("name", "ilike", begriff)], ["id", "name", "complete_name"]],
                 context=CTX, limit=0)
        a = k.kw("ir.actions.act_window", "search_read", [[("name", "ilike", begriff)], ["id", "name", "res_model"]],
                 context=CTX, limit=0)
        treffer[begriff] = {"menues": m, "aktionen": a}
    # Modell- und Feldbezeichnungen pruefen
    for modell in ("itk_projectcategory.projectcategory", "account.analytic.account"):
        fg = k.kw(modell, "fields_get", [[], ["string"]], context=CTX)
        treffer.setdefault("modellbeschriftungen", {})[modell] = {
            f: d["string"] for f, d in fg.items() if f in ("name", "code", "seq")}
    return treffer


def main() -> int:
    os.makedirs(ZIEL, exist_ok=True)
    k11, k18 = o11(), o18("lokal")
    daten = {}

    print("=== Odoo 11: Konten 8400/3400 (und IDs 1161/839) ===", flush=True)
    daten["o11_konten"] = konten(k11, "account.account", ["8400", "3400"])
    for a in daten["o11_konten"]:
        print("   %s | %s | %s | Belegzeilen: %d" % (a["code"], a["name"], a["typ"], a["belegzeilen_mit_diesem_konto"]))

    print("\n=== Odoo 11: Steuern, die auf 8400/3400 verweisen ===", flush=True)
    for a in daten["o11_konten"]:
        s = steuern_auf_konto(k11, a["id"])
        daten["o11_steuern_%s" % a["code"]] = s
        print("   %s: Felder %s -> %d Treffer" % (a["code"], s["felder_geprueft"], len(s["treffer"])))
        for t in s["treffer"][:6]:
            print("      %s | %s | %s%% | %s" % (t["steuer"], t["feld"], t["satz"], t["beschreibung"]))

    felder = ["property_account_income_categ_id", "property_account_expense_categ_id"]
    print("\n=== Odoo 11: ir.property zu den Kategorie-Konten ===", flush=True)
    daten["o11_property"] = property_vorgaben(k11, "product.category", felder)
    for p in daten["o11_property"]:
        print("   %s -> %s (%s)" % (p["feld"], p["wert"], p["res_id"]))

    print("\n=== Odoo 11: Konten des Ertrags-/Aufwandsbereichs mit Verwendung ===", flush=True)
    daten["o11_aufwand_ertrag"] = konten(k11, "account.account",
                                         ["4000", "4100", "4110", "4200", "5000", "5010", "5011",
                                          "5050", "5090", "3400", "8400"])
    for a in daten["o11_aufwand_ertrag"]:
        print("   %-6s %-52s %-28s Belegzeilen: %d" % (a["code"], a["name"], a["typ"], a["belegzeilen_mit_diesem_konto"]))

    print("\n=== Odoo 18 lokal: Kandidatenkonten ===", flush=True)
    daten["o18_konten"] = konten(k18, "account.account",
                                 ["4000", "4001", "4100", "4110", "4200", "5000", "5010", "5011",
                                  "5050", "5051", "5052", "5090", "3400", "8400"])
    for a in daten["o18_konten"]:
        print("   %-6s %-52s %-28s Belegzeilen: %d" % (a["code"], a["name"], a["typ"], a["belegzeilen_mit_diesem_konto"]))

    print("\n=== Odoo 18 lokal: Steuern auf 4000 ===", flush=True)
    k4000 = [a["id"] for a in daten["o18_konten"] if a["code"] == "4000"]
    if k4000:
        daten["o18_steuern_4000"] = steuern_auf_konto(k18, k4000[0])
        print("   Felder: %s | Treffer: %d" % (daten["o18_steuern_4000"]["felder_geprueft"],
                                               len(daten["o18_steuern_4000"]["treffer"])))

    print("\n=== Odoo 18 lokal: ir.property zu den Kategorie-Konten ===", flush=True)
    daten["o18_property"] = property_vorgaben(k18, "product.category", felder)
    print("   ", daten["o18_property"])

    print("\n=== Bezeichnungen ===", flush=True)
    daten["o11_bezeichnungen"] = bezeichnungen(k11, ["Projektkategor", "Kostenstellenkonten", "Kostenstellen"])
    daten["o18_bezeichnungen"] = bezeichnungen(k18, ["Projektkategor", "Kostenstellenkonten", "Kostenstellen"])
    for r in ("o11_bezeichnungen", "o18_bezeichnungen"):
        print("   %s:" % r)
        for begriff, t in daten[r].items():
            if begriff == "modellbeschriftungen":
                print("      Modellfeld-Labels: %s" % t)
                continue
            print("      %-20s Menues: %s | Aktionen: %s"
                  % (begriff, [(m["name"], m["complete_name"]) for m in t["menues"]][:4],
                     [(a["name"], a["res_model"]) for a in t["aktionen"]][:4]))

    p = os.path.join(ZIEL, "konten_rohdaten.json")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, default=str)
    print("\nRohdaten: %s" % p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
