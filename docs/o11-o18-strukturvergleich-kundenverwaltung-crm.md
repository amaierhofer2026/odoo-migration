# Struktur-/Funktionsvergleich Odoo 11 Kundenverwaltung -> Odoo 18 CRM

Stand: 17.09.2026 (Session 115)
Ergaenzt: `docs/o11-o18-strukturvergleich-crm-verkaufschancen.md` (Session 114: Stufen, Teams, Verlustgruende, Feld-Mapping der Verkaufschance)

Quellen:
- Odoo 11 Prod `https://portal.it-kommunal.at`, DB `ITK_V1_a` - ausschliesslich lesend (Referenzsystem)
- Odoo 18 lokal (`http://localhost:8069`) und VM `https://k001959vsx.ipax.at` (verbindliche Abnahmeumgebung)

Keine Datenmigration. Es wurden keine Interessenten und keine Verkaufschancen uebernommen.

Kontrollzahlen (gemessen):
```
crm.lead           Odoo 11 Prod   Odoo 18 lokal   Odoo 18 VM
Verkaufschancen        359              0               0
Interessenten        6.608              1               1     (1 Testdatensatz)
```

## 1. Modul- und Menueame

| | Odoo 11 Prod | Odoo 18 |
|---|---|---|
| Technischer Modulname | `crm` | `crm` (unveraendert, Standard) |
| Sichtbarer App-Name (Anzeige) | Kundenverwaltung | Kundenverwaltung (bis Session 114: "CRM") |
| Name im Quelltext (ohne Sprache) | CRM | CRM (unveraendert) |

Vorgehen: Der sichtbare Menueame wird in Odoo 18 auf "Kundenverwaltung" gesetzt, der technische
Modulname `crm` bleibt unveraendert. Genau dieses Muster verwendet auch Odoo 11 Prod: dort ist der
Quelltext "CRM", die deutsche Anzeige "Kundenverwaltung".

Umsetzung (itk_crm, `setup_runtime._setup_crm_menus`):
- Menue `crm.crm_menu_root` (Wurzelmenue der App).
- Ursache des Fehlers: Dieses Menue ist Moduldaten mit `noupdate=0`. Bei einem Upgrade des Moduls `crm`
  wird der Quelltext zurueckgesetzt, die alte deutsche Uebersetzung "CRM" bleibt in der Datenbank
  stehen - dann zeigt die Oberflaeche wieder "CRM".
- Fix: Quelle, `de_DE` und `en_US` werden gemeinsam geschrieben, und das Setup laeuft bei jedem
  itk_crm-Upgrade erneut (Migration 18.0.1.5.4). Damit bleibt "Kundenverwaltung" stabil.

## 2. Hauptmenues und Untermenues (Punkt 2)

Odoo 11 (read-only aufgenommen, Wurzel "Kundenverwaltung"):

```
Aktivitaeten            (seq 0)   mail.activity
Pipeline                (seq 1)
   Interessenten        (seq 1)   crm.lead
   Pipeline             (seq 5)   crm.lead (Kanban)
   Angebote             (seq 10)  sale.order
Kunden                  (seq 2)   res.partner
Berichtswesen           (seq 20)
   Interessenten        (seq 1)   crm.opportunity.report
   Pipeline             (seq 5)   crm.opportunity.report
   Aktivitaeten         (seq 6)   crm.activity.report
   Vertriebskanaele     (seq 10)  crm.team
Konfiguration           (seq 25)
   Einstellungen        (seq 0)   res.config.settings
   Vertriebskanaele     (seq 5)   crm.team
   Aktivitaetstypen     (seq 10)  mail.activity.type
   Interessenten und Chancen (seq 15)
      Lead Tags         (seq 1)   crm.lead.tag
      Ablehnungsgruende (seq 6)   crm.lost.reason
```

Odoo 18 (nach dem Setup, Status je Punkt):

