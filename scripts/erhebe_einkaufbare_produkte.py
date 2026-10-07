"""Menuepunkt 'Einkaufbare Produkte' vollstaendig erheben (nur lesend).

Aufruf: python scripts/erhebe_einkaufbare_produkte.py o11|lokal|vm [audit-datei]
Erhebt je Instanz: Menue, Aktion, Ansichten (Liste/Suche/Formular/Kanban), Spalten in
Dokumentreihenfolge mit Beschriftung und optional-Kennzeichen, Suchfelder, Filter mit Domain,
Gruppierungen, Favoriten (ir.filters) und die Feldbelegung der relevanten Felder.
"""
from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

inst = sys.argv[1] if len(sys.argv) > 1 else "lokal"
k = o11() if inst == "o11" else o18(inst)
CTX = {"lang": "de_DE"}
LISTENTYP = "tree" if inst == "o11" else "list"

zeilen = []


def schreibe(text=""):
    zeilen.append(text)
    print(text)


def arch_von(model, vtyp, view_id=False):
    """Zusammengefuehrter Arch einer bestimmten Ansicht."""
    if inst == "o11":
        return k.kw(model, "fields_view_get", [view_id or False, vtyp], context=CTX)["arch"]
    r = k.kw(model, "get_views", [[[view_id or False, vtyp]]], context=CTX)
    views = r["views"]
    if isinstance(views, dict):
        return views[vtyp]["arch"]
    return views[-1]["arch"]


def feldinfo(model, felder):
    if not felder:
        return {}
    return k.kw(model, "fields_get", [sorted(set(felder)), ["string", "type", "relation", "required"]],
                context=CTX)


def spalten(arch, model, label):
    """Spalten in Dokumentreihenfolge mit Beschriftung."""
    w = ET.fromstring(arch)
    felder = []
    for f in w.iter("field"):
        feld = f.get("name")
        if not feld:
            continue
        felder.append((feld, f.get("string"), f.get("optional"), f.get("invisible"),
                       f.get("attrs"), f.get("readonly")))
    info = feldinfo(model, [f[0] for f in felder])
    schreibe("\n--- %s (%s) ---" % (label, model))
    for i, (feld, string, optional, invisible, attrs, readonly) in enumerate(felder, 1):
        info_f = info.get(feld, {})
        beschriftung = string or info_f.get("string") or "OHNE BESCHRIFTUNG"
        zusatz = []
        if optional:
            zusatz.append("optional=%s" % optional)
        if invisible not in (None, "0", "False"):
            zusatz.append("invisible=%s" % invisible)
        if attrs:
            zusatz.append("attrs=%s" % attrs[:60])
        if readonly not in (None, "0", "False"):
            zusatz.append("readonly=%s" % readonly)
        schreibe("  %2d. %-34s %-34s %-18s %s" % (
            i, feld, beschriftung[:34], info_f.get("type", "?"), " ".join(zusatz)))
    return [f[0] for f in felder]


def suchansicht(arch, label):
    w = ET.fromstring(arch)
    schreibe("\n--- %s ---" % label)
    for f in w.iter("field"):
        schreibe("  Suchfeld : %-28s filter_domain=%s" % (f.get("name"), (f.get("filter_domain") or "-")[:70]))
    for f in w.iter("filter"):
        domain = (f.get("domain") or "").replace("\n", " ")
        ctx = (f.get("context") or "").replace("\n", " ")
        art = "GRUPPIERUNG" if "group_by" in ctx else "FILTER"
        schreibe("  %-11s: %-38s domain=%s%s" % (
            art, (f.get("string") or f.get("name"))[:38], domain[:70],
            ("  context=%s" % ctx[:60]) if art == "GRUPPIERUNG" else ""))
    for f in w.iter("group"):
        pass
    for f in w.iter("separator"):
        schreibe("  Trenner  : %s" % (f.get("name") or "-"))


# ------------------------------------------------------------------ Menue
schreibe("=== Instanz=%s ===" % inst)
treffer = k.kw("ir.ui.menu", "search_read",
               [[["name", "ilike", "Einkaufbare Produkte"]],
                ["name", "complete_name", "action", "parent_id", "sequence"]], context=CTX)
if not treffer:
    schreibe("Kein Menue mit dem Namen 'Einkaufbare Produkte' gefunden.")
    for m in k.kw("ir.ui.menu", "search_read", [[["name", "ilike", "Produkte"]],
                                                ["complete_name", "action"]], context=CTX)[:15]:
        schreibe("   Kandidat: %s  action=%s" % (m["complete_name"], m["action"]))
    raise SystemExit(0)

