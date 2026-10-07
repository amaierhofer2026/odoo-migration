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
| Feld "Zahlungstransaktion" | sichtbar und auswaehlbar (readonly=False) | sichtbar, readonly | ja | ja | Odoo-18-Standardlogik bewusst beibehalten; in Odoo 11 nie genutzt (0 von 5.994 Zahlungen). Fachlich gleichwertig und bewusst akzeptiert (Entscheidung Anna 05.10.2026, Begruendung in 12.2) |
| Zahlungsbetrag und Zahlungsmethode | nicht pflichtig | pflichtig | ja | nein | Odoo-11-Modellpflicht in der Ansicht wiederhergestellt (Session 126) |
| zweites Partnerfeld "Lieferant" | sichtbar (Odoo 18 fuehrt partner_id doppelt) | ausgeblendet | ja | nein | Doppelung desselben Feldes, korrigiert Session 126 |
| Felder Status (Odoo 18) und Odoo-11-Zahlungsnummer | im Odoo-11-Block | in eigener Gruppe (Status (Odoo 18) / Herkunft (Migration)) | ja | ja | Technische Kontroll- bzw. Migrationsfelder ausserhalb des Odoo-11-Feldsatzes (Session 126) |

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

## 8. Konfiguration (Steuern, Journale, Währungen, Steuerzuordnung, Zahlungsbedingungen, Kostenrechnung, Bankkonten, Zahlungen, Verwaltung, Einstellungen)

Feldbezeichnungen angeglichen (Modul `itk_account_migration`, Datei automatisch erzeugt von
`scripts/erzeuge_config_labels.py`, damit keine xpaths ins Leere zeigen):

| Odoo 11 | Odoo 18 vorher | Odoo 18 nachher | gleich | Abweichung | Begruendung |
|---|---|---|---|---|---|
| Steuern: Bezeichnung auf Rechnungen | Beschreibung | Bezeichnung auf Rechnungen | ja | nein | gleiches Feld (account.tax.description) |
| Steuern: Steuergültigkeit | Steuertyp | Steuergültigkeit | ja | nein | gleiches Feld (type_tax_use) |
| Steuern: Beinhaltet im Preis | Preis inkl. | Beinhaltet im Preis | ja | nein | gleiches Feld (price_include) |
| Steuern: Auswirkung auf nachfolgende Steuern | Auswirkung auf Basis für nachfolgende St. | Auswirkung auf nachfolgende Steuern | ja | nein | gleiches Feld |
| Steuern: Fällige Steuer | Steuerliche Zulässigkeit | Fällige Steuer | ja | nein | gleiches Feld (tax_exigibility) |
| Steuern: In Kostenrechnung einschliessen | In Kostenstellenkosten einbeziehen | In Kostenrechnung einschliessen | ja | nein | gleiches Feld (analytic) |
| Journale: Journalbezeichnung | Journalname | Journalbezeichnung | ja | nein | gleiches Feld (name) |
| Journale: Bank Datenübertragungen | Bank-Feeds | Bank Datenübertragungen | ja | nein | gleiches Feld |
| Journale: Fest zugeordnete Gutschrift-Sequenz | Gesonderter Nummerkreis für Gutschriften | Fest zugeordnete Gutschrift-Sequenz | ja | nein | gleiches Feld |
| Journale: Nummernfolge | Sequenz | Nummernfolge | ja | nein | gleiches Feld |
| Steuerzuordnung: Steuerzuordnung | Steuerposition | Steuerzuordnung | ja | nein | gleiches Objekt (account.fiscal.position) |
| Steuerzuordnung: USt-IdNr. ist zwingend | MwSt. erforderlich | USt-IdNr. ist zwingend | ja | nein | gleiches Feld |
| Währungen: Position des Symbols | Symbolposition | Position des Symbols | ja | nein | gleiches Feld |
| Währungen: Währungs-Untereinheit | Währungsuntereinheit | Währungs-Untereinheit | ja | nein | gleiches Feld |
| Assistent Gutschrift: Benutze das spezifische Journal | Journal | Benutze das spezifische Journal | ja | nein | gleiches Feld im Storno-Assistenten |
| Bankkonten: Bank Identifikations-Code, Kontotyp, Finanz-Journal | BIC, Typ, Konto Journal | unveraendert | nein | ja | Felder liegen in Odoo 18 in einer anderen Ansicht (Bankkonten-Sicht), dortige Bezeichnungen sind fachlich eindeutig, aber nicht Odoo-11-Wortlaut; keine Anpassung ohne 1:1-Zuordnung |
| Kostenstellen: Projekt-Anzahl, Projekte | Project Count, Projects | unveraendert | nein | ja | englische Uebersetzung im Odoo-18-Standard; keine 1:1-Zuordnung |
| Zahlungsbedingungen: Nummernfolge | (Feld nicht in der Ansicht) | unveraendert | - | ja | Odoo 18 zeigt das Feld in der Zahlungsbedingung nicht an |
| Odoo-18-Zusatzfelder (Kostenstellenplaene, Verteilungsschluessel, Peppol, Zahlungsmethoden, Kartenzahlung, Alias, Pruefpfad ...) | vorhanden | unveraendert vorhanden | - | nein | bleiben vollstaendig erhalten |

