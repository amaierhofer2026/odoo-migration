# Abrechnung - endgueltige Abnahmeliste der verbleibenden Abweichungen

Stand: 01.10.2026, Session 122. Grundlage: Browser-Abgleich lokal und VM, Matrix je Formular
(`docs/o11-o18-abrechnung-matrix-formulare.md`), Abschlussmatrix
(`docs/o11-o18-abrechnung-abschlussmatrix.md`). Odoo 11 wurde ausschliesslich gelesen, es wurde
keine Datenmigration durchgefuehrt.

Spalten je Abweichung: Odoo-11-Bezeichnung/Funktion | Odoo-18-Bezeichnung/Funktion |
fachlich gleichwertig | technische Umsetzung in Odoo 18 | spaetere Migrationsregel |
Begruendung, warum kein weiterer Umbau notwendig ist.

## A1. Spalte "Lieferant" (Odoo 11) gegen "Kunde" (Odoo 18) - bewusste Korrektur

| Punkt | Inhalt |
|---|---|
| Odoo 11 | Listenansicht der Rechnungen: Spalte mit der Beschriftung **"Lieferant"**, technisch das Feld `partner_id` |
| Odoo 18 | Spalte **"Kunde"**, technisch `invoice_partner_display_name` (Anzeigename des Rechnungspartners) |
| fachlich gleichwertig | **nein** - die Odoo-11-Beschriftung war fachlich falsch |
| technische Umsetzung | keine Aenderung; Odoo 18 benennt die Spalte korrekt nach der Belegart |
| Migrationsregel | Odoo 11 `account.invoice.partner_id` -> Odoo 18 `account.move.partner_id`, 1:1 ohne Transformation; die Beschriftung ist reine Anzeige |
| Begruendung | Nachgewiesen am Quellcode: in der Odoo-11-Ansicht traegt das Feld `partner_id` das Attribut `string="Lieferant"`. In der Liste der Ausgangsrechnungen zeigt diese Spalte den **Kunden** (bei Eingangsrechnungen den Lieferanten). Eine Angleichung wuerde eine fachlich falsche Beschriftung uebernehmen; Odoo 18 loest das ueber getrennte Belegarten und Sichten korrekt. Datenmigration ist davon nicht betroffen. |

## A2. Rechnungszeile: Beschreibung, Total, Sektion, Kostenstellen-Tags

| Odoo 11 | Odoo 18 | fachlich gleichwertig | technische Umsetzung in Odoo 18 | Migrationsregel | Begruendung |
|---|---|---|---|---|---|
| Spalte **Beschreibung** (`account.invoice.line.name`, Text, Bezeichnung des Feldes in beiden Systemen "Beschreibung") | Spalte **Produkt** (`account.move.line.name`, Zeichen) mit dem Widget `product_label_section_and_note_field`; Produkt, Abschnitt, Notiz und Beschreibung werden in einer Spalte dargestellt | ja | Die Bezeichnung wird im Produktfeld mitgefuehrt und dort auch bearbeitet; kein separates Spaltenfeld | `account.invoice.line.name` -> `account.move.line.name`, 1:1; Abschnitts- und Notizzeilen ueber `display_type` | Die Information ist vollstaendig vorhanden und editierbar; eine eigene Spalte gaebe es in Odoo 18 nur ueber einen Eingriff in das Standard-Widget und wuerde die Abschnitts-/Notizfunktion brechen |
| Spalte **Total** (Feld `price_total`, Bezeichnung "Betrag") | Spalte **Total** (`account.move.line.price_total`), in der Ansicht gesetzt; sichtbar abhaengig von der Preisangabe (Steuer inklusive) | ja | Beschriftung der Spalte wurde auf den Odoo-11-Wortlaut "Total" gesetzt; die Sichtbarkeit steuert Odoo 18 (netto: Zwischensumme, brutto: Total) | `price_total` -> `price_total`, 1:1 | Beide Systeme zeigen je nach Preisangabe eine der beiden Betragsspalten; in Odoo 18 ist die Steuerung ueber `column_invisible` ausdruecklich vorgesehen. Kein Umbau notwendig, die Ausgabe bleibt fachlich korrekt |
| Spalte **Sektion** (`layout_category_id`, many2one) | Zeilentyp **Abschnitt** (`display_type = 'line_section'`), ueber "Abschnitt hinzufuegen" in den Rechnungszeilen | ja | Abschnitte sind in Odoo 18 eigene Zeilen statt einer Spalte; die Beschriftung des Abschnitts steht in `name` | Die 2 Odoo-11-Zeilen mit gesetztem `layout_category_id` (von 10.057 Zeilen) werden als Abschnittszeilen uebernommen; Stammdaten der Sektionen entfallen, da es in Odoo 18 kein entsprechendes Modell gibt und nur 2 Zeilen betroffen sind | Odoo 18 hat Sektionen bewusst von einer Spalte zu einem Zeilentyp gemacht; die Funktion (Gliederung der Rechnung) ist vollstaendig vorhanden, ein Nachbau des Odoo-11-Modells waere unnuebrig |
| Spalte **Kostenstellen-Tags** (`analytic_tag_ids`) | kein direktes Gegenstueck; Kostenstellen laufen in Odoo 18 ueber `analytic_distribution` und Kostenstellenplaene | nein, aber ohne Datenverlust | Keine Umsetzung notwendig - es gibt nichts zu uebertragen | **0 von 10.057** Odoo-11-Rechnungszeilen verwenden Kostenstellen-Tags; das Odoo-18-Modell `account.analytic.tag` existiert nicht mehr (Odoo 17 hat Tags durch Kostenstellenplaene ersetzt). Ist-Wert in Odoo 18: 0 Zeilen mit Kostenstellenverteilung | Ohne Verwendungsdaten und ohne Empfaengermodell ist weder ein Umbau noch eine Migrationsregel erforderlich; die Kostenstelle selbst (`account_analytic_id` -> `analytic_distribution`) ist gemappt und ebenfalls mit 0 Verwendungen belegt |

