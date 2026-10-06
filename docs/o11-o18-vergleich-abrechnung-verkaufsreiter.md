# Odoo 11 -> Odoo 18: Reiter "Verkauf" im Produktformular

Stand: 06.10.2026 (Session 127). Referenz ist Odoo 11 (read-only gemessen, ITK_V1_a).
Abrechnung bleibt IN ARBEIT - dieses Dokument ist keine Abnahme- oder Freigabeerklaerung.

## 1. Auftrag

Der Reiter "Verkauf" (Abrechnung -> Verkauf -> Verkaufbare Produkte -> Produktformular) war in
Odoo 18 nicht ausreichend nah an Odoo 11. Gefordert war feldweises, funktionales und visuelles
Angleichen bei vollstaendiger Erhaltung der Odoo-18-Zusatzfunktionen, inklusive Migrationsregeln
und Browser-Abnahme (lokal und VM, Lese- und Bearbeitungsmodus).

## 2. Sollzustand Odoo 11 (gemessen)

Ansicht `product.template` (Odoo 11, Formular), Seite `name="sales"` (`string="Verkauf"`,
sichtbar wenn `sale_ok` oder `recurring_invoice`):

| Reihenfolge | Element | Inhalt |
| --- | --- | --- |
| 1 | `div name="pricelist_item"` | `separator string="Preiskalkulation"` + Feld `item_ids` (nolabel, context `default_base=list_price`, `default_applied_on=1_product`) |
| 2 | `group name="sale"` > `group name="website"` (`string="Website"`) | `website_url`, `public_categ_ids` (eCommerce-Kategorien), `alternative_product_ids`, `accessory_product_ids`, `inventory_availability`, `available_threshold`, `custom_message`, `website_style_ids` |
| 3 | `group name="email_template_and_project"` | leer (Modul `website_sale_options`/Projekt nicht aktiv) |
| 4 | `group name="subscription"` > `group` | `recurring_invoice` (nur wenn `type = service`), `subscription_template_id` (nur wenn `recurring_invoice`) |

Belegung der Felder in Odoo 11 (653 Vorlagen, davon 649 aktiv):

| Feld | Belegung | Bemerkung |
| --- | --- | --- |
| `item_ids` (Preislisten-Positionen) | 321 Vorlagen, 1.469 Regeln mit Produktbezug | `compute_price`: formula 1003, fixed 460, percentage 6; `price_discount` 951, `fixed_price` 448, `min_quantity` 1, Start-/Enddatum praktisch ungenutzt |
| `subscription_template_id` | 294 | Abo-Vorlage je Produkt |
| `recurring_invoice` | 337 | Abo-Produkt |
| `expense_policy` | 653 | alle auf Standardwert `no` (Feld ist im Odoo-11-Formular nicht sichtbar) |
| `list_price`, `taxes_id` | 610 / 651 | Preis und Steuern |
| `public_categ_ids`, `alternative_product_ids`, `accessory_product_ids`, `custom_message`, `website_published` | 0 | Website-Gruppe ohne Daten |
| `inventory_availability` | 653 | alle `never` (Standardwert) |
| `available_threshold` | 497 | 5,0 (Standardwert), 156 x 0,0 |

Preislistenregeln gesamt in Odoo 11: 1.872; davon 403 ohne Produktbezug (Kategorie-, globale oder
Variantenregeln) - diese gehoeren zur Preisliste, nicht zur Produktvorlage.

## 3. Zustand Odoo 18 vorher / nachher

| Element | Odoo 18 vorher | Odoo 18 nachher |
| --- | --- | --- |
| Preiskalkulation | fehlte vollstaendig (Regeln nur ueber Smart Button "Regeln Preislisten") | Abschnitt "Preiskalkulation" mit editierbarer Regelliste, Odoo-11-Spalten |
| Website-Gruppe | fehlte (Felder existieren nur mit `website_sale`) | unveraendert nicht vorhanden, dokumentierte Abweichung (Abschnitt 5) |
| Abonnement (Vorlage) | Gruppe `subscription` ohne Titel mit `subscription_template_id` | unveraendert (Reihenfolge wie Odoo 11: nach den uebrigen Gruppen) |
| Upselling & Cross-Selling (`optional_product_ids`) | vorhanden | erhalten |
| Weitere Informationen (`product_tag_ids`) | vorhanden | erhalten |
| Ausgabe (`expense_policy`) | vorhanden (nur wenn `visible_expense_policy`) | erhalten, Odoo-18-Standard bleibt |
| Smart Button "Regeln Preislisten" | vorhanden | erhalten (nicht abgeschaltet) |

Technische Umsetzung:

* `itk_product`: neues Feld `item_ids` (`One2many('product.pricelist.item', 'product_tmpl_id')`,
  Beschriftung "Preislisten-Positionen") - gleicher Name und gleiche Relation wie in Odoo 11,
  deshalb migrationsfaehig. Version 18.0.1.0.4.
