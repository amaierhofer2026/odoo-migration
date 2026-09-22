# Uebergabe Session 118 - Bereich Abonnements (Stand 22.09.2026)

Diese Datei ist die Arbeitsgrundlage fuer die naechste Session. Sie fasst zusammen, was im Bereich
Abonnements fertig ist, was offen ist und wie die offenen Punkte technisch anzugehen sind.

## 1. Gesamtstatus

```
ABONNEMENTS = NOCH NICHT ABGESCHLOSSEN

Fertig und auf der VM abgenommen:
   Modulstatus und Grundstruktur (Teil 1)          itk_subscription ist der Traeger, sale_subscription
                                                   ist ein Enterprise-Katalogeintrag ohne Code
   Feldinventar sale.subscription / .line (Teil 2) 40 bzw. 11 Felder, keine fehlenden Ziele
                                                   Schluessel ist code (eindeutig), name ist es nicht
   Formulare, Reiter, Zustandslogik (Teil 3)       48/48 Browserpruefungen gruen
   Abschluss und Mapping (Teil 4)                  Mapping-Tabelle, keine Transformationen
   Stammdaten (Teil 5)                             1 Vorlage und 26 Beendigungsgruende angelegt
                                                   (lokal und VM), 31 Gruende gesamt
   Zusatzverkaeufe und EUR (Teil 6)                Button "Abonnement-Zusatzverkäufe" ergaenzt,
                                                   Partner/Abos/Angebote auf EUR-Preisliste
   Endabnahme (Teil 7)                             Rechnung als Kundenrechnung (move_type out_invoice)
   Migrationsregeln (Teil 8)                       migration/abo_migrationsregeln.json
   Rechnungserzeugung (Teil 10)                    move_type, Finanzposition, mail-Bruecken behoben
   Smart Button Rechnungen (Teil 11)               Odoo-18-Aktion statt account.action_invoice_tree1
   manueller Rechnungsweg (Teil 12)                Finanzposition ohne Odoo-11-Nachbau
   Reiterbeschriftung (Teil 13)                    "Wiederkehrende Buchungen", upgradefest im Modul

Offen:
   Abonnement Produkte (Teil 14): Suchansicht fertig und validiert, Listenansicht und
   Produktformular offen, zwei Entscheidungen offen (siehe Abschnitt 4)
```

## 2. Behobene Fehler in dieser Session (alle auf der VM nachgewiesen)

```
F34 (Vorgeschichte)     VM setzt deutsche Feldbeschriftungen bei jedem Upgrade zurueck
   -> scripts/apply_crm_labels.py / apply_sale_labels.py nach jedem Upgrade
Fehlende Zugriffsregeln sale.subscription.wizard, .wizard.option, .close.reason.wizard
   -> itk_subscription 18.0.1.2.1, Rechte fuer interne Benutzer und Manager
Rechnung wurde als Buchungssatz angelegt (move_type fehlte) -> Summen 0,00
   -> _prepare_invoice_data setzt jetzt 'move_type': 'out_invoice'
get_fiscal_position / map_account / map_tax: Odoo 11 liefert IDs, Odoo 18 Recordsets
   -> Nachbau entfernt, Finanzposition nur noch als ID am Beleg, Zuordnung macht Odoo
message_post_with_view existiert in Odoo 18 nicht mehr
   -> Bruecke auf message_post_with_source (Werte values -> render_values)
account.action_invoice_tree1 existiert in Odoo 18 nicht mehr
   -> account.action_move_out_invoice_type, views im Listenformat
```

## 3. Werkzeuge (alle im Repo unter scripts/)

