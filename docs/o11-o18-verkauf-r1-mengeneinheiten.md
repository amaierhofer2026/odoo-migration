# R1 - Mengeneinheiten: Zuordnung Odoo 11 -> Odoo 18 (vorbereitet und geprueft)

Stand: 29.09.2026, Session 121. Vorbereitung abgeschlossen und lokal sowie auf der VM geprueft.
Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) **ausschliesslich read-only** gelesen.
Geaendert wurde nur Odoo 18 (Mengeneinheiten und eine Dezimalgenauigkeit) - **keine
Datenmigration**, keine Auftraege, Produkte, Kunden oder bestehenden Odoo-18-Funktionen angetastet.

Werkzeuge:
`scripts/apply_verkauf_r1_mengeneinheiten.py` (Vorbereitung, idempotent, Trockenlauf mit `--trocken`),
`scripts/pruefe_verkauf_r1_mengeneinheiten.py` (Pruefung, nur lesend),
Rohdaten `docs/_verkauf_r1_mengeneinheiten_lokal.json` und `..._vm.json` (gitignoriert).

## 1. Ausgangslage (gemessen, read-only)

```
Odoo 11 verwendet in Auftragszeilen und Produkten 13 Mengeneinheiten (product.uom):
  Einheit(en)    2.334 Zeilen | 262 Produkte | Rundung 0,001 | Kategorie "ITK Einheit"
  ITK Einheit    1.622 Zeilen | 376 Produkte | Rundung 0,001 | Kategorie "ITK Einheit"
  GB                45 Zeilen |  11 Produkte | Rundung 0,01  | Kategorie "Volumen"
  13/15/16/19/22/23/29 Gemeinden  10 Zeilen (7 Namen, 2 doppelt) | 0 Produkte | Rundung 0,01
Dezimalgenauigkeit Odoo 11 "Product Unit of Measure" = 3 (0,001)
Dezimalgenauigkeit Odoo 18 (vorher)                  = 2 (0,01)  -> Ursache der Abweichung

Nachweis, dass die Abweichung fachlich relevant ist:
  Odoo 11 fuehrt 2 Auftragszeilen (ids 3944 und 4072) mit der Menge 0,125 in "Einheit(en)".
  Mit Rundung 0,01 waeren diese Mengen nicht unveraendert darstellbar - sie wuerden beim
  Uebernehmen gerundet (Wertaenderung). Die Anpassung ist daher kein Kosmetikthema.
```

## 2. Zuordnung (Mapping ueber fachlich eindeutige Werte, nicht ueber IDs)

| Odoo-11-Einheit | Rundung O11 | Zeilen | Odoo-18-Ziel (id lokal / VM) | Massnahme |
|---|---|---|---|---|
| Einheit(en) | 0,001 | 2.334 | Einheit(en) (1 / 1) | vorhanden, Rundung auf 0,001 gesetzt |
| ITK Einheit | 0,001 | 1.622 | ITK Einheit (29 / 29) | vorhanden, Rundung auf 0,001 gesetzt |
| GB | 0,01 | 45 | GB (31 / 30) | neu angelegt, eigene Kategorie „Datenmenge" |
| 13 Gemeinden (2 Datensaetze) | 0,01 | 2 | 13 Gemeinden (32 / 31) | neu angelegt |
| 15 Gemeinden (2 Datensaetze) | 0,01 | 2 | 15 Gemeinden (33 / 32) | neu angelegt |
| 16 Gemeinden | 0,01 | 1 | 16 Gemeinden (34 / 33) | neu angelegt |
| 19 Gemeinden (2 Datensaetze) | 0,01 | 2 | 19 Gemeinden (35 / 34) | neu angelegt |
| 22 Gemeinden | 0,01 | 1 | 22 Gemeinden (36 / 35) | neu angelegt |
| 23 Gemeinden | 0,01 | 1 | 23 Gemeinden (37 / 36) | neu angelegt |
| 29 Gemeinden | 0,01 | 1 | 29 Gemeinden (38 / 37) | neu angelegt |

```
Deckung: 13 von 13 verwendeten Odoo-11-Einheiten haben eine Odoo-18-Einheit mit gleichem Namen.
Die beiden Odoo-11-Doppelnamen ("13 Gemeinden", "15 Gemeinden", "19 Gemeinden" je zweimal, in
Odoo 11 in verschiedenen Kategorien) bilden auf jeweils eine Odoo-18-Einheit ab - die
Doppelungen unterscheiden sich in Odoo 11 nur durch die Kategorie, nicht fachlich.
```

## 3. Umgesetzte Aenderungen in Odoo 18 (lokal und VM identisch)

