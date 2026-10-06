# Odoo 11 gegen Odoo 18 - Zahlungsformular (Abrechnung > Verkauf/Einkauf > Zahlungen)

Stand: 05.10.2026, Session 126. Auftrag von Anna: vollstaendiger fachlicher Abgleich des
Zahlungsformulars, Pruefung der drei Zusatzfelder, Ursache der schwaecheren Beschriftungen,
Feld-fuer-Feld-Vergleich, zusaetzlich Abrechnung > Einkauf > Zahlungen.

**Status: Zahlungsformular GEPRUEFT (Session 126, Abnahme 19 OK / 0 FEHL auf lokaler Instanz und
VM). Der Bereich Abrechnung bleibt IN ARBEIT** - die abschliessende Kontrolle macht Anna selbst.

Arbeitsweise: Odoo 11 ausschliesslich lesend (`fields_view_get`, `fields_get`, `search_count`,
`read_group`); Odoo 18 lokal und VM; Abnahme im echten Browser.
Werkzeuge: `scripts/vergleich_zahlungsformular_vollstaendig.py` (Arch-Vergleich),
`scripts/browser_zahlungsformular_abnahme.py` (Browser-Abnahme, 19 Pruefungen je Instanz).

## 1. Odoo 11: das Zahlungsformular (read-only gemessen)

Formular `account.payment.form` (View 500), zusammengesetzt mit der Vererbung 1005:

```
Kopfzeile : Buttons "Bestaetigen" (post), "setze auf Entwurf" (action_draft),
            Statusleiste state (Entwurf / Gebucht / Gesendet / Abgestimmt / Abgebrochen)
Gruppe links : Zahlungsart (payment_type, Radio), Partnertyp (partner_type),
               Partner (partner_id), Zahlungsjournal (journal_id),
               Ueberweisung an (destination_journal_id), Zahlungsmethode (payment_method_id, Radio)
Gruppe rechts: Zahlungsdatum (payment_date), Memo (communication),
               Zahlungstransaktion (payment_transaction_id)
ausserhalb   : Zahlungsbetrag (amount) + Waehrung, Nummer (name, readonly)
Smart Buttons: Buchungszeilen (button_journal_entries, in Odoo 11 invisible="1"),
               Rechnungen (button_invoices, nur bei verknuepften Rechnungen),
               Zahlungsabstimmung (open_payment_matching_screen, nur wenn nicht abgestimmt)
Auswahlwerte : payment_type  Geld schicken / Geld erhalten / Interne Ueberweisungen
               partner_type  Kunde / Lieferant
               state         Entwurf / Gebucht / Gesendet / Abgestimmt / Abgebrochen
Modellpflicht: payment_type ja, amount ja, journal_id ja, payment_date ja,
               payment_method_id ja; partner_id nein, communication nein
Bestand      : 5.994 Zahlungen (Einzahlungen CUST.IN/JJJJ/NNNN, Auszahlungen CUST.OUT/...),
               0 mit Zahlungstransaktion, 0 mit Zahlungsreferenz, Abschreibungen 0
```

## 2. Odoo 18: Umsetzung im Modul `itk_account_migration` (Stand 18.0.1.15.0)

```
Kopfzeile : Odoo-11-Kette itk_o11_status (Entwurf / Gebucht / Abgestimmt / Abgebrochen)
            Odoo-18-Knoepfe bleiben erhalten (Bestaetigen, Validieren, Ablehnen, Erstattung,
            Abbrechen, Stornierung anfordern, Als gesendet markieren, Nicht mehr als gesendet
            markieren, setze auf Entwurf)
Gruppe links : Zahlungsart, Partnertyp, Partner, Zahlungsbetrag (pflichtig), Zahlungsjournal,
               Zahlungsmethode (pflichtig)
Gruppe rechts: Zahlungsdatum, Memo, Zahlungstransaktion
darunter     : Bankkonto des Kunden/Lieferanten/Unternehmens (partner_bank_id, Odoo-18-Feld)
technisch    : Gruppe "Herkunft (Migration)": Odoo-11-Zahlungsnummer (itk_o11_payment_number)
               Gruppe "Status (Odoo 18)": Rohstatus state
```

