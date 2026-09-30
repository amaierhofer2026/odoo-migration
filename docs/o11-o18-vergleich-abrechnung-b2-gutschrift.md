# Odoo 11 gegen Odoo 18 - Bereich Abrechnung, B2: Gutschrift (Assistent)

Befund B2 aus Teil 3: Odoo 11 erzeugt Gutschriften ueber den Assistenten `account.invoice.refund`,
Odoo 18 ueber `account.move.reversal`. Frage: ist die in Odoo 11 tatsaechlich verwendete
Gutschrift-Funktion in Odoo 18 fachlich vollstaendig abgedeckt?

Stand: 30.09.2026, Session 122. Reine Analyse und Dokumentation. **An Odoo 18 wurde nichts
geaendert, es wurde nichts migriert, Odoo 11 wurde ausschliesslich lesend verwendet.**

## 1. Vorgehen und Nachweise

| Quelle | Werkzeug | Inhalt |
| --- | --- | --- |
| Odoo 11 Prod (ITK_V1_a) | `ir.model.fields`, `fields_get` de_DE, `ir.ui.view` 578, `fields_view_get` | Felder, Beschriftungen, Pflichtfelder, Dialogaufbau |
| Odoo 11 Quellcode (Version 11.0) | `addons/account/wizard/account_invoice_refund.py`, `addons/account/models/account_invoice.py` | Fachlogik der drei Modi, Wirkung von `_prepare_refund` |
| Odoo 11 Prod Daten | `search_count`, `search_read`, `read_group`, `mail.message` | tatsaechliche Nutzung der 237 Gutschriften |
| Odoo 18 lokal und VM | `ir.model.fields`, `fields_get`, `ir.ui.view` 931, Quellcode `wizard/account_move_reversal.py`, `models/account_move.py` | Felder, Buttons, Fachlogik |
| Odoo 18 VM im Browser | `scripts/browser_b2_gutschrift.py`, `scripts/diag_b2_gutschrift_dialog.py` | Dialog im echten Browser, Vorbelegung, Buttons, Abbruch ohne Ausfuehrung |

Skripte: `scripts/analyse_abrechnung_b2_gutschrift.py`, `scripts/analyse_abrechnung_b2_wirkung.py`,
`scripts/browser_b2_gutschrift.py`, `scripts/diag_b2_gutschrift_dialog.py`.

## 2. Odoo 11: der Assistent `account.invoice.refund`

### 2.1 Sichtbare Felder (View 578, Modul `account`, unveraendert)

| Feld | Beschriftung de_DE | Typ | Pflicht | Bemerkung |
| --- | --- | --- | --- | --- |
| `filter_refund` | Rueckerstattungsmethode | Auswahl | ja | drei Werte, siehe 2.2 |
| `description` | Grund | Text (char) | ja | wird in die neue Gutschrift uebernommen |
| `date_invoice` | Gutschrift-Datum | Datum | ja | wird `date_invoice` und `date_due` der Gutschrift |
| `date` | Buchungsdatum | Datum | nein | Buchungsdatum der Gutschrift |
| `refund_only` | technisches Feld | Boolean | - | blendet die Methodenauswahl aus, wenn die Rechnung teilweise bezahlt ist |

Buttons im Dialog: **"Gutschrift hinzufuegen"** (`invoice_refund`, de_DE-Uebersetzung belegt) und
**"Cancel"**. Ein Feld "Referenz" gibt es im Assistenten nicht.

### 2.2 Die drei Modi (Quellcode `compute_refund`)

1. `refund` - "Gutschrift im Entwurf erstellen": Gutschrift wird im Zustand Entwurf angelegt,
   keine Abstimmung, keine Aenderung an der Rechnung.
2. `cancel` - "Abbrechen: Gutschrift erstellen und ausgleichen": Gutschrift wird angelegt und
   sofort gebucht (`action_invoice_open`) und mit den Forderungszeilen der Rechnung abgestimmt.
   Die Rechnung wird **nicht** auf Zustand Storno gesetzt - sie wird durch den Ausgleich bezahlt
   (die Beschriftung des Modus ist irrefuehrend).
3. `modify` - "Modifizieren: Gutschrift erstellen, ausgleichen und Rechnung im Entwurf erstellen":
   wie 2, zusaetzlich wird eine neue Entwurfsrechnung mit denselben Positionen angelegt.

