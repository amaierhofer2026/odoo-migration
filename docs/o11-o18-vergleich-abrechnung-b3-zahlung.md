# Odoo 11 gegen Odoo 18 - Bereich Abrechnung, B3: Zahlung

Befund B3 aus Teil 3: Odoo 11 erfasst Zahlungen ueber den Dialog "Einzahlung erfassen"
(Aktion 178 auf das Formular von `account.payment`), Odoo 18 ueber den Assistenten
`account.payment.register`. Frage: deckt Odoo 18 den in Odoo 11 tatsaechlich verwendeten
Zahlungsweg vollstaendig ab?

Stand: 30.09.2026, Session 122. Arbeitsweise: Fertigstellung von Odoo 18 fuer die Migration.
**Odoo 11 wurde ausschliesslich lesend verwendet, es wurde nichts migriert.**
In Odoo 18 wurden fuer den Funktionstest Testdaten angelegt (Testdatenbank, siehe Abschnitt 8);
es war **keine Anpassung an Odoo 18 notwendig** (Begruendung in Abschnitt 6).

## 1. Vorgehen und Nachweise

| Quelle | Werkzeug | Inhalt |
| --- | --- | --- |
| Odoo 11 Prod (ITK_V1_a) | `ir.model.fields`, `fields_get` de_DE, `read_group`, `search_count`, Aktion 178 | Felder, Nutzung, Zahlungsarten, Journale |
| Odoo 18 lokal | `scripts/test_b3_zahlung.py` (Vorbelegung lesen, Zahlung anlegen, gegenpruefen) | Funktionstest ueber die Schnittstelle |
| Odoo 18 Test-VM im Browser | `scripts/browser_b3_zahlung.py` (Playwright) | echter Klickpfad Entwurf -> Buchen -> Zahlen -> Zahlung erstellen |
| Odoo 18 Quelldaten | Journal- und Zahlungsmethoden-Einstellungen, `account.payment.method.line` | Vergleich der Stammdaten |

## 2. Odoo 11: der verwendete Zahlungsweg (read-only gemessen)

```
Aktion 178 "Register Payment": ir.actions.act_window auf account.payment, view_mode form,
  target new, Kontext default_invoice_ids = aktive Rechnung
  -> der Anwender fuellt das Zahlungsformular direkt und bucht es ("Validate")
Zahlungen gesamt                       5.987
  mit Zahlungsart "Manuell"            5.987  (Modell account.payment.method, code=manual)
  Journal "Bank fuer Tirol und Vorarlberg AG (EUR)" (BNK1, Typ bank)   5.987
  Eingang (inbound)                    5.877
  Ausgang (outbound, Zahlung an Kunden)  110
  Partnerart "Kunde"                   5.987
  Zustand "Gebucht" (posted)           5.987
Feld communication (Memo) belegt       5.974  (Beispielwerte: R-261135, R-261106 = Rechnungsnummer)
Feld payment_date belegt               5.987
Abschreibungen (writeoff_account_id)       0  -> in Odoo 11 nie verwendet
Zahlungsdifferenz (payment_difference)     0  -> immer 0,00
payment_reference                          0
Sammelzahlungs-Assistent account.register.payments: vorhanden, aber 0 Belege (nie benutzt)
Bankauszuege / Online-Zahlungen            0
Zahlungsnummern                            CUST.IN/2019/0001 ... CUST.IN/2026/1061
```

Fachlich also: manuelle Zahlung auf das Bankjournal, Betrag, Datum, Memo (Rechnungsnummer),
Eingang oder Ausgang, Kunde, sofort gebucht und mit der Rechnung abgestimmt. Keine
Abschreibungen, keine Bankauszuege, keine Gruppenzahlung.

## 3. Odoo 18: der Zahlungsweg

Knopf "Zahlen" auf der gebuchten Rechnung (`action_register_payment`) oeffnet den Assistenten
`account.payment.register`. Im echten Browser auf der VM gemessene Felder und Vorbelegungen:

| Feld im Dialog | Vorbelegung | Entspricht in Odoo 11 |
| --- | --- | --- |
| Journal | Bank (BNK1, Typ bank) | Journal des Formulars |
| Zahlungsmethode | Manual Payment (Bank) | Zahlungsart "Manuell" |
| Betrag | offener Betrag der Rechnung | Betrag |
| Waehrung | EUR | Waehrung |
| Zahlungsdatum | Tagesdatum | Zahlungsdatum |
| Vermerk | Rechnungsnummer (z. B. RE/2026/0005) | Memo (R-...) |
| Bankkonto des Kunden | optional (Feld `partner_bank_id`) | im Odoo-11-Dialog nicht vorhanden (Zusatzfunktion) |

