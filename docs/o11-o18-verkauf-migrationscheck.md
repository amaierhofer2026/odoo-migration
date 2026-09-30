# Gezielter Migrations-Check Bereich Verkauf: Risiken und Zuordnungen

Stand: 29.09.2026, Session 121. **Nur Analyse - es wurde nichts geaendert und nichts migriert.**
Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) ausschliesslich read-only gelesen,
Odoo 18 nicht veraendert.

Werkzeuge (alle nur lesend):
`scripts/analyse_verkauf_migrationscheck_felder.py` (Feldinventar und Belegung je Feld),
`scripts/analyse_verkauf_migrationscheck_aufbau.py` (Formularaufbau, Reiter, Gruppen, Spalten),
`scripts/pruefe_verkauf_migrationscheck_werte.py` (Auswahlwerte, Mengeneinheiten, Einzelfelder),
`scripts/baue_verkauf_migrationscheck_doku.py` (Detailtabelle).
Detailtabelle aller belegten Felder: `docs/o11-o18-verkauf-migrationscheck-felder.md`.
Rohdaten: `docs/_verkauf_migrationscheck_felder.json`, `docs/_verkauf_migrationscheck_aufbau.json`.

## 1. Umfang

```
sale.order       : 89 Felder, davon 39 mit Wert belegt, 50 ohne Wert
sale.order.line  : 53 Felder, davon 33 mit Wert belegt, 20 ohne Wert
Auswahlwerte, Mengeneinheiten, Waehrung und Firmenbezug geprueft (Wertebereich, nicht nur Existenz)
```

## 2. Echte Migrationsrisiken und fehlende Zuordnungen

### R1 - Mengeneinheiten (sale.order.line.product_uom): Rundung weicht ab, zwei Einheiten fehlen

```
Odoo 11: product.uom          Odoo 18: uom.uom   (Modell umbenannt)
in Odoo 11 tatsaechlich verwendet (read-only gezaehlt):
  Einheit(en)        2.334 Zeilen   -> in Odoo 18 vorhanden (id 1), ABER Rundung 0,01 statt 0,001
  ITK Einheit        1.622 Zeilen   -> in Odoo 18 vorhanden (id 29), ABER Rundung 0,01 statt 0,001
  GB                    45 Zeilen   -> in Odoo 18 NICHT vorhanden
  <Zahl> Gemeinden      10 Zeilen   -> 10 verschiedene Einheiten, in Odoo 18 NICHT vorhanden
Odoo 11 fuehrt 33 Einheiten, Odoo 18 (Testbestand) 29; 7 Namen stimmen ueberein.
Risiko 1: Die Zuordnung darf nicht ueber die ID erfolgen (IDs sind verschieden) - sie muss ueber
  den Namen laufen. Sonst zeigt jede Zeile eine falsche Einheit.
Risiko 2 (hoeher): Mengenrundung. Odoo 11 fuehrt "Einheit(en)" und "ITK Einheit" mit Rundung
  0,001, Odoo 18 fuehrt beide mit 0,01. Betroffen sind 3.956 von 4.011 Zeilen (98,6 %).
  Die gespeicherte Menge bleibt zwar erhalten, aber gerundete Anzeigen und daraus berechnete
  Werte koennen abweichen. Vor der Migration entscheiden: Rundung in Odoo 18 auf 0,001 setzen
  oder Abweichung bewusst akzeptieren.
Risiko 3: "GB" (45 Zeilen) und die 10 "<Zahl> Gemeinden"-Einheiten (je 1 Zeile) fehlen in
  Odoo 18 und muessen angelegt oder bewusst zugeordnet werden.
```

### R2 - sale.order.line.price_reduce: in Odoo 18 nicht mehr vorhanden

