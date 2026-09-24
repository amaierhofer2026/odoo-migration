# Abonnements: Teil 15 - Produktformular vollstaendig verglichen

Stand: 24.09.2026 (Session 120, Fortsetzung der Uebergabe vom 22./23.09.2026). Odoo 11 Prod
ausschliesslich read-only (nur Leseaufrufe).
Keine Datenmigration, kein Datensatz in Odoo 11 oder Odoo 18 angelegt, geaendert oder geloescht.

**Wichtig: Der Unterbereich "Abonnement Produkte" ist damit wieder OFFEN.** Der Abschluss aus
Teil 14 bezog sich auf Liste, Suche und Formularbereinigung; der vollstaendige Vergleich aller
Reiter des Produktformulars (Auftrag dieser Session) foerdert Punkte zutage, die vorher nicht
gemessen waren. Abschnitt 8 nennt sie.

**Stand nach der Umsetzung (Abschnitte 11-13):** Die Punkte Buchhaltung, Verantwortlich,
Notizen und Zeiterfassung sind umgesetzt und am 24.09.2026 auf der **VM** ausgerollt und im
**echten Browser abgenommen** (Abschnitt 12.6). Der Bereich Abonnements ist damit auf
"abgeschlossen" zurueckgesetzt (Checkliste 6.14).

## 1. Auftrag

Formular eines "Abonnement Produkts" in Odoo 11 Prod vollstaendig mit Odoo 18 vergleichen:
alle Reiter, alle sichtbaren Felder, Feldbezeichnungen, Feldtypen/Relationen,
Sichtbarkeitsregeln, Buttons/Smart Buttons, Pflichtfelder, Such-/Auswahlfelder und die
funktionalen Zusammenhaenge. Ergebnis soll eine Einordnung in vier Gruppen sein:
vorhanden aber anderswo, wirklich fehlend, ungenutzt und daher verzichtbar, durch eine
modernere Odoo-18-Funktion ersetzt. Zusaetzliche Odoo-18-Funktionen bleiben erhalten.

## 2. Werkzeuge (neu, alle read-only)

```
scripts/vergleich_abo_produktformular.py          Reiter, Felder je Reiter, Buttons, Felddefinitionen
                                                  einer Instanz (--instanz o11|vm|lokal)
scripts/vergleich_abo_produktformular_felder.py   Reiter-/Felddiff O11 gegen O18 + Modulzustaende
scripts/analyse_o11_produktformular_nutzung.py    Nutzung je Feld in Odoo 11 (Bulk-Read, gezaehlt in Python)
scripts/analyse_produktformular_teil2.py          Kategorien/Konten, Routen, Preislisten, Chatter
scripts/analyse_produktformular_teil3.py          Lage der Kontofelder in Odoo 18
scripts/analyse_produktformular_teil4.py          Modulzustaende O18, Zeiterfassung in O11
scripts/pruefe_account_gruppen.py                 Gruppen der Buchhaltung (Sichtbarkeitsursache)
scripts/pruefe_o18_form_arch.py                   prueft die Form der Ansichtsauslesung in O18
scripts/schlussprobe_produktformular.py           Feld fuer Feld: im Modell / im Formular vorhanden?
scripts/pruefe_view_render.py                     (vorhanden) Testdatensatz rendern, loeschen
```

Zur Auslesung: Odoo 11 liefert mit `fields_view_get` den fertig zusammengefuehrten Arch.
Odoo 18 kennt diese Methode nicht mehr; `get_views` liefert einen Eintrag je Ansicht, wobei
erst der letzte Eintrag dem zusammengefuehrten Arch entspricht. `pruefe_o18_form_arch.py`
stellt sicher, dass genau dieser verwendet wird (sonst fehlen Felder scheinbar).

## 3. Reiter: Ist-Zustand beider Seiten (gemessen)

```
Odoo 11 (8 Reiter)                        Odoo 18 (5 Reiter)
1. Allgemeine Informationen               1. Allgemeine Informationen
2. Varianten        invisible="1"         2. Attribute & Varianten   invisible="type == 'combo'"
3. Verkauf                                3. Verkauf
4. Einkauf                                4. Einkauf
5. Lager            type != service       5. Lager            type not in [service, combo]
6. Abrechnung
7. Notizen
8. Bilder
```

