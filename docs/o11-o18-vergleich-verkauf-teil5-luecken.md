# Odoo 11 -> Odoo 18: Bereich Verkauf, Teil 5 Block 2 - Lückenanalyse

Stand: 29.09.2026, Session 121. Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) wurde
ausschliesslich lesend gelesen. Es wurde nichts in Odoo 18 geändert. Keine Datenmigration.

Werkzeuge:
`scripts/analyse_verkauf_teil5_luecken.py` (Hauptanalyse A-F),
`scripts/analyse_verkauf_teil5_luecken_detail.py`, `..._detail2.py`, `..._detail3.py`
(Detailklärung der Kandidaten), Rohdaten `docs/_verkauf_teil5_luecken*.json` (gitignoriert).

## 1. Vorgehen

```
A) Felder: alle in Odoo 11 belegten Felder von sale.order / sale.order.line gegen die
   Feldliste in Odoo 18 (lokal und VM)
B) Modelle und Menueziele: alle Aktionsmodelle der Odoo-11-Verkaufs-, Berichts- und CRM-Menues
   gegen die registrierten Modelle in Odoo 18
C) Automatismen: Server-Aktionen und automatisierte Aktionen auf Verkaufsmodelle
D) Mailvorlagen zu sale.order samt Betreff, Textumfang und angehaengtem Bericht
   (Odoo 11: report_template, Odoo 18: report_template_ids)
E) Stammdaten: die in Odoo 11 tatsaechlich verwendeten Werte (Zahlungsbedingungen, Preislisten,
   Teams, Steuerzuordnungen, Incoterms, UTM, Produkte, Steuern) und ihr Vorhandensein in Odoo 18
F) Berichte, Druckberichte und Ansichtstypen je Instanz
G) Module: installierte Module beider Systeme im Umfeld Verkauf/Lager/Website
H) Nutzungsspuren: Lagerbelege, gelieferte Mengen, Zeiterfassungen, Zahlungstransaktionen
```

## 2. Echte Lücke (1)

### 2.1 Lieferabwicklung (Lageranbindung des Verkaufs)

```
Belege aus Odoo 11 (read-only gemessen):
  installierte Module:  stock (installiert), stock_account (installiert),
                        sale_stock (installiert), delivery (nicht installiert)
  Auftraege mit Lager (warehouse_id):                  2.463 von 2.463
  Auftraege mit Lieferungen (picking_ids):               235
  Lagerbelege mit Verkaufsbezug (stock.picking):         238
  Auftragszeilen mit gelieferter Menge (qty_delivered):    1 (Rest ueber Auftragskopf)
  Auftragszeilen mit amt_invoiced/amt_to_invoice:      4.007
Gegenprobe Odoo 18 (lokal und VM):
  Module: stock, stock_account, sale_stock nicht installiert
  Felder sale.order.warehouse_id / picking_ids / delivery_count: nicht vorhanden
Folge: In Odoo 18 kann ein Verkaufsauftrag keine Lieferung/Lagerbuchung erzeugen. Die in
Odoo 11 genutzte Abwicklung "Auftrag -> Lieferung" ist damit nicht abgebildet.
Einordnung: Es handelt sich um eine strukturelle Luecke im Verkaufsprozess (nicht um ein
Datenmigrationsthema); behebbar durch Installation von stock, stock_account und sale_stock in
Odoo 18 (Struktur), ohne Datenuebernahme.
```

## 3. Geprüft und als Scheinbefund bzw. dokumentierte Abweichung eingeordnet (keine Lücke)

