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

## 10. Einzige benoetigte Anpassung: die zwei Filter mit `service_type = 'timesheet'`

Anna-Vorgabe: "Die Odoo-11-Filter muessen weiterhin fachlich dieselben Produktmengen liefern."
Gemessen:

```
Filter "Festpreis-Dienste"    Domain [('type','=','service'), ('invoice_policy','=','order'),
                                     ('service_type','=','timesheet')]
                              Odoo 11: 33 Treffer      Odoo 18: 0 Treffer
Filter "Zeitbasierte Dienste" Domain [('type','=','service'), ('invoice_policy','=','delivery'),
                                     ('service_type','=','timesheet')]
                              Odoo 11: 0 Treffer       Odoo 18: 0 Treffer
```

Ursache: Odoo 18 kennt den Auswahlwert `timesheet` im Feld `service_type` nicht mehr (Odoo 18 hat
dort nur noch `manual`; die stundenbasierte Abrechnung laeuft in Odoo 18 ueber `service_tracking`).
Die Domains sind unveraendert uebernommen, koennen den Wert aber nicht mehr treffen. "Festpreis-
Dienste" liefert deshalb in Odoo 18 0 statt 33 Produkte.

Drei Moeglichkeiten (nicht umgesetzt, Entscheidung bei Anna):

| Variante | Wirkung | Aufwand/Risiko |
|---|---|---|
| A: `service_type` in Odoo 18 um `timesheet` erweitern (itk_product) | Domains bleiben wie in Odoo 11, Treffer wie in Odoo 11 (33 fuer Festpreis) | ein Modulwert ergaenzt; keine Odoo-18-Funktion entfernt; Auswahlfeld hat dann einen zusaetzlichen Wert |
| B: Domain an Odoo-18-Felder anpassen (`service_tracking`) | gleiche fachliche Absicht, andere Domain | neue fachliche Regel noetig, Ergebnis muss einzeln belegt werden |
| C: so belassen | Filter bleibt sichtbar, trifft aber nie | Anna-Vorgabe "dieselben Produktmengen" waere fuer diesen Filter nicht erfuellt |

Der Filter "Meilenstein-Dienste" (`service_type = 'manual'`) ist nicht betroffen: der Wert existiert
in Odoo 18, in Odoo 11 hatte der Filter 0 Treffer, in Odoo 18 einen (Testbestand).
