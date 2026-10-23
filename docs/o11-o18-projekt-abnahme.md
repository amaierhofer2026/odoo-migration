# Projekt (Odoo 18): Umsetzung und Abnahme

Stand: 09.10.2026, Session 133. Ergaenzung zu `docs/o11-o18-projekt-vergleich.md`.

## 1. Auftrag und Entscheidungen

Auftrag: das Projektmodul in Odoo 18 fachlich wie in Odoo 11 nutzbar machen
(Vergleich siehe `docs/o11-o18-projekt-vergleich.md`), Odoo 11 bleibt read-only.

Entscheidungen von Anna (09.10.2026), umgesetzt:

1. `sale_timesheet`/`sale_project` installieren (Odoo-11-Integration Verkauf/Projekt/
   Zeiterfassung); die fachliche Zeiterfassung selbst bleibt ein eigener Bereich.
2. Startdatum der Aufgabe wiederherstellen (Odoo 18 hat kein Standardfeld; geprueft).
3. Prioritaet an Odoo 11 angleichen (Niedrig/Normal), technische Werte 0/1 bleiben.
4. Menues funktional angleichen, Odoo-18-Struktur belassen, alles sichtbar deutsch.
5. Deutsche Bezeichnungen im Odoo-11-Wortlaut, Zusatzfelder sinnvoll uebersetzt.
6. Projekt-Dashboard nicht kuenstlich nachbauen (funktionaler Ersatz dokumentiert).
7. Odoo-18-Zusatzfunktionen beibehalten, nichts ungefragt aktivieren.
8. Projektphasen: Odoo-18-Standardmodell, deutsche Namen.

## 2. Umsetzung

**Module installiert (offizielle Odoo 18):** `sale_project` 18.0.1.0,
`sale_timesheet` 18.0.1.0 (inkl. `sale_project_stock`). Damit sind Auftragsposition
am Projekt/der Aufgabe (`sale_line_id`), Verkaufs-Kennzahlen, Zeiterfassung mit
Abrechnung und Projektanlage aus dem Verkaufsauftrag vorhanden.

**Neues ITK-Modul `itk_project` 18.0.1.0.1** (haengt von project, hr_timesheet,
sale_project, sale_timesheet ab):

| Punkt | Umsetzung | Datei |
|---|---|---|
| Startdatum der Aufgabe | neues Feld `itk_date_start` (Datetime, "Startdatum"); in Formular, Liste (abwaehlbar) und Suche | `models/project_task.py`, `views/project_task_views.xml` |
| Prioritaet | Auswahlwerte 0/1 unveraendert, sichtbare Bezeichnungen "Niedrig"/"Normal" | `models/project_task.py` |
| Deutsche Bezeichnungen (Ansichten) | erbende Ansichten mit `string=` (Projekt, Aufgabe, Stufen, Kanban-Knoepfe) | `views/project_*_views.xml`, `views/project_kanban_views.xml` |
| Deutsche Feldetiketten (Daten/Export) | 79 Eintraege in `i18n/de.po` (Felder von project, hr_timesheet, sale_project, sale_timesheet, helpdesk_mgmt_project, project_timesheet_time_control), gezielte Overwrite-Ladung | `i18n/de.po`, `scripts/gen_projekt_de_po.py` |
| Projektphasen deutsch | Zu erledigen, In Arbeit, Erledigt, Abgebrochen (Odoo-18-Standarddatensaetze) | `data/project_project_stage.xml` |
| Menue "Start work" | "Arbeit starten" (Menue + Knoepfe in Formular, Liste, Kanban) | `views/project_menus.xml`, `views/project_kanban_views.xml` |
| Stufen-Konfiguration auffindbar | neues Menue Projekt/Konfiguration/Stufen (Odoo-11-Funktion, Odoo 18 hatte kein Menue) | `views/project_menus.xml` |
| Knoepfe Start/Stopp | Formular/Liste per `string`, Kanban-`<a>` per Text/Titel | `views/project_*_views.xml`, `views/project_kanban_views.xml` |

Die Ansichten sind bewusst erbend (Repo-durabel); die Feldetiketten zusaetzlich als
`de.po`, damit auch Export/Dialoge deutsch sind. Die de.po wird mit
`scripts/load_terms_de.py` (overwrite) geladen, danach ist ein Neustart noetig.

## 3. Pruefergebnisse

Werkzeuge: `scripts/verify_projekt.py`, `scripts/scan_projekt_englisch.py`,
`scripts/browser_projekt_abnahme.py`.

