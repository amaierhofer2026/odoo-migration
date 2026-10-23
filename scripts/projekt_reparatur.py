"""Reparatur: migrierte Aufgaben ohne Projekt nachziehen (kein Loeschen).

Hintergrund: Beim ersten Migrationslauf auf einer frischen Datenbank waren die
Projekte im Plan noch ohne Odoo-18-ID, dadurch wurden Aufgaben ohne `project_id`
angelegt. Dieses Skript ordnet sie anhand der Odoo-11-Stammdaten wieder ihrem
Projekt zu - per `write`, ohne Datensaetze zu loeschen.

Aufruf:
  python scripts/projekt_reparatur.py --instanz vm            # Trockenlauf
  python scripts/projekt_reparatur.py --instanz vm --ausfuehren --ich-habe-freigabe
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18  # noqa: E402


def norm(w):
    return " ".join((w or "").split()).lower()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    a = ap.parse_args()
    env = lade_env()
    schreiben = a.ausfuehren and a.ich_habe_freigabe
    if a.ausfuehren and not a.ich_habe_freigabe:
        print("STOPP: --ausfuehren nur mit --ich-habe-freigabe")
        return 2
    if schreiben and not env["ODOO18_DB"].endswith("odoo18_test"):
        print("STOPP: Ziel ist nicht die Testdatenbank")
        return 2

    k11, k18 = o11(), o18(a.instanz)
    print("### Instanz:", a.instanz, " Modus:", "SCHREIBEN" if schreiben else "Trockenlauf")

    au11 = k11.kw("project.task", "search_read", [[]],
                  fields=["id", "name", "project_id", "stage_id", "date_start"],
                  context={"active_test": False}, limit=0)
    # Schluessel 1: Name + Startdatum (in Odoo 11 auf allen Aufgaben gesetzt),
    # Schluessel 2: nur Name (Rueckfall)
    nach_name_start = defaultdict(list)
    nach_name = defaultdict(list)
    for x in au11:
        if x["project_id"]:
            start = str(x["date_start"])[:10] if x["date_start"] else ""
            nach_name_start[(norm(x["name"]), start)].append(x)
            nach_name[norm(x["name"])].append(x)
    ohne11 = [x for x in au11 if not x["project_id"]]
    print("  Odoo 11: %d Aufgaben, davon %d ohne Projekt" % (len(au11), len(ohne11)))

    p18 = defaultdict(list)
    for p in k18.kw("project.project", "search_read", [[]], fields=["id", "name"],
                    context={"active_test": False}, limit=0):
        p18[norm(p["name"])].append(p)

    offen = k18.kw("project.task", "search_read", [[("project_id", "=", False)]],
                   fields=["id", "name", "stage_id", "itk_date_start"],
                   context={"active_test": False}, limit=0)
    print("  Odoo 18: %d Aufgaben ohne Projekt" % len(offen))

    plan, unklar = [], []
    for t in offen:
        start = str(t["itk_date_start"])[:10] if t["itk_date_start"] else ""
        kandidaten = nach_name_start.get((norm(t["name"]), start), [])
        if not kandidaten:
            kandidaten = nach_name.get(norm(t["name"]), [])
        # Mehrere Kandidaten, aber alle im selben Projekt -> eindeutig
        if len(kandidaten) > 1 and len({x["project_id"][0] for x in kandidaten}) == 1:
            pname = kandidaten[0]["project_id"][1]
            ziel = p18.get(norm(pname), [])
            if len(ziel) == 1:
                plan.append((t["id"], ziel[0]["id"], t["name"], pname + " (mehrere Kandidaten, ein Projekt)"))
                continue
        if len(kandidaten) == 1:
            pname = kandidaten[0]["project_id"][1]
            ziel = p18.get(norm(pname), [])
            if len(ziel) == 1:
                plan.append((t["id"], ziel[0]["id"], t["name"], pname))
                continue
        if len(kandidaten) > 1 and t["stage_id"]:
            # Aufloesung ueber die Aufgabenstufe: Stufen sind projektgebunden
            st = k18.kw("project.task.type", "read", [[t["stage_id"][0]]], fields=["project_ids"])
            pids = st[0]["project_ids"] if st else []
            if len(pids) == 1:
                plan.append((t["id"], pids[0], t["name"], "ueber Stufe %s" % t["stage_id"][1]))
                continue
        if not kandidaten:
            # gehoert zu den 5 projektlosen Odoo-11-Aufgaben -> bleibt ohne Projekt
            if any(norm(x["name"]) == norm(t["name"]) for x in ohne11):
                continue
        unklar.append((t["id"], t["name"], len(kandidaten)))

    print("  zuzuordnen: %d, unklar: %d" % (len(plan), len(unklar)))
    for u in unklar[:10]:
        print("   ? ", u)
    for z in plan[:5]:
        print("   + ", z)

    if not schreiben:
        print("\nTrockenlauf - keine Aenderung geschrieben.")
        return 0
    for tid, pid, name, pname in plan:
        k18.kw("project.task", "write", [[tid], {"project_id": pid}])
    print("  gesetzt: %d Aufgaben mit Projekt" % len(plan))
    print("  danach ohne Projekt:", k18.kw("project.task", "search_count",
                                           [[("project_id", "=", False)]],
                                           context={"active_test": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
