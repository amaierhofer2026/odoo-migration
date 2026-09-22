# Abonnements / Subscriptions: Teil 4 - Abschlusspruefung und Migrationsvorbereitung

Stand: 18.09.2026 (Session 118, Teil 4)
Odoo 11 Prod ausschliesslich read-only; Odoo 18 VM = Abnahmeumgebung. Keine Datenmigration.

## 1. Entscheidungen von Anna (18.09.2026)

- `recurring_next_date` bleibt in Odoo 18 "Datum der nächsten Rechnung".
- Der Odoo-11-Button "Abonnement-Zusatzverkäufe" wird **nicht** nachgebaut; die Funktion laeuft in Odoo 18
  ueber Aktion -> Optionen hinzufügen.
- Zusaetzliche Odoo-18-Funktionen bleiben erhalten.
- Die 42 Abos ohne Verkaufsauftrag duerfen spaeter auch ohne Auftrag migriert werden (Odoo 18 unterstuetzt das);
  die konkrete Auswahlregel bleibt offen.

## 2. Reiter, Vorlagen, Gruende, Analyse, Menues, Cronjobs, Rechte, Sequenzen

```
Reiter "Wiederkehrende Buchungen" (O11) / "Abonnement-Einträge" (O18)
   O11: recurring_invoice_line_ids, recurring_total
   O18: recurring_invoice_line_ids (mit den Zeilenspalten inline), recurring_total
   -> gleicher Inhalt, O18 zeigt die Positionen zusaetzlich direkt in der Liste
Reiter "Einstellungen"
   in BEIDEN Systemen identisch: tag_ids, analytic_account_id, payment_mandatory, payment_token_id
   (in Odoo 11 alle vier ungenutzt, Datenbestand 0)

Vorlagen             O11: 5 | O18: 3 (Jahresabrechnung, Monatsabrechnung, Quartalsabrechnung)
                     Fehlen in O18: "5-Jahresabo" und "J- Jahresabrechnungsabo-Mindestvertragsdauer
                     12 Monate" -> Stammdaten vor der Migration anzulegen (Entscheidung noetig)
Vorlagen-Felder      37 (O11) / 38 (O18) - Unterschied nur __last_update (O11) und has_message/rating_ids (O18)

Gruende fuer Beendigung   O11: 33 Eintraege | O18: 5 Eintraege (die ersten fuenf stimmen namentlich ueberein)
                     In Odoo 11 sind 291 Abos mit einem Beendigungsgrund versehen -> die fehlenden
                     28 Gruende sind vor der Migration als Stammdaten anzulegen (Entscheidung noetig)

Abonnementanalyse    O18: Aktion 1114 "Abonnementanalyse" (sale.subscription.report, graph/pivot) - neu
                     gegenueber Odoo 11, bleibt erhalten

Menues               identisch: Abonnements | Zu erneuernde Abonnements | Abonnement Produkte (seq 1/2/4)
                     Konfiguration -> Vorlagen für Abonnements (seq 4); App-Wurzel "Abonnements" (seq 8)

Cronjobs             identisch: "Verkaufsabonnement: wiederkehrende Rechnungen" (1 Tag, aktiv)
                                "Verkaufsabonnement: Ablauf des Abonnements" (1 Woche, aktiv)

Rechte               identisch: Gruppen "ITK-Abonnements / Manager" (R/W/C/D) und
                     "ITK-Abonnements / User (read only)" (nur Lesen) in beiden Systemen,
                     dazu je eine Portal-Regel. Kategorie der Portal-Gruppe unterscheidet sich
                     (O11 "Other Extra Rights", O18 "User types") - Odoo-Kern, ohne Wirkung.

Sequenzen            in BEIDEN Systemen keine ir.sequence fuer Abos. Odoo 11 fuehrt Namen wie NV-01234,
                     Odoo 18 benennt neue Abos nach der Vorlage. Die Nummer/Namen sind reine char-Felder
                     und werden 1:1 uebernommen -> keine technische Luecke.
```

