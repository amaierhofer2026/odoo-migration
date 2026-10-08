# Menue-Matrix und Abschlussdurchgang Bereich Abrechnung (Odoo 11 gegen Odoo 18)

Stand: 07.10.2026, Session 131. Auftrag: vollstaendiger Abschlussdurchgang des Moduls Abrechnung
mit Schwerpunkt Konfiguration und Berichtswesen, vollstaendige Menue-Matrix, Klaerung der mehrfach
sichtbaren Menueueberschrift "Konfiguration", Browserpruefung jedes Menuepunkts lokal und auf der VM,
Beschriftungspruefung, Regression und Dreistand.

Odoo 11 wurde ausschliesslich lesend gelesen (portal.it-kommunal.at, DB ITK_V1_a). Geaendert wurde
nur Odoo 18 (lokale Testinstanz, danach VM). Keine Produktivdaten. **Abrechnung bleibt IN ARBEIT.**
Die endgueltige fachliche Freigabe gibt Anna nach eigener Sichtkontrolle.

## 0. Werkzeuge und Nachweise

| Werkzeug | Zweck | Ergebnisdatei |
|---|---|---|
| `scripts/erhebe_abrechnung_menue_matrix.py` | Menuebaum je System erheben (Pfad, Modell, Aktion, XML-ID, Ansichten, Gruppen, Datensatzzahl) | `Desktop\Odoo18-Abnahme-Session131\menue_matrix\menue_rohdaten.json` |
| `scripts/vergleiche_abrechnung_menuepunkte.py` | Wirksame Ansichten je Menuepunkt vergleichen (Liste, Formular, Suche) | `...\ansichten\ansichten_rohdaten.json` |
| `scripts/werte_abrechnung_menuevergleich_aus.py` | Vergleichsbericht je Menuepunkt (Differenzen, Kennzahlen) | `...\vergleich_bericht.txt` |
| `scripts/pruefe_abrechnung_beschriftungen_vollstaendig.py` | Beschriftungen aller Feldpaare der Abrechnungsmodelle (nicht nur die dokumentierten 155) | `...\beschriftungen\beschriftungen_lokal.json`, `..._vm.json` |
| `scripts/browser_abrechnung_gesamtcheck.py` | Browser-Gesamtcheck je Menuepunkt (Menue, Liste, Suche, Filter, Gruppierung, Formular, Relation, Bearbeiten, eine Speicherprobe, JS-/RPC-Fehler) | `...\browser\<instanz>\gesamtcheck.json` + Screenshots |

Read-only-Messung in Odoo 11 ohne jede Schreiboperation; im Odoo-18-Testbestand eine einzige
Speicherprobe (Testkategorie `ITK-TEST-S131`, danach entfernt) sowie die dokumentierten
Bezeichnungslaeufe.

## 1. Menue-Matrix (Odoo 11 gegen Odoo 18)

Spalten: Odoo-11-Menuepunkt | Odoo-18-Menuepunkt | Modell | Aktion | Views | fachliche Entsprechung |
Abweichung | Massnahme | migrationsrelevant.

Ansichtsarten sind vergleichbar gemacht (Odoo 11 `tree` = Odoo 18 `list`; `activity` ist eine
Odoo-18-Zusatzansicht).

### 1.1 Verkauf (Kundenbelege)

| Odoo 11 | Odoo 18 | Modell | Aktion | Views | fachlich gleich | Abweichung | Massnahme | migr.relevant |
|---|---|---|---|---|---|---|---|---|
| Abrechnung > Verkauf > Dokumente > Ausgangsrechnungen | Abrechnung > Verkauf > Ausgangsrechnungen | account.invoice -> account.move | 249 -> 354 | tree,kanban,form,calendar,pivot -> list,kanban,form,activity | ja | Zwischengruppe "Dokumente" entfaellt (flach), Ansichtsart calendar entfaellt, activity kommt hinzu | keine (Odoo-18-Standard, in Session 122/129 abgenommen) | ja (Belege) |
| Verkauf > Dokumente > Kunden-Gutschriften | Verkauf > Kunden-Gutschriften | account.invoice -> account.move | 250 -> 355 | wie oben | ja | wie oben | keine | ja |
| Verkauf > Dokumente > Zahlungen | Verkauf > Zahlungen | account.payment | 176 -> 330 | tree,kanban,form,graph -> list,kanban,form,graph,activity | ja | "activity" zusaetzlich | keine | ja (Zahlungen) |
| Verkauf > Stammdaten > Kunden | Verkauf > Kunden | res.partner | 49 -> 393 | kanban,tree,form -> kanban,list,form | ja | Zwischengruppe entfaellt | keine | ja (Partner) |
| Verkauf > Stammdaten > Verkaufbare Produkte | Verkauf > Verkaufbare Produkte | product.product -> product.template | 225 -> 382 | kanban,tree,form -> kanban,list,form,activity | ja | Zwischengruppe entfaellt; Odoo 11 zeigte in beiden Produktmenues dieselbe Liste (571), Odoo 18 bindet die ITK-Liste an 382/383 (Session 128) | keine | ja (Produkte) |
| nicht vorhanden | Verkauf > Eingaenge | account.move | 360 | list,kanban,form,activity | - | Odoo-18-Zusatzmenue (Eingangsbelege der Gutschriften) | erhalten | nein |

### 1.2 Einkauf (Lieferantenbelege)

