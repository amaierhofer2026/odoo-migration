# Teil 5, Block 3 – Browser-Gesamtabnahme Verkauf auf der VM

Datum: 29.09.2026
Zielinstanz: Odoo 18 VM `k001959vsx.ipax.at` (Datenbank `odoo18_test`, Firmenbezug IT-Kommunal GmbH)
Vergleichsbasis: Odoo 11 Prod `https://portal.it-kommunal.at` – in diesem Block **ausschliesslich
lesend** verwendet (keine Schreiboperation).
Regel: keine Datenmigration, Aenderungen nur in Odoo 18, Odoo-18-Zusatzfunktionen bleiben erhalten,
Testdaten nach der Pruefung bereinigt.

## 1. Vorgehen

Die Gesamtabnahme besteht aus zwei Teilen:

1. **Aggregatlauf** `scripts/abschluss_verkauf_browser_gesamtabnahme.py --instanz vm`
   Alle elf Browser-Abnahmewerkzeuge des Bereichs Verkauf laufen nacheinander gegen die VM,
   jedes mit eigenem frischem Browserprofil. Der Lauf zaehlt die Pruefungen, sammelt
   JavaScript- und RPC-Fehler und vergleicht den Bestand vor/nach dem Lauf.
2. **Durchgehender Klickpfad** `scripts/browser_verkauf_gesamtdurchgang.py --instanz vm`
   Ein Browser, eine Sitzung, 15 Stationen in fachlicher Reihenfolge (Menues, Liste, Formular,
   Reiter, Lagerbereich, Suche/Filter/Gruppierung, alle Ansichtstypen, Auftragskalender,
   Berichte, Drucken, Zahlungsbedingungen, Preislisten, Verkaufsteams, Lieferfunktion).
   Je Station ein Screenshot.

## 2. Aggregatlauf: 243 OK / 0 FEHL

| Werkzeug | Bereich | Ergebnis |
|---|---|---|
| `browser_verkauf_menue.py` | Menues und Untermenues | 42 OK / 0 FEHL |
| `browser_verkauf_formular_reiter.py` | Formulare und Reiter | 16 OK / 0 FEHL |
| `browser_verkauf_zahlungsbedingung.py` | Zahlungsbedingungen im Formular | 5 OK / 0 FEHL |
| `browser_verkauf_buttons_klicktest.py` | Buttons und Smart Buttons | 26 OK / 0 FEHL |
| `browser_verkauf_statuswechsel_klicktest.py` | Statuswechsel | 35 OK / 0 FEHL |
| `browser_verkauf_filter_suche.py` | Suche, Filter, Gruppierungen | 19 OK / 0 FEHL |
| `browser_verkauf_ansichten.py` | Liste/Kanban/Kalender/Pivot/Graph | 11 OK / 0 FEHL |
| `browser_verkauf_kalender.py` | Auftrags- und Aktivitaetenkalender | 16 OK / 0 FEHL |
| `browser_verkauf_bericht_kanaele.py` | Bericht „Verkaufsauftraege aller Kanaele“ | 18 OK / 0 FEHL |
| `browser_verkauf_druckberichte.py` | Druckberichte | 41 OK / 0 FEHL |
| `browser_verkauf_lieferung.py` | Lager-/Lieferfunktion | 14 OK / 0 FEHL |

```
Gesamt: 243 OK / 0 FEHL ueber 11 Werkzeuge
JavaScript-Fehler: 0, RPC-Fehler: 0
Bestand unveraendert (Testdaten bereinigt): ja
Auffaellig: keine
```

## 3. Durchgehender Klickpfad: 43 OK / 0 FEHL

| Station | Inhalt | Ergebnis |
|---|---|---|
| 1 | Auftragsliste geoeffnet | OK |
| 2 | Hauptmenues der Verkauf-App: Verkauf, Auftraege, Abzurechnen, Produkte, Berichtswesen, Konfiguration | 6 OK |
| 3 | Auftragsformular S00203: Reiter Auftragszeilen/Weitere Informationen, Felder Kunde, Verkaufskontakt, Vertriebsmitarbeiter, Zahlungsbedingungen, Preisliste, Rechnungs-/Lieferadresse | 9 OK |
| 4 | Lagerbereich des Formulars: Lagerhaus, Versandbedingungen, Lieferdatum | 3 OK |
| 5 | Suche nach Auftragsnummer, Filter-/Gruppierungsbereich | 3 OK |
| 6 | Listen-, Kanban-, Kalender-, Pivot- und Graphansicht laden | 5 OK |
| 7 | Auftragskalender zeigt Auftraege | OK |
| 8 | Bericht Verkauf (Aktion 416, Verkaufsanalyse) | OK |
| 9 | Bericht „Verkaufsauftraege aller Kanaele“, Filter „Aktuelles Verkaufsjahr“ aktiv | 2 OK |
| 10 | Drucken-Menue: Angebot/Auftrag, ITK-Angebot/Auftrag, PDF-Angebot, PRO-FORMA-Rechnung | 4 OK |
| 11 | Zahlungsbedingungen: „30 Tage netto“ und „14 Tage“ in der Liste | 2 OK |
| 12 | Preislisten geoeffnet | OK |
| 13 | Verkaufsteams/Vertriebskanaele geoeffnet | OK |
| 14 | Lieferfunktion: Smart Button „Lieferung“ im Testauftrag, Lieferbeleg WH/OUT/00021 geoeffnet | 2 OK |
| 15 | Testdaten bereinigt, Bestand unveraendert, keine Testprodukte zurueckgeblieben | 2 OK |