```
1. Dezimalgenauigkeit "Product Unit of Measure": 2 -> 3   (wie Odoo 11)
2. Rundung "Einheit(en)": 0,01 -> 0,001                   (wie Odoo 11)
3. Rundung "ITK Einheit": 0,01 -> 0,001                   (wie Odoo 11)
4. GB neu angelegt: Kategorie "Datenmenge" (neu), Typ reference, Faktor 1.0, Rundung 0,01
5. Sieben "<Zahl> Gemeinden"-Einheiten neu angelegt: Typ bigger, Faktor 1.0, Rundung 0,01
   Kategorien: "Einheit" (6 Einheiten) und "Arbeitszeit" (1 Einheit: 23 Gemeinden)
   Hinweis: In der Zielkategorie fuehrt bereits eine Einheit die Referenz (z. B. "Einheit(en)"),
   deshalb werden sie wie das Odoo-18-eigene "ITK Einheit" als "bigger" mit Faktor 1.0 gefuehrt.
Ergebnis: 29 -> 37 Einheiten in Odoo 18; alle 29 vorhandenen Einheiten unveraendert erhalten
(das Skript prueft das nach jedem Lauf und meldet Abweichungen).
Wiederholte Laeufe sind wirkungslos (idempotent): zweiter Lauf ohne jede Aenderung.
```

### Bewertung der Rundungsabweichung

```
Warum 0,001 und nicht 0,01:
  Odoo 11 fuehrt die beiden Haupteinheiten (3.956 von 4.011 Zeilen = 98,6 %) mit Rundung 0,001
  und die Dezimalgenauigkeit 3. Wird Odoo 18 bei 0,01 belassen, aendern sich Mengen wie 0,125
  beim Uebernehmen. Die Anpassung stellt die Werteerhaltung sicher.
Risiko der Anpassung: gering und begrenzt
  - Eine feinere Rundung erlaubt zusaetzliche Nachkommastellen, sie verbietet nichts und
    aendert keine gespeicherten Werte.
  - Die Dezimalgenauigkeit wirkt auf Mengenanzeigen (Auftrag, Lager, Rechnung). Bestehende
    Odoo-18-Daten werden nicht umgerechnet, nur die zulaessige Genauigkeit steigt.
  - Es wurde keine Standardeinheit geloescht oder umbenannt; die uebrigen Einheiten behalten
    ihre Rundung 0,01 (genau wie in Odoo 11, wo ebenfalls gemischte Rundungen gefuehrt werden).
  - Rueckgaengig machen: Dezimalgenauigkeit auf 2 und Rundung der beiden Einheiten auf 0,01
    zuruecksetzen - das Skript dokumentiert die Aenderungen einzeln.
Alternative (nicht umgesetzt): Odoo 18 bei 0,01 belassen und die 2 Mengen 0,125 bewusst
  gerundet uebernehmen - dann ist eine Wertaenderung dokumentiert hinzunehmen.
```

## 4. Pruefungen (nur lesend)

```
scripts/pruefe_verkauf_r1_mengeneinheiten.py --instanzen lokal,vm
  Ergebnis: 64 OK / 0 FEHL
  je Instanz 32 Pruefungen:
    - alle 13 verwendeten Odoo-11-Einheiten haben eine Odoo-18-Einheit gleichen Namens
    - keine Odoo-18-Rundung ist groeber als die Odoo-11-Rundung der Einheit
    - "Einheit(en)" und "ITK Einheit" fuehren Rundung 0,001
    - Dezimalgenauigkeit "Product Unit of Measure" = 3
    - Werteerhaltung: alle 4.011 Odoo-11-Auftragsmengen sind mit der Odoo-18-Rundung
      unveraendert darstellbar (0 nicht darstellbare Mengen; 2 Mengen mit 0,125)
    - alle 29 vorher vorhandenen Odoo-18-Einheiten weiterhin vorhanden und aktiv
    - Bestand unveraendert: 13 Produkte, 28 Auftragszeilen (lokal) bzw. 29 (VM)

scripts/abschluss_verkauf_regression.py
  Ergebnis: 886 OK / 0 FEHL ueber 11 Prueflaeufe (lokal und VM)
  -> keine Odoo-18-Funktion beschaedigt: Menues, Formulare, Reiter, Statuswechsel, Filter,
     Ansichten, Kalender, Berichte, Druckberichte, Lageranbindung, Abonnements unveraendert.

scripts/browser_verkauf_gesamtdurchgang.py --instanz vm   (echter Browser auf der Abnahmeumgebung)
  Ergebnis: 43 OK / 0 FEHL, 0 JavaScript-Fehler, 0 RPC-Fehler
  -> Auftragsformular mit Auftragszeilen, Reiter, Ansichten, Druckberichte und Lieferfunktion
     nach der Genauigkeits- und Rundungsaenderung fehlerfrei; Testdaten bereinigt
     (Bestand vorher = nachher: 20 Auftraege, 13 Produkte, 0 Lagerbelege).

Keine Auftraege migriert, keine Produkte oder Kunden angelegt, keine bestehende Einheit entfernt.
```

