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
