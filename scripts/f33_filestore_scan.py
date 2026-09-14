"""F33 read-only: fehlende Filestore-Dateien bestimmen und Wiederfindung pruefen.

Aufruf:
  python scripts/f33_filestore_scan.py <anhaenge.txt> <filestore.txt> <label>

<anhaenge.txt>   Ausgabe von psql -A -F'|' -t:
                 id|name|res_model|res_id|res_field|store_fname|file_size|mimetype|create_date
<filestore.txt>  eine Datei pro Zeile (Pfade relativ zum Filestore bzw. absolute Pfade)

Es wird nichts geschrieben, kopiert oder geloescht.
"""
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict

# Bekannte Sicherungsquellen (Host) - Schluessel = Anzeigename, Wert = Wurzelverzeichnis
QUELLEN = {
    "Altstand vor Phase 3 (11.08.2026)": r"C:\Odoo-Test\filestore_before_phase3_2026-08-11\filestore",
    "PHASE-3-Recovery-Backup (C:\\Odoo-Test\\filestore)": r"C:\Odoo-Test\filestore",
    "BACKUP-2026-07-29 (Altstand)": r"C:\Odoo-Test\BACKUP-2026-07-29",
    "Notfallbackup-Stammlauf (12./13.08.2026)": r"C:\Odoo-Notfallbackup\2026-08-14_2156\filestore",
    "Notfallbackup 31.08.2026": r"C:\Odoo-Notfallbackup\2026-08-31_1500\filestore",
    "Notfallbackup 01.-03.09.2026": r"C:\Odoo-Notfallbackup\2026-09-01_1500\filestore",
    "Notfallbackup 09.09.2026 (letzter)": r"C:\Odoo-Notfallbackup\2026-09-09_1529\filestore",
}
ZIPS = [r"C:\Odoo-Test\backups\odoo18_backup_clean_2026-07-29_1248.zip"]

HASH = re.compile(r"^[0-9a-f]{40}$")


def hashes_im_verzeichnis(wurzel):
    """Alle Filestore-Hashes (Dateinamen) unterhalb eines Verzeichnisses."""
    out = set()
    if not os.path.isdir(wurzel):
        return out
    for w, _, dateien in os.walk(wurzel):
        for d in dateien:
            if HASH.match(d):
                out.add(d)
    return out


def hashes_im_zip(pfad):
    out = set()
    if not os.path.isfile(pfad):
        return out
    try:
        with zipfile.ZipFile(pfad) as z:
            for n in z.namelist():
                b = os.path.basename(n)
                if HASH.match(b):
                    out.add(b)
    except Exception as ex:
        print("   Zip %s nicht lesbar: %s" % (pfad, str(ex)[:80]))
    return out


def lies_anhaenge(pfad):
    out = []
    with open(pfad, encoding="utf-8", errors="replace") as fh:
        for z in fh:
            z = z.rstrip("\n\r")
            if not z.strip():
                continue
            t = z.split("|")
            if len(t) < 9:
                continue
            out.append(dict(zip(["id", "name", "res_model", "res_id", "res_field", "store_fname",
                                 "file_size", "mimetype", "create_date"], t)))
    return out


