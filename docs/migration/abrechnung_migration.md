# Abrechnung: Migration Odoo 11 nach Odoo 18

Stand: 19.11.2026 (Session 149). Technische Dokumentation zum Skript
`scripts/migration/abrechnung_migration.py`. Fachliche Sicht:
`docs/o11-o18-abrechnung-datenmigration.md`.

## 1 Umfang

| Objekt | Odoo 11 (live 19.11.2026) | Ziel Odoo 18 |
|---|---|---|
| Rechnungen und Gutschriften | 6.378 | 6.325 (53 dokumentierte Lücke) |
| Rechnungszeilen | 10.157 | 10.075 |
| Zahlungen | 6.091 (10.931.018,24) | 6.091 als Zahlungsbelege |
| Summen | netto 10.127.812,76 / Steuer 2.012.116,35 / brutto 12.139.929,11 | siehe Abgleich |

## 2 Aufruf

```
# Trockenlauf (Standard, schreibt nichts)
python scripts/migration/abrechnung_migration.py --instanz lokal
python scripts/migration/abrechnung_migration.py --instanz lokal --limit 20

# Schreiblauf Rechnungen
python scripts/migration/abrechnung_migration.py --instanz lokal --ausfuehren --ich-habe-freigabe

# Zahlungen nachziehen
python scripts/migration/abrechnung_migration.py --instanz lokal --zahlungen belege --ausfuehren --ich-habe-freigabe

# Abgleich
python scripts/migration/abrechnung_abgleich.py --instanz lokal
```

Schalter für die fachlichen Weichen:

| Schalter | Werte | Standard | Bedeutung |
|---|---|---|---|
| `--zahlungen` | `keine`, `belege` | `keine` | Zahlungsbelege anlegen und ausgleichen |
| `--anhaenge` | `keine`, `pdf`, `alle` | `keine` | Rechnungsanhänge übernehmen (805 MB) |
| `--gutschrift-journal` | `eigenes`, `kundenrechnungen` | `eigenes` | Journal für Gutschriften |
| `--limit`, `--zahlungen-limit` | Zahl | - | Testlauf mit begrenzter Menge |

## 3 Sicherheitsmechanismen

- Quelle Odoo 11 wird ausschließlich gelesen; `Schreibschutz` bricht jeden Schreibaufruf im
  Trockenlauf ab.
- Schreiben nur mit `--ausfuehren --ich-habe-freigabe`.
- Rechnungen werden mit `state='posted'` **direkt** geschrieben, nicht über `action_post`:
  keine Nummernvergabe, keine Mails, keine Buchungsvalidierung, keine Folgeaktionen.
- Keine Crons, Automationen, Webhooks, Zahlungsprovider, Bank- oder SEPA-Aktionen, keine
  PDF-Erzeugung. Die Zahlungen werden ausschließlich im Bankjournal gebucht.
- Idempotenz über `itk_o11_id` auf `account.move` und `account.payment`; ein zweiter Lauf
  legt nichts neu an.
- Fehler werden gesammelt und mit Odoo-11-ID protokolliert, nicht still verschluckt.

## 4 Mapping (Kurzfassung)

| Odoo 11 | Odoo 18 |
|---|---|
| `account.invoice` | `account.move` |
| `number` (R-JJNNNN) | `name`, unverändert |
| `date_invoice` / `date_due` | `invoice_date` / `invoice_date_due`; `date` = Rechnungsdatum, bei Entwürfen ohne Datum das Erstellungsdatum |
| `state` draft/open/paid | `draft` bzw. `posted`; Zahlungsstatus über Zahlungen |
| Konto 8400 in allen Zeilen | Konto 4000 |
| Steuer „20% Umsatzsteuer“ | „20% Ust“ |
| `payment_term_id` | `invoice_payment_term_id` über den Namen |
| `origin` / `reference` / `comment` | `ref` / `payment_reference` / `narration` |
| `valorisierung_id` | `valorisierung_id` über `itk_o11_id` |
| `account.payment.invoice_ids` | Ausgleich über `account.move.line.reconcile` |

## 5 Sonderfälle und Ergebnisse

| Fall | Behandlung |
|---|---|
| 53 Rechnungen an 12 namenlosen Kontakten | nicht migriert (Kontakte bewusst ohne Namen abgenommen), dokumentierte Lücke 195.316,90 brutto |
| doppelte Nummer R-25001 | Gutschriften im eigenen Journal „Gutschriften“ (neu, Code GUTS) |
| 4 Entwürfe ohne Rechnungsdatum | `date` = Odoo-11-Erstellungsdatum, damit Odoo 18 das Pflichtfeld erfüllt |
| Zeilen ohne Produkt (1) | Freitextzeile ohne Produkt, Konto 4000 |
| 22 Zeilen ohne Steuer | bleiben ohne Steuer |
| Zeilen-Brutto 55,63 über Kopf-Brutto | Kopfwert maßgeblich, Abweichung dokumentiert |

## 6 Laufprotokoll

Wird nach dem Zahlungslauf mit den Endzahlen lokal und VM ergänzt.
