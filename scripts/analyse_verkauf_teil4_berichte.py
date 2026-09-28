"""Read-only Analyse Verkauf Teil 4, Schritt 2: Verkaufsberichte und Druckberichte.

Liest fuer die Berichtsmodelle (Odoo 11 Prod nur lesend, Odoo 18 lokal und VM):
  - Menuepunkte und Aktionen im Bereich Berichtswesen/Verkauf
  - die Modelle report.all.channels.sales und sale.report: Felder, Ansichten, Filter,
    Gruppierungen, Default-Kontext
  - Datenbestand: Anzahl, Zeitraum, Verteilung auf Vertriebskanaele und Zustaende
  - Druckberichte (ir.actions.report) mit Bindung an sale.order/sale.report und Papierformate

Ergebnis: docs/_verkauf_teil4_berichte.json und eine Uebersicht auf der Konsole.

Aufruf:
    python scripts/analyse_verkauf_teil4_berichte.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18
from analyse_verkauf_teil3_suche import arch_auswerten, arch_lesen, entpacke

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}
BERICHTSMODELLE = ["report.all.channels.sales", "sale.report"]


def menues_und_aktionen(client) -> list:
    """Alle Menues im Verkaufsumfeld mit ihrer Aktion und deren Modell."""
    aktionen = {a["id"]: a for a in client.kw(
        "ir.actions.act_window", "search_read",
        [[], ["id", "name", "res_model", "domain", "context", "view_mode", "view_id"]], context=SP)}
    ergebnis = []
    for m in client.kw("ir.ui.menu", "search_read",
                       [[], ["id", "name", "complete_name", "action", "sequence", "parent_id"]],
                       context=SP):
        pfad = m["complete_name"] or m["name"]
        if not (pfad.startswith("Verkauf") or "Verkaufsauftr" in pfad or "Kanal" in pfad):
            continue
        treffer = re.search(r"(\d+)", m.get("action") or "")
        aktion = aktionen.get(int(treffer.group(1))) if treffer else None
        ergebnis.append({"id": m["id"], "pfad": pfad, "aktion_id": aktion["id"] if aktion else None,
                         "aktion": aktion["name"] if aktion else None,
                         "modell": aktion["res_model"] if aktion else None,
                         "domain": aktion["domain"] if aktion else None,
                         "kontext": aktion["context"] if aktion else None,
                         "view_mode": aktion["view_mode"] if aktion else None})
    return sorted(ergebnis, key=lambda x: x["pfad"])


def modell_info(client, modell: str) -> dict:
    treffer = client.kw("ir.model", "search_read", [[("model", "=", modell)],
                                                   ["id", "name", "model", "transient"]], context=SP)
    if not treffer:
        return {"vorhanden": False}
    felder = client.kw("ir.model.fields", "search_read",
                       [[("model", "=", modell)],
                        ["name", "field_description", "ttype", "relation", "store", "readonly"]],
                       context=SP)
    return {"vorhanden": True, "modell": treffer[0], "felder": felder, "anzahl_felder": len(felder)}


def ansichten(client, modell: str, ist18: bool) -> dict:
    ergebnis = {}
    for typ in ("list", "kanban", "pivot", "graph", "search", "tree"):
        if typ == "tree" and ist18:
            continue
        if typ == "list" and not ist18:
            continue
        try:
            gefunden = client.kw("ir.ui.view", "search_read",
                                 [[("model", "=", modell), ("type", "=", typ)],
                                  ["id", "name", "priority", "inherit_id", "arch_db"]], context=SP)
        except Exception:
            continue
        eintraege = []
        for v in gefunden:
            arch = entpacke(v.get("arch_db") or "")
            ausgewertet = {}
            try:
                if typ in ("search",):
                    ausgewertet = arch_auswerten(arch)
                elif typ in ("list", "tree"):
                    ausgewertet = {"spalten": [
                        {"name": f.get("name"), "string": entpacke(f.get("string")),
                         "sum": entpacke(f.get("sum")), "optional": f.get("optional")}
                        for f in ET.fromstring(arch).iter("field")]}
                elif typ in ("pivot", "graph"):
                    ausgewertet = {"felder": [
                        {"name": f.get("name"), "typ": f.get("type")}
                        for f in ET.fromstring(arch).iter("field")]}
            except ET.ParseError as fehler:
                ausgewertet = {"fehler": str(fehler)[:120]}
            eintraege.append({"id": v["id"], "name": v["name"], "priority": v.get("priority"),
                              "inherit": bool(v.get("inherit_id")), "auswertung": ausgewertet})
        if eintraege:
            ergebnis[typ] = eintraege
    return ergebnis


def datenbestand(client, modell: str) -> dict:
    """Anzahl, Zeitraum und Verteilungen des Berichtsmodells (nur lesend)."""
    ergebnis = {"anzahl": client.kw(modell, "search_count", [[]], context=SP)}
    for feld in ("date", "date_order"):
        felder = client.kw(modell, "fields_get", [[], ["type"]], context=SP)
        if feld not in felder:
            continue
        gruppen = client.kw(modell, "read_group", [[], [feld], []], context=SP, limit=1)
        try:
            alle = client.kw(modell, "search_read", [[], [feld]], context=SP, limit=5000,
                             order="%s asc" % feld)
            werte = [z[feld] for z in alle if z.get(feld)]
            if werte:
                ergebnis["zeitraum"] = {"feld": feld, "von": str(min(werte)), "bis": str(max(werte))}
        except Exception as fehler:
            ergebnis["zeitraum"] = {"fehler": str(fehler)[:120]}
        for gruppe in ("team_id", "state", "categ_id", "product_id"):
            if gruppe not in felder:
                continue
            try:
                ergebnis["verteilung_" + gruppe] = [
                    {gruppe: (g[gruppe][1] if isinstance(g.get(gruppe), list) else g.get(gruppe)),
                     "anzahl": g.get("%s_count" % gruppe) or g.get("__count")}
                    for g in client.kw(modell, "read_group", [[], [gruppe], [gruppe]], context=SP)]
            except Exception as fehler:
                ergebnis["verteilung_" + gruppe] = str(fehler)[:120]
    return ergebnis


def gespeicherte_filter(client, modell: str) -> list:
    return client.kw("ir.filters", "search_read",
                     [[("model_id", "=", modell)], ["id", "name", "domain", "context", "is_default",
                                                    "user_id"]], context=SP)


def druckberichte(client) -> list:
    berichte = client.kw("ir.actions.report", "search_read",
                         [[], ["id", "name", "model", "report_name", "report_type", "binding_model_id",
                               "binding_type", "paperformat_id", "attachment"]], context=SP)
    return [b for b in berichte if b.get("model") in ("sale.order", "sale.report", "sale.order.line")]


def main() -> int:
    daten = {}
    for schluessel, client, ist18 in (("o11", o11(), False), ("o18", o18("lokal"), True),
                                      ("vm", o18("vm"), True)):
        eintrag = {"menues": menues_und_aktionen(client), "modelle": {}, "druckberichte": druckberichte(client)}
        for modell in BERICHTSMODELLE:
            info = modell_info(client, modell)
            if not info.get("vorhanden"):
                eintrag["modelle"][modell] = {"vorhanden": False}
                continue
            info["ansichten"] = ansichten(client, modell, ist18)
            info["gespeicherte_filter"] = gespeicherte_filter(client, modell)
            info["datenbestand"] = datenbestand(client, modell) if modell in (
                "report.all.channels.sales", "sale.report") else {}
            eintrag["modelle"][modell] = info
        daten[schluessel] = eintrag
        print("%s: %d Menues, Modelle %s, %d Druckberichte"
              % (schluessel.upper(), len(eintrag["menues"]),
                 ", ".join("%s=%s" % (m, "ja" if eintrag["modelle"][m].get("vorhanden") else "nein")
                           for m in BERICHTSMODELLE), len(eintrag["druckberichte"])))

    ziel = os.path.join(REPO, "docs", "_verkauf_teil4_berichte.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("Daten: %s\n" % ziel)

    for schluessel in ("o11", "o18"):
        d = daten[schluessel]
        print("=== %s: Menues mit Aktion und Modell ===" % schluessel.upper())
        for m in d["menues"]:
            print("  %-52s -> %-22s %s" % (m["pfad"], (m["aktion"] or "-")[:22],
                                           m["modell"] or "-"))
            if m["modell"] in BERICHTSMODELLE:
                print("      domain=%s" % m["domain"])
                print("      kontext=%s view_mode=%s" % (m["kontext"], m["view_mode"]))
        for modell, info in d["modelle"].items():
            print("\n=== %s: Modell %s ===" % (schluessel.upper(), modell))
            if not info.get("vorhanden"):
                print("  nicht vorhanden")
                continue
            print("  Felder: %d" % info["anzahl_felder"])
            for f in info["felder"]:
                print("     %-26s %-12s %-28s %s" % (f["name"], f["ttype"], (f["field_description"] or "")[:28],
                                                     f.get("relation") or ""))
            for typ, liste in info["ansichten"].items():
                for v in liste:
                    print("\n  Ansicht %s id %s '%s' priority %s inherit %s"
                          % (typ, v["id"], v["name"], v["priority"], v["inherit"]))
                    a = v["auswertung"]
                    if typ == "search":
                        for f in a.get("felder", []):
                            print("      Suchfeld %-24s %s" % (f["name"], f["filter_domain"] or ""))
                        for f in a.get("filter", []):
                            print("      Filter %-26s domain=%s" % (f["string"] or f["name"], f["domain"]))
                        for g in a.get("gruppen", []):
                            print("      Gruppierung %-22s %s" % (g["string"] or g["name"], g["context"]))
                    elif typ in ("list", "tree"):
                        print("      Spalten: %s" % ", ".join(
                            "%s%s" % (s["name"], "(%s)" % s["sum"] if s["sum"] else "")
                            for s in a.get("spalten", [])))
                    elif typ in ("pivot", "graph"):
                        print("      Felder: %s" % ", ".join(
                            "%s/%s" % (f["name"], f["typ"]) for f in a.get("felder", [])))
            print("\n  Gespeicherte Filter:")
            if not info["gespeicherte_filter"]:
                print("     (keine)")
            for f in info["gespeicherte_filter"]:
                print("     %-40s Standard=%s domain=%s context=%s"
                      % (f["name"], f["is_default"], f["domain"], f["context"]))
            b = info.get("datenbestand") or {}
            print("  Datenbestand: %s" % {k: v for k, v in b.items() if k != "verteilung_produkt_id"})
        print("\n=== %s: Druckberichte auf sale.order/sale.report ===" % schluessel.upper())
        for r in d["druckberichte"]:
            print("  %-42s %-24s %-12s Bindung %s"
                  % (r["name"], r["report_name"], r["report_type"], r["binding_model_id"] or "-"))
    print("\nOdoo 11 Prod wurde ausschliesslich lesend verwendet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
