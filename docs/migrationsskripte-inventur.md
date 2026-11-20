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
| **Kontakte/Kundenverwaltung** | **ja** | `scripts/migration/kontakte_migration.py` + `kontakte_abgleich.py` | **ja** (123 Tags, 169 Anreden, 6.022 Kontakte, 32 ohne Namen bewusst nicht migriert, 0 Dubletten) | **ja** | **ja** (2. Lauf 0 Neuanlagen, 0 Korrekturen) | verarbeitet personenbezogene Daten; Skript/Mapping/Doku nur IDs und Zaehlwerte | **ABGENOMMEN** |
| **Produkte** | **ja (neu, 12.11.2026)** | `scripts/migration/produkte_migration.py` | **ja** (31 Kategorien, 662 Vorlagen inkl. 4 archivierter, 657 Varianten) | **ja** | **ja** (2. Lauf 0 Neuanlagen) | nein | MIGRIERT |
| **Preislisten** | **ja (neu, 12.11.2026)** | `scripts/migration/preislisten_migration.py` | **ja** (50 Listen, 1.876 Regeln, 0 nicht zuordenbar) | **ja** | **ja** (2. Lauf 0 Neuanlagen) | nein | MIGRIERT |
| **Verkauf** | **ja** | **`scripts/migration/verkauf_migration.py`** + `verkauf_abgleich.py` | **ja** (2.519 Auftraege / 4.079 Zeilen; 0 Abweichungen bei Menge/Preis/Rabatt/Steuer; 94 Kopfsummen dokumentiert) | **ja** | **ja** (zweiter Lauf 0 Neuanlagen, lokal + VM) | nein | **ABGENOMMEN** |
| **Abonnements** | **ja** | **`scripts/migration/abonnement_migration.py`** | **ja** (1.786 Abos / 2.456 Zeilen) | **ja** | **ja** (zweiter Lauf 0 Neuanlagen, lokal + VM) | nein | **ABGENOMMEN** |
| Abrechnung | ja (Testmigration) | `scripts/testmigration_abrechnung.py` | nein (BLOCKER: Kontenstammdaten 8400/3400 fehlen im Odoo-18-Kontenrahmen) | ja | teilweise (Testlauf mit Aufraeumen) | nein | OFFEN |
| Kontakte / CRM (CRM-Teil) | nein | - | CRM-Objekte (Leads, Teams) noch offen; Kontakte selbst sind migriert | entfaellt | entfaellt | - | OFFEN |
| **Umfragen (Survey)** | **ja (neu, 18.11.2026)** | `scripts/migration/survey_migration.py` + `survey_abgleich.py` + `survey_rechte_pruefung.py` | **ja** (2 Umfragen, 2 Abschnitte, 2 Fragen, 2 Vorgaben, 72 Teilnahmen, 71 Antworten) | **ja** | **ja** (2. Lauf 0 Neuanlagen) | verarbeitet Antworttexte; Skript/Mapping/Doku nur IDs, Mengen, Laengen | **MIGRIERT (lokal)** |
| Valorisierung | nein | - | nein | entfaellt | entfaellt | - | OFFEN |
| Lager / Bestand | nein | - | nein | entfaellt | entfaellt | - | OFFEN |

## Stand 12.11.2026 (Ende Session 144)

Der urspruengliche Befund "Verkauf und Abonnements nie migriert" (2.512 Auftraege und
1.777 Abos fehlend) ist **aufgeholt und abgenommen**:

| Objekt | Odoo 11 | Odoo 18 | Status |
|---|---|---|---|
| Auftraege | 2.523 (davon 2.519 migriert) | 2.519 + 13 Testauftraege | ABGENOMMEN |
| Auftragszeilen | 4.079 | 4.079 | 0 Abweichungen Menge/Preis/Rabatt/Steuer |
| Abonnements | 1.786 | 1.786 | ABGENOMMEN |
| Abozeilen | 2.456 | 2.456 | ABGENOMMEN |
| Kontakte | 6.054 | 6.022 | 32 ohne Namen bewusst nicht, ABGENOMMEN |
| Produkte | 662 | 662 | MIGRIERT (Abnahme offen) |
| Preislisten | 50 / 1.876 Regeln | 50 / 1.876 | MIGRIERT (Abnahme offen) |

Datenqualitaet Kontakte: 0 Dubletten nach Bereinigung von 86 Odoo-11-IDs mit 2-7 Kopien
(415 Kopien entfernt, Beziehungen umgehaengt), 0 verlorene Elternbezuege, als
Feldabweichung nur 24 `vat`-Formatfaelle (Odoo normalisiert USt-ID-Formate).

