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

# --------------------------------------------------------------------------
# Entschiedene Kontenzuordnungen (Anna, Session 131)
# --------------------------------------------------------------------------
# Ausgangslage (belegt, siehe docs/o11-o18-abrechnung-kontenzuordnung-8400-3400.md):
# 8400 "Erloese 19% USt" und 3400 "Wareneingang 19% Vorsteuer" sind in Odoo 11
# ausschliesslich globale Firmenvorgaben der Produktkategorien (ir.property, res_id leer;
# keine Kategorie hat ein eigenes Konto). Odoo 11 fuehrt 1.286 Konten, das Ziel 240.
#
# Entschieden (Anna):
#   * 8400 "Erloese 19% USt" (Typ Erloese, 10.040 Belegzeilen in Odoo 11), Entscheidung 08.10.2026
#     -> 4000 "Brutto-Umsatzerloese im Inland (20%)" (Typ income, 39 Belegzeilen im Ziel).
#     Begruendung: das Mapping ist fuer die Belegzeilen bereits dokumentiert (KONTO_MAPPING,
#     docs/o11-o18-abrechnung-abschlusspruefung.md Abschnitt 3) und gilt auch fuer die globale
#     Firmenvorgabe der Kategorien - nicht pro Kategorie.
#   * 3400 "Wareneingang 19% Vorsteuer" (Typ Aufwand, 0 Belegzeilen, von keiner Steuer
#     referenziert), Entscheidung 08.10.2026
#     -> 5010 "Wareneinkauf 20%", also die im Ziel bereits gesetzte globale Firmenvorgabe.
#     Begruendung: keine historischen Buchungen, aus denen eine andere Zuordnung folgen wuerde;
#     5010 ist fachlich naeher an "Wareneingang/Wareneinkauf" als 5000 "Wareneinsatz"; es wird
#     ausdruecklich KEIN neues Konto mit 19%-Bezeichnung angelegt und KEIN Mapping auf 5000
#     erzwungen; die Produktkategorien erben die firmenweite Odoo-18-Vorgabe.
#
# Beide Zuordnungen werden ueber Nummer UND Namen geprueft; Konten werden nie angelegt.
ENTSCHEIDUNGEN_KONTEN = {
    "8400": {
        "ziel_code": "4000",
        "ziel_name": "Brutto-Umsatzerlöse im Inland (20%)",
        "entscheidung": "Anna, 08.10.2026",
        "begruendung": ("Belegzeilen-Mapping 8400 -> 4000 gilt auch fuer die globale "
                        "Firmenvorgabe der Produktkategorien"),
    },
    "3400": {
        "ziel_code": "5010",
        "ziel_name": "Wareneinkauf 20%",
        "entscheidung": "Anna, 08.10.2026",
        "begruendung": ("bestehende globale Odoo-18-Aufwandsvorgabe beibehalten: Odoo-11-Konto hatte "
                        "0 Belegzeilen und diente nur als Firmenvorgabe; kein neues Konto, kein "
                        "Mapping auf 5000, keine kategoriespezifischen Konten"),
    },
}
# Punkt 3 (05.10.2026): Der Odoo-11-Journalcode "Re.:" wird NICHT uebernommen. Er erzeugt im
# Ziel unbrauchbare Nummern ("Re.:/2026/00001", bei Gutschriften "RRe.:/2026/00001"). Odoo 11
# hat genau ein Verkaufsjournal; im Ziel heisst es "Kundenrechnungen" mit Code "RE". Das
# Mapping laeuft daher ueber den Journalcode. Die Odoo-11-Rechnungsnummer bleibt in
# itk_o11_invoice_number erhalten, die Odoo-18-Nummer kommt aus der Zielsequenz (Regel K2a/K2b).
JOURNAL_MAPPING = {"Re.:": "RE"}

# Blocker-Sammelliste (Session 129): Odoo-11-Konten der Produktkategorien ohne eindeutige
# Entsprechung im Ziel. Es wird nichts angelegt und nichts geraten - der Lauf weist den Punkt
# ausdruecklich aus (siehe docs/o11-o18-produktkategorien-mapping.md, Abschnitt 5).
BLOCKER_KONTEN = []

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

# Produktfelder fuer die Testmigration (Session 129 erweitert; Entscheidung Anna:
# supplier_taxes_id, default_code, uom_id/uom_po_id, categ_id, standard_price ergaenzen).
PRODUKT_FELDER = ["id", "name", "type", "list_price", "sale_ok", "purchase_ok", "product_type_id",
                  "invoice_policy", "taxes_id", "supplier_taxes_id", "default_code", "standard_price",
                  "uom_id", "uom_po_id", "categ_id"]

# Beide Seiten werden mit derselben Sprache gelesen und gesucht. Wichtig fuer die Zuordnung
# ueber Namen: ohne Kontext liefert Odoo 11 englische Anzeigenamen ("Unit(s)"), waehrend die
# Zielinstanz deutsche Namen fuehrt ("Einheit(en)") - die Zuordnung wuerde dann scheitern.
CTX = {"lang": "de_DE"}