```
Kundenverwaltung        (seq 0, Wurzel)                     OK  angepasst (vorher "CRM")
   Aktivitaeten         (seq 0)   mail.activity             OK  identisch
      Neue Aktivitaet   (seq 99)  mail.activity             neu in Odoo 18, bleibt
   Pipeline             (seq 1)                             OK  identisch (Quelltext war schon "Pipeline")
      Pipeline          (seq 1)   crm.lead Kanban           OK  identisch
      Interessenten     (seq 2)   crm.lead                  OK  identisch
      Angebote          (seq 3)   sale.order                OK  identisch
      Teams             (seq 4)   crm.team                  bewusst: Zusatzmenue von ITK, bleibt
   Kunden               (seq 5)   res.partner               OK  identisch (Odoo 11: seq 2, Reihenfolge gleich)
   Berichtswesen        (seq 20)                            OK
      Prognose          (seq 1)   crm.lead forecast         neu in Odoo 18, bleibt
      Pipeline          (seq 2)   crm.lead Analyse          OK  entspricht Odoo 11 "Pipeline"
      Leads             (seq 3)   crm.lead Analyse          OK  entspricht Odoo 11 "Interessenten"
      Aktivitaeten      (seq 4)   crm.activity.report       OK  identisch
   Konfiguration        (seq 25)                            OK
      Einstellungen     (seq 0)                             OK  identisch
      Vertriebskanaele  (seq 5)   crm.team                  OK  identisch (Odoo 18 sagte "Verkaufsteams")
      Aktivitaeten      (seq 8)                             neu in Odoo 18 (Gruppe), bleibt
         Aktivitaetstypen (seq 10) mail.activity.type        OK  identisch
         Aktivitaetsplaene (seq 11) mail.activity.plan      neu in Odoo 18, bleibt
      Wiederkehrende Plaene (seq 12)                        neu in Odoo 18, bleibt
      Interessenten und Chancen (seq 15)                    ANPASSUNG: Odoo 18 sagte "Pipeline"
         Stichwoerter   (seq 1)   crm.tag                   OK  entspricht Odoo 11 "Lead Tags"
         Verlustgruende (seq 6)   crm.lost.reason           OK  entspricht Odoo 11 "Ablehnungsgruende"
      Lead-Generierung  (seq 20)  crm_iap_mine              neu in Odoo 18, bleibt
```

Weggefallen gegenueber Odoo 11: das Berichtsmenue "Vertriebskanaele" (`crm.team` in der Berichtsgruppe).
Die Funktion ist in Odoo 18 ueber "Teams" (Pipeline-Gruppe) und "Vertriebskanaele" (Konfiguration)
erreichbar - Odoo-18-Standard, kein Nachbau.

Bewusst nicht nachgebaut: die Odoo-11-Berichte "Interessenten"/"Pipeline" auf dem eigenen Modell
`crm.opportunity.report`. Odoo 18 berichtet aus `crm.lead` (Filter, Gruppierung, Pivot) und liefert
zusaetzlich `Prognose`.

Zugriffsrechte der Menues:
```
Odoo 11 Wurzelmenue:  Gruppen 25 (Sales / Manager) und 23 (Sales / User: Own Documents Only)
Odoo 18 Wurzelmenue:  Gruppen 17 (Sales / Administrator) und 15 (Sales / User: Own Documents Only)
```
Gleichwertig, keine Anpassung noetig.

## 3. Ansichten (Punkt 3)

### Listenansichten (gemessen auf View-Ebene)

| | Odoo 11 Prod | Odoo 18 |
|---|---|---|
| Liste Interessenten | `crm.lead.tree.lead` | `crm.lead.list.lead` + `...inherit.itk` (unsere Erweiterung) |
| ITK-Felder dort | `x_lead_status`, `x_Lead_Quelle`, `x_Anrede_Lead`, `x_Produktinteresse` | dieselben vier (identisch) |
| Liste Verkaufschancen | `crm.lead.tree.opportunity` ohne ITK-Felder | `crm.lead.list.opportunity` ohne ITK-Felder (identisch) |
| Standardspalten | 19 Spalten in der Standardliste | mehr Spalten (u. a. Prioritaet, Aktivitaeten, Herkunft, Erwarteter Umsatz, wiederkehrende Umsaetze) |

Ergebnis: Die ITK-Felder stehen in Odoo 18 an derselben Stelle wie in Odoo 11 (Liste der Interessenten
und im Formular), nicht in der Liste der Verkaufschancen. Kein GAP, keine Anpassung.

### Formular

