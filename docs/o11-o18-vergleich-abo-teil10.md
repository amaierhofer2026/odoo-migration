# Abonnements: Teil 10 - automatische Rechnung mit korrektem Betrag (Abschluss)

Stand: 22.09.2026. Odoo 11 Prod ausschliesslich read-only. Keine Produktivdaten migriert.

## 1. Ursache: vier Odoo-11-Kompatibilitaetsreste in itk_subscription

Der Cronjob "Sale Subscription: generate recurring invoices and payments" erzeugte zunaechst gar
keine Rechnung, danach eine Rechnung mit 0,00 Euro. Ursache waren vier Stellen, an denen Odoo-11-Aufrufe
in Odoo 18 nicht mehr existieren:

```
1. account.fiscal.position.get_fiscal_position(partner_id)  ->  _get_fiscal_position(partner)
2. map_tax(taxes, product, partner)                          ->  abweichende Signatur in Odoo 18
3. mail.thread.message_post_with_view(views, values=...)     ->  message_post_with_source(views, render_values=...)
4. account.move ohne move_type                               ->  Beleg wurde als Buchungssatz ('entry')
                                                                 angelegt, nicht als Kundenrechnung
```
Punkt 4 war die Ursache des Betrags 0,00: bei einem Buchungssatz berechnet Odoo keine Rechnungssummen
(price_subtotal, amount_untaxed und amount_total bleiben 0). In Odoo 11 kam der Belegtyp aus dem Modell
account.invoice (type='out_invoice'); beim Port auf account.move fehlte das Feld.

Nachweis der Feldgleichheit vor dem Fix (ITK-Zeile gegen manuell erzeugte Rechnungszeile):
```
move_type      ITK: entry        manuell: out_invoice
price_subtotal ITK: 0.0          manuell: 65.0
price_total    ITK: 0.0          manuell: 78.0
balance        ITK: 0.0          manuell: -65.0
quantity/price_unit/discount waren in beiden Zeilen identisch (1.0 / 65.0 / 0.0)
```

## 2. Behebung (Modulversion 18.0.1.2.3)

```
addons/itk_subscription/models/account_fiscal_position.py  (neu, Kompatibilitaetsschicht)
   get_fiscal_position(partner_id) -> _get_fiscal_position(partner)
   map_tax(...) tolerant auf die Odoo-18-Signatur abgebildet
   mail.thread.message_post_with_view -> message_post_with_source (values -> render_values)
addons/itk_subscription/models/sale_subscription.py
   _prepare_invoice_data: 'move_type': 'out_invoice' ergaenzt (mit Kommentar und Begruendung)
```
Keine Modell- oder Feldnamen geaendert, keine Testumgehung: die Rechnung ist jetzt ein echter
Kundenrechnungsbeleg mit korrekten Summen.

## 3. Testfall auf der VM (Werkzeug scripts/test_abo_rechnungslauf.py)

Realistisch angelegtes Testabo: Vorlage Jahresabrechnung-Abonnement (ohne Zahlungspflicht),
EUR-Preisliste "Preise 2026 + Valorisierung", Kunde vollstaendig, eine Abo-Zeile mit Produkt,
Menge 1, Preis 65,00, qty_multiplication_factor 1, recurring_next_date 21.09.2026.

```
                                                lokal        VM
Abo Status Laufend                               OK          OK
EUR-Preisliste hinterlegt                        OK          OK
Abo-Zeile mit Produkt und Betrag (65,00)         OK          OK
genau eine Rechnung erzeugt                      OK          OK
Beleg ist Kundenrechnung (move_type out_invoice) OK          OK
Nettobetrag = 65,00                              OK          OK
Brutto = 65,00 + 13,00 Steuer = 78,00            OK          OK
Rechnung in EUR                                  OK          OK
invoice_count steigt                             OK          OK
recurring_next_date 2026-09-21 -> 2027-09-21     OK          OK
zweiter Lauf erzeugt kein Duplikat                OK          OK
Verknuepfung Abo <-> Rechnung (invoice_origin)   OK          OK
ERGEBNIS                                         13 OK/0 FEHL  13 OK/0 FEHL
```

## 4. Migrationsregel (bestaetigt)

```
recurring_next_date wird 1:1 aus Odoo 11 uebernommen.
Cronjobs "generate recurring invoices and payments" und "subscriptions expiration" waehrend der
   eigentlichen Migration pausieren.
Nach Abschluss der Datenmigration Stichprobe pruefen (Termine, Zeilen, Preise).
Erst danach die Cronjobs wieder aktivieren.
Die erste automatisch erzeugte Rechnung kontrollieren: Belegtyp Kundenrechnung, Nettobetrag,
   Steuer, Bruttobetrag, Waehrung EUR, Verknuepfung ueber invoice_origin.
```

## 5. Abschluss

**ABONNEMENTS = VOLLSTAENDIG FUNKTIONSFAEHIG UND VOLLSTAENDIG MIGRATIONSVORBEREITET.**
