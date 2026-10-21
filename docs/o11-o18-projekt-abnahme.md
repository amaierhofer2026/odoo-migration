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
