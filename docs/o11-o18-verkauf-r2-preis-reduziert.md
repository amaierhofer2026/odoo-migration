# R2 - price_reduce: Zuordnung Odoo 11 -> Odoo 18 (Analyse und Transformationsregel)

Stand: 29.09.2026, Session 121. **Nur Analyse.** Odoo 11 ausschliesslich read-only, keine
Datenmigration. In Odoo 18 wurde fuer die Wertebestaetigung je ein Testauftrag mit Testzeilen
angelegt und danach wieder entfernt (Bestand unveraendert). Keine bestehende Odoo-18-Funktion
wurde veraendert.

Werkzeug: `scripts/pruefe_verkauf_r2_preis_reduziert.py` (nur lesend)

## 1. Ausgangslage (gemessen)

```
Odoo 11 (product.uom.sale.order.line):
  price_reduce          float    gespeichert  "Reduzierter Preis"              3.980 von 4.011 belegt
  price_reduce_taxexcl  monetary gespeichert  "Reduzierter Preis zzgl. USt."  3.932 belegt
  price_reduce_taxinc   monetary gespeichert  "Reduzierter Preis inkl. USt."  3.932 belegt
Odoo 18:
  price_reduce          FELD EXISTIERT NICHT MEHR
  price_reduce_taxexcl  monetary gespeichert  "Preisminderung exkl. Steuern"
  price_reduce_taxinc   monetary gespeichert  "Preisminderung inkl. Steuern"

Der Odoo-11-Wert price_reduce ist exakt der Einzelpreis nach Rabatt:
  price_reduce = price_unit * (1 - Rabatt/100), gerundet auf 2 Nachkommastellen.
  Nachweis: In allen 4.011 Auftragszeilen trifft diese Formel zu (0 Abweichungen).
```

## 2. Wertevergleich (Belege)

```
1. price_reduce gegen price_reduce_taxexcl (Odoo 11, alle Zeilen):
   3.960 Zeilen mit Menge > 0: Wert innerhalb 0,01 gleich (3.959 exakt, 1 Zeile mit 0,01 Differenz)
   51 Zeilen mit Menge 0: Odoo 11 fuehrt in price_reduce_taxexcl selbst bereits 0,00
2. Der eine 0,01-Fall (Auftragszeile id 5173, Auftrag A-2400078, Gemeinde Waldbach-Moenichwald):
   Preis 23,00, Rabatt 33,33 %, Menge 2
     Odoo 11: price_reduce 15,33 | price_reduce_taxexcl 15,34 | price_subtotal 30,67
   Ursache: price_reduce rundet den Einzelpreis (15,3341 -> 15,33), price_reduce_taxexcl
   rechnet aus der Zwischensumme (30,67 / 2 = 15,335 -> 15,34). Die beiden Odoo-11-Felder
   weichen hier also selbst um 0,01 voneinander ab - kein Migrationsverlust.
3. Neuberechnung in Odoo 18 (sechs Testzeilen, danach entfernt):
     Preis 94,00 / Rabatt 0 %  / Menge 1  -> taxexcl 94,00  taxinc 112,80  (Odoo 11 id 6544: 94,00)
     Preis 94,00 / Rabatt 0 %  / Menge 3  -> taxexcl 94,00  taxinc 112,80
     Preis 61,00 / Rabatt 75 % / Menge 1  -> taxexcl 15,25  taxinc 18,30   (Odoo 11 id 6542: 15,25)
     Preis 15.803,00 / Rabatt 53,79 %     -> taxexcl 7.302,57 taxinc 8.763,08 (Odoo 11 id 3331)
     Preis 4.067,00 / Rabatt 21,68 %      -> taxexcl 3.185,27 taxinc 3.822,32 (Odoo 11 id 3338)
     Preis 23,00 / Rabatt 33,33 % / Menge 2 -> taxexcl 15,34 taxinc 18,40, Zwischensumme 30,67
       (identisch mit dem Odoo-11-Wert price_reduce_taxexcl)
4. Anzeige: In Odoo 11 wird price_reduce in keiner Verkaufsansicht und keinem Verkaufsbericht
   verwendet - nur zwei Website-Vorlagen (Warenkorb, Zahlung, Modul website_sale) nennen
   price_reduce*. In Odoo 18 nennt keine Ansicht das Feld. Website ist nicht Teil des Bereichs
   Verkauf; website_sale ist in Odoo 18 nicht installiert.
```

