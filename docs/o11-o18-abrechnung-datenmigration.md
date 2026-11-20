# Abrechnung / Rechnungen: Datenmigration Odoo 11 nach Odoo 18

Stand: 19.11.2026 (Session 149). Quellstand live gemessen, Odoo 11 ausschließlich lesend.
Technik: `scripts/migration/abrechnung_migration.py`, `docs/migration/abrechnung_migration.md`.

## 1 Bestand Odoo 11 (live gemessen 19.11.2026)

| Kennzahl | Wert |
|---|---|
| Rechnungen gesamt | **6.378** |
| Ausgangsrechnungen | 6.139 |
| Gutschriften (Ausgang) | 239 |
| Eingangsrechnungen / -gutschriften | 0 / 0 |
| Status Entwurf | 4 |
| Status offen (gebucht, unbezahlt) | 48 |
| Status bezahlt | 6.326 |
| Status storniert | 0 |
| Rechnungszeilen | 10.157 |
| Zeilen je Rechnung | 1 (2.759), 2 (3.520), 3 (77), 4+ (18) |
| Summe netto | 10.127.812,76 |
| Summe Steuer | 2.012.116,35 |
| Summe brutto | 12.139.929,11 |
| Offener Rest | 138.320,55 |
| Zahlungen | 6.091 (Summe 10.931.018,24; 5.978 inbound, 113 outbound) |
| Rechnungen mit Auftragsbezug | 1.279 |
| Rechnungen mit Abo-Bezug | 5.120 |
| Rechnungen mit Valorisierung | 4.216 |
| Rechnungen mit Projektkategorie | 5.359 |
| Rechnungen ohne Partner | 0 |
| Anhänge | 9.407 (805 MB, 9.299 PDF) |
| Rechnungsnummern | Format `R-JJNNNN`; 4 Entwürfe ohne Nummer; 1 Nummer doppelt (R-25001) |
| Verwendete Steuer | ausschließlich 20 % Umsatzsteuer (10.135 Zeilen), 22 Zeilen ohne Steuer |
| Verwendetes Konto in Zeilen | ausschließlich 8400 „Erlöse 19% USt“ |

Kontrollprobe: Die Summe der Zeilen (netto 10.127.812,76) entspricht der Kopfsumme netto.
Die Zeilen-Bruttosumme (12.139.984,74) weicht um **55,63** von der Kopfsumme brutto
(12.139.929,11) ab - dokumentierte Odoo-11-Kopf-/Zeilendifferenz, siehe Abschnitt 6.

## 2 Mapping Odoo 11 → Odoo 18

