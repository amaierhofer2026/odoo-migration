# Produktformular: Odoo 11 gegen Odoo 18 (Bereich Abrechnung, Verkaufbare/Einkaufbare Produkte)

Stand: 05.10.2026, Session 126. Odoo 11 Prod ausschliesslich **read-only** gelesen.
Bereich Abrechnung bleibt **IN ARBEIT** - die Abnahme macht Anna selbst.

Auftrag: Formular, Liste, Suche, Kanban, Aktionen und Verknuepfungen der Menuepunkte
Abrechnung > Verkauf > Verkaufbare Produkte und Abrechnung > Einkauf > Einkaufbare Produkte
feldweise gegen Odoo 11 pruefen und angleichen; Odoo-18-Zusatzfunktionen erhalten,
keine Dummy-Felder, keine Umgehung durch "Odoo-18-Standard".

## 1. Reiter: Ist-Zustand und Umsetzung

```
Odoo 11 (8 Reiter)                    Odoo 18 vorher (5)                Odoo 18 nachher (7)
1. Allgemeine Informationen           1. Allgemeine Informationen        1. Allgemeine Informationen
                                      2. Attribute & Varianten           2. Attribute & Varianten
                                      3. Verkauf                         3. Verkauf
                                      4. Einkauf                         4. Einkauf
                                      5. Lager                           5. Lager
                                                                         6. Abrechnung
                                                                         7. Notizen
```
Vollstaendig, gemessen am Arch:

```
Odoo 11:
1. Allgemeine Informationen (17 Felder)
2. Varianten (1 Felder)
3. Verkauf (11 Felder)
4. Einkauf (2 Felder)
5. Lager (10 Felder)
6. Abrechnung (14 Felder)
7. Notizen (10 Felder)
8. Bilder (1 Felder)

Odoo 18 nachher:
1. Allgemeine Informationen (23 Felder)
2. Attribute & Varianten (5 Felder)
3. Verkauf (4 Felder)
4. Einkauf (34 Felder)
5. Lager (18 Felder)
6. Abrechnung (5 Felder)
7. Notizen (10 Felder)
```

Ursache des fehlenden Reiters **Abrechnung**: Die Seite kommt aus dem `account`-Modul
(`name=invoicing`, Beschriftung "Buchhaltung") und ist dort ueber die **verborgene technische
Gruppe** `account.group_account_readonly` eingeschraenkt - in der Instanz hat sie **0 Benutzer**
(gemessen 05.10.2026), der Reiter ist damit fuer jeden Benutzer unsichtbar. Odoo 11 zeigte den
Reiter ohne Gruppenbeschraenkung. Umsetzung: Beschriftung auf "Abrechnung" gesetzt, Gruppenfilter
entfernt, Odoo-11-Felder in Odoo-11-Gruppen hineingezogen. Die Buchhaltungsfelder behalten ihre
eigenen Gruppenrechte (Odoo 11 hatte sie unsichtbar).

Der Reiter **Notizen** existierte in Odoo 18 nur als Gruppe im ersten Reiter; er ist jetzt wieder
eigener Reiter mit den acht Odoo-11-Gruppen.

Der Reiter **Bilder** ist nicht nachbaubar: `product.image` (und das Feld `product_image_ids`)
existiert in Odoo 18 nicht mehr, und in Odoo 11 war der Reiter **0 von 649 Produkten** belegt
(0 Datensaetze in product.image, 0 Anhaenge an product.template). Odoo 18 zeigt das Hauptbild im
Kopfbereich (wie Odoo 11 das Feld image_medium ausserhalb der Reiter) und Dokumente ueber den
Smart Button "Dokumente"; die Nachrichten liegen im Chatter am Formularende. Kein Dummy-Reiter.

Zweiter Durchgang 05.10.2026 (Auftrag Anna): Das Formular ist nicht nur um fehlende Reiter
ergaenzt, sondern je Reiter inhaltlich, funktional und visuell nach Odoo 11 nachgebaut. Der erste
Reiter hat wieder zwei flache Spalten in Odoo-11-Reihenfolge, alle sichtbaren Beschriftungen
entsprechen dem Odoo-11-Wortlaut (deutsch, kein "Product-Type" mehr), Verkauf/Einkauf/Lager sind in
Odoo-11-Gruppen und -Reihenfolge; Odoo-18-Zusaetze bleiben erhalten. Abnahme im echten Browser:
Reiterpruefung 46 OK / 0 FEHL, Funktionspruefung 43 OK / 0 FEHL - lokal und VM (Abschnitt 9).

## 2. Feldweise Matrix

Legende: "belegt" = Anzahl der Odoo-11-Produktvorlagen mit einem Wert (von 649 Vorlagen). Bei
berechneten Feldern und Auswahlfeldern mit Standardwert bedeutet das nicht automatisch fachliche
Nutzung; massgeblich sind die Angaben in der Spalte "Migrationsregel".
Typverteilung Odoo 11: {'consu': 152, 'general': 273, 'onlineservice': 74, 'service': 47, 'platform': 94, 'sw': 9}.

