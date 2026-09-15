#!/usr/bin/env python3
"""Strukturpruefung Kontakte: Kontaktliste + Kontaktsuche in Odoo 18 - Session 93.

Prueft read-only, ob die Odoo-11-Prod-Spalten und -Filter der Kontaktansichten
wiederhergestellt sind und nichts anderes beschaedigt wurde:

  Liste   : function, is_company, parent_id, salutation, active (optional="show"),
            category_id (optional="show"), zweite Namensspalte display_name (optional="hide"),
            keine Doppelspalten, O18-Spalten (complete_name, ref, phone, email, user_id) weiter da
  Suche   : Filter "Meine Partner" [('user_id','=',uid)] und "Meine Aktivitaeten"
            [('activity_ids.user_id','=',uid)] sowie die O18-Standardfilter
  Daten   : res.partner-Zaehler (keine Datenaenderung erwartet)

Aufruf:
    python scripts/verify_s93_contact_views.py --instanz lokal
    python scripts/verify_s93_contact_views.py --instanz vm
Credentials aus C:\\Odoo-Test\\.env (nie ausgeben).
"""
import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URLS = {"vm": "https://k001959vsx.ipax.at", "lokal": "http://localhost:8069"}


def lade_env():
    env = {}
    with open(os.path.join(BASIS, ".env"), encoding="utf-8") as fh:
        for zeile in fh:
            zeile = zeile.strip()
            if zeile and not zeile.startswith("#") and "=" in zeile:
                k, v = zeile.split("=", 1)
                env[k.strip()] = v.strip()
    return env


