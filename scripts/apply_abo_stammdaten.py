"""Fehlende Abo-Stammdaten aus Odoo 11 in Odoo 18 anlegen (Session 118, Teil 5).

Von Anna freigegeben (18.09.2026): die in Odoo 11 tatsaechlich referenzierten Vorlagen und
Beendigungsgruende in Odoo 18 als Stammdaten vorbereiten.

Grundlage (read-only in Odoo 11 geprueft):
  Vorlagen: 5 in Odoo 11 - 3 existieren in Odoo 18, "5-Jahresabo" wird von 0 Abos referenziert
            (nicht angelegt), "J- Jahresabrechnungsabo-Mindestvertragsdauer 12 Monate" von 1 Abo.
  Beendigungsgruende: 33 in Odoo 11 mit zusammen 291 Verwendungen - 5 existieren in Odoo 18
            (121 Verwendungen), 26 weitere mit 170 Verwendungen werden angelegt,
            2 weitere (id 20 und 24) haben 0 Verwendungen (nicht angelegt).

Es werden ausschliesslich Stammdatensaetze angelegt - keine Abos, keine Auftraege, keine Rechnungen.

Aufruf:
    python scripts/apply_abo_stammdaten.py --instanz lokal
    python scripts/apply_abo_stammdaten.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VORLAGE = {
    "name": "J- Jahresabrechnungsabo-Mindestvertragsdauer 12 Monate",
    "recurring_rule_type": "monthly",
    "recurring_interval": 1,
    "minimum_contract_life": 12,
    "minimum_contract_life_unit": "monthly",
    "contract_termination_period_number": 0,
    "contract_termination_period_unit": "yearly",
    "payment_mandatory": False,
    "user_closable": False,
}

# Sechsundzwanzig Beendigungsgruende mit Verwendungen in Odoo 11 (id 6-33 ohne 20 und 24)
GRUENDE = [
    "Upgrade auf ein höherwertiges Produkt",
    "Service nicht bestellt",
    "Upgrade auf ein höherwertiges Produkt/läuft über GVA Baden",
    "wird ab 2021 über Gemdat OÖ verrechnet!",
    "unter anderem Abo verrechnet!",
    "Andere/hat ursprünglich Basispaket bestellt",
    "Upgrade auf ein höherwertiges Produkt/läuft über GVA Mödling",
    "wird nun über GVA Mödling verrechnet",
    "im GV Amstetten gelistet",
    "doppelt erfasst",
    "im GV Waidhofen/Thaya gelistet",
    "keine Verrechnung/Koop.-projekt Gemdat OÖ",
    "über GV Horn Regionenmandant verrechnet!",
    "Umstieg auf Mayan-Verwaltungsmanager",
    "wird von Intrakommuna abgelöst",
    "wird nicht benötigt",
    "direkter Kunde der Gemdat NÖ",
    "wird unter Gemeinde-Servicezentrum verrechnet",
    "Mindestvertragsdauer muss verändert werden, deswegen neues abo anlegen",
    "nie für amtsweg.gv.at Region Standard registriert",
    "über GV Gänserndorf Regionenmandant verrechnet!",
    "kommt über anderen Anbieter (GV Hollabrunn",
    "Kommt über GAUM Mistelbach",
    "anderer Kundenname",
    "Upgrade auf ein höherwertiges Produkt(GVU Gänserndorf)",
    "Kunde hat bereits ein Gemeindecloudabo, dort wird angepasst!",
]


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
    p.add_argument("--pruefen", action="store_true")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    k = Client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    print("Instanz: %s (%s)" % (a.instanz, url))
    neu = da = 0

    # Vorlage
    vor = k.kw("sale.subscription.template", "search_read", [[["name", "=", VORLAGE["name"]]], ["id"]])
    if vor:
        da += 1
        print("  OK   Vorlage vorhanden: %s" % VORLAGE["name"])
    elif a.pruefen:
        print("  FEHL Vorlage fehlt: %s" % VORLAGE["name"])
    else:
        k.kw("sale.subscription.template", "create", [VORLAGE])
        neu += 1
        print("  OK   Vorlage angelegt: %s" % VORLAGE["name"])

    # Beendigungsgruende
    vorhanden = {g["name"] for g in k.kw("sale.subscription.close.reason", "search_read", [[], ["name"]])}
    fehlend = [g for g in GRUENDE if g not in vorhanden]
    if fehlend and not a.pruefen:
        k.kw("sale.subscription.close.reason", "create", [[{"name": g} for g in fehlend]])
        neu += len(fehlend)
        print("  OK   %d Beendigungsgruende angelegt" % len(fehlend))
    elif fehlend:
        print("  FEHL %d Beendigungsgruende fehlen" % len(fehlend))
    if not fehlend:
        da += len(GRUENDE)
        print("  OK   alle %d Beendigungsgruende vorhanden" % len(GRUENDE))

    # Kontrolle
    alle = {g["name"] for g in k.kw("sale.subscription.close.reason", "search_read", [[], ["name"]])}
    fehlt = [g for g in GRUENDE if g not in alle]
    v = k.kw("sale.subscription.template", "search_count", [[["name", "=", VORLAGE["name"]]]])
    print("\nKontrolle: Vorlage %s, Beendigungsgruende fehlen %d, gesamt in Odoo 18: %d (neu angelegt: %d)"
          % ("vorhanden" if v else "FEHLT", len(fehlt), len(alle), neu))
    return 0 if (v and not fehlt) else 1


if __name__ == "__main__":
    sys.exit(main())