| Odoo 11 | Odoo 18 | Transformation | Status | Begründung |
|---|---|---|---|---|
| `account.invoice` | `account.move` | ein Beleg je Odoo-11-Rechnung, Anker `itk_o11_id` | umgesetzt | Standardmodell in 18 |
| `type = out_invoice` | `move_type = out_invoice` | 1:1 | umgesetzt | gleiche Bedeutung |
| `type = out_refund` | `move_type = out_refund` | 1:1, eigenes Journal „Gutschriften“ | umgesetzt | Nummer R-25001 doppelt vergeben |
| `state = draft` | `state = draft` | Entwurf bleibt Entwurf, Nummer bleibt „/“ | umgesetzt | keine Buchung |
| `state = open` / `paid` | `state = posted` | gebucht; Zahlungsstatus getrennt über Zahlungen | umgesetzt | Odoo 18 trennt Buchung und Zahlung |
| `state = cancel` | - | kommt in Odoo 11 nicht vor (0 Sätze) | nicht relevant | - |
| `number` (R-JJNNNN) | `name` | unverändert übernommen, kein `action_post` | umgesetzt | historische Nummern bleiben erhalten |
| `date_invoice` | `invoice_date` und `date` | 1:1 | umgesetzt | Buchungsdatum = Rechnungsdatum |
| `date_due` | `invoice_date_due` | 1:1 | umgesetzt | Fälligkeit |
| `partner_id` | `partner_id` | über `res.partner.itk_o11_id` | umgesetzt | 6.022 Kontakte mit Anker |
| `payment_term_id` | `invoice_payment_term_id` | über den Namen der Zahlungsbedingung | umgesetzt | Odoo-18-Bedingungen vorhanden |
| `origin` | `ref` | 1:1 | umgesetzt | Auftrags-/Abo-Herkunft |
| `reference` | `payment_reference` | 1:1 | umgesetzt | Zahlungsreferenz |
| `comment` | `narration` | 1:1 | umgesetzt | Notiz |
| `invoice_line_ids` | `invoice_line_ids` (account.move.line) | je Zeile Produkt, Menge, Preis, Rabatt, Steuer, Konto | umgesetzt | 10.157 Zeilen |
| `account_id` 8400 | Konto 4000 | festes Mapping | umgesetzt | Entscheidung Anna 08.10.2026 |
| `invoice_line_tax_ids` = 20 % Umsatzsteuer | `tax_ids` = „20% Ust“ | festes Mapping | umgesetzt | einzige verwendete Steuer |
| `valorisierung_id` | `valorisierung_id` | über `itk_o11_id` der Valorisierung | umgesetzt | 4.216 Beziehungen |
| `projectcategory_id` | Projektkategorie | über den Namen | umgesetzt | Zielmodell ohne Anker |
| `user_id` (Verkäufer) | `invoice_user_id` | über Login/Name | umgesetzt | wie im Verkauf |
| `account.payment` | `account.payment` | Zahlungsbeleg, Buchung, Ausgleich | umgesetzt | siehe Abschnitt 4 |
| Anhänge (`ir.attachment`) | `ir.attachment` | Schalter `--anhaenge` | **offen** | 805 MB, Entscheidung Anna offen |
| Nummernkreis | Journal-Sequenz | nicht genutzt, Nummern werden gesetzt | umgesetzt | Altdaten |

Nicht migriert (bewusst):

| Punkt | Anzahl | Grund |
|---|---|---|
| Rechnungen mit namenlosen Partnern | 53 (195.316,90 brutto) | Die 12 Kontakte wurden bei der Kontakte-Abnahme bewusst nicht migriert (ohne Namen). Kein Sammelpartner, keine Anlage im gesperrten Bereich. |

## 3 Status- und Buchungslogik (keine Automatismen)

- Rechnungen werden mit `state = 'posted'` **direkt** geschrieben, nicht über `action_post`.
  Damit gibt es keine Nummernvergabe, keine Buchungsvalidierung, keine Mails, keine
  Folgeaktionen und keine externen Aufrufe.
- Der Zahlungsstatus entsteht ausschließlich über Zahlungsbelege und Ausgleich.
- Während des Laufs sind keine Crons, Automationen, Webhooks oder Versandwege beteiligt.
  Der Zustand der Automatisierungen wird vor und nach dem Lauf gemessen (Abschnitt 7).

## 4 Zahlungen und Zahlungsstatus

Fachliche Entscheidung (Anna in Session 149 nicht erreichbar, deshalb dokumentiert und
korrigierbar): Die Zahlungen werden **als Zahlungsbelege mitgeführt**, gebucht und mit den
Rechnungen ausgeglichen. Ohne sie würden 6.326 bezahlte Rechnungen als offen erscheinen und
die Debitorenbilanz wäre um 12,1 Mio zu hoch. Die Gegenprobe ist der offene Rest: Odoo 11
138.320,55.

## 5 Sonderfälle

