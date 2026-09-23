# Abonnements: Teil 14 - Abonnement Produkte

Stand: 22.09.2026 (Session 119). Odoo 11 Prod ausschliesslich read-only. Keine Produktivdaten migriert.
Grundlage: `docs/uebergabe-session-118-abonnements.md`, Abschnitt 4.

## 1. Auftrag

Letzter offener Unterbereich des Bereichs Abonnements: **Abonnements -> Abonnement Produkte**.
In der Uebergabe standen zwei offene Entscheidungen und drei Arbeitsschritte:

1. Entscheidung `to_multiply_by_factor` (Formular entfernen?) - **Anna: JA, entfernen.**
2. Entscheidung Lager-Modul `stock` (installieren?) - **Anna: erst pruefen, ob Lager fachlich
   verwendet wurde; nicht nur wegen zweier Spalten installieren.**
3. Erweiterung der Wurzel-Produktliste in `itk_multifactor`, Suchansicht ausliefern,
   VM-Browserabnahme, danach Gesamtbereich gegenpruefen.

## 2. Was in Odoo 11 wirklich vorhanden ist (read-only gemessen)

```
Aktion 514 "Subscription Products" (Menue Abonnement Produkte)
   res_model product.template | view_mode kanban,tree,form | search_view_id 1345
   context {"default_recurring_invoice": true, "search_default_filter_recurring": true,
            "default_type": "service"}
Listenansicht product.template (tree), Spalten in Reihenfolge:
   sequence (handle), default_code, name, is_multi_factor_product, list_price, standard_price,
   product_type_id (string "Status"), categ_id, [type auskommentiert], qty_available,
   virtual_available, uom_id (invisible), active (invisible)
   decoration-danger bei virtual_available < 0
Beschriftungen (de_DE): default_code "Interne Referenz", categ_id "Interne Kategorie",
   uom_id "Mengeneinheit", is_multi_factor_product "To multiply by Factor(per 1000)" (englisch),
   product_type_id "Product-Type" (englisch)
Suchansicht: filter_products, filter_recurring, sechs feste Filter "Service Type ..." mit
   Domains auf Einzelwerte von product_type_id (Consulting, Onlineservice, Software-Lösung,
   Plattform, Hardware, Förderprojekt), zusaetzlich die Standardfilter des stock-Moduls
   (real_stock_available, real_stock_exhausted, real_stock_negative); keine Gruppierungen
Felder: is_multi_factor_product existiert (1 Produkt mit true: "DSGVO-Verarbeitungsverzeichnis
   Preis pro angefangene 1.000 Einwohner"), to_multiply_by_factor existiert NICHT,
   qty_multiplication_factor liegt auf sale.order.line (1.366 Zeilen != 1) und
   sale.subscription.line (560 Zeilen != 1)
Produkte: 649 Templates / 648 Produkte, Produktarten (Feld type): consu 152, service 47,
   general 273, onlineservice 74, platform 94, sw 9; product_type_id: Onlineservice 314,
   Plattform 56, Consulting 19, Software-Lösung 18, Hardware 3, leer 239
```

## 3. Befund Lager (Entscheidung: stock wird NICHT installiert)

Read-only geprueft mit `scripts/analyse_o11_lager.py` und `scripts/analyse_o11_lager_teil2.py`
(Odoo 11 wird dabei nur gelesen):

```
Modul stock                  installed (11.0.1.1), sale_stock 11.0.1.0, stock_account 11.0.1.1,
                             delivery uninstalled
Lagerhaeuser                 1 (WH "My Company") - Standardanlage, nie umbenannt
Lagerorte                    13 gesamt, davon 1 intern (WH/Stock), 1 Lieferant, 1 Kunde, 2 Inventur
stock.move                   327: 288 assigned + 39 storniert, 0 erledigt
stock.move.line              288, alle assigned, 0 erledigt
stock.picking                252: 224 assigned + 28 storniert, 0 erledigt
                             alle Typ "My Company: Delivery Orders" (WH/OUT/...),
                             Herkunft = Verkaufsauftragsnummern (A-1900948 ...)
stock.quant                  0 Zeilen (auch 0 mit Menge != 0)
Bestellvorschlaege           0 (stock.warehouse.orderpoint)
Produkte mit Bestand != 0    0 von 649 (qty_available > 0: 0, < 0: 0)
virtual_available != 0       82 Produkte, ALLE negativ; incoming_qty 0, outgoing_qty 82
Product-Typ "Lagerartikel"   0 (type = 'product'); alle Produkte sind consu/service/ITK-Arten
In Abos genutzte Produkte    209, davon 0 mit Bestand != 0
Verkaufsauftraege            2.461 (2.309 "sale", 147 storniert, 5 Entwurf);
                             1 Auftragszeile mit qty_delivered != 0
```