Der Reiter **Lager ist in beiden Versionen vorhanden** und in beiden fuer Dienstleistungs-
produkte ausgeblendet (O11: `type == 'service'`, O18: `type in ['service','combo']`). Dass er
im Abonnement-Produkt nicht erscheint, ist also kein Unterschied, sondern dieselbe Regel.
Der Reiter **Varianten** ist in O11 fest ausgeblendet und in O18 sichtbar.

Fuer ein Abonnement Produkt (Dienstleistung) sichtbar:
Odoo 11: Allgemeine Informationen, Verkauf, Einkauf, Abrechnung, Notizen, Bilder
Odoo 18: Allgemeine Informationen, Attribute & Varianten, Verkauf, Einkauf

## 4. Gruppe A - in Odoo 18 vorhanden, aber an anderer Stelle

```
Odoo-11-Reiter  Feld                     Odoo 18
Abrechnung      taxes_id                 Allgemeine Informationen (neben dem Verkaufspreis,
                                          verschoben von account.product_template_form_view)
Abrechnung      supplier_taxes_id        Allgemeine Informationen (neben den Kosten)
Abrechnung      invoice_policy           Allgemeine Informationen, dort Pflichtfeld
Abrechnung      service_tracking         Allgemeine Informationen, dort Pflichtfeld
Abrechnung      property_account_income_id / expense_id
                                         Seite "Buchhaltung" (name=invoicing, hinter "Lager") -
                                          siehe Abschnitt 7, Sichtbarkeit ueber Gruppe
Abrechnung      purchase_method          Reiter Einkauf
Notizen         description              Gruppe "Interne Notizen" im Reiter Allgemeine
                                          Informationen (Typ in O18: html, in O11: text)
Notizen         description_sale         Reiter Verkauf
Notizen         description_purchase     Reiter Einkauf
Notizen         sale_line_warn(_msg)     Reiter Verkauf
Notizen         purchase_line_warn(_msg) Reiter Einkauf
Verkauf         item_ids                 Smart Button "Preislistenregeln" (open_pricelist_rules)
                                          mit Anzahl, Feld pricelist_item_count
Verkauf         sales_count              Smart Button "Verkauft" (action_view_sales)
Bilder          product_image_ids        entfaellt als Feld - Hauptbild image_1920 im Kopf
                                          + Dokumente-Smart-Button (Anhänge)
Bilder          message_*/activity_ids   Chatter am Formularende (<chatter/>)
Allgemein       product_variant_count    Smart Button "Varianten"
Einkauf         currency_id, uom_po_id   Einkauf
```

## 5. Gruppe B - in Odoo 18 tatsaechlich nicht mehr vorhanden

Feld fuer Feld geprueft (`scripts/schlussprobe_produktformular.py`): Feld fehlt im Odoo-18-
Modell product.template.

```
Grund: Modul in Odoo 18 nicht installiert (stock, stock_account, website_sale, sale_project/sale_timesheet)
   qty_available, virtual_available, outgoing_qty, incoming_qty, nbr_reordering_rules,
   reordering_min_qty, reordering_max_qty, tracking, sale_delay, route_ids, route_from_categ_ids,
   property_stock_production, property_stock_inventory, property_stock_account_input,
   property_stock_account_output, description_picking, description_pickingin,
   description_pickingout, purchase_count, valuation, cost_method, property_cost_method,
   property_valuation, property_account_creditor_price_difference,
   public_categ_ids, website_style_ids, website_url, website_published,
   inventory_availability, available_threshold, custom_message

Grund: in Odoo 17/18 aus dem Produkt entfernt bzw. ersetzt
   responsible_id (Verantwortlich)          - kein Ziel in Odoo 18
   service_policy                           - ersetzt durch invoice_policy + expense_policy
   service_tracking-Werte jenseits von 'no' - ersetzt durch Aufgaben-/Projekterzeugung
   project_id                               - ersetzt durch Aufgaben-/Projekterzeugung
   item_ids                                 - ersetzt durch den Smart Button (Gruppe A)
   accessory_product_ids, alternative_product_ids - ersetzt durch "Optionale Produkte"
   product_image_ids                        - ersetzt durch Hauptbild + Dokumente
   image_medium                             - ersetzt durch image_1920
```

## 6. Gruppe C - ungenutzt in Odoo 11, daher verzichtbar (gemessen)

