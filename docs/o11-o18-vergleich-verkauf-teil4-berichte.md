# Odoo 11 -> Odoo 18: Bereich Verkauf, Teil 4, Schritt 2 (Verkaufsberichte und Druckberichte)

Stand: 28.09.2026, Session 121. Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) wurde
ausschliesslich lesend gelesen (RPC). Geprueft: Odoo 18 lokal (`odoo18_test`) und VM
(`k001959vsx.ipax.at`). Analysewerkzeug: `scripts/analyse_verkauf_teil4_berichte.py`,
Rohdaten `docs/_verkauf_teil4_berichte.json` (gitignoriert).

**In diesem Schritt wurde nichts umgebaut** - nur Bestandsaufnahme, Vergleich, Mapping und
Umsetzungsvorschlaege.

## 1. Menuepunkte im Berichtswesen

| Odoo 11 | Aktion | Modell | Odoo 18 | Aktion | Modell |
|---|---|---|---|---|---|
| Verkauf/Berichtswesen/Verkauf | 423 Statistik Verkaufsauftraege | `sale.report` | Verkauf/Berichtswesen/Verkauf | 416 Verkaufsanalyse | `sale.report` |
| Verkauf/Berichtswesen/Verkaufsauftraege aller Kanaele | 424 Verkaufsauftraege aller Kanaele | `report.all.channels.sales` | **fehlt** | - | - |
| Verkauf/Berichtswesen/Vertriebskaenale | 171 Vertriebskaenale | `crm.team` | Kundenverwaltung/Berichtswesen/Vertriebskanaele (Entscheidung Teil 1) | 171 Vertriebskanaele | `crm.team` |
| - | - | - | Verkauf/Berichtswesen/Kunden | 419 Verkaufsanalyse nach Kunden | `sale.report` |
| - | - | - | Verkauf/Berichtswesen/Produkte | 418 Verkaufsanalyse nach Produkten | `sale.report` |
| - | - | - | Verkauf/Berichtswesen/Vertriebsmitarbeiter | 417 Verkaufsanalyse nach Vertriebsmitarbeitern | `sale.report` |

Weitere Odoo-11-Aktionen auf `sale.report`: 435/436 "Angebotsstatistik" (graph,
`search_default_order_month`), 618/619 "Verkauf" (pivot,graph, ohne Default-Kontext).
Weitere Odoo-18-Aktionen: 420/422 Verkaufsanalyse (Listen-/Pivot-Sicht, 422 mit Team-Kontext),
421 Angebotsstatistik (graph,list).

Der Odoo-11-Menuepunkt "Verkaufsauftraege aller Kanaele" hat in Odoo 18 also **keine
Entsprechung**; die uebrigen Odoo-11-Berichtsmenues sind vorhanden.

## 2. Odoo 11: Modell und Bericht "Verkaufsauftraege aller Kanaele"

### 2.1 Modell `report.all.channels.sales`

```
Herkunft: SQL-Sicht des Moduls sale (nicht ITK-eigen), 18 Felder
Felder:
  name                char        Auftragsreferenz
  date_order          datetime    Auftragsdatum
  partner_id          many2one    Partner (res.partner)
  user_id             many2one    Verkaeufer (res.users)
  team_id             many2one    Vertriebskanal (crm.team)
  product_id          many2one    Produkt
  product_tmpl_id     many2one    Produktvorlage
  categ_id            many2one    Produktkategorie
  product_qty         float       Produktmenge
  price_subtotal      float       Zwischensumme
  price_total         float       Total
  pricelist_id        many2one    Preisliste
  analytic_account_id many2one    Kostenstelle
  country_id          many2one    Partnerland
  company_id          many2one    Unternehmen
  id / display_name / __last_update (technisch)
Korn: eine Zeile je Auftragsposition (Auftragszeile)
```

### 2.2 Ansichten, Filter, Gruppierungen, Default-Kontext

```
Pivotansicht 1024 "report.all.channels.sales.pivot":  name (Zeile), price_total (Mass)
Suchansicht 1025 "report.all.channels.sales.search":
  Suchfeld date_order
  Filter    "Aktuelles Verkaufsjahr" (name=current_year)
            Domain [('date_order','>=',time.strftime('%Y-01-01'))]
  Gruppierung "Vertriebskanal" (name=team_id) -> {'group_by':'team_id'}
Aktion 424 "Verkaufsauftraege aller Kanaele":
  res_model report.all.channels.sales, view_mode pivot, Domain leer
  Kontext {'search_default_team_id': 1, 'search_default_current_year': 1}
  Menue Verkauf/Berichtswesen/Verkaufsauftraege aller Kanaele
Gespeicherte Filter (ir.filters): keine
```

