# R7 - layout_category_id / layout_category_sequence: belegte Altlast ohne Ziel

Stand: 29.09.2026, Session 121. **Nur Analyse.** Odoo 11 ausschliesslich read-only.
In Odoo 18 wurde nichts geaendert - es war keine Aenderung erforderlich.

## 1. Ausgangslage Odoo 11 (gemessen)

```
sale.order.line.layout_category_id      many2one -> sale.layout.category  Anzeige "Sektion"
sale.order.line.layout_category_sequence integer                            Anzeige "Reihenfolge Auftragszeilen"
Das Modell sale.layout.category ist in Odoo 11 NICHT registriert:
  ir.model-Eintrag existiert nicht; "Lesetest" und fields_get schlagen mit KeyError fehl.
  Die Datenbanktabelle/der Datensatz ist aber vorhanden: read_group loest die Zuordnung zu
  id 1 mit der Bezeichnung "Dienstleistungen" auf.

Belegung:
  Auftragszeilen gesamt                                 4.011
  layout_category_id gesetzt (nicht NULL)                   2
  layout_category_id != 0                                   0
  layout_category_sequence != 0                             0
  Abschnittszeilen (Zeilen ohne Produkt)                    0
```

## 2. Die zwei betroffenen Zeilen (Volltext)

```
Auftrag A-1900915 (03.10.2019, Verkaufsauftrag, Kunde FH Campus Wien)
  Zeile id 3318 | One PlaceMail (sharepoint AddOn) | 1,0 x 202,91 = 202,91 EUR
  Sektion "Dienstleistungen" (id 1) | Sequenz 0
Auftrag A-1900906 (05.09.2019, Verkaufsauftrag, Kunde Oesterreichischer Staedtebund)
  Zeile id 3296 | Support Staedtebund-Academy | 1,0 x 3.000,00 = 3.000,00 EUR
  Sektion "Dienstleistungen" (id 1) | Sequenz 0
Beide Zeilen sind normale Produktzeilen; eine Sequenz wurde nie gesetzt.
```

## 3. Verwendung in den Vorlagen

```
Odoo 11:
  sale.order.form            Feld nur fuer die Gruppe "sale.group_sale_layout" sichtbar
  account.invoice(.line)     Feld ebenfalls nur fuer diese Gruppe
  sale.report_saleorder_document (Standard)  iteriert t-foreach="page" t-as="layout_category",
      Abschnittsueberschrift nur bei Gruppe sale.group_sale_layout
  sale.report_itk_saleorder_document (ITK-Vorlage, im Verkauf verwendet)
      Der komplette Abschnittsblock ist AUSKOMMENTIERT
      (<!--<t t-foreach="page" t-as="layout_category">--> ...) - es wird keine Sektion gedruckt
  sale.report_invoice_layouted  ebenfalls Standardverhalten (Gruppe)
Odoo 18:
  Felder layout_category_id / layout_category_sequence existieren nicht mehr.
  Abschnitte laufen ueber sale.order.line.display_type: 'line_section' / 'line_note'
  sale.report_saleorder_document (Standard)  verarbeitet display_type/line_section
  itk_reports.report_itk_saleorder_document (ITK-Vorlage)  KEINE Abschnittslogik (0 Treffer) -
      genau wie die Odoo-11-ITK-Vorlage
  Im Testbestand gibt es keine Abschnitts- oder Notizzeile (0 von 28 Zeilen).
```

## 4. Einordnung

```
Die Funktion ist in Odoo 11 nachweislich stillgelegt:
  - das Modell sale.layout.category ist nicht registriert (nicht benutzbar)
  - die ITK-Druckvorlage druckt keine Sektionen (auskommentiert)
  - von 4.011 Zeilen tragen 2 eine Zuordnung, ohne Sequenz und ohne sichtbare Wirkung
  - Abschnittszeilen gibt es im Bestand nicht
In Odoo 18 ist die Entsprechung fuer Abschnitte vorhanden (display_type), sie wird vom
Standardbericht verarbeitet und bleibt als Zusatzfunktion erhalten.
```

## 5. Transformationsregel (vorbereitet)

```
layout_category_id       -> bewusst NICHT zu uebernehmen (Feld existiert in Odoo 18 nicht;
   Zuordnung zeigt auf ein nicht registriertes Modell; ITK-Vorlage druckt keine Sektionen)
layout_category_sequence -> bewusst NICHT zu uebernehmen (Sequenz nie gesetzt, Feld entfaellt)
Auswirkung: 2 Auftragszeilen verlieren eine Zuordnung, die in keinem Druck und keiner Auswertung
   des Verkaufs sichtbar wird. Kein Datenwert geht verloren, keine Odoo-18-Funktion entfaellt.
```

## 6. Nachweise

```
Odoo 11: fields_get und ir.model.fields, ir.model-Suche nach sale.layout.category,
  Leseversuche auf das Modell (KeyError), search_count/read_group fuer die Belegung,
  Detailabruf der 2 Zeilen samt Auftrag und Kunde, Durchsicht der QWeb-Vorlagen
  (Archivinhalte von sale.report_saleorder_document, report_invoice_layouted und der
   ITK-Vorlagen - Abschnittsblock auskommentiert)
Odoo 18: fields_get (Felder fehlen), display_type-Auswahl, Durchsicht der Vorlagen
  (Standardvorlage mit display_type, ITK-Vorlage ohne Abschnittslogik), Bestand 0 Abschnittszeilen
Bestand unveraendert: lokal 18 Auftraege / 28 Zeilen / 13 Produkte, VM 20 / 29 / 13
Keine Datenmigration, keine Aenderung an Odoo 18.
```

## 7. Entscheidungen von Anna (29.09.2026) und Status

```
a) Transformationsregel BESTAETIGT: layout_category_id und layout_category_sequence werden
   spaeter bewusst NICHT migriert. Begruendung:
     - nur 2 von 4.011 Auftragszeilen betroffen
     - beide nur mit der Kategorie "Dienstleistungen"
     - layout_category_sequence wurde nicht fachlich genutzt (immer 0)
     - die im Verkauf verwendete ITK-Druckvorlage hat die Sektion nicht ausgegeben
       (Abschnittsblock auskommentiert)
     - Odoo 18 verwendet stattdessen die Standardlogik mit Abschnitts- und Notizzeilen
     - es geht kein fachlich relevanter Inhalt verloren
b) BESTAETIGT: Fuer A-1900915 und A-1900906 werden KEINE kuenstlichen Odoo-18-Abschnittszeilen
   erzeugt. Die beiden historischen Zuordnungen werden nur dokumentiert.
c) Dokumentationskorrektur BESTAETIGT und umgesetzt: Der fruehere Vermerk "alle 1.367 belegten
   Werte 0" war falsch. Korrekt: genau 2 Auftragszeilen trugen layout_category_id mit der
   Sektion "Dienstleistungen" (id 1); layout_category_sequence hatte keinen relevanten Wert
   (immer 0). Die Korrektur ist in den betroffenen Dokumenten eingetragen.

STATUS: R7 ABGESCHLOSSEN (29.09.2026) - analysiert (read-only in Odoo 11), Transformationsregel
  festgehalten, Entscheidungen eingetragen, Dokumentationskorrektur umgesetzt.
  Es war KEINE Aenderung an Odoo 18 erforderlich; keine Datenmigration.
Der Bereich Verkauf bleibt bis zur Vorbereitung von R8 weiterhin NICHT endgueltig abgeschlossen.
```