## 3. Feld-fuer-Feld-Vergleich

| Odoo 11 sichtbar | Beschriftung O11 | Odoo 18 | Beschriftung in Odoo 18 | Pflicht O11 | Pflicht O18 | Bewertung |
|---|---|---|---|---|---|---|
| payment_type | Zahlungsart | payment_type | Zahlungsart | ja | ja (Modell) | gleich |
| partner_type | Partnertyp | partner_type | Partnertyp | nein | ja (Modell) | gleich (O18 strenger) |
| partner_id | Partner | partner_id | Partner | nein | nein | gleich |
| journal_id | Zahlungsjournal | journal_id | Zahlungsjournal | ja | ja | gleich |
| payment_method_id | Zahlungsmethode | payment_method_line_id | Zahlungsmethode | ja | ja (Ansicht) | gleichwertig |
| payment_date | Zahlungsdatum | date | Zahlungsdatum | ja | ja | gleich |
| communication | Memo | memo | Memo | nein | nein | gleich |
| payment_transaction_id | Zahlungstransaktion | payment_transaction_id | Zahlungstransaktion | nein | readonly | vorhanden, ungenutzt (Abschnitt 4) |
| amount | Zahlungsbetrag | amount | Zahlungsbetrag | ja | **war nein -> jetzt ja** | **ergaenzt** |
| name | Nummer | name | Nummer (Titel) | nein | readonly | gleich (O18-Nummer) |
| state (Statusleiste) | Entwurf/Gebucht/Gesendet/Abgestimmt/Abgebrochen | itk_o11_status + state | Kette + Status (Odoo 18) | - | - | Kette gleich, Rohwert separat |
| destination_journal_id | Ueberweisung an | - (Feld entfaellt) | - | nein | - | gleichwertig ueber Aktion "Interne Ueberweisungen" (gekoppelte Zahlung) |
| button_invoices | Rechnungen | button_open_invoices / button_open_bills | Rechnungen | - | - | gleich (nur bei verknuepften Belegen sichtbar) |
| button_journal_entries | Buchungszeilen | button_open_journal_entry | Journal Entry (gruppenbeschraenkt) | in O11 unsichtbar | sichtbar | Odoo-18-Zusatz, bleibt |
| open_payment_matching_screen | Zahlungsabstimmung | button_open_statement_lines | Transaction | - | - | funktional an anderer Stelle (Bank/Abstimmung) |

Ergebnis: **keine fehlende Odoo-11-Funktion mehr.** Zwei Pflichtfelder waren in Odoo 18 nicht
erzwungen und sind ergaenzt; eine Doppelung (zweites Partnerfeld) ist behoben.

## 4. Die drei Zusatzfelder im Einzelnen (Auftrag Anna)

### 4.1 Zahlungstransaktion - `payment_transaction_id`

| Frage | Antwort |
|---|---|
| technischer Name | `payment_transaction_id`, Many2one auf `payment.transaction` |
| Datenquelle | Odoo-18-Modul `account_payment` (Online-Zahlungen); in Odoo 11 Feld desselben Namens im `payment`-Framework |
| enthaelt Werte? | **nein** - lokal 0 von 10, VM 0 von 11 Zahlungen; `payment.transaction` 0, `payment.token` 0 Datensaetze |
| Haeufigkeit im Bestand | 0 % (Odoo 11 Prod ebenfalls 0 von 5.994) |
| fachliche Funktion | Verknuepfung einer Zahlung mit einer Online-Zahlungstransaktion eines Zahlungsdienstleisters (Kreditkarte, Online-SEPA, Wallet) |
| fuer die Migration erforderlich? | **nein** - in Odoo 11 nie belegt |
| im normalen Formular noetig? | Odoo 11 hatte das Feld an genau dieser Stelle (rechts unter Memo) -> **bleibt** (Odoo-11-Treue). Es ist im Odoo-18-Modul `readonly` und deshalb heller beschriftet (Abschnitt 5) |

