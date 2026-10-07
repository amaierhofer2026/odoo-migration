# Uebergabe Session 130 (07.10.2026) - Abrechnung, Konfiguration, Valorisierung

Diese Datei ist der Einstieg fuer die naechste Session. Sie fasst zusammen, was zu lesen ist,
wie gearbeitet wird und wo der Stand ist. Sprache und Form: **nur Deutsch**, einfache Zeichen
(keine Girlanden wie — · → ✓), lokal und VM getrennt mit konkreten Werten belegen.

## 1. Arbeitsregeln (verbindlich)

1. Odoo 11 (Produktion) **ausschliesslich read-only** pruefen. Keine Reparaturen, Commits,
   Pushes oder Datenmigration ohne ausdrueckliche Freigabe von Anna.
2. **Keine Aenderung am Modul Abrechnung ohne konkreten Fehler von Anna.** Abrechnung bleibt
   **IN ARBEIT** - nie als abgeschlossen, eingefroren oder migrationsbereit markieren.
3. Keine Produktivdaten migrieren. Testdaten nach dem Test vollstaendig entfernen und den
   Bestand vorher/nachher vergleichen. Stammdaten nie ungefragt anlegen.
4. Keine Felder nur optisch nachbilden: fachliche Felder, Relationen und Werte muessen
   tatsaechlich funktionieren. Keine Zuordnung ueber Datenbank-IDs, keine Ersatzdaten durch
   Namenssuche; bei Mehrdeutigkeit **abbruch mit Klartext** statt stillem Ueberspringen.
5. Abnahme zaehlt erst nach Deploy + Upgrade + **echtem Browserbild** (Screenshot ansehen),
   nicht nach DOM-Sichtbarkeit oder Skriptausgabe.
6. Label-Regel: fachlich identisches Feld -> sichtbare Odoo-11-Bezeichnung uebernehmen,
   technische Odoo-18-Feldnamen bleiben unveraendert.
7. Skill `odoo-migration-ops`: neues Wissen **nur** in `references/` ergaenzen.

## 2. Systeme und Zugang

| System | Angabe |
|---|---|
| Odoo 11 Produktion | portal.it-kommunal.at, DB `ITK_V1_a`, nur lesen |
| Odoo 18 lokal | http://localhost:8069, DB `odoo18_test`, Container `odoo18` |
| Odoo 18 Test-VM | http://k001959vsx.ipax.at (93.189.28.204), `/opt/odoo18`, docker compose |
| Repo | `C:\Odoo-Test`, GitHub `amaierhofer2026/odoo-migration`, Token in `.env` |
| VM-Shell | `vm_exec.py` / `vm_put.py` in `%LOCALAPPDATA%\Temp` (Paramiko, User k001959, PW `vm_pw.txt`); SSH nur mit VPN/Teleport, sonst Port 443 |
| PR ohne gh-CLI | `scripts/github_pr.py anlegen|status|mergen` |

## 3. Pflichtlektuere fuer die naechste Session

Reihenfolge:

1. **Memory** (wird automatisch geladen) und **USER-Profil** - enthalten die Arbeitsregeln.
2. **Skill `odoo-migration-ops`** mit den Referenzdateien, insbesondere
   `references/o11-o18-namenszuordnung-und-stammdaten.md`,
   `references/pruefskripte-fehlerfest-und-selbsttest.md`,
   `references/browser-und-pruefwerkzeuge.md`.
3. **`PROJECT_KNOWLEDGE.md`** (Hauptwissen, Abschnitte Abrechnung/Verkauf) und
   **`MIGRATION_READINESS_CHECKLIST.md`**.
