# Odoo 11 gegen Odoo 18 - Bereich Abrechnung, Teil 3

Formulare, Reiter, Buttons, Smart Buttons, Zustandswechsel, Zahlungs- und Abstimmungslogik,
Rechnungsdruck und Versand.

Stand: 30.09.2026, Session 122. Status: reine Analyse und Dokumentation, es wurde nichts umgebaut.
Odoo 11 wurde ausschliesslich lesend verwendet. Odoo 18 wurde nur gelesen, kein Upgrade, kein
Schreibvorgang (Nachweis in Abschnitt 9).

Grundlage der Aussagen:

| Quelle | Werkzeug | Zweck |
| --- | --- | --- |
| Odoo 11 Produktiv (ITK_V1_a) | scripts/analyse_abrechnung_teil3_arch.py, _details.py, _prozesse.py | Formularaufbau, Buttons, Bedingungen, Berichte, Vorlagen |
| Odoo 18 lokal (Testbestand) | dieselben Skripte, Modellabfragen | Formularaufbau, Buttons, Bedingungen |
| Odoo 18 Test-VM (k001959vsx.ipax.at) | scripts/browser_abrechnung_rechnung.py (Playwright, echter Browser) | sichtbares Verhalten im Browser |
| Odoo-18-Quellcode auf der VM | account/models/account_move.py | Bedeutung von Knoepfen (z. B. action_print_pdf) |

---

## 1. Formulare und Reiter

### Odoo 11: account.invoice (Formular)

| Reiter (Arch) | Reiter-Beschriftung |
| --- | --- |
| (ohne Name) | Rechnung (Positionen, Zahlungs-Widget, Restbetrag) |
| other_info | Andere Informationen |

Die Rechnung selbst ist ein eigener Reiter, weil Odoo 11 das Formular um das Feld
`payments_widget` (Zahlungen) und `outstanding_credits_debits_widget` (Guthaben und Vorschuesse)
herum aufbaut. Beide Felder liegen belegt im Arch.

### Odoo 18: account.move (Formular)

| Reiter (Arch, name) | Reiter-Beschriftung | im Browser sichtbar |
| --- | --- | --- |
| invoice_tab | Rechnungszeilen | ja |
| other_info | Weitere Informationen | ja |
| other_info (zweiter Abschnitt, Erweiterung) | Weitere Informationen | verschmilzt im Browser mit dem ersten Reiter |

Befund: In beiden Systemen sind im Browser zwei Reiter sichtbar. Odoo 18 hat einen zweiten
Arch-Abschnitt mit demselben Namen (`other_info`), der als Erweiterung an denselben Reiter
angehaengt wird - kein zusaetzlicher Reiter, keine Funktionseinbusse.

Im Reiter "Weitere Informationen" der gebuchten Testrechnung hat der Browser 16 Gruppen gelesen
(Kunde, Lieferadresse?, Valorisierungstext, Kundenreferenz, Vertriebsmitarbeiter, Verkaufsteam,
Empfaengerbank?, Zahlungsreferenz?, Liefer-/Leistungsdatum, Incoterm?, Incoterm-Standort,
Steuerposition?, Zahlungsmethode, Bargeldrundungsmethode?, Automatisch buchen?, Geprueft?).

---

## 2. Kopf-Buttons (Statusleiste) mit ihren Bedingungen

### Odoo 11: vier Knoepfe

| Knopf | Beschriftung | Typ | Ziel | Bedingung im Arch |
| --- | --- | --- | --- | --- |
| action_invoice_open | Bestaetigen | object | action_invoice_open | nur state = draft, hervorgehoben |
| 178 | Einzahlung erfassen | action | act_window 178 -> account.payment (form, target new, `default_invoice_ids`) | nur state = open, hervorgehoben |
| 241 | Nach Gutschrift fragen | action | act_window 241 -> account.invoice.refund (tree,form, target new) | sichtbar wenn type nicht in (in_refund, out_refund) und state in (open, paid) |
| action_invoice_draft | Auf Entwurf setzen | object | action_invoice_draft | nur state = cancel |

