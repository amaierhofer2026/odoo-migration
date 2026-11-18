# CRM / Verkaufschancen: Vergleich Odoo 11 gegen Odoo 18

Stand: 17.11.2026 (Session 145). Quelle Odoo 11 Produktion `ITK_V1_a`,
**ausschliesslich lesend** erhoben (RPC, `active_test=False`). Ziel: Odoo 18
(lokal und VM). Zahlen sind an diesem Tag frisch gemessen, nicht aus frueheren
Sitzungen uebernommen.

## 1 Ausgangszahlen Odoo 11 (17.11.2026)

| Objekt | Anzahl | Anmerkung |
|---|---|---|
| Interessenten und Verkaufschancen (`crm.lead`) | 6.994 | 6.973 aktiv, 21 archiviert |
| davon Interessenten (`type=lead`) | 6.609 | |
| davon Verkaufschancen (`type=opportunity`) | 385 | |
| Stufen (`crm.stage`) | 9 | alle offen (fold=False) |
| Vertriebskanaele (`crm.team`) | 8 | |
| Stichwoerter (`crm.lead.tag`) | 44 | 6.161 Vorgaenge mit Stichwort, 6.327 Zuordnungen |
| Ablehnungsgruende (`crm.lost.reason`) | 5 | 13 Vorgaenge mit Grund |
| Aktivitaetstypen (`mail.activity.type`) | 12 | 5 davon ITK-eigen |
| offene Aktivitaeten auf Vorgaengen (`mail.activity`) | 32 | |
| Lead-Quellen (`utm.source`) | 220 | **kein** Vorgang referenziert sie |
| Kampagnen (`utm.campaign`) | 16 | **kein** Vorgang referenziert sie |
| Medien (`utm.medium`) | 9 | 25 Vorgaenge nutzen "Website" |
| Chatter-Nachrichten (`mail.message`) | 3.479 | auf 964 Vorgaengen |
| Anhaenge (`ir.attachment`) | 204 | 71 MB |
| Favoriten (`ir.filters`) | 17 | |

Verteilung nach Stufe: Neu 6.622, Verrechnet 209, Verloren 138, Angebotsphase 9,
On-Hold 5, Zur Verrechnung bereit 5, ohne Stufe 3, Erfolgreich 2,
Angebot ausgesendet 1.

Verteilung nach Vertriebskanal: Persoenlicher Kontakt 5.626,
Vertriebskanaele (Intern) 643, Suche / Liste 633, Interne Weitergabe 76,
Newsletter 9, Webinar 4, Webseite 2, Telefon 1.

Erwarteter Umsatz gesamt: 1.195.320,35 EUR auf 327 Vorgaengen.

## 2 Statuslogik - der wichtigste Unterschied

Odoo 11 kennt kein `is_won`. "Gewonnen" wird ueber die **Wahrscheinlichkeit 100**
gemessen (Filter `Erfolgreich` = `stage_id.probability = 100`), "Verloren" ueber
`active = False` (Filter `Verloren` = `active = False`).

Gemessene Wahrheit in Odoo 11:

| Groesse | Anzahl |
|---|---|
| Wahrscheinlichkeit 100 (= gewonnen) | 195 |
| davon in Stufe "Verrechnet" | 192 |
| davon in "Zur Verrechnung bereit" | 2 |
| davon in "Erfolgreich" | 1 |
| Wahrscheinlichkeit 0 | 154 (134 aktiv in Stufe "Verloren", 20 archiviert) |
| archiviert | 21 |

Odoo 18 entscheidet ueber `crm.stage.is_won`. Damit "Gewonnen" dieselbe Bedeutung
behaelt, sind in Odoo 18 **"Erfolgreich" und "Verrechnet"** als gewonnen markiert
(Entscheidung Session 145). Sichtbare Folge: Odoo 18 zaehlt 211 gewonnene
Vorgaenge gegen 195 in Odoo 11. Die 17 Differenz sind Vorgaenge in der Stufe
"Verrechnet", die in Odoo 11 eine andere Wahrscheinlichkeit als 100 tragen
(Dateninkonsistenz der Quelle, nicht der Migration).

