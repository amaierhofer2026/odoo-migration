# Odoo 11 -> Odoo 18: Bereich Verkauf, Teil 4, Schritt 1 (Listen-, Kanban-, Pivot-, Graph- und Kalenderansichten)

Stand: 28.09.2026, Session 121. Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) wurde
ausschliesslich lesend gelesen (RPC). Geprueft: Odoo 18 lokal (`odoo18_test`)
und VM (`k001959vsx.ipax.at`).

Analysierte Menueaktionen:

| Odoo 11 | Aktion | Odoo 18 | Aktion |
|---|---|---|---|
| Verkauf/Auftraege/Angebote nach Kunden | 429 | Verkauf/Auftraege/Angebote | 430 |
| Verkauf/Auftraege/Auftraege nach Kunden | 426 | Verkauf/Auftraege/Auftraege | 429 |
| Verkauf/Abrechnung/Auftraege zur Rechnung | 427 | Verkauf/Abzurechnen/Abzurechnende Auftraege | 432 |
| Verkauf/Abrechnung/Auftraege fuer Upselling | 428 | Verkauf/Abzurechnen/Auftraege fuer Upselling | 433 |
| (Kundenverwaltung/Pipeline/Angebote) | 429 | Kundenverwaltung/Pipeline/Angebote | 431 |

## 1. Ansichtsarten je Menue

```
Odoo 11 (alle vier Menues gleich):
  view_mode = tree, kanban, form, calendar, pivot, graph
Odoo 18:
  Angebote, Auftraege, Pipeline, Abzurechnen, Upselling:
  view_mode = list, kanban, form, calendar, pivot, graph, activity
```

Odoo 18 bietet zusaetzlich die Aktivitaetenansicht (`activity`) an - bleibt erhalten.

## 2. Listenansichten

### 2.1 Odoo 11 (eine Ansicht `sale.order.tree`, id 1031, ITK-angepasst, fuer alle vier Menues)

```
Reihenfolge (11 Spalten, alle dauerhaft sichtbar - Odoo 11 kennt keine optionalen Spalten):
  1  message_needaction        (Nachrichten-Symbol)
  2  name                      "Auftragsnummer"
  3  confirmation_date         "Bestelldatum" (Widget Datum)
  4  partner_id                Kunde
  5  partner_invoice_id        Rechnungsadresse
  6  sale_contact_id           Verkaufskontakt
  7  user_id                   Verkaeufer
  8  amount_untaxed            Widget Waehrung, Summe "Total Net"
  9  currency_id               Waehrung
 10  invoice_status            Rechnungsstellung
 11  state                     Status
Standard-Sortierung: keine Angabe in der Ansicht (Modell-Sortierung date_order absteigend)
```

### 2.2 Odoo 18

| Menueaktion | Listenansicht | Spalten |
|---|---|---|
| 430 Angebote | 1223 `sale.view_quotation_tree_with_onboarding` (+ ITK 1526) | 24 |
| 429 Auftraege, 431 Pipeline, 432 Abzurechnen, 433 Upselling | 1220 `sale.view_order_tree` (+ ITK 1528) | 22 |

Spalten der Auftragsliste (1220) in Reihenfolge, `[s]` = in Odoo 18 standardmaessig sichtbar,
`[o]` = optional (ueber die Spaltenauswahl einblendbar):

```
message_needaction                      1
currency_id                             2
name                        "Nummer"    3
date_order                  [s]         4   (Angebotsliste stattdessen create_date "Erstellungsdatum" [s])
confirmation_date "Bestelldatum" [s]    5   <- neu ergaenzt (Odoo-11-Spalte)
commitment_date             [o]         6
expected_date               [o]         7
partner_id                              8
partner_invoice_id                      9
sale_contact_id                        10
user_id                     [s]        11
activity_ids                [s]        12
team_id                     [o]        13
company_id                             14
amount_untaxed "Gesamt exkl. Steuern" [o] 15
amount_tax "Steuern insgesamt"      [o] 16
amount_untaxed Summe "Total Net"       17
tag_ids                     [o]        18
state                       (Angebote [s]) 19
invoice_status              [s]        20
client_order_ref            [o]        21
validity_date               [o]        22
```

### 2.3 Vergleich

| Odoo 11 Spalte | Odoo 18 vorher | Bewertung |
|---|---|---|
| message_needaction | vorhanden | gleich |
| name "Auftragsnummer" | vorhanden, Label "Nummer" | Label differiert (Odoo-18-Standard), Funktion gleich |
| confirmation_date "Bestelldatum" | **nicht vorhanden** | **Luecke - ergaenzt (siehe 5.)** |
| partner_id | vorhanden | gleich |
| partner_invoice_id | vorhanden (ITK) | gleich |
| sale_contact_id | vorhanden (ITK) | gleich |
| user_id "Verkaeufer" | vorhanden, Label "Vertriebsmitarbeiter" | gleich |
| amount_untaxed "Total Net" | vorhanden (Summe "Total Net", Anzeige "Nettobetrag") | gleich |
| currency_id | vorhanden | gleich |
| invoice_status | vorhanden | gleich |
| state | vorhanden | gleich |
| - | zusaetzlich: Erstellungsdatum/Auftragsdatum, Liefertermin, Erwartetes Datum, Vertriebskanal, Firma, Steuern, Stichwoerter, Kundenreferenz, Gueltigkeit, Aktivitaeten | Odoo-18-Zusatz, bleibt |

