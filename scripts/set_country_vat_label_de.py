#!/usr/bin/env python3
"""vat_label des Firmenlandes auf 'UID' setzen (Odoo-11-Wortlaut) - Session 96.

Warum: Odoo 18 setzt das Label des Feldes `vat` zur Render-Zeit aus
`<company>.country_id.vat_label` (Python-Hook FormatVATLabelMixin._get_view,
base/models/res_partner.py). Fuer Oesterreich liefert Odoo 18 den Wert "USt"
(Base-Datensatz res.country base.at) -> eine View kann das NICHT uebersteuern.
Das produktive Odoo 11 zeigt "UID"; dieser Wert ist in Odoo 11 ein
Uebersetzungs-Slot. Damit Odoo 18 denselben Wortlaut zeigt, wird der
Basisdatensatz des Firmenlandes angepasst (Quelle + de_DE).

Das ist eine DATENAENDERUNG in den Basisdaten (res.country), kein Code-Fix:
- idempotent (schreibt nur, wenn der Wert abweicht)
- betrifft genau einen Datensatz (das Land der Firma)
- Rueckgaengig: --revert  (setzt den von Odoo gelieferten Wert "USt" zurueck)

Aufruf:
    python scripts/set_country_vat_label_de.py --instanz lokal|vm [--revert] [--label UID]
"""
import argparse, json, sys, urllib.request, http.cookiejar

URLS = {"lokal": "http://localhost:8069", "vm": "https://k001959vsx.ipax.at"}


def lade_env():
    import os
    pfad = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    env = {}
    for zeile in open(pfad, encoding="utf-8"):
        if "=" in zeile and not zeile.strip().startswith("#"):
            k, v = zeile.split("=", 1)
            env[k.strip()] = v.strip()
    return env


class RPC:
    def __init__(self, url, db, user, pwd):
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.url, self.db = url, db
        self.call("/web/session/authenticate", {"db": db, "login": user, "password": pwd})

    def call(self, pfad, params):
        r = urllib.request.Request(self.url + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode(),
                                   headers={"Content-Type": "application/json"})
        with self.op.open(r, timeout=180) as f:
            return json.loads(f.read().decode())

    def kw(self, model, method, args, context=None, **extra):
        k = {"context": context} if context else {}
        k.update(extra)
        o = self.call("/web/dataset/call_kw", {"model": model, "method": method, "args": args, "kwargs": k})
        if "error" in o:
            raise RuntimeError(json.dumps(o["error"])[:400])
        return o["result"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal", choices=sorted(URLS))
    ap.add_argument("--label", default="UID")
    ap.add_argument("--revert", action="store_true", help="Odoo-Standardwert 'USt' wiederherstellen")
    a = ap.parse_args()
    env = lade_env()
    rpc = RPC(URLS[a.instanz], env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    ziel = "USt" if a.revert else a.label

    firma = rpc.kw("res.company", "search_read", [[], ["name", "country_id"]], limit=1)[0]
    land_id = firma["country_id"][0]
    vorher = rpc.kw("res.country", "read", [[land_id], ["name", "code", "vat_label"]])[0]
    print("Instanz %-6s Firma %-22s Land %s (%s)" % (a.instanz, firma["name"][:22], vorher["code"], vorher["name"]))
    print("   vat_label vorher (de_DE): %r" % vorher["vat_label"])

    if vorher["vat_label"] == ziel:
        print("   keine Aenderung noetig (idempotent).")
    else:
        rpc.kw("res.country", "write", [[land_id], {"vat_label": ziel}], {"lang": "de_DE"})
        rpc.kw("res.country", "write", [[land_id], {"vat_label": ziel}])
        nachher = rpc.kw("res.country", "read", [[land_id], ["vat_label"]], {"lang": "de_DE"})[0]
        print("   vat_label nachher        : %r  ->  %s" % (nachher["vat_label"], "OK" if nachher["vat_label"] == ziel else "FEHLER"))
        if nachher["vat_label"] != ziel:
            return 1

    # Gegenprobe: gerenderte Form zeigt das neue Label (der Hook setzt es aus dem Land)
    arch = rpc.kw("res.partner", "get_views", [[[False, "form"]]], {"de_DE": 1})["views"]["form"]["arch"]
    import re
    treffer = re.search(r'<field name="vat"[^>]*string="([^"]*)"', arch)
    print("   Label im gerenderten Formular: %r" % (treffer.group(1) if treffer else "nicht gefunden"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