Gilt `inv.reconciled` (Rechnung bereits abgestimmt), lehnen die Modi `cancel` und `modify` mit
einer Fehlermeldung ab; ist die Rechnung teilweise bezahlt, bietet der Assistent nur `refund` an.

### 2.3 Was der Assistent an der neuen Gutschrift setzt (Quellcode `_prepare_refund`)

```
Gutschrift erhaelt:  state = draft, number = False (neue Nummer aus dem Nummernkreis)
                     origin = Nummer der Rechnung (z. B. R-19519)
                     refund_invoice_id = Rechnung
                     name = Grund (Feld "Grund" aus dem Assistenten)
                     date_invoice = date_due = Gutschrift-Datum
                     payment_term_id = False, journal_id = Verkaufsjournal
Die Rechnung erhaelt: eine Chatter-Nachricht mit Betreff "Gutschrift" und dem Grund als Text
```

### 2.4 Tatsaechliche Nutzung in Odoo 11 (Messwerte, read-only)

```
Gutschriften (out_refund) gesamt        237
  davon bezahlt (abgestimmt)            222
  davon offen                            15
  davon Entwurf / Storno                   0 / 0
Ueber den Assistenten erzeugt           215  (= 215 Chatter-Nachrichten "Gutschrift" auf
                                              215 verschiedenen Belegen, genau die 215
                                              Gutschriften mit Ursprungsbezug und Begruendung)
Ohne Assistent erzeugt                   22  (kein Ursprungsbezug; davon 11 auch ohne Herkunft)
Mit Ursprungsrechnung                   215
Mit Begruendung im Feld name            215
Ausgangsrechnungen im Zustand Storno      0  (der Modus "Abbrechen" setzt die Rechnung nicht
                                              auf Storno, er gleicht nur aus - passt zum Quellcode)
Entwuerfe unter den Ausgangsrechnungen   14  (alle ohne Datum und mit Herkunft A-/NV-Nummern,
                                              kein Hinweis auf den Modus "Modifizieren")
Feld reference (Lieferantenreferenz)      0  (in Odoo 11 nie verwendet)
Feld name (Referenz/Beschreibung)     1.418  belegt, davon 215 Gutschriften mit Begruendung
```

Beispiele der Begruendungen: "irrtuemlich ausgestellt", "falsch fakturiert", "falsch ausgestellt".

## 3. Odoo 18: der Assistent `account.move.reversal`

### 3.1 Sichtbare Felder (View 931, Modul `account`) und Browser-Beschriftung

| Feld | Beschriftung im Browser (de_DE) | Typ | Pflicht |
| --- | --- | --- | --- |
| `reason` | Begruendung auf Gutschrift angezeigt | Text (char) | nein |
| `journal_id` | Journal | Auswahl | ja (im Dialog mit "?" markiert) |
| `date` | Stornodatum | Datum | nein (Vorbelegung: heutiges Datum) |

Technische Felder ohne Anzeige: `move_ids`, `move_type`, `residual`, `company_id`,
`available_journal_ids`, `new_move_ids`.

### 3.2 Buttons im Dialog

| Button | Methode | Wirkung |
| --- | --- | --- |
| Stornieren | `refund_moves` -> `reverse_moves(is_modify=False)` | Gutschrift im Entwurf, keine Abstimmung |
| Stornieren und Rechnung erstellen | `modify_moves` -> `reverse_moves(is_modify=True)` | Gutschrift mit Abstimmung und neue Entwurfsrechnung |
| Verwerfen | Abbrechen | Dialog schliessen |

### 3.3 Was der Assistent setzt (Quellcode `_prepare_default_reversal`, `reverse_moves`)