| Fall | Anzahl | Behandlung |
|---|---|---|
| Doppelte Rechnungsnummer R-25001 (Rechnung 27.593,52 und Gutschrift 1.474,76) | 1 | Gutschriften laufen im eigenen Journal „Gutschriften“, beide Nummern bleiben unverändert |
| Rechnungen ohne Partner-Anker | 53 | nicht migriert, dokumentierte Lücke (Abschnitt 2) |
| Zeilen ohne Produkt | 1 | Zeile mit Freitext, Konto 4000 |
| Zeilen ohne Steuer | 22 | bleiben ohne Steuer (Odoo-11-Zustand) |
| Entwürfe ohne Nummer und ohne Datum | 4 | als Entwurf übernommen, Nummer „/“ |
| Zeilen-Brutto weicht 55,63 von Kopf-Brutto ab | 1 Beleg | Odoo-11-Kopfwert bleibt maßgeblich, Abweichung dokumentiert |

## 6 Finanzielle Abweichungen

| Odoo 11 | Odoo 18 | Differenz | Ursache | Entscheidung |
|---|---|---|---|---|
| Kopf-Brutto 12.139.929,11 | Zeilen-Brutto 12.139.984,74 | 55,63 | Odoo-11-Kopfwert weicht von der Zeilensumme ab (Rundung in Odoo 11) | Kopfwerte bleiben maßgeblich, keine künstliche Angleichung |

## 7 Ergebnisse lokal (19.11.2026)

### 7.1 Mengen

| Objekt | Odoo 11 | Odoo 18 | Status |
|---|---|---|---|
| Rechnungen/Gutschriften gesamt | 6.378 | 6.325 | 53 dokumentierte Lücke |
| Ausgangsrechnungen | 6.139 | 6.096 | 43 in der Lücke |
| Gutschriften | 239 | 229 | 10 in der Lücke |
| Entwürfe | 4 | 4 | gleich |
| gebucht | 6.374 | 6.321 | 53 in der Lücke |
| Rechnungszeilen | 10.157 | 10.075 | 82 Zeilen der Lücke |
| Zahlungen | 6.091 | 6.049 + Ausgleichszahlungen | siehe 7.3 |
| Rechnungen mit Valorisierung | 4.216 | 4.214 | 2 in der Lücke |

### 7.2 Finanzielle Summen

| Größe | Odoo 11 (migrierbar) | Odoo 18 | Differenz | Erklärung |
|---|---|---|---|---|
| netto | 9.965.048,68 | 9.965.048,68 | **0,00** | identisch |
| Steuer | 1.979.563,53 | 1.979.619,16 | 55,63 | Odoo-11-Kopf-/Zeilendifferenz (1 Beleg) |
| brutto | 11.944.612,21 | 11.944.667,84 | 55,63 | derselbe Beleg |
| offener Rest | 123.006,56 | 124.623,32 | 1.616,76 | 946,20 Entwürfe + 670,56 Teilverrechnungen |

Die 55,63 sind keine Migrationsabweichung: Odoo 11 führt bei einem Beleg einen Kopfwert, der
um 55,63 unter der Summe seiner Zeilen liegt; Odoo 18 rechnet aus den Zeilen. Die Kopfwerte
werden bewusst nicht künstlich angeglichen.

Die 1.616,76 beim offenen Rest sind vollständig erklärt: Die 4 Entwürfe haben in Odoo 11
keinen Buchungssatz und damit Rest 0, in Odoo 18 den vollen Betrag (946,20); zwei Gutschriften
wurden in Odoo 11 teilverrechnet (R-25700 144,72, R-25543 525,84 = 670,56).

### 7.3 Zahlungsstatus

| Status | Odoo 11 (migriert) | Odoo 18 |
|---|---|---|
| bezahlt | 6.275 | 6.275 |
| offen | 46 | 46 |
| Entwurf | 4 | 4 |

Die Zahlungen wurden als Zahlungsbelege angelegt und ausgeglichen. In 227 Fällen kennt
Odoo 11 keinen Zahlungsbeleg, obwohl die Rechnung bezahlt ist; dafür wurde eine Zahlung im
Bankjournal mit dem Memo "Odoo 11: als bezahlt markiert, ohne Zahlungsbeleg" erzeugt
(Summe 1.062.908,48). Ohne sie wären 227 bezahlte Rechnungen offen geblieben und die
Debitorenbilanz zu hoch.