```
Odoo 11: price_reduce (float, 3.980 von 4.011 Zeilen belegt)
Odoo 18: Feld existiert nicht mehr; Nachfolger sind price_reduce_taxexcl und price_reduce_taxinc
  (beide monetary). In Odoo 11 sind diese beiden Felder ebenfalls vorhanden und mit 3.932 Zeilen
  belegt, aber als monetary/berechnet gefuehrt.
Erforderliche Transformationsregel: price_reduce nicht uebernehmen, sondern aus den Basisfeldern
  (price_unit, discount, tax_id, product_uom_qty, currency_id) neu berechnen lassen. Voraussetzung
  ist, dass diese Basisfelder migriert werden; dann ist das Ergebnis fachlich identisch.
```

### R3 - sale.order.state: Auswahlwert 'done' existiert in Odoo 18 nicht

```
Odoo 11 Schluessel: draft, sent, sale, done, cancel
Odoo 18 Schluessel: draft, sent, sale, cancel    (Sperre laeuft ueber Feld 'locked')
Wertebereich in Odoo 11 (read-only gemessen):
  sale 2.312 | cancel 147 | draft 5 | sent 0 | done 0
Folge: Es gibt derzeit KEINEN Auftrag im Zustand 'done' - die Sperre muss also nicht aus 'done'
  abgeleitet werden. Der Odoo-18-Assistent beim Import muss trotzdem beachten: das Setzen von
  state='sale' aktiviert 'locked' nicht automatisch (bereits dokumentiert).
```

### R4 - sale.order.note: Typ text -> html

```
Odoo 11: text, 2.442 von 2.464 Auftraegen belegt
Odoo 18: html
Erforderliche Transformationsregel: Inhalt beim Uebernehmen in HTML wandeln (Zeilenumbrueche,
  Sonderzeichen), sonst geht die Formatierung des Bemerkungstextes verloren. Der Dateninhalt
  selbst bleibt erhalten.
```

### R5 - sale.order.line.invoice_lines: Relation account.invoice.line -> account.move.line

```
Odoo 11: 1.863 von 4.011 Zeilen mit Rechnungszeilen verknuepft
Odoo 18: m2m auf account.move.line (Konten/Buchhaltung)
Erforderliche Transformationsregel: Die Verknuepfung kann nur gesetzt werden, wenn die
  Rechnungen selbst migriert werden und der Zuordnungsschluessel (Rechnungsnummer/Position)
  eindeutig ist. Ohne Rechnungsmigration bleibt die Verknuepfung leer - dann sind die
  Odoo-18-Felder amount_invoiced/amount_to_invoice und invoice_status neu berechnet und koennen
  vom Odoo-11-Wert abweichen. Das ist der einzige Fall, in dem ein Betrag fachlich abweichen kann.
```

### R6 - sale.order.tag_ids: crm.lead.tag -> crm.tag

```
Odoo 11: 1 von 2.464 Auftraegen hat Schlagworte
Erforderliche Transformationsregel: Zuordnung ueber den Tag-Namen (nicht ueber die ID).
Aufwand/Kritikalitaet: sehr klein (1 Datensatz).
```

### R8 - Rechnungsbezogene Betraege (amt_invoiced / amt_to_invoice): in Odoo 18 nicht gespeichert

```
Odoo 11: amt_invoiced   (float, gespeichert) - 1.669 von 4.011 Zeilen mit Wert, davon 1.664 groesser 0
Odoo 11: amt_to_invoice (float, gespeichert) - 1.950 von 4.011 Zeilen mit Wert, davon 1.906 groesser 0
Odoo 18: amount_invoiced / amount_to_invoice existieren, sind aber NICHT gespeichert
  (store = False, berechnet) - der Odoo-11-Wert kann nicht uebernommen werden.
Beispiel Odoo 11: amt_invoiced 18,30 bei price_subtotal 15,25 (Betrag inklusive Steuer).
Folge: In Odoo 18 werden diese Werte aus den verknuepften Rechnungen neu berechnet. Ist die
  Rechnung nicht (oder nicht eindeutig) zugeordnet, steht dort 0 bzw. ein anderer Wert als in
  Odoo 11 - der sichtbare Unterschied ist dann fachlich erklaerbar, aber vorhanden.
Voraussetzung fuer identische Werte: Rechnungen migrieren und ueber invoice_lines
  (account.invoice.line -> account.move.line) korrekt verknuepfen (siehe R5).
```

