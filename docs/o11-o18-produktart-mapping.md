# Produktart / `product_type_id`: datenbasierte Mapping-Tabelle (05.10.2026)

**Status: ENTschieden am 05.10.2026 durch Anna - Variante 1 (siehe Abschnitt 0). Die Umsetzung
erfolgt ausschliesslich als Vorbereitung der spaeteren Migration; eine echte Datenmigration ist
nicht erfolgt und nicht beauftragt. Abrechnung bleibt IN ARBEIT.**

Werkzeuge (wiederholbar, ohne Schreibzugriff):

```
scripts/produktart_mapping_messen.py o11|lokal|vm   Auswahlwerte, Anzahl Produkte, Produktarten,
                                                    Abhaengigkeiten (Filter, Ansichten, Aktionen)
scripts/produktart_details.py        o11|lokal|vm   Kreuztabelle type x product_type_id,
                                                    Feldebene, Filtertreffer, Such-/Listenansichten
scripts/produktart_verwendung_je_modul.py o11|lokal|vm  Verwendung je Belegmodell
Rohdaten: %LOCALAPPDATA%\Temp\produktart\*.json
```

## 0. Entscheidung von Anna (05.10.2026): Variante 1 - verbindliche Regel

1. **`type` 1:1 uebernehmen**, soweit der Wert in Odoo 18 vorhanden ist (alle Odoo-11-Werte ausser
   `product`; `product` ist in Odoo 11 nicht belegt und wird zu `consu` + `is_storable`).
2. **`product_type_id` separat 1:1** ueber Name und technische ID uebernehmen (Zielmodell
   `itk_product.product_type`, IDs 1-6 identisch). Voraussetzung: die Namen bleiben unveraendert.
3. **`type` und `product_type_id` werden nicht verschmolzen und nicht gegenseitig abgeleitet.**
   Insbesondere entsteht aus `type = onlineservice` **keine** Produktart (47 Vorlagen mit ITK-`type`
   ohne Produktart behalten dort nichts).
4. **Lagerfuehrung ausschliesslich ueber `is_storable`** in Odoo 18, abgeleitet aus der
   Odoo-11-Lagerfuehrung (`type in ('product','consu')` -> `is_storable = True`, sonst `False`).
   Odoo 18 erzwingt ohnehin `is_storable = False` fuer `type != 'consu'`.
5. **Lagerartikel bleiben bei `product_type_id` leer**, wenn sie in Odoo 11 leer sind (alle 152).
6. **Die sechs bestehenden ITK-Produktarten bleiben erhalten** (Onlineservice, Software-Lösung,
   Consulting, Plattform, Hardware, Förderprojekt) - Name, Kuerzel und ID unveraendert; Grundlage
   fuer die sechs "Service Type ..."-Filter und die Gruppierung "Status".
7. **Die Odoo-11-Filter muessen dieselben Produktmengen liefern.** Mit Variante 1 bleibt der Filter
   "Dienstleistungen" bei 47 aktiven Vorlagen (nicht 497). Offener Einzelfall bleiben die zwei
   Filter mit `service_type = 'timesheet'` (siehe Abschnitt 10).
8. **Keine Odoo-18-Zusatzfunktion wird entfernt** (`combo`, `is_storable`, ITK-Filter, Gruppierung,
   Standardlogik bleiben).

Stand der Umsetzung: **nur vorbereitet**. Regel im Migrationsskript hinterlegt
(`scripts/testmigration_abrechnung.py`, `typ_ziel`), Pruefskript fuer den Vorlauf
(`scripts/pruefe_produktart_regel.py`, read-only, ohne Schreibzugriff). Keine Produktdaten, Filter,
Ansichten oder Zuordnungen geaendert; Odoo 11 unveraendert.

## 0.1 Gemessene Ausgangslage (read-only)

Gemessen in Odoo 11 Prod (`ITK_V1_a`, ausschliesslich lesend) und in Odoo 18 lokal und VM
(`odoo18_test`). Rohdaten und Skripte siehe oben; die fachliche Pruefung mit Beispielprodukten,
Filtern und Entscheidungsmatrix steht in `docs/o11-o18-produktart-pruefung.md`.

## 1. Wichtigster Befund vorab: zwei verschiedene Felder

In Odoo 11 gibt es **zwei unabhaengige Felder**, die beide "Produktart" bedeuten koennen:

| Feld (Odoo 11) | Modell | Typ | Beschriftung Odoo 11 | Verwendung |
|---|---|---|---|---|
| `type` | product.template | selection, 10 Werte | "Produktart" (deutsche Uebersetzung von "Product Type"); in der Formularansicht ausdruecklich sichtbar | 649 Produkte |
| `product_type_id` | product.template | many2one -> itk_product.product_type | "Product-Type" (Listenansicht: "Status") | 410 Produkte, 239 leer |

Die beiden Felder sind **nicht** ineinander ueberfuehrbar (Kreuztabelle in Abschnitt 4, z. B.
`type = general` 273 Produkte, davon `product_type_id = Onlineservice` 241, `Consulting` 16,
`Software-Lösung` 10, `Hardware` 3, `Plattform` 2, leer 1). Jede Migration braucht daher
**zwei getrennte Regeln** - eine fuer `type`, eine fuer `product_type_id`.

## 2. Tabelle A: Odoo-11-Feld `type` (sichtbare Produktart)

Grundgesamtheit: 649 Produktvorlagen (aktiv). "In Belegen verwendet" = Produkt kommt in mindestens
einer Zeile von Kundenrechnungen, Buchungen, Verkaufsauftraegen, Abonnements, Lagerbewegungen oder
Bestellungen vor (468 Produkte insgesamt).

| Odoo 11 Wert | Bezeichnung | Anzahl verwendeter Produkte | Odoo 18 Zielwert | fachlich identisch | technische Auswirkung | Empfehlung |
|---|---|---|---|---|---|---|
| `consu` | Verbrauchsgüter | 152 gesamt / 122 in Belegen | `type = consu` + `is_storable = True` | ja | Odoo-11-Lagerartikel: 90 von 91 Produkten mit Lagerbewegungen sind `consu`; `product_type_id` dabei immer leer | 1:1 uebernehmen, Lagerart ueber `is_storable` (Odoo 18 trennt Typ und Lagerfuehrung) |
| `service` | Service | 47 / 48 | `type = service` | ja | Odoo-18-Standardlogik erwartet `service` fuer Dienste (z. B. Verkaufs-Sektionen) | 1:1 uebernehmen |
| `general` | Allgemein | 273 / 163 | in Odoo 18 kein Standardwert, aber in der ITK-Auswahl enthalten | nur in der ITK-Auswahl, nicht in der Odoo-18-Standardlogik | 273 Produkte (40 % des Bestands); Odoo-18-Standardpruefungen auf `type = 'service'` / `'consu'` / `'combo'` greifen hier nicht | Entscheidung Anna: Wert erhalten oder auf `service`/`consu` abbilden (Art bleibt in `product_type_id` erhalten) |
| `platform` | Plattform | 94 / 69 | dito (`platform` in der ITK-Auswahl enthalten) | dito | 69 verwendete Produkte, u. a. in Abonnements (45) | dito |
| `onlineservice` | Onlineservice | 74 / 58 | dito | dito | 58 verwendete Produkte; 1 Produkt hat eine Lagerbewegung (Einzelfall) | dito |
| `sw` | Software-Lösung | 9 / 8 | dito | dito | 8 verwendete Produkte | dito |
| `consulting` | Consulting | 0 / 0 | dito | dito | nicht belegt | keine Daten - Wert bleibt formal moeglich |
| `hw` | Hardware | 0 / 0 | dito | dito | nicht belegt | keine Daten |
| `project` | Förderprojekt | 0 / 0 | dito | dito | nicht belegt | keine Daten |
| `product` | Stockable Product | 0 / 0 | **in Odoo 18 nicht vorhanden** | nein (entfaellt) | Odoo 11 nutzte `product` fuer Lagerartikel; Entsprechung ist `is_storable = True` (von Anna bereits bestaetigt, Abschnitt 6) | als `consu` + `is_storable` uebernehmen |

Gegenprobe Odoo 18: Die ITK-Auswahl erlaubt derzeit
`consu, service, combo, general, onlineservice, sw, consulting, platform, hw, project`
(lokal und VM identisch, `fields_get`). Sie enthaelt **alle in Odoo 11 verwendeten Werte** und
zusaetzlich `combo` (Odoo-18-Standard, in Odoo 11 unbekannt); `product` fehlt. Der Modulcode
`addons/itk_product/models/models.py` setzt diese Auswahl ausdruecklich.