```
Gutschrift erhaelt:  ref = "Stornierung von: <Nummer der Rechnung>, <Begruendung>" (ohne
                          Begruendung nur "Stornierung von: <Nummer>")
                     reversed_entry_id = Rechnung
                     date = Stornodatum, invoice_date_due = Stornodatum
                     invoice_date = Stornodatum (bzw. Datum der Rechnung)
                     journal_id = gewaehltes Journal (gleicher Typ wie die Rechnung)
                     invoice_user_id = Verkaeufer der Rechnung
                     invoice_origin = Herkunft der Rechnung (NICHT die Rechnungsnummer)
                     auto_post = "at_date", wenn das Stornodatum in der Zukunft liegt, sonst "no"
Zustand:             Entwurf; bei einem Datum in der Zukunft wird die Gutschrift zum Datum
                     automatisch gebucht
Die Rechnung erhaelt: eine Chatter-Nachricht "Diese Buchung wurde storniert" mit Verweis
Abstimmung:          Stornieren: keine. Stornieren und Rechnung erstellen: die Rechnung wird
                     mit der Gutschrift abgestimmt (cancel=True) und zusaetzlich eine neue
                     Entwurfsrechnung angelegt.
Nummernkreis:        Journal "Kundenrechnungen" (RE) fuehrt refund_sequence = True, Gutschriften
                     bekommen also eine eigene Nummernfolge (Grundlage fuer K2a)
```

## 4. Browser-Nachweis auf der VM (read-only)

Werkzeug: `scripts/browser_b2_gutschrift.py` gegen `https://k001959vsx.ipax.at`,
Beleg id 28, RE/2020/0001. Ergebnis **10 OK / 0 FEHL**:

```
OK  Button 'Gutschrift' gefunden
OK  Dialogtitel 'Gutschrift'
OK  Feld 'Begruendung' vorhanden (leer)
OK  Journal = 'Kundenrechnungen' und Datum = 30.09.2026 vorbelegt
OK  Buttons: Stornieren | Stornieren und Rechnung erstellen | Verwerfen
OK  Dialog mit 'Verwerfen' geschlossen, kein Beleg angelegt (57 vorher, 57 nachher)
OK  keine JavaScript-Fehler, keine RPC-Fehler
```

Screenshot: `Desktop\Odoo18-Abnahme-Session122\b2\01_Gutschrift_Dialog.png`.

## 5. Vergleich Funktion fuer Funktion

| Frage | Odoo 11 (`account.invoice.refund`) | Odoo 18 (`account.move.reversal`) | Bewertung |
| --- | --- | --- | --- |
| Sichtbare Felder | Methode (3 Werte, Pflicht), Grund (Pflicht), Gutschrift-Datum (Pflicht), Buchungsdatum | Begruendung, Journal (Pflicht), Stornodatum | gleichwertig; Odoo 18 mit Journalwahl statt Methodenwahl |
| Grund | Pflichtfeld, landet im Feld `name` der Gutschrift und als Chatter-Nachricht | freies Feld, landet im Feld `ref` (mit Nummer) und wird auf der Gutschrift angezeigt | vorhanden, anderes Zielfeld (siehe U3) |
| Datum | `date_invoice` (Pflicht) und `date` | ein Feld `date` (Stornodatum) fuer Buchungs-, Rechnungs- und Faelligkeitsdatum | gleichwertig, Odoo 18 feiner gekoppelt |
| Referenz | im Assistenten nicht vorhanden; Feld `reference` in Odoo 11 nie benutzt (0) | `ref` wird automatisch gebildet ("Stornierung von: ...") | keine Luecke |
| Moegliche Aktionen | 3 Modi: Gutschrift im Entwurf / ausgleichen / ausgleichen + neue Entwurfsrechnung | 2 Knoepfe: Stornieren / Stornieren und Rechnung erstellen | der Sofort-Ausgleich des Odoo-11-Modus "Abbrechen" fehlt als eigener Knopf (siehe U1) |
| Wirkung auf Rechnung | "Abbrechen"/"Modifizieren" gleichen aus; Rechnung wird nicht auf Storno gesetzt; "Modifizieren" erzeugt neue Entwurfsrechnung | "Stornieren und Rechnung erstellen" gleicht aus und erzeugt neue Entwurfsrechnung | gleich, aber ein Schritt mehr (siehe U1) |
| Status danach | Gutschrift Entwurf (Modus 1) bzw. gebucht (Modi 2 und 3); Rechnung bezahlt | Gutschrift Entwurf (bzw. Automatikbuchung bei Zukunftsdatum); Rechnung abgestimmt und bezahlt | gleich |
| Verknuepfung Rechnung zu Gutschrift | `refund_invoice_id` (Gutschrift) und `refund_invoice_ids` (Rechnung, 212 belegt), zusaetzlich `origin` = Rechnungsnummer | `reversed_entry_id` und `reversal_move_ids`; `invoice_origin` uebernimmt die Herkunft der Rechnung, die Rechnungsnummer steht nur im Text von `ref` | gleichwertig ueber eigene Felder; das Odoo-11-Muster "Nummer im Feld origin" hat kein direktes Gegenstueck (siehe U4) |
| Mehrfachauswahl | ueber die Liste moeglich (`active_ids`) | moeglich (`move_ids`), Dialog zeigt Restbetrag | gleich |
| Nummernvergabe | eigene Nummer aus dem Verkaufsnummernkreis | eigene Nummer aus der Gutschriftenfolge (`refund_sequence = True`) | Grundlage fuer K2a |