## 5. Fachliche Klaerung (29.09.2026, read-only in Odoo 11)

### 5.1 Einheit „GB" - fachlich Gigabyte (Datenmenge)

```
Odoo 11, Datensatz product.uom id 8:
  name "GB", uom_type reference, factor 1.0, rounding 0,01, Kategorie "Volumen"
  Falsch eingeordnet: In der Kategorie "Volumen" fuehrt Odoo 11 ZWEI Referenzeinheiten
  ("GB" und "Liter", beide factor 1.0) - Odoo 11 laesst das zu, Odoo 18 nicht. "GB" gehoerte
  dort nie hin. Wuerde man es in Odoo 18 in "Volumen" legen, waere 1 GB = 1 L umrechenbar - falsch.

Fachliche Bedeutung - belegt durch die Verwendung:
  Alle 11 Produkte mit dieser Einheit stammen aus der Produktkategorie "GemeindeCloud",
  Produktart "Dienstleistung (onlineservice)":
    GemeindeCloud 5 GB / 10 GB / 15 GB / 20 GB / 50 GB / 100 GB / 150 GB / 250 GB / 500 GB /
      1.000 GB  Ersteinrichtung   (Listenpreis 120 bis 600 EUR je Paket)
    GemeindeCloud AD-Anbindung einmalig   (dort als Einheit "GB" mitgefuehrt)
  Alle 45 Auftragszeilen (44 im Zustand Verkaufsauftrag, 1 storniert) haben Menge 1,0 (bzw. 0,0
  bei leeren Positionen) und den Paketpreis als Einzelpreis, z. B.:
    A-2600298  GemeindeCloud 100 GB Ersteinrichtung      1,0 x 555,00 = 555,00 EUR
    A-2500205  GemeindeCloud 5 GB Ersteinrichtung        1,0 x 151,00 = 151,00 EUR
    A-2500097  GemeindeCloud AD-Anbindung einmalig       1,0 x   0,00 =   0,00 EUR
    A-2000270  GemeindeCloud 50 GB Ersteinrichtung       0,0 x 360,00 =   0,00 EUR (leere Position)
    A-2000230  GemeindeCloud AD-Anbindung einmalig       1,0 x 490,00 (Auftrag storniert)
  Zeitraum der Auftraege: A-2000xxx (2020) bis A-2600xxx (2026).
  Weitere Datenmengen-Einheiten (MB, TB, Byte) fuehrt Odoo 11 nicht.

Ergebnis Odoo 18 (bereits hergestellt und geprueft, lokal und VM identisch):
  Kategorie "Datenmenge" (id 8) mit genau einer Einheit: GB, Typ reference, Faktor 1.0,
  Rundung 0,01 - als eigene Kategorie getrennt von "Volumen".
  Pruefung: "Volumen" fuehrt weiterhin L als Referenz und enthaelt GB NICHT; eine Umrechnung
  GB <-> Liter ist damit ausgeschlossen.
  MB/TB wurden bewusst nicht angelegt - sie werden in Odoo 11 nicht verwendet, und die Frage
  1000 oder 1024 (Dezimal/Binaer) waere eine eigene fachliche Entscheidung.
```

### 5.2 Die zehn Zeilen mit „<Zahl> Gemeinden" - Ursache geklaert