Alle neun Stufen sind in Odoo 18 offen (fold=False) - wie in Odoo 11.

## 3 Was in Odoo 18 angepasst wurde (itk_crm 18.0.1.6.1)

| Befund | Massnahme |
|---|---|
| Vertriebskanal "Suche / Liste" fehlte (633 Interessenten) | Team angelegt (Session 114 hatte nur Verkaufschancen gezaehlt: dort 0) |
| Odoo-18-Team heisst "Website", Odoo 11 "Webseite" | umbenannt auf "Webseite" |
| `use_leads` war bei 7 Kanaelen False | wie Odoo 11 auf True gesetzt (ausser "Webseite") |
| Stufe "Verrechnet" war nicht gewonnen und zugeklappt | `is_won=True`, `fold=False` |
| Stufe "Verloren" war zugeklappt | `fold=False` (Odoo 11 zeigt alle Spalten) |
| Ablehnungsgrund "Im Moment keinen Bedarf" nur im en_US-Slot | Name in Quelle, de_DE und en_US; alle fuenf Gruende mit deutschem Wortlaut |
| Fuenf ITK-Aktivitaetstypen fehlten (u. a. "zu Verloren") | angelegt: Support, Formularerstellung, Amtssignatur Verlaengerung, Bereinigungsroutine, zu Verloren |
| Auswahlfelder `x_Lead_Quelle`, `x_Produktinteresse`, `x_lead_status` hatten den Anzeigetext als Schluessel und nur 11 statt 24 Lead-Quellen | technische Schluessel aus Odoo 11 wiederhergestellt (24/10/12 Werte), Anzeige unveraendert |
| Menue "Berichtswesen/Leads" | heisst wieder "Interessenten" (Odoo-11-Wortlaut) |
| `itk_o11_id` fehlte auf den CRM-Modellen | Modul `itk_migration_keys` 18.0.1.1.0 um crm.lead, crm.stage, crm.team, crm.tag, crm.lost.reason, utm.*, mail.activity.type erweitert |

Menuebaum: Odoo 11 fuehrt unter "Kundenverwaltung" 19 Menuepunkte (Aktivitaeten,
Pipeline mit Pipeline/Interessenten/Angebote, Kunden, Berichtswesen mit
Interessenten/Pipeline/Aktivitaeten/Vertriebskaenale, Konfiguration mit
Einstellungen/Vertriebskaenale/Aktivitaetstypen/Interessenten und Chancen mit
Lead Tags und Ablehnungsgruende). Odoo 18 hat dieselben Eintraege und zusaetzlich
reine Odoo-18-Funktionen (Teams im Pipeline-Menue, Prognose, Lead-Generierung,
Wiederkehrende Plaene, Aktivitaetsplaene). Die Zusatzfunktionen bleiben erhalten,
weil sie die Odoo-11-Funktionen nicht ersetzen oder blockieren.

## 4 Bewusst akzeptierte Abweichungen

