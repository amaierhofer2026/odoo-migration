# Kontakte / Kundenverwaltung: Abnahme Odoo 11 -> Odoo 18

Stand 12.11.2026. Freigabe Anna Maierhofer (Abnahme Kontakte/Kundenverwaltung).
Quelle: Odoo 11 `ITK_V1_a`, ausschliesslich lesend. Ziel: Odoo 18.

**Datenschutz:** Dieses Dokument enthaelt nur Zaehlwerte, Feldnamen, technische IDs und
Statusangaben. Keine Namen, Anschriften, E-Mail-Adressen oder Telefonnummern.

## 1 Odoo-11-Iststand (neu erhoben, read-only)

| Kennzahl | Wert |
|---|---|
| Kontakte gesamt | 6.052 |
| davon aktiv | 5.851 |
| davon archiviert | 201 |
| Firmen | 2.382 |
| Personen | 3.469 |
| Kontakte mit Elternkontakt | 3.544 |
| Kontakt-Tags | 123 |
| Anreden (`res.partner.title`) | 169 |

Fachlich genutzte Felder: Name, Firmen-/Personenkennzeichen, Adresse (Strasse, Zusatz,
PLZ, Ort, Land), Telefon, Mobil, E-Mail, Website, Referenz, USt-ID, Funktion, Notiz,
Anrede, Tags, Elternkontakt, Aktivstatus.

Zusatzfelder aus `itk_crm` (in Odoo 11 tatsaechlich verwendet): GKZ,
Multiplication Factor/Thsd, zu Handen, Organisationsbezeichnung, Verkaeufer,
Lieferant-/Kundenkennzeichen, Kundenstatus (Bestands-/Ehemaliger-/Kein Kunde),
Email offiziell.

## 2 Odoo-18-Iststand nach Migration

| Kennzahl | lokal | VM |
|---|---|---|
| Kontakte migriert (`itk_o11_id`) | 6.020 | 6.020 |
| davon aktiv | 5.823 | 5.823 |
| davon archiviert | 197 | 197 |
| Kontakt-Tags | 138 (123 migriert + 15 Altbestand) | 138 |
| Anreden | 131 (169 gelesen, 126 neu + Standard) | 131 |

Nicht migriert: **32 Kontakte ohne Namen** (Odoo 18 verlangt einen Namen, `partner_firstname`
zusaetzlich Vor-/Nachname). Diese 32 sind Rechnungsadressen von Firmen; 7 gebuchte
Rechnungen haengen an 4 davon (dokumentiert in `verkauf-abonnement-migration.md`,
Abschnitt 6). Sie werden nicht mit Platzhaltern erfunden.

## 3 Feld- und Beziehungs-Mapping

| Odoo 11 | Odoo 18 | Umsetzung |
|---|---|---|
| `name` | `name` / `lastname` | vollstaendiger Odoo-11-Name; bei Personen als `lastname` (firstname leer), damit die Anzeige identisch bleibt |
| `is_company` | `is_company` | 1:1 |
| `active` | `active` | 1:1, archivierte Kontakte werden mitgenommen |
| `parent_id` | `parent_id` | 1:1, hierarchisch sortiert (Eltern vor Kindern) |
| `street`, `street2`, `zip`, `city` | gleichnamig | 1:1 nach dem Setzen des Elternkontakts erneut geschrieben |
| `country_id` | `country_id` | ueber Laendercode |
| `email`, `phone`, `mobile`, `website` | gleichnamig | 1:1 |
| `ref` | `ref` | 1:1, Unique-Constraint aus `itk_crm` beachtet |
| `vat` | `vat` | 1:1, historische Formate unveraendert (`no_vat_validation`) |
| `function` | `function` | 1:1 |
| `comment` (Text) | `comment` (HTML) | Text zu HTML konvertiert |
| `title` | `title` | ueber `res.partner.title` (126 neu angelegt) |
| `category_id` | `category_id` | ueber `res.partner.category` (123 Tags, Hierarchie und Farbe) |
| `customer`, `supplier` | - | in Odoo 18 entfallen, ergibt sich aus Belegen |
| `team_id`, `sla_id`, `support_ticket_*`, `opt_out`, `signup_*` | - | in Odoo 18 nicht vorhanden bzw. Helpdesk/Massenmail |
| `image`, `image_medium`, `image_small` | `image_1920` | keine Bilddaten in Odoo 11 vorhanden |

**Beibehaltene Odoo-18-Zusatzfunktionen:** `partner_firstname` (Vor-/Nachname),
Kontakt-Typen (contact/invoice/delivery/other), Aktivitaeten, Chatter, `image_1920`,
Portal-Benutzer, Standard-Suchfilter und Gruppierungen. Sie beeintraechtigen die
Odoo-11-Funktionalitaet nicht.

## 4 Datenabgleich (read-only Werkzeug)

`scripts/migration/kontakte_abgleich.py` vergleicht je migriertem Kontakt Name, Firmen-
kennzeichen, Aktivstatus, Adresse, Kommunikation, Kennungen, Funktion und Notizfeld.

Ergebnis lokal (nach den Korrekturen):

| Pruefung | Ergebnis |
|---|---|
| Kontakte Odoo 11 / Odoo 18 | 6.052 / 6.020 |
| nicht migriert | 32 (ohne Namen, dokumentiert) |
| Elternbeziehung verloren | 1 (Elternkontakt unter den 32 namenlosen) |
| Feldabweichungen | nur `vat` 24 Faelle, ausschliesslich Satzzeichen/Gross-Kleinschreibung |

