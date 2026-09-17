# Strukturvergleich Odoo 11 Prod ↔ Odoo 18: Kontakte → Kontaktformular → Gemeinde-Information

Stand: 15.09.2026 (Session 109)
Quellen: Odoo 11 Prod `portal.it-kommunal.at` (DB `ITK_V1_a`, nur gelesen) und Odoo 18 (lokal + VM `k001959vsx.ipax.at`, DB `odoo18_test`)

Auftrag von Anna: Odoo 11 Prod read-only gegen Odoo 18 vergleichen – Felder, Labels, Typen, Relationen, Pflichtfelder,
Auswahlwerte, Ansichten und Funktionen. Eindeutige strukturelle Unterschiede direkt migrationsgerecht beheben,
moderne Odoo-18-Lösungen beibehalten, keine Produktivdaten migrieren.

## 1. Ergebnis vorab

Der Reiter **Gemeinde-Information** enthält in beiden Systemen **genau dieselben fünf Felder** (`population`,
`community_magnitude`, `population_update`, `status_of_community`, `member_of_city_alliance`), in derselben
Gruppierung ("Einwohnerzahl" / "Andere") und mit derselben Sichtbarkeitsregel (nur für **Unternehmen**:
`invisible = not is_company`). Typen, Relationen und Pflichtfeld-Eigenschaften sind identisch, alle Felder sind
**nicht** Pflichtfelder.

Zwei befunde wurden direkt behoben bzw. dokumentiert:

1. **Behoben:** Die Feldbeschriftungen im **Modell** standen in Odoo 18 teilweise auf Englisch bzw. wichen ab
   (`Magnitude`, `Status of Community`, `Member of City Alliance`, `Community Magnitude`,
   `Einwohnerzahl aktualisiert am`, `Salutation of Community`). Im Formular waren bereits deutsche Beschriftungen
   gesetzt (View-Strings in `itk_crm/views/res_partner.xml`), im Modell aber nicht – und damit auch nicht in Suche,
   Filter, Export und Auswahllisten. Die Modellbeschriftungen wurden auf die Odoo-11-Wortlaute gesetzt
   (`itk_crm` 18.0.1.5.1).
2. **Dokumentiert (Vorgabe für die Datenmigration):** Die Stammdaten "Organisationstyp" sind in Odoo 18 unvollständig
   (nur "Marktgemeinde"), in Odoo 11 sieben Werte (siehe Abschnitt 6).

## 2. Wie die Gemeinde-Felder in Odoo 11 Prod technisch gespeichert sind

Alle Gemeinde-Angaben sind **normale Felder des Moduls `itk_crm` auf `res.partner`** – keine `x_`-Custom-Felder,
kein eigenes Gemeinde-Modell, keine Property-/ir.property-Ablage. Das Modul `itk_crm` ist in Odoo 11 und Odoo 18
identisch aufgebaut (Quelle: `addons/itk_crm/models/models.py`).

| Feld | Speicherung | Besonderheit |
|---|---|---|
| `population` | `fields.Integer`, gespeichert | Einwohnerzahl, Ausgangswert |
| `community_magnitude` | `fields.Char`, **compute, nicht gespeichert** | wird über `_get_community_magnitude()` aus `population` berechnet |
| `community_magnitude_id` | `fields.Many2one('itk_crm.communitymagnitude')`, **compute + gespeichert** | dieselbe Berechnung, Klassen mit Unter-/Obergrenze (`lower_limit`/`upper_limit`) |
| `population_update` | `fields.Date`, gespeichert | Datum der Einwohnerzahl |
| `status_of_community` | `fields.Many2one('itk_crm.statusofcommunity')`, gespeichert | Organisationstyp, Stammdatentabelle |
| `member_of_city_alliance` | `fields.Boolean`, gespeichert | Städtebund-Mitglied |
| `community_salutation` | `fields.Char`, gespeichert | "Organisationsbezeichnung" (im Kenndatenblock, nicht im Reiter) |

