"""Sichtbare Odoo-11-Bezeichnungen auf sale.order setzen (Session 117).

Setzt die Beschriftungen, die Anna fuer den Bereich Angebote/Verkaufsauftraege
aus dem Odoo-11-Wortlaut uebernehmen will. Es werden ausschliesslich
Feldbeschreibungen (de_DE) gesetzt - keine Modell- oder Feldnamen.

Warum ein Skript: Odoo 18 setzt die deutschen Feldbeschriftungen bei einem
Modul-Upgrade auf die Quelltexte zurueck (Session 115, F34). Das Skript laeuft
deshalb nach jedem Upgrade - lokal und auf der VM.

Aufruf:
    python scripts/apply_sale_labels.py --instanz lokal
    python scripts/apply_sale_labels.py --instanz vm
    python scripts/apply_sale_labels.py --instanz vm --pruefen    (nur lesen)
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Odoo-11-Wortlaut, der in Odoo 18 gesetzt werden soll
LABELS = {
    ("sale.order", "team_id"): "Vertriebskanal",
    ("sale.order", "administrative_contact_id"): "Verwaltungskontakt",
    ("sale.order", "opportunity_id"): "Chance",
    ("sale.order", "source_id"): "Referenz",
    ("sale.order", "sale_contact_id"): "Verkaufskontakt",
    ("sale.order", "technical_contact_id"): "Technischer Kontakt",
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
        with self.opener.open(req, timeout=300) as antwort:
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
    for (modell, fname), wunsch in LABELS.items():
        treffer = k.kw("ir.model.fields", "search_read", [[["model", "=", modell], ["name", "=", fname]], ["id"]],
                       context={"lang": "en_US"})
        if not treffer:
            print("  --   %s.%s nicht vorhanden (uebersprungen)" % (modell, fname))
            continue
        fid = treffer[0]["id"]
        ist = k.kw("ir.model.fields", "read", [[fid], ["field_description"]], context={"lang": "de_DE"})[0]["field_description"]
        if ist == wunsch:
            print("  OK   %s.%s = '%s'" % (modell, fname, ist))
            continue
        if a.pruefen:
            abweichung += 1
            print("  FEHL %s.%s = '%s' (erwartet '%s')" % (modell, fname, ist, wunsch))
            continue
        k.kw("ir.model.fields", "write", [[fid], {"field_description": wunsch}], context={"lang": "de_DE"})
        ist2 = k.kw("ir.model.fields", "read", [[fid], ["field_description"]], context={"lang": "de_DE"})[0]["field_description"]
        if ist2 == wunsch:
            geaendert += 1
            print("  OK   %s.%s gesetzt: '%s'" % (modell, fname, wunsch))
        else:
            abweichung += 1
            print("  FEHL %s.%s konnte nicht gesetzt werden (Ist: '%s')" % (modell, fname, ist2))
    print("\nErgebnis: %d gesetzt, %d Abweichungen%s" % (geaendert, abweichung, " (Pruefmodus)" if a.pruefen else ""))
    return 0 if abweichung == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
