"""Wertet die Rohdaten aus erhebe_abrechnung_menue_matrix.py und
vergleiche_abrechnung_menuepunkte.py aus und schreibt je Menuepunkt einen Vergleichsbericht
(Differenzen zuerst, dann Kennzahlen). Nur lesend, keine Serveraufrufe.

Aufruf: python scripts/werte_abrechnung_menuevergleich_aus.py
"""
from __future__ import annotations

import json
import os

VZ = os.path.join(os.path.expanduser("~"), "Desktop", "Odoo18-Abnahme-Session131")
ZAHL = os.path.join(VZ, "ansichten", "ansichten_rohdaten.json")
MENUE = os.path.join(VZ, "menue_matrix", "menue_rohdaten.json")
AUS = os.path.join(VZ, "vergleich_bericht.txt")


def namensliste(spalten):
    return [(s["feld"], s["string"], s.get("optional") or "") for s in spalten]


def main() -> int:
    zahl = json.load(open(ZAHL, encoding="utf-8"))
    menue = json.load(open(MENUE, encoding="utf-8"))
    zeilen = []

    def schreib(text=""):
        zeilen.append(text)

    # Menue-Matrix-Grunddaten aus der Menueerhebung
    schreib("=" * 120)
    schreib("MENUEVERGLEICH ABRECHNUNG - Odoo 11 gegen Odoo 18 (lokal und VM)")
    schreib("=" * 120)
    for schluessel in ("o11", "lokal", "vm"):
        punkte = [z for z in menue[schluessel]
                  if z["pfad"] == "Abrechnung" or z["pfad"].startswith("Abrechnung / ")]
        schreib("\n--- %s: %d Menuezeilen unter Abrechnung, davon %d mit Fensteraktion ---"
                % (schluessel, len(punkte), len([z for z in punkte if z["aktionsart"] == "ir.actions.act_window"])))
        for z in punkte:
            schreib("  %-72s | %-26s | %-30s | %-40s | n=%s" %
                    (z["pfad"], (z["modell"] or "-"), (z["view_mode"] or z["aktionsart"] or "-"),
                     (z["menue_xmlid"] or z["meldung"]), z["anzahl"]))

    # Ansichtsvergleich je System
    punkte18 = zahl["lokal"]
    punkte11 = {z["pfad"]: z for z in zahl["o11"]}
    punkte_vm = {z["pfad"]: z for z in zahl["vm"]}

    for pt in punkte18:
        name18 = pt["pfad"]
        name11 = "Abrechnung" + name18[len("Abrechnung"):]  # gleich benannte Pfade
        p11 = punkte11.get(name11)
        if p11 is None:
            # Odoo 11 fuehrt teils andere Zwischennamen (z. B. Einkauf/Dokumente)
            rest = "/".join(name18.split("/")[2:]).strip()
            kandidaten = [z for z in zahl["o11"] if z["pfad"].endswith(rest)]
            p11 = kandidaten[0] if kandidaten else None
        vm = punkte_vm.get(name18)
        schreib("\n" + "=" * 120)
        schreib("MENUEPUNKT: %s" % name18)
        schreib("  Modell %s | Aktion %s | view_mode %s | view_id %s"
                % (pt.get("modell"), pt.get("aktion"), pt.get("view_mode"), pt.get("view_id")))
        if not pt.get("ansichten"):
            schreib("  keine Ansichtsdaten")
            continue
        a18, a11 = pt["ansichten"], (p11 or {}).get("ansichten")
        for bereich in ("liste", "formular", "suche"):
            schreib("  -- %s --" % bereich)
            if bereich == "liste":
                s18 = namensliste(a18["liste"].get("spalten", []))
                s11 = namensliste(a11["liste"].get("spalten", [])) if a11 else []
                schreib("     O11 %d Spalten: %s" % (len(s11), s11))
                schreib("     O18 %d Spalten: %s" % (len(s18), s18))
                if [x[0] for x in s11] != [x[0] for x in s18]:
                    schreib("     ABWEICHUNG Reihenfolge/Menge: O11 fehlt in O18: %s | O18 zusaetzlich: %s"
                            % ([x for x in [y[0] for y in s11] if x not in [y[0] for y in s18]],
                               [x for x in [y[0] for y in s18] if x not in [y[0] for y in s11]]))
            elif bereich == "formular":
                f18, f11 = a18["formular"], (a11["formular"] if a11 else {})
                schreib("     O11 Reiter: %s" % f11.get("seiten"))
                schreib("     O18 Reiter: %s" % f18.get("seiten"))
                schreib("     O11 Felder (%d): %s" % (len(f11.get("felder", [])),
                                                      [f["feld"] for f in f11.get("felder", [])][:40]))
                schreib("     O18 Felder (%d): %s" % (len(f18.get("felder", [])),
                                                      [f["feld"] for f in f18.get("felder", [])][:40]))
                namen11 = {f["feld"] for f in f11.get("felder", [])}
                namen18 = {f["feld"] for f in f18.get("felder", [])}
                schreib("     O11 fehlt in O18: %s" % sorted(namen11 - namen18)[:25])
                schreib("     O18 zusaetzlich : %s" % sorted(namen18 - namen11)[:25])
                schreib("     O11 Buttons: %s" % sorted(set(f11.get("buttons", []))))
                schreib("     O18 Buttons: %s" % sorted(set(f18.get("buttons", []))))
                schreib("     O18 Smart  : %s" % sorted(set(f18.get("smart", []))))
                schreib("     O18 Statusleiste: %s" % sorted(set(f18.get("statusleiste", []))))
                pf18 = {f["feld"]: (f.get("required"), f.get("readonly")) for f in f18.get("felder", [])}
                pf11 = {f["feld"]: (f.get("required"), f.get("readonly")) for f in f11.get("felder", [])}
                diff = {k: (pf11.get(k), pf18.get(k)) for k in set(pf11) & set(pf18) if pf11[k] != pf18[k]}
                schreib("     Attributabweichungen (required/readonly) O11->O18: %s" % diff)
            else:
                s18, s11 = a18["suche"], (a11["suche"] if a11 else {})
                schreib("     O11 Filter (%d): %s" % (len(s11.get("filter", [])),
                                                      sorted({f["name"] for f in s11.get("filter", []) if f["name"]})))
                schreib("     O18 Filter (%d): %s" % (len(s18.get("filter", [])),
                                                      sorted({f["name"] for f in s18.get("filter", []) if f["name"]})))
                schreib("     O11 Gruppierungen: %s" % sorted({g["name"] for g in s11.get("gruppierungen", []) if g["name"]}))
                schreib("     O18 Gruppierungen: %s" % sorted({g["name"] for g in s18.get("gruppierungen", []) if g["name"]}))
                schreib("     O11 Suchfelder (%d), O18 Suchfelder (%d)"
                        % (len(s11.get("suchfelder", [])), len(s18.get("suchfelder", []))))
        if vm is not None:
            gleich = json.dumps(a18, sort_keys=True, default=str) == json.dumps(vm.get("ansichten"), sort_keys=True, default=str)
            schreib("  lokal gegen VM: %s" % ("identisch" if gleich else "UNTERSCHIED"))
            if not gleich:
                for bereich in ("liste", "formular", "suche"):
                    if json.dumps(a18[bereich], sort_keys=True, default=str) != json.dumps(
                            vm["ansichten"][bereich], sort_keys=True, default=str):
                        schreib("     Unterschied im Bereich %s" % bereich)
                        schreib("       lokal: %s" % json.dumps(a18[bereich], ensure_ascii=False)[:1200])
                        schreib("       vm   : %s" % json.dumps(vm["ansichten"][bereich], ensure_ascii=False)[:1200])

    with open(AUS, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(zeilen))
    print("Bericht: %s (%d Zeilen)" % (AUS, len(zeilen)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
