# Testmigration Abrechnung - Regel und Vorgehen (vorbereitet 05.10.2026, Session 123)

Zweck: Wenige, aber repraesentative Datensaetze aus Odoo 11 in die Odoo-18-Testinstanz
uebertragen, um Mapping, Beziehungen, Reihenfolge und Kontrollen zu belegen, **bevor** die echte
Migration laeuft. Die Testmigration ist ein Nachweis, kein Produktivlauf.

Status: vorbereitet, **noch nicht ausgefuehrt**. Ausfuehren nur nach ausdruecklicher Freigabe.

## 1. Grundregeln

- Quelle: Odoo 11 **Produktion, ausschliesslich lesend**. Es wird dort nichts angelegt, geaendert
  oder geloescht.
- Ziel: Odoo-18-**Testinstanz** (DB `odoo18_test`, VM oder lokal). Das Skript verweigert den Lauf
  gegen jede andere Datenbank.
- Testdaten werden nach der Pruefung wieder entfernt (`--aufraeumen`, siehe Abschnitt 7).
- Keine ID-Uebernahme. Jede Beziehung wird ueber einen fachlichen Schluessel aufgeloest:
  Partner ueber Name (+ GKZ/VAT), Produkt ueber Name/Code, Journal ueber Code, Konto ueber
  Kontocode (mit der dokumentierten Mapping-Tabelle), Steuer ueber Name und Satz,
  Zahlungsbedingung ueber Name.
- Berechnete Felder werden nicht migriert (Summen, Steuerzeilen, Zahlungsstatus,
  Abstimmungsmerkmale, Restbetrag, Kostenstellenverteilung); Odoo 18 rechnet sie neu.
- Jeder Fehler bricht ab. Es wird nichts still uebersprungen (gleicher Grundsatz wie beim
  Feldabdeckungsskript seit 05.10.2026).

## 2. Auswahl der repraesentativen Datensaetze

**Befund 05.10.2026 (read-only in der Produktion gemessen):** Odoo 11 enthaelt 6301 Rechnungen,
davon 6064 Kundenrechnungen (`out_invoice`) und 237 Kunden-Gutschriften (`out_refund`).
**Eingangsrechnungen und Lieferanten-Gutschriften gibt es dort nicht** (0 Datensaetze).
Zustaende: 12 Entwurf, 66 offen (`open`), 6223 bezahlt (`paid`) - ein Zustand `posted` existiert
in Odoo 11 nicht. Ein Lieferantenbeleg kann in der Testmigration daher nur kuenstlich auf der
Zielseite entstehen; die Odoo-18-Eingangsrechnungen der Abnahme sind Testdaten der Zielinstanz.

Die Auswahl trifft das Skript nach festen Regeln, damit sie reproduzierbar ist:

| Position | Regel |
|---|---|
| Ausgangsrechnung (gebucht) | Kundenrechnung mit `state in (open, paid)`, mit den meisten Zeilen, aber hoechstens 10 Zeilen |
| Ausgangsrechnung (Entwurf) | Kundenrechnung mit `state=draft`, hoechstens 10 Zeilen |
| Kunden-Gutschrift | `type=out_refund`, hoechstens 10 Zeilen |
| Eingangsrechnung / Lieferanten-Gutschrift | nur wenn in Odoo 11 vorhanden - derzeit nicht, das Skript meldet das und laesst den Schritt aus |
| Zahlung | eine Zahlung zu einer der gewaehlten Rechnungen, sonst die erste Zahlung insgesamt |
| Kunde Unternehmen | Partner aus der gebuchten Rechnung, wenn `is_company`; sonst erster Firmenkunde |
| Kunde Person | Partner aus der Kunden-Gutschrift, wenn keine Firma; sonst erste Person |
| Lieferant | Partner aus der Eingangsrechnung, sofern vorhanden |
| Produkte | alle Produkte, die in den gewaehlten Belegzeilen vorkommen (hoechstens 6) |
| Stammdaten | nur Journale, Konten, Steuern, Zahlungsbedingungen und Waehrungen, die diese Belege benutzen |

Regel S99 bleibt bindend: Gemeinde/Verband/Firma werden als Unternehmen gefuehrt, der
Ansprechpartner als Person.

## 3. Reihenfolge (aus `docs/o11-o18-abrechnung-abschlusspruefung.md`, Abschnitt 5)

1. Stammdaten: Journale, Konten, Steuern, Zahlungsbedingungen, Produkte, Partner
2. Beziehungen: Zahlungsbedingungen/Steuerzuordnung/Verkaeufer am Partner, Konten an Produkt und
   Kategorie, Kostenstellen
3. Belege: Rechnungen und Gutschriften mit Kopf und Zeilen; Odoo-11-Nummer zusaetzlich in
   `itk_o11_invoice_number` ablegen (Constraint `account_move_unique_name`)
4. Zahlungen: Zahlung mit Methode und Journal, danach Abstimmung ueber
   `reconciled_invoice_ids`/`reconciled_bill_ids`; Odoo-11-Zahlungsnummer in
   `itk_o11_payment_number`
5. Verknuepfungen und Status: Zahlungsstatus, Verkaeufer, Vertriebskanal
6. Kontrolle: Summenvergleich Odoo 11 gegen Odoo 18 (Anzahl Belege, Netto, Steuer, Brutto,
   Anzahl Zahlungen), danach Regression

## 4. Bekannte Constraints, die der Testlauf pruefen soll

- `account_move_unique_name` (Belegnummer je Journal und Unternehmen eindeutig)
- `account_journal_code_company_uniq`
- `account_payment_check_amount_not_negative`
- `account_move_line_check_accountable_required_fields` / `check_credit_debit` /
  `check_amount_currency_balance_sign`
- `res_partner_check_name`

## 5. Abbruchkriterien

Der Lauf bricht ab, wenn

- ein fachlicher Schluessel im Ziel nicht eindeutig aufloesbar ist (z.B. zwei Konten mit demselben
  Code oder ein Partner ohne Namen),
- ein Pflichtfeld im Ziel fehlt,
- eine Summe nach dem Anlegen nicht zur Odoo-11-Vorlage passt,
- ein Constraint verletzt wird.

## 6. Kontrolle nach dem Lauf

- Anzahl uebertragener Belege, Netto/Steuer/Brutto je Beleg gegen Odoo 11
- Anzahl Zahlungen und Abstimmungsstatus
- Browser-Blick auf die uebertragenen Belege in der Testinstanz (echter Browser, Screenshot)
- anschliessend Regression `scripts/abschluss_verkauf_regression.py` und
  `scripts/check_abrechnung_labels.py`

## 7. Aufraeumen

`--aufraeumen` entfernt genau die Datensaetze, die der Lauf angelegt hat. Dazu schreibt der Lauf
jede erzeugte ID mit Modell in das Protokoll (`docs/_testmigration_protokoll.json`); geloescht wird
nur, was dort steht, und nur in der Testinstanz. Belege werden dabei zuerst storniert bzw. in den
Entwurf gesetzt, dann entfernt.

## 8. Aufruf

```
python scripts/testmigration_abrechnung.py --instanz vm --plan           # nur Plan erzeugen (Standard)
python scripts/testmigration_abrechnung.py --instanz vm --ausfuehren     # ausfuehren (nur nach Freigabe)
python scripts/testmigration_abrechnung.py --instanz vm --aufraeumen     # Testdaten entfernen
```

`--plan` ist der Standard und schreibt nichts. `--ausfuehren` verlangt zusaetzlich
`--ich-habe-freigabe`, damit ein versehentlicher Lauf ausgeschlossen ist.
