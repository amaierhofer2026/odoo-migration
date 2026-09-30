# R3 - Status `done` (Gesperrt): Zuordnung Odoo 11 -> Odoo 18

Stand: 29.09.2026, Session 121. **Nur Analyse.** Odoo 11 ausschliesslich read-only.
Fuer die Verhaltensbestaetigung wurde in Odoo 18 ein Testauftrag angelegt und wieder entfernt
(Bestand unveraendert); es war **keine Aenderung an Odoo 18 erforderlich**.

## 1. Ausgangslage Odoo 11 (gemessen)

```
sale.order.state (Auswahl, Anzeige):
  draft   "Angebot"          sent "Angebot gesendet"     sale "Verkaufsauftrag"
  done    "Gesperrt"         cancel "Abgebrochen"
Verteilung im Bestand:  sale 2.312 | cancel 147 | draft 5 | sent 0 | done 0
sale.order.line.state ist ein related Feld auf order_id.state (gleiche Auswahl);
  Verteilung: sale 3.770 | cancel 235 | draft 6 | done 0
Ein Feld "locked" gibt es in Odoo 11 nicht - die Sperre war ausschliesslich der Zustand 'done'.

Bedienung in Odoo 11 (Formular sale.order.form):
  <button name="action_done"   string="Sperre"    states="sale" help="Wenn der Auftrag gesperrt
      ist, koennen Sie diesen nicht mehr aendern. Allerdings koennen Sie immer noch eine Rechnung
      ausstellen oder eine Lieferung vornehmen."/>
  <button name="action_unlock" string="Entsperren" states="done"
      groups="sales_team.group_sale_manager"/>
Suchen/Filter in Odoo 11, die 'done' einschliessen:
  Bestaetigte Auftraege: domain [('state','in',('sale','done'))]
  Verkauf (Angebots-Suche): domain [('state','in',('sale','done'))]
```

## 2. Historischer Nachweis: 'done' wurde nie verwendet

```
Nachverfolgung (mail.tracking.value) aller Verkaufsauftraege, Feld "state":
  1.727 Zustandsaenderungen ausgewertet
  Wechsel nach "Gesperrt" (done): 0
  (Haeufigste Wechsel: Angebot -> Verkaufsauftrag 825, -> Quotation 511,
   Verkaufsauftrag -> Abgebrochen 46, Abgebrochen -> Angebot 42)
Ergebnis: Der Zustand 'done' wurde in Odoo 11 weder aktuell noch historisch verwendet.
  Die Zuordnungsregel ist damit vorsorglich, es ist kein Datensatz betroffen.
```

## 3. Gegenstueck in Odoo 18 (gemessen und am Servercode geprueft)

```
sale.order.state (Auswahl): draft, sent, sale, cancel  -> KEIN 'done'
sale.order.locked: Boolean, gespeichert, Anzeige "Gesperrt"  (gleicher Wortlaut wie Odoo 11)
Formular sale.order.form:
  <button name="action_lock"   string="Sperren"    help="Wenn der Verkauf abgeschlossen ist,
      koennen Sie diesen nicht mehr aendern. Allerdings koennen Sie immer noch eine Rechnung
      ausstellen oder eine Lieferung vornehmen."/>
  <button name="action_unlock" string="Entsperren" invisible="not locked"/>
  Feldschutz: readonly="state == 'cancel' or locked"; "Stornieren" ist bei locked ausgeblendet
Serverlogik (Modul sale, sale_order.py, gelesen im Container):
  action_lock()   -> locked = True
  action_unlock() -> locked = False
  action_cancel() -> verweigert das Stornieren, wenn locked: "You cannot cancel a locked order.
                     Please unlock it first."
Verhaltenstest mit Testauftrag (danach entfernt):
  Auftrag angelegt                      -> state=draft, locked=False
  state='sale' direkt gesetzt (Import)  -> state=sale, locked=False  (Sperre wird NICHT
                                           automatisch gesetzt; confirmation_date bleibt leer)
  locked=True gesetzt                   -> state=sale, locked=True
  action_unlock                         -> state=sale, locked=False
```

## 4. Transformationsregel (vorbereitet)