def zeige(wert):
    """Anzeigename eines m2o-Wertes ([id, name]) oder der Wert selbst."""
    if isinstance(wert, (list, tuple)) and len(wert) > 1:
        return wert[1]
    return wert


def steuer_im_ziel(z, steuer11):
    """Odoo-11-Steuer im Odoo-18-Ziel bestimmen - fachlich, ohne ID-Uebernahme.

    Reihenfolge (dokumentiert in docs/o11-o18-testmigration-regel.md):
      1. gleicher Name,
      2. der Odoo-11-Beschreibungstext (z. B. "20% USt") als Odoo-18-Name, ohne
         Gross-/Kleinschreibung - die Odoo-18-Steuernamen dieses Bestands stammen aus den
         Odoo-11-Beschreibungen,
      3. genau ein Kandidat mit gleichem Satz und gleicher Verwendung (sale/purchase/none),
      4. keine Entsprechung -> (None, Begruendung); der Aufrufer entscheidet, ob das ein Fehler
         ist (Produktsteuer: Abbruch) oder ein Anzulegender Stammdatensatz (Steuerliste).
    Mehrdeutigkeit bricht immer ab (kein stilles Ueberspringen).
    """
    treffer = rpc(z, "account.tax", "search", [[("name", "=", steuer11["name"])]],
                  "Steuer ueber den Namen suchen", context=CTX)
    if len(treffer) > 1:
        raise SystemExit("ABBRUCH: Steuername %r ist im Ziel %d Mal vorhanden - Zuordnung nicht "
                         "eindeutig." % (steuer11["name"], len(treffer)))
    if len(treffer) == 1:
        return treffer[0], "gleicher Name %r" % steuer11["name"]
    beschreibung = (steuer11.get("description") or "").strip()
    if beschreibung:
        kandidaten = rpc(z, "account.tax", "search_read",
                         [[("name", "=ilike", beschreibung), ("type_tax_use", "=", steuer11["type_tax_use"])],
                          ["name", "amount"]], "Steuer ueber die Odoo-11-Beschreibung suchen", context=CTX)
        if len(kandidaten) > 1:
            raise SystemExit("ABBRUCH: Odoo-11-Beschreibung %r passt im Ziel auf %d Steuern - "
                             "Zuordnung nicht eindeutig." % (beschreibung, len(kandidaten)))
        if len(kandidaten) == 1:
            return kandidaten[0]["id"], "Odoo-11-Beschreibung %r = Odoo-18-Name %r" % (
                beschreibung, kandidaten[0]["name"])
    kandidaten = rpc(z, "account.tax", "search_read",
                     [[("amount", "=", steuer11["amount"]), ("type_tax_use", "=", steuer11["type_tax_use"]),
                       ("active", "=", True)], ["name"]], "Steuer ueber Satz und Verwendung suchen",
                     context=CTX)
    if len(kandidaten) > 1:
        raise SystemExit("ABBRUCH: Odoo-11-Steuer %r (%s%%, %s) ist im Ziel nicht eindeutig - %d "
                         "Kandidaten mit gleichem Satz und gleicher Verwendung."
                         % (steuer11["name"], steuer11["amount"], steuer11["type_tax_use"],
                            len(kandidaten)))
    if len(kandidaten) == 1:
        return kandidaten[0]["id"], "einziger Treffer mit %s%% und %s" % (
            steuer11["amount"], steuer11["type_tax_use"])
    return None, "keine Entsprechung im Ziel (Name %r, %s%%, %s, Beschreibung %r)" % (
        steuer11["name"], steuer11["amount"], steuer11["type_tax_use"], steuer11.get("description"))


KONTO_FELDER = ["property_account_income_categ_id", "property_account_expense_categ_id"]


def lade_kategorien(k):
    """Alle Odoo-11-Produktkategorien mit Hierarchie, Namen (beide Sprachen) und Konten lesen.

    Die Namen sind uebersetzbar: die Odoo-11-Wurzel heisst in der Quelle deutsch "Alle" und
    englisch "All" - fuer die Zuordnung werden deshalb beide Namen gefuehrt. Zu jeder Kategorie
    werden die beiden Kontenfelder mitgelesen (Nummer, Name, Kontotyp) - Grundlage fuer die
    fachliche Kontenzuordnung ueber stabile Schluessel.
    """
    felder = ["id", "name", "complete_name", "parent_id"] + KONTO_FELDER
    kats = {}
    for sprache in ("de_DE", "en_US"):
        for x in rpc(k, "product.category", "search_read", [[], felder],
                     "Kategorien lesen (%s)" % sprache, context={"lang": sprache}):
            e = kats.setdefault(x["id"], {"id": x["id"], "name": x["name"],
                                          "parent_id": x["parent_id"],
                                          "complete_name": x["complete_name"], "namen": []})
            if x["name"] not in e["namen"]:
                e["namen"].append(x["name"])
            for feld in KONTO_FELDER:
                if x.get(feld) and not e.get(feld):
                    e[feld] = x[feld]
    # Konten der Kategorien read-only nachlesen (Nummer, Name, Kontotyp)
    konto_ids = set()
    for e in kats.values():
        for feld in KONTO_FELDER:
            if e.get(feld):
                konto_ids.add(e[feld][0])
    konten = {}
    for kid in sorted(konto_ids):
        treffer = rpc(k, "account.account", "read", [[kid], ["code", "name", "user_type_id",
                                                             "internal_type"]],
                      "Kategoriekonto in Odoo 11 lesen", context=CTX)
        if treffer:
            konten[kid] = treffer[0]
    for e in kats.values():
        e["konten"] = {feld: (konten.get(e[feld][0]) if e.get(feld) else None) for feld in KONTO_FELDER}
    return kats