### 4.2 Odoo-11-Zahlungsnummer - `itk_o11_payment_number`

| Frage | Antwort |
|---|---|
| technischer Name | `itk_o11_payment_number`, Char, indiziert, `tracking`, Hilfe-Text; Modul `itk_account_migration` |
| Datenquelle | Migration aus Odoo 11 `account.payment.name` (Muster `CUST.IN/<Jahr>/<NNNN>` bzw. `CUST.OUT/...`) |
| enthaelt Werte? | **nein** - lokal 0 von 10, VM 0 von 11; das Feld wird erst von der Migration gefuellt |
| Haeufigkeit im Bestand | 0 % (Odoo 11: 5.994 Zahlungen mit Nummern, erste CUST.IN/2019/0001, letzte CUST.IN/2026/1061) |
| fachliche Funktion | historische Nachvollziehbarkeit der Odoo-11-Zahlungsnummer (Briefverkehr, Bankbelege) |
| fuer die Migration erforderlich? | **ja** - Regel in `docs/o11-o18-vergleich-abrechnung-teil5-umsetzung.md` Abschnitt 5: Nummer wird in dieses Feld uebernommen; die Odoo-18-Nummerierung bleibt unveraendert, historische Nummern werden **nicht** in die Odoo-18-Sequenz zurueckgeschrieben; zusaetzlich bleibt der Bezug ueber das Memo (Rechnungsnummer) |
| im normalen Formular noetig? | Odoo 11 hatte **kein** solches Feld im Formular. Es ist ein Migrationsfeld -> **aus dem Odoo-11-Block in die Gruppe "Herkunft (Migration)" verschoben** (gleiches Muster wie die Odoo-11-Rechnungsnummer im Rechnungsformular). Sichtbar bleibt es, weil es der Pruefwert fuer die Migration ist |

**Befund zum Mapping:** Die 7 Zahlungen aus dem Juli-Testlauf (id 1-7, `PBNK1/...`) tragen die
Odoo-11-Nummer nur im **Memo** (`CUST.IN/2020/0042` usw.); `itk_o11_payment_number` ist dort leer.
Das sind Testreste eines frueheren Laufs, keine Produktivdaten - die dokumentierte Regel greift ab
der echten Migration.

### 4.3 Status (Odoo 18) - `state`

| Frage | Antwort |
|---|---|
| technischer Name | `state`, Selection (`draft`, `in_process`, `paid`, `canceled`, `rejected`) |
| Datenquelle | Odoo-18-Modell `account.payment` |
| enthaelt Werte? | **ja** - lokal: 2 x in_process, 8 x paid; VM: 11 x paid (10 von 10 bzw. 11 von 11 belegt) |
| Haeufigkeit im Bestand | 100 % |
| fachliche Funktion | technischer Zustand der Zahlung im Odoo-18-Modell; die **fachlich sichtbare** Kette ist `itk_o11_status` (Entwurf / Gebucht / Abgestimmt / Abgebrochen), abgeleitet aus state + Zahlungszustand |
| fuer die Migration erforderlich? | nein (Modellfeld) |
| im normalen Formular noetig? | **Kontrollwert, nicht Teil des Odoo-11-Feldsatzes** -> **in die Gruppe "Status (Odoo 18)" unter den Odoo-18-Angaben verschoben** (gleiches Muster wie im Rechnungsformular, dort im Reiter "Andere Informationen") |

### 4.4 Zusaetzlich vorhanden (nicht in Annas Liste) - `partner_bank_id`

Bankkonto des Kunden / Lieferanten / Unternehmens: Odoo-18-Feld, in Odoo 11 nicht vorhanden,
im Bestand 0 von 10 belegt. Funktion: Bankkonto fuer elektronische Zahlungsarten (SEPA); wird bei
elektronischen Zahlungsmethoden automatisch pflichtig. **Bleibt sichtbar** (Odoo-18-Funktion).

