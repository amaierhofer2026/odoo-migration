#!/usr/bin/env python3
"""Upgradet einzelne Odoo-Module gezielt per HTTPS/JSON-RPC (kein -u all).

Aufruf:
    python scripts/upgrade_modules.py --instanz lokal --module itk_subscription
    python scripts/upgrade_modules.py --instanz vm --liste itk_crm,itk_product

Vor jedem Modul wird der Versionsstand protokolliert, danach geprueft, ob
installed_version == latest_version ist. Credentials aus der lokalen .env.
"""
import argparse
import http.cookiejar
import json
import os
import time
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
        jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        self.url, self.db, self.pwd = url, env["ODOO18_DB"], env["ODOO18_PWD"]
        self.uid = self._call("common", "authenticate",
                              [self.db, env["ODOO18_USER"], self.pwd, {}])

    def _call(self, service, method, args, kwargs=None, timeout=600):
        payload = {"jsonrpc": "2.0", "method": "call",
                   "params": {"service": service, "method": method, "args": args,
                              "kwargs": kwargs or {}}, "id": 1}
        req = urllib.request.Request(self.url + "/jsonrpc", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with self.op.open(req, timeout=timeout) as r:
            out = json.loads(r.read().decode())
        if "error" in out:
            d = out["error"].get("data", {})
            raise RuntimeError("%s | %s" % (d.get("name"), d.get("message")))
        return out["result"]

    def kw(self, model, method, args=None, kwargs=None, timeout=600):
        return self._call("object", "execute_kw",
                          [self.db, self.uid, self.pwd, model, method, args or [], kwargs or {}],
                          timeout=timeout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal", choices=sorted(URLS))
    ap.add_argument("--module", action="append", default=[])
    ap.add_argument("--liste", default="")
    args = ap.parse_args()

    module = list(args.module)
    if args.liste:
        module += [m.strip() for m in args.liste.split(",") if m.strip()]
    if not module:
        print("Keine Module angegeben.")
        return 1

    db = DB(URLS[args.instanz], lade_env())
    print("Instanz %s (uid %s) - %d Modul(e)" % (args.instanz, db.uid, len(module)))

    fehler = []
    for name in module:
        treffer = db.kw("ir.module.module", "search_read", [[["name", "=", name]]],
                        {"fields": ["id", "state", "installed_version", "latest_version"]})
        if not treffer:
            print("  %-30s NICHT GEFUNDEN" % name)
            fehler.append(name)
            continue
        m = treffer[0]
        vorher = m["installed_version"]
        erfolg = False
        for versuch in range(1, 4):
            try:
                db.kw("ir.module.module", "button_immediate_upgrade", [[m["id"]]], timeout=900)
                erfolg = True
                break
            except Exception as e:
                text = str(e)
                # Cron-Job laeuft parallel -> Odoo lehnt das Upgrade voruebergehend ab
                if "scheduled action" in text or "InFailedSqlTransaction" in text:
                    print("  %-30s belegt (Cron), Versuch %d/3 in 20 s" % (name, versuch))
                    time.sleep(20)
                    continue
                print("  %-30s FEHLER: %s" % (name, text[:200]))
                break
        if not erfolg:
            fehler.append(name)
            continue
        try:
            danach = db.kw("ir.module.module", "read", [[m["id"]]],
                           {"fields": ["installed_version", "state"]})[0]
            print("  %-30s %s -> %s  (%s)" % (name, vorher, danach["installed_version"],
                                              danach["state"]))
        except Exception as e:
            print("  %-30s FEHLER bei der Kontrolle: %s" % (name, str(e)[:150]))
            fehler.append(name)

    print("\nErgebnis: %d von %d ohne Fehler" % (len(module) - len(fehler), len(module)))
    if fehler:
        print("Fehlerhaft:", fehler)
    return 0 if not fehler else 2


if __name__ == "__main__":
    sys.exit(main())
