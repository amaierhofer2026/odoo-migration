# Steuern: Odoo 11 gegen Odoo 18 (Bereich Abrechnung > Konfiguration > Finanzen > Steuern)

Stand: 08.10.2026 (Session 131). Quelle: Odoo 11 Produktion `portal.it-kommunal.at` (ausschliesslich
lesend) gegen Odoo 18 Testinstanz (`odoo18_test`, lokal und VM). Werkzeuge (nur lesend):
`scripts/erhebe_steuern_o11_o18.py`, `scripts/werte_steuern_aus.py`; Testbelege:
`scripts/steuern_testbelege.py`; Browserabnahme: `scripts/browser_steuern_abnahme.py`.
Rohdaten: `Desktop/Odoo18-Abnahme-Session131/steuern/`.

## 1. Kennzahlen

| Punkt | Odoo 11 | Odoo 18 |
|---|---|---|
| Steuern im Bestand | **77** | **53** |
| davon produktiv verwendet | **2** | **2** |
| Verkauf / Einkauf | 1 / 1 | 1 / 1 |
| Kontenrahmen | 1.286 Konten | 240 Konten |
| Belege mit steuerbehafteten Zeilen | 6.281 (von 6.065 Ausgangs- und Gutschriftsbelegen) | - |
| Steuerzuordnungen (Fiscal Positions) | 5 | 4 |

Verwendet heisst: die Steuer steht auf mindestens einer Produktvorlage oder mindestens einer
Belegzeile. Gemessen ueber `product.template.taxes_id`/`supplier_taxes_id` und
`account.invoice.line.invoice_line_tax_ids` (Odoo 11) bzw. `account.move.line.tax_ids` (Odoo 18).

## 2. Verwendete Odoo-11-Steuern und ihre Zuordnung (1:1)

| Odoo 11 | Art | Satz | Berechnung | inkl. | Gruppe | Sequenz | Konto | Erstattungskonto | Verwendung | Odoo-18-Ziel | Zustand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 20% Umsatzsteuer | sale | 20% | percent | nein | USt 20% | 10 | 1776 Umsatzsteuer 19% | 1776 | 10.683 (Produkte 12 + Belegzeilen) | **20% Ust** (id 15) | 1:1 |
| 20% Vorsteuer | purchase | 20% | percent | nein | USt 20% | 10 | 1576 Abziehbare Vorsteuer 19% | 1576 | 648 | **20% Vst** (id 43) | 1:1 |

Zuordnungsregel (identisch zum Migrationswerkzeug `steuer_im_ziel`): zuerst gleicher Name, dann die
Odoo-11-Beschreibung als Odoo-18-Name ohne Beachtung der Gross-/Kleinschreibung, dann genau ein
Treffer mit gleichem Satz und gleicher Verwendung. Mehrdeutigkeit bricht ab.

Beide verwendeten Steuern werden ueber die **Beschreibung** aufgeloest:

- `20% Umsatzsteuer` hat die Beschreibung `20% USt` -> Odoo-18-Name `20% Ust` (einziger Treffer).
- `20% Vorsteuer` hat die Beschreibung `20% VSt` -> Odoo-18-Name `20% Vst` (einziger Treffer).

Die Odoo-18-Steuernamen dieses Bestands stammen aus den Odoo-11-Beschreibungen; deshalb ist die
Aufloesung ueber die Beschreibung der stabilere Schluessel als der blosse Name.
Wichtig: haette nur der Name gezogen, waere die Zuordnung **nicht** eindeutig gewesen - allein im
Verkauf gibt es `20% Ust`, `20% Ust O S` und `20% Ust C` mit 20% (3 Kandidaten), im Einkauf 14
Kandidaten mit 20%.

## 3. Merkmalsvergleich der beiden verwendeten Steuern

