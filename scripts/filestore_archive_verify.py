#!/usr/bin/env python3
"""Read-only Pruefung eines Odoo-Filestore-Archivs (tar.gz).

Beantwortet die Fragen aus dem F33-Muster:
  * Ist der Filestore intakt?  -> Odoo benennt Dateien nach dem SHA-1 des Inhalts,
    also muss sha1(Inhalt) == Dateiname gelten.
  * Entspricht die Struktur einem normalen Filestore?
    -> <...>/filestore/<dbname>/<xx>/<hash>, 256 Buckets, keine Fremdnamen.
  * Gehoert er zu einer bestimmten DB?  -> optionaler Abgleich gegen die
    store_fname-Liste eines Dump-Extrakts (MENGENGLEICHHEIT, mit basename!).

Aufruf:
    python filestore_archive_verify.py <archiv.tar.gz>
    python filestore_archive_verify.py <archiv.tar.gz> --expect-store-fnames store_fnames.txt
    python filestore_archive_verify.py <archiv.tar.gz> --dump-listing toc.txt

store_fnames.txt: eine Zeile pro store_fname aus ir_attachment, z. B. erzeugt mit
    docker exec odoo18-db psql -U odoo -d <db> -A -t \
      -c "SELECT store_fname FROM ir_attachment WHERE store_fname IS NOT NULL AND store_fname <> ''" > store_fnames.txt

Es wird NICHTS entpackt, kopiert oder geschrieben (ausser optional die Ausgabe).
"""

import argparse
import hashlib
import io
import os
import re
import sys
import tarfile
import time
from collections import Counter

HEX40 = re.compile(r"^[0-9a-f]{40}$")


def lese_liste(pfad):
    """Eine Datei mit einem Eintrag pro Zeile einlesen (trailing whitespace weg)."""
    with io.open(pfad, encoding="utf-8", errors="replace") as fh:
        return [z.strip().replace("\\", "/") for z in fh if z.strip() and not z.strip().startswith("[")]