## 5. Beschriftungen: Ursache der schwaecheren Darstellung (Auftrag Anna)

Messung im echten Browser (lokale Zahlung 9, alle sichtbaren Beschriftungen):

```
Zahlungsart              o_form_label                          font-weight 500  Deckkraft 1.00
Partnertyp               o_form_label                          font-weight 500  Deckkraft 1.00
Partner                  o_form_label                          font-weight 500  Deckkraft 1.00
Zahlungsbetrag           o_form_label                          font-weight 500  Deckkraft 1.00
Zahlungsjournal          o_form_label                          font-weight 500  Deckkraft 1.00
Zahlungsmethode          o_form_label                          font-weight 500  Deckkraft 1.00
Zahlungsdatum            o_form_label                          font-weight 500  Deckkraft 1.00
Memo                     o_form_label                          font-weight 500  Deckkraft 1.00
Zahlungstransaktion      o_form_label o_form_label_empty
                         o_form_label_readonly                 font-weight 500  Deckkraft 0.66
Odoo-11-Zahlungsnummer   o_form_label o_form_label_empty
                         o_form_label_readonly                 font-weight 500  Deckkraft 0.66
Status (Odoo 18)         o_form_label o_form_label_readonly    font-weight 500  Deckkraft 0.66
Bankkonto des Unternehmens o_form_label                        font-weight 500  Deckkraft 1.00
```

**Ursache:** nicht unsere Ansicht, sondern Odoo-18-Standardstile. Odoo 18 verringert die Deckkraft
der Beschriftung auf 0,66, wenn das Feld `readonly` ist (`o_form_label_readonly`) und zusaetzlich
bei readonly **und leer** (`o_form_label_empty`). Die Schriftstaerke ist bei **allen** Beschriftungen
identisch (500). Die drei Felder wirkten daher nur schwaecher, weil sie readonly sind bzw. leer waren.

**Umgesetzt:** Die zwei verschobenen Felder stehen nicht mehr im Odoo-11-Block, damit dessen
Beschriftungen einheitlich sind. **Keine** Fettschrift erzwungen, **keine** Pflichtfeld-, readonly-
oder Geschaeftslogik entfernt. `Zahlungstransaktion` bleibt heller, weil Odoo 18 das Feld im Modul
`account_payment` als `readonly=True` fuehrt - eine Angleichung wuerde readonly-Logik veraendern.

## 6. Was fehlte, was geaendert wurde, was bewusst bleibt

**Fehlte im Vergleich zu Odoo 11 (ergaenzt):**

1. **Zahlungsbetrag war nicht pflichtig.** Odoo 11 fuehrt `amount` modellpflichtig, Odoo 18 nicht
   (weder Modell noch Ansicht). -> `required="1"` in der Ansicht.
2. **Zahlungsmethode war in unserer Ansicht nicht pflichtig**, obwohl Odoo 18 selbst die
   Zahlungsmethode auf seinem (versteckten) Basisfeld als pflichtig fuehrt und Odoo 11 sie
   modellpflichtig hatte. -> `required="1"`.
3. **Doppeltes Partnerfeld bei Lieferantenzahlungen.** Odoo 18 fuehrt `partner_id` im Odoo-18-Block
   zweimal (Kunden- und Lieferanten-Variante, je mit eigener Sichtbarkeitsbedingung).
   `position="attributes"` wirkt nur auf den **ersten** Treffer - die Lieferanten-Variante blieb
   sichtbar und erschien als zweites, leeres Feld "Lieferant" neben unserem Feld "Partner".
   -> zweite Variante ueber ihre Position in der Gruppe ausgeblendet (`string` ist als Selektor
   verboten: "View inheritance may not use attribute 'string' as a selector").

**Verschoben / ausgeblendet und warum:**

