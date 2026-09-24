"""Abnahmepruefung Bereich Verkauf Teil 2 (Session 121): Feldinventar sale.order/-line.

Prueft READ-ONLY:
  - Odoo 11 Prod: Feldlisten und Nutzungszahlen (nur lesend)
  - Odoo 18 lokal und VM: jedes Odoo-11-Feld hat ein Ziel (gleicher Name, gleicher Typ,
    gleiche Relation) oder ist im Dokument als "kein Ziel vorhanden"/"obsolet" gefuehrt
  - Selection-Werte der gemeinsamen Auswahlfelder stimmen ueberein
  - die als entfallen dokumentierten Felder fehlen in Odoo 18 wirklich
  - ITK-Felder sind mit gleichem Typ und gleicher Relation vorhanden

Aufruf:
    python scripts/verify_s121_verkauf_teil2.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18
from baue_verkauf_teil2_doku import OHNE_ZIEL, TRANSFORMATION

MODELLE = ["sale.order", "sale.order.line"]

# Bewusste, dokumentierte Abweichung bei Auswahlwerten: Odoo 11 kennt den Status "done"
# (0 Datensaetze in Produktivdaten), Odoo 18 fuehrt dafuer "sale" + locked.
SELEKTION_ABWEICHUNG = {
    ("sale.order", "state"): {"done"},
    ("sale.order.line", "state"): {"done"},
}
ITK_FELDER = {
    "sale.order": ["sale_contact_id", "administrative_contact_id", "technical_contact_id",
                   "final_customer_id", "product_category_id", "confirmation_date",
                   "subscription_management"],
    "sale.order.line": ["qty_multiplication_factor", "subscription_id", "partner_id", "salesperson_id"],
}


def inventar(k, modell, mit_nutzung=False):
    fg = k.kw(modell, "fields_get", [[], ["string", "type", "relation", "selection", "required", "store"]],
              context={"lang": "de_DE"})
    daten = {n: {"ttype": f.get("type"), "relation": f.get("relation") or "",
                 "selection": [x[0] for x in f.get("selection") or []],
                 "pflicht": bool(f.get("required"))} for n, f in fg.items()}
    if mit_nutzung:
        daten["__gesamt__"] = k.kw(modell, "search_count", [[]])
    return daten


def main() -> int:
    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    k11, k18, kvm = o11(), o18("lokal"), o18("vm")
    for modell in MODELLE:
        print("\n=== %s ===" % modell)
        a = inventar(k11, modell)
        b = inventar(k18, modell)
        v = inventar(kvm, modell)
        ohne = OHNE_ZIEL[modell]
        print("       Felder: Odoo 11 %d | Odoo 18 lokal %d | VM %d" % (len(a), len(b), len(v)))

        pruefe(set(b) == set(v), "Odoo 18 lokal und VM haben dieselben Felder")

        ziel = fehlt = 0
        abweichung = []
        for n, f in a.items():
            if n not in b:
                if n in ohne:
                    fehlt += 1
                else:
                    abweichung.append("%s (kein Ziel und nicht dokumentiert)" % n)
                continue
            if f["ttype"] != b[n]["ttype"] or f["relation"] != b[n]["relation"]:
                if (modell, n) not in TRANSFORMATION:
                    abweichung.append("%s (Typ/Relation: %s%s -> %s%s)"
                                      % (n, f["ttype"], "/" + f["relation"] if f["relation"] else "",
                                         b[n]["ttype"], "/" + b[n]["relation"] if b[n]["relation"] else ""))
                else:
                    ziel += 1
            else:
                ziel += 1
        pruefe(not abweichung, "jedes Odoo-11-Feld hat ein Ziel oder ist dokumentiert "
                               "(mit Ziel %d, dokumentiert ohne Ziel %d)" % (ziel, fehlt))
        for x in abweichung:
            print("       %s" % x)

        for n in ohne:
            pruefe(n not in b, "dokumentiert entfallen: '%s' fehlt in Odoo 18 wirklich" % n)
            pruefe(n in a, "dokumentiert entfallen: '%s' existiert in Odoo 11" % n)

        sel = [n for n in a if a[n]["selection"] and n in b]
        ungleich = []
        for n in sel:
            if a[n]["selection"] == b[n]["selection"]:
                continue
            erwartet = SELEKTION_ABWEICHUNG.get((modell, n), set())
            nur11 = set(a[n]["selection"]) - set(b[n]["selection"])
            nur18 = set(b[n]["selection"]) - set(a[n]["selection"])
            if erwartet and nur11 == erwartet and not nur18:
                continue
            ungleich.append(n)
        pruefe(not ungleich, "Selection-Werte identisch bzw. dokumentiert abweichend "
                             "bei %d gemeinsamen Auswahlfeldern" % len(sel))
        for n in ungleich:
            print("       %s: O11 %s | O18 %s" % (n, a[n]["selection"], b[n]["selection"]))
        for (m, n), erwartet in SELEKTION_ABWEICHUNG.items():
            if m != modell or n not in a or n not in b:
                continue
            pruefe(set(a[n]["selection"]) - set(b[n]["selection"]) == erwartet,
                   "dokumentierte Statusabweichung '%s': Odoo 11 ohne Odoo 18 nur %s"
                   % (n, ", ".join(sorted(erwartet))))

        for n in ITK_FELDER[modell]:
            pruefe(n in a and n in b and a[n]["ttype"] == b[n]["ttype"]
                   and a[n]["relation"] == b[n]["relation"],
                   "ITK-Feld '%s' in beiden Systemen mit gleichem Typ/Relation" % n)

    print("\n--- Nutzungszahlen Odoo 11 (read-only) ---")
    for modell, soll in (("sale.order", 2000), ("sale.order.line", 4000)):
        n = k11.kw(modell, "search_count", [[]])
        pruefe(n >= soll, "Odoo 11 %s: %d Datensaetze (mindestens %d erwartet)" % (modell, n, soll))

    print("\n%d OK / %d FEHL" % (ok, fehler))
    print("Odoo 11 Prod wurde ausschliesslich lesend verwendet, Odoo 18 nicht veraendert.")
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