| Reiter | Odoo 11 Feld/Funktion | Odoo 18 vorher | Technische Zuordnung | Aenderung | Odoo 18 nachher | Browser lokal | Browser VM | Migrationsregel | Bewusste Abweichung + Begruendung |
|---|---|---|---|---|---|---|---|---|---|
| Allgemeine Informationen | `type` (Produktart, 649/649 belegt) | vorhanden | `type` | unsichtbar wie in Odoo 11 | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen (type) | nein - Odoo 11 hatte hier die Auswahlwerte der ITK-Produktart; sie liegen in Odoo 18 in product_type_id |
| Allgemeine Informationen | `product_type_id` (Product-Type, 410/649 belegt) | vorhanden | `product_type_id` | unveraendert, deutsche Beschriftung | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen | nein - sichtbare Beschriftung 'Produktart' (Anna-Vorgabe 05.10.2026). In Odoo 11 trug die Auswahl type die ITK-Werte (sichtbar als 'Produktart'), product_type_id hiess dort 'Product-Type'; Odoo 18 zeigt die ITK-Produktart in einem Feld |
| Allgemeine Informationen | `categ_id` (Interne Kategorie, 649/649 belegt) | vorhanden | `categ_id` | in die erste Spalte verschoben (Odoo 11) | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen | nein - Beschriftung auf Odoo-11-Wortlaut 'Interne Kategorie' gesetzt |
| Allgemeine Informationen | `default_code` (Interne Referenz, 2/649 belegt) | vorhanden | `default_code` | in die erste Spalte verschoben (Odoo 11) | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen | nein - Beschriftung 'Interne Referenz' (Odoo 11) |
| Allgemeine Informationen | `barcode` (Strichcode, 0/649 belegt) | vorhanden | `barcode` | in die erste Spalte verschoben (Odoo 11) | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen | nein - 0 von 649 Produkten belegt |
| Allgemeine Informationen | `list_price` (Verkaufspreis, 606/649 belegt) | vorhanden | `list_price` | unveraendert | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen | nein |
| Allgemeine Informationen | `is_multi_factor_product` (To multiply by Factor(per 1000), 1/649 belegt) | vorhanden | `is_multi_factor_product` | unveraendert | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen | nein |
| Allgemeine Informationen | `recurring_invoice` (Abonnement Produkt, 333/649 belegt) | vorhanden | `recurring_invoice` | unveraendert (Odoo-11-Position, rechte Spalte) | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen | nein - Odoo 11 zeigte es zusaetzlich im Reiter Verkauf |
| Allgemeine Informationen | `valuation` (Bewertung, 649/649 belegt) | fehlte im Formular | kein Zielfeld | Feld im Odoo-18-Modell nicht mehr vorhanden | - | - | - | keine Migration moeglich | ja - Odoo 11: ueberall unsichtbar; Bewertung steuert Odoo 18 ueber die Produktkategorie |
| Allgemeine Informationen | `cost_method` (Kostenmethode, 649/649 belegt) | fehlte im Formular | kein Zielfeld | Feld im Odoo-18-Modell nicht mehr vorhanden | - | - | - | keine Migration moeglich | ja - Odoo 11: unsichtbar |
| Allgemeine Informationen | `property_cost_method` (Kalkulationsverfahren, 0/649 belegt) | fehlte im Formular | kein Zielfeld | Feld im Odoo-18-Modell nicht mehr vorhanden | - | - | - | keine Migration moeglich | ja - Odoo 11: unsichtbar |
| Allgemeine Informationen | `standard_price` (Kosten, 6/649 belegt) | vorhanden | `standard_price` | unveraendert | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen | nein - 6 von 649 belegt |
| Allgemeine Informationen | `company_id` (Unternehmen, 648/649 belegt) | vorhanden | `company_id` | unsichtbar wie in Odoo 11 | Einkauf | OK (Reiter Einkauf) | OK (Reiter Einkauf) | Wert 1:1 uebernehmen | nein |
| Allgemeine Informationen | `uom_id` (Mengeneinheit, 649/649 belegt) | vorhanden | `uom_id` | keine Aenderung | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen | ja - Odoo 11: unsichtbar, Odoo 18 zeigt das Feld sichtbar neben dem Verkaufspreis |
| Allgemeine Informationen | `uom_po_id` (Einkauf ME, 649/649 belegt) | vorhanden | `uom_po_id` | unveraendert (Reiter Einkauf) | Einkauf | OK (Reiter Einkauf) | OK (Reiter Einkauf) | Wert 1:1 uebernehmen | ja - Odoo 11: unsichtbar |
| Allgemeine Informationen | `currency_id` (Währung, 649/649 belegt) | vorhanden | `currency_id` | unsichtbar | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen | nein |
| Allgemeine Informationen | `product_variant_id` (Produkt, 648/649 belegt) | vorhanden | `product_variant_id` | unsichtbar | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen | nein |
| Varianten | `attribute_line_ids` (Produktattribute, 0/649 belegt) | vorhanden | `attribute_line_ids` | unveraendert (Odoo-18-Reiter 'Attribute & Varianten') | Attribute & Varianten | OK (Reiter Attribute & Varianten) | OK (Reiter Attribute & Varianten) | Wert 1:1 uebernehmen | nein - Odoo 11 blendete den Reiter 'Varianten' fest aus; Odoo 18 zeigt ihn |
| Verkauf | `item_ids` (Preislisten-Positionen, 320/649 belegt) | fehlte im Formular | kein Zielfeld | kein Feld; Odoo-18-Smart Button 'Preislistenregeln' | - | - | - | Preislistenregeln sind Verknuepfungen (product.pricelist.item -> product_tmpl_id) | ja - Odoo 11: Feld im Reiter Verkauf |
| Verkauf | `website_url` (Website-URL, 649/649 belegt) | fehlte im Formular | kein Zielfeld | Feld im Odoo-18-Modell nicht vorhanden (website/sale nicht installiert) | - | - | - | keine Migration moeglich | ja - Odoo 11: unsichtbar |
| Verkauf | `public_categ_ids` (Website-Produktkategorie, 0/649 belegt) | fehlte im Formular | kein Zielfeld | Feld im Odoo-18-Modell nicht vorhanden | - | - | - | keine Migration moeglich | ja - Odoo 11: Website-Kategorien; in Odoo 18 nicht installiert |
| Verkauf | `alternative_product_ids` (Alternative Produkte, 0/649 belegt) | als optional_product_ids vorhanden | `optional_product_ids` | durch Odoo-18-Feld abgebildet | Verkauf | OK (Reiter Verkauf) | OK (Reiter Verkauf) | alternative_product_ids -> optional_product_ids | nein - Odoo 18 fuehrt alternative und optionale Produkte zusammen |
| Verkauf | `accessory_product_ids` (Zubehör, 0/649 belegt) | als optional_product_ids vorhanden | `optional_product_ids` | durch Odoo-18-Feld abgebildet | Verkauf | OK (Reiter Verkauf) | OK (Reiter Verkauf) | accessory_product_ids -> optional_product_ids | nein - siehe oben |
| Verkauf | `inventory_availability` (Lagerverfügbarkeit, 649/649 belegt) | fehlte im Formular | kein Zielfeld | Feld im Odoo-18-Modell nicht vorhanden | - | - | - | keine Migration moeglich | ja - Odoo 11: 0 von 649 belegt |
| Verkauf | `available_threshold` (Verfügbarkeitsgrenze, 493/649 belegt) | fehlte im Formular | kein Zielfeld | Feld im Odoo-18-Modell nicht vorhanden | - | - | - | keine Migration moeglich | ja - Odoo 11: 0 von 649 belegt |
| Verkauf | `custom_message` (Persönliche Nachricht, 0/649 belegt) | fehlte im Formular | kein Zielfeld | Feld im Odoo-18-Modell nicht vorhanden | - | - | - | keine Migration moeglich | ja - Odoo 11: 0 von 649 belegt |
| Verkauf | `website_style_ids` (Style, 0/649 belegt) | fehlte im Formular | kein Zielfeld | Feld im Odoo-18-Modell nicht vorhanden | - | - | - | keine Migration moeglich | ja - Odoo 11: unsichtbar |
| Verkauf | `recurring_invoice` (Abonnement Produkt, 333/649 belegt) | vorhanden | `recurring_invoice` | unveraendert (Odoo-11-Position, rechte Spalte) | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen | nein - Odoo 11 zeigte es zusaetzlich im Reiter Verkauf |
| Verkauf | `subscription_template_id` (Vorlage für Abonnements, 292/649 belegt) | vorhanden | `subscription_template_id` | vom ersten Reiter in den Reiter Verkauf verschoben (Odoo 11) | Verkauf | OK (Reiter Verkauf) | OK (Reiter Verkauf) | Wert 1:1 uebernehmen | nein - Odoo 11 fuehrte die Vorlage in der Gruppe subscription im Verkauf |
| Einkauf | `seller_ids` (Lieferanten, 0/649 belegt) | vorhanden | `seller_ids` | in die Odoo-11-Gruppe 'Lieferanten' gesetzt | Einkauf | OK (Reiter Einkauf) | OK (Reiter Einkauf) | Wert 1:1 uebernehmen | nein - Odoo 11: 0 von 649 belegt |
| Einkauf | `variant_seller_ids` (Verkäufer von Variante, 0/649 belegt) | vorhanden | `variant_seller_ids` | in die Odoo-11-Gruppe 'Lieferanten' gesetzt | Einkauf | OK (Reiter Einkauf) | OK (Reiter Einkauf) | keine Werte zu uebernehmen | nein - in Odoo 18 nur bei mehreren Varianten sichtbar (Gruppe bleibt sichtbar) |
| Lager | `route_ids` (Routen, 649/649 belegt) | vorhanden | `route_ids` | unveraendert (Reiter Lager) | Lager | OK (Reiter Lager) | OK (Reiter Lager) | Wert 1:1 uebernehmen | nein |
| Lager | `route_from_categ_ids` (Routenkategorie, 0/649 belegt) | vorhanden | `route_from_categ_ids` | unveraendert (Reiter Lager) | Lager | OK (Reiter Lager) | OK (Reiter Lager) | berechnet aus der Kategorie, keine Migration | nein |
| Lager | `sale_delay` (Auslieferungszeit, 0/649 belegt) | vorhanden | `sale_delay` | im Reiter Lager in die Gruppe 'Vorgänge' verschoben (Odoo 11) | Lager | OK (Reiter Lager) | OK (Reiter Lager) | Wert 1:1 uebernehmen | nein - Odoo 11: 0 von 649 belegt |
| Lager | `weight` (Gewicht, 0/649 belegt) | vorhanden | `weight` | unveraendert (Reiter Lager, Gruppe Logistik) | Lager | OK (Reiter Lager) | OK (Reiter Lager) | Wert 1:1 uebernehmen | nein - Odoo 11: 0 von 649 belegt |
| Lager | `volume` (Volumen, 0/649 belegt) | vorhanden | `volume` | unveraendert (Reiter Lager, Gruppe Logistik) | Lager | OK (Reiter Lager) | OK (Reiter Lager) | Wert 1:1 uebernehmen | nein - Odoo 11: 0 von 649 belegt |
| Lager | `responsible_id` (Verantwortlich, 649/649 belegt) | vorhanden | `responsible_id` | im Reiter Lager in Odoo-11-Position (Logistik, nach Volumen) | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen | ja - Zusatz: Odoo 18 zeigt das Feld zusaetzlich im ersten Reiter (Beschluss Session 120, damit Abonnement-Produkte es zeigen) |
| Lager | `tracking` (Nachverfolgung, 649/649 belegt) | vorhanden | `tracking` | unveraendert (Odoo 11: unsichtbar) | None | OK (Reiter None) | OK (Reiter None) | Wert 1:1 uebernehmen | nein |
| Lager | `property_stock_production` (Fertigungort (virtuelles Lager), 649/649 belegt) | fehlte im Formular | `property_stock_production` | unveraendert (Odoo 11: unsichtbar) | nicht im Formular (Feld im Modell vorhanden) | - | - | Wert 1:1 uebernehmen | nein |
| Lager | `property_stock_inventory` (Lagerort Bestandsaufnahme, 649/649 belegt) | fehlte im Formular | `property_stock_inventory` | unveraendert (Odoo 11: unsichtbar) | nicht im Formular (Feld im Modell vorhanden) | - | - | Wert 1:1 uebernehmen | nein |
| Lager | `packaging_ids` (Produktverpackungen, 0/649 belegt) | fehlte im Formular | `packaging_ids` | unveraendert (Odoo 11: unsichtbar) | nicht im Formular (Feld im Modell vorhanden) | - | - | Wert 1:1 uebernehmen | nein |
| Abrechnung | `taxes_id` (Steuern (Verkauf), 647/649 belegt) | vorhanden | `taxes_id` | vom ersten Reiter in den Reiter Abrechnung verschoben (Odoo 11) | Abrechnung | OK (Reiter Abrechnung) | OK (Reiter Abrechnung) | Wert 1:1 uebernehmen (account.tax) | nein - 647 von 649 belegt |
| Abrechnung | `property_account_income_id` (Erlöskonto, 0/649 belegt) | fehlte im Formular | `property_account_income_id` | im Reiter Abrechnung, Gruppe Forderungen (Odoo 11) | nicht im Formular (Feld im Modell vorhanden) | - | - | Wert 1:1 uebernehmen, falls gesetzt | ja - Odoo 11: unsichtbar, 0 von 649 belegt; Odoo 18 zeigt es nur mit Buchhaltungsrecht (Gruppe unveraendert) |
| Abrechnung | `supplier_taxes_id` (Steuern (Einkauf), 648/649 belegt) | vorhanden | `supplier_taxes_id` | vom ersten Reiter in den Reiter Abrechnung verschoben (Odoo 11) | Abrechnung | OK (Reiter Abrechnung) | OK (Reiter Abrechnung) | Wert 1:1 uebernehmen (account.tax) | nein - 648 von 649 belegt |
| Abrechnung | `property_account_expense_id` (Aufwandskonto, 0/649 belegt) | fehlte im Formular | `property_account_expense_id` | im Reiter Abrechnung, Gruppe Verbindlichkeiten (Odoo 11) | nicht im Formular (Feld im Modell vorhanden) | - | - | Wert 1:1 uebernehmen, falls gesetzt | ja - Odoo 11: unsichtbar, 0 von 649 belegt |
| Abrechnung | `property_account_creditor_price_difference` (Preisdifferenzkonto, 0/649 belegt) | fehlte im Formular | `property_account_creditor_price_difference` | im Reiter Abrechnung (Odoo 11) | nicht im Formular (Feld im Modell vorhanden) | - | - | Wert 1:1 uebernehmen, falls gesetzt | ja - Odoo 11: unsichtbar, 0 von 649 belegt |
| Abrechnung | `property_valuation` (Inventur Bewertung, 0/649 belegt) | fehlte im Formular | kein Zielfeld | Feld im Odoo-18-Modell nicht mehr vorhanden | - | - | - | keine Migration moeglich | ja - Odoo 11: unsichtbar; Odoo 18 steuert die Bewertung an der Produktkategorie |
| Abrechnung | `property_stock_account_input` (Konto Wareneingang, 0/649 belegt) | fehlte im Formular | kein Zielfeld | Feld im Odoo-18-Modell nicht mehr vorhanden | - | - | - | keine Migration moeglich | ja - Odoo 11: Gruppe Bestandsbewertung |
| Abrechnung | `property_stock_account_output` (Warenversand Konto, 0/649 belegt) | fehlte im Formular | kein Zielfeld | Feld im Odoo-18-Modell nicht mehr vorhanden | - | - | - | keine Migration moeglich | ja - Odoo 11: Gruppe Bestandsbewertung |
| Abrechnung | `invoice_policy` (Fakturierungsregel, 649/649 belegt) | vorhanden | `invoice_policy` | vom ersten Reiter in den Reiter Abrechnung verschoben (Odoo 11) | Abrechnung | OK (Reiter Abrechnung) | OK (Reiter Abrechnung) | Wert 1:1 uebernehmen | nein - in Odoo 18 Pflichtfeld, Werte 1:1 ('order' 649 von 649) |
| Abrechnung | `service_type` (Dienstleistungsverfolgung, 649/649 belegt) | vorhanden | `service_type` | unveraendert unsichtbar | None | OK (Reiter None) | OK (Reiter None) | Wert 1:1 uebernehmen | nein - Odoo 11: 598x 'manual', 51x 'timesheet' |
| Abrechnung | `service_policy` (Rechnung basiert auf, 51/649 belegt) | fehlte im Formular | kein Zielfeld | Feld im Odoo-18-Modell nicht mehr vorhanden | - | - | - | 51 Datensaetze mit 'ordered_timesheet' -> invoice_policy/expense_policy pruefen | ja - Odoo 18 loest die Richtlinie ueber invoice_policy und expense_policy |
| Abrechnung | `service_tracking` (Dienstverfolgung, 649/649 belegt) | vorhanden | `service_tracking` | unveraendert unsichtbar | Allgemeine Informationen | OK (Reiter Allgemeine Informationen) | OK (Reiter Allgemeine Informationen) | Wert 1:1 uebernehmen | nein - Odoo 11: alle 649 'no'; Odoo 18 zeigt das Feld ebenfalls nicht |
| Abrechnung | `project_id` (Projekt, 0/649 belegt) | fehlte im Formular | kein Zielfeld | Feld im Odoo-18-Modell nicht mehr vorhanden | - | - | - | keine Migration moeglich (0 von 649 belegt) | ja - Odoo 18 erzeugt Projekte/Aufgaben ueber die Auftragslogik |
| Abrechnung | `purchase_method` (Kontrollrichtlinie, 649/649 belegt) | vorhanden | `purchase_method` | vom Reiter Einkauf in den Reiter Abrechnung verschoben (Odoo 11) | Abrechnung | OK (Reiter Abrechnung) | OK (Reiter Abrechnung) | Wert 1:1 uebernehmen | nein - 649 von 649 belegt ('receive') |
| Notizen | `description` (Beschreibung, 0/649 belegt) | vorhanden | `description` | vom ersten Reiter in den Reiter Notizen verschoben (Odoo 11) | Notizen | OK (Reiter Notizen) | OK (Reiter Notizen) | Wert 1:1 uebernehmen | nein - Odoo 11: Textfeld, Odoo 18: HTML-Feld (Inhalt wird als HTML uebernommen) |
| Notizen | `description_sale` (Verkaufsbeschreibung, 1/649 belegt) | vorhanden | `description_sale` | vom Reiter Verkauf in den Reiter Notizen verschoben (Odoo 11) | Notizen | OK (Reiter Notizen) | OK (Reiter Notizen) | Wert 1:1 uebernehmen | nein - 1 von 649 belegt |
| Notizen | `description_purchase` (Einkaufsbeschreibung, 0/649 belegt) | vorhanden | `description_purchase` | vom Reiter Einkauf in den Reiter Notizen verschoben (Odoo 11) | Notizen | OK (Reiter Notizen) | OK (Reiter Notizen) | Wert 1:1 uebernehmen | nein - 0 von 649 belegt |
| Notizen | `description_pickingout` (Beschreibung auf Lieferaufträgen, 0/649 belegt) | vorhanden | `description_pickingout` | vom Reiter Lager in den Reiter Notizen verschoben (Odoo 11) | Notizen | OK (Reiter Notizen) | OK (Reiter Notizen) | Wert 1:1 uebernehmen | nein - 0 von 649 belegt |
| Notizen | `description_pickingin` (Beschreibung auf Wareneingängen, 0/649 belegt) | vorhanden | `description_pickingin` | vom Reiter Lager in den Reiter Notizen verschoben (Odoo 11) | Notizen | OK (Reiter Notizen) | OK (Reiter Notizen) | Wert 1:1 uebernehmen | nein - 0 von 649 belegt |
| Notizen | `description_picking` (Beschreibung der Kommisionierung, 0/649 belegt) | vorhanden | `description_picking` | im Reiter Notizen ergaenzt (Odoo 11) | Notizen | OK (Reiter Notizen) | OK (Reiter Notizen) | Wert 1:1 uebernehmen | nein - in Odoo 18 nicht mehr im Formular; Feld im Modell vorhanden, 0 von 649 belegt |
| Notizen | `sale_line_warn` (Auftragsposition, 0/649 belegt) | vorhanden | `sale_line_warn` | vom Reiter Verkauf in den Reiter Notizen verschoben (Odoo 11) | Notizen | OK (Reiter Notizen) | OK (Reiter Notizen) | Wert 1:1 uebernehmen | nein - Beschriftung 'Auftragsposition' (Odoo 11) |
| Notizen | `sale_line_warn_msg` (Mitteilung für Auftragszeile, 0/649 belegt) | vorhanden | `sale_line_warn_msg` | vom Reiter Verkauf in den Reiter Notizen verschoben (Odoo 11) | Notizen | OK (Reiter Notizen) | OK (Reiter Notizen) | Wert 1:1 uebernehmen | nein - Beschriftung 'Mitteilung fuer Auftragszeile' (Odoo 11) |
| Notizen | `purchase_line_warn` (Bestellposition, 0/649 belegt) | vorhanden | `purchase_line_warn` | vom Reiter Einkauf in den Reiter Notizen verschoben (Odoo 11) | Notizen | OK (Reiter Notizen) | OK (Reiter Notizen) | Wert 1:1 uebernehmen | nein - Beschriftung 'Bestellposition' (Odoo 11); Odoo 18 hatte nolabel |
| Notizen | `purchase_line_warn_msg` (Bachricht bei Beschaffungsauftragsposition, 0/649 belegt) | vorhanden | `purchase_line_warn_msg` | vom Reiter Einkauf in den Reiter Notizen verschoben (Odoo 11) | Notizen | OK (Reiter Notizen) | OK (Reiter Notizen) | Wert 1:1 uebernehmen | ja - Beschriftung Odoo 18 'Nachricht für Bestellzeile' beibehalten (Odoo-11-Text war abgeschnitten) |
| Bilder | `product_image_ids` (Bilder, 0/649 belegt) | fehlte im Formular | kein Zielfeld | Feld und Modell product.image in Odoo 18 nicht mehr vorhanden | - | - | - | keine Migration noetig (0 von 649 belegt) | ja - Odoo 11: Reiter Bilder; Odoo 18 zeigt das Hauptbild im Kopf und Dokumente ueber den Smart Button |