| | Odoo 11 Prod | Odoo 18 |
|---|---|---|
| Reiter | Interne Notizen, Weitere Informationen | Interne Notizen, Weitere Informationen, Zusaetzliche Informationen |
| Gruppen | E-Mail, Nachverfolgung, Analyse der Plandaten | Lead Classification, Marketing, Analyse, Kontaktinformationen, Marketing, Nachverfolgung |
| Felder im Formular | 40 | 67 |
| Buttons/Aktionen | 2 (davon 1 Server-Aktion) | 13 (u. a. Smart Buttons: Angebot, Verkauf, Termin planen, Wahrscheinlichkeit setzen, Duplikate, IAP-Anreicherung) |

Ergebnis: Das Odoo-18-Formular ist eine Obermenge. Alle 40 Odoo-11-Felder sind abbildbar (Feld-Mapping
siehe Dokument Session 114), zusaetzlich moderne Odoo-18-Elemente. Kein Rueckbau, kein GAP.

### Kanban

Odoo 11 und Odoo 18 fuehren die ITK-Felder nicht in der Kanban-Karte (identisch). Die Kanban-Karte
selbst ist in Odoo 18 moderner (Aktivitaetsanzeige, Stufenwechsel per Drag and Drop).

## 4. Suche, Filter, Gruppierung, Favoriten (Punkt 4)

Filter (gemessen, Odoo 11: 17 Filterknoten, Odoo 18: 28):

| Odoo 11 | Odoo 18 | Status |
|---|---|---|
| Meine Leads | Meine Pipeline | OK (gleiche Domain `user_id = uid`) |
| Nicht zugewiesen | Nicht zugewiesen | OK |
| Ungelesene Nachrichten | Ungelesene Nachrichten | OK |
| Meine/Verspaetete/Heutige/Anstehende Aktivitaeten | Verspaetete/Heutige/Anstehende Aktivitaeten | OK |
| Archiviert (`active = False`) | nicht als eigener Filter | Odoo 18 filtert ueber Gewonnen/Laufend/Verloren, Archiviertes ist erreichbar |
| Opt Out exkludieren (`opt_out = False`) | entfaellt | Odoo 18 hat kein `opt_out` mehr (Blacklist-Logik) |
| - | Offene Verkaufschancen, Gewonnen, Laufend, Verloren, Ueberfaellige, Erstellungsdatum, Abschlussdatum | neu in Odoo 18 |

Gruppierungen:

| Odoo 11 | Odoo 18 | Status |
|---|---|---|
| Verkaeufer (`user_id`) | Vertriebsmitarbeiter (`user_id`) | OK |
| Vertriebskanal (`team_id`) | Verkaufsteam (`team_id`) | OK |
| Kampagne, Medium, Referenz (`source_id`), Erstellungsmonat | Kampagne, Medium, Herkunft, Erstellungsdatum | OK |
| Kunde (`partner_id`) | fehlt (stattdessen Stadt, Land) | fehlt in Odoo 18 |
| - | Phase, Verlustgrund, Erwarteter Abschluss, Abschlussdatum, Umwandlungsdatum, Eigenschaften | neu in Odoo 18 |

Favoriten (`ir.filters` auf `crm.lead`, gespeicherte Suchen):
```
Odoo 11 Prod: 17 Favoriten (2 als Standard markiert, u. a. "Meine Leads")
Odoo 18:       0
```
Das sind Benutzerdaten (je Benutzer gespeicherte Suchen). Sie werden jetzt nicht uebernommen -
KLÄRUNG NOETIG (siehe unten).

Kleiner GAP: die Gruppierung "Kunde" (`partner_id`) fehlt in Odoo 18. Bewertung: fachlich schwach
relevant (Kontakte lassen sich ueber die Filialsuche finden), Odoo 18 gruppiert nach Stadt/Land. Als
optionaler Nachtrag notiert, kein Blocker. KLÄRUNG NOETIG, ob gewuenscht.

## 5. Konfiguration (Punkt 5)

| Odoo 11 | Odoo 18 | Status |
|---|---|---|
| Stufen (im Kanban bearbeitbar) | Phasen im Kanban bearbeitbar, 9 Stufen vorbereitet | OK (Session 114) |
| Vertriebskanaele (8 in Prod, davon 7 verwendet) | 7 Teams vorbereitet | OK (Session 114) |
| Ablehnungsgruende (5 Namen) | Verlustgruende (5 Namen vorhanden) | OK (Session 114) |
| Lead Tags (`crm.lead.tag`) | Stichwoerter (`crm.tag`) | OK, Modell umbenannt |
| Aktivitaetstypen | Aktivitaetstypen (+ Aktivitaetsplaene, Wiederkehrende Plaene) | OK, Odoo 18 umfangreicher |
| Einstellungen (Interessenten aktiv: `group_use_lead = True`) | Interessenten und Verkaufschancen aktiv | OK |

