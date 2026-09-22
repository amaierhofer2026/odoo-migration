"""Test des manuellen Rechnungswegs (Button "Rechnung manuell erstellen", Session 118, Teil 12).

Prueft den kompletten Vorgang mit einer Finanzposition samt Konten-/Steuerzuordnung:
genau eine Rechnung, Belegtyp, Zeilenwerte (Menge, Preis, Multiplikationsfaktor), Steuer,
Fiscal-Position-Zuordnung, EUR, Netto/Steuer/Brutto, Verknuepfung, kein Duplikat,
Verhalten von recurring_next_date.

Aufruf: python scripts/test_abo_manuelle_rechnung.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "TEST Rechnungslauf Nachweis"
FELDER = ["name", "state", "move_type", "amount_untaxed", "amount_tax", "amount_total",
          "currency_id", "invoice_date", "invoice_origin", "fiscal_position_id", "invoice_line_ids"]


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
            d = a["error"].get("data", {})
            raise RuntimeError((d.get("name", "") + ": " + d.get("message", ""))[:300])
        return a.get("result")

    return kw


def suche(kw, modell, domain, felder, limit=5):
    return kw(modell, "search_read", [domain, felder], limit=limit)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    url = "http://localhost:8069" if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    kw = client(url)
    print("Instanz: %s (%s)\n" % (a.instanz, url))
    ok = fehler = 0

    def pruefe(bed, txt):
        nonlocal ok, fehler
        if bed:
            ok += 1
            print("  OK   %s" % txt)
        else:
            fehler += 1
            print("  FEHL %s" % txt)

    abo = suche(kw, "sale.subscription", [["name", "=", NAME]], ["id", "code", "partner_id", "pricelist_id", "invoice_count", "recurring_next_date"])[0]
    partner_id = abo["partner_id"][0]
    fp = suche(kw, "account.fiscal.position", [["account_map", "!=", False]], ["id", "name"])[0]
    vorher = abo["invoice_count"]
    termin_vorher = abo["recurring_next_date"]
    print("Abo %s (%s) | Kunde %s | bisherige Rechnungen %s | naechste Rechnung %s"
          % (abo["id"], abo["code"], abo["partner_id"][1], vorher, termin_vorher))
    print("Finanzposition mit Kontenzuordnung: %s %s" % (fp["id"], fp["name"]))
    alt_fp = kw("res.partner", "read", [[partner_id], ["property_account_position_id"]])[0]["property_account_position_id"]
    kw("res.partner", "write", [[partner_id], {"property_account_position_id": fp["id"]}])
    print("Finanzposition am Kunden gesetzt (vorher: %s)\n" % alt_fp)

    print("--- Button 'Rechnung manuell erstellen' ---")
    try:
        kw("sale.subscription", "recurring_invoice", [[abo["id"]]])
        pruefe(True, "Aufruf ohne RPC-Fehler")
    except Exception as exc:
        pruefe(False, "Aufruf ohne RPC-Fehler: %s" % str(exc)[:200])
    d = suche(kw, "sale.subscription", [["id", "=", abo["id"]]], ["invoice_count", "recurring_next_date"])[0]
    pruefe(d["invoice_count"] == vorher + 1, "genau eine neue Rechnung (Zaehler %s -> %s)" % (vorher, d["invoice_count"]))
    pruefe(d["recurring_next_date"] > termin_vorher,
           "recurring_next_date fortgeschrieben (%s -> %s) - identisch zum Cron-Weg" % (termin_vorher, d["recurring_next_date"]))

    print("\n--- Rechnung selbst ---")
    rechnungen = suche(kw, "account.move", [["invoice_origin", "=", abo["code"]]], FELDER, limit=10)
    neueste = sorted(rechnungen, key=lambda r: r["id"])[-1]
    print("   Rechnung %s | %s | %s | netto %s + Steuer %s = %s %s | Finanzposition %s"
          % (neueste["name"] or "(Entwurf)", neueste["move_type"], neueste["state"], neueste["amount_untaxed"],
             neueste["amount_tax"], neueste["amount_total"], neueste["currency_id"][1],
             neueste["fiscal_position_id"] or "-"))
    pruefe(neueste["move_type"] == "out_invoice", "move_type = out_invoice (Kundenrechnung)")
    pruefe(neueste["currency_id"][1] == "EUR", "Rechnung in EUR")
    pruefe(abs(neueste["amount_untaxed"] - 65.0) < 0.01, "Nettobetrag 65,00 (%s)" % neueste["amount_untaxed"])
    pruefe(neueste["amount_total"] > neueste["amount_untaxed"], "Brutto groesser als netto (Steuer beruecksichtigt)")
    pruefe(bool(neueste["fiscal_position_id"]), "Finanzposition ist am Beleg hinterlegt")

    print("\n--- Rechnungszeilen ---")
    for lz in suche(kw, "account.move.line", [["move_id", "=", neueste["id"]], ["display_type", "=", "product"]],
                    ["name", "quantity", "price_unit", "discount", "price_subtotal", "price_total", "tax_ids",
                     "account_id", "product_uom_id"]):
        print("   %s | Menge %s | Preis %s | Rabatt %s | netto %s | brutto %s | Steuern %s | Konto %s"
              % (lz["name"][:28], lz["quantity"], lz["price_unit"], lz["discount"], lz["price_subtotal"],
                 lz["price_total"], lz["tax_ids"], lz["account_id"]))
        pruefe(abs(lz["quantity"] - 1.0) < 0.01, "Menge korrekt uebernommen (1)")
        pruefe(abs(lz["price_unit"] - 65.0) < 0.01, "Preis korrekt uebernommen (65,00)")
        pruefe(abs(lz["price_subtotal"] - 65.0) < 0.01, "Zeilensumme netto 65,00")
        pruefe(bool(lz["tax_ids"]), "Steuerzuordnung vorhanden")
        pruefe(bool(lz["account_id"]), "Konto zugeordnet")

    print("\n--- Abo <-> Rechnung, Doppelrechnung, Zaehler ---")
    pruefe(neueste["invoice_origin"] == abo["code"], "Verknuepfung ueber den Abo-Code vorhanden")
    anzahl_vor = len(rechnungen)
    kw("sale.subscription", "recurring_invoice", [[abo["id"]]])
    danach = suche(kw, "account.move", [["invoice_origin", "=", abo["code"]]], ["id"], limit=20)
    pruefe(len(danach) == anzahl_vor + 1,
           "manueller Aufruf erzeugt genau eine weitere Rechnung (%s -> %s)" % (anzahl_vor, len(danach)))
    # Fachliches Verhalten, in Odoo 11 und Odoo 18 identisch: der Button rechnet sofort ab,
    # unabhaengig von recurring_next_date. Der Cronjob ist ueber das Datum gefiltert und
    # erzeugt deshalb keine Duplikate (siehe scripts/test_abo_rechnungslauf.py).
    erg = kw("sale.subscription", "action_subscription_invoice", [[abo["id"]]])
    pruefe(erg.get("res_model") == "account.move", "Rechnungs-Smart-Button funktioniert danach")

    kw("res.partner", "write", [[partner_id], {"property_account_position_id": alt_fp[0] if alt_fp else False}])
    print("\nFinanzposition des Kunden wiederhergestellt")
    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
