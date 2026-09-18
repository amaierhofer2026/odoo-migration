# Odoo Migration – ITK

Migration aller Odoo-Module von **Version 11 nach Version 18** für ITK (IT Kommunal).
1:1-Spiegel des Entwicklungsverzeichnisses `C:\Odoo-Test\`.

## Ziel

- **Alle ~56 Odoo-11-Module** vollständig nach Odoo 18 migrieren
- Jedes Feature, jedes Feld, jede View muss exakt wie in Odoo 11 funktionieren
- Saubere Git-Historie, jeder Schritt nachvollziehbar
- Odoo 18 läuft in Docker (Windows, erreichbar unter `localhost:8069`)

## Verbindliche Migrationsregel: Organisation = Unternehmen, Ansprechpartner = Person

**Ab 15.09.2026 (Session 99), gilt für die spätere Datenmigration und alle Testdaten in Odoo 18:**

- **Gemeinden, Verbände, Firmen und sonstige Organisationen** werden als **Unternehmen** angelegt (`is_company = True`).
- **Natürliche Ansprechpartner** werden als **Person** angelegt (`is_company = False`).
- **Die Zuordnung darf nicht pauschal erfolgen** — jede Zuordnung prüfen, unklare Fälle einzeln entscheiden.

Anlass: Kontakt 79 war als Person angelegt; dadurch fehlten GKZ, Multiplication Factor/Thsd, Organisationsbezeichnung,
Status und der Tab Gemeinde-Information (die Kenndaten hängen an `is_company`). Detail:
`docs/migrationsregel-organisation-vs-person.md`.

---

## Verbindliche Arbeitsregel: VM = Abnahmeumgebung

**Ab 15.09.2026 (Session 97) gilt für das gesamte Migrationsprojekt:**

- **Lokal** (`C:\Odoo-Test`, `localhost:8069`) ist die **Entwicklungsumgebung**: entwickeln, analysieren, vorab testen.
- **Die VM** (`https://k001959vsx.ipax.at`, `/opt/odoo18`, DB `odoo18_test`) ist die **maßgebliche Test- und Abnahmeumgebung**.
- Ein Punkt ist erst **wirklich umgesetzt**, wenn die Änderung auf der VM deployed, in der VM-Datenbank geladen/aktiviert,
  direkt gegen die VM geprüft und dort **im echten Browser** sichtbar bzw. funktional bestätigt ist.
- Ein Git-Pull auf der VM genügt **nicht**: Moduländerungen brauchen ein gezieltes Upgrade in `odoo18_test`.
- Bei UI-/View-Änderungen wird die **tatsächlich aktive View** und die **sichtbare Darstellung** auf der VM kontrolliert
  (XML/DOM/RPC allein zählt nicht).
- Nach Dokumentation, Commit, Push, PR und Merge wird die VM auf den finalen `main`-Stand gebracht und dort abschließend verifiziert.

Prüfwerkzeug: `python scripts/vm_abnahme_check.py` · Detailregel: `docs/arbeitsregel-vm-abnahme.md`.

---

## Migrations-Status

| Modul | Status | Version |
|---|---|---|
| `itk_subscription` (ITK Abo-Management) | ✅ Fertig getestet · 3 Abo-Vorlagen (J/M/Q) · Odoo-18-Fixes: Formular (Chatter/Archiv) + Portal-JS (publicWidget) + Abo-Anlage: EUR-Standardpreisliste automatisch (Fix Session 82, **auf der Test-VM deployt + Praxistest grün, Session 84, 11.09.2026**) | 18.0.1.1.0 |
| `account_invoice_line_number` | ✅ In Odoo 18 integriert · Live-Renummerierung im Formular gefixt (⟳ Docker-Neustart) | 18.0.1.0.0 |
| `itk_product` | ✅ Migriert, installiert | 18.0.1.0.0 |
| `itk_projectcategory` | ✅ Migriert, installiert | 18.0.1.0.0 |
| `itk_sale_management` | ✅ Migriert, installiert (Layout-Fix: Angebotsdatum) | 18.0.1.0.0 |
| `itk_valorisierung` | ✅ Migriert, installiert | 18.0.1.0.0 |
| `sale_order_line_number` | ✅ Fertig getestet · Live-Renummerierung im Formular gefixt (⟳ Docker-Neustart) | 18.0.1.0.0 |
| `itk_saleorder_lines` | ✅ Migriert, installiert | 18.0.1.0.0 |
| `itk_multifactor` | ✅ Fertig getestet (act_window + Wizard-ACL gefixt) | 18.0.1.0.0 |
| `itk_crm` | ✅ Migriert, installiert · Lost Reasons (O11-kompatibel), Automated Action, Aktivitäten-Kanban, „Neue Aktivität“ via nativem Odoo-18-Wizard (B1), Aktivitätstyp-Entscheidung: Typ 2 „Anrufen“ kanonisch (Odoo-Standard), O11-Nachbau „Anrufen“ (Typ 21) entfernt | 18.0.1.5.0 |
| `account_invoice_line_report` | ✅ Migriert, installiert | 18.0.1.0.0 |
| `partner_firstname` | ✅ Migriert, installiert | 18.0.1.0.0 |
| `hr_employee_firstname` | ✅ Migriert, installiert | 18.0.1.0.0 |
| `partner_academic_title` | ✅ Migriert, installiert | 18.0.1.0.0 |
| `itk_base_setup` | ✅ Migriert, installiert | 18.0.1.0.0 |
| `itk_third_party_setup` | ✅ Migriert, installiert | 18.0.1.0.0 |
| `itk_reports` | ✅ Migriert, installiert · 4 ITK-Druckvorlagen (Angebot/Auftrag, Bestellung, Bestellanfrage, Rechnung) alle gerendert | 18.0.1.0.0 |
| `purchase_order_line_number` | ✅ Positionsnummer (1,2,3…) in Bestellungen · Live-Renummerierung im Formular gefixt (⟳ Docker-Neustart) · fehlerhafte de.po korrigiert | 18.0.1.0.0 |
| `merge_sale_order` | ✅ Fertig getestet · Assistent „Aufträge zusammenführen" (4 Strategien, im Aktionsmenü) · fehlende ACL ergänzt · Merge-Bug gefixt · Merge zusätzlich für „Angebot gesendet" (sent) freigegeben (bestätigte Aufträge bleiben bewusst blockiert) | 18.0.1.0.0 |
| `merge_purchase_order` | ✅ Fertig getestet · Assistent „Bestellungen zusammenführen" (4 Strategien, im Aktionsmenü) · ACL ergänzt · Merge-Bug gefixt · Merge für RFQ + RFQ Sent (bestätigte Bestellungen blockiert) | 18.0.1.0.0 |
| `web_no_bubble` | ✅ Migriert, installiert · Blendet animierte Tooltip-Bubbles aus (reines CSS) | 18.0.1.0.0 |
| `web_sheet_full_width` | ✅ Migriert, installiert · Nutzt die volle Bildschirmbreite für Formularansichten (reines CSS) | 18.0.1.0.0 |
| `web_environment_ribbon` | ✅ Migriert, installiert · Farbiges Ribbon-Banner für Test/Dev/Staging (CSS + JS) | 18.0.1.0.0 |
| `sale_merge_draft_invoice` | ✅ Migriert, installiert · Sammelrechnungs-Assistent (Draft Invoices mergen) | 18.0.1.0.0 |
| `web_group_expand` | ⚠️ Geparkt · JS inkompatibel mit Odoo 18 OWL (wie web_tree_resize_column) | 18.0.1.0.0 |
| `website_odoo_debranding` | ✅ Migriert, installiert · Entfernt Odoo-Promotion aus Website-Footer (Template) | 18.0.1.0.0 |
| `partner_external_map` | ✅ Migriert, installiert · Map/Route-Map-Buttons im Partner-Formular (Google Maps, OSM etc.) | 18.0.1.0.0 |
| `mass_email_invoice` | ✅ Migriert, installiert · Massen-Email-Versand für Rechnungen (mail.compose.message) | 18.0.1.0.0 |
| `itk_automated_actions` | ✅ Migriert, installiert · Automatisierte E-Mail bei Urlaubsanträgen (base.automation) | 18.0.1.0.0 |
| `website_cookie_notice` | ✅ Migriert, installiert · Cookie-Zustimmungsbanner auf der Website (Template + JS) | 18.0.1.0.0 |
| `hr_holidays_public` | ✅ Migriert, installiert · Public-Holiday-Management + Urlaubsberechnung (Models + Wizard) | 18.0.1.0.0 |
| `mass_editing` | ✅ Ersetzt durch `server_action_mass_edit` (OCA) + 20 Aktionen aus Odoo 11 | 18.0.1.1.3 |
| `server_action_mass_edit` | ✅ Installiert · 20 Massenbearbeitungen aus Odoo 11 migriert | 18.0.1.1.3 |
| `itk_translation` | ✅ Migriert, installiert · ITK-Partner-Views (GKZ/Status/Community) + ITK-Menü (Kunden/Reseller/Magnitudes) | 18.0.1.0.0 |

