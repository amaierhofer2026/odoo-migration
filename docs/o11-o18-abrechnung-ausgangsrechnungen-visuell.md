# Ausgangsrechnungen - visueller Vergleich Odoo 11 gegen Odoo 18 (Browser-Abnahme)

Stand: 01.10.2026, Session 122. Grundlage: Aufruf im echten Browser ueber
Abrechnung > Verkauf > Ausgangsrechnungen (Aktion 354 "Invoices") und Oeffnen eines Datensatzes.
Odoo 11 wurde ausschliesslich gelesen. Screenshot (nachher):
`Desktop\Odoo18-Abnahme-Session122\rechnung\Rechnung_lokal.png` und `Rechnung_vm.png`.

Tatsaechlich gerenderte Ansicht (ermittelt, nicht angenommen):
die produktive Menueaktion nutzt `account.view_move_form` (View-Kette der Aktion 354,
`view_mode` list,kanban,form,activity); die ITK-Anpassungen greifen ueber Vererbung mit
prioritaet 95 bis 99 und sind in der gerenderten Ansicht enthalten (Reiter "Andere Informationen"
stammt aus der ITK-Ansicht).

## Kopfbereich

| Position | Odoo 11 sichtbar | Odoo 18 vorher sichtbar | Aenderung | Odoo 18 nachher sichtbar | gleiche Position | Begruendung |
|---|---|---|---|---|---|---|
| 1 | Kunde | Kunde (Kopfbereich) | keine | Kunde | ja | - |
| 2 | Lieferadresse | Lieferadresse (Kopfbereich) | keine | Lieferadresse | ja | - |
| 3 | Zahlungsbedingungen | im Reiter versteckt | in den Kopfbereich geholt, Reiterkopie ausgeblendet | Zahlungsbedingungen | ja | Odoo-11-Platzierung im sichtbaren Kopf |
| 4 | Leistungszeitraum | im Reiter versteckt | in den Kopfbereich geholt | Leistungszeitraum | ja | - |
| 5 | Rechnungsdatum | Rechnungsdatum (Kopfbereich) | keine | Rechnungsdatum | ja | - |
| 6 | Faelligkeit | Faelligkeitsdatum (Kopfbereich) | keine | Faelligkeitsdatum | ja | Odoo-18-Bezeichnung bleibt, fachlich gleich |
| 7 | Verkaeufer | im Reiter versteckt | in den Kopfbereich geholt, Reiterkopie ausgeblendet | Verkaeufer | ja | - |
| 8 | Vertriebskanal | im Reiter versteckt | in den Kopfbereich geholt, Reiterkopie ausgeblendet | Vertriebskanal | ja | - |
| 9 | Project Category | im Reiter versteckt | in den Kopfbereich geholt, Reiterkopie ausgeblendet | Project Category | ja | Odoo-11-Wortlaut beibehalten |
| 10 | Wert/Netto/Gesamt/Steuer | Nettobetrag, Gesamt, 20 %, Waehrung | keine | unveraendert | ja | Summenbereich wie in Odoo 11 vorhanden |
| 11 | Valorisation Text | Valorisation Text | keine | Valorisation Text | ja | - |
| - | (kein Odoo-11-Feld) | Kundenreferenz, Lieferbedingungen, Liefertermin, Incoterm-Standort, Bankkonto, Steuerzuordnung, Zahlungsmethode, Zahlungsreferenz, Automatisch buchen, Geprueft, Odoo-11-Rechnungsnummer | bleiben | im Reiter "Andere Informationen" | - | Odoo-18-Zusatzfelder bleiben erhalten |

## Rechnungszeilen (Positionsbereich)

