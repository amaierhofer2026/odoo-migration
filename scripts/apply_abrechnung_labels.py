"""Sichtbare Odoo-11-Bezeichnungen im Bereich Abrechnung setzen (Regel Anna, 30.09.2026).

Setzt ausschliesslich Feldbeschreibungen (de_DE) auf den Odoo-11-Wortlaut, wenn das Feld in
Odoo 18 fachlich dieselbe Bedeutung hat. Interne Feldnamen bleiben unveraendert.

Warum ein Skript: Odoo 18 setzt die deutschen Feldbeschriftungen bei einem Modul-Upgrade auf die
Quelltexte zurueck. Das Skript laeuft deshalb nach jedem Upgrade - lokal und auf der VM.

Aufruf:
    python scripts/apply_abrechnung_labels.py --instanz lokal
    python scripts/apply_abrechnung_labels.py --instanz vm
    python scripts/apply_abrechnung_labels.py --instanz vm --pruefen    (nur lesen)

Nicht gesetzt (bewusst, siehe docs/o11-o18-abrechnung-labelmapping.md):
    - account.move.ref          Odoo-11-Feld reference war ungenutzt (0 Belege)
    - account.move.name         Odoo-11-Feld name hatte eine andere Bedeutung (Begruendung)
    - account.move.move_name    in name aufgegangen, kein eigenes Feld
    - account.move.payment_reference  in Odoo 11 nicht vorhanden
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (Modell, Feld) -> Odoo-11-Wortlaut
LABELS = {
    # Rechnungskopf
    ("account.move", "partner_id"): "Partner",
    ("account.move", "commercial_partner_id"): "Gewerbliche Einheit",
    ("account.move", "invoice_date"): "Rechnungsdatum",
    ("account.move", "invoice_date_due"): "Fälligkeit",
    ("account.move", "date"): "Buchungsdatum",
    ("account.move", "invoice_origin"): "Referenzbeleg",
    ("account.move", "narration"): "Weitere Informationen",
    ("account.move", "invoice_user_id"): "Verkäufer",
    ("account.move", "team_id"): "Vertriebskanal",
    ("account.move", "fiscal_position_id"): "Steuerzuordnung",
    ("account.move", "partner_bank_id"): "Bankkonto",
    ("account.move", "amount_total"): "Total",
    ("account.move", "amount_untaxed_signed"): "Nettobetrag in Unternehmenswährung",
    ("account.move", "amount_total_signed"): "Gesamtbetrag in Rechnungswährung",
    ("account.move", "amount_total_in_currency_signed"): "Gesamt (in eigener Währung)",
    ("account.move", "projectcategory_id"): "Project Category",
    ("account.move", "valorisierung_id"): "Valorisation Text",
    ("account.move", "is_move_sent"): "Gesendet",
    ("account.move", "has_reconciled_entries"): "Bezahlt/Abgestimmt",
    ("account.move", "matched_payment_ids"): "Zahlungsbuchungszeilen",
    ("account.move", "invoice_incoterm_id"): "Lieferbedingungen",
    ("account.move", "invoice_cash_rounding_id"): "Methode zur Bargeldrundung",
    # Rechnungszeile
    ("account.move.line", "move_id"): "Rechnungsreferenz",
    ("account.move.line", "name"): "Beschreibung",
    ("account.move.line", "price_unit"): "Preis pro ME",
    ("account.move.line", "price_subtotal"): "Betrag",
    ("account.move.line", "price_total"): "Betrag",
    ("account.move.line", "product_uom_id"): "Mengeneinheit",
    ("account.move.line", "purchase_line_id"): "Bestellposition",
    ("account.move.line", "sequence"): "Nummernfolge",
    ("account.move.line", "company_currency_id"): "Betriebl. Währung",
    ("account.move.line", "partner_id"): "Partner",
    ("account.move.line", "analytic_distribution"): "Kostenstelle",
}


def lade_env(pfad):
    werte = {}
    with open(pfad, encoding="utf-8") as fh:
        for zeile in fh:
            if "=" in zeile and not zeile.strip().startswith("#"):
                s, w = zeile.split("=", 1)
                werte[s.strip()] = w.strip().strip('"')
    return werte


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="lokal")
    p.add_argument("--pruefen", action="store_true")
    a = p.parse_args()
    env = lade_env(os.path.join(REPO, ".env"))
    url = "http://localhost:8069" if a.instanz == "lokal" else "https://k001959vsx.ipax.at"

    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    def rufe(pfad, prm):
        req = urllib.request.Request(url + pfad, data=json.dumps({"jsonrpc": "2.0", "method": "call",
                                                                  "params": prm}).encode(),
                                     headers={"Content-Type": "application/json"})
        with op.open(req, timeout=300) as f:
            return json.loads(f.read().decode())

    rufe("/web/session/authenticate", {"db": env["ODOO18_DB"], "login": env["ODOO18_USER"],
                                       "password": env["ODOO18_PWD"]})

    def kw(model, methode, args, **kwargs):
        o = rufe("/web/dataset/call_kw", {"model": model, "method": methode, "args": args, "kwargs": kwargs})
        if "error" in o:
            raise RuntimeError(str(o["error"])[:300])
        return o.get("result")

    print("Instanz: %s (%s)" % (a.instanz, url))
    gesetzt = abweichung = fehlt = 0
    for (modell, fname), wunsch in sorted(LABELS.items()):
        treffer = kw("ir.model.fields", "search_read",
                     [[("model", "=", modell), ("name", "=", fname)], ["id"]], context={"lang": "en_US"})
        if not treffer:
            fehlt += 1
            print("  --   %s.%s nicht vorhanden" % (modell, fname))
            continue
        fid = treffer[0]["id"]
        ist = kw("ir.model.fields", "read", [[fid], ["field_description"]], context={"lang": "de_DE"})[0]["field_description"]
        if ist == wunsch:
            continue
        if a.pruefen:
            abweichung += 1
            print("  FEHL %-42s = '%s' (erwartet '%s')" % ("%s.%s" % (modell, fname), ist, wunsch))
            continue
        kw("ir.model.fields", "write", [[fid], {"field_description": wunsch}], context={"lang": "de_DE"})
        ist2 = kw("ir.model.fields", "read", [[fid], ["field_description"]], context={"lang": "de_DE"})[0]["field_description"]
        if ist2 == wunsch:
            gesetzt += 1
            print("  OK   %-42s = '%s'" % ("%s.%s" % (modell, fname), wunsch))
        else:
            abweichung += 1
            print("  FEHL %-42s nicht gesetzt (Ist: '%s')" % ("%s.%s" % (modell, fname), ist2))
    print("\nErgebnis: %d gesetzt, %d Abweichungen, %d nicht vorhanden%s"
          % (gesetzt, abweichung, fehlt, " (Pruefmodus)" if a.pruefen else ""))
    return 0 if abweichung == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
