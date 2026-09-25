# Odoo 11 -> Odoo 18: Bereich Verkauf, Teil 3, Schritt 1 (Formulare und Reiter)

Stand: 24.09.2026, Session 121. Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) wurde
ausschliesslich lesend gelesen. Keine Datenmigration, keine Aenderung an Produktivdaten, keine
Aenderung an Odoo 18 in diesem Schritt.

Umfang dieses Schritts: **Formularaufbau und Reiter** von `sale.order` und `sale.order.line`.
Buttons, Smart Buttons, Statuswechsel, Filter, Gruppierungen und Suche folgen in eigenen Schritten
(so von Anna vorgegeben) und sind hier bewusst nicht enthalten.

Werkzeuge:
- `scripts/analyse_verkauf_teil3_formulare.py` - liest Ansichten, Reiter, Gruppen und Felder
  (Odoo 11, Odoo 18 lokal und VM), schreibt `docs/_verkauf_teil3_formulare.json`
- `scripts/verify_s121_verkauf_teil3_reiter.py` - Abnahmepruefung, 64 OK / 0 FEHL
- `scripts/browser_verkauf_formular_reiter.py` - Browser-Abnahme auf der VM und lokal, 16 OK / 0 FEHL

## 1. Formularansichten

```
                                  Odoo 11    Odoo 18 (lokal = VM)
Formularansichten sale.order         12                 8
Formularansichten sale.order.line     0                 1   (Zeilenformular ist in Odoo 11
                                                            eingebettet, siehe Abschnitt 5)

Odoo 11 (Herkunft): sale, sale_management, sale_payment, website_sale, itk_sale_management (itk),
                    sale_crm, sale_stock, sale_timesheet, sale_order_line_number (Rechnungsform),
                    itk_subscription (Zeilenform)
Odoo 18 (Herkunft): sale, itk_sale_management (itk), sale_crm, sale_management,
                    sale_order_line_number, sale_pdf_quote_builder, sale_purchase, itk_subscription
```

Die Menuepunkte oeffnen die Standardansicht (Odoo 11 Aktionen 429/426 mit den Formularansichten
1031/1032, Odoo 18 Aktionen 429/430 mit 1222/1223). Kein Menuepunkt hat eine abweichende
Formularansicht, die in dieser Pruefung uebersehen werden koennte.

## 2. Reiter des Auftragsformulars

```
Odoo 11 (2 Reiter, keine Sichtbarkeitsregel auf den Seiten)
  1. "Auftragszeilen"          (Seitenname ohne Name, 5 Feldverweise: Zeilenliste + Zwischensumme,
                                Steuern, Gesamt, Geschaeftsbedingungen)
  2. "Weitere Informationen"   (19 Feldverweise)

Odoo 18 (4 Reiter-Knoten)
  1. "Auftragspositionen"      (page order_lines, immer sichtbar)
  2. "Optionale Produkte"      (page optional_products, invisible wenn Status nicht Angebot/gesendet)
  3. "Angebotsbauer"           (page pdf_quote_builder, invisible wenn nicht (Kunde und
                                is_pdf_quote_builder_available))
  4. "Weitere Informationen"   (page other_information, immer sichtbar)
```

Zuordnung:

| Odoo 11 | Odoo 18 | Bewertung |
|---|---|---|
| Auftragszeilen | Auftragspositionen | gleiche Stelle, anderer Wortlaut -> KLAERUNG (siehe Abschnitt 6) |
| (keine Entsprechung) | Optionale Produkte | Odoo-18-Zusatzfunktion (Assistent "Optionen hinzufuegen"), bleibt |
| (keine Entsprechung) | Angebotsbauer | Odoo-18-Zusatzfunktion (PDF-Angebotsbauer), bleibt |
| Weitere Informationen | Weitere Informationen | identisch |

### 2.1 Browser-Nachweis (echtes Rendering)

