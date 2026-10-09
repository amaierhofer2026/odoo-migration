"""Read-only Scan auf verbliebene englische, sichtbare Bezeichnungen im Projektbereich.

Aufruf: python scripts/scan_projekt_englisch.py --instanz lokal|vm
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

# Sehr einfache Englisch-Erkennung: Woerter, die im Projektbereich englisch sind.
EN_WOERTER = re.compile(r"\b(the|of|as|by|with|on|for|and|or|to|in|from|is|are|not|tasks?|sub-?tasks?|attachments?|"
                        r"timesheets?|projects?|stages?|milestones?|members?|tickets?|updates?|ratings?|dependencies|"
                        r"collaborators?|recurrence|recurring|display|allow|show|count|active|open|closed|remaining|"
                        r"allocated|effective|planned|deadline|priority|assigned|assignees?|working|time|color|currency|"
                        r"sequence|status|visible|visibility|share|sharing|blocked|blocking|dependent|personal|portal|"
                        r"skills?|names?|number|total|spent|duration|stage|state|project|task|user|users|company|customer|"
                        r"partner|label|labels?|multi|company|warning|instruction|access|message|messages?|website|"
                        r"deadline|date|start|end|billable|bill|sales?|order|invoice|pricelist|recurrence)\b",
                        re.I)
# Felder, die bewusst neutral/identisch sind (kein Handlungsbedarf)
NEUTRAL = {"ID", "Name", "E-Mail", "Alias", "Tags", "Team", "Status", "Phase", "Stufe", "Frist", "Priorität",
           "Beschreibung", "Projekt", "Kunde", "Kontakt", "Aktiv", "Referenz", "Meilenstein"}


def arch(cli, modell, typ):
    try:
        res = cli.kw(modell, "get_views", [[(False, typ)]], options={"toolbar": False},
                     context={"lang": "de_DE"})
        for v in (res.get("views") or {}).values():
            return v.get("arch") or ""
    except Exception:  # noqa: BLE001
        pass
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    a = ap.parse_args()
    cli = o18(a.instanz)
    gesehen = set()
    treffer = []
    for modell, typen in (("project.project", ["form", "list", "kanban", "search"]),
                          ("project.task", ["form", "list", "kanban", "search"]),
                          ("project.task.type", ["form", "list"]),
                          ("project.tags", ["form", "list"])):
        for typ in typen:
            txt = arch(cli, modell, typ)
            if not txt:
                continue
            try:
                root = ET.fromstring(txt)
            except Exception:  # noqa: BLE001
                continue
            for e in root.iter():
                if e.tag not in ("field", "button", "filter"):
                    continue
                s = (e.get("string") or "").strip()
                if not s or s in NEUTRAL:
                    continue
                schluessel = (modell, e.get("name"), s)
                if schluessel in gesehen:
                    continue
                gesehen.add(schluessel)
                if EN_WOERTER.search(s):
                    treffer.append((modell, typ, e.tag, e.get("name"), s))
    print("=== Verbliebene englische, sichtbare Texte (%s) ===" % a.instanz)
    if not treffer:
        print("  keine")
    for m, t, tag, name, s in sorted(treffer):
        print("  %-18s %-8s %-7s %-26s %s" % (m, t, tag, name, s))
    print("\nAnzahl: %d" % len(treffer))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
