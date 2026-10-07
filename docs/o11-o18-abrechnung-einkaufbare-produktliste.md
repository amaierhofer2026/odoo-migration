# Menuepunkte Abrechnung > Verkauf/Einkauf > Verkaufbare bzw. Einkaufbare Produkte: Odoo 11 gegen Odoo 18

Session 128 (Einkauf) und Session 129 (Verkauf), 06.10.2026. Auftrag von Anna: den Bereich
vollstaendig selbst durchgehen (Liste, Suche/Filter/Gruppierungen, Formular, Mapping,
Datenbestand, Browser lokal und VM) und Odoo 18 an Odoo 11 angleichen. Odoo 11 diente
ausschliesslich lesend als fachliche Referenz.

**Status des Bereichs: Abrechnung bleibt IN ARBEIT** (keine Abschluss-, Einfrier- oder
Migrationsbereitschaftsaussage). Anna kontrolliert anschliessend selbst im Browser.

Beteiligte Dateien:

    addons/itk_account_migration/views/product_template_list_o11.xml   (umgebaut, Session 128)
    addons/itk_product/views/itk_product.xml                           (Filter ergaenzt, Session 128)
    addons/itk_account_migration/__manifest__.py                       18.0.1.19.0 -> 18.0.1.20.0
    addons/itk_product/__manifest__.py                                 18.0.1.0.4  -> 18.0.1.0.5
    scripts/pruefe_aktion_ansicht_einkauf.py, scripte zur Erhebung siehe Abschnitt 9

## 1. Odoo 11 (read-only gemessen, DB ITK_V1_a)

```
Menue     Abrechnung/Einkauf/Stammdaten/Einkaufbare Produkte (ir.ui.menu 169)
Aktion    226 "Einkaufbare Produkte", res_model product.product,
          view_mode kanban,tree,form, limit 80,
          context {'search_default_filter_to_purchase': 1}
Ansicht   view_id 571 = account.product_product_view_tree (primaere Liste)
```

Spalten der Ansicht 571 in Dokumentreihenfolge (Roharch und zusammengefuehrter Arch):

| Nr | Feld | Beschriftung de_DE | Bemerkung |
|---|---|---|---|
| 1 | `default_code` | Interne Referenz | |
| 2 | `name` | Name | |
| 3 | `attribute_value_ids` | Attribute | `groups="product.group_product_variant"`, unsichtbar |
| 4 | `lst_price` | Verkaufspreis | |
| 5 | `taxes_id` | Steuern (Verkauf) | `widget="many2many_tags"` |
| 6 | `supplier_taxes_id` | Steuern (Einkauf) | `widget="many2many_tags"` |

Der Zwillingsmenuepunkt Abrechnung/Verkauf/Stammdaten/Verkaufbare Produkte (Aktion 225) verwendet
**dieselbe Ansicht 571** und unterscheidet sich nur im Standardfilter
(`search_default_filter_to_sell`).

Datenbestand Odoo 11 (648 Produktvarianten):

| Feld | belegt |
|---|---|
| `taxes_id` | 646 |
| `supplier_taxes_id` | 647 |
| `purchase_ok` (Filter "Kann eingekauft werden") | 646 |
| `sale_ok` | 648 |
| `default_code` | 2 |
| `barcode` | 0 |
| `standard_price` (Kosten) | 6 |
| `product_type_id` | 409 |
| `qty_available` | 0 (kein Lagerbestand im Bestand) |
| `virtual_available` | 82 |
| `product.supplierinfo` (Lieferantenbeziehungen) | 0 Saetze |

Suche (zusammengefuehrter Arch der Suchansicht des Menuepunkts):

* Suchfelder: `name` (mit default_code/name/barcode), `categ_id`, `attribute_value_ids`,
  `product_tmpl_id`, `location_id`, `warehouse_id`, `pricelist_id`
* 22 Filtereintraege, darunter "Kann verkauft werden", "Kann eingekauft werden", "Archiviert",
  "Verfuegbare Produkte" (`qty_available > 0`), "Bestandsaufloesung", "Bestandsreichweite",
  sechs "Service Type ...", drei Dienstarten-Filter, "Veroeffentlicht", drei Aktivitaetsfilter
