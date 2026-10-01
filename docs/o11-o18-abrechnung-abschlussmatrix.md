# Abschlussmatrix Bereich Abrechnung (Odoo 11 gegen Odoo 18)

Stand: 01.10.2026, Session 122. Bereich Abrechnung bleibt bis zum Abschluss des
Browser-Durchgangs **IN ARBEIT**. Odoo 11 wurde ausschliesslich gelesen, geaendert wurde nur
Odoo 18, keine Datenmigration, kein Testdatensatz migriert.

Spalten: Odoo-11-Bezeichnung | Odoo-18 vorher | Odoo-18 nachher | Funktion fachlich gleich |
bewusste Abweichung | Begruendung

## 1. App und Menues

| Odoo 11 | Odoo 18 vorher | Odoo 18 nachher | gleich | Abweichung | Begruendung |
|---|---|---|---|---|---|
| Abrechnung | Rechnungsstellung | Abrechnung | ja | nein | gleicher Menueeintrag, nur sichtbare Bezeichnung (de_DE) |
| Abrechnung > Verkauf | Kunden | Verkauf | ja | nein | gleicher Zweig (Kundenbelege) |
| Abrechnung > Einkauf | Lieferanten | Einkauf | ja | nein | gleicher Zweig (Lieferantenbelege) |
| Verkauf > Ausgangsrechnungen | Ausgangsrechnungen | Ausgangsrechnungen | ja | nein | unveraendert |
| Verkauf > Kunden-Gutschriften | Gutschriften | Kunden-Gutschriften | ja | nein | gleiche Gutschriftssicht |
| Einkauf > Eingangsrechnungen | Eingangsrechnungen | Eingangsrechnungen | ja | nein | unveraendert |
| Einkauf > Lieferanten-Gutschriften | Rueckerstattungen | Lieferanten-Gutschriften | ja | nein | gleiche Sicht |
| Verkauf > Verkaufbare Produkte | Produkte | Verkaufbare Produkte | ja | nein | gleiche Produktliste |
| Einkauf > Einkaufbare Produkte | Produkte | Einkaufbare Produkte | ja | nein | gleiche Produktliste |
| Konfiguration > Finanzen | Buchhaltung | Finanzen | ja | nein | gleicher Konfigurationszweig |
| Finanzen > Steuerzuordnung | Steuerpositionen | Steuerzuordnung | ja | nein | fachlich gleiches Objekt (Steuerzuordnung/Steuerposition) |
| Konfiguration > Bankkonten | Banken | Bankkonten | ja | nein | gleiche Bankkonten-Verwaltung |
| Konfiguration > Zahlungen > Zahlungsanbieter | Online-Zahlungen > Zahlungsanbieter | Zahlungen > Zahlungsanbieter | ja | nein | gleicher Zweig, Odoo-11-Wortlaut |
| Verkauf > Zahlungen | Zahlungen | Zahlungen | ja | nein | unveraendert |
| Verkauf > Kunden (Stammdaten) | Kunden | Kunden | ja | nein | unveraendert |
| Berichtswesen > Verwaltung > Rechnungen | Rechnungsanalyse | Rechnungsanalyse | nein | ja | Odoo-11-Bericht "Rechnungen" ist ein Berichtsassistent; in Community nicht verfuegbar (K3) |
| Berichtswesen > PDF Berichte (8 Assistenten) | nicht vorhanden | nicht vorhanden | nein | ja | kein Enterprise-Berichtsmodul (Entscheidung Anna) |
| kein Menue Dashboard | kein Menue Dashboard | kein Menue Dashboard | ja | nein | Odoo 11 hatte im Bereich Abrechnung kein Dashboard; Odoo 18 fuehrt dort ebenfalls keines |
| kein Menue Buchungen | kein Menue Buchungen | kein Menue Buchungen | ja | nein | Odoo 11 hatte im Bereich Abrechnung kein Buchungsmenue; Odoo 18 ebenfalls nicht |
| nicht vorhanden | Eingaenge, Rechnungsanalyse, Pruefpfad, Abrechnungspositionen, Projekt Kategorie, Valorisierung, Kostenrechnung | unveraendert vorhanden | - | nein | Odoo-18-Zusatzfunktionen bleiben vollstaendig erhalten |

## 2. Rechnungs- und Gutschriftsformular