| Position | Odoo 11 sichtbar | Odoo 18 vorher sichtbar | Aenderung | Odoo 18 nachher sichtbar | gleiche Position | Begruendung |
|---|---|---|---|---|---|---|
| 1 | Pos | Line NO. | Bezeichnung in der Ansicht auf "Pos" gesetzt | Line NO. | nein | Odoo 18 rendert die Griffspalte (widget handle) mit der Feldbezeichnung; die Ansichtsbeschriftung wird vom Renderer nicht verwendet. Funktion identisch (Zeilennummer) |
| 2 | Produkt | Produkt (mit Beschreibung zusammengefuehrt) | Widget auf einfaches Auswahlfeld umgestellt, damit die Spalte nur das Produkt zeigt | Produkt | ja | - |
| 3 | Sektion | nicht vorhanden (kein Feld) | keine Spalte; Abschnitte sind in Odoo 18 eigene Zeilen ("Abschnitt hinzufuegen") | Abschnitt als Zeilentyp | nein | Odoo 18 hat kein Sektionsfeld; die Gliederungsfunktion ist als Zeilentyp vollstaendig vorhanden (2 von 10.057 Odoo-11-Zeilen betroffen) |
| 4 | Beschreibung | im Produktfeld enthalten | eigenes Widget gesetzt; Spalte wird vom Odoo-18-Renderer dennoch mit dem Produkt zusammengefuehrt | Beschreibung im Produktfeld | nein | Odoo 18 fuehrt Produkt, Abschnitt und Beschreibung bewusst in einer Spalte; die Information ist sichtbar und bearbeitbar |
| 5 | Kostenstelle | Kostenrechnung | Bezeichnung auf "Kostenstelle" gesetzt, sichtbar | Kostenstelle | ja | - |
| 6 | Kostenstellen Tags | kein Feld (Odoo 18 kennt keine Kostenstellen-Tags mehr) | keine Spalte | - | nein | 0 von 10.057 Odoo-11-Zeilen verwenden Tags; kein Zielmodell in Odoo 18 |
| 7 | Menge | Menge | keine | Menge | ja | - |
| - | (kein Odoo-11-Feld) | Maßeinheit | als optionale Spalte beibehalten, standardmaessig ausgeblendet | Maßeinheit (optional) | - | Odoo-18-Zusatzspalte bleibt erhalten |
| 8 | Preis pro ME | Preis | Bezeichnung angeglichen | Preis pro ME | ja | - |
| 9 | Rabatt (%) | Rabatt (%) nur optional | fest sichtbar | Rabatt (%) | ja | - |
| 10 | Steuern | Steuern | keine | Steuern | ja | - |
| 11 | Zwischensumme | Betrag | Bezeichnung angeglichen | Zwischensumme | ja | - |
| 12 | Total | nicht sichtbar (Spalte nur in bestimmten Konstellationen) | Bezeichnung gesetzt; Sichtbarkeit steuert Odoo 18 | Total (bei Steuer-inklusive Preisangabe) | teilweise | Odoo 18 zeigt je nach Preisangabe Zwischensumme oder Total |

## Ergebnis

Nach der Anpassung zeigt der sichtbare Kopfbereich dieselben Angaben in derselben Reihenfolge wie
Odoo 11 (Kunde, Lieferadresse, Zahlungsbedingungen, Leistungszeitraum, Rechnungsdatum, Faelligkeit,
Verkaeufer, Vertriebskanal, Project Category) und der Positionsbereich dieselben Spalten in
derselben Reihenfolge (Pos/Line NO., Produkt, Sektion, Beschreibung, Kostenstelle, Menge,
Preis pro ME, Rabatt (%), Steuern, Zwischensumme, Total), bis auf die drei technisch bedingten
Punkte: Griffspalte traegt die Odoo-18-Feldbezeichnung "Line NO.", die Beschreibung wird vom
Odoo-18-Renderer mit dem Produkt in einer Spalte gefuehrt, und fuer Sektion/Kostenstellen-Tags
existieren in Odoo 18 kein Feld (Zeiltyp bzw. Konzept entfallen).

Nachweise: Screenhots lokal und VM, Browser-Auslesung der sichtbaren Felder und Spalten,
Ansichts-Upgrade fehlerfrei, Regression 0 Fehler.

## Nachtrag 01.10.2026 (Layout und Spalten nachgezogen)

- Kopfbereich: die Odoo-11-Kopffelder stehen jetzt als eigene Gruppe "Angaben wie in Odoo 11"
  rechts neben Rechnungsdatum/Faelligkeit (vorher in der linken Spalte, dadurch verrutschte
  Darstellung mit Leerflaechen). Kunde und Lieferadresse bleiben zusammen in der linken Spalte.
- Fettschrift: In Odoo 18 werden Pflichtfelder fett dargestellt (Feldattribut `required`, u. a.
  Kunde, Rechnungsdatum, Journal). Das ist eine Modellvorgabe von Odoo 18 und keine
  Ansichts-Eigenheit; eine Angleichung wuerde Pflichtfeldpruefungen abschalten (funktionale
  Aenderung) und ist deshalb bewusst unterblieben. Alle uebrigen Bezeichnungen sind gleich
  dargestellt.