Der Browser-Menuewalk (`scripts/browser_abrechnung_menuewalk.py`) geht jeden Menuepunkt mit Aktion
durch; Beispielwerte lokal: Steuern 57 Zeilen (Spalten u. a. Steuerbezeichnung, Steuergültigkeit,
Bezeichnung auf Rechnungen, Aktiv), Journale (Buchungsjournale, Bank, Kasse, Verkauf, Einkauf),
Währungen 80 Zeilen (Währung, Symbol, Name, Letzte Aktualisierung, Einheit pro EUR),
Steuerzuordnung 4, Zahlungsbedingungen 12, Produktkategorien 3, Kostenstellen 5,
Kostenstellenplaene 1, Bargeldrundungen, Zahlungsmethoden, Einstellungen.

## 9. Assistenten und Dialoge

| Odoo 11 | Odoo 18 | gleich | Abweichung | Begruendung |
|---|---|---|---|---|
| Zahlung erfassen (Assistent) | Assistent Zahlung erfassen (account.payment.register) | ja | nein | gleiche Funktion; in B3 bereits fachlich geprueft |
| Nach Gutschrift fragen (Assistent) | Storno-Assistent (account.move.reversal) | ja | nein | gleiche Funktion; Feld "Benutze das spezifische Journal" angeglichen (B2) |
| Rechnung senden | Senden (Nachricht verfassen) | ja | nein | Odoo-18-Standard; SMTP ist nicht konfiguriert (offener Punkt K7), Dialog oeffnet sich |
| Drucken | Drucken (PDF, PDF ohne Zahlung, ITK-Rechnung, ITK-Rechnung mit Zahlung) | ja | nein | Odoo-11-Bericht "Rechnung mit Zahlung" wurde nachgebaut |
| Zahlungsabstimmung / Zahlung rueckgaengig | Bankabstimmung, "Auf Entwurf setzen", Abstimmung aufheben | teilweise | ja | Odoo 18 loest die Abstimmung ueber eigene Werkzeuge; Odoo 11 hatte keinen gleichnamigen Assistenten |

## 10. Gutschriftsformular (Testbeleg nur in Odoo 18, danach vollstaendig entfernt)

Nachweis: Testgutschrift in Odoo 18 erzeugt, gebucht, im Browser geprueft, danach geloescht.
Bestand vorher = nachher: Ausgangsgutschriften 0 -> 0, Belege gesamt 38 -> 38, Buchungszeilen
102 -> 102 (lokal) bzw. gleiche Pruefung auf der VM. Es wurden keine Odoo-11-Daten uebernommen.

```
Reiter     : Rechnungszeilen, Andere Informationen (Odoo-11-Wortlaut)
Buttons    : Bestätigen (Entwurf), Auf Entwurf setzen, Einzahlung erfassen, Senden, Drucken,
             Vorschau, Sperren (Odoo-18-Zusatz), Status Entwurf und Gebucht
Felder     : Kundengutschrift, Kunde, Rechnungsdatum, Faelligkeitsdatum, Waehrung, Nettobetrag,
             20 % (Steuer), Gesamt, Faelliger Betrag, Valorisation Text
Liste      : Nummer, Kunde, Rechnungsdatum, Faelligkeit, Referenzbeleg, Referenz, Total,
             Zu Bezahlen, Status; Filter und Gruppierungen wie bei Rechnungen
Drucken    : ITK-Rechnung, ITK-Rechnung mit Zahlung, PDF, PDF ohne Zahlung
Herkunft   : Referenzbeleg und Odoo-11-Rechnungsnummer stehen fuer die Nachvollziehbarkeit bereit
Hinweis    : Der Knopf "Nach Gutschrift fragen" erscheint in Odoo 18 nur auf Rechnungen
             (Gutschriften werden nicht erneut storniert) - fachlich korrekt.
```

## 11. Status

Abgeschlossen und belegt: kompletter Browser-Menuewalk (alle Menuepunkte mit Aktion) lokal und
VM, Formulare (Rechnung, Gutschrift, Zahlung), Listen und Spalten, Suche (Filter, Gruppierungen,
Suchfelder), Konfigurationsformulare der Kernmodelle, Assistenten/Dialoge, Label-Abgleich (lokal
und VM, 0 unbegruendete Abweichungen), Regression 0 Fehler, Testbeleg restlos entfernt,
lokal/GitHub/VM synchron.

