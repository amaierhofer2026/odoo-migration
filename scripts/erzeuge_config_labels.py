"""Erzeugt account_config_labels.xml automatisch aus den gewuenschten Odoo-11-Bezeichnungen.

Sucht je Modell die Formularansicht, die das Feld wirklich enthaelt, und setzt dort das
Attribut string. So koennen keine xpaths ins Leere zeigen und kein Upgrade bricht ab.

Aufruf: python scripts/erzeuge_config_labels.py
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18

# Modell -> [(technischer Feldname, sichtbare Odoo-11-Bezeichnung)]
WUNSCH = {
    "account.tax": [("description", "Bezeichnung auf Rechnungen"), ("type_tax_use", "Steuergültigkeit"),
                    ("price_include", "Beinhaltet im Preis"),
                    ("include_base_amount", "Auswirkung auf nachfolgende Steuern"),
                    ("tax_exigibility", "Fällige Steuer"),
                    ("analytic", "In Kostenrechnung einschliessen")],
    "account.journal": [("name", "Journalbezeichnung"), ("bank_statements_source", "Bank Datenübertragungen"),
                        ("refund_sequence", "Fest zugeordnete Gutschrift-Sequenz"),
                        ("sequence", "Nummernfolge")],
    "account.fiscal.position": [("name", "Steuerzuordnung"), ("vat_required", "USt-IdNr. ist zwingend")],
    "account.payment.term": [("sequence", "Nummernfolge")],
    "res.partner.bank": [("bank_bic", "Bank Identifikations-Code"), ("acc_type", "Kontotyp"),
                         ("journal_id", "Finanz-Journal")],
    "product.category": [("property_account_income_categ_id", "Erlöskonto"),
                         ("removal_strategy_id", "Erzwinge Verbrauchsfolge")],
    "res.currency": [("position", "Position des Symbols"),
                     ("currency_subunit_label", "Währungs-Untereinheit")],
    "account.move.reversal": [("journal_id", "Benutze das spezifische Journal")],
    "account.analytic.account": [("line_ids", "Kostenstellen Buchungen"),
                                 ("project_count", "Projekt-Anzahl"), ("project_ids", "Projekte")],
}

KOPF = """<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!--
        Bereich Abrechnung, Konfiguration: sichtbare Feldbezeichnungen im Odoo-11-Wortlaut.
        Automatisch erzeugt von scripts/erzeuge_config_labels.py: je Feld wird die Formularansicht
        gesucht, die es enthaelt. Technische Feldnamen, Modelle und Funktionen bleiben unveraendert;
        Odoo-18-Zusatzfelder und Zusatzfunktionen bleiben erhalten.
    -->
"""


def main() -> int:
    k = o18("lokal")
    bloecke = []
    offen = []
    for modell, felder in WUNSCH.items():
        views = k.kw("ir.ui.view", "search_read",
                     [[("model", "=", modell), ("type", "=", "form")], ["id", "name", "arch_db", "priority"]],
                     order="priority, id")
        xpaths = []
        for feld, text in felder:
            ziel = None
            for v in views:
                if re.search(r"<field name=\"%s\"" % re.escape(feld), v["arch_db"] or ""):
                    ziel = v
                    break
            if ziel is None:
                offen.append("%s.%s (%s)" % (modell, feld, text))
                continue
            xpaths.append((ziel, feld, text))
        if not xpaths:
            continue
        # je Ansicht ein Datensatz
        nach_ansicht = {}
        for v, feld, text in xpaths:
            nach_ansicht.setdefault(v["id"], {"name": v["name"], "felder": []})["felder"].append((feld, text))
        for ansicht_id, daten in nach_ansicht.items():
            rel = re.sub(r"[^a-z0-9_]", "_", daten["name"].lower())
            teil = ['    <record id="auto_%s_%s" model="ir.ui.view">' % (modell.replace(".", "_"), rel)]
            teil.append('        <field name="name">%s.itk.o11.%s</field>' % (modell, rel))
            teil.append('        <field name="model">%s</field>' % modell)
            teil.append('        <field name="inherit_id" ref="%(xmlid)s"/>')
            teil.append('        <field name="priority">99</field>')
            teil.append('        <field name="arch" type="xml">')
            for feld, text in daten["felder"]:
                teil.append('            <xpath expr="//field[@name=\'%s\']" position="attributes">' % feld)
                teil.append('                <attribute name="string">%s</attribute>' % text)
                teil.append('            </xpath>')
            teil.append('        </field>')
            teil.append('    </record>')
            xmlid = k.kw("ir.model.data", "search_read",
                         [[("model", "=", "ir.ui.view"), ("res_id", "=", ansicht_id)],
                          ["module", "name"]])
            kennung = "%s.%s" % (xmlid[0]["module"], xmlid[0]["name"]) if xmlid else None
            if kennung is None:
                offen.append("Ansicht ohne xmlid: %s" % daten["name"])
                continue
            bloecke.append("\n".join(teil) % {"xmlid": kennung})
    datei = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "addons", "itk_account_migration", "views", "account_config_labels.xml")
    open(datei, "w", encoding="utf-8", newline="\n").write(KOPF + "\n".join(bloecke) + "\n</odoo>\n")
    print("Datensaetze geschrieben: %d" % len(bloecke))
    for x in offen:
        print("   nicht gefunden: %s" % x)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