def kontotyp_ziel(konto11):
    """Odoo-11-Kontotyp fachlich auf Odoo-18-Kontotypen abbilden (keine ID-Uebernahme)."""
    bezeichnung = (konto11.get("user_type_id") or [0, ""])[1] or ""
    if "erl" in bezeichnung.lower():
        return ["income", "income_other"]
    if "aufwand" in bezeichnung.lower():
        return ["expense", "expense_direct_cost"]
    return ["income", "income_other", "expense", "expense_direct_cost"]


def konto_im_ziel(z, konto11):
    """Odoo-11-Konto im Ziel aufloesen - ueber Kontonummer UND Namen, nie ueber die ID.

    Es wird **nichts angelegt** (Konten sind Stammdaten). Rueckgabe: (id oder None, Begruendung).
    Kein Treffer bedeutet Blocker fuer die echte Datenmigration; die Begruendung nennt die
    konkreten Kandidaten bzw. die fehlenden Konten.
    """
    code = str(konto11.get("code") or "").strip()
    name11 = (konto11.get("name") or "").strip()
    typen = kontotyp_ziel(konto11)
    # 1. Entschiedene Zuordnung (Anna) hat Vorrang - Zielkonto wird ueber Nummer UND Name
    #    geprueft; weicht der Name ab oder ist die Nummer nicht eindeutig, bricht der Lauf ab
    #    (keine stille Fehlzuordnung).
    entscheidung = ENTSCHEIDUNGEN_KONTEN.get(code)
    if entscheidung:
        treffer = rpc(z, "account.account", "search_read",
                      [[("code", "=", entscheidung["ziel_code"])], ["code", "name", "account_type"]],
                      "Entschiedenes Zielkonto %s suchen" % entscheidung["ziel_code"], context=CTX)
        if len(treffer) != 1:
            raise SystemExit("ABBRUCH: entschiedenes Zielkonto %s ist im Ziel %d Mal vorhanden - "
                             "Zuordnung nicht eindeutig." % (entscheidung["ziel_code"], len(treffer)))
        if treffer[0]["name"].strip() != entscheidung["ziel_name"]:
            raise SystemExit("ABBRUCH: entschiedenes Zielkonto %s heisst im Ziel %r, erwartet war %r "
                             "- Kontenrahmen weicht von der Entscheidung ab."
                             % (entscheidung["ziel_code"], treffer[0]["name"],
                                entscheidung["ziel_name"]))
        return treffer[0]["id"], "Entscheidung %s: %s -> %s %r (%s)" % (
            entscheidung["entscheidung"], code, treffer[0]["code"], treffer[0]["name"],
            entscheidung["begruendung"])
    # 2. Allgemeine Aufloesung ueber Nummer UND Namen (nie ueber die ID).
    if code:
        treffer = rpc(z, "account.account", "search_read", [[("code", "=", code)], ["code", "name"]],
                      "Kontonummer im Ziel suchen", context=CTX)
        if len(treffer) > 1:
            raise SystemExit("ABBRUCH: Kontonummer %s ist im Ziel %d Mal vorhanden - Zuordnung nicht "
                             "eindeutig." % (code, len(treffer)))
        if len(treffer) == 1:
            if treffer[0]["name"].strip() == name11:
                return treffer[0]["id"], "gleiche Nummer %s und gleicher Name %r" % (code, name11)
            return None, ("Nummer %s ist im Ziel mit %r belegt, in Odoo 11 mit %r - Nummer und Name "
                          "weichen ab, keine Zuordnung ueber die Nummer"
                          % (code, treffer[0]["name"], name11))
    gleich = rpc(z, "account.account", "search_read", [[("name", "=", name11)], ["code", "name"]],
                 "Kontoname im Ziel suchen", context=CTX) if name11 else []
    if len(gleich) == 1:
        return None, ("Konto %s %r fehlt; im Ziel gibt es %s %r (andere Nummer) - nur ueber die "
                      "Nummer zuordenbar, deshalb keine Zuordnung" % (code, name11, gleich[0]["code"],
                                                                      gleich[0]["name"]))
    if len(gleich) > 1:
        return None, ("Konto %s %r fehlt; der Name %r ist im Ziel %d Mal vorhanden"
                      % (code, name11, name11, len(gleich)))
    typkonten = rpc(z, "account.account", "search_read", [[("account_type", "in", typen)],
                                                          ["code", "name", "account_type"]],
                    "Konten des passenden Typs suchen", context=CTX)
    return None, ("Konto %s %r fehlt vollstaendig; im Ziel gibt es %d Konten der fachlich passenden "
                  "Typen %s: %s" % (code, name11, len(typkonten), "/".join(typen),
                                    ", ".join("%s %s" % (a["code"], a["name"][:26]) for a in typkonten[:6])))