### Odoo 18: neunzehn Button-Eintraege (mehrere Auspraegungen je Dokumentart)

| Knopf | Beschriftung | Bedingung im Arch |
| --- | --- | --- |
| action_post | Buchen | move_type = entry, kein Zahlungshinweis aktiv |
| action_post | Bestaetigen | move_type ungleich entry |
| action_invoice_sent | Senden | state = posted und keine PDF-Rechnung vorhanden (zwei Auspraegungen) |
| action_print_pdf | Drucken | state = posted und keine PDF-Rechnung vorhanden (zwei Auspraegungen) |
| action_register_payment | Zahlen | state = posted und Zahlungszustand nicht bezahlt/abgebrochen (zwei Auspraegungen) |
| payment_action_capture | Transaktion erfassen | nur bei Online-Transaktionen |
| payment_action_void | Transaktion stornieren | nur bei Online-Transaktionen |
| preview_invoice | Vorschau | Ausgangsrechnung/Gutschrift, nicht Entwurf/Storno |
| 338 | Stornobuchung | nur Buchungen (move_type = entry) |
| action_reverse | Gutschrift | Ausgangs-/Eingangsrechnung im Zustand posted |
| button_cancel | Buchung stornieren / Abbrechen | nur Entwurf (zwei Auspraegungen) |
| button_draft | Auf Entwurf zuruecksetzen | abhaengig von `show_reset_to_draft_button` |
| button_hash | Sperren | nur wenn Journal Hashes fuehrt und noch nicht gesperrt |
| button_request_cancel | Stornierung anfordern | nur wenn Stornierungsantrag noetig |
| button_set_checked | Als geprueft markieren | nur wenn nicht geprueft und nicht Entwurf |
| action_cancel_peppol_documents | PEPPOL abbrechen | nur wenn PEPPOL-Versand offen |

Im Browser auf der VM, gebuchte und bezahlte Ausgangsrechnung RE/2020/0001:
sichtbar Senden, Drucken, Vorschau, Gutschrift, Auf Entwurf zuruecksetzen (plus die
Zustandspfeile Gebucht/Entwurf). Nicht sichtbar und fachlich korrekt ausgeblendet:
Bestaetigen/Buchen (bereits gebucht), Zahlen (bereits bezahlt), Stornobuchung (keine Buchung),
Sperren (Journal ohne Hash), PEPPOL (kein offener Versand).

---

## 3. Smart Buttons

| | Odoo 11 | Odoo 18 |
| --- | --- | --- |
| Smart Buttons im Rechnungsformular | keine | 8 definiert |
| Zahlungsinformationen | ueber die Felder `payments_widget` und `outstanding_credits_debits_widget` im Formular | ueber Smart Button "Zahlungen" (Feld `payment_count`) und Zahlungs-Widget |

Die acht Smart Buttons in Odoo 18 mit ihren Bedingungen:

| Smart Button | Bedingung |
| --- | --- |
| action_open_business_doc | nur Buchungen mit Zahlungsherkunft |
| open_payments (Zahlungen) | nur wenn `payment_count` ungleich 0 |
| open_reconcile_view | nur Buchungen mit Abstimmungen |
| open_created_caba_entries | nur bei Ist-Versteuerungsbuchungen (Odoo 11: nicht genutzt) |
| action_view_payment_transactions | nur wenn Online-Transaktionen vorhanden (Odoo 11: 0) |
| action_view_source_sale_orders (Verkaufsauftraege) | nur wenn `sale_order_count` ungleich 0 |
| action_purchase_matching | nur Eingangsrechnungen |
| action_view_source_purchase_orders | nur Eingangsrechnungen |

Browser-Nachweis: bei der bezahlten Testrechnung war genau ein Smart Button sichtbar,
Beschriftung "1 Zahlungen" (die Rechnung hat eine Zahlung).