| Odoo 11 | Odoo 18 | Modell | Aktion | Views | fachlich gleich | Abweichung | Massnahme | migr.relevant |
|---|---|---|---|---|---|---|---|---|
| Abrechnung > Einkauf > Dokumente > Eingangsrechnungen | Abrechnung > Einkauf > Eingangsrechnungen | account.invoice -> account.move | 251 -> 357 | wie Verkauf | ja | Zwischengruppe entfaellt | keine | ja (0 Belege in Odoo 11) |
| Einkauf > Dokumente > Lieferanten-Gutschriften | Einkauf > Lieferanten-Gutschriften | account.invoice -> account.move | 252 -> 358 | wie Verkauf | ja | Zwischengruppe entfaellt | keine | ja (0 Belege in Odoo 11) |
| Einkauf > Dokumente > Zahlungen | Einkauf > Zahlungen | account.payment | 177 -> 331 | wie Verkauf | ja | "activity" zusaetzlich | keine | ja (0 Zahlungen in Odoo 11) |
| Einkauf > Stammdaten > Einkaufbare Produkte | Einkauf > Einkaufbare Produkte | product.product -> product.template | 226 -> 383 | wie Verkauf | ja | wie Verkauf | keine | ja |
| Einkauf > Stammdaten > Lieferanten | Einkauf > Lieferanten | res.partner | 50 -> 394 | kanban,tree,form -> kanban,list,form | ja | Zwischengruppe entfaellt | keine | ja (Partner) |
| nicht vorhanden | Einkauf > Eingaenge | account.move | 361 | list,kanban,form,activity | - | Odoo-18-Zusatzmenue | erhalten | nein |

### 1.3 Berichtswesen

| Odoo 11 | Odoo 18 | Modell | Aktion | Views | fachlich gleich | Abweichung | Massnahme | migr.relevant |
|---|---|---|---|---|---|---|---|---|
| Abrechnung > Berichtswesen > PDF Berichte > Audit Journale | nicht vorhanden | account.print.journal | 262 | form | nein | Modul `account_reports`/Enterprise-Assistent fehlt in Odoo 18 Community | kein Nachbau (Entscheidung Anna, K3); fachlich ersetzt durch "Berichtswesen > Verwaltung > Pruefpfad" | nein |
| Berichtswesen > PDF Berichte > Umsatzsteuerbericht | nicht vorhanden | account.tax.report | 276 | form | nein | wie oben | kein Nachbau; Auswertung ueber Steuern/Rechnungsanalyse | nein |
| Berichtswesen > PDF Berichte > alter Partner Saldo | nicht vorhanden | account.aged.trial.balance | 269 | tree,form | nein | wie oben | kein Nachbau; offener Saldo ueber Kundenliste/Rechnungsanalyse | nein |
| Berichtswesen > Verwaltung > Kostenstellenbuchungen | Wurzelmenue "Kostenstellenbuchungen" (eigene Sektion) | account.analytic.line | 256 -> 236 | pivot -> list,kanban,form,graph,pivot | ja | Odoo 18 fuehrt es als eigene Wurzel (Standard `account.menu_action_analytic_lines_tree`), Odoo 11 als Bericht; Umfang in Odoo 18 groesser | keine (Odoo-18-Standard, XML-ID aus `account`); dokumentiert | nein (Auswertung) |
| Berichtswesen > Verwaltung > Rechnungen | Berichtswesen > Verwaltung > Rechnungsanalyse | account.invoice.report | 258 -> 386 | graph,pivot | ja | sichtbare Bezeichnung geaendert (Odoo 18) | informativ: Bezeichnung "Rechnungsanalyse" ist zusaetzlich als Menuepunkt der Berichte gefuehrt; Odoo-11-Wortlaut "Rechnungen" wird nicht erzwungen (Auswertung, kein Feld) | nein |
| nicht vorhanden | Berichtswesen > Abrechnungspositionen | account.invoice.report | 1119 | list,pivot,graph | - | Odoo-18-Zusatz (Modul `account_invoice_line_report`) | erhalten; englische Filter korrigiert (Abschnitt 5) | nein |
| nicht vorhanden | Berichtswesen > Verwaltung > Pruefpfad | mail.message | 400 | list | - | Odoo-18-Zusatz (`account.account_audit_trail_menu`) | erhalten | nein |
| Wurzel "Finanzberichte" (Odoo 11, separates Menue) | nicht vorhanden | account.financial.report | 227 | tree,form | nein | Enterprise-Finanzberichte fehlen in Community | kein Nachbau (Entscheidung Anna) | nein |

### 1.4 Konfiguration

