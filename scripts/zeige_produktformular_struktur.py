"""Notebook-Struktur des Produktformulars ausgeben (Reiter, Gruppen, Felder in Reihenfolge).

Read-only. Aufruf: python scripts/zeige_produktformular_struktur.py o11|lokal|vm [--felder]
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def arch(instanz):
    """Liefert den zusammengefuehrten Formular-Arch von product.template."""
    from _o11o18_client import o11, o18
    if instanz == "o11":
        k = o11()
        r = k.kw("product.template", "fields_view_get", [False, "form"], toolbar=False,
                 context={"lang": "de_DE"})
        return r["arch"]
    k = o18(instanz)
    r = k.kw("product.template", "get_views", [[[False, "form"]]], context={"lang": "de_DE"})
    views = r["views"] if isinstance(r, dict) and "views" in r else r
    return views["form"]["arch"]


def zeige(el, tiefe, felder):
    einzug = "   " * tiefe
    for kind in el:
        tag = kind.tag
        if tag in ("field", "label", "button"):
            info = " name=%s" % kind.get("name") if kind.get("name") else ""
            for a in ("string", "widget", "invisible", "readonly", "required", "attrs", "class"):
                if kind.get(a):
                    info += " %s=%s" % (a, kind.get(a)[:70])
            if tag == "label":
                print("%s<label for=%s>%s" % (einzug, kind.get("for"), info))
            elif tag == "button":
                print("%s<button%s>" % (einzug, info))
            elif felder:
                print("%s<field%s>" % (einzug, info))
                for a in kind:
                    if a.tag in ("field", "label"):
                        zeige(kind, tiefe + 1, felder)
            else:
                print("%s<field%s>" % (einzug, info))
        elif tag in ("group", "page", "notebook", "div", "h1", "h2", "separator", "form", "sheet"):
            info = ""
            if kind.get("name"):
                info += " name=%s" % kind.get("name")
            if kind.get("string"):
                info += ' string="%s"' % kind.get("string")
            if kind.get("invisible"):
                info += " invisible=%s" % kind.get("invisible")[:60]
            if kind.get("col"):
                info += " col=%s" % kind.get("col")
            print("%s<%s%s>" % (einzug, tag, info))
            if tag in ("group", "page", "notebook", "form", "sheet", "div", "h1", "h2"):
                zeige(kind, tiefe + 1, felder)
        else:
            print("%s<%s>" % (einzug, tag))


ap = argparse.ArgumentParser()
ap.add_argument("instanz")
ap.add_argument("--felder", action="store_true", help="auch Felder innerhalb von Gruppen")
a = ap.parse_args()
w = arch(a.instanz)
open(os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "Temp", "prodform", "arch_%s.xml" % a.instanz),
     "w", encoding="utf-8").write(w) if os.path.isdir(
    os.path.join(os.environ.get("LOCALAPPDATA", "/tmp"), "Temp", "prodform")) else None
print("Arch-Laenge:", len(w))
wurzel = ET.fromstring(w)
nb = wurzel.find(".//notebook")
if nb is None:
    print("kein Notebook")
    raise SystemExit(1)
zeige(nb, 0, a.felder)
