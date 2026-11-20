# Übergabe Session 148 (19.11.2026) - Bereich Valorisierung abgeschlossen

**Einstieg für die nächste Session: diese Datei zuerst lesen.**

## 1 Stand

| Punkt | Wert |
|---|---|
| Bereich Valorisierung | **ABGENOMMEN UND GESPERRT** (19.11.2026) |
| Branch | `main`, PR #284 gemergt |
| Dreistand | lokal = GitHub main = VM = `8541043` |
| Arbeitsbäume | sauber (lokal und VM) |
| Gesperrte Bereiche | unverändert (Survey, CRM, Abrechnung, Projekt, Personal, Zeiterfassung, Anwesenheiten, Helpdesk, Events, E-Mail-Marketing, Website, Massenbearbeitung, Verkauf, Abonnements, Kontakte) |

## 2 Was in dieser Session gemacht wurde

1. **Odoo 11 read-only neu gemessen** (keine alten Zahlen übernommen):
   Modul `itk_valorisierung`, Modell `itk_valorisierung.valorisierung` mit `name`
   (Code), `description` (Beschreibung), `seq` (Nummernfolge), `_order = seq asc`;
   **10 Hinweise**, alle mit Text (1.462 Zeichen), alle `seq = 0`, kein `active`-Feld;
   keine berechneten Felder, keine Crons, keine Automationen, keine Record Rules.
   Rechnungsbezug `account.invoice.valorisierung_id`: **4.216 von 6.378** Rechnungen
   (4.208 Ausgangsrechnungen, 8 Gutschriften; 4.211 bezahlt, 4 offen, 1 Entwurf).
   Die Prozentsätze stehen ausschließlich im Text - kein Prozent-/Betragsfeld.
2. **Vergleich und Mapping** in `docs/o11-o18-vergleich-valorisierung.md`
   (Modelle, Felder, Rechnungsbezug, Menü, Ansichten, Rechte, Datenqualität,
   akzeptierte Abweichungen).
3. **Rechte auf Odoo-11-Stand zurückgeführt**: `itk_valorisierung` 18.0.1.4.0,
   `security/ir.model.access.csv` mit zwei Regeln (`itk_crm.itk_group_user` lesen,
   `itk_crm.itk_group_manager` alles) statt einer Regel für alle internen Benutzer.
   Zusätzlich entfernte `valorisierung_rechte_bereinigen.py` eine in beiden Datenbanken
   vorhandene Access-Regel **ohne Gruppe und ohne XML-ID**, die alle Gruppenrechte
   ausgehebelt hatte.
4. **Datenmigration**: 10 Beschreibungstexte, Anker `itk_o11_id`, Erstell-/Bearbeitungs-
   datum und Ersteller. `itk_migration_keys` 18.0.1.3.1 (Anker + Zeitstempel-Whitelist).
5. **Nachweise lokal und VM**: Abgleich je 64 OK / 0 (1 offene Abhaengigkeit), Rechte je 11 OK / 0,
   Browser je 15 OK / 0, Idempotenz je 0/0/10/0/0.
6. **Dokumentation**: Vergleichsdokument, `docs/migration/valorisierung_migration.md`,
   `docs/migrationsskripte-inventur.md`, `MIGRATION_READINESS_CHECKLIST.md`,
   `PROJECT_KNOWLEDGE.md`, `README.md`, diese Übergabe.

## 3 EXTERNE ABHÄNGIGKEIT ABRECHNUNG - ERLEDIGT am 19.11.2026 (Session 149)

**Rechnungsverknüpfung:** 4.216 Odoo-11-Rechnungen tragen einen Valorisierungshinweis.
Die Rechnungen sind in Odoo 18 nicht migriert (Bereich Abrechnung in Arbeit), deshalb ist
`account.move.valorisierung_id` nicht befüllbar. `account.move` führt außerdem noch
keinen Migrationsanker `itk_o11_id`.

**ERLEDIGT:** Der Nachlauf wurde nach der Rechnungsmigration auf lokal und VM ausgefuehrt:
4.214 von 4.216 Beziehungen gesetzt und geprueft, 0 Verteilungsabweichungen. Die zwei
offenen Beziehungen gehoeren zu den 53 nicht migrierten Belegen (namenlose Kontakte).
Details: `docs/uebergabe-session-149.md`.

Der Nachlauf ist bereits implementiert und getestet:

```
python scripts/migration/valorisierung_migration.py --instanz lokal|vm --nachlauf-rechnungen
python scripts/migration/valorisierung_migration.py --instanz lokal|vm --nachlauf-rechnungen --ausfuehren --ich-habe-freigabe
python scripts/migration/valorisierung_abgleich.py --instanz lokal|vm
```

Was der Nachlauf tut: liest alle Odoo-11-Rechnungen mit Hinweis, ermittelt die migrierte
Odoo-18-Rechnung über `account.move.itk_o11_id`, setzt nur abweichende Beziehungen
(idempotent), meldet nicht zuordenbare Fälle mit technischen IDs und prüft danach Anzahl
und Verteilung je Hinweis gegen Odoo 11.

Voraussetzung ist erfüllt: `account.move.itk_o11_id` ist seit `itk_migration_keys`
18.0.1.4.0 vorhanden.

