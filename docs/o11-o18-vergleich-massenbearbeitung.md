# Massenbearbeitung: Odoo 11 gegen Odoo 18 (Stand 02.11.2026, Session 140)

Bereich nach Checkliste 6.20. Odoo 11 (`ITK_V1_a`, portal.it-kommunal.at) wurde ausschliesslich
lesend erhoben; es wurde nichts geaendert, angelegt oder geloescht.

Messwerkzeuge (alle read-only gegenueber Odoo 11):
- `scripts/analyse_o11_massenbearbeitung.py` -> `docs/_massenbearbeitung_o11.json`
- `scripts/vergleich_massenbearbeitung.py --instanz lokal|vm` -> `docs/_massenbearbeitung_o18_<instanz>.json`
- `scripts/browser_massenbearbeitung_probe.py --instanz lokal|vm` (echter Chrome; Dialoge werden
  geoeffnet und mit "Abbrechen" beendet, es wird nichts gespeichert)
- `scripts/browser_massenbearbeitung_statusprobe.py --instanz lokal|vm` (prueft, ob die Statusfelder
  im Dialog bedienbar sind)

Regressionsbasis vor dem ersten Eingriff (beide Instanzen, gleiche Werte):
Events 61 OK / 0 FEHL, E-Mail-Marketing 37 OK / 0 FEHL, Personal 54 OK / 0 FEHL,
Projekt 20 OK / 0 FEHL, Verkauf 881 OK / 0 FEHL.

---

## 1 Odoo-11-Live-Stand (gemessen 02.11.2026, 13:34)

| Punkt | Messwert |
|---|---|
| Modul | `mass_editing` 11.0.1.0.1, OCA (Serpent/Tecnativa), state installed |
| Modelle | `mass.object` (Konfiguration), `mass.editing.wizard` (Dialog) |
| Massenaktions-Objekte | **20** (IDs 1, 2, 4, 5, 6, 7, 8, 9, 13, 14, 18, 19, 20, 21, 22, 23, 25, 26, 27, 28) |
| Frueher vorhanden, in Odoo 11 geloescht | 8 IDs (3, 10, 11, 12, 15, 16, 17, 24); hoechste ID 28 |
| Sidebar-Aktionen | 20 x `ir.actions.act_window` auf `mass.editing.wizard`, `target=new`, `view_mode="form, tree"`, Kontext `{'mass_editing_object': <id>}`, `binding_model_id` = Zielmodell, `binding_type=action` |
| Menue | `Einstellungen/Massenverarbeitung/Massenverarbeitung` -> `ir.actions.act_window,488` |
| Rechte Konfiguration | `mass.object`: lesen fuer "Personal / Mitarbeiter", schreiben/anlegen/loeschen fuer "Administration / Zugriffsrechte" |
| Rechte Ausfuehrung | die 20 Aktionen haben keine `groups_id`, also fuer alle internen Benutzer sichtbar |
| Felder von `mass.object` | `name`, `model_id`, `model_list`, `field_ids` (m2m), `ref_ir_act_window_id`; keine Gruppen, keine eigene Ansicht |
| Ansichten der Konfiguration | Liste: Name und Modell. Formular: Name, Modell, Felder, Knopf "Seitenleisten-Schaltflaeche hinzufuegen" |

### 1.1 Dialog in Odoo 11

| Feldtyp | Auswahloptionen (woertlich) |
|---|---|
| Skalar (m2o, date, float, selection, text) | `Set`, `Remove` |
| many2many | `Set`, `Remove`, `Add` |

- Kein Standardwert: `default_get` fuer `selection__<feld>` und `<feld>` liefert `{}` - ohne aktive
  Auswahl passiert nichts.
- Keine Zaehlanzeige der markierten Datensaetze, kein freier Hinweistext, keine Option "nicht aendern".
- Beschriftungen englisch (`Set`, `Remove`, `Add`), Knopf heisst `Apply`.
- Dialogtitel = Name des Massenaktions-Objekts.
- **Wichtig:** der Odoo-11-Assistent entfernt beim Aufbau von `fields_view_get` das `readonly`-Merkmal
  des Zielfelds. Beispiel `state` bei "Angebot zu Auftrag": Felder-Dict enthaelt nur
  `type`, `string`, `selection` (5 Werte: Angebot, Angebot gesendet, Verkaufsauftrag, Gesperrt,
  Abgebrochen) - also im Dialog auswaehlbar, obwohl das Modellfeld `readonly=True` ist.

### 1.2 Die 20 Massenaktionen in Odoo 11 (einzeln)

Spalte "belegt" = Anzahl Datensaetze des Zielmodells mit Wert im Zielfeld (read-only gezaehlt).
Bei `property_product_pricelist` wurde `ir.property` gelesen statt `search_count` (property-Felder
liefern dort falsche Zahlen).

