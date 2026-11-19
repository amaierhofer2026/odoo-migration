# Valorisierung: Migration Odoo 11 nach Odoo 18

Stand: 19.11.2026 (Session 148). Technische Dokumentation zum Skript
`scripts/migration/valorisierung_migration.py`.

## 1 Zweck und Umfang

Der Bereich Valorisierung besteht aus zehn Hinweistexten (Stammdaten), die auf
Rechnungen ausgewählt werden. In Odoo 18 existierten diese zehn Sätze bereits als
Modul-Daten des Moduls `itk_valorisierung` - aber **ohne Beschreibungstext** und ohne
Migrationskennung. Diese Runde ergänzt die Texte, setzt den Anker und bringt die Rechte
auf den Odoo-11-Stand.

| Objekt | Odoo 11 | Odoo 18 vorher | Odoo 18 nachher |
|---|---|---|---|
| Hinweise | 10 | 10 (+1 Testdatensatz) | 10 (+1 Testdatensatz) |
| Hinweise mit Text | 10 | 0 | 10 |
| Textzeichen gesamt | 1.462 | 0 | 1.462 |
| Migrationsanker `itk_o11_id` | - | 0 | 10 |
| Rechnungen mit Hinweis | 4.216 | 0 (keine migrierten Rechnungen) | 0 (offen, siehe 6) |

## 2 Quellen und Ziel

| Rolle | System |
|---|---|
| Quelle (nur lesend) | Odoo 11 Produktion `ITK_V1_a`, JSON-RPC über `scripts/_o11o18_client.py` |
| Ziel | Odoo 18 lokal (`odoo18_test`) bzw. VM (`odoo18_test` auf `k001959vsx.ipax.at`) |
| Zugangsdaten | ausschliesslich `C:\Odoo-Test\.env`, nicht im Repository |

Das Skript schreibt nie nach Odoo 11: Der Client kapselt Odoo 11 als Lese-Verbindung, und
ein `Schreibschutz`-Wrapper bricht jeden Schreibaufruf im Trockenlauf ab.

## 3 Aufruf

```
# Trockenlauf (Standard, schreibt nichts)
python scripts/migration/valorisierung_migration.py --instanz lokal
python scripts/migration/valorisierung_migration.py --instanz vm

# Schreiblauf (nur mit Freigabe)
python scripts/migration/valorisierung_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe

# Mapping-Export (ausserhalb des Repositories ablegen)
python scripts/migration/valorisierung_migration.py --instanz lokal \
  --mapping "%LOCALAPPDATA%\Temp\valo_mapping.json"
```

Ohne `--ich-habe-freigabe` endet ein Schreiblauf mit Rückgabewert 2 und der Meldung
`ABBRUCH: Schreiblauf nur mit --ich-habe-freigabe`.

## 4 Zuordnung (Idempotenz)

Reihenfolge der Zuordnung je Odoo-11-Hinweis:

1. `itk_o11_id` im Zielmodell (nach dem ersten Lauf gesetzt).
2. XML-ID `itk_valorisierung.valorisierung_o11_<Odoo-11-ID>` (Modul-Daten, `noupdate="1"`).
3. Name, getrimmt und nur wenn genau ein Treffer existiert.

Es wird kein Satz neu angelegt, solange die Modul-Daten vorhanden sind. Der Lauf schreibt
nur Felder, die tatsächlich abweichen (`description`, `seq`, `itk_o11_id`), und ist damit
wiederholbar.

Rechnungsverknüpfung: `account.move` führt in Odoo 18 noch keinen Migrationsanker. Das
Skript prüft das Feld (`fields_get`) und ordnet nur zu, was über einen Anker erreichbar
ist. Nicht zuordenbare Rechnungen werden gezählt, nicht geraten.

Ersteller: Der Odoo-11-Benutzer `admin` (Anzeigename "Administrator") wird auf das
bestehende Odoo-18-Konto `anna.maierhofer@it-kommunal.at` abgebildet (dieselbe Regel wie
im CRM). Alle anderen Benutzer über Login, danach über den Namen. Das Konto selbst wird
nicht verändert.

## 5 Ergebnis lokal (19.11.2026)