| Pruefung | lokal | VM |
|---|---|---|
| Strukturpruefung (Modul, Feld, Prioritaet, Ansichten, Phasen, Menue) | 20 OK / 0 FEHL | 20 OK / 0 FEHL |
| Browserabnahme (echter Chrome, echte Bedienung) | 26 OK / 0 FEHL | 26 OK / 0 FEHL |
| Regression Verkauf/Abonnements/Angebote (elf Prueflaeufe, lokal und VM) | 881 OK / 0 FEHL | (in denselben Laeufen enthalten) |

Browserabnahme abgedeckt: Projektliste, Projekt anlegen (Schnellformular),
Projektformular mit Reitern "Einstellungen"/"Kostenrechnung", Aufgabe anlegen,
Startdatum setzen/lesen, Prioritaet Normal, Bearbeiter, Projektzuordnung,
Anhang, Chatter-Nachricht, Projektphase "In Arbeit", Suche, Archivieren;
Aufraeumen mit Bestand vorher == nachher (5 Projekte / 8 Aufgaben).

Deutsche Bezeichnungen: nach der Umstellung sind in den Projekt-, Aufgaben-,
Stufen- und Tag-Ansichten keine englischen Bezeichnungen mehr sichtbar
("Start work"/"Stop", "Members", "Sub-tasks", "Attachments", "Timesheets",
"Tasks Stages", "Color Index", "Currency" u. a. gesetzt). Nur "Tickets" bleibt
bewusst gleich (deutsches Wort).

## 4. Abweichungen und Anmerkungen

1. **Projekt-Dashboard**: Odoo 11 hatte ein Menue "Projekt/Dashboard"; in Odoo 18
   ist die funktionale Entsprechung die Projektuebersicht (Kanban der Projekte,
   Menue "Projekt/Projekte"). Kein Dummy-Menue nachgebaut (Entscheidung 6).
2. **Aufgabenstufen**: ein neu angelegtes Projekt hat zunaechst keine Aufgabenstufen
   (Odoo legt sie bedarfsgesteuert an); deshalb ist "Aufgabenstufe gesetzt" im
   Browserlauf als "kein Ziel vorhanden" gefuehrt. Die Funktion ist vorhanden und
   ueber Projekt/Konfiguration/Stufen erreichbar.
3. **Regression Anpassung** (Werkzeug, kein Produktfehler): durch die bewusste
   Installation von `sale_timesheet`/`sale_project` sind in Verkaufsansichten Felder
   neu vorhanden (`project_ids`, `tasks_count`, `tasks_ids`, `timesheet_count` an
   sale.order; `task_id` an sale.order.line) und eine zweite Zeilenformularansicht.
   Die Verkauf-Pruefskripte fuehrten sie zuvor als "kein Ziel"; sie sind jetzt als
   "seit S133 vorhanden" gefuehrt. Ergebnis danach: 881 OK / 0 FEHL, alle Prueflaeufe
   auf Referenzniveau.
4. **"Start work"/"Stop"** waren auf den Kanban-Karten `<a>`-Elemente mit Textknoten
   statt `<button>`; die Ueberschreibung greift dort ueber Text/Titel.

## 5. Testdaten und offene Punkte

- Alle Testdatensaetze (Projekt, Aufgabe, Anhang, Nachricht, Aktivitaet) wurden im
  selben Lauf wieder entfernt; Bestand vorher == nachher (lokal und VM: 5 Projekte,
  8 Aufgaben; die verbliebenen stammen aus frueheren Sitzungen).
- Odoo 11 blieb unveraendert (nur Leseabfragen).
- Offen: Aufgaben-Gesamtbestand/Stammdaten (Stufen, Tags) sind nicht migriert
  (Stammdaten erst nach Bereichsfreigabe und mit Auswahlregel).

## 6. Session 135 (23.10.2026): Datenmigration und Abschluss

Auftrag: Modul Projekt vollstaendig abschliessen, inklusive Uebernahme aller
Projekt- und Aufgabendaten aus Odoo 11 (auch archivierte), damit die danach
folgende Zeiterfassungsmigration eine stabile Zielstruktur hat. Odoo 11 blieb
read-only.

### 6.1 Neu erhobener Odoo-11-Stand (live, 23.10.2026)

