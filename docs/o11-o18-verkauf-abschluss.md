# Odoo 11 -> Odoo 18: Abschluss Bereich Verkauf

Stand: 29.09.2026, Session 121
Status: **VERKAUF VOLLSTAENDIG FUNKTIONSFAEHIG UND VOLLSTAENDIG MIGRATIONSVORBEREITET**

Vergleichsbasis: Odoo 11 Prod (`https://portal.it-kommunal.at`, DB `ITK_V1_a`) - **ausschliesslich
lesend** verwendet, keine Schreib-, Aenderungs- oder Upgrade-Operation.
Zielsystem: Odoo 18 lokal (`localhost:8069`, DB `odoo18_test`) und VM `k001959vsx.ipax.at`
(Docker `odoo18`, DB `odoo18_test`, Odoo Server 18.0-20260817).

## 1. Auftrag und Umfang

Der Bereich Verkauf wurde in fuenf Teilen vollstaendig gegen Odoo 11 geprueft und in Odoo 18
funktionsfaehig aufgebaut:

```
Teil 1  Grundstruktur: Module, Menuebaum, Menueziele, Nutzungszahlen
Teil 2  Feldinventar sale.order / sale.order.line (belegte Felder, Datentypen, Zweck)
Teil 3  Formulare, Reiter, Buttons, Smart Buttons, Statuswechsel, Suche/Filter/Gruppierungen
Teil 4  Ansichten (Liste, Kanban, Kalender, Pivot, Graph), Auftragskalender, Berichte,
        Druckberichte
Teil 5  Abschlusspruefung: Block 1 Regression, Block 2 Lueckenanalyse (1 echte Luecke
        geschlossen), Stammdatennachtrag "30 Tage netto", Block 3 Browser-Gesamtabnahme auf
        der VM, Block 4 Abschlussmarkierung (dieses Dokument)
```

## 2. Umgesetzte Anpassungen in Odoo 18

```
itk_sale_management   18.0.1.6.0
  Bericht "Verkaufsauftraege aller Kanaele" (Pivot auf sale.report, Aktion, Menuepunkt unter
    Verkauf -> Berichtswesen, Filter "Aktuelles Verkaufsjahr", Gruppierung Vertriebskanal,
    Domain: nur nicht stornierte Auftraege)
  Auftragsansichten, Such-/Feldbezeichnungen, Kalender- und Reiteranpassungen aus Teil 1-4
itk_product           18.0.1.0.3
  product.template.responsible_id auf die Odoo-18-Standarddefinition umgestellt
  (company_dependent/jsonb) - Ursache war der Abbruch "cannot cast type integer to jsonb"
  bei der Installation von stock
Neu installiert (nur Struktur, keine Datenuebernahme):
  stock 18.0.1.1, stock_account 18.0.1.1, sale_stock 18.0.1.0
  auf der VM zusaetzlich project_stock (Datenrest einer Ansicht), l10n_at aktualisiert
Neu angelegt (Stammdatum, ohne Zuordnung):
  Zahlungsbedingung "30 Tage netto" (100 %, 30 Tage ab Rechnungsdatum)
Nicht installiert (bewusst, weil in Odoo 11 ohne Nutzung):
  delivery, sale_timesheet, sale_payment/website_sale
```

## 3. Bewusste Abweichungen von Odoo 11

