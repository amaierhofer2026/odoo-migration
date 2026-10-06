"""Absicherung der beiden Produktformular-Abweichungen in Odoo 11 (read-only).

1. Bilder: nutzt Odoo 11 den Bereich Produktbilder/Anhaenge ueberhaupt?
2. Varianten: gibt es produktive Varianten/Attribute, die von product.product auf
   product.template Probleme machen koennten?

Aufruf: python scripts/pruefe_o11_bilder_und_varianten.py
Nur Leseaufrufe (search_count, search_read, read, read_group).
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11  # noqa: E402

k = o11()
CTX = {"lang": "de_DE"}

print("=" * 78)
print("1. BILDER / ANHAENGE IN ODOO 11")
print("=" * 78)

vorlagen = k.kw("product.template", "search", [[]], context=CTX)
varianten = k.kw("product.product", "search", [[]], context=CTX)
print("product.template: %d | product.product: %d" % (len(vorlagen), len(varianten)))

try:
    n_img = k.kw("product.image", "search_count", [[]], context=CTX)
    print("product.image Datensaetze: %d" % n_img)
    if n_img:
        bilder = k.kw("product.image", "search_read", [[], ["name", "product_tmpl_id", "image"]],
                      context=CTX)
        for b in bilder[:20]:
            print("   ", b["id"], b.get("name"), "->", b.get("product_tmpl_id"),
                  "Bilddaten:", bool(b.get("image")))
        print("   Vorlagen mit Zusatzbildern:", len({b["product_tmpl_id"][0] for b in bilder
                                                   if b.get("product_tmpl_id")}))
except Exception as e:
    print("product.image Fehler:", str(e)[:120])

# Hauptbilder der Vorlagen/Varianten (binary-Felder -> ir.attachment mit res_field)
for modell, ids in (("product.template", vorlagen), ("product.product", varianten)):
    for feld in ("image", "image_medium", "image_small"):
        try:
            w = k.kw(modell, "read", [ids, [feld]], context=CTX)
            belegt = sum(1 for x in w if x.get(feld))
            print("%-16s %-13s belegt: %d/%d" % (modell, feld, belegt, len(ids)))
        except Exception as e:
            print("%-16s %-13s Fehler: %s" % (modell, feld, str(e)[:60]))

# Anhaenge je Produktmodell
for modell in ("product.template", "product.product", "product.image", "product.supplierinfo"):
    try:
        an = k.kw("ir.attachment", "search_read",
                  [[["res_model", "=", modell]], ["name", "res_id", "res_field", "mimetype"]],
                  context=CTX)
        bilder = [a for a in an if (a.get("mimetype") or "").startswith("image/")]
        felder = collections.Counter(a.get("res_field") or "(Datei)" for a in an)
        print("Anhaenge an %-20s: %d | davon Bilder: %d | nach res_field: %s"
              % (modell, len(an), len(bilder), dict(felder)))
        for a in an[:10]:
            print("     ", a["id"], a.get("name"), "res_id=%s" % a.get("res_id"),
                  "res_field=%s" % a.get("res_field"), a.get("mimetype"))
    except Exception as e:
        print("Anhaenge %s Fehler: %s" % (modell, str(e)[:80]))

print()
print("=" * 78)
print("2. VARIANTEN / ATTRIBUTE IN ODOO 11")
print("=" * 78)

je_vorlage = collections.Counter()
for v in k.kw("product.product", "search_read", [[], ["product_tmpl_id"]], context=CTX):
    je_vorlage[v["product_tmpl_id"][0]] += 1
mehrfach = {t: n for t, n in je_vorlage.items() if n > 1}
print("Vorlagen insgesamt: %d | Vorlagen mit mehr als einer Variante: %d"
      % (len(je_vorlage), len(mehrfach)))
if mehrfach:
    namen = k.kw("product.template", "read", [sorted(mehrfach)[:30], ["name", "type", "active"]],
                 context=CTX)
    for n in namen:
        print("   Vorlage %s (%s, aktiv=%s): %d Varianten" % (n["id"], n["name"], n["active"],
                                                              mehrfach[n["id"]]))

for modell in ("product.attribute", "product.attribute.value", "product.attribute.line"):
    try:
        print("%-34s Datensaetze: %d" % (modell, k.kw(modell, "search_count", [[]], context=CTX)))
    except Exception as e:
        print("%-34s Fehler: %s" % (modell, str(e)[:60]))

try:
    print("Attribute:", k.kw("product.attribute", "search_read", [[], ["name", "type", "create_variant"]],
                             context=CTX))
    print("Attributwerte:", k.kw("product.attribute.value", "search_read",
                                 [[], ["name", "attribute_id"]], context=CTX))
except Exception as e:
    print("Attribute lesen Fehler:", str(e)[:80])

try:
    zeilen = k.kw("product.attribute.line", "search_read",
                  [[], ["product_tmpl_id", "attribute_id", "value_ids"]], context=CTX)
    print("Attributzeilen an Vorlagen (product.attribute.line): %d" % len(zeilen))
    for z in zeilen[:20]:
        print("   ", z["product_tmpl_id"], z["attribute_id"], z["value_ids"])
except Exception as e:
    print("Attributzeilen Fehler:", str(e)[:80])

# Vorlagen ohne Variante
ohne = [t for t in vorlagen if t not in je_vorlage]
print("Vorlagen ohne product.product: %d %s" % (len(ohne), ohne[:10]))
for t in k.kw("product.template", "read", [ohne[:10], ["id", "name", "type", "active", "sale_ok",
                                                       "purchase_ok", "recurring_invoice"]],
              context=CTX):
    print("   ", t)
# Varianten ohne vorhandene Vorlage
try:
    alle_tpl = set(k.kw("product.template", "search", [[]], context=CTX))
    print("Varianten mit fehlender Vorlage:",
          len([v for v in varianten if v not in alle_tpl]), "(Pruefung gegen Vorlagen-IDs, nur Info)")
except Exception as e:
    print("Fehler:", str(e)[:80])

# Variantenzuordnung in Belegen: verweisen Belege auf Varianten mit mehreren Geschwistern?
try:
    prod = k.kw("product.product", "read", [varianten, ["product_tmpl_id", "attribute_value_ids"]],
                context=CTX)
    mit_attributen = [p for p in prod if p.get("attribute_value_ids")]
    print("Varianten mit Attributwerten (attribute_value_ids): %d von %d"
          % (len(mit_attributen), len(prod)))
except Exception as e:
    print("attribute_value_ids Fehler:", str(e)[:80])

for modell, feld in (("account.move.line", "product_id"), ("sale.order.line", "product_id"),
                     ("purchase.order.line", "product_id"), ("sale.subscription.line", "product_id"),
                     ("stock.move", "product_id")):
    try:
        ids = k.kw(modell, "search_read", [[[feld, "!=", False]], [feld]], context=CTX)
        verwendete = {x[feld][0] for x in ids if x.get(feld)}
        gefaehrdet = verwendete & set(mehrfach)  # Varianten-IDs, nicht Vorlagen: nur Info
        print("%-24s Zeilen mit Produkt: %-6d verschiedene Produkte: %-5d" %
              (modell, len(ids), len(verwendete)))
    except Exception as e:
        print("%-24s Fehler: %s" % (modell, str(e)[:70]))

# Sind die in Belegen verwendeten Produkte Varianten mit mehreren Geschwistern?
try:
    zeilen_all = k.kw("account.move.line", "search_read", [[["product_id", "!=", False]], ["product_id"]],
                      context=CTX)
    ver = k.kw("product.product", "read", [list({z["product_id"][0] for z in zeilen_all}),
                                           ["id", "product_tmpl_id"]], context=CTX)
    mehrfach_verwendet = [v for v in ver if je_vorlage[v["product_tmpl_id"][0]] > 1]
    print("Rechnungszeilen nutzen %d verschiedene Produkte; davon aus Vorlagen mit mehreren "
          "Varianten: %d" % (len(ver), len(mehrfach_verwendet)))
    for v in mehrfach_verwendet[:10]:
        print("   Variante %s -> Vorlage %s (%d Varianten)" % (v["id"], v["product_tmpl_id"][0],
                                                              je_vorlage[v["product_tmpl_id"][0]]))
except Exception as e:
    print("Rechnungszeilen-Auswertung Fehler:", str(e)[:100])

# Templates mit Attributen, aber nur einer Variante (Haelfte der Faelle)
try:
    tpl_attr = {z["product_tmpl_id"][0] for z in
                k.kw("product.attribute.line", "search_read", [[], ["product_tmpl_id"]],
                     context=CTX)}
    print("Vorlagen mit Attributzeilen: %d | davon mit mehr als einer Variante: %d"
          % (len(tpl_attr), len(tpl_attr & set(mehrfach))))

    # Variantenzuordnung in allen belegrelevanten Modellen pruefen
    for modell, feld in (("account.move.line", "product_id"), ("sale.order.line", "product_id"),
                         ("purchase.order.line", "product_id"),
                         ("sale.subscription.line", "product_id"), ("stock.move", "product_id")):
        z = k.kw(modell, "search_read", [[[feld, "!=", False]], [feld]], context=CTX)
        pids = list({x[feld][0] for x in z if x.get(feld)})
        if not pids:
            print("%-24s keine Produktzeilen" % modell)
            continue
        ver = k.kw("product.product", "read", [pids, ["id", "product_tmpl_id"]], context=CTX)
        mehr = [v for v in ver if je_vorlage[v["product_tmpl_id"][0]] > 1]
        doppelt = collections.Counter(v["product_tmpl_id"][0] for v in ver)
        print("%-24s %d Zeilen, %d Produkte, aus Mehrfachvarianten-Vorlagen: %d, "
              "Vorlagen mit mehreren verwendeten Varianten: %d"
              % (modell, len(z), len(pids), len(mehr),
                 len([t for t, n in doppelt.items() if n > 1])))
except Exception as e:
    print("Auswertung Attribute/Mehrfachvarianten Fehler:", str(e)[:80])
