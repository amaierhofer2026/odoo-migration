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
