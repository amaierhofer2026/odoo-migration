# Uebergabe Session 131 (08.10.2026) - Abrechnung abgeschlossen, Steuern geprueft

Diese Datei ist der Einstieg fuer die naechste Session. Sie fasst zusammen, was zu lesen ist,
wie gearbeitet wird und wo der Stand ist. Sprache und Form: **nur Deutsch**, einfache Zeichen
(keine Girlanden wie — · → ✓), lokal und VM getrennt mit konkreten Werten belegen.

## 1. Arbeitsregeln (verbindlich)

1. Odoo 11 (Produktion) **ausschliesslich read-only** pruefen. Keine Reparaturen, Commits,
   Pushes oder Datenmigration ohne ausdrueckliche Freigabe von Anna.
2. **Abrechnung ist seit 08.10.2026 MIGRATIONSBEREIT** (ausdrueckliche Freigabe Anna, nach
   Schliessung des letzten Blockers 3400). Aenderungen am Modul Abrechnung trotzdem nur bei
   konkretem Fehler von Anna.
3. Keine Produktivdaten migrieren. Testdaten nach dem Test vollstaendig entfernen und den
   Bestand vorher/nachher vergleichen. Stammdaten nie ungefragt anlegen.
4. Keine Felder nur optisch nachbilden: fachliche Felder, Relationen und Werte muessen
   tatsaechlich funktionieren. Keine Zuordnung ueber Datenbank-IDs, keine Ersatzdaten durch
   Namenssuche; bei Mehrdeutigkeit **Abbruch mit Klartext** statt stillem Ueberspringen.
5. Abnahme zaehlt erst nach Deploy + Upgrade + **echtem Browserbild** (Screenshot ansehen),
   nicht nach DOM-Sichtbarkeit oder Skriptausgabe.
6. Label-Regel: fachlich identisches Feld -> sichtbare Odoo-11-Bezeichnung uebernehmen,
   technische Odoo-18-Feldnamen bleiben unveraendert. Menues/Labels **nur ueber die technische
   Kennung** (`ir.model.data`) auswaehlen, niemals ueber Name oder `complete_name`.
7. Skill `odoo-migration-ops`: neues Wissen **nur** in `references/` ergaenzen.

## 2. Systeme und Zugang

| System | Angabe |
|---|---|
| Odoo 11 Produktion | portal.it-kommunal.at, DB `ITK_V1_a`, nur lesen |
| Odoo 18 lokal | http://localhost:8069, DB `odoo18_test`, Container `odoo18` |
| Odoo 18 Test-VM | k001959vsx.ipax.at (93.189.28.204), `/opt/odoo18`, docker compose |
| Repo | `C:\Odoo-Test`, GitHub `amaierhofer2026/odoo-migration`, Token in `.env` |
| VM-Shell | `vm_exec.py` / `vm_put.py` in `%LOCALAPPDATA%\Temp` (Paramiko, User k001959, PW `vm_pw.txt`); SSH nur mit VPN/Teleport, sonst Port 443 |
| PR ohne gh-CLI | `scripts/github_pr.py anlegen|status|mergen` |

Wichtig: Die VM hat in `/opt/odoo18/.env` **keine Odoo-Zugangsdaten** (nur `POSTGRES_PASSWORD`
und `PGDATA_VOLUME`). Alle Migrations- und Pruefskripte laufen **vom lokalen Client** gegen die
VM (`--instanz vm`), nicht auf der VM selbst.

## 3. Pflichtlektuere fuer die naechste Session

Reihenfolge:

1. **Memory** (wird automatisch geladen) und **USER-Profil** - enthalten die Arbeitsregeln.
2. **Skill `odoo-migration-ops`** mit den Referenzdateien, insbesondere
   `references/o11-o18-namenszuordnung-und-stammdaten.md`,
   `references/pruefskripte-fehlerfest-und-selbsttest.md`,
   `references/browser-und-pruefwerkzeuge.md`,
   `references/uebersetzungen-und-menuelabels.md` (neu: `.po` nur mit `--i18n-overwrite`,
   Menueauswahl ueber Kennung, kein `<delete>` auf fehlende Kennungen),
   `references/firmenvorgaben-kategoriekonten.md` (neu: ir.property gegen ir.default),
   `references/docker-compose-volume-falle.md`, `references/menue-matrix-und-sektions-dubletten.md`.
3. **`PROJECT_KNOWLEDGE.md`** (Abschnitte 7-9: Abschluss, Konten 8400/4000 und 3400/5010,
   Steuern) und **`MIGRATION_READINESS_CHECKLIST.md`**.
