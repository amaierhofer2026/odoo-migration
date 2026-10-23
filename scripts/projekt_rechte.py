"""Rechte Projekt: Gruppenmitglieder nach dem Odoo-11-Rechtekonzept setzen.

Standard ist der TROCKENLAUF. Schreiben nur mit
    --ausfuehren --ich-habe-freigabe

Odoo 11: "Projekt / Benutzer" (project.group_project_user) und "Projekt / Manager"
(project.group_project_manager). Zuordnung ueber Login UND Benutzername, weil sich
Logins zwischen Odoo 11 und Odoo 18 geaendert haben (Beispiel Breiteneder Lorenz).
Bestehende Mitglieder werden nicht entfernt.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}
GRUPPEN = ["group_project_user", "group_project_manager"]


def normal(w):
    return (w or "").strip().lower()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    a = ap.parse_args()
    env = lade_env()
    schreiben = a.ausfuehren and a.ich_habe_freigabe
    if a.ausfuehren and not a.ich_habe_freigabe:
        print("STOPP: --ausfuehren nur zusammen mit --ich-habe-freigabe")
        return 2
    if schreiben and not env["ODOO18_DB"].endswith("odoo18_test"):
        print("STOPP: Ziel-DB ist nicht die Testdatenbank:", env["ODOO18_DB"])
        return 2

    k11, k18 = o11(), o18(a.instanz)
    print("### Instanz:", a.instanz, " Modus:", "SCHREIBEN" if schreiben else "Trockenlauf")

    ids11 = {}
    for x in k11.kw("ir.model.data", "search_read",
                    [["&", ("model", "=", "res.groups"), ("module", "=", "project"),
                      ("name", "in", GRUPPEN)]], fields=["name", "res_id"], limit=0):
        ids11[x["name"]] = x["res_id"]
    ids18 = {}
    for x in k18.kw("ir.model.data", "search_read",
                    [["&", ("model", "=", "res.groups"), ("module", "=", "project"),
                      ("name", "in", GRUPPEN)]], fields=["name", "res_id"], limit=0):
        ids18[x["name"]] = x["res_id"]

    mitglieder11 = {}
    for name in GRUPPEN:
        grp = k11.kw("res.groups", "read", [[ids11[name]]], fields=["users"], context=CTX)[0]
        mitglieder11[name] = k11.kw("res.users", "read", [sorted(grp["users"])],
                                    fields=["login", "name"], context={"active_test": False}) \
            if grp["users"] else []
        print("  Odoo 11 %-24s %d Benutzer" % (name, len(mitglieder11[name])))

    u18 = [u for u in k18.kw("res.users", "search_read",
                             [[("share", "=", False), ("active", "=", True)]],
                             fields=["id", "login", "name", "groups_id"], limit=0)
           if u["login"] not in ("__system__", "default", "public", "portaltemplate")]
    print("  Odoo 18 aktive interne Benutzer: %d" % len(u18))

    def trifft(u, liste):
        if any(normal(x["login"]) == normal(u["login"]) for x in liste):
            return True
        return any(normal(x["name"]) == normal(u["name"]) for x in liste)

    plan = {}
    for name in GRUPPEN:
        ziel = [u for u in u18 if trifft(u, mitglieder11[name])]
        fehlen = [u for u in ziel if ids18[name] not in u["groups_id"]]
        plan[name] = (ziel, fehlen)
        print("\n=== %s: %d Benutzer, davon %d zu ergaenzen ===" % (name, len(ziel), len(fehlen)))
        for u in ziel:
            print("   %s %-38s %s" % ("+" if u in fehlen else "=", u["login"], u["name"]))

    for name in GRUPPEN:
        g = k18.kw("res.groups", "read", [[ids18[name]]], fields=["name", "users"], context=CTX)[0]
        print("  vorher %-42s %d Mitglieder" % (g["name"], len(g["users"])))

    if not schreiben:
        print("\nTrockenlauf - keine Aenderung geschrieben.")
        return 0

    for name in GRUPPEN:
        _, fehlen = plan[name]
        if not fehlen:
            continue
        k18.kw("res.groups", "write", [[ids18[name]], {"users": [(4, u["id"]) for u in fehlen]}])
        print("  gesetzt: %s + %d Benutzer" % (name, len(fehlen)))
    for name in GRUPPEN:
        g = k18.kw("res.groups", "read", [[ids18[name]]], fields=["name", "users"], context=CTX)[0]
        print("  nachher %-42s %d Mitglieder" % (g["name"], len(g["users"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