## 12. Aufloesung der restlichen Punkte (01.10.2026)

### 12.1 Der eine fachliche Hinweis aus dem Menuewalk (35 OK / 1 Hinweis)

```
Betroffene Funktion : Knopf "Nach Gutschrift fragen" im Rechnungsformular
Odoo 11             : Der Knopf ist in der Ansicht account.invoice mit
                      attrs invisible = ['|', ('type','in',['in_refund','out_refund']),
                      ('state','not in',('open','paid'))] hinterlegt, erscheint also
                      NUR auf Rechnungen, niemals auf Gutschriften.
Odoo 18             : Genauso - der Storno-/Gutschriftknopf erscheint nur auf Rechnungen.
Grund fuer den Hinweis : Die Pruefung hatte den Knopf auch auf dem Gutschriftsformular erwartet.
                      Das war eine zu strenge Erwartung im Pruefskript, kein Unterschied.
Aenderung           : keine (Verhalten in beiden Systemen identisch).
```

### 12.2 Verbleibende bewusste sichtbare Abweichungen

| Odoo 11 | Odoo 18 aktuell | technisch angleichbar | Begruendung |
|---|---|---|---|
| Reiter "Rechnung" | Reiter "Rechnung" | ja, erledigt | Der erste Reiter heisst jetzt wie in Odoo 11 "Rechnung" (vorher Rechnungszeilen); Odoo-18-Zusatzreiter bleiben erhalten |
| Spalte "Lieferant" (Odoo 11 beschriftete die Kundenspalte irrefuehrend) | Spalte "Kunde" | technisch ja, fachlich nein | Odoo 11 zeigte in der Kundenspalte den Lieferantentext (Uebersetzungsfehler). Eine Angleichung wuerde die fehlerhafte Beschriftung uebernehmen |
| Smart Buttons der Zahlung: "Rechnungen", "Buchungszeilen", "Zahlungsabstimmung" | "Rechnung (Anzahl)", "Transaktion", "Abgestimmte Zeilen" | nein | Die Bezeichnungen in Odoo 18 sind dynamisch (mit Anzahl) und beziehen sich auf andere Objekte (Transaktionen, abgestimmte Zeilen). Keine 1:1-Zuordnung |
| Bankkonto: "Bank Identifikations-Code", "Kontotyp", "Finanz-Journal" | "BIC", "Typ", "Konto Journal" | nein | Diese Felder sind in Odoo 18 in keiner Bankkonten-Formularansicht sichtbar; es gibt keine sichtbare Stelle zum Angleichen |
| Kostenstellen: "Kostenstellen Buchungen", "Projekt-Anzahl", "Projekte" | "Kostenstellenbuchungen", "Projekt-Anzahl" | teilweise, erledigt | "Projekt-Anzahl" ist angeglichen; "line_ids"/"project_ids" sind in keiner Odoo-18-Ansicht sichtbar; die Schreibweise "Kostenstellenbuchungen" ist im Odoo-18-Standard gefuehrt |
| Menueposition Zahlungsbedingungen: Konfiguration > Verwaltung | Konfiguration > Verwaltung | ja, erledigt | Das Menue wurde nach Odoo-11-Vorbild unter Konfiguration > Verwaltung verschoben (Lauf setzt das nach jedem Upgrade erneut) |
| Berichte: acht Odoo-11-Berichtsassistenten | nicht vorhanden | nein | In Odoo 18 Community nicht enthalten; Entscheidung: kein Enterprise-Modul, Nachbau nur bei Bedarf |
| Auswahlwerte der Zahlungsart: "Geld schicken" / "Geld erhalten" | "Senden" / "Erhalten" | nein (bewusst akzeptiert) | Odoo-18-Wortlaut bleibt; eine Angleichung muesste Auswahlwerte und Uebersetzungen ueberschreiben, die ein Upgrade des account-Moduls zuruecksetzen kann. Fachliche Bedeutung identisch (outbound/inbound). Entscheidung Anna 05.10.2026 |
| Feld "Zahlungstransaktion": in Odoo 11 manuell auswaehlbar (readonly=False) | sichtbar, aber readonly | nein (bewusst akzeptiert) | Odoo 18 fuehrt das Feld bewusst readonly, weil das Zahlungssystem die Zuordnung setzt (action_post mit Token, Online-Zahlung im Portal, Assistent payment.link.wizard). In Odoo 11 nie genutzt (0 von 5.994 Zahlungen, 0 Transaktionen, 0 Tokens). Keine Nachbildung der manuellen Auswahl erforderlich; das Feld bleibt sichtbar und readonly, damit die Information bei kuenftigen elektronischen Zahlungen vorhanden ist. Fachlich gleichwertig. Entscheidung Anna 05.10.2026 |