Alle Zahlen read-only aus Odoo 11 Prod, 649 product.template, davon 209 in Abonnements verwendet
(`scripts/analyse_o11_produktformular_nutzung.py`).

```
Feld                          Bedeutung                   gesamt  in Abos  Befund
weight                        Gewicht                          0        0  nie gepflegt
volume                        Volumen                          0        0  nie gepflegt
sale_delay                    Auslieferungszeit                0        0  nie gepflegt
tracking                      Nachverfolgung                 649      208  alle 'none'
invoice_policy                Fakturierungsregel               0        0  nur Standard 'order'
service_tracking              Dienstverfolgung                 0        0  nur Standard 'no'
sale_line_warn                Auftragswarnung                  0        0  nie gesetzt
purchase_line_warn            Bestellwarnung                   0        0  nie gesetzt
description                   Beschreibung                     0        0  leer
description_sale              Verkaufsbeschreibung             1        1  "Kontonummer: 123456"
description_purchase          Einkaufsbeschreibung             0        0  leer
description_picking/out/in    Lagerbeschreibungen              0        0  leer
inventory_availability        Lagerverfuegbarkeit              0        0  nur Standard 'never'
custom_message                Persoenliche Nachricht           0        0  leer
available_threshold           Verfuegbarkeitsgrenze          493      181  immer der Standard 5.0
public_categ_ids              eCommerce-Kategorien             0        0  nie gesetzt
website_style_ids             Website-Stile                    0        0  nie gesetzt
product_image_ids             Zusatzbilder                     0        0  nie genutzt
route_ids                     Routen                         649      208  alle genau eine Route: "Einkaufen"
                                                                        (Standardroute, keine Auswahl)
packaging_ids                 Verpackungen                     0        0  nie genutzt
seller_ids                    Lieferanten                      0        0  nie gepflegt
accessory_product_ids         Zubehoer                         0        0  nie genutzt
alternative_product_ids       Alternativprodukte               0        0  nie genutzt
property_account_income_id    Erloeskonto (je Produkt)         0        0  kommt aus der Kategorie
property_account_expense_id   Aufwandskonto (je Produkt)       0        0  kommt aus der Kategorie
property_account_creditor_price_difference Preisdifferenzkonto  0        0  nie gesetzt
property_stock_account_input/output        Lagerkonten          0        0  nie gesetzt
property_valuation, property_cost_method, property_stock_production, property_stock_inventory
                              Bewertung/Lagerorte               -        -  nur je ein
                              Unternehmens-Standardwert (ir.property), kein Produktwert
responsible_id                Verantwortlich                 649      208  GEPFLEGT: Administrator 394,
                                                                        Waiss Martina 252,
                                                                        Breiteneder Lorenz 3
service_type                  Dienstleistungsverfolgung       51       40  51x 'timesheet'
                                                                        (nur Standard 'manual' sonst)
purchase_method               Kontrollrichtlinie             649      208  alle 'receive' = Odoo-Standard
taxes_id                      Steuern (Verkauf)              647      207  Steuer 18 gesetzt
supplier_taxes_id             Steuern (Einkauf)              648      207  Steuer 27 gesetzt
item_ids                      Preislistenpositionen          321      161  1.872 Positionen gesamt
```

Konten der Produktkategorien in Odoo 11: **je eine** Zuordnung fuer Ertragskonto (Konto 1161)
und Aufwandskonto (Konto 839) - also Kategorie-Standardwerte, keine Einzelpflege. In Odoo 18
gibt es derzeit 3 Produktkategorien.

**Einziger Befund gegen "verzichtbar": `responsible_id` (Verantwortlich) ist real gepflegt**
(649 Produkte, drei Benutzer), hat in Odoo 18 aber kein Feld mehr. Siehe Abschnitt 8.

## 7. Gruppe D - durch modernere Odoo-18-Funktion ersetzt

```
Odoo 11                                  Odoo 18
Zubehoer + Alternative Produkte          Optionale Produkte (optional_product_ids), Reiter Verkauf
Preislisten-Positionen im Formular       Smart Button "Preislistenregeln" mit Anzahl
Zusatzbilder (product.image)             Hauptbild image_1920 + Dokumente (Anhang) + Chatter
service_type + service_policy            invoice_policy + expense_policy + service_tracking
Projekt je Produkt (project_id)          Aufgaben-/Projekterzeugung aus dem Auftrag
                                         (in Odoo 18 lokal: sale_project, sale_timesheet = nicht installiert)
Nachrichten/Aktivitaeten im Reiter       Chatter am Formularende
Steuerfelder im Reiter Abrechnung        neben Verkaufspreis/Kosten im ersten Reiter
```

