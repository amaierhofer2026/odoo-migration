"""Read-only Vorlauf: loesen die Odoo-11-Produktfelder in Odoo 18 ueber fachliche Schluessel auf?

Prueft fuer den gesamten Odoo-11-Produktbestand, ob die in der Testmigrationsregel aufgenommenen
Felder (supplier_taxes_id, taxes_id, default_code, uom_id, uom_po_id, categ_id, standard_price)
im Odoo-18-Ziel zugeordnet werden koennen. Verwendet **dieselben Funktionen wie die
Testmigration** (`steuer_im_ziel`, `kategorie_im_ziel`, `konto_im_ziel`), damit der Vorlauf nicht
von der dokumentierten Regel abweicht. Es wird NICHTS geschrieben - weder in Odoo 11 noch in
Odoo 18.

Aufruf: python scripts/pruefe_produktfeld_mapping.py lokal|vm [datei]
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402
import testmigration_abrechnung as tm  # noqa: E402

inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
CTX = {"lang": "de_DE"}
tm.CTX = CTX
k11 = o11()
k18 = o18(inst)
FELDER = ["name", "default_code", "standard_price", "uom_id", "uom_po_id", "categ_id",
          "taxes_id", "supplier_taxes_id"]

zeilen = []


def schreibe(t=""):
    zeilen.append(t)
    print(t)


def name(wert):
    return wert[1] if isinstance(wert, (list, tuple)) and len(wert) > 1 else wert


def id_von(wert):
    return wert[0] if isinstance(wert, (list, tuple)) else wert


# ------------------------------------------------------------------ 1. Odoo 11 lesen
ids = k11.kw("product.product", "search", [[]], context=CTX)
produkte = []
for i in range(0, len(ids), 200):
    produkte += k11.kw("product.product", "read", [ids[i:i + 200], FELDER], context=CTX)
schreibe("=== Read-only Vorlauf Produktfelder (%s), Regel aus testmigration_abrechnung ===" % inst)
schreibe("Odoo 11: %d Produktvarianten gelesen" % len(produkte))

kategorien11 = tm.lade_kategorien(k11)
tax_ids = sorted({id_von(t) for p in produkte for f in ("taxes_id", "supplier_taxes_id")
                  for t in (p.get(f) or [])})
tax_info11 = {t["id"]: t for t in k11.kw("account.tax", "read", [tax_ids, ["id", "name", "description",
                                                                           "amount", "type_tax_use"]],
                                         context=CTX)} if tax_ids else {}
uoms = {}
for u in k18.kw("uom.uom", "search_read", [[], ["name"]], context=CTX):
    uoms.setdefault(u["name"], []).append(u["id"])
schreibe("Odoo 18 (%s): %d Einheitennamen, %d Odoo-11-Kategorien gelesen, %d Odoo-11-Steuern verwendet"
         % (inst, len(uoms), len(kategorien11), len(tax_ids)))


def einheit_im_ziel(wert):
    """Mengeneinheit wie in der Testmigration: exakter Name, dann ohne Gross-/Kleinschreibung."""
    n = name(wert)
    treffer = uoms.get(n, [])
    if not treffer:
        treffer = [i for k, ids_ in uoms.items() if k.lower() == str(n).lower() for i in ids_]
    if len(treffer) == 1:
        return treffer[0], "Einheitenname"
    return None, ("nicht eindeutig (%d Treffer)" % len(treffer)) if treffer else "fehlt im Ziel"


# Caches: die Aufloesung haengt nur am Odoo-11-Datensatz, nicht am Produkt (spart RPC-Aufrufe).
einheit_cache = {}
steuer_cache = {}
kat_cache = {}


# ------------------------------------------------------------------ 2. Aufloesung je Feld
zusammenfassung = {}
beispiele = {}
for feld in ("default_code", "standard_price", "uom_id", "uom_po_id", "categ_id",
             "taxes_id", "supplier_taxes_id"):
    belegt = aufgeloest = offen = 0
    fehlend = []
    for p in produkte:
        if feld in ("taxes_id", "supplier_taxes_id"):
            werte = p.get(feld) or []
            if not werte:
                continue
            belegt += 1
            alle_ok = True
            for t in werte:
                t11 = tax_info11.get(id_von(t))
                if not t11:
                    alle_ok = False
                    fehlend.append("%s (Odoo-11-Steuer id %s nicht gelesen)" % (p["name"], id_von(t)))
                    continue
                if id_von(t) not in steuer_cache:
                    steuer_cache[id_von(t)] = tm.steuer_im_ziel(k18, t11)
                ziel, wie = steuer_cache[id_von(t)]
                if not ziel:
                    alle_ok = False
                    fehlend.append("%s (Odoo 11: %s)" % (p["name"], t11["name"]))
            aufgeloest += 1 if alle_ok else 0
            offen += 0 if alle_ok else 1
        elif feld == "categ_id":
            wert = p.get(feld)
            if not wert:
                continue
            belegt += 1
            kat_id = id_von(wert)
            if kat_id not in kat_cache:
                try:
                    kat_cache[kat_id] = tm.kategorie_im_ziel(k18, kategorien11, kat_id)
                except SystemExit as fehler:
                    kat_cache[kat_id] = (None, str(fehler)[:80])
            ziel, zustand = kat_cache[kat_id]
            if ziel:
                aufgeloest += 1
            else:
                offen += 1
                fehlend.append("%s (Odoo 11: %s -> %s)" % (p["name"], name(wert), zustand))
        elif feld in ("uom_id", "uom_po_id"):
            wert = p.get(feld)
            if not wert:
                continue
            belegt += 1
            if name(wert) not in einheit_cache:
                einheit_cache[name(wert)] = einheit_im_ziel(wert)
            ziel, wie = einheit_cache[name(wert)]
            if ziel:
                aufgeloest += 1
            else:
                offen += 1
                fehlend.append("%s (Odoo 11: %s -> %s)" % (p["name"], name(wert), wie))
        else:  # default_code, standard_price: 1:1
            wert = p.get(feld)
            if wert in (None, False, "", 0, 0.0):
                continue
            belegt += 1
            aufgeloest += 1
    zusammenfassung[feld] = (belegt, aufgeloest, offen)
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

schreibe("")
schreibe("Verwendete Odoo-11-Steuern (Name | Satz | Verwendung) und Ziel in Odoo 18:")
for tid in tax_ids:
    t = tax_info11.get(tid)
    if not t:
        continue
    ziel, wie = tm.steuer_im_ziel(k18, t)
    schreibe("   %-28s %6s %-12s -> %s" % (t["name"], t["amount"], t["type_tax_use"],
                                           ("Odoo 18: id %s (%s)" % (ziel, wie)) if ziel
                                           else "NICHT GEFUNDEN - %s" % wie))

schreibe("")
schreibe("Konten der Produktkategorien (Odoo 11 -> Odoo 18, es wird nichts angelegt):")
geprueft = set()
for kat_id, kat in sorted(kategorien11.items()):
    for feld, beschriftung in (("property_account_income_categ_id", "Erloeskonto"),
                               ("property_account_expense_categ_id", "Aufwandskonto")):
        konto11 = (kat.get("konten") or {}).get(feld)
        if not konto11 or (feld, konto11["id"]) in geprueft:
            continue
        geprueft.add((feld, konto11["id"]))
        ziel, begruendung = tm.konto_im_ziel(k18, konto11)
        schreibe("   %-15s %-30s -> %s" % (beschriftung, "%s %s" % (konto11["code"], konto11["name"]),
                                           ("Odoo 18: id %s (%s)" % (ziel, begruendung)) if ziel
                                           else "BLOCKER: %s" % begruendung))

if len(sys.argv) > 2:
    with open(sys.argv[2], "w", encoding="utf-8") as fh:
        fh.write("\n".join(zeilen))
    print("\n[gespeichert: %s]" % sys.argv[2])