akt_ids = []
for m in treffer:
    schreibe("\nMenue   : %s (id %s)" % (m["complete_name"], m["id"]))
    if m["action"]:
        schreibe("   action: %s" % m["action"])
        akt_ids.append(int(m["action"].split(",")[1]))

for aid in akt_ids:
    akt = k.kw("ir.actions.act_window", "read",
               [[aid], ["name", "res_model", "view_mode", "domain", "context", "limit",
                        "search_view_id", "filter"]], context=CTX)[0]
    schreibe("\n--- Aktion %s: %s ---" % (aid, akt["name"]))
    for feld in ("res_model", "view_mode", "domain", "context", "limit", "filter"):
        schreibe("  %-12s %s" % (feld, akt.get(feld)))

    vids = k.kw("ir.actions.act_window.view", "search_read",
                [[["act_window_id", "=", aid]], ["view_mode", "view_id", "sequence"]], context=CTX)
    sv_id = akt["search_view_id"] and akt["search_view_id"][0]
    alle = sorted([(v["sequence"], v["view_mode"], v["view_id"][0]) for v in vids] +
                  ([(99, "search", sv_id)] if sv_id else []))
    for seq, vmode, vid in alle:
        v = k.kw("ir.ui.view", "read", [[vid], ["name", "type", "priority", "mode",
                                                "inherit_id", "xml_id", "model"]], context=CTX)[0]
        schreibe("\n  Ansicht seq=%s %-7s id=%-6s %-38s mode=%s inherit=%s xmlid=%s" % (
            seq, vmode, vid, (v["name"] or "")[:38], v["mode"], v["inherit_id"], v["xml_id"]))

    # Ansichten in Dokumentreihenfolge
    if not alle:
        schreibe("\n  HINWEIS: Aktion hat keine eigenen Ansichten -> Standardansichten des Modells")
        alle = [(0, LISTENTYP, False), (99, "search", False)]
    for seq, vmode, vid in alle:
        if vmode == "search":
            a = arch_von(akt["res_model"], "search", vid)
            suchansicht(a, "Suchansicht (id %s) der Aktion %s - %s" % (vid, aid, akt["name"]))
        elif vmode in (LISTENTYP, "tree", "list"):
            a = arch_von(akt["res_model"], vmode, vid)
            spalten(a, akt["res_model"], "Liste seq=%s (id %s) der Aktion %s" % (seq, vid, aid))
        else:
            a = arch_von(akt["res_model"], vmode, vid)
            w = ET.fromstring(a)
            reiter = [(p.get("string") or p.get("name"), p.get("name")) for p in w.iter("page")]
            schreibe("\n  %s (id %s): %d Reiter, %d Felder" % (vmode, vid, len(reiter), len(list(w.iter("field")))))
            for r in reiter:
                schreibe("      Reiter: %s" % (r[0],))

    # Feldbelegung
    schreibe("\n--- Feldbelegung %s (Aktion %s) ---" % (akt["res_model"], aid))
    gesamt = k.kw(akt["res_model"], "search_count", [[]], context=CTX)
    schreibe("  Datensaetze gesamt: %d" % gesamt)
    for feld in ("name", "default_code", "list_price", "standard_price", "taxes_id", "supplier_taxes_id",
                 "purchase_ok", "sale_ok", "qty_available", "virtual_available", "uom_id", "uom_po_id",
                 "barcode", "type", "categ_id", "seller_ids", "active"):
        try:
            anzahl = k.kw(akt["res_model"], "search_count", [[[feld, "!=", False]]], context=CTX)
        except Exception as e:
            anzahl = "Feld fehlt (%s)" % str(e)[:40]
        schreibe("  %-22s belegt: %s" % (feld, anzahl))

    # Favoriten
    fav = k.kw("ir.filters", "search_read",
               [[["model_id", "=", akt["res_model"]]], ["name", "domain", "context", "is_default", "user_id"]],
               context=CTX)
    schreibe("\n--- Favoriten (ir.filters) fuer %s: %d ---" % (akt["res_model"], len(fav)))
    for f in fav:
        schreibe("  %-30s domain=%s context=%s" % (f["name"], f["domain"], f["context"]))

if len(sys.argv) > 2:
    with open(sys.argv[2], "w", encoding="utf-8") as fh:
        fh.write("\n".join(zeilen))
    print("\n[gespeichert: %s]" % sys.argv[2])