4. Bereichsdokumente (neueste zuerst):
   - `docs/o11-o18-vergleich-abrechnung-valorisierung.md` (Session 130, Modell, Ansichten,
     Bezeichnungen, VAL-OK, offene Punkte)
   - `docs/o11-o18-abrechnung-abschlussmatrix.md` (Abschnitt 13, Gesamtdurchgang)
   - `docs/o11-o18-abrechnung-labelmapping.md` (sichtbare Bezeichnungen, Feldpaare)
   - `docs/o11-o18-testmigration-regel.md` (Testmigrationsregel, Produktfelder, Kategorien)
   - `docs/o11-o18-produktkategorien-mapping.md` (Kategorien, Kontenzuordnung = BLOCKER)
   - `docs/o11-o18-abrechnung-ausgangsrechnungen-visuell.md` (Rechnungsformular, Kopfbereich)
   - `docs/o11-o18-abrechnung-einkaufbare-produktliste.md`
5. Diese Datei als Kurzstand.

## 4. Stand 07.10.2026 (Ende Session 130)

- main = lokal = GitHub = VM = **3437002dbc2ec6225e2e6aa2512d44090167477c**,
  Baum **8e6b93e6937041c657b89c4b7abce696f880edc0**; Arbeitsbaeume lokal und VM sauber.
- PR #204 (Bezeichnungen, Feld im Rechnungsformular), #205 (Wortlaut am Beleg),
  #206 (Label-Lauf, VM-Bezeichnungsbefund), #207 (Bedienprobe) gemergt.
- Module lokal und VM: `itk_valorisierung` **18.0.1.3.0**, `itk_account_migration`
  **18.0.1.22.0**, `itk_product` 18.0.1.0.5.
- Valorisierung: Liste und Formular Code | Beschreibung | Nummernfolge; am Beleg
  "Valorisation Text" (Odoo-11-Wortlaut).
- Bezeichnungspruefung lokal und VM: 155 Feldpaare, 0 Abweichungen.
- Regression: 886 OK / 0 FEHL ueber 11 Prueflaeufe, lokal und VM.
- Browser lokal und VM: Abnahme je 4 OK / 0 FEHL, Bedienprobe je 5 OK / 0 FEHL.
- Keine Testdaten, keine offenen Prozesse, VAL-OK unveraendert.

## 5. Werkzeuge, die wieder gebraucht werden

- RPC-Client: `scripts/_o11o18_client.py` (`o11()`, `o18("lokal"|"vm")`, `lade_env()`).
- Modul upgraden:
  `docker compose run --rm -T odoo odoo -u <modul> -d odoo18_test --stop-after-init`,
  danach `docker compose restart odoo` (VM) bzw. `docker restart odoo18` (lokal).
- **Nach jedem Modul-Upgrade Pflicht:** `python scripts/apply_abrechnung_labels.py --instanz lokal`
  und `--instanz vm` - sonst stehen englische oder abweichende Feldbezeichnungen im Formular.
- Aenderungen an `.po`-Dateien greifen schon beim Modul-Upgrade; Aenderungen an
  **Python-Feldbezeichnungen erst nach einem Container-Neustart** (danach Upgrade).
- Bezeichnungen pruefen: `python scripts/check_abrechnung_labels.py --instanz lokal|vm`
  (die Mapping-Tabelle nur mit `--instanz lokal` schreiben lassen, sonst wird die Doku geleert).
  Ansichtsbezeichnungen: `python scripts/check_abrechnung_viewlabels.py --instanz lokal|vm`.
- Regression: `python scripts/abschluss_verkauf_regression.py` (lokal und VM, 11 Prueflaeufe).
- Browser (Playwright/Chrome, headless, echte Instanz):
  `scripts/browser_valorisierung_abnahme.py lokal|vm`,
  `scripts/browser_valorisierung_bedienprobe.py lokal|vm`,
  `scripts/browser_abrechnung_vollstaendig.py lokal|vm 25`,
  `scripts/browser_kategorie_pruefung.py`, `scripts/browser_zeilen_beschreibung.py`.
- Testmigration: `scripts/testmigration_abrechnung.py --plan|--ausfuehren --ich-habe-freigabe|--aufraeumen`,
  Kontrolle `scripts/pruefe_testmigration.py --instanz lokal|vm`.
