# Helpdesk Odoo 11 → Odoo 18: Vergleich, Anpassungen und Abnahme

Stand: 08.10.2026, Session 132. Sprache: nur Deutsch, einfache Zeichen.

Auftrag: Das Helpdesk in Odoo 18 fachlich und funktional so herstellen, dass ITK es
mindestens so verwenden kann wie das Helpdesk in Odoo 11. **Keine Datenmigration**:
es werden keine der 1.223 Odoo-11-Tickets, Anhänge oder Verlaufsdaten übernommen.
Odoo 11 (Produktion) wurde ausschliesslich lesend geprüft.

## 1. Odoo-11-Iststand (read-only erhoben)

### 1.1 Modul und Umfang

| Punkt | Wert |
|---|---|
| Modul | OCA `website_support` 11.0.1.3.1 (Helpdesk = "Website Help Desk / Support Ticket") |
| Zusatzmodule | `website_support_analytic_timesheets` 11.0.1.0.6, `website_support_billing` 11.0.1.0.0 |
| Modelle | 24 Modelle `website.support.*` |
| Datensätze im Modul | 492 (davon 330 Felddefinitionen, 41 Ansichten, 13 Menüs, 13 Aktionen, 10 Mailvorlagen, 6 Sequenzen) |
| Tickets | 1.223 (Stand 08.10.2026) |
| Weitere Bestände | 6 Stufen, 18 Kategorien, 20 Unterkategorien, 4 Prioritäten, 0 Stichwörter, 191 Zusatzfeldwerte, 57 Abschlusskommentare, 1 SLA, 4 SLA-Antwortzeiten, 3 SLA-Alarme, 797 Compose-Vorlagen, 910 Verlaufsnachrichten |

### 1.2 Menübaum (deutsche Anzeige)

```
Helpdesk (Wurzelmenü, Odoo-11-Datenwert "Customer Support", Sequenz 40)
  Support Tickets                      Sequenz 10   Liste, Kanban, Formular, Grafik
  Arbeitszeittabelle Berichte          Sequenz 30
  Konfiguration                        Sequenz 999
    Kategorien                         Sequenz 10
    Unterkategorien                    Sequenz 20
    Status                             Sequenz 30
    Stichwörter                        Sequenz 40
    Prioritäten                        Sequenz 50
    SLA's                              Sequenz 70
    Website Hilfe Gruppen              Sequenz 80   (0 Datensätze, nie genutzt)
    Website Hilfeseiten                Sequenz 90   (0 Datensätze, nie genutzt)
    Einstellungen                      Sequenz 100
```

### 1.3 Ticket-Formular (Aufbau)

Kopfzeile: Antworten (Compose-Assistent), Offen/Antworten, Ticket schliessen, SLA pausieren,
SLA fortsetzen, Umfrage senden, Genehmigungsanfrage stellen.

Zwei Spalten:
- links: Ticket-Nummer, Kanal, Priorität, Stichwörter, Kategorie, Unterkategorie, Status
- rechts: Zugewiesener Benutzer, Partner, Personenname, E-Mail, Genehmigungsanfrage,
  Partner Bewertung, Partner Kommentar, Kommentar bei Abschluss, Abschlusszeitpunkt

Reiter: Beschreibung, Zusätzliche Felder (Extra Details), Dateianhänge, SLA.
Die Zeiterfassung lag unterhalb der Beschreibung. Chatter mit Abonnenten und Verlauf.

### 1.4 Liste, Kanban, Suche

- Liste (10 Spalten): Erstellt am, Ticket-Nummer, Priorität, Zugewiesener Benutzer,
  Personenname, Kategorie, Status, Betreff, SLA Aktiv, Verbleibende SLA-Zeit
- Kanban: nach Status gruppiert; Karte zeigt Betreff, Priorität, Status, Kategorie, Beschreibung
- Suche: Ticket-Nummer, Betreff, Stichwörter, Partner; Filter "Unbeaufsichtigte Tickets";
  Gruppierung nach Kategorie und Benutzer
