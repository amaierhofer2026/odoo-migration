# Struktur-/Funktionsvergleich Odoo 11 Angebote/Verkaufsauftraege -> Odoo 18

Stand: 18.09.2026 (Session 117, Bestandsaufnahme)
Quellen: Odoo 11 Prod `portal.it-kommunal.at` DB `ITK_V1_a` (ausschliesslich lesend) und Odoo 18 lokal + VM

Keine Datenmigration. Es wurde kein Angebot, Auftrag, keine Rechnung und kein Abonnement uebernommen.

## 1. Bestand und Zustaende (Odoo 11 Prod, read-only)

```
sale.order gesamt                             2.460
   state=draft (Angebot)                          5
   state=sent  (Angebot gesendet)                 0
   state=sale  (bestätigter Verkaufsauftrag)   2.308
   state=done                                    0
   state=cancel                                 147
sale.subscription (Abonnements)               1.764
   open 1.482 | cancel 231 | close 48 | draft 3
```

Odoo 18 (Teststand): 16 Auftraege, 5 Abonnements - nur Testdaten, keine Uebernahme aus Odoo 11.
Die von Anna genannten Zustaende sind damit: Angebot (draft, 5), bestaetigter Auftrag (sale, 2308),
storniert (cancel, 147). "Angebot gesendet" und "Abgeschlossen" existieren als Statuswerte, sind in
Odoo 11 aber unbenutzt.

## 2. Statusleiste und Statusuebergaenge

```
                        Odoo 11                                   Odoo 18
Statusleiste            draft, sent, sale (sichtbar)              draft, sent, sale (sichtbar)   -> identisch
Zusatzstatus            done, cancel                              cancel (+ done existiert)      -> identisch
Buttons O11             action_confirm, action_cancel,            action_confirm, action_cancel,
                        action_done, action_draft, action_unlock, action_draft, action_lock,
                        action_quotation_send, print_quotation    action_unlock, action_quotation_send,
                                                                  action_preview_sale_order
```

Odoo 18 ist hier moderner (Sperren, Vorschau, Rabatt-/Preis-/Steuer-Assistenten). Kein Rueckbau.

## 3. Feldvergleich (Odoo 11 -> Odoo 18)

Alle in Odoo 11 tatsaechlich verwendeten Felder haben in Odoo 18 ein Ziel; die ITK-Kontaktfelder
sind bereits im Modul `itk_sale_management` vorhanden und im Formular eingebunden.

```
Odoo-11-Feld              Odoo 11 sichtbar          Odoo-18-Zielfeld            Typ/Relation          Bewertung
state                     Status                    state                       selection             1:1
partner_id                Kunde                     partner_id                  m2o res.partner       1:1
partner_invoice_id        Rechnungsadresse          partner_invoice_id          m2o res.partner       1:1
partner_shipping_id       Lieferadresse             partner_shipping_id         m2o res.partner       1:1
user_id                   Verkaeufer                user_id                     m2o res.users         1:1
team_id                   Vertriebskanal            team_id                     m2o crm.team          1:1 (Label in O18: Verkaufsteam)
pricelist_id              Preisliste                pricelist_id                m2o product.pricelist 1:1
payment_term_id           Zahlungsbedingungen       payment_term_id             m2o account.payment.term 1:1
date_order                Bestelldatum              date_order                  datetime              1:1 (Label: Auftragsdatum)
validity_date             Ablaufdatum               validity_date               date                  1:1 (Label: Gueltigkeit)
confirmation_date         Bestaetigung am           - (Feld entfaellt)          datetime              TRANSFORMATION / KLAERUNG
client_order_ref          Kundenreferenz            client_order_ref            char                  1:1
note                      Geschaeftsbedingungen     note                        text -> html          1:1 (Transformation Typ)
amount_untaxed/tax/total  Nettobetrag/Steuern/Total amount_*                    monetary              1:1
invoice_status            Status Rechnung           invoice_status              selection             1:1 (Label: Rechnungsstatus)
invoice_ids               Rechnungen                invoice_ids                 m2m account.move      1:1
analytic_account_id       Kostenstelle              analytic_distribution       m2o -> Verteilung     TRANSFORMATION (Datenbestand O11: 0)
opportunity_id            Chance                    opportunity_id              m2o crm.lead          1:1 (Label: Verkaufschance)
sale_order_template_id    - (fehlt in O11)          sale_order_template_id      m2o                    NEU in O18, bleibt
warehouse_id              Lager                     warehouse_id                m2o stock.warehouse   1:1 (sale_stock)
incoterm                  Lieferbedingungen         - (in O18 entfernt)         m2o stock.incoterms   entfaellt (Nutzung O11: 0)
origin                    Referenzbeleg             origin                      char                  1:1
medium_id/campaign_id     Medium/Kampagne           medium_id/campaign_id       m2o utm.*             1:1 (Nutzung O11: 0)
source_id                 Referenz                  source_id                   m2o utm.source        1:1 (Label in O18: Quelle)
fiscal_position_id        Steuerzuordnung           fiscal_position_id          m2o account.fiscal.position 1:1 (Label: Steuerposition)
name                      Auftragsreferenz          name                        char                  1:1
order_line                Auftragszeilen            order_line                  o2m sale.order.line   1:1
picking_ids               Pickauftraege             picking_ids                 o2m stock.picking     1:1
project_ids               -                         project_ids                 o2m                    NEU/anders in O18
require_signature/-payment  -                       require_signature/payment   boolean               NEU in O18, bleibt
sale_contact_id           Verkaufskontakt           sale_contact_id             m2o res.partner       1:1 (itk_sale_management)
administrative_contact_id Verwaltungskontakt        administrative_contact_id   m2o res.partner       1:1 (Label in O18: Administrativer Kontakt)
technical_contact_id      Technischer Kontakt       technical_contact_id        m2o res.partner       1:1
final_customer_id         Endkunde                  final_customer_id           m2o res.partner       1:1
product_category_id       Produktkategorie          product_category_id         m2o product.category  1:1
tag_ids                   Stichwoerter              tag_ids                     m2m crm.tag           1:1
is_expired                Ist abgelaufen            is_expired                  boolean               1:1
payment_tx_id/-ids        Transaktionen             - (ersetzt)                 -                     entfaellt (Nutzung O11: 0, O18: transaction_ids)
```