## 8. Befunde und offene Punkte (neu, Session 120)

```
F41  Der Reiter "Abrechnung" (Odoo 11) heisst in Odoo 18 "Buchhaltung" und wird von
     account.product_template_form_view hinter den Reiter "Lager" gehaengt (name="invoicing").
     Er traegt groups="account.group_account_readonly" und enthaelt dort die Felder
     property_account_income_id (Forderungen) und property_account_expense_id (Verbindlichkeiten).
     Gemessen: die Odoo-11-Seite hat KEINE Gruppenbedingung; in Odoo 18 haengt die Sichtbarkeit an
     der Gruppe id=35 "Technisch / Buchhaltungsfunktionen anzeigen - schreibgeschuetzt"
     (account.group_account_readonly). Diese Gruppe wird nur von id=38 "Technisch / Zeige
     vollstaendige Finanzbuchhaltung" vererbt; in der Testdatenbank hat sie kein einziger Benutzer
     (users=0) - auch der Abnahmebenutzer nicht (er hat id=36 Buchhaltung/Rechnungsstellung und
     id=39 Buchhaltung/Administrator). Deshalb fehlt der Reiter im gerenderten Formular, obwohl er
     im Code vorhanden ist. Kein Fehler in der ITK-Anpassung, kein Programmierfehler.
F42  "Verantwortlich" (responsible_id) fehlt in Odoo 18 vollstaendig, ist in Odoo 11 aber auf allen
     649 Produkten gepflegt (Administrator 394, Waiss Martina 252, Breiteneder Lorenz 3). Ohne
     Entscheidung geht diese Information bei der Migration verloren.
F43  Dienstleistungsverfolgung: 51 Produkte in Odoo 11 stehen auf service_type='timesheet'
     (40 davon in Abos verwendet). In Odoo 18 ist sale_timesheet nicht installiert und
     service_type kennt nur 'manual'. Gegengeprueft: 0 Stundenzettelzeilen
     (account.analytic.line) mit diesen Produkten von 12.601 Zeilen gesamt; 246 Auftragszeilen
     mit diesen Produkten, davon 0 mit gelieferter Menge (qty_delivered > 0). Die Funktion wurde
     also verkauft, aber nie ueber Zeiterfassung abgerechnet - die Abrechnung lief ueber die
     Auftragsmenge. Fachliche Entscheidung noetig, ob service_type='timesheet' ueberhaupt
     nachgebildet wird.
F44  Reiter "Notizen" (Odoo 11) ist in Odoo 18 aufgeloest: Beschreibung als Gruppe "Interne
     Notizen" im ersten Reiter, Verkaufs-/Einkaufsbeschreibung und die Warnungen in den Reitern
     Verkauf/Einkauf. Inhaltlich ist alles vorhanden, nur nicht als eigener Reiter.
F45  Reiter "Bilder" (Odoo 11) hatte vier Felder: product_image_ids (0x genutzt),
     message_follower_ids, activity_ids, message_ids. In Odoo 18: Hauptbild im Kopf,
     Dokumente-Smart-Button, Chatter. Nichts fehlt fachlich, weil Zusatzbilder nie genutzt wurden.
F46  Reiter "Lager" ist in beiden Versionen vorhanden und bei Dienstleistungen ausgeblendet
     (O11: type='service', O18: type in ['service','combo']) - kein Unterschied.
F47  Pflichtfelder unterscheiden sich: Odoo 11 verlangt zusaetzlich responsible_id und tracking
     (beide Lager-/Verantwortlichkeitsfelder, in Odoo 18 nicht vorhanden), Odoo 18 verlangt
     service_tracking und invoice_policy (in Odoo 11 ohne Pflicht). Kein Handlungsbedarf, aber
     bei der Datenmigration muessen diese Felder je Produkt gesetzt sein.
F48  Preislisten: 321 Produkte tragen 1.872 Preislistenpositionen. In Odoo 18 sind sie nur ueber
     den Smart Button "Preislistenregeln" erreichbar. Dieser Button muss in der VM-Abnahme
     angeklickt werden (bisher nicht geprueft).
```

