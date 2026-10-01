# Kunden-Gutschrift und Zahlung - visueller Vergleich Odoo 11 gegen Odoo 18 (Browser-Abnahme)

Stand: 01.10.2026, Session 122. Aufruf im echten Browser ueber die produktiven Menuepunkte:
`Abrechnung > Verkauf > Kunden-Gutschriften` (Formular der Belegart Kunden-Gutschrift) und
`Abrechnung > Verkauf > Zahlungen` (Menue Aktion 330, Modell account.payment).
Odoo 11 wurde ausschliesslich gelesen. Screenshots:
`Desktop\Odoo18-Abnahme-Session122\belege\Gutschrift_lokal.png`, `Gutschrift_vm.png`,
`Zahlung_lokal.png`, `Zahlung_vm.png`.

Nachweis zum Testbeleg: Fuer die Gutschrift wurde ausschliesslich in Odoo 18 ein Testbeleg
angelegt, im Browser geprueft und danach entfernt. Bestand vorher = nachher
(Gutschriften 0, Belege 38 bzw. 61, Buchungszeilen 102 bzw. 170, Zahlungen 8 bzw. 11).

## Kunden-Gutschrift

| Position | Odoo 11 sichtbar | Odoo 18 vorher sichtbar | Aenderung | Odoo 18 nachher sichtbar | gleiche Position | Begruendung |
|---|---|---|---|---|---|---|
| Reiter 1 | Rechnung | Rechnungszeilen | Bezeichnung angeglichen | Rechnung | ja | dieselbe Ansicht wie bei Rechnungen |
| Reiter 2 | Andere Informationen | Weitere Informationen | Bezeichnung angeglichen | Andere Informationen | ja | - |
| Kopf 1 | Kunde | Kunde | keine | Kunde | ja | - |
| Kopf 2 | Lieferadresse | Lieferadresse | keine | Lieferadresse | ja | - |
| Kopf 3 | Zahlungsbedingungen | im Reiter versteckt | in den Kopfbereich geholt | Zahlungsbedingungen | ja | wie Ausgangsrechnung |
| Kopf 4 | Leistungszeitraum | im Reiter versteckt | in den Kopfbereich geholt | Leistungszeitraum | ja | - |
| Kopf 5 | Rechnungsdatum | Rechnungsdatum | keine | Rechnungsdatum | ja | - |
| Kopf 6 | Faelligkeit | Faelligkeitsdatum | keine | Faelligkeitsdatum | ja | fachlich gleich |
| Kopf 7 | Verkaeufer | im Reiter versteckt | in den Kopfbereich geholt | Verkaeufer | ja | - |
| Kopf 8 | Vertriebskanal | im Reiter versteckt | in den Kopfbereich geholt | Vertriebskanal | ja | - |
| Kopf 9 | Project Category | im Reiter versteckt | in den Kopfbereich geholt | Project Category | ja | Odoo-11-Wortlaut |
| Summen | Wert, Steuer, Gesamt | Nettobetrag, Gesamt, 20 % | keine | unveraendert | ja | - |
| Zeilen 1 | Pos | Line NO. | Ansichtsbeschriftung "Pos" gesetzt | Line NO. | nein | Odoo 18 rendert die Griffspalte mit der Feldbezeichnung (dokumentiert) |
| Zeilen 2 | Produkt | Produkt (mit Beschreibung zusammengefuehrt) | Widget auf einfache Auswahl umgestellt | Produkt | ja | - |
| Zeilen 3 | Beschreibung | im Produktfeld | eigenes Widget gesetzt, Renderer fuehrt dennoch zusammen | im Produktfeld sichtbar und bearbeitbar | nein | Odoo-18-Standardverhalten |
| Zeilen 4 | Kostenstelle | Kostenrechnung | Bezeichnung angeglichen, sichtbar | Kostenstelle | ja | - |
| Zeilen 5 | Menge, Preis pro ME, Rabatt (%), Steuern, Zwischensumme | Menge, Preis, Rabatt (optional), Steuern, Betrag | Bezeichnungen und Sichtbarkeit angeglichen | Menge, Preis pro ME, Rabatt (%), Steuern, Zwischensumme | ja | - |
| Status | Entwurf, Offen, Bezahlt | Entwurf, Gebucht, Abgebrochen | keine | unveraendert | - | Odoo-18-Statusmodell bleibt erhalten |
| Buttons | Bestätigen, Auf Entwurf setzen, Nach Gutschrift fragen (nur Rechnungen) | Bestätigen, Abbrechen, Neu | keine | unveraendert | ja | der Gutschriftsknopf erscheint in beiden Systemen nur auf Rechnungen |

## Zahlung

| Position | Odoo 11 sichtbar | Odoo 18 vorher sichtbar | Aenderung | Odoo 18 nachher sichtbar | gleiche Position | Begruendung |
|---|---|---|---|---|---|---|
| Feld | Zahlungsart | Zahlungsmethode | Bezeichnung angeglichen | Zahlungsart | ja | payment_method_line_id |
| Feld | Zahlungsdatum | Datum | Bezeichnung angeglichen | Zahlungsdatum | ja | Feld date |
| Feld | Betrag | Betrag | keine | Betrag | ja | - |
| Feld | Journal | Journal | keine | Journal | ja | - |
| Feld | Kunde | Kunde | keine | Kunde | ja | - |
| Feld | Notiz (Verwendungszweck = Rechnungsnummer) | Notiz | keine | Notiz | ja | Memo bleibt Rechnungsnummer |
| Feld | Bankkonto | Bankkonto des Unternehmens | keine | unveraendert | ja | - |
| Feld | - | Odoo-11-Zahlungsnummer, Senden, Erhalten | bleiben | vorhanden | - | Odoo-18-/Migrations-Zusatz |
| Status | Entwurf, Gebucht, Abgestimmt | Entwurf, In Bearbeitung, Bezahlt | keine | unveraendert | - | Odoo-18-Statusmodell bleibt erhalten |
| Buttons | Bestätigen, setze auf Entwurf | Bestätigen, Auf Entwurf zurücksetzen | Bezeichnung angeglichen | setze auf Entwurf | ja | - |
| Smart Buttons | Buchungszeilen, Rechnungen, Zahlungsabstimmung | Rechnung (Anzahl), Transaktion, Abgestimmte Zeilen, Erstattungen | keine Umbenennung | dynamische Odoo-18-Bezeichnungen | nein | keine 1:1-Feldbezeichnung; Objekte und Zaehler weichen ab, Funktionen sind vollstaendig vorhanden (dokumentiert in der Abnahmeliste) |

## Ergebnis

Kunden-Gutschrift und Zahlung zeigen im echten Browser dieselben sichtbaren Felder und Spalten wie
die Ausgangsrechnung bzw. wie Odoo 11. Offen bleiben ausschliesslich die bereits dokumentierten
technischen Punkte (Griffspalte "Line NO.", zusammengefuehrte Beschreibung, dynamische
Smart-Button-Bezeichnungen der Zahlung, Odoo-18-Statusmodell).

Nachweise: Browser-Auslesung lokal und VM, Screenshots (Pfade oben), Testbeleg restlos entfernt,
Ansichts-Upgrade fehlerfrei, Regression 0 Fehler ueber 11 Prueflaeufe.