## A3. Smart Buttons der Zahlung

| Punkt | Inhalt |
|---|---|
| Odoo 11 | Smart Buttons im Zahlungsformular: **"Buchungszeilen"** (Feld `move_line_ids`, in 5.989 Zahlungen belegt), **"Rechnungen"**, **"Zahlungsabstimmung"** |
| Odoo 18 | Smart Buttons derselben Bereiche mit dynamischen Bezeichnungen und Anzahl, z. B. "Rechnung (Anzahl)", "Transaktion", "Abgestimmte Zeilen", "Erstattungen" |
| fachlich gleichwertig | ja - die Funktionen sind vollstaendig vorhanden (Buchungszeilen der Zahlung, verknuepfte Rechnungen, abgestimmte Posten, Erstattungen) |
| technische Umsetzung | keine Umbenennung: die Odoo-18-Bezeichnungen werden bewusst beibehalten |
| Migrationsregel | Zahlung -> Zahlung ohne Transformation; die Verknuepfungen entstehen durch die Abstimmung (`reconciled_invoice_ids`), nicht durch Bezeichnungen |
| Begruendung | Es liegt keine 1:1-Feldbezeichnung vor: die Odoo-18-Texte enthalten zur Laufzeit Zaehler und verweisen auf andere Objekte (Transaktionen statt Buchungszeilen, abgestimmte Zeilen statt Assistent). Ein Umbau wuerde Anzeigeinformationen verlieren, ohne fachlichen Gewinn |

## A4. Berichtsassistenten aus Odoo 11

| Punkt | Inhalt |
|---|---|
| Odoo 11 | Acht Berichtsassistenten unter "Berichtswesen > PDF Berichte" bzw. "Verwaltung": Audit Journale, alter Partner Saldo, Umsatzsteuerbericht, Rechnungsanalyse, Bilanz/Gewinn und Verlust, vorlaeufige Bilanz, Umsaetze nach Konten, Partner-Kontoauszug |
| Odoo 18 | Nicht vorhanden; Odoo 18 Community bietet Rechnungsanalyse, Pruefpfad und Abrechnungspositionen als eigene Auswertungen |
| fachlich gleichwertig | nein - die Assistenten fehlen vollstaendig, ihre Nutzung ist in Odoo 11 nicht nachweisbar (kein Berichtsprotokoll in Community, 12.350 Anhaenge ohne Berichtsbezug geprueft) |
| technische Umsetzung | keine; bewusster Verzicht |
| Migrationsregel | keine Datenmigration - Berichte erzeugen keine Daten |
| Begruendung | Lizenz-/Community-bedingt (das Enterprise-Berichtsmodul `account_reports`/`accountant` ist nicht installiert, Entscheidung von Anna). Kein Nachbau ohne nachgewiesenen fachlichen Bedarf; Auswertungen koennen spaeter mit Community-/ITK-Mitteln entstehen |

## A5. Bankkonto-Feldtexte

