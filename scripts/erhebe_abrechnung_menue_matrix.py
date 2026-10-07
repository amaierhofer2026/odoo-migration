"""Read-only: vollstaendige Menue-Matrix des Bereichs Abrechnung (Odoo 11 gegen Odoo 18).

Erhebt je System (Odoo 11 Prod, Odoo 18 lokal, Odoo 18 VM): Pfad, Menue-ID, XML-ID/Modul des
Menues, Aktion (Art, ID, XML-ID, Name), Modell, view_mode, gebundene Ansicht, Aktionsdomain,
Ansichts-Kontexte, Zugriffsgruppen am Menue, Datensatzzahl je Modell, Anzahl Untermenues.
Zusaetzlich: alle Menues mit dem Namen "Konfiguration" samt Herkunftsmodul und alle Wurzelmenues.

Wichtig: alle Daten werden in SAMMELABFRAGEN gelesen (kein Aufruf je Menue), damit auch die
langsame Odoo-11-Produktion in vertretbarer Zeit durchlaeuft.

Odoo 11 wird ausschliesslich gelesen. Kein stilles Ueberschlagen: nicht aufloesbare Aktionen
werden als Klartext notiert.

Aufruf: python scripts/erhebe_abrechnung_menue_matrix.py [--instanz lokal|vm|alle]
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
ZIEL = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session131", "menue_matrix")


def xmlid_karte(k, modell):
    daten = k.kw("ir.model.data", "search_read",
                 [[("model", "=", modell)], ["module", "name", "res_id"]], context=CTX, limit=0)
    return {d["res_id"]: "%s.%s" % (d["module"], d["name"]) for d in daten}


def erhebe(k, melde=None):
    alle = k.kw("ir.ui.menu", "search_read",
                [[], ["id", "name", "parent_id", "action", "sequence", "child_id", "groups_id", "active"]],
                context=CTX, limit=0)
    mx = xmlid_karte(k, "ir.ui.menu")
    ax = xmlid_karte(k, "ir.actions.act_window")

    # 1) alle referenzierten Aktionen in einem Zug lesen
    fenster_ids, andere = [], []
    for m in alle:
        if not m["action"]:
            continue
        teile = str(m["action"]).split(",")
        if len(teile) != 2:
            continue
        if teile[0] == "ir.actions.act_window":
            fenster_ids.append(int(teile[1]))
        else:
            andere.append((m["id"], teile[0], int(teile[1])))
    fenster = {}
    for block in [fenster_ids[i:i + 200] for i in range(0, len(fenster_ids), 200)]:
        for a in k.kw("ir.actions.act_window", "search_read",
                      [[("id", "in", block)],
                       ["name", "res_model", "view_mode", "view_id", "domain", "context",
                        "search_view_id", "target", "limit"]], context=CTX, limit=0):
            fenster[a["id"]] = a
    fremd = {}
    for modell in sorted({t[1] for t in andere}):
        ids = [t[2] for t in andere if t[1] == modell]
        for a in k.kw(modell, "search_read", [[("id", "in", ids)], ["name"]], context=CTX, limit=0):
            fremd[(modell, a["id"])] = a["name"]

    # 2) Datensatzzahlen je Modell in einem Zug je Modell
    modelle = sorted({a["res_model"] for a in fenster.values()})
    zahlen = {}
    for modell in modelle:
        try:
            zahlen[modell] = k.kw(modell, "search_count", [[]], context=CTX)
        except Exception as fehler:  # Klartext statt stilles Ueberspringen
            zahlen[modell] = "FEHLER: %s" % str(fehler)[:120]
    if melde:
        melde("  %d Menues, %d Fensteraktionen, %d Modelle gezaehlt" % (len(alle), len(fenster), len(modelle)))

    nach_id = {m["id"]: m for m in alle}

    def pfad(m):
        teile, cur, tiefe = [], m, 0
        while cur is not None and tiefe < 8:
            teile.append(cur["name"])
            cur = nach_id.get(cur["parent_id"][0]) if cur["parent_id"] else None
            tiefe += 1
        return " / ".join(reversed(teile))

    zeilen = []
    for m in sorted(alle, key=lambda x: (pfad(x), x["sequence"], x["id"])):
        z = {"menu_id": m["id"], "pfad": pfad(m), "name": m["name"],
             "menue_xmlid": mx.get(m["id"], ""), "seq": m["sequence"], "aktiv": m["active"],
             "gruppen": m["groups_id"], "untermenues": len(m["child_id"] or []),
             "modell": "", "aktionsart": "", "aktion_id": "", "aktion_name": "",
             "aktion_xmlid": "", "view_mode": "", "view_id": "", "domain": "",
             "act_context": "", "suchansicht": "", "target": "", "limit": "",
             "anzahl": "", "meldung": ""}
        if not m["action"]:
            z["meldung"] = "KEINE AKTION (reine Gruppe)"
            zeilen.append(z)
            continue
        teile = str(m["action"]).split(",")
        if len(teile) != 2:
            z["meldung"] = "REFERENZ UNLESBAR: %s" % m["action"]
            zeilen.append(z)
            continue
        art, aid = teile[0], int(teile[1])
        z["aktionsart"], z["aktion_id"] = art, aid
        if art != "ir.actions.act_window":
            z["aktion_name"] = fremd.get((art, aid), "AKTIONSDATENSATZ FEHLT")
            zeilen.append(z)
            continue
        a = fenster.get(aid)
        if a is None:
            z["meldung"] = "FENSTERAKTION %d FEHLT" % aid
            zeilen.append(z)
            continue
        modell = a["res_model"]
        z.update({"modell": modell, "aktion_name": a["name"], "aktion_xmlid": ax.get(aid, ""),
                  "view_mode": a["view_mode"], "view_id": (a["view_id"] or ["", ""])[1],
                  "domain": a["domain"] or "", "act_context": a["context"] or "",
                  "suchansicht": (a["search_view_id"] or ["", ""])[1],
                  "target": a["target"], "limit": a["limit"], "anzahl": zahlen.get(modell, "")})
        zeilen.append(z)
    return zeilen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="alle", choices=["lokal", "vm", "alle"])
    args = ap.parse_args()
    os.makedirs(ZIEL, exist_ok=True)

    def melde(text):
        print(text, flush=True)

    melde("Lese Odoo 11 (nur lesend) ...")
    ergebnis = {"o11": erhebe(o11(), melde)}
    for inst in (["lokal", "vm"] if args.instanz == "alle" else [args.instanz]):
        melde("Lese Odoo 18 %s ..." % inst)
        ergebnis[inst] = erhebe(o18(inst), melde)

    p = os.path.join(ZIEL, "menue_rohdaten.json")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(ergebnis, fh, ensure_ascii=False, indent=1, default=str)
    melde("\nRohdaten: %s" % p)

    melde("\n=== Wurzelmenues (parent_id leer) ===")
    for schluessel in ["o11"] + [i for i in ("lokal", "vm") if i in ergebnis]:
        w = [z for z in ergebnis[schluessel] if z["pfad"] == z["name"]]
        melde("  %-6s %s" % (schluessel, ", ".join("%s(id %d)" % (z["name"], z["menu_id"]) for z in w)))

    melde("\n=== Menues mit dem Namen 'Konfiguration' ===")
    for schluessel in ["o11"] + [i for i in ("lokal", "vm") if i in ergebnis]:
        k = [z for z in ergebnis[schluessel] if z["name"] == "Konfiguration"]
        melde("  %s: %d Treffer" % (schluessel, len(k)))
        for z in sorted(k, key=lambda x: x["pfad"]):
            melde("     id=%-5d xmlid=%-42s pfad=%s" % (z["menu_id"], z["menue_xmlid"], z["pfad"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