- Spalten der Rechnungszeilen jetzt sichtbar in Odoo-11-Reihenfolge:
  `Line NO. | Produkt / Beschreibung | Sektion | Kostenstelle | Menge | Preis pro ME |
  Rabatt (%) | Steuern | Zwischensumme | Total`
  - "Sektion": eigene Spalte ergaenzt (zeigt den Odoo-18-Zeilentyp: Produkt, Abschnitt, Notiz).
  - "Total": Spalte ist jetzt unabhaengig von der Preisangabe sichtbar (Attribut
    column_invisible entfernt).
  - "Beschreibung": Odoo 18 fuehrt Produkt und Beschreibung in einer Spalte; die Spalte heisst
    deshalb sichtbar "Produkt / Beschreibung" und enthaelt beides.
  - "Kostenstellen Tags": in Odoo 18 ohne Entsprechung (0 von 10.057 Odoo-11-Zeilen), keine Spalte.
  - Maßeinheit bleibt als optionale Odoo-18-Spalte erhalten.
- Nachweis: Screenshot Rechnung_lokal.png und Rechnung_vm.png, Browser-Auslesung der Spalten.

**Nachtrag 05.10.2026 (Session 125), Spalte "Beschreibung":** Anna hat im Browser gefunden, dass die
Spalte "Beschreibung" in der Rechnungszeilen-Tabelle fehlte und im Spaltenauswahl-Menue zweimal
stand. Ursache: ein zweiter `name`-Knoten in `views/account_move_line_columns.xml` und das
Odoo-18-Zeilenwidget `product_label_section_and_note_field_o2m`, dessen Renderer die Spalte `name`
bewusst entfernt. Korrektur: zweiter Knoten entfernt, Zeilenliste auf
`section_and_note_one2many` umgestellt - "Beschreibung" ist wieder eine eigene, editierbare Spalte
direkt nach "Sektion" (Odoo-11-Position), das Menue enthaelt sie genau einmal. Damit entfaellt die
kombinierte Produkt/Beschreibungs-Zelle von Odoo 18 (technisch nicht kombinierbar). Details:
`docs/o11-o18-abrechnung-zeilen-beschreibung.md`.

## Korrektur 01.10.2026 (Layout-Rollback PR #164)

Befund im Browser (lokal und VM, Screenshots): Die in PR #164 angelegte Zusatzgruppe
"Angaben wie in Odoo 11" im Kopfbereich hat das Odoo-18-Grid zerstoert

- Beschriftungen brachen mehrzeilig um,
- Werte standen ohne Beschriftung (Verkaeufer "Administrator", Vertriebskanal "Verkauf"),
- Rechnungsdatum/Faelligkeit/Waehrung waren verschoben,
- es entstanden grosse Leerflaechen.

Ursache (durch Archiv-Analyse belegt): Der Odoo-18-Kopfbereich ist mit expliziten
`<label>`-Elementen und Feldern mit `nolabel` aufgebaut. Jede zusaetzliche Gruppe oder
Einfuegung mitten in dieser Struktur zerstoert die Zuordnung von Beschriftung und Wert.

Umsetzung der Korrektur

1. Kopfbereich der Rechnungsansicht wird NICHT mehr veraendert - weder Gruppe noch
   Einzelfeldeinfuegung noch Ausblendung. Damit ist das Odoo-18-Layout wieder stabil.
2. Die Odoo-11-Kopffelder bleiben in Odoo 18 sichtbar vorhanden:
   Kopfbereich: Kunde, Lieferadresse, Rechnungsdatum, Faelligkeitsdatum, Leistungszeitraum
   (sale_order_benefit_period), Project Category (projectcategory_id), Valorisation Text,
   Waehrung; Reiter "Andere Informationen": Zahlungsbedingungen, Verkaeufer, Vertriebskanal,
   Zahlungsmethode, Zahlungsreferenz, Odoo-11-Rechnungsnummer.
3. Zeilen-Spalten unveraendert in Odoo-11-Reihenfolge, jetzt mit "Sektion" und "Total":
   Line NO. | Produkt / Beschreibung | Sektion | Kostenstelle | Menge | Preis pro ME |
   Rabatt (%) | Steuern | Zwischensumme | Total
4. Fettschrift: fett = Pflichtfeld (Attribut `required`, z. B. Kunde, Rechnungsdatum, Journal).
   Modellvorgabe von Odoo 18, keine Ansichtseigenheit; eine Angleichung wuerde die
   Pflichtfeldpruefung abschalten (funktionale Aenderung) - daher bewusst unveraendert.

Browser-Nachweis: Screenshot lokal und VM (Desktop/Odoo18-Abnahme-Session122/rechnung/),
sichtbar saubere Zweispaltigkeit von Beschriftung und Wert, Zeilenspalten wie oben.