```
verify_s118_abo.py                Abschlusspruefung Abos: 19 OK / 0 FEHL (lokal und VM)
test_abo_rechnungslauf.py         Cron-Weg: Rechnung, Termin, kein Duplikat, EUR: 13 OK / 0 FEHL
test_abo_manuelle_rechnung.py     manueller Weg mit Finanzposition: 16 OK / 0 FEHL
test_abo_smartbuttons.py          Smart Buttons (0 / 1 / mehrere Rechnungen): 11 OK / 0 FEHL
pruefe_abo_xmlids.py              alle XML-IDs des Moduls gegen ir.model.data
apply_abo_stammdaten.py           fehlende Vorlagen/Beendigungsgruende, idempotent
fix_currency_eur.py               EUR-Preisliste durchsetzen
cleanup_usd_testdata.py           USD-Testdaten und EUR-Testdaten fuer alle Zustaende
browser_abo_abschluss.py          Browsertest Formular, Zustaende, Buttons, EUR
browser_abo_manuell_klick.py      Browser-Klick auf "Rechnung manuell erstellen"
browser_abo_reiter.py             Reiter auf beiden Wegen
pruefe/vergleich_abo_xmlids...    siehe oben

Analyse Abonnement Produkte (neu, ungetrackt bis zu diesem Commit):
vergleich_abo_produkte.py         versionsunabhaengige Bestandsaufnahme (o11 / vm / lokal)
verify_abo_produkte.py           Pruefung der Umsetzung Abonnement Produkte
```

## 4. Offene Punkte Abonnement Produkte (Teil 14) - so weiterarbeiten

Vorbedingung aus dieser Session (wichtig, sonst schlaegt das Modul-Upgrade fehl):

```
a) is_multi_factor_product gehoert zu itk_multifactor, product_type_id zu itk_product.
   BEIDE Module haengen von itk_subscription ab. Eine Ansicht in itk_subscription darf diese
   Felder deshalb NICHT enthalten ("Das Feld is_multi_factor_product existiert nicht im Modell").
   -> Der fachliche Zusatz gehoert in itk_multifactor (besitzt das Faktor-Feld).
b) qty_available und virtual_available existieren in der Odoo-18-Instanz NICHT
   ("Das Feld qty_available existiert nicht im Modell product.template") - es ist kein
   Lager-Modul (stock) installiert. Diese Odoo-11-Spalten haben derzeit kein Ziel und werden
   nicht migriert. Sie sind erst darstellbar, wenn stock installiert wird.
c) Ein View-Arch mit mehreren XPaths muss in <data> geklammert werden, sonst:
   "Extra content at the end of the document". Einzelne XPaths sind zulaessig.
d) mode="primary" ist hier nicht verwendbar (die Wurzel-Produktliste ist selbst abgeleitet,
   Fehler "Validierung der Ansicht nahe: </header>").

Aufgaben:
1. In itk_multifactor eine Erweiterung der Wurzel-Produktliste anlegen:
      categ_id   optional="show" und string="Interne Kategorie"
      is_multi_factor_product string="Mit Faktor multiplizieren (pro 1.000)"
   (Interne Referenz, Name, Verkaufspreis, Kosten, Status, Produktart, Einheit, Stichwoerter
    sind bereits in der Liste und bleiben unveraendert.)
2. to_multiply_by_factor aus dem Produktformular entfernen (itk_product/views/itk_product.xml,
   Zeile mit <field name="to_multiply_by_factor"/>). Feld bleibt in der DB, keine Daten aendern.
3. Suchansicht ist fertig und validiert (siehe Abschnitt 5) - nur noch mit ausliefern.
4. VM-Browserabnahme: Liste, Spalten, Spaltenauswahl, Suche, Filter, Gruppieren, Produktformular,
   Preise in EUR, keine RPC-/View-Fehler.
5. Entscheidung einholen: Lager-Modul (stock) installieren? Nur dann sind Bestandsmenge und
   geplante Bestandsmenge sichtbar (in Odoo 18 berechnet, niemals migrieren).
```

## 5. Fertige Suchansicht (validiert, noch nicht ausgeliefert)