| Feld | vorher | jetzt | Grund |
|---|---|---|---|
| itk_o11_payment_number | im Odoo-11-Block (rechts unter Memo) | Gruppe "Herkunft (Migration)" | Migrationsfeld, in Odoo 11 nicht vorhanden |
| state (Status (Odoo 18)) | im Odoo-11-Block | Gruppe "Status (Odoo 18)" | Kontrollwert; fachliche Anzeige ist die Odoo-11-Kette |
| partner_id (Lieferanten-Variante) | sichtbar (Doppelung) | ausgeblendet | Doppelung desselben Feldes |

**Bewusst erhaltene Odoo-18-Zusatzfunktionen:** Kopfknoepfe Bestaetigen, Validieren, Ablehnen,
Erstattung, Abbrechen, Stornierung anfordern, Als gesendet markieren, Nicht mehr als gesendet
markieren, setze auf Entwurf; Felder Zahlungsmethode als Journalzeile, Zahlungstoken,
Bankkonten, Erstattungsbetrag, duplizierte Zahlungen; Smart Buttons Rechnungen (Kunden und
Lieferanten), Kontoauszugszeilen/Transaction, Buchungsbeleg (gruppenbeschraenkt), Erstattungen;
Chatter und Reiter unveraendert. Es wurde **keine** Odoo-18-Funktion entfernt.

## 7. Abrechnung > Einkauf > Zahlungen

Verkauf und Einkauf nutzen **dasselbe Formular** (`account.payment`, Aktionen 330 "Kundenzahlungen"
und 331 "Lieferantenzahlungen"); unterschieden wird nur ueber den Aktionskontext
(`default_payment_type`, `default_partner_type`) und die Listenfilter. Im Browser geprueft
(Testzahlung Lieferant, outbound/supplier):

- gleiche Feldreihenfolge und gleiche Beschriftungen wie im Kundenfall
  (Zahlungsart, Partnertyp, Partner, Zahlungsbetrag, Zahlungsjournal, Zahlungsmethode /
  Zahlungsdatum, Memo, Zahlungstransaktion)
- genau **ein** Partnerfeld, genau ein Journal-, Datums- und Memofeld (Doppelung behoben)
- dieselbe technische Gruppe "Herkunft (Migration)" / "Status (Odoo 18)"
- unterschiedlich nur: Smart Button "Rechnungen" zeigt die verknuepften Eingangs- bzw.
  Ausgangsrechnungen; die Bankkontobeschriftung folgt dem Partnertyp
  ("Bankkonto des Lieferanten" / "Bankkonto des Kunden" / "Bankkonto des Unternehmens")

## 8. Abnahme im echten Browser

`scripts/browser_zahlungsformular_abnahme.py lokal|vm` - **lokal 19 OK / 0 FEHL, VM 19 OK / 0 FEHL**:

```
OK  Odoo-11-Beschriftungen vollstaendig und in Odoo-11-Reihenfolge
OK  Odoo-11-Zahlungsnummer erscheint nach dem Odoo-11-Block
OK  technische Gruppen "Herkunft (Migration)" und "Status (Odoo 18)" vorhanden
OK  keines der technischen Felder steht im Odoo-11-Block
OK  Zahlungsbetrag, Zahlungsmethode, Zahlungsart, Journal, Datum pflichtig
OK  Schriftgewicht aller Beschriftungen einheitlich (500)
OK  heller nur readonly/leere Felder (Odoo-18-Standard)
OK  Odoo-11-Statuskette sichtbar (Entwurf/Gebucht/Abgestimmt/Abgebrochen)
OK  Odoo-18-Rohstatus in der technischen Gruppe
OK  Smart Button "Rechnungen" nur bei verknuepfter Rechnung (wie Odoo 11)
OK  Lieferantenzahlung: gleiche Beschriftungen, genau ein Partner-/Journal-/Datums-/Memofeld
OK  Testdaten entfernt, Bestand unveraendert
```

Screenshots: `Desktop/Odoo18-Abnahme-Session126/zahlungsformular_abnahme/<instanz>/`.
Testdaten: lokal id 28/29, VM id 24/25 angelegt und restlos entfernt (Bestand lokal 10, VM 11
vorher = nachher).