## 3. Tabelle B: Odoo-11-Feld `product_type_id` (ITK-Produktart)

Zielmodell in beiden Systemen: `itk_product.product_type`. Die sechs Datensaetze stimmen in Name,
Kuerzel und **technischer ID** ueberein (Odoo 11 und Odoo 18 lokal/VM):

| Odoo 11 ID / Wert | Bezeichnung | Anzahl verwendeter Produkte | Odoo 18 Zielwert | fachlich identisch | technische Auswirkung | Empfehlung |
|---|---|---|---|---|---|---|
| 1 / `Onlineservice` | Onlineservice | 314 gesamt / 192 in Belegen | ID 1 `Onlineservice` (Kuerzel OS) | ja | 6 Suchfilter "Service Type ..." und die Gruppierung "Status" greifen diesen Datensatz | 1:1 ueber Name und ID |
| 2 / `Software-Lösung` | Software-Lösung | 18 / 17 | ID 2 `Software-Lösung` (SW) | ja | wie oben | 1:1 |
| 3 / `Consulting` | Consulting | 19 / 12 | ID 3 `Consulting` (C) | ja | wie oben | 1:1 |
| 4 / `Plattform` | Plattform | 56 / 42 | ID 4 `Plattform` (P) | ja | wie oben | 1:1 |
| 5 / `Hardware` | Hardware | 3 / 1 | ID 5 `Hardware` (HW) | ja | wie oben | 1:1 |
| 6 / `Förderprojekt` | Förderprojekt | 0 / 0 | ID 6 `Förderprojekt` (FP) | ja | in Odoo 11 nicht belegt | Datensatz vorhanden lassen |
| (leer) | keine Produktart | 239 / 204 | leer | ja | 204 der 468 verwendeten Produkte haben keine Produktart; 152 davon sind Lagerartikel (`consu`) | leer uebernehmen, keinen Standardwert setzen |

Damit ist die Zuordnung `product_type_id` **eindeutig 1:1** - gleicher Modellname, gleiche Namen,
gleiche Kuerzel, gleiche IDs 1 bis 6, keine Dubletten, keine Umbenennung noetig. **Von Anna am
05.10.2026 freigegeben** (Regel 2 in Abschnitt 0): Uebernahme separat ueber Name und ID, ohne
Ableitung aus `type`. Voraussetzung bleibt, dass die sechs Namen unveraendert bleiben - die sechs
"Service Type ..."-Filter vergleichen gegen den Namen.

## 4. Kreuztabelle Odoo 11: `type` x `product_type_id` (649 Vorlagen)

```
type             product_type_id-Verteilung (Anzahl Vorlagen)
general    273   Onlineservice 241 | Consulting 16 | Software-Lösung 10 | Hardware 3 | Plattform 2 | leer 1
consu      152   leer 152
platform    94   Onlineservice 65 | Plattform 29
onlineservice 74 leer 44 | Plattform 24 | Onlineservice 6
service     47   leer 41 | Consulting 3 | Onlineservice 2 | Plattform 1
sw           9   Software-Lösung 8 | leer 1
```

Folgerungen:

- Es besteht **keine** eindeutige Beziehung zwischen `type` und `product_type_id` (beide Richtungen
  sind mehrdeutig). `type` kann `product_type_id` nicht ersetzen und umgekehrt.
- Alle 152 Lagerartikel (`consu`) haben **keine** Produktart; alle 91 Produkte mit Lagerbewegungen
  haben `product_type_id = leer`.
- Die Odoo-11-Produktart fuer die ITK-Sicht ist `product_type_id` (in Odoo 11 ueber die Suchfilter
  "Service Type ..." gepflegt); `type` traegt in der Praxis die Grobunterscheidung
  Lagerartikel / Dienstleistung, ist aber inkonsistent gepflegt (241 von 273 `general` sind
  ITK-Onlineservice).

## 5. Abhaengigkeiten (gemessen, nicht vermutet)