| Thema | Odoo 11 | Odoo 18 | Begruendung / Entscheidung |
|---|---|---|---|
| Bericht „Verkaufsauftraege aller Kanaele“ | Modell `report.all.channels.sales` (3.775 Zeilen) | Pivot auf `sale.report`, Aktion + Menuepunkt neu | Modell nicht blind nachgebaut; `sale.report` uebernimmt die fachliche Funktion (Entscheidung Anna) |
| Standardfilter Auftragsliste | kein Vorgabefilter | Filter „Meine Angebote“ aktiv | Odoo-18-Standard bleibt erhalten (dokumentiert, nicht abgeschaltet) |
| Gespeicherte Filter | 16 (15 benutzerindividuell, 2 als Benutzerstandard) | nicht uebernommen | Empfehlung wie Session 115: keine Uebernahme von Benutzerfiltern |
| Proformavorlage | `sale.report_itk_saleorder_proforma` | „PRO-FORMA-Rechnung“ (Odoo-Standard) | kein zusaetzlicher Menueeintrag; ITK-Vorlage bleibt dokumentierte Alt-/Zusatzvorlage (Entscheidung Anna 29.09.2026) |
| Druckberichte | 3 (Angebot/Auftrag, ITK-Layout, Proforma) | 4 (Angebot/Auftrag, ITK-Angebot/Auftrag, PDF-Angebot, PRO-FORMA-Rechnung) | Odoo-18-Zusatzfunktion bleibt erhalten |
| Gruppe im Auftragsformular | „Versand“ | „Lieferung“ | Odoo-18-Standardbezeichnung nach Installation von sale_stock |
| Sperre des Auftrags | Zustand `done` | Feld `locked` | Odoo-18-Logik; Storno nur entsperrt ueber Assistenten `sale.order.cancel` |
| Auftragszeilen-Felder | `amt_invoiced`, `amt_to_invoice`, `price_reduce` | `amount_invoiced`, `amount_to_invoice`, `price_reduce_taxexcl/taxinc` | reine Odoo-Standardumbenennungen, Werte berechnet verfuegbar |
| Zahlungsbedingung „30 Tage netto“ | Zeile mit `value=balance` (0 %), Option `day_after_invoice_date` | neu angelegt: 100 % (`percent`), 30 Tage, `days_after` | die Odoo-11-Auswahl `balance` existiert in Odoo 18 nicht; fachlich gleichwertig |
| Sichtbare Bezeichnungen | Stufe, Verkaeufer, Vertriebskanal, Ablehnungsgrund | beibehalten | Wortlaute bleiben erhalten, wo fachlich passend; Standardfilter nicht umbenannt |

## 4. Bewusst nicht migrierte Punkte (kein Funktionsverlust)

```
Tote Odoo-11-Menues/Funktionen ohne Inhalt:
  Reportlayout Kategorien (sale.layout.category in Odoo 11 nicht registriert, alle 1.367 Werte 0)
  Reklamationen (crm.claim: 0 Datensaetze)
  Berichtsmenue "Vertriebskanaele" (Odoo-11-Altlast)
Ohne Nutzung in Odoo 11 (deshalb nicht erforderlich):
  Zeiterfassung am Auftrag (account.analytic.line mit Auftragspositionsbezug = 0)
  Online-Zahlung (payment.transaction = 0)
  Berichtsanhaenge an Mailvorlagen (0 erzeugte Angebots-PDFs in der Korrespondenz)
Datenmigration (nicht Teil der Strukturmigration):
  Preislisten 25 und Produkte 403 aus Odoo 11 sind in Odoo 18 (Testbestand) nicht angelegt;
  Stammdaten werden nur dokumentiert, eine Datenmigration erfolgt je Bestand nach freigegebener
  Regel. Zahlungsbedingung "30 Tage netto" wurde als Strukturdatum angelegt, ohne Zuordnung
  zu Auftraegen oder Kunden.
```

## 5. Rahmenbedingungen (eingehalten)

```
Keine Datenmigration:
  Es wurden keine Odoo-11-Datensaetze nach Odoo 18 uebernommen. Alle waehrend der Pruefung
  angelegten Testdaten (Auftraege, Lagerbelege, Testprodukte) wurden entfernt; der Bestand ist
  nach jedem Prueflauf unveraendert.
Odoo 11 ausschliesslich read-only:
  Alle Zugriffe nutzten die vorhandenen Lesewerkzeuge (RPC-Lesen, Menue-/Feldinventare,
  Zaehlungen). Keine Schreib-, Aenderungs-, Loesch- oder Upgrade-Operation in Odoo 11.
Odoo-18-Zusatzfunktionen erhalten:
  Standardfilter, Standardansichten, zusaetzliche Druckberichte, Auftrags- und
  Aktivitaetenkalender, Massenbearbeitung, Zusammenfuehren von Auftraegen, Zusatzfelder
  (u. a. transaction_ids) bleiben unveraendert vorhanden.
```

## 6. Endstand und Nachweise