Nutzung in Odoo 11 (read-only gezaehlt, von 2.460 Auftraegen):
```
team_id 2460 | confirmation_date 2436 | opportunity_id 128 | product_category_id 47 | origin 22
sale_contact_id 3 | administrative_contact_id 2 | validity_date 1 | technical_contact_id 1
incoterm 0 | analytic_account_id 0 | payment_tx_id 0 | client_order_ref 0 | final_customer_id 0
source_id/medium_id/campaign_id 0
```

## 4. Formular, Seiten, Smart Buttons

```
Odoo 11: Seiten Auftragszeilen, Weitere Informationen
         Gruppen Lieferadresse, Information Umsatz, Abrechnung, Berichtswesen
         Smart Buttons u. a. action_view_invoice (Rechnungen), action_open_subscriptions (Abonnements),
         action_view_delivery, action_view_project_ids, action_view_task, action_view_timesheet,
         action_view_transaction, print_quotation
Odoo 18: Seiten Auftragszeilen, Optionale Produkte, Angebotsbauer, Weitere Informationen
         Gruppen Verkauf, Rechnungsstellung, Versand, Nachverfolgung
         Buttons u. a. action_view_invoice, action_open_subscriptions, action_view_delivery,
         action_lock/unlock, action_preview_sale_order, action_update_prices, action_update_taxes,
         action_open_discount_wizard, action_add_from_catalog, action_view_purchase_orders
         102 Felder im Formular (Odoo 11: 51)
```

Odoo 18 ist eine Obermenge; die Abo-Verlinkung (`action_open_subscriptions`, `subscription_count`)
ist wie in Odoo 11 vorhanden.

## 5. Abonnements (Vorabpruefung)

Odoo 11 nutzt `sale.subscription` (1.764 Datensaetze) mit `subscription_count` und
`action_open_subscriptions` auf dem Auftrag. In Odoo 18 ist das Modul `sale_subscription` auf der
lokalen Instanz als `uninstallable` gefuehrt (das Modell existiert mit 5 Testdatensaetzen).
**KLAERUNG NOETIG:** Modulstatus auf der VM pruefen und die Abo-Verknuepfung Auftrag <-> Abonnement
vor der Migration klaeren.

### 5.1 Statusumwandlung
Odoo 11 fuehrt den Status `done` (Abgeschlossen, in Prod 0 Datensaetze) und den manuellen Statuswechsel.
Odoo 18 hat diesen Status nicht mehr: abgeschlossene Auftraege sind `state=sale` mit `locked=True`
(Sperre statt eigenem Status). Fuer die Migration bedeutet das: `draft/sent/sale/cancel` sind 1:1,
`done` wird zu `sale` + Sperre. Geprueft im Formular: Feld `locked` und die Buttons
`action_lock`/`action_unlock` sind vorhanden.

### 5.2 Umgesetzte Beschriftungen (Odoo 11-Wortlaut, `scripts/apply_sale_labels.py`)

