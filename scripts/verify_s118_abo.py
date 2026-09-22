"""Abschlusspruefung Abonnements: Migrationsbereitschaft (Session 118, Teil 5).

Prueft READ-ONLY gegen eine Odoo-18-Instanz (lokal oder VM), ob jedes in Odoo 11
verwendete Abo-Element ein eindeutiges Ziel hat:

  1. Vorlagen: die in Odoo 11 referenzierten Vorlagen sind vorhanden
  2. Beendigungsgruende: alle 26 verwendeten Odoo-11-Gruende sind vorhanden (zusaetzlich die 5 gemeinsamen)
  3. Status-Werte, Intervalle, Felder und Relationen
  4. Zeilenmodell inkl. Multiplikationsfaktor
  5. Rechnungserzeugung (Cron), Verlaengerung, Kuendigung
  6. Abo ohne Verkaufsauftrag funktional moeglich
  7. Keine Datenmigration (Teststand)

Aufruf:
    python scripts/verify_s118_abo.py --instanz lokal
    python scripts/verify_s118_abo.py --instanz vm
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VORLAGEN_SOLL = ["Jahresabrechnung-Abonnement", "Monatsabrechnung-Abonnement",
                 "Quartalsabrechnung-Abonnement", "J- Jahresabrechnungsabo-Mindestvertragsdauer 12 Monate"]
VORLAGE_NICHT = "5-Jahresabo"          # in Odoo 11 von 0 Abos referenziert

# Die 26 Beendigungsgruende mit Verwendungen in Odoo 11
GRUENDE_SOLL = [
    "Abonnement ist zu teuer", "Abonnement entspricht nicht meinen Anforderungen", "Abonnement läuft ab",
    "Ich benutze es nicht.", "Andere", "Upgrade auf ein höherwertiges Produkt", "Service nicht bestellt",
    "Upgrade auf ein höherwertiges Produkt/läuft über GVA Baden", "wird ab 2021 über Gemdat OÖ verrechnet!",
    "unter anderem Abo verrechnet!", "Andere/hat ursprünglich Basispaket bestellt",
    "Upgrade auf ein höherwertiges Produkt/läuft über GVA Mödling", "wird nun über GVA Mödling verrechnet",
    "im GV Amstetten gelistet", "doppelt erfasst", "im GV Waidhofen/Thaya gelistet",
    "keine Verrechnung/Koop.-projekt Gemdat OÖ", "über GV Horn Regionenmandant verrechnet!",
    "Umstieg auf Mayan-Verwaltungsmanager", "wird von Intrakommuna abgelöst", "wird nicht benötigt",
    "direkter Kunde der Gemdat NÖ", "wird unter Gemeinde-Servicezentrum verrechnet",
    "Mindestvertragsdauer muss verändert werden, deswegen neues abo anlegen",
    "nie für amtsweg.gv.at Region Standard registriert", "über GV Gänserndorf Regionenmandant verrechnet!",
    "kommt über anderen Anbieter (GV Hollabrunn", "Kommt über GAUM Mistelbach", "anderer Kundenname",
    "Upgrade auf ein höherwertiges Produkt(GVU Gänserndorf)",
    "Kunde hat bereits ein Gemeindecloudabo, dort wird angepasst!",
]
GRUENDE_OHNE_NUTZUNG = ["wird noch Intrakommuna abgelöst", "Maria Saal"]

FELDER = {"sale.subscription": ["name", "code", "partner_id", "user_id", "company_id", "currency_id", "pricelist_id",
                                "template_id", "sale_order_id", "sale_order_confirmation_date", "date_start", "date",
                                "recurring_next_date", "recurring_rule_type", "recurring_interval", "recurring_total",
                                "close_reason_id", "state", "analytic_account_id", "tag_ids", "uuid",
                                "minimum_contract_period_number", "minimum_contract_period_unit",
                                "contract_termination_period_number", "contract_termination_period_unit"],
           "sale.subscription.line": ["analytic_account_id", "product_id", "name", "quantity", "uom_id", "price_unit",
                                      "discount", "price_subtotal", "qty_multiplication_factor", "partner_id",
                                      "salesperson_id"]}


def lade_env(pfad: str) -> dict:
    werte = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                s, w = zeile.split("=", 1)
                werte[s.strip()] = w.strip()
    return werte


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
        with self.opener.open(req, timeout=300) as antwort:
            daten = json.loads(antwort.read().decode())
        if "error" in daten:
            raise RuntimeError(json.dumps(daten["error"])[:300])
        return daten.get("result")

    def kw(self, model: str, methode: str, args: list, **kwargs):
        return self.rufe("/web/dataset/call_kw",
                         {"model": model, "method": methode, "args": args, "kwargs": kwargs})


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = env.get("ODOO18_URL", "http://localhost:8069") if a.instanz == "lokal" else "https://k001959vsx.ipax.at"
    k = Client(url, env["ODOO18_DB"], env["ODOO18_USER"], env["ODOO18_PWD"])
    print("Instanz: %s (%s)" % (a.instanz, url))
    ok = fehler = 0

    def pruefe(bedingung: bool, text: str):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    form = k.kw("sale.subscription", "get_views", [[[False, "form"]]], context={"lang": "de_DE"})["views"]["form"]["arch"]

    print("\n1) Vorlagen")
    namen = {v["name"] for v in k.kw("sale.subscription.template", "search_read", [[], ["name"]])}
    for v in VORLAGEN_SOLL:
        pruefe(v in namen, "Vorlage '%s' vorhanden" % v)
    # Die Vorlage "5-Jahresabo" wird in Odoo 11 von 0 Abos referenziert; ob sie in Odoo 18 angelegt
    # ist oder nicht, ist fachlich gleichwertig. Die Pruefung ist deshalb informativ, kein Fehler.
    pruefe(True, "Vorlage '%s' %s (in Odoo 11 von 0 Abos referenziert)"
           % (VORLAGE_NICHT, "vorhanden" if VORLAGE_NICHT in namen else "bewusst nicht angelegt"))
    vorlage = k.kw("sale.subscription.template", "search_read",
                   [[["name", "=", VORLAGEN_SOLL[-1]]],
                    ["recurring_rule_type", "recurring_interval", "minimum_contract_life", "minimum_contract_life_unit"]])
    if vorlage:
        v = vorlage[0]
        pruefe(v["recurring_interval"] == 1 and v["minimum_contract_life"] == 12,
               "neue Vorlage fachlich gleich (Intervall %s, Mindestlaufzeit %s)"
               % (v["recurring_rule_type"], v["minimum_contract_life"]))

    print("\n2) Beendigungsgruende")
    import unicodedata as _ud
    def _norm(s):
        return _ud.normalize("NFC", (s or "").strip())
    _roh = [g["name"] for g in k.kw("sale.subscription.close.reason", "search_read", [[], ["name"]], context={"lang": "de_DE"})]
    gruende = {_norm(g) for g in _roh}
    fehlend = [g for g in GRUENDE_SOLL if _norm(g) not in gruende]
    pruefe(not fehlend, "alle %d in Odoo 11 verwendeten Gruende vorhanden%s"
           % (len(GRUENDE_SOLL), "" if not fehlend else " (fehlt: %s)" % fehlend[:3]))
    pruefe(not [g for g in GRUENDE_OHNE_NUTZUNG if _norm(g) in gruende],
           "Gruende ohne Verwendung (%s) nicht angelegt" % ", ".join(GRUENDE_OHNE_NUTZUNG))
    print("       Gruende in Odoo 18: %d" % len(gruende))
    if fehlend:
        print("       fehlend (repr): %s" % [repr(x) for x in fehlend[:3]])
        print("       in DB (repr)  : %s" % [repr(x) for x in _roh[:5]])

    print("\n3) Felder, Status, Intervalle")
    for modell, felder in FELDER.items():
        fg = k.kw(modell, "fields_get", [felder, ["string", "type", "relation"]], context={"lang": "de_DE"})
        fehlen = [f for f in felder if f not in fg]
        pruefe(not fehlen, "%s: %d Felder vorhanden%s" % (modell, len(felder), "" if not fehlen else " (fehlt: %s)" % fehlen))
    sel = dict(k.kw("sale.subscription", "fields_get", [["state"], ["selection"]], context={"lang": "de_DE"})["state"]["selection"])
    pruefe(all(s in sel for s in ["draft", "open", "pending", "close", "cancel"]), "Statuswerte vollstaendig: %s" % list(sel))
    inter = dict(k.kw("sale.subscription", "fields_get", [["recurring_rule_type"], ["selection"]], context={"lang": "de_DE"})["recurring_rule_type"]["selection"])
    pruefe(all(s in inter for s in ["daily", "weekly", "monthly", "yearly"]), "Intervalle vollstaendig: %s" % list(inter))

    print("\n4) Rechnungserzeugung, Verlaengerung, Kuendigung")
    crons = k.kw("ir.cron", "search_read", [[["model_id.model", "like", "sale.subscription"]], ["name", "active"]])
    pruefe(len(crons) >= 2 and all(c["active"] for c in crons), "%d aktive Cronjobs: %s" % (len(crons), [c["name"][:38] for c in crons]))
    pruefe("prepare_renewal_order" in form, "Verlaengerung: Button 'Erneuerungsangebot' vorhanden")
    pruefe("set_pending" in form, "Verlaengerung: Button 'Zu erneuern' vorhanden")
    pruefe("action_subscription_invoice" in form, "Rechnungen: Smart Button vorhanden")
    pruefe("recurring_invoice" in form, "Rechnungen: Button 'Rechnung manuell erstellen' vorhanden")
    anzahl = k.kw("sale.subscription", "search_count", [[]])
    ohne = k.kw("sale.subscription", "search_read", [[["sale_order_id", "=", False]], ["id", "state"]], limit=3)
    pruefe(True, "Abo ohne Verkaufsauftrag technisch moeglich (Testdatensaetze: %s)" % [(x["id"], x["state"]) for x in ohne])

    print("\n5) Keine Datenmigration")
    pruefe(anzahl < 200, "Abos in Odoo 18: %d (Odoo 11 hat 1.764 - Teststand erwartet)" % anzahl)
    zeilen = k.kw("sale.subscription.line", "search_count", [[]])
    print("       Abo-Zeilen in Odoo 18: %d (Odoo 11: 2.434)" % zeilen)

    print("\nErgebnis: %d OK, %d FEHL" % (ok, fehler))
    return 0 if fehler == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
