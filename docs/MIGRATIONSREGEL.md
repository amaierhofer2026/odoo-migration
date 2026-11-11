# Verbindliche Projektregel: Datenmigration gehoert zum Modulabschluss

Freigabe: Anna Maierhofer, 11.11.2026 (Session 142). Gilt fuer alle noch nicht
abgeschlossenen Module. Bereits ABGENOMMENE UND GESPERRTE Module bleiben unveraendert.

## 1 Abschlusskriterien je Modul

Ein Modul darf erst als **ABGENOMMEN UND GESPERRT** gelten, wenn ALLE acht Punkte erfuellt
und belegt sind:

1. Struktur und Funktionen von Odoo 11 und Odoo 18 sind verglichen und die notwendigen
   Anpassungen umgesetzt.
2. Alle fuer dieses Modul vorgesehenen fachlichen Daten sind aus Odoo 11 nach Odoo 18
   migriert.
3. Die Datenzuordnung ist fachlich und technisch geprueft.
4. Ein zweiter idempotenter Migrationslauf erzeugt keine unbeabsichtigten Dubletten oder
   zusaetzlichen Datensaetze.
5. Browserabnahme lokal und auf der VM bestanden.
6. Regression der bereits abgeschlossenen Bereiche bestanden.
7. Testdaten sind entfernt.
8. GitHub, lokal und VM haben denselben finalen Stand.

Fehlt einer der Punkte, bleibt der Status offen und wird im Abschlussbericht benannt.

## 2 Pflicht: reproduzierbares Migrationsskript im Repository

Jedes Modul bekommt ein dauerhaftes, reproduzierbares Migrationsskript im Git-Repository.
Daten duerfen nicht einmalig per RPC oder temporaerem Python-Code uebertragen werden.

Ablage: `scripts/migration/<bereich>_migration.py`
Beispiel: `scripts/migration/website_migration.py`

Pflichteigenschaften:

- Odoo 11 ausschliesslich lesend verwenden.
- Odoo 18 als Ziel verwenden.
- Standard ist der **Trockenlauf**; er schreibt nichts.
- Ein ausdruecklicher Parameter verlangt den Schreiblauf. Projektstandard:
  `--ausfuehren --ich-habe-freigabe` (Freigabe durch Anna). Ein bloßes `--schreiben`
  genuegt nicht.
- Idempotent: bestehende Datensaetze werden ueber fachliche Schluessel erkannt,
  keine Dubletten.
- Alte und neue IDs bzw. fachliche Schluessel sind nachvollziehbar zugeordnet
  (`--mapping <datei>`).
- Archivierte Datensaetze werden korrekt behandelt, wenn sie fachlich uebernommen werden.
- Beziehungen zwischen Datensaetzen bleiben erhalten.
- Fehler werden eindeutig protokolliert (Abbruch mit Klartext statt stiller Teilimport).
- Zusammenfassung nach jedem Lauf mit:
  gelesen / angelegt / aktualisiert / uebersprungen / nicht zuordenbar / Fehler.
- Keine Passwoerter, API-Schluessel oder Zugangsdaten im Repository.
- Keine personenbezogenen Daten in Git-Logs, CSV-Beispielen oder Dokumentationen.
- Keine vollstaendigen produktiven Datensaetze in GitHub.

Zugangsdaten kommen ausschliesslich aus der lokal nicht versionierten `.env`
(`ODOO11_*`, `ODOO18_*`). Siehe `scripts/_o11o18_client.py`.

## 3 Dokumentation je Migrationsskript

Pro Skript eine kurze README unter `docs/migration/<bereich>_migration.md` mit:
Quelle, Ziel, Voraussetzungen, Trockenlauf, produktiver Lauf, Sicherheitsmechanismen,
Mapping, bekannte Sonderfaelle, Validierung nach der Migration.

Zusaetzlich ein Laufprotokoll mit Zeitstempel, Commit-ID, Quell- und Zielinstanz sowie
reinen Mengen-/Pruefwerten - ohne personenbezogene Inhalte.

Die Dokumentation benennt offen, dass die Skripte Teil des Migrationsprojekts sind und
unter Freigabe von Anna Maierhofer ausgefuehrt wurden. Urheberschaft wird nicht
umgedeutet oder ausgeschmueckt.

## 4 Status der bestehenden Module

Inventur der bereits vorhandenen Migrationsskripte und der noch offenen Module:
`docs/migrationsskripte-inventur.md`.