```
Module (lokal und VM identisch):
  itk_sale_management 18.0.1.6.0, itk_product 18.0.1.0.3, itk_reports 18.0.1.0.0,
  itk_subscription 18.0.1.2.1, sale_management 18.0.1.0, sale 18.0.1.2,
  stock 18.0.1.1, stock_account 18.0.1.1, sale_stock 18.0.1.0, account 18.0.1.3

Bestand (Strukturpruefung, keine Produktivdaten):
  lokal  18 Auftraege, 28 Auftragszeilen, 13 Produkte, 15 Kunden, 0 Lagerbelege
  VM     20 Auftraege, 29 Auftragszeilen, 13 Produkte, 15 Kunden, 0 Lagerbelege
  Zahlungsbedingungen 12 (inklusive "30 Tage netto"), Verkaufsteams 8
  (VM fuehrt gegenueber lokal mehr Abonnements - dokumentierte Bestandsabweichung)

View-Gesundheit (lokal und VM, alle vorhandenen Ansichtstypen je Modell ladbar):
  sale.order (activity, calendar, form, graph, kanban, list, pivot, search),
  sale.order.line, stock.picking (inkl. project_stock-Erweiterung), product.template,
  product.product, account.move, res.partner, account.payment.term, product.pricelist,
  crm.team - 0 Fehler; Server-Logs ohne Meldungen zu ungueltigen Ansichten

Pruefungen (Werkzeug -> Ergebnis):
  scripts/abschluss_verkauf_regression.py            886 OK / 0 FEHL (11 Prueflaeufe, lokal+VM)
  scripts/abschluss_verkauf_browser_gesamtabnahme.py 243 OK / 0 FEHL (11 Browser-Werkzeuge, VM)
                                                     - in Block 4 auf dem Endstand wiederholt,
                                                     gleiches Ergebnis, Bestand unveraendert
  scripts/browser_verkauf_gesamtdurchgang.py          43 OK / 0 FEHL (15 Stationen, VM)
  scripts/abschluss_verkauf_endstand.py               Endstand ohne offene View-Fehler
  JavaScript-Fehler 0, RPC-Fehler 0 in allen Browserpruefungen
  Screenshots: Desktop\Odoo18-Abnahme-Session121\ (Teil-, Druckberichte-, Lieferungs- und
  gesamtdurchgang-Ordner)
```

## 7. Ergebnis

```
Der Bereich Verkauf ist in Odoo 18 vollstaendig funktionsfaehig:
  Menues, Angebote/Auftraege, Formulare und Reiter, Buttons und Smart Buttons, Statuswechsel,
  Suche/Filter/Gruppierungen, Listen-, Kanban-, Kalender-, Pivot- und Graphansichten,
  Auftragskalender, Verkaufsberichte inklusive "Verkaufsauftraege aller Kanaele", Druckberichte,
  Zahlungsbedingungen, Lager-/Lieferfunktion aus dem Verkaufsauftrag, relevante Stammdaten
  - alles im echten Browser auf der Abnahmeumgebung geprueft.

Der Bereich Verkauf ist vollstaendig migrationsvorbereitet:
  alle in Odoo 11 tatsaechlich verwendeten Funktionen sind abgebildet (1 echte Luecke war die
  Lageranbindung und wurde geschlossen), alle Abweichungen sind dokumentiert, es bestehen
  keine offenen funktionalen oder strukturellen Punkte.
```

Offene Punkte: keine.
Nicht gestartet (Vorgabe): weitere Module (Einkauf, Lager, Buchhaltung, CRM-Abschluss).

Dokumentation dieses Abschlusses:
`docs/o11-o18-verkauf-abschluss.md` (dieses Dokument), Teil-Dokumente
`docs/o11-o18-vergleich-verkauf-teil1..teil5*.md`,
`docs/o11-o18-vergleich-verkauf-teil4-berichte.md`,
`docs/o11-o18-vergleich-verkauf-teil4-druckberichte.md`,
`docs/o11-o18-vergleich-verkauf-teil5-luecken.md`,
`docs/o11-o18-verkauf-teil5-lageranbindung.md`,
`docs/o11-o18-verkauf-teil5-block3-browserabnahme.md`.
