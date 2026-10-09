"""Read-only Vergleich der gerenderten Projekt-Ansichten (Odoo 11 gegen Odoo 18).

Aufruf:
  python scripts/projekt_views.py --quelle o11|lokal|vm [--modell project.project] [--typ form]

Es wird get_views mit Kontext lang=de_DE gelesen (Fallback fields_view_get fuer Odoo 11)
und daraus eine lineare Struktur (Seiten, Felder, Buttons, Gruppen, Spalten, Filter)
ausgegeben. Es werden ausschliesslich lesende Aufrufe gemacht.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18  # noqa: E402


def hole_arch(cli, modell, typ):
    """Liefert das gerenderte Arch (de_DE) fuer einen Ansichtstyp."""
    try:
        res = cli.kw(modell, "get_views", [[(False, typ)]],
                     options={"toolbar": False}, context={"lang": "de_DE"})
        views = res.get("views") or {}
        for _k, v in views.items():
            return v.get("arch")
    except Exception:  # noqa: BLE001
        pass
    # Fallback Odoo 11
    res = cli.kw(modell, "fields_view_get", [], view_type=typ, context={"lang": "de_DE"})
    return res.get("arch")


def finde_all(root, tag):
    return [e for e in root.iter() if e.tag == tag]


def strukturiere(arch):
    root = ET.fromstring(arch)
    d = {"seiten": [], "felder": [], "buttons": [], "gruppen": [], "spalten": [],
         "filter": [], "gruppierungen": [], "suchfelder": []}
    if root.tag in ("form", "list", "tree", "kanban"):
        for e in root.iter():
            if e.tag == "page":
                d["seiten"].append({"name": e.get("name"), "string": e.get("string")})
            elif e.tag == "field":
                d["felder"].append({
                    "name": e.get("name"), "string": e.get("string"), "widget": e.get("widget"),
                    "invisible": e.get("invisible"), "readonly": e.get("readonly"),
                    "required": e.get("required"), "optional": e.get("optional"),
                    "domain": e.get("domain"), "context": (e.get("context") or "")[:40]})
            elif e.tag == "button":
                d["buttons"].append({"name": e.get("name"), "string": e.get("string"),
                                     "type": e.get("type"), "class": e.get("class")})
            elif e.tag == "group":
                d["gruppen"].append({"string": e.get("string"), "name": e.get("name")})
        d["spalten"] = [{"name": f["name"], "string": f.get("string"), "optional": f.get("optional")}
                        for f in d["felder"]]
    elif root.tag == "search":
        for e in root.iter():
            if e.tag == "field":
                d["suchfelder"].append({"name": e.get("name"), "string": e.get("string"),
                                        "filter_domain": e.get("filter_domain")})
            elif e.tag == "filter":
                d["filter"].append({"name": e.get("name"), "string": e.get("string"),
                                    "domain": e.get("domain"), "context": (e.get("context") or "")[:60],
                                    "groupby": [g.get("name") for g in e.iter("groupby")]})
            elif e.tag == "groupby":
                d["gruppierungen"].append(e.get("name"))
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quelle", required=True, choices=["o11", "lokal", "vm"])
    ap.add_argument("--modell", default="project.project")
    ap.add_argument("--typ", default="form")
    a = ap.parse_args()
    cli = o11() if a.quelle == "o11" else o18(a.quelle)
    arch = hole_arch(cli, a.modell, a.typ)
    if not arch:
        print("KEIN ARCH fuer %s %s" % (a.modell, a.typ))
        return 1
    d = strukturiere(arch)
    print("### %s %s %s (%d Zeichen)" % (a.quelle, a.modell, a.typ, len(arch)))
    if a.typ in ("form", "tree", "list", "kanban"):
        print("\nSeiten (%d):" % len(d["seiten"]))
        for s in d["seiten"]:
            print("  %-22s %s" % (s["name"], s["string"]))
        print("\nFelder (%d):" % len(d["felder"]))
        for f in d["felder"]:
            zusatz = []
            for k in ("widget", "invisible", "readonly", "required", "optional", "domain"):
                if f.get(k):
                    zusatz.append("%s=%s" % (k, f[k]))
            print("  %-32s %-44s %s" % (f["name"], (f.get("string") or "")[:44], "; ".join(zusatz)))
        print("\nButtons (%d):" % len(d["buttons"]))
        for b in d["buttons"]:
            print("  %-30s %-34s typ=%s" % (b["name"], (b.get("string") or "")[:34], b["type"]))
        print("\nGruppen (%d):" % len(d["gruppen"]))
        for g in d["gruppen"]:
            print("  %-24s %s" % (g["name"], g["string"]))
    elif a.typ == "search":
        print("\nSuchfelder (%d):" % len(d["suchfelder"]))
        for f in d["suchfelder"]:
            print("  %-28s %s" % (f["name"], f.get("string")))
        print("\nFilter (%d):" % len(d["filter"]))
        for f in d["filter"]:
            print("  %-28s %-30s dom=%s" % (f["name"], (f.get("string") or "")[:30],
                                            (f["domain"] or "")[:60]))
        print("\nGruppierungen: %s" % ", ".join(d["gruppierungen"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