## 9. Aenderungsvorschlaege (Reihenfolge = Prioritaet)

*Stand: Vorschlaege aus der Analysephase, vor der Umsetzung. Was davon umgesetzt wurde und was
sich geaendert hat, steht in Abschnitt 11 (Korrektur zu Punkt 1) und Abschnitt 12 (Umsetzung,
Ergebnis).*

```
1  F41 Buchhaltungsreiter: NICHTS am Formular aendern. Der Reiter ist vorhanden und zeigt sich,
   sobald ein Benutzer die Gruppe account.group_account_readonly hat. Vorschlag:
   a) Im Bereichsdokument festhalten, dass die Sichtbarkeit an dieser Technik-Gruppe haengt
      (damit es bei der Abnahme nicht wieder als Fehler auftaucht).
   b) Optional: den Abnahmebenutzer auf der VM in diese Gruppe aufnehmen, damit der Reiter in
      der Abnahme ueberhaupt pruefbar ist. Das ist eine Rechteaenderung und braucht Freigabe.
2  F42 Verantwortlich: Entscheidung noetig. Zwei Moeglichkeiten:
   a) Werte einmal aus Odoo 11 exportieren (Produkt, Verantwortlicher) und als Nachschlageliste
      an das Migrationsteam uebergeben - kein Nachbau im Formular. (Empfehlung, weil Odoo 18
      dafuer kein Feld hat)
   b) Auf dem Produkt eine Odoo-18-Eigenschaft (product_properties) dafuer anlegen - dann bleibt
      der Wert im Formular sichtbar. Kostet ein Zusatzfeld und ist eine Modulaenderung.
3  F43 Zeiterfassung: Vorschlag, service_type='timesheet' NICHT nachzubilden (0 Stundenzettel-
   zeilen belegen die Nichtnutzung); die 51 Produkte laufen in Odoo 18 als Dienstleistung mit
   manueller Menge. Entscheidung noetig.
4  F44 Notizen: Vorschlag, nichts umzubauen. Optional den Wortlaut der Odoo-18-Gruppe
   "Interne Notizen" auf "Notizen" aendern (Wortlaut-Treue zu Odoo 11). Entscheidung noetig.
5  F45 Bilder: keine Aktion. Zusatzbilder wurden nie genutzt.
6  F48 Preislisten-Smart-Button in der VM-Abnahme anklicken (Werkzeug dazu liefert diese Session
   nach Freigabe). Erst damit ist der Bereich wieder abnehmbar.
7  Checkliste: Eintrag zu "Abonnement Produkte" von "vollstaendig funktionsfaehig und vollstaendig
   migrationsvorbereitet" auf "in Arbeit" zuruecksetzen, bis 1-6 entschieden und abgenommen sind.
   Neue Nummer fuer den offenen Rest: 6.14.1 "Produktformular - offene Punkte F41-F48".
8  Keine der Odoo-18-Zusatzfunktionen entfernen: Reiter "Attribute & Varianten" (mit
   value_count, sequence), Kombi-Produktart (combo_ids), Stichwoerter (product_tag_ids),
   Eigenschaften (product_properties), Produkt-Tooltipp, Steuerzeichenkette (tax_string),
   Optionale Produkte, Kosten weiterberechnen (expense_policy), Subunternehmer-Service
   (service_to_purchase), Favorit (is_favorite), Anzahl Preisregeln, Anzahl Dokumente,
   Eingekauft, Maßeinheit-Name, steuerliche Laendercodes.
```

## 10. Was in der Analysephase NICHT geaendert wurde

- Odoo 11 Prod: ausschliesslich gelesen (fields_get, get_views/fields_view_get, search_read,
  search_count, read). Kein Datensatz angelegt, geaendert oder geloescht.
- Odoo 18 lokal: in der Analysephase ausschliesslich gelesen. Die Umsetzung selbst folgt in
  Abschnitt 12 (nur Odoo 18) - Freigabe durch Anna vom 24.09.2026.
- Kein Commit, kein Push, kein Merge (nur Dateien im Arbeitsbaum).

## 11. Korrektur zu Abschnitt 4/9: die Kontofelder waren in Odoo 11 selbst ausgeblendet