|| `itk_contract` | ❌ Gestrichen · historisches Modul (0 Datensätze, OCA contract nie installiert, Felder in itk_subscription enthalten) | — |
|| `web_tree_resize_column` | ⚠️ Geparkt · JS inkompatibel mit Odoo 18 OWL | 18.0.1.0.0 |
|| `website_support` | ❌ Ersetzt durch OCA `helpdesk_mgmt` · Ticketmigration entfällt (leerer Helpdesk) | — |
|| `website_support_analytic_timesheets` | ❌ Ersetzt durch OCA `helpdesk_mgmt_timesheet` | — |
|| `website_support_billing` | ❌ Ersetzt durch Odoo-18-Standard-Projektabrechnung | — |
|| `itk_support` | ❌ Entfällt · leeres Modul, Menüs in `itk_translation` | — |
|| `hr_holiday_exclude_special_days` | ⚠️ Geparkt · `hr_holidays_public` deckt Public-Holiday-Management bereits ab | — |
|| `itk_update_population` | ⚠️ Geparkt · Historische Einmal-Aktualisierung (2018), Datenimport-Modul | — |
|| `mail_activity_board` | ❌ Entfällt · Kein OCA-18.0-Branch, Activity-System in Odoo 18 nativ integriert | — |
|| `web_responsive` | ❌ Entfällt · Odoo 18 ist nativ responsive (Bootstrap 5 + OWL) | — |
|| `itk_fix_import` | ⚠️ Geparkt · Einmal-Fix ("DO NOT INSTALL AGAIN") | — |
|| `itk_main_company_import` | ⚠️ Geparkt · `installable: False`, Firmendaten manuell konfiguriert | — |
|| `helpdesk_mgmt` | ✅ Installiert (OCA 18.0) · Helpdesk-Ticketsystem (Ersatz für website_support) | 18.0.1.17.1 |
|| `helpdesk_mgmt_project` | ✅ Installiert (OCA 18.0) · Helpdesk-Projektverknüpfung | 18.0.1.3.0 |
|| `project_timesheet_time_control` | ✅ Installiert (OCA 18.0) · Zeiterfassungskontrolle | 18.0.1.0.7 |
|| `helpdesk_mgmt_timesheet` | ✅ Installiert (OCA 18.0) · Helpdesk-Zeiterfassung | 18.0.1.1.3 |
|| `helpdesk_mgmt_sla` | ✅ Installiert (OCA 18.0) · Helpdesk-SLA-Management | 18.0.2.1.0 |
| `itk_helpdesk_category_user` | ✅ Installiert (NEU) · Multi-User-Kategorie-Follower (many2many), keine Auto-Zuweisung | 18.0.1.0.0 |
| `itk_helpdesk_compat` | ✅ Installiert (NEU) · Odoo-11-Helpdesk-Oberfläche: 9 Menüpunkte, 2-stufige Kategorieauswahl, Prioritäten-Modell | 18.0.1.0.0 |

**Modul-Analyse abgeschlossen:** 57 Module analysiert → 37 migriert, 22 geparkt, 3 entfällt, 1 gestrichen. +2 ITK-Neumodule.

## Aktueller Stand & Ausblick (11.09.2026)