| Punkt | Wert |
|---|---|
| Projekte | 33 (28 aktiv, 5 archiviert) |
| Aufgaben | 715 (605 aktiv, 110 archiviert; 5 ohne Projekt) |
| Aufgaben mit Stufe | 656 |
| Aufgaben mit Startdatum | 715 (Feld `date_start` ist in Odoo 11 auf allen gesetzt) |
| Aufgaben mit geplanter Zeit | 65 |
| Aufgaben mit Stichwoertern | 15 |
| Aufgaben mit Frist | 94 |
| Aufgaben mit Bearbeiter | 707 |
| Aufgabenstufen | 87 (83 projektgebunden, 4 projektlos, 48 gefaltet) |
| Stichwoerter | 13 |
| Projekt-Kunden | 2 (beide fehlen in Odoo 18 - Kundenmigration offen) |
| Projektmanager | 32 von 33 |
| Sichtbarkeit | employees 29, followers 4 |
| "Aufgaben verwenden als" | Tasks 31, Kontingent 1, Faelle 1 |
| kanban_state | normal 713, blocked 1, done 1 |
| Prioritaet | alle 0 (Niedrig) |

Hinweis: Odoo 11 wird weiter benutzt; zwischen den Messungen dieser Sitzung
stieg der Aufgabenbestand von 714 auf 715. Vor der Zeiterfassungsmigration wird
erneut erhoben.

### 6.2 Feldabbildung Odoo 11 -> Odoo 18

| Odoo 11 | Odoo 18 | Regel |
|---|---|---|
| `name`, `privacy_visibility`, `label_tasks`, `color`, `allow_timesheets` | gleichnamig | 1:1 |
| `user_id` (Projektmanager) | `user_id` | 1:1 ueber Odoo-18-Benutzer |
| `analytic_account_id` (Pflicht) | `account_id` | Odoo 18 legt die Kostenstelle beim Projekt automatisch an |
| `partner_id` | `partner_id` | nur wenn der Kunde in Odoo 18 existiert (2 Faelle offen) |
| `resource_calendar_id` | `resource_calendar_id` | ueber Namen der 8 in S134 migrierten Arbeitszeitmodelle |
| `type_ids` (Stufen) | `type_ids` | ueber Name + Projektbezug |
| `subtask_project_id` | entfaellt | Odoo 18 hat native Unteraufgaben |
| Aufgabe: `user_id` | `user_ids` | Mehrfachzuweisung, ein Benutzer gesetzt |
| Aufgabe: `planned_hours` | `allocated_hours` | Wert 1:1 |
| Aufgabe: `date_start` | `itk_date_start` | ITK-Feld aus S133 (Odoo 18 hat kein Standardfeld) |
| Aufgabe: `date_deadline` (Datum) | `date_deadline` (Datetime) | Datum + 00:00 |
| Aufgabe: `kanban_state` | `state` | done -> `1_done`, blocked -> `04_waiting_normal`, normal -> Standard (2 Aufgaben betroffen) |
| Aufgabe: `stage_id` | `stage_id` | ueber Stufe + Projektbezug |
| Aufgabe: `tag_ids` | `tag_ids` | ueber Namen (13 Stichwoerter, 15 Aufgaben) |
| Aufgabe: `priority` 0 | `priority` "0" | sichtbar "Niedrig" |
| Aufgabe ohne Projekt (5) | private Aufgabe (`project_id` leer) | uebernommen, in Odoo 18 nur fuer den Ersteller sichtbar |

### 6.3 Umsetzung und Ergebnis

Werkzeuge: `scripts/projekt_migration.py` (Trockenlauf Standard, Schreiben nur mit
`--ausfuehren --ich-habe-freigabe`), `scripts/projekt_rechte.py`,
`scripts/verify_s135_projekt.py`, `scripts/browser_projekt_daten.py`.

Reihenfolge: Benutzerkonten -> Stufen -> Stichwoerter -> Projekte -> Aufgaben.

| Punkt | vorher | nachher |
|---|---|---|
| Projekte (inkl. archiviert) | 5 | **38** (33 aktiv, 5 archiviert) |
| Aufgaben (inkl. archiviert) | 8 | **723** (715 migriert, 8 Testaufgaben) |
| Aufgabenstufen | 16 | **103** (87 migriert) |
| Stichwoerter | 0 | **13** |
| Benutzer (inkl. inaktiv) | 18 | **28** (10 inaktive Konten fuer historische Bearbeiter) |

Idempotenz: zweiter Trockenlauf meldet 0 Neuanlagen in allen Kategorien.

