"""Read-only: Ansichtsvergleich je Menuepunkt im Bereich Abrechnung (Odoo 11 gegen Odoo 18).

Fuer jeden Menuepunkt der App "Abrechnung" (Odoo 18) und der entsprechenden Odoo-11-Menues wird die
WIRKSAME Ansicht verglichen - ueber die Ansichts-ID der jeweiligen Fensteraktion, nicht ueber die
Standardansicht des Modells (Projektlehre: Ansichten je Menue vergleichen).

Erhoben werden je Menuepunkt:
  Liste   : Spalten in Reihenfolge, Bezeichnung, optional/invisible-Spalte, Anzahl
  Formular: Seiten (Reiter) in Reihenfolge, Gruppen, Felder je Seite in Reihenfolge mit
            required/readonly/string, Buttons, Smart Buttons, Statusleiste
  Suche   : Filter (Name, Bezeichnung, Domain), Gruppierungen (Name, Bezeichnung), Suchfelder
  Daten   : Datensatzzahl je Modell

Odoo 11 wird ausschliesslich gelesen. Fehler werden als Klartext ausgegeben (kein stilles
Ueberspringen).

Aufruf: python scripts/vergleiche_abrechnung_menuepunkte.py [--instanz lokal|vm|alle]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
ZIEL = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session131", "ansichten")


def tagname(e):
    return e.tag.split("}")[-1]


def lese_arch(k, modell, typ, view_id, alt):
    """Wirksamen Arch der Ansicht lesen (Odoo 11: fields_view_get, Odoo 18: get_views)."""
    try:
        if alt:
            fv = k.kw(modell, "fields_view_get", [view_id or False, typ], context=CTX)
            return fv.get("arch") or ""
        args = [[[view_id or False, typ]]]
        gv = k.kw(modell, "get_views", args, context=CTX)
        views = (gv or {}).get("views") or {}
        for _vid, daten in views.items():
            return daten.get("arch") or ""
        return ""
    except Exception as fehler:
        return "ARCH-FEHLER: %s" % str(fehler)[:150]


def liste_auswerten(arch):
    if arch.startswith("ARCH-FEHLER:"):
        return {"fehler": arch}
    out = {"spalten": [], "fehler": ""}
    try:
        wurzel = ET.fromstring(arch)
    except ET.ParseError as fehler:
        out["fehler"] = "ARCH UNLESBAR: %s" % str(fehler)[:100]
        return out
    for feld in wurzel.iter():
        if tagname(feld) != "field":
            continue
        name = feld.get("name") or ""
        if not name:
            continue
        out["spalten"].append({"feld": name, "string": feld.get("string") or "",
                               "optional": feld.get("optional") or "",
                               "column_invisible": feld.get("column_invisible") or "",
                               "width": feld.get("width") or ""})
    return out


def formular_auswerten(arch):
    if arch.startswith("ARCH-FEHLER:"):
        return {"fehler": arch}
    out = {"seiten": [], "seiten_felder": {}, "gruppen": [], "felder": [], "buttons": [], "buttons_details": [],
           "smart": [], "statusleiste": [], "fehler": ""}
    try:
        wurzel = ET.fromstring(arch)
    except ET.ParseError as fehler:
        out["fehler"] = "ARCH UNLESBAR: %s" % str(fehler)[:100]
        return out
    for seite in wurzel.iter():
        if tagname(seite) != "page":
            continue
        name = seite.get("string") or seite.get("name") or ""
        out["seiten"].append(name)
        felder = []
        for el in seite.iter():
            if tagname(el) == "field" and el.get("name"):
                felder.append(el.get("name"))
                if el.get("string"):
                    out["felder"].append({"feld": el.get("name"), "string": el.get("string"),
                                          "seite": name, "required": el.get("required") or "",
                                          "readonly": el.get("readonly") or "",
                                          "invisible": el.get("invisible") or ""})
        out["seiten_felder"][name] = felder
    for el in wurzel.iter():
        t = tagname(el)
        if t == "group" and el.get("string"):
            out["gruppen"].append(el.get("string"))
        elif t == "field" and el.get("name") and not any(f["feld"] == el.get("name") for f in out["felder"]):
            out["felder"].append({"feld": el.get("name"), "string": el.get("string") or "",
                                  "seite": "", "required": el.get("required") or "",
                                  "readonly": el.get("readonly") or "",
                                  "invisible": el.get("invisible") or ""})
        elif t == "button":
            text = el.get("string") or "".join(el.itertext()).strip() or el.get("name") or ""
            if text:
                out["buttons"].append(text)
                out["buttons_details"].append({"text": text, "name": el.get("name") or "",
                                               "type": el.get("type") or "", "class": el.get("class") or ""})
        elif t == "header":
            for b in el.iter():
                if tagname(b) == "button":
                    text = b.get("string") or "".join(b.itertext()).strip() or b.get("name") or ""
                    if text:
                        out["statusleiste"].append(text)
    for box in wurzel.iter():
        if "oe_button_box" in (box.get("class") or ""):
            for b in box.iter():
                if tagname(b) == "button":
                    text = b.get("string") or "".join(b.itertext()).strip() or b.get("name") or ""
                    if text:
                        out["smart"].append(text)
    return out


def suche_auswerten(arch):
    if arch.startswith("ARCH-FEHLER:"):
        return {"fehler": arch}
    out = {"filter": [], "gruppierungen": [], "suchfelder": [], "fehler": ""}
    try:
        wurzel = ET.fromstring(arch)
    except ET.ParseError as fehler:
        out["fehler"] = "ARCH UNLESBAR: %s" % str(fehler)[:100]
        return out
    for el in wurzel.iter():
        t = tagname(el)
        if t == "filter":
            out["filter"].append({"name": el.get("name") or "", "string": el.get("string") or "",
                                  "domain": (el.get("domain") or "")[:160],
                                  "context": (el.get("context") or "")[:120],
                                  "invisible": el.get("invisible") or ""})
        elif t == "groupby":
            out["gruppierungen"].append({"name": el.get("name") or "", "string": el.get("string") or "",
                                         "context": (el.get("context") or "")[:120]})
        elif t == "field" and el.get("name"):
            out["suchfelder"].append({"feld": el.get("name"), "string": el.get("string") or "",
                                      "filter_domain": (el.get("filter_domain") or "")[:120]})
    return out


def erhebe_punkt(k, modell, view_id, alt, cache):
    if modell not in cache:
        cache[modell] = {}
    schluessel = (modell, view_id or 0)
    if schluessel in cache[modell]:
        return cache[modell][schluessel]
    typen = ("tree" if alt else "list", "form", "search")
    daten = {"liste": liste_auswerten(lese_arch(k, modell, typen[0], view_id, alt)),
             "formular": formular_auswerten(lese_arch(k, modell, "form", view_id, alt)),
             "suche": suche_auswerten(lese_arch(k, modell, "search", view_id, alt))}
    cache[modell][schluessel] = daten
    return daten


def menuepunkte(k, wurzel_startswith):
    alle = k.kw("ir.ui.menu", "search_read",
                [[], ["id", "name", "parent_id", "action", "sequence"]], context=CTX, limit=0)
    nach_id = {m["id"]: m for m in alle}

    def pfad(m):
        teile, cur, tiefe = [], m, 0
        while cur is not None and tiefe < 8:
            teile.append(cur["name"])
            cur = nach_id.get(cur["parent_id"][0]) if cur["parent_id"] else None
            tiefe += 1
        return " / ".join(reversed(teile))

    ids_aktion = sorted({int(str(m["action"]).split(",")[1]) for m in alle
                         if m["action"] and str(m["action"]).startswith("ir.actions.act_window,")})
    aktionen = {}
    for block in [ids_aktion[i:i + 200] for i in range(0, len(ids_aktion), 200)]:
        for a in k.kw("ir.actions.act_window", "search_read",
                      [[("id", "in", block)], ["name", "res_model", "view_mode", "view_id"]],
                      context=CTX, limit=0):
            aktionen[a["id"]] = a
    punkte = []
    for m in alle:
        p = pfad(m)
        if not p.startswith(wurzel_startswith):
            continue
        if not m["action"] or not str(m["action"]).startswith("ir.actions.act_window,"):
            continue
        aid = int(str(m["action"]).split(",")[1])
        a = aktionen.get(aid)
        if a is None:
            punkte.append({"pfad": p, "menu_id": m["id"], "aktion": aid, "meldung": "AKTION FEHLT"})
            continue
        punkte.append({"pfad": p, "menu_id": m["id"], "aktion": aid, "aktionsname": a["name"],
                       "modell": a["res_model"], "view_mode": a["view_mode"],
                       "view_id": (a["view_id"] or [0, ""])[0]})
    return punkte


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="alle", choices=["lokal", "vm", "alle"])
    args = ap.parse_args()
    os.makedirs(ZIEL, exist_ok=True)

    print("Odoo 11 (nur lesend): Menuepunkte der App Abrechnung ...", flush=True)
    p11 = menuepunkte(o11(), "Abrechnung")
    print("  %d Menuepunkte mit Fensteraktion" % len(p11), flush=True)

    ergebnis = {"o11_punkte": p11}
    cache11 = {}
    k11 = o11()
    for i, pt in enumerate(p11, 1):
        if not pt.get("modell"):
            continue
        print("  O11 %2d/%d %-70s" % (i, len(p11), pt["pfad"][:70]), flush=True)
        pt["ansichten"] = erhebe_punkt(k11, pt["modell"], pt["view_id"], True, cache11)
    ergebnis["o11"] = p11

    for inst in (["lokal", "vm"] if args.instanz == "alle" else [args.instanz]):
        k = o18(inst)
        print("\nOdoo 18 %s: Menuepunkte der App Abrechnung ..." % inst, flush=True)
        punkte = menuepunkte(k, "Abrechnung")
        print("  %d Menuepunkte mit Fensteraktion" % len(punkte), flush=True)
        cache = {}
        for i, pt in enumerate(punkte, 1):
            if not pt.get("modell"):
                continue
            print("  %-5s %2d/%d %s" % (inst, i, len(punkte), pt["pfad"][:68]), flush=True)
            pt["ansichten"] = erhebe_punkt(k, pt["modell"], pt["view_id"], False, cache)
            try:
                pt["anzahl"] = k.kw(pt["modell"], "search_count", [[]], context=CTX)
            except Exception as fehler:
                pt["anzahl"] = "FEHLER: %s" % str(fehler)[:120]
        ergebnis[inst] = punkte

    p = os.path.join(ZIEL, "ansichten_rohdaten.json")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1, default=str)
    print("\nRohdaten: %s" % p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