## 6. Unterschiede und Vorschlaege (noch nichts umgebaut)

### U1 - Sofort-Ausgleich beim Erstellen fehlt als eigener Weg (kleine Luecke, kein Verlust)

Odoo 11 Modus "Abbrechen" erzeugt die Gutschrift, bucht sie sofort und stimmt sie mit der
Rechnung ab - in einem Schritt. Odoo 18 kennt diesen Knopf nicht: "Stornieren" legt die
Gutschrift nur im Entwurf an; der Anwender muss sie buchen und anschliessend abstimmen.
Der Modus "Modifizieren" ist als Knopf "Stornieren und Rechnung erstellen" vorhanden.
**Vorschlag:** nichts umbauen. Der Weg ueber "buchen + abstimmen" ist Odoo-18-Standard und
erzeugt dasselbe Ergebnis (Rechnung abgestimmt, bezahlt). Wenn Sie den Kurzweg dennoch
wollen, waere es ein eigener, freizugebender Umbau (Knopf im Dialog mit Aufruf
`reverse_moves` und anschliessender Abstimmung) - das ist eine Funktion auf dem
Odoo-18-Standard, keine Migrationsvoraussetzung.

### U2 - Zukunftsdatum bucht die Gutschrift automatisch

Odoo 18 setzt `auto_post = at_date`, wenn das Stornodatum in der Zukunft liegt, und bucht die
Gutschrift dann automatisch. Odoo 11 kannte das nicht.
**Auswirkung auf die Migration:** historische Stornodaten liegen in der Vergangenheit, deshalb
greift die Automatik nicht. Beim Import ist `auto_post` bewusst auf `no` zu setzen, damit keine
Gutschrift nachtraeglich automatisch gebucht wird. **Vorschlag:** als Importsregel in Teil 5
vormerken, jetzt nichts aendern.

### U3 - Zielfeld fuer den Grund (215 Gutschriften betroffen)

Odoo 11: der Grund steht im Feld `name` der Gutschrift (Feld "Referenz/Beschreibung", in
Odoo 11 in 1.418 Belegen belegt) und zusaetzlich in der Chatter-Nachricht.
Odoo 18: `name` ist die Belegnummer - das Feld "Beschreibung" gibt es nicht. Der Assistent
schreibt den Grund in `ref` ("Stornierung von: R-19519, falsch fakturiert").
**Befund:** im Feldinventar (Teil 2) ist fuers Odoo-11-Feld `name` kein Ziel definiert;
die 215 Begruendungen wuerden beim Import sonst verloren gehen.
**Vorschlag (nicht umgesetzt):** beim Import `ref` nach Odoo-18-Muster bilden
("Stornierung von: <alte Nummer>, <alter Grund>") und zusaetzlich die Odoo-11-Begruendung in
der Chatter-Nachricht der Gutschrift mitschreiben (die Odoo-11-Chatter-Nachricht "Gutschrift"
mit dem Grund wird ohnehin als Nachricht mitmigriert). Damit bleibt der Grund an zwei Stellen
nachvollziehbar, ohne ein neues Feld. Wenn Sie ein eigenes Feld wuenschen, waere das
gemeinsam mit dem Feld "Odoo-11-Rechnungsnummer" aus K2a zu entscheiden.

### U4 - Herkunft der Gutschrift: Nummer der Rechnung gegen Herkunft der Rechnung

