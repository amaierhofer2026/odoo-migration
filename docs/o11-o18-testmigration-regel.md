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

## 3.1 Produktfelder: Zuordnung und Migrationsregel (Session 129, 06.10.2026)

Auf Annas Auftrag uebertraegt die Testmigration zusaetzlich diese Produktfelder - nie ueber
Odoo-11-IDs, sondern ueber fachliche Schluessel:

| Odoo-11-Feld | Odoo-18-Zielfeld | Zuordnung | Regel |
|---|---|---|---|
| `default_code` | `product.template.default_code` | 1:1 | Text unveraendert (Odoo 11: 2 von 648 belegt) |
| `standard_price` | `product.template.standard_price` | 1:1 | Zahl unveraendert (Odoo 11: 6 von 648 belegt) |
| `uom_id` | `product.template.uom_id` | ueber den Namen der Einheit | genau ein Treffer, sonst Abbruch |
| `uom_po_id` | `product.template.uom_po_id` | ueber den Namen der Einheit | wie oben |
| `categ_id` | `product.template.categ_id` | ueber exakten Namen (beide Sprachen) und exakte Elternkette; fehlende Kategorien werden in der Ziel-Testinstanz angelegt (Abschnitt 3.2) | nur eindeutige Treffer, sonst Abbruch |
| `taxes_id` | `product.template.taxes_id` | vierstufig (siehe unten) | in Odoo 11 bei 646 von 648 belegt |
| `supplier_taxes_id` | `product.template.supplier_taxes_id` | vierstufig | in Odoo 11 bei 647 von 648 belegt |

Steuerzuordnung (`taxes_id` und `supplier_taxes_id`), Stufe fuer Stufe:

1. gleicher Name im Ziel,
2. der Odoo-11-**Beschreibungstext** der Steuer (Feld `description`, z. B. "20% USt") als
   Odoo-18-Name, ohne Gross-/Kleinschreibung - die Steuernamen der Zielinstanz stammen aus
   diesen Beschreibungen,
3. genau ein Kandidat mit gleichem Satz (`amount`) und gleicher Verwendung (`type_tax_use`),
4. sonst: fuer Produktsteuern **Abbruch mit Klartext** (kein stilles Ueberspringen); fuer die
   Steuerliste selbst wird die Steuer angelegt.

Zusaetzlich gilt fuer die Steuerliste (Session 129 nachgezogen): Vor dem Anlegen einer Steuer
wird dieselbe Zuordnung geprueft. Eine vorhandene Zielsteuer wird verwendet - es entsteht
**keine zweite Steuer gleichen Inhalts** (Beispiel: Odoo-11 "20% Umsatzsteuer" wird auf die
vorhandene Odoo-18-Steuer "20% Ust" abgebildet, nicht neu angelegt).

Sprache: Quelle und Ziel werden mit `context {'lang': 'de_DE'}` gelesen und gesucht. Ohne diesen
Kontext liefert Odoo 11 englische Anzeigenamen ("Unit(s)"), waehrend die Zielinstanz deutsche
fuehrt ("Einheit(en)") - die Zuordnung ueber Namen scheitert dann (Befund Session 129, behoben).

Kein stilles Ueberspringen (Auftrag Session 129, nachgezogen und geprueft): Mehrdeutigkeit oder
fehlende Zuordnung fuehrt immer zu einem Abbruch mit Klartext. Auch in den Belegzeilen muessen
Produkt, Konto, Steuer, Waehrung und Zahlungsbedingung eindeutig aufloesbar sein - vorher
wurden Produkt, Steuer und Zahlungsbedingung dort still ausgelassen.

## 3.2 Produktkategorien als Stammdaten (Session 129, 07.10.2026)

Quelle read-only gemessen: 30 Kategorien, 26 mit Produkten, alle 26 flach (keine
Ueberkategorie). Wurzelkategorie ist Odoo-11-id 1 - deutsch "Alle", englisch "All".

Zuordnung (`kategorie_im_ziel` in `scripts/testmigration_abrechnung.py`):

1. Odoo-11-Kategorien werden in **beiden Sprachen** gelesen (de_DE, en_US).
2. Treffer im Ziel ausschliesslich ueber **exakten Namen** (in einer der beiden Sprachen) **und
   exakte Elternkette** (`parent_id`, nicht Pfadtext). Keine Aehnlichkeitszuordnung.
3. Genau ein Treffer mit passender Elternkette -> verwenden.
4. Mehrere Treffer oder abweichende Elternkette -> **Abbruch mit Klartext**.
5. Kein Treffer -> Kategorie **nur in der Ziel-Testinstanz** anlegen (Name in beiden Sprachen,
   gleiche Elternkategorie wie in Odoo 11). Odoo 11 bleibt unveraendert.
