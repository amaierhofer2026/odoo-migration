"""Read-only Analyse Verkauf Teil 3, Schritt 1: Formulare und Reiter.

Vergleicht fuer sale.order und sale.order.line:
  - alle Formularansichten (ir.ui.view) in Odoo 11, Odoo 18 lokal und Odoo 18 VM
  - die Ansicht, die die Auftragsbearbeitung tatsaechlich oeffnet (Menueaktionen)
  - Reiter (Seiten) des Formulars mit Reihenfolge und den je Reiter sichtbaren Feldern

Schreibt docs/_verkauf_teil3_formulare.json und gibt eine Kurzuebersicht aus.

Aufruf:
    python scripts/analyse_verkauf_teil3_formulare.py
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELLE = ["sale.order", "sale.order.line"]

KEIN_STRING = re.compile(r"<field\s+[^>]*name=\"([^\"]+)\"[^>]*>")


def formular_arch(k, modell: str, odoo18: bool) -> str:
    if odoo18:
        daten = k.kw(modell, "get_views", [[[False, "form"]]], context={"lang": "de_DE"})
        return daten["views"]["form"]["arch"]
    # Odoo 11: fields_view_get(view_id, view_type, fields) - bewaehrtes Aufrufmuster dieses Repos
    return k.kw(modell, "fields_view_get", [False, "form", "form"], context={"lang": "de_DE"})["arch"]


def gruppen_im_block(block: str) -> dict:
    """Gruppen (mit Beschriftung) und die darin enthaltenen Felder, grob verschachtelt geparst."""
    ergebnis = {}
    for m in re.finditer(r"<group\b([^>]*)>", block):
        attrs = m.group(1)
        string = (re.search(r'string="([^"]*)"', attrs) or [None, None])[1]
        if not string:
            continue
        rest = block[m.end():]
        tiefe, ende = 1, len(rest)
        for t in re.finditer(r"<group\b[^>]*>|</group>", rest):
            tiefe += 1 if t.group(0).startswith("<group") else -1
            if tiefe == 0:
                ende = t.start()
                break
        ergebnis.setdefault(string, [])
        for f in KEIN_STRING.findall(rest[:ende]):
            if f not in ergebnis[string]:
                ergebnis[string].append(f)
    return ergebnis


def hauptbereich(arch: str) -> dict:
    """Formularinhalt vor dem Notebook: Felder und Gruppen."""
    vor = arch.split("<notebook", 1)[0]
    return {"felder": KEIN_STRING.findall(vor), "gruppen": gruppen_im_block(vor)}


def seiten(arch: str) -> list:
    """Reiter (page) mit Reihenfolge, Beschriftung und den enthaltenen Feldern."""
    ergebnis = []
    for treffer in re.finditer(r"<page\b([^>]*)>", arch):
        attrs = treffer.group(1)
        name = (re.search(r'name="([^"]*)"', attrs) or [None, "?"])[1]
        string = (re.search(r'string="([^"]*)"', attrs) or [None, None])[1]
        # Block bis zum passenden </page>
        rest = arch[treffer.end():]
        tiefe, ende = 1, len(rest)
        for m in re.finditer(r"<page\b[^>]*>|</page>", rest):
            tiefe += 1 if m.group(0).startswith("<page") else -1
            if tiefe == 0:
                ende = m.start()
                break
        block = rest[:ende]
        felder = [f for f in KEIN_STRING.findall(block)]
        ergebnis.append({"name": name, "string": string, "felder": felder,
                         "feld_anzahl": len(felder),
                         "gruppen": gruppen_im_block(block),
                         "struktur": re.findall(r"<(group|separator|notebook|div)\b[^>]*name=\"([^\"]+)\"", block)})
    return ergebnis


def ansichten(k, modell: str, odoo18: bool) -> list:
    views = k.kw("ir.ui.view", "search_read", [[["model", "=", modell], ["type", "=", "form"]],
                                               ["id", "name", "priority", "mode", "active"]],
                 order="priority,name", context={"lang": "de_DE"})
    daten = {}
    for v in views:
        imd = k.kw("ir.model.data", "search_read",
                   [[["model", "=", "ir.ui.view"], ["res_id", "=", v["id"]]], ["module", "name"]])
        v["modul"] = ", ".join(sorted({d["module"] for d in imd})) or "?"
        v["xmlid"] = ", ".join(sorted({"%s.%s" % (d["module"], d["name"]) for d in imd})) or "-"
        daten[v["id"]] = v
    return daten


def aktionen(k, odoo18: bool) -> list:
    namen = ["Angebote", "Aufträge", "Abzurechnende Aufträge", "Aufträge für Upselling",
             "Alle Auftragszeilen"]
    aus = []
    felder = ["name", "res_model", "view_mode", "view_id"] if not odoo18 else \
             ["name", "res_model", "view_mode", "view_id"]
    for a in k.kw("ir.actions.act_window", "search_read",
                  [[["res_model", "in", MODELLE], ["name", "in", namen]], felder],
                  context={"lang": "de_DE"}):
        aus.append({"id": a["id"], "name": a["name"], "res_model": a["res_model"],
                    "view_mode": a["view_mode"], "formular_view": a["view_id"][0] if a["view_id"] else None})
    return aus


def main() -> int:
    daten = {}
    for schluessel, client, ist18 in (("o11", o11(), False), ("o18", o18("lokal"), True),
                                      ("vm", o18("vm"), True)):
        daten[schluessel] = {}
        for modell in MODELLE:
            daten[schluessel][modell] = {
                "ansichten": ansichten(client, modell, ist18),
                "aktionen": aktionen(client, ist18),
                "seiten": seiten(formular_arch(client, modell, ist18)),
                "hauptbereich": hauptbereich(formular_arch(client, modell, ist18)),
            }
        print("%s: %s" % (schluessel.upper(),
                          " | ".join("%s %d Ansichten, %d Reiter"
                                     % (m, len(daten[schluessel][m]["ansichten"]),
                                        len(daten[schluessel][m]["seiten"])) for m in MODELLE)))

    ziel = os.path.join(REPO, "docs", "_verkauf_teil3_formulare.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("Daten: %s" % ziel)

    for modell in MODELLE:
        print("\n=== %s Reiter ===" % modell)
        for schluessel in ("o11", "o18", "vm"):
            print("  %-4s %s" % (schluessel,
                                 [ (p["string"] or p["name"], p["feld_anzahl"])
                                   for p in daten[schluessel][modell]["seiten"]]))
        print("  Menueaktionen mit Formularansicht:")
        for schluessel in ("o11", "o18"):
            for a in daten[schluessel][modell]["aktionen"]:
                print("     %-4s %-40s formular-view %s" % (schluessel, a["name"][:40], a["formular_view"]))
    print("\nOdoo 11 Prod wurde ausschliesslich lesend verwendet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
