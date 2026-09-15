#!/usr/bin/env python3
"""Strukturpruefung Kontakt-Tags (res.partner.category) in Odoo 18 - Session 92.

Liest read-only den Zustand der Tag-Ansichten und -Filter:
  * Modul itk_partner_category (installiert? Version)
  * Listenansicht: display_name (Pfad), id, name (Label "Tag Anzeigename"),
    parent_id/color als optional=hide
  * Formularansicht: display_name read-only, name, parent_id, child_ids, active, color
  * Suchansicht: Suchfeld parent_id (child_of) + Filter Hauptkategorien/Unterkategorien/
    Verwendete/Unverwendete/Mit Kindern/Ohne Kinder
  * Hierarchiesuche ueber display_name (child_of) und die Filter-Domains

Mit --hierarchie-test wird zusaetzlich ein temporaeres Eltern-/Kind-Paar angelegt,
der berechnete Pfad (display_name) und parent_path geprueft und BEIDES WIEDER GELOESCHT.
Die Tag-Anzahl vorher/nachher wird verglichen (muss gleich sein).

Aufruf:
    python scripts/verify_s92_partner_category.py --instanz lokal
    python scripts/verify_s92_partner_category.py --instanz vm --hierarchie-test
Credentials aus C:\\Odoo-Test\\.env (nie ausgeben).
"""
import argparse
import http.cookiejar
import json
import os
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
    ap.add_argument("--hierarchie-test", action="store_true")
    args = ap.parse_args()

    db = DB(URLS[args.instanz], lade_env())
    ok, fehler = [], []

    def pruefe(bedingung, text, detail=""):
        (ok if bedingung else fehler).append(text)
        print("   [%s] %s%s" % ("OK" if bedingung else "FEHLT", text, (" - " + detail) if detail else ""))

    print("Instanz %s (uid %s)" % (args.instanz, db.uid))

    print("\n1) Modul")
    m = db.kw("ir.module.module", "search_read", [[["name", "=", "itk_partner_category"]]],
              {"fields": ["state", "installed_version"]})
    pruefe(bool(m) and m[0]["state"] == "installed", "Modul itk_partner_category installiert",
           m[0]["installed_version"] if m else "nicht gefunden")

    print("\n2) Ansichten (gerendertes Arch)")
    archen = {}
    for typ in ("list", "form", "search"):
        archen[typ] = db.kw("res.partner.category", "get_views", [[[False, typ]]])["views"][typ]["arch"]

    liste = " ".join(archen["list"].split())
    pruefe('name="display_name"' in liste, "Liste: Spalte Anzeigename (display_name)")
    pruefe('name="id"' in liste, "Liste: Spalte ID")
    pruefe('name="name"' in liste and 'string="Tag Anzeigename"' in liste, "Liste: Spalte Tag Anzeigename (name)")
    pruefe('name="parent_id"' in liste and 'optional="hide"' in liste, "Liste: Kategorie (parent_id) optional/ausgeblendet")
    pruefe('name="color"' in liste and liste.count('optional="hide"') >= 2, "Liste: Farbe (color) optional/ausgeblendet")

    form = " ".join(archen["form"].split())
    pruefe('name="name"' in form and 'string="Tag Anzeigename"' in form, "Formular: Tag Anzeigename")
    pruefe('name="display_name"' in form and 'readonly="1"' in form, "Formular: Anzeigename read-only (voller Pfad)")
    pruefe('name="parent_id"' in form and 'string="Oberkategorie"' in form, "Formular: Oberkategorie")
    pruefe('name="child_ids"' in form, "Formular: untergeordnete Kategorien (child_ids)")
    pruefe('name="active"' in form, "Formular: Aktiv")
    pruefe('name="color"' in form, "Formular: Farbe")

    suche = " ".join(archen["search"].split())
    pruefe('name="parent_id"' in suche and 'operator="child_of"' in suche, "Suche: Hierarchiesuche parent_id (child_of)")
    for name, label in (("itk_hauptkategorien", "Hauptkategorien (oberste Ebene)"),
                        ("itk_unterkategorien", "Unterkategorien (mit Oberkategorie)"),
                        ("itk_verwendet", "Verwendete Tags"),
                        ("itk_unverwendet", "Unverwendete Tags"),
                        ("itk_mit_kindern", "Mit Unterkategorien"),
                        ("itk_ohne_kinder", "Ohne Unterkategorien")):
        pruefe('name="%s"' % name in suche, "Suche: Filter %s" % label)
    pruefe("group_parent_id" in suche, "Suche: Gruppieren nach Kategorie erhalten")
    pruefe('name="display_name"' in suche, "Suche: Anzeigename-Suche (child_of-Semantik) erhalten")

    print("\n3) Filter-Domains (muessen fehlerfrei zaehlen)")
    for dom, label in (([("parent_id", "=", False)], "Hauptkategorien"),
                       ([("parent_id", "!=", False)], "Unterkategorien"),
                       ([("partner_ids", "!=", False)], "Verwendete Tags"),
                       ([("partner_ids", "=", False)], "Unverwendete Tags"),
                       ([("child_ids", "!=", False)], "Mit Unterkategorien"),
                       ([("child_ids", "=", False)], "Ohne Unterkategorien")):
        try:
            n = db.kw("res.partner.category", "search_count", [dom])
            pruefe(True, "Domain %s" % label, "%d Tag(s)" % n)
        except Exception as e:
            pruefe(False, "Domain %s" % label, str(e)[:120])

    print("\n4) Hierarchiesuche (child_of-Semantik von display_name)")
    namen = [t["name"] for t in db.kw("res.partner.category", "search_read", [[], ["name"]], {"limit": 1})]
    if namen:
        treffer = db.kw("res.partner.category", "search_read",
                        [[["display_name", "like", namen[0]]], ["display_name"]])
        pruefe(bool(treffer), "Suche nach '%s' liefert Treffer" % namen[0], "%d Treffer" % len(treffer))

    if args.hierarchie_test:
        print("\n5) Hierarchie-Test (temporaeres Paar, wird wieder geloescht)")
        vorher = db.kw("res.partner.category", "search_count", [[]])
        eltern = kind = None
        try:
            eltern = db.kw("res.partner.category", "create",
                           [{"name": "ZZ-TEST ITK-Tag Eltern (temporaer)"}])
            kind = db.kw("res.partner.category", "create",
                         [{"name": "ZZ-TEST ITK-Tag Kind (temporaer)", "parent_id": eltern}])
            e = db.kw("res.partner.category", "read", [[eltern], ["display_name", "parent_path"]])[0]
            k = db.kw("res.partner.category", "read", [[kind], ["display_name", "parent_path"]])[0]
            pruefe(e["display_name"] == "ZZ-TEST ITK-Tag Eltern (temporaer)",
                   "display_name Wurzel = Tag-Name", e["display_name"])
            pruefe(k["display_name"] == "ZZ-TEST ITK-Tag Eltern (temporaer) / ZZ-TEST ITK-Tag Kind (temporaer)",
                   "display_name Kind = voller Pfad", k["display_name"])
            pruefe(k["parent_path"].startswith(str(eltern)) and k["parent_path"] != e["parent_path"],
                   "parent_path des Kindes enthaelt die Eltern-ID", k["parent_path"])
            kinder = db.kw("res.partner.category", "read", [[eltern], ["child_ids"]])[0]["child_ids"]
            pruefe(kind in kinder, "child_ids des Elternteils enthaelt das Kind")
            gefunden = db.kw("res.partner.category", "search", [[["parent_id", "child_of", eltern]]])
            pruefe(sorted(gefunden) == sorted([eltern, kind]), "Suche child_of findet Eltern + Kind")
            gefunden2 = db.kw("res.partner.category", "search",
                              [[["display_name", "like", "ZZ-TEST ITK-Tag Eltern"]]])
            pruefe(sorted(gefunden2) == sorted([eltern, kind]),
                   "Suche display_name like findet auch das Kind", "%d Treffer" % len(gefunden2))
            listen_ids = [r["id"] for r in db.kw("res.partner.category", "search_read",
                                                 [[["parent_id", "in", [eltern]]], ["id"]])]
            pruefe(kind in listen_ids, "Liste der Unterkategorien (parent_id in ...) enthaelt das Kind")
        except Exception as e:
            pruefe(False, "Hierarchie-Test", str(e)[:200])
        finally:
            for rid in (kind, eltern):
                if rid:
                    try:
                        db.kw("res.partner.category", "unlink", [[rid]])
                    except Exception as e:
                        print("   ACHTUNG: Testdatensatz %s nicht geloescht: %s" % (rid, str(e)[:120]))
            nachher = db.kw("res.partner.category", "search_count", [[]])
            pruefe(vorher == nachher, "Aufraeumen: Tag-Anzahl unveraendert", "%d -> %d" % (vorher, nachher))

    print("\nErgebnis: %d OK, %d FEHLER" % (len(ok), len(fehler)))
    if fehler:
        print("Fehlend/Fehlerhaft:")
        for f in fehler:
            print("   - %s" % f)
    return 0 if not fehler else 2


if __name__ == "__main__":
    sys.exit(main())
