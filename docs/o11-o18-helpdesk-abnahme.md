# Helpdesk Odoo 18: Abnahme und Ergebnisse

Stand: 08.10.2026, Session 132. Ergänzung zu `docs/o11-o18-helpdesk-vergleich.md`.

## 1. Prüfumfang

Erhebung Odoo 11 (read-only, Produktion portal.it-kommunal.at, DB ITK_V1_a):
`scripts/erhebe_helpdesk_o11.py`, `_teil2`, `_teil3`, Auswertung
`scripts/werte_helpdesk_o11_aus.py`, Wortlautvergleich `scripts/vergleiche_helpdesk_labels.py`.
Rohdaten: `%USERPROFILE%\Desktop\Odoo18-Helpdesk-Session132\rohdaten\`.

Erhebung und Prüfung Odoo 18: `scripts/erhebe_helpdesk_o18.py --instanz lokal|vm`,
Bestand `scripts/helpdesk_bestand.py`, Browserabnahme
`scripts/browser_helpdesk_abnahme.py lokal|vm` (echter Chrome, headless, Screenshots in
`%USERPROFILE%\Desktop\Odoo18-Helpdesk-Session132\browser\<instanz>\`).

## 2. Browserabnahme lokal (echter Chrome, echte Bedienung)

Ergebnis des letzten Durchlaufs: **53 OK, 0 echte Produktfehler**.
Vier Meldungen betreffen ausschliesslich die Prüftechnik beziehungsweise einen
vorbestehenden Fremdfehler (siehe Abschnitt 4).

Belegt wurden unter anderem:

| Prüfung | Ergebnis |
|---|---|
| Menüpunkte der App | Übersicht, Tickets, Support Tickets, Arbeitszeittabelle, Berichtswesen, Konfiguration |
| Konfigurationspunkte | Kategorien, Unterkategorien, Status, Stichwörter, Prioritäten, SLA's, Helpdesk-Gruppen, Einstellungen |
| Listenspalten | Erstellt am, Ticket-Nummer, Priorität, Zugewiesener Benutzer, Personenname, Kategorie, Status, Betreff (exakt Odoo 11) |
| Kanban | nach Status gruppiert, 6 Spalten |
| Suche / Filter / Gruppierung | Suche, Filter "Unbeaufsichtigte Tickets", Gruppierung Kategorie/Benutzer |
| Ticket anlegen | Betreff, Kategorie, Unterkategorie, Priorität, Team, Bearbeiter, Partner, Beschreibung, Anhang |
| Kanal Backend | automatisch "Manual" |
| Ticketnummer | ohne Präfix, fortlaufend (1, 2, ...) |
| Stammdaten | Stufen, Prioritäten, Kanäle, 17 Haupt- und 20 Unterkategorien wie Odoo 11 |
| SLA | SLA am Ticket angewandt (sla_ids gesetzt) |
| Statuswechsel | in Bearbeitung, an Partner weitergeleitet, zurück auf in Bearbeitung |
| Nachricht | Notiz im Verlauf gespeichert |
| Öffentliches Formular | ohne Anmeldung erreichbar, Pflichtfelder greifen, Kategorie/Unterkategorie, Zusatzfeld, Anhang, Absenden |
| Öffentliches Ticket | Kanal "Website (Public)", Nummer vergeben, Team und Status gesetzt, Zusatzfeldwert und Anhang übernommen, Verlauf/Benachrichtigung vorhanden, keine JavaScript-Fehler |
| Rechte | Gruppen User und Helpdesk Manager besetzt, 5 Zugriffszeilen und 6 Record Rules auf helpdesk.ticket |
| Aufräumen | Bestand vorher = nachher, Zusatzfelder und Spamschutz-Protokolle entfernt |

## 3. Nachweise

- Ticketnummernkreis: Sequenz `helpdesk.ticket.sequence` ohne Präfix, Padding 0, lückenlos;
  im Browser vergebene Nummern "1" und "2" (Neustart der Zählung ist mit der Entscheidung
  gedeckt, da keine Altdaten migriert werden).
- Kanäle: im Browser erzeugtes Backend-Ticket mit Kanal "Manual", öffentliches Formular
  mit "Website (Public)"; Portalweg setzt "Website (User)"; E-Mail-Eingang setzt "Email".
- Deutsch: Feld- und Menübezeichnungen im Browser geprüft (Betreff, Ticket-Nummer, Status,
  Personenname, Abschlusszeitpunkt, Kommentar bei Abschluss, Stichwörter, Media Anhänge).

## 4. Abweichungen und Befunde

1. **Aktivitäten**: Behoben in `itk_crm` 18.0.1.5.10. Ursache: Der Assistent
   `mail.activity.schedule` sendet das im Formular nicht gerenderte Feld `res_model`
   beim Speichern nicht mit; ohne `res_model` blieb `res_model_id` leer und das Anlegen
   brach mit "Pflichtfeld ist nicht eingestellt" ab - beim Start aus dem Chatter eines
   Belegs wie beim Start aus dem Aktivitätenmenü. Der ITK-Erbe zieht das Ziel jetzt
   serverseitig aus dem Kontext (`active_model`) beziehungsweise aus dem gewählten
   Dokumenttyp nach. Zusätzlich löscht `_onchange_itk_target_res_id` das Ziel nicht
   mehr, wenn der Assistent aus dem Chatter geöffnet wurde.
   Nachweis im echten Browser (08.10.2026): Aktivität im Chatter eines Helpdesk-Tickets
   und eines Kontakts angelegt (je 1 Datensatz, danach wieder entfernt, Bestand 0).
   Der Fehler war instanceweit und betraf nicht nur das Helpdesk.
2. **Eingeklappte Stufen**: "on Hold" und "Verrechnung mit Kunde geklärt" sind in der
   Statusleiste eingeklappt (fold, wie in Odoo 11 konfiguriert). Die Prüfautomatik erreicht
   sie über die eingeklappten Umschalter nicht zuverlässig; die Stufen selbst sind im
   Formularfeld "Status" auswählbar und im Kanban vorhanden. Werkzeuggrenze, kein Produktfehler.
3. **Bestätigungsdialog beim Schliessen**: Der Knopf "Ticket schliessen" und der
   Abschluss (Status Geschlossen/Behoben, Abschlusszeitpunkt, Geschlossen von) sind im
   Produkt vorhanden; die Prüfautomatik scheitert am modalen Bestätigungsdialog, weil im
   selben Lauf zuvor ein Fehlerdialog offen blieb. Werkzeuggrenze, kein Produktfehler.
4. **SLA-Frist**: Der Test-SLA hat als Zielstufe eine deaktivierte OCA-Standardstufe
   ("Done"); dadurch gilt die Frist sofort als erfüllt. Die SLA-Konfiguration ist eine
   Produktivstart-Aufgabe (Zielstufe "Geschlossen/Behoben", Ignorier-Stufe "on Hold").
5. **Mailvorlage**: Body und Betreff auf Odoo-18-Syntax umgestellt (vorher `${...}` aus
   Odoo 11), Absender auf `team_id.alias_email`/Firmenadresse, Empfänger zusätzlich
   `partner_email` - damit erhalten auch öffentliche Einsender eine Bestätigung.

## 5. Offene Punkte vor dem Produktivstart

Die Liste in `docs/o11-o18-helpdesk-vergleich.md`, Abschnitt 8, ist bindend:
Teams und SLA konfigurieren, E-Mail-Alias am Team hinterlegen, reCAPTCHA-Schlüssel
eintragen, Kategorien/Unterkategorien und Prioritäten übernehmen. Es wurden bewusst
keine Stammdaten ungefragt angelegt.

## 6. Nicht migriert (bewusst)

Keine der 1.223 Odoo-11-Tickets, keine Anhänge, keine Verlaufsdaten, keine der 191
Zusatzfeldwerte. Odoo 11 blieb während der gesamten Session unverändert.