Zugriffsrechte auf `crm.lead`:
```
Odoo 11: crm.lead.manager (Sales / Manager), crm.lead (Sales / User: Own Documents Only),
         crm.lead.partner.manager (Extra Rights / Contact Creation),
         access_itk_crm_lead_manager (ITK-Gruppe "Manager (edit)", 13 Benutzer)
Odoo 18: crm.lead.manager (Sales / Administrator), crm.lead (Sales / User: Own Documents Only)
Datensatzregeln: Odoo 11 "Personal Leads" + "All Leads" / Odoo 18 dieselben + Multi-Company-Regel
```
Die ITK-eigene Zugriffsregel `access_itk_crm_lead_manager` (Schreibrechte fuer die ITK-Gruppe
"Manager (edit)", in Prod 13 aktive Benutzer) hat in Odoo 18 keine Entsprechung - KLÄRUNG NOETIG.

## 6. Funktionen (Punkt 6)

Fachlich geprueft (Odoo 18, lokal + VM):

| Funktion | Odoo 11 | Odoo 18 |
|---|---|---|
| Interessent anlegen/bearbeiten | ja | ja (Aktivitaeten-Menue, Interessenten) |
| Interessent in Verkaufschance umwandeln | ja (Button "In Chance umwandeln") | ja (Standard-Button) |
| Verkaufschance anlegen/bearbeiten | ja | ja |
| Stufe wechseln | ja (Kanban/Formular) | ja (Kanban/Formular, 9 Stufen) |
| gewonnen/verloren | ja | ja (Button "Gewonnen", Verlust-Dialog mit Grund) |
| Verlustgrund erfassen | ja | ja (`lost_reason_id`) |
| Aktivitaeten planen | ja | ja (+ Aktivitaetsplaene) |
| Verkaeufer/Team | ja | ja |
| erwarteter Umsatz | ja (`planned_revenue`) | ja (`expected_revenue`, umbenannt) |
| Wahrscheinlichkeit | ja (an der Stufe) | ja (am Datensatz, beschreibbar) |
| Abschlussdatum | ja | ja |
| Tags | ja | ja (Stichwoerter) |
| Chatter/Notizen | ja | ja (Anhaenge am Chatter) |
| Angebot erstellen (Smart Button) | ueber Verkaufsmenue | ja (Smart Button "Angebot"/"Verkauf") |

Kein funktionaler GAP festgestellt. Die Odoo-18-Bedienung ist moderner (Drag and Drop im Kanban,
aktivitaetsbasierte Ansichten, Prognose), die Funktionen sind vollstaendig vorhanden.

## 7. Angepasst in dieser Session

1. Sichtbarer App-Name "CRM" -> "Kundenverwaltung" (Menue `crm.crm_menu_root`, Quelle + de_DE + en_US).
2. Konfigurationsgruppe "Pipeline" -> "Interessenten und Chancen" (Menue `crm.menu_crm_config_lead`,
   Wortlaut aus Odoo 11; die Gruppe enthaelt Stichwoerter und Verlustgruende).
3. Robustheit: Beide Anpassungen laufen bei jedem itk_crm-Upgrade erneut (`setup_runtime.setup_all`,
   Migration 18.0.1.5.4), weil `crm.crm_menu_root` Moduldaten mit `noupdate=0` ist.
- `itk_crm` Version: 18.0.1.5.4

## 8. Bewusst Odoo-18-standardmaessig (kein Rueckbau)

- Klassifizierung, Prognose, Wiederkehrende Plaene, Aktivitaetsplaene, Lead-Generierung, Eigenschaften.
- Berichte aus `crm.lead` statt des Odoo-11-Modells `crm.opportunity.report`.
- Smart Buttons (Angebot, Verkauf, Termin, Duplikate, IAP).
- Umbenennungen: Stufe -> Phase, Verkaeufer -> Vertriebsmitarbeiter, Vertriebskanal -> Verkaufsteam,
  Lead Tags -> Stichwoerter, Ablehnungsgruende -> Verlustgruende. Auf Wunsch Umstellung auf die
  Odoo-11-Wortlaute moeglich (nur Beschriftungen, keine Struktur).

