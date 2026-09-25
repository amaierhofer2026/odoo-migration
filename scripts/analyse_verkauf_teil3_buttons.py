"""Read-only Analyse Verkauf Teil 3, Schritt 2: Buttons und Smart Buttons im Auftragsformular.

Liest aus dem Arch des Auftragsformulars (Odoo 11 Prod nur lesend, Odoo 18 lokal und VM):
  - Kopf-Buttons (header)
  - Smart Buttons (div.oe_stat_button mit Feld oder Button)
  - Buttons im Bereich der Auftragszeilen (z.B. Abschnitt/Notiz hinzufuegen)

Der Statuswechsel selbst (Zustaende und Uebergaenge) ist nicht Teil dieses Schritts.

Aufruf:
    python scripts/analyse_verkauf_teil3_buttons.py
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18
from analyse_verkauf_teil3_formulare import formular_arch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUTTON = re.compile(r"<button\b([^>]*?)/?>", re.S)
ATTR = re.compile(r'([a-zA-Z_]+)="([^"]*)"')


def attrs(text: str) -> dict:
    return {k: v for k, v in ATTR.findall(text)}


def block(arch: str, tag: str, attrs_filter: str) -> str:
    """Inhalt des ersten Blocks, dessen oeffnender Tag den Filter enthaelt."""
    m = re.search(r"<%s\b[^>]*%s[^>]*>" % (tag, attrs_filter), arch)
    if not m:
        return ""
    rest = arch[m.end():]
    tiefe, ende = 1, len(rest)
    for t in re.finditer(r"<%s\b[^>]*>|</%s>" % (tag, tag), rest):
        tiefe += 1 if t.group(0).startswith("<" + tag) else -1
        if tiefe == 0:
            ende = t.start()
            break
    return rest[:ende]


def kopf_buttons(arch: str) -> list:
    kopf = block(arch, "header", "")
    ergebnis = []
    for m in BUTTON.finditer(kopf):
        a = attrs(m.group(1))
        ergebnis.append({
            "name": a.get("name"), "string": a.get("string"), "type": a.get("type"),
            "class": a.get("class"), "states": a.get("states"), "attrs": a.get("attrs"),
            "groups": a.get("groups"), "confirm": a.get("confirm"), "special": a.get("special"),
        })
    return ergebnis


def smart_buttons(arch: str) -> list:
    """Smart Buttons: Buttons mit der Klasse oe_stat_button (Odoo 11 und 18 gleich aufgebaut)."""
    ergebnis = []
    for m in re.finditer(r'<button\b([^>]*oe_stat_button[^>]*)>', arch):
        a = attrs(m.group(1))
        rest = arch[m.end():]
        tiefe, ende = 1, len(rest)
        for t in re.finditer(r"<button\b[^>]*>|</button>", rest):
            tiefe += 1 if t.group(0).startswith("<button") else -1
            if tiefe == 0:
                ende = t.start()
                break
        inhalt = rest[:ende]
        ergebnis.append({
            "name": a.get("name"), "type": a.get("type"), "string": a.get("string"),
            "class": (a.get("class") or "")[:60], "groups": a.get("groups"),
            "attrs": a.get("attrs"),
            "felder": re.findall(r'<field\b[^>]*name="([^"]+)"', inhalt),
            "widget": (re.search(r'widget="([^"]+)"', inhalt) or [None, None])[1],
            "text": " ".join(x.strip() for x in re.findall(r'<span[^>]*>([^<]+)</span>', inhalt))[:60],
        })
    return ergebnis


def zeilen_buttons(arch: str) -> list:
    """Buttons innerhalb der eingebetteten Auftragszeilen-Liste."""
    bereich = block(arch, "field", "order_line")
    ergebnis = []
    for m in BUTTON.finditer(bereich):
        a = attrs(m.group(1))
        ergebnis.append({"name": a.get("name"), "string": a.get("string"), "type": a.get("type"),
                         "groups": a.get("groups")})
    # zusaetzlich: Steuerelemente der Liste (Abschnitt/Notiz) ueber Buttonnamen im gesamten Arch
    for name in ("add_section", "add_note", "add_from_catalog"):
        if re.search(r'<button\b[^>]*name="%s"' % name, arch):
            if not any(e["name"] == name for e in ergebnis):
                ergebnis.append({"name": name, "string": None, "type": "object", "gruppen": None})
    return ergebnis


def main() -> int:
    daten = {}
    for schluessel, client, ist18 in (("o11", o11(), False), ("o18", o18("lokal"), True),
                                      ("vm", o18("vm"), True)):
        arch = formular_arch(client, "sale.order", ist18)
        daten[schluessel] = {"kopf": kopf_buttons(arch), "smart": smart_buttons(arch),
                             "zeilen": zeilen_buttons(arch)}
    ziel = os.path.join(REPO, "docs", "_verkauf_teil3_buttons.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("Daten: %s" % ziel)

    for schluessel in ("o11", "o18"):
        d = daten[schluessel]
        print("\n================ %s ================" % schluessel.upper())
        print("Kopf-Buttons (%d):" % len(d["kopf"]))
        for b in d["kopf"]:
            print("   %-28s %-30s type=%-8s states=%-24s groups=%-12s attrs=%s"
                  % (b["name"], (b["string"] or "")[:30], b["type"], (b["states"] or "")[:24],
                     (b["groups"] or "-")[:12], (b["attrs"] or "")[:80]))
        print("Smart Buttons (%d):" % len(d["smart"]))
        for s in d["smart"]:
            print("   name=%-28s felder=%-30s widget=%-10s groups=%-10s attrs=%s"
                  % (s["name"], ",".join(s["felder"])[:30], s["widget"], (s["groups"] or "-")[:10],
                     (s["attrs"] or "")[:60]))
        print("Buttons in den Auftragszeilen (%d): %s"
              % (len(d["zeilen"]), [z["name"] for z in d["zeilen"]]))
    print("\nMenue-/Wortlautvergleich lokal gegen VM (Kopf-Buttons):",
          [b["name"] for b in daten["o18"]["kopf"]] == [b["name"] for b in daten["vm"]["kopf"]])
    print("Odoo 11 Prod wurde ausschliesslich lesend verwendet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
