# ITK-Produktfilter in Odoo 11 - Analyse und Auswirkungen in Odoo 18

Stand: 02.10.2026. Nur lesend ermittelt aus Odoo 11 (Produktion) und Odoo 18 (Test-VM).
Grundlage: Suchansicht product.template in Odoo 11, Feldabfragen und Zaehlungen.
Ausdruecklich ohne Entscheidung - die Entscheidung trifft Anna.

## 1. Funktion in Odoo 11

Die Produktliste hat neben den Standardfiltern zusaetzliche Filter aus ITK-Zusatzmodulen.
Sie greifen auf zwei Felder zu:

- `product_type_id` (Odoo 11 sichtbar "Product-Type"): Auswahlfeld mit den Werten
  Consulting, Onlineservice, Software-Lösung, Plattform, Hardware, Förderprojekt.
- `invoice_policy` (Odoo 11 "Fakturierungsregel"): Abrechnung nach Menge, nach
  Leistungszeitraum (zeitbasiert) oder nach Meilensteinen.
- dazu Standardfelder: `type`, `sale_ok`, `purchase_ok`, `qty_available`, `website_published`.

## 2. Tatsaechliche Nutzung in Odoo 11 (649 Produkte)

| Filter | Domain | Treffer |
|---|---|---|
| Service Type Onlineservice | product_type_id = Onlineservice | 314 |
| Service Type Platform | product_type_id = Plattform | 56 |
| Service Type Consulting | product_type_id = Consulting | 19 |
| Service Type Software-Solution | product_type_id = Software-Lösung | 18 |
| Service Type Hardware | product_type_id = Hardware | 3 |
| Service Type Förderprojekt | product_type_id = Förderprojekt | 0 |
| Festpreis-Dienste | type=service und invoice_policy=Festpreis | 33 |
| Zeitbasierte Dienste | type=service und invoice_policy=Zeitbasiert | 0 |
| Meilenstein-Dienste | type=service und invoice_policy=Meilenstein | 0 |
| Bestandsauflösung | qty_available <= 0 und type nicht Dienstleistung | 449 |
| Verfuegbare Produkte | qty_available > 0 | 0 |
| Bestandsreichweite | qty_available < 0 | 0 |
| Veroeffentlicht | website_published = True | 0 |
| Kann verkauft werden | sale_ok = 1 | 649 |
| Kann eingekauft werden | purchase_ok = 1 | 647 |
| Archiviert | active = False | 4 |
| Produkte | type in (consu, product) | 152 |
| Abonnement Produkte / Produkte | recurring_invoice True/False | 333 / 316 |

Feldbelegung: `product_type_id` ist bei 410 von 649 Produkten gefuellt,
`invoice_policy`, `service_type`, `type`, `sale_ok` bei allen, `purchase_ok` bei 647,
`qty_available` und `website_published` bei keinem Produkt (kein Lagerbestand, kein Website-Modul).

## 3. Betroffene Datensaetze

- product_type_id: 410 Produkte (davon Onlineservice 314, Plattform 56, Consulting 19,
  Software-Lösung 18, Hardware 3; Foerderprojekt 0).
- invoice_policy = Festpreis: 33 Produkte; Zeitbasiert und Meilenstein: 0 Produkte.
- Bestandsfilter: 449 Produkte wuerden unter "Bestandsaufloesung" erscheinen, obwohl kein
  Produkt Lagerbestand fuehrt (qty_available nie belegt) - der Filter ist faktisch wirkungslos.

## 4. Entsprechendes Verhalten in Odoo 18

- Feld `product_type_id` ist vorhanden, sichtbar als "Produkttyp" (Auswahlfeld; Werte im
  Testbestand noch nicht gepflegt).
- Feld `invoice_policy` ist vorhanden, sichtbar als "Abrechnungspolitik".
- Feld `service_type` ist vorhanden ("Dienstleistung verfolgen").
- Feld `qty_available` ist vorhanden ("Vorraetige Menge"), `website_published` fehlt
  (Website-Modul nicht installiert) - in Odoo 11 ohnehin 0 belegt.
- Vorhandene Filter in Odoo 18 derzeit: Dienstleistungen, Gueter, Kombi, Lagerverwaltung,
  Verkauf, Einkauf, Favoriten, Warnungen, Archiviert, Mit Faktor multipliziert,
  Aktive Abonnement Produkte, Produkte, Abonnement Produkte, Aktivitaetsfilter.
  Die ITK-Service-Typ-Filter und die Abrechnungspolitik-Filter fehlen dort.

## 5. Auswirkungen

Beibehaltung (Filter in Odoo 18 nachbauen, sichtbar mit Odoo-11-Wortlaut)
- Aufwand: gering, die Felder existieren in Odoo 18; es sind reine Filtereintraege in der
  Suchansicht (Domains product_type_id / invoice_policy), keine Modellaenderung.
- Nutzen: 410 Produkte bleiben so filterbar wie in Odoo 11; die Einarbeitung fuer Anwender
  bleibt gleich.
- Risiko: gering; die Filter zeigen in Odoo 18 erst dann Treffer, wenn `product_type_id`
  migriert bzw. gepflegt wird.

