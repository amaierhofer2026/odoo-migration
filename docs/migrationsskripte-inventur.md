# Inventur der Migrationsskripte

Stand: 12.11.2026 (Session 142). Verbindliche Regel: `docs/MIGRATIONSREGEL.md`
(Freigabe Anna Maierhofer, **11.11.2026**).

Geprueft wurde je Bereich: liegt ein reproduzierbares Migrationsskript im Repository
(Trockenlauf Standard, ausdruecklicher Freigabeschalter, idempotent)?
**Bereits abgenommene Bereiche wurden nicht veraendert** - diese Tabelle dokumentiert nur
den Ist-Zustand und die Luecken.

## Statusuebersicht (alle bisher bearbeiteten Bereiche)

| Modul / Bereich | Skript vorhanden | Pfad | Datenmigration durchgefuehrt | Trockenlauf geprueft | Idempotent geprueft | Personenbezogene Daten im Skript/Mapping | Status |
|---|---|---|---|---|---|---|---|
| Personal | ja | `scripts/hr_migration.py` | ja (25 Mitarbeiter, 8 Arbeitszeitmodelle, 25 Urlaubsarten, 482 Antraege, 192 Anwesenheiten) | ja | ja | nein | ABGENOMMEN |
| Zeiterfassung | ja | `scripts/zeiterfassung_migration.py` | ja | ja | ja | nein | ABGENOMMEN |
| Anwesenheiten | ja | `scripts/anwesenheiten_migration.py` | ja | ja | ja | nein | ABGENOMMEN |
| Projekt | ja | `scripts/projekt_migration.py` | ja | ja | ja | nein | ABGENOMMEN |
| Events | ja | `scripts/events_migration.py` | ja (121 Events) | ja | ja | nein (keine Teilnehmerdaten) | ABGENOMMEN |
| E-Mail-Marketing | ja | `scripts/marketing_migration.py` | ja (147 Mailings, 8 Listen ohne Mitglieder) | ja | ja | nein (keine Empfaenger) | ABGENOMMEN |
| Massenbearbeitung | nein (kein Datentransfer) | - | nicht erforderlich: 20 Massenaktionen sind Struktur, kein Datenbestand | entfaellt | entfaellt | nein | ABGENOMMEN |
| Helpdesk | nein (bewusst) | - | nein, bewusste Entscheidung: keine historischen Tickets | entfaellt | entfaellt | nein | ABGENOMMEN (ohne Datentransfer) |
| **Website / Webinhalte** | **ja** | **`scripts/migration/website_migration.py`** (Logik `scripts/migrate_website.py`) | **ja** (9 Seiten, 10 Menues, 837 Tracker, 563 Klicks, 1 Anhang) | **ja** (lokal + VM, 0 Aenderungen) | **ja** (Wiederholungslauf 0 Neuanlagen) | nein (Klicks ohne IP/Mailbezug) | **ABGENOMMEN** |
| **Verkauf** | **ja (neu, 12.11.2026)** | **`scripts/migration/verkauf_migration.py`** | **NEIN - 2.512 von 2.514 Auftraegen fehlen in Odoo 18** | **ja** (lokal + VM) | entfaellt bis zum Datenlauf | nein (Skript/Mapping ohne Kunden- und Personendaten) | **OFFEN (Datenmigration)** |
| **Abonnements** | **ja (neu, 12.11.2026)** | **`scripts/migration/abonnement_migration.py`** | **NEIN - 1.777 von 1.788 Abos fehlen in Odoo 18** | **ja** (lokal + VM) | entfaellt bis zum Datenlauf | nein (Skript/Mapping ohne Kunden- und Personendaten) | **OFFEN (Datenmigration)** |
| Abrechnung | ja (Testmigration) | `scripts/testmigration_abrechnung.py` | nein (BLOCKER: Kontenstammdaten 8400/3400 fehlen im Odoo-18-Kontenrahmen) | ja | teilweise (Testlauf mit Aufraeumen) | nein | OFFEN |
| Kontakte / CRM | nein | - (nur `scripts/o11_o18_mapping.py`, Pruefskripte) | nein (personenbezogen, eigener Auftrag noetig) | entfaellt | entfaellt | - | OFFEN |
| Umfragen (Survey) | nein | - | nein (Odoo 11: 2 Umfragen, 73 Teilnahmen) | entfaellt | entfaellt | - | OFFEN |
| Valorisierung | nein | - | nein | entfaellt | entfaellt | - | OFFEN |
| Lager / Bestand | nein | - | nein | entfaellt | entfaellt | - | OFFEN |

## Befund vom 12.11.2026 (wichtig)

Die Trockenlaeufe der beiden neuen Skripte zeigen: **Verkauf und Abonnements sind
strukturell abgenommen, aber datenmaessig nie migriert worden.**

| Objekt | Odoo 11 | in Odoo 18 erkannt | fehlend |
|---|---|---|---|
| Auftraege (`sale.order`) | 2.514 | 2 | **2.512** |
| Abonnements (`sale.subscription`) | 1.788 | 11 | **1.777** |

Zusaetzlich fehlen die Voraussetzungen fuer einen belastbaren Datenlauf:
- Kunden: bei 2.509 der fehlenden Auftraege ist der Kunde in Odoo 18 nicht vorhanden.
- Produkte: bei 2.501 der fehlenden Auftraege fehlt das Produkt (Zuordnung ueber `default_code`).
- Abos: Preisliste bei 1.777, Partner bei 1.775, Vorlage bei 1.777 nicht zuordenbar.

Der Odoo-18-Bestand dieser beiden Bereiche besteht aus Abnahme- und Testdatensaetzen
(z. B. `S00001`, `TEST Abnahme cancel`), nicht aus migrierten Fachdaten.

**Konsequenz:** Beide Bereiche erfuellen Punkt 2 der Projektregel (vollstaendige
Datenmigration) nicht. In dieser Uebersicht stehen sie deshalb auf OFFEN (Datenmigration);
ueber den bestehenden Sperrvermerk entscheidet Anna.

## Offene Module ohne Skript (Empfehlung)

1. Kontakte/CRM: eigenes Skript nach dem Muster `scripts/migration/crm_migration.py`
   erst mit ausdruecklicher Freigabe (personenbezogene Daten).
2. Abrechnung: `scripts/migration/abrechnung_migration.py`, sobald die Kontenstammdaten
   8400/3400 entschieden sind.
3. Umfragen, Valorisierung, Lager: jeweils neues Skript unter `scripts/migration/` von
   Beginn an, inklusive Trockenlauf und Idempotenzpruefung.

## Konventionen (Kurzfassung)

- Skripte unter `scripts/migration/<bereich>_migration.py`.
- Standard = Trockenlauf; Schreiblauf nur mit `--ausfuehren --ich-habe-freigabe`.
- Erkennung ueber fachliche Schluessel (Name, Code, Key, URL), nie ueber Odoo-11-IDs
  als Bruecke.
- Zusammenfassung je Lauf: gelesen / angelegt / aktualisiert / uebersprungen /
  nicht zuordenbar / Fehler.
- Doku je Skript unter `docs/migration/<bereich>_migration.md`.