```
Feld                        vorher (Odoo 18)            jetzt (Odoo 11-Wortlaut)
sale.order.team_id          Verkaufsteam                Vertriebskanal
sale.order.administrative_contact_id  Administrativer Kontakt  Verwaltungskontakt
sale.order.opportunity_id   Verkaufschance              Chance
sale.order.source_id        Quelle                      Referenz
Bewusst Odoo-18-Wortlaut: Auftragsdatum, Gueltigkeit, Rechnungsstatus, Auftragspositionen,
Allgemeine Geschaeftsbedingungen.
```


## 5a. Entscheidungen und Umsetzung (Session 117, zweiter Teil)

### 5a.1 Bestaetigungsdatum (confirmation_date) - eigenes Feld angelegt

Pruefung, ob Odoo 18 ein gleichwertiges Feld hat - Ergebnis: **nein**.

```
Odoo 18: sale.order.date_order = 'Auftragsdatum'. Beim Bestaetigen laeuft
   _prepare_confirmation_values() und liefert {'state': 'sale', 'date_order': fields.Datetime.now()}
   (Modulquelle sale/models/sale_order.py, Zeile 1209-1215).
   -> date_order wird beim Bestaetigen mit dem Bestaetigungszeitpunkt ueberschrieben.
Zusaetzlich erzwingt eine SQL-Bedingung (date_order_conditional_required), dass ein bestaetigter
Auftrag ein date_order hat.
Odoo 11 dagegen fuehrt BEIDE Werte: date_order (Bestelldatum, bleibt erhalten) und
confirmation_date (Bestaetigung am). Semantik weicht also ab - eine Zuordnung von confirmation_date
auf date_order wuerde das Bestelldatum ueberschreiben.
```

Umsetzung (Modul `itk_sale_management` 18.0.1.1.0):

```
Feld: sale.order.confirmation_date, Typ datetime, Beschriftung "Bestätigung am", readonly
Anzeige: im Auftragsformular direkt unter dem Auftragsdatum
Logik: _prepare_confirmation_values() schreibt den Bestaetigungszeitpunkt mit, sofern noch leer
Mapping fuer die Migration: O11 confirmation_date -> O18 confirmation_date (1:1)
                          O11 date_order        -> O18 date_order        (1:1)
```
Damit bleiben beide Werte erhalten; es wurde kein Odoo-11-Feldblind nachgebaut, sondern genau das
fehlende Datum ergaenzt.

### 5a.2 Kostenstelle
In Odoo 11 ist `analytic_account_id` (Kostenstelle) bei 0 von 2.460 Auftraegen gefuellt.
**Kein Alt-Feld nachgebaut.** Fuer eine spaetere Zuordnung bei Bedarf ist das Ziel
`sale.order.line.analytic_distribution` (Odoo 18) dokumentiert - dann auf der Auftragsposition, nicht
am Kopf.

### 5a.3 Abo-Verknuepfung

```
Odoo 18: sale.subscription.sale_order_id -> sale.order   (many2one, Beschriftung "Verkaufsauftrag")
         sale.order.subscription_count   (Zaehler, berechnet)
         smart button action_open_subscriptions im Auftragsformular
Odoo 11: gleiche Logik (Zaehler + Button auf dem Auftrag)
Mapping: Abonnement -> Auftrag ueber sale.subscription.sale_order_id
```
Auf der VM mit sechs Test-Abos geprueft (siehe Abschnitt 5a.4).

### 5a.4 Smart Buttons / Zustandslogik - Browser-Test

Geprueft im echten Browser (`scripts/browser_auftraege_pruef.py`): **lokal 9 OK / 0 FEHL, VM 9 OK / 0 FEHL**.
Die Zaehler und Verlinkungen funktionieren:

```
Angebot (draft)            kein Rechnungs-Smart-Button sichtbar (korrekt, keine Rechnung)
Angebot gesendet (sent)    Formular oeffnet, Statusleiste wie in Odoo 11
Verkaufsauftrag (sale)     Formular oeffnet
Storniert (cancel)         Formular oeffnet, keine Smart Buttons
Auftrag mit Rechnung       Smart Button "1 Rechnungen" sichtbar; Klick oeffnet die Rechnungsliste
Auftrag mit Abonnement     Smart Button "1 Abonnements" sichtbar; Klick oeffnet die Abo-Ansicht
Feld "Bestätigung am"      im Formular sichtbar
```
Auf der VM zusaetzlich bestaetigt: `verify_s117_auftraege.py` 65 OK / 0 FEHL;
die Beschriftungen der Odoo-Felder muessen nach dem Modul-Upgrade erneut gesetzt werden
(`scripts/apply_sale_labels.py`, Muster aus F34).
Screenshots 45 bis 47 im Desktop-Ordner Odoo18-Layoutvergleich-Session95.