### R7 - sale.order.line.layout_category_id: belegte Altlast, in Odoo 18 nicht vorhanden

```
Odoo 11: 2 von 4.011 Zeilen tragen einen Wert; das Modell sale.layout.category ist in Odoo 11
  nicht registriert (totes Menue "Reportlayout Kategorien").
Einordnung: bewusst nicht zu uebernehmen. Die 2 Zeilen verlieren nur ein nicht auswertbares Feld.
```

## 3. Kein Risiko, aber bewusst abweichend (dokumentiert)

```
incoterm: Relation stock.incoterms -> account.incoterms (Modellwechsel). Belegung Odoo 11: 0.
route_id (Auftragszeile): Odoo 11 stock.location.route -> Odoo 18 stock.route (umbenannt). Belegung: 0.
analytic_account_id: in Odoo 11 vorhanden (Belegung 0), im Odoo-18-Formular nicht dargestellt;
  Auswertung laeuft in Odoo 18 ueber die Analytische Verteilung.
is_abandoned_cart / cart_recovery_email_sent: Website-Felder, in Odoo 11 in 0 Auftraegen gesetzt,
  in Odoo 18 nicht im Formular (Website-Funktion in Odoo 11 nicht genutzt).
display_type: Abschnitts-/Notizzeilen. Odoo 11 hat 0 Zeilen ohne Produkt, Odoo 18 fuehrt
  line_section/line_note - kein Uebernahmefall vorhanden.
currency_id: Odoo 11 nur EUR (Stichprobe 400 von 400 Auftraegen EUR), Odoo 18 fuehrt EUR - kein
  Waehrungsumrechnungsrisiko (Hinweis: ITK-Auftraege werden in EUR gefuehrt).
Firmen: Odoo 11 alle 2.464 Auftraege der Firma IT-Kommunal GmbH - keine Mehrfirmenaufteilung
  beim Auftrag, damit kein Konflikt mit firmenabhaengigen (jsonb) Feldern auf Auftragsebene.
Betragsfelder: amount_untaxed, amount_tax, amount_total, price_subtotal, price_total, price_tax,
  qty_invoiced, qty_to_invoice, price_reduce_taxexcl, price_reduce_taxinc sind in Odoo 18 ebenfalls
  gespeichert (compute mit store=True) - beim Schreiben der Positionen berechnet die Odoo-18-Logik
  sie aus Menge, Preis, Rabatt, Steuern und Waehrung neu; das Ergebnis ist fachlich identisch.
  Ausnahme mit echtem Risiko: amount_invoiced / amount_to_invoice - in Odoo 18 NICHT gespeichert
  (siehe R8).
```

## 4. Formular: Reiter und Gruppen (Ursache des unterschiedlichen Aussehens)

```
Odoo 11: 2 Reiter  Auftragszeilen | Weitere Informationen
Odoo 18: 4 Reiter  Auftragszeilen | Optionale Produkte | Angebotsbauer | Weitere Informationen
Odoo-18-Zusatzfunktionen (Optionale Produkte, Angebotsbauer) bleiben erhalten.

Gruppen im Reiter "Weitere Informationen":
  Odoo 11 "Lieferadresse"       -> Odoo 18 "Lieferung"
  Odoo 11 "Information Umsatz"  -> Odoo 18 "Verkauf"
  Odoo 11 "Abrechnung"          -> Odoo 18 "Rechnungsstellung"
  Odoo 11 "Berichtswesen"       -> Odoo 18 "Nachverfolgung"
  Odoo 18 ergaenzt in "Lieferung": incoterm_location, commitment_date, expected_date,
    effective_date, delivery_status (Zusatzfunktionen)
```

