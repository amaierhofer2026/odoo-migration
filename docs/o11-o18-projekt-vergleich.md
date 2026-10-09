# Projekt (Odoo 11 zu Odoo 18): Iststand, Vergleich und Entscheidungsgrundlage

Stand: 09.10.2026, Session 133. Sprache: nur Deutsch, einfache Zeichen.

Auftrag (Anna): Das Modul Projekt in Odoo 11 vollstaendig read-only erheben und mit
dem Projekt-Modul in Odoo 18 vergleichen, damit ITK das Projekt in Odoo 18 fachlich
moeglichst wie in Odoo 11 verwenden kann. Keine echten Projektdaten migrieren, keine
Testdaten in Odoo 11, keine Aenderung ohne Freigabe. Dieses Dokument ist der
Vergleich und die Entscheidungsgrundlage; Aenderungen folgen erst nach Freigabe.

Quellen (alles read-only, keine Aenderung):
- Odoo 11 Produktion `portal.it-kommunal.at`, DB `ITK_V1_a` (nur Leseabfragen).
- Odoo 18 lokal (`http://localhost:8069`, DB `odoo18_test`) und VM
  (`https://k001959vsx.ipax.at`, DB `odoo18_test`).
- Werkzeuge: `scripts/erhebe_projekt.py`, `scripts/projekt_views.py`,
  `scripts/projekt_bestand.py` (alle read-only).
- Rohdaten: `%USERPROFILE%\Desktop\Odoo18-Projekt-Session133\rohdaten\`.

Wichtig vorab: lokal und VM sind in Odoo 18 beim Projekt strukturell identisch
(gleiche Menues, Ansichten, Felder, Bestaende). Einziger Unterschied: das Menue
"Zeiterfassung/Zeiterfassung/Start work" heisst lokal englisch, auf der VM deutsch
"Arbeit starten" (fehlender deutscher Slot lokal), und die VM hat zusaetzlich das
Menue "Helpdesk/Zeiterfassung". Der Odoo-18-Stand wird deshalb einmal berichtet
(Spalte "Odoo 18 lokal = VM"), mit diesen zwei Abweichungen als Fussnote.

## 1. Odoo-11-Iststand (read-only erhoben)

### 1.1 Module

| Modul | Version | State | Bedeutung |
|---|---|---|---|
| project | 11.0.1.1 | installiert | Projekt und Aufgaben |
| analytic | 11.0.1.1 | installiert | Kostenrechnung (Projekt erbt davon) |
| hr_timesheet | 11.0.1.0 | installiert | Zeiterfassung auf Aufgaben |
| hr_timesheet_attendance | 11.0.1.0 | installiert | Zeiterfassung/Anwesenheiten Berichte |
| project_timesheet_holidays | 11.0.1.0 | installiert | Zeiterfassung bei Abwesenheit |
| sale_timesheet | 11.0.1.0 | installiert | Verkauf und Zeiterfassung (Abrechnung nach Aufwand) |
| website_form_project | 11.0.1.0 | installiert | Aufgabenformular im Web |
| itk_projectcategory | 11.0.0.1 | installiert | ITK-Projektkategorie (Abrechnung) |
| website_support_analytic_timesheets | 11.0.1.0.6 | installiert | Helpdesk-Zeiterfassung |
| crm_project | 11.0.1.0 | NICHT installiert | Lead zu Aufgabe |
| rating_project | 11.0.1.0 | NICHT installiert | Bewertung auf Aufgaben |
| pad_project | 11.0.1.0 | NICHT installiert | Pad auf Aufgaben |
| account_analytic_default | 11.0.1.0 | NICHT installiert | Standard-Kostenstelle |
| website_rating_project | 11.0.0.1 | NICHT installiert | Web-Bewertung |

### 1.2 Modelle und Umfang

| Modell | Bezeichnung | Felder | Bestand |
|---|---|---|---|
| project.project | Project | 66 | 28 |
| project.task | Task | 72 | 598 |
| project.task.type | Task Stage (Aufgabenstufe) | 17 | 87 |
| project.tags | Tags of project's tasks | 9 | 13 |
| project.task.merge.wizard | Zusammenfuehren-Assistent | - | (transient) |
| report.project.task.user | Statistik Aufgaben | - | (Bericht) |

Es gibt in Odoo 11 KEINE Projektphasen (`project.project.stage`) und KEINE
Meilensteine (`project.milestone`).

### 1.3 Menuebaum (deutsche Anzeige)

```
Projekt (Wurzel, Sequenz 50)
  Dashboard                          Sequenz 1
  Suchen                             Sequenz 2
    Aufgaben                         Sequenz 5
    Naechste Aktivitaeten            Sequenz 25
  Konfiguration                      Sequenz 100
    Aktivitaetstypen                 Sequenz 10
    Projekte                         Sequenz 10
    Einstellungen                    Sequenz 0
  Berichtswesen                      Sequenz 99
    Statistik Aufgaben               Sequenz 10