## 3. Liste, Suche, Kanban, Aktionen

Beide Menuepunkte verwenden **dieselben Ansichten**; sie unterscheiden sich nur im Standardfilter.

```
Aktion Verkaufbare Produkte (382):  res_model product.template, view_mode kanban,list,form,activity,
                                    Listenansicht product.template.list (account), view_id 1023,
                                    context {'search_default_filter_to_sell': 1}
Aktion Einkaufbare Produkte (383):  identisch, context {'search_default_filter_to_purchase': 1}
Odoo 11: beide Aktionen auf product.product (Varianten), context entsprechend
```

Listenansicht:

```
Odoo 11 (product.product)   Interne Referenz | Name | Attributwerte | Verkaufspreis | Verfuegbar |
                            Prognostiziert | Mengeneinheit | Strichcode
Odoo 18 vorher              Interne Referenz | Name | Verkaufspreis | Steuern (Verkauf) |
                            Steuern (Einkauf)
Odoo 18 nachher             Interne Referenz | Name | Verkaufspreis | Bestandsmenge |
                            Geplante Bestandsmenge | Mengeneinheit | Strichcode |
                            Steuern (Verkauf) | Steuern (Einkauf)
```
Ergaenzt wurden die vier fehlenden Odoo-11-Spalten (alle als `optional="show"`, also sichtbar,
aber abschaltbar). Die Odoo-18-Zusatzspalten bleiben. Die Odoo-11-Spalte "Attributwerte" entfaellt:
Odoo 18 fuehrt die Menues auf `product.template` (eine Zeile je Vorlage), Attribute stehen im Reiter
"Attribute & Varianten". Im Odoo-11-Bestand gibt es keine Produkte mit Attributen, die sichtbare
Wirkung ist deshalb identisch. **Entscheidungspunkt fuer Anna:** Odoo 11 listete `product.product`
(eine Zeile je Variante), Odoo 18 `product.template` (eine Zeile je Vorlage) - ein Umbau auf
Varianten waere moeglich, aendert aber Zaehlung und Standardverhalten der Menues.