Werkzeugtest am 19.11.2026 (lokal, mit 5 echten Odoo-11-Rechnungen und 5 vorhandenen
Odoo-18-Testrechnungen, danach vollständig zurückgenommen): Trockenlauf 1 korrekt / 4 zu
setzen / 4.211 nicht zuordenbar; Schreiblauf 4 gesetzt, Nachprüfung 0
Verteilungsabweichungen; zweiter Lauf 0 zu setzen (idempotent). Bestand vorher = nachher.

Erwartetes Ergebnis nach dem echten Nachlauf: 4.216 verbundene Rechnungen, 0 nicht
zuordenbar, 0 Verteilungsabweichungen, Abgleich ohne Abweichung.

**Testdatensatz "VAL-OK"** ist ein rein technischer Odoo-18-Testdatensatz, **kein
fachlicher Odoo-11-Bestand** (kein `itk_o11_id`, kein Text, kein Gegenstück in Odoo 11).
Er bleibt vorerst stehen, weil ihn Testrechnungen der Abrechnungsrunde verwenden (lokal
1, 66, 67; VM 1) - mit diesen entfernen, nicht vorher. In der Produktionsmigration wird er
nicht angelegt (das Modul liefert nur die zehn `valorisierung_o11_*`-Daten), und der
Nachlauf kann ihn nie als Ziel wählen, weil Ziele ausschließlich über `itk_o11_id`
bestimmt werden. Prüfung vor Produktivstart:
`select count(*) from itk_valorisierung_valorisierung where itk_o11_id is null;` muss 0 sein.

## 4 Werkzeuge

| Zweck | Aufruf |
|---|---|
| Trockenlauf | `python scripts/migration/valorisierung_migration.py --instanz lokal\|vm` |
| Schreiblauf | `... --ausfuehren --ich-habe-freigabe [--mapping <pfad ausserhalb des Repos>]` |
| Abgleich | `python scripts/migration/valorisierung_abgleich.py --instanz lokal\|vm` |
| Rechte prüfen | `python scripts/migration/valorisierung_rechte_pruefung.py --instanz lokal\|vm` |
| Rechte bereinigen | `python scripts/migration/valorisierung_rechte_bereinigen.py --instanz ... [--ausfuehren --ich-habe-freigabe]` |
| Browser | `uv run --with playwright python scripts/browser_valorisierung_daten_abnahme.py --instanz lokal\|vm` |
| Regression | `python scripts/regression_gesperrte_bereiche.py --instanz lokal\|vm` (Hintergrund, 40 Minuten) |

## 5 Lehren aus dieser Session

- **`account.move` hat keinen Migrationsanker** - Skripte dürfen `itk_o11_id` dort nicht
  voraussetzen, sondern müssen das Feld per `fields_get` prüfen (sonst Abbruch).
- **`itk.migration.zeitstempel` führt eine Whitelist** (`ERLAUBTE_MODELLE`). Ein neues
  Modell muss eingetragen werden, sonst schlägt nur der Zeitstempel-Schritt fehl - die
  übrigen Felder sind dann schon geschrieben.
- **Odoo-11-Benutzer `admin` existiert in Odoo 18 nicht.** Ohne Zuordnungsregel landet
  der Ersteller bei "OdooBot" (uid 1). Regel `admin -> Administrator` wie im CRM.
- **Access-Regeln ohne Gruppe hebeln Gruppenrechte aus.** Die Prüfung "interner Benutzer
  darf nicht schreiben" deckt das auf; die Bereinigung ist jetzt ein Skript, kein
  Handeingriff. Ohne diesen Schritt war die VM-Prüfung 6/7 fehlerhaft, lokal nur deshalb
  grün, weil die Regel dort in derselben Session entfernt worden war.
- **Werkzeuggrenze:** `inner_text` liest Textarea-Werte nicht - bei Odoo-Textfeldern
  `input_value()` verwenden. Sonst entstehen falsche "FEHL"-Meldungen (kein Produktfehler).
- **Regression lokal dauert ~40 Minuten** (Verkauf 453 s, Massenbearbeitung 618 s,
  Helpdesk 239 s). Im Hintergrund laufen lassen, nicht im Foreground mit 600-s-Grenze.

## 6 Referenzwerte für die nächste Session

| Größe | Wert |
|---|---|
| Valorisierungshinweise Odoo 11 / Odoo 18 | 10 / 11 (10 migriert + "VAL-OK") |
| Textzeichen gesamt | 1.462 |
| Rechnungen mit Hinweis Odoo 11 / verbunden in Odoo 18 | 4.216 / 0 (offen) |
| Regression lokal | 725 OK / 9 FEHL (Referenz unverändert seit Session 145, im Alleinlauf) |
| Regression VM | 725 OK / 9 FEHL im Alleinlauf (identisch zu lokal) |
| Dreistand | `8541043` |

## 7 Nächster Schritt (nicht automatisch beginnen)

Nicht abgenommen sind weiterhin unter anderem **Abrechnung (Datenmigration)**,
**Produkte/Preislisten (Abnahme)**, **Lager**. Der Rechnungsbezug der Valorisierung wird
beim Bereich Abrechnung nachgezogen (Abschnitt 3). Es wird nichts an diesem Bereich
geändert, solange nicht ausdrücklich beauftragt.