```
product.template.search.abo.produkte - von Odoo fehlerfrei gerendert:
   Filter      filter_multi_factor, filter_abo_aktiv
               erhalten: filter_products, filter_recurring, filter_to_sell/purchase, inactive, type, categ_id
   Gruppierung categ_id (Interne Kategorie), product_type_id (Status), type (Produktart),
               is_multi_factor_product (Mit Faktor multipliziert)
Die Odoo-11-Eintraege "Service Type ..." sind bewusst NICHT nachgebaut: das waren feste Filter auf
einzelne Werte der ITK-Produktart; in Odoo 18 entspricht dem die Gruppierung nach der Produktart.
```

## 6. Arbeitsregeln aus dieser Session

```
1. VM (https://k001959vsx.ipax.at) ist die verbindliche Abnahmeumgebung; lokal ist Entwicklung.
2. Ein Button gilt erst als funktionsfaehig, wenn er auf der VM im echten Browser geklickt wurde
   und der Vorgang ohne RPC-/Serverfehler durchlaeuft. Sichtbarkeit genuegt nicht.
3. Vor jedem Modul-Upgrade: XML-Syntax pruefen, danach die Ansicht als Testdatensatz anlegen
   (ir.ui.view.create) und mit product.template.get_views rendern lassen, Testdatensatz wieder
   loeschen. Erst bei fehlerfreiem Rendern das Modul upgraden.
4. Windows/Docker: neu angelegte Dateien im Addons-Ordner sieht der laufende Container erst nach
   docker restart odoo18. Ohne Neustart laeuft das Upgrade fehlerfrei durch, laedt die Datei aber
   nicht (das erklaert so manches "wirkungslose" Upgrade).
5. Feldbeschriftungen, die auf Uebersetzungen beruhen, werden bei jedem Upgrade zurueckgesetzt
   (F34) - Beschriftungen deshalb direkt im Modul-View setzen (wie beim Reiter "Wiederkehrende
   Buchungen"), das ist upgradefest.
6. Odoo 11 Prod ist strikt read-only. Nie aendern, anlegen, loeschen, migrieren.
7. Keine Datenmigration ohne ausdrueckliche Freigabe.
```

## 7. Migrationsregeln und Vorbereitung

```
migration/abo_migrationsregeln.json   Auswahlregel (1.748 uebernehmen, 16 nicht), Reihenfolge,
                                      Auftrags-Mapping, Multiplikationsfaktor, recurring_next_date
                                      und Cron-Ablauf, Nummernregel, USD-Testdaten
Auswahlregel        alle Abos ausser abgebrochenen ohne Verkaufsauftrag (16)
Reihenfolge         Kontakte -> Produkte/Preislisten -> Auftraege -> Abos -> Zeilen -> Verknuepfungen
Schluessel          code (eindeutig); name ist nicht eindeutig (1.082 x "Jahresabrechnung-Abonnement")
Faktor              qty_multiplication_factor 1:1; is_multi_factor_product ist das fachliche Feld
recurring_next_date 1:1 uebernehmen, Cronjobs vor der Migration pausieren, Stichprobe, dann aktivieren
Produkte            Kategorien -> Masseinheiten (inkl. ITK-Einheit) -> Produkttypen (ueber code)
                    -> EUR-Preislisten -> Produkte; 1:1: name, default_code, Preise, active,
                    recurring_invoice, is_multi_factor_product
                    nicht migrieren: qty_available, virtual_available
                    Varianten: 649 Templates / 648 Produkte, 0 mit mehreren Varianten
```

## 8. Stand bei Uebergabe

```
lokal = GitHub = main = Stand nach diesem Commit (Arbeitsbaum sauber)
VM /opt/odoo18 = derselbe Commit, Container laeuft, /web/login HTTP 200
Module: itk_subscription 18.0.1.2.6 (unveraendert seit Teil 13), itk_multifactor und itk_product
        unveraendert, alle Upgrades fehlerfrei
Testdatenzustand: EUR-Testabos fuer alle fuenf Zustaende, Testauftrag EUR, USD nur noch in
        8 alten Testauftraegen (von Migration und Abnahme ausgeschlossen)
Odoo 11 Prod: unveraendert, ausschliesslich gelesen
```