def kategorie_im_ziel(z, kategorien, kat_id, mitschrift=None):
    """Odoo-11-Produktkategorie im Ziel bestimmen: Name (beide Sprachen) UND exakte Elternkette.

    Keine Zusammenlegung ueber aehnliche Namen (Auftrag Anna, Session 129):
      * genau ein Treffer mit passender Elternkette -> verwenden,
      * mehrere Treffer oder abweichende Elternkette  -> Abbruch mit Klartext,
      * nicht vorhanden -> im Plan als "wird angelegt" ausweisen; im Schreiblauf
        (mitschrift uebergeben) in der Testinstanz anlegen.
    Rueckgabe: (id oder None, Zustand).
    """
    k11 = kategorien.get(kat_id)
    if not k11:
        raise SystemExit("ABBRUCH: Odoo-11-Kategorie id %s ist nicht gelesen." % kat_id)
    name11 = k11["name"]
    treffer = set()
    for kandidat in k11["namen"]:
        for sprache in ("de_DE", "en_US"):
            treffer.update(rpc(z, "product.category", "search", [[("name", "=", kandidat)]],
                               "Produktkategorie ueber den Namen suchen (%s)" % sprache,
                               context={"lang": sprache}))
    treffer = sorted(treffer)
    if len(treffer) > 1:
        raise SystemExit("ABBRUCH: Kategorie %r existiert im Ziel %d Mal - Zuordnung nicht eindeutig "
                         "(keine Zusammenlegung ueber den Namen)." % (name11, len(treffer)))
    eltern11 = k11.get("parent_id")
    eltern_ziel = None
    if eltern11:
        eltern_ziel, _ = kategorie_im_ziel(z, kategorien, eltern11[0], mitschrift)
    if len(treffer) == 1:
        ziel = rpc(z, "product.category", "read", [treffer, ["parent_id"]],
                   "Produktkategorie lesen", context=CTX)[0]
        if bool(ziel["parent_id"]) != bool(eltern11):
            raise SystemExit("ABBRUCH: Kategorie %r liegt im Ziel unter %r, in Odoo 11 aber unter %r "
                             "- keine Zusammenlegung ueber den Namen."
                             % (name11, ziel["parent_id"], eltern11))
        if eltern11 and ziel["parent_id"][0] != eltern_ziel:
            raise SystemExit("ABBRUCH: Elternkette der Kategorie %r weicht ab." % name11)
        return treffer[0], "vorhanden"
    if mitschrift is None:
        return None, "fehlt im Ziel, wird beim Schreiblauf angelegt"
    werte = {"name": name11}
    if eltern_ziel:
        werte["parent_id"] = eltern_ziel
    neue = lege_an(mitschrift, z, "product.category", werte, "name", name11, "Produktkategorie")
    # Namen zusaetzlich in der Quellsprache hinterlegen, damit die Kategorie in beiden
    # Oberflaechensprachen gleich heisst (Odoo 11 fuehrt die Namen ebenfalls zweisprachig).
    rpc(z, "product.category", "write", [[neue], {"name": name11}],
        "Produktkategorie zweisprachig beschriften", context={"lang": "en_US"})
    return neue, "angelegt"


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
    steuern = []  # wird nach dem Lesen der Produkte gefuellt (Belegsteuern + Produktsteuern)
    bedingungen = (rpc(k, "account.payment.term", "read", [sorted(bedingung_ids), ["id", "name"]],
                       "Zahlungsbedingungen lesen") if bedingung_ids else [])
    produkte = rpc(k, "product.product", "read", [sorted(produkt_ids), PRODUKT_FELDER],
                   "Produkte lesen", context=CTX)
    # Steuern der Produkte mitlesen (Verkaufs- und Einkaufssteuern, Session 129)
    for pr in produkte:
        steuer_ids.update(pr.get("taxes_id") or [])
        steuer_ids.update(pr.get("supplier_taxes_id") or [])
    steuern = (rpc(k, "account.tax", "read", [sorted(steuer_ids),
                                              ["id", "name", "amount", "amount_type", "type_tax_use",
                                               "description", "tax_group_id"]], "Steuern lesen",
                   context=CTX)
               if steuer_ids else [])
    return partner, journale, konten, steuern, bedingungen, produkte, lade_kategorien(k)


