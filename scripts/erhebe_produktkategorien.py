"""Read-only: tatsaechlich verwendete Produktkategorien in Odoo 11 und ihr Ziel in Odoo 18.

Aufruf: python scripts/erhebe_produktkategorien.py [lokal|vm]
Zeigt je Odoo-11-Kategorie: Name, vollstaendiger Pfad, Ueberkategorie, Anzahl Produkte
(Vorlagen und Varianten), migrationsrelevante Felder - und ob die Kategorie im Odoo-18-Ziel
ueber den vollstaendigen Namen eindeutig vorhanden ist.
Es wird NICHTS geschrieben.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
k11 = o11()
k18 = o18(inst)
CTX = {"lang": "de_DE"}
FELDER = ["id", "name", "complete_name", "parent_id", "product_count",
          "property_account_income_categ_id", "property_account_expense_categ_id",
          "removal_strategy_id", "packaging_reserve_method"]

zeilen = []


def schreibe(t=""):
    zeilen.append(t)
    print(t)


kat11 = k11.kw("product.category", "search_read", [[], FELDER], context=CTX)
vorlagen_je_kat = {}
for p in k11.kw("product.template", "search_read", [[], ["categ_id"]], context=CTX):
    if p["categ_id"]:
        vorlagen_je_kat.setdefault(p["categ_id"][0], [0, p["categ_id"][1]])[0] += 1
varianten_je_kat = {}
for p in k11.kw("product.product", "search_read", [[], ["categ_id"]], context=CTX):
    if p["categ_id"]:
        varianten_je_kat.setdefault(p["categ_id"][0], 0)
        varianten_je_kat[p["categ_id"][0]] += 1

kat18 = k18.kw("product.category", "search_read", [[], ["id", "name", "complete_name", "parent_id"]],
               context=CTX)
pfade18 = {}
for k in kat18:
    pfade18.setdefault(k["complete_name"], []).append(k["id"])
namen18 = {}
for k in kat18:
    namen18.setdefault(k["name"], []).append(k["id"])

schreibe("=== Odoo-11-Produktkategorien (read-only) ===")
schreibe("Kategorien gesamt: %d | davon mit Produkten: %d" % (
    len(kat11), len([k for k in kat11 if vorlagen_je_kat.get(k["id"], [0])[0]])))
schreibe("")
schreibe("%-46s %-8s %-8s %-22s %-9s %s" % ("Vollstaendiger Pfad (Odoo 11)", "Vorl.", "Var.",
                                             "Ueberkategorie", "im Ziel", "Ziel-Kategorie"))
verwendet = [k for k in kat11 if vorlagen_je_kat.get(k["id"], [0])[0]]
for k in sorted(verwendet, key=lambda x: x["complete_name"]):
    vorlagen = vorlagen_je_kat.get(k["id"], [0, ""])[0]
    varianten = varianten_je_kat.get(k["id"], 0)
    ueber = k["parent_id"][1] if k["parent_id"] else "-"
    treffer_pfad = pfade18.get(k["complete_name"], [])
    treffer_name = namen18.get(k["name"], [])
    if len(treffer_pfad) == 1:
        ziel = "vorhanden (id %s)" % treffer_pfad[0]
        status = "ja"
    elif len(treffer_pfad) > 1:
        ziel = "MEHRDEUTIG %s" % treffer_pfad
        status = "mehrdeutig"
    elif len(treffer_name) == 1:
        ziel = "Name vorhanden, andere Hierarchie (id %s)" % treffer_name[0]
        status = "Name"
    elif len(treffer_name) > 1:
        ziel = "MEHRDEUTIG ueber den Namen %s" % treffer_name
        status = "mehrdeutig"
    else:
        ziel = "neu anzulegen"
        status = "neu"
    schreibe("%-46s %-8d %-8d %-22s %-9s %s" % (k["complete_name"][:46], vorlagen, varianten,
                                                 ueber[:22], status, ziel))

schreibe("")
schreibe("--- Migrationsrelevante Felder der verwendeten Kategorien (Odoo 11) ---")
for k in sorted(verwendet, key=lambda x: x["complete_name"]):
    schreibe("   %-46s Erlöskonto=%-34s Aufwandskonto=%s" % (
        k["complete_name"][:46],
        (k["property_account_income_categ_id"] or ["-", "-"])[1][:34] if k["property_account_income_categ_id"] else "-",
        (k["property_account_expense_categ_id"] or ["-", "-"])[1][:34] if k["property_account_expense_categ_id"] else "-"))

schreibe("")
schreibe("--- Odoo-18-Bestand (%s) ---" % inst)
for k in sorted(kat18, key=lambda x: x["complete_name"]):
    schreibe("   id=%-5s %-40s Ueberkategorie=%s" % (k["id"], k["complete_name"], k["parent_id"]))

if len(sys.argv) > 2:
    with open(sys.argv[2], "w", encoding="utf-8") as fh:
        fh.write("\n".join(zeilen))
    print("\n[gespeichert: %s]" % sys.argv[2])
