#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ITK Abschnitt-1-Korrekturen (Freigabe Anna 02.09.2026, Session 81).
Setzt gezielte de_DE-Slots (Menues, Actions, Felder) per ORM-write mit lang-Context
(jsonb_set-Aequivalent) gegen die VM (https://k001959vsx.ipax.at, DB odoo18_test,
Credentials aus C:\Odoo-Test\.env ODOO18_*). Idempotent; nach jedem Restore aus einem
Backup VOR dem Fix erneut ausfuehren (bzw. beim naechsten Setup-Lauf).
Nur dokumentierte Stellen - keine globale Ersetzung.
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Nachlauf: Menue-/Action-Fixes (de_DE-Slots) + Korrektur helpdesk.sla.stage_id 'Stufe'."""
import json, os, urllib.request, http.cookiejar

URL = "https://k001959vsx.ipax.at"
env = {}
for line in open(r"C:\Odoo-Test\.env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
DB, LOGIN, PWD = env.get("ODOO18_DB", "odoo18_test"), env.get("ODOO18_USER", ""), env.get("ODOO18_PWD", "")
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
def rpc(url, params, timeout=120):
    body = json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with opener.open(req, timeout=timeout) as r:
        resp = json.loads(r.read().decode())
    if "error" in resp:
        raise RuntimeError("RPC-Fehler: %s" % str(resp["error"])[:400])
    return resp.get("result")
res = rpc(URL + "/web/session/authenticate", {"db": DB, "login": LOGIN, "password": PWD})
uid = res.get("uid")
def exec_kw(model, method, args=None, kwargs=None):
    return rpc(URL + "/web/dataset/call_kw", {"model": model, "method": method,
               "args": args or [], "kwargs": kwargs or {}})

MENU_FIX = {736: "Alle Kunden", 737: "Aktuelle Kunden", 738: "Ehemalige Kunden", 739: "Zielkunden",
    740: "Alle Reseller", 891: "Support-Tickets", 601: "Alle Auftragszeilen",
    746: "Alle Tickets", 775: "SLA-Bericht", 757: "Zeiterfassung", 756: "Arbeit starten"}
ACT_FIX = {"Actual customers": "Aktuelle Kunden", "All customers": "Alle Kunden",
    "Former Customers": "Ehemalige Kunden", "Target Customers": "Zielkunden",
    "All Resellers": "Alle Reseller", "Order Lines": "Auftragszeilen",
    "Support Tickets": "Support-Tickets", "Helpdesk Ticket": "Helpdesk-Ticket",
    "Helpdesk Tickets": "Helpdesk-Tickets", "SLA Report": "SLA-Bericht",
    "Start work": "Arbeit starten", "Timesheets": "Zeiterfassung",
    "Set Pricelist for Subscriptions": "Preisliste für Abonnements festlegen",
    "Update Multifactor for Subscriptionlines": "Multifaktor für Abo-Zeilen aktualisieren",
    "Update Population and Multifactor for Partners": "Einwohnerzahl und Faktor für Partner aktualisieren"}
MODS = ["itk_crm","itk_translation","itk_subscription","itk_product","itk_sale_management",
    "itk_valorisierung","itk_projectcategory","itk_base_setup","itk_third_party_setup","itk_reports",
    "itk_saleorder_lines","itk_multifactor","itk_automated_actions","itk_helpdesk_category_user",
    "itk_helpdesk_compat","helpdesk_mgmt","helpdesk_mgmt_project","helpdesk_mgmt_sla",
    "helpdesk_mgmt_timesheet","project_timesheet_time_control","server_action_mass_edit"]

# Menues
ids = list(MENU_FIX.keys())
de_rows = exec_kw("ir.ui.menu", "read", [ids, ["id", "name"]], {"context": {"lang": "de_DE"}})
en_rows = exec_kw("ir.ui.menu", "read", [ids, ["id", "name"]], {"context": {"lang": "en_US"}})
enmap = {x["id"]: x["name"] for x in en_rows}
for x in sorted(de_rows, key=lambda r: r["id"]):
    if x["name"] == enmap.get(x["id"]) and str(x["name"]) != str(MENU_FIX[x["id"]]):
        exec_kw("ir.ui.menu", "write", [[x["id"]], {"name": MENU_FIX[x["id"]]}], {"context": {"lang": "de_DE"}})
        print("MENUE %s: %r -> %r" % (x["id"], x["name"], MENU_FIX[x["id"]]))
    else:
        print("MENUE %s (%r): uebersprungen" % (x["id"], x["name"]))

# Actions
imd = exec_kw("ir.model.data", "search_read",
              [[["module", "in", MODS], ["model", "=", "ir.actions.act_window"]], ["res_id"]])
aids = list({r["res_id"] for r in imd if r.get("res_id")})
de_rows = exec_kw("ir.actions.act_window", "read", [aids, ["id", "name"]], {"context": {"lang": "de_DE"}})
en_rows = exec_kw("ir.actions.act_window", "read", [aids, ["id", "name"]], {"context": {"lang": "en_US"}})
enmap = {x["id"]: x["name"] for x in en_rows}
for x in de_rows:
    if x["name"] in ACT_FIX and x["name"] == enmap.get(x["id"]):
        exec_kw("ir.actions.act_window", "write", [[x["id"]], {"name": ACT_FIX[x["name"]]}], {"context": {"lang": "de_DE"}})
        print("ACTION %s: %r -> %r" % (x["id"], x["name"], ACT_FIX[x["name"]]))

# Korrektur helpdesk.sla.stage_id: Phase -> Stufe
f = exec_kw("ir.model.fields", "search_read", [[["model", "=", "helpdesk.sla"], ["name", "=", "stage_id"]], ["id"]])
if f:
    exec_kw("ir.model.fields", "write", [[f[0]["id"]], {"field_description": "Stufe"}], {"context": {"lang": "de_DE"}})
    print("helpdesk.sla.stage_id -> Stufe")
print("FERTIG")
