# Übergabe Session 122 (Stand 02.10.2026, 14:20 Uhr)

## 1. Umgebung und Zugänge

- Repo: `C:\Odoo-Test`, GitHub `amaierhofer2026/odoo-migration`, Arbeitsstand `main = 37ac72e`
  (lokal = GitHub = VM).
- Odoo 11 Produktion: **nur lesend** über `portal.it-kommunal.at`, DB `ITK_V1_a`.
  Client: `scripts/_o11o18_client.py` (`o11()`, `o18("lokal"|"vm")`).
- Odoo 18 lokal: `http://localhost:8069` (Docker-Container `odoo18` + `odoo18-db`).
- Odoo 18 VM: `https://k001959vsx.ipax.at` (DB `odoo18_test`, Container `odoo18`).
  Browser-Abnahme **nur auf der VM** gültig.
- VM-Shell: `%TEMP%\vm_exec.py` (Paramiko, 93.189.28.204, Benutzer k001959, Passwort `vm_pw.txt`),
  Aufruf: `python vm_exec.py "<Befehl>"`.
- Zugangsdaten Odoo 18: `.env` (`ODOO18_DB`, `ODOO18_USER`, `ODOO18_PWD`), lokal und VM
  dieselben Werte.

## 2. Arbeitsregeln (verbindlich, Anna)

1. Odoo 11 ausschließlich lesen, niemals ändern/anlegen/upgraden.
2. Keine Datenmigration; keine Testdaten bleiben zurück.
3. Sichtbare Bezeichnung = Odoo-11-Wortlaut, wenn das Feld fachlich identisch ist (auch
   ITK-Englisch wie "Multiplication Factor/Thsd"). Technische Feldnamen bleiben Odoo 18.
4. Odoo-18-Zusatzfunktionen und -felder bleiben erhalten, nichts entfernen.
5. Abnahme nur im echten Browser auf der VM (Screenshot selbst ansehen); DOM-Sichtbarkeit,
   `fields_get` oder XML-Arch genügen **nicht**.
6. Odoo-18-Standardaufbau ist keine Begründung für sichtbare Abweichungen.
7. Berichte auf Deutsch, einfache Zeichen, konkrete Werte, lokal und VM getrennt.
8. Git: Arbeitsbranch pushen + PR (`scripts/github_pr.py`, `gh` fehlt), kein Force-Push,
   kein Auto-Merge; vor dem Push Zusammenfassung zeigen.
9. Upgrade-Reihenfolge: VM `docker compose run --rm -T odoo odoo -u <module> -d odoo18_test
   --stop-after-init --no-http`, dann `docker compose restart odoo`, dann
   `python scripts/apply_abrechnung_labels.py --instanz vm`.
   Bei geänderten .po-Dateien zusätzlich `--i18n-overwrite` (siehe unten).

## 3. Wichtiges Betriebswissen (neu in dieser Session)

- Odoo überschreibt vorhandene Übersetzungen bei einem Modul-Upgrade **nicht**.
  Nach jeder .po-Änderung ist `--i18n-overwrite` nötig, sonst zeigt die Oberfläche den alten
  Text (Fehlerquelle bei Knopftexten und Feldern).
- `docker exec odoo18 odoo -u ...` scheitert auf der VM still; nur `docker compose run ...`
  wirkt.
- Lokales Upgrade: `docker exec odoo18 odoo -u <module> --i18n-overwrite -d odoo18_test
  --db_host=db --db_user=odoo --db_password=<POSTGRES_PASSWORD> --stop-after-init --no-http`.
- Details: `odoo-migration-ops/references/odoo18-uebersetzungen-und-beschriftungen.md`.

## 4. Stand der Bereiche

| Bereich | Stand |
|---|---|
| Verkauf | abgeschlossen (Regeln R1-R8), Regression 886 OK / 0 FEHL |
| Abrechnung | **IN ARBEIT** (siehe unten) |
| Abonnements | abgeglichen, PR #184/#185, Browser lokal + VM |
| Kontakte/Partner | abgeschlossen (frühere Session) |

Abgenommen und auf der VM im Browser bestätigt:
- Belege (Kopfbereich, Zeilen-Spalten, Summenblock "Nettobetrag / Steuern / Total" +
  "Fälliger Betrag"), Kunden-Gutschriften, Eingangsrechnungen, Lieferanten-Gutschriften
- Zahlungsformular inkl. Statuskette `itk_o11_status`
  (Entwurf -> Gebucht -> Abgestimmt -> Abgebrochen) und Smart Button "Rechnungen"
