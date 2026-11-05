# Uebergabe Session 140 -> 141

Stand: 05.11.2026. Diese Datei ist der Einstieg fuer die naechste Session.

## 1 Gesperrter Stand (nicht ohne ausdruecklichen Auftrag aendern)

| Bereich | Status |
|---|---|
| Projekt | ABGENOMMEN und GESPERRT |
| Personal | ABGENOMMEN und GESPERRT |
| Zeiterfassung | ABGENOMMEN und GESPERRT |
| Anwesenheiten / Urlaubsantraege | ABGENOMMEN und GESPERRT |
| Verkauf | ABGENOMMEN und GESPERRT |
| Abonnements | ABGENOMMEN und GESPERRT |
| Abrechnung | MIGRATIONSBEREIT (Struktur), Datenmigration bewusst offen |
| Helpdesk | ABGENOMMEN und GESPERRT |
| Events | ABGENOMMEN und GESPERRT |
| E-Mail-Marketing | ABGENOMMEN und GESPERRT |
| **Massenbearbeitung** | **ABGENOMMEN und GESPERRT (05.11.2026, Session 140)** |

Die gesperrten Bereiche laufen nur noch in Regressionstests mit.

## 2 Was Session 140 gemacht hat

Bereich Massenbearbeitung vollstaendig abgeschlossen (Checkliste **6.21**, Dokument
`docs/o11-o18-vergleich-massenbearbeitung.md`):

- Odoo 11 read-only erhoben: 20 `mass.object`-Objekte, je eine Sidebar-Aktion, Menue
  `Einstellungen/Massenverarbeitung`, Rechte (Konfiguration nur Administration), Dialogoptionen.
- Umsetzung der Entscheidungen K1 bis K6 von Anna:
  K1 Dublette 1303 entfernt (wieder 20 Aktionen), K2 "Angebot zu Auftrag" wieder bedienbar
  (readonly wie Odoo 11, **kein** `action_confirm`), K3 Abo-Status unveraendert, K4 Bindung der
  Aktion "Execute Code" entfernt (Automatisierung bleibt), K5 neues Modul
  `itk_massenbearbeitung` mit Menue Massenverarbeitung, K6 kurze Namen.
- Technische Zusatzanpassungen im OCA-Modul `server_action_mass_edit` 18.0.1.1.4:
  T1 Stichwortfelder als Tags, T2 "Hinzufuegen" bei many2many schreibt Verknuepfungen.
- Nachweise: Browserabnahme **265 OK / 0 FEHL** je lokal und VM (20 Aktionen angewendet und
  zurueckgenommen), Rechte **10/0 lokal**, **12/0 VM**, Regression der gesperrten Bereiche
  unveraendert (Events 61/0, Marketing 37/0, Personal 54/0, Projekt 20/0, Verkauf Referenzniveau,
  Zeiterfassung 54/0, Abo 19/0, Helpdesk 35/0).
- Dokumentierte Abweichungen: Abrechnung 42/2 (`property_stock_*` entfallen), Kundenverwaltung 40/1
  (Skript erwartet `itk_crm` 18.0.1.5.7, installiert 18.0.1.5.10), Anwesenheiten mit den
  dokumentierten Odoo-11-Abweichungen (116 Home-Office-Zeilen, 1.221,72 Stunden).
- Testdaten vollstaendig entfernt (Test-Leads, Test-Stichwort, Testbenutzer samt Kontakt).
- Keine fachlichen Daten migriert; Odoo 11 ausschliesslich lesend benutzt.

## 3 Bereiche, die noch NICHT strukturell bearbeitet sind

Read-only gegen Odoo 11 erhoben, Details in Checkliste 6.20.

| Bereich | Odoo-11-Module | Bestand Odoo 11 | Odoo 18 |
|---|---|---|---|
| **Website / Webinhalte** | `website`, `website_form`, `website_links`, `website_rating` | 17 Seiten, 11 Menues | 4 Seiten, 8 Menues (Demodaten) |
| **Umfragen / Survey** | `survey`, `survey_crm` | 2 Umfragen, 2 Fragen, 73 Teilnahmen | nicht installiert |
| **Valorisierung** | `itk_valorisierung` | 10 Valorisierungshinweise, 33 Kostenstellen | Modul vorhanden, Daten offen |
| **Lager / Bestand** | `stock`, `stock_account`, `sale_stock` | 262 Lagerbelege (0 erledigt) | 0 Belege |

