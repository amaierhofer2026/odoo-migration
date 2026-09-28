"""Read-only Analyse Verkauf Teil 3, Schritt 3: Statuswerte, Uebergaenge und Statusbuttons.

Liest fuer sale.order (Odoo 11 Prod nur lesend, Odoo 18 lokal und VM):
  - Auswahlwerte des Feldes state und Anzahl der Datensaetze je Zustand
  - Statusleiste (statusbar_visible)
  - Kopf-Buttons mit Sichtbarkeitsbedingung und Zielzustand, ausgewertet je Zustand
  - zusaetzlich mit den echten Werten eines Testauftrags (fuer Bedingungen mit weiteren Feldern)

Ergebnis: docs/_verkauf_teil3_status.json und eine Uebersicht auf der Konsole.

Aufruf:
    python scripts/analyse_verkauf_teil3_status.py
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o11, o18
from analyse_verkauf_teil3_formulare import formular_arch
from analyse_verkauf_teil3_buttons import attrs
from sichtbarkeit_bedingungen import invisibles_o11, sichtbar, sichtbar_mit_werten

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = {"lang": "de_DE"}

ZIEL = {
    "action_confirm": "sale",
    "action_cancel": "cancel (ueber Assistent)",
    "action_draft": "draft",
    "action_done": "sale, gesperrt",
    "action_lock": "sale, gesperrt",
    "action_unlock": "sale, entsperrt",
    "action_quotation_send": "sent (nach dem Versand)",
    "action_quotation_sent": "sent",
    "print_quotation": "kein Statuswechsel",
    "action_preview_sale_order": "kein Statuswechsel",
    "payment_action_capture": "kein Statuswechsel",
    "payment_action_void": "kein Statuswechsel",
    "action_recovery_email_send": "kein Statuswechsel",
    "425": "kein Statuswechsel (Rechnungsassistent)",
    "428": "kein Statuswechsel (Rechnungsassistent)",
}
WERTE_FELDER = ["name", "state", "locked", "invoice_status", "invoice_count", "picking_ids",
                "authorized_transaction_ids", "id"]


def header_block(arch: str) -> str:
    """Der Inhalt des ersten <header> im Formular."""
    kopf = re.search(r"<header\b[^>]*>", arch)
    if not kopf:
        return ""
    rest = arch[kopf.end():]
    tiefe, ende = 1, len(rest)
    for t in re.finditer(r"<header\b[^>]*>|</header>", rest):
        tiefe += 1 if t.group(0).startswith("<header") else -1
        if tiefe == 0:
            ende = t.start()
            break
    return rest[:ende]


def direkte_buttons(block: str) -> list:
    """Nur Buttons, die unmittelbar im header stehen (keine aus eingebetteten Ansichten)."""
    ergebnis, tiefe, pos = [], 0, 0
    for t in re.finditer(r"<(/?)([a-zA-Z][\w:]*)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*?)(/?)>", block):
        schliessend, name, attribute, selbst = t.group(1), t.group(2), t.group(3), t.group(4)
        if schliessend:
            if name in ("button", "field"):
                tiefe = max(0, tiefe - 1)
            continue
        if name == "button" and tiefe == 0:
            ergebnis.append(attrs(attribute))
        if name in ("button", "field") and not selbst:
            tiefe += 1
    return ergebnis


def button_eintraege(arch: str, ist18: bool) -> list:
    ergebnis = []
    for a in direkte_buttons(header_block(arch)):
        if not a.get("name"):
            continue
        if ist18:
            bedingung = a.get("invisible") or ""
        elif a.get("states"):
            bedingung = "state not in %s" % repr([x.strip() for x in a["states"].split(",")])
        else:
            bedingung = invisibles_o11(a.get("attrs") or "")
        ergebnis.append({
            "name": a["name"], "string": a.get("string"), "type": a.get("type"),
            "groups": a.get("groups"), "bedingung": bedingung,
            "ziel": ZIEL.get(a["name"], "unklar"),
        })
    return ergebnis


def main() -> int:
    daten = {}
    print("Zustandswerte, Anzahl und Statusbuttons (Odoo 11 Prod nur lesend)\n")
    for schluessel, client, ist18 in (("o11", o11(), False), ("o18", o18("lokal"), True),
                                      ("vm", o18("vm"), True)):
        fg = client.kw("sale.order", "fields_get", [["state"], ["selection", "string"]], context=SP)
        auswahl = [s[0] for s in fg["state"]["selection"]]
        anzahl = {g["state"]: g["state_count"]
                  for g in client.kw("sale.order", "read_group", [[], ["state"], ["state"]], context=SP)}
        gesamt = client.kw("sale.order", "search_count", [[]], context=SP)
        arch = formular_arch(client, "sale.order", ist18)
        leiste = re.search(r'statusbar_visible="([^"]+)"', arch)
        # Testauftrag mit echten Werten (fuer Bedingungen mit weiteren Feldern)
        vorhanden = [f for f in WERTE_FELDER
                     if f in client.kw("sale.order", "fields_get", [[], ["type"]], context=SP)]
        kandidat = client.kw("sale.order", "search_read",
                             [[("state", "=", "draft")], vorhanden], context=SP)
        if not kandidat:
            kandidat = client.kw("sale.order", "search_read", [[], vorhanden], context=SP)[:1]
        daten[schluessel] = {
            "auswahl": auswahl, "anzahl": anzahl, "gesamt": gesamt,
            "statusleiste": leiste.group(1) if leiste else None,
            "testwerte": kandidat[0] if kandidat else {},
            "knoepfe": button_eintraege(arch, ist18),
        }
        print("%s: Zustandswerte %s | Statusleiste %s | Anzahl je Zustand %s (gesamt %d)"
              % (schluessel.upper(), auswahl, leiste.group(1) if leiste else "-", anzahl, gesamt))

    ziel = os.path.join(REPO, "docs", "_verkauf_teil3_status.json")
    with open(ziel, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("\nDaten: %s" % ziel)

    for schluessel in ("o11", "o18"):
        d = daten[schluessel]
        werte = {k: v for k, v in d["testwerte"].items() if k in WERTE_FELDER}
        print("\n=== %s: Kopf-Buttons je Zustand ===" % schluessel.upper())
        for z in d["auswahl"]:
            zeilen = []
            for b in d["knoepfe"]:
                sicht_arch = sichtbar(b["bedingung"], z)
                probe = dict(werte, state=z)
                sicht_daten = sichtbar_mit_werten(b["bedingung"], z, probe)
                if sicht_arch is True:
                    zeilen.append("      %-24s -> %-28s immer" % (b["name"], b["ziel"]))
                elif sicht_arch is False:
                    continue
                else:
                    zeilen.append("      %-24s -> %-28s %s (Testauftrag %s: %s)"
                                  % (b["name"], b["ziel"], sicht_arch,
                                     d["testwerte"].get("name", "-"),
                                     "sichtbar" if sicht_daten is True else
                                     "nicht sichtbar" if sicht_daten is False else sicht_daten))
            print("   Zustand %s:" % z)
            print("\n".join(zeilen) if zeilen else "      (keine Buttons)")
    print("\nOdoo 11 Prod wurde ausschliesslich lesend verwendet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