* **keine** Gruppierungen, keine gespeicherten Favoriten (`ir.filters` = 0)

## 2. Odoo 18 vorher (lokal und VM)

```
Menue     Abrechnung/Einkauf/Einkaufbare Produkte (ir.ui.menu 207)
Aktion    383 account.product_product_action_purchasable, res_model product.template,
          view_mode kanban,list,form,activity,
          context {'search_default_filter_to_purchase': 1}, keine gebundene Ansicht
Angezeigt product.template.product.list (id 860) + stock + stock_account + itk_product
```

Damit zeigte der Menuepunkt die **Odoo-18-Standardliste** statt der Odoo-11-Liste:

* 22 Feldzeilen im Arch, davon 11 sichtbare Spalten in anderer Reihenfolge
  (u. a. Favorit, Name, Interne Referenz, "To multiply by Factor(per 1000)", Verkaufspreis,
  Kosten, Interne Kategorie, Status, Bestandsmenge, Prognostizierter Bestand, Mengeneinheit)
* **keine** Steuerspalten (die Odoo-11-Hauptspalten fehlten in dieser Liste vollstaendig)
* auf der **VM englische Beschriftungen**: Sales Taxes, Purchase Taxes, Quantity On Hand,
  Forecasted Quantity, Unit of Measure, Purchase Unit, Barcode, Product Category, Sales,
  Purchase, # Product Variants, Invoicing Policy, Track Service. Ursache: die deutschen
  Feldbeschreibungen dieser Felder fehlen in der VM-Datenbank (das Repo-Skript
  `scripts/apply_abrechnung_labels.py` muss nach jedem Modul-Upgrade laufen, Regel Anna
  30.09.2026). Die lokale Instanz hatte die deutschen Beschriftungen.

Die in Session 126 angelegte Vererbung `view_product_template_list_o11_spalten` erweiterte die
Ansicht `account.product_template_view_tree` (1023) um Bestands-/ME-Spalten. Sie war
**wirkungslos**: die Aktion 383 benutzt diese Ansicht nie, und die Aktion hatte keine gebundene
Liste. Die damalige Doku-Annahme (Odoo 11 zeige Bestandsmenge/Prognose/ME/Strichcode in dieser
Liste) beruhte auf der Standardliste des Modells, nicht auf der Ansicht der Odoo-11-Aktion.

Suche Odoo 18 vorher: 25 Filter im Odoo-11-Wortlaut (Session 123) plus Odoo-18-Zusaetze
(Favoriten, Warnungen, "Mit Faktor multipliziert", "Aktive Abonnement Produkte", Dienstleistungen/
Produkte/Kombi/Lagerverwaltung) und vier Gruppierungen (Produktart, Produktkategorie, Status,
Mit Faktor multipliziert). **"Verfuegbare Produkte" fehlte** - die Notiz in
`addons/itk_product/views/itk_product.xml`, der Filter sei in Odoo 18 schon vorhanden, war falsch:
der Kernfilter `real_stock_available` haengt an der Suchansicht `product.product_search_form_view`
(Lager-/Variantenmenue) und erscheint in diesem Menuepunkt nicht (im Browser geprueft).

## 3. Odoo 18 nachher (Umsetzung Session 128)

**Liste.** Eigene primaere Liste `product.template.list.itk.o11.produkte`
(`itk_account_migration.view_product_template_list_o11_spalten`, priority 99, kein `inherit_id`)
mit den Odoo-11-Spalten in Odoo-11-Reihenfolge und deutschem Odoo-11-Wortlaut. Die Odoo-18-
Zusatzspalten sind **vorhanden, aber standardmaessig ausgeblendet** (`optional="hide"`) und ueber
die Spaltenauswahl zuschaltbar. Keine Spalte wurde geloescht.