| ID | Name | Modell | Feld | Typ | belegt |
|---|---|---|---|---|---|
| 1 | Zuweisung Preisliste NÖ | res.partner | property_product_pricelist | many2one | 3.758 von 5.848 (Individualwerte: Preisliste 1 = 3.286, 4 = 235, 3 = 182, 2 = 55; kein Firmenstandardwert) |
| 2 | Zuweisung zu Preisliste | sale.order | pricelist_id | many2one | 2.493 von 2.493 |
| 4 | Reccuring Total | sale.subscription.line | quantity | float | 2.456 von 2.456 |
| 5 | Angebot zu Auftrag | sale.order | state | selection | 2.493 von 2.493 (sale 2.340, cancel 147, draft 6) |
| 6 | Status Kunde | res.partner | status_of_partner_id | many2one | 2.276 von 5.848 |
| 7 | Zahlungsbedingungen setzen | sale.order | payment_term_id | many2one | 615 von 2.493 |
| 8 | Startdatum des naechsten Leistungszeitraumes | sale.subscription | recurring_next_date | date | 1.785 von 1.785 |
| 9 | Abo-Status aendern | sale.subscription | state | selection | 1.785 von 1.785 (open 1.500, cancel 233, close 49, draft 3) |
| 13 | Produktkategorie zuweisen | product.product | categ_id | many2one | 655 von 655 |
| 14 | Valorisierungstext aendern | account.invoice | valorisierung_id | many2one | 4.216 von 6.339 |
| 18 | Zahlungsbedingungen setzen Abrechnung | account.invoice | payment_term_id | many2one | 5.799 von 6.339 |
| 19 | Rechnungsdatum Abrechnung | account.invoice | date_invoice | date | 6.327 von 6.339 |
| 20 | Datum der naechsten Rechnung | sale.subscription | recurring_next_date | date | 1.785 von 1.785 (gleiches Feld wie 8) |
| 21 | Massenverarbeitung Leistungszeitraum setzen | account.invoice | sale_order_benefit_period | text | 5.845 von 6.339 |
| 22 | Massenverarbeitung Projektkategorie setzen | account.invoice | projectcategory_id | many2one | 5.316 von 6.339 |
| 23 | Tag-Zuweisung | res.partner | category_id | many2many | 2.198 von 5.848 mit mindestens einem Stichwort |
| 25 | Produktinteresse setzen | crm.lead | x_Produktinteresse | selection | 6.592 von 6.970 (ifg 5.595, hinweisgeber 752, formulare 98, intrakommuna 80, anonym_portal 40, ogd 14, sonstiges 6, rubicon 4, verwaltungsmanager 2, gemeindecloud 1) |
| 26 | Lead Quelle setzen | crm.lead | x_Lead_Quelle | selection | 6.468 von 6.970 (ifg_post_aussendung_2025_01_21 4.296, itk_voewg_2025_06_24 463, recherchierte_adressen_04_2025 419, web_hinweis_in_230620 297, ...) |
| 27 | Interessent Stichwort setzen | crm.lead | tag_ids | many2many | 6.155 von 6.970 mit mindestens einem Stichwort |
| 28 | Interessent Lead Status setzen | crm.lead | x_lead_status | selection | 6.712 von 6.970 (angelegt 5.297, event_teilgenommen_angemeldet 463, event_teilngenommen 331, leadverloren 221, kontaktiert 134, event_angemeldet 120, opp_vorhanden 101, aufbereitet 19, kunde 15, rueckruf 7, onhold 3, termin 1) |

Jede der 20 Aktionen arbeitet auf einem real gefuellten Feld; keine ist eine Leerform.

---

## 2 Odoo-18-Stand (lokal und VM, gemessen 02.11.2026)

| Punkt | lokal | VM |
|---|---|---|
| Modul | `server_action_mass_edit` 18.0.1.1.3 (OCA), installed | gleich |
| Modelle | `ir.actions.server` (state=`mass_edit`), `ir.actions.server.mass.edit.line`, `mass.editing.wizard` | gleich |
| Massenbearbeitungs-Aktionen | **21** (IDs 1303 bis 1323), 21 Zeilen in `mass.edit.line` | 21, identische Namen und Felder |
| Zielfelder der 20 Odoo-11-Aktionen | 20 von 20 vorhanden und schreibbar | 20 von 20 |
| Rechte Ausfuehrung | `mass.editing.wizard`: interner Benutzer lesen/schreiben/anlegen/loeschen | gleich |
| Rechte Konfiguration | `ir.actions.server`: "Administration / Einstellungen" | gleich |
| Gruppen an den Aktionen | keine (wie Odoo 11) | keine |
| Konfigurationsort | `Einstellungen/Technisch/Server-Aktionen`, Reiter "Felder" (Zeilen: Reihenfolge, Feld, Widget, Domain) und "Nachricht" | gleich |

### 2.1 Feldebene: was in Odoo 18 aus welchem Odoo-11-Feld wurde

| Odoo-11-Feld | Odoo-18-Feld | Typ | readonly | Anmerkung |
|---|---|---|---|---|
| res.partner.property_product_pricelist | gleich | many2one | nein | firmenabhaengig (nicht gespeichert) |
| sale.order.pricelist_id | gleich | many2one | nein | |
| sale.subscription.line.quantity | gleich | float | nein | Modell jetzt unter "Abonnementbuchung" |
| sale.order.state | gleich | selection | **ja** | Ursache des Fehlers F1 |
| res.partner.status_of_partner_id | gleich | many2one | nein | ITK-Feld |
| sale.order.payment_term_id | gleich | many2one | nein | |
| sale.subscription.recurring_next_date | gleich | date | nein | |
| sale.subscription.state | gleich | selection | nein | bedienbar (5 Werte) |
| product.product.categ_id | gleich | many2one | nein | verknuepft auf product.template.categ_id |
| account.invoice.valorisierung_id | account.move.valorisierung_id | many2one | nein | |
| account.invoice.payment_term_id | account.move.invoice_payment_term_id | many2one | nein | umbenannt |
| account.invoice.date_invoice | account.move.invoice_date | date | nein | umbenannt |
| account.invoice.sale_order_benefit_period | account.move.sale_order_benefit_period | text | nein | |
| account.invoice.projectcategory_id | account.move.projectcategory_id | many2one | nein | |
| res.partner.category_id | gleich | many2many | nein | |
| crm.lead.x_Produktinteresse | gleich | selection | nein | ITK-Auswahlfeld |
| crm.lead.x_Lead_Quelle | gleich | selection | nein | ITK-Auswahlfeld |
| crm.lead.tag_ids | gleich | many2many | nein | |
| crm.lead.x_lead_status | gleich | selection | nein | ITK-Auswahlfeld |

