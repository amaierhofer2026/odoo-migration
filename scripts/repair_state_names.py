"""Bundesland-/State-Stammdaten pruefen und bereinigen (Session 116).

Befund (17.09.2026): In Odoo 18 sind 357 Namen von `res.country.state` als
Mojibake gespeichert - die UTF-8-Bytes wurden als CP437 gelesen, z. B.
'Bucure╚Öti' statt 'București' oder 'Õîùõ║¼Õ©é' statt '北京市'. Gleiche
Datensaetze lokal und auf der VM; Odoo 11 Prod ist nicht betroffen (dort sind
die Namen korrekt).

Quelle der richtigen Namen: die Odoo-Moduldatei
`base/data/res.country.state.csv` (im Container). Sie wird als Sollwert gelesen.

Es werden ausschliesslich die Namen betroffener `res.country.state`-Datensaetze
gesetzt - keine Personen-, Kontakt- oder Verkaufsdaten, keine Zuordnungen.

Aufruf:
    python scripts/repair_state_names.py --instanz lokal --pruefen
    python scripts/repair_state_names.py --instanz vm
"""
from __future__ import annotations

import argparse
import csv
import http.cookiejar
import io
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUELLDATEI = "/usr/lib/python3/dist-packages/odoo/addons/base/data/res.country.state.csv"

# Zeichen, die auf eine CP437/CP850-Fehlkodierung hindeuten (Box-Zeichen,
# Bruchzeichen, Waehrungszeichen in lateinischen Namen, Ersatzzeichen)
VERDAECHTIG = re.compile("["
                         "\u2500-\u257f"      # Box Drawing
                         "\u2580-\u259f"      # Block Elements
                         "\u2550-\u256c"
                         "\ufffd"             # Replacement Character
                         "\u00a2\u00a3\u00a5\u00a9\u00ac\u00bb\u00bc\u00bd"  # ¢£¥©¬»¼½
                         "\u00d7"             # ×
                         "]")
# Kombinationen, die typisch fuer doppelt kodierte Umlaute/Diakritika sind
MUSTER = ["\u00e2\u0080", "\u00c3\u201a", "\u00c2\u00a0", "\u00c3\u0192", "\u00e2\u20ac"]


def lade_env(pfad: str) -> dict:
    werte = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                s, w = zeile.split("=", 1)
                werte[s.strip()] = w.strip()
    return werte


def lade_quelle() -> dict:
    """Sollnamen aus der Odoo-Moduldatei im Container lesen."""
    roh = subprocess.run(["docker", "exec", "odoo18", "cat", QUELLDATEI],
                         capture_output=True, check=False).stdout.decode("utf-8", "replace")
    if not roh:
        return {}
    return {z["id"]: z["name"] for z in csv.DictReader(io.StringIO(roh)) if z.get("id")}


def verdaechtig(name: str) -> bool:
    """Umgebungsunabhaengige Pruefung auf beschädigte Namen."""
    if not name:
        return True
    if VERDAECHTIG.search(name):
        return True
    if any(m in name for m in MUSTER):
        return True
    if any(unicodedata.category(z) == "Cc" for z in name):
        return True
    return False


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
    quelle = lade_quelle()
    print("Instanz: %s (%s) | Sollnamen aus der Modulquelle: %d" % (a.instanz, url, len(quelle)))

    daten = k.kw("ir.model.data", "search_read",
                 [[["model", "=", "res.country.state"], ["module", "=", "base"]], ["name", "res_id"]],
                 context={"lang": "en_US"}, limit=4000)
    ids = [d["res_id"] for d in daten]
    namen = {s["id"]: s["name"] for s in
             k.kw("res.country.state", "read", [ids, ["name"]], context={"lang": "en_US"})} if ids else {}

    zu_fix = []
    kaputt_ohne_soll = []
    for d in daten:
        soll = quelle.get(d["name"])
        ist = namen.get(d["res_id"], "")
        if soll and ist != soll:
            zu_fix.append((d["res_id"], d["name"], ist, soll))
        elif not soll and verdaechtig(ist):
            kaputt_ohne_soll.append((d["res_id"], d["name"], ist))
    sonst_kaputt = [(i, n, v) for i, v in namen.items() if verdaechtig(v) and i not in {x[0] for x in zu_fix}]

    print("\nAbweichungen zur Modulquelle: %d" % len(zu_fix))
    for rid, xid, ist, soll in sorted(zu_fix, key=lambda x: x[1])[:12]:
        print("   %-16s ist=%-40r soll=%r" % (xid, ist, soll))
    print("beschaedigte Namen ohne Sollwert in der Quelle: %d" % len(kaputt_ohne_soll))
    print("weitere verdaechtige Namen: %d" % len(sonst_kaputt))

    if a.pruefen:
        print("\nPruefmodus: nichts geschrieben.")
        return 1 if (zu_fix or kaputt_ohne_soll or sonst_kaputt) else 0

    geaendert = 0
    for rid, xid, ist, soll in zu_fix:
        k.kw("res.country.state", "write", [[rid], {"name": soll}], context={"lang": "en_US"})
        k.kw("res.country.state", "write", [[rid], {"name": soll}], context={"lang": "de_DE"})
        geaendert += 1
    print("\n%d State-Namen korrigiert." % geaendert)

    # Kontrolle
    namen2 = {s["id"]: s["name"] for s in
              k.kw("res.country.state", "read", [ids, ["name"]], context={"lang": "en_US"})} if ids else {}
    rest = [(d["name"], namen2.get(d["res_id"])) for d in daten
            if quelle.get(d["name"]) and namen2.get(d["res_id"]) != quelle[d["name"]]]
    verd = [(i, n) for i, n in namen2.items() if verdaechtig(n)]
    print("Kontrolle: Abweichungen %d, verdaechtige Namen %d" % (len(rest), len(verd)))
    for i, n in verd[:5]:
        print("   noch verdaechtig: id=%s %r" % (i, n))
    return 0 if not rest and not verd else 1


if __name__ == "__main__":
    sys.exit(main())