**Bindung.** An die Aktionen gebunden ueber `ir.actions.act_window.view` (je view_mode `list`,
sequence 1): seit Session 128 an Aktion 383 (Einkaufbare Produkte), seit Session 129 auch an
Aktion 382 (Verkaufbare Produkte) - Odoo 11 zeigte in beiden Menuepunkten dieselbe Ansicht 571.
Die Aktionen selbst wurden nicht veraendert; dadurch bleiben alle uebrigen Produktlisten (Lager,
Verkauf > Produkte, Einkauf > Produkte, Abo-Produkte, Preislisten) unberuehrt. Nachweis:
`scripts/pruefe_produktlisten_unveraendert.py` - nur die Aktionen 382 und 383 tragen eine
gebundene Liste.

**Filter.** "Verfuegbare Produkte" (`qty_available > 0`) wurde im Odoo-11-Wortlaut und mit der
Odoo-11-Domain in `addons/itk_product/views/itk_product.xml` ergaenzt
(`itk_real_stock_available`), wie die uebrigen Odoo-11-Filter aus Session 123.

Sichtbare Spalten (Odoo 11 1:1, nicht abwaehlbar):

| Nr | Feld | Beschriftung |
|---|---|---|
| 1 | `default_code` | Interne Referenz |
| 2 | `name` | Name |
| 3 | `list_price` | Verkaufspreis |
| 4 | `taxes_id` | Steuern (Verkauf) |
| 5 | `supplier_taxes_id` | Steuern (Einkauf) |

Zuschaltbare Odoo-18-Zusatzspalten (`optional="hide"`, Beschriftung im Odoo-11-Wortlaut, wo
Odoo 11 das Feld kannte):

| Feld | Beschriftung | Einordnung |
|---|---|---|
| `product_variant_count` | # Produkt Varianten | Odoo-18-Zusatz |
| `categ_id` | Interne Kategorie | Odoo 11 vorhanden, in dessen Liste nicht sichtbar |
| `product_type_id` | Status | ITK-Feld; Odoo 11 nannte es "Product-Type" (Entscheidung Session 123/124 bleibt) |
| `type` | Produktart | Odoo-11-Feld, read-only |
| `standard_price` | Kosten | Odoo-11-Feld |
| `uom_id` | Mengeneinheit | Odoo-11-Feld |
| `uom_po_id` | Einkauf ME | Odoo-11-Feld |
| `barcode` | Strichcode | Odoo-11-Feld |
| `qty_available` | Bestandsmenge | Odoo-11-Feld (in dessen Liste nicht sichtbar) |
| `virtual_available` | Prognostizierter Bestand | Odoo-11-Wortlaut der Variantenliste |
| `responsible_id` | Verantwortlich | Odoo-18-Zusatz |
| `product_tag_ids` | Stichwörter | Odoo-18-Zusatz (Odoo 11 hat das Feld nicht) |
| `is_favorite` | Favorit | Odoo-18-Zusatzfunktion |
| `sale_ok` | Kann verkauft werden | Odoo-11-Feld, in dessen Liste nur Filter |
| `purchase_ok` | Kann eingekauft werden | Odoo-11-Feld, in dessen Liste nur Filter |

Technische Hilfsspalten fuehren Waehrung (`currency_id`, `cost_currency_id`) und Zustand
(`active`, `show_on_hand_qty_status_button`) - sie sind nicht sichtbar, aber fuer die
Geldspalten und die Bestandsfarben notwendig. Das Aktivitaetssymbol der Odoo-18-Standardliste
bleibt erhalten.

## 4. Feld- und Relationsmapping (Liste und Migrationsregel)