- **Odoo 18 läuft auf der IPAX-Test-VM**, Zugriff über **https://k001959vsx.ipax.at** (nginx + Let's Encrypt, Auto-Renew), Datenbank **odoo18_test** (am 31.08.2026 1:1 vom lokalen Teststand übertragen)
- **Lokale Odoo-18-Umgebung** (Windows Docker, http://localhost:8069) besteht separat weiter; PostgreSQL (Named Volume) und Filestore sind persistent
- **GitHub/main, lokale Umgebung und Test-VM stehen auf demselben Stand** — die VM wurde am 11.09.2026 per `git pull --ff-only origin main` nachgezogen (Session 84); den jeweils aktuellen Commit siehe GitHub-Historie bzw. `git log --oneline -1` in den drei Arbeitsbäumen
- **VM-Zugang:** ausschließlich über **VPN + Teleport** (`k001959vsv`, User `k001959`) — direkter Port 22 ist von außen VM-seitig gefiltert (Analyse 10.09.2026, Session 83). Gearbeitet wird dort über Git + gezielte Einzel-Upgrades (`docker compose stop odoo` → one-shot `-u <modul>` → `start`), nie `-u all`.
- **Abo-Anlage auf der VM repariert und getestet (Session 84, 11.09.2026):** `itk_subscription` von 18.0.1.0.0 auf **18.0.1.1.0** per gezieltem **Einzel-Upgrade** aktualisiert (`docker compose stop odoo` → one-shot `-u itk_subscription` → `start`). **Neue Abos können wieder gespeichert werden** — Anlegen/Speichern ohne den früheren Abbruch „Ein Pflichtfeld ist nicht gesetzt — Pricelist (pricelist_id)", Wiedereröffnung stabil, Währung durchgängig EUR. **Verwendete EUR-Preisliste: `product.pricelist` id 34 „Preisliste 2026 + Valorisierung" (EUR, aktiv seit 03.09.2026) — Festpreise 65,00 / 15,00**; die USD-Preisliste id 1 bleibt inaktiv. 5 Bestandsabos datenidentisch unverändert (Testabo angelegt, geprüft, wieder entfernt).
- **Umfang der VM-Arbeiten (bewusst eingehalten):** kein `-u all`, **kein** Upgrade anderer Module, **keine** DB-Migration, **keine** Systemänderung außer dem Odoo-Neustart. Offener Rest: Browser-Klicktest der Abo-Anlage durch Anna.
- **Keine produktiven Odoo-11-Daten migriert**; aktuell 158 installierte Module (15 itk_*-Module + verwendete OCA/Helpdesk-Module)
- **Abnahme-Phase gestartet:** Die fachliche/technische Abnahme von Odoo 18 vor der O11-Datenmigration wird über **`MIGRATION_READINESS_CHECKLIST.md`** geführt (Sprache, Umlaute/Encoding, Währung, Grundeinstellungen, Fachbereiche, Testreihenfolge; O11→O18-Mapping dort vorerst OFFEN). Stand: Abschnitt-1-Sprachkorrekturen F14–F26 (Session 81) und EUR-Preislisten-Aktivierung/Abo-Fix (Session 82, deployt Session 84) umgesetzt; offen u. a. USD-Thematik aus Testdaten (F2/F3/F4 — bewusst noch unangetastet), Doppelkonto F28, OCA-Modulnamen, Core-View-Encoding-Artefakte (F29, derzeit nicht sichtbar) — jede Korrektur nur mit Freigabe.
- **F33 Filestore-Luecke untersucht (Session 90, 14.09.2026):** 895 Anhangsdatensaetze verweisen auf **513 fehlende Dateien** (432 Odoo-Standardgrafiken + 81 Datendateien: 43 echte Fotos, 7 Beleg-PDFs, 4 Dashboards, 1 Logo, 1 CSS, 25 Platzhalter) - in **keiner** lokalen Sicherung vorhanden (Abdruck: `dump.sql` mit `db_datas` leer; Details in `PROJECT_KNOWLEDGE.md` Session 90). Vollstaendiges **Odoo-11-Backup lokal gefunden** (`Desktop\Odoo_DB_Dump_2026_09_03` + byte-identische Kopie in `Nextcloud`: `ITK_V1_a.pg_dump` 48 MB + `ITK_V1_a_filestore.tar.gz` 1,61 GB / 21.789 Dateien), deckt aber nur 18 der 513 per Hash ab. Ohne IPAX machbar: 432 Modulgrafiken + 18 Fotos + ~25 Fotos semantisch ueber die O11-DB; offen: 7 PDFs + 4 Dashboards. Read-only Werkzeug: `scripts/f33_filestore_scan.py`. Noch **nichts** kopiert oder repariert.

- - **Bereich Kontakte → Kontaktformular/Kontaktliste (Session 93, 15.09.2026 — Struktur umgesetzt):** Kontaktliste um die Odoo-11-Spalten erweitert, die in Odoo 18 fehlten (`function`, `is_company`, `parent_id`, `salutation`, `active` als `optional="show"`, `category_id` wieder sichtbar, doppelte Namensspalte ausgeblendet); Kontaktsuche um die Odoo-11-Filter **„Meine Partner“** und **„Meine Aktivitäten“** ergänzt. Modul `itk_base_setup` 18.0.1.0.1. **Formular:** keine Änderung nötig — die O11-Bestandteile sind in Odoo 18 vorhanden (Chatter, Bildfelder, Kundensperren, Warnungen, Konten gruppengesteuert). Verifiziert lokal **und** auf der VM: `scripts/verify_s93_contact_views.py` je **40/40 OK**. Offen als **KLÄRUNG NÖTIG**: `opt_out`/Versandbereitschaft, Website-Veröffentlichung am Kontakt, Wortlaute der Smart-Buttons, Tab „Rechnungsstellung“, O11-Buttons ohne O18-Modul (Reklamation, Events, Kostenstellenkonten). Keine Daten übernommen.
- **Kundenverwaltung / CRM vollstaendig abgeglichen (Session 115, 17.09.2026):**
  `docs/o11-o18-strukturvergleich-kundenverwaltung-crm.md`. Sichtbarer App-Name jetzt **"Kundenverwaltung"** (vorher "CRM"),
  Konfigurationsgruppe jetzt **"Interessenten und Chancen"** (vorher "Pipeline"); beide Namen werden bei jedem itk_crm-Upgrade
  erneut gesetzt (`itk_crm` **18.0.1.5.7**), weil `crm.crm_menu_root` Moduldaten mit `noupdate=0` ist.
  Wortlaute auf Odoo 11 umgestellt (Stufe, Verkaeufer, Vertriebskanal, Ablehnungsgrund, Lead Tags,
  Ablehnungsgruende), Gruppierung "Kunde" ergaenzt, Berichtswesen/Vertriebskanaele hergestellt,
  Loeschrecht crm.lead fuer die bestehende ITK-Gruppe "Manager (edit)" ergaenzt (keine Benutzerzuordnung). Menues, Ansichten, Suche/Filter,
  Konfiguration und Funktionen verglichen: keine funktionale Luecke; ITK-Felder liegen wie in Odoo 11 in der Liste der Interessenten
  und im Formular. Weiterhin **keine Datenmigration** (0 von 359 Verkaufschancen, 0 von 6.608 Interessenten).
  Pruefwerkzeug `scripts/verify_s115_kundenverwaltung.py` (lokal 20 OK). Odoo 11 Prod nur lesend genutzt.
- **Bereich CRM → Verkaufschancen vorbereitet (Session 114, 15.09.2026):**
  `docs/o11-o18-strukturvergleich-crm-verkaufschancen.md`. **Zahlen-Korrektur:** 6.967 `crm.lead` = 6.608 Interessenten +
  **359 Verkaufschancen** (der Wert „6.966“ aus Session 101 war die Gesamtzahl). **Stufe „Angebot ausgesendet“** war in Odoo 18
  tatsächlich nicht vorhanden und ist ergänzt; die 9 Stufen stehen jetzt in der Odoo-11-Reihenfolge. **7 tatsächlich verwendete
  Teams** als Stammdaten vorbereitet (5 neu, „Webseite“ → Odoo-18-„Website“ aktiviert; „Suche / Liste“ mit 0 Chancen nicht),
  Teamleiter gesetzt. **Verlustgründe:** alle 5 Odoo-11-Namen schon vorhanden, in Odoo 11 bei 0 Chancen genutzt — nichts anzulegen.
  Feld-Mapping (16 Felder) inkl. Umbenennungen `planned_revenue` → `expected_revenue`, `lost_reason` → `lost_reason_id`,
  `crm.lead.tag` → `crm.tag`, `description` text → html. **Keine Verkaufschance migriert.** Gepflegt im Repo (
  `itk_crm` 18.0.1.5.2: `data/crm_stages.xml`, `setup_runtime._setup_crm_teams`). Prüfung `scripts/verify_s114_crm_chancen.py`,
  lokal 52 OK / 0 FEHL. Offene Fachfragen in Abschnitt 6 des Dokuments.

- **Tab „Support Ticket“ MIGRATIONSBEREIT (Sessions 112/113, 15.09.2026, auf der VM verifiziert):**
  `docs/o11-o18-strukturvergleich-kontakt-support-ticket.md`. Odoo 11 nutzt `website_support`, Odoo 18 die OCA-Helpdesk-Funktion
  `helpdesk_mgmt` (+ SLA/Projekt/Timesheet) und ITKs `itk_helpdesk_compat`. Die beiden Odoo-11-Felder im Reiter (`sla_id`, `stp_ids`)
  entfallen (0 von 5.842 Kontakten genutzt), der Smart-Button ist funktional gleichwertig („Support Tickets“). Behoben: der Reiter
  zeigte nur einen Platzhaltertext und enthält jetzt die Odoo-18-Ticketliste des Kontakts (nur lesend, 7 Spalten) —
  `itk_base_setup` 18.0.1.2.3. Prüfung `scripts/verify_s112_support_ticket.py`, lokal 35 OK / 0 FEHL und **VM 35 OK / 0 FEHL**;
  Browser-Test mit `scripts/browser_reiter_pruef.py` (alle 7 Spalten sichtbar, Screenshot `21_VM_SupportTicket.png`).
  **Ticket-Migration verbindlich selektiv (Vorgabe Session 113):** keine automatische Übernahme aller 1.210 Tickets; vor der
  Migration Auswahlregel festlegen (Status, Alter/Erstell- bzw. Abschlussdatum, fachliche Relevanz, ggf. Kategorie), alte
  abgeschlossene Tickets nicht automatisch übernehmen — offener Migrationspunkt (Grundlage: Geschlossen/Behoben 1.170, Open 26,
  in Bearbeitung 12, on Hold 1; 483 mit Kontaktbezug). Struktur geprüft: Kontaktbezug, Bearbeiter, Stufe, Kategorie, Team, Titel,
  Inhalte/Chatter und Anhänge direkt migrierbar; Ticketnummer, Erstellzeitpunkt und Ersteller sind schreibgeschützt
  (technischer Importweg nötig). Status-Zuordnung nahezu 1:1 (nur „Open“ gegen „Offen“).

- **Tab „Gemeinde-Information“ ABGESCHLOSSEN / MIGRATIONSBEREIT (Sessions 109/110, 15.09.2026):**
  `docs/o11-o18-strukturvergleich-kontakt-gemeinde-information.md`. Feldbestand in beiden Systemen identisch (Einwohnerzahl,
  Größenklasse, Stand vom, Organisationstyp, Städtebund-Mitglied); Gemeinde-Felder sind normale `itk_crm`-Felder auf dem
  Kontakt (keine x_-Felder, kein eigenes Modell); Größenklasse wird aus der Einwohnerzahl berechnet. Behoben: englische
  Modellbeschriftungen auf die Odoo-11-Wortlaute gesetzt (`itk_crm` 18.0.1.5.1). Session 110: Organisationstypen als
  Ziel-Stammdaten angelegt (Marktgemeinde M, Gemeinde G, Stadtgemeinde ST, Magistrat SR, Magistrat der Stadt MAG,
  Gemeindeverband GV; Mapping-Schlüssel Code) und die Feldbreite im Reiter korrigiert (`itk_base_setup` 18.0.1.2.2,
  colspan — vorher 26 px, jetzt 256 px). Prüfung `scripts/verify_s109_gemeinde_info.py`, lokal 45 OK / 0 FEHL.

- **Tab „Abrechnung“ geprüft und MIGRATIONSBEREIT (Session 108, 15.09.2026):**
  `docs/o11-o18-strukturvergleich-kontakt-abrechnung.md`. Odoo 18 ist im Reiter vollständiger (Bankkonten, Rechnungsversand,
  E-Rechnungsformat, Peppol/VOKZ, Kreditlimits, `autopost_bills`) → kein Rückbau, keine Lücke. Verschobene Felder dokumentiert
  (Zahlungsbedingungen/Steuerposition → „Verkauf & Einkauf“; Bankkonten → „Abrechnung“). **VOKZ geklärt:** = Peppol-Kennung
  `peppol_eas` 9915 „VOKZ für Österreich“; in Odoo 11 kein VOKZ-Feld. Prüfung `scripts/verify_s108_abrechnung.py`
  44 OK / 0 FEHL (lokal und VM).

- **Tab „Verkauf & Einkauf“ ABGESCHLOSSEN / MIGRATIONSBEREIT (Sessions 105–107, 15.09.2026, auf der VM verifiziert):** Feld-Mapping Odoo 11 → Odoo 18 für 23 Felder
  (`docs/o11-o18-strukturvergleich-kontakt-verkauf-einkauf.md`). Kein optischer Rückbau; Odoo 18 ist im Tab vollständiger.
  Behoben: beide Odoo-18-Preislisten waren inaktiv → EUR-Preisliste aktiviert (lokal + VM, reversibel). Offen als
  KLÄRUNG: Preislisten-Zuordnung, 46 fehlende Benutzer, Steuerpositionen, `opt_out`. Prüfung:
  `scripts/verify_s105_verkauf_einkauf.py` 50 OK / 0 FEHL (lokal und VM).
  Session 106: Beschriftung `ref` auf „Interne Referenz“ umgestellt (`itk_base_setup` 18.0.1.2.1).
  Verbindliche Vorgaben für die Datenmigration: Preislisten vorher anlegen/mappen, Benutzer-Mappingstrategie
  (aktive 1:1, ausgeschiedene deaktiviert als historische Verkäuferbeziehung, unklare später einzeln),
  Steuerpositionen zuordnen, `opt_out` über Marketing-/Blacklist-Logik — Details in
  `docs/o11-o18-strukturvergleich-kontakt-verkauf-einkauf.md` Abschnitt 5.

- **picking_warn ausgewertet (Sessions 103/104, 15.09.2026, Empfehlung offen bei Anna):** In Odoo 11 Prod nutzt **kein einziger** der 5.842 Kontakte das Feld
  (`picking_warn = 'no-message'` bei allen, kein Warntext); auch Verkaufs-/Rechnungs-/Einkaufswarnung sind bei 0 Kontakten aktiv.
  → **keine Daten zu migrieren, kein eigenes Feld nötig** (Empfehlung; Entscheidung bei Anna). Die Odoo-18-Einstellung
  „Warnungen“ (Einkauf) bleibt auf Wunsch aktiv, damit „Warnung beim Einkaufsauftrag“ sichtbar bleibt.

- **Tab „Interne Notizen“ angeglichen UND ABGESCHLOSSEN (Sessions 102–104, 15.09.2026):** Abschnittstitel im Odoo-11-Wortlaut („Alarmierung bei
  Auftrag“, „Warnung beim Einkaufsauftrag“), Platzhalter „Interner Hinweis ...“; die Einkaufs-Warnung ist über die
  Odoo-18-Einstellung „Warnungen“ (Einkauf) sichtbar. `picking_warn` („Warnung beim Kommissionieren“) existiert in Odoo 18
  nicht mehr → kein Nachbau. `itk_base_setup` 18.0.1.2.0, auf der VM im Browser verifiziert
  (Screenshot `13_VM_InterneNotizen.png`). Doku: `docs/o11-o18-strukturvergleich-kontakt-interne-notizen.md`.

- **Adressblock abgeschlossen (Session 101, 15.09.2026):** Annas Entscheidung — die Adressmaske passt funktional, **kein
  Odoo-11-Nachbau**. Lieferadresse (O18) = Zustellungsadresse (O11); Privatadresse wird nicht nachgebaut (in Odoo 11 von 0
  Datensätzen genutzt, Odoo 18 hat eine eigene Logik); übrige Adresstypen/Felder funktional vorhanden. Status
  **migrationsbereit**, keine Code-Änderungen. Dokument: `docs/o11-o18-strukturvergleich-kontakte-personen-firmen.md` (Abschnitt 6).

- **Bereich Kontakte → Firmen/Personen & Ansprechpartner (Session 100, 15.09.2026):** Neue Ansprechpartner im Tab
  „Kontakte & Adressen“ werden wieder als **Kontakt** angelegt (Odoo 18 setzte im `child_ids`-Kontext `default_type: 'other'`,
  Odoo 11 nutzt den Feldstandard `contact`) — `itk_base_setup` 18.0.1.1.0, auf der VM verifiziert. Gleich in beiden Systemen:
  Firmen/Personen-Radio, `parent_id`-Domain, Karteninhalte. Kein Nachbau nötig: Adresstyp „Privatadresse“ (Odoo 11: 0 Datensätze).
  Klärung offen: Wortlaute (Adressart/Adresstyp, Verbundenes/Zugehöriges Unternehmen, Zustellungs-/Lieferadresse).
  Doku: `docs/o11-o18-strukturvergleich-kontakte-personen-firmen.md`.

- **Nachbesserung Kontaktansicht (Session 98, 15.09.2026):** Auf der VM fehlten an Kontakt 79 „Ist ein Lieferant“/„Ist ein Kunde“
  (unser Fehler: falsche `is_company`-Bedingung — Odoo 11 hat dort keine) und die Titel-Felder standen im Hauptblock. Behoben in
  `itk_base_setup` 18.0.1.0.9: Lieferant/Kunde immer sichtbar; Titel/akademische Titel in eigener Gruppe unterhalb des Adressblocks
  (bei Firmen ausgeblendet). Kontakt 79 ist auf der VM ein Unternehmen — deshalb sind dort GKZ, Multiplication Factor/Thsd und
  Organisationsbezeichnung sichtbar, bei Personen bleiben sie wie in Odoo 11 verborgen. Auf der VM im echten Browser verifiziert
  (Screenshots `10_VM_Kontakt79_FINAL_*`). Der Bereich war zuvor zu früh als abgenommen bezeichnet.

- **Sichtbares Kontaktformular fertiggestellt (Session 96, 15.09.2026):** Ursache gefunden, warum die Ansicht im Browser unverändert blieb — die View hing an einer **Erweiterungs-View** (itk_crm, prio 16) und wurde deshalb früh angewendet, danach liefen akademische Titel/Website/Karte/Firstname darüber. Sie hängt jetzt an der **Wurzel** `base.view_partner_form` mit `priority 90` und greift zuletzt. Sichtbare Anordnung exakt nach Vorgabe: Kenndaten links GKZ/Multiplication Factor/Thsd/zu Handen/Organisationsbezeichnung, rechts Verkäufer/Ist ein Lieferant/Ist ein Kunde/Status; Adressblock links Adresse/UID/Stichwörter, rechts Telefon/Mobil/E-Mail/Website/Sprache; Titel und akademische Titel am Blockende; Tabs in Odoo-11-Reihenfolge. `vat`-Label auf „UID“ über `scripts/set_country_vat_label_de.py` (Basisdaten, `--revert` möglich). Im echten Browser geprüft: **lokal = VM identisch**; Screenshots `Desktop\Odoo18-Layoutvergleich-Session95\5_/6_...`. Keine Produktionsdaten berührt.
- **Layoutvergleich im echten Browser (Session 95, 15.09.2026):** Die geöffnete Kontaktansicht wurde in Chromium (Playwright, `scripts/browser_form_layout.py`) gegen **Odoo 11 Prod** gerendert und verglichen — nicht mehr nur XML/Arch. Angeglichen in `itk_base_setup` 18.0.1.0.5: **Tab-Reihenfolge** (Interne Notizen 2.), **Kenndaten-Spalten** (links GKZ, Multiplication Factor/Thsd, Ist ein Lieferant, Ist ein Kunde — rechts Verkäufer, zu Handen, Organisationsbezeichnung, Status), **Smart-Button-Reihenfolge** (Verkaufschancen, Verkauf, Meetings), `multi_factor`-Label repo-durable. Ergebnis: Render **lokal = VM** identisch; Screenshots auf dem Desktop (`Odoo18-Layoutvergleich-Session95`), Doku `docs/o11-o18-kontaktformular-layoutvergleich.md`. **Neue Arbeitsregel: „vorhanden" ≠ „erledigt"** — immer auch sichtbar? richtige Position? gleiche Funktion? gleiche Bedienlogik? prüfen.
- **Bereich Kontakte → geöffnetes Kontaktformular (Session 94, 15.09.2026 — Struktur umgesetzt):** Feld-für-Feld-Vergleich (64 gemeinsame Felder) gegen Odoo 11 Prod. Angeglichen: `title` → **Titel** (O18 zeigte „Anrede“), `street2` → **Straße 2** (O18-Tippfehler), `child_ids` → **Kontakte**, `user_id` → **Verkäufer** in beiden Vorkommen; dazu `i18n/de.po` im Repo mit gezielter Overwrite-Ladung. Kenndaten-Bereich (GKZ, Multiplication Factor/Thsd, zu Handen, Organisationsbezeichnung), alle Tabs (inkl. Support Ticket) und die Smart Buttons waren bereits vollständig vorhanden. Modul `itk_base_setup` 18.0.1.0.3. Verifiziert lokal **und** VM: `scripts/verify_s94_contact_form.py` je **28/28 OK**. Offen als **KLÄRUNG NÖTIG**: `vat`-Label UID vs. USt (kommt aus den Basisdaten `res.country.vat_label`), `ref`-Wortlaut, Wortlaute der Smart Buttons, Website-Veröffentlichung, `opt_out`, Buttons nicht migrierter O11-Module. Keine Daten übernommen.
- **Erster Bereich des O11-→O18-Strukturvergleichs: Kontakte → Kontakt-Tags (Session 92, 15.09.2026 — nur Struktur, keine Daten):** Struktur-/Funktionsvergleich gegen das produktive Odoo 11 (nur lesend) in `docs/o11-o18-strukturvergleich-kontakt-tags.md`; neues Modul **`itk_partner_category`** macht die Odoo-18-Ansichten migrationsbereit: Liste mit *Anzeigename* (voller Hierarchiepfad), *ID* und *Tag Anzeigename*, Kategorie/Farbe nur optional; Formular mit read-only-Pfad, Oberkategorie, untergeordneten Kategorien, Aktiv und Farbe; Suche mit Hierarchiesuche (child_of) und Filtern (Hauptkategorien, verwendete/unverwendete Tags, mit/ohne Unterkategorien). **Keine** Odoo-11-Tags und **keine** der 5.307 Zuordnungen uebernommen; `x_tag_anzeigename2` und `parent_left/right` bewusst nicht nachgebaut. Pruefskript: `scripts/verify_s92_partner_category.py` — lokal **und auf der VM 36/36 OK** (inkl. Hierarchie-Test und Aufräumen), Installation auf der VM per `scripts/upgrade_modules.py --instanz vm --update-list --install`; lokal = GitHub = VM auf `64e6203`.
- **O11-Filestore-Backup geprueft (Session 91, 15.09.2026, read-only):** `ITK_V1_a_filestore.tar.gz` gehoert zweifelsfrei zur O11-DB `ITK_V1_a` (Dump-Kopf: `dbname: ITK_V1_a`, PostgreSQL 10.23; die 21.789 `store_fname` des Dumps und die 21.789 Archivdateien sind **mengenidentisch**), ist **zu 100 % intakt** (`SHA-1(Inhalt) == Dateiname`, 0 Abweichungen, 1,89 GB, alle 256 Buckets) und direkt verwendbar. Damit sind **502 der 513 fehlenden Dateien ohne IPAX beschaffbar** (40 Bild-Datensaetze per Hash + 12 semantisch); definitiv offen bleiben **7 Beleg-PDFs + 4 Dashboard-Dateien + 6 Bild-Datensaetze** (3 echte Personen, 12 Testkonten). Werkzeuge: `scripts/f33_filestore_scan.py`, `scripts/filestore_archive_verify.py`. **Nichts kopiert, entpackt oder geaendert.** Naechster Block: O11-Prod-vs.-O18-Feld-/Strukturvergleich.
- **Dritte Runde deutscher Begriffe (Session 89, 14.09.2026):** **Titel vorangestellt/nachgestellt**, **Projekte/Aufgaben**, **SLA-Frist/SLA erfüllt/Team-SLA/Ticket-SLA/Gültige SLAs/SLA setzen** (neue Datei `helpdesk_mgmt_sla/i18n/de.po`), **Zeiterfassung erlauben/Geplante Stunden/Fortschritt/Reststunden/Zeitsteuerung anzeigen/Zeiterfassung/Gesamtstunden/Arbeit starten-stoppen-fortsetzen** (neue Datei `helpdesk_mgmt_timesheet/i18n/de.po`), Korrektur **Erneuerungsangebot** und **Abo-Auftrag**, Kategorie **Anonymisierungsportal** (Daten, beide Instanzen). Helpdesk-Grundbegriff und Feld Team bleiben bewusst. Verifikation: `scripts/verify_s89_de.py` -> 36/36 OK. **Achtung bei .po-Dateien:** die erste `#.`-Zeile eines Eintrags muss `#. module: <modul>` lauten, sonst bricht der Import mit `AttributeError: 'NoneType' object has no attribute 'groups'` ab (der PO-Reader ruft `match.groups()` ungeschuetzt auf). VM-Deploy am 14.09.2026: Pull, Neustart, 5 Einzel-Upgrades, gezielte Ladung, Neustart -> **lokal 36/36 und VM 36/36 OK**, Log 0 Fehler, lokal = GitHub = VM auf `0f10547`.
- **Zehn weitere Begriffe deutsch (Session 88, 14.09.2026):** Der PO-Reader mischt die **`.pot`-Referenzen** in die `.po` (`PoFileReader` -> `merge`) - dadurch blieben deutsche Texte trotz korrekter `.po` englisch (F32). `scripts/fix_po_xmlids_de.py` korrigiert jetzt auch die `.pot`-Dateien (**625 weitere Referenzen in 10 Modulen**). Umgesetzt: **Rechnung manuell erstellen** (Abo-Button), **Vorname/Nachname**, **Einwohnerzahl**, **Einwohnerzahl aktualisiert am**, **Peppol-Endpunkt**, **Karte/Routenplaner**, Helpdesk-Duplikatbegriffe, Menues **ITK-Menü**, **SLAs**, **Helpdesk-Gruppen**. Neue Werkzeuge: `scripts/load_terms_de.py` (gezielte Nachladung mit `overwrite=True`) und `scripts/verify_s88_de.py` (read-only Pruefung lokaler Instanz + VM). Nicht geaendert: fachlich unklare Begriffe, OCA-Modulnamen, DB-gepflegte Menues/Stages/Kategorien. Wichtig: Python-Label-Aenderungen (itk_crm) und Aenderungen aus `odoo shell` werden erst nach einem Container-Neustart sichtbar. VM-Deploy am 14.09.2026 durchgefuehrt (Pull, Neustart, 8 Einzel-Upgrades, 2 gezielte Ueberschreib-Ladungen, Neustart): **lokal 17/17 und VM 17/17 OK**, lokal = GitHub = VM auf `e94b511`. Log-Gegenprobe 48 h ohne neue Fehlerarten.
- **Deutsche Texte kommen jetzt aus dem Repo (Session 87, 11.09.2026):** Ursache der englischen Feld-/Button-Texte behoben — die `i18n/de.po` der migrierten Module referenzierten Odoo-11-XML-IDs (einfacher Unterstrich), `model:` statt `model_terms:` für Views und die in Odoo 18 entfernte Form `selection:modell,feld:index`; der PO-Import ignoriert solche Einträge stillschweigend. Korrektur per `scripts/fix_po_xmlids_de.py` (**543 Referenzen in 15 Modulen**) + **deutsche ITK-Modulnamen** in 14 Manifesten (Apps-Liste, z. B. „ITK CRM-Erweiterung", „ITK Druckvorlagen"). Nach gezielten Einzel-Upgrades lokal verifiziert: Abo-Felder (`Kunde`, `Startdatum`, `Preisliste`), Abo-Statuswerte (**Neu/Laufend/Zu erneuern/Abgeschlossen/Abgebrochen**), Abo-Buttons und Apps-Liste deutsch; **„Kundenverwaltung" unverändert**. **VM-Deploy am 14.09.2026 nachgezogen** (direkter SSH-Zugang wieder offen): Pull auf `1f07d61`, Neustart, 26 Module einzeln upgegradet, Verifikation auf der VM identisch grün → lokal = GitHub = VM.
- **Zeitzonen gesetzt (Session 86, 11.09.2026):** alle **14 aktiven internen Benutzer** stehen auf **`Europe/Vienna`** — auf **VM und lokal** (uid 13–24 gesetzt, uid 2/8 waren bereits korrekt); ohne Zeitzone hätte Odoo mit UTC gerechnet (Zeiten 2 h zu früh). Die 4 inaktiven technischen/System-/Portal-Konten blieben unberührt, es wurde nichts gelöscht oder archiviert.
- **Berichtigt (Session 83 geprüft, Session 85 nachgezogen):** Das EUR-Symbol ist jetzt auf **beiden** Instanzen korrekt `€` (VM Session 81, **lokal 11.09.2026: ein gezielter Feld-Write auf `res.currency` id 126 — keine globale Ersetzung, VM unverändert**); Odoo-Formatter `65,00 €`/`1.234,56 €`, gerenderte Rechnung/Auftrag ohne Mojibake. F11 (itk_projectcategory) und F12 (tree→list-Upgrades) sind erledigt: installierte Version = Repo-Version auf beiden Instanzen.
- Weitere Modul-Upgrades bzw. Funktionsanpassungen nur **kontrolliert und nach Bedarf** (je Freigabe)
- **Noch offen:** E-Mail-Versand (SMTP) — Konfiguration in einer der nächsten Sessions; Admin-Passwort-Rotation (bewusst separat, nach Sicherheitsfund Session 77)

## Geparkte/Archivierte Module

|| Modul | Grund |
||---|---|
|| `web_tree_resize_column` | JS inkompatibel mit Odoo 18 OWL |
|| `web_group_expand` | JS inkompatibel mit Odoo 18 OWL |
|| `mass_editing` | Ersetzt durch `server_action_mass_edit` (OCA) |
|| `hr_holiday_exclude_special_days` | `hr_holidays_public` bereits migriert |
|| `itk_fix_import` | Einmal-Fix ("DO NOT INSTALL AGAIN") |
|| `itk_main_company_import` | `installable: False`, Firmendaten manuell |
|| `itk_update_population` | Historische Einmal-Aktualisierung (2018) |
|| 9× `itk_initial_*` / `itk_data_setup` | Datenimport-Module → Daten über CSV migrieren (siehe DATA_MIGRATION_CHECKLIST.md) |
|| `bi_crm_claim` | 0 Datensätze, nie produktiv genutzt |
|| `website_support` | Ersetzt durch OCA `helpdesk_mgmt` |
|| `website_support_analytic_timesheets` | Ersetzt durch OCA `helpdesk_mgmt_timesheet` |
|| `website_support_billing` | Ersetzt durch Odoo-18-Standard-Projektabrechnung |
|| `itk_support` | Leeres Modul, Menüs in `itk_translation` |

## Entfällt (Funktionalität in Odoo 18 nativ / kein OCA-18.0-Branch)

|| Modul | Grund |
||---|---|
|| `mail_activity_board` | Kein OCA-18.0-Branch, Activity-System nativ in Odoo 18 |
|| `web_responsive` | Odoo 18 nativ responsive (Bootstrap 5 + OWL) |
|| `itk_contract` | 0 Datensätze, Felder in itk_subscription enthalten |

## Datenmigration

Die `DATA_MIGRATION_CHECKLIST.md` enthält den vollständigen Plan für den
Datenexport aus Odoo 11 und Import nach Odoo 18: Reihenfolge, Kontrollzahlen,
Abhängigkeiten und Importwege pro Datenbereich.

## Struktur

```
odoo-migration/
├── addons/              → 37 Odoo-Addons (35 funktionsfähig + 2 geparkt)
├── geparkt/             → 22 geparkte + 3 entfällt
├── config/              → Odoo-Konfiguration
├── odoo11 module/       → 0 verbleibende Odoo-11-Quellen (alle analysiert)
├── postgres/            → PostgreSQL-Datenbank
├── docker-compose.yml   → Docker-Stack (Odoo 18 + PostgreSQL 16)
├── MIGRATION_READINESS_CHECKLIST.md → Abnahme-Checkliste Odoo 18 vor O11-Migration (Sprache/Währung/Encoding/Grundeinstellungen/Fachbereiche + Testreihenfolge)
├── PROJECT_KNOWLEDGE.md → Detailliertes Projekt-Tagebuch
└── README.md            → Diese Datei
```

## Details

Das **PROJECT_KNOWLEDGE.md** enthält:
- Komplette Session-Chronik (alle Änderungen, Fehler & Lösungen)
- Rollback-Anleitungen (Git-Checkout zu jedem Stand)
- Zugänge & technische Konfiguration

## Testsystem

| Komponente | Adresse / Zugang |
|---|---|
| Odoo 18 (lokal, Windows Docker) | http://localhost:8069 |
| Odoo 18 Test-VM (IPAX, Ubuntu 26.04) | **https://k001959vsx.ipax.at** (nginx-Reverse-Proxy + Let's-Encrypt-Zertifikat, HTTP→HTTPS-Redirect; Odoo lauscht weiterhin NUR auf 127.0.0.1:8069, PostgreSQL nur Docker-intern). **Zugang: VPN + Teleport** auf `k001959vsv` (User `k001959`) — direkter `ssh k001959@93.189.28.204` läuft ins Timeout, Port 22 ist von außen VM-seitig gefiltert (Befund 10.09.2026, Session 83); Analyse/DB-Arbeiten daher über HTTPS-JSON-RPC oder Teleport-Shell. Teststand `odoo18_test` am 31.08.2026 1:1 übertragen; VM auf `main` = `1d6c835` (11.09.2026); VM-Backups unter `/opt/odoo18/backups/` |
| PostgreSQL (lokal) | localhost:5432, User `odoo` |
| PostgreSQL (Test-VM) | nur internes Docker-Netz (kein Host-Port-Mapping, nicht öffentlich erreichbar) |
| Odoo 11 (Referenz, alt) | dekommissioniert — alte VM wurde am 31.08.2026 durch die Ubuntu-26.04-Neuinstallation ersetzt; die IP 93.189.28.204 dient jetzt der Odoo-18-Test-VM |
| Docker-Stack | `docker compose up -d` im Projektverzeichnis — erfordert `.env` mit `POSTGRES_PASSWORD` (wird nicht committet) |

## Betriebshinweise

**Web-Zugriff (seit 01.09.2026):** https://k001959vsx.ipax.at — nginx (Port 80/443) als Reverse-Proxy vor Odoo (127.0.0.1:8069). ufw: nur 22/80/443 offen. Let's-Encrypt-Zertifikat mit Auto-Renew (certbot, deploy-hook nginx-reload). Konfiguration: `config/odoo.conf` (gitignored, Vorlage `config/odoo.conf.example`) + `config/nginx_odoo.conf` (Referenz, deployed als /etc/nginx/sites-available/odoo).

**Nach jedem `docker compose down && docker compose up -d`** kann die Login-/Web-Oberfläche
ungestylt erscheinen (kein Odoo-Design, fehlende Login-Felder). Ursache sind veraltete
Asset-Bundles in der DB-Tabelle `ir.attachment` (URLs `/web/assets/*`), die auf tote Datei-Hashes
zeigen. **Fix:** diese Anhänge löschen (`ir.attachment` mit URL `/web/assets/%`) und die Seite neu
laden – Odoo regeneriert die CSS/JS-Bundles automatisch. Details siehe PROJECT_KNOWLEDGE.md
(Session 12 Nachtrag & Session 21).

## Lizenz

LGPL-3
