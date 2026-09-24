# Odoo 11 -> Odoo 18: Bereich Verkauf, Teil 1 (Grundstruktur, Menues, Module)

Stand: 24.09.2026, Session 121. Odoo 11 Prod (`portal.it-kommunal.at`, DB `ITK_V1_a`) wurde
ausschliesslich lesend verwendet (nur Suche/Lesen, kein Schreiben). Keine Datenmigration,
keine Aenderung an Produktivdaten. Angepasst wird nur Odoo 18.

Werkzeuge: `scripts/analyse_verkauf_menue.py` (Menuebaum beider Instanzen, schreibt
`docs/_verkauf_menue_daten.json`), `scripts/analyse_verkauf_teil1.py` (Module und Nutzungszahlen),
`scripts/_o11o18_client.py` (read-only RPC-Client).

## 1. Modulinventar

Odoo 11 Prod, verkaufsrelevante Module (Zustand | Version):

```
sale                         installed  11.0.1.1     Verkauf
sale_management              installed  11.0.1.0     Verkaufsmanagement
sale_stock                   installed  11.0.1.0     Verkaufs- und Lagerverwaltung
sale_timesheet               installed  11.0.1.0     Zeiterfassung im Vertrieb
sales_team                   installed  11.0.1.0     Vertriebskanaele
account                      installed  11.0.1.1     Abrechnung
product                      installed  11.0.1.2     Produkte und Preislisten
crm                          installed  11.0.1.0     Kundenverwaltung
sale_order_line_number       installed  11.0.1.0.0   Sale Order Line Number
account_invoice_line_number  installed  11.0.1.0.0   Account Invoice Line Number
itk_sale_management          installed  11.0.0.2     itk_sale_management
itk_saleorder_lines          installed  11.0.0.4     itk_saleorder_lines
itk_product                  installed  11.0.0.1     itk_product
itk_multifactor              installed  11.0.0.1     itk_multifactor
itk_reports                  installed  11.0.0.4     itk_reports
mass_editing                 installed  11.0.1.0.1   Massenverarbeitung
merge_sale_order             uninstalled            Merge Sale Order
sale_merge_draft_invoice     uninstalled            Sale Merge Draft Invoice
```

Odoo 18 (lokal), gleiche Liste:

```
sale                         installed  18.0.1.2     Verkauf
sale_management              installed  18.0.1.0     Verkauf
sale_stock                   uninstalled            Verkaufs- und Lagerverwaltung
sale_timesheet               uninstalled            Verkauf Zeiterfassung
sales_team                   installed  18.0.1.1     Verkaufsteams
account                      installed  18.0.1.3     Rechnungsstellung
product                      installed  18.0.1.2     Produkte & Preislisten
crm                          installed  18.0.1.8     CRM
sale_order_line_number       installed  18.0.1.0.0   Sale Order Line Number
account_invoice_line_number  installed  18.0.1.0.0   Account Invoice Line Number
itk_sale_management          installed  18.0.1.1.0   itk_sale_management
itk_saleorder_lines          installed  18.0.1.0.0   ITK Auftragszeilen
itk_product                  installed  18.0.1.0.2   itk_product
itk_multifactor              installed  18.0.1.1.1   ITK Multiplikationsfaktor
itk_reports                  installed  18.0.1.0.0   itk_reports
merge_sale_order             installed  18.0.1.0.0   Merge Sale Order
sale_merge_draft_invoice     installed  18.0.1.0.0   Sale Merge Draft Invoice
mass_editing                 uninstalled            (ersetzt durch server_action_mass_edit 18.0.1.1.3)
```

Unterschiede mit Wirkung auf den Bereich Verkauf:

```
1. sale_stock: in Odoo 11 installiert, in Odoo 18 nicht. Bereits entschieden (Session 119):
   stock wird nicht installiert (0 Bestand, 0 erledigte Lieferungen). Auswirkung auf Verkauf:
   Liefer-Status und Bestands-Spalten der Auftragszeilen entfallen begruendet.
2. sale_timesheet: in Odoo 11 installiert, in Odoo 18 nicht. Bereits entschieden (Session 120):
   service_type wird nicht uebernommen (0 Stundenzettelzeilen).
3. mass_editing -> server_action_mass_edit: Nachfolgemodul ist installiert.
4. merge_sale_order und sale_merge_draft_invoice: in Odoo 11 NICHT installiert, in Odoo 18
   vorhanden (Zusatzfunktion, bleibt). In Odoo 11 also keine Vorlage zu vergleichen.
```

## 2. Menuebaum Verkauf

Odoo 11 Prod: Wurzelmenue `Verkauf` (id 294, Sequenz 7) mit 23 Menues:

