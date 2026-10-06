"""Vollstaendiger Feldabgleich Zahlungsformular: Odoo 11 gegen Odoo 18 (nur lesend).

Aufruf: python scripts/vergleich_zahlungsformular_vollstaendig.py [o11|o18|lokal|vm|beide]

Gibt je Formular aus:
  - Kopfzeile: Statusleiste und Knoepfe
  - Gruppen in Reihenfolge mit ihren Feldern (Name, Beschriftung, required, readonly, widget)
  - Auswahlwerte der Auswahlfelder
  - Smart Buttons
"""
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, r"C:/Odoo-Test/scripts")
from _o11o18_client import o11, o18  # noqa: E402

CTX = {"lang": "de_DE"}


def attrs(node):
    d = {k: v for k, v in node.attrib.items()}
    for eintrag in (node.get("attrs") or "").split(","):
        if ":" in eintrag:
            k, v = eintrag.split(":", 1)
    return d


def beschriftung(feld, modellfelder):
    s = feld.get("string")
    if s:
        return s
    return (modellfelder.get(feld.get("name"), {}) or {}).get("string", "?")


def zeige_formular(titel, arch, modellfelder, mit_gruppen=True):
    print("\n" + "=" * 100)
    print(titel)
    print("=" * 100)
    w = ET.fromstring(arch)

    # Kopfzeile
    for header in w.iter("header"):
        for kind in list(header):
            if kind.tag == "field":
                print("  [Kopf] field %-26s string=%r widget=%s invisible=%s"
                      % (kind.get("name"), kind.get("string"), kind.get("widget"),
                         kind.get("invisible")))
            elif kind.tag == "button":
                print("  [Kopf] button %-25s string=%r invisible=%s"
                      % (kind.get("name"), kind.get("string"), kind.get("invisible")))
        for b in header.iter("button"):
            print("  [Kopf] button(inner) %-18s string=%r invisible=%s"
                  % (b.get("name"), b.get("string"), b.get("invisible")))

    # Gruppen mit Inhalt
    gesehen = set()
    for g in w.iter("group"):
        felder = [f.get("name") for f in list(g) if f.tag == "field"]
        if not felder:
            continue
        kennung = tuple(felder)
        if kennung in gesehen:
            continue
        gesehen.add(kennung)
        print("  [Gruppe name=%s string=%r]" % (g.get("name"), g.get("string")))
        for f in list(g):
            if f.tag != "field":
                continue
            print("     %-28s label=%-30r req=%-8s readonly=%-6s widget=%-14s col/inv=%s/%s"
                  % (f.get("name"), beschriftung(f, modellfelder)[:30],
                     f.get("required") or "-", f.get("readonly") or "-",
                     f.get("widget") or "-", f.get("column_invisible") or "-",
                     f.get("invisible") or "-"))

    # alle Felder, die in keiner Gruppe stehen (flach)
    print("  [sonstige Felder]")
    for f in w.iter("field"):
        if f.get("name") in {x.get("name") for g in w.iter("group") for x in list(g) if x.tag == "field"}:
            continue
        print("     %-28s label=%-30r req=%-8s readonly=%-6s widget=%-14s invisible=%s"
              % (f.get("name"), beschriftung(f, modellfelder)[:30], f.get("required") or "-",
                 f.get("readonly") or "-", f.get("widget") or "-", f.get("invisible") or "-"))

    # Seiten/Reiter
    for seite in w.iter("page"):
        print("  [Reiter] name=%s string=%r" % (seite.get("name"), seite.get("string")))

    # Smart Buttons
    print("  [Smart Buttons]")
    for b in w.iter("button"):
        if b.get("class") and "oe_stat_button" in (b.get("class") or ""):
            print("     name=%-26s string=%r" % (b.get("name"), b.get("string")))


# ------------------------------------------------------------------ Odoo 11
if len(sys.argv) == 1 or sys.argv[1] in ("o11", "beide"):
    k = o11()
    felder11 = k.kw("account.payment", "fields_get", [[], ["string", "type", "selection", "required", "readonly"]], context=CTX)
    gv = k.kw("account.payment", "fields_view_get", [False, "form"], context=CTX)
    zeige_formular("ODOO 11: account.payment.form (zusammengesetzt)", gv["arch"], felder11)
    print("\n  [Auswahlwerte Odoo 11]")
    for f in ("payment_type", "partner_type", "state", "payment_method", "journal_id"):
        d = felder11.get(f)
        if d and d.get("type") == "selection":
            print("     %-14s %s" % (f, d.get("selection")))
    print("  [Modellpflicht Odoo 11]")
    for f in ("partner_id", "amount", "journal_id", "date", "memo", "payment_type", "partner_type"):
        d = felder11.get(f) or {}
        print("     %-22s required=%s readonly=%s typ=%s" % (f, d.get("required"), d.get("readonly"), d.get("type")))

# ------------------------------------------------------------------ Odoo 18
for inst in (["lokal", "vm"] if len(sys.argv) > 1 and sys.argv[1] in ("lokal", "vm", "beide") else []):
    k = o18(inst)
    felder18 = k.kw("account.payment", "fields_get", [[], ["string", "type", "selection", "relation"]], context=CTX)
    gv = k.kw("account.payment", "get_view", [False, "form"], context=CTX)
    zeige_formular("ODOO 18 (%s): account.payment Formular (zusammengesetzt, mit ITK-Vererbung)" % inst,
                   gv["arch"], felder18)
    print("\n  [Auswahlwerte Odoo 18]")
    for f in ("payment_type", "partner_type", "state", "payment_method_line_id", "journal_id"):
        d = felder18.get(f)
        if d and d.get("type") == "selection":
            print("     %-22s %s" % (f, d.get("selection")))
    print("  [Modellpflicht Odoo 18]")
    for f in ("partner_id", "amount", "journal_id", "date", "memo", "payment_type", "partner_type"):
        d = felder18.get(f) or {}
        print("     %-22s required=%s typ=%s" % (f, d.get("required"), d.get("type")))