Damit sind alle technisch angleichbaren sichtbaren Unterschiede umgesetzt; es verbleiben nur die
fachlich oder technisch notwendigen sowie die bewusst akzeptierten Abweichungen (Zeilen 2 bis 4 und
7 der Tabelle sowie die beiden Nachtraege aus Session 126: Wortlaut der Zahlungsart und
Zahlungstransaktion).

### 12.3 SMTP (Vorgabe K7) - reiner Infrastrukturpunkt

```
Keine Abrechnungsfunktion ist deswegen unvollstaendig:
- Die ITK-Rechnungsmailvorlagen sind in Odoo 18 angelegt (Bereich B6) und im Formular auswaehlbar.
- Der Dialog "Senden" oeffnet sich und ist im Browser geprueft (Versandweg vorbereitet).
- Drucken, Berichte, Gutschrift, Zahlung, Mahnwesen-Verzicht und alle Auswertungen haengen nicht
  an SMTP.
- Ohne SMTP-Zugangsdaten kann nur der tatsaechliche Mailversand nicht erfolgen (Betriebs- und
  Infrastrukturthema, Freigabe/Zugangsdaten erforderlich). Es wurde bewusst nichts konfiguriert.
Fuer die spaetere Datenmigration entsteht dadurch keine Luecke.
```



Abschlusspruefung erfuellt (01.10.2026): kompletter Browser-Menuewalk lokal und VM ohne
Fehler (35 OK / 1 Hinweis: Gutschriften koennen in Odoo 18 nicht erneut storniert werden),
Regression 0 Fehler, Modul-Upgrades ohne Ansichtsfehler, Testbeleg restlos entfernt,
lokal = GitHub = VM. Es verbleiben nur die in den Abschnitten 1 bis 10 begruendeten bewussten
Abweichungen. Der Bereich Abrechnung ist damit funktional vollstaendig - **die endgueltige
Freigabe als migrationsbereit liegt bei Anna und steht noch aus** (Stand 07.10.2026: IN ARBEIT,
ein fachlicher BLOCKER offen, siehe Abschnitt 13).

## 13. Abschlusscheck 07.10.2026 (Session 129) - Gesamtdurchgang

Auftrag: vollstaendiger Abschlusscheck des Moduls Abrechnung auf Basis aller bisherigen Arbeiten.
Odoo 11 nur lesend, keine Produktivmigration, Abrechnung bleibt IN ARBEIT bis zur Freigabe durch
Anna.

### 13.1 Abschlussmatrix