Ohne Handlungsbedarf: Einkauf (`purchase`, 0 Belege), Reklamationen (`bi_crm_claim`, 0 Datensaetze).

Nicht als eigener Bereich: Kalender (Abwesenheitsbloecke aus `hr_holidays`), Helpdesk-Daten
(1.254 `website_support`-Tickets, Bereich gesperrt, Datenmigration dokumentierte Abhaengigkeit).

## 4 Vorgehen pro Bereich (unveraendert)

1. Odoo-11-Livebestand read-only erheben, 2. Odoo-18-Bestand lokal und VM erheben,
3. Vergleichs-/Mappingdokument in `docs/`, 4. echte Entscheidungspunkte vorlegen,
5. Odoo 18 anpassen, 6. Trockenlauf, 7. lokal pruefen, 8. VM deployen,
9. Browserabnahme lokal und VM (echtes Bild, jede Aktion anwenden und zuruecknehmen),
10. Rechtepruefung mit Testbenutzer, 11. Regression der gesperrten Bereiche,
12. Testdaten entfernen und nachweisen, 13. Doku (Bereichsdokument, Checkliste,
PROJECT_KNOWLEDGE, README, diese Datei), 14. Commit/Push/PR/Merge, 15. VM auf `main`,
16. Dreistand nachweisen (Commit, Baum, Dateiliste).

Regeln: Odoo 11 niemals schreiben; keine Kontakte/Personen/E-Mail-Adressen anlegen, solange die
Kontaktmigration nicht freigegeben ist; Mehrdeutiges nicht raten, sondern Kandidaten mit
Vor-/Nachteilen vorlegen; Abnahme nur mit echtem Browserbild; Testbenutzer immer samt Kontakt
(`res.users` legt einen `res.partner` an) entfernen.

## 5 Start der naechsten Session

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
python scripts/apply_massenbearbeitung.py --instanz lokal --pruefen
```

## 6 Git-Stand

Der gueltige Stand ist immer `git log -1` (diese Datei kann ihren eigenen Commit nicht enthalten).
Session 140: Branch `itk/s140-massenbearbeitung`, Commits `f6b3a49` (Bestand und Vergleich) und
`cc58332` (Umsetzung), danach Doku-Commit und PR/Merge nach `main`.

## 7 Werkzeuge (weiterverwendbar)

| Datei | Zweck |
|---|---|
| `scripts/_o11o18_client.py` | RPC-Client `o11()` / `o18("lokal"\|"vm")`, read-only Zugriff |
| `scripts/upgrade_modules.py` | Modulinstallation/-update je Instanz (mit Label-Abgleich danach) |
| `scripts/analyse_o11_massenbearbeitung.py` | Odoo-11-Bestand der Massenbearbeitung (JSON) |
| `scripts/vergleich_massenbearbeitung.py` | Feld-/Aktionsvergleich Odoo 11 gegen Odoo 18 |
| `scripts/apply_massenbearbeitung.py` | K1/K4/T1 idempotent anwenden, `--pruefen` read-only |
| `scripts/browser_massenbearbeitung_abnahme.py` | Browserabnahme aller 20 Aktionen (anwenden + zuruecknehmen) |
| `scripts/rechte_massenbearbeitung.py` | Rechteprobe mit Testbenutzer, raeumt selbst auf |
| `scripts/bericht_massenbearbeitung.py` | Abnahmetabelle als Markdown erzeugen |
| `%LOCALAPPDATA%\Temp\vm_exec.py` | Shell auf der VM (Paramiko) |

## 8 Naechster Bereich (Vorschlag)

**Website / Webinhalte** - groesster offener Bereich mit kundennahen Inhalten (FAQ Gemeindecloud,
IFG-Portal, Anonymisierungs-Portal, Kurse); Odoo 18 hat nur Demoseiten. Alternativ Umfragen (klein,
73 Teilnahmen) oder Valorisierung (gehoert fachlich zur Abrechnung).