4. Bereichsdokumente (neueste zuerst):
   - `docs/o11-o18-steuern-mapping.md` (Steuern: Kennzahlen, Mapping, Sonderfall R-24832,
     Sonderzeichen-Korrektur)
   - `docs/o11-o18-abrechnung-kontenzuordnung-8400-3400.md` (Entscheidungen 8400 -> 4000,
     3400 -> 5010)
   - `docs/o11-o18-abrechnung-menue-matrix.md` (vollstaendige Menue-Matrix)
   - `docs/o11-o18-abrechnung-abschlussmatrix.md` (Abschnitte 8b, 13, 14)
   - `docs/o11-o18-abrechnung-labelmapping.md`, `docs/o11-o18-testmigration-regel.md`,
     `docs/o11-o18-produktkategorien-mapping.md`
   - `docs/o11-o18-vergleich-abrechnung-valorisierung.md`
5. Diese Datei als Kurzstand.

## 4. Stand 08.10.2026 (Ende Session 131)

- main = lokal = GitHub = VM = **a6a4b8a50821b784679e200b03694cff54111db3**,
  Baum **59a946e1c8c822e272d9b5ad6f6585d78c543bd7**,
  Dateidifferenz-Nachweis (sha1 ueber `git ls-tree -r HEAD`) **7ad59128b72543a8a56f1a312a027acb893c64d5**;
  Arbeitsbaeume lokal und VM sauber. Stand am 08.10.2026 erneut in allen vier Punkten
  nachgeprueft (lokal, GitHub via `origin/main`, VM via Git in `/opt/odoo18`).
- PRs dieser Session gemergt: #209 (Menue/Beschriftungen/Werkzeuge), #210 (Volume je Umgebung),
  #211 (VM-Abnahme), #212 (Konten 8400/4000 + Wortlaute), #213 (haengendes `<delete>` entfernt),
  #214 (Entscheidung 3400 -> 5010), #215 (Steuern-Pruefung), #216 (Sonderfall R-24832),
  #217 (Sonderzeichen in Steuerbeschreibungen), #218 (Uebergabedokumentation, dieser Stand).
- Module lokal und VM: `itk_projectcategory` **18.0.1.0.3**, `itk_crm` **18.0.1.5.8**,
  `account_invoice_line_report` **18.0.1.0.1**, `itk_valorisierung` **18.0.1.3.0**,
  `itk_account_migration` **18.0.1.22.0**, `itk_product` **18.0.1.0.5**.
- **Entschieden und umgesetzt:** 8400 "Erloese 19% USt" -> **4000** "Brutto-Umsatzerloese im
  Inland (20%)"; 3400 "Wareneingang 19% Vorsteuer" -> **5010** "Wareneinkauf 20%" (bestehende
  globale Odoo-18-Firmenvorgabe). Beides als **globale Firmenvorgabe** der Produktkategorien,
  **nicht** pro Kategorie; **kein neues Konto**, **kein Mapping auf 5000**.
  Umsetzung: Register `ENTSCHEIDUNGEN_KONTEN` + `pruefe_firmenvorgabe()` in
  `scripts/testmigration_abrechnung.py` (Pruefung ueber Nummer UND Namen).
- **Steuern:** Odoo 11 fuehrt 77 Steuern, produktiv verwendet werden **2** (20% Umsatzsteuer sale,
  20% Vorsteuer purchase); beide 1:1 zugeordnet ueber die Odoo-11-**Beschreibung**
  (20% USt -> 20% Ust, 20% VSt -> 20% Vst). 75 unbenutzte Altbestandssteuern (19%/7%, deutsche
  Schablonen) werden bewusst nicht migriert. Steuerkonten 1776/1576 (Odoo 11) gegen 3500/2500
  (Odoo 18) stimmig; Odoo 18 hat 53 Steuern, davon 5 archiviert (58 Datensaetze).
- **Sonderfall R-24832** (Zeilensteuer ohne gebuchte Steuer, einziger Fall unter 6.281 Belegen):
  Migration nach dem gebuchten Ist-Zustand ohne Steuer. Regel
  `ist_sonderfall_ohne_steuerbuchung()` greift nur bei (1) Zeilensteuer vorhanden,
  (2) `amount_tax = 0,00`, (3) keiner Steuerbuchungszeile. Nachweis
  `scripts/pruefe_sonderfall_r24832.py`: 6.281 Belege geprueft, genau 1 Treffer, 6.280 behalten
  ihre Steuer; migrierter Beleg in allen Betraegen und im Zahlungsstatus identisch.
