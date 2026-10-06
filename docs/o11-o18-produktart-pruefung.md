# Produktarten: fachliche Pruefung Odoo 11 gegen Odoo 18 (05.10.2026)

**Status: reine Analyse. Keine Entscheidung, keine Umsetzung, keine Aenderung an Produktdaten,
Filtern, Ansichten oder Zuordnungen. Abrechnung bleibt IN ARBEIT.** Auftrag und Pruefpunkte von
Anna (05.10.2026); die offene Frage `type` (Produktart) bleibt ausdruecklich offen.

**Nachtrag 05.10.2026 (nach der Analyse): Anna hat entschieden - Variante 1.** `type` wird 1:1
uebernommen, soweit der Wert in Odoo 18 vorhanden ist; `product_type_id` wird separat 1:1 ueber
Name und ID uebernommen; `type` und `product_type_id` werden nicht verschmolzen und nicht
gegeneinander abgeleitet; die Lagerfuehrung laeuft ausschliesslich ueber `is_storable`;
Lagerartikel bleiben bei `product_type_id` leer; die sechs ITK-Produktarten bleiben erhalten; die
Odoo-11-Filter muessen dieselben Produktmengen liefern. Verbindliche Regelfassung:
`docs/o11-o18-produktart-mapping.md`, Abschnitt 0. Umsetzung nur vorbereitet (Migrationsskript und
Pruefskript), keine Datenmigration, keine Aenderung an Daten, Filtern oder Ansichten. Die
Abschnitte 7 und 11 dieses Berichts sind damit historisch (Entscheidungsvorlage).

Datenbasis (alles read-only, keine Testdaten angelegt, Odoo 11 Prod nur gelesen):

```
Odoo 11 Prod   ITK_V1_a        653 Produktvorlagen (649 aktiv), 411 in Rechnungszeilen,
                                403 in Verkaufszeilen, 209 in Abo-Zeilen, 91 mit Lagerbewegungen
Odoo 18 lokal  odoo18_test     23 Produktvorlagen (Testbestand)
Odoo 18 VM     odoo18_test     23 Produktvorlagen (Testbestand, gleiche Daten)
```

Werkzeuge: `scripts/produktart_mapping_messen.py`, `scripts/produktart_details.py`,
`scripts/produktart_verwendung_je_modul.py`, `scripts/produktart_pruefung_bericht.py`;
Rohdaten `%LOCALAPPDATA%\Temp\produktart\*.json`; Code-/Arch-Pruefungen im Container
(`pruefe_odoo18_code*.sh`, nur grep).

## 1. Zwei getrennte Felder - Kurzfassung

| Feld | Odoo 11 | Odoo 18 aktuell |
|---|---|---|
| `type` | Auswahl mit 10 Werten (`consu`, `service`, `general`, `onlineservice`, `sw`, `consulting`, `platform`, `hw`, `project`, `product`), Beschriftung "Product Type" (deutsch "Produktart"), Pflicht, im Formular sichtbar | Auswahl mit 10 Werten (`consu`, `service`, `combo`, `general`, `onlineservice`, `sw`, `consulting`, `platform`, `hw`, `project`), Pflicht, im Formular unsichtbar (`invisible="1"` in itk_product) |
| `product_type_id` | many2one -> `itk_product.product_type`, Beschriftung "Product-Type" (Liste: "Status"), 413 Vorlagen belegt, 240 leer | viele2one -> `itk_product.product_type`, Beschriftung "Produktart" (Modell), Liste "Status", im Formular sichtbar |

Die beiden Felder sind unabhaengig: **413 von 653** Vorlagen tragen eine Produktart,
davon passen nur **43** zum `type`-Wert, **370** weichen ab (Beispiel: Acta Nova
Nutzungsentgelt, `type = general`, Produktart = Software-Lösung). **240** Vorlagen haben
keine Produktart - 193 davon sind Lagerartikel oder Service, 47 tragen einen ITK-`type`-Wert ohne
Produktart.

Genauigkeit zum Odoo-18-Auswahlfeld `type`: der Odoo-18-Kern (product/models/product_template.py)
kennt `consu`, `service`, `combo`; das ITK-Modul `itk_product/models/models.py` setzt die Auswahl
zusaetzlich auf die neun ITK-Werte. Gemessen (`fields_get`, lokal und VM) ergibt das zehn Werte:
`combo` (Odoo-18-Standard) plus die ITK-Werte; der Odoo-11-Wert `product` fehlt.

