# Übergabe Session 149 (19.11.2026) - Bereich Abrechnung / Rechnungen

**Einstieg für die nächste Session: diese Datei zuerst lesen.**

## 1 Stand

| Punkt | Wert |
|---|---|
| Bereich Abrechnung / Rechnungen | **ABGENOMMEN UND GESPERRT** (lokal und VM) |
| Valorisierung | externe Abhängigkeit Abrechnung **erfüllt** (4.214 von 4.216 Beziehungen) |
| Branch / PR | `feat/abrechnung-datenmigration`, PR #289 gemergt |
| Regression lokal | 725 OK / 9 FEHL (Referenz unverändert) |
| Regression VM | 722 OK / 11 FEHL |
| Gesperrte Bereiche | unverändert |

## 2 Was in dieser Session gemacht wurde

1. **Odoo 11 live erhoben** (read-only): 6.378 Belege (6.139 Ausgangsrechnungen, 239
   Gutschriften, keine Eingangsbelege), 4 Entwurf / 48 offen / 6.326 bezahlt / 0 storniert,
   10.157 Zeilen, 6.091 Zahlungen, 9.407 Anhänge (805 MB). Summen netto 10.127.812,76 /
   Steuer 2.012.116,35 / brutto 12.139.929,11, offener Rest 138.320,55.
2. **Migrationsskript** `scripts/migration/abrechnung_migration.py` mit Trockenlauf,
   Freigabe, Idempotenz, Mapping-Export und Schaltern für die offenen Weichen.
3. **6.325 Belege migriert** (6.096 Rechnungen, 229 Gutschriften), 10.075 Zeilen,
   historische Nummern unverändert, Steuer 20 % Ust, Konto 4000.
4. **Zahlungen**: 6.091 Zahlungsbelege plus Ausgleich; 227 Rechnungen ohne Odoo-11-Beleg
   erhielten eine Ersatzzahlung mit Herkunftsvermerk.
5. **Nachweise lokal**: Abgleich 15/0, Browser 11/0, Rechte 6/0, Idempotenz 0/6.325/0/0,
   Valorisierungs-Nachlauf 4.214 korrekt / 0 zu setzen / 0 Verteilungsabweichungen.
6. **Dokumentation**: `docs/o11-o18-abrechnung-datenmigration.md`,
   `docs/migration/abrechnung_migration.md`, Checkliste, PROJECT_KNOWLEDGE, Inventur.

## 3 Offene Punkte

| Punkt | Stand |
|---|---|
| VM-Datenmigration | abgeschlossen, Ergebnisse identisch zu lokal |
| VM-Regression | 722 OK / 11 FEHL (Personal 2 = Werkzeuggrenze, belegt) |
| Anhänge (9.407, 805 MB) | nicht migriert; Schalter `--anhaenge` vorhanden, Entscheidung Anna offen |
| 53 Belege an 12 namenlosen Kontakten | nicht migriert, dokumentierte Lücke 195.316,90 brutto |
| 2 Valorisierungsbeziehungen | in dieser Lücke, daher nicht zuordenbar |

## 4 Fachliche Entscheidungen (Anna war nicht erreichbar, jeweils korrigierbar)

| Weiche | Entscheidung | Begründung |
|---|---|---|
| Zahlungsstatus | Zahlungsbelege mitführen und ausgleichen | sonst 6.326 bezahlte Rechnungen offen, Debitorenbilanz 12,1 Mio zu hoch |
| Belege ohne Odoo-11-Zahlungsbeleg (227) | Ersatzzahlung im Bankjournal mit Memo-Herkunft | Status wie Odoo 11, nachvollziehbar |
| Doppelte Nummer R-25001 | Gutschriften im eigenen Journal GUTS | beide Nummernkreise bleiben erhalten |
| 53 Belege ohne Partneranker | nicht migrieren | Kontakte wurden bewusst ohne Namen abgenommen, kein Sammelpartner |
| Anhänge | nicht migriert | 805 MB je Instanz, jederzeit per Schalter nachholbar |

## 5 Werkzeuge

| Zweck | Aufruf |
|---|---|
| Rechnungen (Trockenlauf) | `python scripts/migration/abrechnung_migration.py --instanz lokal\|vm` |
| Rechnungen (Schreiben) | `... --ausfuehren --ich-habe-freigabe [--limit N]` |
| Zahlungen | `... --zahlungen belege --ausfuehren --ich-habe-freigabe` |
| Ausgleich | `python scripts/migration/abrechnung_zahlungsausgleich.py --instanz ... --ausfuehren --ich-habe-freigabe` |
| Abgleich | `python scripts/migration/abrechnung_abgleich.py --instanz lokal\|vm` |
| Rechte | `python scripts/migration/abrechnung_rechte_pruefung.py --instanz lokal\|vm` |
| Browser | `uv run --with playwright python scripts/browser_abrechnung_daten_abnahme.py --instanz lokal\|vm` |
| Valorisierungs-Nachlauf | `python scripts/migration/valorisierung_migration.py --instanz ... --nachlauf-rechnungen [--ausfuehren --ich-habe-freigabe]` |

## 6 Lehren aus dieser Session

- **Rechnungen nie über `action_post` buchen**: direkt `state='posted'` schreiben, sonst
  Nummernvergabe, Mails und Automatismen.
- **`date` ist in Odoo 18 Pflicht**: Entwürfe ohne Rechnungsdatum brauchen das
  Odoo-11-Erstellungsdatum.
- **Gutschriften brauchen `payment_type='outbound'`**, sonst scheitert der Ausgleich.
- **Rechnung und Gutschrift nicht gegeneinander verrechnen**: Odoo 18 setzt `reversed`
  und zeigt "STORNIERT", obwohl die Rechnung in Odoo 11 bezahlt ist. Nach jedem Ausgleich
  den Belegstatus im Browser prüfen.
- **Odoo-18-Zahlungen kennen kein `posted`** (draft/in_process/paid/canceled) - ein Filter
  auf `state != 'posted'` markiert alles als offen.
- **Forderungskonto je Partner** (2000 Inland, 2100 EU): die Zahlungszeile muss vor dem
  Ausgleich auf das Konto der Rechnung umgehängt werden.
- **Ersatzzahlungen nur einmal anlegen**: mehrere Läufe erzeugten 392 Duplikate, die
  vollständig entfernt wurden (Aufräumskript im Scratch, Memo-Erkennung).
- **Regression nie parallel** lokal und VM fahren (Werkzeugabbrüche).

## 7 Referenzwerte

| Größe | Wert |
|---|---|
| Belege Odoo 11 / Odoo 18 | 6.378 / 6.325 (53 dokumentierte Lücke) |
| Zeilen | 10.157 / 10.075 |
| Summe netto | 9.965.048,68 / 9.965.048,68 (migrierbar) |
| Steuer/Brutto-Differenz | 55,63 (Odoo-11-Kopf-/Zeilendifferenz) |
| Offener Rest | 123.006,56 / 124.623,32 (Differenz 1.616,76 erklärt) |
| Zahlungsstatus | 6.275 bezahlt / 46 offen / 4 Entwurf |
| Valorisierungsbeziehungen | 4.214 gesetzt + geprüft, 2 in der Lücke |
| Regression lokal | 725 OK / 9 FEHL |

## 8 Nächster Schritt

1. VM-Migration abschließen (Rechnungen, Zahlungen, Ausgleich, Abgleich, Browser, Rechte).
2. VM-Regression allein fahren.
3. Dreistand herstellen, Bereichsstatus setzen.
4. Nicht automatisch mit dem nächsten Modul beginnen.
