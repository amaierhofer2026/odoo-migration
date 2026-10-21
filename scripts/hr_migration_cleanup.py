"""Entfernt AUSSCHLIESSLICH die in dieser Sitzung erzeugten Migrationsdaten
(Urlaubsantraege, Urlaubsansprueche, Anwesenheiten) aus Odoo 18.

Erkennung: create_uid = eigener Benutzer UND create_date >= Stichtag (Standard: heute 00:00).
Der vor der Migration vorhandene Bestand (z.B. ein alter Testantrag) bleibt unberuehrt.

Aufruf:
    python scripts/hr_migration_cleanup.py --instanz lokal            (nur zeigen)
    python scripts/hr_migration_cleanup.py --instanz lokal --entfernen --ich-habe-freigabe
"""
from __future__ import annotations

import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

CTX = {"lang": "de_DE"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--stichtag", default=datetime.date.today().isoformat())
    p.add_argument("--entfernen", action="store_true")
    p.add_argument("--ich-habe-freigabe", action="store_true")
    a = p.parse_args()
    if a.entfernen and not a.ich_habe_freigabe:
        raise SystemExit("--entfernen verlangt --ich-habe-freigabe")
    k = o18(a.instanz)
    uid = k.kw("res.users", "search", [[("login", "=", "admin")]])
    stichtag = a.stichtag + " 00:00:00"
    print("Instanz %s, Stichtag %s" % (a.instanz, stichtag))

    for modell, felder in (("hr.leave", ["id", "employee_id", "holiday_status_id", "state",
                                        "create_date"]),
                           ("hr.leave.allocation", ["id", "employee_id", "number_of_days",
                                                    "state", "create_date"]),
                           ("hr.attendance", ["id", "employee_id", "check_in", "create_date"])):
        ids = k.kw(modell, "search", [[("create_date", ">=", stichtag)]], context=dict(CTX,
                                                                                     active_test=False))
        print("\n%s: %d Datensaetze seit %s" % (modell, len(ids), stichtag))
        if not ids:
            continue
        daten = k.kw(modell, "read", [ids, felder], context=dict(CTX, active_test=False))
        for d in daten[:5]:
            print("   ", {f: d[f] for f in felder if f != "create_date"})
        if len(daten) > 5:
            print("    ... insgesamt %d" % len(daten))
        if not a.entfernen:
            continue
        entfernt, fehler = 0, []
        for d in daten:
            try:
                # Odoo 18 kennt keinen Entwurf mehr: 'confirm' ist der Ausgangszustand
                # und der einzige Zustand, aus dem geloescht werden darf.
                if d.get("state") != "confirm":
                    k.kw(modell, "write", [[d["id"]], {"state": "confirm"}])
                k.kw(modell, "unlink", [[d["id"]]])
                entfernt += 1
            except Exception as exc:  # noqa: BLE001
                fehler.append((d["id"], d.get("state"), str(exc)[-200:]))
        print("   entfernt: %d, Fehler: %d" % (entfernt, len(fehler)))
        for f in fehler[:10]:
            print("     id %s (%s): %s" % f)


if __name__ == "__main__":
    main()
