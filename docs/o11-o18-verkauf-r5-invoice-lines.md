# R5 - invoice_lines / Modellwechsel account.invoice.line -> account.move.line

Stand: 29.09.2026, Session 121. **Nur Analyse.** Odoo 11 ausschliesslich read-only.
In Odoo 18 wurden zwei Testrechnungen/-auftraege angelegt und vollstaendig entfernt;
es war **keine Aenderung an Odoo 18 erforderlich**.

## 1. Ausgangslage Odoo 11 (gemessen)

```
Feld sale.order.line.invoice_lines      many2many -> account.invoice.line
  Verknuepfungstabelle: sale_order_line_invoice_rel
  Spalten:              order_line_id / invoice_line_id
Gegenfeld account.invoice.line.sale_line_ids  many2many -> sale.order.line
  dieselbe Tabelle sale_order_line_invoice_rel, Spalten invoice_line_id / order_line_id
sale.order.invoice_ids und invoice_count sind in Odoo 11 NICHT gespeichert (berechnet) -
  es gibt dort also keinen eigenen Wert zu uebernehmen.

Umfang im Bestand:
  Auftragszeilen gesamt                                 4.011
  Zeilen mit Rechnungszeilen (invoice_lines)            1.863
  Zeilen mit qty_invoiced > 0                           1.863   (deckungsgleich)
  verknuepfte Rechnungszeilen                           1.863
  davon verschiedene Rechnungen                         1.201
    Kundenrechnungen (out_invoice)                      1.194
    Kundengutschriften (out_refund)                         7
    Status: bezahlt 1.168 | offen 22 | Entwurf 11
    Jahre:  2019: 47 | 2020: 119 | 2021: 201 | 2022: 182 | 2023: 146 | 2024: 141 |
            2025: 135 | 2026: 219
  betroffene Auftraege (mindestens eine verknuepfte Zeile)  1.198
```

## 2. Odoo 18: Gegenstueck (gemessen und getestet)

```
Feld sale.order.line.invoice_lines   many2many -> account.move.line, store=True, readonly=False
Feld account.move.line.sale_line_ids many2many -> sale.order.line, store=True, readonly=True
Beide nutzen DIESELBE Verknuepfungstabelle wie Odoo 11:
  sale_order_line_invoice_rel, Spalten order_line_id / invoice_line_id
  -> nur das Zielmodell der Rechnungszeile hat sich geaendert
     (account.invoice.line -> account.move.line); Tabellenstruktur bleibt identisch.
sale.order.invoice_ids / invoice_count sind auch in Odoo 18 nicht gespeichert (berechnet).

Test in Odoo 18 (Testrechnung, danach entfernt):
  Verknuepfung von der Auftragszeile aus gesetzt   -> Rechnungszeile zeigt sie in der
      Gegenrichtung (account.move.line.sale_line_ids)
  Verknuepfung von der Rechnungszeile aus gesetzt  -> Auftragszeile zeigt sie (invoice_lines)
  Verknuepfung geloescht                           -> beide Seiten leer
  Auswirkung auf berechnete Felder der Auftragszeile: qty_invoiced reagiert sofort (1,0),
      amount_invoiced bleibt 0,0, solange die Rechnung im Entwurf ist
```

## 3. Transformationsregel (vorbereitet)

```
invoice_lines wird NICHT als Wert uebernommen, sondern als Verknuepfung hergestellt:
  - Zuordnung ueber die Verknuepfungstabelle sale_order_line_invoice_rel
    (Auftragszeilen-ID <-> Rechnungszeilen-ID), nachdem beide Seiten migriert sind
  - Schluessel der Zuordnung: Rechnungsnummer + Position der Rechnungszeile,
    NICHT die Odoo-11-IDs (die IDs sind in Odoo 18 andere)
  - die Verknuepfung kann von jeder Seite gesetzt werden; Odoo pflegt die Gegenseite automatisch
Voraussetzung: Die Rechnungen (account.move und account.move.line) werden migriert und den
  Auftragszeilen zugeordnet. Ohne Rechnungsmigration:
    - keine Verknuepfung setzen (sonst zeigen die IDs ins Leere)
    - Folge: invoice_status bleibt/ergibt 'no' und amount_invoiced / amount_to_invoice = 0
      (Kopplung an R8) - die Abweichung zu Odoo 11 ist dann dokumentiert und fachlich erklaerbar
Einordnung nach der Statusliste: "Transformationsregel erforderlich" (Modellwechsel), mit
  identischer Verknuepfungstabelle. Keine Aenderung an Odoo 18 erforderlich.
```