```
Instanz VM  (k001959vsx.ipax.at)    16 OK / 0 FEHL
Instanz lokal                        16 OK / 0 FEHL
Angebot/Entwurf   S00189 (sent)     sichtbare Reiter: Auftragspositionen, Optionale Produkte,
                                    Weitere Informationen (3) - Klick auf "Optionale Produkte"
                                    wechselt die Anzeige
bestaetigter Auftrag S00203 (sale)  sichtbare Reiter: Auftragspositionen, Weitere Informationen (2)
Gruppen im Reiter "Weitere Informationen" sichtbar: VERKAUF, RECHNUNGSSTELLUNG, VERSAND,
                                    NACHVERFOLGUNG
Fehlerzaehler                       0 JavaScript-Fehler, 0 RPC-Fehler
Screenshots                         Desktop\Odoo18-Abnahme-Session121\03_Reiter_*_vm.png,
                                    03_Reiter_*_lokal.png, 04_Reiter_Weitere_Informationen_*.png
```

Die beiden Zusatzreiter sind **regelabhaengig** und im Testbestand nicht bzw. nur im Angebot
sichtbar: "Optionale Produkte" nur bei Status Angebot/gesendet, "Angebotsbauer" nur wenn der
Kunde gesetzt ist und `is_pdf_quote_builder_available` gilt - dieses Feld ist im gesamten
Odoo-18-Testbestand False (lokal und VM geprueft), der Reiter "Angebotsbauer" erscheint daher in
der Praxis nicht. Das ist kein Fehler, sondern die Odoo-18-Standardlogik.

## 3. Reiter "Weitere Informationen" - Gruppen und Felder

```
Odoo 11                                    Odoo 18
Lieferadresse      (3)                     Versand            (2)
  warehouse_id, incoterm, picking_policy     commitment_date, expected_date
Information Umsatz (8)                     Verkauf            (8)
  user_id, tag_ids, team_id,                 user_id, team_id, require_signature, require_payment,
  is_abandoned_cart, cart_recovery_email_sent, prepayment_percent, reference, client_order_ref,
  client_order_ref, company_id,              tag_ids
  analytic_account_id
Abrechnung         (3)                     Rechnungsstellung  (3)
  date_order, fiscal_position_id,            show_update_fpos, fiscal_position_id, invoice_status
  invoice_status
Berichtswesen      (5)                     Nachverfolgung     (5)
  origin, campaign_id, medium_id,            origin, opportunity_id, campaign_id, medium_id,
  source_id, opportunity_id                  source_id
```

Bewertung je Feld:

| Odoo-11-Feld | Gruppe Odoo 11 | Gruppe Odoo 18 | Bewertung |
|---|---|---|---|
| user_id | Information Umsatz | Verkauf | verschoben (Gruppe umbenannt) |
| team_id | Information Umsatz | Verkauf | verschoben |
| tag_ids | Information Umsatz | Verkauf | verschoben |
| client_order_ref | Information Umsatz | Verkauf | verschoben |
| company_id | Information Umsatz | Hauptbereich | verschoben (Odoo-18-Standardplatz) |
| analytic_account_id | Information Umsatz | - | 0 Verwendungen, entfaellt (Ziel `analytic_distribution` auf der Zeile) |
| is_abandoned_cart | Information Umsatz | - | Website-Kaufvorgang, 0 Verwendungen |
| cart_recovery_email_sent | Information Umsatz | - | Website-Kaufvorgang, 0 Verwendungen |
| date_order | Abrechnung | Hauptbereich | verschoben (Odoo-18-Standardplatz) |
| fiscal_position_id | Abrechnung | Rechnungsstellung | gleich |
| invoice_status | Abrechnung | Rechnungsstellung | gleich |
| origin | Berichtswesen | Nachverfolgung | verschoben (Gruppe umbenannt) |
| opportunity_id, campaign_id, medium_id, source_id | Berichtswesen | Nachverfolgung | gleich |
| warehouse_id, incoterm, picking_policy | Lieferadresse | - | Felder aus `sale_stock` (Modul bewusst nicht installiert); die Gruppe heisst in Odoo 18 "Versand" und traegt andere Felder |

Zusaetzliche Felder der Odoo-18-Gruppen (bleiben, Zusatzfunktion): require_signature,
require_payment, prepayment_percent, reference (Gruppe Verkauf), show_update_fpos
(Rechnungsstellung), commitment_date, expected_date (Versand).

## 4. Hauptbereich (vor dem Notebook)