| Lauf | angelegt | aktualisiert | übersprungen | Fehler | Dubletten |
|---|---|---|---|---|---|
| Trockenlauf | 0 | 10 (angekündigt) | 0 | 0 | 0 |
| 1. Schreiblauf | 0 | 10 | 0 | 1 (Zeitstempel, siehe 7) | 0 |
| 2. Schreiblauf nach Whitelist-Ergänzung | 0 | 0 | 10 | 0 | 0 |
| 3. Lauf (Idempotenz) | 0 | 0 | 10 | 0 | 0 |

Zeitstempel: 10 Zeilen nachgezogen, danach 1 Zeile (Hinweis 1, Ersteller `admin`), danach 0.

Abgleich (`scripts/migration/valorisierung_abgleich.py --instanz lokal`): **65 Prüfungen
OK, 0 Abweichungen**, darunter je Hinweis Code, Nummernfolge, Beschreibung (Prüfsumme),
Erstellungsdatum, Bearbeitungsdatum und Erstellerzuordnung sowie die Summe der
Textlängen (1.462 Zeichen).

## 6 Offene Abhängigkeit: Rechnungsverknüpfung

4.216 Odoo-11-Rechnungen tragen einen Valorisierungshinweis. Die Rechnungen sind in
Odoo 18 nicht migriert (Bereich Abrechnung in Arbeit), deshalb ist
`account.move.valorisierung_id` in Odoo 18 nicht befüllbar.

Festlegung: Die **Stammdaten** sind in dieser Runde vollständig migriert. Die
**Rechnungsverknüpfung** wird mit der Rechnungsmigration nachgezogen. Das Skript meldet
die Zahl der offenen Fälle bei jedem Lauf (`Rechnungen mit Hinweis (O11) 4216, in Odoo 18
offen: 4216`). Es wird nichts geraten und nichts stillschweigend weggelassen.

## 7 Aufgetretene Fehler und Behebung

| Fehler | Ursache | Behebung |
|---|---|---|
| `WertError: Feld itk_o11_id existiert nicht auf account.move` | Rechnungen sind nicht migriert, Anker fehlt dort | Skript prüft das Feld per `fields_get` statt es vorauszusetzen |
| `Zeitstempel: Modell nicht erlaubt` | `itk.migration.zeitstempel` führt eine Whitelist | `itk_valorisierung.valorisierung` in `ERLAUBTE_MODELLE` aufgenommen (Modul 18.0.1.3.1) |
| Ersteller von Hinweis 1 war "OdooBot" | Odoo-11-`admin` hat in Odoo 18 keinen Login `admin` | Benutzerregel `admin -> Administrator` wie im CRM |
| Browserprüfung "Beschreibungstext sichtbar" schlug fehl | Werkzeuggrenze: `inner_text` liest Textarea-Werte nicht | Prüfung liest `input_value()` der Textareas - kein Produktfehler |

## 8 Rechte (Änderung in dieser Runde)

| Rolle | Odoo 11 | Odoo 18 vorher | Odoo 18 nachher |
|---|---|---|---|
| Interner Benutzer ohne ITK-Gruppe | kein Zugriff | **alle Rechte** (Regel ohne Gruppe) | kein Zugriff |
| `ITK / User (read only)` | lesen | alle Rechte | lesen |
| `ITK / Manager (edit)` | alles | alle Rechte | alles |
| Administrator | alles | alles | alles (Konto unverändert) |

Umsetzung: `addons/itk_valorisierung/security/ir.model.access.csv` führt jetzt zwei Regeln
(`itk_crm.itk_group_user` lesen, `itk_crm.itk_group_manager` alles). Eine in der Datenbank
manuell angelegte Regel ohne Gruppe und ohne XML-ID (alle Rechte für alle Benutzer) wurde
entfernt, weil sie die Gruppenrechte ausgehebelt hätte.

Prüfung: `scripts/migration/valorisierung_rechte_pruefung.py --instanz lokal|vm` legt
temporäre Benutzer in den drei Rollen an, prüft Lesen/Schreiben/Anlegen/Löschen und räumt
sie wieder ab. Ergebnis lokal: **11 Prüfungen OK, 0 Fehlschläge**, Bestand vorher =
nachher (11 Hinweise, 6.131 Kontakte).

## 9 Stammdaten-Abhängigkeiten