## 2. Repraesentative Produkte je Gruppe (Odoo 11, read-only)

Auswahlregel: je Gruppe die drei Vorlagen mit der meisten Verwendung (Rechnungszeilen dreifach,
Abo-Zeilen zweifach, Lagerbewegungen einfach gewichtet). Gruppen nach Produktart bzw. `type`.

| Gruppe | Produkt | type (Bezeichnung) | Produktart (Bezeichnung) | sale_ok | purchase_ok | Lagerbewegungen | in Rechnungen | in Verkaufsauftraegen | in Abos | type und Art fachlich gleich? |
|---|---|---|---|---|---|---|---|---|---|---|
| ITK-Art: Consulting | E-Government-Strategieberatung | general (Allgemein) | Consulting (Consulting) | ja | ja | nein | ja (20) | ja (21) | nein | nein |
| ITK-Art: Consulting | E-Government-Referenzstädte/Digitale Städte | general (Allgemein) | Consulting (Consulting) | ja | ja | nein | ja (40) | ja (31) | nein | nein |
| ITK-Art: Consulting | Reisekosten | general (Allgemein) | Consulting (Consulting) | ja | ja | nein | ja (20) | ja (12) | nein | nein |
| ITK-Art: Hardware | Canon-Scanner | general (Allgemein) | Hardware (Hardware) | ja | ja | nein | nein | nein | nein | nein |
| ITK-Art: Hardware | Bluetec Barcodescanner | general (Allgemein) | Hardware (Hardware) | ja | ja | nein | nein | nein | nein | nein |
| ITK-Art: Hardware | Barcode-Klebeetiketten | general (Allgemein) | Hardware (Hardware) | ja | ja | nein | ja (1) | ja (1) | nein | nein |
| ITK-Art: Onlineservice | DSGVO-Verarbeitungsverzeichnis Preis pro ang | general (Allgemein) | Onlineservice (Onlineservice) | ja | ja | nein | ja (211) | ja (31) | ja (35) | nein |
| ITK-Art: Onlineservice | Amtsweg.gv.at Formularsammlung Österreich Pr | general (Allgemein) | Onlineservice (Onlineservice) | ja | ja | nein | ja (2797) | ja (610) | ja (603) | nein |
| ITK-Art: Onlineservice | Amtsweg.gv.at Formularsammlung Österreich So | general (Allgemein) | Onlineservice (Onlineservice) | ja | ja | nein | ja (2773) | ja (600) | ja (602) | nein |
| ITK-Art: Plattform | Hinweisgeberportal bis 15.000 EW  | platform (Plattform) | Plattform (Plattform) | ja | ja | nein | ja (170) | ja (42) | ja (31) | ja |
| ITK-Art: Plattform | Hinweisgeberportal bis 100 Mitarbeiter/innen | platform (Plattform) | Plattform (Plattform) | ja | ja | nein | ja (47) | ja (9) | ja (9) | ja |
| ITK-Art: Plattform | Hinweisgeberportal bis 100 Mitarbeiter/innen | platform (Plattform) | Plattform (Plattform) | ja | ja | nein | ja (67) | ja (18) | ja (19) | ja |
| ITK-Art: Software-Lösung | IFG-Verfahren Ersteinrichtung Mandant | sw (Software-Lösung) | Software-Lösung (Software-Lösung) | ja | ja | nein | ja (19) | ja (21) | nein | ja |
| ITK-Art: Software-Lösung | IFG-Verfahren Bereitstellung Anwendung als M | sw (Software-Lösung) | Software-Lösung (Software-Lösung) | ja | ja | nein | ja (26) | ja (20) | ja (17) | ja |
| ITK-Art: Software-Lösung | IFG-Verfahren Plattform-Basislizenz für bis  | sw (Software-Lösung) | Software-Lösung (Software-Lösung) | ja | ja | nein | ja (33) | ja (21) | ja (12) | ja |
| ohne ITK-Art: type=consu (Lagerartikel) | E-Abfertigung Transaktionskosten | consu (Verbrauchsgüter) | leer (keine Produktart) | ja | ja | ja (21) | ja (22) | ja (21) | nein | ja |
| ohne ITK-Art: type=consu (Lagerartikel) | ZVK-Mitglied Rabatt | consu (Verbrauchsgüter) | leer (keine Produktart) | ja | ja | nein | ja (28) | nein | ja (2) | ja |
| ohne ITK-Art: type=consu (Lagerartikel) | A-Tool einmalige Setupkosten | consu (Verbrauchsgüter) | leer (keine Produktart) | ja | ja | ja (76) | ja (28) | ja (73) | nein | ja |
| ohne ITK-Art: type=general | E-Abfertigung Versandprofil | general (Allgemein) | leer (keine Produktart) | ja | ja | nein | ja (1) | ja (1) | nein | nein |
| ohne ITK-Art: type=onlineservice | Einrichtungsgebühr der Österreichischen Post | onlineservice (Onlineservice) | leer (keine Produktart) | ja | ja | nein | ja (219) | ja (234) | nein | nein |
| ohne ITK-Art: type=onlineservice | IFG-Portal Betrieb jährliches Nutzungsentgel | onlineservice (Onlineservice) | leer (keine Produktart) | ja | ja | nein | ja (38) | ja (38) | ja (39) | nein |
| ohne ITK-Art: type=onlineservice | IFG-Portal jährliches Nutzungsentgelt mehr a | onlineservice (Onlineservice) | leer (keine Produktart) | ja | ja | ja (2) | ja (40) | ja (2) | ja (2) | nein |
| ohne ITK-Art: type=service | amtsweg.gv.at Formularsammlung Bundesland St | service (Service) | leer (keine Produktart) | ja | ja | nein | ja (9) | ja (15) | ja (15) | ja |
| ohne ITK-Art: type=service | Personentage | service (Service) | leer (keine Produktart) | ja | ja | nein | ja (97) | ja (88) | nein | ja |
| ohne ITK-Art: type=service | Dienstleistungsstunden | service (Service) | leer (keine Produktart) | ja | ja | nein | ja (124) | ja (116) | nein | ja |
| ohne ITK-Art: type=sw | Communex Plattform Class A  | sw (Software-Lösung) | leer (keine Produktart) | ja | ja | nein | ja (1) | ja (1) | ja (1) | nein |