| Odoo 11 | Odoo 18 vorher | Odoo 18 nachher | gleich | Abweichung | Begruendung |
|---|---|---|---|---|---|
| Reiter "Rechnung" | Reiter "Rechnungszeilen" | Rechnungszeilen | teilweise | ja | Inhalt gleich (Positionen); Odoo 18 trennt Kopfbereich und Positionen anders |
| Reiter "Andere Informationen" | Weitere Informationen | Andere Informationen | ja | nein | gleicher Reiter (Buchhaltungsangaben) |
| Button "Bestätigen" | Bestätigen / Buchen | Bestätigen / Buchen | ja | nein | gleiche Buchungsfunktion; Odoo 18 zeigt je Zustand eigenen Wortlaut |
| Button "Auf Entwurf setzen" | Auf Entwurf zurücksetzen | Auf Entwurf setzen | ja | nein | gleiche Funktion |
| Button "Nach Gutschrift fragen" | Gutschrift | Nach Gutschrift fragen | ja | nein | gleicher Assistent (Storno/Gutschrift) |
| Button "Einzahlung erfassen" | Zahlen | Einzahlung erfassen | ja | nein | gleicher Zahlungsassistent |
| keine Smart Buttons | 8 Smart Buttons (Zahlungen, Abgestimmte Zeilen, Einkaufsabgleich, Ist-Versteuerung, Verkaufs-/Einkaufsauftraege, Transaktionen) | unveraendert vorhanden | - | nein | Odoo-18-Zusatzfunktionen bleiben erhalten |
| kein Button "Senden"/"Drucken" am Kopf | Senden, Drucken, Vorschau, PEPPOL, Sperren, Storno | unveraendert vorhanden | - | nein | Zusatzfunktionen bleiben erhalten |

## 3. Zahlungsformular

| Odoo 11 | Odoo 18 vorher | Odoo 18 nachher | gleich | Abweichung | Begruendung |
|---|---|---|---|---|---|
| Button "Bestätigen" | Bestätigen / Validieren | unveraendert | ja | nein | gleiche Buchungsfunktion |
| Button "setze auf Entwurf" | Auf Entwurf zurücksetzen | setze auf Entwurf | ja | nein | gleiche Funktion |
| Smart Button "Rechnungen" | Rechnung(en) | unveraendert | ja | nein | gleiche Verknuepfung; Odoo 18 zeigt Text und Anzahl dynamisch |
| Smart Button "Zahlungsabstimmung" | Abgestimmte Zeilen | unveraendert | teilweise | ja | fachlich verwandt, aber anderer Umfang (Abstimmung statt Assistent) |
| Smart Button "Buchungszeilen" | Transaktion / Kontoauszugszeilen | unveraendert | teilweise | ja | Odoo 18 trennt Kontoauszugszeilen und Transaktionen |
| kein "Erstattung" | Erstattung | unveraendert vorhanden | - | nein | Odoo-18-Zusatzfunktion |

## 4. Listenansichten und Spalten

| Odoo 11 | Odoo 18 vorher | Odoo 18 nachher | gleich | Abweichung | Begruendung |
|---|---|---|---|---|---|
| Nummer | Nummer | Nummer | ja | nein | - |
| Lieferant (Kundenspalte, irrefuehrende Odoo-11-Bezeichnung) | Kunde | Kunde | ja (Inhalt) | ja | Odoo 11 beschriftete die Kundenspalte "Lieferant"; Odoo 18 trennt korrekt nach Belegart |
| Rechnungsdatum | Rechnungsdatum | Rechnungsdatum | ja | nein | - |
| Faelligkeit | Faelligkeitsdatum | Faelligkeit / Faelligkeitsdatum | ja | nein | Odoo-11-Wortlaut zusaetzlich verfuegbar |
| Referenz | Referenz | Referenz | ja | nein | - |
| Referenzbeleg (Herkunft) | Referenzbeleg | Referenzbeleg | ja | nein | - |
| Total | Total | Total | ja | nein | - |
| Zu Bezahlen | Zu Bezahlen | Zu Bezahlen | ja | nein | - |
| Status | Status | Status | ja | nein | - |
| keine Steuerspalten | Exklusive Steuern, Steuer | unveraendert (optional) | - | nein | Odoo-18-Zusatzspalten bleiben erhalten |
| keine Verkaeuferspalte | Verkaeufer (optional) | unveraendert | - | nein | Zusatzspalte bleibt |
| Odoo-11-Rechnungsnummer | neu | Odoo-11-Rechnungsnummer (optional) | - | nein | Feld fuer die Migration (K2a) |

