"""Diagnose: ist 'Pruefpfad' im Browser-Menuebaum (load_menus) enthalten? (read-only)"""
from __future__ import annotations

import http.cookiejar
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o18

k18 = o18("vm")
env = lade_env()

# 1) Menue- und Aktionsdatensatz
for m in k18.kw("ir.ui.menu", "search_read", [[("name", "=", "Prüfpfad")],
                                              ["id", "name", "action", "groups_id", "parent_id", "sequence"]],
                context={"lang": "de_DE", "ir.ui.menu.full_list": True}):
    print("Menue: %s" % m)
    art, aid = m["action"].split(",")
    if art == "ir.actions.act_window":
        d = k18.kw("ir.actions.act_window", "read", [[int(aid)],
                                                     ["name", "res_model", "domain", "groups_id", "binding_model_id"]])
        print("Aktion: %s" % d[0])

# 2) load_menus (Quelle des Browsers) pruefen
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
req = urllib.request.Request("https://k001959vsx.ipax.at/web/session/authenticate",
                            data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                             "params": {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                                        "password": env["ODOO18_PWD"]}}).encode(),
                            headers={"Content-Type": "application/json"})
op.open(req).read()
req = urllib.request.Request("https://k001959vsx.ipax.at/web/webclient/load_menus",
                            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {}}).encode(),
                            headers={"Content-Type": "application/json"})
antwort = json.loads(op.open(req).read().decode())
menues = antwort.get("result", {}).get("menus", {})
namen = {v.get("name", "") for v in menues.values()}
print("\nload_menus: %d Menues" % len(menues))
print("'Prüfpfad' enthalten: %s" % ("Prüfpfad" in namen))
for v in menues.values():
    if v.get("name") in ("Prüfpfad", "Rechnungsanalyse", "Abrechnungspositionen", "Verwaltung",
                         "Berichtswesen", "Kunden", "Lieferanten", "Konfiguration"):
        print("   id=%-5s parent=%-5s action=%-22s %s" % (v.get("id"), v.get("parent_id"),
                                                          str(v.get("action"))[:22], v.get("name")))