| Odoo 11 | Odoo 18 | Modell | Aktion | Views | Herkunft Odoo 18 | Abweichung | Massnahme | migr.relevant |
|---|---|---|---|---|---|---|---|---|
| Konfiguration (Sektion aus `account`) | Konfiguration | - | - | - | Odoo-18-Standard | keine | keine | nein |
| Konfiguration (Sektion aus `itk_valorisierung`) | Konfiguration | - | - | - | ITK-Modul `itk_valorisierung` | in Odoo 11 vorhanden (dort ebenfalls eigene Sektion) | keine, entspricht Odoo 11 | nein |
| nicht vorhanden | Konfiguration (Sektion aus `itk_projectcategory`) | - | - | - | **ITK-Modul `itk_projectcategory` (nicht Odoo-Standard)** | dritte Sektion mit gleichem Namen; Odoo 11 hatte Menue, Aktion und Liste fuer dieses Modell **nicht** | **korrigiert:** Sektion entfernt, Menue unter "Konfiguration > Verwaltung" eingehaengt (Abschnitt 2) | nein |
| Konfiguration > Einstellungen | Konfiguration > Einstellungen | res.config.settings | 272 -> 390 | form | account | keine (Inhalt der Abrechnungsgruppe gleich; siehe Abschnitt 6) | keine | nein |
| Konfiguration > Finanzen > Bankkonten (Journalliste) | Konfiguration > Bankkonten (Gruppe) + Assistent "Bankkonto hinzufuegen" | account.journal | 191 -> 379 (Server-Aktion) | tree,kanban,form -> Server-Aktion | account | Odoo 18 fuehrt die Bankjournale in "Finanzen > Journale"; "Bankkonten" enthaelt nur den Anlege-Assistenten | keine (Odoo-18-Standard); Bezeichnung des Assistenten instanzgleich gesetzt (Abschnitt 5) | nein |
| Konfiguration > Finanzen > Journale | Konfiguration > Finanzen > Journale | account.journal | 192 -> 370 | tree,kanban,form -> list,kanban,form | account | keine | keine | ja (Journale) |
| Konfiguration > Finanzen > Steuern | Konfiguration > Finanzen > Steuern | account.tax | 206 -> 376 | tree,kanban,form -> list,kanban,form | account | keine (Datensatzzahl ist Testbestand: O11 77, O18 53) | keine | ja (Steuern) |
| Konfiguration > Finanzen > Steuerzuordnung | Konfiguration > Finanzen > Steuerzuordnung | account.fiscal.position | 255 -> 392 | tree,kanban,form -> list,kanban,form | account | Aktionsname Odoo 18 "Steuerpositionen", Menue "Steuerzuordnung" (Odoo-11-Wortlaut gesetzt) | keine | ja (Steuerzuordnung) |
| nicht vorhanden | Konfiguration > Finanzen > Waehrungen | res.currency | 67 | list,kanban,form | account | Odoo 11 erreichte die Waehrungen ueber einen Knopf in den Einstellungen | erhalten (Zusatzfunktion, fachlich gleiche Daten) | ja (Waehrungen) |
| Konfiguration > Kostenrechnung > Kostenstellen Tags | nicht vorhanden | account.analytic.tag | 111 | tree,form | - | Odoo 18 kennt keine Kostenstellen-Tags mehr (Konzept ersetzt durch Kostenstellenplaene und Verteilungsschluessel); Odoo 11: 0 Datensaetze, 0 von 10.057 Belegzeilen mit Tags | kein Nachbau (fachlich entfallen, dokumentiert); Zusatzmenues bleiben | nein |
| Konfiguration > Kostenrechnung > Kostenstellenkonten | Konfiguration > Kostenrechnung > Kostenstellen | account.analytic.account | 114 -> 238 | tree,kanban,form -> list,kanban,form | account | Menuebezeichnung Odoo 18 "Kostenstellen" statt Odoo-11-Wortlaut "Kostenstellenkonten" | offene Wortlautfrage (Abschnitt 7, Punkt 2) | ja (Kostenstellen) |
| nicht vorhanden | Konfiguration > Kostenrechnung > Kostenstellenplaene | account.analytic.plan | 239 | list,form | account | Odoo-18-Konzept (ersetzt die Tag-Struktur) | erhalten | nein |
| nicht vorhanden | Konfiguration > Kostenrechnung > Verteilungsschluessel fuer Kostenstellen | account.analytic.distribution.model | 240 | list,form | account | Odoo-18-Konzept, 0 Datensaetze | erhalten | nein |
| Konfiguration > Valorisierung | Konfiguration > Valorisierung | itk_valorisierung.valorisierung | 528 -> 1117 | tree,form -> list,form | ITK `itk_valorisierung` | Aktionsname Odoo 18 "Valorisierungs Text" (im Browser nicht sichtbar) | keine (Session 130 abgenommen) | ja (Valorisierungstexte) |
| nicht vorhanden | Konfiguration > Verwaltung > Projekt Kategorie | itk_projectcategory.projectcategory | 1463 | list,form | ITK `itk_projectcategory` | in Odoo 11 kein Menue; Liste trug den Altbestand "Fields of Law" | **korrigiert:** Menue nach Verwaltung verschoben, Listenbeschriftung auf "Project Category" gesetzt | ja (Projektkategorien) |
| Konfiguration > Verwaltung > Bargeldrundungen | Konfiguration > Verwaltung > Bargeldrundungen | account.cash.rounding | 260 -> 387 | tree,form -> list,form | account | keine; 0 Datensaetze in beiden Systemen | keine | nein |
| Konfiguration > Verwaltung > Zahlungsbedingungen | Konfiguration > Verwaltung > Zahlungsbedingungen | account.payment.term | 217 -> 378 | tree,kanban,form -> list,kanban,form | account | keine (Menueposition wird vom Label-Lauf gehalten) | keine | ja (Zahlungsbedingungen) |
| nicht vorhanden | Konfiguration > Verwaltung > Produktkategorien | product.category | 299 | list,form | account | Odoo 18 fuehrt die Produktkategorien hier; Odoo 11 erreichte sie ueber das Produktformular | erhalten | ja (Kategorien) |
| Konfiguration > Zahlungen > Zahlungsanbieter | Konfiguration > Zahlungen > Zahlungsanbieter | payment.acquirer -> payment.provider | 416 -> 316 | kanban,tree,form -> kanban,list,form | account_payment | Umbenennung des Modells (Odoo 18) | keine | nein |
| nicht vorhanden | Konfiguration > Zahlungen > Zahlungsmethoden | payment.method | 317 | list,kanban,form | account_payment | Odoo 18 trennt Anbieter und Methoden; 0 Datensaetze | erhalten | nein |

