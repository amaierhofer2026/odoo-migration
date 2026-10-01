# Odoo 11 gegen Odoo 18 - Bereich Abrechnung, Teil 5: Umsetzung der Stammdaten und Zuordnungen

Stand: 30.09.2026, Session 122. Umsetzung der in Teil 5 vorbereiteten Punkte.
Geprueft am 30.09.2026 mit vollstaendiger Abdeckung (kein Lese-Limit) - siehe Punkte 3 und 4.
Grundregeln unverandert: Odoo 11 ausschliesslich read-only, keine Datenmigration,
Aenderungen nur in Odoo 18, Odoo-18-Zusatzfunktionen bleiben erhalten.

Rohdaten der Erhebung: `scripts/erhebe_teil5_rohdaten.py` (liest Odoo 11 nur).

## 1. Feld "Odoo-11-Rechnungsnummer" (Entscheidung K2a)

Neues Modul `addons/itk_account_migration` (Version 18.0.1.0.0, Abhaengigkeit `account`).

```
Feld          : account.move.itk_o11_invoice_number   (Char, gespeichert, indiziert, mitverfolgt)
Bezeichnung   : "Odoo-11-Rechnungsnummer" (de_DE, entspricht dem Odoo-11-Wortlaut)
Weiteres Feld : account.payment.itk_o11_payment_number  ("Odoo-11-Zahlungsnummer", Punkt 5)
Sichtbarkeit  : Rechnungsformular im Reiter "Weitere Informationen" (nach dem Feld Referenz),
                nur bei Ausgangs-/Eingangsrechnungen und Gutschriften; Listenspalte optional
                ausblendbar; in der Suche als Suchfeld vorhanden.
Lesbarkeit    : in den Ansichten read-only (readonly="1"). Im normalen Betrieb nicht aenderbar;
                die Migration kann das Feld ueber Skripte befuellen.
Mapping       : Odoo 11 account.invoice.number -> Odoo 18 account.move.itk_o11_invoice_number
                (nur historische Nachvollziehbarkeit). Die laufende Nummer bleibt account.move.name
                in der Odoo-18-Sequenz. Es wird keine bestehende Odoo-18-Nummer ueberschrieben.
Nachweis lokal: Felder vorhanden (Type char, gespeichert), Installationslauf ohne Fehler.
```

## 2. Valorisierungstexte (Stammdaten)

Odoo 11 fuehrt 10 Valorisierungstexte, Odoo 18 enthielt bisher nur "VAL-OK".
Die 10 Texte wurden als Stammdaten vorbereitet in
`addons/itk_valorisierung/data/valorisierungstexte_o11.xml` (noupdate="1"), Modul auf 18.0.1.1.0.
Die XML-ID `valorisierung_o11_<Odoo-11-ID>` haelt die Zuordnung dauerhaft fest.

```
Odoo 11 ID | Text                                          -> Odoo 18
1  VALORISIERUNGSHINWEIS 2019
2  VALORISIERUNGSHINWEIS 2020
3  VALORISIERUNGSHINWEIS 2021
4  VALORISIERUNGSHINWEIS 2022
5  VALORISIERUNGSHINWEIS 2023
6  Valorisierungshinweis 2024
7  VALORISIERUNGHINWEIS 2024 Acta Nova   (Schreibweise aus Odoo 11 uebernommen,
                                          abschliessendes Leerzeichen entfernt)
8  VALORISIERUNGSHINWEIS 2024 gerundete Zahlen
9  Valorisierungshinweis 2025
10 Valorisierungshinweis 2026
-> alle 10 als neue Datensaetze angelegt; Ergebnis Odoo 18: 11 Texte (1 vorhandener + 10),
   keine Dubletten (Pruefung ueber den Namen).
```

## 3. Konten-Mapping (Vollstaendigkeitscheck 30.09.2026)

Geprueft ohne Lese-Limit (`scripts/pruefe_teil5_abdeckung.py`, Odoo 11 read-only):
Buchungszeilen gesamt 34.492, Summe der Kontengruppen 34.492, Zeilen ohne Konto 0.
Abdeckung damit 100 % - es gibt kein weiteres tatsaechlich bebuchtes Konto.

```
Odoo 11 Konto     Bezeichnung Odoo 11                     Zeilen | Odoo-18-Zielkonto
1201 (liquidity)  Bank                                      5.989 | 2801 Bank
1410 (receivable) Forderungen aus Lieferungen u.Leistung   12.252 | 2000 Forderungen aus Lieferungen
                                                                    und Leistungen Inland
1776 (other)      Umsatzsteuer 19%                          6.241 | 3500 Umsatzsteuer 20%
8400 (other)      Erloese 19% USt                          10.010 | 4000 Brutto-Umsatzerloese im Inland (20%)
                                                        ---------
Summe                                                      34.492 | = Buchungszeilen gesamt
```

