"""Abnahmepruefung Bereich Kontakte -> Kontaktformular -> Gemeinde-Information (Session 109).

Prueft READ-ONLY gegen eine Odoo-18-Instanz (lokal oder VM):
  1. Sind alle Gemeinde-Felder vorhanden (Name, Typ, Relation, Pflichtfeld)?
  2. Tragen die Modellbeschriftungen die Odoo-11-Wortlaute (auch fuer Suche/Filter/Export)?
  3. Zeigt der gerenderte Arch des Reiters die Felder mit deutscher Beschriftung und is_company-Regel?
  4. Sind die Stammdaten (Groessenklassen, Organisationstypen) vorhanden?
  5. Funktioniert die Berechnung der Groessenklasse aus der Einwohnerzahl?

Aufruf:
    python scripts/verify_s109_gemeinde_info.py --instanz lokal
    python scripts/verify_s109_gemeinde_info.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Feld -> (Typ, Relation, Soll-Beschriftung wie Odoo 11)
FELDER = {
    "population": ("integer", None, "Einwohnerzahl"),
    "community_magnitude": ("char", None, "Gr\u00f6\u00dfenklasse"),
    "community_magnitude_id": ("many2one", "itk_crm.communitymagnitude", "Gr\u00f6\u00dfenklasse"),
    "population_update": ("date", None, "Stand vom"),
    "status_of_community": ("many2one", "itk_crm.statusofcommunity", "Organisationstyp"),
    "member_of_city_alliance": ("boolean", None, "St\u00e4dtebund-Mitglied"),
    "community_salutation": ("char", None, "Organisationsbezeichnung"),
}

# Felder des Reiters Gemeinde-Information mit erwarteter Beschriftung im Arch
ARCH_FELDER = {
    "population": "Einwohnerzahl",
    "community_magnitude": "Gr\u00f6\u00dfenklasse",
    "population_update": "Stand vom",
    "status_of_community": "Organisationstyp",
    "member_of_city_alliance": "St\u00e4dtebund-Mitglied",
}

# Organisationstypen, die in Odoo 11 produktiv vorkommen (Vorgabe fuer die Migration)
ORGANISATIONSTYPEN_11 = ["Marktgemeinde", "Gemeinde", "Stadtgemeinde", "Magistrat", "Magistrat der Stadt",
                         "Gemeindeverband", "-"]


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
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    k = Client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    print("Instanz: %s (%s, DB %s)" % (a.instanz, url, env["ODOO18_DB"]))
    ok = fehler = 0

    def pruefe(bedingung: bool, text: str):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    print("\n1) Felder in Odoo 18 (Typ, Relation, Pflichtfeld)")
    felder = k.kw("res.partner", "fields_get", [list(FELDER), ["type", "relation", "required"]])
    for name, (typ, rel, _) in FELDER.items():
        d = felder.get(name)
        if not d:
            pruefe(False, "%s fehlt" % name)
        elif d["type"] != typ or (rel and d.get("relation") != rel):
            pruefe(False, "%s: Typ %s/%s (erwartet %s/%s)" % (name, d["type"], d.get("relation"), typ, rel))
        else:
            pruefe(True, "%s: %s%s, Pflichtfeld=%s" % (name, d["type"], " -> " + rel if rel else "", d.get("required")))

    print("\n2) Modellbeschriftungen (wirken in Suche, Filter, Export)")
    for name, (_, _, soll) in FELDER.items():
        ist = k.kw("res.partner", "fields_get", [[name], ["string"]], context={"lang": "de_DE"})[name]["string"]
        pruefe(ist == soll, "%s: '%s' (Odoo 11: '%s')" % (name, ist, soll))

    print("\n3) Gerenderter Arch des Reiters 'Gemeinde-Information'")
    arch = k.kw("res.partner", "get_views", [[[False, "form"]]], context={"lang": "de_DE"})["views"]["form"]["arch"]
    i = arch.find('name="community_info"')
    pruefe(i > 0, "Reiter 'community_info' im Arch gefunden")
    j = arch.find("<page", i + 10)
    seg = arch[i:(j if j > 0 else i + 4000)]
    for feld, beschriftung in ARCH_FELDER.items():
        treffer = re.search(r'<field\b[^>]*name="%s"[^>]*/?>' % feld, seg)
        pruefe(bool(treffer), "Feld %s im Reiter" % feld)
        if treffer:
            pruefe('string="%s"' % beschriftung in treffer.group(0),
                   "%s mit Beschriftung '%s'" % (feld, beschriftung))
            pruefe("is_company" in treffer.group(0), "%s nur fuer Unternehmen sichtbar" % feld)

    print("\n4) Stammdaten")
    klassen = k.kw("itk_crm.communitymagnitude", "search_read", [[], ["name", "lower_limit", "upper_limit"]], order="seq")
    pruefe(len(klassen) >= 14, "Groessenklassen: %d (Odoo 18/Repo: 14)" % len(klassen))
    luecken = [p["name"] for p in k.kw("res.partner", "search_read", [[["population", "!=", False]], ["name"]], limit=1)]
    print("       Hinweis: Kontakte mit Einwohnerzahl im Testbestand: %d"
          % k.kw("res.partner", "search_count", [[["population", "!=", False]]]))
    typen = [t["name"] for t in k.kw("itk_crm.statusofcommunity", "search_read", [[], ["name"]], context={"active_test": False})]
    pruefe(len(typen) >= 1, "Organisationstypen vorhanden: %d" % len(typen))
    fehlend = [t for t in ORGANISATIONSTYPEN_11 if t not in typen]
    if fehlend:
        print("       GAP (Vorgabe fuer die Datenmigration, noch nicht anzulegen): %s" % ", ".join(fehlend))

    print("\n5) Funktion: Groessenklasse wird aus der Einwohnerzahl berechnet")
    probe = k.kw("res.partner", "search_read", [[["population", "!=", False]], ["name", "population", "community_magnitude", "community_magnitude_id"]], limit=3)
    for p in probe:
        hat = bool(p["community_magnitude"]) or bool(p["community_magnitude_id"])
        pruefe(hat, "%s: Einwohnerzahl %s -> Groessenklasse %s" % (p["name"][:34], p["population"], p["community_magnitude"] or "-"))

    print("\n6) Modulstand und Kontrollzahlen")
    fuer = {m["name"]: m["installed_version"] for m in k.kw("ir.module.module", "search_read", [[["name", "in", ["itk_crm", "itk_base_setup"]]], ["name", "installed_version"]])}
    print("       itk_crm: %s | itk_base_setup: %s" % (fuer.get("itk_crm"), fuer.get("itk_base_setup")))
    pruefe(fuer.get("itk_crm", "").startswith("18.0.1.5"), "itk_crm auf Stand 18.0.1.5.x (%s)" % fuer.get("itk_crm"))
    print("       Kontakte gesamt: %d" % k.kw("res.partner", "search_count", [[]]))

    print("\nERGEBNIS: %d OK, %d FEHL" % (ok, fehler))
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