Befund: Die Smart Buttons sind Odoo-18-Zusatzfunktion. In Odoo 11 gab es diesen Weg nicht,
die Zahlungsinformationen standen direkt im Formular. Kein Nachbau noetig, die Information
ist in Odoo 18 ueber den Smart Button und das Zahlungs-Widget erreichbar.

---

## 4. Zustandswechsel

### Odoo 11

```
Entwurf --[Bestaetigen / action_invoice_open]--> Offen --[Einzahlung erfassen / 178]--> Bezahlt
Storno  --[Auf Entwurf setzen / action_invoice_draft]--> Entwurf
Offen oder Bezahlt --[Nach Gutschrift fragen / 241]--> Assistent account.invoice.refund --> Gutschrift
```

Belegte Zustandswerte Odoo 11: Entwurf 14, Offen 43, Bezahlt 6.220, Storno 0.

### Odoo 18

```
Entwurf --[Bestaetigen bzw. Buchen / action_post]--> Gebucht
Gebucht --[Zahlen / action_register_payment]--> Zahlungszustand bezahlt oder teilweise
Gebucht --[Auf Entwurf zuruecksetzen / button_draft]--> Entwurf
Entwurf --[Abbrechen / button_cancel]--> Storno
Gebucht --[Gutschrift / action_reverse --> account.move.reversal]--> Gutschrift
Gebucht --[Sperren / button_hash]--> Nummer unveraenderlich (erst nach Migration nach K2c)
```

Unterschiede, die dokumentiert bleiben muessen:

1. Odoo 11 kennt den Zustand "Offen" (`state = open`, 43 Belege). Odoo 18 trennt Zustand
   (Entwurf/Gebucht/Storno) und Zahlungszustand (`payment_state`). Die 43 offenen Belege
   sind der einzige Zustandswert ohne direkte Entsprechung - Abbildungsregel folgt in Teil 5.
2. Odoo 11 "Auf Entwurf setzen" gilt nur fuer Storno-Belege, Odoo 18 "Auf Entwurf
   zuruecksetzen" gilt fuer gebuchte Belege (und nur, wenn die Buchhaltung das erlaubt).
   Fachlich derselbe Zweck, andere Ausgangslage.
3. Die Gutschrift entsteht in Odoo 11 ueber einen Assistenten mit Feldern (Grund, Datum),
   in Odoo 18 ueber `account.move.reversal`. Pruefauftrag (Befund B2): Feldinventar des
   Odoo-11-Assistenten gegen den Odoo-18-Weg legen, damit Grund und Referenz erhalten bleiben.

---

## 5. Zahlungs- und Abstimmungslogik

| Merkmal | Odoo 11 | Odoo 18 (lokal / VM, Testbestand) |
| --- | --- | --- |
| Zahlungsmodell | account.payment (5.987 Belege) | account.payment (7 / 7) |
| Zahlung mit Rechnungsbezug | 5.985 | ueber `reconciled_invoice_ids` |
| Zahlungsdialog aus der Rechnung | act_window 178 auf account.payment-Formular | action_register_payment -> Assistent account.payment.register |
| Sammelzahlungs-Assistent | account.register.payments vorhanden, 0 Belege (nicht benutzt) | account.payment.register (Standardweg) |
| Abstimmungen | 6.123 Teil-, 6.081 Vollabstimmungen | 7 / 7 |
| Abstimmungsmodelle | Modell vorhanden, mit dem Lesekonto nicht lesbar (kein Leserecht) | 4 (Odoo-Standard, zusaetzlich) |
| Bankauszuege | 0 Auszuege, 0 Auszugszeilen | 0 / 0 |
| Manuelle Abstimmung | Odoo-11-Client-Aktion (Menue Abrechnung) | in Odoo 18 durch Abstimmung auf Journalposten ersetzt |

