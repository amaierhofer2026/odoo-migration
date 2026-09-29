"""Teil 5, Block 1: Regressionstest Modul Verkauf (alle Prueflaeufe gegen lokal und VM).

Fuehrt alle Verkaufs-Prueflaeufe der Teile 1-4 aus, vergleicht die Ergebnisse mit den
dokumentierten Referenzwerten und sammelt abweichende Pruefungen.

Ergebnis: docs/_verkauf_teil5_regression.json und Konsolenausgabe

Aufruf:
    python scripts/abschluss_verkauf_regression.py            (alle)
    python scripts/abschluss_verkauf_regression.py --nur menue,teil2
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Skript, dokumentierter Referenzwert (OK), Bereich
PRUEFUNGEN = [
    ("scripts/verify_s121_verkauf_menue.py", 41, "Teil 1 Menues/Module"),
    ("scripts/verify_s121_verkauf_teil2.py", 111, "Teil 2 Feldinventar"),
    ("scripts/verify_s121_verkauf_teil3_reiter.py", 64, "Teil 3.1 Formulare/Reiter"),
    ("scripts/verify_s121_verkauf_teil3_status.py", 53, "Teil 3.3 Statuswechsel"),
    ("scripts/verify_s121_verkauf_teil3_filter.py", 199, "Teil 3.4 Filter/Gruppierungen/Suche"),
    ("scripts/verify_s121_verkauf_teil4_ansichten.py", 146, "Teil 4.1 Ansichten"),
    ("scripts/verify_s121_verkauf_kalender.py", 33, "Teil 4.1 Kalender"),
    ("scripts/verify_s121_verkauf_teil4_bericht_kanaele.py", 84, "Teil 4.2 Bericht aller Kanaele"),
    ("scripts/verify_s121_verkauf_teil4_druckberichte.py", 69, "Teil 4.3 Druckberichte"),
    ("scripts/verify_s117_auftraege.py", 67, "Bestand Auftraege/Lageranbindung"),
    ("scripts/verify_s118_abo.py", 19, "Bestand Abonnements"),
]
MUSTER = re.compile(r"(?:Ergebnis:\s*)?(\d+)\s*OK\s*[,/]\s*(\d+)\s*FEHL")


def starte(skript: str):
    t0 = time.time()
    ergebnis = subprocess.run([sys.executable, skript], cwd=REPO, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    ausgabe = (ergebnis.stdout or "") + (ergebnis.stderr or "")
    treffer = MUSTER.findall(ausgabe)
    fehl_zeilen = [z.strip() for z in ausgabe.splitlines() if z.strip().startswith("FEHL")]
    letzte = treffer[-1] if treffer else None
    return {"ok": int(letzte[0]) if letzte else None,
            "fehl": int(letzte[1]) if letzte else None,
            "fehl_zeilen": fehl_zeilen,
            "dauer": round(time.time() - t0, 1),
            "exit": ergebnis.returncode,
            "ausgabe_datei": None}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--nur", default="", help="kommagetrennte Stichworte, z. B. menue,teil2")
    a = p.parse_args()
    filter_liste = [x.strip() for x in a.nur.split(",") if x.strip()]

    ergebnisse = {}
    auffaellig = []
    print("Regressionstest Verkauf (Teil 5, Block 1) - lokal und VM")
    print("Erwartete Werte stammen aus den dokumentierten Abnahmen (Teile 1-4).\n")
    for skript, referenz, bereich in PRUEFUNGEN:
        name = os.path.basename(skript)
        if filter_liste and not any(f in name for f in filter_liste):
            continue
        print("--- %s (%s) ---" % (name, bereich))
        daten = starte(skript)
        daten.update({"referenz": referenz, "bereich": bereich, "skript": skript})
        ergebnisse[name] = daten
        if daten["fehl"] is None:
            print("   ABBRUCH: kein Ergebnis erkennbar (Exit %s)" % daten["exit"])
            auffaellig.append(name)
        else:
            print("   %d OK / %d FEHL (Referenz %d OK), %.1f s"
                  % (daten["ok"], daten["fehl"], referenz, daten["dauer"]))
            if daten["fehl"] or daten["ok"] != referenz:
                auffaellig.append(name)
                for zeile in daten["fehl_zeilen"][:5]:
                    print("      %s" % zeile)

    gesamt_ok = sum(d["ok"] or 0 for d in ergebnisse.values())
    gesamt_fehl = sum(d["fehl"] or 0 for d in ergebnisse.values())
    print("\nGesamt: %d OK / %d FEHL ueber %d Prueflaeufe" % (gesamt_ok, gesamt_fehl, len(ergebnisse)))
    if auffaellig:
        print("Auffaellig: %s" % ", ".join(auffaellig))
    else:
        print("Alle Prueflaeufe auf Referenzniveau, keine Abweichung.")

    ziel = os.path.join(REPO, "docs", "_verkauf_teil5_regression.json")
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump({"ergebnisse": ergebnisse, "gesamt_ok": gesamt_ok, "gesamt_fehl": gesamt_fehl,
                   "auffaellig": auffaellig}, fh, ensure_ascii=False, indent=1)
    print("Rohdaten: %s" % ziel)
    return 1 if auffaellig else 0


if __name__ == "__main__":
    raise SystemExit(main())
