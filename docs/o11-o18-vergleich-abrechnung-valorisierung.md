# Bereich Abrechnung > Konfiguration > Valorisierung - Vergleich Odoo 11 gegen Odoo 18

Stand: 07.10.2026, Session 130. Odoo 11 wurde ausschliesslich read-only gelesen
(portal.it-kommunal.at, DB ITK_V1_a). Ziel: der Bereich verhaelt sich in Odoo 18 fachlich
und visuell wie in Odoo 11; Odoo-18-Zusatzfunktionen bleiben erhalten. **Abrechnung bleibt
IN ARBEIT**, keine Freigabe.

## 1. Anlass

Manuelle Kontrolle (Anna, 07.10.2026) ergab eine sichtbare Abweichung in der Liste:

| | Odoo 18 vorher | Odoo 11 |
|---|---|---|
| Spalte 1 | Code | Code |
| Spalte 2 | Description | **Beschreibung** |
| Spalte 3 | Sequence | **Nummernfolge** |

Die uebrigen Angaben in diesem Dokument stammen aus dem read-only Vergleich, der daraufhin
vollstaendig nachgezogen wurde.

## 2. Modell und technische Feldnamen

| Punkt | Odoo 11 | Odoo 18 | Bewertung |
|---|---|---|---|
| Modell | `itk_valorisierung.valorisierung` | `itk_valorisierung.valorisierung` | identisch |
| `_description` | "Valorisierung" | "Valorisierung" | identisch |
| `_order` | `seq asc` | `seq asc` | identisch |
| Felder | `name`, `description`, `seq` + Metadaten (`create_uid`, `create_date`, `write_uid`, `write_date`, `__last_update`) | `name`, `description`, `seq` + dieselben Metadaten | identisch |
| Feldtypen | `name` char, `description` text, `seq` integer | ebenso | identisch |
| Pflichtfelder | keine | keine | identisch |
| `readonly` | nur Metadaten | nur Metadaten | identisch |
| Defaults | keine | keine | identisch |

Feldbeschriftungen (Quellsprache und deutsche Anzeige):

| Feld | Odoo 11 Quelle | Odoo 11 deutsch | Odoo 18 Quelle | Odoo 18 deutsch (nach Korrektur) |
|---|---|---|---|---|
| `name` | Code | Code | Code | Code |
| `description` | Description | Beschreibung | Description | Beschreibung |
| `seq` | Sequence | Nummernfolge | Sequence | Nummernfolge |

## 3. Ursache der Abweichung (nicht die Uebersetzung selbst)

Die Uebersetzungen standen in `addons/itk_valorisierung/i18n/de_DE.po` bereits richtig drin
("Description" -> "Beschreibung", "Sequence" -> "Nummernfolge"). Sie wurden aber nicht
angewendet, weil die Verweise (`#:`) in der Datei noch nach Odoo-11-Muster gebildet waren:

| | XML-ID des Feldes |
|---|---|
| Odoo 11 | `itk_valorisierung.field_itk_valorisierung_valorisierung_description` |
| Odoo 18 | `itk_valorisierung.field_itk_valorisierung_valorisierung__description` |

Odoo 18 erzeugt Feld-XML-IDs mit **doppeltem** Unterstrich vor dem Feldnamen (ebenso
`__seq`, `__name`, `__create_uid` ...). Da die Verweise nicht mehr auf ein Feld zeigten,
blieb die englische Quellbezeichnung sichtbar.

**Korrektur:** Verweise in `i18n/de_DE.po` auf das Odoo-18-Muster umgestellt.
Nachweis, dass Odoo 18 die `.po`-Datei auswertet und nicht die mitgelieferte, aus der
Odoo-11-Zeit stammende `de_DE.mo`: die Bezeichnungen folgen der geaenderten `.po`-Datei
(die `.mo` traegt die alten Verweise).

### 3.1 Zweiter Teil derselben Bezeichnungspruefung (nachgezogen)

Bei der Kontrolle der Feldbezeichnung am **Rechnungsformular** fiel eine weitere Abweichung auf,
die sich zwischen lokal und VM unterschiedlich zeigte:

| Stand | `account.move.valorisierung_id`, deutsch | englisch |
|---|---|---|
| Odoo 11 | "Valorisation Text" | "Valorisation Text" |
| Odoo 18 lokal (vorher) | "Valorisation Text" (nur scheinbar richtig - gespeicherter Altbestand in der Datenbank) | "Valorisierungstext" |
| Odoo 18 VM (vorher) | "Valorisierungstext" | "Valorisierungstext" |

