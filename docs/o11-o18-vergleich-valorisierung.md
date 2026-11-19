# Valorisierung: Odoo 11 zu Odoo 18

Stand: 19.11.2026 (Session 148). Read-only erhoben gegen Odoo 11 Prod `ITK_V1_a` sowie
gegen Odoo 18 lokal (`odoo18_test`) und VM. Die Zahlen sind frisch gemessen.

Der Bereich ist klein und klar: zehn Hinweistexte als Stammdaten, die auf Rechnungen
ausgewählt werden. Es gibt keine berechneten Felder, keine Automatisierung und keine
eigenen Berichte.

## 1 Bestand Odoo 11 (gemessen 19.11.2026)

### 1.1 Modul und Modell

| Punkt | Wert |
|---|---|
| Modul | `itk_valorisierung` (installiert) |
| Modell | `itk_valorisierung.valorisierung` |
| Felder | `name` (Code, char), `description` (Beschreibung, text), `seq` (Nummernfolge, integer) |
| Reihenfolge | `_order = seq asc` |
| Berechnete Felder | **keine** |
| Cron / Automationen | **keine** |
| Berichte | **keine** |
| Rechnungsbezug | `account.invoice.valorisierung_id` (many2one, Label "Valorisation Text") |

### 1.2 Datenbestand

| Kennzahl | Wert |
|---|---|
| Valorisierungshinweise | **10** (2019 bis 2026) |
| davon aktiv / archiviert | 10 / 0 (kein `active`-Feld im Modell) |
| Hinweise mit Text | 10 (alle) |
| Hinweise ohne Text | 0 |
| Alle `seq` | 0 |
| Ersteller | Odoo-11-Benutzer 10 (Waiss Martina), ein Satz von Benutzer 1 |
| Rechnungen mit Hinweis | **4.216** von 6.378 |
| davon Ausgangsrechnungen / Gutschriften | 4.208 / 8 |
| davon bezahlt / offen / Entwurf | 4.211 / 4 / 1 |

Die Texte enthalten die Valorisierungsprozente und die Indexbasis, zum Beispiel
"Valorisierung von 2,2 % ... (VPI 2005; 10/2017 vs. 10/2018)". Die Prozentsätze stehen
ausschliesslich im Text - es gibt kein Prozent- oder Betragsfeld.

Verteilung der Rechnungen auf die Hinweise: 2019 = 1, 2020 = 460, 2021 = 534, 2022 = 553,
2023 = 644, 2024 = 639, 2024 Acta Nova = 8, 2024 gerundet = 30, 2025 = 697, 2026 = 650.

### 1.3 Menüs, Ansichten, Rechte

| Punkt | Odoo 11 |
|---|---|
| Menü | Abrechnung / Konfiguration / Valorisierung |
| Aktion | "Valorisation Text", Ansichten Liste und Formular |
| Ansichten | Liste und Formular des Modells; Felder Code, Beschreibung, Nummernfolge; keine eigene Suche, kein Kanban |
| Rechnungsformular | Feld "Valorisation Text" als eigene Gruppe **nach dem Feld `notice`** (Abo-Notiz) |
| Gruppe `itk_crm.itk_group_user` ("ITK / User (read only)") | nur lesen |
| Gruppe `itk_crm.itk_group_manager` ("ITK / Manager (edit)") | lesen, schreiben, anlegen, löschen |
| Record Rules | keine eigenen |
| Öffentlich / Portal | kein Zugriff |

## 2 Bestand Odoo 18

| Punkt | Wert |
|---|---|
| Modul | `itk_valorisierung` **18.0.1.3.0**, lokal und VM installiert |
| Modell und Felder | identisch (`name`, `description`, `seq`), Beschriftungen deutsch: Code, Beschreibung, Nummernfolge |
| Ansichten | Liste `itk_valorisierung.valorisierung.tree`, Formular `itk_valorisierung.valorisierung.form`; Felder wie Odoo 11 |
| Menü | Abrechnung / Konfiguration / Valorisierung (Aktion 1117) |
| Rechnungsformular | Feld `valorisierung_id` ebenfalls nach `notice` eingefügt, Label "Valorisation Text" |
| Datensätze | **11**: die 10 Odoo-11-Hinweise als Modul-Daten (`valorisierung_o11_1` bis `_10`, Block `noupdate="1"`) **ohne Beschreibungstext** - dazu ein Testdatensatz "VAL-OK" ohne XML-ID |
| Rechte | eine Access-Regel für `base.group_user` mit **allen** Rechten (lesen, schreiben, anlegen, löschen) |
| Rechnungen | 708 (lokal) bzw. 1.563 (VM), davon 3 mit Valorisierung - alles Testdaten der Abrechnungsrunde, keine migrierten Rechnungen |