**Wichtig für die Migration:** `community_magnitude` und `community_magnitude_id` sind **berechnet** und müssen
**nicht** migriert werden – sie ergeben sich in Odoo 18 automatisch aus `population`
(`_compute_communitymagnitude`, auch als `on_change` bei Änderung der Einwohnerzahl). Verifiziert in Odoo 18:
Einwohnerzahl 1.909 → Größenklasse "1.501 bis 2.000".

## 3. Feld-Mapping

| Odoo-11-Feld | Bedeutung | Odoo-18-Zielfeld | Feldtyp | Zuordnung |
|---|---|---|---|---|
| `population` | Einwohnerzahl | `population` | integer | **1:1** (2.675 Werte, davon 2.280 Unternehmen) |
| `community_magnitude` | Größenklasse | `community_magnitude` | char (compute) | **nicht migrieren** – berechnet aus `population` |
| `community_magnitude_id` | Größenklasse (Stammdatenbezug) | `community_magnitude_id` | many2one `itk_crm.communitymagnitude` | **nicht migrieren** – berechnet aus `population` |
| `population_update` | Stand vom | `population_update` | date | **1:1** (2.093 Werte, alle Unternehmen) |
| `status_of_community` | Organisationstyp | `status_of_community` | many2one `itk_crm.statusofcommunity` | **1:1**, aber **Stammdaten-Mapping erforderlich** (Abschnitt 6) |
| `member_of_city_alliance` | Städtebund-Mitglied | `member_of_city_alliance` | boolean | **1:1** (277 Werte, alle Unternehmen) |
| `community_salutation` | Organisationsbezeichnung | `community_salutation` | char | **1:1** (im Kenndatenblock sichtbar) |

**Entfällt:** nichts. **Neu ohne Odoo-11-Quelle:** nichts. Der Reiter ist vollständig abbildbar.

## 4. Labels, Typen, Pflichtfelder, Ansicht

| Prüfung | Odoo 11 | Odoo 18 |
|---|---|---|
| Feldbestand im Reiter | 5 Felder | 5 Felder (identisch) |
| Gruppierung | "Einwohnerzahl", "Andere" | identisch |
| Reiter-Beschriftung | "Gemeinde-Information" | "Gemeinde-Information" |
| Sichtbarkeit | nur Unternehmen (`is_company`) | identisch (`invisible="not is_company"`) |
| Pflichtfelder | keine | keine |
| Typen/Relationen | integer, char, date, many2one, boolean | identisch |
| Auswahlwerte | `status_of_community`: 7 Stammdatensätze; Größenklassen: 16 Sätze in Prod | Organisationstyp: 1 Satz; Größenklassen: 14 Sätze (siehe Abschnitt 6) |
| Funktion | Größenklasse wird bei Änderung der Einwohnerzahl neu berechnet (`on_change`) | identisch (`on_change="1"` + `compute`) |
| Modellbeschriftungen | deutsch (Größenklasse, Organisationstyp, Städtebund-Mitglied, Stand vom) | **waren englisch → in Session 109 auf die Odoo-11-Wortlaute gesetzt** |

## 5. Datenlage in Odoo 11 Prod (read-only)

| Feld | Kontakte mit Wert | davon Unternehmen |
|---|---|---|
| `population` | 2.675 | 2.280 |
| `community_magnitude` (berechnet) | 5.843 (16 verschiedene Werte) | 2.380 |
| `population_update` | 2.093 | 2.093 |
| `status_of_community` | 2.093 | 2.093 |
| `member_of_city_alliance` | 277 | 277 |

Häufigste Größenklassen in Odoo 11: "bis 500" (1.009), "1.001 bis 1.500" (381), "1.501 bis 2.000" (344),
"3.001 bis 5.000" (319), "501 bis 1000" (295).

## 6. Umgesetzte Änderung (Session 109): Modellbeschriftungen auf die Odoo-11-Wortlaute

Datei `addons/itk_crm/models/models.py`, Modulversion `itk_crm` **18.0.1.5.1**:

| Feld | vorher (Odoo 18) | jetzt (wie Odoo 11) |
|---|---|---|
| `status_of_community` | Status of Community | **Organisationstyp** |
| `community_magnitude` | Magnitude | **Größenklasse** |
| `community_magnitude_id` | Community Magnitude | **Größenklasse** |
| `population_update` | Einwohnerzahl aktualisiert am | **Stand vom** |
| `member_of_city_alliance` | Member of City Alliance | **Städtebund-Mitglied** |
| `community_salutation` | Salutation of Community | **Organisationsbezeichnung** |

`population` war bereits korrekt ("Einwohnerzahl"). Die Beschriftungen wirken damit auch in Suche, Filter, Export und
Auswahllisten – nicht nur im Formular (dort waren sie über die View-Strings schon deutsch). Feldnamen, Typen,
Berechnungen und Daten bleiben unverändert.

Die deutschen Übersetzungseinträge wurden in beiden Datenbanken geprüft; es blieben keine alten Werte stehen.
Nicht geändert wurden Beschriftungen außerhalb dieses Reiters (u. a. `asset_partner` "Asset Partner",
`official_email` "Official Email", `firstname` "First name"), die in ihren eigenen Bereichen zu behandeln sind.

## 7. Organisationstypen als Ziel-Stammdaten vorbereitet (Session 110)

Auf Anweisung von Anna wurden die in Odoo 11 Prod **tatsächlich verwendeten** Organisationstypen in Odoo 18 als
Stammdaten angelegt — **ohne** Kontakte umzustellen und **ohne** Odoo-11-Zuordnungen zu übernehmen.

### 7.1 Read-only verifizierter Odoo-11-Bestand

| Odoo-11-ID | Code | Name | Kontakte in Odoo 11 | Ziel in Odoo 18 |
|---|---|---|---|---|
| 9 | M | Marktgemeinde | 768 | vorhanden (id 1), Code ergänzt auf **M** |
| 10 | G | Gemeinde | 1.122 | **neu angelegt** (id 2) |
| 7 | ST | Stadtgemeinde | 188 | **neu angelegt** (id 3) |
| 8 | SR | Magistrat | 13 | **neu angelegt** (id 4) |
| 12 | MAG | Magistrat der Stadt | 2 | **neu angelegt** (id 5) |
| 13 | GV | Gemeindeverband | 0 | **neu angelegt** (id 6, Nummernfolge 10) |
| 11 | - | - (Platzhalter) | 0 | **bewusst nicht angelegt** |

Summe der zugeordneten Kontakte in Odoo 11: **2.093** — alle fünf tatsächlich genutzten Typen sind damit vorhanden.

**Hinweis:** Der von Anna genannte Wert „Magistrat der Stadt“ ist richtig, „Magistrat“ (13 Kontakte) fehlte in der
Aufstellung, wird aber produktiv verwendet und wurde deshalb mit angelegt. Der Platzhalter „-“ hat 0 Kontakte und
wurde nicht angelegt.

**Mapping-Schlüssel ist der Code** (nicht die ID — IDs sind zwischen Datenbanken nicht stabil).

### 7.2 Zustand nach der Vorbereitung

| Odoo-18-ID | Code | Name |
|---|---|---|
| 1 | M | Marktgemeinde |
| 2 | G | Gemeinde |
| 3 | ST | Stadtgemeinde |
| 4 | SR | Magistrat |
| 5 | MAG | Magistrat der Stadt |
| 6 | GV | Gemeindeverband |

Angelegt auf **lokal und auf der VM**, idempotent (vorhandene Datensätze werden nicht doppelt erzeugt). Kontakte
wurden nicht verändert: 70 Kontakte, davon weiterhin 1 mit einem Organisationstyp (bestehender Testdatensatz).

### 7.3 Reihenfolge bei der späteren Datenmigration

1. Organisationstypen sind vorhanden (dieser Schritt ist erledigt).
2. Beim Übertragen der Kontakte `status_of_community` über den **Code** zuordnen (M, G, ST, SR, MAG, GV).
3. `population` migrieren; Größenklasse und Größenklassen-Bezug werden automatisch berechnet.
4. `population_update` (Stand vom) und `member_of_city_alliance` (Städtebund-Mitglied) 1:1 übernehmen.