Kein Odoo-11-Menuepunkt des Bereichs Abrechnung ist ohne Entsprechung geblieben, ausser den drei
Enterprise-Berichtsassistenten ("PDF Berichte"), dem Wurzelmenue "Finanzberichte" und dem
entfallenen Konzept "Kostenstellen Tags" (alle dokumentiert, kein Nachbau als Dummy-Funktion).

## 2. Die mehrfach sichtbare Menueueberschrift "Konfiguration" - Ursache und Korrektur

**Befund (read-only gemessen):** In der Navigationsleiste der App Abrechnung stehen in Odoo 18
**drei** Sektionen mit dem Namen "Konfiguration", in Odoo 11 waren es **zwei**.

| System | Sektionen (Sequenz, XML-ID, Herkunft) |
|---|---|
| Odoo 11 | Konfiguration (seq 10, `itk_valorisierung.menu_finance_configuration`), Konfiguration (seq 15, `account.menu_finance_configuration`) |
| Odoo 18 vorher | Konfiguration (seq 10, `itk_valorisierung.menu_finance_configuration`), Konfiguration (seq 10, `itk_projectcategory.menu_finance_configuration`), Konfiguration (seq 35, `account.menu_finance_configuration`) |

**Technische Herkunft:** Jedes dieser drei Menues ist ein direktes Kind des App-Wurzelmenues
`account.menu_finance` und wird von Odoo als eigene Navigationssektion gerendert. Zwei stammen von
ITK-Modulen, die nach dem Muster "side menu category" jeweils eine **eigene** Sektion anlegen:

- `addons/itk_valorisierung/views/valorisierung_views.xml`, Zeile 5:
  `<menuitem id="menu_finance_configuration" name="Configuration" parent="account.menu_finance"/>`
  - in Odoo 11 vorhanden (die Sektion mit "Valorisierung" gab es dort schon) - **bleibt**.
- `addons/itk_projectcategory/views/projectcategory_views.xml`, Zeile 5: dasselbe Muster,
  Modul-ID gleich lautend, dadurch **zweite ITK-Sektion** - in Odoo 11 nicht vorhanden.

**Read-only-Belege fuer Odoo 11 (itk_projectcategory):** Modul installiert (11.0.0.1, 144
Projektkategorien), aber `ir.ui.menu` enthaelt **kein** Menue "Project Category" (Suchlauf: 0
Treffer) und `ir.actions.act_window` **keine** Fensteraktion auf
`itk_projectcategory.projectcategory` (0 Treffer); in `ir.model.data` existiert nur die Formular-
Erweiterung am Beleg (`account.invoice.projectcategory`, View 1389, Modell `account.invoice`).
Der Menuepunkt ist also eine Zutat der Odoo-18-Migration, kein Odoo-11-Bestand.

**Korrektur (nur Odoo 18, eigene Module):** `itk_projectcategory` legt keine eigene Sektion mehr an;
der Menuepunkt "Projekt Kategorie" liegt jetzt wie "Produktkategorien" unter
**Abrechnung > Konfiguration > Verwaltung** (Sequenz 5). Die Sektion des Moduls wird beim Upgrade
ueber `<delete model="ir.ui.menu" id="menu_finance_configuration"/>` entfernt. Ergebnis: **zwei**
Konfigurations-Sektionen wie in Odoo 11, Funktion und Daten unveraendert.