```
Odoo 11: 25 Feldverweise
  state, picking_ids, subscription_count, delivery_count, timesheet_count, project_ids,
  tasks_count, invoice_count, payment_transaction_count, name, partner_id,
  can_directly_mark_as_paid, sale_contact_id, administrative_contact_id, technical_contact_id,
  final_customer_id, product_category_id, partner_invoice_id, partner_shipping_id, validity_date,
  user_id, confirmation_date, pricelist_id, currency_id, payment_term_id

Odoo 18: 32 Feldverweise
  locked, authorized_transaction_ids, state, partner_credit_warning, duplicated_order_ids,
  subscription_count, invoice_count, purchase_order_count, name, partner_id, sale_contact_id,
  administrative_contact_id, technical_contact_id, final_customer_id, product_category_id,
  partner_invoice_id, partner_shipping_id, sale_order_template_id, subscription_management,
  validity_date, user_id, confirmation_date, date_order, has_active_pricelist,
  show_update_pricelist, pricelist_id, country_code, company_id, currency_id, tax_country_id,
  tax_calculation_rounding_method, payment_term_id
```

Jeder fachliche Odoo-11-Bestandteil des Hauptbereichs ist in Odoo 18 vorhanden (im Hauptbereich
oder, bei `date_order` und `company_id`, an der Odoo-18-Standardstelle im Hauptbereich).
Weggefallen sind ausschliesslich Zaehler und Schaltflaechen aus nicht installierten Modulen:
picking_ids, delivery_count (Lager), timesheet_count, project_ids, tasks_count (Zeiterfassung),
payment_transaction_count (Zahlungen, in Odoo 18 ueber `transaction_ids`), can_directly_mark_as_paid
(Website).

Odoo-18-Bestandteile ohne Odoo-11-Vorlage im Hauptbereich (bleiben): locked (Sperre),
authorized_transaction_ids, partner_credit_warning, duplicated_order_ids, purchase_order_count,
sale_order_template_id, subscription_management, has_active_pricelist, show_update_pricelist,
country_code, tax_country_id, tax_calculation_rounding_method.

### 4.1 ITK-Erweiterung des Formulars

Die ITK-Felder stehen in beiden Systemen im Hauptbereich des Auftragsformulars, direkt nach dem
Kundenfeld. In Odoo 18 setzt `itk_sale_management` (Ansicht "sale.order.form (itk)",
`inherit_id = sale.view_order_form`) genau diese Erweiterungen:

```
1. Feld partner_id ersetzt und danach eingefuegt: sale_contact_id, administrative_contact_id,
   technical_contact_id (jeweils domain [('parent_id','=',partner_id)]), product_category_id
2. Feld user_id und confirmation_date nach date_order eingefuegt
```

Wichtig (in der Ansicht dokumentiert): die Einfuegung erfolgt mit `position="after"` auf
`date_order`, weil Odoo 18 das Datumsfeld als getrenntes Label-Div plus Feld rendert;
`position="before"` hatte den Wert nach unten verschoben.

## 5. Auftragszeilen-Formular (sale.order.line)

In beiden Systemen hat das Zeilenformular **keinen Reiter** (kein Notebook) - es besteht nur aus
Feldern. Unterschied in der Ablage: Odoo 11 fuehrt **keine eigene Formularansicht** fuer
`sale.order.line` (0 Datensaetze in `ir.ui.view`), das Zeilenformular ist im Auftragsformular
eingebettet. Odoo 18 fuehrt genau eine: `sale.order.line.form.readonly`. Der Aufbau ist
gleichwertig; die Felder selbst sind in Teil 2 vollstaendig verglichen.

Die Zeilenbearbeitung im Auftragsformular erfolgt in beiden Systemen im Reiter 1 als eingebettete
Liste. Odoo 11 verwies dort auf 5 Felder, Odoo 18 auf die Zeilenliste mit zusaetzlichen
Odoo-18-Spalten (Details folgen im Schritt "Filter und Listenansichten").

## 6. Befunde und offene Entscheidungen