### 5a.5 Beschriftungen
Die Odoo-18-Bezeichnungen Auftragsdatum, Gueltigkeit, Rechnungsstatus und Auftragspositionen bleiben
(fachlich korrekt). Zusaetzliche Odoo-18-Funktionen (Optionale Produkte, Angebotsbauer, Sperren,
Vorschau, Preis-/Steuer-Assistent) bleiben erhalten.


## 6. Abschluss (18.09.2026) - Bereich abgeschlossen

Der Bereich Angebote / Verkaufsauftraege ist strukturell und funktional abgeschlossen und fuer die
spaetere Datenmigration vorbereitet. Vorbereitet heisst: Struktur, Felder, Relationen, Zustaende,
Beschriftungen und Pruefwerkzeuge sind fertig - **es wurden keine Daten uebernommen**.

**Von Anna festgehaltene Punkte:**

1. **Bestaetigungsdatum:** Mapping Odoo 11 `confirmation_date` -> Odoo 18 `confirmation_date` ist
   vorbereitet (eigenes Feld "Bestätigung am" in `itk_sale_management` 18.0.1.1.0).
   Die Datenuebernahme erfolgt erst bei der spaeteren Migration.
2. **Kostenstelle:** keine Altwerte vorhanden (Odoo 11: 0 von 2.460 Auftraegen). Ziel bei kuenftigem
   Bedarf: `sale.order.line.analytic_distribution`.
3. **Odoo-18-Beschriftungen** Auftragsdatum, Gueltigkeit, Rechnungsstatus und Auftragspositionen
   bleiben bestehen.
4. **Abo-Modul:** `sale_subscription` ist als **Voraussetzung vor der spaeteren Abo-Migration**
   dokumentiert (Status auf lokal und VM `uninstallable`, Modell mit Testdaten vorhanden).
   Jetzt keine weitere Aktion und keine IPAX-Anfrage.

**Pruefstand (Endstand):**

```
scripts/verify_s117_auftraege.py     lokal 65 OK / 0 FEHL    VM 65 OK / 0 FEHL
scripts/browser_auftraege_pruef.py   lokal  9 OK / 0 FEHL    VM  9 OK / 0 FEHL
Modul itk_sale_management            18.0.1.1.0
Datenmigration                       keine (Odoo 18: 16 Testauftraege, 6 Test-Abos)
Odoo 11 Prod                         ausschliesslich read-only
```

Nach jedem Modul-Upgrade auf der VM: `python scripts/apply_sale_labels.py --instanz vm` ausfuehren
(die Beschriftungen der Odoo-Felder werden beim Upgrade zurueckgesetzt, Muster F34).

1. `confirmation_date` (2.436 von 2.460 Auftraegen genutzt) hat in Odoo 18 kein Feld. In Odoo 18 wird das
   Bestaetigungsdatum ueber `date_order` gefuehrt. Zu klaeren: soll das Bestaetigungsdatum erhalten bleiben
   (dann Zielregel festlegen), oder entfaellt es?
2. `analytic_account_id` (Kostenstelle) ist in Odoo 11 bei 0 Auftraegen gefuellt; Odoo 18 nutzt
   `analytic_distribution`. Zielregel fuer die Migration festlegen (Datenbestand 0).
3. Abo-Modul `sale_subscription` in Odoo 18: Status auf der VM, Verknuepfung Auftrag <-> Abo.
4. Sichtbare Beschriftungen (Angleichung an Odoo 11 vorgeschlagen, noch nicht umgesetzt):
   team_id "Verkaufsteam" -> "Vertriebskanal", administrative_contact_id "Administrativer Kontakt" ->
   "Verwaltungskontakt", opportunity_id "Verkaufschance" -> "Chance", source_id "Quelle" -> "Referenz".
   Weitere Unterschiede bewusst belassen: Auftragsdatum, Gueltigkeit, Rechnungsstatus, Auftragspositionen,
   Allgemeine Geschaeftsbedingungen.
5. Mehrzustands-Browserpruefung auf der VM (Angebot, Angebot gesendet, bestaetigter Auftrag,
   Auftrag mit Rechnung, Auftrag mit Abo) steht aus - Testdaten dafuer muessen in Odoo 18 erst angelegt
   oder vorhandene Testauftraege genutzt werden (keine Odoo-11-Daten).

## 7. Werkzeug

`scripts/verify_s117_auftraege.py` prueft read-only gegen eine Odoo-18-Instanz (lokal oder VM):
Statuswerte und Statusleiste, Header-Buttons, Smart Buttons, die Zielfelder samt Typ/Relation,
die ITK-Kontaktfelder, die sichtbaren Beschriftungen, die Abo-Verknuepfung und dass keine
Odoo-11-Auftragsdaten uebernommen wurden.
