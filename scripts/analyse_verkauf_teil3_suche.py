"""Read-only Analyse Verkauf Teil 3, Schritt 4: Suchfelder, Filter, Gruppierungen je Menueaktion.

Liest fuer sale.order (Odoo 11 Prod nur lesend, Odoo 18 lokal und VM):
  - je Aktion (ir.actions.act_window) die wirksame Suchansicht (action.search_view_id, sonst
    Standardansicht des Modells) mit Suchfeldern, Filtern und Gruppierungen
  - Domain, Kontext (Default-Filter) und Ansichtsarten der Aktion
  - die Menuepunkte, die diese Aktionen aufrufen
  - gespeicherte Filter (ir.filters)

Ergebnis: docs/_verkauf_teil3_suche.json und eine Uebersicht auf der Konsole.

Aufruf:
    python scripts/analyse_verkauf_teil3_suche.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}
MODELL = "sale.order"


def entpacke(text):
    if text is None:
        return None
    for zeichen, ersatz in (("&amp;", "&"), ("&gt;", ">"), ("&lt;", "<"), ("&quot;", '"'),
                            ("&#39;", "'"), ("&apos;", "'")):
        text = text.replace(zeichen, ersatz)
    return text


def arch_lesen(client, view_id, ist18: bool) -> str:
    """Kombinierte Suchansicht fuer eine konkrete Ansichts-ID (False = Standard)."""
    if ist18:
        daten = client.kw(MODELL, "get_views", [[[view_id or False, "search"]]], context=SP)
        return daten["views"]["search"]["arch"]
    return client.kw(MODELL, "fields_view_get", [view_id or False, "search", "search"],
                     context=SP)["arch"]


def arch_auswerten(arch: str) -> dict:
    felder, filter_, gruppen = [], [], []
    try:
        wurzel = ET.fromstring("<search>%s</search>" % arch)
    except ET.ParseError as fehler:
        return {"fehler": str(fehler), "felder": [], "filter": [], "gruppen": []}
    for knoten in wurzel.iter():
        if knoten.tag == "field":
            felder.append({"name": knoten.get("name"), "string": entpacke(knoten.get("string")),
                           "filter_domain": entpacke(knoten.get("filter_domain")),
                           "operator": knoten.get("operator")})
        elif knoten.tag == "filter":
            eintrag = {"name": knoten.get("name"), "string": entpacke(knoten.get("string")),
                       "domain": entpacke(knoten.get("domain")),
                       "context": entpacke(knoten.get("context"))}
            if (eintrag["context"] or "").find("group_by") >= 0:
                gruppen.append(eintrag)
            else:
                filter_.append(eintrag)
    return {"felder": felder, "filter": filter_, "gruppen": gruppen}


def erhebe(client, ist18: bool) -> dict:
    aktionen = client.kw("ir.actions.act_window", "search_read",
                         [[("res_model", "=", MODELL)],
                          ["id", "name", "domain", "context", "view_mode", "search_view_id"]],
                         context=SP)
    menues = []
    for m in client.kw("ir.ui.menu", "search_read",
                       [[("action", "!=", False)], ["id", "name", "complete_name", "action"]],
                       context=SP):
        treffer = re.search(r"(\d+)", m.get("action") or "")
        if treffer:
            menues.append({"pfad": m["complete_name"], "aktion_id": int(treffer.group(1))})
    ergebnis = {"aktionen": [], "gespeicherte_filter":
                client.kw("ir.filters", "search_read",
                          [[("model_id", "=", MODELL)],
                           ["id", "name", "domain", "context", "is_default", "user_id"]], context=SP)}
    for a in aktionen:
        sv = a.get("search_view_id")
        vid = sv[0] if isinstance(sv, list) else (sv or False)
        arch = arch_lesen(client, vid, ist18)
        daten = arch_auswerten(arch)
        daten.update({"id": a["id"], "name": a["name"], "domain": a["domain"],
                      "context": a["context"], "view_mode": a["view_mode"],
                      "suchansicht_id": vid, "suchansicht_name": sv[1] if isinstance(sv, list) else None,
                      "menues": [m["pfad"] for m in menues if m["aktion_id"] == a["id"]]})
        ergebnis["aktionen"].append(daten)
    return ergebnis


def main() -> int:
    daten = {}
    for schluessel, client, ist18 in (("o11", o11(), False), ("o18", o18("lokal"), True),
                                      ("vm", o18("vm"), True)):
        daten[schluessel] = erhebe(client, ist18)
        print("%s: %d Aktionen, %d gespeicherte Filter"
              % (schluessel.upper(), len(daten[schluessel]["aktionen"]),
                 len(daten[schluessel]["gespeicherte_filter"])))

    ziel = os.path.join(REPO, "docs", "_verkauf_teil3_suche.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("Daten: %s\n" % ziel)

    for schluessel in ("o11", "o18"):
        d = daten[schluessel]
        print("=== %s: Aktionen mit Menue, Default-Kontext, Suchfeldern, Filtern, Gruppierungen ==="
              % schluessel.upper())
        for a in d["aktionen"]:
            if not a["menues"]:
                continue
            print("\n  Aktion %s '%s'" % (a["id"], a["name"]))
            for m in sorted(set(a["menues"])):
                print("     Menue: %s" % m)
            print("     domain:  %s" % a["domain"])
            print("     context: %s   (Default-Filter)" % (a["context"] or "{}"))
            print("     view_mode: %s | Suchansicht: %s %s" % (a["view_mode"], a["suchansicht_id"],
                                                               a["suchansicht_name"] or ""))
            print("     Suchfelder: %s" % ", ".join(f["name"] for f in a["felder"]))
            print("     Filter:")
            for f in a["filter"]:
                print("        %-30s domain=%s" % (f["string"] or f["name"], f["domain"] or "-"))
            print("     Gruppierungen:")
            for g in a["gruppen"]:
                print("        %-30s %s" % (g["string"] or g["name"], g["context"]))
        print("\n  Gespeicherte Filter:")
        if not d["gespeicherte_filter"]:
            print("     (keine)")
        for f in d["gespeicherte_filter"]:
            print("     %-40s Standard=%-5s Domain %s Kontext %s"
                  % (f["name"], f["is_default"], f["domain"], f["context"]))

    print("\nOdoo 11 Prod wurde ausschliesslich lesend verwendet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