# --------------------------------------------------------------------------
# 2. Plan gegen die Zielinstanz pruefen (nur lesend)
# --------------------------------------------------------------------------
def pruefe_ziel(z, partner, journale, konten, steuern, bedingungen, produkte, kategorien):
    plan = []
    konto_geprueft = set()
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
        try:
            ziel_steuer, wie = steuer_im_ziel(z, s)
            zustand = ("vorhanden (%s)" % wie) if ziel_steuer else "fehlt im Ziel"
        except SystemExit as fehler:
            zustand = "nicht eindeutig"
            wie = str(fehler)[:160]
        plan.append({"modell": "account.tax", "schluessel": s["name"], "zustand": zustand,
                     "was": "Steuer %s %s%%" % (s["name"], s["amount"])})
        print("      Steuer %-24s -> %s" % (s["name"], zustand if ziel_steuer else wie))
    for b in bedingungen:
        pruefe("account.payment.term", "name", b["name"], "Zahlungsbedingung")
    steuern11 = {s["id"]: s for s in steuern}
    for pr in produkte:
        pruefe("product.template", "name", pr["name"], "Produkt")
        for feld, modell, beschriftung in (("uom_id", "uom.uom", "Mengeneinheit"),
                                           ("uom_po_id", "uom.uom", "Einkauf ME")):
            wert = pr.get(feld)
            if not wert:
                continue
            ziel = rpc(z, modell, "search", [[("name", "=", zeige(wert))]], "%s suchen" % beschriftung,
                       context=CTX)
            wie = "gleicher Name"
            if not ziel:
                ziel = rpc(z, modell, "search", [[("name", "=ilike", zeige(wert))]],
                           "%s suchen (ohne Gross-/Kleinschreibung)" % beschriftung, context=CTX)
                wie = "Name ohne Gross-/Kleinschreibung"
            zustand = "vorhanden" if len(ziel) == 1 else ("nicht eindeutig" if ziel else "fehlt im Ziel")
            plan.append({"modell": modell, "schluessel": zeige(wert), "zustand": zustand,
                         "was": "%s fuer Produkt %s" % (beschriftung, pr["name"])})
            print("      %-18s %-44s -> %-14s %s" % (feld, zeige(wert), zustand,
                                                      wie if ziel else ""))
        # Produktkategorie: exakter Name und exakte Elternkette, keine Aehnlichkeitszuordnung
        if pr.get("categ_id"):
            kat_id = pr["categ_id"][0]
            kat11 = kategorien.get(kat_id, {})
            ziel_id, zustand = kategorie_im_ziel(z, kategorien, kat_id)
            plan.append({"modell": "product.category", "schluessel": kat11.get("complete_name", ""),
                         "zustand": "vorhanden" if ziel_id else
                                    "fehlt im Ziel, wird beim Schreiblauf angelegt",
                         "was": "Interne Kategorie fuer Produkt %s" % pr["name"]})
            print("      %-18s %-44s -> %s" % ("categ_id", kat11.get("complete_name", "")[:44], zustand))
            # Konten der Kategorie (Session 129): eigener Pruefpunkt. Es wird nichts angelegt
            # und nichts geraten - fehlt die Entsprechung, ist das ein Blocker.
            for feld, beschriftung in (("property_account_income_categ_id", "Erloeskonto"),
                                       ("property_account_expense_categ_id", "Aufwandskonto")):
                konto11 = (kat11.get("konten") or {}).get(feld)
                if not konto11:
                    continue
                schluessel = (feld, konto11["id"])
                if schluessel in konto_geprueft:
                    continue
                konto_geprueft.add(schluessel)
                ziel_konto, begruendung = konto_im_ziel(z, konto11)
                zustand = "vorhanden" if ziel_konto else "BLOCKER"
                plan.append({"modell": "account.account",
                             "schluessel": "%s %s" % (konto11["code"], konto11["name"]),
                             "zustand": zustand,
                             "was": "%s der Kategorie %s" % (beschriftung,
                                                             kat11.get("complete_name", ""))})
                print("      %-18s %-30s -> %-8s %s"
                      % (beschriftung, ("%s %s" % (konto11["code"], konto11["name"]))[:30], zustand,
                         begruendung if not ziel_konto else ""))
                if not ziel_konto:
                    BLOCKER_KONTEN.append("%s %r (Kategorie %s): %s"
                                          % (konto11["code"], konto11["name"],
                                             kat11.get("complete_name", ""), begruendung))
        for feld, beschriftung in (("taxes_id", "Steuern (Verkauf)"),
                                   ("supplier_taxes_id", "Steuern (Einkauf)")):
            for tid in (pr.get(feld) or []):
                t11 = steuern11.get(tid)
                if not t11:
                    continue
                try:
                    ziel_id, wie = steuer_im_ziel(z, t11)
                    zustand = "vorhanden" if ziel_id else "fehlt im Ziel"
                except SystemExit as fehler:
                    ziel_id, wie, zustand = None, str(fehler)[:120], "nicht eindeutig"
                plan.append({"modell": "account.tax", "schluessel": t11["name"], "zustand": zustand,
                             "was": "%s fuer Produkt %s (%s)" % (beschriftung, pr["name"], wie)})
                print("      %-18s %-44s -> %-14s %s" % (feld, t11["name"], zustand,
                                                          wie if ziel_id is not None else ""))
        for feld, beschriftung in (("default_code", "Interne Referenz"),
                                   ("standard_price", "Kosten")):
            if pr.get(feld) not in (None, False, ""):
                plan.append({"modell": "product.template", "schluessel": str(pr[feld]), "zustand": "1:1",
                             "was": "%s fuer Produkt %s" % (beschriftung, pr["name"])})
                print("      %-18s %-30s -> 1:1" % (feld, pr[feld]))
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
               kategorien, mitschrift):
    # --- Stammdaten in der dokumentierten Reihenfolge -----------------------
    # Journale werden NICHT angelegt: die Odoo-11-Journale werden ueber JOURNAL_MAPPING auf die
    # vorhandenen Zieljournale abgebildet (Punkt 3).
    if BLOCKER_KONTEN:
        print("\n   HINWEIS: Die Kontenfelder der Produktkategorien werden NICHT gesetzt - "
              "%d Odoo-11-Konten ohne eindeutige Entsprechung (siehe Plan/Blocker)."
              % len(BLOCKER_KONTEN))
    for s in steuern:
        # Erst zuordnen: vorhandene Zielsteuer verwenden (z. B. Odoo-18 "20% Ust" fuer die
        # Odoo-11-Steuer "20% Umsatzsteuer" ueber deren Beschreibung "20% USt"), sonst anlegen.
        # Verhindert doppelte Steuern in der Testinstanz.
        try:
            ziel_steuer, wie = steuer_im_ziel(z, s)
        except SystemExit as fehler:
            raise SystemExit("ABBRUCH: Steuer %r nicht eindeutig zuordenbar - %s"
                             % (s["name"], str(fehler)[:200]))
        if ziel_steuer:
            print("      Steuer %-24s -> vorhanden (id %s, %s)" % (s["name"], ziel_steuer, wie))
            continue
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
    steuern11 = {s["id"]: s for s in steuern}
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
        # --- Session 129: zusaetzliche Produktfelder fachlich zuordnen (keine ID-Uebernahme) ---
        if pr.get("default_code"):
            werte["default_code"] = pr["default_code"]
        if pr.get("standard_price"):
            werte["standard_price"] = pr["standard_price"]
        for feld, modell, beschriftung in (("uom_id", "uom.uom", "Mengeneinheit"),
                                           ("uom_po_id", "uom.uom", "Einkauf ME")):
            wert = pr.get(feld)
            if not wert:
                continue
            treffer = rpc(z, modell, "search", [[("name", "=", zeige(wert))]], "%s suchen" % beschriftung,
                          context=CTX)
            if not treffer:
                treffer = rpc(z, modell, "search", [[("name", "=ilike", zeige(wert))]],
                              "%s suchen (ohne Gross-/Kleinschreibung)" % beschriftung, context=CTX)
            if len(treffer) != 1:
                raise SystemExit("ABBRUCH: %s %r fuer Produkt %r ist im Ziel nicht eindeutig "
                                 "(%d Treffer)." % (beschriftung, zeige(wert), pr["name"], len(treffer)))
            werte[feld] = treffer[0]
        # Produktkategorie: exakter Name und exakte Elternkette; fehlende Kategorien werden
        # ausschliesslich hier in der Testinstanz angelegt (Auftrag Anna, Session 129).
        if pr.get("categ_id"):
            kat_id_ziel, zustand = kategorie_im_ziel(z, kategorien, pr["categ_id"][0], mitschrift)
            if not kat_id_ziel:
                raise SystemExit("ABBRUCH: Kategorie fuer Produkt %r konnte nicht bestimmt werden (%s)."
                                 % (pr["name"], zustand))
            werte["categ_id"] = kat_id_ziel
            print("      %-18s %-24s -> %s" % ("categ_id", pr["categ_id"][1][:24], zustand))
        for feld, beschriftung in (("taxes_id", "Steuern (Verkauf)"),
                                   ("supplier_taxes_id", "Steuern (Einkauf)")):
            ziel_steuern = []
            for tid in (pr.get(feld) or []):
                t11 = steuern11.get(tid)
                if not t11:
                    raise SystemExit("ABBRUCH: Odoo-11-Steuer id %s fuer Produkt %r nicht gelesen."
                                     % (tid, pr["name"]))
                ziel_id, wie = steuer_im_ziel(z, t11)
                if not ziel_id:
                    raise SystemExit("ABBRUCH: %s fuer Produkt %r nicht zuordenbar - %s"
                                     % (beschriftung, pr["name"], wie))
                ziel_steuern.append(ziel_id)
                print("      %-18s %-24s -> Odoo 18 id=%-5s (%s)"
                      % (beschriftung, t11["name"], ziel_id, wie))
            if ziel_steuern:
                werte[feld] = [(6, 0, ziel_steuern)]
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
                pname = produkt_name[z_["product_id"][0]]
                treffer = rpc(z, "product.product", "search", [[("name", "=", pname)]], "Produkt suchen")
                if len(treffer) != 1:
                    raise SystemExit("ABBRUCH: Produkt %r aus Beleg %s ist im Ziel nicht eindeutig "
                                     "vorhanden (%d Treffer)." % (pname, b["number"] or "Entwurf",
                                                                  len(treffer)))
                wz["product_id"] = treffer[0]
            if z_.get("account_id"):
                alt = str(z_["account_id"][1]).split()[0]
                code = KONTO_MAPPING.get(alt, alt)
                treffer = rpc(z, "account.account", "search", [[("code", "=", code)]], "Konto suchen")
                if len(treffer) != 1:
                    raise SystemExit("ABBRUCH: Konto %s (Odoo 11: %s) fehlt im Ziel oder ist nicht "
                                     "eindeutig (%d Treffer)." % (code, z_["account_id"][1], len(treffer)))
                wz["account_id"] = treffer[0]
            steuer_ids = []
            for t_ in (z_.get("invoice_line_tax_ids") or []):
                s = next((x for x in steuern if x["id"] == t_), None)
                if not s:
                    raise SystemExit("ABBRUCH: Odoo-11-Steuer id %s aus Beleg %s ist nicht gelesen."
                                     % (t_, b["number"] or "Entwurf"))
                ziel_steuer, wie = steuer_im_ziel(z, s)
                if not ziel_steuer:
                    raise SystemExit("ABBRUCH: Steuer %r aus Beleg %s nicht zuordenbar - %s"
                                     % (s["name"], b["number"] or "Entwurf", wie))
                steuer_ids.append(ziel_steuer)
            if steuer_ids:
                wz["tax_ids"] = [(6, 0, steuer_ids)]
            zeilen_werte.append((0, 0, wz))
        waehrung = rpc(z, "res.currency", "search", [[("name", "=", name(b["currency_id"]))]],
                       "Waehrung suchen")
        if len(waehrung) != 1:
            raise SystemExit("ABBRUCH: Waehrung %r aus Beleg %s ist im Ziel nicht eindeutig (%d Treffer)."
                             % (name(b["currency_id"]), b["number"] or "Entwurf", len(waehrung)))
        werte = {"move_type": b["type"], "partner_id": ziel_partner[0], "journal_id": ziel_journal[0],
                 "invoice_date": b["date_invoice"], "invoice_date_due": b["date_due"],
                 "currency_id": waehrung[0],
                 "invoice_line_ids": zeilen_werte}
        if b.get("payment_term_id"):
            treffer = rpc(z, "account.payment.term", "search",
                          [[("name", "=", name(b["payment_term_id"]))]], "Zahlungsbedingung suchen")
            if len(treffer) != 1:
                raise SystemExit("ABBRUCH: Zahlungsbedingung %r aus Beleg %s ist im Ziel nicht "
                                 "eindeutig (%d Treffer)." % (name(b["payment_term_id"]),
                                                              b["number"] or "Entwurf", len(treffer)))
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