```
3.1 Felder sale.order.line: amt_invoiced -> amount_invoiced, amt_to_invoice -> amount_to_invoice,
    price_reduce -> price_reduce_taxexcl/taxinc; qty_invoiced/qty_to_invoice weiterhin vorhanden.
    Reine Umbenennungen der Odoo-Standardfelder; alle Werte sind in Odoo 18 berechnet verfuegbar.
3.2 Felder layout_category_id / layout_category_sequence: KORREKTUR 29.09.2026 - nicht "alle
    1.367 Werte 0", sondern: von 4.011 Auftragszeilen tragen genau 2 eine Sektion
    (layout_category_id id 1 "Dienstleistungen": Zeilen zu A-1900915 und A-1900906);
    layout_category_sequence ist immer 0. Das Modell sale.layout.category ist in Odoo 11 nicht
    registriert (totes Menue, bereits in Teil 1 dokumentiert) -> kein Nachbau noetig.
    Einzelheiten: docs/o11-o18-verkauf-r7-layout-category.md
3.3 Reklamationen (crm.claim, crm.claim.category, crm.claim.stage): Modelle existieren in Odoo 11,
    Datenbestand crm.claim = 0 (nur 3 Kategorien, 4 Phasen); die Menues waren bereits in Teil 1
    als tot dokumentiert -> keine Funktion in Verwendung.
3.4 Lead-Tags: crm.lead.tag (Odoo 11) ist in Odoo 18 crm.tag (vorhanden).
3.5 CRM-Statistik: crm.opportunity.report (Odoo 11) existiert in Odoo 18 nicht unter diesem Namen;
    CRM-Auswertungen laufen ueber crm.lead (Bereich Kundenverwaltung, dort abgehandelt).
3.6 report.all.channels.sales: bewusst nicht nachgebaut; in Teil 4 Schritt 2 als Bericht auf
    sale.report umgesetzt (Entscheidung Anna).
3.7 Mailvorlagen: Odoo 11 hatte "IT-Kommunal GmbH Angebot" sowie "Sales Order - Send by Email",
    letztere mit dem Bericht "Angebot / Auftrag ORG" (sale.report_itk_saleorder, also ITK-Layout).
    Odoo 18 haengt an "Verkauf: Angebot senden", "Auftragsbestätigung" und "Zahlung erledigt" den
    Bericht "PDF-Angebot" (sale.report_saleorder, Odoo-Standardlayout) an.
    Nutzungsspur Odoo 11: 2.271 E-Mail-Nachrichten auf Verkaufsauftraegen, aber 0 Anhaenge an
    Nachrichten (keine erzeugten Angebots-PDFs in der Korrespondenz); die 83 PDF-Anhaenge an
    Auftraegen sind Kundendokumente. Die Berichtsanhaenge-Funktion war also nicht in Verwendung.
    Ergebnis: dokumentierte Abweichung, kein Handlungsbedarf; die Odoo-18-Vorlagen bleiben
    unveraendert erhalten.
3.8 Stammdaten (Datenmigrationsthema, keine Strukturluecke):
    Zahlungsbedingungen: 3 verwendet; "14 Tage" und "Sofortige Zahlung" in Odoo 18 vorhanden,
      "30 Tage netto" fehlte in Odoo 18 -> am 29.09.2026 in Odoo 18 angelegt
      (siehe docs/o11-o18-verkauf-teil5-lageranbindung.md Abschnitt 7; Odoo-11-Konfiguration
      eine Zeile, 30 Tage ab Rechnungsdatum, 100 %). Keine Zuordnung zu Auftraegen oder Kunden.
    Preislisten: 25 verwendet, in Odoo 18 (Testbestand) nicht vorhanden.
    Produkte: 403 verwendet, 401 davon in Odoo 18 nicht vorhanden (Testbestand).
    Teams/Vertriebskanaele: 4 verwendet, alle in Odoo 18 vorhanden.
    Steuerzuordnungen, Incoterms, UTM-Quellen/-Medien/-Kampagnen: 0 Verwendungen in Odoo 11.
    Gemass Vorgabe werden Stammdaten nur dokumentiert und nicht ungefragt angelegt.
3.9 Automatismen: Odoo 11 hat keine Server-Aktion und keine automatisierte Aktion auf
    Verkaufsmodelle; die automatisierte Aktion "Interessent 'zur Verrechnung bereit'"
    (Lead/Verkaufschance) existiert in beiden Systemen. Keine Luecke.
3.10 Zeiterfassung (sale_timesheet): in Odoo 11 nicht in Verwendung
     (account.analytic.line mit Auftragspositionsbezug = 0) -> nicht erforderlich.
3.11 Online-Zahlung (sale_payment/website_sale): in Odoo 11 ohne Nutzung
     (payment.transaction = 0) -> nicht erforderlich; Odoo 18 bringt mit transaction_ids sogar
     eine zusaetzliche Funktion mit.
3.12 Weitere Odoo-11-Module ohne Entsprechung in Odoo 18 gehoeren zu anderen Bereichen oder sind
     Migrationshelfer: website_sale/website_form/website_partner/website_payment (Website),
     website_support* und bi_crm_claim (Helpdesk), itk_contract (Vertraege),
     itk_*_import und itk_data_setup/itk_fix_import (Einmal-Importhelfer der Migration),
     web_diagram/web_kanban_gauge/web_planner/web_settings_dashboard/web_tree_resize_column
     (Odoo-11-Web-Addons, in Odoo 18 durch Standardfunktionen ersetzt).
3.13 Berichte und Ansichten: Odoo 18 hat je Ansichtstyp gleich viele oder mehr Ansichten
     (Listenansichten 8 gegen 6, Kanban 3 gegen 1, Pivot 1 gegen 1, Graph 1 gegen 1,
     Kalender 2 gegen 1 mit Auftrags- und Aktivitaetenkalender) und vier statt drei
     Druckberichte; keine Luecke.
```

