"""Abnahmepruefung Verkauf Teil 3, Schritt 1 (Session 121): Formulare und Reiter.

Prueft READ-ONLY in einem Lauf:
  - Odoo 11 Prod: Reiter und Gruppen des Auftragsformulars (nur lesend)
  - Odoo 18 lokal und VM: dieselben Reiter, lokal = VM
  - Zuordnung der Odoo-11-Reiter/Gruppen auf Odoo 18
  - Auftragszeilen-Formular hat in beiden Systemen keinen Reiter (kein Notebook)

Aufruf:
    python scripts/verify_s121_verkauf_teil3_reiter.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18
from analyse_verkauf_teil3_formulare import formular_arch, seiten, hauptbereich

REITER_O11 = ["Auftragszeilen", "Weitere Informationen"]
REITER_O18 = ["Auftragspositionen", "Optionale Produkte", "Angebotsbauer", "Weitere Informationen"]

# Odoo-11-Reiter/Gruppe -> Odoo-18-Reiter/Gruppe
GRUPPEN_MAPPING = {
    "Lieferadresse": "Versand",              # Lagerfelder entfallen, Gruppe bleibt erhalten
    "Information Umsatz": "Verkauf",
    "Abrechnung": "Rechnungsstellung",
    "Berichtswesen": "Nachverfolgung",
}

# Felder, die im Odoo-11-Hauptbereich (vor dem Notebook) stehen und in Odoo 18 vorhanden sein muessen
HAUPT_O11 = ["state", "name", "partner_id", "sale_contact_id", "administrative_contact_id",
             "technical_contact_id", "final_customer_id", "product_category_id",
             "partner_invoice_id", "partner_shipping_id", "validity_date", "user_id",
             "confirmation_date", "pricelist_id", "currency_id", "payment_term_id"]


def main() -> int:
    ok = fehler = 0

    def pruefe(bedingung, text):
        nonlocal ok, fehler
        if bedingung:
            ok += 1
            print("  OK   %s" % text)
        else:
            fehler += 1
            print("  FEHL %s" % text)

    k11, k18, kvm = o11(), o18("lokal"), o18("vm")
    arch11 = formular_arch(k11, "sale.order", False)
    arch18 = formular_arch(k18, "sale.order", True)
    archvm = formular_arch(kvm, "sale.order", True)

    print("1) Reiter des Auftragsformulars")
    s11 = [p["string"] or p["name"] for p in seiten(arch11)]
    s18 = [p["string"] or p["name"] for p in seiten(arch18)]
    svm = [p["string"] or p["name"] for p in seiten(archvm)]
    print("       Odoo 11 : %s" % s11)
    print("       Odoo 18 : %s (lokal)" % s18)
    print("       Odoo 18 : %s (VM)" % svm)
    pruefe(s11 == REITER_O11, "Odoo 11 hat die erwarteten Reiter (%d)" % len(s11))
    pruefe(s18 == REITER_O18, "Odoo 18 lokal hat die erwarteten Reiter (%d)" % len(s18))
    pruefe(svm == REITER_O18, "Odoo 18 VM hat dieselben Reiter wie lokal")
    pruefe(s18[:1] + s18[-1:] == [REITER_O18[0], REITER_O18[-1]],
           "erster und letzter Reiter in Odoo 18 entsprechen Odoo 11 (umbenannt bzw. gleich)")

    print("\n2) Gruppen im Reiter 'Weitere Informationen'")
    g11 = {}
    for p in seiten(arch11):
        if (p["string"] or "") == "Weitere Informationen":
            g11 = p["gruppen"]
    g18 = {}
    for p in seiten(arch18):
        if (p["string"] or "") == "Weitere Informationen":
            g18 = p["gruppen"]
    print("       Odoo 11 : %s" % list(g11))
    print("       Odoo 18 : %s" % list(g18))
    for alt, neu in GRUPPEN_MAPPING.items():
        pruefe(alt in g11, "Odoo 11 hat die Gruppe '%s'" % alt)
        pruefe(neu in g18, "Odoo 18 hat die Zielgruppe '%s' (aus '%s')" % (neu, alt))
    for feld in ("user_id", "team_id", "tag_ids", "client_order_ref"):
        pruefe(feld in g11.get("Information Umsatz", []) and feld in g18.get("Verkauf", []),
               "Feld '%s' liegt in Odoo 11 und Odoo 18 in der entsprechenden Gruppe" % feld)
    for feld in ("fiscal_position_id", "invoice_status"):
        pruefe(feld in g11.get("Abrechnung", []) and feld in g18.get("Rechnungsstellung", []),
               "Feld '%s' liegt in Odoo 11 und Odoo 18 in der entsprechenden Gruppe" % feld)
    for feld in ("origin", "opportunity_id", "campaign_id", "medium_id", "source_id"):
        pruefe(feld in g11.get("Berichtswesen", []) and feld in g18.get("Nachverfolgung", []),
               "Feld '%s' liegt in Odoo 11 und Odoo 18 in der entsprechenden Gruppe" % feld)

    print("\n3) Hauptbereich (vor dem Notebook)")
    h11 = hauptbereich(arch11)["felder"]
    h18 = hauptbereich(arch18)["felder"]
    for feld in HAUPT_O11:
        pruefe(feld in h11, "Odoo 11 Hauptbereich enthaelt '%s'" % feld)
        pruefe(feld in h18, "Odoo 18 hat '%s' im Formular (Hauptbereich)" % feld)
    nur11 = [f for f in h11 if f not in h18 and f not in ("picking_ids", "delivery_count",
                                                          "timesheet_count", "project_ids",
                                                          "tasks_count", "payment_transaction_count",
                                                          "can_directly_mark_as_paid")]
    pruefe(not nur11, "keine unerwarteten Odoo-11-Hauptfelder ohne Odoo-18-Entsprechung (%s)" % (nur11 or "-"))

    print("\n4) Auftragszeilen-Formular")
    for name, k, ist18 in (("lokal", k18, True), ("VM", kvm, True)):
        p = seiten(formular_arch(k, "sale.order.line", ist18))
        pruefe(not p, "%s: Zeilenformular hat keinen Reiter (kein Notebook), wie in Odoo 11" % name)
    pruefe(not seiten(formular_arch(k11, "sale.order.line", False)),
           "Odoo 11: Zeilenformular hat ebenfalls keinen Reiter")
    n11 = k11.kw("ir.ui.view", "search_count", [[["model", "=", "sale.order.line"], ["type", "=", "form"]]])
    n18 = k18.kw("ir.ui.view", "search_count", [[["model", "=", "sale.order.line"], ["type", "=", "form"]]])
    nvm = kvm.kw("ir.ui.view", "search_count", [[["model", "=", "sale.order.line"], ["type", "=", "form"]]])
    print("       eigene Formularansichten sale.order.line: Odoo 11 %d | lokal %d | VM %d" % (n11, n18, nvm))
    pruefe(n11 == 0, "Odoo 11 fuehrt keine eigene Zeilenformularansicht (eingebettet)")
    pruefe(n18 == nvm == 1, "Odoo 18 fuehrt genau eine Zeilenformularansicht (lokal = VM)")

    print("\n5) Ansichten und Menueaktionen")
    for schluessel, k, ist18, anzahl in (("Odoo 11", k11, False, 2), ("Odoo 18 lokal", k18, True, 6),
                                         ("Odoo 18 VM", kvm, True, 6)):
        n = k.kw("ir.ui.view", "search_count", [[["model", "=", "sale.order"], ["type", "=", "form"]]])
        pruefe(n >= anzahl, "%s: mindestens %d Formularansichten fuer sale.order (%d)" % (schluessel, anzahl, n))

    print("\n%d OK / %d FEHL" % (ok, fehler))
    print("Odoo 11 Prod wurde ausschliesslich lesend verwendet, Odoo 18 nicht veraendert.")
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