def firmenvorgabe_kategoriekonten(z):
    """Firmenvorgabe (ir.default) der Konto-Felder von product.category im Ziel lesen.

    Odoo 18 fuehrt Firmenvorgaben als `ir.default` (das Modell `ir.property` gibt es nicht
    mehr); fachlich entspricht das den Odoo-11-`ir.property`-Eintraegen mit leerem `res_id`.
    Rueckgabe: {Feldname: {code, name, account_type, id} oder None}.
    """
    feldids = rpc(z, "ir.model.fields", "search",
                  [[("model", "=", "product.category"),
                    ("name", "in", ["property_account_income_categ_id",
                                    "property_account_expense_categ_id"])]],
                  "Konto-Felder der Produktkategorie suchen", context=CTX)
    if not feldids:
        return {}
    namen = {f["id"]: f["name"] for f in rpc(z, "ir.model.fields", "read",
                                             [feldids, ["name", "field_description"]],
                                             "Konto-Felder benennen", context=CTX)}
    vorgaben = rpc(z, "ir.default", "search_read",
                   [[("field_id", "in", feldids)], ["field_id", "json_value", "company_id"]],
                   "Firmenvorgabe der Kategoriekonten lesen", context=CTX)
    aus = {}
    for v in vorgaben:
        roh = str(v.get("json_value") or "").strip()
        konto = None
        if roh.isdigit():
            k = rpc(z, "account.account", "read", [[int(roh)], ["code", "name", "account_type"]],
                    "Firmenvorgabekonto lesen", context=CTX)
            if k:
                konto = k[0]
        aus[namen.get(v["field_id"][0], v["field_id"][1])] = {"konto": konto,
                                                              "firma": v.get("company_id")}
    return aus