### 2.2 Vorhandene Aktionen (alle `state=mass_edit`, `binding_type=action`)

| O18-ID | Name | Modell | Feld |
|---|---|---|---|
| 1303 | Massenbearbeitung Kontakte | Kontakt | Stichwoerter |
| 1304 | Zuweisung Preisliste NÖ | Kontakt | Preisliste |
| 1305 | Zuweisung zu Preisliste | Angebot | Preisliste |
| 1306 | Recurring Total | Abonnementbuchung | Menge |
| 1307 | Angebot zu Auftrag | Angebot | Status |
| 1308 | Status Kunde | Kontakt | Status |
| 1309 | Zahlungsbedingungen setzen | Angebot | Zahlungsbedingungen |
| 1310 | Startdatum des naechsten Leistungszeitraumes | Verkauf ueber Abonnement | Datum der naechsten Rechnung |
| 1311 | Abo-Status aendern | Verkauf ueber Abonnement | Status |
| 1312 | Produktkategorie zuweisen | Produktvariante | Interne Kategorie |
| 1313 | Valorisierungstext aendern | Rechnung | Valorisation Text |
| 1314 | Zahlungsbedingungen setzen Abrechnung | Rechnung | Zahlungsbedingungen |
| 1315 | Rechnungsdatum Abrechnung | Rechnung | Rechnungsdatum |
| 1316 | Datum der naechsten Rechnung | Verkauf ueber Abonnement | Datum der naechsten Rechnung |
| 1317 | Leistungszeitraum setzen | Rechnung | Leistungszeitraum |
| 1318 | Projektkategorie setzen | Rechnung | Project Category |
| 1319 | Tag-Zuweisung | Kontakt | Stichwoerter |
| 1320 | Produktinteresse setzen | Lead/Verkaufschance | Produktinteresse |
| 1321 | Lead Quelle setzen | Lead/Verkaufschance | Lead Quelle |
| 1322 | Interessent Stichwort setzen | Lead/Verkaufschance | Stichwoerter |
| 1323 | Interessent Lead Status setzen | Lead/Verkaufschance | Lead Status |

Zaehlpruefung: 20 Odoo-11-Objekte -> 21 Odoo-18-Aktionen. Die Differenz ist eine **Dublette**
(1303 "Massenbearbeitung Kontakte" und 1319 "Tag-Zuweisung" setzen beide `Stichwoerter` am Kontakt).

Das Pruefskript meldet daher "21 OK / 1 FEHL" (Soll 20, Ist 21). Der eine FEHL ist der Befund B1 und
kein Werkzeugfehler; alle 20 Feldpruefungen sind OK.

---

## 3 Vergleich je Massenaktion

Odoo 18 (Community) hat **keine** eingebaute Massenbearbeitung: die Listenansicht ist zeilenweise
inline editierbar, aber nicht fuer mehrere markierte Datensaetze gleichzeitig. Die gleichwertige
Funktion ist `server_action_mass_edit` (bereits installiert, im Bereich Abrechnung abgenommen,
Teil 4 vom 30.09.2026). Ein Nachbau entfaellt.

| O11-ID | Name | Wofuer verwendet | O18-Zielfeld | Standardfunktion in Odoo 18 | Zustand |
|---|---|---|---|---|---|
| 1 | Zuweisung Preisliste NÖ | einem Kontaktbestand eine andere Verkaufspreisliste zuweisen | vorhanden | nein (Kontaktliste nur zeilenweise) | OK |
| 2 | Zuweisung zu Preisliste | Preisliste auf vielen Angeboten nachziehen | vorhanden | nein | OK |
| 4 | Reccuring Total | Menge auf Abo-Positionen in Serie korrigieren | vorhanden | nein | OK |
| 5 | Angebot zu Auftrag | mehrere Angebote in einem Schritt bestaetigen | vorhanden, aber readonly | `action_confirm` je Auftrag, Standard-Aktion "Angebot als gesendet markieren"; keine Massenfunktion | **FEHLER F1: Dialog nicht bedienbar** |
| 6 | Status Kunde | ITK-Status (Gemeinde/Kunde) auf vielen Kontakten setzen | vorhanden | nein | OK |
| 7 | Zahlungsbedingungen setzen | Zahlungsbedingung auf vielen Auftraegen aendern | vorhanden | nein | OK |
| 8 | Startdatum naechster Leistungszeitraum | Abrechnungslauf neu takten | vorhanden | nein | OK |
| 9 | Abo-Status aendern | Abos in Serie kuendigen/beenden | vorhanden | Schliessen/Kuendigen je Abo; keine Massenfunktion | OK (schreibt Status direkt, siehe K3) |
| 13 | Produktkategorie zuweisen | Produkte umkategorisieren (Kategorie steuert Konten/Steuern) | vorhanden | nein | OK |
| 14 | Valorisierungstext aendern | Valorisierungshinweis auf vielen Rechnungen setzen | vorhanden | nein | OK |
| 18 | Zahlungsbedingungen Abrechnung | Zahlungsbedingung auf vielen Rechnungen | vorhanden | nein | OK |
| 19 | Rechnungsdatum Abrechnung | Rechnungsdaten in Serie nachtragen | vorhanden | nein | OK |
| 20 | Datum der naechsten Rechnung | wie 8, zweiter Einstiegspunkt | vorhanden | nein | OK (Dublette schon in Odoo 11) |
| 21 | Leistungszeitraum setzen | Leistungszeitraum (Text) auf vielen Rechnungen | vorhanden | nein | OK |
| 22 | Projektkategorie setzen | Projektkategorie auf vielen Rechnungen | vorhanden | nein | OK |
| 23 | Tag-Zuweisung | Stichwoerter in Serie zuweisen/entfernen | vorhanden | nein | OK, aber Dublette 1303/1319 |
| 25 | Produktinteresse setzen | Kampagnen-/Produktinteresse auf Leadbestand | vorhanden | nein | OK |
| 26 | Lead Quelle setzen | Herkunft der Leadquelle auf Leadbestand | vorhanden | `source_id` ("Herkunft") ist ein anderes Feld, kein Ersatz | OK |
| 27 | Interessent Stichwort setzen | Stichwoerter auf Leads | vorhanden | nein | OK |
| 28 | Interessent Lead Status setzen | Lead-Status in Serie setzen | vorhanden | nein | OK |