Der Menueaufruf zeigte also eine Pivot-Tabelle: Auftragsreferenzen als Zeilen, **Vertriebskanal
als Spalte** (aus dem Default-Kontext), Mass **Total** (`price_total`), und durch den zweiten
Default-Filter nur das **aktuelle Verkaufsjahr**.

### 2.3 Tatsaechliche Nutzung / Datenbestand (Odoo 11 Prod, lesend gemessen)

```
Saetze gesamt        3775   = genau die Auftragszeilen nicht stornierter Auftraege
                             (sale.order.line gesamt 4010, davon storniert 235 -> 3775)
Zeitraum             2018-02-01 bis 2026-09-28 (Produktivsystem waechst taeglich)
Verteilung Kanal     Vertriebskaene (Intern) 3747, Interne Weitergabe 20,
                     Persoenlicher Kontakt 5, Newsletter 3
Belegung Felder      pricelist_id 3775/3775, team_id 3775/3775, product_id 3775/3775,
                     product_qty 3726/3775, analytic_account_id 0/3775 (nie verwendet)
Auftragszeilen je Jahr: 2024 = 233, 2025 = 641, 2026 = 406
Vergleich            sale.report (O11) hat 3987 Saetze inkl. storniert; 2026 = 406 (identisch,
                     weil stornierte Zeilen 2026 nicht vorkommen)
```

## 3. Odoo 11: Modell `sale.report` (Menue "Verkauf" = Statistik Verkaufsauftraege)

```
31 Felder, u. a. date (Auftragsdatum), confirmation_date (Bestaetigung am), state,
  team_id, user_id, partner_id, categ_id, product_id, product_tmpl_id, pricelist_id,
  price_subtotal, price_total, product_uom_qty, qty_delivered, qty_invoiced, qty_to_invoice,
  amt_invoiced, amt_to_invoice, nbr, volume, weight, warehouse_id, country_id, company_id
Pivotansicht 1016: team_id (Spalte), confirmation_date (Zeile), price_subtotal (Mass)
Graphansicht 1017: date (Zeile), price_subtotal (Mass)
Suchansicht 1018:
  Filter "Dieses Jahr" (name=year, unsichtbar) [date zwischen 01.01. und 31.12. des Jahres]
  Filter "Angebote" (Quotations), "Verkauf" (Sales: state not in draft/cancel/sent)
  Gruppierungen Verkaeufer (user_id), Vertriebskanal (team_id), Land des Partner (country_id),
  Kunde (partner_id), Produktkategorie (categ_id), Status (state), Unternehmen (company_id),
  Auftragsmonat (date:month)
Aktion 423: view_mode graph,pivot, Domain leer,
  Kontext {'search_default_Sales':1, 'group_by_no_leaf':1, 'group_by':[]}
Weitere Odoo-11-Aktionen: 435/436 "Angebotsstatistik" (graph, search_default_order_month),
  618/619 "Verkauf" (pivot,graph, ohne Default-Kontext)
Gespeicherte Filter: 4 benutzerspezifische ("Nach Produkt", "Nach Verkaeufern",
  "Nach Verkaufsteam", "Vertriebsprozess" = aktuelles Jahr ohne stornierte, gruppiert nach Status)
Datenbestand: 3987 Saetze, 2018-02-01 bis 2026-09-28; nach Status sale 3747, cancel 235, draft 5
```

## 4. Odoo 18: Status quo

```
Menue Verkauf/Berichtswesen: Kunden, Produkte, Verkauf, Vertriebsmitarbeiter
  -> alle auf sale.report (Verkaufsanalyse), view_mode graph,pivot (416 zusaetzlich list,form)
  -> Aktion 416 hat Domain [('state','!=','cancel')] und
     Kontext {'search_default_Sales':1, 'group_by':[], 'search_default_filter_order_date':1}
Ein Bericht "Verkaufsauftraege aller Kanaele" und das Modell report.all.channels.sales
  existieren in Odoo 18 NICHT.
sale.report in Odoo 18: 41 Felder, darunter date, state, team_id, user_id, partner_id,
  categ_id, product_id, product_tmpl_id, pricelist_id, product_uom_qty,
  price_subtotal (monetary), price_total (monetary), nbr, qty_delivered, volume,
  line_invoice_status, country_id, company_id, industry_id
  NICHT vorhanden: date_order (heisst jetzt date), confirmation_date, analytic_account_id,
  product_qty (heisst jetzt product_uom_qty)
Ansichten: Pivot 1201 (team_id Spalte, date Zeile, product_uom_qty Mass),
  Graph 1202 (date, product_uom_qty), Graph 1203/1204 (Kreis/Balken ohne Felder)
Suchansicht 1206:
  Filter "Datum" (name=year, unsichtbar, date=date, default_period=year)      <- aktuelles Jahr
  Filter "Angebote" (Quotations), "Verkaufsauftraege" (Sales)
  Filter "filter_date" (date=date, default_period=month)                      <- Zeitraumauswahl
  Filter "filter_order_date" (unsichtbar, letzte 365 Tage)
  Filter "Abzurechnen", "Komplett abgerechnet" (line_invoice_status)
  Gruppierungen Vertriebsmitarbeiter (user_id), Verkaufsteam (team_id), Kunde (partner_id),
  Kundenland (country_id), Kundenbranche (industry_id), Produkt (product_tmpl_id),
  Produktvariante (product_id), Produktkategorie (categ_id), Status (state), Auftragsdatum (date)
Testdatenbestand: lokal 28 Saetze, VM 29 Saetze (keine Migration, nur Testdaten)
```