Knoepfe im Dialog: **"Zahlung erstellen"** (primaer) und **"Verwerfen"**.
Nicht angezeigt, aber vorhanden (Assistentenfelder): Zahlungsdifferenz mit Behandlung
"Offen halten" oder "Als vollstaendig bezahlt markieren", Differenzenkonto, Buchungstext,
"Zahlungen gruppieren", Waehrung des Benutzers. Diese Felder waren in Odoo 11 vorhanden
(Abschreibungen), aber ungenutzt.

Ohne Dialogaenderung erreichbar: Zahlung aus einer Gutschrift (Ausgang, "Zahlung an Kunden"),
was den 110 Odoo-11-Ausgangszahlungen entspricht.

## 4. Funktionstest lokal (Schnittstelle)

Werkzeug: `scripts/test_b3_zahlung.py --instanz lokal --ausfuehren`, Testrechnung
RE/2026/0001 (id 1, 3,60, Zustand gebucht, Zahlungszustand nicht bezahlt).

```
Vorbelegung des Assistenten: Journal Bank, Zahlungsmethode Manual Payment (Bank), Betrag 3,6,
  Waehrung EUR, Zahlungsdatum 30.09.2026, Vermerk RE/2026/0001, Zahlungsdifferenz 0,0
  ("Offen halten"), Partner Kunde, Zahlungsart Eingang
Ergebnis nach dem Ausfuehren:
  Zahlung id 8, PBNK1/2026/00002, 3,60, Memo RE/2026/0001, Zustand bezahlt, Journal Bank
  Buchungssatz: 2803 Ausstehende Eingaenge 3,60 Soll / 2000 Forderungen ... 3,60 Haben
  Rechnung RE/2026/0001: Zahlungszustand bezahlt, Restbetrag 0,00
  Zaehler: Zahlungen 7 -> 8, Teilabstimmungen 7 -> 8
```

## 5. Browser-Abnahme auf der VM (echter Klickpfad)

Werkzeug: `scripts/browser_b3_zahlung.py --instanz vm`, Ergebnis **16 OK / 0 FEHL**.
Ablauf auf der Test-VM (Entwurfsrechnung -> buchen -> zahlen):

```
OK  Knopf 'Bestaetigen' im Entwurf vorhanden und geklickt, Rechnung danach gebucht
OK  Knopf 'Zahlen' sichtbar und gefunden (Kopfzeile: Senden, Drucken, Zahlen, Vorschau,
    Gutschrift, Auf Entwurf zuruecksetzen)
OK  Dialog 'Zahlen' mit Journal (Bank), Zahlungsmethode, Betrag (78,00), Waehrung (EUR),
    Zahlungsdatum (30.09.2026), Vermerk (RE/2026/0005)
OK  Knoepfe 'Zahlung erstellen' und 'Verwerfen'
OK  nach 'Zahlung erstellen': Dialog geschlossen, Anzeige 'Bezahlt am 30.09.2026',
    Smart Button '1 Zahlungen'
OK  Gegenprobe Datenbank: Zahlungen 10 -> 11, Rechnung bezahlt (Rest 0,00),
    Zahlung PBNK1/2026/00005 mit Memo RE/2026/0005
OK  keine JavaScript-Fehler (0), keine RPC-Fehler (0)
```

Screenshots: `Desktop\Odoo18-Abnahme-Session122\b3\01_Zahlung_Dialog.png`,
`02_Zahlung_gebucht.png`.

## 6. Vergleich und Bewertung

| Frage | Odoo 11 | Odoo 18 | Bewertung |
| --- | --- | --- | --- |
| Zahlung erfassen | Dialog auf `account.payment` | Assistent `account.payment.register` | gleichwertig, ueberall belegt |
| Zahlungsart | Auswahl am Formular ("Manuell") | Feld "Zahlungsmethode" (Zeile am Journal) | gleichwertig, Beschriftung abweichend (Z2) |
| Betrag, Datum, Waehrung | vorhanden | vorhanden | gleich |
| Memo / Vermerk | `communication`, Wert = Rechnungsnummer | `memo`/`communication`, Vorbelegung Rechnungsnummer | gleich |
| Eingang / Ausgang | `payment_type` | `payment_type` | gleich |
| Abschreibung (Differenz) | vorhanden, nie genutzt (0) | vorhanden (Auswahl offen/vollstaendig bezahlt, Differenzenkonto) | keine Luecke, nichts nachbauen |
| Gruppenzahlung | technisch ueber Sammelassistent (ungenutzt) | "Zahlungen gruppieren" | Odoo-18-Zusatzfunktion bleibt |
| Zustand danach | Rechnung bezahlt, Zahlung gebucht | Rechnung bezahlt, Zahlung bezahlt | gleich |
| Abstimmung | automatisch beim Buchen | automatisch beim Erstellen | gleich |
| Nummernkreis der Zahlung | CUST.IN/2019/0001 | PBNK1/2026/00001 | Migrationspunkt (Z4) |