## 9. KLÄRUNG NOETIG

1. Favoriten: 17 gespeicherte Suchen aus Odoo 11 (2 Standard) - uebernehmen, neu aufbauen oder verwerfen?
   Betrifft Benutzerdaten, daher nicht automatisch.
2. Gruppierung "Kunde" (`partner_id`) in der Suche ergaenzen?
3. ITK-Zugriffsregel `access_itk_crm_lead_manager` (Gruppe "Manager (edit)", 13 aktive Benutzer in Prod):
   in Odoo 18 nachbilden (eigene Gruppe + Regel) oder ueber die Odoo-18-Rollen abbilden?
4. Odoo-11-Berichtsmenue "Vertriebskanaele" (`crm.team` in der Berichtsgruppe): nachbauen oder
   Odoo-18-Standard belassen?
5. Wortlaute (siehe Abschnitt 8): Odoo-11-Begriffe wiederherstellen oder Odoo-18-Begriffe behalten?
6. Datenmigration Interessenten/Verkaufschancen: Auswahlregel und Zeitpunkt (nicht Teil dieser Session).

## 10. Nachtrag Session 115: Wortlaute, Gruppierung Kunde, Berichtsmenue, Berechtigungen

### 10.1 Sichtbare Wortlaute auf Odoo 11 umgestellt (itk_crm 18.0.1.5.5)

Quelle: Odoo 11 Prod, `fields_get(lang=de_DE)` und die Konfigurationsmenues (read-only).

```
Feld/Bereich            Odoo 11 sichtbar          Odoo 18 vorher            Odoo 18 jetzt
crm.lead.stage_id       Stufe                     Phase                     Stufe
crm.lead.user_id        Verkaeufer                Vertriebsmitarbeiter      Verkaeufer
crm.lead.team_id        Vertriebskanal            Verkaufsteam              Vertriebskanal
crm.lead.tag_ids        Stichwoerter              Stichwoerter              unveraendert
crm.lead.lost_reason_id Ablehnugsgrund (Odoo-11-  Verlustgrund              Ablehnungsgrund
                        Schreibfehler in Prod)
crm.lead.date_deadline  Erwartetes Abschlussdatum Erwarteter Abschluss      Erwartetes Abschlussdatum
Menue Konfiguration     Lead Tags                 Stichwoerter              Lead Tags
Menue Konfiguration     Ablehnungsgruende         Verlustgruende            Ablehnungsgruende
Aktion (Stufenliste)    (Odoo 11 ohne Menue)      Phasen                    Stufen
```

Umsetzung: `setup_runtime._setup_crm_labels` (Feldbeschreibungen in de_DE, Menue- und Aktionsnamen)
sowie `data/crm_bezeichnungen_views.xml` (Suchfilter in beiden Suchansichten). Technische Modell- und
Feldnamen bleiben unveraendert. Beide Stellen laufen bei jedem itk_crm-Upgrade erneut, damit die
Odoo-Basismodule die deutschen Texte nicht wieder zuruecksetzen.

### 10.2 Gruppierung "Kunde" ergaenzt

Odoo 11 bietet unter "Gruppieren nach" die Gruppierung "Kunde" (`partner_id`). In Odoo 18 fehlte sie.
Ergaenzt in beiden Suchansichten (`crm.view_crm_case_opportunities_filter`, `crm.view_crm_case_leads_filter`)
als Filter `groupby_partner` mit `context={'group_by': 'partner_id'}`. Reine Suchansicht, keine Datenänderung.

### 10.3 Berichtsmenue "Vertriebskanaele"

In Odoo 11 hing unter Kundenverwaltung/Berichtswesen der Menuepunkt "Vertriebskänale" (Aktion "Sales Channels",
Modell `crm.team`, Ansicht kanban,form). Das war kein Auswertungsbericht, sondern die Team-Kanbanansicht.
Dieselbe Ansicht existiert in Odoo 18 (`sales_team.crm_team_action_pipeline`, "Teams", kanban,form).
Umsetzung: Menuepunkt "Vertriebskanäle" unter Berichtswesen (Sequenz 10, wie Odoo 11) auf die vorhandene
Odoo-18-Aktion. Kein eigener Bericht, kein historisches Modell nachgebaut.

