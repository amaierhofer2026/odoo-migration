"""Erzeugt die Abnahmetabelle Massenbearbeitung aus dem Browser-Ergebnis.

Liest docs/_massenbearbeitung_browser_<instanz>.json und gibt Markdown-Zeilen aus:
  Odoo-11-Aktion | Odoo-18-Aktion | Status | getestetes Verhalten | bewusste Abweichung

Aufruf: python scripts/bericht_massenbearbeitung.py --instanz lokal
"""
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Odoo-11-Objekt-ID -> (Odoo-11-Name, bewusste Abweichung)
O11 = {
    1304: "Zuweisung Preisliste NÖ",
    1305: "Zuweisung zu Preisliste",
    1306: "Reccuring Total",
    1307: "Angebot zu Auftrag",
    1308: "Status Kunde",
    1309: "Zahlungsbedingungen setzen",
    1310: "Startdatum des nächsten Leistungszeitraumes",
    1311: "Abo-Status ändern",
    1312: "Produktkategorie zuweisen",
    1313: "Valorisierungstext ändern",
    1314: "Zahlungsbedingungen setzen Abrechnung",
    1315: "Rechnungsdatum Abrechnung",
    1316: "Datum der nächsten Rechnung",
    1317: "Massenverarbeitung Leistungszeitraum setzen",
    1318: "Massenverarbeitung Projektkategorie setzen",
    1319: "Tag-Zuweisung",
    1320: "Produktinteresse setzen",
    1321: "Lead Quelle setzen",
    1322: "Interessent Stichwort setzen",
    1323: "Interessent Lead Status setzen",
}

ABWEICHUNG = {
    1307: "ja (Status direkter Feld-Write wie Odoo 11, kein action_confirm)",
    1311: "ja (Status direkter Feld-Write wie Odoo 11)",
    1319: "nein (Stichwortfeld als Tags statt Unterliste)",
    1322: "nein (Stichwortfeld als Tags statt Unterliste)",
}


def kurz(wert):
    if isinstance(wert, (list, tuple)) and len(wert) == 2:
        return wert[1]
    return wert


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instanz", default="lokal")
    a = ap.parse_args()
    pfad = os.path.join(REPO, "docs", "_massenbearbeitung_browser_%s.json" % a.instanz)
    daten = json.load(open(pfad, encoding="utf-8"))
    print("| Odoo-11-Aktion | Odoo-18-Aktion | Status | getestetes Verhalten | bewusste Abweichung |")
    print("|---|---|---|---|---|")
    for e in daten["aktionen"]:
        aid = e["id"]
        name11 = O11.get(aid, "?")
        ok = (not e.get("ausnahme")) and bool(e.get("aenderungen") or e.get("wert"))
        if e.get("ausnahme") or e.get("fehler"):
            status = "FEHLER"
        elif e.get("aenderungen") or e.get("wert_gesetzt"):
            status = "OK"
        else:
            status = "PRUEFEN"
        teile = []
        if e.get("datensaetze"):
            teile.append("%d Datensätze" % len(e["datensaetze"]))
        if e.get("wert"):
            teile.append("Wert %s" % e["wert"])
        if e.get("wert_anzeige"):
            teile.append("Dialog zeigt %s" % e["wert_anzeige"])
        felder = sorted({u["feld"] for u in e.get("aenderungen", [])})
        if felder:
            teile.append("geschrieben: %s" % ", ".join(felder))
        elif e.get("wert_gesetzt"):
            teile.append("Schreibvorgang belegt")
        if e.get("folgefelder") or any(f in ("invoice_status", "date", "is_manually_modified",
                                             "invoice_date_due")
                                       for f in felder):
            teile.append("berechnete Folgefelder mitgefuehrt")
        if e.get("ruecknahme", {}).get("rest") == []:
            teile.append("Ausgangswerte wiederhergestellt")
        print("| %s | %s | %s | %s | %s |" % (
            name11, e["name"], status, "; ".join(teile), ABWEICHUNG.get(aid, "nein")))
    print()
    print("Gesamt:", len(daten["aktionen"]), "Aktionen geprueft am", daten["stand"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
