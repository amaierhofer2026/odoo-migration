# Testdatenanalyse Verkauf/Abonnements (Odoo 18)

Stand 12.11.2026. Read-only Analyse; es wurde **nichts geloescht**.
Grundlage: Odoo 18 lokal, gleiche Struktur auf der VM.

Klassifikationsmerkmal: Ein Datensatz gilt als Odoo-11-Bestand, wenn er ein `itk_o11_id`
traegt. Alles ohne diese Kennung ist Odoo-18-Eigenbestand (Test, Demo, Installation).

## 1 Testauftraege (12)

| ID | Nummer | Status | Betrag | Zeilen | Rechnungen | In Odoo 11 vorhanden |
|---|---|---|---|---|---|---|
| 202 | S00200 | sale | 28,80 | 1 | 0 | nein |
| 200 | S00198 | sale | 28,80 | 1 | 0 | nein |
| 190 | S00190 | sale | 192,00 | 5 | 0 | nein |
| 189 | S00189 | sent | 72,00 | 4 | 0 | nein |
| 188 | S00188 | sent | 120,00 | 1 | 0 | nein |
| 180 | S00180 | sale | 49,00 | 1 | 0 | nein |
| 179 | S00179 | sale | 94,80 | 1 | 0 | nein |
| 176 | S00176 | sale | 58,80 | 1 | 0 | nein |
| 173 | S00173 | sale | 68,40 | 1 | 0 | nein |
| 40 | S00040 | sale | 60,00 | 1 | 0 | nein |
| 7 | S00007 | sale | 60,00 | 1 | 0 | nein |
| **198** | **A-1900011** | sale | 102,00 | 2 | 0 | **ja (1 Treffer)** |

Alle 12 wurden zwischen 01.07.2026 und 22.09.2026 angelegt, also in der Odoo-18-Testphase
und lange vor der Migration am 12.11.2026. Ihre Kunden und Produkte tragen kein
`itk_o11_id`.

**Sonderfall ID 198:** Der Auftrag heisst `A-1900011` - und dieser Auftrag existiert in
Odoo 11. In Odoo 18 gibt es ihn **zweimal**:

| ID | itk_o11_id | Status | Betrag | Angelegt |
|---|---|---|---|---|
| 247 | 964 | sale | 102,00 | 12.11.2026 (migriert) |
| 198 | 0 | sale | 102,00 | 24.07.2026 (Testkopie) |

ID 247 ist der echte, migrierte Auftrag. ID 198 ist eine **inhaltlich identische
Testkopie** aus der Testphase. Er ist nicht der migrierte Datensatz und darf nicht als
echter Bestand gelten.

## 2 Testprodukte (25)

Alle angelegt zwischen 18.06.2026 und 30.10.2026, keines mit `itk_o11_id`:

`Abo_Amtssignatur Test`, `Abo Cloud Produkt`, `Amtsweg.gv.at Formularsammlung Österreich
Pre…`, `Amtsweg.gv.at Formularsammlung Österreich Soc…`, `Cloud_Service`,
`Event Registration`, `Premium Zugang`, `Produkt A`, `Produkt B`, `Produkt C`,
`Service on Timesheets`, `T-Abo M`, `T-Abo-M`, `T-Abo-M2`, `T-A-M`,
`Test-Abo monatlich`, `TEST-Abo Monatlich` (3×), `TEST Abo Produkt Monatlich`,
`Test test`, `T-FIN`, `TF-M3`, `TX`, `TX2`.

Die Namen mit „Test", „T-Abo", „TX", „Produkt A/B/C" sind eindeutig Testanlagen.
`Event Registration` und `Service on Timesheets` stammen aus der Modulinstallation
(Oktober 2026). Die beiden `Amtsweg.gv.at…`-Eintraege sind manuelle Kopien aus der
Testphase (24.07.2026, ohne Odoo-11-Bezug).

## 3 Abhaengigkeiten (der eigentliche Befund)

| Abhaengigkeit | Anzahl |
|---|---|
| Rechnungen, die Testprodukte verwenden | **32** |
| davon gebucht (`posted`) | **7** (RE/2020/0001 … RE/2026/0002, Jahresreihen 2020–2026, 105,38–194,40 €) |
| davon Entwurf (`draft`) | 25 (Abo-Testrechnungen und Journalbuchungen, 22.09.–10.11.2026) |
| Auftragszeilen mit Testprodukten | 12 Auftraege (alle oben) |
| Abozeilen mit Testprodukten | 0 |
| Kunden/Partner ohne Odoo-11-Bezug an diesen Rechnungen | **alle** |

**Entscheidend:** Kein einziger Datensatz der Testkette traegt ein `itk_o11_id`.
Es ist also kein migrierter Bestand betroffen - weder Kunde, noch Produkt, noch Auftrag,
noch Rechnung.

## 4 Bewertung und Empfehlung

Die Kette ist inhaltlich eindeutig Testbestand: 12 Auftraege, 25 Produkte, 32 Rechnungen,
alle ohne Odoo-11-Bezug, alle aus der Testphase Juni–November 2026.

**Trotzdem wurde nicht geloescht**, weil zwei Punkte eine Entscheidung brauchen:

1. **7 gebuchte Rechnungen** (`posted`) sind buchhalterisch wirksam. Sie zu entfernen
   bedeutet Storno + Loeschen in einem abgenommenen Buchhaltungsbereich - das ist kein
   Testdaten-Aufraeumen mehr, sondern ein Eingriff in die Abrechnung.
2. Solange diese 7 Rechnungen bestehen, koennen die davon verwendeten Produkte nicht
   geloescht werden (Referenzschutz). Eine Teilbereinigung wuerde also eine halbe Kette
   hinterlassen.

**Vorschlag (sicher, in dieser Reihenfolge):**

1. 25 Entwurfsrechnungen und Journalbuchungen loeschen (unstrittig, keine Buchungswirkung).
2. 12 Testauftraege stornieren und loeschen (keine Rechnungen daran).
3. 7 gebuchte Testrechnungen separat behandeln: Storno und Loeschen nur mit
   ausdruecklicher Freigabe fuer den Buchhaltungsbereich.
4. Danach die 25 Testprodukte loeschen.

Bis zu dieser Entscheidung bleibt der Testbestand dokumentiert stehen.
