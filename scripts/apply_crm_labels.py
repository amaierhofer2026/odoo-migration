"""Sichtbare Odoo-11-Bezeichnungen der Kundenverwaltung setzen (Session 115).

Hintergrund (auf der VM empirisch nachgewiesen):
Beim Upgrade von itk_crm setzt Odoo 18 die deutschen Beschriftungen der
crm.lead-Felder auf die Quelltexte zurueck (Registry-Abgleich der
ir.model.fields-Datensaetze laeuft nach dem Setup-Schritt des Moduls). Die
Label-Funktion im Modul kann das deshalb nicht allein halten.

Dieses Skript setzt die Beschriftungen idempotent per RPC - lokal und auf der
VM - und wird nach jedem itk_crm-Upgrade auf der VM ausgefuehrt. Damit bleibt
die Oberflaeche auf dem Odoo-11-Wortlaut, ohne dass Daten geaendert werden:
es werden ausschliesslich Beschriftungen (Feldtexte) gesetzt.

Aufruf:
    python scripts/apply_crm_labels.py --instanz lokal
    python scripts/apply_crm_labels.py --instanz vm
    python scripts/apply_crm_labels.py --instanz vm --pruefen    (nur lesen)
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Feldbeschriftungen auf crm.lead (Wortlaut aus Odoo 11 Prod, fields_get de_DE)
FELDER = {
    "crm.lead.stage_id": "Stufe",
    "crm.lead.user_id": "Verkäufer",
    "crm.lead.team_id": "Vertriebskanal",
    "crm.lead.lost_reason_id": "Ablehnungsgrund",
    "crm.lead.date_deadline": "Erwartetes Abschlussdatum",
}

# Menues und Aktionsnamen (xmlid -> deutscher Wortlaut)
XMLIDS = {
    "crm.menu_crm_lead_categ": ("ir.ui.menu", "Lead Tags"),
    "crm.menu_crm_lost_reason": ("ir.ui.menu", "Ablehnungsgründe"),
    "crm.crm_stage_action": ("ir.actions.act_window", "Stufen"),
    "sales_team.sales_team_crm_tag_action": ("ir.actions.act_window", "Lead Tags"),
    "crm.crm_lost_reason_action": ("ir.actions.act_window", "Ablehnungsgründe"),
}


def lade_env(pfad: str) -> dict:
    werte = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                s, w = zeile.split("=", 1)
                werte[s.strip()] = w.strip()
    return werte


class Client:
    def __init__(self, url: str, db: str, user: str, pwd: str):
        self.url = url.rstrip("/")
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        self.rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})

    def rufe(self, pfad: str, params: dict):
        req = urllib.request.Request(
            self.url + pfad,
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode(),
            headers={"Content-Type": "application/json"})
        with self.opener.open(req, timeout=240) as antwort:
            daten = json.loads(antwort.read().decode())
        if "error" in daten:
            raise RuntimeError(json.dumps(daten["error"])[:300])
        return daten.get("result")

    def kw(self, model: str, methode: str, args: list, **kwargs):
        return self.rufe("/web/dataset/call_kw",
                         {"model": model, "method": methode, "args": args, "kwargs": kwargs})


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="vm")
    p.add_argument("--pruefen", action="store_true", help="nur lesen, nichts schreiben")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    k = Client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    print("Instanz: %s (%s)" % (a.instanz, url))
    geaendert = abweichung = 0

    for schluessel, wunsch in FELDER.items():
        teile = schluessel.split(".")
        modell, fname = ".".join(teile[:-1]), teile[-1]
        treffer = k.kw("ir.model.fields", "search_read",
                       [[["model", "=", modell], ["name", "=", fname]], ["id"]], context={"lang": "en_US"})
        if not treffer:
            print("  FEHL %s nicht gefunden" % schluessel)
            abweichung += 1
            continue
        fid = treffer[0]["id"]
        ist = k.kw("ir.model.fields", "read", [[fid], ["field_description"]], context={"lang": "de_DE"})[0]["field_description"]
        if not a.pruefen and ist != wunsch:
            k.kw("ir.model.fields", "write", [[fid], {"field_description": wunsch}], context={"lang": "de_DE"})
            ist2 = k.kw("ir.model.fields", "read", [[fid], ["field_description"]], context={"lang": "de_DE"})[0]["field_description"]
            if ist2 == wunsch:
                geaendert += 1
                print("  OK   %s gesetzt: '%s'" % (schluessel, wunsch))
            else:
                abweichung += 1
                print("  FEHL %s konnte nicht gesetzt werden (Ist: '%s')" % (schluessel, ist2))
        else:
            if ist == wunsch:
                print("  OK   %s = '%s'" % (schluessel, ist))
            else:
                abweichung += 1
                print("  FEHL %s = '%s' (erwartet '%s')" % (schluessel, ist, wunsch))

    for xmlid, (model, wunsch) in XMLIDS.items():
        module, name = xmlid.split(".")
        d = k.kw("ir.model.data", "search_read", [[["module", "=", module], ["name", "=", name]], ["res_id"]])
        if not d:
            print("  --   %s nicht vorhanden (uebersprungen)" % xmlid)
            continue
        rid = d[0]["res_id"]
        ist = k.kw(model, "read", [[rid], ["name"]], context={"lang": "de_DE"})[0]["name"]
        if not a.pruefen and ist != wunsch:
            k.kw(model, "write", [[rid], {"name": wunsch}], context={"lang": "de_DE"})
            ist2 = k.kw(model, "read", [[rid], ["name"]], context={"lang": "de_DE"})[0]["name"]
            if ist2 == wunsch:
                geaendert += 1
                print("  OK   %s gesetzt: '%s'" % (xmlid, wunsch))
            else:
                abweichung += 1
                print("  FEHL %s konnte nicht gesetzt werden (Ist: '%s')" % (xmlid, ist2))
        else:
            if ist == wunsch:
                print("  OK   %s = '%s'" % (xmlid, ist))
            else:
                abweichung += 1
                print("  FEHL %s = '%s' (erwartet '%s')" % (xmlid, ist, wunsch))

    print("\nErgebnis: %d gesetzt, %d Abweichungen%s" % (geaendert, abweichung, " (Pruefmodus)" if a.pruefen else ""))
    return 0 if abweichung == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