| Ort | Abhaengigkeit | Betrifft | Beleg |
|---|---|---|---|
| Odoo 11 Suchansicht `product.template.search.inherit` | 6 Filter "Service Type Consulting/Onlineservice/Software-Solution/Platform/Hardware/Förderprojekt" mit `[('product_type_id','=',"<Name>")]` | `product_type_id` (per **Name**) | Arch gelesen |
| Odoo 11 Suchansicht (gleiche Ansicht) | Filter "Products" / "Subscription products" ueber `recurring_invoice` | Abonnements, **nicht** Produktart | Arch gelesen |
| Odoo 11 Listenansicht `Product Template Tree ITK` | Spalte `product_type_id` mit Beschriftung "Status" | `product_type_id` | Arch gelesen |
| Odoo 11 Formular `Product Template ITK` | zeigt `type` (sichtbar) **und** `product_type_id` | beide Felder | Arch gelesen |
| Odoo 11 ir.filters | 244 gespeicherte Filter, davon 1 Treffer ohne Produktartbezug (Abonnement-Filter auf Zeileninhalt) | keine | RPC |
| Odoo 11 Automationen/Serveraktionen | keine | keine | RPC |
| Odoo 11 Modelle mit `product_type_id` | nur `product.template` (store) und `product.product` (nicht gespeichert) | - | ir.model.fields |
| Odoo 18 Suchansicht `Product Template Search ITK Produktfilter` | 6 Filter "Service Type ..." auf `product_type_id` (per Name), 3 Filter "Zeitbasierte/Festpreis/Meilenstein-Dienste" auf `type = 'service'` + `invoice_policy` + `service_type`, 2 Bestandsfilter auf `is_storable` | beide Felder | Arch gelesen |
| Odoo 18 Suchansicht `product.template.search.abo.produkte` | Gruppierung "Status" (`group_by product_type_id`), Filter "Aktive Abonnement Produkte" (`recurring_invoice`) | `product_type_id`, Abo ueber `recurring_invoice` | Arch gelesen |
| Odoo 18 Listenansicht `Product Template Tree ITK` | Spalte "Status" (`product_type_id`) | `product_type_id` | Arch gelesen |
| Odoo 18 Code `addons/itk_product/models/models.py` | definiert die `type`-Auswahl mit den ITK-Werten und `product_type_id` (string "Produkttyp") | beide Felder | Quelle gelesen |
| Verkauf / Einkauf | haengen an `sale_ok` / `purchase_ok`, nicht an der Produktart | keine | Odoo-18-Kommentar in der Produktfilter-Ansicht (Odoo 11 1:1) |
| Lager | Odoo 11: `type` in (`product`, `consu`); Odoo 18: `is_storable` | `type` / `is_storable` | 90 von 91 Lagerbewegungen sind `consu` |

**Wichtig fuer jede Entscheidung:** Die sechs "Service Type ..."-Filter und die Gruppierung "Status"
arbeiten mit dem **Namen** des Produktart-Datensatzes (`('product_type_id','=','Consulting')`).
Eine Umbenennung oder ein zusaetzlicher Datensatz mit gleichem Namen wuerde die Filter still
unwirksam machen. Umgekehrt bleiben die Filter nur funktionsfaehig, wenn die sechs Namen exakt
erhalten bleiben.

## 6. Verwendung je Belegmodell in Odoo 11 (verwendete Produkte)

| Modul | Produkte | `type` (Produktart) | `product_type_id` (ITK-Art) |
|---|---|---|---|
| Kundenrechnungen | 411 | general 140, consu 107, platform 59, onlineservice 52, service 45, sw 8 | leer 181, Onlineservice 162, Plattform 42, SW 17, Consulting 8, HW 1 |
| Verkaufsauftraege | 403 | general 155, consu 83, platform 66, onlineservice 46, service 45, sw 8 | Onlineservice 183, leer 152, Plattform 42, SW 14, Consulting 11, HW 1 |
| Abonnements | 209 | general 101, platform 45, service 24, consu 21, onlineservice 12, sw 6 | Onlineservice 116, leer 51, Plattform 25, SW 12, Consulting 5 |
| Lagerbewegungen | 91 | consu 90, onlineservice 1 | leer 91 |
| Bestellungen | 0 | - | - |

Abonnements und Verkauf haengen **fachlich** an `recurring_invoice` und `sale_ok`, nicht an der
Produktart; die Lagerfuehrung haengt in Odoo 11 an `type = consu`/`product`, in Odoo 18 an
`is_storable`. Die Produktart selbst steuert in beiden Systemen nur Auswertung, Filter und
Gruppierung.