| Merkmal | Odoo 11 (20% Umsatzsteuer / 20% Vorsteuer) | Odoo 18 (20% Ust / 20% Vst) | Bewertung |
|---|---|---|---|
| Bezeichnung | 20% Umsatzsteuer / 20% Vorsteuer | 20% Ust / 20% Vst | fachlich gleich, Wortlaut abweichend (Odoo-18-Wortlaut bleibt) |
| Beschreibung auf Belegen | 20% USt / 20% VSt | UST_022 Normalsteuersatz 20% / VST_060 Normalsteuersatz 20% | abweichend: Odoo 18 fuehrt hier den oesterreichischen Kontenrahmen-Code |
| Verkauf/Einkauf | sale / purchase | sale / purchase | gleich |
| Steuersatz | 20% | 20% | gleich |
| Preis inklusive | nein | nein | gleich |
| Steuerberechnung | percent | percent | gleich |
| Steuergruppe | USt 20% | 20% | fachlich gleich (Anzeigename) |
| Steuerkonten | 1776 Umsatzsteuer 19% (Verbindlichkeit) / 1576 Abziehbare Vorsteuer 19% (Umlaufvermoegen) | 3500 Umsatzsteuer 20% (liability_current) / 2500 Vorsteuern 20% (asset_current) | Kontenart identisch; 1776 -> 3500 ist als Belegzeilen-Mapping bereits dokumentiert, 1576 -> 2500 entspricht der Kontenart und ist im Ziel bereits so gesetzt |
| Rueckerstattungslogik | Erstattungskonto = Steuerkonto | Rueckrepartitionszeile 100% auf dasselbe Konto | gleich |
| Sequenz | 10 | 50 | technische Reihenfolge, keine fachliche Wirkung |
| Aktiv | ja | ja | gleich |
| Inklusiv-Basis | nein | nein | gleich |

Belege zur Steuerlogik (im Ziel gebucht, `scripts/steuern_testbelege.py`):

- Verkauf: Entwurf 100,00 -> gebucht RE/2026/0003, Steuer 20,00, **Steuerbuchung auf Konto 3500
  Umsatzsteuer 20%**.
- Einkauf: Entwurf 100,00 -> gebucht RECHN/2026/10/0001, Steuer 20,00, **Steuerbuchung auf Konto
  2500 Vorsteuern 20%**.
- Beide Testbelege wurden nach der Pruefung wieder entfernt (Entwurf -> geloescht), Bestand vorher =
  nachher.

## 4. Nicht verwendete Odoo-11-Steuern (nicht migrationsrelevant)