### 10.4 Zugriffsregel "Manager (edit)" (Odoo 11, Gruppe id 75) - Analyse und Mapping

Odoo 11 (read-only): Die Gruppe "Manager (edit)" hat 24 Zugriffsregeln, ausschliesslich auf ITK-eigene
Stammdatenmodelle (Status of Community, Community Magnitude, Community Code, Title put in Front/Back,
Valorisierung, Product-Type, Product Template, Product, Project Category, Status of Partner), zusaetzlich
auf Lead/Opportunity (`access_itk_crm_lead_manager`) und Contact. Sie impliziert eine weitere ITK-Gruppe,
hat keine Datensatzregeln und keine Menues. 13 aktive Benutzer.

Mapping auf Odoo 18 (kein Nachbau der Altgruppe):

```
Odoo 11 Regel                         Odoo 18 Entsprechung                          Status
Lead/Opportunity R/W/C/D              Sales / Administrator (crm.lead.manager)      vorhanden (inkl. Loeschen)
Contact R/W/C/D                       Sales / Administrator + Kontakt-Rechte        vorhanden
ITK-Stammdaten (Gemeinde, Produkt)    Standard-Schreibrechte der jeweiligen Module  vorhanden
```

Bewertung: Fuer die ITK-Stammdaten deckt Odoo 18 die Rechte ueber die jeweiligen Modulgruppen ab. Ein
fachlich relevanter Unterschied bleibt beim Loeschrecht auf `crm.lead`: In Odoo 11 hatten die 13 Benutzer
dieses Recht, in Odoo 18 hat es nur Sales/Administrator. Das ist eine Rollenzuordnung und damit eine
Datenentscheidung -> KLAERUNG NOETIG (siehe 10.6). Es wurde keine Altgruppe nachgebaut.

### 10.5 Favoriten (gespeicherte Suchen) in Odoo 11 - Analyse

(keine Uebernahme, wie von Anna vorgegeben)

```
Favorit                       Benutzer              Standard  Inhalt
Aussendung Communex 11.05.26  Blagojevic Dejvid     nein      Namenssuche nach 'verband' (partner_name/email/name)
Aussendung Hinweis 230307     ALLE (geteilt)        nein      x_Lead_Quelle = mail_hinweis_1
Event/Webinar angemeldet      ALLE (geteilt)        nein      x_lead_status = event_angemeldet
Gerd Webinar 30.01.24         Soritz Gerd           ja        Namenssuche 'Webinar 240130' bzw. 'webinar'
IFG Webinar 3                 Czarnecki Clemens     nein      x_Lead_Quelle = 3 IFG-Webinar-Werte
IFG Webinar 4                 Czarnecki Clemens     nein      x_Lead_Quelle = 4 IFG-Webinar-Werte
Interessenten                 Soritz Gerd           nein      x_Produktinteresse = hinweisgeber
Kontaktierte Leads            Sallmann Ronald       nein      x_lead_status = kontaktiert, gruppiert nach Verkaeufer
Lead Angelegt                 Czarnecki Clemens     nein      user_id = Czarnecki, x_lead_status = angelegt
Lead kontaktiert              Czarnecki Clemens     nein      user_id = Czarnecki, x_lead_status = kontaktiert
Leads 230411                  Czarnecki Clemens     nein      user_id = Czarnecki, x_Lead_Quelle = web_hinweis_in_230411
Leads verloren                Czarnecki Clemens     nein      user_id = Czarnecki, x_lead_status = leadverloren
Meine Leads                   Czarnecki Clemens     ja        user_id = 63 (fest auf diesen Benutzer)
Nicht Lead angelegt           Czarnecki Clemens     nein      user_id = Czarnecki, x_lead_status != angelegt
Offene Leads                  Czarnecki Clemens     nein      user_id = Czarnecki, x_lead_status != leadverloren
Online Formulare              Czarnecki Clemens     nein      user_id = Czarnecki, x_Produktinteresse = formulare
Webinar 240130                Czarnecki Clemens     nein      Namenssuche 'webinar'
```