| Odoo-11-Feld | Bedeutung | Odoo-18-Zielfeld | Relation / Transformation | Migrationsregel |
|---|---|---|---|---|
| `default_code` | Interne Referenz | `product.template.default_code` | 1:1 (char) | unveraendert uebernehmen |
| `name` | Name | `product.template.name` | 1:1 (jsonb) | unveraendert uebernehmen |
| `lst_price` | Verkaufspreis | `product.template.list_price` | 1:1 (float) | 1:1, nicht aus Preislisten neu berechnen |
| `taxes_id` | Steuern (Verkauf) | `product.template.taxes_id` | m2m `account.tax` | ueber Steuernamen zuordnen, keine Odoo-11-IDs |
| `supplier_taxes_id` | Steuern (Einkauf) | `product.template.supplier_taxes_id` | m2m `account.tax` | wie oben |
| `attribute_value_ids` | Attributwerte | `product.template.attribute_line_ids` | o2m Vorlagen-Attribute | Odoo-11-Bestand: 0 Produkte mit Attributen; keine Zuordnung noetig |
| `qty_available`, `virtual_available` | Bestand, Prognose | gleichnamige berechnete Felder | berechnet aus Lagerbewegungen | nicht migrieren, entstehen aus den Lagerbewegungen |
| `uom_id`, `uom_po_id` | Mengeneinheit, Einkauf ME | `product.template.uom_id`, `uom_po_id` | m2o `uom.uom` | ueber den Namen der Einheit zuordnen |
| `barcode` | Strichcode | `product.template.barcode` | 1:1 (char) | unveraendert (Odoo-11-Bestand: 0 belegt) |
| `standard_price` | Kosten | `product.template.standard_price` | 1:1 (float) | 1:1 |
| `categ_id` | Interne Kategorie | `product.template.categ_id` | m2o `product.category` | ueber Kategoriepfad/Namen |
| `type` | Produktart | `product.template.type` + `is_storable` | selection | Entscheidung aus Session 123/124 bleibt unveraendert |
| `product_type_id` | ITK-Produkttyp | `product.template.product_type_id` (itk_product) | m2o `itk_product.product_type` | Entscheidung aus Session 116-124 bleibt unveraendert |
| Lieferantenbeziehungen (`seller_ids`) | Lieferanten | `product.supplierinfo` | o2m | Odoo-11-Bestand: 0 Saetze - keine Daten, Struktur vorhanden |
| Preislistenregeln (`item_ids`) | Preiskalkulation | `product.pricelist.item` | siehe Reiter "Verkauf" | Regeln ueber Preislisten-/Produktnamen, keine IDs blind uebernehmen |

Die bereits getroffenen Entscheidungen zu `type`, `product_type_id` und `is_storable` wurden
**nicht** angetastet. Keine Dummyfelder: jede Spalte der Liste ist ein echtes Feld mit echter
Relation und echten Werten (Steuern 646/647 belegt, Verkaufspreis 648 belegt).

## 5. Filter und Gruppierungen (Vergleich)

| Odoo 11 | Odoo 18 nachher | Bewertung |
|---|---|---|
| Kann verkauft werden (`sale_ok`) | Kann verkauft werden (`sale_ok`) | gleich (Wortlaut und Domain) |
| Kann eingekauft werden (`purchase_ok = 1`) | Kann eingekauft werden (`purchase_ok = True`) | **gleich** - Standardfilter des Menuepunkts, im Browser geprueft (9 von 9 einkaufbaren Vorlagen lokal, 8 von 8 auf der VM) |
| Produkte (`type in (consu, product)`) | Produkte (`type = consu`) | fachlich gleich: in Odoo 18 sind Verbrauchs- und Lagerartikel beide `consu`; `is_storable` trennt sie. Zusatz "Lagerverwaltung" (`is_storable`) ist ein Odoo-18-Zusatz |
| Verfuegbare Produkte (`qty_available > 0`) | **ergaenzt** (Session 128) | fehlte; in Odoo 11 ohne Treffer, jetzt wieder vorhanden |
| Bestandsaufloesung, Bestandsreichweite | vorhanden (Session 123) | gleich |
| sechs "Service Type ...", Zeitbasierte/Festpreis-/Meilenstein-Dienste | vorhanden (Session 123) | gleich |
| Archiviert | vorhanden | gleich |
| Veroeffentlicht (`website_published`) | nicht nachgebaut | Abweichung: Feld existiert in Odoo 18 nicht (Website-Modul nicht installiert), in Odoo 11 0 Treffer |
| — | Dienstleistungen, Kombi, Lagerverwaltung, Favoriten, Warnungen, Mit Faktor multipliziert, Aktive Abonnement Produkte, drei Aktivitaetsfilter | Odoo-18-Zusatzfunktionen, bleiben erhalten |
| keine Gruppierungen | Produktart, Produktkategorie, Status, Mit Faktor multipliziert | Odoo-18-Zusatzfunktionen, bleiben erhalten |
| keine Favoriten (`ir.filters` 0) | Favoritenfunktion vorhanden | Odoo-18-Zusatzfunktion, keine Migration noetig |

