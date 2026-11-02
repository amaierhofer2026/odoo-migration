# Uebergabe Session 139 -> 140

Stand: 02.11.2026. Diese Datei ist der Einstieg fuer die naechste Session.

## 1. Gesperrter Stand (nicht ohne ausdruecklichen Auftrag aendern)

| Bereich | Status |
|---|---|
| Projekt | ABGENOMMEN und GESPERRT |
| Personal | ABGENOMMEN und GESPERRT |
| Zeiterfassung | ABGENOMMEN und GESPERRT |
| Anwesenheiten / Urlaubsantraege | ABGENOMMEN und GESPERRT |
| Verkauf | ABGENOMMEN und GESPERRT |
| Abonnements | ABGENOMMEN und GESPERRT |
| Helpdesk | ABGENOMMEN und GESPERRT |
| **Events** | **ABGENOMMEN und GESPERRT** (30.10.2026, bestaetigt 02.11.2026) |
| **E-Mail-Marketing** | **ABGENOMMEN und GESPERRT** (30.10.2026, bestaetigt 02.11.2026) |

Diese Bereiche laufen nur noch in Regressionstests mit. Endpruefungen auf dem letzten
`main`: Events 61/0, E-Mail-Marketing 37/0 (je lokal und VM), Browser 35/0 und 20/0.

**Kontakte/Kundenverwaltung:** Struktur bearbeitet und migrationsbereit (Checkliste 6.1-6.10),
**Datenmigration bewusst offen** (Entscheidung Anna, 02.11.2026). Kein automatischer Start
der Kontaktmigration.

## 2. Bereiche, die noch NICHT strukturell bearbeitet sind

Read-only gegen Odoo 11 erhoben (02.11.2026), Details in Checkliste **6.20**.

| Bereich | Odoo-11-Module | Bestand Odoo 11 | Odoo 18 | Fachliches Gewicht |
|---|---|---|---|---|
| **Massenbearbeitung** | `mass_editing` | 20 Massenaktions-Objekte | Modul fehlt | hoch - taeglich genutztes Arbeitswerkzeug (Preisliste, Abo-Status, Zahlungsbedingungen, Rechnungs-/Leistungsdatum, Tag-Zuweisung, Lead-Quelle, Interessent-Status, Valorisierungstext) |
| **Website / Webinhalte** | `website`, `website_form`, `website_links`, `website_rating` | 17 Seiten, 11 Menues | 4 Seiten, 8 Menues (Demo) | hoch - kundennahe FAQ (Gemeindecloud/Ebox, IFG-Portal, Anonymisierungs-Portal, Kurse) |
| **Umfragen / Survey** | `survey`, `survey_crm` | 2 Umfragen, 2 Fragen, 73 Teilnahmen | nicht installiert | mittel - "Staedtebund Academy: Welche Kurse" mit 73 Antworten |
| **Valorisierung** | `itk_valorisierung` | 10 Valorisierungshinweise 2019-2026, 33 Kostenstellen | Modul fehlt | mittel - gehoert fachlich zur Abrechnung, dort noch nicht abgedeckt |
| **Lager / Bestand** | `stock`, `stock_account`, `sale_stock` | 262 Lagerbelege (231 offen, 31 storniert, **0 erledigt**), 342 Buchungen, 0 Bestandsmengen | 0 Belege | niedrig - keine Vollzuege, nur Verkaufsanbindung |

Ohne Handlungsbedarf: **Einkauf** (`purchase`, 0 Belege), **Reklamationen** (`bi_crm_claim`,
0 Datensaetze - bereits als tote Menues dokumentiert).

Nicht als eigener Bereich: **Kalender** (471 Termine sind Abwesenheitsbloecke aus
`hr_holidays`, gehoert zu Anwesenheiten), **Helpdesk-Daten** (1.254 `website_support`-Tickets,
Bereich gesperrt, Datenmigration dokumentierte Abhaengigkeit).

## 3. Empfehlung fuer die naechste Session

**Massenbearbeitung** oder **Website** - beide aus dem Bestand begruendet:

- Massenbearbeitung: die 20 Aktionen sind Arbeitsablaeufe, die ohne Ersatz fehlen
  (Odoo 18 bringt kein `mass_editing`; OCA-Module pruefen, sonst ITK-Nachbau).
- Website: die FAQ-Inhalte sind kundenrelevant; Odoo 18 hat nur Demoseiten.

Umfragen und Valorisierung sind klein und gut abgrenzbar, Lager hat keine Vollzuege.

## 4. Vorgehen pro Bereich (unveraendert)

1. Odoo-11-Livebestand read-only erheben, 2. Odoo-18-Bestand lokal + VM erheben,
3. Vergleichs-/Mappingdokument in `docs/`, 4. echte Entscheidungspunkte vorlegen,
5. Odoo 18 anpassen, 6. Trockenlauf, 7. lokal migrieren, 8. VM migrieren,
9. Idempotenz (zweiter Lauf ohne Dubletten), 10. Beziehungen und Mengen pruefen,
11. Browser lokal, 12. Browser VM, 13. Rechte mit Testbenutzern, 14. Regression der
gesperrten Bereiche, 15. eigene Testdaten entfernen, 16. Dokumentation
(Checkliste, PROJECT_KNOWLEDGE, README), 17. Commit/Push/PR/Merge,
18. VM auf `main`, 19. Dreistand nachweisen.

Regeln, die gelten: Odoo 11 niemals schreiben; keine Kontakte/Personen/E-Mail-Adressen
anlegen, solange die Kontaktmigration nicht freigegeben ist; Mehrdeutiges nicht raten,
sondern Kandidaten mit Vor-/Nachteilen vorlegen; Abnahme nur mit echtem Browserbild.

## 5. Start der naechsten Session

```
cd C:\Odoo-Test
git status --short --branch && git log --oneline -3
python "$LOCALAPPDATA/Temp/vm_exec.py" "cd /opt/odoo18 && echo HEAD=HEAD$(git rev-parse HEAD)ENDE; git status --porcelain | wc -l"
```

Regression vor dem ersten Eingriff (je `--instanz lokal` und `vm`):

```
python scripts/verify_s138_events.py --instanz lokal
python scripts/verify_s138_marketing.py --instanz lokal
python scripts/verify_personal.py --instanz lokal
python scripts/verify_s135_projekt.py --instanz lokal
python scripts/abschluss_verkauf_regression.py
```

## 6. Git-Stand

Der gueltige Stand ist immer `git log -1` (diese Datei kann ihren eigenen Commit nicht
enthalten). Letzter bekannter Stand vor dieser Uebergabe: `main` = `603c8e4`
(lokal, GitHub, VM gleich; Baum `074cd08`, Dateiliste `c9f2dbd`, Arbeitsbaeume sauber).

## 7. Werkzeuge (bereits vorhanden, weiterverwendbar)

| Datei | Zweck |
|---|---|
| `scripts/_o11o18_client.py` | RPC-Client `o11()` / `o18("lokal"\|"vm")`, read-only Zugriff |
| `scripts/upgrade_modules.py` | Modulinstallation/-update auf einer Instanz |
| `scripts/verify_s138_events.py`, `verify_s138_marketing.py` | Strukturabnahme der gesperrten Bereiche |
| `scripts/browser_events_abnahme.py`, `browser_marketing_abnahme.py` | Browserabnahme |
| `scripts/marketing_rechte.py` | Muster fuer Rechteproben mit Testbenutzer und Aufraeumen |
| `%LOCALAPPDATA%\Temp\vm_exec.py` | Shell auf der VM (Paramiko) |