- Grafik: Ticketanzahl je Erstellungsdatum

### 1.5 Stammdaten und Wortlaute

- Stufen (Anzeige): Offen, in Bearbeitung, on Hold, Geschlossen/Behoben,
  an Partner weitergeleitet, Verrechnung mit Kunde geklärt
- Prioritäten: Niedrig (#ffff00), Mittel (#ffbf00), Hoch (#ff0000), Angebotsanforderung (#58acfa)
- Kanal (Auswahlliste): Email, Manual, Website (Public), Website (User)
- Ticketnummer: fortlaufend, ohne Präfix, lückenlos (no_gap); Stand 4.177
- Rechte: Support Client (21 Benutzer), Support Staff (21), Support Manager (6)
- SLA "Standard SLA Support ITK Produkte": 4 Antwortzeiten (48 Std., 24-Stunden-Zählung)
- öffentliches Formular: 1.167 der 1.223 Tickets kamen über "Website (Public)",
  33 über "Email", 17 über "Manual", 6 über "Website (User)"; das Formular hatte reCAPTCHA

Deutsche Feldbezeichnungen in Odoo 11 (aus den Übersetzungen belegt):
Betreff, Ticket-Nummer, Status, Kanal, Priorität, Stichwörter, Kategorie, Unterkategorie,
Zugewiesener Benutzer, Partner, Personenname, E-Mail, Partner Kommentar,
Kommentar bei Abschluss, Abschlusszeitpunkt, Geschlossen von, Media Anhänge,
Extra Details, SLA Aktiv, Verbleibende SLA-Zeit.

## 2. Odoo-18-Ausgangszustand

Ersatz für `website_support` ist OCA `helpdesk_mgmt` 18.0.1.17.1 mit
`helpdesk_mgmt_project`, `helpdesk_mgmt_sla`, `helpdesk_mgmt_timesheet`
sowie den ITK-Modulen `itk_helpdesk_compat` und `itk_helpdesk_category_user`.

Befunde im Ausgangszustand (vor dieser Session):

| Nr | Befund |
|---|---|
| B1 | `itk_helpdesk_compat` importierte sein Paket `controllers` nicht; die Portal-Anpassungen waren wirkungslos, es gab keine Route für ein öffentliches Formular |
| B2 | Kanalwerte Odoo-18-Standard (Web, Email, Phone, Other) statt der vier Odoo-11-Kanäle |
| B3 | Kanäle wurden nicht aus dem Entstehungsweg gesetzt (Portal setzte "Web") |
| B4 | Ticketnummernkreis OCA-Standard HT00001 statt fortlaufend ohne Präfix |
| B5 | Ticketformular ohne Team-Feld (Team nicht zuweisbar) |
| B6 | Feldbezeichnungen teils englisch (Titel, Ticketnummer, Stufe, Color, Name/Sequence im Prioritätsmodell) bzw. abweichend (Abschluss, Kontakt, Partnername, E-mail, Medienanhänge) |
| B7 | Menü "Hilfeseiten" war ein Platzhalter ohne Funktion |
| B8 | Menüpunkt "Support Tickets" lag unter "Tickets > ..." statt direkt unter der App; "Timesheets", "Dashboard" und "SLAs" waren englisch bzw. anders benannt als in Odoo 11 |
| B9 | Beschreibung war Pflichtfeld (Odoo 11 verlangte keine Beschreibung) |
| B10 | Mailvorlage "Neues Ticket bei IT-Kommunal" nutzte `team_id.email` - dieses Feld gibt es im Odoo-18-Team nicht (Renderfehler beim Speichern) |
| B11 | Ansicht "Anhang" (many2many_binary) und Beschriftung "Zusätzliche Felder" wichen vom Odoo-11-Wortlaut ab |
| B12 | `itk_helpdesk_category_user` setzte den Parameter `tracking` auf einem Many2many-Feld (Warnung, wirkungslos) |
| B13 | Zwei Vorlagen-Ansichten nutzten `t-att-...="#{...}"` (falsche Attributart); das Portal-Formular brach dadurch mit QWeb-Fehler ab |

## 3. Entscheidungen von Anna (verbindlich)

1. **Kanäle**: Die vier Odoo-11-Kanäle werden hergestellt (Email, Manual, Website (Public),
   Website (User)) und automatisch aus dem Entstehungsweg gesetzt. Odoo-18-Zusatzwerte
   dürfen erhalten bleiben.
2. **Öffentliches Ticketformular** ohne Anmeldung wird wiederhergestellt, mit Spamschutz.
3. **Ticketnummern**: fortlaufend, lückenlos, ohne Präfix wie in Odoo 11.

## 4. Umsetzung (itk_helpdesk_compat 18.0.1.1.2, itk_helpdesk_category_user 18.0.1.0.1)

| Nr | Maßnahme | Datei |
|---|---|---|
| M1 | Paket `controllers` importiert; öffentliches Formular `/support/ticket/new` mit eigener Route (auth="public") | `__init__.py`, `controllers/public.py`, `views/helpdesk_public_templates.xml` |
| M2 | Spamschutz: Honigtopf-Feld, Rate-Limit je IP und insgesamt je Stunde (Modell `itk.helpdesk.public.submission`), reCAPTCHA bei hinterlegtem Schlüssel | `controllers/public.py`, `models/itk_helpdesk_public_submission.py` |
| M3 | Kanäle Email/Manual/Website (Public)/Website (User); "Web" archiviert; Kanal automatisch nach Herkunft (Backend = Manual, Portal = Website (User), öffentlich = Website (Public), E-Mail-Eingang = Email) | `data/helpdesk_channels.xml`, `models/helpdesk_ticket.py`, `controllers/portal.py` |
| M4 | Ticketnummer ohne Präfix, Padding 0, lückenlos | `migrations/18.0.1.1.0/post-migration.py` |
| M5 | Formular: Team-Feld ergänzt; Knoepfe "Offen / Antworten" und "Ticket schliessen"; Felder nach Odoo-11-Anordnung; Reiter Beschreibung/Zusätzliche Felder/Dateianhänge/SLA/Zeiterfassung | `views/helpdesk_ticket_views.xml` |
| M6 | Listenansicht exakt in Odoo-11-Spaltenfolge; Kanban wieder in der Aktion; kein Vorfilter mehr | `views/helpdesk_ticket_views.xml` |
| M7 | Suche: Filter "Unbeaufsichtigte Tickets", Gruppierung Kategorie/Benutzer | `views/helpdesk_ticket_views.xml` |
| M8 | Deutsche Bezeichnungen (de.po + Ansichtstexte) nach Odoo-11-Wortlaut | `i18n/de.po`, `views/*.xml` |
| M9 | Menüführung: "Support Tickets" direkt unter der App, Konfiguration in Odoo-11-Reihenfolge, "Übersicht", "Arbeitszeittabelle", "SLA's"; Platzhalter "Hilfeseiten" entfernt | `views/menus.xml`, `migrations/18.0.1.1.0/post-migration.py` |
| M10 | Beschreibung nicht mehr Pflicht; Feld "Geschlossen von" ergänzt | `models/helpdesk_ticket.py` |
| M11 | Mailvorlage nutzt `team_id.alias_email` bzw. Firmenadresse, Empfänger zusätzlich `partner_email`; Stufe "Offen" trägt die Vorlage | `migrations/18.0.1.1.1+1.1.2`, `__init__.py` |
| M12 | Eigene Felder des Prioritätsmodells deutsch; Kategorie-Benutzer im Odoo-11-Wortlaut; `tracking`-Warnung entfernt | `models/itk_helpdesk_priority.py`, `itk_helpdesk_category_user/*` |
| M13 | Falsche `t-att-`/`#{}`-Kombinationen in beiden Vorlagen korrigiert | `views/helpdesk_ticket_templates.xml`, `helpdesk_public_templates.xml` |

## 5. Vergleichstabelle (Funktion → Entsprechung → Unterschied → Anpassung)

| Odoo 11 | Odoo 18 | Unterschied | Anpassung |
|---|---|---|---|
| Modul website_support | OCA helpdesk_mgmt + itk_helpdesk_compat | anderes Modul, gleiche Aufgabe | Oberfläche und Menüs nachgebaut, Funktionen belassen |
| Stufe `state` (many2one) | `stage_id` (many2one) | Feldname, gleiche Funktion | Beschriftung "Status", identische Stufen |
| Priorität `priority_id` | `priority_id` (eigenes Modell) | OCA hat zusätzlich Sterne-Priorität | Sterne ausgeblendet, ITK-Priorität massgeblich |
| Kanal `channel` (Auswahlfeld) | `channel_id` (many2one) | Auswahl vs. Stammdaten | vier Odoo-11-Werte, automatisch gesetzt |
| Kategorie/Unterkategorie (zwei Modelle) | ein Modell mit `parent_id` | ein Baum statt zwei Modelle | Menüs Kategorien/Unterkategorien, Domain auf die Hauptkategorie |
| Zusatzfelder (ticket.field) | `dynamic_field_value_ids` | gleiche Idee, neues Modell | Reiter "Zusätzliche Felder", Feldbezeichnung "Extra Details" |
| Partner/Personenname/E-Mail | `partner_id`/`partner_name`/`partner_email` | gleiche Funktion | deutsche Beschriftungen Partner/Personenname/E-Mail |
| Zugewiesener Benutzer | `user_id` | gleich | Beschriftung wie Odoo 11 |
| Geschlossen von | neu: `closed_by_id` | Odoo 18 hatte das Feld nicht | Feld ergänzt, wird beim Schliessen gesetzt |
| Abschlusszeitpunkt | `closed_date` | gleich | Beschriftung wie Odoo 11 |
| Kommentar bei Abschluss | `close_comment` | gleich | Beschriftung wie Odoo 11 |
| SLA pausieren/fortsetzen | `helpdesk_mgmt_sla` mit "Ignorier-Stufen" | anderer Mechanismus | dokumentiert, Konfiguration für Produktivstart |
| Umfrage senden / Genehmigungsanfrage | nicht vorhanden | in Odoo 11 praktisch ungenutzt (2 Bewertungen) | bewusst nicht nachgebaut, dokumentiert |
| Website Hilfe Gruppen/Seiten | nicht vorhanden | in Odoo 11 leer | Platzhaltermenü entfernt |
| Anhänge | `attachment_ids` | gleich | Beschriftung "Media Anhänge" |
| Chatter/Verlauf | `mail.thread` | gleich | übernommen |
| Teams | nicht vorhanden | Odoo-18-Zusatz | Feld sichtbar, Menü "Helpdesk-Gruppen" |
| Aktivitäten | nicht vorhanden (Odoo 11: Verlauf) | Odoo-18-Zusatz | übernommen |

## 6. Bewusst erhaltene Odoo-18-Zusatzfunktionen

- Teams (Helpdesk-Gruppen) mit SLA-Flag und Arbeitszeiten
- SLA-Modul mit Fristen und Ignorier-Stufen, Dashboard "Übersicht"
- Zeiterfassung auf Tickets (Reiter "Zeiterfassung")
- Aktivitäten und geplante Aktivitäten
- Duplikaterkennung, Portalzugriff, Bewertungsmodell (rating_ids)
- Berichtswesen (Pivot/Grafik) als Ersatz für die Odoo-11-Grafik im Ticketmenü
- Kanäle Phone und Other als zusätzliche Werte

## 7. Bewusste Abweichungen

| Abweichung | Grund |
|---|---|
| Zeiterfassung als eigener Reiter statt unter der Beschreibung | Odoo-18-Standard von helpdesk_mgmt_timesheet, Funktion gleichwertig |
| Bezeichnung "Zeiterfassung" statt des in Odoo 11 unübersetzt englischen "Timesheet" | deutscher Wortlaut |
| "Zuletzt aktualisiert von" statt "Zuletzt aktualisiert durch" | Grundwortlaut des Odoo-18-Kerns, nicht helpdesk-spezifisch |
| Statusfeld heisst technisch `stage_id` ("Stufe"), sichtbar "Status" | Label-Regel: sichtbare Odoo-11-Bezeichnung, technischer Name bleibt |
| Grafik im Ticketmenü entfällt, Berichtswesen/Pivot bleibt | Odoo-18-Standard, gleiche Auswertung |
| Umfrage/Genehmigung entfallen | in Odoo 11 mit 2 Bewertungen praktisch ungenutzt |
| Helpdesk-Gruppen (Teams) und deren Menü sind neu | Odoo 11 kannte keine Teams; ohne Teams gäbe es keine SLA-Zuordnung |

## 8. Konfiguration für den Produktivstart (nicht ungefragt angelegt)

1. **Teams**: Team(s) anlegen, "Use SLA" setzen, Arbeitszeiten pflegen, Teamleiter zuweisen.
2. **SLA**: Eintrag mit Zielstufe "Geschlossen/Behoben", Ignorier-Stufe "on Hold"
   (entspricht "SLA pausieren" aus Odoo 11), Kategorien und Reaktionszeit
   (Odoo 11: 48 Stunden, 24-Stunden-Zählung für vier Kategorien).
3. **Kategorien/Unterkategorien**: Die 17 Haupt- und 20 Unterkategorien sind in der
   Testinstanz bereits vorhanden; für die Produktion aus Odoo 11 übernehmen
   (Stammdaten, keine Ticketdaten).
4. **Prioritäten**: Niedrig, Mittel, Hoch, Angebotsanforderung mit den Odoo-11-Farben.
5. **Zusatzfelder**: Definitionen je Unterkategorie (Odoo 11 nutzte 191 Werte;
   Beispiel "Angebot anfordern": Einwohnerzahl, Produkt).
6. **E-Mail-Eingang**: Alias am Helpdesk-Team hinterlegen, damit der Kanal "Email"
   automatisch gesetzt wird.
7. **reCAPTCHA**: Schluessel unter Einstellungen > Google reCAPTCHA hinterlegen;
   ohne Schlüssel ist die Prüfung inaktiv, Honigtopf und Rate-Limit bleiben aktiv.
8. **Nummernkreis**: ohne Präfix, Padding 0, lückenlos (bereits eingestellt).
9. **Rechte**: Helpdesk/User für Sachbearbeiter, Helpdesk Manager für Konfiguration;
   Portalnutzer sehen ihre eigenen Tickets.
10. **Benachrichtigungsvorlagen**: "Neues Ticket bei IT-Kommunal" ist der Stufe "Offen"
    zugeordnet; weitere Vorlagen (Zuweisung, Abschluss, Statuswechsel) sind englisch
    und können später übersetzt werden.

## 9. Prüfungen

Siehe Abschnitt "Ergebnisse" in `docs/o11-o18-helpdesk-abnahme.md`.

## 10. Offene Punkte

- SLA-Konfiguration und Team-Alias sind Produktivstart-Aufgaben (Abschnitt 8).
- Vorlagen für Benachrichtigungen sind teils englisch (OCA-Standard).
- Die Odoo-11-Genehmigungs- und Umfragefunktion ist nicht nachgebaut (ungenutzt).
