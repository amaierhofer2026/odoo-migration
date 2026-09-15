# Migrationsregel: Organisation = Unternehmen, Ansprechpartner = Person

**Verbindlich ab 15.09.2026 (Sessions 98/99).** Gilt für den späteren Datenimport aus Odoo 11 und für alle
Test-/Prüfdaten in Odoo 18.

## 1. Der Befund

In der Ansicht von Kontakt 79 (`[20201] Magistrat der Stadt Villach`) auf der VM fehlten **GKZ**,
**Multiplication Factor/Thsd**, **Organisationsbezeichnung**, **Status** und der Tab **Gemeinde-Information**.
Nach dem Umschalten des Datensatzes auf „Unternehmen" war alles sichtbar.

**Ursache:** Der Datensatz war als **Person** angelegt (`is_company = False`, `company_type = 'person'`),
obwohl er eine Gemeinde vertritt. Die firmenbezogenen Kenndaten sind in Odoo 18 **und** in Odoo 11 nur bei
Unternehmen sichtbar (`invisible: is_company = False` bei `ref`, `multi_factor`, `community_salutation`,
`status_of_partner_id`; der Tab `community_info` ebenso). Es lag **kein** View-Fehler vor — die gerenderten
Formular-Arches von lokal und VM sind byteidentisch (36.572 Zeichen).

**Zusatzbefund (unabhängig davon, behoben in `itk_base_setup` 18.0.1.0.8):** `Ist ein Lieferant` / `Ist ein Kunde`
hatten bei uns fälschlich eine `is_company`-Bedingung. Odoo 11 hat dort **keine** Bedingung
(`<field name="supplier" modifiers="{}"/>`) — die beiden Felder sind jetzt bei Firmen und Personen sichtbar.

**Betroffene Testdatensätze (nur festgestellt, nicht geändert):** In Odoo 18 existieren mehrere als **Person**
angelegte Datensätze mit Organisationsnamen (Beispielgruppe `MIG-TEST-0xx`, u. a. 76–79). An der aktuellen
Testdatenstruktur wurde ausdrücklich **nichts** geändert.

## 2. Verbindliche Regel (Anna, 15.09.2026)

1. **Gemeinden, Verbände, Firmen und sonstige Organisationen** werden in Odoo 18 als **Unternehmen** angelegt
   (`is_company = True`, `company_type = 'company'`).
2. **Natürliche Ansprechpartner** werden als **Person** angelegt (`is_company = False`, `company_type = 'person'`).
3. **Die Zuordnung darf bei der Migration nicht pauschal erfolgen.** Jede Zuordnung wird geprüft; unklare Fälle
   werden als Liste vorgelegt und einzeln entschieden.

## 3. Warum das fachlich entscheidend ist

| Auswirkung | Unternehmen | Person |
|---|---|---|
| Kenndaten | GKZ, Multiplication Factor/Thsd, zu Handen, Organisationsbezeichnung, Status sichtbar | nicht sichtbar (firmenbezogen) |
| Tabs | „Gemeinde-Information" sichtbar | nicht sichtbar |
| Steuer-/Zahlungsfelder | vollständig | reduziert |
| Ansprechpartner-Logik | Kind-Datensätze über `parent_id` | über `parent_id` an die Organisation gehängt |
| Filter/Listen | Kunde/Lieferant-Kennzahlen, GKZ-Suche | Personenlisten |

Falsche Typisierung führt zu fehlenden Feldern, falschen Filtern und falscher Kunden-/Lieferantenlogik — und
sie fällt in der Abnahme sofort auf (genau dieser Befund).

## 4. Vorgehen beim späteren Import (Vorschlag, noch nicht ausgeführt)

- **`is_company` aus Odoo 11 übernehmen**, nicht neu erfinden: Odoo 11 führt das Feld für jeden Datensatz mit.
- **Gegenproben vor dem Import** (read-only, Liste zur Freigabe):
  - Organisation-Indizien: gefüllte `ref`/Gemeindekennzahl, Namen mit Rechtsform- oder Verwaltungsbegriffen
    (Gemeinde, Marktgemeinde, Stadt, Magistrat, Bezirkshauptmannschaft, Verband, GmbH, AG, KG, Verein, Schule, Pfarre).
  - Person-Indizien: `firstname`/`lastname` gefüllt, Anrede/Titel gesetzt, Kind von einer Organisation.
- **Widersprüche als Klärliste** ausgeben (z. B. „Name enthält Gemeinde, `is_company` ist aber False") und
  **einzeln** entscheiden lassen — kein automatischer Massen-Umschlag.
- Nach dem Import prüfen: Anzahl Unternehmen/Personen vorher (Odoo 11) = nachher (Odoo 18) und Stichproben
  in der Ansicht (Kenndaten sichtbar bei Unternehmen, ausgeblendet bei Personen).

## 5. Prüfhinweis für die Abnahme

Beim Testen von Kontaktansichten immer den **Datensatztyp** mitprüfen (`is_company`, `company_type`).
Ein „fehlendes Feld" kann eine Typisierungsfrage sein und kein Strukturfehler. Kurzprüfung per RPC:
`res.partner.read([<id>], ['name','is_company','company_type'])`.