Suche: Odoo 11 hatte 11 Filter und **keine** Gruppierungen; Odoo 18 zeigt dieselben 11 Filter im
Odoo-11-Wortlaut (Session 123) plus die Odoo-18-Standardfilter sowie zwei eigene Gruppierungen
(Status, Mit Faktor multipliziert). Keine Aenderung in Session 126.

Kanban: Odoo 11 (image_small, lst_price, type, product_variant_count, qty_available, uom_id),
Odoo 18 (image_128, list_price, qty_available, uom_id, product_properties, Aktivitaet)
- funktional gleichwertig, Odoo-18-Optik bleibt.

Aktionen/Buttons im Formular: Odoo 11 hatte die Buttons Variantenpreise, Lagerbestand korrigieren,
Kosten aktualisieren, Produktlieferungen, Routen, Los-/Seriennummer sowie die Smart Buttons
Varianten, Auf Lager, Verkauf, Einkauf, Website. Odoo 18 fuehrt Smart Buttons (Preislistenregeln,
Varianten, Bestand/Prognose, Eingekauft, Verkauft, Dokumente, Meldebestand), die Kopfbuttons
Menge aktualisieren, Auffuellen, Etiketten drucken und den Diagramm-Knopf im Reiter Lager.
Alle Odoo-18-Knoepfe bleiben erhalten.