## 5. Felder des Reiters „Weitere Informationen" (Odoo 11, 19 Felder) nach Odoo 18

| Odoo-11-Feld | Odoo-11-Gruppe | Odoo 18: Reiter | Odoo 18: Gruppe |
|---|---|---|---|
| warehouse_id | Lieferadresse | Weitere Informationen | Lieferung |
| incoterm | Lieferadresse | Weitere Informationen | Lieferung |
| picking_policy | Lieferadresse | Weitere Informationen | Lieferung |
| user_id | Information Umsatz | Weitere Informationen | Verkauf |
| tag_ids | Information Umsatz | Weitere Informationen | Verkauf |
| team_id | Information Umsatz | Weitere Informationen | Verkauf |
| client_order_ref | Information Umsatz | Weitere Informationen | Verkauf |
| company_id | Information Umsatz | Kopfbereich des Formulars (unsichtbar) | - |
| analytic_account_id | Information Umsatz | nicht im Formular (Odoo 11 ohne Wert) | - |
| is_abandoned_cart | Information Umsatz | nicht im Formular (Website-Feld) | - |
| cart_recovery_email_sent | Information Umsatz | nicht im Formular (Website-Feld) | - |
| date_order | Abrechnung | Kopfbereich („Auftragsdatum", ausserhalb Entwurf) | - |
| fiscal_position_id | Abrechnung | Weitere Informationen | Rechnungsstellung |
| invoice_status | Abrechnung | Weitere Informationen | Rechnungsstellung |
| origin | Berichtswesen | Weitere Informationen | Nachverfolgung |
| campaign_id | Berichtswesen | Weitere Informationen | Nachverfolgung |
| medium_id | Berichtswesen | Weitere Informationen | Nachverfolgung |
| source_id | Berichtswesen | Weitere Informationen | Nachverfolgung |
| opportunity_id | Berichtswesen | Weitere Informationen | Nachverfolgung |

```
Zusaetzlich in Odoo 18 in "Weitere Informationen" (Zusatzfunktionen, bleiben erhalten):
  Verkauf: require_signature, require_payment, prepayment_percent, reference
  Lieferung: incoterm_location, commitment_date, expected_date, effective_date, delivery_status,
             show_json_popover, json_popover
  Rechnungsstellung: show_update_fpos
```

## 6. Sichtbare Spalten der Auftragszeilen (Ursache der unterschiedlichen Tabelle)

```
Odoo 11 (12 Spalten):
  product_id | order_id | order_partner_id | name | salesman_id | product_uom_qty |
  qty_delivered | qty_invoiced | qty_to_invoice | product_uom | route_id | price_subtotal

Odoo 18 (11 Spalten):
  order_id | order_partner_id | name | salesman_id | product_uom_qty |
  qty_delivered | qty_invoiced | qty_to_invoice | product_uom | price_subtotal | currency_id

Unterschiede:
  Odoo 11 zeigt product_id (eigene Produktspalte) und route_id (Lagerroute des Produkts)
  Odoo 18 zeigt currency_id (Waehrung ueber das Betrags-Widget), product_id und route_id nicht
  Odoo 18 fuehrt die Zeilen im Formular ueber das Widget "sol_o2m" (Modus list,kanban);
    Odoo 11 nutzte mode="tree,kanban" ohne dieses Widget
  Beide Systeme bieten die Positionsliste als Liste und als Kanban (kein Unterschied)

Fachliche Folge: In Odoo 18 werden Produkt und Lagerroute nicht als eigene Spalten gefuehrt; die
Route steuert die Beschaffung (in Odoo 11 nur 0 Zeilen mit route_id belegt), das Produkt steht im
Feld "name" (Beschreibung). Kein Datenverlust - die Felder bleiben am Datensatz vorhanden
(product_id, product_uom, product_uom_qty, discount, price_unit, tax_id).
```

## 7. Auftragsliste und Kopfbereich des Formulars

```
Spalten der Auftragsliste
  Odoo 11 (11): message_needaction | name | confirmation_date | partner_id | partner_invoice_id |
                sale_contact_id | user_id | amount_untaxed | currency_id | invoice_status | state
  Odoo 18 (23): message_needaction | currency_id | name | date_order | confirmation_date |
                commitment_date | expected_date | partner_id | partner_invoice_id |
                sale_contact_id | user_id | activity_ids | team_id | company_id | amount_untaxed |
                amount_tax | tag_ids | state | effective_date | delivery_status | invoice_status |
                client_order_ref | validity_date
  -> Odoo 18 zeigt 12 zusaetzliche Spalten (Zusatzfunktionen, bleiben erhalten).
  -> Achtung Anzeige: In Odoo 18 steht an Stelle von "confirmation_date" zusaetzlich "date_order";
     beide Felder existieren (Bestaetigungsdatum bleibt erhalten).

Kopfbereich des Formulars (ausserhalb der Reiter)
  Odoo 11: name, partner_id, partner_invoice_id, partner_shipping_id, payment_term_id,
           pricelist_id, validity_date, user_id, sale_contact_id, currency_id, state, amount-Felder
           ueber Smart Buttons (invoice_count, delivery_count, timesheet_count, tasks_count,
           project_ids, picking_ids, subscription_count, payment_transaction_count,
           can_directly_mark_as_paid), administrative_contact_id, technical_contact_id,
           final_customer_id, product_category_id, confirmation_date
  Odoo 18: dieselben ITK-Felder plus Zusatzfunktionen (locked, date_order, company_id,
           tax_country_id, has_active_pricelist, show_update_pricelist, sale_order_template_id,
           subscription_management, purchase_order_count, duplicated_order_ids,
           authorized_transaction_ids, partner_credit_warning, country_code)
  -> ITK-eigene Felder (administrative_contact_id, technical_contact_id, final_customer_id,
     product_category_id, sale_contact_id, confirmation_date, subscription_count) sind in
     Odoo 18 im Kopfbereich vorhanden.
```

## 8. Gesamtbild

```
Echte Risiken:  8
  R1 Mengeneinheiten (Zuordnung ueber Namen, Rundung 0,001 gegen 0,01, fehlende Einheiten)
  R2 price_reduce (Feld entfallen, Nachfolger price_reduce_taxexcl/taxinc)
  R3 Zustand 'done' (Auswahlwert entfaellt; aktuell 0 Auftraege betroffen)
  R4 note text -> html
  R5 invoice_lines (account.invoice.line -> account.move.line)
  R6 tag_ids (crm.lead.tag -> crm.tag, 1 Datensatz)
  R7 layout_category_id (Altlast, 2 Zeilen, bewusst nicht zu uebernehmen)
  R8 amt_invoiced / amt_to_invoice (in Odoo 18 nicht gespeichert, 1.669 und 1.950 Zeilen)
Klaerung vor der Datenmigration noetig: Rundungsentscheidung bei "Einheit(en)"/"ITK Einheit",
  Anlage oder Zuordnung der Einheiten "GB" und der 10 "<Zahl> Gemeinden"-Einheiten,
  Umgang mit den rechnungsbezogenen Betraegen (R5/R8)
Ohne Risiko (in Odoo 11 ohne Wert oder fachlich gleich): incoterm, route_id, analytic_account_id,
  Website-Felder, Abschnitts-/Notizzeilen, Waehrung, Firmenbezug, uebrige Betrags- und Mengenfelder
Kein Handlungsbedarf in Odoo 18: alle geprueften Zusaetzfunktionen bleiben erhalten
```

**Es wurde nichts geaendert und nichts migriert.** Odoo 11 ausschliesslich read-only.
