"""Testmigration Abrechnung: wenige repraesentative Datensaetze Odoo 11 -> Odoo 18 Testinstanz.

Regel und Begruendung: docs/o11-o18-testmigration-regel.md
Stand 05.10.2026 (Session 123). Erstlauf am 05.10.2026 auf der VM durchgefuehrt.

Aufruf:
    python scripts/testmigration_abrechnung.py --instanz vm --plan          (Standard, schreibt nichts)
    python scripts/testmigration_abrechnung.py --instanz vm --ausfuehren --ich-habe-freigabe
    python scripts/testmigration_abrechnung.py --instanz vm --aufraeumen

Grundsaetze:
  - Quelle Odoo 11 wird ausschliesslich gelesen.
  - Ziel darf nur die Testdatenbank sein (ODOO18_DB, geprueft gegen odoo18_test).
  - Beziehungen werden ueber fachliche Schluessel aufgeloest, nie ueber IDs.
  - Jeder Fehler bricht ab (Exit-Code 1), nichts wird still uebersprungen.
  - Erzeugte Datensaetze wandern in ein Protokoll; --aufraeumen loescht nur diese.

Typzuordnung Produkte (Entscheidung Anna 05.10.2026, Variante 1 - siehe
docs/o11-o18-produktart-mapping.md und docs/o11-o18-produktart-pruefung.md):
Odoo 11 fuehrt im Feld `type` auch ITK-Werte (consu, service, general, onlineservice, sw,
consulting, platform, hw, project, product). Die Odoo-18-Auswahl kennt dieselben ITK-Werte
plus combo. Regel:
    consu, service und alle ITK-Werte -> 1:1 uebernehmen (Wert existiert in Odoo 18),
    product -> consu + is_storable (Wert existiert in Odoo 18 nicht, in Odoo 11 nicht belegt).
`is_storable` wird ausschliesslich aus der Odoo-11-Lagerfuehrung abgeleitet
(type in (consu, product) -> is_storable = True, sonst False), niemals aus `type` oder
`product_type_id` abgeleitet.
`product_type_id` wird separat und 1:1 ueber den Namen uebernommen (Zielmodell
itk_product.product_type, gleiche IDs 1-6); bleibt in Odoo 11 leer, bleibt in Odoo 18 leer.
`type` und `product_type_id` werden nicht verschmolzen und nicht gegenseitig abgeleitet.
Der Filter "Dienstleistungen" (`type = service`) behaelt damit dieselbe Treffermenge wie in
Odoo 11 (47 aktive Vorlagen); die sechs "Service Type ..."-Filter haengen weiterhin an
`product_type_id` und bleiben unveraendert.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18  # noqa: E402

ZIEL_DB = "odoo18_test"
PROTOKOLL = os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "Temp",
                         "testmigration_protokoll.json")
CTX = {"lang": "de_DE"}

# Konten-Mapping aus docs/o11-o18-abrechnung-abschlusspruefung.md, Abschnitt 3
KONTO_MAPPING = {"1201": "2801", "1410": "2000", "1776": "3500", "8400": "4000"}
# Punkt 3 (05.10.2026): Der Odoo-11-Journalcode "Re.:" wird NICHT uebernommen. Er erzeugt im
# Ziel unbrauchbare Nummern ("Re.:/2026/00001", bei Gutschriften "RRe.:/2026/00001"). Odoo 11
# hat genau ein Verkaufsjournal; im Ziel heisst es "Kundenrechnungen" mit Code "RE". Das
# Mapping laeuft daher ueber den Journalcode. Die Odoo-11-Rechnungsnummer bleibt in
# itk_o11_invoice_number erhalten, die Odoo-18-Nummer kommt aus der Zielsequenz (Regel K2a/K2b).
JOURNAL_MAPPING = {"Re.:": "RE"}
# Punkt 1 (05.10.2026): Die Odoo-18-Typauswahl des Moduls itk_product kennt dieselben
# ITK-Werte wie Odoo 11 (consu, service, combo, general, onlineservice, sw, consulting,
# platform, hw, project) - nachgewiesen per fields_get auf lokal und VM. Deshalb wird der Typ
# 1:1 uebernommen. KEIN pauschales Umstellen auf service: "general" betrifft allein 273
# Produkte, "platform" 94, "onlineservice" 74, "sw" 9 (Stand 05.10.2026).
# Sonderfall: Odoo 11 kennt zusaetzlich den Typ "product" (Lagerartikel). Den gibt es in
# Odoo 18 nicht; er wird auf consu + is_storable abgebildet (0 Produkte betroffen).
ITK_TYPEN = {"onlineservice", "sw", "consulting", "platform", "hw", "project", "general",
             "combo"}


def rpc(k, modell, methode, args, was, **kwargs):
    try:
        return k.kw(modell, methode, args, **kwargs)
    except Exception as fehler:  # noqa: BLE001
        raise SystemExit("ABBRUCH: %s fehlgeschlagen (%s.%s): %s"
                         % (was, modell, methode, str(fehler)[:300]))


def name(von):
    return von[1] if isinstance(von, (list, tuple)) and len(von) > 1 else None


def typ_ziel(o11_typ):
    """Odoo-11-Typ -> (Odoo-18-Typ, is_storable) nach der Regel im Modulkopf (Variante 1).

    is_storable wird ausschliesslich aus der Odoo-11-Lagerfuehrung abgeleitet
    (type in ('product','consu') -> True), nie aus type oder product_type_id.
    """
    if o11_typ == "product":
        return "consu", True          # Odoo-11-Lagerartikel, in Odoo 18 nicht vorhanden
    if o11_typ == "consu":
        return "consu", True          # 1:1 plus Lagerfuehrung ueber is_storable (Vorgabe Anna)
    if o11_typ == "service" or o11_typ in ITK_TYPEN:
        return o11_typ, False         # 1:1, die Zielauswahl kennt dieselben Werte
    raise SystemExit("ABBRUCH: unbekannter Odoo-11-Produkttyp %r - Zuordnung fehlt." % o11_typ)


# --------------------------------------------------------------------------
# 1. Auswahl in Odoo 11 (nur lesend)
# --------------------------------------------------------------------------
BELEG_FELDER = ["id", "number", "type", "state", "partner_id", "journal_id", "date_invoice",
                "date_due", "payment_term_id", "currency_id", "amount_untaxed", "amount_tax",
                "amount_total", "residual", "invoice_line_ids", "payment_ids", "move_id"]
ZEILEN_FELDER = ["id", "name", "quantity", "price_unit", "discount", "product_id", "account_id",
                 "invoice_line_tax_ids", "account_analytic_id"]


def waehle_belege(k):
    """Je Belegart einen kleinen, mehrzeiligen Beleg; zusaetzlich eine bezahlte Rechnung mit Zahlung."""
    auswahl = {}
    for art, zustaende in (("out_invoice", ["open", "paid"]), ("out_refund", ["paid", "open"])):
        ids = rpc(k, "account.invoice", "search",
                  [[("type", "=", art), ("state", "in", zustaende)], 0, 60],
                  "Belege suchen (%s)" % art)
        treffer = [b for b in rpc(k, "account.invoice", "read", [ids, BELEG_FELDER],
                                  "Belege lesen (%s)" % art)
                   if b["invoice_line_ids"] and len(b["invoice_line_ids"]) <= 10]
        if treffer:
            auswahl[art] = sorted(treffer, key=lambda b: -len(b["invoice_line_ids"]))[0]
    # bezahlte Rechnung samt Zahlung (fuer die Kette Beleg -> Zahlung -> Abstimmung)
    for art in ("in_invoice", "in_refund"):
        if not rpc(k, "account.invoice", "search", [[("type", "=", art)], 0, 5],
                   "Belege suchen (%s)" % art):
            print("   %s: in der Produktion nicht vorhanden (0 Datensaetze)." % art)
    zahlungen = rpc(k, "account.payment", "search_read",
                    [[("invoice_ids", "!=", False)], ["id", "name", "amount", "payment_date",
                                                     "partner_id", "journal_id", "payment_method_id",
                                                     "payment_type", "state", "invoice_ids"]],
                    "Zahlungen lesen", limit=40)
    for p in zahlungen:
        if p["state"] != "posted" or len(p["invoice_ids"]) != 1:
            continue
        b = rpc(k, "account.invoice", "read", [p["invoice_ids"], BELEG_FELDER],
                "Rechnung der Zahlung lesen")[0]
        if (b["invoice_line_ids"] and len(b["invoice_line_ids"]) <= 10
                and b["state"] == "paid" and abs(b["amount_total"] - p["amount"]) < 0.01):
            auswahl["bezahlte_rechnung"] = b
            auswahl["zahlung"] = p
            break
    entwuerfe = rpc(k, "account.invoice", "search",
                    [[("type", "=", "out_invoice"), ("state", "=", "draft")], 0, 30],
                    "Belegentwuerfe suchen")
    if entwuerfe:
        for b in rpc(k, "account.invoice", "read", [entwuerfe, BELEG_FELDER], "Entwuerfe lesen"):
            if b["invoice_line_ids"] and len(b["invoice_line_ids"]) <= 10:
                auswahl["out_invoice_draft"] = b
                break
    # Punkt 6: Belege einbeziehen, gegen die in Odoo 11 abgestimmt wurde. In Odoo 11 kann eine
    # Gutschrift gegen eine Rechnung abgestimmt sein (kein account.payment) - ohne den
    # Gegenbeleg laesst sich dieser Zustand im Ziel nicht herstellen.
    bereits = {b["id"] for s, b in auswahl.items() if s != "zahlung"}
    gegenstuecke = set()
    for s, b in list(auswahl.items()):
        if s == "zahlung" or not b.get("move_id"):
            continue
        meine = rpc(k, "account.move.line", "search", [[("move_id", "=", b["move_id"][0])]],
                    "Buchungszeilen der Rechnung suchen")
        for ze in rpc(k, "account.move.line", "read", [meine, ["full_reconcile_id"]],
                      "Abstimmung lesen"):
            if not ze["full_reconcile_id"]:
                continue
            partner_zeilen = rpc(k, "account.move.line", "search",
                                 [[("full_reconcile_id", "=", ze["full_reconcile_id"][0]),
                                   ("id", "not in", meine)]], "Gegenzeilen suchen")
            for gz in rpc(k, "account.move.line", "read", [partner_zeilen, ["move_id"]],
                          "Gegenzeilen lesen"):
                andere = rpc(k, "account.invoice", "search", [[("move_id", "=", gz["move_id"][0])]],
                             "Gegenbeleg suchen")
                if andere and andere[0] not in bereits:
                    gegenstuecke.add(andere[0])
    for gid in sorted(gegenstuecke):
        b = rpc(k, "account.invoice", "read", [[gid], BELEG_FELDER], "Gegenbeleg lesen")[0]
        if b["invoice_line_ids"] and len(b["invoice_line_ids"]) <= 10 and \
                b["type"] in ("out_invoice", "out_refund"):
            auswahl["gegenbeleg_%s" % gid] = b
            print("   Gegenbeleg einbezogen: %s (%s, %d Zeilen, gegen den ausgewaehlten Beleg "
                  "abgestimmt)" % (b["number"], b["type"], len(b["invoice_line_ids"])))
    return auswahl


def waehle_zeilen(k, beleg):
    return rpc(k, "account.invoice.line", "read", [beleg["invoice_line_ids"], ZEILEN_FELDER],
               "Belegzeilen lesen")


def sammle_zeilen(k, belege):
    return {t: (waehle_zeilen(k, b) if t != "zahlung" else []) for t, b in belege.items()}


def waehle_stammdaten(k, belege, zeilen):
    partner_ids, journal_ids, konto_ids, steuer_ids, bedingung_ids, produkt_ids = (set() for _ in range(6))
    for t, b in belege.items():
        if t == "zahlung":
            if b.get("partner_id"):
                partner_ids.add(b["partner_id"][0])
            if b.get("journal_id"):
                journal_ids.add(b["journal_id"][0])
            continue
        for feld, sammlung in (("partner_id", partner_ids), ("journal_id", journal_ids),
                               ("payment_term_id", bedingung_ids)):
            if b.get(feld):
                sammlung.add(b[feld][0])
        for z in zeilen[t]:
            if z.get("account_id"):
                konto_ids.add(z["account_id"][0])
            if z.get("product_id"):
                produkt_ids.add(z["product_id"][0])
            steuer_ids.update(z.get("invoice_line_tax_ids") or [])
    partner = rpc(k, "res.partner", "read", [sorted(partner_ids),
                                             ["id", "name", "is_company", "vat", "street", "street2",
                                              "zip", "city", "lang", "country_id", "customer",
                                              "supplier", "property_payment_term_id", "ref", "email",
                                              "phone", "community_salutation", "community_magnitude",
                                              "commercial_company_name"]], "Partner lesen")
    journale = rpc(k, "account.journal", "read", [sorted(journal_ids), ["id", "name", "code", "type"]],
                   "Journale lesen")
    konten = rpc(k, "account.account", "read", [sorted(konto_ids), ["id", "code", "name"]], "Konten lesen")
    steuern = (rpc(k, "account.tax", "read", [sorted(steuer_ids),
                                              ["id", "name", "amount", "amount_type", "type_tax_use",
                                               "tax_group_id"]], "Steuern lesen") if steuer_ids else [])
    bedingungen = (rpc(k, "account.payment.term", "read", [sorted(bedingung_ids), ["id", "name"]],
                       "Zahlungsbedingungen lesen") if bedingung_ids else [])
    produkte = rpc(k, "product.product", "read", [sorted(produkt_ids),
                                                  ["id", "name", "type", "list_price", "sale_ok",
                                                   "purchase_ok", "product_type_id", "invoice_policy",
                                                   "taxes_id", "supplier_taxes_id"]], "Produkte lesen")
    return partner, journale, konten, steuern, bedingungen, produkte


# --------------------------------------------------------------------------
# 2. Plan gegen die Zielinstanz pruefen (nur lesend)
# --------------------------------------------------------------------------
def pruefe_ziel(z, partner, journale, konten, steuern, bedingungen, produkte):
    plan = []
    def pruefe(modell, feld, wert, was):
        treffer = rpc(z, modell, "search_count", [[(feld, "=", wert)]], "Zielpruefung %s %r" % (modell, wert))
        if treffer > 1:
            raise SystemExit("ABBRUCH: Schluessel %r ist in %s nicht eindeutig (%d Treffer)."
                             % (wert, modell, treffer))
        plan.append({"modell": modell, "schluessel": wert,
                     "zustand": "vorhanden" if treffer else "fehlt im Ziel", "was": was})
    for p in partner:
        pruefe("res.partner", "name", p["name"], "Partner")
    for j in journale:
        # Punkt 3: Abbildung des Odoo-11-Codes auf das Zieljournal
        pruefe("account.journal", "code", JOURNAL_MAPPING.get(j["code"], j["code"]),
               "Journal (Odoo 11: %s)" % j["code"])
    for K in konten:
        code = KONTO_MAPPING.get(str(K["code"]), str(K["code"]))
        pruefe("account.account", "code", code, "Konto (gemappt von %s)" % K["code"])
    for s in steuern:
        pruefe("account.tax", "name", s["name"], "Steuer %s %s%%" % (s["name"], s["amount"]))
    for b in bedingungen:
        pruefe("account.payment.term", "name", b["name"], "Zahlungsbedingung")
    for pr in produkte:
        pruefe("product.template", "name", pr["name"], "Produkt")
    return plan


# --------------------------------------------------------------------------
# 3. Ausfuehren (nur mit --ausfuehren --ich-habe-freigabe)
# --------------------------------------------------------------------------
def lege_an(mitschrift, z, modell, werte, feld, wert, was):
    vorhanden = rpc(z, modell, "search", [[(feld, "=", wert)]], "Suche %s %r" % (modell, wert))
    if vorhanden:
        # Bereits vorhanden (z. B. Wiederholung nach einem Abbruch): nur vormerken, nicht loeschen.
        mitschrift.append({"modell": modell, "id": vorhanden[0], "schluessel": wert, "neu": False})
        return vorhanden[0]
    neue = rpc(z, modell, "create", [werte], "Anlegen %s (%s)" % (modell, was))
    mitschrift.append({"modell": modell, "id": neue, "schluessel": wert, "neu": True})
    print("   angelegt: %-22s id=%-6s %s" % (modell, neue, wert))
    return neue


def hole_steuergruppe(z, steuer):
    """Steuergruppe im Ziel: gleicher Name, sonst Gruppe einer 20%-Verkaufssteuer."""
    if steuer.get("tax_group_id"):
        gleich = rpc(z, "account.tax.group", "search", [[("name", "=", name(steuer["tax_group_id"]))]],
                     "Steuergruppe suchen")
        if gleich:
            return gleich[0]
    vorhandene = rpc(z, "account.tax", "search", [[("amount", "=", steuer["amount"]),
                                                   ("type_tax_use", "=", steuer["type_tax_use"]),
                                                   ("tax_group_id", "!=", False)]], "Steuer suchen", limit=1)
    if vorhandene:
        return rpc(z, "account.tax", "read", [vorhandene, ["tax_group_id"]], "Steuergruppe lesen")[0]["tax_group_id"][0]
    gruppen = rpc(z, "account.tax.group", "search", [[]], "Steuergruppen suchen", limit=1)
    if not gruppen:
        raise SystemExit("ABBRUCH: im Ziel existiert keine Steuergruppe.")
    return gruppen[0]


def fuehre_aus(z, k, belege, zeilen, partner, journale, konten, steuern, bedingungen, produkte,
               mitschrift):
    # --- Stammdaten in der dokumentierten Reihenfolge -----------------------
    # Journale werden NICHT angelegt: die Odoo-11-Journale werden ueber JOURNAL_MAPPING auf die
    # vorhandenen Zieljournale abgebildet (Punkt 3).
    for s in steuern:
        lege_an(mitschrift, z, "account.tax",
                {"name": s["name"], "amount": s["amount"], "amount_type": s["amount_type"],
                 "type_tax_use": s["type_tax_use"], "tax_group_id": hole_steuergruppe(z, s)},
                "name", s["name"], "Steuer")
    for b in bedingungen:
        lege_an(mitschrift, z, "account.payment.term", {"name": b["name"]}, "name", b["name"],
                "Zahlungsbedingung")
    ziel_partner_felder = rpc(z, "res.partner", "fields_get", [[], ["type"]], "Partnerfelder lesen")
    for p in partner:
        # Punkt 2 (05.10.2026): Odoo 11 zeigt den Partner als "[ref] community_salutation"
        # (z. B. "[20609] Marktgemeinde Greifenburg"), das Feld `name` enthaelt nur "Greifenburg".
        # Odoo 18 bildet diese Zusammensetzung nicht nach - ohne Regel verliert der Kunde seine
        # sichtbare Bezeichnung. Deshalb: sichtbarer Name = community_salutation, sonst name.
        # Der Kurzname bleibt in `name`... -> siehe commercial_company_name, `ref` bleibt `ref`.
        sichtbarer_name = p.get("community_salutation") or p["name"]
        werte = {"name": sichtbarer_name, "is_company": p["is_company"], "vat": p["vat"] or False,
                 "street": p["street"] or False, "street2": p["street2"] or False,
                 "zip": p["zip"] or False, "city": p["city"] or False,
                 "lang": p["lang"] or "de_DE",
                 "customer_rank": 1 if p.get("customer") else 0,
                 "supplier_rank": 1 if p.get("supplier") else 0}
        # ITK-Partnerfelder mitnehmen, sonst geht die sichtbare Organisationsbezeichnung verloren
        # (Befund 05.10.2026: Odoo 11 zeigt "[20609] Marktgemeinde Greifenburg", das Feld `name`
        #  enthaelt nur "Greifenburg").
        # Kurznamen aus Odoo 11 getrennt festhalten, damit nichts verloren geht
        if "commercial_company_name" in ziel_partner_felder and p.get("name"):
            werte["commercial_company_name"] = p["name"]
        for feld in ("ref", "email", "phone", "community_salutation", "community_magnitude"):
            if feld in ziel_partner_felder and p.get(feld):
                werte[feld] = p[feld]
        if p.get("country_id"):
            land = rpc(k, "res.country", "read", [[p["country_id"][0]], ["code"]], "Land lesen")[0]["code"]
            treffer = rpc(z, "res.country", "search", [[("code", "=", land)]], "Land suchen")
            if not treffer:
                raise SystemExit("ABBRUCH: Land %s fehlt im Ziel." % land)
            werte["country_id"] = treffer[0]
        lege_an(mitschrift, z, "res.partner", werte, "name", sichtbarer_name, "Partner")
    for pr in produkte:
        ziel_typ, storable = typ_ziel(pr["type"])
        werte = {"name": pr["name"], "type": ziel_typ, "list_price": pr["list_price"],
                 "sale_ok": pr["sale_ok"], "purchase_ok": pr["purchase_ok"]}
        if storable is not None:
            werte["is_storable"] = storable
        if pr.get("invoice_policy"):
            werte["invoice_policy"] = pr["invoice_policy"]
        if pr.get("product_type_id"):
            treffer = rpc(z, "itk_product.product_type", "search",
                          [[("name", "=", name(pr["product_type_id"]))]], "Produkttyp suchen")
            if not treffer:
                raise SystemExit("ABBRUCH: Produkttyp %r fehlt im Ziel." % name(pr["product_type_id"]))
            werte["product_type_id"] = treffer[0]
        if pr.get("taxes_id"):
            s = next((x for x in steuern if x["id"] == pr["taxes_id"][0]), None)
            if s:
                treffer = rpc(z, "account.tax", "search", [[("name", "=", s["name"])]], "Steuer suchen")
                if treffer:
                    werte["taxes_id"] = [(6, 0, treffer)]
        lege_an(mitschrift, z, "product.template", werte, "name", pr["name"], "Produkt")

    # --- Belege -------------------------------------------------------------
    journal_code = {j["id"]: j["code"] for j in journale}
    # Wichtig: der m2o-Anzeigename aus Odoo 11 traegt Praefixe (z. B.
    # "[Gemeindeverband Karnische Region] Gemeindeverband Karnische Region").
    # Aufgeloest wird ueber den echten Satznamen aus dem gelesenen Datensatz.
    # Punkt 2: derselbe sichtbare Name wie beim Anlegen (community_salutation, sonst name)
    partner_name = {p["id"]: (p.get("community_salutation") or p["name"]) for p in partner}
    produkt_name = {pr["id"]: pr["name"] for pr in produkte}
    neue_belege = {}
    for t, b in belege.items():
        if t == "zahlung":
            continue
        ziel_partner = rpc(z, "res.partner", "search",
                           [[("name", "=", partner_name[b["partner_id"][0]])]], "Partner suchen")
        journal_ziel_code = JOURNAL_MAPPING.get(journal_code[b["journal_id"][0]],
                                                journal_code[b["journal_id"][0]])
        ziel_journal = rpc(z, "account.journal", "search",
                           [[("code", "=", journal_ziel_code)]], "Journal suchen")
        if not ziel_journal:
            raise SystemExit("ABBRUCH: Zieljournal mit Code %r fehlt." % journal_ziel_code)
        if not ziel_partner or not ziel_journal:
            raise SystemExit("ABBRUCH: Partner oder Journal fuer %s fehlt im Ziel." % b["number"])
        zeilen_werte = []
        for z_ in zeilen[t]:
            wz = {"name": z_["name"], "quantity": z_["quantity"], "price_unit": z_["price_unit"],
                  "discount": z_["discount"] or 0.0}
            if z_.get("product_id"):
                treffer = rpc(z, "product.product", "search",
                              [[("name", "=", produkt_name[z_["product_id"][0]])]], "Produkt suchen")
                if treffer:
                    wz["product_id"] = treffer[0]
            if z_.get("account_id"):
                alt = str(z_["account_id"][1]).split()[0]
                code = KONTO_MAPPING.get(alt, alt)
                treffer = rpc(z, "account.account", "search", [[("code", "=", code)]], "Konto suchen")
                if not treffer:
                    raise SystemExit("ABBRUCH: Konto %s (Odoo 11: %s) fehlt im Ziel."
                                     % (code, z_["account_id"][1]))
                wz["account_id"] = treffer[0]
            steuer_ids = []
            for t_ in (z_.get("invoice_line_tax_ids") or []):
                s = next((x for x in steuern if x["id"] == t_), None)
                if s:
                    treffer = rpc(z, "account.tax", "search", [[("name", "=", s["name"])]], "Steuer suchen")
                    if treffer:
                        steuer_ids.append(treffer[0])
            if steuer_ids:
                wz["tax_ids"] = [(6, 0, steuer_ids)]
            zeilen_werte.append((0, 0, wz))
        werte = {"move_type": b["type"], "partner_id": ziel_partner[0], "journal_id": ziel_journal[0],
                 "invoice_date": b["date_invoice"], "invoice_date_due": b["date_due"],
                 "currency_id": rpc(z, "res.currency", "search",
                                    [[("name", "=", name(b["currency_id"]))]], "Waehrung suchen")[0],
                 "invoice_line_ids": zeilen_werte}
        if b.get("payment_term_id"):
            treffer = rpc(z, "account.payment.term", "search",
                          [[("name", "=", name(b["payment_term_id"]))]], "Zahlungsbedingung suchen")
            if treffer:
                werte["invoice_payment_term_id"] = treffer[0]
        werte["itk_o11_invoice_number"] = b["number"] or ""
        # Doppelanlage bei Wiederholung verhindern: erst ueber die Odoo-11-Nummer suchen,
        # bei Entwuerfen (ohne Nummer) ueber Partner + Art + Datum.
        vorhanden = rpc(z, "account.move", "search", [[("itk_o11_invoice_number", "=", b["number"])]],
                        "Beleg suchen (Odoo-11-Nummer)") if b["number"] else []
        if not vorhanden:
            vorhanden = rpc(z, "account.move", "search",
                            [[("partner_id", "=", ziel_partner[0]), ("move_type", "=", b["type"]),
                              ("invoice_date", "=", b["date_invoice"]), ("state", "=", "draft")]],
                            "Beleg suchen (Entwurf)")
        if vorhanden:
            neue = vorhanden[0]
            mitschrift.append({"modell": "account.move", "id": neue, "schluessel": b["number"],
                               "neu": False})
            print("   Beleg %-12s ist im Ziel bereits vorhanden (id=%s) - nicht erneut angelegt."
                  % (b["number"] or "Entwurf", neue))
        else:
            neue = rpc(z, "account.move", "create", [werte], "Beleg anlegen (%s)" % b["number"])
            mitschrift.append({"modell": "account.move", "id": neue, "schluessel": b["number"],
                               "neu": True})
        neue_belege[t] = {"id": neue, "quelle": b}
        if b["state"] in ("open", "paid"):
            ist_zustand = rpc(z, "account.move", "read", [[neue], ["state"]], "Zustand lesen")[0]["state"]
            if ist_zustand == "draft":
                rpc(z, "account.move", "action_post", [[neue]], "Beleg buchen (%s)" % b["number"])
            else:
                print("   Beleg %-12s ist bereits im Zustand %s." % (b["number"], ist_zustand))
        geprueft = rpc(z, "account.move", "read",
                       [[neue], ["name", "state", "amount_untaxed", "amount_tax", "amount_total",
                                 "amount_residual", "payment_state", "itk_o11_invoice_number"]],
                       "Beleg gegenlesen")[0]
        print("   Beleg %-12s O11 %8.2f/%8.2f/%8.2f  O18 %8.2f/%8.2f/%8.2f  Zustand %s Zahlung %s"
              % (b["number"], b["amount_untaxed"], b["amount_tax"], b["amount_total"],
                 geprueft["amount_untaxed"], geprueft["amount_tax"], geprueft["amount_total"],
                 geprueft["state"], geprueft["payment_state"]))
        print("        Odoo-11-Nummer im Ziel: %r | Odoo-18-Nummer: %s"
              % (geprueft["itk_o11_invoice_number"], geprueft["name"]))

    # --- Zahlung mit Abstimmung --------------------------------------------
    if "zahlung" in belege and "bezahlte_rechnung" in neue_belege:
        p = belege["zahlung"]
        ziel_journal = rpc(z, "account.journal", "search",
                           [[("code", "=", journal_code[p["journal_id"][0]])]], "Journal suchen")
        methode = rpc(z, "account.payment.method.line", "search_read",
                      [[("journal_id", "=", ziel_journal[0]), ("payment_type", "=", "inbound")],
                       ["id", "name"]], "Zahlungsart suchen")
        if not ziel_journal or not methode:
            raise SystemExit("ABBRUCH: Journal oder Zahlungsart fuer die Zahlung fehlt im Ziel.")
        partner_id = rpc(z, "res.partner", "search", [[("name", "=", partner_name[p["partner_id"][0]])]],
                         "Partner suchen")[0]
        # Zahlung idempotent ueber die Odoo-11-Zahlungsnummer im Herkunftsfeld
        # (Punkt 4: account.payment.itk_o11_payment_number existiert im Modul
        # itk_account_migration und ist auf lokal und VM installiert).
        vorhandene_zahlung = rpc(z, "account.payment", "search",
                                 [[("itk_o11_payment_number", "=", p["name"])]], "Zahlung suchen")
        if vorhandene_zahlung:
            zahlung_id = vorhandene_zahlung[0]
            mitschrift.append({"modell": "account.payment", "id": zahlung_id,
                               "schluessel": p["name"], "neu": False})
            print("   Zahlung %s ist im Ziel bereits vorhanden (id=%s)." % (p["name"], zahlung_id))
        else:
            werte = {"payment_type": "inbound", "partner_type": "customer", "partner_id": partner_id,
                     "amount": p["amount"], "date": p["payment_date"],
                     "journal_id": ziel_journal[0], "payment_method_line_id": methode[0]["id"],
                     "memo": p["name"], "itk_o11_payment_number": p["name"]}
            zahlung_id = rpc(z, "account.payment", "create", [werte], "Zahlung anlegen (%s)" % p["name"])
            mitschrift.append({"modell": "account.payment", "id": zahlung_id,
                               "schluessel": p["name"], "neu": True})
            rpc(z, "account.payment", "action_post", [[zahlung_id]], "Zahlung buchen")
        print("   Zahlung %-18s %8.2f angelegt und gebucht (Abstimmung folgt im Nachlauf)."
              % (p["name"], p["amount"]))

    # Punkt 5: Abstimmungen erst nach allen Belegen und Zahlungen herstellen
    stelle_ab(z, k, belege, neue_belege, mitschrift)
    return mitschrift


def versuche_abstimmung(z, zeilen, was):
    """Abstimmung setzen; ist sie schon vorhanden, ist das kein Fehler.

    Die harte Pruefung passiert anschliessend in der Gegenpruefung Zustand/Restbetrag.
    """
    try:
        rpc(z, "account.move.line", "reconcile", [zeilen], was)
    except SystemExit as fehler:
        print("      Hinweis (%s): %s" % (was, str(fehler)[:140]))


def forderungszeilen(z, move_id, was):
    """Alle Forderungszeilen einer Buchung im Ziel."""
    return rpc(z, "account.move.line", "search",
               [[("move_id", "=", move_id), ("account_id.account_type", "=", "asset_receivable")]],
               was)


def stelle_ab(z, k, belege, neue_belege, mitschrift):
    """Nachlauf: Abstimmungen wie in Odoo 11 herstellen und 1:1 gegenpruefen.

    Zwei Wege, beide aus Odoo 11 abgeleitet - es wird nichts kuenstlich erzeugt:
      a) Zahlung <-> Rechnung: ueber account.payment.invoice_ids in Odoo 11
      b) Beleg <-> Beleg: Belege, die in Odoo 11 dieselbe Abstimmung (full_reconcile_id) teilen
    """
    print("\n   Nachlauf: Abstimmungen herstellen")
    o11_zu_o18 = {}
    for s, b in belege.items():
        if s in neue_belege:
            o11_zu_o18[b["id"]] = neue_belege[s]["id"]

    # a) Zahlungen
    if "zahlung" in belege:
        p = belege["zahlung"]
        ziel_zahlungen = rpc(z, "account.payment", "search",
                             [[("itk_o11_payment_number", "=", p["name"])]], "Zahlung suchen")
        if not ziel_zahlungen:
            raise SystemExit("ABBRUCH: Zahlung %s nicht im Ziel gefunden." % p["name"])
        z_move = rpc(z, "account.payment", "read", [[ziel_zahlungen[0]], ["move_id"]],
                     "Zahlungsbuchung lesen")[0]["move_id"][0]
        zeilen = forderungszeilen(z, z_move, "Forderungszeile der Zahlung suchen")
        for iid in p["invoice_ids"]:
            if iid in o11_zu_o18:
                zeilen += forderungszeilen(z, o11_zu_o18[iid], "Forderungszeile der Rechnung suchen")
        if len(zeilen) < 2:
            raise SystemExit("ABBRUCH: fuer die Zahlung wurden nur %d Forderungszeilen gefunden."
                             % len(zeilen))
        versuche_abstimmung(z, zeilen, "Zahlung abstimmen")
        print("   Zahlung %s mit Rechnung abgestimmt." % p["name"])

    # b) Belegpaare ueber die Odoo-11-Abstimmung
    gruppen = {}
    for o11_id in o11_zu_o18:
        b = rpc(k, "account.invoice", "read", [[o11_id], ["move_id"]], "Buchung lesen")[0]
        if not b["move_id"]:
            continue
        meine = rpc(k, "account.move.line", "search", [[("move_id", "=", b["move_id"][0])]],
                    "Buchungszeilen suchen")
        for ze in rpc(k, "account.move.line", "read", [meine, ["full_reconcile_id"]],
                      "Abstimmung lesen"):
            if ze["full_reconcile_id"]:
                gruppen.setdefault(ze["full_reconcile_id"][0], set()).add(o11_id)
    for gid, ids in gruppen.items():
        ziel_ids = [o11_zu_o18[i] for i in ids if i in o11_zu_o18]
        if len(ziel_ids) < 2:
            continue
        zeilen = []
        for mid in ziel_ids:
            zeilen += forderungszeilen(z, mid, "Forderungszeilen suchen")
        if len(zeilen) >= 2:
            versuche_abstimmung(z, zeilen, "Belegpaar abstimmen")
            print("   Belegpaar abgestimmt: %s" % ", ".join(
                str(belege[s]["number"]) for s, b in belege.items()
                if s in neue_belege and belege[s]["id"] in ids))

    # Gegenpruefung 1:1 gegen Odoo 11
    print("   Gegenpruefung Zustand/Restbetrag gegen Odoo 11:")
    for s, b in belege.items():
        if s not in neue_belege:
            continue
        zustand = rpc(z, "account.move", "read",
                      [[neue_belege[s]["id"]], ["name", "state", "payment_state",
                                               "amount_residual"]], "Zustand lesen")[0]
        # Erwartung aus dem Odoo-11-Restbetrag ableiten (payment_state in Odoo 18)
        if b["state"] == "draft":
            erwartet = "draft"
        elif abs(b["residual"]) < 0.01:
            erwartet = "paid"
        elif abs(b["residual"] - b["amount_total"]) < 0.01:
            erwartet = "not_paid"
        else:
            erwartet = "partial"
        ist = zustand["payment_state"] if zustand["state"] == "posted" else "draft"
        # Entwuerfe haben in Odoo 11 keinen Restbetrag; dort zaehlt nur der Zustand.
        # Odoo 18 fuehrt eine voll gutgeschriebene Rechnung als "Gutgeschrieben" (reversed),
        # Odoo 11 zeigte "Bezahlt". Fachlich derselbe Zustand (Rest 0) - dokumentierte
        # Abweichung in der Bezeichnung.
        gutgeschrieben = (erwartet == "paid" and ist == "reversed")
        ok = (ist == erwartet or gutgeschrieben) and (erwartet == "draft"
                                   or abs(zustand["amount_residual"] - b["residual"]) < 0.01)
        if gutgeschrieben:
            print("        (Odoo 18 zeigt 'Gutgeschrieben' statt 'Bezahlt')")
        print("      %-12s Odoo 11 %-6s Rest %8.2f | Odoo 18 %-8s Rest %8.2f  %s"
              % (b["number"] or "Entwurf", b["state"], b["residual"], ist,
                 zustand["amount_residual"], "OK" if ok else "ABWEICHUNG"))
        if not ok:
            raise SystemExit("ABBRUCH: Zustand des Belegs %s weicht von Odoo 11 ab."
                             % (b["number"] or "Entwurf"))


def raeume_auf(z):
    if not os.path.exists(PROTOKOLL):
        raise SystemExit("ABBRUCH: kein Protokoll %s - nichts zu entfernen." % PROTOKOLL)
    daten = json.load(open(PROTOKOLL, encoding="utf-8"))
    eintraege = [e for e in reversed(daten.get("angelegt", [])) if e.get("neu", True)]
    # Mehrfachlaeufe vermerken denselben Datensatz mehrfach -> eindeutig machen.
    gesehen, eindeutig = set(), []
    for e in eintraege:
        schluessel = (e["modell"], e["id"])
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        eindeutig.append(e)
    eintraege = eindeutig
    anzahl, fehlend = 0, 0

    def weg(modell, eintrag, vortext=None):
        """Loescht einen Datensatz; fehlt er schon, wird das nur vermerkt."""
        nonlocal anzahl, fehlend
        if not rpc(z, modell, "search", [[("id", "=", eintrag["id"])]], "Existenz pruefen"):
            fehlend += 1
            return
        if vortext:
            try:
                rpc(z, modell, vortext, [[eintrag["id"]]], "Vorbereiten %s" % modell)
            except SystemExit as f:
                print("   Hinweis: %s" % str(f)[:160])
        rpc(z, modell, "unlink", [[eintrag["id"]]], "Datensatz entfernen (%s)" % modell)
        anzahl += 1

    for e in eintraege:
        if e["modell"] == "account.payment":
            weg("account.payment", e, "action_draft")
    for e in eintraege:
        if e["modell"] == "account.move":
            weg("account.move", e, "button_draft")
    for e in eintraege:
        if e["modell"] not in ("account.move", "account.payment"):
            weg(e["modell"], e)
    print("Entfernt: %d Datensaetze (nur die im Protokoll vermerkten); %d waren bereits weg."
          % (anzahl, fehlend))
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
    if a.ausfuehren and not a.ich_habe_freigabe:
        raise SystemExit("ABBRUCH: --ausfuehren verlangt zusaetzlich --ich-habe-freigabe.")

    k, z = o11(), o18(a.instanz)
    print("Quelle: Odoo 11 Produktion (nur lesend) | Ziel: %s (%s)" % (a.instanz, ZIEL_DB))

    if a.aufraeumen:
        raeume_auf(z)
        return 0

    belege = waehle_belege(k)
    zeilen = sammle_zeilen(k, belege)
    print("\nAusgewaehlte Datensaetze:")
    for t, b in belege.items():
        if t == "zahlung":
            print("   %-20s %s, %.2f, %s" % (t, b["name"], b["amount"], b["payment_date"]))
        else:
            print("   %-20s %-12s %-8s %6d Zeilen, brutto %.2f, Rest %.2f"
                  % (t, b["number"] or "Entwurf", b["state"], len(b["invoice_line_ids"]),
                     b["amount_total"], b["residual"]))
    partner, journale, konten, steuern, bedingungen, produkte = waehle_stammdaten(k, belege, zeilen)
    print("Stammdaten: %d Partner, %d Journale, %d Konten, %d Steuern, %d Zahlungsbedingungen, %d Produkte"
          % (len(partner), len(journale), len(konten), len(steuern), len(bedingungen), len(produkte)))
    for pr in produkte:
        print("   Produkt %-58s O11-Typ %-14s -> O18 %s%s" % (
            pr["name"][:58], pr["type"], typ_ziel(pr["type"])[0],
            " + is_storable" if typ_ziel(pr["type"])[1] else ""))

    plan = pruefe_ziel(z, partner, journale, konten, steuern, bedingungen, produkte)
    fehlend = [x for x in plan if x["zustand"] == "fehlt im Ziel"]
    print("\nPlan: %d Positionen, davon %d im Ziel noch nicht vorhanden." % (len(plan), len(fehlend)))
    for x in fehlend:
        print("   fehlt: %-22s %-30s %s" % (x["modell"], x["schluessel"][:30], x["was"]))

    if not a.ausfuehren:
        print("\nTROCKENLAUF: Es wurde nichts geschrieben.")
        print("Zum Ausfuehren: --ausfuehren --ich-habe-freigabe (nur nach Freigabe).")
        return 0

    mitschrift = []
    if os.path.exists(PROTOKOLL):
        alt = json.load(open(PROTOKOLL, encoding="utf-8")).get("angelegt", [])
        # Nur noch existierende Eintraege uebernehmen (nach einem Aufraeumen sind sie weg).
        offen = []
        for e in alt:
            if e.get("neu", True) and not rpc(z, e["modell"], "search",
                                              [[("id", "=", e["id"])]], "Existenz pruefen"):
                continue
            offen.append(e)
        mitschrift.extend(offen)
        print("\nHinweis: %d von %d Eintraegen aus einem frueheren Lauf noch vorhanden."
              % (len(offen), len(alt)))
    try:
        fuehre_aus(z, k, belege, zeilen, partner, journale, konten, steuern, bedingungen, produkte,
                   mitschrift)
    finally:
        with open(PROTOKOLL, "w", encoding="utf-8") as fh:
            json.dump({"angelegt": mitschrift}, fh, ensure_ascii=False, indent=1)
    print("\nAngelegt: %d Datensaetze. Protokoll: %s" % (len(mitschrift), PROTOKOLL))
    return 0


if __name__ == "__main__":
    sys.exit(main())