6. Angelegte Kategorien werden im Protokoll vermerkt (`neu: true`) und von `--aufraeumen`
   entfernt.

Die Odoo-11-Wurzel "Alle"/"All" wird ueber den englischen Namen auf die vorhandene Odoo-18-
Kategorie "All" (id 1) abgebildet, nicht neu angelegt.

Ergebnis des kontrollierten Testlaufs auf der VM (07.10.2026): 2 Kategorien angelegt
("Amtssignatur, E-Abfertigung, E-Postfaecher", "Nutzungsentgelt"), 11 von 11 Produkten mit der
richtigen Kategorie, im Browser geprueft (7 OK / 0 FEHL), danach 23 Datensaetze entfernt und
Bestand vorher = nachher. Vollstaendige Tabelle und Belege:
`docs/o11-o18-produktkategorien-mapping.md`.

Offen: die Kontenfelder der Kategorien (Odoo 11 einheitlich Erloes 8400 / Aufwand 3400) sind im
Testbestand nicht abbildbar (anderer Kontenrahmen, 240 Konten) - eigener Schritt Kontenmigration.

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

Das Protokoll liegt ausserhalb des Repos unter
`%LOCALAPPDATA%\Temp\testmigration_protokoll.json`; darin steht jeder selbst angelegte Datensatz
mit Modell, ID und fachlichem Schluessel. Nur diese Datensaetze entfernt `--aufraeumen`.

## 9. Erster Schreiblauf am 05.10.2026 (Session 123) und seine Befunde

Ausgefuehrt auf der VM gegen `odoo18_test`, danach geprueft mit `scripts/pruefe_testmigration.py`
(75 Pruefungen bestanden, 0 Abweichungen) und anschliessend vollstaendig entfernt - der Bestand war
danach wieder exakt wie vorher (Anzahlen, Digests, Summen und Belegnamen identisch).

Uebertragen wurden: Kundenrechnung R-261121 (offen, 4 Zeilen), Kunden-Gutschrift R-26800 (bezahlt,
4 Zeilen), Kundenrechnung R-261131 (bezahlt, 1 Zeile) mit Zahlung CUST.IN/2026/1064, ein
Rechnungsentwurf (2 Zeilen), 4 Partner, 11 Produkte, 1 Journal, 1 Steuer, 1 Zahlungsbedingung.

Befunde, die fuer die echte Migration wichtig sind:

1. **Odoo-11-`type` traegt die ITK-Werte.** Die Auswahl kannte consu, service, general,
   onlineservice, sw, consulting, platform, hw, project, product. In Odoo 11 verteilen sich die
   Produkte auf consu 152, service 47, onlineservice 74, platform 94, sw 9. Odoo 18 kennt nur
   consu/service/combo. Zuordnung im Skript: consu -> consu, product -> consu + is_storable,
   service -> service, alle ITK-Werte -> service. **Das ist eine Annahme und braucht deine
   fachliche Bestaetigung.** `type` und `product_type_id` sind in Odoo 11 unabhaengig
   (Produkt 719: type=platform, product_type_id=Onlineservice) - `product_type_id` wird 1:1 ueber
   den Namen uebernommen.
2. **Partner-Anzeigename:** Odoo 11 zeigt "[20609] Marktgemeinde Greifenburg", das Feld `name`
   enthaelt nur "Greifenburg". Die Bezeichnung kommt aus `community_salutation`
   (Organisationsbezeichnung), dazu `ref` (20609) und `community_magnitude`. Odoo 18 hat dieselben
   ITK-Felder; sie muessen mitwandern, sonst verliert der Kunde seine sichtbare Bezeichnung.
3. **Odoo-11-Journalcode "Re.:"** ist als Code ungeeignet: Odoo 18 vergibt daraus
   "Re.:/2026/00001" und fuer Gutschriften "RRe.:/2026/00001". Das Ziel hat bereits ein
   Verkaufsjournal mit Code "RE". Hier braucht es eine Entscheidung (eigenes Journal anlegen oder
   auf das bestehende abbilden).
4. **`itk_o11_payment_number` gibt es in Odoo 18 nicht.** Die Odoo-11-Zahlungsnummer wird in
   `memo` gefuehrt. Entweder Feld anlegen oder diese Ablage fachlich bestaetigen.
5. **Abstimmung:** Das Feld `reconciled_invoice_ids` beim Anlegen einer Zahlung stimmt in Odoo 18
   nicht ab. Die Abstimmung wird ausdruecklich ueber `account.move.line.reconcile` hergestellt.
6. **Bezahlter Altbeleg ohne Zahlungsdatensatz:** Die Gutschrift R-26800 ist in Odoo 11 bezahlt,
   die Zahlung steckt aber in einer Buchung (nicht in `account.payment`). Ohne diese Buchung bleibt
   der Beleg im Ziel offen. Fuer die echte Migration muss der Zahlungsweg solcher Belege
   mitgeklaert werden.