## 5. Vergleich und Mapping

### 5.1 Felder des Kanaele-Berichts

| Odoo 11 `report.all.channels.sales` | Odoo 18 `sale.report` | Bewertung |
|---|---|---|
| name (Auftragsreferenz) | name | gleich |
| date_order (Auftragsdatum) | date | umbenannt, gleiche Funktion |
| partner_id | partner_id | gleich |
| user_id | user_id | gleich |
| team_id (Vertriebskanal) | team_id (Verkaufsteam) | gleich, Label differiert |
| product_id / product_tmpl_id | product_id / product_tmpl_id | gleich |
| categ_id | categ_id | gleich |
| product_qty (Produktmenge) | product_uom_qty (Bestellte Menge) | umbenannt, gleiche Funktion |
| price_subtotal / price_total | price_subtotal / price_total (monetary) | gleich |
| pricelist_id | pricelist_id | gleich |
| analytic_account_id (Kostenstelle) | nicht vorhanden | in Odoo 11 auf **0** von 3775 Zeilen belegt -> entfaellt (Odoo 18 fuehrt Kostenstellen je Zeile als analytic_distribution) |
| country_id / company_id | country_id / company_id | gleich |
| - | zusaetzlich state, nbr, qty_delivered, line_invoice_status, industry_id, volume u. a. | Odoo-18-Zusatz |

Korn identisch: eine Zeile je Auftragsposition.

### 5.2 Filter, Gruppierungen, Default-Kontext

| Odoo 11 (Kanaele-Bericht) | Odoo 18 (sale.report) | Bewertung |
|---|---|---|
| Filter "Aktuelles Verkaufsjahr" `[('date_order','>=',Jahresanfang)]` | Filter "Datum" (name=`year`, `date=date`, `default_period="year"`), unsichtbar, per Kontext aktivierbar | gleichwertig (Odoo-18-Mechanik der Datumsfilter) |
| Gruppierung "Vertriebskanal" (`group_by team_id`) | Gruppierung "Verkaufsteam" (`group_by team_id`) | gleiche Gruppierung, Label differiert |
| Default-Kontext `{'search_default_team_id': 1, 'search_default_current_year': 1}` | uebertragbar auf `{'search_default_sales_channel': 1, 'search_default_year': 1}` | gleichwertig, in dieser Form neu anzulegen |
| Pivot Mass `price_total`, Zeile `name`, Spalte Kanal | Pivot 1201 hat Mass `product_uom_qty`, Zeile `date`, Spalte `team_id` | Mass/Zeile ueber `pivot_measures` bzw. eigene Pivotansicht einstellbar |
| Kein Ausschluss stornierter Auftraege im Modell selbst (Modell enthaelt nur nicht stornierte) | Aktion 416 schliesst ueber Domain `[('state','!=','cancel')]` aus | gleichwertig ueber Domain |
| - | zusaetzlich: Zeitraumauswahl (Monat/Jahr), Abzurechnen, Komplett abgerechnet, Branche, Produktvariante | Odoo-18-Zusatz, bleibt |

### 5.3 Druckberichte

| Odoo 11 | Berichtsname | Odoo 18 | Bewertung |
|---|---|---|---|
| Angebot/Auftrag | `sale.report_itk_saleorder` | ITK-Angebot/Auftrag (`itk_reports.report_itk_saleorder`) | uebernommen |
| Angebot / Auftrag ORG | `sale.report_itk_saleorder` (gleicher Bericht, zweiter Menueeintrag) | Angebot/Auftrag (`sale.report_saleorder_raw`) | funktional abgedeckt |
| Proformarechnung | `sale.report_itk_saleorder_proforma` | PRO-FORMA-Rechnung (`sale.report_saleorder_pro_forma`) | uebernommen |
| - | - | PDF-Angebot (`sale.report_saleorder`) | Odoo-18-Zusatz, bleibt |

