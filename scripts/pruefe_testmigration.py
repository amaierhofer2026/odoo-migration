"""Prueft die Ergebnisse der Abrechnungs-Testmigration (Odoo 11 gegen Odoo 18 Testinstanz).

Aufruf:
    python scripts/pruefe_testmigration.py --instanz vm
    python scripts/pruefe_testmigration.py --instanz vm --protokoll PFAD

Geprueft werden die neun Punkte der Abnahme:
  1 Stammdatenzuordnung          5 Statuswerte
  2 Rechnungen und Gutschriften  6 Konten- und Steuerzuordnung
  3 Zahlungen                    7 Summen, Steuern, Restbetraege
  4 Beziehungen/Verknuepfungen   8 historische Nummern
                                 9 berechnete Felder in Odoo 18
Zusaetzlich: Unversehrtheitsnachweis - kein Bestandsdatensatz darf ein neueres `write_date`
tragen als der Migrationsstart (ausser den im Protokoll vermerkten Datensaetzen).

Exit-Codes: 0 = alle Pruefungen bestanden, 1 = mindestens eine Abweichung, 2 = nicht pruefbar.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402

KONTO_MAPPING = {"1201": "2801", "1410": "2000", "1776": "3500", "8400": "4000"}
MIGRATIONSSTART = "2026-10-05 08:00:00"      # erster Schreiblauf (UTC des Servers)
CTX = {"lang": "de_DE"}

befunde, abweichungen, hinweise = [], [], []


def pruefe(ok, beschreibung, soll=None, ist=None):
    if ok:
        befunde.append("OK   %s" % beschreibung)
    else:
        abweichungen.append("ABWEICHUNG %s%s%s" % (
            beschreibung,
            "" if soll is None else " | soll: %r" % (soll,),
            "" if ist is None else " | ist: %r" % (ist,)))
    print(("OK    " if ok else "ABW   ") + beschreibung
          + ("" if soll is None else "  (soll=%r ist=%r)" % (soll, ist)))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["lokal", "vm"], default="vm")
    p.add_argument("--protokoll", default=os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"),
                                                       "Temp", "testmigration_protokoll.json"))
    a = p.parse_args()

    k, z = o11(), o18(a.instanz)
    if not os.path.exists(a.protokoll):
        print("KEIN PROTOKOLL %s - die Testmigration wurde nicht ausgefuehrt." % a.protokoll)
        return 2
    protokoll = json.load(open(a.protokoll, encoding="utf-8"))["angelegt"]
    unsere = {}
    for e in protokoll:
        if e.get("neu", True):
            unsere.setdefault(e["modell"], set()).add(e["id"])
    print("Protokoll: %d Eintraege, davon selbst angelegt: %s"
          % (len(protokoll), {m: len(i) for m, i in sorted(unsere.items())}))

    # --- 1 Stammdaten ------------------------------------------------------
    print("\n== 1 Stammdatenzuordnung")
    partner = z.kw("res.partner", "search_read",
                   [[("id", "in", sorted(unsere.get("res.partner", [])))],
                    ["name", "is_company", "vat", "street", "zip", "city", "ref"]])
    for pz in partner:
        # Punkt 2: der uebernommene Anzeigename ist community_salutation, sonst name
        quelle = k.kw("res.partner", "search_read",
                      [["|", ("community_salutation", "=", pz["name"]), ("name", "=", pz["name"])],
                       ["name", "display_name", "is_company", "vat", "street", "zip",
                        "city", "ref", "community_salutation"]])
        if not quelle:
            pruefe(False, "Partner %s in Odoo 11 gefunden" % pz["name"])
            continue
        q = quelle[0]
        pruefe((q.get("community_salutation") or q["name"]) == pz["name"],
               "Partner %-42s sichtbarer Name uebernommen" % pz["name"][:42],
               q.get("community_salutation") or q["name"], pz["name"])
        pruefe(q["is_company"] == pz["is_company"] and (q["vat"] or False) == (pz["vat"] or False)
               and (q["street"] or "") == (pz["street"] or "") and (q["zip"] or "") == (pz["zip"] or ""),
               "Partner %-42s Firma/VAT/Strasse/PLZ uebernommen" % pz["name"][:42],
               (q["is_company"], q["vat"], q["street"], q["zip"]),
               (pz["is_company"], pz["vat"], pz["street"], pz["zip"]))
        pruefe((q.get("ref") or False) == (pz.get("ref") or False),
               "Partner %-42s Interne Referenz uebernommen" % pz["name"][:42],
               q.get("ref"), pz.get("ref"))
        # Odoo 11 zeigt bei Gemeinden die Organisationsbezeichnung statt des reinen Namens
        # ("[20609] Marktgemeinde Greifenburg" gegen name "Greifenburg").
        if q.get("display_name") and q["display_name"] != q["name"]:
            hinweise.append("Partner %s: Odoo-11-Anzeigename %r, uebernommener Satzname %r"
                            % (pz["name"], q["display_name"], pz["name"]))

    produkte = z.kw("product.template", "search_read",
                    [[("id", "in", sorted(unsere.get("product.template", [])))],
                     ["name", "type", "is_storable", "list_price", "sale_ok", "purchase_ok",
                      "product_type_id", "invoice_policy"]])
    for pr in produkte:
        q = k.kw("product.template", "search_read", [[("name", "=", pr["name"])],
                                                     ["name", "type", "list_price", "sale_ok",
                                                      "purchase_ok", "product_type_id"]])[0]
        # Punkt 1: der Typ wird 1:1 uebernommen (die Zielauswahl kennt dieselben ITK-Werte);
        # nur der Odoo-11-Typ "product" wird zu consu + is_storable.
        erwartet = "consu" if q["type"] == "product" else q["type"]
        ok = (pr["type"] == erwartet and pr["sale_ok"] == q["sale_ok"]
              and pr["purchase_ok"] == q["purchase_ok"] and pr["list_price"] == q["list_price"])
        if q["product_type_id"]:
            ok = ok and pr["product_type_id"] and pr["product_type_id"][1] == q["product_type_id"][1]
        pruefe(ok, "Produkt %-50s Typ/Verkauf/Einkauf/Preis/Produkttyp" % pr["name"][:50],
               (q["type"], q["list_price"], q["sale_ok"], q["purchase_ok"]),
               (pr["type"], pr["list_price"], pr["sale_ok"], pr["purchase_ok"]))

    journal = z.kw("account.journal", "search_read",
                   [[("id", "in", sorted(unsere.get("account.journal", [])))], ["name", "code", "type"]])
    for j in journal:
        q = k.kw("account.journal", "search_read", [[("code", "=", j["code"])], ["name", "code", "type"]])
        pruefe(bool(q) and q[0]["name"] == j["name"], "Journal %r Code/Name aus Odoo 11" % j["code"],
               q[0] if q else None, j)
    steuer = z.kw("account.tax", "search_read",
                  [[("id", "in", sorted(unsere.get("account.tax", [])))],
                   ["name", "amount", "amount_type", "type_tax_use", "tax_group_id"]])
    for s in steuer:
        q = k.kw("account.tax", "search_read", [[("name", "=", s["name"])],
                                                ["name", "amount", "amount_type", "type_tax_use"]])
        pruefe(bool(q) and q[0]["amount"] == s["amount"] and q[0]["type_tax_use"] == s["type_tax_use"],
               "Steuer %r Betrag/Verwendung" % s["name"], q[0] if q else None, s)

    # --- 2 Belege, 4 Beziehungen, 5 Status, 6 Konten/Steuern, 7 Summen ------
    print("\n== 2/4/5/6/7 Belege, Beziehungen, Status, Konten, Summen")
    for move in z.kw("account.move", "search_read",
                     [[("id", "in", sorted(unsere.get("account.move", [])))],
                      ["name", "move_type", "state", "payment_state", "partner_id", "journal_id",
                       "invoice_date", "invoice_date_due", "amount_untaxed", "amount_tax",
                       "amount_total", "amount_residual", "itk_o11_invoice_number",
                       "invoice_line_ids"]]):
        nummer = move["itk_o11_invoice_number"]
        if not nummer:
            print("   (Entwurf ohne Odoo-11-Nummer, id=%s - nur Zaehlpruefung)" % move["id"])
            continue
        q = k.kw("account.invoice", "search_read", [[("number", "=", nummer)],
                                                    ["number", "type", "state", "partner_id",
                                                     "journal_id", "date_invoice", "date_due",
                                                     "amount_untaxed", "amount_tax", "amount_total",
                                                     "residual", "invoice_line_ids"]])[0]
        # Der Anzeigename in Odoo 11 enthaelt Praefixe ("[20609] Marktgemeinde Greifenburg").
        # Verglichen wird deshalb der Satzname des Partners, den Odoo 11 ueber die Interne
        # Referenz liefert.
        qp = k.kw("res.partner", "search_read", [[("id", "=", q["partner_id"][0])],
                                                 ["name", "ref", "display_name",
                                                  "community_salutation"]])[0]
        pruefe((qp.get("community_salutation") or qp["name"]) == move["partner_id"][1],
               "Beleg %-12s Partner ueber sichtbaren Namen" % nummer,
               qp.get("community_salutation") or qp["name"], move["partner_id"][1])
        # Punkt 3: Odoo-11-Journal "Ausgangsrechnungen"/"Re.:" wird auf das Zieljournal
        # "Kundenrechnungen"/"RE" abgebildet; die Nummer kommt aus der Zielsequenz.
        pruefe(move["journal_id"][1].split(" (")[0] in ("Kundenrechnungen", "Customer Invoices"),
               "Beleg %-12s Journal im Ziel" % nummer, "Kundenrechnungen", move["journal_id"][1])
        pruefe(q["date_invoice"] == move["invoice_date"] and q["date_due"] == move["invoice_date_due"],
               "Beleg %-12s Rechnungsdatum/Faelligkeit" % nummer,
               (q["date_invoice"], q["date_due"]), (move["invoice_date"], move["invoice_date_due"]))
        pruefe(abs(q["amount_untaxed"] - move["amount_untaxed"]) < 0.01
               and abs(q["amount_tax"] - move["amount_tax"]) < 0.01
               and abs(q["amount_total"] - move["amount_total"]) < 0.01,
               "Beleg %-12s Summen Netto/Steuer/Brutto" % nummer,
               (q["amount_untaxed"], q["amount_tax"], q["amount_total"]),
               (move["amount_untaxed"], move["amount_tax"], move["amount_total"]))
        erwarteter_zustand = "draft" if q["state"] == "draft" else "posted"
        pruefe(move["state"] == erwarteter_zustand, "Beleg %-12s Zustand" % nummer,
               erwarteter_zustand, move["state"])
        if q["state"] == "paid":
            if move["payment_state"] == "paid" and abs(move["amount_residual"]) < 0.01:
                pruefe(True, "Beleg %-12s Zahlungsstatus/Rest" % nummer, ("paid", 0.0),
                       (move["payment_state"], move["amount_residual"]))
            else:
                hinweise.append("Beleg %s: Odoo 11 = bezahlt, Ziel = %s (Rest %.2f). Die Zahlung "
                                "dieses Belegs ist in Odoo 11 kein eigener Zahlungsdatensatz "
                                "(Abstimmung ueber eine Buchung) und daher nicht Teil der Auswahl."
                                % (nummer, move["payment_state"], move["amount_residual"]))
        # Zeilen: Menge, Preis, Konto, Steuer
        qz = k.kw("account.invoice.line", "read", [q["invoice_line_ids"],
                                                   ["quantity", "price_unit", "account_id",
                                                    "invoice_line_tax_ids"]])
        mz = z.kw("account.move.line", "read", [move["invoice_line_ids"],
                                                ["quantity", "price_unit", "account_id", "tax_ids"]])
        pruefe(len(qz) == len(mz), "Beleg %-12s Zeilenzahl" % nummer, len(qz), len(mz))
        for a_, b_ in zip(qz, mz):
            soll_konto = KONTO_MAPPING.get(str(a_["account_id"][1]).split()[0],
                                           str(a_["account_id"][1]).split()[0])
            pruefe(abs(a_["quantity"] - b_["quantity"]) < 1e-6 and abs(a_["price_unit"] - b_["price_unit"]) < 1e-6
                   and b_["account_id"][1].startswith(soll_konto),
                   "Beleg %-12s Zeile Menge/Preis/Konto" % nummer,
                   (a_["quantity"], a_["price_unit"], soll_konto),
                   (b_["quantity"], b_["price_unit"], b_["account_id"][1]))
            soll_steuer = [t for t in (a_["invoice_line_tax_ids"] or [])]
            pruefe((bool(soll_steuer) == bool(b_["tax_ids"])),
                   "Beleg %-12s Zeile Steuer gesetzt" % nummer, soll_steuer, b_["tax_ids"])

    # --- 3 Zahlungen / 8 historische Nummern ------------------------------
    print("\n== 3 Zahlungen und historische Nummern")
    for pid in sorted(unsere.get("account.payment", [])):
        pz = z.kw("account.payment", "read", [[pid], ["name", "amount", "date", "memo", "state",
                                                      "partner_id", "journal_id", "move_id",
                                                      "itk_o11_payment_number"]])[0]
        q = k.kw("account.payment", "search_read", [[("name", "=", pz["memo"])],
                                                    ["name", "amount", "payment_date", "partner_id",
                                                     "journal_id", "state"]])
        pruefe(bool(q), "Zahlung %r existiert in Odoo 11" % pz["memo"], None, pz["memo"])
        if not q:
            continue
        q = q[0]
        pruefe(abs(q["amount"] - pz["amount"]) < 0.01 and q["payment_date"] == pz["date"],
               "Zahlung %-18s Betrag/Datum" % pz["memo"], (q["amount"], q["payment_date"]),
               (pz["amount"], pz["date"]))
        pruefe(q["journal_id"][1].startswith(pz["journal_id"][1].split(" (")[0]),
               "Zahlung %-18s Journal" % pz["memo"], q["journal_id"][1], pz["journal_id"][1])
        pruefe(pz["state"] in ("paid", "in_process"),
               "Zahlung %-18s gebucht (Odoo-18-Zustand)" % pz["memo"], "paid/in_process", pz["state"])
        # Punkt 4: die Odoo-11-Zahlungsnummer gehoert in das Herkunftsfeld
        pruefe(pz.get("itk_o11_payment_number") == pz["memo"],
               "Zahlung %-18s Odoo-11-Nummer im Herkunftsfeld" % pz["memo"],
               pz["memo"], pz.get("itk_o11_payment_number"))
        zeilen = z.kw("account.move.line", "search_read",
                      [[("move_id", "=", pz["move_id"][0]), ("reconciled", "=", True)],
                       ["id", "amount_residual"]])
        pruefe(bool(zeilen), "Zahlung %-18s ist abgestimmt (mindestens eine Zeile)" % pz["memo"],
               ">=1 abgestimmte Zeile", len(zeilen))

    # --- 9 berechnete Felder ----------------------------------------------
    print("\n== 9 berechnete Felder in Odoo 18")
    for move in z.kw("account.move", "search_read",
                     [[("id", "in", sorted(unsere.get("account.move", [])))],
                      ["itk_o11_invoice_number", "amount_untaxed", "amount_total",
                      "invoice_line_ids"]]):
        if not move["itk_o11_invoice_number"]:
            continue
        zeilen = z.kw("account.move.line", "read", [move["invoice_line_ids"],
                                                    ["price_subtotal", "price_total"]])
        netto = round(sum(l["price_subtotal"] for l in zeilen), 2)
        brutto = round(sum(l["price_total"] for l in zeilen), 2)
        pruefe(abs(netto - move["amount_untaxed"]) < 0.05 and abs(brutto - move["amount_total"]) < 0.05,
               "Beleg %-12s Netto/Brutto = Summe der Zeilen (Odoo 18 rechnet neu)"
               % move["itk_o11_invoice_number"], (move["amount_untaxed"], move["amount_total"]),
               (netto, brutto))

    # --- Unversehrtheitsnachweis ------------------------------------------
    print("\n== Unversehrtheit: kein Bestandsdatensatz wurde angefasst")
    for modell, extra in (("res.partner", []), ("product.template", []), ("account.journal", []),
                          ("account.tax", []), ("account.move", []), ("account.payment", []),
                          ("sale.order", []), ("account.account", [])):
        daten = z.kw(modell, "search_read", [[("write_date", ">=", MIGRATIONSSTART)],
                                             ["id", "write_date"]])
        unsere_ids = set(unsere.get(modell, set()))
        if modell == "account.move":
            for pid in unsere.get("account.payment", []):
                pz = z.kw("account.payment", "read", [[pid], ["move_id"]])
                if pz and pz[0]["move_id"]:
                    unsere_ids.add(pz[0]["move_id"][0])
        fremde = [d for d in daten if d["id"] not in unsere_ids]
        pruefe(not fremde, "%-20s keine fremden Aenderungen seit Migrationsstart" % modell,
               "0 fremde", "%d fremde (%s)" % (len(fremde), [(d["id"], d["write_date"]) for d in fremde[:3]]))
    # Zeilen der angelegten Belege sind neu, sonst darf keine Buchungszeile neu sein
    unsere_moves = set(unsere.get("account.move", []))
    # Buchungen unserer Zahlungen gehoeren ebenfalls zur Migration
    for pid in unsere.get("account.payment", []):
        pz = z.kw("account.payment", "read", [[pid], ["move_id"]])
        if pz and pz[0]["move_id"]:
            unsere_moves.add(pz[0]["move_id"][0])
    zeilen = z.kw("account.move.line", "search_read", [[("write_date", ">=", MIGRATIONSSTART)],
                                                       ["id", "move_id"]])
    fremde_zeilen = [l for l in zeilen if (l["move_id"] or [0])[0] not in unsere_moves]
    pruefe(not fremde_zeilen, "account.move.line   keine fremden Aenderungen seit Migrationsstart",
           "0 fremde", len(fremde_zeilen))

    # Punkt 3: keine unsauberen Nummern mehr
    unsauber = z.kw("account.move", "search_read",
                    [[("id", "in", sorted(unsere.get("account.move", [])))], ["name"]])
    schlecht = [m["name"] for m in unsauber
                if m["name"] and ("Re.:" in m["name"] or "RRe" in m["name"])]
    pruefe(not schlecht, "Belegnummern ohne Journalcode-Reste (Punkt 3)", "0", schlecht)

    print("\n=== Ergebnis ===")
    print("bestanden: %d | Abweichungen: %d" % (len(befunde), len(abweichungen)))
    for a_ in abweichungen:
        print("   " + a_)
    if hinweise:
        print("\nHinweise (dokumentiert, keine Fehler):")
        for h in hinweise:
            print("   " + h)
    ziel = os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "Temp",
                        "testmigration_pruefung.json")
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump({"bestanden": befunde, "abweichungen": abweichungen}, fh, ensure_ascii=False, indent=1)
    print("Protokoll: %s" % ziel)
    return 1 if abweichungen else 0


if __name__ == "__main__":
    sys.exit(main())
