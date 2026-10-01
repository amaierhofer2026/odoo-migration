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

Damit sind alle technisch angleichbaren sichtbaren Unterschiede umgesetzt; es verbleiben nur die
fachlich oder technisch notwendigen Abweichungen (Zeilen 2 bis 4 und 7 der Tabelle).

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
Abweichungen. Der Bereich Abrechnung ist damit **funktional vollstaendig und migrationsvorbereitet**.
