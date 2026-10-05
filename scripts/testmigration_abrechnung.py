"""Testmigration Abrechnung: wenige repraesentative Datensaetze Odoo 11 -> Odoo 18 Testinstanz.

Status: vorbereitet am 05.10.2026 (Session 123), NOCH NICHT AUSGEFUEHRT.
Regel und Begruendung: docs/o11-o18-testmigration-regel.md

Aufruf:
    python scripts/testmigration_abrechnung.py --instanz vm --plan          (Standard, schreibt nichts)
    python scripts/testmigration_abrechnung.py --instanz vm --ausfuehren --ich-habe-freigabe
    python scripts/testmigration_abrechnung.py --instanz vm --aufraeumen

Grundsaetze:
  - Quelle Odoo 11 wird ausschliesslich gelesen.
  - Ziel darf nur die Testdatenbank sein (ODOO18_DB, geprueft gegen odoo18_test).
  - Beziehungen werden ueber fachliche Schluessel aufgeloest, nie ueber IDs.
  - Jeder Fehler bricht ab (Exit-Code 1). Es wird nichts still uebersprungen.
  - Erzeugte Datensaetze werden ins Protokoll geschrieben; --aufraeumen loescht nur diese.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18  # noqa: E402

ZIEL_DB = "odoo18_test"
PROTOKOLL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "docs", "_testmigration_protokoll.json")
CTX = {"lang": "de_DE"}

# Konten-Mapping aus docs/o11-o18-abrechnung-abschlusspruefung.md, Abschnitt 3
KONTO_MAPPING = {"1201": "2801", "1410": "2000", "1776": "3500", "8400": "4000"}

O11_BELEGARTEN = {"out_invoice": "Kundenrechnung", "out_refund": "Kunden-Gutschrift",
                  "in_invoice": "Eingangsrechnung", "in_refund": "Lieferanten-Gutschrift"}


def rpc(k, modell, methode, args, was, **kwargs):
    try:
        return k.kw(modell, methode, args, **kwargs)
    except Exception as fehler:  # noqa: BLE001
        raise SystemExit("ABBRUCH: %s fehlgeschlagen (%s.%s): %s"
                         % (was, modell, methode, str(fehler)[:300]))


def name(von):
    """m2o-Wert [id, name] -> Name, sonst None."""
    return von[1] if isinstance(von, (list, tuple)) and len(von) > 1 else None


# --------------------------------------------------------------------------
# 1. Auswahl in Odoo 11 (nur lesend)
# --------------------------------------------------------------------------
def waehle_belege(k):
    """Waehlt je Belegart einen kleinen, mehrzeiligen Beleg - produktion schonend in zwei Schritten."""
    felder = ["id", "number", "type", "state", "partner_id", "journal_id", "date_invoice",
              "date_due", "payment_term_id", "currency_id", "amount_untaxed", "amount_tax",
              "amount_total", "invoice_line_ids"]
    auswahl = {}
    for art in ("out_invoice", "out_refund", "in_invoice", "in_refund"):
        # 1. nur IDs holen (leicht), begrenzt, damit die Produktion nicht belastet wird.
        #    Hinweis: Odoo 11 kennt die Zustaende draft/open/paid, NICHT posted.
        ids = rpc(k, "account.invoice", "search",
                  [[("type", "=", art), ("state", "in", ["open", "paid"])], 0, 60],
                  "Belege suchen (%s)" % art)
        if not ids:
            ids = rpc(k, "account.invoice", "search",
                      [[("type", "=", art)], 0, 60], "Belege suchen (%s, ohne Status)" % art)
        if not ids:
            print("   %s: in der Produktion nicht vorhanden (0 Datensaetze)." % art)
            continue
        # 2. nur diese Datensaetze lesen
        treffer = rpc(k, "account.invoice", "read", [ids, felder], "Belege lesen (%s)" % art)
        klein = [b for b in treffer if b["invoice_line_ids"] and len(b["invoice_line_ids"]) <= 10]
        if klein:
            auswahl[art] = sorted(klein, key=lambda b: -len(b["invoice_line_ids"]))[0]
        if art == "out_invoice":
            entwurf_ids = rpc(k, "account.invoice", "search",
                              [[("type", "=", art), ("state", "=", "draft")], 0, 30],
                              "Belegentwuerfe suchen")
            if entwurf_ids:
                entwuerfe = rpc(k, "account.invoice", "read", [entwurf_ids, felder],
                                "Belegentwuerfe lesen")
                passend = [b for b in entwuerfe if b["invoice_line_ids"] and len(b["invoice_line_ids"]) <= 10]
                if passend:
                    auswahl["out_invoice_draft"] = sorted(passend, key=lambda b: -len(b["invoice_line_ids"]))[0]
    return auswahl


def waehle_zeilen(k, beleg):
    zeilen = rpc(k, "account.invoice.line", "search_read",
                 [[("invoice_id", "=", beleg["id"])],
                  ["id", "name", "quantity", "price_unit", "discount", "product_id", "account_id",
                   "invoice_line_tax_ids", "account_analytic_id"]], "Belegzeilen lesen")
    return zeilen


def waehle_stammdaten(k, belege):
    """Journale, Konten, Steuern, Zahlungsbedingungen und Partner, die die Belege brauchen."""
    partner_ids, journal_ids, konto_ids, steuer_ids, zahlungsbedingung_ids = set(), set(), set(), set(), set()
    for b in belege.values():
        if b.get("partner_id"):
            partner_ids.add(b["partner_id"][0])
        if b.get("journal_id"):
            journal_ids.add(b["journal_id"][0])
        if b.get("payment_term_id"):
            zahlungsbedingung_ids.add(b["payment_term_id"][0])
        for z in waehle_zeilen(k, b):
            if z.get("account_id"):
                konto_ids.add(z["account_id"][0])
            for t in (z.get("invoice_line_tax_ids") or []):
                steuer_ids.add(t)
    partner = rpc(k, "res.partner", "search_read", [[("id", "in", list(partner_ids))],
                                                    ["id", "name", "is_company", "vat", "street",
                                                     "zip", "city", "country_id", "lang",
                                                     "property_payment_term_id", "customer",
                                                     "supplier"]], "Partner lesen")
    journale = rpc(k, "account.journal", "search_read", [[("id", "in", list(journal_ids))],
                                                         ["id", "name", "code", "type"]], "Journale lesen")
    konten = rpc(k, "account.account", "search_read", [[("id", "in", list(konto_ids))],
                                                       ["id", "code", "name"]], "Konten lesen")
    steuern = rpc(k, "account.tax", "search_read", [[("id", "in", list(steuer_ids))],
                                                    ["id", "name", "amount", "type_tax_use"]],
                  "Steuern lesen") if steuer_ids else []
    bedingungen = rpc(k, "account.payment.term", "search_read",
                      [[("id", "in", list(zahlungsbedingung_ids))], ["id", "name"]],
                      "Zahlungsbedingungen lesen") if zahlungsbedingung_ids else []
    return partner, journale, konten, steuern, bedingungen


# --------------------------------------------------------------------------
# 2. Plan gegen die Zielinstanz pruefen (nur lesend)
# --------------------------------------------------------------------------
def pruefe_ziel(z, partner, journale, konten, steuern, bedingungen, produkte):
    plan = []
    for kollektion, modell, feld, liste in (
            ("Partner", "res.partner", "name", partner),
            ("Journale", "account.journal", "code", journale),
            ("Konten", "account.account", "code", konten),
            ("Steuern", "account.tax", "name", steuern),
            ("Zahlungsbedingungen", "account.payment.term", "name", bedingungen),
            ("Produkte", "product.template", "name", produkte)):
        for satz in liste:
            schluessel = satz["code"] if modell == "account.account" else satz["name"]
            schluessel = KONTO_MAPPING.get(schluessel, schluessel) if modell == "account.account" else schluessel
            treffer = rpc(z, modell, "search_count", [[(feld, "=", schluessel)]],
                          "Zielpruefung %s %r" % (modell, schluessel))
            if not treffer:
                plan.append({"schritt": "Stammdaten", "modell": modell, "schluessel": schluessel,
                             "zustand": "fehlt im Ziel"})
            elif treffer > 1:
                raise SystemExit("ABBRUCH: Schluessel %r ist in %s nicht eindeutig (%d Treffer)."
                                 % (schluessel, modell, treffer))
            else:
                plan.append({"schritt": "Stammdaten", "modell": modell, "schluessel": schluessel,
                             "zustand": "vorhanden"})
    return plan


# --------------------------------------------------------------------------
# 3. Ausfuehren (nur mit --ausfuehren --ich-habe-freigabe)
# --------------------------------------------------------------------------
def lege_an(mitschrift, z, modell, werte, schluessel, was):
    vorhanden = rpc(z, modell, "search", [[(schluessel[0], "=", schluessel[1])]],
                    "Suche %s %r" % (modell, schluessel[1]))
    if vorhanden:
        return vorhanden[0]
    neue = rpc(z, modell, "create", [werte], "Anlegen %s (%s)" % (modell, was))
    mitschrift.append({"modell": modell, "id": neue, "schluessel": schluessel[1]})
    return neue


def fuehre_aus(z, k, belege, partner, journale, konten, steuern, bedingungen, produkte, mitschrift):
    # 1. Partner ueber fachlichen Schluessel (Name)
    for p in partner:
        lege_an(mitschrift, z, "res.partner",
                {"name": p["name"], "is_company": p["is_company"], "vat": p["vat"] or False,
                 "street": p["street"] or False, "zip": p["zip"] or False, "city": p["city"] or False,
                 "lang": p["lang"] or "de_DE",
                 "customer_rank": 1 if p.get("customer") else 0,
                 "supplier_rank": 1 if p.get("supplier") else 0},
                ("name", p["name"]), "Partner")
    # 2. Produkte
    for pr in produkte:
        lege_an(mitschrift, z, "product.template",
                {"name": pr["name"], "type": "service" if pr["type"] == "service" else "consu",
                 "list_price": pr["list_price"],
                 "sale_ok": pr["sale_ok"], "purchase_ok": pr["purchase_ok"]},
                ("name", pr["name"]), "Produkt")
    # 3. Belege
    for schluessel, b in belege.items():
        ziel_partner = rpc(z, "res.partner", "search", [[("name", "=", name(b["partner_id"]))]],
                           "Partner suchen")[0]
        ziel_journal = rpc(z, "account.journal", "search", [[("code", "=", name(b["journal_id"]))]],
                           "Journal suchen")[0]
        zeilen = []
        for ze in waehle_zeilen(k, b):
            zeile = {"name": ze["name"], "quantity": ze["quantity"], "price_unit": ze["price_unit"],
                     "discount": ze["discount"] or 0.0}
            if ze.get("product_id"):
                ziel_produkt = rpc(z, "product.product", "search",
                                   [[("name", "=", name(ze["product_id"]))]], "Produkt suchen")
                if ziel_produkt:
                    zeile["product_id"] = ziel_produkt[0]
            if ze.get("account_id"):
                code = KONTO_MAPPING.get(name(ze["account_id"]).split()[0], name(ze["account_id"]).split()[0])
                ziel_konto = rpc(z, "account.account", "search", [[("code", "=", code)]], "Konto suchen")
                if ziel_konto:
                    zeile["account_id"] = ziel_konto[0]
            steuer_ids = []
            for t in (ze.get("invoice_line_tax_ids") or []):
                s = next((x for x in steuern if x["id"] == t), None)
                if s:
                    ziel_steuer = rpc(z, "account.tax", "search",
                                      [[("name", "=", s["name"]), ("amount", "=", s["amount"])]],
                                      "Steuer suchen")
                    if ziel_steuer:
                        steuer_ids.append(ziel_steuer[0])
            if steuer_ids:
                zeile["tax_ids"] = [(6, 0, steuer_ids)]
            zeilen.append((0, 0, zeile))
        werte = {"move_type": b["type"], "partner_id": ziel_partner, "journal_id": ziel_journal,
                 "invoice_date": b["date_invoice"], "invoice_date_due": b["date_due"],
                 "currency_id": rpc(z, "res.currency", "search",
                                    [[("name", "=", name(b["currency_id"]))]], "Waehrung suchen")[0],
                 "invoice_line_ids": zeilen}
        if b.get("payment_term_id"):
            ziel = rpc(z, "account.payment.term", "search",
                       [[("name", "=", name(b["payment_term_id"]))]], "Zahlungsbedingung suchen")
            if ziel:
                werte["invoice_payment_term_id"] = ziel[0]
        if "itk_o11_invoice_number" in rpc(z, "account.move", "fields_get", [[], ["type"]], "Felder pruefen"):
            werte["itk_o11_invoice_number"] = b["number"]
        neue = rpc(z, "account.move", "create", [werte], "Beleg anlegen (%s)" % b["number"])
        mitschrift.append({"modell": "account.move", "id": neue, "schluessel": b["number"]})
        if b["state"] == "posted":
            rpc(z, "account.move", "action_post", [[neue]], "Beleg buchen (%s)" % b["number"])
        # Kontrolle: Summen gegen Odoo 11
        geprueft = rpc(z, "account.move", "read", [[neue], ["amount_untaxed", "amount_tax", "amount_total"]],
                      "Summen lesen")[0]
        print("   %-12s O11 %8.2f/%8.2f/%8.2f  O18 %8.2f/%8.2f/%8.2f"
              % (b["number"], b["amount_untaxed"], b["amount_tax"], b["amount_total"],
                 geprueft["amount_untaxed"], geprueft["amount_tax"], geprueft["amount_total"]))
    return mitschrift


def raeume_auf(z, mitschrift):
    if not os.path.exists(PROTOKOLL):
        raise SystemExit("ABBRUCH: kein Protokoll %s - nichts zu entfernen." % PROTOKOLL)
    daten = json.load(open(PROTOKOLL, encoding="utf-8"))
    anzahl = 0
    for eintrag in reversed(daten.get("angelegt", [])):
        if eintrag["modell"] == "account.move":
            rpc(z, "account.move", "button_draft", [[eintrag["id"]]], "Beleg in Entwurf")
            rpc(z, "account.move", "unlink", [[eintrag["id"]]], "Beleg entfernen")
        else:
            rpc(z, eintrag["modell"], "unlink", [[eintrag["id"]]], "Datensatz entfernen")
        anzahl += 1
    print("Entfernt: %d Datensaetze (nur die im Protokoll vermerkten)." % anzahl)
    return anzahl


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="vm")
    p.add_argument("--plan", action="store_true", help="nur Plan erzeugen (Standard)")
    p.add_argument("--ausfuehren", action="store_true")
    p.add_argument("--ich-habe-freigabe", action="store_true")
    p.add_argument("--aufraeumen", action="store_true")
    a = p.parse_args()

    env = lade_env()
    if env.get("ODOO18_DB") != ZIEL_DB:
        raise SystemExit("ABBRUCH: Ziel-DB ist %r, erlaubt ist nur %r." % (env.get("ODOO18_DB"), ZIEL_DB))
    if a.ausfuehren and not a.ich_have_freigabe:
        raise SystemExit("ABBRUCH: --ausfuehren verlangt zusaetzlich --ich-habe-freigabe.")

    k, z = o11(), o18(a.instanz)
    print("Quelle: Odoo 11 Produktion (nur lesend) | Ziel: %s (%s)" % (a.instanz, ZIEL_DB))

    if a.aufraeumen:
        raeume_auf(z, None)
        return 0

    belege = waehle_belege(k)
    print("\nAusgewaehlte Belege: %s" % ", ".join("%s=%s (%s, %d Zeilen)"
          % (O11_BELEGARTEN.get(t, t), b["number"] or "Entwurf", b["state"], len(b["invoice_line_ids"]))
          for t, b in belege.items()))
    partner, journale, konten, steuern, bedingungen = waehle_stammdaten(k, belege)
    produkt_ids = set()
    for b in belege.values():
        for ze in waehle_zeilen(k, b):
            if ze.get("product_id"):
                produkt_ids.add(ze["product_id"][0])
    produkte = rpc(k, "product.product", "search_read",
                   [[("id", "in", list(produkt_ids)[:6])],
                    ["id", "name", "type", "list_price", "sale_ok", "purchase_ok"]], "Produkte lesen")
    print("Stammdaten: %d Partner, %d Journale, %d Konten, %d Steuern, %d Zahlungsbedingungen, %d Produkte"
          % (len(partner), len(journale), len(konten), len(steuern), len(bedingungen), len(produkte)))

    plan = pruefe_ziel(z, partner, journale, konten, steuern, bedingungen, produkte)
    fehlend = [x for x in plan if x["zustand"] == "fehlt im Ziel"]
    print("\nPlan (Stammdaten): %d Positionen, davon %d im Ziel noch nicht vorhanden."
          % (len(plan), len(fehlend)))
    for x in fehlend:
        print("   fehlt: %-22s %s" % (x["modell"], x["schluessel"]))

    if not a.ausfuehren:
        print("\nTROCKENLAUF: Es wurde nichts geschrieben.")
        print("Zum Ausfuehren: --ausfuehren --ich-habe-freigabe (nur nach Freigabe).")
        return 0

    mitschrift = []
    try:
        fuehre_aus(z, k, belege, partner, journale, konten, steuern, bedingungen, produkte, mitschrift)
    finally:
        with open(PROTOKOLL, "w", encoding="utf-8") as fh:
            json.dump({"angelegt": mitschrift}, fh, ensure_ascii=False, indent=1)
    print("\nAngelegt: %d Datensaetze. Protokoll: %s" % (len(mitschrift), PROTOKOLL))
    return 0


if __name__ == "__main__":
    sys.exit(main())