```
Verkauf
  Auftraege
    Angebote nach Kunden        -> Aktion 429 Angebote (sale.order), ohne Domain
    Auftraege nach Kunden       -> Aktion 426 Verkaufsauftraege (sale.order),
                                   Domain state not in draft, sent, cancel
    Kunden                      -> Aktion 48 Kunden (res.partner), search_default_customer
    Auftrag-Ansichten           -> Aktion 548 Auftragspositionen (sale.order.line)
  Abrechnung (Gruppe: Verkauf / User)
    Auftraege zur Rechnung      -> Aktion 427, Domain invoice_status = to invoice
    Auftraege fuer Upselling    -> Aktion 428, Domain invoice_status = upselling
  Katalog (Gruppe: Verkauf / User)
    Produkte                    -> Aktion 166 (product.template), search_default_filter_to_sell
    Preislisten                 -> Aktion 167 (product.pricelist)
  Berichtswesen (Gruppe: Verkauf / Manager)
    Verkauf                     -> Aktion 423 Statistik Verkaufsauftraege (sale.report, graph+pivot)
    Vertriebskanaele            -> Aktion 171 (crm.team, Kanban)
    Verkaufsauftraege aller Kanaele -> Aktion 424 (report.all.channels.sales, nur pivot)
  Konfiguration (Gruppe: Verkauf / Manager)
    Einstellungen               -> Aktion 441 (res.config.settings, context module sale_management)
    Vertriebskanaele            -> Aktion 172 (crm.team)
    Verkaufsauftraege (Gruppen: Abrechnungsmanager, Verkauf Manager, volle Finanzbuchhaltung)
      Reportlayout Kategorien   -> Aktion 440 (Modell sale.layout.category)
      Kundendienst / Dienstleistungen / Reklamationen -> Aktion 508 (crm.claim)
```

Odoo 18 (lokal): Wurzelmenue `Verkauf` (id 255, Sequenz 30) mit 37 Menues:

```
Verkauf
  Auftraege
    Alle Auftragszeilen         -> Aktion 1118 Auftragszeilen (sale.order.line)
    Angebote                    -> Aktion 430 (sale.order), Default-Filter "Meine Angebote"
    Auftraege                   -> Aktion 429 (sale.order)
    Verkaufsteams               -> Aktion 184 (crm.team, context in_sales_app)
    Kunden                      -> Aktion 393 (res.partner), search_default_customer
  Abzurechnen
    Abzurechnende Auftraege     -> Aktion 432 (Domain invoice_status to invoice, create False)
    Auftraege fuer Upselling    -> Aktion 433 (Domain invoice_status upselling, create False)
  Produkte
    Produkte                    -> Aktion 444 (product.template)
    Produktvarianten            -> Aktion 296 (product.product)
    Preislisten                  -> Aktion 302 (product.pricelist)
  Berichtswesen
    Verkauf                     -> Aktion 416 Verkaufsanalyse (sale.report)
    Vertriebsmitarbeiter        -> Aktion 417 (sale.report, group_by user_id)
    Produkte                    -> Aktion 418 (sale.report, group_by Produkt)
    Kunden                      -> Aktion 419 (sale.report, group_by partner_id)
  Konfiguration
    Einstellungen               -> Aktion 427
    Verkaufsteams               -> Aktion 186 (crm.team)
    Verkaufsauftraege
      Angebotsvorlagen          -> Aktion 450 (sale.order.template)
      Kopf-/Fusszeilen          -> Aktion 453 (quotation.document)
      Stichwoerter              -> Aktion 183 (crm.tag)
    Produkte
      Attribute, Kombi-Moeglichkeiten, Produktkategorien, Produkt-Stichwoerter
    Online-Zahlungen
      Zahlungsanbieter, Zahlungsmethoden
    Masseinheiten
      Masseinheitskategorien
    Aktivitaeten
      Aktivitaetsplaene         -> Aktion 443 (mail.activity.plan)
```

### 2.1 Zuordnung der Odoo-11-Menues

