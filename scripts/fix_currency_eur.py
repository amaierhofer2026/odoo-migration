"""Waehrungen und Preislisten auf EUR stellen (Session 118, Abschluss).

Auftrag von Anna (18.09.2026): fachlich wird ausschliesslich EUR verwendet. USD darf in Odoo 18
nicht mehr verwendet werden. Es werden deshalb:
  - die inaktive USD-Preisliste ermittelt und deaktiviert,
  - alle Partner, Verkaufsauftraege und Abonnements auf die aktive EUR-Preisliste umgestellt,
  - die Firmenwaehrung und die Waehrungen geprueft.

Es werden ausschliesslich Preislisten-/Waehrungsverknuepfungen gesetzt - keine Preise, keine
Betraege und keine Abodaten werden veraendert.

Aufruf:
    python scripts/fix_currency_eur.py --instanz lokal --pruefen
    python scripts/fix_currency_eur.py --instanz lokal
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EUR_PREISLISTE = "Preisliste 2026 + Valorisierung"


def lade_env(pfad: str) -> dict:
    werte = {}
    for zeile in open(pfad, encoding="utf-8"):
        if "=" in zeile and not zeile.strip().startswith("#"):
            s, w = zeile.split("=", 1)
            werte[s.strip()] = w.strip()
    return werte


class Client:
    def __init__(self, url, db, user, pwd):
        self.url = url.rstrip("/")
        jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        self.rufe("/web/session/authenticate", {"db": db, "login": user, "password": pwd})

    def rufe(self, pfad, params):
        req = urllib.request.Request(self.url + pfad,
                                     data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}).encode(),
                                     headers={"Content-Type": "application/json"})
        with self.opener.open(req, timeout=300) as f:
            daten = json.loads(f.read().decode())
        if "error" in daten:
            raise RuntimeError(json.dumps(daten["error"])[:300])
        return daten.get("result")

    def kw(self, model, methode, args, **kwargs):
        return self.rufe("/web/dataset/call_kw", {"model": model, "method": methode, "args": args, "kwargs": kwargs})


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--pruefen", action="store_true")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    k = Client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    print("Instanz: %s (%s)" % (a.instanz, url))
    aenderungen = 0

    firma = k.kw("res.company", "search_read", [[], ["name", "currency_id"]], context={"lang": "de_DE"})
    print("  Firma: %s, Waehrung %s" % (firma[0]["name"], firma[0]["currency_id"][1]))
    if firma[0]["currency_id"][1] != "EUR":
        print("  FEHL Firmenwaehrung ist nicht EUR")

    print("\n  Alle Preislisten (auch inaktive):")
    pls = k.kw("product.pricelist", "search_read", [[], ["id", "name", "currency_id", "active"]],
               context={"lang": "de_DE", "active_test": False})
    eur = None
    for pl in pls:
        waehrung = pl["currency_id"][1] if pl["currency_id"] else "-"
        print("    id=%-4s %-44s %-6s aktiv=%s" % (pl["id"], pl["name"][:44], waehrung, pl["active"]))
        if pl["name"] == EUR_PREISLISTE and waehrung == "EUR":
            eur = pl
    if not eur:
        print("  FEHL EUR-Preisliste '%s' nicht gefunden" % EUR_PREISLISTE)
        return 1
    if not eur["active"]:
        if a.pruefen:
            print("  FEHL EUR-Preisliste ist inaktiv")
        else:
            k.kw("product.pricelist", "write", [[eur["id"]], {"active": True}])
            aenderungen += 1
            print("  OK   EUR-Preisliste aktiviert (id %s)" % eur["id"])

    usd = [pl for pl in pls if pl["currency_id"] and pl["currency_id"][1] == "USD"]
    for pl in usd:
        if pl["active"]:
            if a.pruefen:
                print("  FEHL USD-Preisliste '%s' ist aktiv" % pl["name"])
            else:
                k.kw("product.pricelist", "write", [[pl["id"]], {"active": False}])
                aenderungen += 1
                print("  OK   USD-Preisliste '%s' deaktiviert (id %s)" % (pl["name"], pl["id"]))

    print("\n  Umstellen auf die EUR-Preisliste (id %s):" % eur["id"])
    for modell, feld, zusatz in [("res.partner", "property_product_pricelist", [["property_product_pricelist", "!=", eur["id"]]]),
                                 ("sale.order", "pricelist_id", [["pricelist_id", "!=", eur["id"]]]),
                                 ("sale.subscription", "pricelist_id", [["pricelist_id", "!=", eur["id"]]]),
                                 ("purchase.order", "pricelist_id", [["pricelist_id", "!=", eur["id"]]])]:
        try:
            ids = k.kw(modell, "search", [zusatz])
        except Exception as exc:
            print("    %-16s nicht pruefbar (%s)" % (modell, str(exc)[:40]))
            continue
        if not ids:
            print("    %-16s bereits vollstaendig auf EUR" % modell)
            continue
        if a.pruefen:
            print("  FEHL %-16s %d Datensaetze zeigen nicht auf die EUR-Preisliste" % (modell, len(ids)))
        else:
            # bestaetigte Belege lassen keine Preislisten-/Waehrungsaenderung zu (Odoo-Constraint)
            offen, gesperrt = [], []
            for rid in ids:
                try:
                    k.kw(modell, "write", [[rid], {feld: eur["id"]}])
                    offen.append(rid)
                except Exception:
                    gesperrt.append(rid)
            if offen:
                aenderungen += len(offen)
                print("  OK   %-16s %d Datensaetze auf EUR umgestellt" % (modell, len(offen)))
            if gesperrt:
                print("  --   %-16s %d Datensaetze gesperrt (bestaetigt/abgeschlossen): %s"
                      % (modell, len(gesperrt), gesperrt[:6]))

    # Kontrolle
    print("\n  Kontrolle nach der Umstellung:")
    for modell, dom in [("sale.order", [["currency_id.name", "=", "USD"]]),
                        ("sale.subscription", [["currency_id.name", "=", "USD"]]),
                        ("account.move", [["currency_id.name", "=", "USD"]])]:
        try:
            print("    %-18s USD-Datensaetze: %s" % (modell, k.kw(modell, "search_count", [dom])))
        except Exception as exc:
            print("    %-18s %s" % (modell, str(exc)[:50]))
    print("\nErgebnis: %d Aenderungen" % aenderungen)
    return 0


if __name__ == "__main__":
    sys.exit(main())
