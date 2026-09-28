"""Read-only Analyse Verkauf Teil 4, Schritt 1: Ansichten je Menueaktion.

Fuer jede Menueaktion auf sale.order (Odoo 11 Prod nur lesend, Odoo 18 lokal und VM):
  - Ansichtsarten (view_mode) und die wirksame Hauptansicht der Aktion
  - Listenansicht: Spalten in Reihenfolge mit Attributen (string, optional, widget, sum),
    Standard-Sortierung und Optionen (create/edit/delete/editable)
  - Kanban: Kartenfelder und Einstellungen
  - Pivot und Graph: Felder mit Rolle (row/col/measure) und Typ
  - Kalender: Datumsfelder und Farbe
  - Default-Gruppierung aus dem Aktionskontext (search_default_*group_by*)

Ergebnis: docs/_verkauf_teil4_ansichten.json und eine Uebersicht auf der Konsole.

Aufruf:
    python scripts/analyse_verkauf_teil4_ansichten.py
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
TYPEN = ["list", "kanban", "pivot", "graph", "calendar"]


def typ_name(typ: str, ist18: bool) -> str:
    """Odoo 11 kennt nur "tree"; ab Odoo 17 heisst der Typ "list"."""
    return "tree" if (typ == "list" and not ist18) else typ


def entpacke(text):
    if text is None:
        return None
    for zeichen, ersatz in (("&amp;", "&"), ("&gt;", ">"), ("&lt;", "<"), ("&quot;", '"'),
                            ("&#39;", "'"), ("&apos;", "'")):
        text = text.replace(zeichen, ersatz)
    return text


def ansicht_lesen(client, view_id, typ: str, ist18: bool) -> tuple:
    """Kombinierte Ansicht und die tatsaechlich verwendete Ansichts-ID."""
    echter_typ = typ_name(typ, ist18)
    if ist18:
        daten = client.kw(MODELL, "get_views", [[[view_id or False, echter_typ]]], context=SP)
        eintrag = daten["views"].get(echter_typ) or {}
        return eintrag.get("arch") or "", eintrag.get("id")
    daten = client.kw(MODELL, "fields_view_get", [view_id or False, echter_typ, echter_typ], context=SP)
    return daten.get("arch") or "", daten.get("view_id")


def liste_auswerten(arch: str) -> dict:
    try:
        wurzel = ET.fromstring(arch)
    except ET.ParseError as fehler:
        return {"fehler": str(fehler), "spalten": []}
    spalten = []
    for feld in wurzel.iter("field"):
        spalten.append({
            "name": feld.get("name"), "string": entpacke(feld.get("string")),
            "optional": feld.get("optional"), "widget": feld.get("widget"),
            "sum": entpacke(feld.get("sum")), "readonly": feld.get("readonly"),
            "invisible": entpacke(feld.get("invisible")), "groups": feld.get("groups"),
        })
    return {"spalten": spalten,
            "attrs": {k: entpacke(v) for k, v in wurzel.attrib.items() if k in
                      ("string", "default_order", "editable", "create", "edit", "delete")},
            "decoration": sorted(k for k in wurzel.attrib if k.startswith("decoration"))}


def kanban_auswerten(arch: str) -> dict:
    try:
        wurzel = ET.fromstring(arch)
    except ET.ParseError as fehler:
        return {"fehler": str(fehler)}
    kartenfelder = []
    for vorlage in wurzel.iter("t"):
        if vorlage.get("t-name") in (None, "kanban-box"):
            for feld in vorlage.iter("field"):
                if feld.get("name") not in kartenfelder:
                    kartenfelder.append(feld.get("name"))
    return {"attrs": {k: entpacke(v) for k, v in wurzel.attrib.items()},
            "alle_felder": [f.get("name") for f in wurzel.iter("field")],
            "kartenfelder": kartenfelder,
            "templates": sorted({t.get("t-name") for t in wurzel.iter("t") if t.get("t-name")})}


def pivot_auswerten(arch: str) -> dict:
    wurzel = ET.fromstring(arch)
    return {"attrs": {k: entpacke(v) for k, v in wurzel.attrib.items()},
            "felder": [{"name": f.get("name"), "typ": f.get("type"),
                        "string": entpacke(f.get("string"))} for f in wurzel.iter("field")]}


def graph_auswerten(arch: str) -> dict:
    wurzel = ET.fromstring(arch)
    return {"attrs": {k: entpacke(v) for k, v in wurzel.attrib.items()},
            "felder": [{"name": f.get("name"), "typ": f.get("type"),
                        "string": entpacke(f.get("string"))} for f in wurzel.iter("field")]}


def kalender_auswerten(arch: str) -> dict:
    wurzel = ET.fromstring(arch)
    return {"attrs": {k: entpacke(v) for k, v in wurzel.attrib.items()},
            "felder": [f.get("name") for f in wurzel.iter("field")]}


AUSWERTER = {"list": liste_auswerten, "kanban": kanban_auswerten, "pivot": pivot_auswerten,
             "graph": graph_auswerten, "calendar": kalender_auswerten}


def erhebe(client, ist18: bool) -> dict:
    menues = []
    for m in client.kw("ir.ui.menu", "search_read",
                       [[("action", "!=", False)], ["id", "complete_name", "action"]], context=SP):
        treffer = re.search(r"(\d+)", m.get("action") or "")
        if treffer:
            menues.append((int(treffer.group(1)), m["complete_name"]))
    ergebnis = []
    for a in client.kw("ir.actions.act_window", "search_read",
                       [[("res_model", "=", MODELL)],
                        ["id", "name", "view_mode", "view_id", "context", "domain"]], context=SP):
        pfade = sorted({p for mid, p in menues if mid == a["id"]})
        if not pfade:
            continue
        haupt = a["view_id"]
        haupt_id = haupt[0] if isinstance(haupt, list) else (haupt or False)
        eintrag = {"id": a["id"], "name": a["name"], "view_mode": a["view_mode"],
                   "view_id": haupt_id, "context": a["context"], "domain": a["domain"],
                   "menues": pfade, "ansichten": {}}
        for typ in a["view_mode"].split(","):
            typ = typ.strip()
            if typ == "form":
                continue
            typ = "list" if typ in ("tree", "list") else typ
            if typ not in AUSWERTER:
                eintrag["ansichten"][typ] = {"hinweis": "Ansichtsart ohne Auswertung"}
                continue
            vid = haupt_id if typ == a["view_mode"].split(",")[0].strip().replace("tree", "list") else False
            try:
                arch, echte_id = ansicht_lesen(client, vid, typ, ist18)
                daten = AUSWERTER[typ](arch)
                daten["ansichts_id"] = echte_id
                daten["arch_laenge"] = len(arch)
                eintrag["ansichten"][typ] = daten
            except Exception as fehler:
                eintrag["ansichten"][typ] = {"fehler": str(fehler)[:200]}
        ergebnis.append(eintrag)
    return {"aktionen": ergebnis}


def main() -> int:
    daten = {}
    for schluessel, client, ist18 in (("o11", o11(), False), ("o18", o18("lokal"), True),
                                      ("vm", o18("vm"), True)):
        daten[schluessel] = erhebe(client, ist18)
        print("%s: %d Menueaktionen auf %s" % (schluessel.upper(), len(daten[schluessel]["aktionen"]),
                                               MODELL))

    ziel = os.path.join(REPO, "docs", "_verkauf_teil4_ansichten.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("Daten: %s\n" % ziel)

    for schluessel in ("o11", "o18"):
        print("=== %s: Ansichten je Menueaktion ===" % schluessel.upper())
        for a in daten[schluessel]["aktionen"]:
            print("\n  Aktion %s '%s'  view_mode=%s" % (a["id"], a["name"], a["view_mode"]))
            for p in a["menues"]:
                print("     Menue: %s" % p)
            print("     Kontext: %s" % (a["context"] or "{}"))
            for typ, k in a["ansichten"].items():
                if k.get("fehler"):
                    print("     %s: Fehler %s" % (typ, k["fehler"]))
                    continue
                if typ == "list":
                    print("     Liste (Ansicht %s): Sortierung %s, Optionen %s"
                          % (k.get("ansichts_id"), k["attrs"].get("default_order"), k["attrs"]))
                    for i, s in enumerate(k["spalten"], 1):
                        print("        %2d. %-22s '%s'%s%s%s%s" % (
                            i, s["name"], s["string"] or "",
                            " optional=%s" % s["optional"] if s["optional"] else "",
                            " widget=%s" % s["widget"] if s["widget"] else "",
                            " sum=%s" % s["sum"] if s["sum"] else "",
                            " groups=%s" % s["groups"] if s["groups"] else ""))
                elif typ == "kanban":
                    print("     Kanban (Ansicht %s): %s" % (k.get("ansichts_id"), k.get("attrs")))
                    print("        Kartenfelder: %s" % ", ".join(k.get("kartenfelder") or []))
                elif typ in ("pivot", "graph"):
                    print("     %s (Ansicht %s): %s" % (typ, k.get("ansichts_id"), k.get("attrs")))
                    print("        Felder: %s" % ", ".join(
                        "%s(%s)" % (f["name"], f["typ"] or "?") for f in k.get("felder", [])))
                else:
                    print("     %s (Ansicht %s): %s | Felder %s"
                          % (typ, k.get("ansichts_id"), k.get("attrs"), k.get("felder")))
    print("\nOdoo 11 Prod wurde ausschliesslich lesend verwendet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