**Ergebnis: kein funktionaler Unterschied.** Der in Odoo 11 verwendete Zahlungsweg ist mit
Odoo-18-Bordmitteln vollstaendig abbildbar; eine Anpassung an Odoo 18 war nicht erforderlich.

### Offene Punkte (dokumentiert, keine Funktionseinbusse)

- **Z2 Zahlungsmethode-Beschriftung:** Odoo 11 zeigte "Manuell", Odoo 18 zeigt im deutschen
  Dialog "Manual Payment" (der Name der Zahlungsmethodenzeile am Journal ist nicht uebersetzbar,
  nur umbenennbar; das Feld `account.payment.method.name` selbst heisst de_DE "Manuelle Zahlung").
  Das ist eine reine Beschriftung. **Entscheidung erforderlich:** Zeilen umbenennen
  ("Manuelle Zahlung (Bank)") oder Odoo-18-Standard belassen und die Abweichung dokumentieren.
  Nach Ihrer Regel sind Zahlungsmethoden und Journale Stammdaten - ich habe sie daher nicht
  angetastet.
- **Z3 Journalname:** Odoo 11 fuehrt das Bankjournal als "Bank fuer Tirol und Vorarlberg AG (EUR)"
  (Code BNK1), der Testbestand als "Bank" (Code BNK1). Der Name gehoert zu den Stammdaten und
  wird bei der Migration gesetzt; der Code BNK1 passt bereits.
- **Z4 Zahlungsnummern:** Odoo 11 `CUST.IN/JJJJ/NNNN`, Odoo 18 `PBNK1/JJJJ/NNNNN`. Regel fuer
  historische Zahlungen gehoert in die Migrationsregeln (Teil 5); die Testdaten zeigen, dass die
  Reihenfolge pro Journal und Jahr laeuft.
- **Z5 Abschreibungen und Gruppenzahlungen** waren in Odoo 11 ungenutzt, in Odoo 18 aber
  vorhanden und getestet sichtbar (Feld "Zahlungsdifferenz" mit Auswahl). Nichts nachgebaut.
- **Z6 Bankauszuege, Online-Zahlungen, Zahlungstoken:** in Odoo 11 nicht verwendet, in Odoo 18
  als Zusatzfunktion vorhanden und unangetastet.

## 7. Nachweis, dass Odoo 11 unveraendert blieb

Alle Abfragen gegen Odoo 11 sind `search_read`/`search_count`/`read_group`/`fields_get`.
Es wurde keine Schreibmethode aufgerufen; es wurden keine Belege angelegt, geaendert oder
geloescht.

## 8. Angelegte Testdaten (transparent)

Funktionstests erzeugen Testdaten in der jeweiligen Testdatenbank (keine Produktivdaten,
keine Migration):

| Datenbank | Beleg | Inhalt |
| --- | --- | --- |
| lokal | `account.payment` id 8 (PBNK1/2026/00002) | Testzahlung 3,60 auf RE/2026/0001 |
| VM | `account.payment` id 9, 10, 11 (PBNK1/2026/00003 bis 00005) | Testzahlungen 78,00 / 94,80 / 78,00 |
| VM | Rechnungen id 41, 45, 46 | im Browser gebucht (RE/2026/0003 bis 0005) und bezahlt |

Die Testbelege sind an den Nummern PBNK1/2026/00002 ff. und den Rechnungsnummern
RE/2026/0003 ff. des Testbestands erkennbar.

## 9. Grenzen der Aussage

- Getestet ist der Zahlungsweg fuer Ausgangsrechnungen (Eingang) mit vollstaendiger Zahlung.
  Der Ausgangsfall (Zahlung an einen Kunden aus einer Gutschrift) ist im Dialog fachlich
  identisch, im Browser aber nicht geklickt; in Odoo 11 gab es dafuer 110 Belege.
- Teilzahlungen, Abschreibungen und Gruppenzahlungen wurden nicht ausgefuehrt, weil sie in
  Odoo 11 nicht vorkommen (0 Belege). Die Felder sind vorhanden und beschrieben.

## 10. Naechster Schritt

B6 Mailvorlagen (Versand), danach Teil 4 (Ansichten, Listen, Filter, Massenaktionen).