## 4. Ergebnis Block 2

```
Echte funktionale/strukturelle Luecken: 1
  Lieferabwicklung (sale_stock/stock/stock_account fehlen in Odoo 18, in Odoo 11 mit
  238 Lagerbelegen aus Verkaeufen in Verwendung)
Alle uebrigen Kandidaten: Scheinbefunde (Umbenennungen, tote Funktionen, 0 Verwendungen)
oder dokumentierte Abweichungen/Stammdatenthemen.
Odoo-18-Zusatzfunktionen: unveraendert vorhanden (u. a. vier Druckberichte, Auftrags- und
Aktivitaetenkalender, Angebots-/Auftragsvorlagen, transaction_ids).
```

## 5. Schliessung der Luecke (29.09.2026, Freigabe Anna)

Die Luecke wurde geschlossen: `stock`, `stock_account` und `sale_stock` sind in Odoo 18 installiert
(lokal und VM), die Felder `warehouse_id`, `picking_ids`, `delivery_count`, `picking_policy`,
`procurement_group_id` und `move_ids` sind vorhanden, und die Lieferfunktion ist im echten Browser
auf der VM geprueft (Testauftrag mit Lieferbeleg, danach bereinigt).

Details: `docs/o11-o18-verkauf-teil5-lageranbindung.md`.

```
Dabei noetige Nebenschritte (nur Odoo 18):
  itk_product 18.0.1.0.3: product.template.responsible_id auf die Odoo-18-Standarddefinition
    umgestellt (company_dependent, jsonb) - vorher Abbruch "cannot cast type integer to jsonb"
  Lokalisierung l10n_at auf der VM aktualisiert (Odoo verlangte das vor der Installation)
  project_stock auf der VM installiert (Datenrest einer Ansicht fuehrte zu einem Client-Fehler
    in der Lieferansicht; lokal war das Modul bereits installiert)
Ergebnis: RPC-Pruefung lokal 26 OK / 0 FEHL und VM 26 OK / 0 FEHL,
  Browserpruefung lokal 14 OK / 0 FEHL und VM 14 OK / 0 FEHL (0 JS-/RPC-Fehler),
  Regressionstest Verkauf und Abonnements 886 OK / 0 FEHL
Testdaten vollstaendig entfernt, keine Odoo-11-Daten uebernommen.
```

Offene Punkte in Block 2: keine.
