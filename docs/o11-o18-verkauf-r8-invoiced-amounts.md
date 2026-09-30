# R8 - amt_invoiced / amt_to_invoice: Zuordnung Odoo 11 -> Odoo 18

Stand: 29.09.2026, Session 121. **Nur Analyse.** Odoo 11 ausschliesslich read-only.
Fuer den Beweis wurde in Odoo 18 ein Testauftrag mit einer Testrechnung angelegt, gebucht und
danach vollstaendig entfernt; es war **keine Aenderung an Odoo 18 erforderlich**.

## 1. Ausgangslage Odoo 11 (gemessen)

```
sale.order.line.amt_invoiced    monetary, gespeichert, readonly  Anzeige "Abgerechneter Betrag"
sale.order.line.amt_to_invoice  monetary, gespeichert, readonly  Anzeige "Abzurechnender Betrag"

Belegung:
  Auftragszeilen gesamt                       4.011
  amt_invoiced  gesetzt                       1.669  (davon positiv 1.664, negativ 5)
  amt_to_invoice gesetzt                      1.950  (davon positiv 1.906, negativ 44)

Inhalt der Werte: steuerinklusive Betraege.
  A-2600297 Zeile: price_subtotal 15,25 | price_total 18,30 (= +20 % USt.) | amt_invoiced 18,30
  A-2600294 Zeile: price_subtotal 147,50 | price_total 177,00 | amt_invoiced 354,00
                   (zweimal abgerechnet) | amt_to_invoice -177,00 (ueberabgerechnet)
Summen ueber die Zeilen mit amt_invoiced > 0:
  price_subtotal (netto)   2.474.940,50
  price_total (inkl. USt.)  2.969.628,64
  amt_invoiced              3.084.047,20   (hoeher, weil mehrfach abgerechnet wurde)
  amt_to_invoice             -114.742,56   (negative Werte bei Ueberabrechnung)
```

## 2. Gegenstueck in Odoo 18 (Quelle und Test)

```
sale.order.line.amount_invoiced    monetary, NICHT gespeichert, berechnet, readonly
                                   Anzeige "Abgerechneter Betrag"
sale.order.line.amount_to_invoice  monetary, NICHT gespeichert, berechnet, readonly
                                   Anzeige "Nicht abgerechnetes Saldo"
Die Felder sind also - anders als in Odoo 11 - nicht speicherbar; ein Import kann sie nicht
setzen. Die Werte entstehen ausschliesslich durch Neuberechnung.

Quelle im Modul sale (im Container gelesen, sale_order_line.py):
  _compute_amount_invoiced:
    Summe ueber die verknuepften Rechnungszeilen von price_total (INKL. Steuern),
    nur fuer Rechnungen im Zustand 'posted' (oder payment_state 'invoicing_legacy'),
    mit Waehrungsumrechnung auf die Auftragswaehrung; Gutschriften gehen negativ ein
    (direction_sign).
  _compute_amount_to_invoice:
    (price_total / product_uom_qty) * (abzurechnende Menge - bereits abgerechnete Menge)
    -> ergibt 0,00 wenn vollstaendig abgerechnet und negative Werte bei Ueberabrechnung.
Damit sind beide Felder fachlich deckungsgleich zu Odoo 11 (dort ebenfalls steuerinklusive).

Beweis mit Testauftrag und Testrechnung (danach entfernt):
  Auftrag mit Zeile 1,0 x 100,00 EUR zzgl. 20 % USt. (price_total 120,00)
  Rechnung im ENTWURF verknuepft  -> amount_invoiced   0,00 | qty_invoiced 1,0 |
                                     amount_to_invoice 120,00
  Rechnung GEBUCHT                -> amount_invoiced 120,00 | qty_invoiced 1,0 |
                                     amount_to_invoice   0,00 | untaxed_amount_invoiced 100,00
  Auftragskopf                    -> invoice_status "invoiced", invoice_count 1
Ergebnis: Odoo 18 berechnet die Werte genau aus den verknuepften, gebuchten Rechnungszeilen -
  wie Odoo 11. Entwurfsrechnungen zaehlen nicht.
```

## 3. Transformationsregel (vorbereitet)

