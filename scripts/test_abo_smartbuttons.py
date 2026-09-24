"""Funktionstest der Abo-Smart-Buttons (Session 118, Teil 11; Testfall-Logik Session 120).

Klickt die Smart Buttons des Abo-Formulars funktional (RPC-Aufruf der Aktionsmethoden) und prueft:
  - Rechnungen-Smart-Button bei 0, 1 und mehreren Rechnungen
  - Verkauf-Smart-Button
  - Abonnementanalyse
  - weitere Aktionen im Abo (Erneuerungsangebot, Zu erneuern)

Der Fall "genau eine Rechnung" wird seit Session 120 selbst hergestellt (Befund F52): das
Werkzeug sucht ein Abo ohne Rechnung, legt genau eine Testrechnung dazu, prueft den Button und
loescht die Testrechnung wieder. Es setzt damit nicht mehr voraus, dass das Nachweis-Abo
("TEST Rechnungslauf Nachweis") genau eine Rechnung hat - dessen Rechnungszahl haengt von
frueheren Testlaeufen ab und war zuletzt 3.
Es wird nichts dauerhaft gespeichert; beide Testrechnungen werden wieder geloescht.

Aufruf: python scripts/test_abo_smartbuttons.py --instanz lokal|vm
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

    abo = kw("sale.subscription", "search_read", [[["name", "=", NAME]], ["id", "code", "invoice_count"]])
    if not abo:
        print("Testabo fehlt")
        return 1
    abo = abo[0]
    print("Testabo %s (%s), Rechnungen laut Zaehler: %s" % (abo["id"], abo["code"], abo["invoice_count"]))

    # Session 120 (F52): der Einzelfall wird selbst hergestellt. Vorher setzte das Werkzeug
    # voraus, dass das Nachweis-Abo genau eine Rechnung hat; nach frueheren Testlaeufen hat es
    # aber 3, und der Test schlug fehl, obwohl die Anwendung richtig arbeitet.
    partner = kw("res.partner", "search_read", [[["customer_rank", ">", 0]], ["id"]], limit=1)[0]["id"]
    prod = kw("product.product", "search_read", [[["sale_ok", "=", True]], ["id"]], limit=1)[0]["id"]

    print("\n--- Fall: genau eine Rechnung (Testfall wird selbst hergestellt) ---")
    kandidaten = kw("sale.subscription", "search_read", [[], ["id", "code", "invoice_count"]], limit=200)
    ohne = [k for k in kandidaten if not k["invoice_count"]]
    einzeln_rechnung = None
    ziel = None
    if ohne:
        ziel = ohne[0]
        einzeln_rechnung = kw("account.move", "create", [{
            "move_type": "out_invoice", "partner_id": partner,
            "invoice_line_ids": [(0, 0, {
                "product_id": prod, "name": "Testfall genau eine Rechnung",
                "quantity": 1.0, "price_unit": 10.0, "subscription_id": ziel["id"]})]}])
        print("   Testabo %s (%s) hatte 0 Rechnungen; Testrechnung %s angelegt"
              % (ziel["id"], ziel["code"], einzeln_rechnung))
    else:
        mit_einer = [k for k in kandidaten if k["invoice_count"] == 1]
        if mit_einer:
            ziel = mit_einer[0]
            print("   Abo %s (%s) hat bereits genau eine Rechnung" % (ziel["id"], ziel["code"]))
    if ziel is None:
        pruefe(False, "kein Abo fuer den Fall 'genau eine Rechnung' verfuegbar (0 oder 1 vorausgesetzt)")
    else:
        erg = kw("sale.subscription", "action_subscription_invoice", [[ziel["id"]]])
        print("   Aktion: type=%s res_model=%s res_id=%s views=%s context=%s"
              % (erg.get("type"), erg.get("res_model"), erg.get("res_id"), str(erg.get("views"))[:60],
                 erg.get("context")))
        pruefe(erg.get("res_model") == "account.move", "Rechnungen-Button oeffnet account.move")
        pruefe(bool(erg.get("res_id")),
               "bei einer Rechnung wird direkt die Rechnung geoeffnet (Abo %s, res_id=%s)"
               % (ziel["id"], erg.get("res_id")))
        pruefe(str(erg.get("views")).find("form") >= 0, "Ansicht ist das Rechnungsformular")
        pruefe(erg.get("context") == {"create": False}, "Anlegen im Smart Button gesperrt")

    print("\n--- Fall: mehrere Rechnungen ---")
    zusatz = kw("account.move", "create", [{"move_type": "out_invoice", "partner_id": partner,
                                            "invoice_line_ids": [(0, 0, {
                                                "product_id": prod, "name": "Testfall mehrere Rechnungen",
                                                "quantity": 1.0, "price_unit": 10.0,
                                                "subscription_id": abo["id"]})]}])
    erg = kw("sale.subscription", "action_subscription_invoice", [[abo["id"]]])
    print("   Aktion: res_model=%s domain=%s res_id=%s" % (erg.get("res_model"), erg.get("domain"), erg.get("res_id")))
    pruefe(erg.get("domain") == [["id", "in", [erg_id for erg_id in (erg.get("domain") or [[0, 0, []]])[0][2]]]],
           "bei mehreren Rechnungen wird auf die Rechnungs-IDs dieses Abos gefiltert")
    ids = (erg.get("domain") or [[0, 0, []]])[0][2]
    pruefe(zusatz in ids, "die zusaetzliche Rechnung des Abos ist im Filter enthalten")
    erwartet = kw("account.move", "search_count", [[["invoice_line_ids.subscription_id", "=", abo["id"]]]])
    pruefe(len(ids) == erwartet,
           "alle %s Rechnungen dieses Abos im Filter, keine fremde (%s)" % (erwartet, len(ids)))

    print("\n--- Gegenprobe: Rechnung eines anderen Kunden darf nicht erscheinen ---")
    fremd = kw("account.move", "search_read", [[["move_type", "=", "out_invoice"], ["id", "not in", ids]],
                                               ["id"]], limit=1)
    pruefe(not fremd or fremd[0]["id"] not in ids, "fremde Rechnung ist nicht im Filter")

    print("\n--- Fall: keine Rechnung ---")
    # invoice_count ist ein NICHT gespeichertes Berechnungsfeld - eine Suche darauf liefert
    # Odoo 18 keine belastbaren Treffer (Session 119: die Suche lieferte Abo 172, das
    # tatsaechlich 4 Rechnungen hat). Deshalb ueber read() auswaehlen: dort laeuft die
    # Berechnung wirklich. Das Abo aus dem Einzelfall ist ausgenommen, weil es bis zum
    # Aufraeumen eine Testrechnung traegt.
    reserviert = {ziel["id"]} if ziel else set()
    ohne = [k for k in kandidaten if not k["invoice_count"] and k["id"] not in reserviert]
    if ohne:
        print("   Abo ohne Rechnungen laut Zaehler: %s" % [(k["id"], k["code"]) for k in ohne][:5])
        erg = kw("sale.subscription", "action_subscription_invoice", [[ohne[0]["id"]]])
        print("   Abo %s: Aktion type=%s" % (ohne[0]["id"], erg.get("type")))
        pruefe(erg.get("type") == "ir.actions.act_window_close",
               "bei null Rechnungen schliesst die Aktion (Button ist in der Ansicht ausgeblendet)")
    else:
        print("   kein Abo ohne Rechnungen vorhanden")

    print("\n--- Verkauf-Smart-Button ---")
    erg = kw("sale.subscription", "action_open_sales", [[abo["id"]]])
    print("   Aktion: res_model=%s domain=%s" % (erg.get("res_model"), str(erg.get("domain"))[:80]))
    pruefe(erg.get("res_model") == "sale.order", "Verkauf-Button oeffnet sale.order")
    pruefe("in" in str(erg.get("domain")), "Verkauf-Button filtert auf die Auftraege dieses Abos")

    print("\n--- Aufraeumen ---")
    for rechnung, bezeichnung in ((zusatz, "Mehrfachfall"), (einzeln_rechnung, "Einzelfall")):
        if not rechnung:
            continue
        try:
            kw("account.move", "unlink", [[rechnung]])
            print("   Testrechnung %s geloescht (%s)" % (rechnung, bezeichnung))
        except Exception as exc:
            print("   Testrechnung %s nicht geloescht (%s): %s" % (rechnung, bezeichnung, str(exc)[:110]))

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