## 3. Kanban

```
Odoo 11 (Ansicht 1030 sale.order.kanban, class o_kanban_mobile):
  Kartenfelder: name, partner_id, amount_total, date_order, state, currency_id
Odoo 18 (Ansicht 1217 sale.view_sale_order_kanban, class o_kanban_mobile, sample=1, quick_create=false):
  Kartenfelder: name, partner_id, amount_total, date_order, state, currency_id, activity_ids
```

Gleichwertig; Odoo 18 zeigt zusaetzlich das Aktivitaetssymbol auf der Karte und den Schalter
"sample" (Beispieldaten in leeren Listen). Bleibt erhalten.

## 4. Pivot, Graph, Kalender, Gruppierungen

| Ansicht | Odoo 11 | Odoo 18 | Bewertung |
|---|---|---|---|
| Pivot | `date_order` Zeile, `amount_total` Mass | gleich (+ sample=1) | gleich |
| Graph | `partner_id` Dimension, `amount_total` Mass, Balken | gleich (+ sample=1) | gleich |
| Kalender | `sale.order.calendar` (1027): date_start=**date_order**, color=state, Monat | `sale.view_sale_order_calendar` (1214): date_start=**activity_date_deadline**, mode=month, event_limit=5, create=0 | **Unterschied - siehe offene Entscheidung** |
| Default-Gruppierung | keine (Kontexte ohne `group_by`) | keine | gleich |
| Aktivitaetenansicht | gibt es nicht | `activity` in allen Menues | Odoo-18-Zusatz, bleibt |

Der Odoo-11-Kalender zeigte Auftraege nach **Auftragsdatum**; der Odoo-18-Kalender zeigt die
**naechste Aktivitaet** je Auftrag (Standard von Odoo 18). Damit fehlt in Odoo 18 die
Odoo-11-Ansicht "Auftraege im Monatskalender nach Datum".

## 5. Umsetzung in Odoo 18 (nur ergaenzt)

Modul `itk_sale_management`, Version 18.0.1.4.0, Datei `views/sale_order.xml`:

```
Angebotsliste (ITK-Ansicht 1526, erbt sale.view_quotation_tree):
  xpath //field[@name='create_date'] position="after"
    <field name="confirmation_date" string="Bestelldatum" optional="show"/>
Auftragsliste (ITK-Ansicht 1528, erbt sale.view_order_tree):
  xpath //field[@name='date_order'] position="after"
    <field name="confirmation_date" string="Bestelldatum" optional="show"/>
```

Damit ist die Odoo-11-Spalte "Bestelldatum" in beiden Listen wieder sichtbar (Odoo-11-Wortlaut,
Position direkt hinter der Datumsspalte) und zusaetzlich in der Spaltenauswahl abwaehlbar.
Es wurde nichts entfernt; alle Odoo-18-Spalten, Ansichten und Ansichtsarten bleiben unveraendert.

## 6. Nachweise

```
scripts/analyse_verkauf_teil4_ansichten.py    je Menueaktion: Ansichtsarten, Listen-/Kanban-/
                                              Pivot-/Graph-/Kalenderansicht, Default-Kontexte
scripts/verify_s121_verkauf_teil4_ansichten.py Prueflauf Odoo 11 (lesend) + lokal + VM
scripts/browser_verkauf_ansichten.py          Browserabnahme: Liste, Kanban, Pivot, Graph, Kalender
docs/_verkauf_teil4_ansichten.json            Rohdaten (gitignoriert)
```

Lokal (28.09.2026):

```
Modul-Upgrade itk_sale_management 18.0.1.4.0 (nach docker restart odoo18)     ohne Fehler
Prueflauf: Odoo 11 36 OK / 0 FEHL (Ausgangslage), lokal ohne Abweichung
Browser: Angebotsliste zeigt "Bestelldatum" (12 sichtbare Spalten), Spaltenauswahl enthaelt es,
         Kanban, Pivot, Graph und Kalender oeffnen fehlerfrei, zurueck zur Liste ok
         11 OK / 0 FEHL, 0 JavaScript- und 0 RPC-Fehler
Screenshots: Desktop\Odoo18-Abnahme-Session121\22_Liste_Bestelldatum_*.png bis 26_Kalender_*.png
```

**VM-Abnahme (28.09.2026, Buer-Zugang, Git-Stand 02de950):**