## 4. Bewusste Abweichungen (mit Begruendung)

```
1. Reiter Bilder: kein Nachbau, weil product.image in Odoo 18 entfaellt und in Odoo 11
   0 von 649 Produkten belegt war (Hauptbild im Kopf, Dokumente-Smart-Button, Chatter).
2. service_policy, project_id: Feld im Odoo-18-Modell nicht mehr vorhanden; die Richtlinie
   laeuft in Odoo 18 ueber invoice_policy und expense_policy (51 Produkte mit
   service_policy 'ordered_timesheet' -> bei der Migration pruefen).
3. property_valuation, property_stock_account_input/-output, cost_method, property_cost_method,
   valuation: in Odoo 18 entfernt (Bewertung an der Produktkategorie); in Odoo 11 unsichtbar.
4. website-Felder (public_categ_ids, inventory_availability, available_threshold, custom_message,
   website_style_ids, website_url): Modul in Odoo 18 nicht installiert; in Odoo 11 0 belegt.
5. Attributwert-Spalte der Liste: siehe Abschnitt 3.
6. purchase_line_warn_msg: Odoo-11-Beschriftung war abgeschnitten ("Bachricht bei
   Beschaffungsauftra"), es bleibt der korrekte Odoo-18-Wortlaut.
7. 'Description for Internal' bleibt wie in Odoo 11 englisch (Odoo 11 hatte dafuer keine
   deutsche Uebersetzung).
```

## 5. Migration

Fuer **jedes** belegte Odoo-11-Produktfeld ist das Zielfeld in Abschnitt 2 vermerkt; belegte
Felder sind insbesondere: name, type, categ_id, product_type_id (410), list_price (606),
recurring_invoice (333), subscription_template_id (292), standard_price (6), uom_id/uom_po_id,
sale_ok, purchase_ok, purchase_method (649), route_ids, tracking, responsible_id, taxes_id (647),
supplier_taxes_id (648), invoice_policy (649), service_type (649), service_tracking, active.
Beziehungen: categ_id -> product.category, taxes_id/supplier_taxes_id -> account.tax,
product_type_id -> itk_product.product_type, subscription_template_id -> sale.subscription.template,
route_ids -> stock.route, uom_id/uom_po_id -> uom.uom. Alle Zielfelder existieren in Odoo 18.

## 6. Nachweise