def lies_filestore(pfad):
    s = set()
    with open(pfad, encoding="utf-8", errors="replace") as fh:
        for z in fh:
            z = z.strip().replace("\\", "/")
            if z:
                s.add(os.path.basename(z))
    return s


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    anhaenge_datei, filestore_datei, label = sys.argv[1], sys.argv[2], sys.argv[3]

    anhaenge = lies_anhaenge(anhaenge_datei)
    vor_ort = lies_filestore(filestore_datei)
    print("=" * 100)
    print("F33 - Instanz %s" % label.upper())
    print("=" * 100)
    print("Anhaenge in der DB (mit Filestore-Datei): %d" % len(anhaenge))
    print("Dateien im AKTUELLEN Filestore dieser Instanz: %d" % len(vor_ort))

    fehlend = [a for a in anhaenge if os.path.basename(a["store_fname"]) not in vor_ort]
    vorhanden = [a for a in anhaenge if os.path.basename(a["store_fname"]) in vor_ort]
    print("--> fehlend: %d | vorhanden: %d" % (len(fehlend), len(vor_ort) and len(vorhanden)))

    # Klassifizierung: Bildfeld (res_field) vs. echtes Dokument (kein res_field)
    dokumente = [a for a in fehlend if not a["res_field"]]
    bilder = [a for a in fehlend if a["res_field"]]
    print("\n   davon Bild-/Binärfelder (Avatare, Logos, Icons): %d" % len(bilder))
    print("   davon echte Anhaenge/Belege (ohne res_field):       %d" % len(dokumente))

    print("\n-- Fehlende Dateien nach Modell/Feld (Top 20) --")
    for (m, f), n in Counter((a["res_model"], a["res_field"] or "(Dokument)") for a in fehlend).most_common(20):
        print("   %-30s %-24s %d" % (m, f, n))

    print("\n-- Echte Anhaenge/Belege im Detail (%d) --" % len(dokumente))
    for a in sorted(dokumente, key=lambda x: x["create_date"]):
        print("   %-52s %-18s res_id=%-6s %9s B  %s  %s"
              % ((a["name"] or "")[:52], a["res_model"] or "(ohne Modell)", a["res_id"] or "-",
                 a["file_size"], a["create_date"], a["mimetype"][:24]))

    print("\n-- Bildfelder nach Modell --")
    for m, n in Counter(a["res_model"] for a in bilder).most_common():
        print("   %-30s %d" % (m, n))

    groesse = sum(int(a["file_size"] or 0) for a in fehlend)
    print("\nSumme der fehlenden Bytes: %d (%.1f MB)" % (groesse, groesse / 1048576.0))

    print("\n-- Wiederfindung in den Sicherungen (Abgleich ueber Datei-Hash) --")
    zuordnung = defaultdict(set)
    for name, wurzel in QUELLEN.items():
        satz = hashes_im_verzeichnis(wurzel)
        treffer = 0
        for a in fehlend:
            h = os.path.basename(a["store_fname"])
            if h in satz:
                treffer += 1
                zuordnung[h].add(name)
        print("   %-52s %6d Dateien im Bestand | deckt %d der fehlenden ab"
              % (name[:52], len(satz), treffer))
    for zp in ZIPS:
        satz = hashes_im_zip(zp)
        treffer = sum(1 for a in fehlend if os.path.basename(a["store_fname"]) in satz)
        print("   %-52s %6d Dateien im Archiv | deckt %d der fehlenden ab"
              % (("Zip: " + os.path.basename(zp))[:52], len(satz), treffer))
        for a in fehlend:
            h = os.path.basename(a["store_fname"])
            if h in satz:
                zuordnung[h].add("Zip " + os.path.basename(zp))

    ohne = [a for a in fehlend if os.path.basename(a["store_fname"]) not in zuordnung]
    gedeckt = len(fehlend) - len(ohne)
    print("\n   ERGEBNIS: %d von %d fehlenden Dateien in mindestens einer Sicherung vorhanden,"
          " %d nirgends gefunden" % (gedeckt, len(fehlend), len(ohne)))

    if ohne:
        print("\n-- Nirgends gefunden: Verteilung --")
        for (m, f), n in Counter((a["res_model"], a["res_field"] or "(Dokument)") for a in ohne).most_common(15):
            print("   %-30s %-24s %d" % (m, f, n))
        print("\n-- Nirgends gefunden: die groessten 20 --")
        for a in sorted(ohne, key=lambda x: -int(x["file_size"] or 0))[:20]:
            print("   %-50s %-26s %9s B  %s" % ((a["name"] or "")[:50], a["res_model"],
                                                a["file_size"], a["create_date"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