```
git pull --ff-only + docker restart odoo18 auf der VM
Modul-Upgrade itk_sale_management 18.0.1.4.0 ueber RPC                       ohne Fehler
Prueflauf verify_s121_verkauf_teil4_ansichten.py  Odoo 11 36 + lokal 55 + VM 55 = 146 OK / 0 FEHL
Browserabnahme browser_verkauf_ansichten.py       VM 11 OK / 0 FEHL, 0 JS- und 0 RPC-Fehler
  - Angebotsliste zeigt 12 sichtbare Spalten inklusive "Bestelldatum"
  - Spaltenauswahl enthaelt "Bestelldatum"
  - Kanban, Pivot, Graph und Kalender oeffnen fehlerfrei, zurueck zur Liste ok
  - keine Schreibvorgaenge: Bestand unveraendert 20 Auftraege / 29 Auftragszeilen
Label-Ruecksetzer (bekanntes Muster F34) nach dem Modul-Upgrade: 3 Feldbeschriftungen auf der VM
  nachgezogen mit scripts/apply_sale_labels.py --instanz vm; Kontrolle
  verify_s117_auftraege.py --instanz vm = 65 OK / 0 FEHL
Screenshots: Desktop\Odoo18-Abnahme-Session121\22_Liste_Bestelldatum_vm.png bis 26_Kalender_vm.png
```

## 7. Offene Entscheidung: Kalenderansicht

Odoo 11 hatte einen Monatskalender nach Auftragsdatum; Odoo 18 liefert stattdessen einen
Aktivitaetenkalender (naechste Aktivitaet je Auftrag). Beide koennen nicht gleichzeitig die
Standardkalenderansicht desselben Menues sein. Moeglichkeiten:

```
A) Eigene Kalenderansicht nach Auftragsdatum zusaetzlich anbieten, erreichbar ueber einen
   eigenen Menuepunkt unter Verkauf/Auftraege ("Auftragskalender"). Additiv: der Odoo-18-
   Aktivitaetenkalender bleibt unveraendert. (Empfehlung)
B) Standardkalender der Verkaufsmenues auf das Auftragsdatum umstellen. Der Aktivitaetenkalender
   entfaellt dann als Kalenderansicht (die Aktivitaetenansicht selbst bleibt erhalten).
C) Nichts aendern und den Odoo-11-Kalender als nicht uebernommen dokumentieren.
```

Bisher wurde **keine** dieser Varianten umgesetzt; der Kalender ist unveraendert.

## 8. Umsetzung Option A: Auftragskalender nach Auftragsdatum (Entscheidung Anna, 28.09.2026)

Modul `itk_sale_management`, Version 18.0.1.5.0, Datei `views/sale_order_views_kalender.xml`:

```
1) Neue Kalenderansicht  itk_sale_management.view_saleorder_kalender_itk
   "sale.order.calendar (itk) - Auftragsdatum", Modell sale.order, priority 99:
     <calendar string="Auftragskalender" date_start="date_order" color="state"
               mode="month" quick_create="false">
       Felder partner_id, amount_total, state
   -> Basis ist das Auftragsdatum (date_order), Farbe nach Status, wie in Odoo 11.

2) Neue Aktion  itk_sale_management.action_saleorder_kalender_itk
   "Auftragskalender", res_model sale.order, view_mode calendar,list,form,
   view_ids: calendar -> view_saleorder_kalender_itk (erste Ansicht), list -> sale.view_order_tree,
             form -> sale.view_order_form
   Hinweis: In Odoo 18 ist das Feld `views` nicht gespeichert; die Zuordnung laeuft ueber view_ids.

3) Neuer Menuepunkt  itk_sale_management.menu_saleorder_kalender_itk
   "Auftragskalender" unter Verkauf/Auftraege (parent sale.sale_order_menu), Reihenfolge 25
   -> steht damit direkt nach "Auftraege".
```

Es wurde nichts an bestehenden Ansichten, Aktionen, Menues oder Rechten geaendert; der
Odoo-18-Aktivitaetenkalender (`sale.view_sale_order_calendar`, date_start = activity_date_deadline)
bleibt unveraendert der Kalender der Verkaufsmenues.

Nachweis der Datumsbasis (Browser, Monat September 2026):

```
Auftraege mit Auftragsdatum im Monat (per RPC): S00198, S00200
Im Auftragskalender angezeigt:                 S00198, S00200  -> identisch
Kontrolle: Auftraege mit fruehrerem Auftragsdatum (S00180, S00182, S00188, S00189, S00190)
           erscheinen nicht
Gegenprobe Bestaetigungsdatum: im Testbestand kein Auftrag mit Bestaetigung im Monat und
           abweichendem Auftragsdatum vorhanden (daher nicht pruefbar, dokumentiert)
Aktivitaetenkalender der Angebotsliste: anderer Ereignissatz (Aktivitaetsdatum) - unveraendert
```

Lokales Ergebnis: `browser_verkauf_kalender.py` 16 OK / 0 FEHL, 0 JavaScript- und 0 RPC-Fehler;
`verify_s121_verkauf_kalender.py` (Odoo 11 lesend + lokal) 0 FEHL.
Screenshots: 27_Auftragskalender_*.png, 28_Aktivitaetenkalender_*.png.