**Auswertung:** Es gab in Odoo 11 nie einen Lagerbestand und nie eine erledigte Lagerbewegung.
Die 252 Lieferauftraege sind automatische Nebenprodukte des Bestaetigens von Verkaufsauftraegen
(sale_stock) und wurden nie bearbeitet; die 327 Bewegungen stehen auf "assigned" oder
"storniert". Die 82 negativen "Geplanten Bestandsmengen" sind ausschliesslich die Summe dieser
offenen Ausgaenge - eine Ableitung, kein fachlicher Wert. Lagerorte, Lagerhaeuser und Bewegungen
wurden also nicht produktiv genutzt.

**Konsequenz:** Das Modul `stock` wird nicht installiert. `qty_available` (Bestandsmenge) und
`virtual_available` (Geplante Bestandsmenge) haben damit in Odoo 18 kein Ziel und entfallen.
Begruendung: In Odoo 11 zeigten beide Spalten fuer alle 649 Produkte Bestand 0; die geplante
Menge war nur das negative Gegenstueck nie ausgefuehrter Lieferauftraege. Es gibt keinen
Produktivwert, der in Odoo 18 fehlen wuerde. Wuerde `stock` nur fuer diese zwei Spalten
installiert, entstuenden in Odoo 18 neue Lagerorte, neue Menues, ein neues Rechte-/Bewertungs-
und Liefermodul sowie Aenderungen an Produktformular und Auftragsabwicklung - ohne fachlichen
Gegenwert. (Zur Einordnung: in Odoo 11 waere das Lager-Modul fachlich ebenso verzichtbar gewesen;
es lief dort nur mit, weil es Standardbestandteil der Verkaufsinstallation ist.)

## 4. Umsetzung in Odoo 18

### 4.1 `itk_multifactor` 18.0.1.1.1 (Listenansicht, Suchansicht, Formular)

```
views/itk_product.xml
   Wurzel-Produktliste product.product_template_tree_view
      is_multi_factor_product  optional="show"   (bleibt vor dem Verkaufspreis)
      categ_id                 string="Interne Kategorie", optional="show"
   NEU: product.template.search.abo.produkte (inherit product.product_template_search_view)
      Filter        filter_multi_factor      "Mit Faktor multipliziert"
                    filter_abo_aktiv         "Aktive Abonnement Produkte"
                    (erhalten: Produkte, Abonnement Produkte, Dienstleistungen, Güter, Kombi,
                     Verkauf, Einkauf, Favoriten, Warnungen, Archiviert)
      Gruppierung   Status (product_type_id), Mit Faktor multipliziert
                    (erhalten: Produktart, Produktkategorie)
   Produktformular: is_multi_factor_product als eigene Zeile unter dem Verkaufspreis
__manifest__.py  depends um 'itk_product' ergaenzt (product_type_id fuer Liste und Suche)
```

### 4.2 `itk_product` 18.0.1.0.1 (Formular bereinigt)

`to_multiply_by_factor` ist aus dem Produktformular entfernt (XPath in `views/itk_product.xml`).
Das Feld bleibt in der Datenbank und an den Produkten unveraendert - es wird nur nicht mehr
angezeigt. Belegt: das Feld existiert in Odoo 11 **nicht** (weder product.template noch
product.product); es ist eine beim Migrieren entstandene Dublette zu `is_multi_factor_product`,
hat 0 Verwendungen im Code und wurde nie beschrieben.

### 4.3 Bewusste Abweichungen