Alle anderen Felder stimmen zeichengenau.

## 5 Gefundene und behobene Fehler

| Fehler | Umfang | Ursache | Behebung |
|---|---|---|---|
| Elternbeziehung verloren | **423** Kontakte | Kinder wurden in Batch-Reihenfolge angelegt; lag der Elternkontakt in einem spaeteren Batch, blieb `parent_id` leer | Skript sortiert die Kinder jetzt nach Hierarchietiefe; Nachzieh-Schritt setzt `parent_id` (423 korrigiert, 1 offen: Elternkontakt unter den 32 namenlosen) |
| Adresse vom Elternkontakt ueberschrieben | 342 Stadt, 80 Strasse, 27 PLZ | Odoo 18 kopiert beim Setzen von `parent_id` die Adresse des Parents ueber die des Kindes | Adressfelder werden nach dem Elternbezug erneut aus Odoo 11 geschrieben (449 Kontakte) |
| Funktion leer | 304 | gleicher Effekt wie oben | im selben Nachzieh-Schritt behoben |
| Anzeigename umsortiert | 18 | `partner_firstname` berechnet `name` aus Vor-/Nachname | Odoo-11-Name als `lastname` gesetzt, Anzeige damit identisch |
| Falsch-Positive im Abgleich | 304 + 2 | Odoo 11 liefert `False`, Odoo 18 `""` | Normalisierung im Abgleich-Werkzeug korrigiert |

## 6 Migrationsskript

`scripts/migration/kontakte_migration.py`

- Odoo 11 nur lesend, Ziel Odoo 18 (`--instanz lokal|vm`)
- Trockenlauf ist Standard; Schreiben nur mit `--ausfuehren --ich-habe-freigabe`
- idempotent ueber `itk_o11_id` (Modul `itk_migration_keys`)
- Schritte: Kategorien (hierarchisch), Anreden, `ref`-Konflikte mit Demodaten,
  Kontakte (topologisch sortiert), Nachzug `parent_id`, Nachzug Adresse/Funktion,
  Nachzug Anzeigename
- Zusammenfassung je Lauf: gelesen / angelegt / aktualisiert / uebersprungen /
  nicht zuordenbar / Fehler
- Mapping-Export mit `--mapping` (nur IDs)

Wiederholungslauf lokal: 0 Neuanlagen, 0 Fehler. Die Korrektur-Schritte melden beim
zweiten Lauf ebenfalls 0, weil sie nur bei Abweichung schreiben.

## 7 Browserabnahme lokal (Chromium, Odoo-18-Webclient)

| Pruefung | Ergebnis |
|---|---|
| Listenansicht | 5.919 aktive Kontakte, Pager "1-80 / 5919" |
| Firmenkontakt | Formular oeffnet; KENNDATEN (GKZ, Multiplication Factor/Thsd, zu Handen, Organisationsbezeichnung), Lieferant/Kunde, Kundenstatus, Adresse, UID, Stichwoerter, Telefon, E-Mail, Website sichtbar |
| Personenkontakt (Ansprechpartner) | Formular oeffnet; Nachname/Vorname, Elternkontakt, Adresse, Stelle, UID sichtbar |
| Parent-/Child-Beziehung | Firmenkontakt 3630 mit zwei untergeordneten Ansprechpartnern, Kind oeffnet mit Elternbezug |
| Archivierter Kontakt | Formular oeffnet mit Banner "ARCHIVIERT" |
| Suche | Eingabe "20101" in der Suchleiste liefert 2 Treffer (Pager "1-2 / 2") |
| Kundenspezifische Felder | alle `itk_crm`-Felder im Formular vorhanden und gefuellt |

**Einschraenkung:** Filter und Gruppierung wurden in der UI nicht abschliessend
durchgeklickt (Filtermenue im Testbrowser nicht erreichbar). Sie sind ueber die
Standard-Suchleiste von Odoo 18 vorhanden; die Pruefung wird nachgeholt.

## 8 Regression

| Bereich | lokal | VM |
|---|---|---|
| Personal | 54 OK / 0 | 54 OK / 0 |
| Projekt | 20 OK / 0 | 20 OK / 0 |
| Events | 61 OK / 0 | 61 OK / 0 |
| Marketing | 37 OK / 0 | 37 OK / 0 |
| Website | unveraendert (12 Seiten, 837 Tracker, 563 Klicks) | dito |

## 9 Testdaten

Fuer die Browserpruefung wurden keine neuen Kontakte angelegt; es wurden ausschliesslich
vorhandene migrierte Datensaetze geoeffnet. Eine Rechtepruefung mit temporaeren Benutzern
steht noch aus (Abschnitt 10).

## 10 Offene Punkte

1. **32 Kontakte ohne Namen** - nicht migriert, dokumentiert (Entscheidung Anna offen).
2. **1 Elternbeziehung** verweist auf einen dieser 32 Kontakte.
3. **Rechtepruefung** mit temporaeren Testbenutzern (normaler Benutzer, Manager/Admin)
   noch nicht durchgefuehrt.
4. **Filter/Gruppierung** in der UI noch nicht durchgeklickt.
5. **VM-Browserabnahme** nach dem laufenden Korrektur-Lauf noch offen.
