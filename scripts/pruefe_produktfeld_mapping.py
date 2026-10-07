"""Read-only Vorlauf: loesen die Odoo-11-Produktfelder in Odoo 18 ueber fachliche Schluessel auf?

Prueft fuer den gesamten Odoo-11-Produktbestand, ob die in der Testmigrationsregel neu
aufgenommenen Felder (supplier_taxes_id, default_code, uom_id, uom_po_id, categ_id,
standard_price) im Odoo-18-Ziel ueber Namen zugeordnet werden koennen. Es wird NICHTS
geschrieben - weder in Odoo 11 noch in Odoo 18.

Aufruf: python scripts/pruefe_produktfeld_mapping.py lokal|vm [datei]
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
k11 = o11()
k18 = o18(inst)
CTX11 = {"lang": "de_DE"}
CTX18 = {"lang": "de_DE"}
FELDER = ["name", "default_code", "standard_price", "uom_id", "uom_po_id", "categ_id",
          "taxes_id", "supplier_taxes_id", "type", "sale_ok", "purchase_ok"]

zeilen = []


def schreibe(t=""):
    zeilen.append(t)
    print(t)


def name(wert):
    return wert[1] if isinstance(wert, (list, tuple)) and len(wert) > 1 else wert


# ------------------------------------------------------------------ 1. Odoo 11 lesen
ids = k11.kw("product.product", "search", [[]], context=CTX11)
produkte = []
for i in range(0, len(ids), 200):
    produkte += k11.kw("product.product", "read", [ids[i:i + 200], FELDER], context=CTX11)
schreibe("=== Read-only Vorlauf Produktfelder (%s) ===" % inst)
schreibe("Odoo 11: %d Produktvarianten gelesen" % len(produkte))

# ------------------------------------------------------------------ 2. Zielbestand Odoo 18
uoms = {u["name"]: u["id"] for u in k18.kw("uom.uom", "search_read", [[], ["name"]], context=CTX18)}
kategorien = {}
for kat in k18.kw("product.category", "search_read", [[], ["name", "complete_name"]], context=CTX18):
    kategorien[kat["name"]] = kat["id"]
    kategorien[kat["complete_name"]] = kat["id"]
steuern = {}
konflikte = []
for st in k18.kw("account.tax", "search_read", [[], ["name", "amount", "type_tax_use"]], context=CTX18):
    steuern.setdefault(st["name"], []).append("%s|%s" % (st["amount"], st["type_tax_use"]))
schreibe("Odoo 18 (%s): %d Einheiten, %d Kategorien, %d Steuernamen" % (inst, len(uoms), len(kategorien), len(steuern)))

# Odoo-11-Steuernamen mit Satz und Verwendung sammeln (Gegenprobe)
# Achtung: many2many-Felder liefern im RPC eine Liste von IDs, keine [id, name]-Paare.
def id_von(wert):
    return wert[0] if isinstance(wert, (list, tuple)) else wert


tax_ids = sorted({id_von(t) for p in produkte for f in ("taxes_id", "supplier_taxes_id")
                  for t in (p.get(f) or [])})
tax_info11 = {t["id"]: t for t in k11.kw("account.tax", "read", [tax_ids, ["id", "name", "amount", "type_tax_use"]],
                                         context=CTX11)} if tax_ids else {}


def loese(feld, wert):
    """Wert in Odoo 18 ueber den fachlichen Schluessel aufloesen."""
    if not wert:
        return None, "leer"
    if feld in ("uom_id", "uom_po_id"):
        return uoms.get(name(wert)), "Einheitenname"
    if feld == "categ_id":
        return kategorien.get(name(wert)), "Kategoriename"
    if feld in ("taxes_id", "supplier_taxes_id"):
        treffer = steuern.get(name(wert))
        if treffer:
            return treffer, "Steuername (%s)" % treffer[0]
        return None, "Steuername fehlt"
    return wert, "1:1"


# ------------------------------------------------------------------ 3. Aufloesung je Feld
zusammenfassung = {}
beispiele = {}
for feld in ("default_code", "standard_price", "uom_id", "uom_po_id", "categ_id",
             "taxes_id", "supplier_taxes_id"):
    belegt = 0
    aufgeloest = 0
    fehlend = []
    for p in produkte:
        if feld in ("taxes_id", "supplier_taxes_id"):
            werte = p.get(feld) or []
            if not werte:
                continue
            belegt += 1
            alle_ok = True
            for t in werte:
                o11_name = tax_info11.get(id_von(t), {}).get("name")
                ziel, wie = loese(feld, o11_name)
                if not ziel:
                    alle_ok = False
                    fehlend.append("%s (Odoo 11: %s)" % (p["name"], o11_name))
            aufgeloest += 1 if alle_ok else 0
        else:
            wert = p.get(feld)
            if wert in (None, False, "", 0, 0.0):
                continue
            belegt += 1
            ziel, wie = loese(feld, wert)
            if ziel:
                aufgeloest += 1
            else:
                fehlend.append("%s (Odoo 11: %s)" % (p["name"], name(wert)))
    zusammenfassung[feld] = (belegt, aufgeloest, len(fehlend))
    beispiele[feld] = fehlend[:5]

schreibe("")
schreibe("%-22s %8s %11s %9s" % ("Feld", "belegt", "aufloesbar", "offen"))
for feld, (belegt, aufgeloest, offen) in zusammenfassung.items():
    schreibe("%-22s %8d %11d %9d" % (feld, belegt, aufgeloest, offen))
schreibe("")
schreibe("Beispiele nicht aufloesbarer Werte (max. 5 je Feld):")
for feld, liste in beispiele.items():
    if liste:
        schreibe("   %-22s %s" % (feld, "; ".join(liste)))

# Steuer-Detailgegenprobe: Odoo-11-Name -> Odoo-18-Name/Satz
schreibe("")
schreibe("Verwendete Odoo-11-Steuern (Name | Satz | Verwendung) und Ziel in Odoo 18:")
for tid in tax_ids:
    t = tax_info11.get(tid)
    if not t:
        continue
    ziel = steuern.get(t["name"])
    schreibe("   %-28s %6s %-12s -> %s" % (t["name"], t["amount"], t["type_tax_use"],
                                           ("Odoo 18: %s" % ", ".join(ziel)) if ziel else "NICHT GEFUNDEN"))

if len(sys.argv) > 2:
    with open(sys.argv[2], "w", encoding="utf-8") as fh:
        fh.write("\n".join(zeilen))
    print("\n[gespeichert: %s]" % sys.argv[2])
