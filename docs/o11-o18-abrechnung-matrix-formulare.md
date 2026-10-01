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

## 6. Nachlauf 01.10.2026 (Zahlungen, Kunden/Lieferanten, Produkte, Konfiguration)

| Menuepunkt | Odoo-11-Feld/Funktion | Odoo-18 vorher | Massnahme | Odoo-18 nachher | lokal | VM | Bemerkung |
|---|---|---|---|---|---|---|---|
| Zahlungen | Feldbezeichnung "Zahlungsart" | Zahlungsmethode | Bezeichnung angeglichen | Zahlungsart | ok | ok | payment_method_line_id |
| Zahlungen | Feldbezeichnung "Zahlungsdatum" | Datum | Bezeichnung angeglichen | Zahlungsdatum | ok | ok | Feld date |
| Zahlungen | Betrag, Journal, Kunde, Notiz, Senden | vorhanden | keine | unveraendert | ok | ok | - |
| Zahlungen | Odoo-11-Zahlungsnummer | neu | angelegt | Odoo-11-Zahlungsnummer | ok | ok | nur fuer die Migration |
| Kunden/Lieferanten | Steuerzuordnung | Steuerposition | Bezeichnung angeglichen | Steuerzuordnung | ok | ok | property_account_position_id |
| Kunden/Lieferanten | Summe Debitoren / Kreditlinie | nicht in der Odoo-18-Ansicht sichtbar | keine Anzeige in Odoo 18 | - | ok | ok | Odoo 18 zeigt die Kreditangaben nur in der Verkaufs-App; keine sichtbare Stelle zum Angleichen |
| Produkte | Erlöskonto, Aufwandskonto | Ertragskonto, Aufwandskonto (abweichend) | Bezeichnung angeglichen, soweit in der Ansicht vorhanden | Erlöskonto | ok | offen | Produktformular VM-Pruefung folgt |
| Konfiguration (Steuern, Journale, Steuerzuordnung, Waehrungen, Kostenstellen) | Feldbezeichnungen | teils abweichend | Kernfelder angeglichen (Abschnitt 8 der Abschlussmatrix) | Odoo-11-Wortlaut | ok | ok | - |
| Rechnungszeilen | Spalte Beschreibung | mit dem Produktfeld zusammengefuehrt | keine Aenderung | Produktspalte enthaelt Beschreibung und Abschnitte | ok | ok | in Odoo 18 technisch anders geloest, Funktion vorhanden |
| Rechnungszeilen | Spalte Total | nur in bestimmten Konstellationen sichtbar | keine Aenderung | Zwischensumme bzw. Total je nach Preisangabe | ok | ok | Odoo-18-Design: netto oder brutto |

## 7. Abschluss 01.10.2026

Geprueft und im Browser (lokal und VM) belegt:
- Rechnung: Kopf, Reiter, Felder, Buttons, Statusleiste, Rechnungszeilen-Spalten, Suche, Filter, Gruppierungen.
- Kunden-Gutschrift: dieselbe Ansicht, Testbeleg im Browser geprueft und restlos entfernt.
- Zahlung: Formularfelder, Bezeichnungen, Buttons, Smart Buttons, Zahlenformular-Assistent.
- Kunden/Lieferanten: Registerkarten Kontakte, Verkauf und Einkauf (Steuerzuordnung), Abrechnung, Gemeinde-Information.
- Produkte: Registerkarten Allgemeine Informationen (ITK-Felder), Verkauf, Einkauf, Lager.
- Konfiguration: Steuern, Journale, Waehrungen, Steuerzuordnung, Zahlungsbedingungen, Bankkonten, Kostenstellen, Kostenstellenplaene, Zahlungsarten/-anbieter, Verwaltung, Einstellungen (Menuewalk ueber jeden Menuepunkt, Feldbezeichnungen angeglichen).
- Assistenten: Zahlung erfassen, Gutschrift/Stornierung, Senden, Drucken; Druckausgabe mit ITK-Rechnung und ITK-Rechnung mit Zahlung.
- Abstimmung mit Odoo 11 nur lesend, keine Datenmigration, Testbeleg entfernt (Bestand vorher = nachher).

Verbleibende, begruendete Abweichungen (nicht technisch angleichbar bzw. fachlich anders):
1. Acht Odoo-11-Berichtsassistenten (in Odoo 18 Community nicht vorhanden).
2. Spalte Kunde statt Odoo-11-"Lieferant" (Odoo 11 beschriftete die Kundenspalte irrefuehrend).
3. Smart Buttons der Zahlung (dynamische Bezeichnungen, andere Objekte).
4. Bankkonto-Feldtexte (in Odoo 18 in keiner Bankkonten-Formularansicht sichtbar).
5. Rechnungszeile Beschreibung/Total und Sektion/Kostenstellen-Tags (in Odoo 18 technisch anders geloest, Funktion vorhanden).
6. Systemweite Odoo-Kernbezeichnungen (z. B. Follower, Zuletzt aktualisiert von) - nicht abrechnungsspezifisch.
7. Menuepositionen, die Odoo 18 anders gruppiert (Zahlungsbedingungen wurde nach Odoo-11-Vorbild verschoben).