| Abhängigkeit | Status |
|---|---|
| Modul `itk_valorisierung` (Ziel) | installiert, 18.0.1.4.0 |
| Modul `itk_migration_keys` (Anker, Zeitstempel) | installiert, 18.0.1.3.1 |
| Gruppen `itk_crm.itk_group_user` / `itk_crm.itk_group_manager` | vorhanden, Administrator in beiden |
| Feld `valorisierung_id` auf `account.move` | vorhanden, im Formular nach dem Feld `notice` |
| Partnersätze, Produkte, Aufträge | für diesen Bereich nicht benötigt (keine eigenen Bezüge) |

## 10 Datenschutz

Die Hinweistexte sind fachliche Stammdaten ohne Personenbezug (Prozentsätze und
Indexbasis). Rechnungs-, Kunden- und Benutzerdaten werden nur gezählt, nie ausgegeben.
Der Mapping-Export enthält technische IDs, Namen der Hinweise und Textlängen - keine
Rechnungs- oder Kundendaten - und liegt ausserhalb des Repositories.

## 11 Ergebnisse VM (19.11.2026)

| Schritt | Ergebnis |
|---|---|
| `git pull` auf `main` | 8541043, Arbeitsbaum sauber |
| Upgrade `itk_valorisierung`, `itk_migration_keys` | ohne Fehler |
| Trockenlauf | 10 zu aktualisieren, 0 nicht zuordenbar, 4.216 Rechnungen offen |
| 1. Schreiblauf | 10 aktualisiert, 10 Zeitstempel nachgezogen, 0 Fehler |
| 2. Lauf (Idempotenz) | 0 angelegt, 0 aktualisiert, 10 übersprungen, 0 Zeitstempel, 0 Fehler, 0 Dubletten |
| Abgleich | **65 Prüfungen OK, 0 Abweichungen** |
| Rechteprüfung | nach Bereinigung **11 OK / 0** |
| Browserabnahme | **15 OK / 0**, Bestand 11 → 11 |
| Bestand | 11 Hinweise (10 Odoo-11-Sätze + Testdatensatz "VAL-OK", von 1 Testrechnung genutzt) |

## 12 Rechte-Altbestand auf der VM

Die VM führte dieselbe Access-Regel ohne Gruppe und ohne Modul-XML-ID (id 1541) wie die
lokale Instanz. Sie stammt nicht aus dem Repository (die CSV enthält nur die zwei
Gruppenregeln) und hebelt die Gruppenrechte aus. Bereinigung jetzt reproduzierbar:

```
python scripts/migration/valorisierung_rechte_bereinigen.py --instanz vm            # Trockenlauf
python scripts/migration/valorisierung_rechte_bereinigen.py --instanz vm --ausfuehren --ich-habe-freigabe
```

Das Skript entfernt ausschließlich Regeln ohne Gruppe **und** ohne XML-ID, ist idempotent
und zeigt vorher/nachher alle Regeln mit Gruppe und Rechten. Nach der Bereinigung bleiben
genau die zwei Modulregeln (User lesen, Manager alles); die Rechteprüfung bestätigt
11 OK / 0 auf der VM.

## 13 Bewusst akzeptierte Abweichungen

| Abweichung | Begründung |
|---|---|
| Rechnungsverknüpfung 0 von 4.216 | Rechnungen nicht migriert; Nachzug mit der Abrechnung (Abschnitt 6) |
| Testdatensatz "VAL-OK" bleibt | von 1 (VM) bzw. 3 (lokal) Testrechnungen der Abrechnungsrunde genutzt; Löschen würde Testrechnungen verwaisen lassen - nach der Abrechnungsmigration mit diesen entfernen |
| Nummernfolge durchgehend 0 | Odoo-11-Bestand, unverändert übernommen; damit keine fachliche Sortierung, wie in Odoo 11 |
| Schreibweisen der Codes gemischt ("VALORISIERUNGSHINWEIS 2019", "Valorisierungshinweis 2025", "VALORISIERUNGHINWEIS 2024 Acta Nova") | Odoo-11-Original, inklusive Tippfehler ohne "S" und Leerzeichen am Ende; bewusst nicht normalisiert |
| Odoo-18-Suchfilter und Gruppierungen | Standardfunktionen, stören die Odoo-11-Funktion nicht |