Odoo 11 setzt `origin` der Gutschrift auf die **Nummer der Rechnung** (215 mal belegt).
Odoo 18 setzt `invoice_origin` auf die **Herkunft der Rechnung** (z. B. `NV-00962`) und
stellt die Rechnungsnummer nur in den Text von `ref`.
**Vorschlag (nicht umgesetzt):** beim Import `invoice_origin` wie in Odoo 18 ueblich aus der
Herkunft der Rechnung fuellen und `reversed_entry_id` setzen; die Odoo-11-Herkunft
(`origin` = Rechnungsnummer) geht damit nicht verloren, weil die Nummer im `ref`-Text steht.
Regel in Teil 5 vormerken.

### U5 - 22 Gutschriften ohne Ursprungsbezug

22 der 237 Gutschriften wurden nicht ueber den Assistenten erzeugt (kein `refund_invoice_id`),
11 davon haben auch keine Herkunft. Beim Import bleibt bei diesen Belegen der Bezug leer.
**Vorschlag:** nichts rekonstruieren, Luecke dokumentieren. Eine Zuordnung von Hand waere eine
fachliche Entscheidung, die nur mit Ihren Daten moeglich ist.

### U6 - Teilweise bezahlte Rechnungen

Odoo 11 bietet bei teilweise bezahlten Rechnungen nur den Modus "Gutschrift im Entwurf"
(`refund_only`). Odoo 18 schraenkt nicht ein.
**Bewertung:** keine Luecke, Odoo 18 ist grosszuegiger.

### U7 - Mehrfachauswahl unterschiedlicher Belegarten

Odoo 11 arbeitet mit einer Rechnungsliste, Odoo 18 mit `move_ids` und prueft, dass alle Belege
derselben Firma angehoeren und gebucht sind; bei gemischten Belegarten bleibt der Knopf
"Stornieren und Rechnung erstellen" ausgeblendet (`invisible` auf `move_type == 'entry'`).
**Bewertung:** keine Luecke, Verhalten dokumentiert.

## 7. Antwort auf die Leitfrage

Die in Odoo 11 tatsaechlich verwendete Gutschrift-Funktion ist in Odoo 18 fachlich abgedeckt:

- Gutschrift mit Begruendung, Datum und Journal: vorhanden (Zielfeld `ref` statt `name`, U3).
- Gutschrift im Entwurf belassen (Odoo-11-Modus 1): entspricht "Stornieren" (Bruch 215/215).
- Gutschrift ausgleichen und Rechnung abrechnen (Odoo-11-Modus 2): in Odoo 18 mit einem
  zusaetzlichen manuellen Schritt (buchen und abstimmen), Ergebnis identisch (U1).
- Gutschrift ausgleichen und neue Entwurfsrechnung (Odoo-11-Modus 3): entspricht "Stornieren
  und Rechnung erstellen" (U1).
- Verknuepfung Rechnung zu Gutschrift: ueber `reversed_entry_id` / `reversal_move_ids`
  (U4, Umstellung der Herkunftsregel beim Import).
- Nummernvergabe: eigene Gutschriftenfolge, passt zur Entscheidung K2a.

Offen bleiben damit nur Punkte, die keine Funktion betreffen, sondern die Migration der Altdaten:
Zielfeld fuer den Grund (U3), Herkunftsregel (U4), 22 Gutschriften ohne Bezug (U5) und die
Importsregel `auto_post = no` (U2).

## 8. Grenzen der Aussage

- Der Assistent wurde im Browser nur geoeffnet und wieder verworfen (read-only). Die Wirkung der
  beiden Knoepfe ist aus dem Quellcode der VM belegt und aus der Odoo-11-Datenlage
  nachvollzogen; sie wurde bewusst nicht ausgefuehrt, weil dabei Belege entstehen.
- Welchen der drei Odoo-11-Modi die Anwender im Einzelfall gewaehlt haben, laesst sich aus den
  Daten nicht rekonstruieren (der Modus wird nicht gespeichert). Fuer die Migration ist das
  ohne Belang, weil nur das Ergebnis zaehlt (Gutschrift, Zustand, Ausgleich, Verknuepfung).
- Die Odoo-11-Quellcodeaussagen stammen aus dem Zweig `11.0` des Odoo-Repositoriums, nicht aus
  dem laufenden Produktivstand; die Datenlage (222 bezahlte, 15 offene Gutschriften, 0 Storno)
  passt dazu.