## 3 Mapping: Odoo 11 | Odoo 18 | Transformation | Status | Entscheidung

### 3.1 Modell und Felder

| Odoo 11 | verwendet? | Odoo 18 | Status | Entscheidung |
|---|---|---|---|---|
| `itk_valorisierung.valorisierung` | ja (10) | gleiches Modell | 1:1 vorhanden | übernehmen |
| `name` (Code) | ja | `name` | 1:1 | übernehmen |
| `description` (Beschreibung) | ja (Texte) | `description` | 1:1, **Daten fehlen** | Texte migrieren |
| `seq` (Nummernfolge) | ja (alle 0) | `seq` | 1:1 | übernehmen |
| `create_uid` / `create_date` / `write_uid` / `write_date` | ja | gleiche Felder | 1:1 | über Zeitstempel-Import nachziehen |
| `active` | gibt es nicht | gibt es nicht | 1:1 | keine Archivierung nötig |

### 3.2 Rechnungsbezug

| Odoo 11 | Odoo 18 | Status | Entscheidung |
|---|---|---|---|
| `account.invoice.valorisierung_id` (m2o) | `account.move.valorisierung_id` (m2o) | 1:1 vorhanden | Feld bleibt; Befüllung erst mit der Rechnungsmigration |
| 4.216 Rechnungen mit Hinweis | 0 migrierte Rechnungen | **Abhängigkeit** | siehe 5.1 |
| Feldgruppe nach `notice` im Rechnungsformular | identisch eingefügt | 1:1 | keine Änderung |

### 3.3 Menü, Ansichten, Rechte

| Odoo 11 | Odoo 18 | Status | Entscheidung |
|---|---|---|---|
| Menü Abrechnung / Konfiguration / Valorisierung | gleich, deutsch | 1:1 | keine Änderung |
| Aktion "Valorisation Text" | "Valorisierungs Text" | anders benannt | auf Odoo-11-Wortlaut angleichen |
| Liste und Formular mit Code/Beschreibung/Nummernfolge | gleich | 1:1 | keine Änderung |
| Suche/Filter/Gruppierung | Odoo-18-Standard (Suchfeld, Filter, Gruppieren nach) | Zusatz | bleibt erhalten |
| Rechte: `itk_group_user` nur lesen, `itk_group_manager` alles | eine Regel für alle internen Benutzer mit allen Rechten, zusätzlich eine Regel ohne Gruppe (Altbestand in der DB) | **weiter gefasst** | zurückgeführt: zwei Regeln je Gruppe, Altbestand entfernt (`valorisierung_rechte_bereinigen.py`) |
| Keine Record Rules | keine | 1:1 | keine |

### 3.4 Nicht vorhanden (bewusst nicht nachgebaut)

| Punkt | Begründung |
|---|---|
| Prozent-/Betragsfelder | Odoo 11 rechnet nicht; die Prozente stehen im Text |
| Berichte, Automatisierungen, Crons | in Odoo 11 nicht vorhanden |
| Kanban, Kalender, Pivot | in Odoo 11 nicht vorhanden; Odoo 18 bietet sie nicht an |

## 4 Datenmigration

Skript: `scripts/migration/valorisierung_migration.py`, Dokumentation
`docs/migration/valorisierung_migration.md`.

| Objekt | Odoo 11 | Ziel Odoo 18 |
|---|---|---|
| Valorisierungshinweise | 10 | 10 (bestehende Modul-Datensätze, Texte ergänzen) |
| Rechnungsverknüpfungen | 4.216 | 0 in dieser Runde (Rechnungen nicht migriert, siehe 5.1) |

Vorgehen:

1. Die zehn Hinweise werden über den Namen und die XML-ID `valorisierung_o11_<id>` des
   Moduls zugeordnet; zusätzlich erhält jeder Satz den Anker `itk_o11_id`.
2. Die Beschreibungstexte werden unverändert übernommen (keine Normalisierung, keine
   Kürzung).