```
"Service Type ..."-Filter (Odoo 11)   NICHT nachgebaut: sie haben dort einzelne Werte der
                                      ITK-Produktart fest verdrahtet. Odoo 18 leistet das
                                      ueber die Gruppierung "Status" (product_type_id).
Bestandsfilter (Verfuegbare Produkte, Bestandsaufloesung, Bestandsreichweite)
                                      NICHT nachgebaut: kamen aus dem stock-Modul und
                                      haben ohne Lager keine Grundlage.
Bestandsmenge / Geplante Bestandsmenge
                                      entfallen (Abschnitt 3).
default_code im Formular              Odoo 18 (Basismodul product) beschriftet das Feld im
                                      Formular "Referenz"; die Liste zeigt wie Odoo 11
                                      "Interne Referenz". Standardbeschriftung bleibt -
                                      dokumentiert statt umbenannt.
product_type_id im Formular           "Produkttyp" (Odoo 11: "Product-Type"), in der Liste
                                      "Status" wie in Odoo 11.
Spalte "Produktart"                   Odoo 18 blendet Spalten nicht mehr ueber invisible="1"
                                      aus (dafuer gibt es column_invisible) - die in
                                      itk_product gesetzte Ausblendung des Feldes type wirkt
                                      in der Liste daher nicht mehr. Die Spalte bleibt als
                                      sinnvolle Odoo-18-Zusatzspalte sichtbar
                                      (Werte: Dienstleistung, Verbrauchsgüter).
```

## 5. Befunde (neu, Session 119)

```
F35  Faktor-Feld im Produktformular war unsichtbar. Der Anker
     //field[@name='list_price'] trifft in Odoo 18 das Feld INNERHALB von
     <div name="list_price_uom"/>; is_multi_factor_product landete dadurch in der Preiszeile
     und wurde im Formular nicht dargestellt (auf der VM im Browser belegt, Screenshot 66 der
     ersten Abnahme). Behoben: Anker //div[@name='list_price_uom'] position=after.
F36  pruefe_abo_xmlids.py meldete 12 "fehlende XML-IDs", die keine sind: das Muster ref="..."
     traf auch href="..." (z.B. www.odoo.com in Mail-Templates). Werkzeug korrigiert
     (Wortgrenze + Filter auf gueltige modul.name-Kennungen); Ergebnis jetzt: 0 fehlende IDs.
F37  test_abo_smartbuttons.py waehlte den Fall "keine Rechnung" ueber eine Suche auf
     invoice_count - ein NICHT gespeichertes Berechnungsfeld. Odoo 18 liefert dabei keinen
     belastbaren Treffer (es kam Abo 172 zurueck, das tatsaechlich 4 Rechnungen hat) und der
     Test schlug fehl, obwohl die Anwendung richtig arbeitet (Abo 185 ohne Rechnungen liefert
     korrekt ir.actions.act_window_close). Werkzeug korrigiert: Auswahl ueber read().
F38  Versionsangaben in den Session-118-Dokumenten (itk_subscription 18.0.1.2.3 bis 18.0.1.2.6)
     sind im Repo nicht belegt: Git-Historie und DB stehen auf 18.0.1.2.1 (1.0.0 -> 1.1.0 ->
     1.2.0 -> 1.2.1). Die Code-Aenderungen der Teile 10-13 sind vorhanden, nur die
     Versionsnummer wurde nie hochgesetzt. Korrigiert in PROJECT_KNOWLEDGE.md und in der
     Uebergabe (dort als datierter Hinweis).
F39  Sicherheitsfund: scripts/browser_abo_pruef.py enthielt das Kennwort der Odoo-11-Prod-
     Instanz im Klartext. Entfernt - Zugangsdaten kommen jetzt aus der gitignorierten .env
     (ODOO11_USER/ODOO11_PWD). Kein Eingriff in Odoo 11, keine History-Umschreibung.
F40  browser_abo_abschluss.py prueft den Ziel-Smart-Button ueber das URL-Muster ("account.move"
     in der Adresse). Odoo 18 nutzt sprechende URLs (/odoo/sale.subscription/172/invoicing), die
     Pruefung schlug deshalb fehl, obwohl der Klick funktioniert - im Browser nachgestellt: der
     Button "4 Rechnungen" oeffnet die Liste "Ausgangsrechnungen" mit genau 4 Rechnungen in EUR.
     Zusaetzlich forderte der Test "ein laufendes Abo mit Verkaufsauftrag", waehlte aber das erste
     laufende Abo der Liste (Abo 172 ohne Auftrag). Beides korrigiert: Zielansicht wird jetzt ueber
     Brotkrumen/Inhalt geprueft, die Auswahl erfolgt per Suche auf state=open mit Auftrag.
     Ergebnis danach 55 OK / 0 FEHL.
```

## 6. Pruefungen

Werkzeuge (alle im Repo unter `scripts/`):