```
1. Wortlaut des ersten Reiters: ENTSCHIEDEN am 24.09.2026 (Anna) und umgesetzt - der Reiter heisst
   in Odoo 18 wieder "Auftragszeilen" (Odoo-11-Wortlaut). Umsetzung: itk_sale_management 18.0.1.2.0,
   eigene Ansicht an der Wurzel-View sale.view_order_form (priority 99,
   xpath //page[@name='order_lines'], position="attributes"). Lokal nach dem Modul-Upgrade geprueft;
   VM-Deploy und Browser-Abnahme folgen.
2. Der Reiter "Angebotsbauer" erscheint wegen is_pdf_quote_builder_available = False in keinem
   Testauftrag; der Reiter "Optionale Produkte" nur bei Angebot/gesendet. Beide bleiben als
   Odoo-18-Standardfunktion erhalten, die Sichtbarkeitsregeln sind oben dokumentiert.
3. ENTSCHIEDEN am 24.09.2026 (Anna): Die Odoo-11-Gruppe "Lieferadresse" wird nicht nachgebaut -
   ihre Felder stammen ausschliesslich aus `sale_stock` (bewusst nicht installiert). Die
   Odoo-18-Gruppe "Versand" bleibt mit ihren eigenen Feldern erhalten.
4. Felder, die in Odoo 18 den Platz gewechselt haben (date_order, company_id in den Hauptbereich),
   sind funktional gleichwertig; keine Anpassung vorgeschlagen.
```

## 7. Nachweise

```
scripts/verify_s121_verkauf_teil3_reiter.py   64 OK / 0 FEHL (Odoo 11 read-only, lokal und VM)
scripts/browser_verkauf_formular_reiter.py    VM 16 OK / 0 FEHL, lokal 16 OK / 0 FEHL (echte Klicks)
scripts/analyse_verkauf_teil3_formulare.py    Reiter, Gruppen und Felder je Instanz
Rohdaten                                      docs/_verkauf_teil3_formulare.json (gitignoriert)
Testdaten                                     keine angelegt, keine geaendert
Odoo 11 Prod                                  ausschliesslich lesend
```

**STATUS: TEIL 3, SCHRITT 1 (FORMULARE UND REITER) ANALYSIERT, LOKAL UND AUF DER VM IM BROWSER
ABGENOMMEN.** Keine Aenderung an Odoo 18. Offen in diesem Schritt: die Entscheidung zum Wortlaut
des ersten Reiters.

Naechste Schritte (ausdruecklich noch nicht bearbeitet): Buttons, Smart Buttons, Statuswechsel,
Filter, Gruppierungen, Suche.

## 8. Umsetzung der Entscheidungen (24.09.2026)

Auf Entscheidung von Anna (alle drei Punkte) umgesetzt; geaendert wurde ausschliesslich Odoo 18,
Odoo 11 Prod blieb read-only:

```
1. Reiterbeschriftung "Auftragspositionen" -> "Auftragszeilen"
   Modul: itk_sale_management 18.0.1.2.0 (vorher 18.0.1.1.0)
   Datei: addons/itk_sale_management/views/sale_order_views_reiterbezeichnung.xml
   Technik: eigene Ansicht an der WURZEL-View sale.view_order_form, priority 99,
            xpath //page[@name='order_lines'], position="attributes", string="Auftragszeilen"
   Nachweis lokal: get_views(de_DE) liefert als ersten Reiter "Auftragszeilen";
            Browser-Abnahme lokal 16 OK / 0 FEHL (Reiter sichtbar und anklickbar)
2. Gruppe "Lieferadresse": kein Nachbau (Felder aus sale_stock). Nur dokumentiert.
3. Zahlungsbedingung "14 Tage": nb_days von 0 auf 14 korrigiert (14 Tage nach Rechnungsdatum).
   Werkzeug: scripts/apply_verkauf_stammdaten.py --instanz lokal|vm [--pruefen] (idempotent)
   Nachweis lokal: 3 OK / 0 FEHL nach dem Schreiben, Prueflauf danach 3 OK / 0 FEHL;
            "Sofortige Zahlung" (nb_days 0) und "30 Tage" (nb_days 30) unveraendert
   Browser lokal: Zahlungsbedingung zeigt "100,000000 Prozent 14 Tage nach Rechnungsdatum",
            5 OK / 0 FEHL, Screenshot 05_Zahlungsbedingung_14_Tage_lokal.png
```

VM-Deploy und Browser-Abnahme der Punkte 1 und 3 folgen (siehe Checkliste 6.15).