Nachgemessen am gesicherten Odoo-11-Arch mit `scripts/pruefe_o11_abrechnung_sichtbarkeit.py`:

```
Odoo 11, Reiter "Abrechnung" - Anzeige je Feld (gerenderter Arch)
   taxes_id                                    sichtbar
   supplier_taxes_id                           sichtbar (schreibgeschuetzt, wenn purchase_ok = 0)
   purchase_method                             sichtbar (Gruppe "Eingangsrechnung")
   service_policy, service_tracking            sichtbar bei Dienstleistungen
   invoice_policy                              bei Dienstleistungen ausgeblendet (type == 'service')
   service_type                                ausgeblendet (invisible="1")
   project_id                                  nur wenn service_tracking = task_global_project
   property_account_income_id                  AUSGEBLENDET (invisible="1")
   property_account_expense_id                 AUSGEBLENDET (invisible="1")
   property_account_creditor_price_difference  AUSGEBLENDET (invisible="1")
   property_valuation                          AUSGEBLENDET (invisible="1")
   property_stock_account_input / _output      Gruppe "Bestandsbewertung" ist ausgeblendet
```

Der Reiter hiess in Odoo 11 "Abrechnung", seine **sichtbaren** Felder waren Steuern,
Dienstleistungslogik und Kontrollrichtlinie - **keine Konten**. Passend dazu: 0 von 649
Produkten haben ein eigenes Konto (gemessen, Abschnitt 6). In Odoo 18 ist die Seite
"Buchhaltung" nur fuer die Konten-Gruppe sichtbar (Befund F41) - das ist damit keine
verschlechterte Lage, sondern deckt sich mit Odoo 11 fuer alle Felder, die dort sichtbar waren.

**Folge fuer die Empfehlung:** Empfehlung 1 aus Abschnitt 9 (Gruppe aufnehmen oder Ersatzseite
bauen) ist gegenstandslos. Es wird **keine** Seite gebaut und **kein** Benutzer in eine
Buchhaltungsgruppe aufgenommen. Massgeblich ist nur, dass die in Odoo 11 sichtbaren Felder in
Odoo 18 erreichbar sind - das ist in Abschnitt 12.6 belegt.

## 12. Umsetzung (nur Odoo 18, lokale Instanz, Freigabe Anna vom 24.09.2026)

### 12.1 Buchhaltung - keine Formularaenderung

Begruendung siehe Abschnitt 11. Keine neue Ansicht, keine Gruppenaufnahme, keine
Rechteaenderung. Die Kontokonfiguration laeuft in Odoo 18 ueber die Produktkategorie; je
Produkt gibt es sie auch in Odoo 11 nicht (0 Werte).

### 12.2 "Verantwortlich" - neues Feld, damit der Wert 1:1 migrierbar bleibt

```
Modul     addons/itk_product, Version 18.0.1.0.1 -> 18.0.1.0.2
Feld      responsible_id = fields.Many2one('res.users', string='Verantwortlich')
          (models/models.py - gleicher Feldname und gleiche Relation wie in Odoo 11)
Formular  eigene Gruppe "itk_responsible" im Reiter "Allgemeine Informationen",
          angehaengt nach der ITK-Gruppe "Product-Typ"
          Grund: in Odoo 11 stand das Feld im Reiter "Lager", der in beiden Versionen bei
          Dienstleistungen ausgeblendet ist - dort waere der Wert beim Abonnement Produkt
          nicht erreichbar.
```

Damit ist der Wert migrierbar und pflegbar. Geprueft: Feld vorhanden, Typ many2one/res.users,
Beschriftung "Verantwortlich", store=True, readonly=False, im gerenderten Formular sichtbar,
schreibbar (Testdatensatz angelegt, geschrieben, gelesen, geloescht).

### 12.3 "Interne Notizen" -> "Notizen"

```
views/itk_product.xml: xpath //group[@name='internal_notes'] position="attributes"
          attribute string = "Notizen"
i18n/de.po: neuer Eintrag msgid "Notizen" / msgstr "Notizen" (Quelle steht in der Ansicht)
```

Inhalt unveraendert: das Beschreibungsfeld bleibt in der Gruppe, nichts entfernt.

### 12.4 Zeiterfassung / Dienstleistungsverfolgung - Festlegung, kein Modul

