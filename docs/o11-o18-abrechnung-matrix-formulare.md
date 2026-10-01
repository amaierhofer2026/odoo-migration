# Matrix je Formular - Bereich Abrechnung (feldweiser Abgleich Odoo 11 gegen Odoo 18)

Stand: 01.10.2026, Session 122. Bereich Abrechnung: **IN ARBEIT**.
Spalten: Menuepunkt | Odoo-11-Feld/Funktion | Odoo-18 vorhanden vor Aenderung | Massnahme |
Odoo-18 nachher | Browser lokal | Browser VM | Bemerkung

## 1. Verkauf > Ausgangsrechnungen > Rechnung (Formular)

| Menuepunkt | Odoo-11-Feld/Funktion | Odoo-18 vorher | Massnahme | Odoo-18 nachher | lokal | VM | Bemerkung |
|---|---|---|---|---|---|---|---|
| Rechnung | Reiter "Rechnung" | Rechnungszeilen | Bezeichnung angeglichen | Rechnung | ok | ok | - |
| Rechnung | Reiter "Andere Informationen" | Weitere Informationen | Bezeichnung angeglichen | Andere Informationen | ok | ok | - |
| Rechnung | Kunde | Kunde | vorhanden | Kunde | ok | ok | - |
| Rechnung | Lieferadresse | Lieferadresse | vorhanden | Lieferadresse | ok | ok | - |
| Rechnung | Rechnungsdatum | Rechnungsdatum | vorhanden | Rechnungsdatum | ok | ok | - |
| Rechnung | Faelligkeit | Faelligkeitsdatum | vorhanden | Faelligkeitsdatum | ok | ok | Odoo-18-Bezeichnung, fachlich gleich |
| Rechnung | Zahlungsbedingungen | nicht sichtbar | Gruppe "Angaben wie in Odoo 11" ergaenzt, Feld sichtbar gemacht | Zahlungsbedingungen | ok | ok | Modulabhaengigkeiten ergaenzt |
| Rechnung | Leistungszeitraum | nicht sichtbar | Feld sichtbar gemacht | Leistungszeitraum | ok | ok | Feld sale_order_benefit_period |
| Rechnung | Project Category | nicht sichtbar | Feld sichtbar gemacht | Project Category | ok | ok | Odoo-11-Wortlaut beibehalten (Ihre Vorgabe) |
| Rechnung | Verkaeufer | Verkaeufer | vorhanden | Verkaeufer | ok | ok | - |
| Rechnung | Vertriebskanal | Vertriebskanal | vorhanden | Vertriebskanal | ok | ok | Feld team_id |
| Rechnung | Valorisation Text | Valorisation Text | vorhanden | Valorisation Text | ok | ok | - |
| Rechnung | Zahlungsmethode | Zahlungsmethode | vorhanden | Zahlungsmethode | ok | ok | - |
| Rechnung | Zahlungsreferenz | Zahlungsreferenz | vorhanden | Zahlungsreferenz | ok | ok | - |
| Rechnung | Odoo-11-Rechnungsnummer | neu | angelegt (K2a) | Odoo-11-Rechnungsnummer | ok | ok | nur fuer die Migration |
| Rechnung | Button "Auf Entwurf setzen" | Auf Entwurf zurücksetzen | Bezeichnung angeglichen | Auf Entwurf setzen | ok | ok | - |
| Rechnung | Button "Nach Gutschrift fragen" | Gutschrift | Bezeichnung angeglichen | Nach Gutschrift fragen | ok | ok | nur auf Rechnungen, wie in Odoo 11 |
| Rechnung | Button "Einzahlung erfassen" | Zahlen | Bezeichnung angeglichen | Einzahlung erfassen | ok | ok | bei bezahlten Rechnungen ausgeblendet |
| Rechnung | Statusleiste | Entwurf/Gebucht/Abgebrochen | vorhanden | unveraendert | ok | ok | Odoo-18-Zustaende bleiben |

## 2. Rechnungszeilen (Spalten im Rechnungsformular)