```
Odoo 11                                     Odoo 18                                   Bewertung
Auftraege/Angebote nach Kunden              Auftraege/Angebote                        gleichwertig
Auftraege/Auftraege nach Kunden             Auftraege/Auftraege                       gleichwertig
Auftraege/Kunden                            Auftraege/Kunden                          gleichwertig
Auftraege/Auftrag-Ansichten                 Auftraege/Alle Auftragszeilen             gleichwertig
Abrechnung/Auftraege zur Rechnung           Abzurechnen/Abzurechnende Auftraege       gleichwertig
Abrechnung/Auftraege fuer Upselling         Abzurechnen/Auftraege fuer Upselling      gleichwertig (gleicher Name)
Katalog/Produkte                            Produkte/Produkte                         gleichwertig
Katalog/Preislisten                         Produkte/Preislisten                      gleichwertig
Berichtswesen/Verkauf                       Berichtswesen/Verkauf                     Obermenge (O18 hat 4 Berichte)
Berichtswesen/Vertriebskanaele              (O18: Berichtswesen/Vertriebskanaele      siehe 6.12: Menue liegt in der
                                             liegt in der Kundenverwaltung)            Kundenverwaltung, gleiche Ansicht
Berichtswesen/Verkaufsauftraege aller       FEHLT                                     Anpassung empfohlen fuer Teil 4
Kaenale
Konfiguration/Einstellungen                 Konfiguration/Einstellungen               gleichwertig
Konfiguration/Vertriebskanaele              Konfiguration/Verkaufsteams               gleichwertig (gleiche Ansicht
                                                                                      crm.team, anderer Wortlaut)
Konfiguration/Verkaufsauftraege/            FEHLT, Modell existiert in Odoo 18        tote Odoo-11-Funktion, siehe 3.3
Reportlayout Kategorien                     ebenfalls nicht
Konfiguration/.../Reklamationen             FEHLT, Modul bi_crm_claim nicht in O18    tote Odoo-11-Funktion, siehe 3.3
```

Zusatzmenues in Odoo 18 ohne Odoo-11-Vorlage (bleiben, keine Anpassung):
Produktvarianten, Verkaufsteams unter Auftraege, Angebotsvorlagen, Kopf-/Fusszeilen, Stichwoerter,
Produkte-Attribute/Kombi-Moeglichkeiten/Produktkategorien/Produkt-Stichwoerter, Online-Zahlungen,
Masseinheiten, Aktivitaetsplaene, die drei zusaetzlichen Auswertungen.

## 3. Nutzung in Odoo 11 Prod (Zahlen als Beleg)

### 3.1 Menueziele

```
sale.order                        2.461   (draft 5, sale 2.309, cancel 147, sent 0, done 0)
sale.order.line                   4.007
sale.report                       3.984
produkt.template                    649
product.product                     648
product.pricelist                    50
product.pricelist.item            1.872
crm.team                              8
account.payment.term                  4
account.tax                          77
report.all.channels.sales         3.772
sale.subscription                 1.764   (Bereich Abonnements, eingefroren)
res.partner                       5.845
Aktive Benutzer                      57, davon in Gruppe Verkauf / User: 40
```

Auftraege je Vertriebskanal: `Vertriebskanaele (Intern)` 2.443, `Interne Weitergabe` 13,
`Persoenlicher Kontakt` 4, `Newsletter` 1.

### 3.2 Sichtbarkeitsunterschied (Default-Filter)

`Verkauf/Auftraege/Angebote` in Odoo 18 startet mit dem Default-Filter "Meine Angebote"
(Kontext `search_default_my_quotation: 1`). Die Odoo-11-Menues hatten keinen solchen Vorgabefilter.
Wirkung: nach dem Einstieg sieht ein Benutzer zunaechst nur seine eigenen Angebote, nicht alle.
Zu entscheiden in Teil 3 (Empfehlung: Odoo-18-Standardfilter belassen, Abweichung dokumentieren;
Alternative: `search_default_my_quotation` im Menue entfernen).

### 3.3 Tote Odoo-11-Menues (keine Migration noetig, keine Anpassung)

```
Reportlayout Kategorien (Aktion 440): Modell sale.layout.category ist in Odoo 11 nicht als Modell
  registriert (ir.model leer, Abfrage schlaegt mit KeyError fehl). Das Feld layout_category_id
  ("Sektion") auf sale.order.line ist auf 2 von 4.007 Zeilen gesetzt, layout_category_sequence auf
  1.366 Zeilen (Odoo-11-Standardwert 1). Kein funktionierendes Odoo-11-Feature.
Reklamationen (Aktion 508): Modell crm.claim aus Modul bi_crm_claim, 0 Datensaetze in Odoo 11.
```

## 4. Nutzung durch die Benutzer: gespeicherte Filter (Odoo 11)

16 gespeicherte Filter auf `sale.order`/`sale.order.line` in Odoo 11, alle benutzergebunden
(keiner systemweit, keiner ohne Benutzer): 15 x Waiss Martina (darunter 14 Auftragssammlungen je
Projekt: A-Tool, Gemdat, Kufgem, Comm-Unity, Gemeindecloud, Hinweisgeber, IFG), 1 x Wuerrer Florian.
**3** davon sind als Benutzerstandard gesetzt (is_default = True) - das sind die einzigen, die einen
Menueaufruf vorbelegen:

```
"Angebote"                            Benutzer Martina Waiss, Modell sale.order, Aktion 429 (Angebote)
                                      Domain leer, Kontext group_by state
                                      -> nur Gruppierung nach Status, keine Dateneinschraenkung
"Angebote nach Verkaeufer"            Benutzer Administrator, Modell sale.order, Aktion 429
                                      Domain leer, Kontext group_by user_id
                                      -> nur Gruppierung nach Verkaeufer
"Verkaufsauftraege A-Tool Comm-Unity" Benutzer Martina Waiss, Modell sale.order, Aktion 426
                                      Domain order_line ilike 'A-Tool' UND user_id ilike 'Comm-un'
                                      -> persoenliche Auftragssammlung, Dateneinschraenkung
```

Bewertung (read-only geprueft): Kein Filter ist systemweit (0 Datensaetze ohne Benutzer), Odoo 18
hat auf sale.order/sale.order.line ebenfalls 0 gespeicherte Filter. Die beiden Gruppierungs-
Voreinstellungen (Status, Verkaeufer) sind in Odoo 18 ueber die Standard-Suchfunktion "Gruppieren
nach" abbildbar, ohne Nachbau. Der dritte Filter ist eine persoenliche Projektauswahl, die ueber
Teiltextsuche in Zeilen und Verkaeuferkennung arbeitet und an Odoo-11-Projektnamen haengt; er hat
keine Systemwirkung. Empfehlung: keine Migration; Entscheidung von Anna noch offen.

## 5. Vorschlag fuer den Teil-Schnitt (Bereich Verkauf)

```
Teil 1  Grundstruktur: Module, Menuebaum, Nutzungszahlen, tote Menues, Teilplan  (dieses Dokument)
Teil 2  Vollstaendiges Feldinventar sale.order und sale.order.line
        (jedes in Odoo 11 verwendete Feld mit Nutzungszahl und Odoo-18-Ziel, inklusive
        itk_sale_management, itk_saleorder_lines, itk_multifactor, sale_order_line_number)
Teil 3  Formulare, Reiter, Buttons, Smart Buttons, Statuswechsel, Filter, Gruppierungen,
        Suchfunktionen und Ansichten im Browser (lokal und VM), inklusive der
        Oeffnungs-Defaults der Menues ("Meine Angebote")
Teil 4  Listen- und Suchansichten je Menuepunkt, Berichte und Auswertungen
        (inklusive Nachbau "Verkaufsauftraege aller Kanaele"), Preislisten- und
        Stammdatenpruefung fuer den Verkauf
Teil 5  Abschlusspruefung mit Mapping-Tabelle, fehlende Stammdaten (nach Freigabe),
        Checkliste 6.15 auf ABGESCHLOSSEN, Uebergabe
```

Hinweis: der Unterbereich "Angebote / Verkaufsauftraege (sale.order)" wurde in Session 117
vollstaendig verglichen, umgesetzt und inklusive Mehrzustands-Browserpruefung auf der VM
abgenommen (Checkliste 6.13; `verify_s117_auftraege.py` 65 OK, `browser_auftraege_pruef.py`
9 OK, jeweils lokal und VM). Fuer den Bereich Verkauf sind daher vor allem die noch nicht
betrachteten Teile offen: Feldinventar der Auftragszeilen, Listen-/Suchansichten,
Konfigurations- und Berichtsmenues, Stammdaten des Verkaufs.

## 6. Entscheidungen von Anna (24.09.2026) und verbindliche Vorgaben

```
1. "Verkaufsauftraege aller Kanaele" WIRD in Odoo 18 nachgebaut (der Bericht enthaelt in Odoo 11
   tatsaechlich Daten, 3.772 Zeilen). Umsetzung Odoo-18-konform: Auswertung auf sale.report mit
   Gruppierung nach Vertriebskanal (team_id) und Filter "aktuelles Verkaufsjahr" - kein Nachbau des
   Odoo-11-Modells report.all.channels.sales und keine Odoo-11-Pivot-Technik. Einordnung: Teil 4.
2. Der automatische Default-Filter "Meine Angebote" im Menue Auftraege/Angebote WIRD ENTFERNT
   (der Menueaufruf verhaelt sich dann wie in Odoo 11). Der Filter selbst bleibt in der Suchleiste
   auswaehlbar. Einordnung: Teil 3 (Aenderung an der Menueaktion, mit Deploy und Browser-Abnahme
   auf der VM).
3. Die 15 benutzerspezifischen gespeicherten Filter werden NICHT migriert. Die 3 als Standard
   markierten Favoriten wurden am 24.09.2026 read-only geprueft (Abschnitt 4): keiner ist
   systemweit, zwei setzen nur eine Gruppierung (in Odoo 18 ueber "Gruppieren nach" abbildbar),
   einer ist eine persoenliche Projektauswahl. Empfehlung: keine Migration. Entscheidung offen.
4. Odoo-18-Zusatzfunktionen (Angebotsvorlagen, Kopf-/Fusszeilen, Verkaufsteams, Produktvarianten,
   zusaetzliche Auswertungen) bleiben erhalten.
```