* `itk_account_migration`: Vererbung des Reiters "Verkauf" - Abschnitt "Preiskalkulation" vor der
  Gruppe "Upselling & Cross-Selling", Regelliste mit den Spalten Preisliste, Ermittle Preis,
  Festpreis, Min. Bestellmenge, Startdatum, Enddatum (weitere Spalten ueber die
  Spaltenauswahl zuschaltbar). Version 18.0.1.18.0.

## 4. Feldweise Zuordnung und Migrationsregel

| Odoo-11-Feld | Odoo-18-Zielfeld | Transformationsregel | Beziehung/ID-Regel | Pruefung |
| --- | --- | --- | --- | --- |
| `item_ids[].pricelist_id` | `product.pricelist.item.pricelist_id` | Preisliste ueber ihren Namen in Odoo 18 suchen (in Odoo 11 heisst sie gleich); Regel der gefundenen Preisliste zuordnen | keine Odoo-11-ID uebernehmen | Anzahl Regeln je Preisliste O11/O18 |
| `item_ids[].product_tmpl_id` | `product.pricelist.item.product_tmpl_id` | auf die migrierte Produktvorlage setzen (Zuordnung ueber `default_code`/Name der Vorlage) | Produkt-ID neu, nicht aus Odoo 11 | Anzahl Regeln je Produktvorlage |
| `item_ids[].applied_on` | `product.pricelist.item.applied_on` | 1:1 (`3_global`, `2_product_category`, `1_product`, `0_product_variant`) | - | Verteilung O11/O18 |
| `item_ids[].compute_price` | `product.pricelist.item.compute_price` | 1:1 (`fixed`, `percentage`, `formula`) | - | Verteilung formula/fixed/percentage |
| `item_ids[].base` | `product.pricelist.item.base` | 1:1 (`list_price`, `standard_price`, `pricelist`) | - | Stichproben |
| `item_ids[].fixed_price` | `product.pricelist.item.fixed_price` | 1:1 | - | Stichproben (448 belegt) |
| `item_ids[].percent_price` | `product.pricelist.item.percent_price` | 1:1 (Dezimalwert 0-100) | - | Stichproben |
| `item_ids[].price_discount` | `product.pricelist.item.price_discount` | 1:1 (Formelrabatt) | - | Stichproben (951 belegt) |
| `item_ids[].price_surcharge`, `price_round` | gleichnamige Odoo-18-Felder | 1:1 | - | Stichproben |
| `item_ids[].min_quantity` | `product.pricelist.item.min_quantity` | Typwechsel ganzzahlig -> Dezimal (Wert bleibt) | - | Wertvergleich je Regel |
| `item_ids[].date_start`, `date_end` | `product.pricelist.item.date_start`, `date_end` | Typwechsel Datum -> Datum/Uhrzeit, Uhrzeit 00:00:00 | - | Wertvergleich |
| `item_ids[].currency_id`, `company_id` | gleichnamige Odoo-18-Felder | ueber Name bzw. Waehrung des Unternehmens aufloesen | keine ID-Uebernahme | Stichproben |
| `item_ids[].name` | `product.pricelist.item.name` | Text uebernehmen (Odoo 18 erzeugt sonst einen Standardnamen) | - | Stichproben |
| `subscription_template_id` | `sale.subscription.template.subscription_template_id` (Feld `subscription_template_id`) | Abo-Vorlage ueber ihren Namen zuordnen; Vorlagen vorher in Odoo 18 anlegen/pruefen | keine ID-Uebernahme | 294 Belegungen wiederfinden |
| `recurring_invoice` | `product.template.recurring_invoice` | 1:1 (Boolean) | - | 337 Belegungen |
| `expense_policy` | `product.template.expense_policy` | 1:1 (Auswahl); alle Odoo-11-Werte sind `no` | - | 653 Werte |
| `invoice_policy` (Abrechnung) | `product.template.invoice_policy` | 1:1 - bereits umgesetzt (Reiter "Abrechnung") | - | siehe Vergleichsmatrix Abrechnung |
| `list_price` | `product.template.list_price` | 1:1 aus dem Odoo-11-Speicherwert; **nicht** aus den Regeln neu berechnen (Odoo 11 fuehrt `list_price` als berechneten und gespeicherten Wert) | - | 610 Werte |
| `public_categ_ids`, `website_published`, `website_style_ids`, `custom_message` | kein Odoo-18-Zielfeld (Modul `website_sale` nicht installiert) | keine Migration - in Odoo 11 ohne Daten | - | 0 Belegungen in Odoo 11 |
| `alternative_product_ids`, `accessory_product_ids` | fachlicher Nachfolger `product.template.optional_product_ids` (Odoo-18-Zusatz, erhalten) | keine Migration noetig (0 Belegungen); falls spaeter Daten auftauchen: Beziehungen ueber Namen auf `optional_product_ids` abbilden | keine ID-Uebernahme | 0 Belegungen in Odoo 11 |
| `inventory_availability`, `available_threshold` | kein Odoo-18-Zielfeld | keine Migration (nur Odoo-11-Standardwerte `never` / 5,0) | - | Verteilung 653 / 497 |