3. Erstell-/Bearbeitungsdatum und Ersteller werden über `itk.migration.zeitstempel`
   nachgezogen.
4. Der Odoo-18-Testdatensatz "VAL-OK" wird nur entfernt, wenn er an keiner Rechnung
   hängt; sonst bleibt er und wird als Sonderfall protokolliert.
5. Die Rechnungsverknüpfung wird geprüft: Gibt es in Odoo 18 Rechnungen mit
   `itk_o11_id`, werden sie zugeordnet; sonst wird die Zahl der offenen Verknüpfungen
   ausgewiesen.

## 5 Abweichungen und Abhängigkeiten

### 5.1 Rechnungsverknüpfung (offene externe Abhängigkeit Abrechnung, verbindlich)

4.216 Odoo-11-Rechnungen tragen einen Valorisierungshinweis. Die Rechnungen selbst sind
in Odoo 18 noch nicht migriert (Bereich Abrechnung ist in Arbeit: Kontenstammdaten
8400/3400 sind entschieden, die Migration ist nicht durchgeführt). Solange es keine
migrierten Rechnungen gibt, kann `account.move.valorisierung_id` nicht befüllt werden.

Deshalb gilt: Die **Stammdaten** der Valorisierung werden in dieser Runde vollständig
migriert. Die **Rechnungsverknüpfung** wird mit der Rechnungsmigration nachgezogen; das
Migrationsskript wertet sie bei jedem Lauf erneut aus und meldet die offenen Fälle.

Es wird nichts geraten: Rechnungen ohne migrierte Entsprechung werden gezählt, nicht
zugeordnet.

**Verbindlich:** Nach Abschluss der Abrechnungsmigration müssen alle
Valorisierungs-Rechnungsbeziehungen automatisch nachgezogen und erneut geprüft werden.
Dafür ist der Nachlauf `--nachlauf-rechnungen` im Migrationsskript vorgesehen
(Dokumentation Abschnitt 14): er liest die Odoo-11-Bezüge, ordnet über
`account.move.itk_o11_id` zu, setzt nur abweichende Beziehungen, meldet nicht zuordenbare
Fälle und prüft Anzahl und Verteilung je Hinweis. Der Abgleich prüft die Beziehungen
fachlich nach. Der Werkzeugtest ist in Abschnitt 15 der Migrationsdokumentation belegt.

### 5.2 Rechte (angeglichen)

Odoo 18 gab jedem internen Benutzer alle Rechte auf die Valorisierungstexte. Odoo 11
erlaubte Lesen für "ITK / User (read only)" und Änderungen nur für
"ITK / Manager (edit)". Das wird auf den Odoo-11-Stand zurückgeführt: keine
Rechteausweitung, keine Rechteentziehung für Manager.

### 5.3 Testdatensatz "VAL-OK"

Der Satz existiert nur in Odoo 18 (kein Odoo-11-Gegenstück, kein Text) und wird von drei
Testrechnungen der Abrechnungsrunde verwendet. Er gehört nicht zum echten Bestand; sein
Umgang wird dokumentiert (Entfernen nur, wenn keine Rechnung ihn nutzt).

## 6 Datenqualität in den Codes

Die Codes sind in Odoo 11 uneinheitlich geschrieben und werdenzeichengenau übernommen:
"VALORISIERUNGSHINWEIS 2019" bis 2023 in Großbuchstaben, "Valorisierungshinweis 2024"
bis 2026 in gemischter Schreibweise, "VALORISIERUNGHINWEIS 2024 Acta Nova" zusätzlich mit
Tippfehler (fehlendes "S") und einem Leerzeichen am Ende. Es wird nichts normalisiert -
die Codes sind fachliche Schlüssel und stehen so auf Rechnungen und in Auswertungen.
Die Nummernfolge ist in allen zehn Sätzen 0, also gibt es keine fachliche Sortierung
(wie in Odoo 11).

## 7 Akzeptierte Abweichungen

| Abweichung | Begründung |
|---|---|
| Rechnungsverknüpfung 0 von 4.216 in dieser Runde | Rechnungen sind nicht migriert; Nachzug mit der Abrechnung (5.1) |
| Odoo-18-Suchfilter und Gruppierungen | Standardfunktionen, stören die Odoo-11-Funktion nicht |
| Aktionsname wird angeglichen | Odoo-11-Wortlaut "Valorisation Text" |