Nicht nachgebaut (dokumentierte Abweichung): die Odoo-11-Suchfelder `product_tmpl_id`,
`location_id`, `warehouse_id`, `pricelist_id`. `product_tmpl_id` entfaellt durch das Vorlagenmodell,
`location_id`/`warehouse_id` sind in Odoo 18 nicht gespeicherte Suchfelder der Lager-Suchansicht
und dort weiterhin vorhanden, ein Feld `pricelist_id` gibt es auf `product.template` nicht
(Preislisten haengen an `product.pricelist.item`).

## 6. Formularpruefung aus dieser Liste (echter Browser)

Aus der Liste geoeffnet wurden eine Dienstleistung und ein Warenprodukt (beide einkaufbar):

* Reiter: Allgemeine Informationen, Attribute & Varianten, Verkauf, Einkauf, Lager, Abrechnung,
  Notizen (7) - wie in Session 126 abgenommen
* Smart Buttons: Regeln Preislisten, Dokumente, "Eingekauft", "Verkauft", "Eingang/Ausgang"
* Beschriftungen deutsch im Odoo-11-Wortlaut sichtbar: Interne Referenz, Interne Kategorie,
  Strichcode, Verkaufspreis, Kosten, Produktart, Verantwortlich, Einkauf ME, Steuern (Verkauf),
  Steuern (Einkauf) (Reiter Abrechnung)
* **keine** englische Beschriftung im Formular (weder lokal noch VM)
* Felder vorhanden: `default_code`, `barcode`, `uom_id`, `uom_po_id`, `standard_price`,
  `list_price`, `categ_id`, `taxes_id`, `supplier_taxes_id`
* Bearbeitungsmodus: das Formular oeffnet bearbeitbar (`o_form_editable`); ein temporaeres
  Testprodukt wurde angelegt, der Verkaufspreis im Formular geaendert (66,00 -> 77,50), gespeichert
  und der Wert in der Datenbank geprueft; danach wurde das Testprodukt geloescht
  (Bestand vorher == nachher)
* Mengeneinheit: Odoo 18 zeigt die Verkaufs-Mengeneinheit im Formular als Einheit am Preis
  ("pro Einheit(en)"), im Reiter Einkauf als "Einkauf ME" - Odoo-11-Wortlaut der Liste bleibt
  "Mengeneinheit"

## 7. Testmigrationsregeln und diese Produktfelder (Pruefung, keine Migration)

Geprueft wurde `scripts/testmigration_abrechnung.py` (Plan-Lauf, schreibt nichts) gegen
`docs/o11-o18-testmigration-regel.md`. Die Regel uebertraegt Produkte nur so weit, wie die
gewaehlten Belegzeilen sie brauchen (hoechstens 6 Produkte):

| Feld | in Odoo 11 belegt | in der Testmigrationsregel | Bewertung |
|---|---|---|---|
| `name` | 648/648 | ja | uebernommen |
| `type` (+ `is_storable`) | 648/648 | ja (Variante 1) | uebernommen |
| `list_price` | 648/648 | ja | uebernommen |
| `sale_ok`, `purchase_ok` | 648/646 | ja | uebernommen |
| `invoice_policy` | 648/648 | ja | uebernommen |
| `product_type_id` | 409/648 | ja (ueber den Namen) | uebernommen |
| `taxes_id` | 646/648 | ja (ueber den Steuernamen) | uebernommen |
| **`supplier_taxes_id`** | **647/648** | **nein** | **Luecke fuer eine Produktmigration** |
| `default_code` | 2/648 | nein | Luecke (klein, 2 Produkte) |
| `uom_id` / `uom_po_id` | 648/648 | nein | Luecke |
| `categ_id` | 648/648 | nein | Luecke |
| `standard_price` | 6/648 | nein | Luecke (klein) |
| `barcode` | 0/648 | nein | kein Bedarf |
| Lieferanten (`seller_ids`) | 0 Saetze | nein | strukturell vorhanden, keine Daten |