```
Odoo 11 Nutzung je Feld      scripts/analyse_o11_produktfelder_nutzung.py
Arch/Reiter-Struktur         scripts/zeige_produktformular_struktur.py o11|lokal|vm
Feld-/Ansichtsvergleich      scripts/vergleich_produkt_ansichten.py o11|lokal|vm
Formular- und Reiterabnahme  scripts/browser_produktformular_reiter_abnahme.py lokal|vm
                             (46 Pruefpunkte je Instanz, Ergebnis 46 OK / 0 FEHL)
Vorher-/Nachher-Bilder       scripts/browser_produktformular_aufnahme.py lokal|vm <ordner>
DOM-Sonde Einzelfelder       scripts/_sonde_produktformular_dom.py lokal|vm
```
Bilder: `Desktop/Odoo18-Abnahme-Session126/produktformular_vorher/vm` (Zustand vor der Aenderung),
`produktformular/lokal` und `produktformular/vm` (nachher, je Reiter und Liste).

## 7. Absicherung der bewussten Abweichungen (05.10.2026, Odoo 11 read-only)

### 7.1 Reiter Bilder - es gibt keine Produktbilder und keine Anhaenge

Gemessen in Odoo 11 Prod (`scripts/pruefe_o11_bilder_und_varianten.py`, nur Leseaufrufe):

```
product.image Datensaetze                         0
image / image_medium / image_small belegt
   product.template (649)                     0 / 0 / 0
   product.product  (648)                     0 / 0 / 0
Anhaenge (ir.attachment) an
   product.template                               0   davon Bilder 0
   product.product                                0   davon Bilder 0
   product.image                                  0
   product.supplierinfo                           0
```

Ergebnis: In Odoo 11 ist **kein einziges Produktbild und kein einziger Anhang** an Produkten
gespeichert - weder Zusatzbilder (product.image war leer), noch Hauptbilder (alle drei
Bildfelder zu 0 Prozent belegt), noch Dateianhaenge. Durch das fehlende Feld
`product_image_ids` in Odoo 18 gehen daher **keine Daten verloren**, und es ist **keine
Migrationsregel** erforderlich (es gibt nichts zu uebernehmen). Waeren Zusatzbilder vorhanden,
waere die Regel: Datei aus dem Odoo-11-Filestore in `product.template.image_1920` bzw. in einen
Anhang am Produkt uebernehmen - dieser Fall tritt nicht ein.

### 7.2 product.product -> product.template - keine produktiven Varianten

Gemessen (dieselben Skripte, Odoo 11 read-only):

```
product.template                          649
product.product                           648
Vorlagen mit mehr als einer Variante        0
Varianten mit Attributwerten (attribute_value_ids)   0 von 648
product.attribute                           2   ("Variante Flo", "Variante Kat", Typ radio)
product.attribute.value                     5
product.attribute.line                      2   (beide an Vorlage 300 "Test Produkt 2", archiviert)
Vorlagen ohne Variante                      1   (Vorlage 263, in keinem Beleg verwendet)
```

Belegverweise (jede Zeile zeigt auf die Variante, nicht auf die Vorlage):

```
account.move.line      10039 Zeilen, 410 Produkte, aus Mehrfachvarianten-Vorlagen 0
sale.order.line         4015 Zeilen, 403 Produkte, aus Mehrfachvarianten-Vorlagen 0
purchase.order.line        0 Zeilen (keine Eingangsrechnungen in Odoo 11)
sale.subscription.line   2438 Zeilen, 209 Produkte, aus Mehrfachvarianten-Vorlagen 0
stock.move               327 Zeilen,  91 Produkte, aus Mehrfachvarianten-Vorlagen 0
Vorlagen mit mehreren in Belegen verwendeten Varianten: 0 (in allen Modellen)
```

Ergebnis: Es gibt **keine produktiven Varianten**. Jede Vorlage hat genau eine Variante, kein
Produkt traegt Attributwerte. Eine Mehrfachzuordnung (mehrere Varianten derselben Vorlage in einer
Zeile einer Rechnung/eines Auftrags), ein Datenverlust oder eine falsche Verknuepfung ist damit
ausgeschlossen. Die Zuordnung Vorlage <-> Variante bleibt 1:1 und ist ueber
`product.product.product_tmpl_id` eindeutig aufloesbar; die Belegzeilen zeigen weiterhin auf die
(neu erzeugte) Variante.

Migrationsregeln fuer die beiden Randfaelle (beide unkritisch, kein Produktivbezug):

```
Vorlage 263 "Aufbau einer Plattform fuer interkommunalen Wissens- und Erfahrungsaustausch"
   hat in Odoo 11 keine Variante und ist in keinem Beleg, keiner Preisliste und keiner
   Lieferanteninfo verwendet (0 Treffer in allen geprueften Modellen).
   Regel: beim Anlegen in Odoo 18 entsteht die Variante automatisch; es ist keine
   Belegzuordnung nachzuziehen.
Vorlage 300 "Test Produkt 2" (aktiv=False, Typ service, in keinem Beleg verwendet) traegt die
   beiden einzigen Attributzeilen und deren Werte.
   Regel: Attribute und Werte (2 Attribute, 5 Werte) sind reine Stammdaten ohne
   Variantenwirkung in Odoo 11. Sie werden nur uebernommen, wenn die Stammdaten gebraucht
   werden; dabei ist sicherzustellen, dass genau eine Variante je Vorlage erhalten bleibt
   (keine Variantenvervielfachung). Da die Vorlage archiviert und unbenutzt ist, ist auch ein
   Verzicht dokumentierbar.
```

## 8. Funktions- und Verknuepfungspruefung der sieben Reiter (echter Browser)

Werkzeug: `scripts/browser_produktformular_funktionen.py lokal|vm` - oeffnet ein echtes Produkt
der Menues (id 3 "Produkt B", Ware mit Verkaeufen und Einkaeufen), prueft je Reiter die
Funktionen und klickt Smart Buttons an (nur oeffnen, nichts speichern).
Ergebnis: **lokal 43 OK / 0 FEHL, VM 43 OK / 0 FEHL** (05.10.2026).