## 3. Transformationsregel (vorbereitet)

```
price_reduce wird NICHT als eigener Wert uebernommen und in Odoo 18 NICHT nachgebaut.
Der reduzierte Preis ergibt sich in Odoo 18 aus den migrierten Basisfeldern:
    price_unit, discount, product_uom_qty, tax_id, currency_id
und steht dort als price_reduce_taxexcl (zzgl. USt.) und price_reduce_taxinc (inkl. USt.) bereit.

Werteerhaltung:
  - Alle 4.011 Zeilen: price_reduce = price_unit * (1 - Rabatt/100)  (Formelnachweis)
  - 3.959 von 3.960 Zeilen mit Menge > 0: Odoo-18-Wert exakt gleich dem Odoo-11-Wert
  - 1 Zeile: 0,01 Differenz, weil die beiden Odoo-11-Felder selbst um 0,01 abweichen
    (kein Verlust durch die Migration)
  - 51 leere Positionen (Menge 0): Odoo 18 fuehrt 0,00 - genau wie Odoo 11 es in
    price_reduce_taxexcl/taxinc bereits fuehrt; die Zwischensumme dieser Zeilen ist 0,00 und
    price_reduce wird nirgends angezeigt. Fachlich keine Auswirkung.

Einordnung nach der Statusliste: "durch Odoo-18-Funktion ersetzt" (Nachfolgefelder
price_reduce_taxexcl / price_reduce_taxinc), keine Umbenennung eines Feldes.
```

## 4. Pruefung (nur lesend)

```
scripts/pruefe_verkauf_r2_preis_reduziert.py --instanz lokal | vm
  lokal 9 OK / 0 FEHL | VM 9 OK / 0 FEHL  (Odoo-11-Teil identisch, Odoo-18-Teil je Instanz)
  Pruefungen: Feld und Belegung, Formel gegen Basisfelder fuer alle Zeilen,
  Gleichheit mit price_reduce_taxexcl (Toleranz 0,01), leere Positionen, Zielfelder in Odoo 18,
  Anzeige in Ansichten und Berichten beider Systeme.
Testdaten in Odoo 18: 7 Testzeilen in 2 Testauftraegen angelegt und vollstaendig entfernt
  (Bestand vorher = nachher: lokal 18 Auftraege / 28 Zeilen).
```

## 5. Entscheidung von Anna (29.09.2026) und Status

```
1. price_reduce wird in Odoo 18 NICHT als eigenes Feld nachgebaut und nicht direkt migriert.
2. Der Wert wird bei der spaeteren Datenmigration aus den migrierten Basisfeldern
   price_unit, discount, product_uom_qty, tax_id und currency_id durch die
   Odoo-18-Standardlogik neu berechnet (Felder price_reduce_taxexcl / price_reduce_taxinc).
3. Die beiden Sonderfaelle bleiben unveraendert dokumentiert:
   - 1 Zeile mit 1-Cent-Eigenrundung in Odoo 11 (Zeile id 5173, Auftrag A-2400078: price_reduce
     15,33 gegen price_reduce_taxexcl 15,34)
   - 51 leere Positionen (Menge 0), in Odoo 18 mit 0,00 in den Zielfeldern - wie in Odoo 11

STATUS: R2 ABGESCHLOSSEN (29.09.2026) - analysiert, Transformationsregel festgehalten, geprueft
  (lokal 9 OK / 0 FEHL, VM 9 OK / 0 FEHL). Es war KEINE Aenderung an Odoo 18 erforderlich;
  keine bestehende Odoo-18-Funktion wurde entfernt, keine Datenmigration durchgefuehrt.
Der Bereich Verkauf bleibt bis zur Vorbereitung der Risiken R3 bis R8 weiterhin NICHT endgueltig
abgeschlossen.
```