Ergebnis: **19 von 20 Aktionen sind gleichwertig vorhanden und im Dialog bedienbar, 1 Aktion ist
defekt (F1).** Keine Funktion fehlt ersatzlos; ein Nachbau des Moduls ist nicht noetig.

---

## 4 Fehler F1: "Angebot zu Auftrag" ist in Odoo 18 nicht bedienbar

| Nachweis | Odoo 11 | Odoo 18 |
|---|---|---|
| Modellfeld `sale.order.state` | `readonly=True` | `readonly=True` |
| Felder-Dict des Dialogs fuer `state` | `type`, `string`, `selection` (5 Werte) - **kein readonly** | `readonly=True`, `type=selection` |
| Browserbild (18 Angebote markiert, Aktion "Angebot zu Auftrag", Auswahl "Setzen") | - | Statusfeld leer, keine Auswahlwerte |
| Vergleich: "Abo-Status aendern" | - | Statusfeld mit 5 Werten (Neu, Laufend, Zu erneuern, Abgeschlossen, Abgebrochen) |

Ursache: der Odoo-11-Assistent hat beim Aufbau der Dialogfelder `readonly` verworfen, der
OCA-18-Assistent uebernimmt das Merkmal unveraendert. Ein Anwender kann daher den Zielstatus nicht
waehlen; die Aktion ist fuer ihren Zweck unbrauchbar. Das ist der einzige der 20 Faelle - alle
anderen Zielfelder sind in Odoo 18 beschreibbar. Ein Klick auf "Anwenden" wurde bewusst nicht
ausgefuehrt, weil er Daten schreiben wuerde.

---

## 5 Browser-Ist-Stand (lokal, echter Chrome, nichts gespeichert)

Aktionsmenue der Listenansichten (Auszug der Massenbearbeitungs-Eintraege):

| Liste | Massenbearbeitungs-Eintraege |
|---|---|
| Kontakte (80 markiert) | Massenbearbeitung Kontakte, Zuweisung Preisliste NÖ, Status Kunde, Tag-Zuweisung |
| Ausgangsrechnungen (27) | Valorisierungstext aendern, Zahlungsbedingungen setzen Abrechnung, Rechnungsdatum Abrechnung, Leistungszeitraum setzen, Projektkategorie setzen |
| Leads (1) | Produktinteresse setzen, Lead Quelle setzen, Interessent Stichwort setzen, Interessent Lead Status setzen, **Execute Code** (siehe B2) |
| Angebote (18) | Zuweisung zu Preisliste, Angebot zu Auftrag, Zahlungsbedingungen setzen |
| Abonnements (10) | **Preisliste fuer Abonnements festlegen** (neu in Odoo 18), Startdatum des naechsten Leistungszeitraumes, Abo-Status aendern, Datum der naechsten Rechnung |

Dialoge (alle deutsch, alle mit "Abbrechen" beendet):

| Dialog | Auswahloptionen | Hinweiszeile |
|---|---|---|
| Tag-Zuweisung | Nicht ändern, Setzen, Entfernen, Hinzufügen | "Die Behandlung wird für den/die 80 ausgewählten Datensatz/e durchgeführt." |
| Zuweisung Preisliste NÖ | Nicht ändern, Setzen, Entfernen | "Die Behandlung wird für den/die 80 ausgewählten Datensatz/e durchgeführt." |
| Status Kunde | Nicht ändern, Setzen, Entfernen | "Die Behandlung wird für den/die 80 ausgewählten Datensatz/e durchgeführt." |
| Rechnungsdatum Abrechnung | Nicht ändern, Setzen, Entfernen | "Die Behandlung wird für den/die 27 ausgewählten Datensatz/e durchgeführt." |
| Interessent Lead Status setzen | Nicht ändern, Setzen, Entfernen | "Die Behandlung wird für den/die 1 ausgewählten Datensatz/e durchgeführt." |
| Angebot zu Auftrag | Nicht ändern, Setzen, Entfernen | "Die Behandlung wird für den/die 18 ausgewählten Datensatz/e durchgeführt." (Statusfeld leer, F1) |
| Abo-Status aendern | Nicht ändern, Setzen, Entfernen | "Die Behandlung wird für den/die 10 ausgewählten Datensatz/e durchgeführt." (5 Statuswerte waehlbar) |

**Werkzeugfehler, ausdruecklich als solcher:** ein erster Prueflauf meldete vier fehlende deutsche
Uebersetzungen in `addons/server_action_mass_edit/i18n/de.po`. Ursache war ein zu einfacher
Pruefausdruck, der mehrzeilige `msgstr`-Bloecke nicht zusammensetzte. Korrekte Messung:
45 Eintraege, **0 ohne Uebersetzung**; der Dialog ist im Browser vollstaendig deutsch. Es gibt
hier keinen Uebersetzungsbedarf.