## 9. Entscheidungen von Anna (05.10.2026)

**1. Auswahlwortlaut Zahlungsart bleibt Odoo-18-Standard ("Senden" / "Erhalten").**
Keine technische Umstellung auf den Odoo-11-Wortlaut ("Geld schicken" / "Geld erhalten"), weil
dafuer die Auswahlwerte bzw. Uebersetzungen des `account`-Moduls ueberschrieben werden muessten und
ein Modul-Upgrade das zuruecksetzen kann. Massgeblich ist die fachlich richtige Bedeutung und die
Migration, nicht eine riskante kosmetische Anpassung. Damit entfaellt der Punkt als offener Punkt;
die Abweichung bleibt allein sprachlich und ist hier dokumentiert.

**2. Die Odoo-18-Smart-Buttons bleiben vollstaendig erhalten.** Es wird **kein** kuenstlicher
Odoo-11-Knopf "Zahlungsabstimmung" nachgebaut, weil es dafuer keine 1:1-Entsprechung gibt.
Entscheidend ist, dass die fachliche Funktion der Abstimmung vorhanden ist und die Verknuepfungen
bei der Migration korrekt uebernommen werden. Beides ist gegeben:

```
Funktion in Odoo 18 vorhanden:
  reconciled_invoice_ids / reconciled_bill_ids   Abgestimmte Ausgangs-/Eingangsrechnungen
  reconciled_statement_line_ids                  Abgestimmte Kontoauszugszeilen
  move_id (Journalbuchung)                       Buchungsbeleg
  paired_internal_transfer_payment_id            gekoppelte interne Transferzahlung
  account.partial.reconcile                      Abstimmungspaare (im Bestand vorhanden)
  Smart Buttons: Rechnungen (Kunden/Lieferanten), Kontoauszugszeilen,
                 Buchungsbeleg (gruppenbeschraenkt), Erstattungen

Migration der Verknuepfungen (Regel, dokumentiert und im Testlauf geuebt):
  docs/o11-o18-vergleich-abrechnung-teil5-feldabbildung.md, Punkt Zahlungen (B3):
    "Historische Zahlungen werden ueber die Abstimmung abgebildet (Zahlung, Bankjournal BNK1,
     Memo = Rechnungsnummer). Zahlungsnummern des Altsystems werden nicht neu vergeben;
     Rechnungen als bezahlt ausweisen."
  docs/o11-o18-testmigration-regel.md, Schritt 4:
    "Zahlungen: Zahlung mit Methode und Journal, danach Abstimmung ueber
     reconciled_invoice_ids/reconciled_bill_ids; Odoo-11-Zahlungsnummer in
     itk_o11_payment_number."
```

**Status:** Das Zahlungsformular gilt damit als **geprueft** (Abnahme 19 OK / 0 FEHL je Instanz).
Der Bereich **Abrechnung bleibt IN ARBEIT**, bis Anna ihn abschliessend kontrolliert.

## 10. Technische Hinweise (kein Handlungsbedarf)

1. **Beschriftung der Zahlungsmethode:** Odoo 11 zeigte "Manuell", Odoo 18 den Namen der
   Journalzeile ("Manuelle Zahlung (Bank)"). Stammdaten, nicht angetastet (aus B3 uebernommen).
2. **Zahlungstransaktion bleibt heller beschriftet**, weil das Odoo-18-Modul `account_payment`
   das Feld readonly fuehrt.

## 11. Nachtrag: Bedienfunktion "Zahlungstransaktion" (Anna, 05.10.2026)

Anlass: Im Odoo-18-Formular ist das Feld sichtbar, aber readonly - man kann nichts auswaehlen.
In Odoo 11 war es auswaehlbar. Vollstaendiger Vergleich der Bedienfunktion:

**1. Technisches Feld und Relation in Odoo 11**

```
account.payment.payment_transaction_id   Many2one -> payment.transaction
definiert vom Modul  : payment   (ir.model.fields id 5876, modules='payment')
readonly/required    : readonly=False, required=False, store=True
Formular             : account.payment.form, rechtes Feld unter Memo, ohne readonly-Attribut
```

