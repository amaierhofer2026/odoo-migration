"""Strukturvergleich Formularansichten: Odoo 11 gegen Odoo 18 (nur lesend).

Aufruf: python scripts/vergleiche_formulare.py <modell> [<modell> ...]
Gibt je Modell die sichtbaren Felder mit Beschriftung in Reihenfolge, Gruppen und Reiter aus.
"""
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402


def hole_arch(client, modell, version):
    if version == 11:
        try:
            return client.kw(modell, "fields_view_get", [False, "form"], context={"lang": "de_DE"}).get("arch")
        except Exception as fehler:
            return "FEHLER: %s" % str(fehler)[:120]
    try:
        gv = client.kw(modell, "get_views", [[[False, "form"]]], context={"lang": "de_DE"})
        return list((gv.get("views") or {}).values())[0]["arch"]
    except Exception as fehler:
        return "FEHLER: %s" % str(fehler)[:120]


def ausgabe(arch, ueberschrift):
    print("=== %s ===" % ueberschrift)
    if not arch or arch.startswith("FEHLER"):
        print("   ", arch)
        return
    w = ET.fromstring(arch)
    for c in w.iter():
        tag = c.tag.split("}")[-1]
        if tag == "group":
            name = c.get("name") or c.get("string") or "-"
            if c.get("name") or c.get("string"):
                print("   [group %s]" % name)
        elif tag == "page":
            print("   [Reiter %r invisible=%s]" % ((c.get("string") or "")[:30], (c.get("invisible") or "")[:24]))
        elif tag == "field":
            inv = c.get("invisible") or ""
            if inv in ("1", "True"):
                continue
            print("      %-30s string=%-28r widget=%-16s invisible=%s" % (
                c.get("name"), (c.get("string") or "")[:28], (c.get("widget") or "-")[:16], inv[:26]))
        elif tag in ("button", "label"):
            if tag == "label":
                print("      label %-24s string=%r" % (c.get("for"), (c.get("string") or "")[:30]))
            else:
                print("      button %-24s string=%r" % (c.get("name"), (c.get("string") or "")[:30]))


for modell in sys.argv[1:] or ["res.partner", "product.template"]:
    print("\n################ %s ################" % modell)
    ausgabe(hole_arch(o11(), modell, 11), "Odoo 11 %s" % modell)
    ausgabe(hole_arch(o18("lokal"), modell, 18), "Odoo 18 %s" % modell)