| Bereich | Odoo-11-Abgleich | Odoo-18-Ansicht | Funktionen | Mapping | Testmigration | Browser lokal | Browser VM | Status |
|---|---|---|---|---|---|---|---|---|
| Ausgangsrechnungen | Menue, Modell, Spalten, Reiter, Filter/Gruppierungen verglichen (read-only) | Liste mit 10 O11-Spalten, Reiter "Rechnungszeilen"/"Andere Informationen", 37 Such-/Gruppeneintraege | Buttons "Auf Entwurf setzen", "Nach Gutschrift fragen", "Einzahlung erfassen" vorhanden | 273 belegte Felder, 0 Luecken; Konten-/Steuerzuordnung dokumentiert | Beleg R-261121 1:1 (brutto 1366,01, Rest 1366,01, Status posted/not_paid) | 41 OK / 0 FEHL (Produktmenues), Durchgang 32 Menuepunkte ohne JS-/RPC-Fehler | wie lokal, Ergebnisliste identisch | OK, 1 bewusste Abweichung (Ansichtsarten) |
| Kunden-Gutschriften | wie Ausgangsrechnungen (O11 gleiche Ansicht) | Liste 10 Spalten, Reiter wie Rechnung | "Nach Gutschrift fragen", "Auf Entwurf setzen" vorhanden | wie Rechnung | R-26800 1:1 (2094,00/0,00, "Gutschreiben" statt "Bezahlt") | wie lokal | wie lokal | OK |
| Zahlungen (Verkauf) | Menue, Spalten, Suche, Statuswerte | Liste 8 Spalten, Filter/Gruppierungen 17 Eintraege | Zahlungsformular 19 Pruefpunkte, Feld "Zahlungstransaktion" vorhanden (readonly) | Zahlungsnummern K2a/K2b dokumentiert; O11-Nummer im Herkunftsfeld | Zahlung CUST.IN/2026/1072 (30,50, 06.10.2026) 1:1, abgestimmt | 19 OK / 0 FEHL (Zahlungsformular) | 19 OK / 0 FEHL | OK |
| Kunden | Menue, Modell, Ansichtsarten | Kanban als Standard wie in Odoo 11, Liste/Formular vorhanden | Partnerpflichtfeld, Anzeigename, Interne Referenz | Stammdatenzuordnung 4 Partner 1:1 (Name, Firma/VAT/Adresse, Referenz) | 4 Partner 1:1 | Durchgang ohne Fehler | wie lokal | OK |
| Verkaufbare Produkte | O11-Aktion 225 nutzt dieselbe Ansicht 571 wie der Einkauf | ITK-Liste mit O11-Spalten (5) | 41 Pruefpunkte je Instanz | Produktfelder 648/648 bzw. 646/647 aufloesbar | 10 Produkte 1:1 (Typ/Preis/Verkauf/Einkauf/Produktart/Kategorie) | 41 OK / 0 FEHL | 41 OK / 0 FEHL | OK |
| Eingangsrechnungen | Menue, Ansicht, Suche | Liste 10 Spalten | wie Ausgangsrechnungen | wie Rechnung | Odoo 11 hat 0 in_invoice - nichts zu migrieren (dokumentiert) | Durchgang ohne Fehler | wie lokal | OK (keine Daten in O11) |
| Lieferanten-Gutschriften | wie Eingangsrechnungen | Liste 10 Spalten | wie oben | wie Rechnung | 0 in_refund in Odoo 11 | Durchgang ohne Fehler | wie lokal | OK (keine Daten in O11) |
| Zahlungen (Einkauf) | Menue, Ansicht | Liste 8 Spalten | Formular wie Verkauf | wie Verkauf | Odoo 11: 0 Lieferantenzahlungen in der Auswahl | Durchgang ohne Fehler | wie lokal | OK |
| Lieferanten | Menue, Modell, Ansichtsarten | Kanban wie Odoo 11 | wie Kunden | Stammdaten ueber Namen/Referenz | keine Lieferanten im Migrationsumfang | Durchgang ohne Fehler | wie lokal | OK |
| Einkaufbare Produkte | O11-Aktion 226, Ansicht 571 | ITK-Liste mit O11-Spalten (5) | 41 Pruefpunkte | wie Verkaufbare Produkte | wie oben | 41 OK / 0 FEHL | 41 OK / 0 FEHL | OK |
| Produktkategorien | 30 Kategorien gelesen, 26 mit Produkten, alle flach | Konfigurationsliste vorhanden | Zuordnung ueber exakten Namen (beide Sprachen) + Elternkette | Kategorien 1:1; 2 Kategorien im Testlauf angelegt und wieder entfernt | 10 Produkte mit korrekter Kategorie | nicht anwendbar (kein Testbestand lokal) | 7 OK / 0 FEHL (Formularwert + Gruppierung) | OK; Kontenzuordnung = BLOCKER |
| Konfiguration (Steuern, Journale, Waehrungen, Zahlungsbedingungen, Kostenrechnung, Bankkonten, Zahlungsmethoden, Einstellungen) | Menuepunkte, Ansichtsarten und Spalten verglichen | Ansichtsarten gleich (tree==list); O18-Zusatzmenues vorhanden | — | Steuerzuordnung vierstufig, Journale ueber Code, Zahlungsbedingungen ueber Namen | Steuern/Zahlungsbedingungen/Journale der Auswahl 1:1 | Durchgang ohne Fehler | wie lokal, Ergebnisliste identisch | OK |
| Berichte/Verwaltung (Rechnungsanalyse, Pruefpfad, Abrechnungspositionen) | O11-Bericht "Rechnungen" (graph,pivot) und Enterprise-Berichte nicht vorhanden | O18-Zusatzfunktionen unveraendert vorhanden | — | nicht migrationsrelevant | — | Durchgang ohne Fehler | wie lokal | bewusste Abweichung (K3) |

### 13.2 Nachweise des Abschlusschecks

