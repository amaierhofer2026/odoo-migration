"""Teil 5, Block 3: Browser-Gesamtabnahme Verkauf auf der VM (Aggregatlauf).

Fuehrt alle Browser-Abnahmewerkzeuge des Bereichs Verkauf nacheinander auf der Zielinstanz aus,
zaehlt die Pruefungen, sammelt Abweichungen und JavaScript-/RPC-Fehler und prueft am Ende, dass
der Bestand unveraendert ist (Testdaten bereinigt).

Aufruf:
    python scripts/abschluss_verkauf_browser_gesamtabnahme.py --instanz vm
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from _o11o18_client import o18  # noqa: E402

SP = {"lang": "de_DE"}

# Skript, Bereich, dokumentierter Referenzwert (OK)
WERKZEUGE = [
    ("scripts/browser_verkauf_menue.py", "Menues und Untermenues", 42),
    ("scripts/browser_verkauf_formular_reiter.py", "Formulare und Reiter", 16),
    ("scripts/browser_verkauf_zahlungsbedingung.py", "Zahlungsbedingungen", 5),
    ("scripts/browser_verkauf_buttons_klicktest.py", "Buttons und Smart Buttons", 26),
    ("scripts/browser_verkauf_statuswechsel_klicktest.py", "Statuswechsel", 35),
    ("scripts/browser_verkauf_filter_suche.py", "Suche, Filter, Gruppierungen", 19),
    ("scripts/browser_verkauf_ansichten.py", "Listen/Kanban/Pivot/Graph", 11),
    ("scripts/browser_verkauf_kalender.py", "Auftrags- und Aktivitaetenkalender", 16),
    ("scripts/browser_verkauf_bericht_kanaele.py", "Bericht Verkaufsauftraege aller Kanaele", 18),
    ("scripts/browser_verkauf_druckberichte.py", "Druckberichte", 41),
    ("scripts/browser_verkauf_lieferung.py", "Lager-/Lieferfunktion", 14),
]
MUSTER = re.compile(r"(?:Ergebnis:\s*)?(\d+)\s*OK\s*[,/]\s*(\d+)\s*FEHL")


def starte(skript: str, instanz: str):
    # Frisches Browserprofil je Werkzeug: verhindert Abbrueche durch liegengebliebene
    # Chrome-Profile vorheriger Laeufe (TargetClosedError)
    temp = os.environ.get("TEMP", "/tmp")
    for muster in ("pw_verkauf_*", "pw_gesamtdurchgang_*"):
        for pfad in glob.glob(os.path.join(temp, muster)):
            shutil.rmtree(pfad, ignore_errors=True)
    time.sleep(2)
    t0 = time.time()
    ergebnis = subprocess.run(
        ["uv", "run", "--with", "playwright", "--with", "pypdf", "python", skript,
         "--instanz", instanz],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    ausgabe = (ergebnis.stdout or "") + (ergebnis.stderr or "")
    treffer = MUSTER.findall(ausgabe)
    letzte = treffer[-1] if treffer else None
    js = re.search(r"JavaScript-Fehler:\s*(\d+)", ausgabe)
    rpc = re.search(r"RPC-Fehler:\s*(\d+)", ausgabe)
    return {
        "ok": int(letzte[0]) if letzte else None,
        "fehl": int(letzte[1]) if letzte else None,
        "js_fehler": int(js.group(1)) if js else None,
        "rpc_fehler": int(rpc.group(1)) if rpc else None,
        "fehl_zeilen": [z.strip() for z in ausgabe.splitlines() if z.strip().startswith("FEHL")],
        "dauer": round(time.time() - t0, 1),
        "exit": ergebnis.returncode,
        "ausgabe": ausgabe,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--instanz", choices=["vm", "lokal"], default="vm")
    a = p.parse_args()
    k = o18(a.instanz)

    def bestand():
        return {"auftraege": k.kw("sale.order", "search_count", [[]], context=SP),
                "lagerbelege": k.kw("stock.picking", "search_count", [[]], context=SP),
                "produkte": k.kw("product.template", "search_count", [[]], context=SP),
                "testartikel": k.kw("product.template", "search_count",
                                    [[("name", "ilike", "ZZ-Test")]], context=SP)}

    vorher = bestand()
    print("Browser-Gesamtabnahme Verkauf (%s)" % a.instanz)
    print("Bestand vorher: %s" % vorher)
    auffaellig = []
    ergebnisse = {}
    gesamt_ok = gesamt_fehl = gesamt_js = gesamt_rpc = 0

    for skript, bereich, referenz in WERKZEUGE:
        name = os.path.basename(skript)
        print("\n=== %s (%s) ===" % (name, bereich))
        daten = starte(skript, a.instanz)
        daten.update({"bereich": bereich, "referenz": referenz, "skript": skript})
        ergebnisse[name] = daten
        if daten["ok"] is None:
            print("  ABBRUCH: kein Ergebnis erkennbar (Exit %s)" % daten["exit"])
            print("  %s" % daten["ausgabe"][-600:].replace("\n", "\n  "))
            auffaellig.append(name)
            continue
        gesamt_ok += daten["ok"]
        gesamt_fehl += daten["fehl"]
        gesamt_js += daten["js_fehler"] or 0
        gesamt_rpc += daten["rpc_fehler"] or 0
        print("  %d OK / %d FEHL (Referenz %d), JS-Fehler %s, RPC-Fehler %s, %.0f s"
              % (daten["ok"], daten["fehl"], referenz, daten["js_fehler"], daten["rpc_fehler"],
                 daten["dauer"]))
        for zeile in daten["fehl_zeilen"][:6]:
            print("     %s" % zeile)
        if daten["fehl"] or daten["ok"] != referenz or (daten["js_fehler"] or 0) or (daten["rpc_fehler"] or 0):
            auffaellig.append(name)
        daten.pop("ausgabe", None)

    nachher = bestand()
    print("\nBestand nachher: %s" % nachher)
    bestand_gleich = (vorher["auftraege"] == nachher["auftraege"]
                      and vorher["lagerbelege"] == nachher["lagerbelege"]
                      and vorher["produkte"] == nachher["produkte"]
                      and nachher["testartikel"] == 0)

    print("\nGesamt: %d OK / %d FEHL ueber %d Werkzeuge, JavaScript-Fehler %d, RPC-Fehler %d"
          % (gesamt_ok, gesamt_fehl, len(ergebnisse), gesamt_js, gesamt_rpc))
    print("Bestand unveraendert (Testdaten bereinigt): %s" % bestand_gleich)
    print("Auffaellig: %s" % (", ".join(auffaellig) if auffaellig else "keine"))

    ziel = os.path.join(REPO, "docs", "_verkauf_teil5_browser_gesamtabnahme.json")
    with open(ziel, "w", encoding="utf-8") as fh:
        json.dump({"instanz": a.instanz, "ergebnisse": ergebnisse, "gesamt_ok": gesamt_ok,
                   "gesamt_fehl": gesamt_fehl, "js_fehler": gesamt_js, "rpc_fehler": gesamt_rpc,
                   "bestand_vorher": vorher, "bestand_nachher": nachher,
                   "bestand_gleich": bestand_gleich, "auffaellig": auffaellig}, fh,
                  ensure_ascii=False, indent=1)
    print("Rohdaten: %s" % ziel)
    return 1 if (auffaellig or not bestand_gleich) else 0


if __name__ == "__main__":
    raise SystemExit(main())