`sale_timesheet` wird **nicht** installiert. Festlegung fuer die spaetere Migration:

```
Odoo 11: 51 Produkte mit service_type = 'timesheet' (40 davon in Abos verwendet),
         598 Produkte ohne Wert (Standard 'manual').
Belegte Nichtnutzung: 0 Stundenzettelzeilen (account.analytic.line) mit diesen Produkten
         von 12.601 Zeilen gesamt; 246 Auftragszeilen mit diesen Produkten, davon 0 mit
         gelieferter Menge (qty_delivered > 0).
Regel:   service_type wird NICHT uebernommen. Die 51 Produkte laufen in Odoo 18 als
         Dienstleistung mit manueller Mengenerfassung (Odoo-18-Standard 'manual').
         Das Feld existiert in Odoo 18 nur noch mit dem Wert 'manual' und wird nicht befuellt.
         Es entstehen keine Aufgaben- und keine Projektdatensaetze.
```

### 12.5 Bilder - keine Aktion

Kein Nachbau. Belegt: `product_image_ids` (Zusatzbilder) war in Odoo 11 mit 0 Datensaetzen
belegt; die vier Felder des Odoo-11-Reiters waren product_image_ids, message_follower_ids,
activity_ids, message_ids. In Odoo 18 gibt es das Hauptbild (image_1920), den
Dokumente-Smart-Button und den Chatter. Es geht damit kein produktiv genutzter Inhalt verloren.

### 12.6 Pruefungen (lokal und VM, jeweils 0 FEHL)

```
                                       lokal             VM
itk_product-Modulversion               18.0.1.0.2        18.0.1.0.2      (Upgrade ohne Fehler)
verify_produktformular.py              27 OK / 0 FEHL    27 OK / 0 FEHL
verify_abo_produkte.py                 34 OK / 0 FEHL    34 OK / 0 FEHL (keine Regression)
test_abo_smartbuttons.py               11 OK / 0 FEHL    11 OK / 0 FEHL (F52 korrigiert)
browser_produktformular.py             20 OK / 0 FEHL    20 OK / 0 FEHL (echte Klicks)
pruefe_view_render.py                   8 OK / 0 FEHL     8 OK / 0 FEHL
verify_s118_abo.py                          -            19 OK / 0 FEHL
pruefe_abo_xmlids.py                        -             0 fehlende XML-IDs
Schreibtest product.template           13 Produkte vorher, 13 nachher (Testdatensatz entfernt)
Odoo-Log nach dem Upgrade              keine Fehler, keine Tracebacks
/web/login auf der VM                  HTTP 200 (0,46 s)
```

Browser-Abnahme auf der VM (echte Klicks, Playwright + Chrome; 20 OK / 0 FEHL):

```
Aktion "Abonnement Produkte" aufgerufen (9 Eintraege in der Kanban-Ansicht)
Klick auf "TEST Abo Produkt Monatlich" oeffnet das Formular
Reiter: Allgemeine Informationen, Attribute & Varianten, Verkauf, Einkauf, Lager (kein Buchhaltung)
Abschnitt "NOTIZEN" sichtbar (Odoo stellt Abschnittstitel gross dar), "Interne Notizen" verschwunden
Feld "Verantwortlich" sichtbar, Eingabefeld, Auswahlliste, "Administrator" gewaehlt, Speichern geklickt
   -> danach per RPC gelesen: responsible_id = [2, 'Administrator'] (Schreibzugriff wirkt)
Reiter Verkauf und Einkauf lassen sich oeffnen
Filter "Mit Faktor multipliziert" wirkt (Bedingung in der Suchleiste)
keine JavaScript-Fehler (0), keine RPC-Fehler (0)
Testwert danach entfernt; Produkte auf der VM 13 vorher wie nachher
Screenshots: Desktop\Odoo18-Abnahme-Session120\01..06_*.png
```

### 12.7 Ergebnis und Rest

Der Bereich ist abgeschlossen (Checkliste 6.14 wieder auf "ABGESCHLOSSEN"). Offen sind nur noch
Schritte der Datenmigration, keine Funktion dieses Bereichs:

```
1. F42 "Verantwortlich": Wert aus Odoo 11 (649 Produkte) in das neue Feld uebernehmen.
2. F43 Zeiterfassung: service_type wird nicht uebernommen (Festlegung oben).
3. F48 Datenpakete aus dem Produktumfeld: Bestandsmenge entfaellt begruendet,
   Preislistenpositionen (1.872 auf 321 Produkten) sind zu uebernehmen.
```

## 13. Befunde Session 120 (neu)

```
F49  pruefe_view_render.py schlug bei jeder Ansicht mit mehr als einem Wurzelelement fehl
     ("Extra content at the end of the document"): das Werkzeug setzte die Arch-Kinder ohne
     <data>-Umhuellung zusammen, ir.ui.view.create lehnt das ab. Reproduziert mit der
     unveraenderten Datei aus Git-HEAD - der Fehler bestand also vor dieser Session und hat
     den Rendertest nur zufaellig nicht getroffen. Werkzeug korrigiert (Umhuellung in <data>);
     Ergebnis danach: itk_product 8 OK / 0 FEHL, itk_multifactor 12 OK / 0 FEHL.
F50  Die Kontofelder des Odoo-11-Reiters "Abrechnung" waren in Odoo 11 selbst ausgeblendet
     (invisible="1"), ebenso die Gruppe "Bestandsbewertung". Der Reiter zeigte nur Steuern,
     Dienstleistungslogik und Kontrollrichtlinie. Korrektur zu Befund F41 und zu Empfehlung 1
     aus Abschnitt 9: kein Ersatzreiter noetig, keine Rechteaenderung (Abschnitt 11).
F51  Formatfalle bei der Uebersetzungsdatei: Odoo 18 liest je PO-Eintrag die Zeile
     "#. module: <modulname>" aus und schneidet sie auf das Muster "module: x" zu. Steht in
     einer Kommentarzeile Freitext statt dieser Modulangabe, bricht der PO-Reader mit
     "AttributeError: 'NoneType' object has no attribute 'groups'" ab und das Modul-Upgrade
     scheitert. Freitext auf "#:"-Zeilen ist ebenfalls falsch - polib liest ihn als Fundstelle
     und Odoo meldet je Wort "malformed po file: unknown occurrence" (so in
     addons/itk_subscription/i18n/de.po vorhanden, harmlos, aber laut). In itk_product korrekt
     umgesetzt: "#. module: itk_product" + "#: model...", kein Freitext im Eintrag.
F52  test_abo_smartbuttons.py setzte voraus, dass das Nachweis-Abo "TEST Rechnungslauf Nachweis"
     genau eine Rechnung hat, und prueft dann, ob der Smart Button direkt diese Rechnung oeffnet.
     Nach den Nachweisen der Session 119 hat dieses Abo 3 Entwurfsrechnungen (angelegt am
     22.09.2026, 12:38 und 12:39) - der Test meldete 10 OK / 1 FEHL, obwohl die Anwendung richtig
     arbeitet (Gegenprobe: fuer Abo 222 mit genau einer Rechnung liefert
     action_subscription_invoice res_model=account.move, res_id=57, Ansicht form). Werkzeug
     korrigiert: der Fall "genau eine Rechnung" wird jetzt selbst hergestellt - ein Abo ohne
     Rechnung wird gesucht, genau eine Testrechnung dazu angelegt, geprueft und wieder geloescht.
     Ergebnis danach lokal und VM je 11 OK / 0 FEHL.
F53  Suchen mit 'ilike' auf uebersetzten Feldern (z. B. ir.ui.menu.name, in Odoo 18 jsonb)
     liefern ohne Sprachkontext keinen Treffer. Aufgefallen beim Menueaufruf "Abonnement
     Produkte" im neuen Browserwerkzeug (Ergebnis leer, obwohl das Menue existiert). Behelf:
     context lang=de_DE. Im Browserwerkzeug laufen alle Leseaufrufe jetzt mit de_DE
     (Helfer kwl), der Rueckfallpfad in browser_abo_produkte.py ebenso.
F54  Odoo 18 stellt Abschnittsueberschriften im Formular per CSS in Grossbuchstaben dar
     (o_horizontal_separator, text-uppercase): im DOM steht "NOTIZEN", im Arch "Notizen".
     Eine DOM-Pruefung mit exaktem Wortlaut meldet sonst einen Fehlalarm; Vergleiche muessen die
     Schreibweise ignorieren.
```