## 9. Entscheidungen von Anna (30.09.2026) - verbindlich

```
Arbeitsweise Abrechnung ab 30.09.2026: Befunde nicht mehr einzeln analysieren und stoppen.
  Ziel ist die tatsaechliche Fertigstellung von Odoo 18 fuer die spaetere Datenmigration.
  Odoo 11 ausschliesslich read-only; keine Datenmigration; Odoo 18 direkt anpassen, wenn die
  fachliche Loesung eindeutig ist; Odoo-18-Zusatzfunktionen nicht entfernen; nur bei echten
  fachlichen Entscheidungen mit mehreren sinnvollen Varianten stoppen.
B2 Gutschrift:
  - Odoo-18-Standard account.move.reversal verwenden (kein Nachbau des Odoo-11-Assistenten).
  - Verknuepfung Rechnung <-> Gutschrift ueber reversed_entry_id und reversal_move_ids.
  - Den historischen Odoo-11-Grund bei der Migration erhalten und fachlich korrekt abbilden.
  - Ursprung und alte Rechnungsnummer nachvollziehbar erhalten.
  - Keine Rekonstruktion ungenutzter Odoo-11-Felder.
  - Den Odoo-18-Workflow (Stornieren, Stornieren und Rechnung erstellen, Verwerfen) beibehalten.
  - Den optionalen alten Kurzbefehl "Abbrechen / sofort ausgleichen" NICHT nachbauen, weil das
    fachliche Ergebnis mit Odoo-18-Bordmitteln erreicht wird (buchen und abstimmen).
```

Umsetzung dieser Entscheidungen:

| Punkt | Ergebnis |
| --- | --- |
| Odoo-18-Standard verwenden | keine Aenderung an Odoo 18 noetig: `account.move.reversal` ist aus Sicht von Teil 3 und B2 fachlich ausreichend (Dialog mit Begruendung, Journal, Stornodatum; zwei Wege plus Verwerfen) |
| Kein Nachbau des Odoo-11-Assistenten | keine Code-Aenderung; U1 wird bewusst nicht umgesetzt |
| Verknuepfung | Odoo 18 setzt `reversed_entry_id` (Gutschrift) und berechnet `reversal_move_ids` (Rechnung); beim Import wird die Verknuepfung ueber das Feld `refund_invoice_id` der Altdaten gesetzt (Regel Teil 5) |
| Historischer Grund erhalten | Mapping-Regel: Odoo-11-Feld `name` (Grund/Beschreibung) wird beim Import in `ref` nach Odoo-18-Muster geschrieben ("Stornierung von: <alte Nummer>, <alter Grund>") und bleibt zusaetzlich in der mitmigrierten Chatter-Nachricht erhalten. Nachtrag im Feldinventar Teil 2 |
| Ursprung und alte Nummer nachvollziehbar | `origin` der Altdaten (Nummer der Rechnung) bleibt als Text im `ref`; die alte Belegnummer wird zusaetzlich im geplanten Feld "Odoo-11-Rechnungsnummer" (K2a) gesichert; `invoice_origin` wird wie in Odoo 18 ueblich aus der Herkunft der Rechnung gebildet |
| Keine Rekonstruktion ungenutzter Felder | betrifft insbesondere den Odoo-11-Modus "Modifizieren" (kein Hinweis auf Nutzung) und das Odoo-11-Feld `reference` (0 Belege): nichts nachbauen, nichts rekonstruieren |
| Odoo-18-Workflow beibehalten | die drei Knoepfe und die Automatikbuchung bei Zukunftsdatum bleiben unveraendert; Importregel `auto_post = no` (U2) stellt sicher, dass die Automatik bei Altdaten nicht greift |

Damit ist B2 abgeschlossen: **keine Aenderung an Odoo 18 erforderlich**, alle offenen Punkte sind
Migrationsregeln fuer Teil 5 (U2, U3, U4, U5).

## 10. Naechster Schritt

B3 Zahlung (Odoo-11-Dialog "Einzahlung erfassen" gegen Odoo-18-Assistent
`account.payment.register`), danach B6 Mailvorlagen. Nichts davon begonnen.