def pruefe_archiv(archiv_pfad):
    """Streaming-Pruefung: sha1(Inhalt) == Dateiname, Struktur, Groessen."""
    t0 = time.time()
    dateien = set()          # 40-Hex-Dateinamen
    fremdnamen = []          # Dateien, deren Name KEIN 40-Hex-Hash ist
    tiefen = Counter()
    praefixe = set()
    verzeichnisse = 0
    abweichungen = []        # (name, sha1_inhalt)
    leer = 0
    fehler = []
    groessen = []
    bytes_gesamt = 0

    with tarfile.open(archiv_pfad, "r|gz") as tf:      # r|gz = streaming, kein Index
        for member in tf:
            if member.isdir():
                verzeichnisse += 1
                continue
            if not member.isfile():
                continue
            name = os.path.basename(member.name)
            tiefen[len([t for t in member.name.replace("\\", "/").split("/") if t])] += 1
            if not HEX40.match(name):
                fremdnamen.append(member.name)
                continue
            praefixe.add(name[:2])
            try:
                fh = tf.extractfile(member)
                if fh is None:
                    fehler.append(member.name)
                    continue
                h = hashlib.sha1()
                n = 0
                while True:
                    block = fh.read(1 << 20)
                    if not block:
                        break
                    n += len(block)
                    h.update(block)
            except Exception as exc:                     # noqa: BLE001
                fehler.append("%s (%s)" % (member.name, exc))
                continue
            if n == 0:
                leer += 1
            if h.hexdigest() != name:
                abweichungen.append((name, h.hexdigest()))
            dateien.add(name)
            groessen.append(n)
            bytes_gesamt += n

    groessen.sort()
    dauer = time.time() - t0
    return {
        "dateien": dateien,
        "anzahl": len(dateien),
        "fremdnamen": fremdnamen,
        "tiefen": tiefen,
        "verzeichnisse": verzeichnisse,
        "praefixe": praefixe,
        "abweichungen": abweichungen,
        "leer": leer,
        "fehler": fehler,
        "bytes": bytes_gesamt,
        "min": groessen[0] if groessen else 0,
        "median": groessen[len(groessen) // 2] if groessen else 0,
        "max": groessen[-1] if groessen else 0,
        "dauer": dauer,
    }


def main():
    ap = argparse.ArgumentParser(description="Read-only Integritaetspruefung eines Filestore-Archivs")
    ap.add_argument("archiv")
    ap.add_argument("--expect-store-fnames", help="Datei mit store_fname-Zeilen aus dem Dump (Paarungsbeweis)")
    ap.add_argument("--dump-listing", help="optional: pg_restore --list Ausgabe, nur zum Kopf-Abdruck")
    args = ap.parse_args()

    if not os.path.isfile(args.archiv):
        sys.exit("FEHLER: Archiv nicht gefunden: %s" % args.archiv)

    if args.dump_listing:
        print("=== Dump-Kopf (%s) ===" % args.dump_listing)
        for z in lese_liste(args.dump_listing)[:12]:
            if z.startswith(("dbname:", "Dumped", "; ", "Archive created")):
                print("  " + z)
        print("")

    r = pruefe_archiv(args.archiv)
    print("Archiv: %s" % args.archiv)
    print("Pruefzeit: %.1f s" % r["dauer"])
    print("Dateien mit SHA-1-Namen geprueft: %d" % r["anzahl"])
    print("  davon Inhalt == Dateiname (intakt): %d (%.2f %%)"
          % (r["anzahl"] - len(r["abweichungen"]), 100.0 * (r["anzahl"] - len(r["abweichungen"])) / max(1, r["anzahl"])))
    print("  Abweichungen: %d | leere Dateien: %d | Lesefehler: %d"
          % (len(r["abweichungen"]), r["leer"], len(r["fehler"])))
    for name, ist in r["abweichungen"][:10]:
        print("      %s  ->  Inhalt %s" % (name, ist))
    for name in r["fehler"][:10]:
        print("      LESEFEHLER %s" % name)
    print("")
    print("Struktur: Tiefen %s | Verzeichnisse %d" % (dict(r["tiefen"]), r["verzeichnisse"]))
    print("Ordner-Praefixe (2 Hex) belegt: %d von 256" % len(r["praefixe"]))
    if r["fremdnamen"]:
        print("  ACHTUNG: %d Dateien ohne 40-Hex-Namen (kein regulaerer Filestore-Inhalt):" % len(r["fremdnamen"]))
        for n in r["fremdnamen"][:10]:
            print("      %s" % n)
    print("Bytes gesamt (unkomprimiert): %d (%.2f GB)" % (r["bytes"], r["bytes"] / 1e9))
    print("Groessen: min %d B | median %d B | max %d B" % (r["min"], r["median"], r["max"]))

    if args.expect_store_fnames:
        # PITFALL: store_fname traegt in der DB das Praefix '<xx>/' -> IMMER basename().
        erwartet = {os.path.basename(z) for z in lese_liste(args.expect_store_fnames) if HEX40.match(os.path.basename(z))}
        gefunden = r["dateien"]
        schnitt = erwartet & gefunden
        print("")
        print("=== Paarungsbeweis (basename-Normalisierung!) ===")
        print("  store_fname in der DB (verschieden): %d" % len(erwartet))
        print("  Dateien im Archiv:                   %d" % len(gefunden))
        print("  Schnittmenge:                        %d" % len(schnitt))
        print("  nur in der DB (Datei fehlt):         %d" % len(erwartet - gefunden))
        print("  nur im Archiv (Datei ohne Metadaten):%d" % len(gefunden - erwartet))
        if erwartet and not schnitt:
            print("  HINWEIS: gleiche Kardinalitaet + 0 Treffer => zuerst die eigene")
            print("          Normalisierung pruefen, bevor das Backup angezweifelt wird.")
        elif erwartet and erwartet == gefunden:
            print("  => Mengen IDENTISCH: der Filestore gehoert zweifelsfrei zu dieser DB.")


if __name__ == "__main__":
    main()
