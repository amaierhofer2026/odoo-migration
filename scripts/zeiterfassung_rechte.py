"""Rechte Zeiterfassung: Gruppenmitglieder nach dem Odoo-11-Rechtekonzept setzen.

Standard ist der TROCKENLAUF (keine Schreibzugriffe). Schreiben nur mit
    --ausfuehren --ich-habe-freigabe

Regel (aus Odoo 11 abgeleitet, docs/o11-o18-zeiterfassung-vergleich.md 3.5):
  * Odoo 11 "Zeiterfassung / Benutzer" (hr_timesheet.group_hr_timesheet_user):
    eigene Zeilen anlegen/aendern; Schreiben nur eigene (Record Rule), Lesen aller
    Zeilen.  ->  Odoo 18 Gruppe "Benutzer: nur eigene Zeiterfassungen" (607).
    Zuordnung: alle aktiven internen Benutzer, deren Login in Odoo 11 in dieser
    Gruppe war.
  * Odoo 11 Schreibrecht auf ALLE Projekt-Zeilen hatte nur "Projekt / Manager"
    (project.group_project_manager, Rule account.analytic.line.timesheet.manager).
    ->  Odoo 18 Gruppe "Benutzer: Alle Zeiterfassungen" (608) nur fuer diesen
    Personenkreis. Bestehende Mitglieder werden NICHT entfernt.

Aufruf:
  python scripts/zeiterfassung_rechte.py --instanz lokal
  python scripts/zeiterfassung_rechte.py --instanz lokal --ausfuehren --ich-habe-freigabe
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
G_ONLY_OWN = 607      # hr_timesheet.group_hr_timesheet_user
G_ALL = 608           # hr_timesheet.group_hr_timesheet_approver


def normal(wert):
    return (wert or "").strip().lower()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    a = ap.parse_args()

    env = lade_env()
    ziel_db = env["ODOO18_DB"]
    schreiben = a.ausfuehren and a.ich_habe_freigabe
    if a.ausfuehren and not a.ich_habe_freigabe:
        print("STOPP: --ausfuehren nur zusammen mit --ich-habe-freigabe")
        return 2
    if schreiben and not ziel_db.endswith("odoo18_test"):
        print("STOPP: Ziel-DB ist nicht die Testdatenbank:", ziel_db)
        return 2

    k11, k18 = o11(), o18(a.instanz)
    print("### Instanz:", a.instanz, " DB:", ziel_db, " Modus:", "SCHREIBEN" if schreiben else "Trockenlauf")

    # Odoo 11: Mitglieder der beiden Gruppen (read-only)
    g11 = k11.kw("ir.model.data", "search_read",
                 [["&", ("model", "=", "res.groups"),
                   "|", ("name", "=", "group_hr_timesheet_user"),
                   ("name", "=", "group_project_manager")]],
                 fields=["module", "name", "res_id"], limit=0)
    ids = {x["name"]: x["res_id"] for x in g11}
    mitglieder = {}
    for name, gid in ids.items():
        grp = k11.kw("res.groups", "read", [[gid]], fields=["users"])
        users = k11.kw("res.users", "read", [sorted(grp[0]["users"])],
                       fields=["login", "name", "active"]) if grp and grp[0]["users"] else []
        mitglieder[name] = {normal(u["login"]): u for u in users}
        print("  Odoo 11 %-28s %d Benutzer" % (name, len(users)))

    # Odoo 18: aktive interne Benutzer
    u18 = k18.kw("res.users", "search_read",
                 [[("share", "=", False), ("active", "=", True)]],
                 fields=["id", "login", "name", "groups_id"], limit=0)
    u18 = [u for u in u18 if u["login"] not in ("__system__", "default", "public", "portaltemplate")]
    print("  Odoo 18 aktive interne Benutzer: %d" % len(u18))

    # Zuordnung: Login, sonst Benutzername. Hintergrund: in Odoo 11 lautet der Login
    # von "Breiteneder Lorenz" noch lorenz.galler@..., in Odoo 18
    # lorenz.breiteneder@... - ein reiner Login-Vergleich wuerde ihn uebersehen.
    def trifft(u, gruppe):
        kennung = mitglieder.get(gruppe, {})
        if normal(u["login"]) in kennung:
            return True
        return any(normal(x["name"]) == normal(u["name"]) for x in kennung.values())

    nur_eigene = [u for u in u18 if trifft(u, "group_hr_timesheet_user")]
    alle = [u for u in u18 if trifft(u, "group_project_manager")]

    print("\n=== Plan Gruppe 607 (nur eigene Zeiterfassungen) ===")
    for u in nur_eigene:
        print("   + %-38s %s" % (u["login"], u["name"]))
    print("   (%d Benutzer)" % len(nur_eigene))
    print("\n=== Plan Gruppe 608 (alle Zeiterfassungen, Odoo-11-Projektmanager) ===")
    for u in alle:
        print("   + %-38s %s" % (u["login"], u["name"]))
    print("   (%d Benutzer)" % len(alle))

    fehlend_607 = [u["login"] for u in nur_eigene if G_ONLY_OWN not in u["groups_id"]]
    fehlend_608 = [u["login"] for u in alle if G_ALL not in u["groups_id"]]
    print("\n  fehlen in 607: %d %s" % (len(fehlend_607), fehlend_607))
    print("  fehlen in 608: %d %s" % (len(fehlend_608), fehlend_608))

    vorher = k18.kw("res.groups", "read", [[G_ONLY_OWN, G_ALL]], fields=["name", "users"], context=CTX)
    for g in vorher:
        print("  vorher %-42s %d Mitglieder" % (g["name"], len(g["users"])))

    if not schreiben:
        print("\nTrockenlauf - keine Aenderung geschrieben.")
        return 0

    for gid, logins in ((G_ONLY_OWN, fehlend_607), (G_ALL, fehlend_608)):
        if not logins:
            continue
        ids_add = [u["id"] for u in u18 if u["login"] in logins]
        k18.kw("res.groups", "write", [[gid], {"users": [(4, i) for i in ids_add]}])
        print("  gesetzt: Gruppe %s + %d Benutzer" % (gid, len(ids_add)))

    nachher = k18.kw("res.groups", "read", [[G_ONLY_OWN, G_ALL]], fields=["name", "users"], context=CTX)
    for g in nachher:
        print("  nachher %-42s %d Mitglieder" % (g["name"], len(g["users"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