## 3. Rechnungsentstehung, Verlaengerung, Kuendigung, Abo ohne Auftrag

```
Rechnungsentstehung   Cron "wiederkehrende Rechnungen" (taeglich) erzeugt aus den Abo-Zeilen die
                      Rechnungszeilen; sichtbar ueber den Zaehler "Rechnungen" (invoice_count) und
                      den Smart Button action_subscription_invoice.
                      Odoo 11 und Odoo 18 nutzen dieselbe Mechanik (gleiches Modul, gleicher Cron).
                      Beleg VM: laufendes Abo 182 zeigt "1 Rechnungen"; Abo 185 (ohne Auftrag)
                      stellt ebenfalls Rechnungen.
Verlaengerung         Button "Erneuerungsangebot" (prepare_renewal_order), sichtbar wenn Status nicht Neu;
                      "Zu erneuern" (set_pending) und Menue "Zu erneuernde Abonnements" vorhanden.
Kuendigung/Abschluss  Buttons "Abo-Auftrag schließen" (setzt Status Abgeschlossen + Beendigungsgrund)
                      und "Abo-Auftrag abbrechen" (Status Abgebrochen), Sichtbarkeitsregeln identisch;
                      Feld "Grund für die Beendigung" erscheint in beiden Systemen bei Abgeschlossen
                      und Abgebrochen.
Abo ohne Auftrag      erneut bestaetigt: Odoo 18 unterstuetzt es vollstaendig (Abo 172 Status Neu und
                      Abo 185 Status Laufend, beide ohne sale_order_id, Formular/Aktionen/Zaehler korrekt).
```

## 4. Migrations-Mapping-Tabelle (Abo-Kopf)

```
Bereich / Feld (Odoo 11)             Ziel in Odoo 18                Einstufung
name                                 name                          1:1
code                                 code                          1:1
partner_id                           partner_id                    1:1
partner_invoice_id/address           (nicht im Abo-Modell)         nicht uebernehmen
user_id                              user_id                       1:1
team_id                              (fehlt in O11)                nur Odoo 18, optional
company_id                           company_id                    1:1
currency_id                          currency_id                   1:1
pricelist_id                         pricelist_id                  1:1
payment_term_id                      payment_term_id               1:1 (in O11 nicht gefuellt)
template_id                          template_id                  1:1 (Vorlagen vorher anlegen - 2 fehlen)
sale_order_id                        sale_order_id                 1:1 (42 Abos ohne Auftrag erlaubt)
sale_order_confirmation_date         sale_order_confirmation_date  1:1
date_start                           date_start                    1:1
date                                 date                          1:1
recurring_next_date                  recurring_next_date           1:1 (Beschriftung Odoo 18)
recurring_rule_type                  recurring_rule_type           1:1 (Werte wortgleich)
recurring_interval                   recurring_interval            1:1
recurring_total                      recurring_total               berechnet (wird aus den Zeilen gerechnet)
recurring_monthly                    recurring_monthly             berechnet
contract_termination_period_number   gleich                        1:1
contract_termination_period_unit     gleich                        1:1 (berechnetes Feld, Werte werden gesetzt)
minimum_contract_period_number       gleich                        1:1
minimum_contract_period_unit         gleich                        1:1
end_of_contract_date                 end_of_contract_date          berechnet
noticeperiod                         noticeperiod                  1:1 (Datenbestand 0)
close_reason_id                      close_reason_id               1:1 (Gruende vorher anlegen - 28 fehlen)
state                                state                         1:1 (Werte wortgleich; pending in O11 leer)
tag_ids                              tag_ids                       1:1 (Datenbestand 0)
analytic_account_id                  analytic_account_id           1:1 (Datenbestand 0)
payment_mandatory / payment_token_id gleich                        optional (Datenbestand 0)
description                          description                   1:1
industry_id                          industry_id                   1:1 (Datenbestand 0)
uuid                                 uuid                          1:1
message_ids / chatter                message_ids                   1:1 (Chatter)
```

