"""Gibt den zusammengefuehrten Odoo-18-Arch der Produktansichten roh aus (read-only).

Session 119, Teil 14. Zeigt, welche Views beitragen (inherit-Kette) und wie der
gerenderte Arch aussieht - wichtig fuer XPath-Anker, optional="show" und group_by-Format.

Aufruf: python scripts/dump_o18_ansichten.py --instanz lokal|vm --modell product.template --art list|search|form
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--modell", default="product.template")
    p.add_argument("--art", default="list")
    p.add_argument("--nur-marker", action="store_true", help="nur Feldliste/Marker statt Volltext")
    a = p.parse_args()

    env = {}
    for z in open(os.path.join(REPO, ".env"), encoding="utf-8"):
        if "=" in z and not z.strip().startswith("#"):
            k, v = z.split("=", 1)
            env[k.strip()] = v.strip()
    url = "http://localhost:8069" if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rpc(pfad, prm):
        r = urllib.request.Request(url + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": prm}).encode(),
                                   headers={"Content-Type": "application/json"})
        with op.open(r, timeout=300) as f:
            return json.loads(f.read().decode())

    rpc("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"], "password": env["ODOO18_PWD"]})

    def kw(m, me, args, **K):
        o = rpc("/web/dataset/call_kw", {"model": m, "method": me, "args": args, "kwargs": K})
        if "error" in o:
            raise RuntimeError(str(o["error"].get("data", {}).get("message"))[:300])
        return o["result"]

    erg = kw(a.modell, "get_views", [[[False, a.art]]], context={"lang": "de_DE"})
    arch = ""
    for _k, v in erg["views"].items():
        arch = v["arch"]
    print("Instanz=%s Art=%s Modell=%s" % (a.instanz, a.art, a.modell))
    if a.nur_marker:
        import re
        print("FELDER: %s" % re.findall(r'<field name="([^"]+)"', arch))
        print("OPTIONAL: %s" % re.findall(r'<field name="([^"]+)"[^>]*optional="([^"]+)"', arch))
        print("GROUPBY : %s" % re.findall(r"group_by[^\w]+(\w+)", arch))
        return 0
    print(arch)
    return 0


if __name__ == "__main__":
    sys.exit(main())