```
Odoo 11 state 'done' ("Gesperrt")  ->  Odoo 18 state='sale' UND locked=True
Alle uebrigen Zustaende 1:1:  draft -> draft, sent -> sent, sale -> sale, cancel -> cancel
  (bei 'sale' wird locked NICHT gesetzt - siehe Verhaltenstest; die Sperre muss explizit
   gesetzt werden, sonst waere ein Odoo-11-Auftrag nach der Migration entsperrt)
Auftragszeilen: kein Sonderfall - sale.order.line.state erbt in Odoo 18 ebenfalls von der
  Auftragszeile (related auf order_id.state)
Zusatzpruefung der Abhaengigkeiten:
  Die Odoo-11-Filter "Bestaetigte Auftraege" und "Verkauf" schlossen 'done' ein. In Odoo 18
  laufen gesperrte Auftraege weiterhin unter state='sale', deshalb decken die entsprechenden
  Odoo-18-Filter sie ohne Anpassung mit ab.
  Kein Odoo-18-Filter und keine Odoo-18-Regel verwendet den Wert 'done' (Pruefung der
  Verkaufsansichten: nur der Gruppenname "sale.group_auto_done_setting" enthaelt die Zeichenfolge)
Einordnung nach der Statusliste: "durch Odoo-18-Funktion ersetzt" (Zustand 'done' -> Feld `locked`),
Wortlaut "Gesperrt" bleibt identisch. Keine Aenderung an Odoo 18 erforderlich.
```

## 5. Abweichung beim Wortlaut (zur Kenntnis, Entscheidung offen)

```
Zustand 'cancel': Odoo 11 "Abgebrochen"  ->  Odoo 18 "Storniert"
Empfehlung: Odoo-18-Bezeichnung beibehalten und die Abweichung dokumentieren (wie bei den
  uebrigen Standardbezeichnungen; der Zustandswert 'cancel' selbst ist identisch).
Eine Umbenennung waere eine reine Anzeigeaenderung und ist nicht erforderlich.
```

## 6. Nachweise

```
Odoo 11: read-only RPC (read_group auf state, fields_get, Formulararchiv,
  mail.tracking.value der Verkaufsauftraege)
Odoo 18: fields_get, Formular-/Suchansicht, Servercode des Moduls sale im Container,
  Verhaltenstest mit Testauftrag (S00232) - Testauftrag wieder entfernt
Bestand nach der Analyse: lokal 18 Auftraege / 28 Zeilen / 13 Produkte / 0 Lagerbelege,
  VM 20 Auftraege / 29 Zeilen / 13 Produkte / 0 Lagerbelege (unveraendert)
Keine Datenmigration, keine Aenderung an Odoo 18.
```

## 7. Entscheidungen von Anna (29.09.2026) und Status

```
1. Transformationsregel BESTAETIGT:
   Odoo 11 state = 'done'  ->  Odoo 18 state = 'sale' UND locked = True
   Hintergrund: 'done' bedeutete in Odoo 11 fachlich "gesperrt"; Odoo 18 bildet diese Sperre
   ueber das Feld `locked` ab. Aktuell sind 0 Datensaetze betroffen - die Regel dient als
   sichere Fallback-Regel.
   Alle anderen Zustaende bleiben 1:1: draft, sent, sale, cancel.
   WICHTIG: Bei state = 'sale' darf `locked` NICHT automatisch gesetzt werden - nur dann, wenn
   der Odoo-11-Datensatz tatsaechlich im Zustand 'done' war. Der Verhaltenstest hat bestaetigt,
   dass Odoo 18 beim direkten Setzen von state='sale' das Feld `locked` unberuehrt laesst
   (locked bleibt False) - die Sperre wird ausschliesslich aus dem Odoo-11-Zustand 'done' abgeleitet.
2. Wortlaut 'cancel' BESTAETIGT: Die Odoo-18-Bezeichnung "Storniert" bleibt bestehen, keine
   Umbenennung auf "Abgebrochen". Der technische Status 'cancel' ist identisch; die abweichende
   sichtbare Bezeichnung wird nur dokumentiert.

STATUS: R3 ABGESCHLOSSEN (29.09.2026) - analysiert (read-only in Odoo 11, Servercode und
  Verhalten in Odoo 18 geprueft), Transformationsregel festgehalten, Entscheidungen eingetragen.
  Es war KEINE Aenderung an Odoo 18 erforderlich, keine bestehende Funktion wurde entfernt,
  keine Datenmigration durchgefuehrt, Testdaten vollstaendig entfernt.
Der Bereich Verkauf bleibt bis zur Vorbereitung der Risiken R4 bis R8 weiterhin NICHT endgueltig
abgeschlossen.
```