Daraus folgt als offener Punkt nur noch Entscheidung 3 (Standardfavoriten). Alles andere ist
entschieden und den Teilen 3 und 4 zugeordnet.

Nicht mehr offen (in Teil 1 gegengeprueft und korrigiert):

```
confirmation_date: geloest in Session 117. In Odoo 11 heisst das Feld "Bestätigung am"
  (datetime, 2.437 von 2.461 Auftraegen gefuellt), in Odoo 18 existiert das Feld mit gleichem
  Namen, gleicher Beschriftung und gleichem Typ (Feld in itk_sale_management 18.0.1.1.0).
  Die Checkliste 6.13 fuehrt es noch als KLAERUNG NOETIG; das ist ein veralteter Stand.

Mehrzustands-Browserpruefung auf der VM: in Session 117 durchgefuehrt
  (scripts/browser_auftraege_pruef.py lokal 9 OK / VM 9 OK, verify_s117_auftraege.py 65 OK).
  Die Checkliste 6.13 nennt sie noch als offen; ebenfalls veralteter Stand.
```

## 7. Hinweise fuer die naechsten Teile

```
- sale_stock und sale_timesheet sind in Odoo 18 nicht installiert (Entscheidungen aus Session 119/120).
  Felder dieser Module (Bestand, gelieferte Menge, service_type) werden in Teil 2 als "entfaellt"
  mit Begruendung gefuehrt, nicht als Luecke.
- Massgebliche Abnahmeumgebung bleibt die VM (https://k001959vsx.ipax.at); alle Nachweise je Teil
  lokal und auf der VM, im Browser mit echten Klicks.
- Odoo 11 Prod wird ausschliesslich lesend verwendet.
```

## 8. Nachweise (Teil 1)

```
                                        lokal                          VM (k001959vsx.ipax.at)
scripts/verify_s121_verkauf_menue.py    41 OK / 0 FEHL                 41 OK / 0 FEHL (in einem Lauf,
                                                                        beide Instanzen geprueft)
scripts/browser_verkauf_menue.py        43 OK / 0 FEHL                 43 OK / 0 FEHL
                                        (echte Klicks)                 (echte Klicks, 0 JS-/RPC-Fehler)
Menuebaum Verkauf                       37 Menues                      37 Menues, identisch zu lokal
sale.order (Teststand)                  18                             20
Screenshots                             Desktop\Odoo18-Abnahme-Session121\01_App_Verkauf.png bis
                                        02_Menue_Konfiguratio.png (VM-Lauf)
Testdaten                               keine angelegt oder geaendert
```

Der Browser-Nachweis auf der VM oeffnet die App Verkauf, klickt Auftraege, Abzurechnen, Produkte,
Berichtswesen und Konfiguration und liest die sichtbaren Menuepunkte. Zusaetzlich als Gegenprobe:
"Verkaufsauftraege aller Kanaele", "Reportlayout Kategorien" und "Reklamationen" sind in keiner
Gruppe sichtbar. Teil 1 aendert nichts an Odoo 18 (reine Bestandsaufnahme), daher waren kein Deploy
und kein Modul-Upgrade noetig.

**Befund aus dem Browser (Session 121):** Odoo 18 haengt das Menue-Popover als `.o-popover
o-dropdown--menu` an das Ende des Body, nicht in die Navigationsleiste. Sichtbarkeitspruefungen
ueber `offsetParent` schlagen dort fehl (position: fixed); zuverlaessig ist `getClientRects()`.
Die Odoo-11-Untergruppe "Verkaufsauftraege" erscheint in Odoo 18 nur als Abschnittstitel im Menue
Konfiguration, die drei Eintraege darunter (Angebotsvorlagen, Kopf-/Fusszeilen, Stichwoerter) sind
klickbar.

**STATUS TEIL 1: ABGESCHLOSSEN (lokal und VM, Browser). Kein Eingriff in Daten oder Ansichten.**
Bereich Verkauf insgesamt weiterhin in Arbeit.