653 Vorlagen gesamt, 413 mit Produktart, 240 ohne. In Odoo 11 sind die
Lagerartikel (`type = consu`) ausnahmslos ohne Produktart; die ITK-Produktart tragen nur
Dienstleistungsprodukte.

### 2.1 Dieselben Produkte in Odoo 18

Die Odoo-18-Testinstanz enthaelt nur 23 Vorlagen. Von den geprueften Beispielen existieren dort
nur zwei (aus der frueheren Testmigration, Zuordnung ueber den Namen):

| Instanz | O18-ID | Produkt | type | Produktart | is_storable | in Buchungen | in Abos | Lagerbewegungen |
|---|---|---|---|---|---|---|---|---|
| lokal | 224 | Amtsweg.gv.at Formularsammlung Österreich Pr | service | leer | nein | ja | ja | nein |
| lokal | 225 | Amtsweg.gv.at Formularsammlung Österreich So | service | leer | nein | ja | ja | nein |
| vm | 224 | Amtsweg.gv.at Formularsammlung Österreich Pr | service | leer | nein | ja | ja | nein |
| vm | 225 | Amtsweg.gv.at Formularsammlung Österreich So | service | leer | nein | ja | ja | nein |

Befund: Die beiden migrierten Produkte stehen in Odoo 18 als `type = service` **ohne Produktart**,
obwohl ihre Odoo-11-Quellen eine Produktart tragen (Amtsweg.gv.at Preis pro ... : `type = general`,
Produktart = Onlineservice; Sockelbetrag: `type` = general bzw. onlineservice bzw. service,
Produktart = Onlineservice). Der aktuelle Stand der Testmigration uebertraegt die Produktart also
**nicht** - das ist ein Befund ueber den vorhandenen Testdatensatz, keine Regel. Das Skript
`scripts/testmigration_abrechnung.py` enthaelt inzwischen einen Transfer von `product_type_id`
(Zeilen 327 ff.), sein Modulkopf beschreibt aber noch die aeltere Annahme "Odoo 18 kennt nur
consu/service/combo ... ITK-Werte -> service" (Zeilen 18-23), waehrend die Funktion `typ_ziel`
(Zeilen 72-78) die ITK-Werte 1:1 durchreicht. Diese Textstelle widerspricht dem Code und der
gemessenen Odoo-18-Auswahl.

## 3. Produktfilter: Domains, Treffer, Stichproben

Alle Filter der Produktsuchansichten (Odoo 11: 23 Filter, Odoo 18 lokal und VM: je 34).
Die produktart-relevanten Filter im Vergleich:

| Filter | Domain Odoo 11 | Domain Odoo 18 | Treffer Odoo 11 | Treffer Odoo 18 (lokal) | Domain |
|---|---|---|---|---|---|
| Service Type Onlineservice | [('product_type_id', '=', 'Onlineservice')] | [('product_type_id', '=', 'Onlineservice')] | 314 | 1 | gleiche Domain |
| Service Type Consulting | [('product_type_id', '=', 'Consulting')] | [('product_type_id', '=', 'Consulting')] | 19 | 0 | gleiche Domain |
| Service Type Software-Solution | [('product_type_id', '=', 'Software-Lösung')] | [('product_type_id', '=', 'Software-Lösung')] | 18 | 0 | gleiche Domain |
| Service Type Platform | [('product_type_id', '=', 'Plattform')] | [('product_type_id', '=', 'Plattform')] | 56 | 0 | gleiche Domain |
| Service Type Hardware | [('product_type_id', '=', 'Hardware')] | [('product_type_id', '=', 'Hardware')] | 3 | 0 | gleiche Domain |
| Service Type Förderprojekt | [('product_type_id', '=', 'Förderprojekt')] | [('product_type_id', '=', 'Förderprojekt')] | 0 | 0 | gleiche Domain |
| Bestandsauflösung | [('qty_available','&lt;=',0),('type','not in',('service', 'consu'))] | [('qty_available', '&lt;=', 0), ('is_storable', '=', True)] | 449 | 0 | abweichende Domain |
| Zeitbasierte Dienste | [('type', '=', 'service'), ('invoice_policy', '=', 'delivery'), ('service_type', '=', 'timesheet | [('type', '=', 'service'), ('invoice_policy', '=', 'delivery'), ('service_type', '=', 'timesheet | 0 | 0 | gleiche Domain |
| Festpreis-Dienste | [('type', '=', 'service'), ('invoice_policy', '=', 'order'), ('service_type', '=', 'timesheet')] | [('type', '=', 'service'), ('invoice_policy', '=', 'order'), ('service_type', '=', 'timesheet')] | 33 | 0 | gleiche Domain |
| Meilenstein-Dienste | [('type', '=', 'service'), ('invoice_policy', '=', 'delivery'), ('service_type', '=', 'manual')] | [('type', '=', 'service'), ('invoice_policy', '=', 'delivery'), ('service_type', '=', 'manual')] | 0 | 1 | gleiche Domain |
| Dienstleistungen | [('type','=','service')] | [('type','=','service')] | 47 | 6 | gleiche Domain |

Auswertung:

- **Sechs Filter "Service Type ..."** (Consulting, Onlineservice, Software-Solution, Platform,
  Hardware, Förderprojekt): Domain in beiden Systemen identisch auf `product_type_id` und den
  Namen. Treffer Odoo 11: 19 / 314 / 18 / 56 / 3 / 0. Treffer Odoo 18: 0 / 1 / 0 / 0 / 0 / 0
  (nur Testbestand). Ergebnis: derselbe Filter findet dieselben Produkte, solange die sechs
  Produktart-Datensaetze ihre Namen behalten - die Domain vergleicht gegen den **Namen**.
- **Bestandsaufloesung**: Domain unterscheidet sich. Odoo 11
  `[('qty_available','&lt;=',0),('type','not in',('service','consu'))]` findet **449** Produkte -
  faktisch alle ITK-Wert-Produkte mit Bestand kleiner/gleich 0 (der gemeinte Odoo-11-Typ `product`
  hat 0 Produkte, der Filter griff also breiter als beabsichtigt). Odoo 18
  `[('qty_available','&lt;=',0),('is_storable','=',True)]` findet heute **0** (kein Lagerartikel im
  Testbestand) und wuerde nach der Migration die 152 Lagerartikel pruefen. Der Filter findet damit
  **nicht** dieselbe Produktmenge wie in Odoo 11; die Zuordnung `type not in (service,consu)` ->
  `is_storable = True` ist von Anna bestaetigt, aendert aber die Treffermenge.
- **Zeitbasierte Dienste / Festpreis-Dienste / Meilenstein-Dienste**: Domain identisch, aber Odoo 18
  kennt den Odoo-11-Auswahlwert `service_type = 'timesheet'` nicht mehr (Odoo 18 hat nur `manual`).
  Odoo 11: 0 / 33 / 0 Treffer. Odoo 18: 0 / 0 / 1. Die beiden Filter mit `timesheet` koennen in
  Odoo 18 nie treffen; "Meilenstein-Dienste" findet in Odoo 18 ein Produkt, in Odoo 11 keines.
- **Dienstleistungen** `[('type','=','service')]`: Odoo 11 47, Odoo 18 6. Dieser Filter ist der
  einzige, der direkt von der Entscheidung `type` abhaengt (siehe Abschnitt 6).
- Weitere Odoo-18-Filter ohne Odoo-11-Entsprechung: `goods` "Güter" `[('type','=','consu')]`,
  `is_storable` "Lagerverwaltung".

## 4. Gruppierung "Status" / Produktart

| | Odoo 11 | Odoo 18 aktuell |
|---|---|---|
| Feld | `product_type_id` (many2one -> itk_product.product_type) | `product_type_id` (gleiches Modell) |
| Gruppierung | **keine**: in keiner product.template-Ansicht und in keinem der 244 gespeicherten Filter ist `group_by product_type_id` vorhanden; "Status" war in Odoo 11 nur eine **Spalte** der Listenansicht "Product Template Tree ITK" | Gruppierungsfilter "Status" (`context="{'group_by': 'product_type_id'}"`) in der Suchansicht `product.template.search.abo.produkte` (Modul `itk_multifactor`), zusaetzlich Spalte "Status" in der Liste (`itk_product`) |
| Ergebnis | Zaehlung je Produktart nur ueber die Liste bzw. ueber die sechs Filter | Gruppierung erzeugt die Gruppen nach denselben Datensaetzen |

Bewertung: Die Gruppierung ist eine **Odoo-18-Ergaenzung** (von ITK gebaut), keine 1:1-Entsprechung
zu Odoo 11. Fachlich erzeugt sie dieselben Gruppen wie die Odoo-11-Spalte "Status" und die
Odoo-11-Filter, weil dieselbe Relation und dieselben sechs Datensaetze verwendet werden. Sie ist an
denselben Namen gebunden wie die Filter.

## 5. Lagerartikel und `is_storable`

Odoo 11 (Daten): 152 Vorlagen mit `type = consu` (plus 0 mit `type = product`); 90 davon mit
Lagerbewegungen; **alle 152 ohne Produktart**. Die eine Vorlage mit ITK-Typ und Lagerbewegung:
"IFG-Portal jaehrliches Nutzungsentgelt mehr a..." (`type = onlineservice`, 2 Lagerbewegungen) -
Einzelfall.

Odoo 18 (Code, read-only geprueft):

```
stock/models/product.py:704  is_storable = fields.Boolean('Track Inventory', store=True,
                             compute='compute_is_storable', readonly=False)
stock/models/product.py:769  def compute_is_storable(self):
stock/models/product.py:770      self.filtered(lambda t: t.type != 'consu' and t.is_storable)
                                     .write({"is_storable": False})
stock/models/product.py:435  ('is_storable', '=', True)   # Bestandslogik
```

Damit gilt in Odoo 18: Bestandsfuehrung haengt **ausschliesslich** an `is_storable`, und ein
Produkt kann nur dann `is_storable = True` tragen, wenn `type = 'consu'` ist. `product_type_id`
wird im Odoo-18-Kern **uberhaupt nicht** verwendet - der Ausdruck kommt nur in den ITK-Modulen
`itk_product`, `itk_multifactor` und `itk_account_migration` vor; es gibt weder Pflichtfeld noch
Constraint darauf (geprueft per grep). `product_type_id` darf bei Lagerartikeln daher leer bleiben;
das ist der aktuelle Odoo-11-Zustand (alle 152 Lagerartikel ohne Produktart) und in Odoo 18 ohne
Nebenwirkung.

Offener Punkt: Im Odoo-18-Testbestand gibt es **kein** Produkt mit `is_storable = True` und keine
Lagerbewegung. Die Bestandslogik ist deshalb nur statisch (Code/Felddefinition) belegt, nicht mit
einem echten Lagerfall getestet. Ein solcher Test braucht ein Lagerprodukt im Testbestand, das ich
ohne Freigabe nicht anlege.

## 6. Nebenwirkungen einer Aenderung an `type`

Statische Pruefung des Odoo-18-Kerns (nur grep, keine Aenderung):

```
Vergleiche auf type in Odoo-18-Kernmodulen (Treffer):
   sale_project 7 | sale_timesheet 6 | sale_purchase 3 | sale 2 | delivery 2 | mrp 2 |
   repair 2 | stock_landed_costs 2 | pos_sale 2 | itk-Faelle: product 1 | stock 1 |
   purchase 1 | sale_service 1 | website_sale 1
combo-Vergleiche: 25 (product, sale, point_of_sale, website_sale, account, loyalty)
is_storable: stock 36, mrp 23, purchase_stock 18, website_sale_stock 15, stock_account 12, ...
```

Bedeutung:

1. Die Odoo-18-Standardlogik prueft `type` an wenigen, klar benannten Stellen - vor allem
   projekt- und stundenbasierte Dienste (`sale_project`, `sale_timesheet`), Einkauf/Verkauf-Kopplung
   (`sale_purchase`), Lieferung und Lagernebenkosten. Ein Produkt mit `type = 'general'` oder
   `'platform'` wird von diesen Stellen wie ein Nicht-Dienst behandelt - **genau wie in Odoo 11**,
   wo dieselben Werte ebenfalls nicht `service` waren.
2. `is_storable` ist in Odoo 18 unabhaengig von den ITK-Werten, wird aber bei `type != 'consu'`
   zwangsweise auf `False` gesetzt. Eine Zuordnung, die Lagerartikel auf etwas anderes als `consu`
   abbildet, wuerde die Bestandsfuehrung ausschalten.
3. `combo` ist ein Odoo-18-Zusatz (Produktbuendel). Keine Massnahme darf `combo` entfernen; die
   ITK-Auswahl schliesst es nicht aus (gemessen vorhanden).
4. Abonnements und Rechnungen haengen an `recurring_invoice`, `invoice_policy`, `sale_ok`,
   `purchase_ok` und den Belegen selbst - **nicht** an `type` oder `product_type_id`. Eine Aenderung
   an `type` veraendert keine Belegdaten; sie aendert Filterergebnisse, Gruppierungen und die
   Standardlogik (Punkt 1).

## 7. Variantenvergleich (berechnet aus den Odoo-11-Daten)

Beide Varianten betreffen die Zuordnung des Feldes `type`; `product_type_id` bleibt davon
unberuehrt (Regel nach Abschnitt 1/8).

| Kriterium | Variante 1: `type` 1:1 uebernehmen | Variante 2: auf Odoo-18-Logik abbilden (`consu`/`service`), Art in `product_type_id` |
|---|---|---|
| Betroffene Produkte | alle 653 Vorlagen (keine Aenderung der Werte) | 501 Vorlagen mit Dienstleistungswerten werden `service`; 152 Lagerartikel bleiben `consu` (+ `is_storable`) |
| Nur `service` betroffen (Filter "Dienstleistungen") | 47 aktiv (wie Odoo 11) | 497 aktiv - der Filter findet danach 346 verwendete Produkte statt 48 |
| Filter "Service Type ..." (sechs) | unveraendert, 19/314/18/56/3/0 in Odoo 11 | unveraendert (sie haengen an `product_type_id`) |
| Filter "Zeitbasierte/Festpreis-Dienste" | bleiben leer (Odoo 18 kennt `timesheet` nicht) | bleiben leer (bedingen `service_type = 'timesheet'`) |
| Filter "Bestandsaufloesung" | 0 im Testbestand, nach Migration 152 Lagerartikel | gleich |
| Betroffene Lagerartikel | 152 Vorlagen, 90 mit Lagerbewegungen; unveraendert | 152 Vorlagen: `consu` + `is_storable = True` (nur so ist Bestandsfuehrung in Odoo 18 moeglich) |
| Betroffene Rechnungen | keine Datenwirkung (Rechnungszeilen tragen kein `type`) | keine Datenwirkung |
| Betroffene Abonnements | 188 Vorlagen in Abo-Zeilen mit Dienstleistungswert; keine Datenwirkung | keine Datenwirkung, aber diese 188 Produkte gelten dann als Dienste |
| Odoo-18-Funktionen | Standardlogik behandelt `general`/`platform`/... wie in Odoo 11 als Nicht-Dienst; keine Odoo-18-Zusaetze betroffen | projekt-/stundenbasierte Funktionen (`sale_project`, `sale_timesheet`) greifen fuer 497 Produkte statt 47; `combo` und alle anderen Zusaetze bleiben |
| Risiko | Odoo-18-Kerncode erhaelt Werte ausserhalb `consu/service/combo`; im Bestand geprueft: keine Fehler, aber `is_storable` wird fuer diese Werte zwangsweise `False` (Lager unberuehrt) | `type` verliert die Feinheit; Abweichung zum Odoo-11-Filterergebnis "Dienstleistungen" (47 -> 497) |
| Datenlage | `type` und `product_type_id` bleiben wie in Odoo 11 getrennt gepflegt | `type` wird grob, die fachliche Art liegt allein in `product_type_id` |

Keine der beiden Varianten ist umgesetzt; die Entscheidung liegt bei Anna. Aus den Daten spricht
fuer Variante 1, dass Odoo 18 die ITK-Werte bereits zulaesst und Odoo 11 dieselben Produkte
ebenfalls nicht als `service` fuehrte (Filterergebnis bleibt identisch, Standardlogik verhaelt sich
gleich). Fuer Variante 2 spricht, dass die Odoo-18-Standardfunktionen fuer Dienste (Projekt,
Stundenerfassung) dann auf den Dienstleistungsprodukten greifen.

## 8. Entscheidungsmatrix

| Bereich | Odoo 11 | Odoo 18 aktuell | fachlich gleich | Problem | moegliche Loesung | Risiko | Empfehlung |
|---|---|---|---|---|---|---|---|
| `type` (Wertelauf) | 10 Werte, 6 verwendet, Lagerartikel = `consu`/`product` | 10 Werte (ITK + `combo`), `product` fehlt | teilweise: gemeinsame Werte ja, `product` nein | `product` hat keine Entsprechung | `product` (0 Produkte) auf `consu` + `is_storable` | keines (nicht belegt) | so belassen, von Anna bestaetigt |
| `type` (Zuordnung) | sichtbar, inkonsistent gepflegt | unsichtbar, ITK-Auswahl | offen | zwei moegliche Regeln, Auswirkung auf Filter und Dienste | Variante 1 oder 2 | siehe Abschnitt 7 | Entscheidung Anna |
| `product_type_id` | 6 Datensaetze, 413 belegt | 6 Datensaetze, 1 belegt (Testbestand) | ja (Name, Kuerzel, ID 1-6) | keines, solange Namen bleiben | 1:1 ueber Name und ID | Umbenennung wuerde sechs Filter still entwerten | 1:1, aber ausdruecklich noch nicht freigegeben |
| Lagerartikel | 152 `consu`, 0 `product`, 90 mit Bewegungen | kein Lagerartikel im Testbestand | offen (nicht testbar) | Bestandslogik nur statisch belegt | Test mit einem Lagerprodukt nach Freigabe | ohne Test bleibt die Bestandsfuehrung unbelegt | Test nach Freigabe |
| `product_type_id` bei Lagerartikeln | leer (alle 152) | leer | ja | keines | leer lassen | keines (Feld wird vom Kern nicht verwendet) | leer lassen |
| Filter "Service Type ..." | 6 Filter, 416 Treffer | 6 Filter vorhanden, 1 Treffer (Testbestand) | ja | an den Namen gebunden | Namen unveraendert lassen | Umbenennung entwertet die Filter | so belassen |
| Filter "Bestandsaufloesung" | `type not in (service,consu)`, 449 Treffer | `is_storable = True`, 0 Treffer | nein | Treffermenge aendert sich | wie von Anna bestaetigt beibehalten | Auswertungen mit anderer Treffermenge | beibehalten, Abweichung dokumentieren |
| Filter "Zeitbasierte/Festpreis-Dienste" | `service_type='timesheet'`, 0/33 Treffer | Domain identisch, aber `timesheet` fehlt | nein | zwei Filter koennen nie treffen | Domain an Odoo-18-Werte anpassen oder belassen | Anpassung waere eine neue fachliche Regel | Entscheidung Anna |
| Gruppierung "Status" | nicht vorhanden, nur Spalte "Status" | Gruppierung ueber `product_type_id` | Odoo-18-Ergaenzung | keine Entsprechung in Odoo 11 | beibehalten | keines | erhalten |
| Abos, Verkauf, Einkauf | Funktionen unabhaengig von der Produktart | dito | ja | keines | keine Massnahme | keines | keine Aenderung |

## 9. Was ausdruecklich unveraendert bleibt

- Keine Produktdaten, keine Filter, keine Ansichten, keine Zuordnungen geaendert; Modulstand
  unveraendert (18.0.1.17.0 lokal und VM).
- Odoo 11 ausschliesslich lesend gelesen; keine Testdaten angelegt oder hinterlassen.
- Keine Odoo-18-Zusatzfunktion entfernt oder bewertet; `combo`, `is_storable`, die ITK-Filter und
  die Gruppierung "Status" bleiben wie sie sind.
- Abrechnung bleibt IN ARBEIT; keine Abschluss- oder Migrationsbereit-Markierung.

## 10. Textstellen, die dem gemessenen Stand widersprechen (nur benannt, nicht geaendert)

1. `scripts/testmigration_abrechnung.py`, Zeilen 18-23: beschreibt "Odoo 18 kennt nur
   consu/service/combo ... ITK-Werte -> service", waehrend die Funktion `typ_ziel` (Zeilen 72-78)
   die ITK-Werte 1:1 durchreicht und die Odoo-18-Auswahl sie zulaesst.
2. `addons/itk_multifactor/views/itk_product.xml`, Zeilen 28-33: "Die Odoo-11-Service-Type-Filter
   werden bewusst NICHT nachgebaut" - die sechs Filter sind aber in
   `addons/itk_product/views/itk_product.xml` vorhanden (Zeilen 55-60, Session 123).
3. `MIGRATION_READINESS_CHECKLIST.md` und `PROJECT_KNOWLEDGE.md`: an einer Stelle steht noch, die
   Odoo-11-Service-Type-Filter seien nicht nachgebaut und in Odoo 18 leiste das die Gruppierung;
   Abschnitt 3 dieses Berichts belegt das Gegenteil.
4. Die beiden migrierten Testprodukte (O18 224/225) tragen keine Produktart, obwohl ihre
   Odoo-11-Quellen eine haben.

Diese vier Punkte waren reine Text-/Testdatenbefunde. **Am 05.10.2026 bereinigt:** Punkte 1 bis 3
(Modulkopf im Migrationsskript, Kommentar in `itk_multifactor`, Checklist/PROJECT_KNOWLEDGE).
Offen bleibt Punkt 4: die beiden Testprodukte Odoo 18 224/225 tragen keine Produktart, obwohl ihre
Odoo-11-Quellen Onlineservice haben. Sie erhalten sie beim naechsten Testlauf der Migration nach
der jetzt festgelegten Regel (oder auf ausdrueckliche Anweisung einzeln); ich habe sie nicht
angefasst.

## 11. Empfehlung (Entscheidungsvorlage vom 05.10.2026 - durch Annas Entscheidung abgeloest)

1. `type`: Entscheidung bei Anna. Datengrundlage fuer Variante 1 (1:1) und Variante 2 (Abbildung)
   siehe Abschnitt 7; keine der beiden ist umgesetzt.
   **Nachtrag:** entschieden ist Variante 1.
2. `product_type_id`: 1:1 ueber Name und ID ist belegt (6 Datensaetze, gleiche IDs 1-6, keine
   Dubletten) - Freigabe durch Anna steht aus. Voraussetzung fuer die sechs "Service Type ..."-Filter
   ist, dass die Namen unveraendert bleiben.
   **Nachtrag:** freigegeben.
3. Lagerartikel: `product_type_id` leer lassen ist unschaedlich (Feld wird vom Odoo-18-Kern nicht
   verwendet). Vor einer Freigabe sollte ein Lagerprodukt mit `is_storable = True` einmal im
   Odoo-18-Browser geprueft werden - dafuer brauche ich ein Testprodukt, das ich ohne deine
   Freigabe nicht anlege.
   **Nachtrag:** Regel bestaetigt (leer lassen); der Lagerfall im Browser bleibt offen.
4. ITK-DiensteFilter: "Zeitbasierte" und "Festpreis-Dienste" koennen in Odoo 18 nicht treffen
   (`service_type = 'timesheet'` fehlt). Ob die Domains angepasst werden, ist eine fachliche
   Entscheidung.
   **Nachtrag:** offen - die einzige noch anpassungsbeduerftige Stelle
   (`docs/o11-o18-produktart-mapping.md`, Abschnitt 10).
5. Textstellen aus Abschnitt 10 nach Freigabe bereinigen.
   **Nachtrag:** am 05.10.2026 bereinigt (Migrationsskript-Kopf, Kommentar in itk_multifactor,
   Checklist und PROJECT_KNOWLEDGE); offen bleibt nur die Testdatensaetze 224/225 in Odoo 18.