**2. War es in Odoo 11 editierbar?** Ja. Modellseitig `readonly=False`, im Formular als einfaches
Feld gefuehrt - also **manuell auswaehlbar**. Annas Beobachtung ist damit bestaetigt.

**3. Welche Werte waren auswaehlbar?** Jeder Datensatz aus `payment.transaction`
(Zahlungstransaktion eines Zahlungsanbieters). Im Odoo-11-Produktivbestand: **0 Transaktionen**,
0 Zahlungstokens, 10 konfigurierte Zahlungsanbieter (`payment.acquirer`), alle ungenutzt.

**4. Welche Geschaeftslogik hing daran?** Das Feld verbindet die Zahlung mit ihrer
Online-Transaktion. Es wird vom Zahlungsanbieter-Framework gesetzt (Transaktion -> Zahlung) und von
diesem fuer Zustands- und Erstattungslogik gelesen. Eine manuell eingetragene fremde Transaktion
hatte keine unterstuetzte Funktion.

**5. Tatsaechliche Nutzung in Odoo 11 (Auftrag):**

```
Zahlungen gesamt                 5.994
mit Zahlungstransaktion              0   (0 %)
mit Zahlungstoken                    0
payment.transaction                  0
payment.acquirer                    10   (konfiguriert, nie verwendet)
payment_reference                    0
```
Die manuelle Auswahl wurde in Odoo 11 also **nie** benutzt.

**6. Wie ist dieselbe Funktion in Odoo 18 vorgesehen?** Feld `payment_transaction_id`
(Many2one -> payment.transaction), definiert im Modul **`account_payment`** ("Payment - Account",
Zahlungen aus Online-Transaktionen), dort **readonly=True**. Die Verknuepfung stellt das
Zahlungssystem automatisch her:

```python
account_payment/models/account_payment.py
  action_post()                      # Knopf "Bestaetigen"
    payments_need_tx = filter(p -> p.payment_token_id and not p.payment_transaction_id)
    transactions = payments_need_tx.sudo()._create_payment_transaction()
    ...
      payment.payment_transaction_id = transaction   # Link the transaction to the payment
account_payment/models/payment_transaction.py
  _create_payment(): erzeugt die Zahlung mit 'payment_transaction_id': self.id
```

Voraussetzung ist eine elektronische Zahlungsmethode mit gespeichertem Token
(`payment_token_id`); `use_electronic_payment_method` steuert die Sichtbarkeit.

**7. Ist das readonly in Odoo 18 beabsichtigt?** Ja. Das Feld gehoert dem Zahlungssystem und
steuert Logik: Erstattung (`source_transaction_id`), Tokens, Zustaende
(done/pending/authorized), Referenz/Vermerk. Odoo 18 zeigt es in seiner eigenen Ansicht sogar nur
technisch und nur fuer elektronische Zahlungen:

```
account_payment/views/account_payment_views.xml:29
  <field name="payment_transaction_id" groups="base.group_no_one"
         invisible="not use_electronic_payment_method"/>
```

**8. Gibt es in Odoo 18 andere Wege zur selben Verknuepfung?** Ja, drei Standardwege - ohne
manuelle Feldauswahl:

1. Knopf **"Bestaetigen"** (`action_post`) bei Zahlung mit elektronischer Methode/Token erzeugt und
   verknuepft die Transaktion automatisch.
2. **Online-Zahlung des Kunden** (Portal "Jetzt bezahlen"): die Transaktion erzeugt die Zahlung
   samt Verknuepfung.
3. Assistent **`payment.link.wizard`** ("Zahlungslink", Modul `payment`; Verkaufsvariante in
   `sale`): erzeugt einen Zahlungslink, die Zahlung entsteht verknuepft.

**Ergebnis (Antwort auf die vier Fragen)**