- Berichte/Screenshots dieser Session:
  `%USERPROFILE%\Desktop\Odoo18-Abnahme-Session129\valorisierung\` (Vergleich, Labels,
  Regression, Browserbilder, Bedienprobe).

## 6. Offene Punkte (nicht ohne Auftrag anfassen)

1. **BLOCKER vor Produktivmigration:** Kontenzuordnung 8400 "Erloese 19 % USt" / 3400
   "Wareneingang 19 % Vorsteuer". In Odoo 11 sind das globale Firmenvorgaben der
   Produktkategorien; im Odoo-18-Testkontenrahmen gibt es kein eindeutiges Gegenstueck.
   Nichts anlegen, nichts raten.
2. Migration der Odoo-11-Preislistenregeln, insbesondere der 403 Regeln ohne Produktbezug.
3. Namenszuordnung und Anlage der Abonnementvorlagen vor der echten Migration.
4. Kategorien "amtsweg.gv.at Premium Standard" und "Whistleblowing" nur anlegen, wenn eine
   tatsaechlich migrierte Referenz sie braucht.
5. Rechnungsnotiz (`notice`) ist im Odoo-18-Rechnungsformular ausgeblendet, Odoo 11 zeigt sie.
   Feld des Moduls itk_subscription; Aenderung nur auf Zuruf (eine Zeile in
   `addons/itk_account_migration/views/account_move_form_kopf.xml`).
6. Zugriffsrechte: Odoo 11 trennt "ITK / User (read only)" und "ITK / Manager (edit)",
   Odoo 18 gibt internen Benutzern volle Rechte auf die Valorisierungstexte.
7. Beschreibungen der 10 Valorisierungstexte sind in Odoo 18 leer; bei der echten
   Datenmigration sind `name`, `description`, `seq` zu uebertragen (Schluessel: bereinigter Name).
8. Testwert `VAL-OK` in der Odoo-18-Testinstanz: Test-/Altbestand, referenziert nur von einem
   Testentwurf ("Test Firma"). **Nicht loeschen, nicht aendern**, bis Anna es entscheidet.

## 7. Bewusste Abweichungen (dokumentiert, bleiben)

- Platzierung des Valorisierungstexts im Formular: Odoo 18 im Kopfbereichsblock, Odoo 11 im
  Bereich "Weitere Informationen". Feld sichtbar und bedienbar.
- Aktionsname deutsch "Valorisierungs Text" statt Odoo 11 "Valorisation Text"; im Browser nicht
  sichtbar (Brotkrumen zeigen den Menuenamen).
- Odoo-18-Zusatzfeld `account.bank.statement.line.valorisierung_id` (in Odoo 11 nicht vorhanden,
  0 Datensaetze).
- Odoo-18-Zusatzfunktionen in Menues und Ansichten bleiben erhalten, solange sie die
  Odoo-11-Funktion nicht veraendern.

## 8. Vorgehensmuster fuer den naechsten Bereich

1. Odoo 11 read-only messen (Modell, Felder, Typen, Pflichtfelder, readonly, Defaults, Ansichten,
   Spaltenreihenfolge, Suche, Filter, Gruppierungen, Sortierung, Buttons, Verwendung, Datenbestand).
2. Mit Odoo 18 lokal und VM vergleichen, Unterschiede mit konkreten Werten belegen.
3. Abweichungen dokumentieren; beheben nur, was eindeutig gegen Odoo 11 steht.
4. Lokal upgraden und im Browser pruefen, dann VM per Git nachziehen und dort upgraden.
5. Browser-Abnahme lokal und VM, Regression, Bestand vorher/nachher.
6. Commit, Branch pushen, PR stellen, selbst mergen, VM per Git nachziehen, Dreistand belegen.
7. Abschlussbericht kurz: Abschlussmatrix, BLOCKER, bewusste Abweichungen, offene fachliche
   Entscheidungen, technisch vollstaendig. Abrechnung weiter IN ARBEIT lassen.
