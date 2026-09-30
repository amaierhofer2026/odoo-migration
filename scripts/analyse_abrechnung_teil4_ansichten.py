"""Read-only Teil 4: Ansichten, Listen, Filter, Gruppen, Suche und Massenaktionen der Rechnung.

Vergleicht Odoo 11 (account.invoice) gegen Odoo 18 (account.move):
  - Listenspalten der Rechnungsuebersicht (tree/list) mit Beschriftungen
  - Suchansicht: Filter und Gruppierungen
  - Massenaktionen (gebundene Server-Aktionen und Assistenten)

Aufruf:  python scripts/analyse_abrechnung_teil4_ansichten.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18

# Odoo-11-Aktionen auf der Rechnung (aus Teil 1/3 bekannt) plus Odoo-18-Gegenstueck
AKTION_IDS_O11 = [178, 241, 249, 250, 260, 261, 262, 263, 264]
SPALTEN_INTERESSE = ["valorisierung", "projectcategory", "notice", "payment_term", "residual",
                     "amount_total", "date_due", "origin", "reference", "number", "partner"]


def arch(k, modell, typ):
    try:
        d = k.kw(modell, "get_views", [[[False, typ]]], context={"lang": "de_DE"})
        return d["views"][typ]["arch"]
    except Exception:
        return k.kw(modell, "fields_view_get", [[], typ], context={"lang": "de_DE"})["arch"]


def xml(text):
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"&(?!(amp|lt|gt|quot|apos|#\d+);)", "&amp;", text)
    return ET.fromstring(text)


def blatt(arch_text):
    """Listenspalten mit Beschriftung aus einer tree/list-Ansicht."""
    w = xml(arch_text)
    spalten = []
    for f in w.findall(".//field"):
        if f.get("invisible") == "1" or f.get("column_invisible") == "1":
            continue
        spalten.append((f.get("name"), f.get("string") or ""))
    return spalten


def suche(arch_text):
    """Filter und Gruppierungen aus einer search-Ansicht."""
    w = xml(arch_text)
    filter_, gruppen = [], []
    for f in w.findall(".//filter"):
        eintrag = (f.get("name") or "", f.get("string") or f.get("help") or "",
                   f.get("domain") or "", f.get("context") or "")
        if f.get("context") and "group_by" in (f.get("context") or ""):
            gruppen.append(eintrag)
        else:
            filter_.append(eintrag)
    return filter_, gruppen


def main() -> int:
    lade_env()
    k11, k18 = o11(), o18("lokal")
    aus = {}

    print("=" * 78)
    print("1) Listenspalten der Rechnungsuebersicht")
    print("=" * 78)
    for name, k, modell in (("O11", k11, "account.invoice"), ("O18", k18, "account.move")):
        try:
            text = arch(k, modell, "tree")
        except Exception:
            text = arch(k, modell, "list")
        spalten = blatt(text)
        aus[name + "_spalten"] = spalten
        print("-- %s (%d Spalten) --" % (name, len(spalten)))
        print("   %s" % ", ".join("%s(%s)" % (n, s[:18]) for n, s in spalten))
        treffer = [n for n, _ in spalten if any(i in (n or "") for i in SPALTEN_INTERESSE)]
        print("   davon fachlich interessant: %s" % treffer)

    print("\n" + "=" * 78)
    print("2) Suchansicht: Filter und Gruppierungen")
    print("=" * 78)
    for name, k, modell in (("O11", k11, "account.invoice"), ("O18", k18, "account.move")):
        text = arch(k, modell, "search")
        filter_, gruppen = suche(text)
        aus[name + "_filter"] = filter_
        aus[name + "_gruppen"] = gruppen
        print("-- %s: %d Filter, %d Gruppierungen --" % (name, len(filter_), len(gruppen)))
        for f in filter_:
            print("   Filter : %-34s domain=%s" % (f[1][:34] or f[0], f[2][:70]))
        for g in gruppen:
            print("   Gruppe : %-34s context=%s" % (g[1][:34] or g[0], g[3][:70]))

    print("\n" + "=" * 78)
    print("3) Massenaktionen und gebundene Aktionen auf der Rechnung")
    print("=" * 78)
    for name, k, modell in (("O11", k11, "account.invoice"), ("O18", k18, "account.move")):
        print("-- %s --" % name)
        for a in k.kw("ir.actions.act_window", "search_read",
                      [[("res_model", "=", modell)], ["id", "name", "view_mode", "binding_model_id",
                                                      "target", "domain"]], order="id"):
            print("   act_window %-5s %-42s %s bindung=%s" % (a["id"], a["name"][:42],
                                                              a["view_mode"], a["binding_model_id"]))
        for a in k.kw("ir.actions.server", "search_read",
                      [[("model_id.model", "=", modell)], ["id", "name", "state", "binding_model_id",
                                                           "code"]], order="id"):
            print("   server     %-5s %-42s bindung=%s" % (a["id"], a["name"][:42], a["binding_model_id"]))
        for a in k.kw("ir.actions.client", "search_read",
                      [[], ["id", "name", "tag"]], order="id"):
            if "reconcil" in (a["tag"] or ""):
                print("   client     %-5s %-42s %s" % (a["id"], a["name"][:42], a["tag"]))

    print("\n" + "=" * 78)
    print("4) Massenbearbeitung / Sammelaktionen in beiden Systemen")
    print("=" * 78)
    for name, k, modell in (("O11", k11, "account.invoice"), ("O18", k18, "account.move")):
        n = k.kw("ir.actions.server", "search_count", [[("model_id.model", "=", modell)]])
        m = k.kw("ir.actions.act_window", "search_count", [[("res_model", "=", modell)]])
        print("   %s: %d Server-Aktionen, %d Fensteraktionen auf %s" % (name, n, m, modell))

    ziel = os.path.join(tempfile.gettempdir(), "abrechnung_teil4_ansichten.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(aus, fh, ensure_ascii=False, indent=1, default=str)
    print("\nRohdaten: %s" % ziel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