Zeiterfassung (Wurzel, Sequenz 55)
  Zeiterfassung                      Sequenz 5
    Meine Stundenzettel              Sequenz 10
    Alle Zeiterfassungen             Sequenz 10
  Konfiguration
    Einstellungen
  Berichtswesen
    Zeiterfassung
      Nach Mitarbeiter               Sequenz 10
      Nach Projekt                   Sequenz 15
      Nach Aufgabe                   Sequenz 20
      Anwesenheit                    Sequenz 10
      Nach Abrechnungsrate           Sequenz 40
    Kosten und Erloese               Sequenz 50
```

### 1.4 Projektformular (gerenderte Ansicht, deutsch)

Zwei Reiter: "Einstellungen", "E-Mails".

Sichtbare Elemente: zwei Zaehler-Buttons "Dokumente" (doc_count) und "Aufgaben"
(task_count); Feld Kostenstelle (analytic_account_id, in der Ansicht unsichtbar
geschaltet, da Pflichtfeld); Name (Kostenstelle); "Nutze Aufgaben als"
(label_tasks); "Zeiterfassungen erlauben" (allow_timesheets); "Projektmanager"
(user_id); Sub-Task-Projekt (subtask_project_id); "Privatsphaere" (privacy_visibility,
Radio); "Kunde" (partner_id); E-Mail-Alias-Felder (alias_id, alias_name, alias_domain,
"E-Mails annehmen von" alias_contact); Abonnenten. Button "Zeiterfassung" (Aktion 409).

### 1.5 Aufgabenformular (gerenderte Ansicht, deutsch)

Drei Reiter: "Beschreibung", "Zeiterfassung", "Weitere Informationen".

Kopf: Statusleiste (stage_id, "Stufe"), Zaehler "Unteraufgaben", Aktiv-Schalter,
Kanban-Status, Prioritaet, Titel (name), Projekt (project_id), Zugewiesen an (user_id),
Auftragselement (sale_line_id), Frist (date_deadline), Stichwoerter (tag_ids).

Weitere Felder: Beschreibung; geplante Stunden (planned_hours, "Ursprueglich geplante
Stunden"), Fortschritt, Zeiterfassung (timesheet_ids); geleistete/verbleibende/gesamt
Stunden; Kunde (partner_id); E-Mail (email_from); uebergeordnete Aufgabe (parent_id,
Unteraufgaben child_ids); Firmen- und Technik-Felder. Knoepfe: "Mir zuweisen",
"Uebergeordnete Aufgabe", Verkaufsauftrag (action_view_so).

### 1.6 Liste, Kanban, Suche

- Projektliste: Nummernfolge (handle), Projektbezeichnung, Projektmanager, Kontakt.
- Projekt-Kanban: gruppiert nach Projektmanager; Karte mit Name, Projektmanager, Kontakt.
- Aufgabenliste: (Reihenfolge) Aufgabenbezeichnung, Projekt, Zugewiesen an, geplante
  Stunden, verbleibende Stunden, geleistete Stunden, Frist, Stufe, Fortschritt.
- Aufgaben-Kanban: nach Stufe, mit Prioritaet, Beschreibung, Frist, Tags, Fortschritt.
- Projektsuche: Felder Projektbezeichnung/Projektmanager/Kontakt; Filter "Meine
  Favoriten", "Abonniert von mir", "Archiviert", Manager, Kontakt.
- Aufgabensuche: 6 Suchfelder, 16 Filter (u. a. "Meine Aufgaben", "Nicht zugewiesen",
  "Markiert", "Archiviert", Aktivitaetsfilter, Projekt/Aufgabe/Zugewiesen an/Stufe/
  Unternehmen).

### 1.7 Stufen (project.task.type) und Nutzung

87 Aufgabenstufen; 83 sind einem Projekt zugeordnet, 4 sind projektlos (New, Basic,
Advanced, amtsweg.gv.at - Partner und Dritte). Die Stufen sind projektbezogen (m2m
Feld project_ids). Felder: Bezeichnung Stufe, Nummernfolge, "Gefaltet im Kanban"
(fold), Beschreibung, E-Mail Vorlage, drei Legenden-Texte (Rot/Gruen/Grau),
"Stern-Erklaerung" (legend_priority), Projects.

### 1.8 Bestand und tatsaechliche Nutzung (Odoo 11)

| Punkt | Wert |
|---|---|
| Projekte | 28 (alle aktiv) |
| Sichtbarkeit (privacy_visibility) | employees 25, followers 3 |
| "Nutze Aufgaben als" (label_tasks) | Tasks 27, Faelle 1 |
| Aufgaben | 598 (alle aktiv; 1 ohne Projekt) |
| Aufgaben-Prioritaet | alle 0 (Niedrig) |
| Aufgaben-Kanban-Status (kanban_state) | alle "normal" |
| Aufgaben mit Stufe | 548 (50 ohne) |
| Aufgaben mit Frist | 44 |
| Aufgaben mit Stichwort | 1 (von 598) |
| Aufgaben mit Unteraufgabe | 0 |
| Aufgaben mit geplanter Zeit | 22 (planned_hours > 0) |
| Aufgaben mit Zeiterfassung | 127 |
| Aufgaben mit Beschreibung | 547 |
| Aufgaben mit Notizen (notes) | 0 |
| Aufgaben mit Auftragsposition (sale_line_id) | 0 |
| Projekt-Stichwoerter (tag_ids) | 0 Projekte |
| Projekt-Verknuepfung Auftrag (sale_line_id) | 0 |
| Projekt-Start-/Enddatum | 0 |
| Projekt-Abos (subscription_ids) | 0 |
| Zeiterfassungszeilen (account.analytic.line) | 12.657 (12.375 mit Projekt, 12.516 mit Aufgabe, 282 ohne Projekt) |
| Zeiterfassung mit so_line (Auftragsposition) | 0 |
| Projekt-Freigabe Zeiterfassung (allow_timesheets) | 28 (alle) |

Verteilung der Aufgaben auf Stufen (Top): Fertiggestellt 247, Produktive Freigabe 112,
ohne Stufe 50, Erledigt 29, Produktivsetzen 19, Zeiterfassung 18, gesonderte
Verrechnung 17.

Verteilung Zugewiesen an (Top): Breiteneder Lorenz 463, Tiefling Agnes 40,
Osagie Jonathan 30, Maierhofer Anna 17, Sallmann Alexander 15.

### 1.9 Rechte, Gruppen, Regeln

| Gruppe | Mitglieder | implied |
|---|---|---|
| Projekt / Manager (group_project_manager) | 19 | Projekt / Benutzer |
| Projekt / Benutzer (group_project_user) | 22 | Basis-Benutzer |
| "Use Subtask Project" (Technisch) | 11 | - |

Zugriffsrechte: Projekt (User R/W/C, Manager R/W/C/D, Employee R/W/C, Portal R,
Timesheets/User R), Aufgabe (User R/W/C/D, Manager R/W/C/D, Employee R, Portal R,
Timesheets/User R/W), Stufe (Manager R/W/C/D; User/Employee/Portal nur R), Tags.
Record Rules: Projekt/Aufgabe je employees (Folgen erforderlich), portal users,
project manager (sieht alles), multi-company; Statistik Aufgaben multi-company.

### 1.10 Einstellungen

`group_subtask_project` (Unteraufgaben), `module_hr_timesheet` (Zeiterfassung),
`module_sale_timesheet` (Zeitabrechnung), `module_project_timesheet_holidays`,
`module_project_forecast`, `module_rating_project`, `project_time_mode_id`
(Projekt-Zeiteinheit), `leave_timesheet_project_id`/`leave_timesheet_task_id`.

## 2. Odoo-18-Ausgangszustand (lokal = VM)

### 2.1 Module

| Modul | Version | State | Bedeutung |
|---|---|---|---|
| project | 18.0.1.3 | installiert | Projekt und Aufgaben |
| analytic | 18.0.1.2 | installiert | Kostenrechnung |
| hr | 18.0.1.1 | installiert | Mitarbeiter (Zeiterfassung) |
| hr_timesheet | 18.0.1.1 | installiert | Zeiterfassung auf Aufgaben |
| hr_timesheet_attendance | 18.0.1.1 | installiert | Anwesenheiten |
| project_timesheet_holidays | 18.0.1.0 | installiert | Zeiterfassung bei Abwesenheit |
| project_timesheet_time_control | 18.0.1.0.7 | installiert | Start/Stopp-Zeitsteuerung |
| project_todo | 18.0.1.0 | installiert | To-Do (Private Aufgaben) |
| project_account | 18.0.1.0 | installiert | Projekt und Abrechnung |
| project_hr_skills | 18.0.1.0 | installiert | Projekt und Kompetenzen |
| project_purchase | 18.0.1.0 | installiert | Projekt und Einkauf |
| project_stock | 18.0.1.0 | installiert | Projekt und Lager |
| project_sms | 18.0.1.1 | installiert | Projekt und SMS |
| itk_projectcategory | 18.0.1.0.3 | installiert | ITK-Projektkategorie (Abrechnung) |
| helpdesk_mgmt_project | 18.0.1.3.0 | installiert | Helpdesk-Verknuepfung |
| helpdesk_mgmt_timesheet | 18.0.1.1.3 | installiert | Helpdesk-Zeiterfassung |
| **sale_project** | 18.0.1.0 | **NICHT installiert** | Projekt aus Verkaufsauftrag |
| **sale_timesheet** | 18.0.1.0 | **NICHT installiert** | Abrechnung nach Aufwand (Verkauf/Zeiterfassung) |
| timesheet_grid | 18.0.1.0 | **uninstallable** | Timesheet-Raster |

### 2.2 Modelle und Umfang

Odoo 18 hat deutlich mehr Modelle als Odoo 11:

| Modell | Bezeichnung | Felder | Bestand lokal/VM |
|---|---|---|---|
| project.project | Project | 122 | 5 |
| project.task | Task | 124 | 8 |
| project.task.type | Task Stage | 17 | 16 |
| project.tags | Project Tags | 10 | 0 |
| project.project.stage | Project Stage (Projektphase) | - | 4 |
| project.milestone | Project Milestone | - | 0 |
| project.update | Project Update | - | 0 |
| project.collaborator | Collaborators in project shared | - | 0 |
| project.task.recurrence | Task Recurrence | - | - |
| project.task.stage.personal | Personal Task Stage | - | 1 |
| project.share.wizard / .collaborator.wizard | Projekt-Freigabe | - | (transient) |
| report.project.task.user | Tasks Analysis | - | (Bericht) |

### 2.3 Menuebaum (deutsche Anzeige)

```
Projekt (Wurzel, Sequenz 70)
  Projekte                           Sequenz 1
  Aufgaben                           Sequenz 2
    Meine Aufgaben                   Sequenz 1
    Alle Aufgaben                    Sequenz 2
  Berichtswesen                      Sequenz 99
    Aufgabenanalyse                  Sequenz 10
    Kundenbewertungen                Sequenz 51
  Konfiguration                      Sequenz 100
    Einstellungen                    Sequenz 0
    Projekte                         Sequenz 5
    Projektphasen                    Sequenz 9
    Stichwoerter                     Sequenz 10
    Aktivitaetstypen                 Sequenz 10
    Aktivitaetsplaene                Sequenz 10