| Punkt | Begruendung |
|---|---|
| Won-Zaehlung 211 gegen 195 | Odoo 18 entscheidet je Stufe; die 17 Vorgaenge in "Verrechnet" mit abweichender Wahrscheinlichkeit sind Quellinkonsistenz |
| Reine Systemnachrichten im Chatter nicht uebertragen (2.158 von 3.479) | ohne Text (Stufenwechsel, "Interessent wurde erstellt", "Chance gewonnen"); die 1.321 fachlichen Nachrichten sind uebertragen |
| 3 Vorgaenge ohne Stufe stehen in Odoo 18 auf "Neu" | Odoo 11 hatte keine Stufe gespeichert, Odoo 18 verlangt eine; bewusste technische Mappingregel |
| `utm.source` (220) und `utm.campaign` (16) nicht migriert | Belegt: 0 von 6.994 Vorgaengen nutzen eine Quelle oder Kampagne. Das einzige genutzte Medium "Website" (25 Vorgaenge) ist migriert. |
| `kanban_state`, `opt_out`, `day_open`, `day_close` nicht uebernommen | In Odoo 18 nicht vorhanden bzw. berechnet (`kanban_state` entfaellt, `day_open`/`day_close` werden berechnet) |
| Automatische Aktionen: eine Automation "Interessent zur Verrechnung bereit" existiert in Odoo 18 als Nachricht (kein E-Mail-Versand) | Odoo 11 verschickte drei E-Mail-Aktionen. Kein Mailversand aus dem Testsystem; nachbaubar, wenn der Mailserver steht. |
| Favoriten (17) nicht uebernommen | Entscheidung Session 115: benutzerspezifische Filter, kein systemweiter Standard |
| Vorgaenge ohne Verkaeufer: 27 | genau die 27 Vorgaenge, die schon in Odoo 11 keinen Verkaeufer hatten - keine Verluste |

## 4a Verkaeuferzuordnung - verbindliche Regeln (Freigabe Anna Maierhofer)

Alle 13 in Odoo 11 verwendeten Verkaeufer sind zugeordnet, **0 offen**.
Zuordnung ausschliesslich ueber Login, Anzeigename oder ausdrueckliche Regel -
nie ueber Datenbank-IDs.

| Odoo-11-Benutzer | Vorgaenge | Weg | Ziel in Odoo 18 |
|---|---|---|---|
| Benutzer 15 | 5.625 | Login | Benutzer 8 |
| Benutzer 63 | 956 | Login | Benutzer 53 (inaktiv) |
| Benutzer 20 | 137 | **explizite Regel** | Benutzer 15 (Login im Ziel abweichend) |
| Benutzer 17 | 136 | Login | Benutzer 22 |
| Benutzer 46 | 29 | Login | Benutzer 14 |
| Benutzer 71 | 24 | Login | Benutzer 23 |
| Benutzer 78 | 19 | Login | Benutzer 18 |
| Benutzer 19 | 14 | Login | Benutzer 50 (inaktiv) |
| Benutzer 89 | 10 | Login | Benutzer 13 |
| Benutzer 87 (Maierhofer Anna) | 8 | **explizite Regel** | **Administrator** (bestehendes Konto) |
| Benutzer 10 | 4 | Login | Benutzer 24 |
| Benutzer 18 | 4 | Login | Benutzer 20 |
| Benutzer 80 (Sammelkonto) | 1 | **historischer Benutzer** | neu angelegt, inaktiv |

(Die vollstaendige Tabelle mit Klarnamen liegt ausserhalb des Repositories im
Sitzungsprotokoll; im Repository stehen nur technische IDs.)

Zwei Regeln sind ausdruecklich hinterlegt und im Skript als `BENUTZER_MAPPING`
bzw. `HISTORISCHE_BENUTZER` dokumentiert:

1. **Maierhofer Anna -> Administrator.** Der Odoo-11-Benutzer "Maierhofer Anna"
   ist dieselbe reale Benutzerin wie das bestehende Odoo-18-Konto "Administrator"
   (Login anna.maierhofer@it-kommunal.at). In Odoo 18 existiert zusaetzlich ein
   Konto "Maierhofer Anna" (Login Anna.maierhofer@...); dieses ist **nicht** das
   Ziel. Das Administrator-Konto bleibt unveraendert: kein neues Konto, keine
   Umbenennung, keine Rechteaenderung. Ohne diese Regel haette der doppelte Login
   die 8 Vorgaenge zufaellig dem falschen Konto zugeordnet.
2. **Breiteneder Lorenz.** Fuehrt in Odoo 11 den veralteten Login
   lorenz.galler@it-kommunal.at, heisst in Odoo 18 lorenz.breiteneder@....
   137 Vorgaenge.
3. **ACO-Market** (Sammelkonto, keine Person) existiert in Odoo 18 nicht. Es wurde
   als minimale historische Benutzerstruktur angelegt und sofort inaktiv gesetzt
   (Login aco-market@it-kommunal.at), damit der eine Vorgang seine Zuordnung behaelt.

