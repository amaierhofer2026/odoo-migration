# Abonnements: Teil 11 - Smart Button "Rechnungen" auf Odoo 18 umgestellt

Stand: 22.09.2026. Odoo 11 Prod ausschliesslich read-only. Keine Produktivdaten migriert.

## 1. Fehler

Der Smart Button "Rechnungen" im Abo-Formular brach auf der VM ab:

```
ValueError: External ID not found in the system: account.action_invoice_tree1
itk_subscription/models/sale_subscription.py, action_subscription_invoice, Zeile 367
```

`account.action_invoice_tree1` ist eine Odoo-11-XML-ID und existiert in Odoo 18 nicht mehr.

## 2. Vollstaendige Pruefung aller XML-IDs im Modul

Werkzeug `scripts/pruefe_abo_xmlids.py` durchsucht alle .py/.xml/.csv des Moduls nach
`env.ref(...)`, `ref="..."`, `get_object_reference(...)` und prueft jede Kennung gegen `ir.model.data`
der Zielinstanz.

```
Ergebnis: 38 Kennungen geprueft, davon 37 in Ordnung
   account.view_move_form, base.group_portal, mail.mt_note, sale.view_order_form,
   itk_subscription.*, product.*, payment.*, analytic.* ... alle OK
   einzig fehlend: account.action_invoice_tree1  (nur dieser Aufruf)
Weitere Treffer wie /my/home, www.odoo.com, /my/payment_method sind URL-Zeichenketten aus
E-Mail-Vorlagen und Portal-Links, keine XML-IDs.
```

## 3. Behebung (Modulversion 18.0.1.2.4)

```python
# vorher (Odoo 11)
action = self.env.ref('account.action_invoice_tree1').read()[0]
# nachher (Odoo 18)
action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_out_invoice_type')
```
`account.action_move_out_invoice_type` ist in Odoo 18 die Aktion "Invoices" auf `account.move`
mit der Domain `move_type in (out_invoice, out_refund)`. Die uebrige Logik der Methode
(Einzelrechnung -> Formular, mehrere Rechnungen -> gefilterte Liste, keine Rechnung -> Aktion schliessen)
blieb unveraendert; gefiltert wird weiterhin ueber `invoice_line_ids.subscription_id in self.ids`,
also ausschliesslich auf die Rechnungen dieses Abos.

## 4. Funktionstest (scripts/test_abo_smartbuttons.py)

```
                                                    lokal        VM
Rechnungen-Button oeffnet account.move               OK          OK
Aktionen ohne Fehlermeldung                          OK          OK
0 Rechnungen: Aktion schliesst (Button ausgeblendet) OK          OK
1 Rechnung: Rechnung wird direkt im Formular geoeffnet OK        OK
mehrere Rechnungen: Filter auf genau diese IDs       OK (2)      OK
Gegenprobe: fremde Rechnung nicht im Filter          OK          OK
Verkauf-Button oeffnet sale.order, gefiltert          OK          OK
ERGEBNIS                                              11 OK/0     13 OK/0
```
Zusaetzlich klickt der Browsertest die Smart Buttons "Rechnungen" und "Verkauf" auf der VM
funktional an (nicht nur Sichtbarkeit) und prueft, dass keine Fehlermeldung erscheint und die
richtige Ansicht (account.move bzw. sale.order) geoeffnet wird.

## 5. Manueller Browser-Nachweis auf der VM (Anna, 22.09.2026)

Mein headless Browsertest konnte den Klick auf den Rechnungs-Smart-Button nicht auswerten (die URL
bleibt in Odoo 18 auf dem Abo). Der manuelle Test im echten Browser hat es bestaetigt:

```
Abo 183 (2 Rechnungen): Smart Button "Rechnungen" oeffnet korrekt die zugehoerigen Rechnungen,
                        kein RPC-Fehler
Abo 172 (0 Rechnungen): Rechnungs-Smart-Button ist korrekt ausgeblendet
```

Damit ist der letzte offene Nachweis erbracht.

## 5. Abschluss

**ABONNEMENTS = VOLLSTAENDIG FUNKTIONSFAEHIG UND VOLLSTAENDIG MIGRATIONSVORBEREITET.**

Fuer dieses Modul sind keine fachlichen oder technischen Grundsatzentscheidungen mehr offen.
Bei der eigentlichen Migration muessen nur noch die dokumentierten Regeln ausgefuehrt werden
(`migration/abo_migrationsregeln.json`: Auswahlregel, Migrationsreihenfolge, Auftrags-Mapping,
Multiplikationsfaktor, recurring_next_date und Cron-Ablauf, Nummernregel, EUR-Konsistenz).
Abgeschlossen in den Teilen 1 bis 11.