```
Ergebnis: 43 OK / 0 FEHL
JavaScript-Fehler: 0, RPC-Fehler: 0
Bestand: vorher 20 Auftraege / 13 Produkte / 0 Lagerbelege
         nachher 20 Auftraege / 13 Produkte / 0 Lagerbelege
```

Screenshots: `C:\Users\anna.maierhofer\Desktop\Odoo18-Abnahme-Session121\gesamtdurchgang\`
(01_Angebote_vm.png bis 15_Lieferung_vm.png).

Stichproben am Screenshot geprueft:
- `10_Bericht_Kanaele_vm.png` – Bericht „Verkaufsauftraege aller Kanaele“, Facette
  „Aktuelles Verkaufsjahr“ aktiv, Pivot mit Gesamt 863,80 und Auftragszeilen S00097 bis S00203.
- `15_Lieferung_vm.png` – Lieferbeleg WH/OUT/00021 aus dem Testauftrag (Referenz S00224),
  Lieferadresse „Test Firma“, Position „ZZ-Test Gesamtdurchgang Lagerartikel“, Status Bereit.

## 4. Anpassungen an den Abnahmewerkzeugen (keine fachliche Aenderung)

Bei der Gesamtabnahme fielen drei Erwartungen auf, die aus frueheren Teilen stammten und
nachgezogen wurden – es handelt sich **nicht** um Fehler in Odoo 18:

| Befund | Ursache | Korrektur |
|---|---|---|
| `browser_verkauf_menue.py` erwartete „Verkaufsauftraege aller Kanaele“ als *nicht* sichtbar | Bericht existiert seit Teil 4, Schritt 2 | Eintrag in die erwarteten Menuepunkte der Gruppe „Berichtswesen“ verschoben (42 OK) |
| `browser_verkauf_formular_reiter.py` suchte die Gruppe „Versand“ | Mit der Lageranbindung heisst die Gruppe in Odoo 18 „Lieferung“ | Erwartung auf „Lieferung“ umgestellt (16 OK) |
| `browser_verkauf_buttons_klicktest.py` / `..._statuswechsel_klicktest.py` liessen Lagerbelege liegen | Ein bestaetigter Auftrag erzeugt seit der Lageranbindung eine Lieferung; sie blieb nach dem Loeschen des Testauftrags zurueck | Beide Werkzeuge entfernen die Lagerbelege des Testauftrags vor dem Loeschen des Auftrags |

Zusaetzlich wurde `browser_verkauf_druckberichte.py` gegen Abbrueche beim PDF-Download
abgesichert (erneuter Versuch, Ausweichkopie aus dem Download-Zwischenspeicher) und der
Aggregatlauf startet jedes Werkzeug mit frischem Browserprofil.

Zwischenstand beim ersten Versuch: 5 liegengebliebene Lagerbelege und 1 Testauftrag
(WH/OUT/00007 bis 00011, Auftrag S00214) wurden mit `scripts/aufraeumen_verkauf_testdaten.py`
entfernt; seitdem ist der Bestand nach jedem Lauf unveraendert.

## 5. Regression Verkauf und Abonnements

`scripts/abschluss_verkauf_regression.py` – 11 Prueflaeufe lokal und VM:

```
Gesamt: 886 OK / 0 FEHL ueber 11 Prueflaeufe
Alle Prueflaeufe auf Referenzniveau, keine Abweichung.
```

Enthalten: Menue 41, Teil 2 Feldinventar 111, Teil 3.1 Reiter 64, Teil 3.3 Statuswechsel 53,
Teil 3.4 Filter/Gruppierungen/Suche 199, Teil 4.1 Ansichten 146, Kalender 33,
Teil 4.2 Bericht aller Kanaele 84, Teil 4.3 Druckberichte 69, Bestand Auftraege/Lager 67,
Bestand Abonnements 19.

## 6. Bewertung

Alle in Block 3 geforderten Bereiche wurden im echten Browser auf der Abnahmeumgebung geprueft:

- Menues und Untermenues: vollstaendig sichtbar, keine fehlenden Eintraege
- Angebote/Auftraege, Formulare und Reiter: vollstaendig, inklusive Lagerbereich
- Buttons und Smart Buttons, Statuswechsel: alle Klicks ohne Fehler
- Suche, Filter, Gruppierungen: vorhanden und wirksam
- Listen-, Kanban-, Kalender-, Pivot- und Graphansicht: laden mit Daten
- Auftragskalender: zeigt Auftraege
- Verkaufsberichte inkl. „Verkaufsauftraege aller Kanaele“: oeffnen, Filter „Aktuelles
  Verkaufsjahr“ aktiv, Kennzahlen plausibel
- Druckberichte: alle vier Menuepunkte im echten Browser erreichbar, PDF-Erzeugung erfolgreich
- Zahlungsbedingungen: „30 Tage netto“ vorhanden und in der Konfiguration sichtbar
- Lager-/Lieferfunktion: Smart Button, Lieferbeleg, Bezug Auftrag zu Lieferung funktioniert
- Relevante Stammdaten: Preislisten und Verkaufsteams/Vertriebskanaele vorhanden

Keine neuen echten Luecken, keine Fehler. Keine Datenmigration, Odoo 11 unveraendert.

Offen bleibt Block 4 (Abschlussmarkierung „Verkauf vollstaendig funktionsfaehig und
vollstaendig migrationsvorbereitet“).