Bewertung: Die Fachlogik ist gleich (Rechnung, Zahlung mit Rechnungsbezug, Abstimmung,
Zahlungszustand). Odoo 18 fuehrt den Zahlungszustand als eigenes Feld und bietet die Abstimmung
ueber Journalposten mit Abstimmungsmodellen. Die in Odoo 11 nicht genutzten Teile
(Bankauszuege, Sammelzahlung, Ist-Versteuerung, Online-Zahlungen) sind in Odoo 18 als
Zusatzfunktion vorhanden und bleiben erhalten.

Offener Pruefpunkt (Befund B3): Der Odoo-11-Zahlungsdialog fuehrt die Felder des
account.payment-Formulars direkt (Zahlungsart, Memo, Datum). Der Odoo-18-Assistent
account.payment.register fuehrt u. a. Zahlungsart, Journal, Datum, Referenz und
Gruppierungsoptionen. Vor der Migration ist abzugleichen, dass jede in Odoo 11 tatsaechlich
genutzte Angabe uebernommen werden kann.

---

## 6. Rechnungsdruck

### Odoo 11

| Bericht | Typ | Bindung |
| --- | --- | --- |
| id 537 "Rechnung" | qweb-pdf | gebunden an account.invoice |
| id 538 "Rechnung mit Zahlung" | qweb-pdf | gebunden an account.invoice |
| id 230 "Rechnungen ORG" | qweb-pdf | ohne Bindung |
| id 231 "Rechnungen ohne Zahlung ORG" | qweb-pdf | ohne Bindung |

Im Formular selbst gibt es in Odoo 11 keinen Drucken-Knopf: gedruckt wurde ueber die
Drucken-Auswahl des Aktionsmenues bzw. ueber die Listenansicht.

### Odoo 18

| Bericht | Bindung |
| --- | --- |
| id 323 "Invoice PDF" | keine Bindung |
| id 324 "Original Bills" | gebunden an Journal Entry |
| id 325 "PDF without Payment" | gebunden an Journal Entry |
| id 406 "Invoice report generated by Odoo" | keine Bindung (Odoo-Berichtsgenerator) |
| id 1231 "ITK-Rechnung" | gebunden an Journal Entry |

Im Formular gibt es in Odoo 18 einen eigenen Knopf "Drucken". Er ruft `action_print_pdf` auf
und erzeugt direkt das PDF der Standardvorlage (Quellcode account_move.py Zeile 5543 ff.:
`_get_default_pdf_report_id` und `report_action`).

Browser-Nachweis (VM): Klick auf "Drucken" hat das PDF `RE_2020_0001.pdf` erzeugt. Beide
Berichte sind ohne Anhangsablage eingestellt (`attachment_use = False`), es wurde also kein
Anhang und kein Schreibvorgang ausgeloest (Nachweis Abschnitt 9).

In der Formularansicht erschien im Aktionsmenue kein Eintrag "Drucken" (Browser-Beleg, VM).
Der Weg im Formular fuehrt ueber den Knopf. Der Mehrfachdruck aus der Liste ist Teil der
spaeteren Berichtsanalyse (Vorgabe K3: keine Berichte nachbauen, zuerst Nutzung feststellen).

---

## 7. Versand (E-Mail und Massenversand)

| Merkmal | Odoo 11 | Odoo 18 |
| --- | --- | --- |
| Versandkennzeichen | Feld `sent`, 2.549 Rechnungen als versendet markiert | Feld `is_move_sent` |
| Knopf im Formular | kein eigener Knopf (Versand ueber den Chatter bzw. Massenversand) | Knopf "Senden" (action_invoice_sent) |
| Assistent | mail.compose.message (Chatter) | account.move.send (Assistent mit Vorlagen, Anhaengen, Optionen) |
| Massenversand | Modul mass_email_invoice installiert (Menue Massenverarbeitung) | Modul mass_email_invoice installiert, Aktionsmenue "Massenversand Rechnungen per Email" (Browser-Beleg) |
| Mailvorlagen auf Rechnung | 9 Vorlagen (u. a. "Rechnung: ${object.company_name} Rechnung (Ref ${object.number})", "Rechnungsstellung: Allgemeine Rechnung", sowie 3 Mahnvorlagen) | 5 Vorlagen ("Invoice: Sending", "Credit Note: Sending", "Self-billing invoice: Sending", "Self-billing credit note: Sending", "Website Subscription: Payment success") |
| Felder im Formular | `sent` | `is_move_sent`, `is_being_sent`, `invoice_pdf_report_id`, `checked` |