Ursache: das Modul fuehrte das Feld mit der Quellbezeichnung "Valorisierungstext" (deutsch), die
von der Odoo-11-Bezeichnung "Valorisation Text" abweicht. Odoo 11 zeigt auch in deutscher Anzeige
"Valorisation Text" (nachgemessen mit `lang=de_DE`).

**Korrektur:** `addons/itk_valorisierung/models/account_invoice.py` fuehrt das Feld jetzt mit der
Odoo-11-Bezeichnung `string="Valorisation Text"`; die beiden `.po`-Eintraege
"Valorisation Text" / "Valorisation Texts" (deutsche Uebersetzung "Valorisierungs Text") sind
entfernt, damit die deutsche Anzeige wie in Odoo 11 unveraendert die Quellbezeichnung zeigt.
Modulstand: itk_valorisierung **18.0.1.3.0**.

Lehre fuer den Ablauf: eine `.po`-Aenderung greift schon beim Modul-Upgrade, eine Aenderung an
**Python**-Bezeichnungen erst nach einem **Neustart** des Odoo-Containers (danach Upgrade).
Beides wurde lokal und auf der VM so gefahren.

## 4. Ansichten

| Punkt | Odoo 11 | Odoo 18 | Bewertung |
|---|---|---|---|
| Listenansicht | View 1375 `tree`, `string="Valorisation Texts"`, Reihenfolge `name`, `description`, `seq` | `list`, gleiche Reihenfolge | identisch (Spaltenreihenfolge 1:1) |
| Formularansicht | View 1376 `form`, `sheet > group > name, description, seq` | ebenso, eine Gruppe, keine Reiter | identisch |
| Suchansicht | nur Feld `name` (Standard), keine Filter, keine Gruppierungen, keine Favoriten | ebenso | identisch |
| Buttons/Aktionen | keine (nur Speichern/Verwerfen des Formulars) | ebenso | identisch |
| Server-Aktionen | keine | keine | identisch |
| Sortierung | `_order = seq asc`; alle 10 Datensaetze haben `seq = 0` | ebenso (11 Datensaetze, alle `seq = 0`) | identisch; Reihenfolge praktisch nach ID |
| Anlage/Bearbeitung/Loeschen | ueber Formular, Standardrechte der ITK-Gruppen | ebenso ueber Formular | Funktion identisch, Rechtsmodell abweichend (Abschnitt 7) |

Menue und Aktion:

| Punkt | Odoo 11 | Odoo 18 |
|---|---|---|
| Menue | Abrechnung > Konfiguration > Valorisierung (Menue 392) | Abrechnung > Konfiguration > Valorisierung |
| Aktion | 528 `Valorisation Text`, `view_mode = tree,form` | 1117 `Valorisation Text` (Quelle) / "Valorisierungs Text" (deutsch) |
| Hilfe-Text (leere Liste) | "Create the first Valorisation Text" | derselbe Text (englisch, wie Odoo 11) |
| Zielmodell | `itk_valorisierung.valorisierung` | identisch |

Der Aktionsname ist in Odoo 11 auch in deutscher Anzeige "Valorisation Text" (keine
Uebersetzung hinterlegt), in Odoo 18 deutsch "Valorisierungs Text". Der Aktionsname ist im
Browser nicht sichtbar (Brotkrumen zeigen den Menuenamen "Valorisierung"); deshalb als
nicht sichtbare Abweichung dokumentiert, keine Aenderung.

## 5. Bestehende Datensaetze

Odoo 11 fuehrt **10** Valorisierungstexte (IDs 1-10), alle mit `seq = 0`, alle mit gefuellter
Beschreibung.

Odoo 18 fuehrt **11** Datensaetze: dieselben 10 Namen (angeliefert aus
`addons/itk_valorisierung/data/valorisierungstexte_o11.xml`, geladen 30.09.2026, `noupdate="1"`)
plus den Testwert `VAL-OK`.

