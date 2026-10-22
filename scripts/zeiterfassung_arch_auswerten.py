"""Lokale Auswertung der erhobenen Rohdaten (kein RPC): Ansichts-Inhalte lesbar machen.

Aufruf:
  python scripts/zeiterfassung_arch_auswerten.py --quelle o11 [--modell account.analytic.line]

Liest zeiterfassung_<quelle>_teil2.json (Felder/Buttons/Gruppen je Ansicht) und
teil3.json (Suchfilter/Gruppierungen) und gibt eine kompakte Liste aus.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import xml.etree.ElementTree as ET

STD = os.path.join(os.environ.get("USERPROFILE", "."), "Desktop",
                   "Odoo18-Zeiterfassung-Session135", "rohdaten")


def attribut_text(e):
    teile = []
    for k in ("invisible", "readonly", "required", "widget", "domain", "options",
              "sum", "avg", "optional", "groups", "string", "states", "force_save",
              "decoration-danger", "decoration-info", "decoration-muted", "password", "no_create"):
        if k in e.attrib:
            teile.append("%s=%s" % (k, e.attrib[k]))
    return "; ".join(teile)


def arch_lesen(arch, label):
    print("\n--- %s ---" % label)
    if not arch or arch.startswith("__FEHLER__"):
        print("   (kein Arch)", str(arch)[:120])
        return
    arch = re.sub(r"<!--.*?-->", "", arch, flags=re.S)
    try:
        root = ET.fromstring(arch)
    except Exception as exc:  # noqa: BLE001
        print("   XML-Fehler:", exc)
        print(arch[:600])
        return
    # Seiten
    seiten = [p.get("string") or p.get("name") for p in root.iter("page")]
    if seiten:
        print("   Seiten:", seiten)
    # Felder in Reihenfolge
    felder = []
    for f in root.iter("field"):
        name = f.get("name")
        at = attribut_text(f)
        felder.append("%-26s %s" % (name, at))
    print("   Felder (%d):" % len(felder))
    for f in felder:
        print("     ", f)
    # Buttons
    bts = []
    for tag in ("button",):
        for b in root.iter(tag):
            bts.append("%-28s name=%-26s type=%s %s" % ((b.get("string") or "")[:28], b.get("name"),
                                                      b.get("type"), attribut_text(b)))
    if bts:
        print("   Buttons (%d):" % len(bts))
        for b in bts:
            print("     ", b)
    # Filter / Gruppierungen (search)
    for tag in ("filter", "group"):
        el = [e for e in root.iter(tag)]
        if el and tag == "filter":
            print("   Filter (%d):" % len(el))
            for f in el:
                dom = (f.get("domain") or "").replace("\n", " ")
                ctx = (f.get("context") or "").replace("\n", " ")
                print("      %-30s %-28s dom=%s %s" % (f.get("name"), (f.get("string") or "")[:28],
                                                       dom[:90], ctx[:80]))
    gruppen = [e for e in root.iter("group") if e.get("expand") is not None or e.get("string") is None]
    sep = [e.get("string") for e in root.iter("separator")]
    if sep:
        print("   Trenner:", sep)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quelle", required=True, choices=["o11", "lokal", "vm"])
    ap.add_argument("--ordner", default=STD)
    ap.add_argument("--modell", default="account.analytic.line")
    a = ap.parse_args()

    p2 = os.path.join(a.ordner, "zeiterfassung_%s_teil2.json" % a.quelle)
    with open(p2, encoding="utf-8") as fh:
        d2 = json.load(fh)
    p3 = os.path.join(a.ordner, "zeiterfassung_%s_teil3.json" % a.quelle)
    d3 = {}
    if os.path.exists(p3):
        with open(p3, encoding="utf-8") as fh:
            d3 = json.load(fh)

    print("### Quelle:", a.quelle, " Modell:", a.modell)
    for v in d2.get("ansichten", []):
        if v["model"] != a.modell:
            continue
        arch = d2.get("arches", {}).get(str(v["id"])) or d2.get("arches", {}).get(v["id"])
        arch_lesen(arch, "%s | %s | prio %s | %s | xml=%s" % (v["type"], v["name"], v["priority"],
                                                             "primary" if v["mode"] == "primary" else "inherit",
                                                             v["xml_id"]))
    for vid, arch in (d3.get("such_arch") or {}).items():
        info = next((v for v in d3.get("suchansichten", []) if str(v["id"]) == str(vid)), None)
        if not info or info["model"] != a.modell:
            continue
        arch_lesen(arch, "SEARCH | %s | xml=%s" % (info["name"], info["xml_id"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