class DB:
    def __init__(self, url, env):
        self.url = url
        jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        self.db, self.pwd = env["ODOO18_DB"], env["ODOO18_PWD"]
        r = self._roh("/web/session/authenticate", {"db": self.db, "login": env["ODOO18_USER"], "password": self.pwd})
        self.uid = (r.get("result") or {}).get("uid")
        if not self.uid:
            sys.exit("FEHLER: Anmeldung fehlgeschlagen (%s)" % json.dumps(r)[:200])

    def _roh(self, pfad, prm):
        req = urllib.request.Request(self.url + pfad,
                                     data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": prm}).encode(),
                                     headers={"Content-Type": "application/json"})
        with self.op.open(req, timeout=180) as f:
            return json.loads(f.read().decode())

    def kw(self, model, method, args, kwargs=None):
        o = self._roh("/web/dataset/call_kw", {"model": model, "method": method, "args": args,
                                              "kwargs": kwargs or {}})
        if "error" in o:
            raise RuntimeError(json.dumps(o["error"])[:300])
        return o["result"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal", choices=sorted(URLS))
    args = ap.parse_args()
    db = DB(URLS[args.instanz], lade_env())
    de = {"lang": "de_DE"}
    ok, fehler = [], []

    def pruefe(bedingung, text, detail=""):
        (ok if bedingung else fehler).append(text)
        print("   [%s] %s%s" % ("OK" if bedingung else "FEHLT", text, (" - " + detail) if detail else ""))

    print("Instanz %s (uid %s)" % (args.instanz, db.uid))

    print("\n1) Modul")
    m = db.kw("ir.module.module", "search_read", [[["name", "=", "itk_base_setup"]]],
              {"fields": ["state", "installed_version"]})
    pruefe(bool(m) and m[0]["state"] == "installed", "itk_base_setup installiert",
           m[0]["installed_version"] if m else "nicht gefunden")
    pruefe(bool(m) and m[0]["installed_version"] >= "18.0.1.0.1", "Version >= 18.0.1.0.1", m[0]["installed_version"] if m else "-")

    print("\n2) Kontaktliste")
    arch = db.kw("res.partner", "get_views", [[[False, "list"]]], {"context": de})["views"]["list"]["arch"]
    flach = " ".join(arch.split())

    def hat_feld(name):
        return re.search(r'<field[^>]*name="%s"' % re.escape(name), flach) is not None

    def optional_von(name):
        m2 = re.search(r'<field[^>]*name="%s"[^>]*/?>' % re.escape(name), flach)
        if not m2:
            return None
        o = re.search(r'optional="([^"]*)"', m2.group(0))
        return o.group(1) if o else ""

    for feld, label in (("function", "Stelle"), ("is_company", "Ist ein Unternehmen"),
                        ("parent_id", "Zugehoeriges Unternehmen"), ("salutation", "Anrede"), ("active", "Aktiv")):
        pruefe(hat_feld(feld), "Spalte %s (%s) vorhanden" % (feld, label), "optional=%r" % optional_von(feld))
        pruefe(optional_von(feld) == "show", "Spalte %s/Optional-Status 'show'" % feld)
    pruefe(optional_von("category_id") == "show", "Stichwoerter (category_id) sichtbar", "optional=%r" % optional_von("category_id"))
    pruefe(optional_von("display_name") == "hide", "zweite Namensspalte display_name ausgeblendet",
           "optional=%r" % optional_von("display_name"))
    for feld in ("complete_name", "ref", "phone", "email", "user_id", "country_id"):
        pruefe(hat_feld(feld), "O18-Spalte %s weiterhin vorhanden" % feld)

    # Doppelte Spalten nur zaehlen, wenn sie auch sichtbar sind (hidden via column_invisible/optional=hide zaehlt nicht)
    sichtbar = []
    for m2 in re.finditer(r'<field[^>]*/?>', flach):
        tag = m2.group(0)
        nm = re.search(r'name="([^"]+)"', tag)
        if not nm:
            continue
        versteckt = ("column_invisible" in tag) or ('optional="hide"' in tag)
        if not versteckt:
            sichtbar.append(nm.group(1))
    doppelt = sorted({n for n in sichtbar if sichtbar.count(n) > 1})
    pruefe(not doppelt, "keine doppelten sichtbaren Spalten", str(doppelt) if doppelt else "")

    print("\n3) Kontaktsuche")
    sarch = db.kw("res.partner", "get_views", [[[False, "search"]]], {"context": de})["views"]["search"]["arch"]
    sflach = " ".join(sarch.split())
    pruefe('name="itk_my_partners"' in sflach and "string=\"Meine Partner\"" in sflach,
           "Filter 'Meine Partner' vorhanden")
    pruefe("username" not in sflach and "('user_id','=',uid)" in sflach.replace('"', "'"),
           "Domain 'Meine Partner' = user_id = aktueller Benutzer")
    pruefe('name="itk_activities_my"' in sflach, "Filter 'Meine Aktivitaeten' vorhanden")
    pruefe("activity_ids.user_id" in sflach, "Domain 'Meine Aktivitaeten' = activity_ids.user_id")
    for f in ("type_person", "type_company", "customer", "supplier", "salesperson", "activities_overdue",
              "activities_today", "activities_upcoming_all", "inactive", "group_country"):
        pruefe('name="%s"' % f in sflach, "O18-Filter %s weiterhin vorhanden" % f)

    print("\n4) Filter-Domains (muessen fehlerfrei zaehlen)")
    for dom, label in (([("user_id", "=", db.uid)], "Meine Partner"),
                       ([("activity_ids.user_id", "=", db.uid)], "Meine Aktivitaeten"),
                       ([("parent_id", "!=", False)], "Mit uebergeordnetem Kontakt"),
                       ([("is_company", "=", True)], "Unternehmen"),
                       ([("category_id", "!=", False)], "Mit Stichwort")):
        try:
            n = db.kw("res.partner", "search_count", [dom])
            pruefe(True, "Domain %s" % label, "%d Kontakte" % n)
        except Exception as e:
            pruefe(False, "Domain %s" % label, str(e)[:120])

    print("\n5) Daten unveraendert (Kontrollzahlen)")
    for modell in ("res.partner", "res.partner.category", "sale.subscription", "sale.order"):
        try:
            print("      %-22s %d" % (modell, db.kw(modell, "search_count", [[]])))
        except Exception as e:
            print("      %-22s FEHLER %s" % (modell, str(e)[:80]))

    print("\nErgebnis: %d OK, %d FEHLER" % (len(ok), len(fehler)))
    if fehler:
        for f in fehler:
            print("   - %s" % f)
    return 0 if not fehler else 2


if __name__ == "__main__":
    sys.exit(main())