## Naechste Bereiche (Empfehlung fuer Session 145)

1. **Produkte und Preislisten abnehmen** - Daten sind migriert und idempotent, es fehlen
   nur Browserabnahme, Rechte und Sperrvermerk.
2. **CRM (Leads, Teams)** - Skript `scripts/migration/crm_migration.py` neu, mit
   ausdruecklicher Freigabe (personenbezogene Daten).
3. **Abrechnung** - Kontenstammdaten sind entschieden (8400 -> 4000, 3400 -> 5010),
   `scripts/testmigration_abrechnung.py` zum produktiven Migrationsskript ausbauen.
4. **Umfragen, Valorisierung, Lager** - jeweils neues Skript unter `scripts/migration/`
   von Beginn an, inklusive Trockenlauf und Idempotenzpruefung.

## Konventionen (Kurzfassung)

- Skripte unter `scripts/migration/<bereich>_migration.py`.
- Standard = Trockenlauf; Schreiblauf nur mit `--ausfuehren --ich-habe-freigabe`.
- Erkennung ueber das technische Feld `itk_o11_id` (Modul `itk_migration_keys`,
  unsichtbar, nur Zahlen) - ergaenzend zu fachlichen Schluesseln (Code, Key, URL).
  Wichtig: `active_test=False` beim Bestandslesen, sonst werden archivierte Datensaetze
  nicht erkannt und bei jedem Lauf neu angelegt (Ursache der 86 Dubletten).
- Zusammenfassung je Lauf: gelesen / angelegt / aktualisiert / uebersprungen /
  nicht zuordenbar / Fehler.
- Doku je Skript unter `docs/migration/<bereich>_migration.md`.

## Session 148 (19.11.2026): Valorisierung

| Skript | Zweck | Modus | Stand |
|---|---|---|---|
| `scripts/migration/valorisierung_migration.py` | 10 Valorisierungshinweise: Beschreibungstext, Anker `itk_o11_id`, Zeitstempel; Rechnungsbezug pruefen und offene Faelle melden | Trockenlauf Standard, `--ausfuehren --ich-habe-freigabe` | lokal 0/0/10/0/0 |
| `scripts/migration/valorisierung_abgleich.py` | feldweiser Abgleich O11 <-> O18 (Code, Text per Pruefsumme, Nummernfolge, Daten, Ersteller, Textsumme) sowie fachliche Rechnungspruefung, sobald Rechnungen einen Anker haben | nur lesend | 64 OK / 0 Abweichungen / 1 offene Abhaengigkeit (lokal und VM) |
| `scripts/migration/valorisierung_rechte_pruefung.py` | drei Rollen (ohne ITK-Gruppe, User, Manager) lesen/schreiben/anlegen/loeschen, Aufraeumen | schreibend (temporaer) | 11 OK / 0 (lokal) |
| `scripts/browser_valorisierung_daten_abnahme.py` | Browserabnahme nach Migration: Liste, Formular, Suche, Filter, Anlegen, Rechnungsfeld | echter Chrome | 15 OK / 0 (lokal) |
| `scripts/browser_valorisierung_abnahme.py` | Strukturabnahme aus Session 129 (unveraendert weitergenutzt) | echter Chrome | Bestand |

## Session 149 (19.11.2026): Abrechnung / Rechnungen

| Skript | Zweck | Modus | Stand |
|---|---|---|---|
| `scripts/migration/abrechnung_migration.py` | Rechnungen und Gutschriften (6.325), Zeilen, Nummern, Steuer, Valorisierung; Schalter `--zahlungen`, `--anhaenge`, `--gutschrift-journal` | Trockenlauf Standard, `--ausfuehren --ich-habe-freigabe` | lokal 6.325 / Idempotenz 0/6.325/0/0 |
| `scripts/migration/abrechnung_zahlungsausgleich.py` | Zahlungen buchen, Ausgleich der bezahlten Belege, Ersatzzahlungen fuer Belege ohne Beleg | schreibend mit Freigabe | lokal 6.275 bezahlt, 0 Fehler |
| `scripts/migration/abrechnung_abgleich.py` | Anzahl, Typen, Status, Nummern, Summen, Zeilen, Partner, Valorisierung, offener Rest | nur lesend | 15 OK / 0 Abweichungen (lokal) |
| `scripts/migration/abrechnung_rechte_pruefung.py` | drei Rollen plus Odoo-11-Regelvergleich | schreibend (temporaer) | 6 OK / 0 (lokal) |
| `scripts/browser_abrechnung_daten_abnahme.py` | Liste, Filter, historische Rechnung, Positionen, Suche, Gruppierung, Valorisierung | echter Chrome | 11 OK / 0 (lokal) |
