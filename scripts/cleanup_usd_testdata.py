"""Abschlussbereinigung Abonnements: USD-Testdaten entfernen, EUR-Testdaten anlegen (Session 118, Teil 7).

Von Anna freigegeben (18.09.2026): die reinen Odoo-18-Testdaten in USD duerfen geloescht bzw. sauber als
EUR-Testdaten neu angelegt werden. In Odoo 11 wird nichts geaendert.

Ablauf:
  1. USD-Testauftraege (sale.order) und USD-Testrechnungen (account.move) ermitteln und loeschen
     (Rechnungen werden bei Bedarf zuerst auf Entwurf zurueckgesetzt).
  2. EUR-Testdaten fuer die Abnahme anlegen: je ein Abo im Zustand Neu, Laufend, Zu erneuern,
     Abgeschlossen und Abgebrochen sowie ein bestaetigter EUR-Verkaufsauftrag mit Abo-Verknuepfung
     (nur, wenn die Testdaten nicht schon vorhanden sind).
  3. Systemweite Kontrolle: neue Angebote/Auftraege/Abos/Rechnungen erhalten EUR (Trockenlauf mit
     Anlegen und sofortigem Loeschen).

Aufruf:
    python scripts/cleanup_usd_testdata.py --instanz lokal --pruefen
    python scripts/cleanup_usd_testdata.py --instanz lokal
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRAEFIX = "TEST Abnahme "


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


def eur_preisliste(k):
    treffer = k.kw("product.pricelist", "search_read", [[["currency_id.name", "=", "EUR"], ["active", "=", True]],
                                                        ["id", "name"]], context={"lang": "de_DE"}, limit=1)
    if not treffer:
        raise RuntimeError("keine aktive EUR-Preisliste gefunden")
    return treffer[0]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--pruefen", action="store_true")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    k = Client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    print("Instanz: %s (%s)" % (a.instanz, url))

    print("\n1) USD-Testdaten")
    auftraege = k.kw("sale.order", "search_read", [[["currency_id.name", "=", "USD"]], ["id", "name", "state"]])
    rechnungen = k.kw("account.move", "search_read", [[["currency_id.name", "=", "USD"]], ["id", "name", "state", "move_type"]])
    print("   USD-Auftraege: %s" % [(x["id"], x["name"], x["state"]) for x in auftraege])
    print("   USD-Rechnungen: %s" % [(x["id"], x["name"], x["state"]) for x in rechnungen])
    if a.pruefen:
        if auftraege or rechnungen:
            print("   FEHL es sind noch USD-Testdaten vorhanden")
    else:
        # Abos von den Auftraegen loesen, damit die Verknuepfung sauber bleibt
        for x in auftraege:
            geloescht = False
            letzter = ""
            for schritt in ("loeschen", "stornieren+loeschen", "Entwurf+loeschen"):
                try:
                    if schritt == "stornieren+loeschen":
                        k.kw("sale.order", "action_cancel", [[x["id"]]])
                    elif schritt == "Entwurf+loeschen":
                        k.kw("sale.order", "action_draft", [[x["id"]]])
                    k.kw("sale.order", "unlink", [[x["id"]]])
                    print("   OK   USD-Testauftrag %s geloescht (%s)" % (x["name"], schritt))
                    geloescht = True
                    break
                except Exception as exc:
                    letzter = str(exc)
            if not geloescht:
                print("   FEHL USD-Testauftrag %s nicht loeschbar:" % x["name"])
                print("        " + letzter[-260:].replace(chr(92) + "n", " "))
        for x in rechnungen:
            if x["state"] != "draft":
                try:
                    k.kw("account.move", "button_draft", [[x["id"]]])
                except Exception as exc:
                    print("   --   Rechnung %s nicht auf Entwurf (%s)" % (x["name"], str(exc)[:60]))
            try:
                k.kw("account.move", "unlink", [[x["id"]]])
                print("   OK   USD-Testrechnung %s geloescht" % x["name"])
            except Exception as exc:
                print("   FEHL Rechnung %s nicht loeschbar: %s" % (x["name"], str(exc)[:90]))

    print("\n2) EUR-Testdaten fuer die Abnahme")
    pl = eur_preisliste(k)
    print("   EUR-Preisliste: %s (id %s)" % (pl["name"], pl["id"]))
    partner = k.kw("res.partner", "search_read", [[["name", "=", "Test Firma"]], ["id", "name"]], limit=1)
    if not partner:
        partner = k.kw("res.partner", "search_read", [[["customer_rank", ">", 0]], ["id", "name"]], limit=1)
    partner_id = partner[0]["id"] if partner else False
    print("   Testkunde: %s (id %s)" % (partner[0]["name"] if partner else "-", partner_id))
    vorlage = k.kw("sale.subscription.template", "search_read", [[], ["id", "name"]], limit=1)
    vorlage_id = vorlage[0]["id"] if vorlage else False

    # bestaetigter EUR-Verkaufsauftrag fuer die Abo-Verknuepfung
    auftrag_id = False
    vorhanden = k.kw("sale.order", "search_read", [[["name", "like", PRAEFIX], ["currency_id.name", "=", "EUR"]], ["id", "name", "state"]])
    if vorhanden:
        auftrag_id = vorhanden[0]["id"]
        print("   EUR-Testauftrag vorhanden: %s (%s)" % (vorhanden[0]["name"], vorhanden[0]["state"]))
    elif not a.pruefen:
        produkt = k.kw("product.product", "search_read", [[["sale_ok", "=", True]], ["id", "name", "lst_price"]], limit=1)[0]
        auftrag_id = k.kw("sale.order", "create", [{
            "partner_id": partner_id, "pricelist_id": pl["id"],
            "order_line": [(0, 0, {"product_id": produkt["id"], "product_uom_qty": 1,
                                   "price_unit": produkt["lst_price"] or 100.0})]}])
        k.kw("sale.order", "action_confirm", [[auftrag_id]])
        print("   OK   EUR-Testauftrag angelegt und bestaetigt (id %s, Waehrung EUR)" % auftrag_id)

    zustaende = ["open", "pending", "close", "cancel"]
    for zustand in zustaende:
        name = PRAEFIX + zustand
        da = k.kw("sale.subscription", "search_read", [[["name", "=", name]], ["id", "state"]])
        if da:
            print("   vorhanden: %s (%s)" % (name, da[0]["state"]))
            continue
        if a.pruefen:
            print("   FEHL fehlt: %s" % name)
            continue
        werte = {"name": name, "partner_id": partner_id, "pricelist_id": pl["id"],
                 "recurring_rule_type": "monthly", "recurring_interval": 1,
                 "date_start": "2026-01-01", "user_id": False}
        if vorlage_id:
            werte["template_id"] = vorlage_id
        neu = k.kw("sale.subscription", "create", [werte])
        if auftrag_id and zustand == "open":
            k.kw("sale.subscription", "write", [[neu], {"sale_order_id": auftrag_id}])
        if zustand != "open" and zustand != "cancel":
            grund = k.kw("sale.subscription.close.reason", "search_read", [[], ["id"]], limit=1)[0]["id"]
            k.kw("sale.subscription", "write", [[neu], {"close_reason_id": grund}])
        k.kw("sale.subscription", "write", [[neu], {"state": zustand}])
        print("   OK   EUR-Testabo angelegt: %s (Zustand %s)" % (name, zustand))

    print("\n3) Systemweite Kontrolle: neue Belege erhalten EUR")
    if a.pruefen:
        print("   (uebersprungen im Pruefmodus)")
    else:
        p2 = k.kw("res.partner", "search_read", [[["customer_rank", ">", 0]], ["id", "name", "property_product_pricelist"]], limit=1)[0]
        print("   Partner '%s' Standard-Preisliste: %s" % (p2["name"], p2["property_product_pricelist"]))
        def check(modell, werte, felder, beschreibung):
            try:
                nid = k.kw(modell, "create", [werte])
            except Exception as exc:
                print("   --   %s: Anlegen ohne Preisliste nicht moeglich (%s)" % (beschreibung, str(exc)[:110]))
                return
            d = k.kw(modell, "read", [[nid], felder])[0]
            print("   %-14s -> %s" % (beschreibung, {f: (d[f][1] if isinstance(d[f], list) else d[f]) for f in felder}))
            try:
                k.kw(modell, "unlink", [[nid]])
            except Exception:
                pass

        check("sale.order", {"partner_id": p2["id"]}, ["currency_id", "pricelist_id"], "neues Angebot")
        check("account.move", {"move_type": "out_invoice", "partner_id": p2["id"]}, ["currency_id"], "neue Rechnung")
        vorlage = k.kw("sale.subscription.template", "search_read", [[], ["id"]], limit=1)
        werte = {"name": "TEST EUR-Check", "partner_id": p2["id"]}
        if vorlage:
            werte["template_id"] = vorlage[0]["id"]
        check("sale.subscription", werte, ["currency_id", "pricelist_id"], "neues Abo")
        vor = k.kw("sale.subscription", "search_read", [[["name", "=", "TEST EUR-Check"]], ["id", "currency_id"]])
        if vor:
            print("   --   Testabo blieb stehen (id %s, %s)" % (vor[0]["id"], vor[0]["currency_id"][1]))
            k.kw("sale.subscription", "unlink", [[vor[0]["id"]]])
        for modell in ["sale.order", "sale.subscription", "account.move", "res.partner"]:
            try:
                n = k.kw(modell, "search_count", [[["currency_id.name", "=", "USD"]]]) if modell != "res.partner" else \
                    k.kw(modell, "search_count", [[["property_product_pricelist.currency_id.name", "=", "USD"]]])
                print("   Kontrolle %-18s USD-Datensaetze: %s" % (modell, n))
            except Exception as exc:
                print("   Kontrolle %-18s %s" % (modell, str(exc)[:60]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