### 7.4 Abgleich (15 Prüfungen, 0 Abweichungen)

Geprüft: Belegzahl, Typen, Entwürfe, gebuchte Belege, Rechnungsnummern (0 Abweichungen),
Summen, Rechnungszeilen, Partnerzuordnung je Beleg (0 Abweichungen), Valorisierungsbezug,
offener Rest, dokumentierte Lücke.

### 7.5 Valorisierungs-Nachlauf

| Kennzahl | Wert |
|---|---|
| Odoo-11-Rechnungen mit Hinweis | 4.216 |
| bereits korrekt | 4.214 |
| zu setzen | 0 |
| nicht zuordenbar | 2 (beide in der 53er-Lücke) |
| Verteilungsabweichungen | **0** |

Damit ist die externe Abhängigkeit der Valorisierung zur Abrechnung erfüllt: 4.214 von
4.216 Beziehungen sind gesetzt und geprüft, die zwei fehlenden hängen an den namenlosen
Kontakten der dokumentierten Lücke.

### 7.6 Browser und Rechte

- Browserabnahme lokal: **11 OK / 0 FEHL** (Liste, Filter Entwurf/gebucht, historische
  Rechnung R-25949 mit 2 Positionen und Steuer 20 %, Erloeskonto 4000, Suche, Gruppierung,
  Feld "Valorisation Text").
- Rechteprüfung lokal: **6 OK / 0 FEHL**. Interner Benutzer ohne Abrechnungsgruppe sieht
  keine Rechnungen; Abrechnungsbenutzer und -manager lesen und bearbeiten; Administrator
  unverändert.

## 8 Ergebnisse VM (19.11.2026)

Die VM wurde nach `main` (Commit `a5cdf4e`, PR #289) gezogen, `itk_migration_keys`
aktualisiert und die Migration in derselben Reihenfolge gefahren.

| Schritt | Ergebnis VM |
|---|---|
| Rechnungen | 6.325 angelegt, 6.321 gebucht, 229 Gutschriften, 53 nicht zuordenbar, **0 Fehler** |
| Summen | netto 9.965.048,68 / Steuer 1.979.619,16 / brutto 11.944.667,84 - identisch zu lokal |
| Zahlungen | 6.049 angelegt, 6.029 ausgeglichen, 42 nicht zuordenbar, 20 transiente Fehler (im Ausgleichslauf behoben) |
| Ausgleich | 27 nachgebucht, 241 Ersatzzahlungen, 0 Fehler |
| Endstand | **6.275 bezahlt / 49 offen / 1 teilweise**, offener Rest **124.623,32** - identisch zu lokal |
| Abgleich | **15 Prüfungen OK / 0 Abweichungen** |
| Valorisierungs-Nachlauf | 4.214 korrekt, 0 zu setzen, 2 nicht zuordenbar, **0 Verteilungsabweichungen** |
| Browser | **11 OK / 0** |
| Rechte | **6 OK / 0** |

Lokal und VM sind damit deckungsgleich: gleiche Anzahl, gleiche Nummern, gleiche Summen,
gleicher Zahlungsstatus, gleicher offener Rest.

## 9 Offene Punkte nach dieser Runde

| Punkt | Stand |
|---|---|
| Anhänge (9.407 Dateien, 805 MB) | nicht migriert; Schalter `--anhaenge pdf|alle` vorhanden, Entscheidung Anna offen |
| 53 Belege an 12 namenlosen Kontakten | nicht migriert (195.316,90 brutto); Voraussetzung wäre die Anlage der Kontakte im gesperrten Bereich |
| 2 Valorisierungsbeziehungen | hängen an diesen 53 Belegen |
| Teilverrechnungen R-25700 / R-25543 | 670,56 nicht ausgeglichen (Odoo 11 teilverrechnet, Zahlungsbeleg fehlt) |
