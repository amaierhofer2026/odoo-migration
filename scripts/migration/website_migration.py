#!/usr/bin/env python3
"""Website/Webinhalte: finales, reproduzierbares Migrationsskript Odoo 11 -> Odoo 18.

Teil des ITK-Migrationsprojekts (Odoo 11 -> Odoo 18). Der abgenommene
Migrationsweg wurde mit diesem Skript ausgefuehrt; die Laeufe sind in
`docs/migration/website_migration.md` mit Zeitstempel, Commit-ID, Quell- und
Zielinstanz sowie reinen Mengenwerten protokolliert.

Aufruf (Trockenlauf ist Standard und schreibt nichts):
    python scripts/migration/website_migration.py --instanz lokal
    python scripts/migration/website_migration.py --instanz vm

Schreiblauf nur mit ausdruecklicher Freigabe:
    python scripts/migration/website_migration.py --instanz lokal \
        --ausfuehren --ich-habe-freigabe

Weitere Optionen:
    --nur anhang,demo,seiten,menues,einstellungen,tracker
    --mapping <datei.json>   Zuordnung Odoo-11-id -> Odoo-18-id/Key schreiben
    --abnahme                nur Bestandszahlen vergleichen (read-only)

Quelle: Odoo 11 Prod (ITK_V1_a) - ausschliesslich lesend.
Ziel:   Odoo 18 (lokal odoo18_test oder Test-VM).

Die Logik liegt in `scripts/migrate_website.py` (Markup: `scripts/website_markup.py`);
dieses Skript ist der verbindliche Einstiegspunkt mit Freigabeschalter und
Zusammenfassung im Projektformat.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HIER)
sys.path.insert(0, SCRIPTS)

import _o11o18_client as client  # noqa: E402
import migrate_website as mw  # noqa: E402

OBJEKTE = ["anhang", "seiten", "menues", "einstellungen", "tracker"]


def _bestand(cl, anhang_name: str = None) -> dict:
    """Bestandszahlen Ziel (read-only) fuer Vorher/Nachher."""
    d = {
        "seiten": cl.kw("website.page", "search_count", [[]]),
        "seiten_veroeffentlicht": cl.kw("website.page", "search_count", [[["is_published", "=", True]]]),
        "menues": cl.kw("website.menu", "search_count", [[]]),
        "tracker": cl.kw("link.tracker", "search_count", [[]]),
        "klicks": cl.kw("link.tracker.click", "search_count", [[]]),
        "kampagnen": cl.kw("utm.campaign", "search_count", [[]]),
        "medien": cl.kw("utm.medium", "search_count", [[]]),
        "quellen": cl.kw("utm.source", "search_count", [[]]),
    }
    if anhang_name:
        d["anhang"] = cl.kw("ir.attachment", "search_count", [[["name", "=", anhang_name]]])
    return d


def _mapping(o11, cl, seiten_ids: dict) -> dict:
    """Zuordnung Odoo 11 -> Odoo 18 ueber fachliche Schluessel (ohne Personendaten)."""
    out = {"seiten": [], "menues": [], "tracker": []}
    seiten11 = {p["id"]: p for p in o11["seiten"]}
    for o11_id, ziel in mw.SEITEN.items():
        rec = cl.kw("website.page", "search_read", [[["url", "=", ziel["url"]]], ["id", "url", "key"]])
        o18 = next((r for r in rec if r["key"] == ziel["key"]), rec[0] if rec else None)
        out["seiten"].append({
            "o11_id": o11_id, "o11_name": seiten11[o11_id]["name"], "key": ziel["key"],
            "url": ziel["url"], "o11_veroeffentlicht": bool(seiten11[o11_id]["website_published"]),
            "o18_page_id": o18["id"] if o18 else None,
        })
    root = cl.kw("website", "search_read", [[]], fields=["menu_id"])[0]["menu_id"]
    kids = cl.kw("website.menu", "search_read", [[["parent_id", "=", root[0]]], ["id", "name", "url"]])
    for o11_id, name, url, seite, seq in mw.MENUES:
        o18 = next((k for k in kids if k["url"] == url), None)
        out["menues"].append({"o11_id": o11_id, "name": name, "url": url,
                              "o18_menu_id": o18["id"] if o18 else None})
    codes = cl.kw("link.tracker.code", "search_read", [[], ["code", "link_id"]], limit=5000)
    code_map = {c["code"]: c["link_id"][0] for c in codes}
    for t in o11["tracker"]:
        out["tracker"].append({"o11_id": t["id"], "code": t["code"],
                               "count": t["count"] or 0, "o18_tracker_id": code_map.get(t["code"])})
    return out


def _zusammenfassung(zahlen: dict, vor: dict, nach: dict, o11: dict) -> str:
    """Tabelle im Projektformat: gelesen / angelegt / aktualisiert / uebersprungen /
    nicht zuordenbar / Fehler."""
    def z(schritt, feld, default=0):
        return zahlen.get(schritt, {}).get(feld, default)

    # gelesen = Anzahl der aus Odoo 11 gelesenen Objekte dieser Art
    gelesen = {
        "anhang": 1,
        "seiten": len(mw.SEITEN),
        "menues": len(mw.MENUES),
        "einstellungen": 1,
        "tracker": len(o11["tracker"]),
    }
    zeilen = []
    for objekt in OBJEKTE:
        angelegt = z(objekt, "neu") or z(objekt, "neu_geplant")
        aktualisiert = z(objekt, "arch_aktualisiert") + z(objekt, "geaendert")
        if objekt in ("seiten", "menues", "anhang"):
            aktualisiert += 0
        uebersprungen = z(objekt, "vorhanden")
        nicht_zuordenbar = z(objekt, "akkordeon_ohne_ziel") or 0
        fehler = z(objekt, "_fehler")
        zeilen.append((objekt, gelesen[objekt], angelegt, aktualisiert, uebersprungen,
                       nicht_zuordenbar, fehler))
    zeilen.append(("klicks (historisch)", z("tracker", "klicks_soll"),
                   z("tracker", "klicks_neu"), 0, 0, 0, 0))
    breite = "{:<22}{:>9}{:>9}{:>13}{:>14}{:>17}{:>8}"
    txt = [breite.format("Objekt", "gelesen", "angelegt", "aktualisiert",
                         "uebersprungen", "nicht zuordenbar", "Fehler")]
    txt.append("-" * 92)
    for z_ in zeilen:
        txt.append(breite.format(*[str(x) for x in z_]))
    txt.append("")
    txt.append("Bestand Odoo 18: " + ", ".join("%s %s -> %s" % (k, vor.get(k), nach.get(k))
                                               for k in vor))
    return "\n".join(txt)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instanz", default="lokal", choices=["lokal", "vm"])
    ap.add_argument("--ausfuehren", action="store_true",
                    help="Schreiblauf; ohne diesen Schalter nur Trockenlauf")
    ap.add_argument("--ich-habe-freigabe", action="store_true",
                    help="bestaetigt die Freigabe von Anna fuer den Schreiblauf")
    ap.add_argument("--nur", help="Komma-Liste: %s" % ",".join(mw.SCHRITTE))
    ap.add_argument("--mapping", help="Zuordnung Odoo 11 -> Odoo 18 als JSON schreiben")
    ap.add_argument("--abnahme", action="store_true", help="nur Bestandszahlen vergleichen")
    args = ap.parse_args()

    if args.ausfuehren and not args.ich_have_freigabe:
        print("ABBRUCH: Schreiblauf nur mit --ich-habe-freigabe (Freigabe von Anna).")
        return 2

    schritte = [s.strip() for s in args.nur.split(",")] if args.nur else mw.SCHRITTE
    for s in schritte:
        if s not in mw.SCHRITTE:
            ap.error("unbekannter Schritt %r (erlaubt: %s)" % (s, ", ".join(mw.SCHRITTE)))

    start = time.strftime("%Y-%m-%d %H:%M:%S")
    o11cl = client.o11()
    ziel = mw.Schreibschutz(client.o18(args.instanz), args.ausfuehren)
    lauf = mw.Lauf(args.ausfuehren)

    print("=== Website-Migration %s | %s ===" % (
        args.instanz, "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF (schreibt nichts)"))
    print("Start:", start)

    o11 = mw.lade_o11(o11cl)
    o18 = mw.lade_o18(ziel)
    website_id = o18["website"]["id"]
    anhang_name = o11["anhang"]["name"]
    vor = _bestand(ziel, anhang_name)

    print("Odoo 11: %d Seiten (%d veroeffentlicht), %d Menues, %d Tracker, %d Klicks"
          % (len(o11["seiten"]), sum(1 for p in o11["seiten"] if p["website_published"]),
             len(o11["menues"]), len(o11["tracker"]), sum(t["count"] for t in o11["tracker"])))
    print("Odoo 18 vorher: %d Seiten, %d Menues, %d Tracker, %d Klicks"
          % (vor["seiten"], vor["menues"], vor["tracker"], vor["klicks"]))

    if args.abnahme:
        print(json.dumps(mw.abnahme(o11cl, ziel, args.instanz), ensure_ascii=False, indent=1))
        return 0

    anhang = {"id": mw.ANHANG_ID, "name": o11["anhang"]["name"]}
    if "anhang" in schritte:
        anhang = mw.schritt_anhang(o11, ziel, lauf)
    elif "seiten" in schritte:
        anhang = mw.schritt_anhang(o11, ziel, lauf)
    if "demo" in schritte:
        mw.schritt_demo(o11, ziel, lauf, website_id)
    seiten = {}
    if "seiten" in schritte:
        seiten = mw.schritt_seiten(o11, ziel, lauf, anhang, website_id)
    if "menues" in schritte:
        mw.schritt_menues(o11, ziel, lauf, seiten, website_id)
    if "einstellungen" in schritte:
        mw.schritt_einstellungen(o11, ziel, lauf, website_id)
    if "tracker" in schritte:
        mw.schritt_tracker(o11, ziel, lauf)

    nach = _bestand(ziel, anhang_name)
    print()
    print(_zusammenfassung(lauf.zahlen, vor, nach, o11))

    if args.mapping:
        mp = _mapping(o11, ziel, seiten)
        os.makedirs(os.path.dirname(args.mapping) or ".", exist_ok=True)
        with open(args.mapping, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(mp, fh, ensure_ascii=False, indent=1)
        print("\nMapping geschrieben: %s (Seiten %d, Menues %d, Tracker %d)"
              % (args.mapping, len(mp["seiten"]), len(mp["menues"]), len(mp["tracker"])))

    # Abschlusspruefung: Zielzahlen gegen Quelle
    fehler = []
    if nach["tracker"] < len(o11["tracker"]):
        fehler.append("Tracker %d < Odoo 11 %d" % (nach["tracker"], len(o11["tracker"])))
    if nach["klicks"] < sum(t["count"] for t in o11["tracker"]):
        fehler.append("Klicks %d < Odoo 11 %d" % (nach["klicks"], sum(t["count"] for t in o11["tracker"])))
    if nach["seiten"] < len(mw.SEITEN):
        fehler.append("Seiten %d < uebernommen %d" % (nach["seiten"], len(mw.SEITEN)))
    print("\nAbschlusspruefung:", "OK" if not fehler else "; ".join(fehler))
    print("Modus:", "SCHREIBEN" if args.ausfuehren else "TROCKENLAUF")
    return 0 if not fehler else 1


if __name__ == "__main__":
    raise SystemExit(main())