---

## 6 Weitere Unterschiede und Befunde

| Nr | Befund | Bewertung |
|---|---|---|
| U1 | Dialogoptionen: Odoo 11 `Set/Remove/Add` (englisch), Odoo 18 `Nicht ändern/Setzen/Entfernen/Hinzufügen` | Odoo 18 besser, bleibt |
| U2 | Odoo 11 ohne "nicht aendern" und ohne Standardwert; Odoo 18 mit "Nicht ändern" als Standard | gleichwertig bis besser, bleibt |
| U3 | Odoo 18 zusaetzlich: Zaehlanzeige der markierten Datensaetze, freier Hinweistext (`mass_edit_message`), Domain je Zeile (`apply_domain`) | neue sinnvolle Funktionen, bleiben |
| U4 | Odoo 18 zusaetzlich: Konfiguration je Feldzeile mit Reihenfolge und Widget | bleibt |
| U5 | Konfigurationsort: Odoo 11 Menue `Einstellungen/Massenverarbeitung`; Odoo 18 nur `Einstellungen/Technisch/Server-Aktionen` | Kandidat fuer eigenes Menue (K5) |
| B1 | Dublette 1303 "Massenbearbeitung Kontakte" und 1319 "Tag-Zuweisung" (beide Stichwoerter am Kontakt) | bereinigen (K1) |
| B2 | "Execute Code" im Aktionsmenue der Leads: die Automatisierung "Interessent 'zur Verrechnung bereit'" hat in Odoo 18 eine gebundene Server-Aktion. In Odoo 11 ist dieselbe Automatisierung **nicht** gebunden (`binding_model_id = False`); ausserdem Odoo 11 `state=email`, Odoo 18 `state=code` mit Chatter-Nachricht | Anzeigebereinigung empfohlen, inhaltliche Angleichung gehoert in den Bereich CRM/Automatisierung - dort nicht ohne Auftrag aendern |
| B3 | Neue Odoo-18-Funktion "Preisliste fuer Abonnements festlegen" (`sale.subscription.set.pricelist.confirm`, gebunden an Abonnement) hat keine Odoo-11-Entsprechung | bleibt (neue sinnvolle Funktion) |
| B4 | Name "Zuweisung Preisliste NÖ" beschreibt den Hauptanlass; die Aktion ist nicht auf eine Preisliste festgelegt. Odoo 11 fuehrt 49 Preislisten (viele "nicht mehr verwenden"), Odoo 18 derzeit eine aktive (ID 34, EUR) | Preislisten-Zuordnung ist Teil der Kontakt-Datenmigration, nicht dieses Bereichs |

---

## 7 Entscheidungspunkte

**K1 Dublette 1303/1319.** Empfehlung: Aktion 1303 "Massenbearbeitung Kontakte" entfernen, damit im
Aktionsmenue der Kontakte wieder genau ein Eintrag fuer Stichwoerter steht (Odoo-11-Zustand). Keine
Daten betroffen, die Aktion 1319 "Tag-Zuweisung" bleibt mit dem Odoo-11-Namen.

**K2 Fehler F1 "Angebot zu Auftrag" (1307).** Zwei Moeglichkeiten:
- (a) Empfehlung: Massenbearbeitung auf `state` ersetzen durch eine Server-Aktion vom Typ "Code",
  die `records.action_confirm()` aufruft (Name "Angebote bestaetigen"). Das nutzt die
  Odoo-18-Standardlogik. Nebenwirkung: das Bestelldatum (`date_order`) wird auf den
  Bestaetigungszeitpunkt gesetzt, weil `action_confirm` das so vorsieht.
- (b) Gleiches Verhalten wie Odoo 11: den OCA-Assistenten so anpassen, dass er `readonly` verwirft
  (kleiner Eingriff in die Modul-Kopie), dann schreibt die Massenbearbeitung den Status direkt,
  ohne Bestelldatum und ohne Folgelogik.

Bitte entscheiden, welche Variante; ohne Entscheidung bleibt F1 offen und die Aktion unbrauchbar.

**K3 "Abo-Status aendern" (1311).** Funktioniert, schreibt den Status aber direkt (kein
Schliessen-/Kuendigungsweg, keine Abo-Standardlogik). Empfehlung: wie Odoo 11 belassen und hier als
bewusste Abweichung von der Standardlogik dokumentieren. Alternative: Code-Aktion mit den
Abo-Standardmethoden - dann Fachfreigabe notwendig, weil sich das Ergebnis je Abo aendern kann.

**K4 "Execute Code" (B2).** Empfehlung: Bindung der Automatisierungs-Aktion entfernen, damit der
Eintrag aus dem Aktionsmenue verschwindet (in Odoo 11 war er nicht sichtbar). Die inhaltliche
Angleichung der Automatisierung (E-Mail statt Chatter-Nachricht) ist ein eigener Auftrag im Bereich
CRM.

**K5 Konfigurationsmenue.** Empfehlung: ITK-Menue `Einstellungen/Massenverarbeitung` mit gefilterter
Ansicht auf `state=mass_edit` anlegen (reine Menue- und Domain-Aenderung, keine Logik). Damit sind
die 21 Aktionen wie in Odoo 11 an einer Stelle pflegbar.

**K6 Namen im Aktionsmenue.** Odoo 11 zeigte "Massenverarbeitung (Zuweisung Preisliste NÖ)", Odoo 18
zeigt nur den Objektnamen. Empfehlung: kurze Namen behalten; das Odoo-11-Praefix ist auf Wunsch in
einem Durchlauf ergaenzbar.

