# Eingangsrechnungen und Lieferanten-Gutschriften - visueller Vergleich (Browser-Abnahme)

Stand: 01.10.2026, Session 122. Aufruf im echten Browser ueber die produktiven Menuepunkte:
`Abrechnung > Einkauf > Eingangsrechnungen` (Aktion 357) und
`Abrechnung > Einkauf > Lieferanten-Gutschriften` (Aktion 358), jeweils Liste geoeffnet und ein
Datensatz im Formular. Odoo 11 wurde ausschliesslich gelesen.
Screenshots: `Desktop\Odoo18-Abnahme-Session122\belege\Eingangsrechnungen_lokal.png`,
`Eingangsrechnungen_vm.png`, `Lieferanten_Gutschriften_lokal.png`,
`Lieferanten_Gutschriften_vm.png`.

## Listenansicht

| Position | Odoo 11 sichtbar | Odoo 18 vorher sichtbar | Aenderung | Odoo 18 nachher sichtbar | gleiche Position | Begruendung |
|---|---|---|---|---|---|---|
| 1 | Nummer | Nummer | keine | Nummer | ja | - |
| 2 | Lieferant | Lieferant | keine | Lieferant | ja | bei Eingangsbelegen ist die Bezeichnung in beiden Systemen richtig |
| 3 | Rechnungsdatum | Rechnungsdatum | keine | Rechnungsdatum | ja | - |
| 4 | Faelligkeit | Faelligkeit | keine | Faelligkeit | ja | Bezeichnung bereits im Odoo-11-Wortlaut |
| 5 | Referenz/Referenzbeleg | Referenzbeleg, Referenz | keine | unveraendert | ja | - |
| 6 | Betrag, Steuer, Total, Zu bezahlen | Exklusive Steuern, Total, Zu Bezahlen | keine | unveraendert | ja | - |
| 7 | Status | Status | keine | Status | ja | - |
| Menuebezeichnung | Eingangsrechnungen / Lieferanten-Gutschriften | Eingangsrechnungen / Lieferanten-Gutschriften | keine | unveraendert | ja | Menuebezeichnungen wurden bereits angeglichen (vorher "Rueckerstattungen") |

## Formular (beide Belegarten nutzen die Rechnungsansicht)

| Position | Odoo 11 sichtbar | Odoo 18 vorher sichtbar | Aenderung | Odoo 18 nachher sichtbar | gleiche Position | Begruendung |
|---|---|---|---|---|---|---|
| Reiter 1 | Rechnung | Rechnungszeilen | Bezeichnung angeglichen | Rechnung | ja | - |
| Reiter 2 | Andere Informationen | Weitere Informationen | Bezeichnung angeglichen | Andere Informationen | ja | - |
| Kopf | Kunde/Lieferant, Rechnungsdatum, Faelligkeit, Referenz | Lieferant, Rechnungsdatum, Faelligkeit, Referenz | keine | unveraendert | ja | - |
| Kopf | Zahlungsbedingungen, Leistungszeitraum, Project Category | im Reiter versteckt | in den sichtbaren Kopfbereich geholt | Zahlungsbedingungen, Leistungszeitraum, Project Category | ja | gleiche Anpassung wie bei Ausgangsrechnungen |
| Kopf | Verkaeufer, Vertriebskanal | im Reiter versteckt | in den sichtbaren Kopfbereich geholt | Verkaeufer, Vertriebskanal | ja | - |
| Zeilen | Pos, Produkt, Beschreibung, Kostenstelle, Menge, Preis pro ME, Rabatt (%), Steuern, Zwischensumme | Line NO., Produkt, Kostenrechnung, Menge, Preis, Rabatt (optional), Steuern, Betrag | Bezeichnungen und Sichtbarkeit angeglichen | Line NO., Produkt, Kostenstelle, Menge, Preis pro ME, Rabatt (%), Steuern, Zwischensumme | ja, bis auf Griffspalte/Beschreibung | technische Punkte wie bei Ausgangsrechnungen dokumentiert |
| Buttons | Bestätigen, Auf Entwurf setzen | Bestätigen, Abbrechen | keine | unveraendert | ja | - |
| Status | Entwurf, Offen, Bezahlt | Entwurf, Gebucht, Abgebrochen | keine | unveraendert | - | Odoo-18-Statusmodell bleibt |

## Ergebnis

Eingangsrechnungen und Lieferanten-Gutschriften zeigen in Odoo 18 dieselben sichtbaren Listen-Spalten
und im Formular denselben Aufbau wie die Ausgangsrechnungen (Kopfbereich mit Zahlungsbedingungen,
Leistungszeitraum, Project Category, Verkaeufer, Vertriebskanal; Zeilen mit Kostenstelle,
Preis pro ME, Rabatt (%), Steuern, Zwischensumme). Es waren keine weiteren Anpassungen noetig; bei
Eingangsbelegen ist die Spalte "Lieferant" in beiden Systemen korrekt benannt.

Nachweise: Browser-Auslesung lokal und VM, Screenshots (Pfade oben), Ansichts-Upgrade fehlerfrei,
Regression 0 Fehler ueber 11 Prueflaeufe, keine Testdaten angelegt.