```
Kopfbereich  Smart Buttons: Regeln Preislisten, Dokumente, Verkauft (1,000 Einheit(en)),
             Eingekauft (2,000 Einheit(en)), Bestand (Eingang: 0 Ausgang: 0)
             Klickproben: Verkauft -> Verkaufsanalyse (action-420), Eingekauft ->
             Einkaufshistorie (action-1175), Regeln Preislisten -> product.pricelist.item
             Kopfknoepfe: Auffuellen, Etiketten drucken (Dialog oeffnet und schliesst ohne
             Speicherung)
             "Varianten" wird bei nur einer Variante nicht angezeigt (Odoo-18-Regel) -
             dokumentierte Abweichung zu Odoo 11, das den Zaehler immer zeigte
Allgemeine   Produktart (itk_product.product_type, deutsche Beschriftung), Interne Kategorie
Informationen (product.category), Interne Referenz, Strichcode, Verantwortlich (res.users),
             Verkaufspreis, Kosten, Kann verkauft/eingekauft werden, Abonnement Produkt
             (recurring_invoice); Reihenfolge im echten Browser geprueft: Produktart, Interne
             Kategorie, Interne Referenz, Strichcode, Verantwortlich, Bestand verfolgen |
             Verkaufspreis, To multiply by Factor(per 1000), Abonnement Produkt, Kosten;
             keine englische Beschriftung "Product-Type" mehr, keine verschachtelten Kaesten
Verkauf      Optionale Produkte (Odoo-18-Feld fuer alternative/Zubehoer-Produkte),
             Stichwoerter, Spesen weiter verrechnen (Auswahl aktiv "Nein");
             Abonnement-Vorlage (subscription_template_id) aus dem ersten Reiter hierher,
             in der Browserpruefung mit Wert "Monatsabrechnung-Abonnement" sichtbar
Einkauf      Lieferantenliste mit Spalten Lieferant/Menge/Preis/Waehrung/Liefervorlaufzeit
             (Zeile vorhanden, Hinzufuegen moeglich), Einkauf ME editierbar
Lager        Odoo-11-Reihenfolge: Vorgaenge (Routen stock.route, Knopf "Diagramm ansehen",
             Routenkategorie, Auslieferungszeit) | Logistik (Gewicht, Volumen, Verantwortlich
             als Avatar) | Verpackung (Liste mit Spalten und Hinzufuegen)
Abrechnung   Steuern (Verkauf) und Steuern (Einkauf) als Chips belegt (20% USt / 20% VSt,
             account.tax), Steuerzeichenkette "+ 1,20 € Inkl. Steuern", Fakturierungsregel und
             Kontrollrichtlinie als Radioknoepfe mit den Werten (Bestellte Mengen / Gelieferte
             Mengen bzw. Auf bestellte Mengen / Auf erhaltene Mengen), beide editierbar
Notizen      Beschreibung (HTML-Feld, in Odoo 11 Textfeld), Verkaufs-, Einkaufs- und drei
             Lieferbeschreibungen sichtbar und editierbar; Warnhinweise Verkauf/Einkauf als
             Auswahl mit Wert "Keine Nachricht"
Attribute &  Attributliste mit Spalten Attribut/Werte und "Zeile hinzufuegen" vorhanden
Varianten
```
Bilder je Reiter: `Desktop/Odoo18-Abnahme-Session126/produktformular_funktionen/{lokal,vm}`.

## 9. Reiterweise Abnahme (05.10.2026, echter Browser lokal und VM)

Auftrag vom 05.10.2026: jeder Reiter einzeln im echten Browser gegen Odoo 11 vergleichen und
nachbauen - Felder, deutsche Beschriftungen, Reihenfolge, Gruppen, Sichtbarkeit, Pflicht/readonly,
Verknuepfungen, Funktionen, Listen. Odoo-18-Zusaetze bleiben erhalten.

### 9.1 Allgemeine Informationen (neu aufgebaut)

```
Odoo 11 (zwei Spalten)                Odoo 18 vorher                     Odoo 18 nachher
links:  Produktart (type, ITK-Werte)  links: verschachtelte Untergruppen links:  Produktart
        Product-Type (product_type_id)        (Product-Type, Verantwortlich,       Interne Kategorie
        Interne Kategorie (categ_id)          Kategorie/Referenz/Strichcode),      Interne Referenz
        Interne Referenz (default_code)       dadurch bis zu vier Spalten          Strichcode
        Strichcode (barcode)          rechts: Verkaufspreis, Kosten,       rechts: Verkaufspreis
rechts: Verkaufspreis (list_price)             Faktor                                 To multiply by Factor
        To multiply by Factor         zus.: Kasten "Subscription" mit                (per 1000)
        Abonnement Produkt            Abonnement Produkt + Vorlage          zus.:  Abonnement Produkt
        Kosten (standard_price)                                                 Kosten
                                                                            zusaetze: Verantwortlich,
                                                                            Bestand verfolgen, Kombi
```

Umgesetzt:
- Der erste Block ist wieder **eine Spaltenklammer mit genau zwei flachen Gruppen** (`group_general`,
  `group_standard_price`); die Hilfsgruppen `product_type`, `itk_responsible` und
  `itk_kategorie_referenz` sind entfernt (sie erzeugten die zusaetzlichen Spalten).
- Feldreihenfolge links in Odoo-11-Ordnung: Produktart, Interne Kategorie, Interne Referenz,
  Strichcode; danach die Odoo-18-Zusaetze Verantwortlich, Bestand verfolgen, Kombination, Service-
  abwicklung, Tooltip, Bewertung je Los.
- Feldreihenfolge rechts in Odoo-11-Ordnung: Verkaufspreis, To multiply by Factor(per 1000),
  Abonnement Produkt, Kosten (die unsichtbaren Odoo-18-Felder liegen dazwischen, sie sind nicht
  sichtbar).
- Beschriftungen: `product_type_id` heisst sichtbar **Produktart** (Vorgabe Anna 05.10.2026;
  Odoo 11 zeigte fuer die ITK-Produktart das Feld `type` als "Produktart" und fuehrte
  `product_type_id` zusaetzlich als "Product-Type"). Vorher: "Product-Type".
- "Abonnement Produkt" bleibt im ersten Reiter (Odoo-11-Position, rechte Spalte), die
  **Abonnement-Vorlage** wechselt in den Reiter Verkauf (Odoo-11-Position).
- `product_properties` (Odoo-18-Produktmerkmale) liegt jetzt unterhalb der Spaltenklammer, damit
  die zwei Spalten sauber bleiben.

Funktionen/Verknuepfungen geprueft: Produktart (`itk_product.product_type`), Kategorie
(`product.category`), Verkaufspreis/Kosten editierbar, To multiply by Factor(per 1000) als
Auswahlkasten, Abonnement Produkt als Haken, Verantwortlich (`.res.users`, Avatar-Widget).
Migrationsmapping: `type` 1:1 (unsichtbar), `product_type_id` 1:1 ueber den Namen (Odoo-11-Werte
consu/service/general/onlineservice/sw/consulting/platform/hw/project/product),
`categ_id`/`default_code`/`barcode`/`list_price`/`standard_price`/`recurring_invoice`/
`subscription_template_id` je 1:1. Die Zuordnung der Odoo-11-Auswahlwerte von `type` auf
`consu`/`service` ist in `docs/o11-o18-testmigration-regel.md` als **offene fachliche
Bestaetigung** vermerkt (Odoo 11: consu 152, service 47, onlineservice 74, platform 94, sw 9).