Die Zeilen verteilen sich ausschliesslich auf die Journale "Ausgangsrechnungen (EUR)" und
"Bank fuer Tirol und Vorarlberg AG (EUR)"; damit ist der Migrationsumfang Abrechnung
(Rechnungen, Gutschriften, Zahlungen) vollstaendig abgedeckt. Ein groesserer Buchhaltungsbestand
mit weiteren Konten existiert in Odoo 11 nicht.
Hinweis: Odoo 11 wird weiterhin produktiv genutzt, die Zeilenzahlen steigen daher leicht
(z. B. Bank 5.987 am Vormittag, 5.989 am Nachmittag). Die Zuordnung ist ueber die Kontenbedeutung
definiert und damit unabhaengig von der Zeilenzahl.

## 4. Steuer-Mapping (Vollstaendigkeitscheck 30.09.2026)

Alle vier steuerrelevanten Sammlungen wurden vollstaendig gelesen (ohne Limit). Es tritt
ausschliesslich eine einzige Steuer auf:

```
Odoo 11 Steuer 18 "20% Umsatzsteuer" (20 %, percent, sale, exklusiv):
  Buchungszeilen mit Steuerzuordnung (tax_ids) : 9.988
  Steuerzeilen der Buchungen (tax_line_id)     : 6.241
  Rechnungszeilen mit Steuer                   : 10.029 von 10.051
  Rechnungsteuerzeilen (account.invoice.tax)   : 6.275 von 6.275 (alle)
-> Odoo 18 Steuer 15 "20% Ust" (20 %, percent, sale, exklusiv) = 1:1
```

Abdeckung der tatsaechlich belegten steuerrelevanten Zeilen: 100 % - keine andere Steuer ist
irgendwo belegt. Die 22 Rechnungszeilen ohne Steuer sind keine Steuerluecke im Mapping, sondern
in Odoo 11 selbst ohne Steuer gefuehrt (Angaben "Anzahlung", "Anzahlung von 50.0%",
"Uebernachtungen lt. Liste", "Bahnreise Fahrtkosten Wien-Muenchen"); sie werden bei der
Migration ebenfalls ohne Steuer uebernommen und sind vor der Migration nicht anzupassen.

## 5. Zahlungsnummern-Regel (Odoo 11 -> Odoo 18)

Erhebung (read-only, 5.987 Zahlungen in Odoo 11):

```
Muster          : CUST.IN/<Jahr>/<laufend 4-stellig>   (Einzahlungen)
                  CUST.OUT/<Jahr>/<laufend 4-stellig>  (Auszahlungen)
erste Nummer    : CUST.IN/2019/0001
letzte Nummer   : CUST.IN/2026/1061
laufend         : die laufende Nummer waechst innerhalb des Jahres und laeuft bei 9999 nicht
                  in eine fuenfte Stelle (Grenze in der Praxis nicht erreicht)
```

Regel:
1. Die Odoo-11-Zahlungsnummer wird bei der Migration in das neue Feld
   `account.payment.itk_o11_payment_number` uebernommen (historische Nachvollziehbarkeit).
2. Die Odoo-18-Nummerierung bleibt unveraendert: neue Zahlungen erhalten ihre Nummer aus der
   bestehenden Odoo-18-Sequenz des Zahlungsjournals (kein Eingriff, keine Sequenzbeschaedigung).
3. Historische Nummern werden nicht in die Odoo-18-Sequenz zurueckgeschrieben, damit die
   Sequenz nicht beschädigt oder gesperrt wird.
4. Zusaetzlich bleibt die Zahlung ueber das Memo-Feld (Rechnungsnummer) mit der Rechnung
   verbunden - Das entspricht dem tatsaechlichen Odoo-11-Verhalten (Memo = Rechnungsnummer).

## 6. Nachweise

```
lokal   : Modul installiert (Instanz lokal, keine Fehler); Felder vorhanden (char, gespeichert);
          Valorisierungstexte 11 (1 vorhanden + 10 vorbereitet);
          Ansichten: Formular, Liste, Suche (read-only).
VM      : Deploy auf Branch, Modul installiert, gleiche Pruefungen (siehe Ergebnisse unten).
Regression: scripts/abschluss_verkauf_regression.py = 886 OK / 0 FEHL ueber 11 Prueflaeufe.
```

## 7. Endstatus Teil 5

Vollstaendig vorbereitet: Feldabbildung (53 Feldpaare), Migrationsregeln K1-K9,
Feld "Odoo-11-Rechnungsnummer" und "Odoo-11-Zahlungsnummer", Valorisierungstexte,
Konten-Mapping (4 Konten), Steuer-Mapping (1 Steuer), Zahlungsnummern-Regel,
Bericht "ITK-Rechnung mit Zahlung", Label-Abgleich fest im Upgrade-Verfahren.
Kein Blocker fuer eine spaetere Testmigration eines einzelnen Rechnungsdatensatzes:
die Zuordnungen sind eindeutig; die Testmigration selbst ist noch nicht gestartet und
wurde ausdruecklich nicht begonnen.