**K7 Kein Nachbau.** Fuer keine der 20 Aktionen gibt es eine Odoo-18-Standardfunktion fuer mehrere
Datensaetze. Das bereits installierte OCA-Modul bleibt die Grundlage; es wird nichts nachgebaut und
keine Odoo-18-Standardlogik ueberschrieben.

---

## 8 Was unveraendert bleibt

- Odoo 11 wurde nicht beschrieben, es wurden keine fachlichen Daten migriert, angelegt oder geloescht.
- Die 21 Aktionen bleiben bestehen, solange K1 bis K6 nicht entschieden sind.
- Die gesperrten Bereiche (Projekt, Personal, Zeiterfassung, Anwesenheiten, Verkauf, Abonnements,
  Helpdesk, Events, E-Mail-Marketing) wurden nicht angefasst und laufen nur in der Regression mit.

---

## 9 Umsetzung (Session 140, Entscheidungen K1 bis K6 vom 02.11.2026)

### 9.1 Aenderungen

| Punkt | Umsetzung | Ort |
|---|---|---|
| K1 | Dublette entfernt: Server-Aktion 1303 "Massenbearbeitung Kontakte" geloescht, "Tag-Zuweisung" (1319) bleibt | `scripts/apply_massenbearbeitung.py` |
| K2 | OCA-Assistent verwirft beim Aufbau der Dialogfelder das Merkmal `readonly` (wie Odoo 11); Statusfelder sind damit waehlbar | `addons/server_action_mass_edit/wizard/mass_editing_wizard.py` |
| K3 | keine Aenderung; "Abo-Status aendern" schreibt den Status direkt (dokumentierte Abweichung) | - |
| K4 | Bindung der Automatisierungs-Aktion "Execute Code" am Lead entfernt; Automatisierung bleibt aktiv | `scripts/apply_massenbearbeitung.py` |
| K5 | Modul `itk_massenbearbeitung` 18.0.1.0.0: Menue Einstellungen > Massenverarbeitung, gefilterte Liste (Domain `state=mass_edit`), Anlegen mit Vorbelegung `state=mass_edit` | `addons/itk_massenbearbeitung/` |
| K6 | kurze Objektnamen beibehalten | - |
| T1 | Stichwortfelder im Dialog als Tags (`widget_option` = `many2many_tags`) statt Unterliste | `apply_massenbearbeitung.py` (Zeilen von 1319, 1322) |
| T2 | "Hinzufuegen" bei many2many schreibt Verknuepfungen `(4,id)`; vorher blieb die Aktion wirkungslos | `mass_editing_wizard.py` |

Modulstand: `server_action_mass_edit` 18.0.1.1.3 auf **18.0.1.1.4** (zwei ITK-Anpassungen, im Quelltext
kommentiert).

### 9.2 Warum kein `action_confirm` (K2)

Anna hat Variante (b) freigegeben: die Odoo-11-Funktion soll wieder bedienbar sein, ohne zusaetzliche
Geschaeftslogik. Belege:

| Frage | Messung |
|---|---|
| Was hat Odoo 11 geaendert? | `sale.order` hat in Odoo 11 **kein eigenes `write()`** (nur `SaleOrderLine.write`); die Massenbearbeitung schreibt ausschliesslich das konfigurierte Feld |
| Wie sah der Odoo-11-Zustand der Daten aus? | 2.342 Auftraege mit `state = sale`, **alle** mit `confirmation_date`, **keiner** ohne |
| Was wuerde `action_confirm()` in Odoo 18 zusaetzlich tun? | `write(_prepare_confirmation_values())` = `state` + `date_order` (jetzt); `itk_sale_management` ergaenzt `confirmation_date`; danach `_action_confirm()`: `sale_stock` -> `_action_launch_stock_rule()` (Lieferungen), `sale_project` -> Projekte/Aufgaben, `sale_purchase` -> Bestellungen |
| Installierte Module mit `_action_confirm` | `sale_stock`, `sale_project`, `sale_purchase`, `stock`, `project` (mrp, repair, delivery nicht installiert) |

Ergebnis: Die Massenbearbeitung schreibt nur `state`. Im Test wurde geprueft, dass `date_order`,
`confirmation_date` und die Zahl der `stock.picking` unveraendert bleiben.

### 9.3 Fehler F1 und seine Behebung

| Nachweis | Odoo 11 | Odoo 18 vorher | Odoo 18 nachher |
|---|---|---|---|
| Felder-Dict des Dialogs fuer `sale.order.state` | ohne `readonly`, 5 Auswahlwerte | `readonly=True`, Feld leer | ohne `readonly`, 4 Auswahlwerte |
| Bedienbarkeit im Browser | gegeben | nicht gegeben | gegeben |

Odoo 18 kennt den Odoo-11-Zustand "Gesperrt" (done) nicht mehr; die Auswahl zeigt Angebot,
Angebot gesendet, Verkaufsauftrag, Storniert.

---

## 10 Browserabnahme (echter Chrome, jede Aktion angewendet und zurueckgenommen)

Je Aktion: Liste oeffnen, zwei Datensaetze markieren, Aktion im Menue "Aktion" waehlen, Dialog
pruefen (Titel, Optionen, Zaehlanzeige, Feldtyp), Modus und Wert setzen, "Anwenden", per RPC
Feld-Diff pruefen, Ausgangswerte zurueckschreiben und nachpruefen.

Ergebnis lokal und VM: **je 265 OK / 0 FEHL ueber 20 Aktionen**.

