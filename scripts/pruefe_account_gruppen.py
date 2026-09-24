"""Klaert, ob der Odoo-18-Benutzer die Gruppe account.group_account_readonly hat (Seite 'Buchhaltung')."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vergleich_abo_produktformular as V  # noqa: E402

SP = {"lang": "de_DE"}


def probes(instanz, login):
    k = V.client(instanz)
    print("=== %s ===" % instanz)
    g = k("ir.model.data", "search_read",
          [[["module", "=", "account"], ["model", "=", "res.groups"]], ["res_id", "name"]], context=SP, limit=40)
    ids = {x["name"]: x["res_id"] for x in (g or [])}
    for n in ("group_account_readonly", "group_account_user", "group_account_invoice", "group_account_manager",
              "group_account_basic", "group_account_adviser"):
        if n in ids:
            print("   %-28s id=%s" % (n, ids[n]))
    u = k("res.users", "search_read", [[["login", "=", login], ], ["id", "login", "groups_id"]], context=SP)
    if not (isinstance(u, list) and u):
        print("   Benutzer nicht gefunden: %s" % u)
        return
    meine = set(u[0]["groups_id"])
    for n, i in ids.items():
        print("   %-28s id=%-5s im Benutzer: %s" % (n, i, i in meine))
    xid = k("ir.model.data", "search_read",
            [[["model", "=", "ir.ui.view"], ["res_id", "=", 1024]], ["module", "name"]], context=SP)
    print("   Ansicht 1024 xml_id: %s" % xid)
    m = k("ir.model.data", "search_read", [[["model", "=", "ir.ui.view"]], ["res_id", "name", "module"]],
          context=SP, limit=0)
    treffer = [x for x in (m or []) if x["res_id"] == 1024]
    print("   xml_id der Ansicht: %s" % treffer)
    print()


probes("o18", "anna.maierhofer@it-kommunal.at")
probes("o11", "anna.maierhofer@it-kommunal.at")