Rechte (Odoo-11-Konzept, bestehende Mitglieder nicht entfernt):

| Gruppe | Odoo 11 | Odoo 18 nachher |
|---|---|---|
| Projekt / Benutzer | 23 | **13** (alle aktiven internen Benutzer) |
| Projekt / Manager | 20 | **12** (Odoo-11-Managerkreis) |

### 6.4 Sonderfaelle und bewusste Entscheidungen

1. **Archivierte Datensaetze** (5 Projekte, 110 Aufgaben) wurden mit `active=False`
   uebernommen.
2. **5 Aufgaben ohne Projekt** wurden als private Aufgaben uebernommen
   (Odoo 18 kennt keine projektlose Aufgabe mit Teamsichtbarkeit).
3. **10 fehlende Benutzerkonten** wurden als inaktive Benutzer angelegt, damit die
   Bearbeiterzuordnung von 683 Aufgaben nicht verloren geht. Odoo 18 verweigert
   `create` mit `active=False`; die Konten werden aktiv angelegt und sofort
   archiviert.
4. **Stichwoerter** wurden 1:1 uebernommen, einschliesslich der in Odoo 11
   vorhandenen Schreibweisen "Premiu"/"premui" (fachlich identisch zu "Premium").
5. **Zwei Projektkunden fehlen** in Odoo 18 ("[70101] Statutarstadt Innsbruck",
   "[WLV-Voeslau] Wasserleitungsverband ..."); die Projekte wurden ohne Kunde
   angelegt, der Punkt bleibt offen bis zur Kundenmigration.
6. **kanban_state** existiert in Odoo 18 nicht mehr; die zwei abweichenden
   Datensaetze wurden auf `state` abgebildet.

### 6.5 Pruefungen

| Pruefung | lokal | VM |
|---|---|---|
| `verify_s135_projekt.py` | 20 / 0 | **20 / 0** |
| Browser S133-Abnahme (echte Bedienung, Testdaten entfernt) | 26 / 0 | 26 / 0 (S133) |
| Browser migrierte Daten (`browser_projekt_daten.py`) | bestanden | bestanden |
| Regression Verkauf/Abrechnung | **881 / 0** (11 Laeufe) | - |
| Regression Personal | **54 / 0** | - |

Browserbelege (echter Chrome): Projektformular "amtsweg.gv.at - Support (42103 AFS +
41403 FSW)" mit Projektmanager Breiteneder Lorenz, Zaehler "7/10 Aufgaben",
Reiter Beschreibung/Einstellungen/Kostenrechnung; Aufgabe "FSW update" mit
Startdatum 03.04.2023, Bearbeiter Administrator + Soritz Gerd, Stufenleiste,
Status "In Bearbeitung"; Projektliste 1-32 von 32 (aktive Projekte); Stufenliste
19 Eintraege (Ansicht "Aufgabenphasen").

### 6.6 VM-Stand

Migration und Rechte wurden auf der VM mit demselben Skript und derselben
Odoo-11-Quelle ausgefuehrt: 33 Projekte, 715 Aufgaben, 87 Stufen, 13 Stichwoerter,
10 inaktive Benutzer; Rechte Projekt/Benutzer 13, Projekt/Manager 12.
`verify_s135_projekt.py --instanz vm`: **20 / 0**.

Fehlerfall und Reparatur (dokumentiert, kein offener Punkt): beim ersten VM-Lauf
waren die Projekte im Plan noch ohne Odoo-18-ID, dadurch entstanden Aufgaben ohne
Projekt. Reparatur ueber `scripts/projekt_reparatur.py` (Zuordnung per Name +
Startdatum, bei Mehrdeutigkeit Stufe; `write`, kein Loeschen): 710 Aufgaben
nachgezogen, 5 projektlose Odoo-11-Aufgaben bleiben bewusst ohne Projekt.
Das Migrationsskript wurde korrigiert (Projektzuordnung wird nach dem Anlegen der
Projekte neu aufgebaut).

### 6.7 Offene Punkte

1. Zwei Projektkunden fehlen in Odoo 18 (Kundenmigration offen).
2. 5 projektlose Odoo-11-Aufgaben sind in Odoo 18 private Aufgaben (nur fuer den
   Ersteller sichtbar) - funktional gewollt, dokumentiert.
3. Odoo 11 wird weiter benutzt (Aufgabenbestand 714 -> 715 waehrend der Sitzung);
   vor der Zeiterfassungsmigration wird erneut erhoben.
