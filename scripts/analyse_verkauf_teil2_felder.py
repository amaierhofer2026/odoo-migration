"""Read-only Feldinventar Verkauf Teil 2: sale.order und sale.order.line.

Sammelt fuer Odoo 11 Prod (nur lesend), Odoo 18 lokal und Odoo 18 VM:
  - jedes Feld des Modells (Name, Beschriftung, Typ, Relation, Pflicht, readonly, gespeichert,
    berechnet/related, Herkunftsmodul, uebersetzbar)
  - Anzahl der Datensaetze mit Wert je Feld (nur bei gespeicherten Feldern)
  - Selection-Werte je Auswahlfeld

Ergebnis: docs/_verkauf_teil2_felder.json (Analyse-Artefakt, nicht im Repo) und eine Kurzausgabe.

Aufruf:
    python scripts/analyse_verkauf_teil2_felder.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELLE = ["sale.order", "sale.order.line"]
ATTRS_IMF = ["name", "field_description", "ttype", "relation", "required", "readonly", "store",
             "related", "modules", "selectable", "translate", "state", "help", "index"]


def felder(k, modell: str) -> dict:
    """Feldinventar eines Modells inkl. Nutzungszaehlung."""
    imf = k.kw("ir.model.fields", "search_read",
               [[["model", "=", modell]], ATTRS_IMF], order="name", context={"lang": "de_DE"})
    # Beschriftungen und Auswahlwerte in der Anzeigesprache zusaetzlich direkt vom Modell holen
    fg = k.kw(modell, "fields_get", [[], ["string", "type", "relation", "selection", "required",
                                          "readonly", "store", "help"]], context={"lang": "de_DE"})
    gesamt = k.kw(modell, "search_count", [[]])
    ergebnis = {}
    for f in imf:
        name = f["name"]
        info = {
            "beschriftung": f.get("field_description"),
            "ttype": f.get("ttype"),
            "relation": f.get("relation") or None,
            "pflicht": bool(f.get("required")),
            "readonly": bool(f.get("readonly")),
            "gespeichert": bool(f.get("store")),
            "related": f.get("related") or None,
            "module": f.get("modules") or "",
            "uebersetzbar": bool(f.get("translate")),
            "state": f.get("state"),
            "selectable": bool(f.get("selectable")),
            "help": (f.get("help") or "").strip() or None,
            "anzeige": (fg.get(name) or {}).get("string"),
            "pflicht_anzeige": bool((fg.get(name) or {}).get("required")),
        }
        sel = (fg.get(name) or {}).get("selection")
        if sel:
            info["selection"] = [[str(a), str(b)] for a, b in sel]
        if info["gespeichert"] and not info["related"]:
            try:
                info["belegt"] = k.kw(modell, "search_count", [[[name, "!=", False]]])
            except Exception as fehler:
                info["belegt"] = "FEHLER: %s" % str(fehler)[:60]
        else:
            info["belegt"] = None
        ergebnis[name] = info
    return {"modell": modell, "datensaetze": gesamt, "felder": ergebnis}


def main() -> int:
    daten = {}
    for schluessel, client in (("o11", o11()), ("o18", o18("lokal")), ("vm", o18("vm"))):
        daten[schluessel] = {m: felder(client, m) for m in MODELLE}
        print("%s fertig" % schluessel.upper())
        for m in MODELLE:
            print("   %-16s %3d Felder, %d Datensaetze" % (m, len(daten[schluessel][m]["felder"]),
                                                           daten[schluessel][m]["datensaetze"]))

    ziel = os.path.join(REPO, "docs", "_verkauf_teil2_felder.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("Daten: %s" % ziel)

    print("\n--- Vergleich Odoo 11 gegen Odoo 18 lokal ---")
    for m in MODELLE:
        a = set(daten["o11"][m]["felder"])
        b = set(daten["o18"][m]["felder"])
        print("%s: O11 %d | O18 %d | gemeinsam %d | nur O11 %d | nur O18 %d"
              % (m, len(a), len(b), len(a & b), len(a - b), len(b - a)))
        typfehler = [(n, daten["o11"][m]["felder"][n]["ttype"], daten["o18"][m]["felder"][n]["ttype"],
                      daten["o11"][m]["felder"][n]["relation"], daten["o18"][m]["felder"][n]["relation"])
                     for n in sorted(a & b)
                     if daten["o11"][m]["felder"][n]["ttype"] != daten["o18"][m]["felder"][n]["ttype"]
                     or (daten["o11"][m]["felder"][n]["relation"] or "") != (daten["o18"][m]["felder"][n]["relation"] or "")]
        print("   Typ-/Relationsabweichungen: %d" % len(typfehler))
        for t in typfehler:
            print("      %-28s O11 %s%s -> O18 %s%s" % (t[0], t[1], "/" + str(t[3]) if t[3] else "",
                                                        t[2], "/" + str(t[4]) if t[4] else ""))
    print("\n--- Menue-/Feldzahlen Odoo 18 VM gegen lokal ---")
    for m in MODELLE:
        print("%s: lokal %d | VM %d | identische Namen %s"
              % (m, len(daten["o18"][m]["felder"]), len(daten["vm"][m]["felder"]),
                 set(daten["o18"][m]["felder"]) == set(daten["vm"][m]["felder"])))
    print("\nOdoo 11 Prod wurde ausschliesslich lesend verwendet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
