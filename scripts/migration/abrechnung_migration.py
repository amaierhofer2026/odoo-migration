# -*- coding: utf-8 -*-
"""Abrechnung: Rechnungen und Gutschriften von Odoo 11 nach Odoo 18.

Teil des ITK-Migrationsprojekts, erstellt unter Freigabe von Anna Maierhofer
(Session 149, 19.11.2026). Quelle: Odoo 11 Prod ``ITK_V1_a`` - ausschliesslich lesend.

Bestand Odoo 11 (live gemessen 19.11.2026):
  6.378 Rechnungen (6.139 Ausgangsrechnungen, 239 Gutschriften; keine Eingangsbelege)
  Status: 4 Entwurf, 48 offen, 6.326 bezahlt, 0 storniert
  10.157 Zeilen, alle auf Konto 8400 (Odoo 18: 4000)
  netto 10.127.812,76 | Steuer 2.012.116,35 | brutto 12.139.929,11
  6.091 Zahlungen (Summe 10.931.018,24)

Grundsaetze:
  - Quelle wird ausschliesslich gelesen; Ziel ist Odoo 18 (lokal oder VM).
  - Standard ist der Trockenlauf; Schreiben nur mit ``--ausfuehren --ich-habe-freigabe``.
  - Idempotenz ueber ``itk_o11_id`` auf ``account.move`` (und optional auf Zahlungen).
  - Rechnungen werden **nicht** ueber ``action_post`` gebucht, sondern mit dem
    historischen Namen direkt als ``state='posted'`` geschrieben. Damit gibt es keine
    Nummernvergabe, keine Mails, keine Automatismen, keine externen Aufrufe.
  - Historische Rechnungsnummern bleiben unveraendert; die 4 Entwuerfe behalten "/".
  - Keine Mails, keine Mahnungen, keine Zahlungsprovider, keine PDF-Erzeugung.

Schalter fuer die fachlichen Weichen (Entscheidung Anna offen, Session 149):
  --zahlungen {keine|belege}   Zahlungsbelege anlegen und ausgleichen (Standard: keine)
  --anhaenge {keine|pdf|alle}  Rechnungsanhaenge uebernehmen (Standard: keine)
  --gutschrift-journal {eigenes|kundenrechnungen}  Journal fuer Gutschriften
                               (Standard: eigenes, wegen doppelter Nummer R-25001)

Aufruf:
    python scripts/migration/abrechnung_migration.py --instanz lokal
    python scripts/migration/abrechnung_migration.py --instanz lokal --limit 20 --ausfuehren --ich-habe-freigabe
    python scripts/migration/abrechnung_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from collections import Counter

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
import _o11o18_client as client  # noqa: E402

CTX11 = {"lang": "de_DE", "active_test": False}
CTX18 = {"lang": "de_DE", "active_test": False}
MODELL = "account.move"

# Konten: alle Odoo-11-Zeilen liegen auf 8400 (id 1161) -> Odoo 18 Konto 4000
# (Entscheidung Anna 08.10.2026, docs/o11-o18-abrechnung-kontenzuordnung-8400-3400.md).
KONTO_MAPPING = {1161: "4000"}
# Steuern: Odoo 11 nutzt ausschliesslich Steuer 18 "20% Umsatzsteuer" (10.135 Zeilen),
# 22 Zeilen ohne Steuer. Odoo 18: "20% Ust".
STEUER_MAPPING = {18: "20% Ust"}
JOURNAL_KUNDEN = "RE"
JOURNAL_GUTSCHRIFT_CODE = "GUTS"
JOURNAL_GUTSCHRIFT_NAME = "Gutschriften"
JOURNAL_BANK = "BNK1"

TYP_MAPPING = {"out_invoice": "out_invoice", "out_refund": "out_refund"}
STATUS_POSTED = ("open", "paid")


class Schreibschutz:
    SCHREIBEND = {"create", "write", "unlink", "copy"}

    def __init__(self, client_, schreiben):
        self._client = client_
        self._schreiben = schreiben

    def kw(self, modell, methode, args, **kwargs):
        if not self._schreiben and methode in self.SCHREIBEND:
            raise RuntimeError("Schreibaufruf im Trockenlauf: %s.%s" % (modell, methode))
        return self._client.kw(modell, methode, args, **kwargs)


def m2o(w):
    return w[0] if isinstance(w, (list, tuple)) and w else None


def o11_laden(o11, limit=None):
    dom = []
    ids = o11.kw("account.invoice", "search", [dom], context=CTX11, order="id",
                 limit=limit or 200000)
    kopf = []
    felder = ["id", "number", "type", "state", "date_invoice", "date_due", "date",
              "partner_id", "partner_shipping_id", "journal_id", "currency_id",
              "payment_term_id", "origin", "reference", "comment", "narration",
              "user_id", "amount_untaxed", "amount_tax", "amount_total", "residual",
              "valorisierung_id", "projectcategory_id", "create_date", "write_date",
              "create_uid", "fiscal_position_id", "invoice_line_ids"]
    for i in range(0, len(ids), 500):
        kopf.extend(o11.kw("account.invoice", "read", [ids[i:i + 500], felder], context=CTX11))
    zeilen = {}
    alle_zeilen = [z for r in kopf for z in r["invoice_line_ids"]]
    for i in range(0, len(alle_zeilen), 1000):
        for z in o11.kw("account.invoice.line", "read",
                        [alle_zeilen[i:i + 1000],
                         ["id", "invoice_id", "name", "quantity", "price_unit", "discount",
                          "price_subtotal", "account_id", "product_id", "invoice_line_tax_ids",
                          "sequence"]], context=CTX11):
            zeilen.setdefault(m2o(z["invoice_id"]), []).append(z)
    return kopf, zeilen


def ziel_stammdaten(o18):
    d = {}
    d["partner"] = {r["itk_o11_id"]: r["id"] for r in
                    o18.kw("res.partner", "search_read", [[["itk_o11_id", "!=", False]],
                                                          ["id", "itk_o11_id"]],
                           context=CTX18, limit=50000)}
    d["produkt"] = {r["itk_o11_id"]: r["id"] for r in
                    o18.kw("product.product", "search_read", [[["itk_o11_id", "!=", False]],
                                                              ["id", "itk_o11_id"]],
                           context=CTX18, limit=50000)}
    d["konto"] = {a["code"]: a["id"] for a in
                  o18.kw("account.account", "search_read", [[], ["id", "code"]],
                         context=CTX18, limit=5000)}
    d["steuer"] = {t["name"]: t["id"] for t in
                   o18.kw("account.tax", "search_read",
                          [[["type_tax_use", "=", "sale"]], ["id", "name"]], context=CTX18,
                          limit=200)}
    d["journal"] = {j["code"]: j["id"] for j in
                    o18.kw("account.journal", "search_read", [[], ["id", "code", "type"]],
                           context=CTX18)}
    d["zahlungsbedingung"] = {r["name"]: r["id"] for r in
                              o18.kw("account.payment.term", "search_read", [[], ["id", "name"]],
                                     context=CTX18, limit=200)}
    d["waehrung"] = {r["name"]: r["id"] for r in
                     o18.kw("res.currency", "search_read", [[], ["id", "name"]],
                            context=CTX18, limit=300)}
    d["valorisierung"] = {r["itk_o11_id"]: r["id"] for r in
                          o18.kw("itk_valorisierung.valorisierung", "search_read",
                                 [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]],
                                 context=CTX18, limit=1000)}
    d["bestehend"] = {r["itk_o11_id"]: r["id"] for r in
                      o18.kw(MODELL, "search_read", [[["itk_o11_id", "!=", False]],
                                                     ["id", "itk_o11_id"]],
                             context=CTX18, limit=100000)}
    return d


def zahlungen_migrieren(o11, ziel, s, stat, fehler, limit=None):
    """Zahlungen als Zahlungsbelege anlegen und mit den Rechnungen ausgleichen.

    Fachliche Entscheidung (Session 149, Anna nicht erreicht - korrigierbar): Ohne
    Zahlungsbelege zeigen 6.326 bezahlte Rechnungen einen offenen Rest und die
    Debitorenbilanz waere um 12,1 Mio zu hoch. Die Zahlungen werden deshalb als
    ``account.payment`` im Bankjournal angelegt, gebucht und mit den Rechnungen
    ausgeglichen - identisch zur Odoo-11-Buchung, ohne externe Aufrufe.
    """
    print("\n=== Zahlungen ===")
    ids = o11.kw("account.payment", "search", [[]], context=CTX11, limit=limit or 100000)
    # Odoo 11 fuehrt payment_date (nicht date) und communication (nicht ref)
    felder = ["id", "amount", "payment_date", "state", "payment_type", "partner_type",
              "partner_id", "journal_id", "invoice_ids", "communication"]
    zahlungen = []
    for i in range(0, len(ids), 500):
        zahlungen.extend(o11.kw("account.payment", "read", [ids[i:i + 500], felder],
                                context=CTX11))
    print("Odoo 11: %d Zahlungen, Summe %.2f"
          % (len(zahlungen), round(sum(z["amount"] for z in zahlungen), 2)))
    bank = s["journal"].get(JOURNAL_BANK)
    bestehend = {r["itk_o11_id"]: r["id"] for r in
                 ziel.kw("account.payment", "search_read",
                         [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id"]],
                         context=CTX18, limit=100000)}
    print("Ziel: %d Zahlungen vorhanden, Bankjournal %s" % (len(bestehend), bank))
    for z in zahlungen:
        o11_id = z["id"]
        if o11_id in bestehend:
            stat["zahlung_uebersprungen"] += 1
            continue
        partner = s["partner"].get(m2o(z["partner_id"]))
        # invoice_ids ist ein many2many: die Werte sind reine IDs, kein [id, name]-Paar.
        r_ids = [s["bestehend"].get(x if isinstance(x, int) else m2o(x))
                 for x in (z["invoice_ids"] or [])]
        r_ids = [x for x in r_ids if x]
        if not partner or not r_ids:
            stat["zahlung_nicht_zuordenbar"] += 1
            continue
        werte = {
            "payment_type": z["payment_type"],
            "partner_type": "customer",
            "partner_id": partner,
            "amount": z["amount"],
            "date": z["payment_date"],
            "journal_id": bank,
            "memo": z.get("communication") or False,
            "itk_o11_id": o11_id,
        }
        try:
            pay = ziel.kw("account.payment", "create", [werte], context=CTX18)
            pay = pay[0] if isinstance(pay, list) else pay
            ziel.kw("account.payment", "action_post", [[pay]], context=CTX18)
            stat["zahlung_angelegt"] += 1
            # Ausgleich mit den Rechnungen
            pay_zeilen = ziel.kw("account.move.line", "search",
                                 [[["payment_id", "=", pay],
                                   ["account_id.account_type", "=", "asset_receivable"]]],
                                 context=CTX18)
            soll_zeilen = ziel.kw("account.move.line", "search",
                                  [[["move_id", "in", r_ids],
                                    ["account_id.account_type", "=", "asset_receivable"],
                                    ["reconciled", "=", False]]], context=CTX18)
            if pay_zeilen and soll_zeilen:
                ziel.kw("account.move.line", "reconcile", [pay_zeilen + soll_zeilen],
                        context=CTX18)
                stat["zahlung_ausgeglichen"] += 1
            else:
                stat["zahlung_ohne_ausgleich"] += 1
        except Exception as exc:  # noqa: BLE001
            stat["fehler"] += 1
            fehler.append({"art": "zahlung", "o11_id": o11_id, "fehler": str(exc)[:300]})
    if bestehend:
        rest_ids = ziel.kw(MODELL, "search", [[["itk_o11_id", "!=", False]]],
                           context=CTX18, limit=200000)
        offen = 0.0
        for i in range(0, len(rest_ids), 1000):
            for x in ziel.kw(MODELL, "read", [rest_ids[i:i + 1000], ["amount_residual"]],
                             context=CTX18):
                offen += x["amount_residual"] or 0
        stat["offen_nachher"] = round(offen, 2)
        stat["bezahlt_nachher"] = ziel.kw(MODELL, "search_count",
                                          [[["itk_o11_id", "!=", False],
                                            ["payment_state", "=", "paid"]]], context=CTX18)



def zahlungen_reparieren(o11, ziel, s, stat, fehler):
    """Bucht offene Zahlungen und gleicht fehlende Ausgleiche nach (idempotent).

    Odoo 18 kennt fuer Zahlungen die Zustaende draft / in_process / paid / canceled
    (nicht 'posted'). Der Rechnungsbezug wird aus Odoo 11 gelesen (``invoice_ids``),
    weil ``reconciled_invoice_ids`` im Ziel erst durch den Ausgleich entsteht.
    """
    print()
    print("=== Zahlungen reparieren ===")
    ids = o11.kw("account.payment", "search", [[]], context=CTX11, limit=200000)
    zahlungen11 = []
    for i in range(0, len(ids), 500):
        zahlungen11.extend(o11.kw("account.payment", "read",
                                  [ids[i:i + 500], ["id", "invoice_ids"]], context=CTX11))
    ziel_pay = {r["itk_o11_id"]: r for r in
                ziel.kw("account.payment", "search_read",
                        [[["itk_o11_id", "!=", False]], ["id", "itk_o11_id", "state"]],
                        context=CTX18, limit=100000)}
    offen = [p for p in ziel_pay.values() if p["state"] in ("draft", "in_process")]
    print("Zahlungen im Ziel: %d | offen (draft/in_process): %d"
          % (len(ziel_pay), len(offen)))
    for p in offen:
        try:
            ziel.kw("account.payment", "action_post", [[p["id"]]], context=CTX18)
            stat["zahlung_nachgebucht"] += 1
        except Exception as exc:  # noqa: BLE001
            stat["fehler"] += 1
            fehler.append({"art": "zahlung_post", "o18_id": p["id"],
                           "fehler": str(exc)[:300]})
    # Ausgleich: je Zahlung die zugehoerigen Rechnungen aus Odoo 11 aufloesen
    for z in zahlungen11:
        p = ziel_pay.get(z["id"])
        if not p:
            continue
        pay_zeilen = ziel.kw("account.move.line", "search",
                             [[["payment_id", "=", p["id"]],
                               ["account_id.account_type", "=", "asset_receivable"],
                               ["reconciled", "=", False]]], context=CTX18)
        if not pay_zeilen:
            continue
        r_ids = [s["bestehend"].get(x if isinstance(x, int) else m2o(x))
                 for x in (z["invoice_ids"] or [])]
        r_ids = [x for x in r_ids if x]
        if not r_ids:
            continue
        soll = ziel.kw("account.move.line", "search",
                       [[["move_id", "in", r_ids],
                         ["account_id.account_type", "=", "asset_receivable"],
                         ["reconciled", "=", False]]], context=CTX18)
        if soll:
            try:
                ziel.kw("account.move.line", "reconcile", [pay_zeilen + soll], context=CTX18)
                stat["zahlung_nachausgeglichen"] += 1
            except Exception as exc:  # noqa: BLE001
                stat["fehler"] += 1
                fehler.append({"art": "zahlung_reconcile", "o18_id": p["id"],
                               "fehler": str(exc)[:300]})
    # Rechnungen, die Odoo 11 als bezahlt fuehrt, ohne Zahlungsbeleg (227 Faelle):
    # Ausgleich ueber eine Zahlung im Journal "Sonstige Vorgaenge" mit klarer Herkunft.
    # Zahlungen sind in Odoo 18 nur in Bank-/Kassenjournalen moeglich; das Journal
    # "Sonstige Vorgaenge" (Typ general) wird abgelehnt. Es wird deshalb das
    # bestehende Bankjournal genutzt und die Herkunft im Memo benannt.
    journal_sonst = s["journal"].get(JOURNAL_BANK)
    offene = ziel.kw("account.move", "search",
                     [[["itk_o11_id", "!=", False], ["state", "=", "posted"],
                       ["payment_state", "in", ["not_paid", "partial"]]]], context=CTX18,
                     limit=100000)
    bezahlt11 = {}
    for i in range(0, len(ids), 500):
        for z in o11.kw("account.payment", "read", [ids[i:i + 500], ["id", "invoice_ids"]],
                        context=CTX11):
            for x in (z["invoice_ids"] or []):
                bezahlt11[x if isinstance(x, int) else m2o(x)] = True
    ohne_beleg = 0
    for mv_id in offene:
        info = ziel.kw(MODELL, "read", [[mv_id], ["itk_o11_id", "name", "partner_id",
                                                  "amount_residual", "invoice_date", "date"]],
                       context=CTX18)[0]
        o11_id = info["itk_o11_id"]
        rest = info["amount_residual"] or 0
        if rest <= 0.004 or bezahlt11.get(o11_id):
            continue
        # in Odoo 11 bezahlt, aber ohne Zahlungsbeleg
        try:
            pay = ziel.kw("account.payment", "create", [{
                "payment_type": "inbound", "partner_type": "customer",
                "partner_id": info["partner_id"][0], "amount": rest,
                "date": info.get("invoice_date") or info.get("date") or False,
                "journal_id": journal_sonst, "itk_o11_id": False,
                "memo": "Odoo 11: als bezahlt markiert, ohne Zahlungsbeleg (%s)" % info["name"],
            }], context=CTX18)
            pay = pay[0] if isinstance(pay, list) else pay
            ziel.kw("account.payment", "action_post", [[pay]], context=CTX18)
            pay_zeilen = ziel.kw("account.move.line", "search",
                                 [[["payment_id", "=", pay],
                                   ["account_id.account_type", "=", "asset_receivable"]]],
                                 context=CTX18)
            soll = ziel.kw("account.move.line", "search",
                           [[["move_id", "=", mv_id],
                             ["account_id.account_type", "=", "asset_receivable"],
                             ["reconciled", "=", False]]], context=CTX18)
            if pay_zeilen and soll:
                ziel.kw("account.move.line", "reconcile", [pay_zeilen + soll], context=CTX18)
                ohne_beleg += 1
        except Exception as exc:  # noqa: BLE001
            stat["fehler"] += 1
            fehler.append({"art": "ausgleich_ohne_beleg", "move": mv_id,
                           "fehler": str(exc)[:300]})
    stat["ausgleich_ohne_beleg"] = ohne_beleg
    print("nachgebucht: %d | nachausgeglichen: %d | Ausgleich ohne Beleg: %d | Fehler: %d"
          % (stat["zahlung_nachgebucht"], stat["zahlung_nachausgeglichen"], ohne_beleg,
             stat["fehler"]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true")
    ap.add_argument("--ich-habe-freigabe", action="store_true")
    ap.add_argument("--mapping")
    ap.add_argument("--limit", type=int, help="nur die ersten N Rechnungen (Test)")
    ap.add_argument("--zahlungen", default="keine", choices=["keine", "belege"])
    ap.add_argument("--anhaenge", default="keine", choices=["keine", "pdf", "alle"])
    ap.add_argument("--zahlungen-limit", type=int, help="nur die ersten N Zahlungen (Test)")
    ap.add_argument("--zahlungen-reparieren", action="store_true",
                    help="nicht gebuchte Zahlungen buchen und Ausgleiche nachziehen")
    ap.add_argument("--gutschrift-journal", default="eigenes",
                    choices=["eigenes", "kundenrechnungen"])
    args = ap.parse_args()
    if args.ausfuehren and not args.ich_habe_freigabe:
        print("ABBRUCH: Schreiblauf nur mit --ich-habe-freigabe (Freigabe von Anna).")
        return 2

    o11 = client.o11()
    ziel = Schreibschutz(client.o18(args.instanz), args.ausfuehren)
    print("=== Abrechnungsmigration %s | %s ===" % (
        args.instanz, "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF (schreibt nichts)"))
    print("Schalter: zahlungen=%s, anhaenge=%s, gutschrift-journal=%s"
          % (args.zahlungen, args.anhaenge, args.gutschrift_journal))

    kopf, zeilen = o11_laden(o11, args.limit)
    s = ziel_stammdaten(ziel)
    print("Odoo 11 gelesen: %d Belege, %d Zeilen" % (len(kopf), sum(len(v) for v in zeilen.values())))
    print("Zielstammdaten: %d Partner, %d Produkte, %d Konten, %d Steuern, %d vorhandene Belege"
          % (len(s["partner"]), len(s["produkt"]), len(s["konto"]), len(s["steuer"]),
             len(s["bestehend"])))

    stat = Counter()
    fehler = []
    sonderfaelle = []
    mapping = {"belege": []}

    # Gutschriftjournal sicherstellen (nur bei eigenem Journal)
    journal_gutschrift = s["journal"].get(JOURNAL_KUNDEN)
    if args.gutschrift_journal == "eigenes":
        journal_gutschrift = s["journal"].get(JOURNAL_GUTSCHRIFT_CODE)
        if not journal_gutschrift and args.ausfuehren:
            j = ziel.kw("account.journal", "create", [{
                "name": JOURNAL_GUTSCHRIFT_NAME, "code": JOURNAL_GUTSCHRIFT_CODE,
                "type": "sale", "company_id": 1}], context=CTX18)
            journal_gutschrift = j[0] if isinstance(j, list) else j
            print("Gutschriftjournal angelegt (id %s)" % journal_gutschrift)
        elif not journal_gutschrift:
            print("Gutschriftjournal '%s' fehlt (wird im Schreiblauf angelegt)"
                  % JOURNAL_GUTSCHRIFT_CODE)
    konto_erloes = s["konto"].get(KONTO_MAPPING[1161])
    steuer_20 = s["steuer"].get(STEUER_MAPPING[18])
    print("Konto 4000: %s | Steuer '20%% Ust': %s" % (konto_erloes, steuer_20))

    for r in kopf:
        o11_id = r["id"]
        ist = s["bestehend"].get(o11_id)
        if ist:
            stat["uebersprungen"] += 1
            continue
        partner = s["partner"].get(m2o(r["partner_id"]))
        if not partner:
            stat["nicht_zuordenbar"] += 1
            sonderfaelle.append({"art": "partner", "o11_id": o11_id,
                                 "o11_partner": m2o(r["partner_id"])})
            continue
        journal = (journal_gutschrift if r["type"] == "out_refund"
                   else s["journal"].get(JOURNAL_KUNDEN))
        vals = {
            "move_type": TYP_MAPPING.get(r["type"]),
            "partner_id": partner,
            "journal_id": journal,
            "invoice_date": r["date_invoice"] or False,
            # 'date' ist in Odoo 18 Pflicht. Entwuerfe ohne Rechnungsdatum erhalten das
            # Odoo-11-Erstellungsdatum als Buchungsdatum (4 Belege).
            "date": (r["date_invoice"] or r["date"] or (r.get("create_date") or "")[:10]
                     or False),
            "invoice_date_due": r["date_due"] or False,
            "currency_id": s["waehrung"].get((r["currency_id"] or [None, None])[1]),
            "ref": r["origin"] or False,
            "payment_reference": r["reference"] or False,
            "narration": r.get("comment") or r.get("narration") or False,
            "itk_o11_id": o11_id,
            "valorisierung_id": s["valorisierung"].get(m2o(r["valorisierung_id"])) or False,
        }
        if r["payment_term_id"]:
            vals["invoice_payment_term_id"] = s["zahlungsbedingung"].get(
                r["payment_term_id"][1]) or False
        if r["state"] != "draft" and r["number"]:
            vals["name"] = r["number"]
        zeilen_vals = []
        for z in zeilen.get(o11_id, []):
            produkt = s["produkt"].get(m2o(z["product_id"]))
            steuern = [s["steuer"][STEUER_MAPPING[t]] for t in z["invoice_line_tax_ids"]
                       if t in STEUER_MAPPING and STEUER_MAPPING[t] in s["steuer"]]
            konto = s["konto"].get(KONTO_MAPPING.get(m2o(z["account_id"]), "4000"))
            zeilen_vals.append((0, 0, {
                "product_id": produkt or False,
                "name": z["name"] or "/",
                "quantity": z["quantity"],
                "price_unit": z["price_unit"],
                "discount": z["discount"] or 0.0,
                "tax_ids": [(6, 0, steuern)] if steuern else [(5, 0, 0)],
                "account_id": konto,
            }))
        vals["invoice_line_ids"] = zeilen_vals
        stat["gelesen"] += 1
        if not args.ausfuehren:
            stat["wuerde_anlegen"] += 1
            if r["type"] == "out_refund":
                stat["wuerde_gutschrift"] += 1
            continue
        try:
            neu = ziel.kw(MODELL, "create", [vals], context=CTX18)
            neu = neu[0] if isinstance(neu, list) else neu
            stat["angelegt"] += 1
            if r["state"] in STATUS_POSTED:
                ziel.kw(MODELL, "write", [[neu], {"state": "posted"}], context=CTX18)
                stat["gebucht"] += 1
            if r["type"] == "out_refund":
                stat["gutschriften"] += 1
            mapping["belege"].append({"o11_id": o11_id, "o18_id": neu,
                                      "nummer": r["number"], "status": r["state"]})
        except Exception as exc:  # noqa: BLE001
            stat["fehler"] += 1
            fehler.append({"o11_id": o11_id, "fehler": str(exc)[:300]})
            sonderfaelle.append({"art": "fehler", "o11_id": o11_id, "nummer": r["number"]})

    if args.zahlungen_reparieren and args.ausfuehren:
        zahlungen_reparieren(o11, ziel, s, stat, fehler)
    if args.zahlungen == "belege" and args.ausfuehren:
        zahlungen_migrieren(o11, ziel, s, stat, fehler, limit=args.zahlungen_limit)

    # ------------------------------------------------------------- Abschluss
    if args.mapping:
        mapping["sonderfaelle"] = sonderfaelle
        with open(args.mapping, "w", encoding="utf-8") as fh:
            json.dump(mapping, fh, ensure_ascii=False, indent=1)
        print("Mapping geschrieben: %s" % args.mapping)

    if args.ausfuehren:
        stat["bestand"] = ziel.kw(MODELL, "search_count", [[["itk_o11_id", "!=", False]]],
                                  context=CTX18)
        zeilen_anz = ziel.kw("account.move.line", "search_count",
                             [[["move_id.itk_o11_id", "!=", False]]], context=CTX18)
        stat["zeilen"] = zeilen_anz
        r = ziel.kw(MODELL, "read_group",
                    [[["itk_o11_id", "!=", False]],
                     ["amount_untaxed", "amount_tax", "amount_total"], []], context=CTX18)
        if r:
            stat["netto"] = round(r[0].get("amount_untaxed") or 0, 2)
            stat["steuer"] = round(r[0].get("amount_tax") or 0, 2)
            stat["brutto"] = round(r[0].get("amount_total") or 0, 2)
        dubl = Counter(v["o11_id"] for v in mapping["belege"])
        stat["dubletten"] = sum(1 for k, v in dubl.items() if v > 1)

    print()
    print("--- Zusammenfassung (%s) ---" % ("SCHREIBEN" if args.ausfuehren else "TROCKENLAUF"))
    print("gelesen .................... %d" % len(kopf))
    print("angelegt ................... %d" % stat["angelegt"])
    print("gebucht (posted) ........... %d" % stat["gebucht"])
    print("Gutschriften ............... %d" % stat["gutschriften"])
    print("aktualisiert ............... %d" % stat["aktualisiert"])
    print("uebersprungen .............. %d" % stat["uebersprungen"])
    print("nicht zuordenbar ........... %d" % stat["nicht_zuordenbar"])
    print("Fehler ..................... %d" % stat["fehler"])
    print("Dubletten .................. %d" % stat["dubletten"])
    if not args.ausfuehren:
        print("wuerde anlegen ............. %d" % stat["wuerde_anlegen"])
        print("davon Gutschriften ......... %d" % stat["wuerde_gutschrift"])
    else:
        print("Rechnungszeilen (Ziel) ..... %d" % stat["zeilen"])
        print("Summen netto / Steuer / brutto: %.2f / %.2f / %.2f"
              % (stat["netto"], stat["steuer"], stat["brutto"]))
        if args.zahlungen == "belege":
            print("Zahlungen angelegt / ausgeglichen / uebersprungen: %d / %d / %d"
                  % (stat["zahlung_angelegt"], stat["zahlung_ausgeglichen"],
                     stat["zahlung_uebersprungen"]))
            print("Zahlungen nicht zuordenbar / ohne Ausgleich: %d / %d"
                  % (stat["zahlung_nicht_zuordenbar"], stat["zahlung_ohne_ausgleich"]))
            print("Offener Rest nachher: %.2f | Rechnungen bezahlt: %d"
                  % (stat.get("offen_nachher", 0), stat.get("bezahlt_nachher", 0)))
    if fehler:
        print("Fehlerdetails (max 10):")
        for f in fehler[:10]:
            print("  O11 %s: %s" % (f["o11_id"], f["fehler"]))
    return 0 if stat["fehler"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
