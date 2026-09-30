"""Read-only Feldinventar Abrechnung Teil 2: account.invoice/-line gegen account.move/-line.

Aufruf:
    python scripts/analyse_abrechnung_teil2_felder.py            # Messung lokal + VM, JSON nach %TEMP%
    python scripts/analyse_abrechnung_teil2_felder.py --kurz     # nur Zusammenfassung

Odoo 11 Prod wird ausschliesslich lesend verwendet.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18

PAARE = [("account.invoice", "account.move"), ("account.invoice.line", "account.move.line")]
FELDER = ["name", "field_description", "ttype", "relation", "required", "readonly", "store",
          "related", "modules", "selectable", "translate", "state", "index", "help"]
AUSGABE = os.path.join(tempfile.gettempdir(), "abrechnung_teil2_felder.json")


def felder(k, modell):
    """ir.model.fields (autoritativ) + fields_get (Anzeige/Selektionen)."""
    roh = k.kw("ir.model.fields", "search_read", [[("model", "=", modell)], FELDER],
               order="name", context={"lang": "de_DE"})
    fg = k.kw(modell, "fields_get", [[], ["string", "type", "relation", "selection", "required",
                                          "readonly", "store"]], context={"lang": "de_DE"})
    return roh, fg


def zaehle(k, modell, feld):
    """Belegte Datensaetze, nur sinnvoll bei gespeicherten, nicht abgeleiteten Feldern."""
    try:
        return k.kw(modell, "search_count", [[(feld, "!=", False)]])
    except Exception as fehler:
        return "n/v (%s)" % str(fehler)[:30].replace("\n", " ")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--kurz", action="store_true")
    a = p.parse_args()
    lade_env()
    k11 = o11()
    k18 = o18("lokal")
    daten = {}

    for modell11, modell18 in PAARE:
        for schluessel, k, modell in (("o11", k11, modell11), ("o18", k18, modell18)):
            roh, fg = felder(k, modell)
            eintraege = {}
            for f in roh:
                e = {x: f.get(x) for x in FELDER}
                g = fg.get(f["name"], {})
                e["string_fg"] = g.get("string")
                e["selection"] = g.get("selection")
                e["required_fg"] = g.get("required")
                e["readonly_fg"] = g.get("readonly")
                e["store_fg"] = g.get("store")
                e["type_fg"] = g.get("type")
                e["relation_fg"] = g.get("relation")
                # Nutzung bei allen gespeicherten Feldern messen (auch abgeleiteten/store=True)
                if g.get("store") is not False:
                    e["belegt"] = zaehle(k, modell, f["name"])
                eintraege[f["name"]] = e
            daten.setdefault(modell11, {})[schluessel] = {
                "modell": modell,
                "felder": eintraege,
                "anzahl_ir_model_fields": len(roh),
                "anzahl_fields_get": len(fg),
                "nur_in_ir_model_fields": sorted(set(eintraege) - set(fg)),
                "nur_in_fields_get": sorted(set(fg) - set(eintraege)),
            }

    for modell11, modell18 in PAARE:
        d = daten[modell11]
        a11 = set(d["o11"]["felder"])
        a18 = set(d["o18"]["felder"])
        gemeinsam = sorted(a11 & a18)
        nur11 = sorted(a11 - a18)
        nur18 = sorted(a18 - a11)
        print("\n===== %s (O11, %d Felder) gegen %s (O18, %d Felder) ====="
              % (modell11, len(a11), modell18, len(a18)))
        print("gemeinsam %d | nur O11 %d | nur O18 %d" % (len(gemeinsam), len(nur11), len(nur18)))
        print("ir.model.fields gegen fields_get: O11-Abweichungen %s / %s | O18-Abweichungen %s / %s"
              % (d["o11"]["nur_in_ir_model_fields"], d["o11"]["nur_in_fields_get"],
                 d["o18"]["nur_in_ir_model_fields"], d["o18"]["nur_in_fields_get"]))
        if not a.kurz:
            print("  nur O11: %s" % nur11)
            print("  nur O18: %s" % nur18)

        # Typ-/Relationsabweichungen bei gemeinsamen Feldern
        abw = []
        for f in gemeinsam:
            t11 = d["o11"]["felder"][f]["ttype"]
            t18 = d["o18"]["felder"][f]["ttype"]
            r11 = d["o11"]["felder"][f]["relation"] or ""
            r18 = d["o18"]["felder"][f]["relation"] or ""
            if t11 != t18 or r11 != r18:
                abw.append((f, t11, t18, r11, r18))
        print("  Typ-/Relationsabweichungen bei gemeinsamen Feldern: %d" % len(abw))
        for f, t11, t18, r11, r18 in abw:
            print("     %-32s O11 %-12s %-24s | O18 %-12s %s" % (f, t11, r11, t18, r18))

        # Nutzung in Odoo 11 (nur gespeicherte, nicht abgeleitete Felder)
        if not a.kurz:
            print("  -- belegte Datensaetze in Odoo 11 (gespeichert, nicht abgeleitet) --")
            for f in sorted(d["o11"]["felder"]):
                e = d["o11"]["felder"][f]
                if e["store_fg"] is False or e["related"]:
                    continue
                if f.startswith(("__", "message_", "activity_", "access_", "website_",
                                 "create_", "write_", "display_name", "id")):
                    continue
                print("     %-32s %s" % (f, zaehle(k11, modell11, f)))

    with open(AUSGABE, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(daten, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("\nRohdaten (nicht im Repo): %s" % AUSGABE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