- Kunden, Lieferanten, Such-/Filter-/Gruppierungsansichten, Konfigurationsformulare
- Produkte: 68 Feldbeschriftungen angeglichen (PR #187)

Migrations-Readiness Abrechnung:
- Feldabdeckung: **273 belegte Felder, 0 offene Mappings** (frischer Lauf 02.10.2026 14:09-14:17)
- Beziehungen, Constraints, berechnete Felder, Migrationsreihenfolge dokumentiert in
  `docs/o11-o18-abrechnung-abschlusspruefung.md` (Abschnitte 1-12)
- Beschriftungsprüfung: **155 Feldpaare, 0 Abweichungen** lokal und VM
  (`scripts/check_abrechnung_labels.py`, Tabelle `docs/o11-o18-abrechnung-labelmapping.md`)

## 5. Offene Punkte (Entscheidung/Arbeit in der neuen Session)

1. **ITK-Produktfilter** - Analyse liegt vor (`docs/o11-o18-abrechnung-itk-produktfilter.md`):
   Funktion (product_type_id, invoice_policy, service_type), Nutzung (Onlineservice 314,
   Plattform 56, Consulting 19, Software-Lösung 18, Hardware 3, Förderprojekt 0, Festpreis 33,
   Bestandsauflösung 449), betroffene Datensätze, Verhalten in Odoo 18, Folgen bei
   Beibehaltung / Anpassung / Weglassen. **Anna entscheidet; noch nichts geändert.**
2. **Testdaten auf der VM**: 3 Abo-Testprodukte ("Test-Abo monatlich", "TEST-Abo Monatlich",
   "TEST Abo Produkt Monatlich") plus die übrigen Testprodukte (13 gesamt).
   Löschen erst nach Zuruf.
3. **Restansichten**: Kanban-Ansichten und leere Listen im Abrechnungsumfeld noch nicht
   vollständig browsergeprüft.
4. **Testmigration** mit wenigen repräsentativen Datensätzen vorbereiten (Regel + Skript,
   noch nicht ausführen).
5. **Kleinigkeit**: Über dem Feld "Product-Type" steht zusätzlich die ITK-Gruppenüberschrift
   "PRODUKT-TYP" (doppelt) - entfernen?

## 6. Wichtige Dateien und IDs

- Module: `addons/itk_account_migration` (Views, `models/account_payment_o11_status.py`,
  `static/src/xml/itk_tax_totals.xml`), `addons/itk_subscription`, `addons/itk_multifactor`,
  `addons/itk_reports`, `addons/itk_valorisierung`.
- Skripte: `_o11o18_client.py`, `apply_abrechnung_labels.py`, `check_abrechnung_labels.py`,
  `pruefe_abschluss_feldabdeckung.py`, `pruefe_beziehungen_constraints.py`,
  `abschluss_verkauf_regression.py`, `github_pr.py`, `browser_abrechnung_vollstaendig.py`,
  `browser_abo_abnahme.py`, `browser_abo_menues.py`, `browser_produkt_labels.py`,
  `upgrade_modules.py`.
- Dokumente: `docs/o11-o18-abrechnung-abschlusspruefung.md`,
  `docs/o11-o18-abrechnung-itk-produktfilter.md`, `docs/o11-o18-abonnement-abgleich.md`,
  `docs/o11-o18-abrechnung-labelmapping.md`, `MIGRATION_READINESS_CHECKLIST.md`,
  `PROJECT_KNOWLEDGE.md`.
- Menü/Aktionen Odoo 18: Abrechnung-Wurzel `193`, Zahlungen `330`, Ausgangsrechnungen `354`,
  Verkaufbare Produkte `382`, Einkaufbare Produkte `383`, Abonnements `1105`.
- Screenshots: `Desktop\Odoo18-Abnahme-Session122\` (`abonnement`, `produkte`, `rechnung`, `belege`).

## 7. Erste Schritte in der neuen Session

1. Stand prüfen: `git -C C:/Odoo-Test log --pretty=%h -1` (erwartet `37ac72e`),
   VM: `python "$TEMP/vm_exec.py" "cd /opt/odoo18 && git log -1 --format=%h"`.
2. Prüfläufe (jeweils ca. 5-8 Minuten):
   `python scripts/pruefe_abschluss_feldabdeckung.py` (273 / 0),
   `python scripts/check_abrechnung_labels.py --nur-abweichungen` (155 / 0),
   `python scripts/abschluss_verkauf_regression.py` (886 OK / 0 FEHL).
3. Dann Annas Entscheidung zum Produktfilter einholen und die offenen Punkte 2-5 abarbeiten.
