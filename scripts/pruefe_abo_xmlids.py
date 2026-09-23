"""Prueft alle XML-IDs/ref-Aufrufe in itk_subscription gegen die Odoo-18-Registry (Session 118, Teil 11).

Findet env.ref(...), ref="..." und ref in XML-Dateien, dazu der Aufruf von Aktionsnamen, und prueft
jede ID per RPC: existiert sie, welches Modell, welche Aktion.

Aufruf: python scripts/pruefe_abo_xmlids.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import glob
import http.cookiejar
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODUL = os.path.join(REPO, "addons", "itk_subscription")


def lade_env(pfad):
    w = {}
    for z in open(pfad, encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            w[k.strip()] = v.strip()
    return w


def client(url):
    env = lade_env(os.path.join(REPO, ".env"))
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(url + "/web/session/authenticate",
                                 data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
                                     "db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                     "password": env["ODOO18_PWD"]}}).encode(),
                                 headers={"Content-Type": "application/json"})
    with op.open(req, timeout=120) as f:
        f.read()

    def kw(modell, methode, args, **kwargs):
        r = urllib.request.Request(url + "/web/dataset/call_kw",
                                   data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {
                                       "model": modell, "method": methode, "args": args,
                                       "kwargs": kwargs}}).encode(),
                                   headers={"Content-Type": "application/json"})
        with op.open(r, timeout=600) as f:
            a = json.loads(f.read().decode())
        if "error" in a:
            meldung = a["error"].get("data", {}).get("message", a["error"].get("message", ""))
            raise RuntimeError(json.dumps(meldung)[:300])
        return a.get("result")

    return kw


def ist_xmlid(kennung):
    """XML-IDs sind 'modul.name'. Alles mit Pfad-/Ausdruckszeichen ist ein URL- oder
    Template-Rest und keine XML-ID (z.B. href="www.odoo.com" traf frueher das Muster ref=")."""
    if not kennung or " " in kennung:
        return False
    if any(zeichen in kennung for zeichen in "/\\$?&#{}%'+()"):
        return False
    if kennung.count(".") < 1 or kennung.startswith(("http", "www.")):
        return False
    return True


def sammle_ids():
    treffer = {}
    for pfad in glob.glob(os.path.join(MODUL, "**", "*.*"), recursive=True):
        if os.path.splitext(pfad)[1] not in (".py", ".xml", ".csv"):
            continue
        text = open(pfad, encoding="utf-8", errors="replace").read()
        for nr, zeile in enumerate(text.splitlines(), 1):
            # \bref(...) / \bref="..." - ohne Wortgrenze wuerde href="..." mitgelesen.
            for muster in (r"env\.ref\(\s*['\"]([^'\"]+)['\"]", r"\bref\(\s*['\"]([^'\"]+)['\"]",
                           r"\bref=\"([^\"]+)\"",
                           r"get_object_reference\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]",
                           r"selectvalue[^>]*\bref=\"([^\"]+)\""):
                for m in re.finditer(muster, zeile):
                    kennung = "%s.%s" % (m.group(1), m.group(2)) if len(m.groups()) == 2 else m.group(1)
                    if not ist_xmlid(kennung):
                        continue
                    treffer.setdefault(kennung, []).append(
                        "%s:%s" % (os.path.relpath(pfad, REPO).replace("\\", "/"), nr))
    return treffer


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    url = "http://localhost:8069" if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    kw = client(url)
    ids = sammle_ids()
    print("Instanz: %s | gefundene Referenzen: %d\n" % (a.instanz, len(ids)))
    fehlend = []
    print("%-58s %-10s %s" % ("XML-ID", "Status", "Verwendung"))
    for kennung in sorted(ids):
        treffer = kw("ir.model.data", "search_read",
                     [[["module", "=", kennung.split(".")[0]], ["name", "=", ".".join(kennung.split(".")[1:])]],
                      ["model", "res_id"]], limit=1)
        if treffer:
            status = "OK"
            zusatz = treffer[0]["model"]
        else:
            # Sonderfall: ID ohne Modulpraefix oder anderer Modulname
            treffer2 = kw("ir.model.data", "search_read", [[["name", "=", kennung.split(".")[-1]]], ["model", "module"]], limit=1)
            if treffer2:
                status = "OK*"
                zusatz = "%s (Modul %s)" % (treffer2[0]["model"], treffer2[0]["module"])
            else:
                status = "FEHLT"
                zusatz = "-"
                fehlend.append(kennung)
        print("%-58s %-10s %s %s" % (kennung, status, zusatz, sorted(set(ids[kennung]))[:2]))

    print("\n--- Aktionsaufloesung der Abo-Smart-Buttons ---")
    abo = kw("sale.subscription", "search_read", [[], ["id", "name", "code", "invoice_count", "sale_order_count"]], limit=1)
    if abo:
        abo = abo[0]
        print("   Testabo %s (%s): Rechnungen %s | Verkaeufe %s" % (abo["id"], abo["code"], abo["invoice_count"], abo["sale_order_count"]))
        for methode in ["action_subscription_invoice", "action_open_sales"]:
            try:
                ergebnis = kw("sale.subscription", methode, [[abo["id"]]])
                print("   %-30s -> name=%s res_model=%s domain=%s views=%s"
                      % (methode, ergebnis.get("name"), ergebnis.get("res_model"),
                         str(ergebnis.get("domain"))[:90], str(ergebnis.get("views"))[:70]))
            except Exception as exc:
                print("   %-30s -> FEHLER: %s" % (methode, str(exc)[:150]))
    else:
        print("   kein Abo gefunden")
    print("\nErgebnis: %d fehlende XML-IDs%s" % (len(fehlend), (": " + ", ".join(fehlend)) if fehlend else ""))
    return 1 if fehlend else 0


if __name__ == "__main__":
    sys.exit(main())