Zeiterfassung (Wurzel, Sequenz 75)
  Meine Zeiterfassungen              Sequenz 10
  Zeiterfassung                      Sequenz 5
    Meine Zeiterfassungen            Sequenz 10
    Alle Zeiterfassungen             Sequenz 10
    Start work / Arbeit starten      Sequenz 10
  Berichtswesen                      Sequenz 99
    Zeiterfassung
      Nach Mitarbeiter               Sequenz 10
      Nach Projekt                   Sequenz 15
      Nach Aufgabe                   Sequenz 20
    Analyse von Zeiterfassung / Anwesenheit
  Konfiguration                      Sequenz 100
Abrechnung/Konfiguration/Verwaltung/Projektkategorien  (itk_projectcategory)
```

### 2.4 Projektformular (gerenderte Ansicht, deutsch)

Drei Reiter: "Beschreibung", "Einstellungen", "Kostenrechnung".

Kopf: Phasenleiste (stage_id, Projektphase); Zaehler Aufgaben, Fortschritt,
"Status" (last_update_status, "Projektaktualisierung"); Tickets (ticket_count);
Name; "Bezeichnung der Aufgaben" (label_tasks); Kunde (partner_id); Stichwoerter
(tag_ids); Projektmanager (user_id); "Geplantes Datum" (date_start/daterange);
zugewiesene Zeit (allocated_hours); Beschreibung; Sichtbarkeit (privacy_visibility,
Radio); Alias-Felder; "Aufgabenabhaengigkeiten", "Meilensteine", "Zeiterfassung"
(allow_timesheets); Kundenbewertung; Kostenstelle (account_id). Knoepfe: "Projekt
teilen", Aufgaben ansehen, `project_update_all_action`, "Start work"/"Arbeit starten".

Neu gegenueber Odoo 11: Projektphasen, Projektaktualisierungen (Status),
Meilensteine, Kundenbewertung, Projekt-Freigabe/Teilen, Kostenrechnung als
eigener Reiter.

### 2.5 Aufgabenformular (gerenderte Ansicht, deutsch)

Vier Reiter: "Beschreibung", "Zeiterfassung", "Teilaufgaben", "Blockiert durch".
Dazu die "Persoenliche Phase" (personal_stage_type_id).

Kopf: Phasenleiste (stage_id), Status (state), Titel (name), Prioritaet,
Projekt (project_id), "Assignees" (user_ids, Mehrfachzuweisung), Stichwoerter,
Frist (date_deadline, Datum UND Uhrzeit), Kunde, Meilenstein.

Felder: zugewiesene Zeit (allocated_hours), Fortschritt, Zeiterfassung, geleistete/
verbleibende Zeit; Unteraufgaben (child_ids, native Unteraufgaben); Abhaengigkeiten
(depend_on_ids "Blockiert durch"); Wiederkehrende Aufgaben (recurrence); Beschreibung;
Aktivitaeten (Chatter).

Wichtige Strukturunterschiede zur Odoo-11-Aufgabe:
- Zugewiesen: Odoo 11 `user_id` (eine Person), Odoo 18 `user_ids` (mehrere Personen).
- Prioritaet: Odoo 11 [Niedrig, Normal], Odoo 18 [Niedrig, Hoch].
- Frist: Odoo 11 Datum, Odoo 18 Datum+Uhrzeit.
- Zusaetzlicher Status `state` (In Bearbeitung/Rueckmeldung erbeten/.../Erledigt/
  Abgebrochen/Warten) und persoenliche Phasen.
- Kein Feld fuer "Startdatum" (Odoo 11 hatte `date_start`, auf allen 598 Aufgaben gesetzt).
- Geplante Zeit heisst `planned_hours` (Odoo 11) bzw. `allocated_hours` (Odoo 18).

### 2.6 Liste, Kanban, Suche

- Projektliste (33 Felder): Name, Kunde, Projektmanager, "Geplantes Datum",
  Meilenstein-Fortschritt, Status, Phase, Stichwoerter, zugewiesene/geleistete/
  verbleibende Zeit, Letzte Aktualisierung. Spalten teils optional (abwaehlbar).
- Projekt-Kanban: Karte mit Name, Kunde, Projektmanager, Fortschritt, Bewertung.
- Aufgabenliste: Titel, Projekt, Assignees, Phase, Frist, Zeiterfassung, Fortschritt,
  Aktivitaet, Bewertung, Stichwoerter, persoenliche Phase.
- Aufgaben-Kanban: nach Phase, mit Prioritaet, Frist, Tags, Fortschritt, Aktivitaet.
- Projektsuche: 5 Suchfelder, 16 Filter ("Meine Projekte", "Meine Favoriten",
  "Nicht zugewiesen", "Zeiterfassung > 100 %", "Verspaetete Meilensteine", Datums-
  und Aktivitaetsfilter, "Open Tickets", Gruppe nach Phase/Status/Stichwoerter).
- Aufgabensuche: 9 Suchfelder, 38 Filter (u. a. "Meine Aufgaben", "Verfolgt",
  "Nicht zugewiesen", "Private Aufgaben", "Blockiert", "Blockierend",
  "Zeiterfassung 80 %", Fristfilter, "Offene/Abgeschlossene Aufgaben", Aktivitaeten).

### 2.7 Stufen, Phasen und Nutzung

- Aufgabenstufen (project.task.type): 16 Datensaetze; einige projektbezogen
  (Internal; je Projekt To-do/In Bearbeitung/Erledigt/Abgebrochen), die uebrigen
  sind "persoenliche Phasen" der To-Do-App (Eingang, Heute, Diese Woche, Diesen
  Monat, Spaeter, Erledigt, Abgebrochen; user_id gesetzt).
- Projektphasen (project.project.stage): 4 (To Do, In Progress, Done, Cancelled),
  alle englisch benannt; alle 5 Projekte stehen auf "To Do". Odoo 11 hatte keine
  Projektphasen.
- Projekt-Tags: 0 Eintraege (Odoo 11: 13). Aufgabenstufen und Tags sind Stammdaten
  und noch nicht migriert.
- Bestand Odoo 18: 5 Projekte und 8 Aufgaben, alle aus frueheren Testsitzungen
  (Abo/Helpdesk-Testdaten, u. a. "S00176 - Test-Abo monatlich", "Helpdesk
  Test-Projekt"). Diese Testdaten wurden nicht von dieser Session angelegt und
  werden nicht geloescht.

## 3. Vergleichstabelle (Funktion, Odoo 11, Odoo 18, Unterschied, Bewertung)

| Funktion | Odoo 11 | Odoo 18 | Unterschied | Bewertung |
|---|---|---|---|---|
| Traegermodell Projekt | project.project erbt account.analytic.account; Kostenstelle Pflicht; Feld `name` = "Kostenstelle" | project.project eigenes Modell; Kostenstelle (`account_id`) optional | Kopplung geloest | Odoo-18-Standard uebernehmen (Kostenrechnung eigener Reiter) |
| Projektphasen | nicht vorhanden | project.project.stage (4) | Odoo-18-Zusatz | beibehalten, deutsche Namen noetig |
| Aufgabenstufen | project.task.type, 87 projektbezogen | project.task.type + persoenliche Phasen | gleiches Modell, zusaetzliche persoenliche Stufen | Struktur vorhanden; Stammdaten spaeter |
| Zugewiesen | user_id (eine Person) | user_ids (mehrere) | Feldname und Kardinalitaet | Odoo-18-Mehrfachzuweisung beibehalten |
| Prioritaet | Niedrig/Normal | Niedrig/Hoch | zweiter Wert anders | Wortlaut/Bedeutung klaeren |
| Frist | date_deadline (Datum) | date_deadline (Datum+Uhrzeit) | Datentyp | Odoo-18-Typ uebernehmen |
| Startdatum Aufgabe | date_start vorhanden (598 gesetzt) | kein Feld | Feld fehlt | Entscheidung: nachbauen oder nicht |
| Geplante/zugeteilte Zeit | planned_hours | allocated_hours | Feldname | Umbenennung dokumentieren |
| Aufgabenstatus | kanban_state (Grau/Gruen/Rot) | state + persoenliche Phase | neuer Status | Odoo-18-Zusatz beibehalten |
| Unteraufgaben | parent_id/child_ids + subtask_project_id | parent_id/child_ids (nativ) | vereinfacht | Odoo-18-Standard uebernehmen |
| Stichwoerter (Aufgabe) | project.tags (13) | project.tags (0) | Stammdaten fehlen | Stammdaten spaeter |
| Verkauf/Auftrag | sale_timesheet installiert; sale_line_id auf Projekt und Aufgabe | sale_project + sale_timesheet NICHT installiert; kein sale_line_id | Funktion fehlt | Entscheidung: Module installieren? (in Odoo 11 ungenutzt: 0 Verknuepfungen) |
| Zeiterfassung | account.analytic.line, user-basiert | account.analytic.line, employee-basiert; Projekt-Freigabe noetig | Mitarbeiterbezug | Odoo-18-Standard uebernehmen |
| Berichtswesen | Statistik Aufgaben (Grafik/Pivot) | Aufgabenanalyse (Pivot/Grafik) | Wortlaut | Wortlaut klaeren |
| Projekt-Dashboard | Menue "Projekt/Dashboard" | Aktion vorhanden, kein Menue | Menue fehlt | Entscheidung: Menue anlegen? |
| Rechte | Projekt/Manager (19), Projekt/Benutzer (22) | Projekt/Administrator (2), Projekt/Benutzer (2) | Gruppenrollen | Struktur vorhanden; Mitglieder spaeter |
| Bewertung/Meilensteine/Abhaengigkeiten/Wiederholung/Projekt-Freigabe/Kompetenzen/To-Do | nicht vorhanden | vorhanden | Odoo-18-Zusaetze | je Punkt beibehalten/ausblenden entscheiden |

## 4. Modulabhaengigkeiten und fehlende Funktionen

- **sale_timesheet** (Odoo 11: installiert, "Sales Timesheet") und
  **sale_project** (Projekt aus Verkaufsauftrag) sind in Odoo 18 NICHT installiert
  (nur "uninstalled" = verfuegbar, nicht geladen). Dadurch fehlen in Odoo 18:
  `sale_line_id` auf Projekt und Aufgabe, der Knopf "Verkaufsauftrag" auf der
  Aufgabe, die Projekterstellung aus einer Auftragsposition und die Abrechnung
  nach Aufwand (Verkauf/Zeiterfassung). In Odoo 11 war die Funktion vorhanden,
  aber faktisch ungenutzt (0 Aufgaben mit Auftragsposition, 0 Zeiterfassungszeilen
  mit so_line).
- **timesheet_grid** ist in Odoo 18 "uninstallable" (nicht ladbar).
- Zeiterfassung selbst (hr_timesheet) ist in beiden Versionen installiert;
  Odoo 18 verlangt die Projekt-Freigabe `allow_timesheets` und eine Mitarbeiter-
  Zuordnung (`employee_id`), Odoo 11 arbeitete ueber `user_id`.
- Analytic: Odoo 11 hat analytische Tags (`account.analytic.tag`), Odoo 18 hat
  stattdessen analytische Plaene und Verteilungsmodelle.

## 5. Deutsche Bezeichnungen: Befund

Die Pruefung der de_DE-Sicht zeigt in Odoo 18 englische Bezeichnungen. Wichtige
sichtbare Felder ohne deutsche Bezeichnung (deutsch = englisch):

Projekt: "Color Index" (Odoo 11: Farbkennzeichnung), "Currency" (Waehrung),
"Members" (Mitglieder), "Show Project on Dashboard" (Projekt auf dem Dashboard
anzeigen), "Tasks Stages" (Aufgabenstufen), "Task Count"/"Tasks" (Aufgaben),
"Working Time" (Arbeitszeit), "Associated Timesheets", "Ticket Count", "Update
Count", "Milestone Count", "Collaborators", "Last Update Status", "Can Mark
Milestone As Done", "Privacy Visibility Warning" u. a. (insgesamt 44 Felder).

Aufgabe: "Attachments" (Odoo 11: Hauptanhaenge), "Sub-tasks" (Unteraufgaben),
"Color Index", "Sub-task Count" (Anzahl Unteraufgaben), "Timesheets" (Zeiterfassung),
"Website Messages" (Website-Nachrichten), "Allow timesheets", "Milestones",
"Task Dependencies", "Dependent Tasks", "Display In Project", "Personal Stages"
u. a. (insgesamt 32 Felder).

Aufgabenstufe: "Disabled Rating Warning". Tags: "Projects", "Tasks".

Zusaetzlich englische Menue-/Knopftexte in Odoo 18: Menue "Start work" (auf der VM
"Arbeit starten"), Buttons "Start work"/"Stop". Projektphasen-Namen
(To Do, In Progress, Done, Cancelled) sind englische Standardwerte.

Abweichende gemeinsame Wortlaute (Odoo 11 gegen Odoo 18, de_DE):
Name des Projekts "Kostenstelle" gegen "Name"; Aufgabenstufe "Stufe" gegen "Phase";
Aufgabentitel "Aufgabentitel" gegen "Titel"; "Geleistete Stunden" gegen "Zeitaufwand";
"Verbleibende Stunden" gegen "Verbleibende Zeit"; "Abonnenten" gegen "Follower";
"Nummernfolge" gegen "Sequence"; "Waehrung" gegen "Currency"; "Arbeitszeit" gegen
"Working Time"; "Statistik Aufgaben" gegen "Aufgabenanalyse".

## 6. Bewusst beizubehaltende Odoo-18-Zusatzfunktionen (Vorschlag, noch nicht entschieden)

Projektphasen, Projektaktualisierungen (Status on_track/at_risk/...), Meilensteine,
Kundenbewertung (rating), Aufgabenabhaengigkeiten, wiederkehrende Aufgaben,
Projekt-Freigabe/Teilen mit Kollaborateuren (Portal), Personal/Kompetenzen,
private To-Do-Aufgaben, Projekt-Kanban mit Fortschritt. Diese Funktionen stoeren
den Odoo-11-Ablauf nicht; nach Annas Regel bleiben sie erhalten, solange sie nicht
stoeren. Endgueltig je Punkt entscheidet Anna.

## 7. Bewusst nicht nachzubauen (Vorschlag)

- Analytische Tags (`account.analytic.tag`) - ersetzt durch Odoo-18-analytische
  Plaene/Verteilung.
- `subtask_project_id` (Odoo-11-Sonderweg fuer Unteraufgaben) - ersetzt durch native
  Unteraufgaben.
- `notes` (Feld vorhanden, aber auf keiner der 598 Aufgaben genutzt).

## 8. Entscheidungspunkte fuer Anna (hier wird gemessen, nicht entschieden)

1. **Auftrag/Zeiterfassung (sale_timesheet, sale_project).** In Odoo 11 vorhanden,
   aber ungenutzt (0 Verknuepfungen). Module in Odoo 18 installieren (Funktion
   herstellen) oder bewusst weglassen?
2. **Startdatum auf Aufgabe.** Odoo 11 hatte `date_start` (auf allen 598 Aufgaben
   gesetzt); Odoo 18 hat kein solches Feld. Nachbauen (eigenes Feld im ITK-Modul)
   oder weglassen?
3. **Prioritaet.** Odoo 11 hatte Niedrig/Normal, Odoo 18 Niedrig/Hoch. Odoo-18-Werte
   uebernehmen oder an Odoo-11-Wortlaut ("Normal") angleichen?
4. **Menuefuehrung und Wortlaute.** Odoo 11: "Suchen" (Aufgaben, Naechste
   Aktivitaeten), "Dashboard", "Berichtswesen/Statistik Aufgaben",
   "Konfiguration/Projekte". Odoo 18: "Projekte", "Aufgaben" (Meine/Alle),
   "Berichtswesen/Aufgabenanalyse", "Konfiguration/Projekte/Projektphasen/
   Stichwoerter". Menues und Wortlaute an Odoo 11 angleichen, oder Odoo-18-Struktur
   belassen?
5. **Deutsche Bezeichnungen.** Die 44 (Projekt), 32 (Aufgabe), 1 (Stufe) und 2
   (Tags) englischen Feldbezeichnungen sowie die englischen Menue-/Knopftexte
   ("Start work", "Stop") und Phasennamen auf Deutsch setzen - sichtbare
   Odoo-11-Bezeichnung wo fachlich 1:1, sonst deutsche Neuuebersetzung?
6. **Projekt-Dashboard.** Odoo 11 hatte ein Menue "Projekt/Dashboard"; in Odoo 18
   ist die Aktion vorhanden, aber kein Menue. Menue anlegen oder weglassen?
7. **Odoo-18-Zusaetze.** Liste aus Abschnitt 6 je Funktion: sinnvoll beibehalten,
   stoerend und ausblenden, oder ohne Relevanz?
8. **Projektphasen (To Do/In Progress/Done/Cancelled).** Standardnamen behalten oder
   deutsche/ITK-Namen setzen?

## 9. Noch offen

- Stammdaten (Stufen, Tags, Projektphasen) sind nicht migriert - laut Projektregel
  erst nach Bereichsfreigabe und nur mit Auswahlregel.
- Rechte-Mitgliederlisten (Projekt/Manager und Projekt/Benutzer) sind spaeter
  gegen die Odoo-11-Benutzerlisten abzugleichen.
- Browsernachweise (lokal und VM) und Regression folgen erst nach der Umsetzung.