```
Alle zehn Einheiten wurden am 02.01.2020 zwischen 14:57 und 15:29 von der Benutzerin
"Waiss Martina" angelegt - in derselben Sitzung wie die zugehoerigen Auftraege (die Auftraege
A-2000001 bis A-2000011 entstanden am 02.01.2020). Jede Einheit entstand Sekunden bis wenige
Minuten vor der zugehoerigen Auftragszeile, die Einheit traegt jeweils die Gemeindezahl des Kunden.

| Einheit | angelegt | Auftrag | Kunde | Produkt | Menge | Preis |
|---|---|---|---|---|---|---|
| 13 Gemeinden | 02.01.2020 15:11:04 | A-2000003 | (FALSCH) Abfallverband Schwechat | Ersteinrichtungskosten amtsweg.gv.at - Region | 1,0 | 1.204,26 |
| 13 Gemeinden | 02.01.2020 15:20:05 | A-2000006 | GVA Moedling | Ersteinrichtungskosten amtsweg.gv.at - Region | 1,0 | 1.204,26 |
| 15 Gemeinden | 02.01.2020 15:07:32 | A-2000002 | GVA Waidhofen/Thaya | Ersteinrichtungskosten amtsweg.gv.at - Region | 1,0 | 1.280,16 |
| 15 Gemeinden | 02.01.2020 15:29:34 | A-2000011 | GDA Amstetten | Ersteinrichtungskosten amtsweg.gv.at - Region | 1,0 | 1.280,16 |
| 16 Gemeinden | 02.01.2020 15:16:22 | A-2000005 | GVU Scheibbs | Ersteinrichtungskosten amtsweg.gv.at - Region | 1,0 | 1.318,11 |
| 19 Gemeinden | 02.01.2020 15:25:26 | A-2000008 | GV Horn | Ersteinrichtungskosten amtsweg.gv.at - Region | 1,0 | 1.431,96 |
| 19 Gemeinden | 02.01.2020 15:27:02 | A-2000009 | GABL | Ersteinrichtungskosten amtsweg.gv.at - Region | 1,0 | 1.431,96 |
| 22 Gemeinden | 02.01.2020 15:23:26 | A-2000007 | GV Krems | Ersteinrichtungskosten amtsweg.gv.at - Region | 1,0 | 1.545,81 |
| 23 Gemeinden | 02.01.2020 15:00:17 | A-2000001 | GV Zwettl | Ersteinrichtungskosten amtsweg.gv.at - Region | 1,0 | 1.583,76 |
| 29 Gemeinden | 02.01.2020 15:28:26 | A-2000010 | GVA Baden | Ersteinrichtungskosten amtsweg.gv.at - Region | 1,0 | 1.811,34 |

```
Erkenntnis:
  Das Produkt ist immer dasselbe: "Ersteinrichtungskosten amtsweg.gv.at - Region..." (Dienstleistung,
  Produktkategorie "Dienstleistungspauschale"), dessen eigene Einheit "Einheit(en)" ist. Die
  Auftragszeile weicht davon ab und traegt die Sondereinheit "<Zahl> Gemeinden"; der Preis
  entspricht der Ersteinrichtungspauschale gestaffelt nach Anzahl der Gemeinden des Verbands.
  Damit ist die Ursache eindeutig: Bei der Ersteinrichtung im Januar 2020 hat die Anwenderin je
  Kunde eine eigene Einheit angelegt, deren Name die Gemeindezahl beschreibt - ein Notbehelf, um
  den gestaffelten Pauschalpreis sichtbar zu machen. Fachliche Einheitenfunktion hat das nicht
  (Faktor 1.0, Referenztyp, kein Produkt verwendet sie; Zeilenmenge immer 1,0).
  Kein Vorgang in Odoo 11 hat diese Einheiten spaeter weiterverwendet (alle zehn Zeilen stammen
  vom 02.01.2020).

Umsetzung nach Entscheidung: unveraendert belassen. Die sieben Einheiten bleiben in Odoo 18
bestehen, die zehn Zeilen werden nicht auf "Einheit(en)" zusammengefuehrt.
```

## 6. Entscheidungen von Anna (29.09.2026) und Status

```
1. "GB" bleibt in Odoo 18 als eigene Einheit in der Kategorie "Datenmenge".
   Keine Verbindung und keine Umrechnung zu Liter/Volumen (eigene Kategorie - dadurch technisch
   ausgeschlossen).
2. Die sieben historischen Einheiten 13/15/16/19/22/23/29 Gemeinden bleiben in Odoo 18 bestehen.
3. Bei der spaeteren Datenmigration werden sie 1:1 nach dem Namen zugeordnet - NICHT auf
   "Einheit(en)" zusammengefuehrt.
4. Rundung "Einheit(en)" und "ITK Einheit" bleibt 0,001; Dezimalgenauigkeit
   "Product Unit of Measure" bleibt 3.

Regel fuer die Datenmigration (festgehalten):
   sale.order.line.product_uom wird ueber den NAMEN der Einheit zugeordnet
   (product.uom.name -> uom.uom.name), niemals ueber die ID. Die Odoo-11-Doppelnamen
   (13/15/19 Gemeinden je zweimal) bilden auf die gleichnamige Odoo-18-Einheit ab.

STATUS: R1 ABGESCHLOSSEN (29.09.2026) - dokumentiert, umgesetzt, lokal und VM geprueft:
   Zuordnung 13 von 13 verwendeten Odoo-11-Einheiten, Rundung angeglichen, fehlende Einheiten
   angelegt, Zuordnungsregel festgehalten, Pruefung 64 OK / 0 FEHL, Regression 886 OK / 0 FEHL,
   echter Browser auf der VM 43 OK / 0 FEHL mit 0 JavaScript- und 0 RPC-Fehlern.
Der Bereich Verkauf bleibt bis zur Vorbereitung der Risiken R2 bis R8 weiterhin NICHT endgueltig
abgeschlossen.
```

## 7. Naechster Schritt

R2 (`price_reduce`) wird separat bearbeitet. R3-R8 bleiben offen.
