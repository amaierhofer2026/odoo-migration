"""Erzeugt die Ansicht fuer die Rechnungszeilen-Spalten im Odoo-11-Wortlaut.

Sucht die Listenansichten von account.move.line, die die Spalten Preis, Zwischensumme und
Rabatt rendern, und erzeugt daraus eine Ansicht mit den Odoo-11-Bezeichnungen. So bricht kein
Upgrade ab, weil nur Felder verwendet werden, die in der jeweiligen Ansicht existieren.

Aufruf: python scripts/erzeuge_rechnungszeilen_labels.py
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18

# technischer Feldname -> (Odoo-11-Bezeichnung, Standardspalte sichtbar machen?)
ZIEL = {"price_unit": ("Preis pro ME", False),
        "price_subtotal": ("Zwischensumme", False),
        "discount": ("Rabatt (%)", True)}


def main() -> int:
    k = o18("lokal")
    views = k.kw("ir.ui.view", "search_read",
                 [[("model", "=", "account.move.line"), ("type", "in", ("list", "tree"))],
                  ["id", "name", "arch_db", "priority"]], order="priority, id")
    bloecke = []
    for v in views:
        arch = v["arch_db"] or ""
        vorhanden = set(re.findall(r'<field name="([^"]+)"', arch))
        treffer = [(f, t, s) for f, (t, s) in ZIEL.items() if f in vorhanden]
        if not treffer or not arch.lstrip().startswith("<tree"):
            continue
        kennung = k.kw("ir.model.data", "search_read",
                       [[("model", "=", "ir.ui.view"), ("res_id", "=", v["id"])], ["module", "name"]])
        if not kennung:
            continue
        xmlid = "%s.%s" % (kennung[0]["module"], kennung[0]["name"])
        rel = re.sub(r"[^a-z0-9_]", "_", v["name"].lower())
        teil = ['    <record id="zeilen_%s" model="ir.ui.view">' % rel,
                '        <field name="name">account.move.line.list.itk.o11.%s</field>' % rel,
                '        <field name="model">account.move.line</field>',
                '        <field name="inherit_id" ref="%s"/>' % xmlid,
                '        <field name="priority">96</field>',
                '        <field name="arch" type="xml">']
        for feld, text, sichtbar in treffer:
            teil.append('            <xpath expr="//field[@name=\'%s\']" position="attributes">' % feld)
            teil.append('                <attribute name="string">%s</attribute>' % text)
            if sichtbar:
                teil.append('                <attribute name="optional">show</attribute>')
            teil.append('            </xpath>')
        teil += ['        </field>', '    </record>']
        bloecke.append((xmlid, "\n".join(teil)))
        print("Ansicht %-52s -> %s" % (xmlid, [t[0] for t in treffer]))
    inhalt = ('<?xml version="1.0" encoding="utf-8"?>\n<odoo>\n'
              '    <!-- Bereich Abrechnung: Rechnungszeilen-Spalten im Odoo-11-Wortlaut.\n'
              '         Nur string-Attribute; technische Feldnamen bleiben unveraendert. -->\n'
              + "\n".join(b[1] for b in bloecke) + "\n</odoo>\n")
    datei = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "addons", "itk_account_migration", "views", "account_move_line_labels.xml")
    open(datei, "w", encoding="utf-8", newline="\n").write(inhalt)
    print("geschrieben: %s (%d Ansichten)" % (datei, len(bloecke)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
