"""Read-only: Kontenzuordnung der Produktkategorien Odoo 11 -> Odoo 18.

Aufruf: python scripts/pruefe_kategorie_kontenzuordnung.py

1. Odoo 11: die beiden Konten 8400/3400 vollstaendig lesen (Nummer, Name, Kontotyp, weitere
   fachliche Merkmale) - Grundlage fuer die Zuordnung ueber stabile Schluessel.
2. Odoo 18 (lokal + VM): Zielkontenrahmen pruefen - exakte Nummer, Namensmuster, Kontotyp,
   Kategoriekonten. Es wird NICHTS angelegt und NICHTS geraten.
"""
from __future__ import annotations

import sys

sys.path.insert(0, "C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
FELDER11 = ["code", "name", "internal_type", "user_type_id", "reconcile", "deprecated",
            "currency_id", "company_id"]
FELDER18 = ["code", "name", "account_type", "reconcile"]

print("=== 1. Odoo 11: die beiden Kategoriekonten ===")
k = o11()
ids = k.kw("account.account", "search", [[("code", "in", ["8400", "3400"])]], context=CTX)
for a in k.kw("account.account", "read", [ids, FELDER11], context=CTX):
    print("   %-6s %-34s intern=%-8s Typ=%s abgleich=%s gesperrt=%s"
          % (a["code"], a["name"], a["internal_type"], a["user_type_id"], a["reconcile"],
             a.get("deprecated")))
print("   Odoo-11-Kontenrahmen gesamt: %d" % k.kw("account.account", "search_count", [[]], context=CTX))

print("\n=== 2. Odoo 18: Zielkontenrahmen ===")
for inst in ("lokal", "vm"):
    z = o18(inst)
    print("--- %s ---" % inst)
    print("   Konten gesamt: %d" % z.kw("account.account", "search_count", [[]], context=CTX))
    for code in ("8400", "3400"):
        treffer = z.kw("account.account", "search_read", [[("code", "=", code)], FELDER18], context=CTX)
        print("   Konto %s exakt: %s" % (code, treffer if treffer else "NICHT VORHANDEN"))
    for muster in ("Erlös", "Erloes", "Wareneingang", "Wareneinkauf"):
        treffer = z.kw("account.account", "search_read", [[("name", "ilike", muster)], FELDER18],
                       context=CTX)
        print("   Name enthaelt %-13s: %d Treffer %s"
              % (muster, len(treffer), [(a["code"], a["name"][:40], a["account_type"]) for a in treffer[:6]]))
    for typ in ("income", "income_other", "expense", "expense_direct_cost"):
        treffer = z.kw("account.account", "search_read", [[("account_type", "=", typ)], FELDER18],
                       context=CTX)
        print("   Kontotyp %-20s: %3d Konten %s"
              % (typ, len(treffer), [(a["code"], a["name"][:26]) for a in treffer[:5]]))
    print("   Kategoriekonten im Ziel: %s"
          % z.kw("product.category", "search_read", [[], ["complete_name",
                                                          "property_account_income_categ_id",
                                                          "property_account_expense_categ_id"]],
                 context=CTX))
    print("   Unternehmen-Standardkonten (res.company): %s"
          % z.kw("res.company", "search_read", [[], ["name", "income_currency_exchange_account_id",
                                                     "expense_currency_exchange_account_id"]],
                 context=CTX))