| Odoo-11-Aktion | Odoo-18-Aktion | Status | getestetes Verhalten | bewusste Abweichung |
|---|---|---|---|---|
| Zuweisung Preisliste NÖ | Zuweisung Preisliste NÖ | OK | 2 Datensätze; Wert Preisliste 2026 + Valorisierung; Dialog zeigt Preisliste 2026 + Valorisierung (EUR); Schreibvorgang belegt; Ausgangswerte wiederhergestellt | nein |
| Zuweisung zu Preisliste | Zuweisung zu Preisliste | OK | 2 Datensätze; Wert Preisliste 2026 + Valorisierung; Dialog zeigt Preisliste 2026 + Valorisierung (EUR); geschrieben: pricelist_id; Ausgangswerte wiederhergestellt | nein |
| Reccuring Total | Recurring Total | OK | 2 Datensätze; Wert 2; Dialog zeigt 2,00; geschrieben: quantity; Ausgangswerte wiederhergestellt | nein |
| Angebot zu Auftrag | Angebot zu Auftrag | OK | 2 Datensätze; Wert Verkaufsauftrag; Dialog zeigt Verkaufsauftrag; geschrieben: state; Ausgangswerte wiederhergestellt | ja (Status direkter Feld-Write wie Odoo 11, kein action_confirm) |
| Status Kunde | Status Kunde | OK | 2 Datensätze; Wert Bestandskunde; Dialog zeigt Bestandskunde; geschrieben: status_of_partner_id; Ausgangswerte wiederhergestellt | nein |
| Zahlungsbedingungen setzen | Zahlungsbedingungen setzen | OK | 2 Datensätze; Wert 15 Tage; Dialog zeigt 15 Tage; geschrieben: payment_term_id; Ausgangswerte wiederhergestellt | nein |
| Startdatum des nächsten Leistungszeitraumes | Startdatum des nächsten Leistungszeitraumes | OK | 2 Datensätze; Wert 01.12.2026; Dialog zeigt 01.12.2026; geschrieben: recurring_next_date; Ausgangswerte wiederhergestellt | nein |
| Abo-Status ändern | Abo-Status ändern | OK | 2 Datensätze; Wert Zu erneuern; Dialog zeigt Zu erneuern; geschrieben: state; Ausgangswerte wiederhergestellt | ja (Status direkter Feld-Write wie Odoo 11) |
| Produktkategorie zuweisen | Produktkategorie zuweisen | OK | 2 Datensätze; Wert Expenses; Dialog zeigt All / Expenses; Schreibvorgang belegt; Ausgangswerte wiederhergestellt | nein |
| Valorisierungstext ändern | Valorisierungstext ändern | OK | 2 Datensätze; Wert VAL-OK; Dialog zeigt VAL-OK; geschrieben: is_manually_modified, valorisierung_id; berechnete Folgefelder mitgefuehrt; Ausgangswerte wiederhergestellt | nein |
| Zahlungsbedingungen setzen Abrechnung | Zahlungsbedingungen setzen Abrechnung | OK | 2 Datensätze; Wert 15 Tage; Dialog zeigt 15 Tage; geschrieben: invoice_date_due, invoice_payment_term_id, is_manually_modified; berechnete Folgefelder mitgefuehrt; Ausgangswerte wiederhergestellt | nein |
| Rechnungsdatum Abrechnung | Rechnungsdatum Abrechnung | OK | 2 Datensätze; Wert 01.12.2026; Dialog zeigt 01.12.2026; geschrieben: date, invoice_date, is_manually_modified; berechnete Folgefelder mitgefuehrt; Ausgangswerte wiederhergestellt | nein |
| Datum der nächsten Rechnung | Datum der nächsten Rechnung | OK | 2 Datensätze; Wert 01.12.2026; Dialog zeigt 01.12.2026; geschrieben: recurring_next_date; Ausgangswerte wiederhergestellt | nein |
| Massenverarbeitung Leistungszeitraum setzen | Leistungszeitraum setzen | OK | 2 Datensätze; Wert Test S140; Dialog zeigt Test S140; geschrieben: is_manually_modified, sale_order_benefit_period; berechnete Folgefelder mitgefuehrt; Ausgangswerte wiederhergestellt | nein |
| Massenverarbeitung Projektkategorie setzen | Projektkategorie setzen | OK | 2 Datensätze; Wert amtsweg.gv.at - BUNDESLAND STANDARD; Dialog zeigt amtsweg.gv.at - BUNDESLAND STANDARD; geschrieben: is_manually_modified, projectcategory_id; berechnete Folgefelder mitgefuehrt; Ausgangswerte wiederhergestellt | nein |
| Tag-Zuweisung | Tag-Zuweisung | OK | 2 Datensätze; Wert AFS; Dialog zeigt AFS; geschrieben: category_id; Ausgangswerte wiederhergestellt | nein (Stichwortfeld als Tags statt Unterliste) |
| Produktinteresse setzen | Produktinteresse setzen | OK | 2 Datensätze; Wert IFG; Dialog zeigt IFG; geschrieben: x_Produktinteresse; Ausgangswerte wiederhergestellt | nein |
| Lead Quelle setzen | Lead Quelle setzen | OK | 2 Datensätze; Wert Recherchierte Adressen April 2025; Dialog zeigt Recherchierte Adressen April 2025; geschrieben: x_Lead_Quelle; Ausgangswerte wiederhergestellt | nein |
| Interessent Stichwort setzen | Interessent Stichwort setzen | OK | 2 Datensätze; Wert TEST S140; Dialog zeigt TEST S140; geschrieben: tag_ids; Ausgangswerte wiederhergestellt | nein (Stichwortfeld als Tags statt Unterliste) |
| Interessent Lead Status setzen | Interessent Lead Status setzen | OK | 2 Datensätze; Wert Lead kontaktiert; Dialog zeigt Lead kontaktiert; geschrieben: x_lead_status; Ausgangswerte wiederhergestellt | nein |