## 8. Anzeige des Organisationstyps: Feld war abgeschnitten (Session 110)

**Befund (Browser auf der VM):** Der Wert wurde abgeschnitten — z. B. war von „Marktgemeinde“ nur ein Teil sichtbar.

**Messung vorher (lokal und VM identisch):** Feldbreite **26 px**, benötigte Textbreite 118 px → abgeschnitten.

**Ursache:** Der Reiter besteht aus zwei Gruppen. Die Gruppe „Andere“ ist doppelt verschachtelt und bekam dadurch
nur ein Viertel der Reiterbreite (230 px). Davon nahm die Beschriftung „Organisationstyp“ 108 px ein, sodass für den
Wert nur 26 px blieben.

**Korrektur (gezielt, keine globale UI-Änderung):** In `itk_base_setup` (18.0.1.2.2) zwei Attribute im Reiter
„Gemeinde-Information“: `colspan="2"` auf der Gruppe „Andere“ (volle halbe Reiterbreite) und `colspan="2"` auf dem
Feld `status_of_community`.

**Messung nachher:** Gruppe 461 px, Feldbreite **256 px**, benötigte Textbreite 119 px (längster Wert
„Magistrat der Stadt“) → **vollständig lesbar**, kein Abschneiden.

## 9. Beobachtung außerhalb dieses Bereichs (nicht geändert)

In Odoo 18 gibt es einen zweiten, leeren Reiter „Rechnungsstellung“ (technisch `accounting_disabled`), der nur bei
Personen sichtbar ist; in Odoo 11 hieß der entsprechende Reiter ebenfalls „Abrechnung“. Auf Anweisung nicht bearbeitet.

## 10. Endstand-Verifikation auf der VM (Session 110, verbindliche Abnahmeumgebung)

Alle Prüfungen über HTTPS gegen https://k001959vsx.ipax.at nach den Modul-Upgrades:

| Prüfung | Ergebnis |
|---|---|
| `itk_crm` | **18.0.1.5.1** installiert, `latest_version` identisch |
| `itk_base_setup` | **18.0.1.2.2** installiert, `latest_version` identisch |
| Modellbeschriftungen (7 Felder) | alle auf den Odoo-11-Wortlaut: Einwohnerzahl, Größenklasse (2x), Stand vom, Organisationstyp, Städtebund-Mitglied, Organisationsbezeichnung |
| Reiter-Arch | Gruppe „Andere“ mit `colspan="2"`, Feld `status_of_community` mit `colspan="2"`, alle Beschriftungen deutsch, Regel „nur Unternehmen“ |
| Organisationstypen auf der VM | 6 Datensätze: M Marktgemeinde, G Gemeinde, ST Stadtgemeinde, SR Magistrat, MAG Magistrat der Stadt, GV Gemeindeverband |
| Mapping-Prüfung | alle Codes stimmen mit Odoo 11 überein (Mapping-Schlüssel Code) |
| Browser-Messung Feldbreite | **256 px** (vorher 26 px), Client- und Scrollbreite identisch → **kein Abschneiden** |
| Längster Wert | „Magistrat der Stadt“ benötigt 119 px → vollständig lesbar |
| Browser-Prüfung Kontakt 72 | sichtbar: Einwohnerzahl 1.909, Größenklasse „1.501 bis 2.000“, Stand vom 31.10.2018, Organisationstyp „Marktgemeinde“, Städtebund-Mitglied |
| Screenshots | `19_VM_GemeindeInfo_final.png`, `18_VM_GemeindeInfo_Messung.png` (Desktop\Odoo18-Layoutvergleich-Session95) |
| Kontrollzahlen | 70 Kontakte unverändert; 1 Kontakt mit Organisationstyp (Testdatensatz); 14 Größenklassen |

**Bereich Gemeinde-Information ist damit abgeschlossen und migrationsbereit.**

Der zusätzliche leere Reiter „Rechnungsstellung“ wurde auf Anweisung **nicht** bearbeitet.