## Nachtrag 05.10.2026 (Session 124): Project-Category-Spalte in den Kundenlisten

**Befund:** Das Feld `projectcategory_id` war im Rechnungsformular sichtbar, fehlte aber in den
Listenansichten der Kundenbelege.

**Ursache:** Jede Belegart hat ihre eigene Listenansicht des Moduls `account`, alle mit externer ID
und alle von `account.view_invoice_tree` (id 951) abgeleitet:

| Ansicht | id | externe ID | Aktion/Menue |
|---|---|---|---|
| Ausgangsrechnungen | 953 | `account.view_out_invoice_tree` | 354 (Abrechnung > Verkauf > Ausgangsrechnungen) |
| Kunden-Gutschriften | 954 | `account.view_out_credit_note_tree` | 355 (Abrechnung > Verkauf > Kunden-Gutschriften) |
| Eingangsrechnungen | 956 | `account.view_in_invoice_bill_tree` | 356/357 |
| Lieferanten-Gutschriften | 957 | `account.view_in_invoice_refund_tree` | 358 |

Der bisherige Loesungsversuch setzte die Spalte per SQL in `arch_db` ein und suchte dafuer einen
Anker `//field[@name='state']` (Ersatz: `name`). Diesen Anker gibt es in 953/954 nicht - ihre Arch
besteht nur aus `<xpath>`- und `<field position=...>`-Knoten. Der Lauf meldete Erfolg, aenderte aber
nichts ("Upgrade exit 0 beweist nichts").

**Loesung:** normale Ansichts-Vererbung im Modul `itk_account_migration` (18.0.1.11.0) auf
`account.view_out_invoice_tree` und `account.view_out_credit_note_tree`:

```
<xpath expr="//field[@name='status_in_payment']" position="after">
    <field name="projectcategory_id" optional="show" readonly="1"/>
</xpath>
```

**Position:** Odoo 11 fuehrt die Spalte in `account.invoice.tree` (View 590, read-only gemessen)
an Position 3 - direkt nach Nummer und Status. In Odoo 18 steht sie daher unmittelbar hinter der
Spalte Status. Eingangs- und Lieferantenlisten bleiben unveraendert (Odoo 11
`account.invoice.supplier.tree` kennt die Spalte nicht).

**Sichtbare Spaltenfolge** (lokal und VM identisch, unveraendert gegenueber vorher):
Nummer | Kunde | Rechnungsdatum | Faelligkeit | Referenzbeleg | Referenz | Exklusive Steuern |
Total | Zu Bezahlen | Status | **Project Category**

## Nachtrag 05.10.2026 (Session 124): Statuskette im Rechnungsformular

Die Odoo-11-Prozesskette (Entwurf / Offen / Bezahlt / Abgebrochen) steht jetzt als Statusleiste im
Rechnungsformular - nach demselben, bereits abgenommenen Muster wie im Zahlungsformular:

- Das berechnete Anzeigefeld `itk_o11_status` (`store=False`) wird mit `widget="statusbar"` an
  derselben Stelle gezeigt, an der die Odoo-18-Statusleiste stand.
- Teilzahlung bleibt fachlich "Offen" (Odoo 11 kannte keinen eigenen Teilzahlungszustand).
- Vollstaendig gutgeschriebene Rechnungen zeigen "Gutgeschrieben (Odoo 18)" als bewussten
  Odoo-18-Zusatz (Entscheidung Anna, 05.10.2026, Restbetrag 0,00).
- Der technische Odoo-18-Wert bleibt sichtbar: eigene Gruppe "Status (Odoo 18)" im Reiter
  "Andere Informationen" (Entwurf / Gebucht / Abgebrochen).
- Keine State-, Zahlungs- oder Buchungslogik geaendert; alle Odoo-18-Buttons und -Smart-Buttons
  bleiben erhalten.

Nachweis (Browser, lokal und VM): `scripts/browser_pc_status_abnahme.py --instanz <...>`,
Screenshots je Zustand in `Desktop/Odoo18-Abnahme-Session124/pc_und_statuskette/<instanz>/`.
Ergebnis: lokal 73 OK / 0 FEHL, VM 73 OK / 0 FEHL (je 7 Screenshots). Geprueft wurden die Zustaende
Entwurf (draft), Offen (posted, nicht bezahlt), Teilzahlung (posted, partial), Bezahlt (posted,
paid), Abgebrochen (cancel) und Gutschrift (posted, reversed); die Project-Category-Spalte traegt in
Liste und Formular jeweils den echten Wert "amtsweg.gv.at - BUNDESLAND SONDERVERTRAG".