Anpassung (nur die tatsaechlich genutzten Filter nachbauen)
- Aufwand: gering, betrifft Service Type Onlineservice/Platform/Consulting/Software-Lösung/
  Hardware und Festpreis-Dienste.
- Die Filter Foerderprojekt, Zeitbasierte Dienste, Meilenstein-Dienste, Verfuegbare Produkte,
  Bestandsreichweite und Veroeffentlicht haben 0 Treffer in Odoo 11 und koennten entfallen.
- Nutzen: schlanke Filterliste, keine funktionslosen Eintraege.

Weglassen (nur die Odoo-18-Standardfilter nutzen)
- Folge: 410 Produkte mit Produkttyp sind in Odoo 18 nicht mehr ueber Produkttyp filterbar;
  "Festpreis-Dienste" (33 Produkte) ebenfalls nicht.
- Die Standardfilter (Dienstleistungen, Gueter, Verkauf, Einkauf, Archiviert) bleiben.
- Aufwand: keiner, aber eine sichtbare Funktionseinbusse gegenueber Odoo 11.

## 6. Entscheidung (05.10.2026, Session 123)

Anna entscheidet: **vollstaendiger Nachbau** - alle ITK-Filter werden in Odoo 18 sichtbar
gemacht, auch die sechs mit 0 Treffern in Odoo 11 (Förderprojekt, Zeitbasierte Dienste,
Meilenstein-Dienste, Verfügbare Produkte, Bestandsreichweite, Veröffentlicht waren es
urspruenglich; "Verfügbare Produkte" existierte in Odoo 18 bereits identisch).

Umgesetzt in `addons/itk_product/views/itk_product.xml`, Record
`view_product_template_search_itk_produktfilter` (geerbte Suchansicht
`product.product_template_search_view`, mode extension, priority 17). Keine Modell- und
keine Datenänderung, nur Filtereintraege. Wortlaut und Domaenen 1:1 aus Odoo 11,
interne Namen mit `itk_`-Praefix gegen Namenskollisionen mit Odoo-18-Standardfiltern:

| Sichtbarer Wortlaut (Odoo 11) | Domain in Odoo 18 |
|---|---|
| Service Type Consulting | `[('product_type_id', '=', 'Consulting')]` |
| Service Type Onlineservice | `[('product_type_id', '=', 'Onlineservice')]` |
| Service Type Software-Solution | `[('product_type_id', '=', 'Software-Lösung')]` |
| Service Type Platform | `[('product_type_id', '=', 'Plattform')]` |
| Service Type Hardware | `[('product_type_id', '=', 'Hardware')]` |
| Service Type Förderprojekt | `[('product_type_id', '=', 'Förderprojekt')]` |
| Zeitbasierte Dienste | `[('type','=','service'), ('invoice_policy','=','delivery'), ('service_type','=','timesheet')]` |
| Festpreis-Dienste | `[('type','=','service'), ('invoice_policy','=','order'), ('service_type','=','timesheet')]` |
| Meilenstein-Dienste | `[('type','=','service'), ('invoice_policy','=','delivery'), ('service_type','=','manual')]` |
| Bestandsauflösung | `[('qty_available','<=',0), ('is_storable','=',True)]` |
| Bestandsreichweite | `[('qty_available','<',0)]` |

Zwei Festlegungen dabei:

- **Bestandsauflösung**: Odoo 11 filterte mit `type not in ('service','consu')` und meinte damit
  den damaligen Typ `product` (Lagerartikel). Den Typ gibt es in Odoo 18 nicht mehr, Entsprechung
  ist `is_storable = True`. Von Anna bestaetigt.
- **Veröffentlicht** (`website_published`) wird **nicht** nachgebaut: Das Feld existiert in
  Odoo 18 nicht (Website-Modul nicht installiert), der Filter hatte in Odoo 11 ohnehin 0 Treffer.
  Im Code als Kommentar begruendet.

Zusaetzlich wurden die drei Odoo-18-Standardfilter des Produktsuchmenues auf den Odoo-11-Wortlaut
zurueckgestellt (Domains unveraendert): `filter_to_sell` "Verkauf" -> "Kann verkauft werden",
`filter_to_purchase` "Einkauf" -> "Kann eingekauft werden", `goods` "Güter" -> "Produkte".

Im Produktformular wurde die Position angeglichen: `product_type_id` steht wieder am Anfang der
Gruppe Allgemeine Informationen (in Odoo 11 direkt hinter "Produktart"; "Produktart" ist in
Odoo 18 unsichtbar, das Feld ist dadurch die erste Zeile). Vorher stand es am Ende der Gruppe.
Die ITK-Gruppenueberschrift "Product-Typ" ueber dem Feld ist entfernt - Odoo 11 hatte dort keine,
in Odoo 18 wurde sie durch die Grossschreibung der Gruppentitel als doppelte Beschriftung
("PRODUKT-TYP" ueber "Product-Type") sichtbar.

Nachweis: 11 Filter per RPC in `product.template` und `product.product` vorhanden (wie in
Odoo 11), alle Domaenen laufen fehlerfrei; im echten Browser auf der VM angesehen
(`produkt_filter_vm.png`, `produkt_formular_vm.png`, Session 123).