| Punkt | Inhalt |
|---|---|
| Odoo 11 | "Bank Identifikations-Code", "Kontotyp", "Finanz-Journal" (`res.partner.bank.bank_bic`, `acc_type`, `journal_id`) |
| Odoo 18 | Feldbezeichnungen "BIC", "Typ", "Konto Journal" - diese Felder sind in keiner Bankkonten-Formularansicht sichtbar |
| fachlich gleichwertig | ja (gleiche Felder) |
| technische Umsetzung | keine - es gibt keine sichtbare Stelle zum Angleichen (die Felder werden in Odoo 18 in der Bankkonten-Sicht nicht gerendert) |
| Migrationsregel | `res.partner.bank`: `acc_number`, `bank_bic`, `acc_type`, `journal_id` werden 1:1 uebernommen; Beschriftungen sind reine Anzeige |
| Begruendung | Ohne sichtbares Feld ist eine Umbenennung wirkungslos; die Datenmigration haengt nicht an Beschriftungen |

## A6. Systemweite Odoo-Kernbezeichnungen

| Punkt | Inhalt |
|---|---|
| Odoo 11 | z. B. "Abonnenten", "Zuletzt aktualisiert durch", "Nummernfolge" |
| Odoo 18 | "Follower", "Zuletzt aktualisiert von", "Sequenz" (in den Abrechnungsansichten wurden die Abrechnungs-relevanten Vorkommen angeglichen, u. a. Journale, Steuerzuordnung, Zahlungsbedingungen) |
| fachlich gleichwertig | ja |
| technische Umsetzung | teilweise angeglichen (dort, wo das Feld in einer Abrechnungsansicht sichtbar ist); im uebrigen System unveraendert |
| Migrationsregel | keine - Beschriftungen ohne Datenwirkung |
| Begruendung | Diese Bezeichnungen gehoeren zum Odoo-Kern und erscheinen in allen Modulen (Chatter, Audit-Felder). Eine systemweite Umbenennung waere ausserhalb des Bereichs Abrechnung und wuerde andere Bereiche veraendern (Vorgabe: nur sichtbare Bezeichnungen im Abrechnungsbereich angleichen) |

## A7. Menuegruppierungen

| Punkt | Inhalt |
|---|---|
| Odoo 11 | "Konfiguration > Verwaltung > Zahlungsbedingungen"; "Verwaltung" enthaelt Zahlungsbedingungen und Bargeldrundungen |
| Odoo 18 | Zahlungsbedingungen wurde nach Odoo-11-Vorbild nach "Konfiguration > Verwaltung" verschoben (wird nach jedem Upgrade erneut gesetzt); Odoo-18-Zusatzmenues (Rechnungsanalyse, Pruefpfad, Abrechnungspositionen, Eingaenge, Kostenstellenplaene, Verteilungsschluessel) bleiben erhalten |
| fachlich gleichwertig | ja |
| technische Umsetzung | Menue-Verschiebung per Label-/Menue-Lauf (`scripts/apply_abrechnung_labels.py`), kein Eingriff in Menue-IDs |
| Migrationsregel | keine - Menues enthalten keine Daten |
| Begruendung | Die verbleibenden Unterschiede sind reine Gruppierungen des Odoo-18-Standards (z. B. "Rechnungsstellung" als Konfigurationsabschnitt, Zahlungsanbieter unter "Zahlungen"); alle Punkte sind erreichbar und benannt wie in Odoo 11 |

## Abschluss

Alle sieben Abweichungen sind dokumentiert, keine davon ist funktional oder migrationsrelevant:
- Funktionen sind vorhanden (Sektionen, Kostenstelle, Betrags-Spalten, Smart Buttons, Assistenten,
  Druck und Versand).
- Fehlende Elemente haben **keine Verwendungsdaten** in Odoo 11 (Kostenstellen-Tags 0 von 10.057,
  Kostenstelle 0 von 10.057, Sektion 2 von 10.057) oder erzeugen keine Daten (Berichte, Menues,
  Beschriftungen).
- Die Datenzuordnung ist fuer die spaetere Migration eindeutig: `partner_id`, `name`,
  `price_subtotal`, `price_total` 1:1; Sektionen als Abschnittszeilen; Kostenstelle ueber
  `analytic_distribution`; Bankkonten 1:1.

Damit ist der Bereich **Abrechnung endgueltig eingefroren**: funktional vollstaendig und
migrationsvorbereitet. Ab hier keine Umbauten mehr, ausser es wird ein konkreter reproduzierbarer
Fehler gefunden.
