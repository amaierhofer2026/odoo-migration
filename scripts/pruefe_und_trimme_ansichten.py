"""Haelt in account_config_labels.xml nur die xpaths, deren Felder in der Zielansicht existieren.

Verhindert ParseError-Laeufe: erst pruefen, dann schreiben. Odoo 11 bleibt unberuehrt.

Aufruf: python scripts/pruefe_und_trimme_ansichten.py
"""
from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18

DATEI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "addons", "itk_account_migration", "views", "account_config_labels.xml")


def main() -> int:
    k = o18("lokal")
    text = open(DATEI, encoding="utf-8").read()
    ersetzt = 0
    entfernt = []
    for treffer in re.finditer(r'<field name="inherit_id" ref="([^"]+)"/>', text):
        pass
    # je Datensatz pruefen
    bloecke = re.split(r"(?=<record id=)", text)
    neu = []
    for block in bloecke:
        m = re.search(r'<field name="inherit_id" ref="([^"]+)"/>', block)
        if not m:
            neu.append(block)
            continue
        xmlid = m.group(1)
        modul, name = xmlid.split(".")
        daten = k.kw("ir.model.data", "search_read", [[("module", "=", modul), ("name", "=", name)],
                                                      ["res_id"]])
        if not daten:
            print("   Ansicht nicht gefunden: %s -> Datensatz wird verworfen" % xmlid)
            continue
        arch = k.kw("ir.ui.view", "read", [[daten[0]["res_id"]], ["arch_db"]])[0]["arch_db"] or ""
        vorhanden = set(re.findall(r'<field name="([^"]+)"', arch))
        def pruefe(x):
            feld = re.search(r"//field\[@name='([^']+)'\]", x.group(0))
            if not feld:
                return True
            ok = feld.group(1) in vorhanden
            if not ok:
                entfernt.append((xmlid, feld.group(1)))
            return ok
        # je xpath im Datenblock entscheiden
        def ersetze(xm):
            return xm.group(0) if pruefe(xm) else ""
        neuer_block = re.sub(r"<xpath expr=.*?</xpath>", ersetze, block, flags=re.S)
        if "//field" in neuer_block:
            neu.append(neuer_block)
            ersetzt += 1
        else:
            print("   Datensatz ohne gueltige xpaths verworfen: %s" % xmlid)
    open(DATEI, "w", encoding="utf-8", newline="\n").write("".join(neu))
    print("Gueltige Datensaetze: %d" % ersetzt)
    for x in entfernt:
        print("   entfernt (Feld nicht in der Ansicht): %s -> %s" % x)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