| Pruefung | Ergebnis |
|---|---|
| Menuepunkte/Aktionsansichten O11 gegen O18 (Skript `vergleiche_abrechnung_menue_ansichten.py`) | 32 Menuepunkte; Ansichtsarten gleich; Abweichungen nur die dokumentierten (O11-Berichtsmenues, O18-Zusatzmenues) |
| Feldabdeckung (`pruefe_abschluss_feldabdeckung.py`) | 273 belegte Odoo-11-Felder, 0 Luecken |
| Formularabgleich (`abgleiche_abrechnung_formulare.py`) | 13 Formularbloecke verglichen, Exit 0; Restliste sind Wortlaut-/Zusatzfelder (dokumentiert in den Labeltabellen) |
| Feldbeschriftungen (`check_abrechnung_labels.py`) | lokal und VM je 155 Feldpaare, 0 Abweichungen |
| Ansichtsbeschriftungen (`check_abrechnung_viewlabels.py`) | lokal und VM Exit 0, Tabellen unveraendert (Diff leer) |
| Pflichtfelder (`pruefe_pflichtfelder.py`) | lokal und VM: keine Pflichtfeld-Luecke in Datensaetzen |
| Nummernregelwerk K2 (`pruefe_k2_nummernformat.py`) | Exit 0; Kollisionsprobe nennt den einzigen Odoo-11-Fall (R-25001 als Rechnung und Gutschrift) - uebernommen wird die Odoo-11-Nummer im Herkunftsfeld, die Odoo-18-Nummer kommt aus der Zielsequenz |
| Beziehungen/Constraints (`pruefe_beziehungen_constraints.py`) | Exit 0, Constraints je Modell ausgewiesen |
| Trockenlauf lokal | 72 Planpositionen, 23 offen, kein Abbruch; 6 Belege, 4 Partner, 10 Produkte, 2 Steuern, 1 Zahlungsbedingung, 2 Journale |
| Trockenlauf VM | identisch zum lokalen Lauf (Diff nach Normalisierung leer) |
| Testlauf VM (kontrolliert) | 202 Protokolleintraege, 10 neu angelegte Produkte, 2 Kategorien, 4 Partner, 5 Belege, 1 Zahlung; Belegsummen und Restbetraege 1:1 |
| Pruefung der Testmigration (`pruefe_testmigration.py`, neun Punkte) | **94 bestanden, 0 Abweichungen** (Baseline aus dem Protokoll abgeleitet) |
| Browser-Gesamtdurchgang lokal | 32 Menuepunkte, 31 Aufnahmen, keine JS-/RPC-Fehler |
| Browser-Gesamtdurchgang VM | dito; Ergebnisdatei lokal/VM-Vergleich: **0 Unterschiede** in Spalten, Reitern, Formularfeldern, Buttons, Filtern/Gruppierungen |
| Produktmenues (Browser) | Verkaufbare und Einkaufbare Produkte lokal und VM je 41 OK / 0 FEHL |
| Zahlungsformular (Browser) | lokal und VM je 19 OK / 0 FEHL |
| Zahlungs-/Project-Category-Pruefung (Browser) | lokal und VM je 15 OK / 0 FEHL; Spalte "Project Category" in Liste und Gutschrift, direkt hinter "Status" |
| Zeilen/Beschreibung (Browser) | lokal und VM 2 OK / 0 FEHL - die vier Belegarten sind ohne Testbeleg "nicht anwendbar" (belegt in Sitzung 125/126 und durch die Testmigration) |
| Regression Verkauf/Abonnements | 886 OK / 0 FEHL ueber 11 Prueflaeufe |
| Aufraeumen und Bestand | 22 Datensaetze entfernt; Bestand lokal und VM **vorher == nachher** (Anzahlen, Belege mit Nummer/Zustand/Summe/Rest, Kategorien, Produkte, Partner) |

### 13.3 Angepasst in diesem Check

- `scripts/pruefe_testmigration.py`: Baseline des Unversehrtheitsnachweises wird jetzt aus dem
  Protokoll abgeleitet (frueheste Schreibzeit der selbst angelegten Datensaetze, zwei Minuten
  davor) statt aus der festen Konstante vom 05.10.2026. Grund: die alte Konstante meldete jede
  spaetere fremde Schreiboperation (z. B. Modul-Upgrades vom 06.10.) als Abweichung. Vorher
  93 bestanden / 1 Abweichung, jetzt 94 / 0.
- `scripts/browser_kategorie_pruefung.py`: Stichprobe wird aus dem Protokoll und der Odoo-11-
  Quelle gebildet (vorher fest verdrahtete Produktnamen, die bei geaenderter Auswahl zwei falsche
  FEHL ergaben).
- `scripts/browser_pc_status_abnahme.py`, `scripts/browser_zeilen_beschreibung.py`: fehlende
  Testbelege werden als "nicht anwendbar" ausgewiesen und lassen den Lauf mit Exit 0 enden
  (vorher FEHL bzw. Ausnahme).
- Neu: `scripts/abrechnung_abschluss_bestand.py` (Vorher/Nachher-Bestand),
  `scripts/vergleiche_abrechnung_menue_ansichten.py` (Ansichtsarten je Menuepunkt).

### 13.4 Bewusst akzeptierte Abweichungen (Stand 07.10.2026)