| Odoo-11-Spalte | Odoo-18 vorher | Massnahme | Odoo-18 nachher | lokal | VM | Bemerkung |
|---|---|---|---|---|---|---|
| Pos | Line NO. | vorhanden | Line NO. | ok | ok | funktional gleich (Zeilennummer) |
| Produkt | Produkt | vorhanden | Produkt | ok | ok | - |
| Sektion | nicht als Spalte | keine Spalte; Odoo 18 fuehrt Abschnitte als Zeilentyp ("Abschnitt hinzufuegen") | Abschnitt-Zeile verfuegbar | ok | ok | technisch anders geloest, Funktion vorhanden |
| Beschreibung | nicht sichtbar | noch offen | nicht sichtbar | offen | offen | Feld wird im Produktfeld mitgefuehrt; Spalte folgt |
| Kostenstelle | Kostenrechnung | vorhanden | Kostenrechnung | ok | ok | - |
| Kostenstellen-Tags | kein 1:1 (Odoo 18 nutzt Verteilung/Kostenstellenplaene) | keine Angleichung | - | - | - | fachlich nicht identisch |
| Menge | Menge | vorhanden | Menge | ok | ok | - |
| Masseinheit | Masseinheit | vorhanden | Masseinheit | ok | ok | - |
| Preis pro ME | Preis | Bezeichnung angeglichen | Preis pro ME | ok | ok | - |
| Rabatt | Rabatt (%) nur optional | Spalte sichtbar gemacht | Rabatt (%) | ok | ok | - |
| Steuern | Steuern | vorhanden | Steuern | ok | ok | - |
| Zwischensumme | Betrag | Bezeichnung angeglichen | Zwischensumme | ok | ok | - |
| Total | nicht als Spalte | noch offen | nicht sichtbar | offen | offen | Summenblock zeigt Total; Spalte folgt |

## 3. Kunden-Gutschriften

| Menuepunkt | Odoo-11-Feld/Funktion | Odoo-18 vorher | Massnahme | Odoo-18 nachher | lokal | VM | Bemerkung |
|---|---|---|---|---|---|---|---|
| Kunden-Gutschriften | Menuebezeichnung | Gutschriften | angeglichen | Kunden-Gutschriften | ok | ok | - |
| Kunden-Gutschriften | Formular, Reiter, Felder, Spalten | dieselbe Ansicht wie Rechnung | wirkt automatisch mit | wie Rechnung | ok | ok | Testbeleg im Browser geprueft und entfernt |
| Kunden-Gutschriften | Button "Nach Gutschrift fragen" | nicht vorhanden | keine | nicht vorhanden | ok | ok | Odoo 11 blendet ihn ebenfalls aus |

## 4. Zahlungen, Eingangsrechnungen, Lieferanten-Gutschriften, Stammdaten, Konfiguration

| Menuepunkt | Odoo-11-Feld/Funktion | Odoo-18 vorher | Massnahme | Odoo-18 nachher | lokal | VM | Bemerkung |
|---|---|---|---|---|---|---|---|
| Verkauf/Einkauf > Zahlungen | Button "setze auf Entwurf" | Auf Entwurf zurücksetzen | angeglichen | setze auf Entwurf | ok | ok | - |
| Verkauf/Einkauf > Zahlungen | Formular/Kopf/Layout | Odoo-18-Layout | feldweiser Abgleich offen | - | offen | offen | als naechstes |
| Einkauf > Eingangsrechnungen | Formular (gleiche Ansicht wie Rechnung) | - | wirkt mit | wie Rechnung | ok | ok | - |
| Einkauf > Lieferanten-Gutschriften | Menuebezeichnung | Rueckerstattungen | angeglichen | Lieferanten-Gutschriften | ok | ok | - |
| Kunden/Lieferanten, Produkte | Feldbezeichnungen | teils englisch | feldweiser Abgleich offen | - | offen | offen | als naechstes |
| Konfiguration (Steuern, Journale, Waehrungen, Steuerzuordnung, Bankkonten, Zahlungsarten) | Feldbezeichnungen | teils abweichend | Kernfelder angeglichen (Abschnitt 8 der Abschlussmatrix) | Odoo-11-Wortlaut | ok | ok | Rest folgt feldweise |

## 5. Stand und naechste Schritte

Erledigt und im Browser belegt (lokal und VM): Rechnungskopf mit Zahlungsbedingungen,
Leistungszeitraum, Project Category; Reiter; Buttons; Rechnungszeilen-Spalten Preis pro ME,
Rabatt, Steuern, Zwischensumme, Kostenrechnung, Menge, Masseinheit, Produkt, Line NO.

Offen: Spalten Beschreibung und Total in den Rechnungszeilen; feldweiser Abgleich der
Zahlungsformulare, der Kunden/Lieferanten- und Produktformulare sowie der restlichen
Konfigurationsformulare; danach vollstaendige Matrix und Abschlusspruefung.
Der Bereich Abrechnung bleibt bis dahin IN ARBEIT. Odoo 11 wurde ausschliesslich gelesen,
es wurde nichts migriert.