| Odoo-11-ID | Name Odoo 11 | in Odoo 18 vorhanden | Beschreibung Odoo 18 |
|---|---|---|---|
| 1 | VALORISIERUNGSHINWEIS 2019 | ja | leer |
| 2 | VALORISIERUNGSHINWEIS 2020 | ja | leer |
| 3 | VALORISIERUNGSHINWEIS 2021 | ja | leer |
| 4 | VALORISIERUNGSHINWEIS 2022 | ja | leer |
| 5 | VALORISIERUNGSHINWEIS 2023 | ja | leer |
| 6 | Valorisierungshinweis 2024 | ja | leer |
| 7 | "VALORISIERUNGHINWEIS 2024 Acta Nova " (mit Leerzeichen am Ende) | ja, ohne Leerzeichen am Ende | leer |
| 8 | VALORISIERUNGSHINWEIS 2024 gerundete Zahlen | ja | leer |
| 9 | Valorisierungshinweis 2025 | ja | leer |
| 10 | Valorisierungshinweis 2026 | ja | leer |

Ergebnis: **alle 10 Odoo-11-Datensaetze sind eindeutig abbildbar** - Zuordnung ueber den Namen,
keine Dublette, keine Luecke. Einzige Besonderheit: ID 7 traegt in Odoo 11 ein Leerzeichen am
Ende, in Odoo 18 nicht; der bereinigte Name ist identisch, die Zuordnung bleibt eindeutig.

**Offener Migrationspunkt (Daten):** die Beschreibungen (`description`) sind in Odoo 18 leer -
die Moduldatei legt nur die Namen an. Bei der echten Datenmigration sind `name`, `description`
und `seq` zu uebertragen; `name` ist der stabile fachliche Schluessel.

## 6. Wo die Valorisierungstexte tatsaechlich verwendet werden

| Verwendung | Odoo 11 | Odoo 18 |
|---|---|---|
| Rechnung / Gutschrift | `account.invoice.valorisierung_id`, **4216** belegte Rechnungen | `account.move.valorisierung_id`, 1 belegter Entwurf (Testbeleg "Test Firma", 2,40 EUR, 13.07.2026) |
| Rechnungszeile | `account.invoice.line.valorisierung_id` (berechnet, kein eigener Wert) | `account.move.line.valorisierung_id` (berechnet) |
| Bankauszug | nicht vorhanden | `account.bank.statement.line.valorisierung_id` (Odoo-18-Feld, 0 Datensaetze) |

Im Rechnungsformular steht das Feld in Odoo 11 sichtbar: View 1377
`account.invoice.valorisierung` haengt eine Gruppe direkt nach der Rechnungsnotiz
(`notice`) im Bereich "Weitere Informationen" ein; `modifiers={}` = sichtbar. Odoo 11 zeigt
dort zuerst die Beschriftung "Rechnungsnotiz:" mit dem Notizfeld und direkt darunter den
Valorisierungstext.

## 7. Gefundene Abweichungen in Odoo 18 und ihr Status

| Nr | Abweichung | Nachweis | Status |
|---|---|---|---|
| 1 | Listen-/Formularbezeichnungen "Description"/"Sequence" statt "Beschreibung"/"Nummernfolge" | Browser lokal + VM | **behoben** (Verweise in der `.po`-Datei) |
| 2 | Feldbezeichnung am Beleg: "Valorisierungstext" statt Odoo-11-"Valorisation Text" (auf der VM sichtbar, lokal nur durch einen Altbestand in der Datenbank verdeckt) | RPC `lang=de_DE` / `lang=en_US` auf beiden Instanzen | **behoben** (Feldbezeichnung im Modell auf den Odoo-11-Wortlaut gesetzt, `.po`-Eintrag entfernt, itk_valorisierung 18.0.1.3.0) |
| 3 | `valorisierung_id` war im Rechnungsformular **nicht erreichbar**: die ITK-Kopfbereichs-Ansicht (`account.move.form.itk.o11.kopfbereich`) blendete das Feld aus, obwohl es (anders als die verschobenen Kopffelder) keine zweite Fundstelle hat. Odoo 11 zeigt es sichtbar. | Odoo 11: `fields_view_get(594,"form")` -> `modifiers={}`; Odoo 18: `invisible="1"` im kombinierten Arch, im Browser kein Element `[name="valorisierung_id"]` | **behoben** (Ausblendung entfernt, itk_account_migration 18.0.1.22.0) |
| 4 | `notice` (Rechnungsnotiz) ist im Rechnungsformular weiterhin ausgeblendet; Odoo 11 zeigt die Beschriftung "Rechnungsnotiz:" mit dem Notizfeld | wie Nr. 3 | **offen - Ihre Entscheidung.** Kein Feld des Valorisierungsbereichs; die Rechnungsnotiz gehoert zum Modul itk_subscription (abgeschlossener Bereich). Auf Ihren Zuruf eine Zeile in `account_move_form_kopf.xml`. |
| 5 | Zugriffsrechte: Odoo 11 trennt "ITK / User (read only)" und "ITK / Manager (edit)"; Odoo 18 gibt internen Benutzern volle Rechte auf die Valorisierungstexte | `ir.model.access` Odoo 11: 8 Eintraege (2 Saetze); Odoo 18: 4 Eintraege `base.group_user` | **offen - Ihre Entscheidung.** Gleiches Muster wie die uebrigen ITK-Stammdatenmodule in Odoo 18. |
| 6 | Platzierung des Valorisierungstexts im Formular: Odoo 11 im Bereich "Weitere Informationen" nach der Rechnungsnotiz, Odoo 18 im Kopfbereichsblock | Screenshot `03_rechnung.png` | dokumentierte Abweichung (Feld sichtbar und bedienbar; Verschiebung folgt dem Odoo-18-Ansichtsaufbau) |
| 7 | Aktionsname deutsch "Valorisierungs Text" statt Odoo 11 "Valorisation Text" | RPC mit `lang=de_DE` | nicht sichtbar (Brotkrumen zeigen den Menuenamen), keine Aenderung |