Fuer die Testmigration der Rechnungen genuegt die Regel (dort ist nur `taxes_id` noetig). Fuer die
spaetere echte Produktmigration fehlen `supplier_taxes_id`, `default_code`, `uom_id`/`uom_po_id`,
`categ_id` und `standard_price` - das ist ein Befund, **keine** durchgefuehrte Erweiterung. Die
Regel wird erst nach Freigabe von Anna erweitert; eine echte Datenmigration fand nicht statt.

**Nachtrag Session 129:** Die Regel wurde auf Annas Auftrag erweitert (siehe
`docs/o11-o18-testmigration-regel.md`, Abschnitt "Produktfelder"): `default_code` und
`standard_price` 1:1, `uom_id`/`uom_po_id` ueber den Einheitennamen, `categ_id` ueber den
Kategorienamen, `taxes_id`/`supplier_taxes_id` in vier Stufen (gleicher Name, Odoo-11-
Beschreibungstext als Odoo-18-Name, eindeutiger Satz plus Verwendung, sonst Abbruch).
Vorlauf (`--plan`, schreibt nichts) lokal und VM: 11 Produkte der ausgewaehlten Belege, Steuern
11/11 und Einheiten 11/11 aufloesbar, Kategorien 2/11 (9 fehlen im Testbestand).
Vorlaufprotokolle: `Desktop/Odoo18-Abnahme-Session129/testmigration_vorlauf/plan_lokal.txt`
und `plan_vm.txt`.

## 8. Abnahme

```
RPC/Arch-Pruefung   scripts/pruefe_aktion_ansicht_einkauf.py, scripts/erhebe_einkaufbare_produkte.py
Browser-Abnahme     scripts/browser_einkaufbare_produkte.py lokal|vm   (echter Chrome)
Bilder + Ergebnis   Desktop/Odoo18-Abnahme-Session128/einkaufbare_produkte/<lokal|vm>/
```

Ergebnis (siehe Abschnitt 8 des Session-Abschlussberichts): lokal und VM jeweils ohne
Fehlermeldung, Bestand vorher == nachher, keine Testdaten zurueckgeblieben.

## 8. Offene Punkte

1. **Produktkategorien fehlen im Testbestand (Befund Session 129):** Die Odoo-11-Produkte fuehren
   eigene Kategorien (z. B. "Amtssignatur, E-Abfertigung, E-Postfächer", "Nutzungsentgelt",
   "Dienstleistungspauschale"); die Odoo-18-Testinstanz hat nur All/Expenses/Saleable. Im
   Vorlauf der Testmigration lassen sich deshalb 9 von 11 Produkten keine Kategorie zuordnen.
   Die Kategorieanlage ist ein eigener Stammdatenschritt und braucht Annas Freigabe - es wurden
   **keine** Kategorien angelegt.
2. **Modell der Liste:** Odoo 11 listet Varianten (`product.product`, eine Zeile je Variante),
   Odoo 18 Vorlagen (`product.template`). Bestehende Entscheidung aus Session 126, unveraendert.
3. **Website-Gruppe** (`public_categ_ids` usw.): nur mit `website_sale` nachbaubar, in Odoo 11
   ohne Daten - unveraendert wie im Reiter "Verkauf" dokumentiert.
4. **Feldbeschreibungen lokal/VM:** die VM-Datenbank fuehrte fuer mehrere Produktfelder englische
   Beschreibungen. Nach jedem Modul-Upgrade muessen `scripts/apply_abrechnung_labels.py` (und die
   Ansichtspruefungen) laufen - das macht `scripts/upgrade_modules.py` automatisch. Die Liste
   setzt ihre Wortlaute zusaetzlich selbst im Repo (`string="..."`), damit die sichtbare Liste
   unabhaengig von den Datenbank-Slots stimmt.

## 9. Status

**Abrechnung bleibt IN ARBEIT.** Keine Abschlussmarkierung, kein Einfrieren, keine
Migrationsbereitschaft fuer diesen Bereich.