| Frage | Antwort |
|---|---|
| 1. Odoo-11-Verhalten | Feld sichtbar und manuell auswaehlbar (readonly=False) - in der Praxis nie verwendet (0 von 5.994 Zahlungen, 0 Transaktionen) |
| 2. Odoo-18-Standard | Feld bewusst readonly; Verknuepfung automatisch durch das Zahlungssystem (action_post mit Token, Online-Zahlung, Zahlungslink); Odoo 18 zeigt das Feld selbst nur mit technischen Features und bei elektronischen Zahlungsmethoden |
| 3. funktional gleichwertig | **Ja** - die fachliche Funktion (Zuordnung Zahlung <-> Online-Transaktion) ist vollstaendig vorhanden und zusaetzlich abgesichert; die Odoo-11-Manualauswahl war ungenutzt und kein unterstuetzter Geschaeftsvorgang |
| 4. Anpassung notwendig | **Nein** - Odoo-18-Standardlogik bleibt unveraendert; das Feld wird **nicht** kuenstlich editierbar gemacht und die Payment-Logik nicht angetastet. Es bleibt an der Odoo-11-Position sichtbar (readonly), weil Odoo 11 es dort zeigte |

**Nachweis im echten Browser (lokal und VM, identisch)**

```
Feld sichtbar, Beschriftung "Zahlungstransaktion"
DOM-Klassen    : o_field_widget o_readonly_modifier o_field_empty o_field_many2one
Eingabefelder  : 0  -> nicht bedienbar (kein Eingabe-/Auswahlfeld)
Wert           : leer; Label-Deckkraft 0,66 (readonly und leer)
Felddefinition : readonly=True, many2one -> payment.transaction
Zahlung        : use_electronic_payment_method=False, payment_token_id=False,
                 payment_transaction_id=False, payment_method_code='manual'
Bestand        : payment.transaction 0, payment.token 0, payment.provider 17 (alle ungenutzt)
```

Werkzeug: `scripts/browser_zahlungstransaktion_check.py lokal|vm`; Screenshots
`Desktop/Odoo18-Abnahme-Session126/zahlungstransaktion/<instanz>/`.

**Entscheidung von Anna (05.10.2026): bewusst akzeptierte, fachlich gleichwertige Abweichung**

> "Die Zahlungstransaktion soll nicht kuenstlich editierbar gemacht werden. Bitte die
> Odoo-18-Standardlogik beibehalten. Da das Feld in Odoo 11 zwar auswaehlbar, aber in unseren
> produktiven Daten bei 0 von 5.994 Zahlungen verwendet wurde, ist keine Nachbildung der manuellen
> Auswahl erforderlich. Das Feld Zahlungstransaktion kann sichtbar und readonly bleiben, damit die
> Information bei zukuenftigen elektronischen Zahlungen vorhanden ist."

Festgehalten:

- **Keine Anpassung.** Odoo-18-Standardlogik bleibt unveraendert; kein zusaetzliches editierbares
  Feld, keine Aenderung an Modell, readonly-Attributen oder Payment-Logik.
- **Sichtbar und readonly** an der Odoo-11-Position - die Information steht bei kuenftigen
  elektronischen Zahlungen bereit (dann fuellt das Zahlungssystem sie automatisch).
- **Keine Nachbildung der manuellen Auswahl** aus Odoo 11 (dort 0 von 5.994 Zahlungen genutzt,
  0 Transaktionen im Bestand).
- Einstufung: **fachlich gleichwertig und bewusst akzeptiert** (Odoo-18-Zusatzlogik).
- Die von Odoo 18 selbst genutzte Sichtbarkeitsregel
  (`groups="base.group_no_one"`, `invisible="not use_electronic_payment_method"`) wird **nicht**
  uebernommen - das Feld bleibt wie in Odoo 11 immer sichtbar.
- Fuer die Migration ist nichts zu tun: in Odoo 11 gibt es keine Werte zu uebernehmen
  (0 Transaktionen, 0 Tokens).

Eingetragen in `docs/o11-o18-abrechnung-abschlussmatrix.md` Abschnitt 12.2 (Register der bewussten
Abweichungen).