Alle drei in Odoo 11 vorhandenen Druckberichte sind in Odoo 18 vorhanden (im Klicktest aus
Teil 3, Schritt 2: alle vier Eintraege im Drucken-Menue sichtbar). **Kein Handlungsbedarf.**

## 6. Bewertung: `sale.report` kann die Funktion uebernehmen

`report.all.channels.sales` ist eine reine SQL-Sicht auf Auftragszeilen mit Auftrags-, Kunden-,
Verkaeufer-, Kanal-, Produkt- und Preisangaben. Genau diese Angaben liefert `sale.report` in
Odoo 18 (Korn, Felder, Filter, Gruppierungen). Der einzige echte Unterschied ist die
Voreinstellung des Berichts (Default-Gruppierung nach Kanal, Filter aktuelles Jahr, Pivot mit
`price_total`), also reine Konfiguration.

**Empfehlung: das Odoo-11-Modell `report.all.channels.sales` NICHT nachbauen.** Statt dessen den
Menuepunkt auf `sale.report` neu anlegen und konfigurieren. Das entspricht der Vorgabe, kein
veraltetes Modell zu kopieren, und haelt die Odoo-18-Berichtsmechanik (Zeitraumauswahl,
dynamische Masse) nutzbar.

## 7. Konkreter Umsetzungsvorschlag (noch nicht umgesetzt)

Modul `itk_sale_management`, neue Datei `views/sale_report_views_kanaele.xml`, Version 18.0.1.6.0:

```xml
1) Eigene Pivotansicht (Abbildung des Odoo-11-Pivots: Auftragsreferenz als Zeile, Total als Mass)
   record itk_sale_management.view_sale_report_pivot_kanaele
     <pivot string="Verkaufsauftraege aller Kanaele">
       <field name="name" type="row"/>
       <field name="price_total" type="measure"/>
     </pivot>

2) Neue Aktion
   record itk_sale_management.action_sale_report_all_channels  (ir.actions.act_window)
     name        "Verkaufsauftraege aller Kanaele"
     res_model   sale.report
     view_mode   "pivot,graph,list"
     domain      [('state', '!=', 'cancel')]        (wie Odoo 11: ohne stornierte Auftraege)
     context     {'search_default_sales_channel': 1,      (Gruppierung nach Kanal)
                  'search_default_year': 1,               (aktuelles Verkaufsjahr)
                  'pivot_measures': ['price_total']}      (Mass Total wie Odoo 11)
     view_ids    pivot -> eigene Pivotansicht, graph -> sale.report.graph, list -> sale.report.list

3) Neuer Menuepunkt
   menuitem itk_sale_management.menu_sale_report_all_channels
     name     "Verkaufsauftraege aller Kanaele"
     parent   sale.menu_sale_report            (Verkauf/Berichtswesen)
     action   action_sale_report_all_channels
     sequence direkt nach "Verkauf"
```

Ergaenzend moeglich (zur Entscheidung): ein eigener Suchfilter in Odoo-11-Wortlaut
"Vertriebskanal" (`group_by team_id`) zusaetzlich zum Odoo-18-Filter "Verkaufsteam", damit der
Menueaufruf auch sprachlich dem Odoo-11-Bericht entspricht. Odoo-18-Filter bleiben unberuehrt.

Erwartetes Ergebnis (Werte aus dem Testbestand ableitbar): Pivot mit einer Zeile je Auftrag,
Spalten je Vertriebskanal, Mass Total, Beschraenkung auf das laufende Verkaufsjahr und ohne
stornierte Auftraege.

## 8. Offene Entscheidungen fuer Anna

```
1. Label der Gruppierung: Odoo-11-Wortlaut "Vertriebskanal" zusaetzlich anbieten oder die
   Odoo-18-Gruppierung "Verkaufsteam" verwenden? (Empfehlung: zusaetzlich anbieten)
2. Mass im Pivot: "Total" (price_total, wie Odoo 11) als Vorgabe setzen? (Empfehlung: ja,
   zusaetzlich bleibt "Bestellte Menge" als waehlbares Mass erhalten)
3. Zeile im Pivot: Auftragsreferenz (wie Odoo 11) als Vorgabe, Auftragsdatum weiterhin waehlbar?
4. Mit dem Menuepunkt unter Verkauf/Berichtswesen einverstanden (statt eines eigenen
   Obermenues)?
5. Die vier Odoo-18-Berichtsmenues (Kunden, Produkte, Verkauf, Vertriebsmitarbeiter) bleiben
   unveraendert - einverstanden?
```

**STATUS: TEIL 4, SCHRITT 2 - Analyse, Mapping und Umsetzungsvorschlag fertig.
Es wurde nichts umgebaut; Umsetzung erst nach Freigabe.**