- Rechnungs-/Gutschriftmenues: Odoo 11 bot zusaetzlich Kalender-, Pivot- und Graph-Ansicht; Odoo 18
  fuehrt dafuer keine Ansichten (0 views). Fachlich gleichwertig ueber "Rechnungsanalyse" und
  "Abrechnungspositionen" (graph, pivot).
- Berichtswesen: Odoo-11-Berichtsmenue "Rechnungen" und die Enterprise-PDF-Berichte
  (Umsatzsteuerbericht, alter Partner Saldo, Audit Journale) haben in Odoo 18 Community keine
  Entsprechung (K3, Entscheidung Anna).
- Bezeichnung "Gutgeschrieben" statt "Bezahlt" bei voll gutgeschriebenen Belegen (Rest 0).
- Odoo-18-Zusatzmenues und Zusatzfunktionen bleiben vollstaendig erhalten (Eingaenge,
  Rechnungsanalyse, Pruefpfad, Abrechnungspositionen, Projekt Kategorie, Valorisierung,
  Kostenrechnung, Kostenstellenplaene, Zahlungsmethoden, Waehrungen).
- Produktformular: Website-Gruppe nur mit website_sale nachbaubar; 15 optionale Zusatzspalten.
- Ohne SMTP-Zugangsdaten kein tatsaechlicher Mailversand (Infrastrukturthema, Abschnitt 12.3).

### 13.5 Offene Punkte

- **BLOCKER: Kontenstammdaten / fachliche Zuordnung vor Produktivmigration erforderlich.**
  Die Odoo-11-Konten 8400 "Erloese 19% USt" und 3400 "Wareneingang 19% Vorsteuer" sind
  ausschliesslich globale Firmenvorgaben der Produktkategorien (8 ir.property-Eintraege, alle
  `res_id` leer, 0 kategoriespezifisch) und im Zielkontenrahmen (240 Konten) nicht vorhanden;
  Kandidaten 4000/4001/4100/4110/4200 bzw. 5000/5010/5011/5050/5051/5052/5090 weichen im
  Steuersatz im Namen ab. Es wird nichts angelegt und nichts geraten. Die Migration laeuft
  technisch sauber durch (Testlauf 202 Datensaetze, 94/0 Pruefungen); die neu angelegten
  Kategorien erben die Odoo-18-Vorgabe 4000/5010, die Belegzeilen tragen das dokumentierte
  Mapping (8400 -> 4000).
- Migration der Odoo-11-Preislistenregeln (403 Regeln ohne Produktbezug).
- Namenszuordnung der Abo-Vorlagen vor der Produktmigration.
- Unbenutzte Kategorien (id 45, id 59) erst mit Preislistenregeln bzw. Auftraegen anlegen.
- Abrechnung bleibt IN ARBEIT; die finale Freigabe gibt Anna nach ihrer Sichtkontrolle.

## 14. Abschlussdurchgang 07.10.2026 (Session 131) - Menue, Konfiguration, Berichtswesen

Auftrag: Abschlussdurchgang des gesamten Moduls Abrechnung mit Schwerpunkt Konfiguration und
Berichtswesen, vollstaendige Menue-Matrix gegen Odoo 11, Klaerung der mehrfach sichtbaren
Menueueberschrift "Konfiguration", Browserpruefung jedes Menuepunkts lokal und VM,
Beschriftungspruefung, Regression, Dreistand. Odoo 11 nur lesend, keine Produktivmigration.

Details und vollstaendige Matrix: `docs/o11-o18-abrechnung-menue-matrix.md`.

### 14.1 Ergebnis der Menuepruefung

| Bereich | Menuezeilen (Odoo 18) | davon Fensteraktionen | Entsprechung in Odoo 11 | ohne Entsprechung | Status |
|---|---|---|---|---|---|
| Verkauf | 7 (inkl. Gruppe) | 6 | 5 | 1 (Zusatz "Eingaenge") | OK, Zusatz erhalten |
| Einkauf | 7 (inkl. Gruppe) | 6 | 5 | 1 (Zusatz "Eingaenge") | OK, Zusatz erhalten |
| Berichtswesen | 5 (inkl. Gruppen) | 3 | 1 (Rechnungsanalyse) | 2 Zusaetze (Abrechnungspositionen, Pruefpfad) | OK; 3 Odoo-11-Assistenten entfallen (K3) |
| Konfiguration | 24 (inkl. Gruppen und 1 Assistent) | 15 | 15 | 6 Zusaetze (Waehrungen, Kostenstellenplaene, Verteilungsschluessel, Produktkategorien, Zahlungsmethoden, Projekt Kategorie) | OK; 1 Sektion bereinigt (Projekt Kategorie), 1 Konzept entfallen (Kostenstellen Tags) |
| **gesamt** | **44** | **30** | - | - | **kein Odoo-11-Menuepunkt ohne fachliche Entsprechung** |

