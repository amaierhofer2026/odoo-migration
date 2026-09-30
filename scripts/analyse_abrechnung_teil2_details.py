"""Read-only Detailmessung Abrechnung Teil 2: Beschriftungen, Pflicht/readonly, Auswahlwerte.

Aufruf:  python scripts/analyse_abrechnung_teil2_details.py
Odoo 11 Prod wird ausschliesslich lesend verwendet.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import lade_env, o11, o18

PAARE = [("account.invoice", "account.move"), ("account.invoice.line", "account.move.line")]
QUELLE = os.path.join(tempfile.gettempdir(), "abrechnung_teil2_felder.json")
ZIEL = os.path.join(tempfile.gettempdir(), "abrechnung_teil2_details.json")

AUSWAHL = {
    "account.invoice": ["state", "type", "reference_type"],
    "account.move": ["state", "move_type", "payment_state", "invoice_filter_type_domain"],
    "account.invoice.line": ["invoice_type"],
    "account.move.line": ["display_type", "parent_state"],
}


def main() -> int:
    lade_env()
    daten = json.load(open(QUELLE, encoding="utf-8"))
    k11 = o11()
    k18 = o18("lokal")
    aus = {}

    for modell11, modell18 in PAARE:
        a = daten[modell11]["o11"]["felder"]
        b = daten[modell11]["o18"]["felder"]
        gemeinsam = sorted(set(a) & set(b))

        abw_label = [(f, a[f]["string_fg"], b[f]["string_fg"])
                     for f in gemeinsam if (a[f]["string_fg"] or "") != (b[f]["string_fg"] or "")]
        abw_type = [(f, a[f]["ttype"], b[f]["ttype"], a[f]["relation"], b[f]["relation"])
                    for f in gemeinsam
                    if a[f]["ttype"] != b[f]["ttype"] or (a[f]["relation"] or "") != (b[f]["relation"] or "")]
        req11 = sorted(f for f in a if a[f].get("required_fg"))
        req18 = sorted(f for f in b if b[f].get("required_fg"))
        ro11 = sorted(f for f in a if a[f].get("readonly_fg"))
        ro18 = sorted(f for f in b if b[f].get("readonly_fg"))
        berechnet11 = sorted(f for f in a if a[f].get("store_fg") is False)
        berechnet18 = sorted(f for f in b if b[f].get("store_fg") is False)
        itk11 = sorted((f, a[f]["modules"]) for f in a if (a[f]["modules"] or "")
                       not in ("account", "base", "mail", "sale", "purchase", "analytic",
                               "account_payment", "account_invoice_line_number",
                               "account_invoice_line_report"))
        itk18 = sorted((f, b[f]["modules"]) for f in b if (b[f]["modules"] or "")
                       not in ("account", "base", "mail", "sale", "purchase", "analytic",
                               "account_payment", "account_invoice_line_number",
                               "account_invoice_line_report", "account_edi_ubl_cii",
                               "account_peppol", "stock_account", "account_peppol_selfbilling"))

        print("\n===== %s / %s =====" % (modell11, modell18))
        print("gemeinsam %d" % len(gemeinsam))
        print("-- Beschriftungsunterschiede (de_DE) bei gemeinsamen Feldern: %d --" % len(abw_label))
        for f, s11, s18 in abw_label:
            print("   %-30s O11 '%s' | O18 '%s'" % (f, s11, s18))
        print("-- Typ-/Relationsabweichungen: %d --" % len(abw_type))
        for f, t11, t18, r11, r18 in abw_type:
            print("   %-30s O11 %-12s %-24s | O18 %-12s %s" % (f, t11, r11 or "", t18, r18 or ""))
        print("-- Pflichtfelder O11: %s" % req11)
        print("-- Pflichtfelder O18: %s" % req18)
        print("-- nur in O18 zusaetzlich pflichtig: %s" % sorted(set(req18) - set(req11)))
        print("-- nicht mehr pflichtig in O18: %s" % sorted(set(req11) - set(req18)))
        print("-- readonly nur O11 (Stichprobe gemeinsamer Felder): %s"
              % sorted(set(ro11) & set(gemeinsam) - set(ro18)))
        print("-- berechnet (store=False) O11: %d | O18: %d" % (len(berechnet11), len(berechnet18)))
        print("-- ITK-/Drittmodul-Felder O11 (vorhanden in O18?): %s" % itk11)
        print("-- ITK-/Drittmodul-Felder O18: %s" % itk18)

        aus[modell11] = {"abw_label": abw_label, "abw_type": abw_type, "req11": req11, "req18": req18,
                         "ro11": ro11, "ro18": ro18, "berechnet11": berechnet11,
                         "berechnet18": berechnet18, "itk11": itk11, "itk18": itk18}

    print("\n===== Auswahlwerte =====")
    for modell, felder in AUSWAHL.items():
        k = k11 if modell.startswith("account.invoice") else k18
        for feld in felder:
            try:
                d = k.kw(modell, "fields_get", [[feld], ["selection", "string"]], context={"lang": "de_DE"})
                print("   %-25s %-26s %s" % (modell, feld, d[feld].get("selection")))
            except Exception as fehler:
                print("   %-25s %-26s FEHLER %s" % (modell, feld, str(fehler)[:60]))

    with open(ZIEL, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(aus, fh, ensure_ascii=False, indent=1, sort_keys=True)
    print("\nRohdaten (nicht im Repo): %s" % ZIEL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