Bewertung: 2 der 17 sind benutzeruebergreifend geteilt, 15 gehoeren einzelnen Benutzern. Die beiden als
Standard markierten Favoriten sind benutzerindividuell (Soritz, Czarnecki) und auf feste Benutzer-IDs
gebunden - es gibt keinen systemweit wichtigen Standardfilter. Odoo 18 hat die Standardfilter
"Meine Pipeline" / "Meine Leads" (dynamisch auf den angemeldeten Benutzer) sowie Filter je Stufe. Ein
kuenstlicher Vorab-Nachbau ist daher nicht erforderlich. Wer die beiden geteilten Favoriten
("Aussendung Hinweis 230307", "Event/Webinar angemeldet") wieder haben moechte, kann sie in Odoo 18 als
geteilte Favoriten neu anlegen - Entscheidung bei Anna (10.6).

### 10.6 Offene Entscheidungen nach dem Nachtrag

1. Loeschrecht auf `crm.lead` fuer die 13 Benutzer der Odoo-11-Gruppe "Manager (edit)": in Odoo 18 ueber
   Sales/Administrator abbilden oder Rollen anders vergeben?
2. Die zwei geteilten Favoriten neu anlegen?
3. Filterbezeichnungen des Odoo-18-Standards ("Meine Pipeline", "Offene Verkaufschancen",
   "Ueberfaellige Verkaufschancen") auf Odoo-11-Wortlaute umstellen? Odoo 11 hatte "Meine Leads" - der
   Filterknoten wird in Odoo 18 von Pipeline und Interessenten gemeinsam verwendet.
4. Datenmigration (Auswahlregel, Zeitpunkt) - weiterhin gestoppt.

### 10.7 Browser-Nachweis (Session 115)

```
Instanz   Werkzeug                                  Ergebnis
lokal     scripts/browser_kundenverwaltung_pruef.py 27 OK / 0 FEHL   (itk_crm 18.0.1.5.5)
VM        scripts/browser_kundenverwaltung_pruef.py 22 OK / 5 FEHL   (itk_crm 18.0.1.5.4)
lokal     scripts/verify_s115_kundenverwaltung.py   32 OK / 0 FEHL
```

Auf der VM sind die 5 Abweichungen ausschliesslich die neuen Wortlaute: sie erscheinen erst nach dem
naechsten VM-Deploy von 18.0.1.5.5. Geprueft und auf der VM bereits bestaetigt: App-Name
"Kundenverwaltung", Menueband (Aktivitaeten, Pipeline, Kunden, Berichtswesen, Konfiguration), Pipeline mit
allen 9 Stufen, Interessenten-Liste mit den ITK-Spalten, Formular, Stufenliste (9 von 9),
Vertriebskanaele (7 Teams), Berichtswesen/Vertriebskanaele (Team-Karten).
Screenshots: `31_..38_<INSTANZ>_*.png` im Desktop-Ordner Odoo18-Layoutvergleich-Session95.

## 11. Entscheidungen von Anna (17.09.2026) und Umsetzung

### 11.1 Favoriten
Die 17 gespeicherten Suchen aus Odoo 11 werden **bewusst nicht uebernommen**. Sie wirken wie konkrete
historische Arbeitsfilter und gehoeren nicht zur Grundfunktion der Kundenverwaltung; 15 von 17 waren
ohnehin benutzerspezifisch. Benutzer koennen in Odoo 18 jederzeit neue Favoriten anlegen. Dokumentiert,
keine Aktion noetig.

### 11.2 Berechtigungen: Loeschrecht auf crm.lead
Vorgabe: die 13 Benutzer **nicht** pauschal zu Sales/Administrator machen; die alte Funktion ueber eine
gezielte Gruppe abbilden.

Befund: die Odoo-11-Gruppen "User (read only)" und "Manager (edit)" existieren in Odoo 18 bereits als
ITK-Gruppen (`itk_crm.itk_group_user`, `itk_crm.itk_group_manager`, Kategorie ITK) - sie sind also kein
Nachbau, sondern die Fortfuehrung. Es fehlte genau ein Recht: das Loeschen von `crm.lead`.

Umsetzung (itk_crm ab 18.0.1.5.6, `security/ir.model.access.csv`):

```
access_itk_crm_lead_manager  ->  crm.model_crm_lead  ->  itk_crm.itk_group_manager
                             perm_read=0 perm_write=0 perm_create=0 perm_unlink=1
```

Damit erhalten Mitglieder der ITK-Gruppe "Manager (edit)" **nur** das Loeschrecht auf Interessenten/
Verkaufschancen. Lesen, Schreiben und Anlegen kommen weiterhin ausschliesslich ueber die normalen
Verkaufsrollen (Sales/User) - keine vollstaendigen Administratorrechte.