## 7. Zwei moegliche Regelungen fuer `type` (zur Entscheidung, keine davon umgesetzt)

**Variante 1 - Werte 1:1 uebernehmen.** Die Odoo-18-Auswahl der ITK erlaubt alle in Odoo 11
verwendeten Werte (bis auf `product`, das nicht belegt ist), also technisch machbar.
Folge: Die Produktart bleibt in `type` sichtbar wie in Odoo 11. Zugleich greifen die
Odoo-18-Standardpruefungen auf `type = 'service'` nicht, und die drei ITK-Filter "Zeitbasierte /
Festpreis- / Meilenstein-Dienste" (Domain `type = 'service'`) wuerden nur die 48 Produkte mit
`type = service` finden, nicht die 346 verwendeten Dienstleistungsprodukte (`general`, `platform`,
`onlineservice`, `sw`, `service` - von 468 verwendeten Produkten insgesamt).

**Variante 2 - Grobabbildung auf `consu`/`service` + `is_storable`, Art in `product_type_id`.**
Lagerartikel (`consu`, `product`) -> `consu` + `is_storable = True` (152 Produkte, Datenlage
eindeutig), alle Dienstleistungswerte (`general`, `platform`, `onlineservice`, `sw`, `consulting`,
`hw`, `project`) -> `service` (497 Produkte). Folge: Odoo-18-Standardlogik und die ITK-DiensteFilter
arbeiten wie vorgesehen; die fachliche ITK-Art bleibt vollstaendig in `product_type_id` erhalten
(314 Onlineservice, 56 Plattform, 19 Consulting, 18 Software-Lösung, 3 Hardware) und ist dort
heute schon gepflegt und gefiltert. Nachteil: `type` verliert die Feinheit, die es in Odoo 11
ohnehin nur inkonsistent trug.

**Entscheidung (Anna, 05.10.2026): Variante 1.** `type` wird 1:1 uebernommen, soweit der Wert in
Odoo 18 vorhanden ist (`product` ist dort nicht vorhanden und in Odoo 11 nicht belegt -> `consu` +
`is_storable`). Damit bleibt der Filter "Dienstleistungen" bei 47 aktiven Vorlagen, und die
Odoo-18-Standardlogik verhaelt sich wie in Odoo 11 (ITK-Werte gelten wie dort als Nicht-Dienst).
`product_type_id` wird unabhaengig davon separat 1:1 uebernommen (Abschnitt 3). Variante 2 wird
nicht umgesetzt.

## 8. Was bereits mit Anna abgestimmt ist (nicht Teil der offenen Frage)

- **`type = product` (Stockable Product):** existiert in Odoo 18 nicht; Entsprechung ist
  `is_storable = True`. Von Anna bestaetigt (`docs/o11-o18-abrechnung-itk-produktfilter.md`).
  In Odoo 11 nicht belegt (0 Produkte).
- **Filter "Bestandsauflösung":** Odoo 11 `type not in ('service','consu')` -> Odoo 18
  `is_storable = True`. Von Anna bestaetigt.
- **Filter "Veröffentlicht"** (`website_published`): nicht nachgebaut (Feld fehlt, 0 Treffer).
- Die sechs "Service Type ..."-Filter sind in Odoo 18 vorhanden und laufen fehlerfrei.

## 9. Stand der offenen Punkte nach der Entscheidung

**Entschieden am 05.10.2026 (Variante 1, Abschnitt 0).** Umsetzung nur vorbereitet; keine
Produktdaten, Filter, Ansichten oder Zuordnungen geaendert, keine Datenmigration ausgefuehrt,
Odoo 11 nur lesend gelesen. Abrechnung bleibt IN ARBEIT.

1. `type`: entschieden (Variante 1).
2. `product_type_id`: freigegeben (1:1 ueber Name und ID, Abschnitt 3).
3. `product_type_id` bei Lagerartikeln leer lassen: entschieden (Regel 5).
4. Einzige noch anpassungsbeduerftige Stelle: die zwei Filter mit `service_type = 'timesheet'`
   (Abschnitt 10). Alles andere bleibt unveraendert.

## 10. Die zwei Filter mit `service_type = 'timesheet'` - gemessener Sachstand

