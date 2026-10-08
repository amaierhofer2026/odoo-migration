"""Auswertung der Steuererhebung: Mapping-Tabelle Odoo 11 -> Odoo 18 und Kennzahlen.

Liest die Rohdaten aus scripts/erhebe_steuern_o11_o18.py und wendet genau die Zuordnungsregel des
Migrationswerkzeugs an (steuer_im_ziel in testmigration_abrechnung.py):
  1. Odoo-11-Beschreibung == Odoo-18-Name (gleiche Verwendung Verkauf/Einkauf) -> eindeutig,
  2. sonst: einziger Treffer mit gleichem Satz und gleicher Verwendung -> eindeutig,
  3. sonst: kein Treffer / nicht eindeutig.
Es wird NICHTS geschrieben; die Ausgabe ist die Grundlage fuer die Doku.

Aufruf: python scripts/werte_steuern_aus.py
"""
from __future__ import annotations

import json
import os
import sys

ZIEL = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session131", "steuern")


def kurz(wert):
    if isinstance(wert, (list, tuple)) and len(wert) > 1:
        return "%s" % wert[1]
    return str(wert)


def kennzahlen(daten):
    o11, o18 = daten["o11_steuern"], daten["o18_steuern"]
    v11, v18 = daten["o11_verwendung"], daten["o18_verwendung"]

    def benutzt(name, verwendung):
        e = verwendung.get(name) or {}
        return e.get("produkte_sale", 0) + e.get("produkte_purchase", 0) + e.get("belegzeilen", 0)

    zeilen = []
    for t in sorted(o11, key=lambda x: (x["type_tax_use"], x["name"])):
        name11 = t["name"]
        besch11 = (t.get("description") or "").strip()
        art = t["type_tax_use"]
        n11 = benutzt(name11, v11)
        # Regel 1: Beschreibung == Odoo-18-Name
        # Gleiche Semantik wie das Werkzeug: search mit ("name", "=ilike", beschreibung)
        # = Vergleich ohne Beachtung der Gross-/Kleinschreibung.
        kandidaten = [x for x in o18 if besch11 and
                      (x["name"] or "").strip().lower() == besch11.lower()
                      and x["type_tax_use"] == art] if besch11 else []
        regel = "Beschreibung = Odoo-18-Name"
        if not kandidaten:
            # Regel 2: gleicher Satz und gleiche Verwendung
            kandidaten = [x for x in o18 if abs((x.get("amount") or 0) - (t.get("amount") or 0)) < 1e-6
                          and x["type_tax_use"] == art]
            regel = "einziger Treffer mit %s%% und %s" % (t.get("amount"), art)
        if len(kandidaten) == 1:
            ziel = kandidaten[0]
            zustand = "1:1" if n11 else "1:1 (nicht verwendet)"
            ziel_txt = "%s (id %s)" % (ziel["name"], ziel["id"])
        elif len(kandidaten) > 1:
            zustand = "nicht eindeutig"
            ziel_txt = "%d Kandidaten: %s" % (len(kandidaten),
                                              ", ".join("%s (%s%%)" % (k["name"], k["amount"])
                                                        for k in kandidaten[:5]))
        else:
            zustand = "fehlt im Ziel (verwendet!)" if n11 else "fehlt im Ziel (nicht verwendet)"
            ziel_txt = "-"
        zeilen.append({"name11": name11, "beschreibung11": besch11, "art": art,
                       "satz": t.get("amount"), "berechnung": t.get("amount_type"),
                       "inklusive": t.get("price_include"), "gruppe": kurz(t.get("tax_group_id")),
                       "sequenz": t.get("sequence"), "aktiv": t.get("active"),
                       "konto": kurz(t.get("account_id")), "erstattungskonto": kurz(t.get("refund_account_id")),
                       "verwendung11": n11, "zustand": zustand, "ziel": ziel_txt, "regel": regel})
    return zeilen


def main() -> int:
    p = os.path.join(ZIEL, "steuern_rohdaten.json")
    daten = json.load(open(p, encoding="utf-8"))
    zeilen = kennzahlen(daten)
    verwendet = [z for z in zeilen if z["verwendung11"]]
    gemappt = [z for z in zeilen if z["zustand"].startswith("1:1") and z["verwendung11"]]
    ohne = [z for z in verwendet if z["zustand"] not in ("1:1",)]

    print("=== Kennzahlen ===")
    print("Odoo 11 Steuern gesamt      : %d" % len(zeilen))
    print("davon produktiv verwendet   : %d" % len(verwendet))
    print("davon 1:1 gemappt           : %d" % len(gemappt))
    print("davon ohne eindeutige Zuordnung: %d" % len(ohne))
    print("Odoo 18 Steuern im Ziel     : %d" % len(daten["o18_steuern"]))
    print("Odoo 18 davon verwendet     : %d" % len([k for k, v in daten["o18_verwendung"].items()
                                                 if any(v.values())]))

    print("\n=== Verwendete Odoo-11-Steuern ===")
    for z in verwendet:
        print("   %-42s %-9s %6s%% %-12s inkl=%s Gruppe=%-18s Konto=%-28s Erstattung=%-28s Verwendung=%s"
              % (z["name11"][:42], z["art"], z["satz"], z["berechnung"], z["inklusive"],
                 z["gruppe"], z["konto"], z["erstattungskonto"], z["verwendung11"]))
        print("      Beschreibung=%r -> %s  [%s | %s]" % (z["beschreibung11"], z["ziel"], z["zustand"],
                                                           z["regel"]))

    print("\n=== Odoo-18-Steuern mit Verwendung ===")
    for name, e in sorted(daten["o18_verwendung"].items()):
        if any(e.values()):
            t = next((x for x in daten["o18_steuern"] if x["name"] == name), {})
            print("   %-42s %-9s %6s%% %-12s Gruppe=%-18s Verwendung=%s"
                  % (name[:42], t.get("type_tax_use"), t.get("amount"), t.get("amount_type"),
                     kurz(t.get("tax_group_id")), e))

    print("\n=== Odoo-11-Steuern OHNE Verwendung (nicht migrationsrelevant) ===")
    ohne_verwendung = [z for z in zeilen if not z["verwendung11"]]
    for z in ohne_verwendung:
        print("   %-42s %-9s %6s%% Sequenz=%-4s aktiv=%-5s -> %s | %s"
              % (z["name11"][:42], z["art"], z["satz"], z["sequenz"], z["aktiv"], z["zustand"], z["ziel"]))

    # Markdown-Tabelle fuer die Doku
    md = ["| Odoo-11-Steuer | Beschreibung | Art | Satz | Berechnung | inkl. | Gruppe | Sequenz | "
          "verwendet | Odoo-18-Ziel | Zustand |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for z in zeilen:
        md.append("| %s | %s | %s | %s%% | %s | %s | %s | %s | %s | %s | %s |"
                  % (z["name11"], z["beschreibung11"] or "-", z["art"], z["satz"], z["berechnung"],
                     "ja" if z["inklusive"] else "nein", z["gruppe"], z["sequenz"],
                     z["verwendung11"] or "0", z["ziel"], z["zustand"]))
    p2 = os.path.join(ZIEL, "mapping_tabelle.md")
    open(p2, "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
    print("\nMapping-Tabelle: %s" % p2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
