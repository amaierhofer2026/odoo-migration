"""Read-only: Konten an product.category in Odoo 11 und Referenzen der Kategorien.

Aufruf: python scripts/pruefe_kategorie_konten_und_referenzen.py [o11|o18-lokal|o18-vm]

Odoo 11:
  1. ir.property-Eintraege zu property_account_income_categ_id /
     property_account_expense_categ_id (je Kategorie UND global) - zeigt, wo der Wert wirklich
     gespeichert ist (Eigenwert der Kategorie oder Firmenvorgabe).
  2. Alle property_-Felder je verwendeter Kategorie, inkl. Lager-/Bewertungskonten.
  3. Alle Felder, die ueberhaupt auf product.category verweisen (ir.model.fields, relation),
     und die Trefferzahlen der 4 unbenutzten Kategorien in diesen Feldern.
"""
from __future__ import annotations

import sys

sys.path.insert(0, "C:/Odoo-Test/scripts")
from _o11o18_client import o11  # noqa: E402

CTX = {"lang": "de_DE"}
k = o11()

print("=== 1. ir.property: Kontenfelder der Produktkategorien (Odoo 11) ===")
namen = ["property_account_income_categ_id", "property_account_expense_categ_id"]
felder = k.kw("ir.model.fields", "search_read",
              [[("model", "=", "product.category"), ("name", "in", namen)],
               ["id", "name", "field_description"]], context=CTX)
print("   Felder: %s" % [(f["name"], f["field_description"]) for f in felder])
ids = [f["id"] for f in felder]
eintraege = k.kw("ir.property", "search_read",
                 [[("fields_id", "in", ids)], ["name", "res_id", "value_reference", "company_id"]],
                 context=CTX) if ids else []
print("   ir.property-Eintraege gesamt: %d" % len(eintraege))
global_ = [e for e in eintraege if not e["res_id"]]
je_kat = [e for e in eintraege if e["res_id"]]
print("   davon global (res_id leer, gilt fuer alle Kategorien): %d" % len(global_))
print("   davon kategoriespezifisch: %d" % len(je_kat))
for e in global_:
    print("      GLOBAL   %-38s -> %-28s (Firma %s)"
          % (e["name"], e["value_reference"], e["company_id"]))
for e in sorted(je_kat, key=lambda x: x["res_id"])[:30]:
    print("      KATEGORIE %-38s res_id=%-24s -> %s" % (e["name"], e["res_id"], e["value_reference"]))

print("\n=== 2. property_-Felder je verwendeter Kategorie (Auswahl: Konten) ===")
kat_ids = k.kw("product.category", "search", [[]], context=CTX)
kat = k.kw("product.category", "read", [kat_ids, ["complete_name", "property_account_income_categ_id",
                                                  "property_account_expense_categ_id"]], context=CTX)
werte = {}
for x in kat:
    werte.setdefault((str(x["property_account_income_categ_id"]),
                      str(x["property_account_expense_categ_id"])), []).append(x["complete_name"])
print("   verschiedene Wertepaare: %d" % len(werte))
for (ein, aus), namensliste in werte.items():
    print("      Erlös=%s | Aufwand=%s | %d Kategorien: %s"
          % (ein, aus, len(namensliste), ", ".join(namensliste[:6]) + (" ..." if len(namensliste) > 6 else "")))

print("\n=== 3. Felder mit Bezug auf product.category (Odoo 11) ===")
bezug = k.kw("ir.model.fields", "search_read",
             [[("relation", "=", "product.category"), ("ttype", "in", ["many2one", "many2many"])],
              ["model", "name", "ttype", "field_description"]], context=CTX)
print("   %d Felder in %d Modellen" % (len(bezug), len({b["model"] for b in bezug})))
unbenutzt = {2: "verkaufbar", 34: "Transaktionen", 45: "amtsweg.gv.at Premium Standard",
             59: "Whistleblowing"}
verwendet_ids = set()
for pid in k.kw("product.template", "search", [[]], context=CTX):
    pass
for p in k.kw("product.template", "search_read", [[], ["categ_id"]], context=CTX):
    if p["categ_id"]:
        verwendet_ids.add(p["categ_id"][0])
print("   Kategorien mit Produkten: %d | ohne Produkt: %d" % (len(verwendet_ids), len(unbenutzt)))
print("\n   Referenzen der 4 unbenutzten Kategorien:")
for kid, kname in unbenutzt.items():
    treffer = []
    for b in bezug:
        if b["model"] == "product.category" and b["name"] == "parent_id":
            continue
        try:
            n = k.kw(b["model"], "search_count", [[(b["name"], "=", kid)]], context=CTX)
        except Exception as fehler:  # Modell/Feld nicht lesbar
            treffer.append("%s.%s: nicht lesbar (%s)" % (b["model"], b["name"], str(fehler)[:40]))
            continue
        if n:
            treffer.append("%s.%s: %d" % (b["model"], b["name"], n))
    kinder = k.kw("product.category", "search_count", [[("parent_id", "=", kid)]], context=CTX)
    if kinder:
        treffer.append("product.category.parent_id: %d" % kinder)
    print("      id %-3s %-32s -> %s" % (kid, kname, ", ".join(treffer) if treffer else "keine Referenz"))

print("\n   Gegenprobe - dieselbe Abfrage fuer alle 26 verwendeten Kategorien (nur Treffer):")
for kid in sorted(verwendet_ids):
    treffer = []
    for b in bezug:
        if b["model"] == "product.category" and b["name"] == "parent_id":
            continue
        if b["model"] == "product.template" and b["name"] == "categ_id":
            continue  # das ist die Verwendung selbst
        try:
            n = k.kw(b["model"], "search_count", [[(b["name"], "=", kid)]], context=CTX)
        except Exception:
            continue
        if n:
            treffer.append("%s.%s=%d" % (b["model"], b["name"], n))
    kinder = k.kw("product.category", "search_count", [[("parent_id", "=", kid)]], context=CTX)
    if kinder:
        treffer.append("Kinder=%d" % kinder)
    if treffer:
        print("      id %-4s -> %s" % (kid, ", ".join(treffer)))