27 Vorgaenge hatten bereits in Odoo 11 keinen Verkaeufer; sie bleiben ohne -
das ist keine Migrationseinbusse.

## 4b Chatter: Klassifikation und Umfang

| Klasse | Anzahl | Uebertragen |
|---|---|---|
| Reine Systemmeldung ohne Text (Stufenwechsel, "Interessent wurde erstellt", "Chance gewonnen") | 2.158 | nein |
| Fachliche Nachrichten mit Text (Notizen, E-Mails, Aktivitaetsnotizen) | 1.321 | **ja, vollstaendig** |
| Gesamt | 3.479 | |

Die 1.321 fachlichen Nachrichten sind mit Text, Autor, Datum, Typ und Subtyp
uebertragen; 150 davon tragen Anhaenge. Technisch nicht uebertragbar war keine.

## 4c Anhaenge: Analyse und Umfang

| Merkmal | Wert |
|---|---|
| Anzahl | 204 (alle einem Vorgang zugeordnet, keiner ohne Bezug) |
| Gesamtgroesse | 67,9 MB (groesste Datei 2,5 MB, keine Datei ueber 5 MB) |
| Dateitypen | 171 PDF, 17 Text, 12 DOCX, 1 DOC, 1 PPTX, 2 E-Mail (RFC822) |
| Bewertung | fachliche Dokumente (Angebote, Formulare, Korrespondenz), keine technischen Systemanhaenge |
| Uebertragen | **204 von 204**, gleiche Groesse |

## 5 Zuordnung (kein ID-Matching)

- **Kontakte**: ueber `res.partner.itk_o11_id` (aus der Kontaktmigration). 275 von
  275 referenzierten Kontakten vorhanden.
- **Verkaeufer**: ueber Login, sonst ueber den Namen. Wichtig: Odoo-11-Benutzer 20
  hat den veralteten Login `lorenz.galler@...`, heisst aber "Breiteneder Lorenz" und
  ist in Odoo 18 als `lorenz.breiteneder@...` (id 15) vorhanden. Eine reine
  Login-Zuordnung haette 137 Vorgaenge ohne Verkaeufer gelassen.
- **Stufen, Teams, Ablehnungsgruende, Stichwoerter, Medien, Aktivitaetstypen**: ueber
  den Namen, nie ueber die Datenbank-ID. Gleichnamige Ziele gelten als Konflikt und
  werden nicht automatisch zugeordnet.
- **Bundeslaender**: ueber den Namen innerhalb Oesterreich (die IDs unterscheiden
  sich zwischen Odoo 11 und Odoo 18).
- **Laender**: ueber den ISO-Code.
- **Anreden**: ueber den Namen des `res.partner.title`.
- **Verkaufsmedien**: ueber den Namen; "Website" (25 Vorgaenge) ist migriert.
  Quellen und Kampagnen sind nachweislich unbenutzt (0 Vorgaenge) und bleiben
  deshalb in Odoo 11. Die ITK-Auswahlfelder `x_Lead_Quelle`, `x_Produktinteresse`
  und `x_lead_status` tragen die eigentliche Kanalinformation und sind vollstaendig
  migriert (24 / 10 / 12 Auswahlwerte, alle Werte erhalten).

## 7a Regression der gesperrten Bereiche (lokal, 18.11.2026)

Werkzeug: `scripts/regression_gesperrte_bereiche.py --instanz lokal`
Gesamtergebnis: **725 OK / 9 FEHL** ueber elf Bereiche. Kein Fehlschlag ist ein
Produktfehler; alle neun sind Werkzeuggrenzen und unten einzeln belegt.

| Bereich | Ergebnis |
|---|---|
| Kontakte/Kundenverwaltung | 32 OK / 4 FEHL |
| Verkauf | 239 OK / 4 FEHL |
| Helpdesk | 58 OK / 1 FEHL |
| Abonnements, Projekt, Personal, Zeiterfassung, Anwesenheiten/Urlaub, Events, E-Mail-Marketing, Massenbearbeitung | bestanden (0 FEHL) |