Berechtigungs-Mapping (Odoo 11 -> Odoo 18):

```
Odoo 11                                    Odoo 18                                            Status
Gruppe User (read only) (id 74)            itk_crm.itk_group_user                             vorhanden
Gruppe Manager (edit) (id 75)              itk_crm.itk_group_manager                          vorhanden
access_itk_crm_lead_manager (R/W/C/D)      R/W/C ueber Sales-Rollen + D ueber ITK-Regel        ergaenzt (nur D)
access_itk_crm_respartner_manager (R/W/C/D) base.group_partner_manager / Kontakt-Rechte        vorhanden (Standard)
ITK-Stammdaten (Gemeinde, Produkt ...)     Schreibrechte der jeweiligen ITK-/Odoo-Module        vorhanden
```

Benutzerzuordnung: **nicht** vorgenommen. Mitglied der Gruppe ist derzeit nur der Administrator
(so wie das Modul es anlegt). Die 13 Odoo-11-Benutzer werden erst bei der Benutzerbereinigung/-migration
zugeordnet.

### 11.3 Filterbezeichnungen
Die Odoo-18-Standardfilter bleiben unveraendert. Insbesondere "Meine Pipeline" wird behalten, weil der
Filterknoten technisch von Interessenten und Verkaufschancen gemeinsam verwendet wird - eine Umbenennung
in "Meine Leads" waere irrefuehrend. Die fachlich notwendigen Filtermoeglichkeiten aus Odoo 11 sind
vorhanden (siehe Abschnitt 4); fehlende Funktionen wurden ergaenzt (Gruppierung "Kunde").

Wortlaut-Abweichungen, die bewusst bleiben (Dokumentation):

```
Odoo 11                     Odoo 18                     Bewertung
Meine Leads                 Meine Pipeline              technisch gemeinsam genutzt, Odoo-18-Wortlaut bleibt
-                           Offene Verkaufschancen      neu in Odoo 18, sinnvoll
-                           Ueberfaellige Verkaufsch.   neu in Odoo 18, sinnvoll
Archiviert (active=False)   ueber Gewonnen/Verloren     Funktion vorhanden
Opt Out exkludieren         entfaellt (kein opt_out)    Odoo 18 nutzt Blacklist-Logik
```

### 11.4 Datenmigration
Weiterhin vollstaendig gestoppt: keine Interessenten, keine Verkaufschancen, keine Favoriten, keine
Benutzerzuordnungen. Odoo 11 Prod wurde ausschliesslich lesend verwendet.

## 12. Browser-Abnahme auf der VM (17.09.2026)

```
Werkzeug: scripts/browser_kundenverwaltung_pruef.py --instanz vm       31 OK / 0 FEHL
Werkzeug: scripts/browser_kundenverwaltung_pruef.py --instanz lokal    28 OK / 0 FEHL
Werkzeug: scripts/verify_s115_kundenverwaltung.py --instanz lokal      35 OK / 0 FEHL
Werkzeug: scripts/verify_s114_crm_chancen.py --instanz vm              52 OK / 0 FEHL
```

Auf der VM im echten Browser bestaetigt:

```
sichtbarer App-Name Kundenverwaltung                 ja (Menueband)
Hauptmenues Aktivitaeten/Pipeline/Kunden/Berichtswesen/Konfiguration   ja
Pipeline mit allen 9 Stufen                          ja (Kanban-Spalten)
Interessenten (Liste mit ITK-Spalten)                ja
Angebote                                             ja
Kunden                                               ja (76 Karten)
Berichtswesen inkl. Vertriebskanaele                 ja (13 Team-Karten)
Konfiguration: Stufen 9/9, Vertriebskanaele 7        ja
Konfiguration: Ablehnungsgruende 5, Lead Tags 10     ja
Suche/Filter/Gruppieren inkl. Kunde                  ja (Verkaeufer, Vertriebskanal, Kunde, Stufe, Ablehnungsgrund)
Formular mit Reitern und Beschriftungen              ja (Verkaeufer, Vertriebskanal, Stichwoerter, Statusleiste)
```

Screenshots 31 bis 42 als `..._VM_*.png` im Ordner Odoo18-Layoutvergleich-Session95 (Desktop).
Beim Browser-Test wurden keine Datensaetze angelegt, geaendert oder geloescht.