**75 der 77 Odoo-11-Steuern werden nicht verwendet**: keine Produktvorlage und keine Belegzeile
traegt sie. Es handelt sich ueberwiegend um Ueberbleibsel des deutschen Standardkontenrahmens
(19% und 7%, Typ `type_tax_use = none`, z. B. "19% USt gem. §13b UStG", "7% Vorsteuer",
"19% Einfuhrumsatzsteuer", "19% USt Steuerpflichtige Sonstige Leistung", "10,7% Vorsteuer
Land-/Forstwirtschaft").

Diese Steuern werden **nicht angelegt und nicht zugeordnet**. Dokumentiert als
"nicht migrationsrelevant" (keine Verwendungsevidenz). Damit wird ausdruecklich keine Steuerliste
optisch nachgebaut.

## 5. Zum Unterschied 19% (Altbestand) gegen 20% (heutige Odoo-18-Steuern)

- Die produktiv verwendeten Odoo-11-Steuern rechnen mit **20%** (Normalsteuersatz Oesterreich); der
  Zusatz "19%" steckt nur in den **Kontobezeichnungen** (1776 "Umsatzsteuer 19%", 1576 "Abziehbare
  Vorsteuer 19%"), nicht im Steuersatz.
- Die Odoo-11-Steuern mit 19%/7% im Namen sind **unbenutzt** (siehe Abschnitt 4).
- Odoo 18 fuehrt eigene 19%-Steuern (`19% Ust`, `19% Ust O C`, `19% Vst J M`, 19.0%). Diese sind
  Bestandteil des Zielkontenrahmens und werden **nicht** als Ersatz fuer die unbenutzten
  Odoo-11-Schablonen herangezogen.
- Es findet **keine fachliche Umdeutung aufgrund aehnlicher Namen** statt: zugeordnet wird
  ausschliesslich ueber die Beschreibung der tatsaechlich verwendeten Steuern, verifiziert ueber
  Satz, Verwendung, Kontenart und Buchungsergebnis.

## 6. Steuerzuordnungen (Steuerzuordnung / Fiscal Positions)

| | Odoo 11 | Odoo 18 |
|---|---|---|
| Anzahl Positionen | 5 | 4 |
| automatisch anwenden | nein (alle) | ja (alle) |
| Steuerabbildungen gesamt | 15 | 11 |
| Verwendung | 1 Partner, **4 Belege** | 22 Belege, 0 Partner |

Die Odoo-11-Positionen bilden die verwendeten Steuern auf Ausfuhr-, EU- und §13b-Steuern ab
(z. B. `20% Umsatzsteuer -> Steuerfreie innergem. Lieferung`). Die Migration uebertraegt das Feld
Steuerzuordnung nicht; die Auswirkung wurde daher belegt gemessen:

| Odoo-11-Beleg | Position | Zeilensteuer | gebuchte Steuer Odoo 11 | Migration |
|---|---|---|---|---|
| R-25951 | Dienstleister EU (mit USt-ID) | keine | 0,00 | identisch (keine Zeilensteuer) |
| R-25949 | Dienstleister EU (mit USt-ID) | 20% Umsatzsteuer | 278,46 | identisch (Steuer wird mitmigriert) |
| R-25950 (Gutschrift) | Dienstleister EU (mit USt-ID) | 20% Umsatzsteuer | 278,46 | identisch |
| R-24832 | Dienstleister EU (mit USt-ID) | 20% Umsatzsteuer | **0,00** (keine Steuerzeile gebucht) | **abweichend** (siehe Abschnitt 7) |

## 7. Befund mit Migrationsrelevanz: Beleg R-24832

- R-24832 (Ausgangsrechnung, bezahlt, 06.11.2024) traegt auf beiden Zeilen die Steuer
  `20% Umsatzsteuer`, hat aber **keine gebuchte Steuer**: `amount_tax = 0,00`, keine
  `account.invoice.tax`-Zeile, und die Buchung enthaelt nur das Forderungskonto 1410 (Soll 278,15)
  und zweimal 8400 Erloese 19% USt (Haben 171,10 und 107,05) - die Steuer wurde nie gebucht.
- Umfang geprueft: von **6.281** Odoo-11-Belegen mit steuerbehafteten Zeilen ist dies der
  **einzige** ohne gebuchte Steuer.
- Folge bei der Migration: die Zeilensteuer (20%) wandert mit, Odoo 18 berechnet dann eine Steuer
  von rund 55,63 EUR, die Odoo 11 nicht gebucht hat. Der Beleg waere danach um diesen Betrag hoeher.
- Bewertung: kein Fehler der Steuerzuordnung und kein Fehler des Zielkontenrahmens, sondern eine
  Inkonsistenz im Odoo-11-Altbestand bei einem einzelnen Beleg (0,02% aller steuerbehafteten
  Belege).

**Entscheidung Anna, 08.10.2026:** Der historische Beleg wird nach seinem **tatsaechlich gebuchten
finanziellen Zustand** migriert - ohne Steuer auf den Rechnungszeilen, ohne Nachberechnung der
20% USt und ohne Erzeugung einer Steuerbuchung. Gesamtbetrag, Restbetrag, Zahlungsstatus,
Forderung und Erloes bleiben unveraendert.

### 7.1 Eng begrenzte Sonderregel in der Testmigration

Umgesetzt in `scripts/testmigration_abrechnung.py` als `ist_sonderfall_ohne_steuerbuchung()`. Die
Regel greift **nur**, wenn am Odoo-11-Beleg alle drei Bedingungen belegt sind:

1. mindestens eine Belegzeile traegt eine Steuer,
2. `amount_tax` des Belegs ist 0,00,
3. es gibt keine Steuerbuchungszeile (`account.invoice.tax`).

Trifft eine Bedingung nicht zu, wird die Steuer wie bisher uebernommen. Es werden **keine Steuern
allgemein entfernt**. Beim Treffer werden die Zeilen mit ausdruecklich leerer Steuermenge angelegt
(`tax_ids = [(6, 0, [])]`), damit das Ziel nicht die Standardsteuer der Produktvorlage nachzieht.
Der Lauf protokolliert jeden Treffer im Klartext.

Nachweis (Werkzeug `scripts/pruefe_sonderfall_r24832.py`):

| Pruefung | Ergebnis |
|---|---|
| Odoo-11-Belege mit steuerbehafteten Zeilen geprueft | 6.281 |
| davon Sonderfall-Kandidat | **1** (R-24832) |
| uebrige Belege, die ihre Steuer normal erhalten | 6.280 |
| Odoo 11 R-24832 | paid, ohne 278,15, Steuer 0,00, total 278,15, Rest 0,00 |
| Odoo 18 R-24832 (RE/2024/0002) | posted, ohne 278,15, Steuer 0,00, total 278,15, Rest 0,00, Zahlung paid |
| Steuerbuchungszeilen in Odoo 18 | 0 |
| Belegzeilen mit Steuer in Odoo 18 | 0 |
| Buchungszeilen | Odoo 11 3 (1410 Forderung, zweimal 8400) gegen Odoo 18 3 (2000 Forderung, zweimal 4000) |
| Zahlung | CUST.IN/2024/0821 mitgezogen und abgestimmt, Zustand paid |

### 7.2 Zusatzbefund: automatische Steuerzuordnung im Ziel aendert Konten

Bei der ersten Umsetzung scheiterte die Abstimmung der Zahlung. Ursache (belegt): Odoo 18 wendet bei
Partnern aus EU/Drittland von sich aus eine Steuerzuordnung an. Im Testfall setzte die automatische
Zuordnung "Europaeische Union" das Forderungskonto 2000 auf 2100 um; die Zahlung buchte auf 2000,
die Abstimmung war damit unmoeglich. Ausserdem zog die Produktvorlage ihre Standardsteuer nach
(55,63 EUR statt 0,00), solange die Zeilensteuermenge nicht ausdruecklich leer gesetzt war.

Behebung, dokumentiert im Werkzeug: migrierte Belege erhalten ausdruecklich
`fiscal_position_id = False` (die Odoo-11-Steuerzuordnung wird nicht uebertragen; damit gelten die
dokumentierten Konten 2000/4000 statt der automatisch abgebildeten 2100) und im Sonderfall eine
ausdruecklich leere Steuermenge. Beides ist im Code kommentiert und gilt fuer alle migrierten
Belege, nicht nur fuer den Sonderfall.

## 8. Was bewusst NICHT gemacht wurde

- Keine Odoo-18-Steuer geloescht, ersetzt, umbenannt oder in der Reihenfolge veraendert.
- Keine der 75 unbenutzten Odoo-11-Steuern angelegt.
- Keine neuen Steuern oder Konten erzeugt.
- Keine Zusammenlegung ueber aehnliche Namen; keine Umdeutung von 19%-Schablonen.
- Die Odoo-18-Zusatzsteuern des Kontenrahmens (53 Steuern, u. a. Ausfuhr-, EU-, §13b- und
  Eigenverbrauchssteuern) bleiben unveraendert erhalten.

## 8a. Sonderzeichen in den Steuerbeschreibungen (Korrektur 08.10.2026)

**Befund (Auftrag Anna):** In der Oberflaeche erschienen Beschreibungen wie
"UST_019 Grundstuecksumsaetze 0% (T° 6 Abs. 1 Z 9 lit. a)" und
"UST_016 Kleinunternehmer 0% (T° 6 Abs. 1 Z 27)" - statt "§ 6" stand "T°".

**Tatsaechlicher Wert in Odoo 18 (gemessen):** In den Beschreibungen stand nicht "§", sondern die
Zeichenfolge **U+252C U+00BA** ("┬º"). Das ist der UTF-8-Code des Paragrafzeichens (C2 A7),
faelschlich als CP437/CP850 gelesen. Umlaute und ß waren korrekt (ä 21, ß 7, ü 2, Ü 1 Vorkommen) -
betroffen war ausschliesslich das Paragrafzeichen.

**Herkunft:** Der Kontenrahmen Oesterreich (`l10n_at`) liefert die Beschreibungen aus
`/usr/lib/python3/dist-packages/odoo/addons/l10n_at/data/template/account.tax-at.csv`. Diese
Quelldatei ist **korrekt UTF-8**; die Zeile fuer UST_019 enthaelt die Bytes `C2 A7` (= "§") und
"Grundstuecksumsaetze" mit korrekten Umlauten. Der Fehler entstand beim Import/der Datenhaltung
dieser Instanz, nicht in der Quelle. (Die Datei ist Teil des Odoo-Images und wird nicht veraendert.)

**Umfang und Korrektur (Werkzeug `scripts/korrigiere_steuerbeschreibungen.py`):**

| Feld | Sprache | betroffene Steuern | korrigierte Stellen |
|---|---|---|---|
| Beschreibung (`description`) | de_DE | 19 aktive + 1 archivierte (id 6) | 21 |
| Beschreibung (`description`) | en_US | 14 | 15 |
| Bezeichnung auf Rechnungen (`invoice_label`) | de_DE | 6 | 6 |
| Bezeichnung auf Rechnungen (`invoice_label`) | en_US | 6 | 6 |
| Steuerbezeichnung (`name`) | beide | 0 | 0 |
| **Summe** | | **46 Feldkorrekturen** | **48 Stellen** |

Zwei Felder fielen erst bei der Nachpruefung auf:

- **Bezeichnung auf Rechnungen** (`invoice_label`): mit `description` und `name` das dritte
  uebersetzbare Textfeld der Steuer; in der Steuerliste eine eigene Spalte (z. B. "RC 20% T° 19
  Abs. 1a"). Wurde mitkorrigiert.
- **Archivierte Steuer id 6** ("0% Ust L 1e", `active = False`): sie ist in der Liste sichtbar und
  trug den Fehler noch. Die Suche beruecksichtigt jetzt ausdruecklich auch archivierte Datensaetze
  (`active in (True, False)`), damit nichts uebersehen wird.

Korrigiert wurden ausschliesslich die Textfelder der Steuern, in beiden Sprachen: "┬º" -> "§".
Weitere geprüfte Modelle ohne Befund: `account.account`, `account.journal`, `account.tax.group`,
`account.fiscal.position`, `product.category`, `account.payment.term`, `itk_valorisierung`,
`account.move`.

**Bewusst NICHT geaendert:** In zwei Beschreibungen (id 39, 40) steht "&gt;=" statt ">". Das Feld
`account.tax.description` ist in Odoo 18 ein HTML-Feld (`type=html`, `sanitize=True`); der
Sanitizer speichert ">" als "&gt;" und zeigt es in HTML-Kontexten korrekt als ">" an. Ein
Schreibversuch mit ">" wird sofort wieder in "&gt;" gewandelt (geprueft) - das ist der korrekte
Speicherzustand, kein Darstellungsfehler.

**Unveraendert geblieben ist alle Steuerlogik:** Saetze, Berechnungsart, Preis inklusive,
Steuergruppen, Sequenzen, Aktiv-Status, Steuerkonten, Repartitionszeilen, Verknuepfungen und die
Steuerzuordnungen. Es wurden keine Steuern angelegt, geloescht oder umbenannt.

**Wiederholbarkeit:** Das Werkzeug ist idempotent (`--pruefen` meldet 0 offene Stellen). Wird der
Kontenrahmen neu installiert, kann der Fehler erneut auftreten - dann das Werkzeug erneut
ausfuehren (analog zu `apply_abrechnung_labels.py` nach Upgrades).

**Browserbeleg:** Liste und Formulare (UST_019, UST_016, UST_021, VST_061) zeigen "§" und kein
fehlerhaftes Zeichen; Screenshots unter
`Desktop/Odoo18-Abnahme-Session131/steuern/browser/<instanz>/`.

## 9. Bezug

- `docs/o11-o18-abrechnung-abschlusspruefung.md` (Belegzeilen-Mapping samt 1776 -> 3500)
- `docs/o11-o18-testmigration-regel.md` (Steueraufloesung im Werkzeug)
- `scripts/testmigration_abrechnung.py` (`steuer_im_ziel`)
- `docs/o11-o18-abrechnung-abschlussmatrix.md` (Bereichsstatus)