7. **Keine Lieferantenbelege in Odoo 11** (0 `in_invoice`, 0 `in_refund`) - Lieferantenfaelle
   koennen nur mit Testdaten der Zielinstanz geprueft werden.


## 10. Punkte 1-7 aus der ersten Auswertung - Bearbeitung am 05.10.2026

1. **Produkttyp-Mapping:** Die Annahme "Odoo 18 kennt nur consu/service" war falsch. Das Modul
   `itk_product` setzt die Auswahl in Odoo 18 auf dieselben ITK-Werte wie Odoo 11 (consu, service,
   combo, general, onlineservice, sw, consulting, platform, hw, project; per `fields_get` auf lokal
   und VM belegt). Der Typ wird daher **1:1** uebernommen. Kein pauschales Umstellen auf service:
   in Odoo 11 sind general 273 Produkte, platform 94, onlineservice 74, sw 9, service 47, consu 152;
   hw, consulting und project sind nicht belegt. Nur der Odoo-11-Typ `product` (Lagerartikel, in
   Odoo 18 nicht vorhanden und in Odoo 11 nicht belegt) wird zu `consu` + `is_storable`.
**Nachtrag 05.10.2026: entschieden (Variante 1).** Anna hat am 05.10.2026 festgelegt: `type` 1:1
uebernehmen, soweit der Wert in Odoo 18 vorhanden ist; `product_type_id` separat 1:1 ueber Name und
ID; keine Verschmelzung und keine gegenseitige Ableitung; Lagerfuehrung ausschliesslich ueber
`is_storable`; Lagerartikel bleiben bei `product_type_id` leer; die sechs ITK-Produktarten bleiben
erhalten; die Odoo-11-Filter muessen dieselben Produktmengen liefern (Filter "Dienstleistungen"
bleibt bei 47 aktiven Vorlagen). Vollstaendige, datenbasierte Grundlage und die einzige noch
anpassungsbeduerftige Stelle (`service_type = 'timesheet'`): `docs/o11-o18-produktart-mapping.md`.
Umsetzung nur vorbereitet - keine Datenmigration.
2. **Partner-Anzeigename:** Regel ermittelt: Odoo 11 zeigt `[ref] community_salutation`
   (z. B. "[20609] Marktgemeinde Greifenburg"), waehrend `name` nur "Greifenburg" enthaelt.
   Odoo 18 bildet diese Zusammensetzung nicht nach. Transformationsregel im Skript:
   sichtbarer Name = `community_salutation`, sonst `name`; `ref`, `community_salutation`,
   `community_magnitude` und der Kurzname (`commercial_company_name`) wandern mit.
   Verbleibende, beabsichtigte Abweichung: der `[ref]`-Praefix steht in Odoo 18 im Feld `ref`
   und nicht im Anzeigenamen.
### 10.1 Bewusste, fachlich gleichwertige Abweichungen zu Odoo 11 (Entscheidung Anna, 05.10.2026)

Beide Punkte werden **nicht** an Odoo 11 angeglichen. Sie sind bewusst so entschieden und
fachlich gleichwertig:

- **"Gutgeschrieben" statt "Bezahlt":** Eine vollstaendig gutgeschriebene Rechnung fuehrt Odoo 18
  im Zahlungsstatus als `reversed` und zeigt "Gutgeschrieben"; Odoo 11 zeigte dafuer "Bezahlt".
  Voraussetzung fuer diese Bewertung - im Testlauf belegt: Restbetrag = 0,00, Gegenbeleg/
  Gutschrift korrekt verknuepft und die Abstimmung fachlich vollstaendig. Es wird **nicht**
  kuenstlich auf "Bezahlt" umbenannt (kein Eingriff in die Odoo-18-Statuslogik).
- **Partnername ohne `[ref]`-Praefix:** Odoo 11 zeigte den Partner als "[20609] Marktgemeinde
  Greifenburg", Odoo 18 zeigt "Marktgemeinde Greifenburg"; der Referenzwert steht weiterhin im
  Feld `ref`. Die sichtbare Bezeichnung (Organisationsbezeichnung aus `community_salutation`)
  bleibt damit erhalten, nur der Praefix wird in Odoo 18 nicht in den Anzeigenamen gezogen.

3. **Journal/Nummernfolge:** Ursache geklaert - Odoo 11 fuehrt genau ein Verkaufsjournal
   "Ausgangsrechnungen" mit dem Code "Re.:"; Odoo 18 uebernahm den Code und bildete daraus
   "Re.:/2026/00001" bzw. "RRe.:/2026/00001". Das Ziel hat bereits "Kundenrechnungen" mit Code
   "RE". Es wird **kein Journal angelegt**; die Abbildung laeuft ueber `JOURNAL_MAPPING`
   ("Re.:" -> "RE"). Nummern im Test danach: RE/2026/0006, RRE/2026/00001. Die Odoo-11-Nummer
   bleibt in `itk_o11_invoice_number`.