## 8. Datensatz VAL-OK (Herkunft geklaert, nicht geloescht)

| Frage | Befund |
|---|---|
| Woher kommt der Datensatz? | Manuell in der **Odoo-18-Testinstanz** angelegt: `create_uid = 2 (Administrator)`, `create_date = 2026-07-01 09:58:42` - also vor dem Laden der ITK-Moduldaten (30.09.2026) |
| Moduldatensatz? | Nein. Kein Eintrag in `ir.model.data`; `addons/itk_valorisierung/data/valorisierungstexte_o11.xml` enthaelt ihn nicht |
| In Odoo 11 vorhanden? | Nein, Odoo 11 fuehrt 10 Datensaetze ohne VAL-OK |
| Wird er verwendet? | Ja, von genau einem Test-Entwurf: Ausgangsrechnung "Test Firma", 2,40 EUR, 13.07.2026 (lokal und VM je 1 Beleg). Keine echten Belege |
| Schon dokumentiert? | Ja, in `docs/o11-o18-vergleich-abrechnung-teil1.md` (Zeile 364) und `docs/o11-o18-vergleich-abrechnung-teil5-umsetzung.md` (Zeile 31) als **Testwert** |
| Bewertung | Test-/Altbestand der Testinstanz, **keine** Migrationsnotwendigkeit, keine Produktivdaten |
| Massnahme | **nichts geloescht, nichts geaendert** (Ihre Vorgabe). Der Datensatz und der Testbeleg bleiben, bis Sie es anders entscheiden. |

## 9. Migrationsfelder

| Feld | Uebernahme | Schluessel |
|---|---|---|
| `name` | ja | stabiler fachlicher Schluessel (bereinigter Name; Odoo-11-ID 7 hat ein Leerzeichen am Ende) |
| `description` | ja, in Odoo 18 noch leer | Text, unveraendert uebernehmen |
| `seq` | ja | alle Werte 0; Sortierung bleibt `seq asc` |
| Verweis am Beleg | ja | `account.invoice.valorisierung_id` -> `account.move.valorisierung_id` ueber den Namen des Valorisierungstexts, nicht ueber die Datenbank-ID |

## 10. Nachweise

| Nachweis | Datei |
|---|---|
| Vergleich Modell/Ansichten/Daten Odoo 11 gegen Odoo 18 | `Desktop\Odoo18-Abnahme-Session129\valorisierung\vergleich_valorisierung.txt` |
| Detailpruefung Texte, Referenzen, Namen, Verwendung | `...\valorisierung\valorisierung_details.txt` |
| Browser-Abnahme lokal | `...\valorisierung\browser_lokal.txt`, Bilder `browser\lokal\01_liste.png`, `02_formular.png`, `03_rechnung.png` |
| Browser-Abnahme VM | `...\valorisierung\browser_vm.txt`, Bilder `browser\vm\` |
| Regression und Bezeichnungspruefungen | `...\valorisierung\regression_lokal.txt`, `regression_vm.txt` |
| Pruefskripte | `scripts/vergleiche_valorisierung.py`, `scripts/pruefe_valorisierung_details.py`, `scripts/browser_valorisierung_abnahme.py` |