```
amt_invoiced und amt_to_invoice werden NICHT direkt uebernommen (technisch unmoeglich: in Odoo 18
berechnet und nicht gespeichert). Odoo 18 ermittelt sie aus den migrierten Rechnungsdaten.
Voraussetzungen fuer identische Werte:
  1. Rechnungen und Rechnungszeilen werden migriert und gebucht (Zustand 'posted')
  2. die Verknuepfung Auftragszeile <-> Rechnungszeile wird gesetzt (Regel R5)
Folgen, wenn die Rechnungen NICHT migriert werden (gemessener Fall "Entwurfsrechnung"):
  amount_invoiced   = 0,00
  amount_to_invoice = voller Betrag der Zeile (z. B. 120,00 statt 0,00)
  invoice_status    = "to invoice" statt "invoiced"
  -> Fuer die 1.863 historisch abgerechneten Auftragszeilen ist das eine sichtbare, aber
     fachlich erklaerbare Abweichung; sie ist zu dokumentieren.
Mit Rechnungsmigration sind die Werte identisch (durch die Berechnungsquelle belegt).
Einordnung nach der Statusliste: "durch Odoo-18-Funktion ersetzt" (Neuberechnung aus den
Rechnungsdaten). Keine Aenderung an Odoo 18 erforderlich.
```

## 4. Nachweise

```
Odoo 11: fields_get (Typ, gespeichert, readonly, Bezeichnung), search_count fuer Belegung und
  Vorzeichen, Beispielzeilen mit price_subtotal/price_total/amt_invoiced/amt_to_invoice,
  Summenauswertung ueber alle Zeilen mit amt_invoiced > 0
Odoo 18: ir.model.fields (store=False, berechnet, readonly), Quelltext des Moduls sale im
  Container (Compute-Methoden gelesen), End-to-End-Test mit gebuchter Rechnung, danach
  vollstaendige Bereinigung (Testauftrag und Testrechnung entfernt)
Bestand unveraendert: lokal 18 Auftraege / 28 Zeilen / 13 Produkte / 37 Rechnungen,
  VM 20 Auftraege / 29 Zeilen / 13 Produkte (jeweils 0 Lagerbelege)
Keine Datenmigration, keine Aenderung an Odoo 18.
```

## 5. Entscheidungen von Anna (29.09.2026) und Status

```
a) Regel BESTAETIGT: amt_invoiced und amt_to_invoice werden spaeter NICHT als gespeicherte Werte
   aus Odoo 11 uebernommen. Odoo 18 berechnet diese Werte selbst neu. Voraussetzungen dafuer:
     - historische Rechnungen werden mitmigriert
     - Rechnungszeilen werden korrekt migriert
     - die Verknuepfung Auftragszeile <-> Rechnungszeile aus R5 wird hergestellt
     - die relevanten Rechnungen haben den fachlich richtigen Buchungsstatus (gebucht)
b) Fachliche Erwartung BESTAETIGT und ausdruecklich dokumentiert: Werden historische Rechnungen
   nicht migriert bzw. nicht verknuepft, ist zu erwarten:
     - amount_invoiced = 0
     - amount_to_invoice zeigt den noch abzurechnenden Betrag
     - invoice_status kann auf "to invoice" stehen
   Diese Abweichung darf spaeter NICHT als Migrationsfehler interpretiert werden.
   Ziel der eigentlichen Migration bleibt, dass die historischen Rechnungsbezuege erhalten
   bleiben, damit Odoo 18 die Werte moeglichst identisch zu Odoo 11 neu berechnet.
c) BESTAETIGT: weder amt_invoiced noch amt_to_invoice werden direkt uebernommen oder kuenstlich
   gespeichert.

STATUS: R8 ABGESCHLOSSEN (29.09.2026) - analysiert (read-only in Odoo 11, Servercode und
  End-to-End-Test in Odoo 18), Regel und fachliche Erwartung festgehalten. Es war KEINE Aenderung
  an Odoo 18 erforderlich; Testauftrag und Testrechnung vollstaendig entfernt, keine Datenmigration.
Damit sind alle acht Risiken des Migrations-Checks (R1 bis R8) technisch vorbereitet.
Der Bereich Verkauf wird noch NICHT endgueltig abgeschlossen; Gesamtstatus:
docs/o11-o18-verkauf-gesamtstatus-r1-r8.md
```
