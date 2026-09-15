#!/usr/bin/env python3
"""Strukturpruefung Kontaktformular (Detailansicht) in Odoo 18 - Session 94.

Prueft read-only gegen die Odoo-11-Produktivvorlage:
  * Kenndaten-Bereich mit GKZ, Multiplication Factor/Thsd, zu Handen, Organisationsbezeichnung,
    Verkaeufer, Kunde-/Lieferanten-Kennzeichnung, Status
  * Feldbeschriftungen (de_DE, gerendertes Formular): Titel, Strasse 2, Kontakte, Verkaeufer
  * Tabs inkl. Support Ticket, Gemeinde-Information, Interne Notizen, Abrechnung
  * Smart Buttons (Verkaufschancen, Verkauf, Einkaeufe, Lieferantenrechnungen, Aufgaben, Abonnements)
  * Kontrollzahlen (keine Datenaenderung)

Aufruf:
    python scripts/verify_s94_contact_form.py --instanz lokal
    python scripts/verify_s94_contact_form.py --instanz vm
Credentials aus C:\\Odoo-Test\\.env (nie ausgeben).
"""
import argparse
import http.cookiejar
import json
import os
import re
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
        self.url = url
        jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        self.db, self.pwd = env["ODOO18_DB"], env["ODOO18_PWD"]
        r = self._roh("/web/session/authenticate", {"db": self.db, "login": env["ODOO18_USER"], "password": self.pwd})
        self.uid = (r.get("result") or {}).get("uid")
        if not self.uid:
            sys.exit("FEHLER: Anmeldung fehlgeschlagen (%s)" % json.dumps(r)[:200])

    def _roh(self, pfad, prm):
        req = urllib.request.Request(self.url + pfad,
                                     data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": prm}).encode(),
                                     headers={"Content-Type": "application/json"})
        with self.op.open(req, timeout=180) as f:
            return json.loads(f.read().decode())

    def kw(self, model, method, args, kwargs=None):
        o = self._roh("/web/dataset/call_kw", {"model": model, "method": method, "args": args,
                                              "kwargs": kwargs or {}})
        if "error" in o:
            raise RuntimeError(json.dumps(o["error"])[:300])
        return o["result"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal", choices=sorted(URLS))
    args = ap.parse_args()
    db = DB(URLS[args.instanz], lade_env())
    ok, fehler = [], []

    def pruefe(bedingung, text, detail=""):
        (ok if bedingung else fehler).append(text)
        print("   [%s] %s%s" % ("OK" if bedingung else "FEHLT", text, (" - " + detail) if detail else ""))

    print("Instanz %s (uid %s)" % (args.instanz, db.uid))

    print("\n1) Modul")
    m = db.kw("ir.module.module", "search_read", [[["name", "=", "itk_base_setup"]]],
              {"fields": ["state", "installed_version"]})
    pruefe(bool(m) and m[0]["state"] == "installed", "itk_base_setup installiert",
           m[0]["installed_version"] if m else "-")

    print("\n2) Gerendertes Kontaktformular (de_DE)")
    arch = db.kw("res.partner", "get_views", [[[False, "form"]]], {"context": {"lang": "de_DE"}})["views"]["form"]["arch"]
    flach = re.sub(r"\s+", " ", re.sub(r"<!--.*?-->", "", arch, flags=re.S))

    def label_von(feld):
        treffer = [re.search(r'string="([^"]*)"', m.group(0)) for m in re.finditer(r"<field\b[^>]*name=\"%s\"[^>]*?/?>" % feld, flach)]
        return [t.group(1) for t in treffer if t]

    print("   Feldbeschriftungen (Odoo-11-Sollwert):")
    for feld, soll in (("title", "Titel"), ("street2", "Straße 2"), ("child_ids", "Kontakte"), ("user_id", "Verkäufer")):
        ist = label_von(feld)
        pruefe(bool(ist) and all(x == soll for x in ist), "%-12s Label = %r" % (feld, soll), "ist: %s" % (ist or "-"))
    pruefe(any(x == "UID" for x in label_von("vat")) or any(x == "USt" for x in label_von("vat")),
           "vat-Label gesetzt (UID/USt)", "ist: %s" % (label_von("vat") or "-"))

    print("\n3) Kenndaten-Bereich")
    pruefe('string="Kenndaten"' in flach, "Gruppe 'Kenndaten' vorhanden")
    for feld, soll in (("ref", "GKZ"), ("multi_factor", None), ("attention_of", "zu Handen"),
                       ("community_salutation", "Organisationsbezeichnung"), ("user_id", "Verkäufer"),
                       ("status_of_partner_id", "Status")):
        vorhanden = re.search(r"<field\b[^>]*name=\"%s\"" % feld, flach) is not None
        det = "Label: %s" % (label_von(feld) or "-")
        pruefe(vorhanden, "Feld %s im Formular%s" % (feld, (" (Soll %r)" % soll) if soll else ""), det)

    print("\n4) Tabs")
    for tab in ("Kontakte &amp; Adressen", "Interne Notizen", "Verkauf &amp; Einkauf", "Abrechnung",
                "Gemeinde-Information", "Support Ticket"):
        pruefe('string="%s"' % tab in flach, "Tab %s" % tab.replace("&amp;", "&"))

    print("\n5) Smart Buttons / Kennzahlen")
    for feld in ("opportunity_count", "sale_order_count", "purchase_order_count", "supplier_invoice_count",
                 "task_count", "subscription_count", "meeting_count", "total_invoiced", "helpdesk_ticket_count_string"):
        pruefe(re.search(r"<field\b[^>]*name=\"%s\"" % feld, flach) is not None, "Kennzahl %s vorhanden" % feld)

    print("\n6) Daten unveraendert (Kontrollzahlen)")
    for modell in ("res.partner", "res.partner.category", "sale.subscription", "sale.order"):
        print("      %-22s %d" % (modell, db.kw(modell, "search_count", [[]])))

    print("\nErgebnis: %d OK, %d FEHLER" % (len(ok), len(fehler)))
    for f in fehler:
        print("   - %s" % f)
    return 0 if not fehler else 2


if __name__ == "__main__":
    sys.exit(main())
