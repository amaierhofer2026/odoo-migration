"""Abwesenheitsbezug der Zeiterfassung nachziehen (Schnittstelle Anwesenheiten <-> Zeiterfassung).

Die Zeiterfassungs-Migration (Session 136) legt Zeilen ohne Abwesenheitsbezug an,
wenn die zugehoerige Abwesenheit in Odoo 18 noch nicht gebucht war (Fall
Abwesenheit #87 auf der VM) oder wenn der Bezug beim Anlegen nicht eindeutig war.
Dieses Skript zieht den Bezug aus Odoo 11 nach: Odoo 11 fuehrt an jeder
Zeiterfassungszeile `holiday_id` - die Zeile wird ueber Mitarbeiter, Datum und
Dauer zugeordnet und die Odoo-18-Abwesenheit ueber Mitarbeiter, Art und Zeitraum.

Odoo 11 wird ausschliesslich gelesen. Standard ist der Trockenlauf.

Aufruf:
    python scripts/anwesenheiten_zeiterfassung_bezug.py --instanz lokal|vm [--setzen]
"""
from __future__ import annotations

import argparse
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

DE = {"lang": "de_DE"}


def nt(s):
    return " ".join((s or "").split())


def nn(s):
    return nt(s).lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    ap.add_argument("--setzen", action="store_true")
    a = ap.parse_args()
    k11 = o11()
    k18 = o18(a.instanz)
    ctx11 = dict(DE, active_test=False)
    ctx18 = dict(DE, active_test=False)

    print("Instanz %s - %s" % (a.instanz, "SCHREIBEN" if a.setzen else "TROCKENLAUF"))

    b11 = k11.kw("hr.employee", "search_read", [[], ["id", "name", "work_email"]], context=ctx11)
    s11 = {t["id"]: t for t in k11.kw("hr.holidays.status", "search_read", [[], ["id", "name"]],
                                      context=ctx11)}
    h11 = k11.kw("hr.holidays", "search_read",
                 [[], ["id", "employee_id", "holiday_status_id", "date_from", "date_to", "type"]],
                 context=ctx11, order="id")
    z11 = k11.kw("account.analytic.line", "search_read",
                 [[("holiday_id", "!=", False)], ["id", "employee_id", "date", "unit_amount",
                                                  "holiday_id"]], context=ctx11, order="date,id")

    b18 = k18.kw("hr.employee", "search_read", [[], ["id", "name", "work_email"]], context=ctx18)
    typ18 = {t["id"]: t for t in k18.kw("hr.leave.type", "search_read", [[], ["id", "name"]],
                                        context=ctx18)}
    l18 = k18.kw("hr.leave", "search_read",
                 [[], ["id", "employee_id", "holiday_status_id", "request_date_from",
                       "request_date_to"]], context=ctx18, order="id")

    nach_email = {nn(e["work_email"]): e for e in b18 if e["work_email"]}
    nach_name = {nn(e["name"]): e for e in b18}
    ma = {}
    for e in b11:
        z = nach_email.get(nn(e["work_email"])) or nach_name.get(nn(e["name"]))
        if z:
            ma[e["id"]] = z
    nach_typ = collections.defaultdict(list)
    for t in typ18.values():
        nach_typ[nt(t["name"])].append(t)
    ty = {}
    for tid, t in s11.items():
        treffer = nach_typ.get(nt(t["name"]))
        if treffer and len(treffer) == 1:
            ty[tid] = treffer[0]

    # Odoo-11-Abwesenheit -> Odoo-18-Abwesenheit
    leave_map = {}
    index = collections.defaultdict(list)
    for r in l18:
        if r["employee_id"] and r["holiday_status_id"]:
            index[(r["employee_id"][0], r["holiday_status_id"][0],
                   r["request_date_from"], r["request_date_to"])].append(r["id"])
    for h in h11:
        if not h["employee_id"] or h["holiday_status_id"][0] not in ty:
            continue
        e = ma.get(h["employee_id"][0])
        if not e:
            continue
        schluessel = (e["id"], ty[h["holiday_status_id"][0]]["id"],
                      (h["date_from"] or "")[:10], (h["date_to"] or "")[:10])
        ids = index.get(schluessel) or []
        if len(ids) == 1:
            leave_map[h["id"]] = ids[0]

    # Odoo-18-Zeilen je Mitarbeiter/Datum/Dauer
    zeilen = collections.defaultdict(list)
    for z in k18.kw("account.analytic.line", "search_read",
                    [[("employee_id", "!=", False)], ["id", "employee_id", "date", "unit_amount",
                                                      "holiday_id"]],
                    context=ctx18, order="date,id"):
        zeilen[(z["employee_id"][0], z["date"], round(z["unit_amount"] or 0.0, 2))].append(z)

    offen, unklar, ohne_leave = [], [], []
    for z in z11:
        if not z["employee_id"]:
            continue
        e = ma.get(z["employee_id"][0])
        if not e:
            continue
        lid = leave_map.get(z["holiday_id"][0])
        if not lid:
            ohne_leave.append((z["id"], z["holiday_id"][1]))
            continue
        kandidaten = [x for x in zeilen.get((e["id"], z["date"], round(z["unit_amount"] or 0.0, 2)), [])
                      if not x["holiday_id"]]
        if len(kandidaten) == 1:
            offen.append((z["id"], kandidaten[0]["id"], lid, e["name"], z["date"]))
        elif len(kandidaten) > 1:
            unklar.append((z["id"], [x["id"] for x in kandidaten]))

    print("  Odoo 11: %d Zeilen mit Abwesenheitsbezug" % len(z11))
    print("  zuzuordnen: %d | ohne Odoo-18-Abwesenheit: %d | mehrdeutig: %d"
          % (len(offen), len(ohne_leave), len(unklar)))
    for x in offen[:12]:
        print("     O11-Zeile %6d -> O18-Zeile %6d, Abwesenheit %5d, %-28s %s"
              % (x[0], x[1], x[2], x[3][:28], x[4]))
    if unklar:
        print("  mehrdeutig (nicht geaendert):", unklar[:5])
    if ohne_leave:
        print("  Abwesenheit ohne Odoo-18-Gegenstueck (nicht geaendert):", ohne_leave[:5])

    gesetzt = 0
    if a.setzen:
        for z_o11, z_o18, lid, _name, _datum in offen:
            try:
                k18.kw("account.analytic.line", "write", [[z_o18], {"holiday_id": lid}])
                gesetzt += 1
            except Exception as exc:  # noqa: BLE001
                print("     FEHLER Zeile %s: %s" % (z_o18, str(exc)[-200:]))
        print("  gesetzt: %d" % gesetzt)

    rest = k18.kw("account.analytic.line", "search_count",
                  [[("holiday_id", "=", False), ("employee_id", "!=", False)]], context=ctx18)
    print("  Zeilen ohne Abwesenheitsbezug in Odoo 18 (gesamt): %d" % rest)
    return 0 if (a.setzen or not offen) else 1


if __name__ == "__main__":
    sys.exit(main())