Anna-Vorgabe: "Die Odoo-11-Filter muessen weiterhin fachlich dieselben Produktmengen liefern."
Gemessen in Odoo 11 (read-only):

```
Filter "Festpreis-Dienste"     [('type','=','service'), ('invoice_policy','=','order'),
                                ('service_type','=','timesheet')]      -> 33 Treffer
Filter "Zeitbasierte Dienste"  [('type','=','service'), ('invoice_policy','=','delivery'),
                                ('service_type','=','timesheet')]      ->  0 Treffer
Odoo-11-Daten:  service_type     manual 600, timesheet 53
                service_policy   ordered_timesheet 53, sonst leer
                service_tracking auf allen 653 Vorlagen 'no' (nie benutzt)
```

Gemessen in Odoo 18 (lokal und VM):

```
service_type      nur 'manual'; der Wert 'timesheet' wird vom Modul sale_timesheet ergaenzt
                  (sale_timesheet/models/product_template.py:17  selection_add)
service_policy    existiert in Odoo 18 im Modul sale_project (nicht installiert)
service_tracking  nur 'no'; die uebrigen Werte kommen von sale_project/sale_timesheet
Module            sale_timesheet uninstalled, sale_project uninstalled
Folge             beide Filter koennen in der Testinstanz nicht treffen (0 Treffer),
                  unabhaengig von Produktdaten oder Migration
```

Fachliche Entsprechung - geprueft, keine Domain-Aenderung:

1. Odoo 11 hatte **beide** Felder parallel: `service_type` (manual/timesheet) und
   `service_tracking` (Aufgabe/Projekt erstellen). Die zwei Filter benutzen `service_type`.
2. `service_tracking` war in Odoo 11 auf **allen 653 Vorlagen 'no'** - es traegt keine Information
   und ist damit **nicht** die fachliche Entsprechung dieser Filter. Eine Umstellung der Domains auf
   `service_tracking` waere neue Fachlogik und wuerde 0 Produkte finden.
3. Die Entsprechung ist der **Auswahlwert `service_type = 'timesheet'` selbst** (gleiches Feld,
   gleicher technischer Name, gleiche Bedeutung: Zeiterfassung bei Projekt). Er ist in Odoo 18
   vorhanden, sobald das Modul `sale_timesheet` installiert ist; `service_policy` bringt
   `sale_project` mit.