- **Zusatzbefund (wichtig fuer alle Bereiche):** Odoo 18 wendet bei EU-/Drittlandspartnern von
  sich aus eine Steuerzuordnung an und bildet dabei Konten ab (Forderung 2000 -> 2100), wodurch
  die Zahlungsabstimmung scheiterte. Migrierte Belege erhalten deshalb ausdruecklich
  `fiscal_position_id = False`. Ebenso zieht die Produktvorlage ihre Standardsteuer nach, wenn
  die Zeilensteuermenge nicht ausdruecklich leer gesetzt wird.
- **Sonderzeichen in Steuerbeschreibungen:** statt "§" stand U+252C U+00BA ("T°") in 46 Feldern
  (48 Stellen); korrigiert mit `scripts/korrigiere_steuerbeschreibungen.py` in beiden Sprachen und
  allen drei Textfeldern (name, description, invoice_label), inklusive der archivierten Steuer
  id 6. Danach 0 offen. Die Feldnamen der Steuern sind Sonderfaelle: `description` und
  `invoice_label` liegen im Reiter "Erweiterte Optionen".
- Bezeichnungspruefung lokal und VM: 155 Feldpaare, 0 Abweichungen.
- Browser: Menue-Matrix-Prüfung lokal 4 OK / 0 FEHL und VM 4 OK / 0 FEHL; Steuerliste/Formulare
  lokal 10 OK / 0 FEHL und VM 10 OK / 0 FEHL; Steuerbeschreibungen lokal 5 OK / 0 FEHL und VM
  5 OK / 0 FEHL.
- Regression: **886 OK / 0 FEHL** ueber 11 Prueflaeufe, lokal und VM.
- Bestand lokal: 70 Partner, 13 Produktvorlagen, 3 Kategorien, 39 Belege, 105 Belegzeilen,
  10 Zahlungen, 53 Steuern, 240 Konten, 5 Kostenstellen, 26 Projektkategorien, 11
  Valorisierungstexte. VM: 70 / 10 / 3 / 59 / 166 / 11 / 53 / 240 / 5 / 26 / 11.
  Keine Testdaten, keine offenen Prozesse, VAL-OK unveraendert.

## 5. Werkzeuge, die wieder gebraucht werden

- RPC-Client: `scripts/_o11o18_client.py` (`o11()`, `o18("lokal"|"vm")`, `lade_env()`).
- Modul upgraden: `docker compose run --rm --no-deps -T odoo odoo -u <modul> -d odoo18_test
  --stop-after-init`, danach `docker compose restart odoo` (lokal und VM).
  **`.po`-Aenderungen greifen nur mit zusaetzlichem `--i18n-overwrite`**; Python-Feldbezeichnungen
  erst nach einem Container-Neustart.
- **Nach jedem Upgrade Pflicht:** `python scripts/apply_abrechnung_labels.py --instanz lokal|vm`
  (setzt Menue- und Feldbezeichnungen, idempotent, Auswahl ueber Kennungen).
- Bezeichnungen pruefen: `scripts/check_abrechnung_labels.py --instanz lokal|vm`
  (Mapping-Tabelle nur mit `--instanz lokal` schreiben lassen) und
  `scripts/check_abrechnung_viewlabels.py --instanz lokal|vm`.
- Regression: `python scripts/abschluss_verkauf_regression.py` (lokal und VM, 11 Prueflaeufe).
- Testmigration: `scripts/testmigration_abrechnung.py --plan | --ausfuehren --ich-habe-freigabe |
  --aufraeumen [--beleg <Odoo-11-Nummer>]` (gezielte Einzelmigration inkl. Mitziehen der Zahlung),
  Kontrolle `scripts/pruefe_testmigration.py --instanz lokal|vm`.
- Konten: `scripts/erhebe_konterverwendung_8400_3400.py` (+ `_teil2`, `_teil3`).
- Steuern: `scripts/erhebe_steuern_o11_o18.py`, `scripts/werte_steuern_aus.py`,
  `scripts/steuern_testbelege.py --anlegen|--entfernen`,
  `scripts/steuern_testbelege_entfernen.py` (Marker `ITK-STEUERTEST`),
  `scripts/pruefe_sonderfall_r24832.py`, `scripts/korrigiere_steuerbeschreibungen.py --pruefen`.
- Browser (Playwright/Chrome, headless): `scripts/browser_abrechnung_menue*.py`,
  `scripts/browser_abrechnung_wortlaut_konten.py lokal|vm`,
  `scripts/browser_steuern_abnahme.py lokal|vm`,
  `scripts/browser_steuern_beschreibungen.py lokal|vm`,
  `scripts/browser_valorisierung_abnahme.py`, `scripts/browser_abrechnung_vollstaendig.py`.