Grundsaetze: berechnete Odoo-18-Felder werden nicht direkt beschrieben, IDs werden nie blind
uebernommen, jede Beziehung wird ueber Name/Schluessel aufgeloest.

## 5. Abweichungen (bewusst, nicht nachgebaut)

1. **Website-Gruppe aus Odoo 11 fehlt weiter.** Die Felder `public_categ_ids`,
   `alternative_product_ids`, `accessory_product_ids`, `inventory_availability`,
   `available_threshold`, `custom_message`, `website_published` existieren in Odoo 18 nur mit dem
   Modul `website_sale`; das ist nicht installiert. In Odoo 11 sind diese Felder leer
   (Ausnahme: zwei Felder mit Standardwerten). Es wurden bewusst keine Dummy-Felder gebaut.
2. **`recurring_invoice` erscheint nur einmal.** Odoo 11 zeigte das Feld zweimal (Reiter
   "Allgemeine Informationen" und Reiter "Verkauf", dort nur bei `type = service`). Odoo 18 zeigt
   das Abo-Kennzeichen weiterhin im Reiter "Allgemeine Informationen"; im Reiter "Verkauf" steht
   wie von Ihnen beschrieben nur die Abo-Vorlage.
3. **Gruppentitel "Upselling & Cross-Selling" bleibt englisch.** Der Titel stammt aus Odoo 18
   (`sale`), die deutsche Uebersetzung von Odoo enthaelt die Zeichenkette nicht. Ein deutscher
   Titel ("Zusatzverkaeufe") waere moeglich - bitte entscheiden, damit kein Odoo-18-Wortlaut
   eigenmaechtig ersetzt wird.
4. **`expense_policy` erscheint nur, wenn Odoo 18 es zulaesst** (`visible_expense_policy`); das
   ist Odoo-18-Standardlogik und wurde nicht veraendert.
5. **Regeln ohne Produktbezug** (403 in Odoo 11, Kategorie-/Global-/Variantenregeln) erscheinen
   nicht am Produkt, sondern an der jeweiligen Preisliste - sie sind Teil der
   Preislisten-Migration, nicht dieses Reiters.

## 6. Browser-Abnahme

Skript `scripts/browser_verkauf_reiter_abnahme.py` (echter Chrome, Reiter "Verkauf",
Produkt mit bestehender Preislistenregel, zusaetzlich Abo-Produkt und Bearbeitungsmodus):

| Instanz | Ergebnis | Bilder |
| --- | --- | --- |
| lokal (Odoo 18, odoo18_test) | 18 OK / 0 FEHL | `Desktop/Odoo18-Abnahme-Session126/verkauf_reiter/lokal/` |
| VM (k001959vsx.ipax.at, odoo18_test) | 18 OK / 0 FEHL | `Desktop/Odoo18-Abnahme-Session126/verkauf_reiter/vm/` |

Geprueft: Abschnitt "Preiskalkulation" und Reihenfolge im Reiter, Spalten und Werte der Regelliste,
Smart Button "Regeln Preislisten", Odoo-18-Zusaetze (Optionale Produkte, Stichwoerter, Ausgabe),
Abo-Vorlage am Abo-Produkt, Bearbeitungsmodus der Regelliste, kein Testdatensatz hinterlassen.

Hinweis: In dieser Odoo-18-Version hat das Produktformular keinen Bearbeiten-Schalter in der
Kontrollleiste (im DOM kein `o_form_button_edit`, auch mit frischem Browserprofil und beim Oeffnen
aus der Listenansicht). Der Bearbeitungsmodus wurde deshalb ueber einen neuen Datensatz geprueft,
der ohne Speichern wieder verlassen wurde (Vorlagen vorher/nachher gleich).

## 7. Offene Punkte

* Migration der Preislisten selbst (Preislisten anlegen, 403 Regeln ohne Produktbezug) ist noch
  nicht im Testmigrationsskript - als Regel dokumentiert, nicht umgesetzt.
* Deutscher Titel fuer die Odoo-18-Gruppe "Upselling & Cross-Selling" (Abschnitt 5.3).
* Abo-Vorlagen (`sale.subscription.template`) muessen vor der Produktmigration namentlich
  vorhanden sein (Odoo 11: 5 Vorlagen, Odoo-18-Testinstanz: 4 lokal / 5 auf der VM).