4. **Historische Zahlungsnummer:** Die Meldung "Feld fehlt" war ein Fehler meiner Abfrage - ich
   hatte `itk_o11_payment_number` auf `account.move` gesucht statt auf `account.payment`. Das Feld
   existiert (Modul `itk_account_migration` 18.0.1.10.0, auf lokal und VM installiert, Typ char).
   Die Zahlung wird jetzt dort abgelegt (zusaetzlich im `memo`): `itk_o11_payment_number =
   CUST.IN/2026/1064`.
5. **Abstimmung als Nachlauf:** Zahlungen und Belegpaare werden nach dem Anlegen aller Belege und
   Zahlungen in einem eigenen Nachlauf (`stelle_ab`) abgestimmt und danach 1:1 gegen Odoo 11
   geprueft (Zustand und Restbetrag je Beleg). `reconciled_invoice_ids` beim Anlegen wirkt nicht.
6. **Bezahlte Altbelege:** Ursache in Odoo 11 geklaert - die Gutschrift R-26800 ist **nicht per
   Zahlungsdatensatz** beglichen, sondern gegen die Rechnung R-26797 abgestimmt (Buchungszeile
   32874 "auf falschen Kunden ausgestellt", Gegenstueck 32858 in Buchung R-26797). Regel: der
   Gegenbeleg wird automatisch mit ausgewaehlt und im Nachlauf genauso abgestimmt. Es werden
   **keine kuenstlichen Zahlungen** erzeugt.
   Beobachtete Abweichung in der Bezeichnung: Odoo 18 fuehrt die voll gutgeschriebene Rechnung
   als `reversed` ("Gutgeschrieben"), Odoo 11 zeigte "Bezahlt" - fachlich derselbe Zustand (Rest 0).
7. **Eingangsrechnungen:** Odoo 11 hat 0 `in_invoice` und 0 `in_refund`. Es wird nichts erzeugt;
   die Odoo-18-Testdaten der Zielinstanz zaehlen nicht zum Migrationsumfang.

## 11. Zweiter Testlauf (05.10.2026) und Aufraeumen

Ausgefuehrt auf der VM, danach geprueft (`scripts/pruefe_testmigration.py`): **96 Pruefungen
bestanden, 0 Abweichungen**, 5 dokumentierte Hinweise. 1:1-Gegenpruefung je Beleg:
R-261121 offen/Rest 1366,01; R-26800 bezahlt/0,00; R-261131 bezahlt/0,00; Entwurf Entwurf;
R-26797 gutgeschrieben/0,00. Danach `--aufraeumen`: 22 Datensaetze entfernt; Bestandsvergleich
(Anzahlen, Digests je Modell, Belegsummen und Belegnamen) **identisch** zum Ausgangsstand.

## 12. Dritter Testlauf (07.10.2026, Session 129) - Produktkategorien

Anlass: Kategorien waren im Ziel noch nicht aufloesbar (Abbruch) und wurden als offener Punkt
gefuehrt. Vorgehen und Ergebnis:

- Trockenlauf lokal und VM: identisch, 76 Planpositionen, 24 noch nicht vorhanden, kein Abbruch.
- Schreiblauf auf der VM: **23 neu angelegte Datensaetze** - 11 Produktvorlagen, 2
  Produktkategorien, 4 Partner, 5 Belege, 1 Zahlung. Protokoll: 202 Eintraege (179 vorhandene
  Ziel-Datensaetze unveraendert wiederverwendet).
- Beleg-Gegenpruefung: R-261121 offen/Rest 1366,01; R-26800, R-260993, R-26797 bezahlt/0,00;
  ein Entwurf. Keine Abweichung.
- Browserabnahme VM (`scripts/browser_kategorie_pruefung.py`): **7 OK / 0 FEHL** -
  Feld "Interne Kategorie" je Produkt gleich der Odoo-11-Kategorie; Gruppierung der Produktliste
  nach Produktkategorie zeigt genau eine Gruppe je Kategorie, keine Dubletten.
- Aufraeumen: **23 Datensaetze entfernt** (nur die im Protokoll als neu vermerkten), 0 fehlten.
  Bestand VM vorher = nachher: Kategorien 3, Vorlagen 10, Varianten 10, Belege 59, Partner 70,
  Steuern 53, Zahlungsbedingungen 12. Restkontrolle ohne Treffer.
- Details, Kategorietabelle und Mapping: `docs/o11-o18-produktkategorien-mapping.md`.

Abrechnung bleibt IN ARBEIT.