def pruefe_firmenvorgabe(z):
    """Firmenvorgabe der Kategoriekonten im Ziel pruefen und gegen die Entscheidungen halten.

    Erwartung aus Odoo 11: Ertragskonto = 8400 (entschieden -> 4000), Aufwandskonto = 3400
    (keine Entscheidung -> BLOCKER, der im Ziel vorhandene Odoo-18-Kontenrahmenwert wird
    ausdruecklich NICHT als Zuordnung gewertet).
    """
    vorgabe = firmenvorgabe_kategoriekonten(z)
    print("\nFirmenvorgabe der Produktkategorien im Ziel (ir.default, Firmenweit):")
    plan = []
    for feld, beschriftung, quelle in (
            ("property_account_income_categ_id", "Ertragskonto", "8400"),
            ("property_account_expense_categ_id", "Aufwandskonto", "3400")):
        eintrag = vorgabe.get(feld) or {}
        konto = eintrag.get("konto")
        zeigt = ("%s %s" % (konto["code"], konto["name"])) if konto else "nicht gesetzt"
        entscheidung = ENTSCHEIDUNGEN_KONTEN.get(quelle)
        if entscheidung and konto and konto["code"] == entscheidung["ziel_code"]:
            zustand = "passt zur Entscheidung"
            hinweis = "Entscheidung %s: %s -> %s" % (entscheidung["entscheidung"], quelle,
                                                     entscheidung["ziel_code"])
        elif entscheidung:
            zustand = "ABWEICHUNG"
            hinweis = ("Entscheidung erwartet %s, Ziel zeigt %s - vor dem Schreiblauf klaeren"
                       % (entscheidung["ziel_code"], zeigt))
        else:
            zustand = "keine Entscheidung (BLOCKER bleibt)"
            hinweis = ("Odoo-11-Quelle %s hat keine freigegebene Entsprechung; der Zielwert ist "
                       "der Kontenrahmen-Standard und wird nicht als Zuordnung gewertet" % quelle)
        print("   %-14s Odoo-11 %s  ->  Ziel %-46s %s" % (beschriftung, quelle, zeigt, zustand))
        print("      %s" % hinweis)
        plan.append({"modell": "ir.default", "schluessel": "%s (Odoo 11: %s)" % (beschriftung, quelle),
                     "zustand": zustand, "was": zeigt})
    return plan


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
    (partner, journale, konten, steuern, bedingungen, produkte,
     kategorien) = waehle_stammdaten(k, belege, zeilen)
    print("Stammdaten: %d Partner, %d Journale, %d Konten, %d Steuern, %d Zahlungsbedingungen, "
          "%d Produkte, %d Kategorien (Odoo 11)"
          % (len(partner), len(journale), len(konten), len(steuern), len(bedingungen), len(produkte),
             len(kategorien)))
    for pr in produkte:
        print("   Produkt %-58s O11-Typ %-14s -> O18 %s%s" % (
            pr["name"][:58], pr["type"], typ_ziel(pr["type"])[0],
            " + is_storable" if typ_ziel(pr["type"])[1] else ""))

    plan = pruefe_ziel(z, partner, journale, konten, steuern, bedingungen, produkte, kategorien)
    plan.extend(pruefe_firmenvorgabe(z))
    fehlend = [x for x in plan if "fehlt im Ziel" in x["zustand"]]
    print("\nPlan: %d Positionen, davon %d im Ziel noch nicht vorhanden." % (len(plan), len(fehlend)))
    for x in fehlend:
        print("   fehlt: %-22s %-30s %s" % (x["modell"], x["schluessel"][:30], x["was"]))
    if BLOCKER_KONTEN:
        print("\nBLOCKER (keine eindeutige Zuordnung, es wird nichts angelegt und nichts geraten):")
        for b in BLOCKER_KONTEN:
            print("   %s" % b)
        print("   -> Kontenstammdaten sind ein eigener, freizugebender Schritt (Kontenmigration).")
        print("      Die Odoo-11-Kategorien tragen keine eigenen Konten: beide Werte kommen aus der")
        print("      Firmenvorgabe (ir.property, res_id leer).")

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
                   kategorien, mitschrift)
    finally:
        with open(PROTOKOLL, "w", encoding="utf-8") as fh:
            json.dump({"angelegt": mitschrift}, fh, ensure_ascii=False, indent=1)
    print("\nAngelegt: %d Datensaetze. Protokoll: %s" % (len(mitschrift), PROTOKOLL))
    return 0


if __name__ == "__main__":
    sys.exit(main())