**Kontakte (4).** Das Pruefskript oeffnet den ersten `crm.lead` und sucht dort die
Beschriftungen des Interessentenformulars. Der erste Datensatz ist nach der Migration
eine Verkaufschance; dort heisst die Zusatzseite "Zusaetzliche Informationen" und der
Vertriebskanal liegt auf dieser Seite. Browserbeleg (`formular_lokal_interessent.png`,
`formular_lokal_verkaufschance.png`): im Interessentenformular sind "Vertriebskanal",
"Weitere Informationen", "Stichwoerter", "Verkäufer", "Produktinteresse", "Lead Status"
und "Lead Quelle" sichtbar; in der Verkaufschance sind dieselben Felder sichtbar,
"Vertriebskanal" auf dem Reiter "Zusaetzliche Informationen" (Odoo-18-Standard).
"Bundesland" ist in beiden Formularen der Platzhalter des Feldes `state_id` - genau wie
in Odoo 11, wo es ebenfalls nur `placeholder="Bundesland"` war. Der Suchtext "Bundesland"
erscheint daher nur, solange kein Wert gewaehlt ist; das Feld selbst ist vorhanden.

**Verkauf (4).** `browser_verkauf_kalender.py` vergleicht die im Kalender sichtbaren
Auftraege mit denen des angezeigten Monats. Die Monatsansicht zeigt die Randwoche mit
(26.-31.10.2026 in der ersten Novemberwoche), deshalb erscheinen dort Auftraege mit
Oktober-Auftragsdatum (A-2600339 bis A-2600341, alle 27.10.2026). Das ist die
Kalenderdarstellung, nicht ein falsches Datum. `browser_verkauf_bericht_kanaele.py`
entnimmt dem Pivot den groessten Zahlenwert (`max(werte)`) statt der Summe; der Pivot
selbst zeigt die richtige Gesamtsumme 356.617,85 EUR (Sollwert nicht storniert).
Beides Werkzeugfehler.

**Helpdesk (1).** Statuswechsel auf "on Hold" scheitert an der eingeklappten Stufe
(`fold`, wie in Odoo 11 konfiguriert). Bereits bei der Helpdesk-Abnahme als
Werkzeuggrenze dokumentiert (`docs/o11-o18-helpdesk-abnahme.md`, Punkt 2); die Stufe ist
im Formularfeld "Status" waehlbar.

**Bewusste Strukturabweichung.** In Odoo 11 stand der Vertriebskanal bei
Verkaufschancen im Hauptbereich (Gruppe "Diverse"), in Odoo 18 steht er auf der Seite
"Zusaetzliche Informationen". Die Funktion ist vorhanden und nutzbar; die Odoo-18-Ansicht
wird nicht ueberschrieben.

**Endstand nach dem letzten Modul-Upgrade (sequenziell, ohne Parallelbetrieb):**

| Instanz | Regression | Browser | Rechte |
|---|---|---|---|
| lokal | 725 OK / 9 FEHL | 55 OK / 0 FEHL | 22 OK / 0 FEHL |
| VM | 724 OK / 10 FEHL | 55 OK / 0 FEHL | 22 OK / 0 FEHL |

Die VM hat einen Fehlschlag mehr: `browser_verkauf_ansichten.py` meldet
"Ansicht 'Graph' geoeffnet" als nicht erreicht. Die Graph-Ansicht fuer `sale.order`
existiert auf beiden Instanzen (je ein `ir.ui.view` vom Typ `graph`); der Browser hat
sie ueber VPN nicht rechtzeitig gerendert. Ladezeitgrenze, kein Produktfehler.
Helpdesk liegt auf der VM jetzt bei 58 OK / 1 FEHL - die drei Menue-Fehlschlaege der
Vorrunde sind mit der Label-Korrektur entfallen.