**Ergebnis: keine Aenderung an den Filtern.** Sie bleiben unveraendert. Zwei Filter ("Zeitbasierte
Dienste", "Festpreis-Dienste") treffen in der aktuellen Testinstanz nicht, weil ihnen der
Modulumfang fehlt - das ist eine Modulumfangs-Entscheidung, keine Filterfrage:

| Moeglichkeit | Wirkung | Bewertung |
|---|---|---|
| Zielumfang enthaelt `sale_timesheet` (und ggf. `sale_project`) | die Domains treffen wie in Odoo 11 (Festpreis 33), zusaetzlich stehen Zeiterfassung/Projektdienste zur Verfuegung | von Anna zu entscheiden; die Filter bleiben dafuer unveraendert |
| Zielumfang ohne diese Module | die zwei Filter bleiben sichtbar und leer; "Meilenstein-Dienste" (`service_type = 'manual'`) funktioniert weiter | dokumentierte Abweichung |

Folge fuer die Migration (neu, noch nicht umgesetzt): In Odoo 11 tragen **53 Vorlagen**
`service_type = 'timesheet'` und `service_policy = 'ordered_timesheet'` - also echte Fachdaten, die
zu den zwei Filtern gehoeren. Das Migrationsskript uebertraegt bisher nur `invoice_policy`, nicht
`service_type` und `service_policy` (`scripts/testmigration_abrechnung.py`, Abschnitt
Produktuebernahme). Uebernehmen laesst sich der Wert nur, wenn der Zielumfang die Module
`sale_timesheet`/`sale_project` enthaelt - sonst lehnt Odoo den Auswahlwert ab. Damit gilt:

- Mit `sale_timesheet`/`sale_project` im Ziel: `service_type` und `service_policy` 1:1 uebertragen
  (53 Vorlagen), die zwei Filter treffen wie in Odoo 11 (Festpreis 33).
- Ohne diese Module: die beiden Felder nicht uebertragen, bewusst dokumentieren; die Filter bleiben
  leer. Kein Ersatz durch eine Ableitung aus `type` oder `product_type_id`.

Entscheidung liegt bei Anna (Modulumfang); ich habe nichts geaendert.

## 11. Praktischer Lager-Test in Odoo 18 (05.10.2026)

Auftrag: temporaeres Lager-Testprodukt ausschliesslich in der Odoo-18-Testinstanz anlegen, Lagerfall
praktisch pruefen, danach vollstaendig entfernen und den Bestand vorher/nachher kontrollieren.
Werkzeuge: `scripts/lagerprodukt_test.py` (Anlegen, Inventuranpassung, Aufraeumen, Zaehlen),
`scripts/browser_lagerprodukt_test.py` (Browserpruefung lokal und VM),
`scripts/vm_lager_aufraeumen.py` (VM-Bereinigung, weil SSH gesperrt war).

Testprodukt (lokal product.template 233 / VM 286): `ZZ-TEST-LAGER`, `type = consu`,
`is_storable = True`, `product_type_id` zunaechst leer, sale_ok/purchase_ok ja.

Ergebnisse (lokal und VM identisch):

```
Reiter "Lager"          erscheint nur bei lagerfuehrbaren Produkten - beim Testprodukt sichtbar,
                        bei allen nicht lagerfuehrbaren Produkten fehlt er (Odoo-18-Regel)
Formular                "Bestand verfolgen" gesetzt; "Produktart" separat gepflegt; type unsichtbar
Smart Buttons           "5,000 Einheit(en) Vorrätig", "5,000 Prognostiziert", "0 Meldebestände",
                        "Eingang: 0 Ausgang: 0" - nur bei is_storable vorhanden
Inventuranpassung       +5 Stueck auf WH/Bestand gebucht (eine abgeschlossene Lagerbewegung,
                        kein Bewertungssatz in der Buchhaltung - Kategorie ist "Manual")
Filter Lagerverwaltung  findet das Testprodukt (is_storable)
Filter Bestandsauflösung (Bestand <= 0 UND is_storable)
                        vor der Buchung: findet das Testprodukt
                        nach der Buchung: findet es nicht mehr (Bestand 5) - Regel greift korrekt
Filter Service Type Platform
                        findet das Testprodukt, obwohl type = consu ist - Beleg, dass
                        product_type_id unabhaengig von type gepflegt wird
Verkauf/Einkauf         neue Belegformulare (Verkaufsauftrag, Bestellung) geoeffnet, ohne Speichern;
                        Produkt bleibt verkauf- und einkaufbar
Konsistenz              type = consu + is_storable = True + product_type_id = Plattform
                        gleichzeitig: kein Fehler, keine Warnung, Lagerlogik unveraendert;
                        Odoo 18 erzwingt weiterhin is_storable = False nur fuer type != consu
Abnahmeergebnis         lokal: vorher 12 OK / 0 FEHL, nachher 16 OK / 0 FEHL
                        VM:    vorher 12 OK / 0 FEHL, nachher 16 OK / 0 FEHL
Bilder                  Desktop/Odoo18-Abnahme-Session126/lager_test/{lokal,vm}/{vorher,nachher}
```

Bereinigung (vollstaendig, per ID kontrolliert):

```
                                lokal              VM
product.template                13 / 13            10 / 10      (vorher / nachher)
product.product                 13 / 13            10 / 10
stock.quant                      0 / 0              0 / 0
stock.move                       0 / 0              0 / 0
stock.move.line                  0 / 0              0 / 0
stock.picking                    0 / 0              0 / 0
stock.valuation.layer            0 / 0              0 / 0
account.move                    38 / 38            59 / 59
account.move.line              102 / 102          166 / 166
Filter Bestandsaufloesung        0 / 0              0 / 0
Filter Lagerverwaltung           0 / 0              0 / 0
Testprodukt vorhanden            nein               nein
temporaere Serveraktion          0                  0
```

Hinweis zur Bereinigung: Odoo blockiert das Loeschen abgeschlossener Lagerbewegungen,
Bewertungssaetze und belegter Quants per ORM. Die gezielten DELETE-Anweisungen (nur die IDs des
Testprodukts) liefen daher lokal per psql und auf der VM ueber eine einmalige Odoo-Serveraktion,
die danach wieder geloescht wurde. Odoo 11 wurde in keinem Schritt beruehrt.