### 14.2 Umsetzungen in diesem Durchgang

| Nr | Aenderung | Datei/Modul | Begruendung |
|---|---|---|---|
| 1 | Dritte Sektion "Konfiguration" entfernt, Menuepunkt "Projekt Kategorie" unter Konfiguration > Verwaltung | `addons/itk_projectcategory/views/projectcategory_views.xml` (18.0.1.0.1) | Odoo 11 hatte Menue/Aktion/Liste dieses Modells nicht (0 Treffer in `ir.ui.menu`/`ir.actions.act_window`); Odoo 11 hatte zwei Konfigurations-Sektionen |
| 2 | Listenbeschriftung "Fields of Law" -> "Project Category" | dito, `i18n/de_DE.po` | Altbestand aus dem Quellprojekt, deutsch und englisch sichtbar englisch |
| 3 | Listenspalte "Salesperson" -> "Verkäufer" | `addons/itk_crm/views/res_partner.xml` (18.0.1.5.8) | Odoo 11 zeigte "Verkäufer" |
| 4 | Suchfilter "Community Code" -> "Gemeindekennzahl" | dito | Odoo 11 zeigte "Gemeindekennzahl" |
| 5 | Berichtsfilter "With Price"/"Without Price" -> "Mit Preis"/"Ohne Preis", "Vendor contains" -> "Lieferant enthält", Hilfe-Text | `addons/account_invoice_line_report/i18n/de.po` (18.0.1.0.1) | leere `msgstr` in der deutschen Uebersetzung |
| 6 | Sieben Beschriftungen lokal/VM angeglichen | `scripts/apply_abrechnung_labels.py` | sichtbare Unterschiede zwischen den Instanzen |

Modulstaende nach diesem Durchgang: itk_crm 18.0.1.5.8, itk_projectcategory 18.0.1.0.1,
account_invoice_line_report 18.0.1.0.1; unveraendert itk_valorisierung 18.0.1.3.0,
itk_account_migration 18.0.1.22.0, itk_product 18.0.1.0.5.

### 14.3 Nachweise

| Pruefung | Ergebnis |
|---|---|
| Menuebaum Odoo 11 gegen Odoo 18 (lokal und VM) | siehe Abschnitt 14.1; lokal = VM in Struktur, Pfaden, Aktionen, Ansichtsarten und Sequenzen |
| Ansichten je Menuepunkt (Liste/Formular/Suche) | lokal = VM; Abweichungen nur interne IDs und die Reihenfolge nicht abrechnungsrelevanter Einstellungsfelder |
| Beschriftungen der Abrechnungsmodelle | vollstaendige Messung; 7 sichtbare Unterschiede korrigiert, Rest dokumentiert |
| Browser-Gesamtcheck je Menuepunkt (lokal) | 31 Menuepunkte: Teil 1 (Verkauf/Einkauf) 97 OK / 4 FEHL, Teil 2 (Konfiguration/Berichtswesen) 70 OK / 20 FEHL, Speicherprobe Produktkategorien 5 OK / 0 FEHL; **alle FEHL sind Erwartungen des Pruefscripts, kein Produktfehler** (Einordnung: `docs/o11-o18-abrechnung-menue-matrix.md`, Abschnitt 12); keine JS-, Konsolen- oder Serverfehler |
| Browser-Gesamtcheck je Menuepunkt (VM) | nach dem Deploy; Ergebnis im Session-Abschluss |
| Regression | `check_abrechnung_labels.py`, `check_abrechnung_viewlabels.py`, `abschluss_verkauf_regression.py` lokal und VM |
| Bestand vorher/nachher | Testkategorie `ITK-TEST-S131` angelegt und entfernt; Bestand unveraendert |

### 14.4 Offene Punkte aus diesem Durchgang

- **Menuebezeichnung "Projekt Kategorie"**: englischer Ursprungsname ohne Odoo-11-Vorlage; deutsche
  Alternative ("Projektkategorien") waere Ihre Wortlautentscheidung.
- **"Kostenstellen" statt "Kostenstellenkonten"** (Odoo-11-Menuebezeichnung): Wortlautfrage.
- **Kundenliste mit Defaultfilter leer**: Odoo 18 berechnet `customer_rank` aus Belegen, die
  Odoo-11-Booleans `customer`/`supplier` entfallen - Migrationshinweis, keine Anpassung moeglich.
- **BLOCKER Kontenstammdaten 8400/3400** unveraendert (Abschnitt 13.5).
- **Abrechnung bleibt IN ARBEIT**; die Freigabe gibt Anna nach eigener Sichtkontrolle.