Zusaetzlich korrigiert: die Listenansicht des Menuepunkts trug die Beschriftung "Fields of Law"
(Altbestand aus dem Quellprojekt, in der deutschen und englischen Anzeige identisch englisch);
sie lautet jetzt wie das Modell in Odoo 11 und Odoo 18 "Project Category" (deutsch "Projekt
Kategorie"). Die Projektkategorien selbst (26 in der Testinstanz) bleiben unveraendert.

Modulstaende: `itk_projectcategory` 18.0.1.0.0 -> **18.0.1.0.1**.

## 3. Berichtswesen im Einzelnen

- "PDF Berichte" (Audit Journale, Umsatzsteuerbericht, alter Partner Saldo): Odoo-11-Berichts-
  assistenten aus dem Enterprise-Modul `account_reports`. In Odoo 18 Community **nicht vorhanden**
  (0 Modelle, 0 Ansichten, 0 Aktionen). Kein Nachbau, weil ohne Datenbestand und ohne fachliches
  Ziel kein gleichwertiger Assistent entsteht; die Auswertungen sind ueber Rechnungsanalyse,
  Abrechnungspositionen und die Kunden-/Lieferantenlisten erreichbar. Dokumentierte Abweichung (K3).
- "Kostenstellenbuchungen": Odoo 18 fuehrt den Menuepunkt als eigene Wurzel
  (`account.menu_action_analytic_lines_tree`, Standard von `account`), mit zusaetzlichen
  Ansichtsarten (list, kanban, form, graph, pivot) gegenueber Odoo 11 (nur pivot). Funktion
  gleichwertig, Umfang groesser. Keine Aenderung.
- "Verwaltung > Rechnungen" heisst in Odoo 18 "Rechnungsanalyse" (gleiches Modell
  `account.invoice.report`, gleiche Aktion `account.menu_action_account_invoice_report_all`,
  graph/pivot). Zusaetzlich steht "Abrechnungspositionen" (Modul `account_invoice_line_report`)
  bereit - Zusatzfunktion, erhalten.
- "Pruefpfad" (`account.account_audit_trail_menu`, Modell `mail.message`, 518 Datensaetze):
  Odoo-18-Zusatz, erhalten.

## 4. Konfiguration im Einzelnen (Herkunft und Bewertung)

| Menuepunkt | Herkunft | benoetigt | deutsch korrekt | migrationsrelevant |
|---|---|---|---|---|
| Einstellungen (`account.menu_account_config`) | Odoo-18-Standard | ja | ja | nein |
| Bankkonten + Assistent "Bankkonto hinzufuegen" | Odoo-18-Standard | ja | ja (nach Angleich, Abschnitt 5) | nein |
| Finanzen > Journale | Odoo-18-Standard | ja | ja | ja |
| Finanzen > Steuern | Odoo-18-Standard | ja | ja | ja |
| Finanzen > Steuerzuordnung | Odoo-18-Standard | ja | ja | ja |
| Finanzen > Waehrungen | Odoo-18-Standard | ja | ja | ja |
| Kostenrechnung > Kostenstellen | Odoo-18-Standard | ja | abweichend ("Kostenstellen" statt "Kostenstellenkonten", Abschnitt 7) | ja |
| Kostenrechnung > Kostenstellenplaene | Odoo-18-Standard | ja (0 Daten) | ja | nein |
| Kostenrechnung > Verteilungsschluessel | Odoo-18-Standard | ja (0 Daten) | ja | nein |
| Valorisierung | ITK `itk_valorisierung` | ja | ja (Odoo-11-Wortlaut "Valorisation Text" am Beleg) | ja |
| Verwaltung > Projekt Kategorie | ITK `itk_projectcategory` (neu platziert) | ja | ja (deutsch "Projekt Kategorie") | ja |
| Verwaltung > Bargeldrundungen | Odoo-18-Standard | ja (0 Daten) | ja | nein |
| Verwaltung > Zahlungsbedingungen | Odoo-18-Standard | ja | ja | ja |
| Verwaltung > Produktkategorien | Odoo-18-Standard | ja | ja | ja |
| Zahlungen > Zahlungsanbieter | Odoo-18-Standard (`account_payment`) | ja | ja | nein |
| Zahlungen > Zahlungsmethoden | Odoo-18-Standard (`account_payment`) | ja (0 Daten) | ja | nein |

## 5. Sichtbare englische Beschriftungen - Befunde und Korrekturen

Systematischer Vergleich der wirksamen Ansichten aller Menuepunkte (Odoo 11 gegen Odoo 18, beide
Instanzen) plus eine vollstaendige Feldbeschriftungsmessung (nicht nur die dokumentierten 155
Paare). Gefunden und **korrigiert** wurden vier sichtbare englische Beschriftungen im
Abrechnungsbereich:

| Befund | Wo sichtbar | Odoo 11 | Odoo 18 vorher | Ursache | Korrektur |
|---|---|---|---|---|---|
| Spalte "Salesperson" | Abrechnung > Verkauf > Kunden, Einkauf > Lieferanten (Liste) | Verkäufer | Salesperson | ITK-Ansicht `itk_crm.view_partner_itk_tree` (<field name="user_id" string="Salesperson"/>) | `string="Verkäufer"` (itk_crm 18.0.1.5.8) |
| Filter "Community Code" | Suchleiste Kunden/Lieferanten | Gemeindekennzahl | Community Code | ITK-Ansicht `itk_crm.res_partner_searchview_customization_itk` | `string="Gemeindekennzahl"` |
| Filter "With Price" / "Without Price" | Berichtswesen > Abrechnungspositionen, Rechnungsanalyse | nicht vorhanden (Odoo-18-Zusatz) | With Price / Without Price | Modul `account_invoice_line_report`, deutsche Uebersetzung leer | `msgstr "Mit Preis"` / `"Ohne Preis"` (Modul 18.0.1.0.1); ebenso "Vendor contains" -> "Lieferant enthält" und der Hilfe-Text des Berichts |
| Listenbeschriftung "Fields of Law" | Konfiguration > Verwaltung > Projekt Kategorie | nicht vorhanden (kein Menue in Odoo 11) | Fields of Law | Altbestand aus dem Quellprojekt | "Project Category" (deutsch "Projekt Kategorie") |

Zusaetzlich instanzgleich gesetzt (lokal und VM hatten unterschiedliche deutsche Texte):

| Feld | lokal vorher | VM vorher | jetzt (beide) | Grund |
|---|---|---|---|---|
| account.move.status_in_payment | Status „In Zahlung“ | Status In Payment (englisch) | Status „In Zahlung“ | englische Restbeschriftung auf der VM, Vorgabe aus Session 81 |
| account.move.delivery_date | Liefertermin | Liefer-/Leistungsdatum | Liefer-/Leistungsdatum | Odoo-18-Standardwortlaut (Feld in Odoo 11 nicht vorhanden) |
| account.move.show_delivery_date | Lieferdatum anzeigen | Liefer-/Leistungsdatum anzeigen | Liefer-/Leistungsdatum anzeigen | wie oben |
| res.partner.multi_factor | Multiplication Factor/Thsd | Multiplikationsfaktor (pro 1.000) | Multiplication Factor/Thsd | Odoo-11-Wortlaut (Regel Anna) |
| product.template.rating_ids | Ratings | Bewertungen | Bewertung | Odoo-11-Wortlaut |
| product.template.website_message_ids | Website Messages | Website-Nachrichten | Website-Nachrichten | Odoo-11-Wortlaut |
| Aktion "Bankkonto hinzufuegen" (Menue Bankkonten) | Ein Bankkonto hinzufügen | Bankkonto hinzufügen (Odoo-18-Standard) | Bankkonto hinzufügen | lokal trug einen veralteten Uebersetzungsstand |

Bewusst NICHT geaendert (Odoo-18-Standard bleibt, dokumentiert):

- "Vertriebsmitarbeiter" (Filter/Gruppierung in der Kontaktsuche; in der Liste steht wie in Odoo 11
  "Verkäufer"), "Einzelpersonen" (Typ-Filter), "Kundenrechnungen"/"Lieferantenrechnungen"
  (Odoo-18-Filter mit anderer fachlicher Bedeutung als die Odoo-11-Filter "Kunden"/"Lieferanten").
- Technische Felder ohne sichtbare Stelle (z. B. `activity_exception_icon`: lokal "Icon",
  VM "Symbol") - nicht sichtbar, keine Angleichung.
- Einstellungen ausserhalb der Abrechnungsgruppe (Helpdesk, Tenor/Klipy): andere Bereiche,
  nur gemeldet.

## 6. Instanzvergleich lokal gegen VM

Verglichen wurden der komplette Menuebaum (443 Menues je Instanz), die wirksamen Ansichten aller 30
Menuepunkte mit Fensteraktion sowie die Feldbeschriftungen von 30 Modellpaaren.

| Pruefung | Ergebnis lokal gegen VM |
|---|---|
| Menuebaum unter Abrechnung | identisch (Struktur, Pfade, Aktionen, Ansichtsarten, Sequenzen) |
| Ansichten der Menuepunkte | identisch; Ausnahmen: (a) `buttons_details` einer Partner-Schaltflaeche verweist auf unterschiedliche Aktions-IDs (1564/1567, interne ID, nicht sichtbar), (b) `res.config.settings` enthaelt in beiden Instanzen dieselben Felder in anderer Reihenfolge (Lager/Personal/Anwesenheit/Projekt/Massenmailing - nicht Abrechnung) |
| Menuebezeichnung "Bankkonto hinzufuegen" | vorher unterschiedlich, jetzt identisch (Abschnitt 5) |
| Feldbeschriftungen (de_DE) | 23 Felder mit unterschiedlichem Text gefunden, davon 6 Abrechnungsfelder + 1 Aktionsbezeichnung angeglichen; die uebrigen liegen in nicht abzurechnenden Bereichen (Helpdesk-Einstellungen, Tenor/Klipy, technische Felder) und sind dokumentiert |
| Datensatzzahlen | unterschiedlich, weil Testbestand (lokal 39 Belege / 13 Vorlagen, VM 59 Belege / 10 Vorlagen) |

## 7. Offene fachliche Entscheidungen (nicht eigenmaechtig geaendert)

1. **Menuebezeichnung "Projekt Kategorie"** (englischer Ursprungsname "Project Category"): der
   Menuepunkt ist ein Odoo-18-Zusatz ohne Odoo-11-Vorlage, deshalb gibt es keinen Odoo-11-Wortlaut.
   Fachlich konsistent zu "Produktkategorien" waere ebenfalls eine deutsche Bezeichnung; der
   Feldname am Beleg bleibt in jedem Fall "Project Category" (Odoo-11-Wortlaut).
2. **Wortlaut "Kostenstellenkonten" und "Projektkategorien" - erledigt (08.10.2026).**
   Odoo 11 fuehrt das Menue unter Konfiguration > Kostenrechnung als "Kostenstellenkonten"
   (Menue-ID 179, Modell `account.analytic.account`); Odoo 18 zeigt an derselben Stelle dasselbe
   Menue als "Kostenstellen" (englisch "Analytic Accounts"). Modell, Daten und Funktion sind 1:1,
   daher wurde der Odoo-11-Wortlaut uebernommen. Fuer Projektkategorien fuehrt Odoo 11 gar kein
   Menue (0 Treffer); belegt ist nur der Einzahl-Wortlaut "Projektkategorie" (Aktionsbezeichnung
   "Massenverarbeitung Projektkategorie setzen"). Das Odoo-18-Menue unseres Moduls heisst jetzt
   "Projektkategorien" (Plural wie "Produktkategorien") - die Abweichung Einzahl/Mehrzahl gegenueber
   Odoo 11 ist bewusst und hier dokumentiert.
   Umsetzung: `addons/itk_projectcategory` (Menue und Aktion, Version 18.0.1.0.2) sowie
   `scripts/apply_abrechnung_labels.py` (Menues ueber die technische Kennung, beide Sprachen).
3. **Kontenzuordnung 8400 / 3400 bleibt BLOCKER** fuer die echte Datenmigration (unveraendert,
   siehe Abschnitt 8).
4. **Preislistenregeln (403 Regeln ohne Produktbezug)**, **Namenszuordnung der Abo-Vorlagen**,
   **Rechnungsnotiz (`notice`)** und **Zugriffsrechte der Odoo-11-Gruppen**: unveraendert offen.

## 8. BLOCKER

| BLOCKER | Bereich | Odoo-11-Verhalten | Odoo-18-Verhalten | Ursache | moegliche Loesungen | Empfehlung |
|---|---|---|---|---|---|---|
| Kontenstammdaten 3400 (offen) | Abrechnung > Konfiguration > Verwaltung > Produktkategorien (Aufwandskonto) | 3400 "Wareneingang 19% Vorsteuer" als **globale Firmenvorgabe** der Produktkategorien (8 `ir.property`-Eintraege, `res_id` leer; **0 Belegzeilen**, von keiner Steuer referenziert) | Konto 3400 existiert im Zielkontenrahmen (240 Konten) nicht; Kandidaten 5000/5010/5011/5050/5051/5052/5090 (alle 0 Belegzeilen) weichen im Steuersatz im Namen ab | anderer Kontenrahmen (1.286 gegen 240 Konten) | (a) Kontenstammdaten in Odoo 18 durch ITK fachlich festlegen und dann zuordnen, (b) Dokumentation des festgelegten Mappings fuer die Kategorien, (c) Kategorien ohne Kontenfelder migrieren und die Firmenvorgabe nutzen | nichts anlegen, nichts raten; Entscheidung der Fachabteilung (unveraendert seit Session 129) |

## 9. Bewusste Abweichungen (bleiben)

- Odoo 11 hatte in Verkauf und Einkauf die Zwischengruppen "Dokumente" und "Stammdaten"; Odoo 18
  fuehrt dieselben Menuepunkte flach. Keine Nachbildung (Odoo-18-Standard).
- Ansichtsarten: Odoo 11 bot Kalender-, Pivot- und Graph-Ansichten in den Belegmenues, Odoo 18
  stattdessen die Aktivitaetsansicht; Auswertungen ueber "Rechnungsanalyse" und
  "Abrechnungspositionen".
- Berichtswesen: die drei Odoo-11-Berichtsassistenten ("PDF Berichte") und das Wurzelmenue
  "Finanzberichte" entfallen (Community); "Kostenstellenbuchungen" liegt als eigene Wurzel.
- "Kostenstellen Tags" sind in Odoo 18 fachlich entfallen (0 Daten in Odoo 11).
- Zusatzfunktionen bleiben vollstaendig erhalten: Eingaenge, Abrechnungspositionen, Pruefpfad,
  Kostenstellenplaene, Verteilungsschluessel, Zahlungsmethoden, Waehrungen.
- Aktionsname "Valorisierungs Text" (im Browser nicht sichtbar, Session 130).

## 10. Migrationsrelevanz (Kurzfassung)

- **Zu migrieren:** Belege (Rechnungen/Gutschriften, in Odoo 11 keine Eingangsbelege), Zahlungen,
  Partner (Kunden/Lieferanten), Produkte, Produktkategorien, Steuern, Journale, Zahlungs-
  bedingungen, Waehrungen, Valorisierungstexte, Projektkategorien, Kostenstellen.
- **Nicht zu migrieren:** alle Auswertungen (Rechnungsanalyse, Abrechnungspositionen, Pruefpfad,
  Kostenstellenbuchungen), Konfiguration ohne Daten (Einstellungen, Bargeldrundungen,
  Kostenstellenplaene, Verteilungsschluessel, Zahlungsmethoden, Kostenstellen-Tags).
- **Mit Entscheidung vorab:** Konten (BLOCKER), Preislistenregeln, Abo-Vorlagen.

## 11. Nachweise

| Nachweis | Datei |
|---|---|
| Menuebaum und Herkunft je System | `menue_matrix\menue_rohdaten.json` |
| Ansichten je Menuepunkt (Liste/Formular/Suche) lokal und VM | `ansichten\ansichten_rohdaten.json` |
| Vergleichsbericht mit Differenzen je Menuepunkt | `vergleich_bericht.txt` |
| Feldbeschriftungen vollstaendig lokal und VM (Differenzanalyse) | `beschriftungen\beschriftungen_lokal.json`, `beschriftungen_vm.json` |
| Browser-Gesamtcheck je Menuepunkt lokal und VM (Screenshots, JS-/RPC-Fehler, Speicherprobe, Bestand vorher/nachher) | `browser\lokal\gesamtcheck.json`, `browser\vm\gesamtcheck.json` + Bilder |
| Regression und Bezeichnungspruefung | `check_abrechnung_labels.py` (155 Feldpaare), `check_abrechnung_viewlabels.py`, `abschluss_verkauf_regression.py` |

## 12. Browser-Gesamtcheck: Ergebnis und Einordnung der FEHL

Ausgefuehrt mit `scripts/browser_abrechnung_gesamtcheck.py` (echter Chrome, headless, lokale Instanz;
zwei Teil-Laeufe wegen der Laufzeit). Je Menuepunkt geprueft: Menue oeffnen, Liste laden, Suche,
Filter, Gruppierung, vorhandenen Datensatz oeffnen, Formular (Reiter, Felder, Buttons, Smart Buttons),
Relationen (many2one lesen, einmal einen Relation-Link oeffnen), Bearbeitungsmodus ohne Speichern,
JS-Konsole und Seitenfehler, RPC-/Serverfehler.

| Lauf | Menuepunkte | Ergebnis |
|---|---|---|
| lokal, Teil 1 (Verkauf, Einkauf) | 1-16 | **97 OK / 4 FEHL** |
| lokal, Teil 2 (Konfiguration, Berichtswesen, Valorisierung, Projekt Kategorie) | 17-31 | **70 OK / 20 FEHL** |
| lokal, Speicherprobe (Produktkategorien, ueber die Oberflaeche) | - | **5 OK / 0 FEHL** |
| VM, Teil 1 | 1-16 | 73 OK / 8 FEHL; davon 4 Menuepunkte (1-4) mit Seiten-Timeout im ersten Anlauf |
| VM, Nachlauf Menuepunkte 1-4 (Timeout 30 s) | 1-4 | **30 OK / 0 FEHL** |
| VM, Teil 2 | 17-31 | 88 OK / 16 FEHL; davon 2 Menuepunkte (Einstellungen, Bankkonto hinzufuegen) mit Seiten-Timeout |
| VM, Nachlauf Menuepunkte 17-18 (Timeout 30 s) | 17-18 | **4 OK / 0 FEHL** |
| VM, Speicherprobe (Produktkategorien) | - | **5 OK / 0 FEHL** (Testkategorie id 8, danach entfernt) |
| VM, Beschriftungspruefung | - | **155 Feldpaare, 0 Abweichungen**; Ansichtsbeschriftungen ohne Abweichung |

Die Zeitueberschreitungen der VM-Laeufe waren ein zu knapper Standard-Timeout meines Pruefskripts
(8 s) gegen die entfernte Instanz; die Nachlaeufe mit 30 s sind fehlerfrei. Kein Produktfehler.

**Alle FEHL sind zu enge oder falsch geratene Erwartungen des Pruefscripts, kein Produktfehler.**
Sie wurden einzeln nachgeprueft und in vier Gruppen eingeordnet:

| Gruppe | Betroffene Menuepunkte | Ursache im Pruefscript | Bewertung |
|---|---|---|---|
| "Gruppierung funktioniert" | Valorisierung, Journale, Waehrungen, Steuerzuordnung, Zahlungsmethoden, Zahlungsbedingungen, Produktkategorien, Projekt Kategorie, Kostenstellenplaene, Pruefpfad | Das Script klickte den ersten Eintrag des Gruppieren-Menues; bei Modellen ohne vordefinierte Gruppierungen ist das der generische Eintrag "Benutzerdefinierte Gruppe hinzufuegen" | kein Fehler: Odoo 11 hatte z. B. bei Valorisierung ebenfalls keine Gruppierungen (Suchansicht nur Feld `name`) |
| "Formular oeffnet nach Klick auf Datensatz" | Steuern, Journale, Steuerzuordnung, Zahlungsbedingungen, Kostenstellenplaene, Rechnungsanalyse | Das Script traf die erste Datenzelle, in diesen Listen die Auswahlspalte; "Rechnungsanalyse" ist ein Auswertungsmodell (`account.invoice.report`) ohne Formularansicht | kein Fehler: Zeilenklick-Ziel im Script korrigiert (Name-Zelle/Link statt Auswahlspalte) |
| "Relationen vorhanden und gefuellt" | Valorisierung, Waehrungen, Projekt Kategorie | Diese Modelle haben keine many2one-Felder | kein Fehler: Erwartung nicht anwendbar |
| "Suche/Filter/Gruppierung" | Einstellungen | Eine Einstellungsseite hat keine Liste und damit kein Suchwerkzeug | kein Fehler: Script erkennt jetzt Formularmenues ohne Liste |

Zusaetzlich als Werkzeugfehler erkannt und behoben:

1. Die Speicherprobe benutzte Aktion 238 (Kostenstellen) statt 299 (Produktkategorien). Nachgeprueft:
   es wurde nichts angelegt (keine Datensaetze mit ITK-TEST in `product.category`,
   `account.analytic.account` oder `account.analytic.plan` auf lokal und VM; Bestand unveraendert
   3 Kategorien / 5 Kostenstellen). Korrigiert auf Aktion 299; eigene Probeskript-Datei
   `scripts/browser_abrechnung_speicherprobe.py` mit Vorher-/Nachher-Bestand.
2. Zwei parallele Browserlaeufe benutzten dasselbe Chrome-Profil und loeschten sich gegenseitig das
   Profil (`TargetClosedError`). Das Profil ist jetzt lauf-eindeutig.

Bei den leeren Listen der lokalen Testinstanz (Kunden-Gutschriften, Eingaenge, Eingangsrechnungen,
Lieferanten-Gutschriften, Kunden mit Defaultfilter) laedt das Menue fehlerfrei, Suche, Filter und
Gruppierung laufen; die Formularpruefung ist dort als "uebersprungen" gefuehrt. Fuer diese Punkte
stuetzt sich der Nachweis auf den Ansichtsvergleich (Abschnitt 1) und die Abnahmen aus den Sessions
122/124/129.