Gesamt: 20 Aktionen geprueft am 2026-11-05T14:23:47


---

## 11 Rechtepruefung

Testbenutzer ohne Einstellungsrechte (`base.group_user` + `base.group_partner_manager`),
angelegt und nach der Pruefung samt Kontakt wieder entfernt.

| Pruefung | lokal | VM |
|---|---|---|
| Aktion im Menue "Aktion" sichtbar | OK | OK |
| Dublette nicht mehr im Menue | OK | OK |
| Dialog bedienbar, Optionen Nicht aendern/Setzen/Entfernen/Hinzufuegen | OK | OK |
| Zaehlanzeige nennt die markierten Datensaetze | OK | OK |
| Menue Einstellungen > Massenverarbeitung gesperrt | OK ("Sie haben keinen Zugriff auf Datensaetze Serveraktion") | OK (gleiche Meldung) |
| Schreiben auf eine Server-Aktion verweigert | OK | OK |
| Assistent fuer den Benutzer lesbar | OK | OK |
| Testbenutzer und Testkontakt entfernt | OK | OK |

Ergebnis: **lokal 10 OK / 0 FEHL, VM 12 OK / 0 FEHL** (VM mit zwei zusaetzlichen Pruefungen zur
Menueaktion, deren ID je Datenbank aufgeloest wird).

Zusatzbefund: ein Benutzer ohne Schreibrecht auf `res.partner` bekommt die Aktion sauber verweigert
(Meldung im Server-Log: "Forbidden server action 'Tag-Zuweisung' ... does not have access to
res.partner"). Das ist Odoo-Standardverhalten und bleibt.

---

## 12 Regression

| Pruefung | lokal | VM |
|---|---|---|
| Events (`verify_s138_events`) | 61 OK / 0 | 61 OK / 0 |
| E-Mail-Marketing (`verify_s138_marketing`) | 37 OK / 0 | 37 OK / 0 |
| Personal (`verify_personal`) | 54 OK / 0 | 54 OK / 0 |
| Projekt (`verify_s135_projekt`) | 20 OK / 0 | 20 OK / 0 |
| Verkauf (`abschluss_verkauf_regression`) | Referenzniveau, keine Abweichung | Referenzniveau |
| Zeiterfassung (`verify_s135_zeiterfassung`) | 54 OK / 0 | 54 OK / 0 |
| Abonnements (`verify_s118_abo`) | 19 OK / 0 | 19 OK / 0 |
| Helpdesk (`verify_s112_support_ticket`) | 35 OK / 0 | 35 OK / 0 |
| Abrechnung (`verify_s108_abrechnung`) | 42 OK / 2 | 42 OK / 2 |
| Kundenverwaltung (`verify_s115_kundenverwaltung`) | 40 OK / 1 | 40 OK / 1 |
| Anwesenheiten (`verify_s137_anwesenheiten`) | dokumentierte Abweichungen | dokumentierte Abweichungen |

Die roten Punkte sind **keine Regressionen dieses Bereichs**, sondern dokumentierte Abweichungen
gegen die Odoo-11-Referenz beziehungsweise veraltete Erwartungen in den Pruefskripten:

- Abrechnung: `property_stock_customer` / `property_stock_supplier` entfallen in Odoo 18
  (in PROJECT_KNOWLEDGE als "entfallen" gefuehrt; das Pruefskript zaehlt sie als FEHL).
- Kundenverwaltung: das Skript erwartet `itk_crm` 18.0.1.5.7, installiert ist 18.0.1.5.10
  (Stand nach dem Helpdesk-Bereich).
- Anwesenheiten: 116 Home-Office-Zeilen und 1.221,72 Stunden sind die **dokumentierten** Werte
  (Checkliste und `docs/o11-o18-zeiterfassung-abnahme.md` nennen 116 Zeilen, 1.226 und 4.362
  Zeilen auf archivierten Projekten/Aufgaben); das Skript vergleicht gegen die Odoo-11-Werte.

Beleg fuer die Unberuehrtheit: seit Sitzungsbeginn (02.11.2026 13:00) gibt es **keine**
Schreibzugriffe auf `hr.leave` (0), `hr.attendance` (0), `account.analytic.line` (0) und
`project.task` (0). Geschrieben wurden nur die Modelle der Testprobe (Kontakte, Auftraege, Abos,
Rechnungen, Produkte, Leads - jeweils mit Ruecknahme).

---

## 13 Bewusste Abweichungen

| Abweichung | Begruendung |
|---|---|
| "Angebot zu Auftrag" und "Abo-Status aendern" schreiben den Status direkt | Odoo-11-Verhalten; `action_confirm` wuerde Bestelldatum und Folgebelege erzeugen (K2) |
| Preislistenwechsel auf bestaetigten Auftraegen wird von Odoo 18 abgelehnt | Odoo-18-Standardschutz, wird nicht ueberschrieben |
| Stichwortfelder erscheinen im Dialog als Tags statt als Unterliste | Bedienbarkeit (T1); Odoo 11 zeigte im selben Dialog eine Liste mit eigenem Dialog |
| Massenaktionen ohne Praefix "Massenverarbeitung (...)" | K6, kuerzere Namen, das Menue Massenverarbeitung stellt den Zusammenhang her |
| Konfiguration unter Einstellungen > Massenverarbeitung statt (wie Odoo 11) zusaetzlich unter Technisch | K5: Odoo 18 fuehrt die Aktionen als Server-Aktionen; das Menue bietet die gefilterte Sicht |