- Berichte/Screenshots dieser Session:
  `%USERPROFILE%\Desktop\Odoo18-Abnahme-Session131\` (`konten\`, `steuern\`, `browser\`).

## 6. Offene Punkte (nicht ohne Auftrag anfassen)

1. Migration der Odoo-11-Preislistenregeln, insbesondere der **403 Regeln ohne Produktbezug**.
2. Namenszuordnung und Anlage der **Abonnementvorlagen** vor der echten Migration.
3. Kategorien "amtsweg.gv.at Premium Standard" und "Whistleblowing" nur anlegen, wenn eine
   tatsaechlich migrierte Referenz sie braucht.
4. Rechnungsnotiz (`notice`) ist im Odoo-18-Rechnungsformular ausgeblendet, Odoo 11 zeigt sie
   (eine Zeile in `addons/itk_account_migration/views/account_move_form_kopf.xml`).
5. Zugriffsrechte: Odoo 11 trennt "ITK / User (read only)" und "ITK / Manager (edit)", Odoo 18
   gibt internen Benutzern volle Rechte auf die Valorisierungstexte.
6. Beschreibungen der 10 Valorisierungstexte sind in Odoo 18 leer; bei der echten Datenmigration
   sind `name`, `description`, `seq` zu uebertragen (Schluessel: bereinigter Name).
7. Testwert `VAL-OK` in der Odoo-18-Testinstanz: Test-/Altbestand, referenziert nur von einem
   Testentwurf ("Test Firma"). **Nicht loeschen, nicht aendern**.
8. Steuerzuordnungen (Fiscal Positions) werden **nicht** uebertragen. Betroffen sind **4**
   Odoo-11-Belege; 3 davon migrieren identisch, R-24832 ist ueber die Sonderregel abgedeckt.
   Vor der echten Migration entscheiden, ob Zuordnungen uebertragen werden sollen.
9. Sonderzeichen im Kontenrahmen koennen bei einer Neuinstallation erneut auftreten
   (`l10n_at`-CSV wird falsch dekodiert) - dann `korrigiere_steuerbeschreibungen.py` erneut
   ausfuehren.

## 7. Bewusste Abweichungen (dokumentiert, bleiben)

- Odoo-18-Zusatzfunktionen in Menues, Ansichten und Steuern bleiben erhalten, solange sie die
  Odoo-11-Funktion nicht veraendern.
- Steuergruppe "20%" statt Odoo 11 "USt 20%" und Sequenz 50 statt 10 (Anzeige/Reihenfolge, keine
  fachliche Wirkung).
- Menue "Projektkategorien" (Mehrzahl); Odoo 11 kennt kein Menue, dort heisst die Sache
  "Projektkategorie" (Einzahl).
- `amount_tax = 0,00` in Odoo 18 zeigt "Gutgeschrieben" statt Odoo 11 "Bezahlt" bei voll
  gutgeschriebenen Belegen (Rest 0).
- "&gt;=" statt ">" in zwei Steuerbeschreibungen: das Feld ist ein HTML-Feld mit Sanitizer, dort
  ist die Entitaet der korrekte Speicherzustand.

## 8. Vorgehensmuster fuer den naechsten Bereich

1. Odoo 11 read-only messen (Modell, Felder, Typen, Pflichtfelder, readonly, Defaults, Ansichten,
   Spaltenreihenfolge, Suche, Filter, Gruppierungen, Sortierung, Buttons, Verwendung, Bestand).
2. Mit Odoo 18 lokal und VM vergleichen, Unterschiede mit konkreten Werten belegen.
3. Abweichungen dokumentieren; beheben nur, was eindeutig gegen Odoo 11 steht.
4. Lokal upgraden und im Browser pruefen, dann VM per Git nachziehen und dort upgraden.
5. Browser-Abnahme lokal und VM, Regression, Bestand vorher/nachher.
6. Commit, Branch pushen, PR stellen, selbst mergen, VM per Git nachziehen, Dreistand belegen.
7. Abschlussbericht kurz: Abschlussmatrix, Blocker, bewusste Abweichungen, offene fachliche
   Entscheidungen, technischer Stand.

## 9. Startpunkt fuer die naechste Session

Abrechnung ist migrationsbereit und abgeschlossen (Steuern eingeschlossen). Fuer den naechsten
Bereich ist noch nichts vorbereitet - Anna gibt den Bereich und den Auftrag vor. Wahrscheinliche
Kandidaten aus den offenen Punkten: **Preislisten/Regeln**, **Abonnements (Abo-Vorlagen)**,
**Produkte**, **CRM/Partner** oder **Helpdesk**. Angebotenes Vorgehen: zuerst read-only-Erhebung
des Bereichs in Odoo 11 gegen Odoo 18 (lokal und VM), dann Abweichungsliste als Entscheidungs-
grundlage, bevor irgendetwas geaendert wird.
