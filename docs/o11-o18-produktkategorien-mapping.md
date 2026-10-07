# Produktkategorien (product.category) Odoo 11 -> Odoo 18 - Mapping und Migrationsregel

Stand: 07.10.2026, Session 129. Auftrag: Produktkategorien als Stammdaten fuer die spaetere
Migration pruefen, Mapping erstellen, Zuordnung testen, Testlauf kontrolliert ausfuehren,
Testdaten vollstaendig entfernen. **Abrechnung bleibt IN ARBEIT.**

Quelle: Odoo 11 Produktion (portal.it-kommunal.at, DB ITK_V1_a) - ausschliesslich lesend.
Ziel: Odoo 18 Testinstanzen (lokal, VM odoo18_test).
Messskript: `scripts/erhebe_produktkategorien.py` (read-only, Erhebung als Textdatei ablegbar).

## 1. Bestand in Odoo 11

- Kategorien gesamt: **30**, davon **26 mit Produkten** (648 Produktvorlagen), **4 ohne Produkt**.
- **Alle 26 verwendeten Kategorien liegen flach auf oberster Ebene** (keine Ueberkategorie).
  Die einzige Hierarchie im Bestand ist die unbenutzte Kategorie id 2 "verkaufbar" (Pfad
  "All / Saleable") - Odoo-11-Standard, ohne Produkte.
- Die Wurzelkategorie ist id 1: deutscher Name **"Alle"**, englischer Name **"All"**
  (Pfad "All"). Uebersetzbare Namen sind der Kern dieser Aufgabe: derselbe Datensatz heisst in
  der deutschen Oberflaeche "Alle", in der englischen "All".

### Verwendete Kategorien mit Produktanzahl (Odoo 11, read-only)

| Vollstaendiger Pfad (Odoo 11) | Vorlagen | Varianten | Ueberkategorie |
|---|---|---|---|
| All | 175 | 175 | - |
| Nutzungsentgelt | 120 | 120 | - |
| Dienstleistungspauschale | 53 | 53 | - |
| Amtssignatur, E-Abfertigung, E-Postfaecher | 41 | 41 | - |
| Betriebskostenpauschale | 40 | 39 | - |
| amtsweg.gv.at Formularsammlung Individual Standard | 29 | 29 | - |
| Hinweisgeber | 28 | 28 | - |
| amtsweg.gv.at Region | 25 | 25 | - |
| amtsweg.gv.at Bundesland light | 22 | 22 | - |
| Mach Mit | 16 | 16 | - |
| amtsweg.gv.at. BLFS NOE | 16 | 16 | - |
| Heurigenanmeldung | 14 | 14 | - |
| amtsweg.gv.at Bundesland Standard | 14 | 14 | - |
| GemeindeCloud | 11 | 11 | - |
| Named-user Lizenz | 11 | 11 | - |
| amtsweg.gv.at BLFS OOE | 8 | 8 | - |
| KI-Antragsassistent | 7 | 7 | - |
| OOE Bauformulare Var. 3 | 5 | 5 | - |
| Artikel | 3 | 3 | - |
| Corporate-Lizenz | 3 | 3 | - |
| DSGVO-Verarbeitungsverzeichnis | 2 | 2 | - |
| amtsweg.gv.at Bundesland Standard OeStB Sondervariante | 2 | 2 | - |
| BLFS OOE Stadt Wels | 1 | 1 | - |
| Concurrent-User Lizenz | 1 | 1 | - |
| OOE Bauformulare Var. 2 | 1 | 1 | - |
| amtsweg.gv.at. BLFS OOE | 1 | 1 | - |

Ohne Produkt (unbenutzt, daher nicht migrieren): id 2 "verkaufbar" (Pfad "All / Saleable"),
id 34 "Transaktionen", id 45 "amtsweg.gv.at Premium Standard", id 59 "Whistleblowing".

### Migrationsrelevante Felder der verwendeten Kategorien

| Feld Odoo 11 | Belegung | Werte |
|---|---|---|
| property_account_income_categ_id (Erlöskonto) | 26 von 26 | einheitlich 8400 "Erlöse 19% USt" |
| property_account_expense_categ_id (Aufwandskonto) | 26 von 26 | einheitlich 3400 "Wareneingang 19% Vorsteuer" |
| parent_id | 26 von 26 leer | keine Hierarchie |