Verbleibende Abweichungen: "Verantwortlich" und "Bestand verfolgen" sind Odoo-18-Felder ohne
Odoo-11-Gegenstueck und stehen deshalb im ersten Reiter (Beschluss Session 120); Odoo 11 zeigte
"Abonnement Produkt" zusaetzlich im Reiter Verkauf (Odoo 18 zeigt es einmal).

### 9.2 Verkauf

```
Odoo 11                                    Odoo 18 vorher          Odoo 18 nachher
Preiskalkulation (Liste der Item-Regeln)   Up-Selling              Up-Selling
Website (oeffentliche Kategorien,          Weitere Informationen   Weitere Informationen
Alternative/Zubehoer, Verfuegbarkeit)      Ausgabe                 Ausgabe
Gruppe subscription:                       (Abonnement-Vorlage     Gruppe ohne Ueberschrift:
  Abonnement Produkt                        lag im ersten Reiter)   Abonnement-Vorlage
  Vorlage fuer Abonnements
```

Umgesetzt: die Abonnement-Vorlage (`subscription_template_id`) steht jetzt im Reiter Verkauf, in
einer Gruppe ohne Gruppenueberschrift - genau wie die Odoo-11-Gruppe `subscription`. Geprueft im
Browser (Produkt 6 "Test-Abo monatlich"): Vorlage sichtbar mit Wert "Monatsabrechnung-Abonnement",
lokal und VM (Bild `produktformular_funktionen/*/09_abo_verkauf.png`).
Migrationsmapping: `item_ids` Odoo 11 (0 von 649 belegt) -> Odoo 18 fuehrt Preislistenregeln als
Smart Button "Regeln Preislisten" am Produkt (`product.pricelist.item`); Website-Felder entfallen
(Modul nicht installiert, in Odoo 11 0 belegt); `optional_product_ids` bildet Odoo-11
Alternative/Zubehoer ab; `recurring_invoice`/`subscription_template_id` 1:1.

### 9.3 Einkauf

Umgesetzt: die zwei Odoo-11-Gruppen **"Lieferanten"** (Lieferantenliste `seller_ids` und
Variantenlieferanten `variant_seller_ids`) sind wiederhergestellt; vorher standen beide Felder
ohne Gruppe direkt im Reiter. Browserpruefung: Lieferantenliste mit Spalten
Lieferant/Menge/Preis/Waehrung/Liefervorlaufzeit und "Zeile hinzufuegen", Einkauf ME editierbar.
Migrationsmapping: `seller_ids` 1:1 (Odoo 11: 0 von 649 belegt), `variant_seller_ids` ohne Werte
(Odoo 11: 0), `uom_po_id` 1:1. Verbleibende Abweichung: die zweite Gruppe "Lieferanten" ist bei
Einzelvarianten leer (in Odoo 11 war dort nur das Feld unsichtbar); "Einkauf ME" bleibt sichtbar
(Odoo 11 hatte es unsichtbar).

### 9.4 Lager

Umgesetzt: Odoo-11-Reihenfolge hergestellt - "Vorgaenge" (Routen, Routenkategorie,
Auslieferungszeit), "Logistik" (Gewicht, Volumen, Verantwortlich), "Verpackung". Vorher stand
"Verantwortlich" vor Gewicht/Volumen und "Auslieferungszeit" in "Logistik". Browserpruefung:
Routen-Auswahl (stock.route, "Einkaufen" gesetzt), Knopf "Diagramm ansehen", Gewicht 0,00,
Volumen 0,00, Verantwortlich mit Avatar, Verpackungsliste mit Hinzufuegen.
Migrationsmapping: `route_ids`/`route_from_categ_ids`/`weight`/`volume`/`sale_delay`/
`responsible_id` je 1:1 (alle 0 von 649 belegt).

### 9.5 Abrechnung

Bereits im ersten Durchgang umgesetzt (Reiter war in Odoo 18 durch das Gruppenrecht
`account.group_account_readonly` unsichtbar): Gruppen "Forderungen" (Steuern Verkauf),
"Verbindlichkeiten" (Steuern Einkauf), "Abrechnung" (Fakturierungsregel), "Eingangsrechnung"
(Kontrollrichtlinie). Browserpruefung: Steuern als Chips (20% USt / 20% VSt), Steuerzeichenkette,
Fakturierungsregel und Kontrollrichtlinie als Radioknoepfe, beide editierbar.
Migrationsmapping: `invoice_policy` -> Fakturierungsregel, `purchase_method` -> Kontrollrichtlinie,
`taxes_id`/`supplier_taxes_id` (account.tax) 1:1; `service_policy`, `service_type`, `project_id`
und `property_stock_account_*` existieren in Odoo 18 nicht (in Odoo 11 unsichtbar bzw. 0 belegt).

### 9.6 Notizen

Umgesetzt: eigener Reiter mit den acht Odoo-11-Gruppen (interne Beschreibung, Kundenbeschreibung,
Lieferantenbeschreibung, Beschreibung fuer Auslieferungsauftraege, Wareneingang, interne Transfers,
Warnung Verkauf, Warnung Einkauf). Browserpruefung: alle sechs Beschreibungsfelder sichtbar und
editierbar, beide Warndropdowns mit Wert "Keine Nachricht". Verbleibende Abweichung: die interne
Beschreibung ist in Odoo 18 ein HTML-Feld (Odoo 11: Textfeld) - fachlich gleichwertig.

### 9.7 Attribute & Varianten und Bilder

"Attribute & Varianten" ist ein Odoo-18-Zusatzreiter und bleibt erhalten (Attributliste mit
Spalten Attribut/Werte, Zeile hinzufuegen). Reiter "Bilder": in Odoo 18 nicht nachbaubar, in
Odoo 11 0 von 649 Produkten belegt (Abschnitt 7.1).

## 10. Status

Umgesetzt und im echten Browser lokal und auf der VM geprueft (Reiterpruefung 46 OK / 0 FEHL,
Funktionspruefung 43 OK / 0 FEHL, Bilder gesehen): Reiter Abrechnung und Notizen
wiederhergestellt, erster Reiter neu aufgebaut (zwei flache Spalten in Odoo-11-Reihenfolge,
deutsche Beschriftungen), Verkauf/Einkauf/Lager in Odoo-11-Gruppen und -Reihenfolge, vier
Odoo-11-Spalten in der Liste ergaenzt, keine Odoo-18-Funktion entfernt, keine Dummy-Felder,
kein Feld doppelt im Formular (Arch geprueft).
**Abrechnung bleibt IN ARBEIT** - nicht als migrationsbereit oder abgeschlossen markiert.