Befunde:
- B6 (Vorlagen): Odoo 11 hatte 9 Vorlagen inkl. drei Mahnvorlagen. Odoo 18 bringt 5
  Standardvorlagen mit englischen Bezeichnungen. Die inhaltliche Angleichung der Vorlagen
  (ITK-Texte, Valorisierung, Betreffzeilen) ist ein eigener, noch nicht begonnener Punkt.
- B7 (Mahnwesen): In Odoo 11 liegen Mahnvorlagen, das Mahnmodul selbst ist nicht installiert.
  Vorgabe K7/K3: nicht nachbauen, in der Berichts-/Vorlagenanalyse pruefen.
- B8 (Sichtbarkeit "Senden"): Odoo 18 blendet "Senden" und "Drucken" aus, solange kein PDF
  erzeugt wurde, und zeigt stattdessen andere Wege (`is_being_sent`, `invoice_pdf_report_id`).
  Das ist Odoo-18-Verhalten, kein Fehler; bei der Abnahme zu beachten.

---

## 8. Browser-Nachweis auf der VM (read-only)

Werkzeug: scripts/browser_abrechnung_rechnung.py (Playwright mit echtem Chrome, headless),
Ziel: https://k001959vsx.ipax.at, Beleg id 28, RE/2020/0001, Breitenbrunn am Neusiedler See,
105,38, Zahlungszustand paid, 1 Zahlung. Ergebnis: 12 OK / 0 FEHL.

```
OK  Reiter 'Rechnungszeilen' sichtbar
OK  Reiter 'Weitere Informationen' sichtbar
OK  Statusleiste zeigt 'Gebucht'
OK  Button 'Senden' sichtbar
OK  Button 'Drucken' sichtbar
OK  Button 'Gutschrift' sichtbar
OK  Button 'Auf Entwurf zuruecksetzen' sichtbar
OK  Smart Button '1 Zahlungen' sichtbar
OK  Klick auf 'Drucken' erzeugt ein PDF (RE_2020_0001.pdf)
OK  Gruppen im Reiter 'Weitere Informationen' sichtbar (16)
OK  keine JavaScript-Fehler (0)
OK  keine RPC-Fehler (HTTP >= 400) (0)
```

Screenshots: Desktop/Odoo18-Abnahme-Session122/teil3/01_Rechnung_gebucht.png,
03_Weitere_Informationen.png.

Aktionsmenue der gebuchten Rechnung im Browser (VM): Herunterladen, Duplizieren, Loeschen,
Einen Zahlungslink erstellen, Massenversand Rechnungen per Email, Teilen,
"In Rechnung/Gutschrift umwandeln", Zahlen, "Zahlung sperren/entsperren",
"Zeilen pro Steuer (ent-)gruppieren", ZIP exportieren.

---

## 9. Nachweis, dass nichts geaendert wurde

| Pruefung | Ergebnis |
| --- | --- |
| Odoo 11 (portal.it-kommunal.at, ITK_V1_a) | ausschliesslich search_read, search_count, fields_view_get; keine Schreibmethode aufgerufen |
| Odoo 18 Test-VM | Beleg 28 unveraendert: `write_date = 2026-09-18 10:04:30`, `is_move_sent = False`, `invoice_pdf_report_id = False` |
| Anhaenge zu account.move auf der VM | 0 (auch kein neuer Anhang aus dem Drucken-Klick) |
| Berichte | `attachment_use = False` fuer "Invoice PDF" (323) und "ITK-Rechnung" (1231) |
| Odoo 18 lokal | nur Lesezugriffe (get_views, search_read, search_count) |