## 4. Nachweise

```
Odoo 11: fields_get und ir.model.fields (Feld, Relation, Verknuepfungstabelle, Spalten),
  search_count fuer Zeilen/Rechnungen, vollstaendige Auswertung aller 1.863 verknuepften
  Rechnungszeilen samt Rechnungstyp, Status und Jahr
Odoo 18: fields_get und ir.model.fields (gleiche Tabelle, gleiche Spalten), Schreibtest in beide
  Richtungen mit Testrechnung, Auswirkung auf qty_invoiced/amount_invoiced, danach Bereinigung
Bestand nach der Analyse: lokal 18 Auftraege / 28 Zeilen / 13 Produkte / 0 Lagerbelege,
  37 Rechnungen (unveraendert), 0 Auftragszeilen mit Rechnungsbezug
Keine Datenmigration, keine Aenderung an Odoo 18.
```

## 5. Entscheidungen von Anna (29.09.2026) und Status

```
a) Transformationsregel BESTAETIGT: invoice_lines wird spaeter NICHT als Feldwert 1:1
   uebernommen. Die Beziehung zwischen sale.order.line und der Rechnungszeile wird nach der
   Migration beider Seiten ueber die Tabelle sale_order_line_invoice_rel wiederhergestellt.
   Die Zuordnung darf NICHT ueber Odoo-11-IDs erfolgen, sondern ueber einen stabilen fachlichen
   Schluessel, z. B. Rechnungsnummer, Position/Reihenfolge der Rechnungszeile und - falls
   noetig - zusaetzlich Produkt bzw. Auftragszeilenbezug zur Absicherung.
   Ist eine Zuordnung nicht eindeutig, wird sie nicht gesetzt und der Fall vorgelegt.
b) Voraussetzung BESTAETIGT: Die Verknuepfung darf erst hergestellt werden, wenn die
   zugehoerigen Rechnungen und Rechnungszeilen in Odoo 18 vorhanden und eindeutig zuordenbar
   sind. Werden Rechnungen spaeter nicht migriert, wird auch keine historische
   invoice_lines-Verknuepfung gesetzt.
c) Umfang BESTAETIGT: Die historischen Verknuepfungen (1.863 Zeilen aus 1.201 Rechnungen)
   sollen grundsaetzlich wiederhergestellt werden, sofern die zugehoerigen Rechnungen migriert
   werden. Ziel ist, dass qty_invoiced, Rechnungsstatus und die Zuordnung der Auftragszeilen
   danach fachlich korrekt aus den verknuepften Rechnungszeilen berechnet werden.
   Ausdrueckliche Vorgabe: qty_invoiced, amount_invoiced und invoice_status NICHT direkt aus
   Odoo 11 uebernehmen - Odoo 18 berechnet diese Werte aus den migrierten Rechnungsdaten.

STATUS: R5 ABGESCHLOSSEN (29.09.2026) - analysiert (read-only in Odoo 11, Verknuepfungs- und
  Schreibtests in Odoo 18), Transformationsregel und Voraussetzungen festgehalten,
  Entscheidungen eingetragen. Es war KEINE Aenderung an Odoo 18 erforderlich; Testrechnung und
  Testauftrag vollstaendig entfernt, keine Datenmigration.
Der Bereich Verkauf bleibt bis zur Vorbereitung der Risiken R6 bis R8 weiterhin NICHT endgueltig
abgeschlossen.
```