Der Kontenrahmen des Odoo-18-Testbestands ist ein anderer (240 Konten, z. B. 4000 "Brutto-
Umsatzerloese im Inland (20%)", 5010 "Wareneinkauf 20%"). **Die beiden Odoo-11-Konten 8400 und
3400 existieren dort nicht** - die Kontenfelder der Kategorien koennen im Testbestand deshalb
nicht gesetzt werden und bleiben offen (eigener Schritt "Kontenmigration"; die Kategorien
werden in Odoo 18 ohne diese beiden Felder angelegt, die Odoo-18-Vorgaben der Kategorie
bleiben unveraendert).

## 2. Mapping Odoo 11 -> Odoo 18

| Odoo-11-Kategorie | Ziel Odoo 18 | Begruendung |
|---|---|---|
| All (id 1) | vorhandene Kategorie "All" (id 1) | gleicher Name in beiden Sprachen; in beiden Systemen die Wurzelkategorie |
| die uebrigen 25 verwendeten Kategorien | **neu anzulegende Kategorie gleichen Namens** | Name in Odoo 11 und Odoo 18 identisch, keine Odoo-18-Entsprechung vorhanden |
| All / Saleable (unbenutzt) | keine Zuordnung | in Odoo 11 ohne Produkte; Odoo-18-Kategorie "All / Saleable" bleibt unveraendert |
| Transaktionen, amtsweg.gv.at Premium Standard, Whistleblowing (unbenutzt) | keine Zuordnung | in Odoo 11 ohne Produkte |

Keine Zusammenlegung ueber aehnliche Namen: die 25 Kategorien sind fachlich eigenstaendig
(eigene Preise, eigene Zuordnung im Berichtswesen) und werden getrennt angelegt.

## 3. Migrationsregel fuer categ_id (endgueltig)

Umgesetzt in `scripts/testmigration_abrechnung.py` (`lade_kategorien`, `kategorie_im_ziel`):

1. Alle Odoo-11-Kategorien werden read-only **in beiden Sprachen** gelesen (de_DE und en_US).
2. Zuordnung ausschliesslich ueber **exakten Namen** - in beiden Sprachen - **und exakte
   Elternkette** (Vergleich parent_id, nicht Pfadtext). Eine Zuordnung ueber Aehnlichkeit
   findet nicht statt.
3. Genau ein Treffer mit passender Elternkette -> vorhandene Zielkategorie wird verwendet.
4. Mehrere Treffer, abweichende Elternkette -> **Abbruch mit Klartext** (kein stilles
   Ueberspringen, kein Zusammenlegen).
5. Kein Treffer -> Kategorie wird **nur in der Ziel-Testinstanz** angelegt, mit Namen in beiden
   Sprachen und derselben Elternkategorie wie in Odoo 11. Odoo 11 wird nie veraendert.
6. Angelegte Kategorien stehen im Protokoll (`neu: true`) und werden von `--aufraeumen`
   wieder entfernt.
7. Produkte erhalten die Kategorie ueber `categ_id`; fehlt die Kategorie im Ziel, wird sie
   vorher angelegt (keine leere Zuordnung).

Beispiel Wurzelkategorie: Odoo-11-"Alle"/"All" wird ueber den englischen Namen auf die
vorhandene Odoo-18-Kategorie "All" (id 1) abgebildet - nicht neu angelegt.

## 4. Trockenlauf (nur lesend) - lokal und VM

`python scripts/testmigration_abrechnung.py --instanz lokal|vm --plan`

- Stammdaten: 4 Partner, 2 Journale, 1 Konto, 2 Steuern, 1 Zahlungsbedingung, **11 Produkte,
  30 Kategorien (Odoo 11)**.
- Steuern: "20% Umsatzsteuer" -> vorhandene Odoo-18-Steuer "20% Ust", "20% Vorsteuer" ->
  "20% Vst" (jeweils ueber die Odoo-11-Beschreibung "20% USt"/"20% VSt").
- Kategorien: 10 Produktpositionen -> "Amtssignatur, E-Abfertigung, E-Postfaecher" und
  "Nutzungsentgelt" fehlen im Ziel und werden beim Schreiblauf angelegt; "All" ist vorhanden.
- Plan: 76 Positionen, davon 24 im Ziel noch nicht vorhanden (11 Produkte, 2 Kategorien,
  4 Partner, 5 Belege, 1 Zahlung, 1 Belegpaar-Abstimmung).
- Ergebnis lokal und VM identisch, kein Abbruch, keine Mehrdeutigkeit. Protokolle:
  `Desktop/Odoo18-Abnahme-Session129/kategorien_testlauf/plan_lokal_neu.txt` und `plan_vm_neu.txt`.

## 5. Kontrollierter Testlauf auf der VM

`python scripts/testmigration_abrechnung.py --instanz vm --ausfuehren --ich-habe-freigabe`

- **Neu angelegt (23 Datensaetze):** 11 Produktvorlagen, **2 Produktkategorien**
  ("Amtssignatur, E-Abfertigung, E-Postfaecher" id 4, "Nutzungsentgelt" id 5), 4 Partner,
  5 Belege, 1 Zahlung (Protokoll 202 Eintraege gesamt, davon 179 bereits vorhandene
  Ziel-Datensaetze, die unveraendert wiederverwendet wurden).
- Belege: Betraege, Zustand und Restbetraege stimmen mit Odoo 11 ueberein
  (R-261121 1366,01 offen; R-26800, R-260993, R-26797 bezahlt; ein Entwurf).
- Produkt -> Kategorie nach dem Lauf (RPC-Gegenprobe der 11 Produkte):
  **11 OK / 0 FEHL** - 7x "Nutzungsentgelt", 2x "Amtssignatur, E-Abfertigung, E-Postfaecher",
  2x "All", jeweils gleich der Odoo-11-Kategorie.

## 6. Browserabnahme (echter Chrome, VM)

`uv run --with playwright python scripts/browser_kategorie_pruefung.py vm` -> **7 OK / 0 FEHL**

- Produktformular, Feld **"Interne Kategorie"** (Wert im Formularfeld gelesen):
  "Amtssignatur Verlaengerung bis 1.000 Einwohner" = "Amtssignatur, E-Abfertigung,
  E-Postfaecher"; "IFG-Portal Nutzungsentgelt je weiterem Mandanten" = "Nutzungsentgelt";
  "Einrichtungsgebuehr der Oesterreichischen Post AG" = "All".
- Produktliste nach **"Produktkategorie"** gruppiert: genau drei Gruppen, je Kategorie genau
  eine Gruppe - "All (12)", "Amtssignatur, E-Abfertigung, E-Postfaecher (2)",
  "Nutzungsentgelt (7)". Keine doppelten Gruppen, keine leere Gruppe.
- Bilder: `Desktop/Odoo18-Abnahme-Session129/kategorien_browser/vm/`.

## 7. Dubletten- und Aufraeumkontrolle

- Kategorien im Ziel waehrend des Tests: 5 = 3 Odoo-18-Standard ("All", "All / Expenses",
  "All / Saleable") + 2 neu angelegte. Keine Dubletten, keine unbenutzten Zusatzkategorien.
- Nach `python scripts/testmigration_abrechnung.py --instanz vm --aufraeumen`:
  **23 Datensaetze entfernt** (genau die im Protokoll als neu vermerkten), 0 waren bereits weg.
- Bestand VM vorher = nachher: Produktkategorien 3, Produktvorlagen 10, Varianten 10,
  Belege 59, Partner 70, Steuern 53, Zahlungsbedingungen 12.
- Restkontrolle: Kategorie "Nutzungsentgelt" 0 Treffer, Kategorie "Amtssignatur ..." 0,
  Testprodukte 0, Belege mit Odoo-11-Nummer 0. Keine Testdaten zurueckgeblieben.

## 8. Nachgeprueft: kein stilles Ueberspringen

Auf Auftrag ausdruecklich geprueft und nachgezogen (Details: `docs/o11-o18-testmigration-regel.md`):

- **Steuern** (`supplier_taxes_id`, `taxes_id`, Belegzeilen): Vier-Stufen-Zuordnung
  (Name, Odoo-11-Beschreibung, Satz+Verwendung). Keine Entsprechung -> Abbruch mit Klartext;
  mehrere Kandidaten -> Abbruch. Vorhandene Zielsteuer wird verwendet, **es wird keine
  zweite Steuer gleichen Inhalts angelegt**.
- **Mengeneinheiten** (`uom_id`, `uom_po_id`): genau ein Treffer (Name, dann ohne
  Gross-/Kleinschreibung), sonst Abbruch.
- **Kategorie** (`categ_id`): siehe Abschnitt 3.
- **Interne Referenz, Verkaufspreis** (`default_code`, `standard_price`): 1:1; leere Odoo-11-
  Werte werden bewusst nicht uebertragen (kein Fehlerfall).
- **Belegzeilen**: Produkt, Konto, Steuer, Waehrung und Zahlungsbedingung muessen eindeutig
  sein - sonst Abbruch (vorher wurden Produkt, Steuer und Zahlungsbedingung still ausgelassen).

## 9. Offene Punkte

1. Kontenfelder der Kategorien (Erloes-/Aufwandskonto 8400/3400) sind im Testbestand nicht
   abbildbar (anderer Kontenrahmen) - offen bis zur Kontenmigration.
2. Die 25 Kategorien werden durch die Migrationslogik **zur Laufzeit** angelegt und im
   Testlauf danach wieder entfernt. Sollen sie dauerhaft im Ziel vorab angelegt werden, ist
   das ein eigener, freizugebender Schritt (Stammdaten).
3. Abrechnung bleibt IN ARBEIT - nicht als abgeschlossen, eingefroren oder migrationsbereit
   markiert.