---

## 10. Befundliste (jeder Befund einzeln, nichts umgebaut)

| Nr. | Befund | Bewertung | Vorschlag |
| --- | --- | --- | --- |
| B1 | Odoo-11-Zustand "Offen" (43 Belege) hat in Odoo 18 keine Entsprechung im Feld `state` | offen, bereits in Teil 2 dokumentiert | Abbildungsregel (Zustand + Zahlungszustand) in Teil 5 festlegen |
| B2 | Gutschrift: Odoo 11 nutzt den Assistenten account.invoice.refund, Odoo 18 action_reverse | Funktionsgleichheit wahrscheinlich, nicht belegt | Feldinventar des Odoo-11-Assistenten gegen account.move.reversal legen (Grund, Datum, Referenz) |
| B3 | Zahlung: Odoo 11 oeffnet das account.payment-Formular, Odoo 18 den Assistenten account.payment.register | Funktionsgleichheit wahrscheinlich, nicht belegt | Feldabgleich Zahlungsart, Journal, Datum, Memo/Referenz vor der Migration |
| B4 | Abstimmung: Odoo 11 hatte Bankauszuege und Sammelzahlung ungenutzt, Odoo 18 bringt sie als Zusatzfunktion | keine Luecke | nichts nachbauen, Zusatzfunktionen erhalten |
| B5 | Druck: Odoo 11 hatte 2 gebundene Berichte (Rechnung, Rechnung mit Zahlung) und 2 freie "ORG"-Berichte, Odoo 18 hat 5 inkl. "ITK-Rechnung" | Nutzung in Odoo 11 offen | erst Berichtsanalyse (Vorgabe K3), nichts nachbauen |
| B6 | 9 Mailvorlagen in Odoo 11 gegen 5 Standardvorlagen in Odoo 18, Bezeichnungen englisch | Angleichung noetig, kein Fehler | Vorlagenpruefung als eigener Schritt (Texte, Betreff, Valorisierung) |
| B7 | Mahnvorlagen in Odoo 11 vorhanden, Mahnmodul nicht installiert | kein Bestandteil der Migration | dokumentiert lassen, nicht nachbauen |
| B8 | "Senden"/"Drucken" werden in Odoo 18 ausgeblendet, solange kein PDF vorliegt | Odoo-18-Verhalten | bei der Abnahme beachten, keine Anpassung |
| B9 | Smart Buttons (8) und PEPPOL-/Transaktionsknoepfe sind Odoo-18-Zusatzfunktion ohne Odoo-11-Gegenstueck | keine Luecke | erhalten, nicht entfernen |

---

## 11. Grenzen der Aussage

- Die Browser-Abnahme deckt eine gebuchte, bezahlte Ausgangsrechnung ab. Der Weg fuer
  Entwuerfe, Gutschriften und Eingangsrechnungen ist im Arch geprueft, aber nicht geklickt.
- Der Zahlungsweg (Assistent account.payment.register) wurde nicht geoeffnet und nicht
  ausgefuehrt: das ist Teil der spaeteren Funktionsabnahme, weil dabei Belege entstehen.
- Die Nutzung der acht Berichte in Odoo 11 ist nicht Gegenstand von Teil 3 (Vorgabe K3).

---

## 12. Naechster Schritt (Vorschlag, noch nicht begonnen)

```
Teil 4: Ansichten, Listen, Filter, Suche und Massenaktionen der Rechnung
Teil 5: Migrationsregeln und Feldabbildung (Zustand "Offen", K2a-Umsetzung, K1 Konten, K5 Steuern)
Teil 6: Berichtsanalyse (K3) und Vorlagen (B6)
```

Nichts davon ist begonnen. Umsetzungsvorschlaege zu den Befunden B2 bis B6 lege ich erst nach
Ihrer Freigabe vor.
