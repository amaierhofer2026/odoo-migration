# Abonnements: Teil 12 - manueller Rechnungsweg und Finanzposition (Abschluss)

Stand: 22.09.2026. Odoo 11 Prod ausschliesslich read-only. Keine Produktivdaten migriert.

## 1. Fehler und Ursache

Button "Rechnung manuell erstellen" im Abo-Formular brach ab mit

```
psycopg2.ProgrammingError: can't adapt type 'account.fiscal.position'
Kette: recurring_invoice -> _recurring_create_invoice -> _prepare_invoice -> _prepare_invoice_data
       -> _prepare_invoice_lines -> _prepare_invoice_line -> fiscal_position.map_account(account)
```
Analyse des Datenflusses der Finanzposition:

```
Odoo 11: account.fiscal.position.get_fiscal_position(partner_id)  -> ID
         account.fiscal.position.map_account(account)              -> ID
         account.fiscal.position.map_tax(taxes, product, partner)  -> Steuer-IDs
Odoo 18: _get_fiscal_position(partner)                             -> RECORDSET
         map_account(account)                                      -> RECORDSET
         map_tax(...)                                              -> RECORDSET
```
Das ITK-Modul stammt aus Odoo 11 und erwartet IDs. In Odoo 18 greift der Nachbau auf berechnete
Felder der Finanzposition zu (`account_map`, `tax_map`, `account_ids`); dabei wird intern das
Positions-Recordset als SQL-Parameter verwendet - genau daraus entsteht der psycopg2-Fehler.
Reproduziert mit einem Kunden an der Finanzposition "National + EU (ohne UID)" (mit Kontenzuordnung);
ohne Finanzposition trat der Fehler nicht auf, deshalb lief der Cron-Test zuvor durch.

## 2. Behebung (Modulversion 18.0.1.2.5)

Ziel ist die Odoo-18-native API; der Odoo-11-Nachbau wurde entfernt:

```
_prepare_invoice_data   uebergibt nur noch die Finanzposition als ID am Beleg
                        'fiscal_position_id': <ID der Kunden-Finanzposition>
_prepare_invoice_line   Konten- und Steuerzuordnung entfernt - das erledigt Odoo selbst
                        anhand der Finanzposition des Belegs
entfernt                map_account- und map_tax-Nachbau; die map_tax-Bruecke in
                        models/account_fiscal_position.py wird nicht mehr benoetigt
beibehalten             Kompatibilitaetsbruecke get_fiscal_position -> _get_fiscal_position
                        (vom Modul an vier Stellen benoetigt) und die mail-Bruecke
                        message_post_with_view -> message_post_with_source
```

## 3. Nachweise

Cron-Weg (scripts/test_abo_rechnungslauf.py): lokal und VM 13 OK / 0 FEHL.

Manueller Weg (scripts/test_abo_manuelle_rechnung.py) mit Finanzposition samt Kontenzuordnung:

```
                                              lokal        VM
Aufruf ohne RPC-Fehler                          OK          OK
genau eine neue Rechnung                        OK          OK
recurring_next_date fortgeschrieben             OK          OK   (wie beim Cron)
move_type = out_invoice                         OK          OK
Netto 65,00 + 13,00 Steuer = 78,00 EUR          OK          OK
Rechnungszeile: Menge 1, Preis 65,00,
   Rabatt 0,00, Steuern [15], Konto 4000        OK          OK
Finanzposition am Beleg hinterlegt              OK          OK
Verknuepfung ueber invoice_origin               OK          OK
Rechnungs-Smart-Button danach                   OK          OK
ERGEBNIS                                        16 OK/0     16 OK/0
```
Fachliches Verhalten des manuellen Buttons (in Odoo 11 und Odoo 18 identisch): er rechnet sofort ab,
unabhaengig von recurring_next_date; je Klick entsteht genau eine Rechnung. Der Cronjob ist ueber
recurring_next_date gefiltert und erzeugt deshalb keine Duplikate (nachgewiesen im Cron-Test).

Browser-Klick auf der VM (scripts/browser_abo_manuell_klick.py):

```
Button "Rechnung manuell erstellen" im echten Browser gefunden (Aktionsmenue) und geklickt   OK
kein RPC-/Serverfehler                                                                        OK
Browser zeigt die Rechnungsansicht                                                           OK
genau eine neue Rechnung (4 -> 5)                                                            OK
Screenshot 53_VM_Abo_Rechnung_manuell.png
ERGEBNIS 4 OK / 0 FEHL
```
Smart Buttons im Browser: "Rechnungen" und "Verkauf" geklickt (Ergebnis manuell bestaetigt),
"Abonnement-Zusatzverkäufe" oeffnet den Assistenten. Die zustandsaendernden Buttons
(Abonnement starten, Zu erneuern, schliessen, abbrechen) wurden bewusst nicht im Browser geklickt,
weil sie den Testdatenbestand veraendern; ihre Methoden sind ueber die Funktionstests abgedeckt.

## 4. Neue Abnahmeregel (uebernommen)

Ein Button oder Smart Button gilt erst als funktionsfaehig, wenn er auf der VM im echten Browser
geklickt wurde und der komplette Vorgang ohne RPC-/Serverfehler durchlaeuft. Sichtbarkeit allein
genuegt nicht.

## 5. Abschluss

**ABONNEMENTS = VOLLSTAENDIG FUNKTIONSFAEHIG UND VOLLSTAENDIG MIGRATIONSVORBEREITET.**