## 5. Migrations-Mapping-Tabelle (Abo-Zeilen)

```
Feld (Odoo 11)                       Ziel in Odoo 18                Einstufung
analytic_account_id (Aboauftrag)     analytic_account_id            1:1 (Verknuepfung Zeile -> Abo)
product_id                           product_id                     1:1
name (Beschreibung)                  name                           1:1
quantity                             quantity                       1:1
uom_id                               uom_id                         1:1 (uom.uom)
price_unit                           price_unit                     1:1
discount                             discount                       1:1 (in 57 % der Zeilen gefuellt)
price_subtotal                       price_subtotal                 berechnet
qty_multiplication_factor            qty_multiplication_factor      1:1 (ITK-Multiplikationsfaktor, pro 1.000,
                                                                    alle 2.434 Zeilen gefuellt)
partner_id                           partner_id                     1:1
salesperson_id                       salesperson_id                 1:1
```

## 6. Status als MIGRATIONSVORBEREITET

**Keine strukturellen oder funktionalen Luecken.** Modelle, Felder, Relationen, Selection-Werte,
Formulare, Reiter, Sichtbarkeitsregeln, Buttons, Smart Buttons, Menues, Cronjobs, Rechte und die
Zustandslogik sind zwischen Odoo 11 Prod und Odoo 18 deckungsgleich. Es gibt kein Feld ohne Ziel und
keine notwendige Transformation (Teil 2). Rechnungsentstehung, Verlaengerung, Kuendigung und Abos ohne
Verkaufsauftrag sind funktional geprueft.

Damit ist der Bereich **strukturell und funktional MIGRATIONSVORBEREITET**.
**Nicht** Teil dieses Status sind die Stammdaten und die Auswahlregel (Abschnitt 7) - sie sind
Datenschritte und werden erst mit der Datenmigration entschieden. Es wurden keine Daten uebernommen.

## 7. Noch vor Datenmigration zu entscheiden

1. **Vorlagen:** Odoo 11 hat 5 Vorlagen, in Odoo 18 fehlen "5-Jahresabo" und
   "J- Jahresabrechnungsabo-Mindestvertragsdauer 12 Monate" -> anzulegen (ja/nein, exakter Wortlaut).
2. **Beendigungsgruende:** Odoo 11 hat 33, in Odoo 18 sind 5 vorhanden -> die fehlenden 28 vorher anlegen;
   Zuordnung Odoo 11 -> Odoo 18 ueber den Namen.
3. **Auswahlregel der Abos:** welche Abos uebernommen werden (Status, Alter, Auftragsbezug). Die 42 Abos
   ohne Verkaufsauftrag duerfen laut Entscheidung mit migriert werden; Konkretisierung offen.
4. **Reihenfolge:** Verkaufsauftraege vor Abos (1.722 Abos verweisen auf einen Auftrag).
5. **Multiplikationsfaktor:** Regel bestaetigen, dass `qty_multiplication_factor` 1:1 uebernommen wird
   (ITK-Preislogik, pro 1.000) - betrifft die Abrechnung, deshalb vorher freigeben.
6. **Rechnungsstellung:** offene Frage, ob fuer laufende Abos nach der Migration die naechste Rechnung
   automatisch entstehen soll (`recurring_next_date` uebernehmen) oder erst nach manueller Pruefung.
7. **Nummern/Namen:** Odoo 11 fuehrt NV-Nummern im Feld `name`/`code`; kuenftige Abos werden nach der
   Vorlage benannt. Entscheiden, ob die alten Nummern unveraendert uebernommen werden (empfohlen: ja, 1:1).
8. Abo-Modul `sale_subscription` (Enterprise-Katalog ohne Code) bleibt als Katalogeintrag unangetastet.
