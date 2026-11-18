"""Regression der abgenommenen und gesperrten Bereiche (lokal und VM).

Ruft die vorhandenen Abnahme-Skripte der gesperrten Bereiche nacheinander auf
und stellt die Ergebnisse tabellarisch gegenueber. Es wird nichts geschrieben
ausser den Logdateien unter dem Scratch-Verzeichnis; die Abnahme-Skripte selbst
raeumen ihre Testdaten auf (Stand der jeweiligen Abnahme).

Aufruf:
    python scripts/regression_gesperrte_bereiche.py --instanz lokal
    python scripts/regression_gesperrte_bereiche.py --instanz vm --nur Kontakte,Projekt
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
LOG = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                   "Temp", "regression_gesperrt")
os.makedirs(LOG, exist_ok=True)

# (Bereich, Skript, Aufrufart) - "opt": --instanz <wert>, "pos": positionales Argument
BEREICHE = [
    ("Kontakte/Kundenverwaltung", "browser_kundenverwaltung_pruef.py", "opt"),
    ("Verkauf", "abschluss_verkauf_browser_gesamtabnahme.py", "opt"),
    ("Abonnements", "browser_abo_abnahme.py", "pos"),
    ("Projekt", "browser_projekt_abnahme.py", "pos"),
    ("Personal", "browser_personal_abnahme.py", "pos"),
    ("Zeiterfassung", "browser_zeiterfassung_abnahme.py", "opt"),
    ("Anwesenheiten/Urlaub", "browser_anwesenheiten_abnahme.py", "opt"),
    ("Helpdesk", "browser_helpdesk_abnahme.py", "pos"),
    ("Events", "browser_events_abnahme.py", "opt"),
    ("E-Mail-Marketing", "browser_marketing_abnahme.py", "opt"),
    ("Massenbearbeitung", "browser_massenbearbeitung_abnahme.py", "opt"),
]

MUSTER = [
    re.compile(r"Ergebnis[^:]*:\s*(\d+)\s*OK\s*/\s*(\d+)\s*FEHL", re.I),
    re.compile(r"(\d+)\s*OK\s*/\s*(\d+)\s*FEHL", re.I),
    re.compile(r"OK\s*:\s*(\d+).*?FEHL\s*:\s*(\d+)", re.I | re.S),
]


def auswerten(text: str):
    """Sucht die Ergebniszeile (OK/FEHL) in der Ausgabe."""
    for muster in MUSTER:
        treffer = muster.findall(text)
        if treffer:
            ok, fehl = treffer[-1]
            return int(ok), int(fehl)
    fehl = len(re.findall(r"^\s*FEHL", text, re.M))
    ok = len(re.findall(r"^\s*OK", text, re.M))
    return ok, fehl


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--instanz", required=True, choices=["lokal", "vm"])
    ap.add_argument("--nur", help="kommagetrennte Teilmenge der Bereiche")
    ap.add_argument("--timeout", type=int, default=1500)
    args = ap.parse_args()

    auswahl = BEREICHE
    if args.nur:
        wunsch = [w.strip().lower() for w in args.nur.split(",")]
        auswahl = [b for b in BEREICHE if any(w in b[0].lower() for w in wunsch)]

    print("=== Regression gesperrte Bereiche (%s) ===" % args.instanz, flush=True)
    ergebnisse = []
    for name, skript, art in auswahl:
        pfad = os.path.join(REPO, "scripts", skript)
        if not os.path.exists(pfad):
            print("  FEHL %-28s Skript fehlt: %s" % (name, skript), flush=True)
            ergebnisse.append({"bereich": name, "status": "skript fehlt", "ok": 0, "fehl": 0})
            continue
        befehl = [sys.executable, "-u", pfad]
        befehl += (["--instanz", args.instanz] if art == "opt" else [args.instanz])
        t0 = time.time()
        try:
            lauf = subprocess.run(befehl, cwd=REPO, capture_output=True, text=True,
                                  timeout=args.timeout, encoding="utf-8", errors="replace")
            text = (lauf.stdout or "") + (lauf.stderr or "")
            ok, fehl = auswerten(text)
            status = "bestanden" if fehl == 0 and lauf.returncode == 0 else "abweichend"
        except subprocess.TimeoutExpired:
            text, ok, fehl, status = "", 0, 0, "zeitueberschreitung"
        dauer = time.time() - t0
        logdatei = os.path.join(LOG, "%s_%s_%s.log" % (args.instanz, name.split("/")[0]
                                                       .replace(" ", "_").lower(),
                                                       time.strftime("%H%M%S")))
        with open(logdatei, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("  %-9s %-28s %3d OK / %3d FEHL  (%4.0f s)"
              % (status.upper()[:9], name, ok, fehl, dauer), flush=True)
        ergebnisse.append({"bereich": name, "status": status, "ok": ok, "fehl": fehl,
                           "sekunden": round(dauer), "log": logdatei})

    gesamt_ok = sum(e["ok"] for e in ergebnisse)
    gesamt_fehl = sum(e["fehl"] for e in ergebnisse)
    offen = [e["bereich"] for e in ergebnisse if e["status"] != "bestanden"]
    print("\nSumme: %d OK / %d FEHL" % (gesamt_ok, gesamt_fehl), flush=True)
    print("Nicht bestanden: %s" % (", ".join(offen) if offen else "keine"), flush=True)
    ziel = os.path.join(LOG, "regression_%s.json" % args.instanz)
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump({"instanz": args.instanz, "ergebnisse": ergebnisse,
                   "summe_ok": gesamt_ok, "summe_fehl": gesamt_fehl}, fh,
                  indent=1, ensure_ascii=False)
    print("JSON: %s" % ziel, flush=True)
    return 0 if not offen else 1


if __name__ == "__main__":
    sys.exit(main())