```
vergleich_abo_produkte.py --instanz o11|vm|lokal   Bestandsaufnahme O11/O18
analyse_o11_lager.py, analyse_o11_lager_teil2.py   Lager-Nutzung Odoo 11 (read-only)
dump_o18_ansichten.py                              zusammengefuehrter Odoo-18-Arch (roh)
pruefe_view_render.py                              Testdatensatz anlegen, rendern, loeschen
verify_abo_produkte.py                             Umsetzung Abonnement Produkte (34 Pruefungen)
browser_abo_produkte.py                            Browserabnahme (echte Klicks, Screenshots)
```

```
lokal (Entwicklung)
   RNG beider geaenderter XML-Dateien                        VALID
   pruefe_view_render.py                                     19 OK / 0 FEHL (nach Ankerfix 12 OK / 0)
   upgrade_modules.py  itk_product 18.0.1.0.1                ohne Fehler
                       itk_multifactor 18.0.1.1.0 / 1.1.1    ohne Fehler
   verify_abo_produkte.py                                    34 OK / 0 FEHL
   browser_abo_produkte.py                                   47 OK / 0 FEHL

VM (k001959vsx.ipax.at, verbindliche Abnahmeumgebung)
   Deploy: a07b1d8 -> 4b7389a -> ec2c896 (git pull --ff-only), Container neu gestartet
   upgrade_modules.py  itk_product 18.0.1.0.1                ohne Fehler
                       itk_multifactor 18.0.1.1.0 / 1.1.1    ohne Fehler
   verify_abo_produkte.py                                    34 OK / 0 FEHL
   browser_abo_produkte.py                                   47 OK / 0 FEHL
      Spalten: Produktname, Interne Referenz, Stichwörter, Mit Faktor multiplizieren
      (pro 1.000), Verkaufspreis, Kosten, Status, Interne Kategorie, Produktart, Einheit
      Spaltenauswahl: Ab- und Wiederanwahl von "Interne Kategorie" wirkt
      Suche "Test" liefert das Produkt als Bedingung in der Suchleiste
      Filter: 9 Filter angeboten, "Mit Faktor multipliziert" angeklickt und als Bedingung
      gesetzt; Gruppierungen: 4 angeboten, "Status" angeklickt und als Gruppen dargestellt
      Formular: "Mit Faktor multiplizieren (pro 1.000)" genau einmal sichtbar,
      Preise in EUR, keine JavaScript- und keine RPC-Fehler
      Screenshots: Desktop/Odoo18-Abnahme-Session119/60..66_VM_*.png
   keine Bestandsmenge / Geplante Bestandsmenge in Liste und Suche
```

Gesamtbereich Abonnements erneut gegengeprueft (read-only Werkzeuge + vorhandene Testskripte):

```
verify_s118_abo.py --instanz vm          19 OK / 0 FEHL
pruefe_abo_xmlids.py --instanz vm        0 fehlende XML-IDs (nach Werkzeugkorrektur F36)
test_abo_rechnungslauf.py --instanz vm   13 OK / 0 FEHL
test_abo_manuelle_rechnung.py --instanz vm 16 OK / 0 FEHL
test_abo_smartbuttons.py --instanz vm    11 OK / 0 FEHL (nach Werkzeugkorrektur F37)
browser_abo_abschluss.py --instanz vm   55 OK / 0 FEHL (nach Werkzeugkorrektur F40)
```

Testdatenzustand nach der Pruefung: neue Pruef-Abos und Rechnungsentwuerfe aus den
Testskripten (Zaehler siehe Abschnitt 7), keine Produktivdaten, keine Migration.

## 7. Ergebnis

Der Unterbereich **Abonnement Produkte** ist in Odoo 18 auf der VM im echten Browser
abgenommen: Liste, Spalten, Spaltenauswahl, Suche, Filter, Gruppierungen, Produktformular und
EUR-Darstellung arbeiten ohne RPC- oder JavaScript-Fehler. Alle in Odoo 11 tatsaechlich
verwendeten Listenelemente haben ein Ziel; die einzigen nicht abgebildeten Odoo-11-Spalten
(Bestandsmenge, Geplante Bestandsmenge) sind mit Begruendung entfallen. Die Odoo-18-
Zusatzfunktionen (Kombi-Produktart, Stichwörter, Activities-Anzeige, Spaltenauswahl,
Gruppierung nach Produktart) bleiben erhalten.