## 5. Suche: Filter, Gruppierungen, Suchfelder

| Odoo 11 | Odoo 18 vorher | Odoo 18 nachher | gleich | Abweichung | Begruendung |
|---|---|---|---|---|---|
| Entwurf | Entwurf | Entwurf | ja | nein | - |
| Offen | nicht direkt sichtbar | Offen | ja | nein | ergaenzt (gebraucht, Zahlungsstatus offen/teilweise) |
| Bezahlt | nicht direkt sichtbar | Bezahlt | ja | nein | ergaenzt |
| Ueberfaellig | Ueberfaellig | Ueberfaellig | ja | nein | - |
| Meine Rechnungen | Meine Rechnungen | Meine Rechnungen | ja | nein | - |
| Meine Aktivitaeten | nicht direkt sichtbar | Meine Aktivitaeten | ja | nein | ergaenzt |
| Verspaetete/Heutige/Anstehende Aktivitaeten | in Untermenue | zusaetzlich flach sichtbar | ja | nein | Odoo-11-Anordnung wiederhergestellt, Untermenue bleibt |
| Gruppierung "Partner" | Kunde | Partner (zusaetzlich) | ja | nein | Odoo-11-Wortlaut ergaenzt |
| Gruppierung "Verkaeufer" | Vertriebsmitarbeiter | Verkaeufer (zusaetzlich) | ja | nein | Odoo-11-Wortlaut ergaenzt |
| Gruppierung "Status" | Status | Status | ja | nein | - |
| Gruppierung "Rechnungsdatum" | Rechnungsdatum | Rechnungsdatum | ja | nein | - |
| Gruppierung "Faelligkeit" | Faelligkeitsdatum | Faelligkeit (zusaetzlich) | ja | nein | Odoo-11-Wortlaut ergaenzt |
| Suchfelder date, number, partner_id, journal_id, team_id, user_id | vorhanden (anders benannt) | unveraendert plus Odoo-11-Bezeichnungen | ja | nein | technische Suchfelder bleiben |
| keine Peppol-/Pruef-Filter | Gebucht, Abgebrochen, Nicht gesendet, Ausgangsrechnungen, Gutschriften, Zu pruefen, Peppol bereit, Zu zahlen, In Zahlung | unveraendert vorhanden | - | nein | Odoo-18-Zusatzfilter bleiben erhalten |

## 6. Feld- und Spaltenbezeichnungen

Vollstaendig dokumentiert in `docs/o11-o18-abrechnung-labelmapping.md` (57 Feldpaare, 33 gesetzte
Bezeichnungen, 0 unbegruendete Abweichungen) und `docs/o11-o18-abrechnung-viewlabels.md`
(Listenspalten). Bewusste Ausnahmen: `account.move.ref`, `account.move.payment_reference`,
`account.move.name` (keine fachlich identische 1:1-Zuordnung) sowie die Spalte Kunde/Lieferant.

## 7. Nachweise

```
Lokal : Menue-, Filter-, Gruppierungs- und Formulardurchgang im echten Browser
        (scripts/browser_abrechnung_oberflaeche.py, scripts/browser_abrechnung_durchgang.py)
VM    : gleicher Durchgang auf k001959vsx.ipax.at (verbindliche Abnahmeumgebung)
Label-/Menue-Lauf: lokal 12 gesetzt, VM 20 gesetzt, 0 Abweichungen
Regression: 0 Fehler
```

## 8. Status

Der Bereich Abrechnung ist weiterhin **IN ARBEIT**: der Durchgang ist fuer Menues, Filter,
Gruppierungen, Suchfelder, Listenansichten, Rechnungs-, Gutschrifts- und Zahlungsformular
dokumentiert. Offen bleiben die Detailpruefung der uebrigen Konfigurationsuntermenues
(Steuern, Journale, Waehrungen, Steuerzuordnung, Zahlungsbedingungen, Kostenrechnung) und der
Assistenten/Dialoge (Zahlungsassistent, Gutschriftsassistent) im Browser. Danach erfolgt die
Abschlussmarkierung.
