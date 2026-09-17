# MIGRATION-READINESS-CHECKLIST — Odoo 18 Abnahme vor der Odoo-11-Datenmigration

> **Zweck:** Fachliche und technische Abnahme der Odoo-18-Testumgebung (ITK), **bevor** produktive Odoo-11-Daten migriert werden.
> **Referenzumgebung:** https://k001959vsx.ipax.at — DB `odoo18_test` (IPAX-Test-VM, Ubuntu 26.04, Docker odoo:18 + postgres:16)
> **Stand:** 03.09.2026 — Abschnitt 1 (A Sprache): read-only-RPC-Inventar (Session 80), Korrekturen F14–F26 ausgeführt (Session 81, VM-Slots + Repo-Code). **Session 82 (03.09.):** Abo-Anlage-Fix (Pflichtfeld `pricelist_id`) — Ursache, Fix und Tests in PROJECT_KNOWLEDGE.md (Session 82); EUR-Preisliste id 34 „Preisliste 2026 + Valorisierung" auf lokal + VM **aktiviert** (Befund F5 teilweise behoben). Detail-Inventar: `docs/abnahme_sprache_ui_abschnitt1.md`.
> **Datengrundlage dieses Dokuments:** ausschließlich read-only-Analysen (SQL über die VM-DB, Repo-Vergleich). Keine Änderungen an DB, Modulen, Views, Konfiguration oder Daten.
>
> **WICHTIGE REGELN (fortgeschrieben):**
> - Keine Korrekturen ohne ausdrückliche Freigabe. Befunde werden hier dokumentiert, nicht behoben.
> - **Feld-für-Feld-Vergleich O11→O18 (seit 15.09.2026, Session 92):** Referenz ist jetzt vorhanden — **lesender** Zugriff auf das produktive Odoo 11 (`https://portal.it-kommunal.at`) und der lokale Produktiv-Dump `ITK_V1_a` (03.09.2026, PostgreSQL 10.23). Der Vergleich läuft **bereichsweise** in Abschnitt 6 und hat mit Kontakte → Kontakt-Tags begonnen.
> - **In dieser Phase wird nur die Odoo-18-Struktur vorbereitet.** Es werden **keine** Odoo-11-Daten, Tags oder Zuordnungen übernommen (keine der 5.307 Kontakt-Tag-Zuordnungen, keine Produktionsinhalte). Die Datenmigration folgt erst, wenn alle Bereiche in Odoo 18 angepasst und getestet sind.
> - Kein `-u all`, keine Modul-Upgrades, keine Datenmigration, keine Testdaten, kein E-Mail-Server-Setup in dieser Phase.
> - **VERBINDLICHE MIGRATIONSREGEL (ab 15.09.2026, Session 99): Organisationen werden in Odoo 18 als Unternehmen angelegt, natürliche Ansprechpartner als Person.**
>   Gemeinden, Verbände, Firmen und sonstige Organisationen = `is_company = True`; Personen = `is_company = False`. Die Zuordnung darf bei der
>   Migration **nicht pauschal** erfolgen — jede Zuordnung prüfen, unklare Fälle einzeln entscheiden. Anlass: Kontakt 79 war als Person angelegt,
>   dadurch waren GKZ, Multiplication Factor/Thsd, Organisationsbezeichnung, Status und der Tab Gemeinde-Information unsichtbar (die Kenndaten hängen
>   an `is_company`). Detail und Vorgehen beim Import: `docs/migrationsregel-organisation-vs-person.md`. Beim Testen immer auch `is_company`/`company_type`
>   des Datensatzes mitprüfen — ein „fehlendes Feld“ kann eine Typisierungsfrage sein.
> - **VERBINDLICHE ABNAHMEREGEL (ab 15.09.2026, Session 97): Die VM https://k001959vsx.ipax.at ist die maßgebliche Test- und Abnahmeumgebung.**
>   Lokal (`C:\Odoo-Test`, `localhost:8069`) dient der Entwicklung, Analyse und dem Vorabtest. Ein Punkt gilt erst als umgesetzt bzw.
>   abgeschlossen, wenn er (1) auf der VM deployed, (2) in der VM-DB `odoo18_test` geladen/aktiviert, (3) direkt gegen die VM geprüft
>   und (4) dort im echten Browser sichtbar bzw. funktional bestätigt ist. Ein Git-Pull allein genügt nicht: gezieltes Modul-Upgrade
>   bzw. notwendige Aktivierung auf der VM immer prüfen. Bei UI-/View-Änderungen die tatsächlich aktive View und die sichtbare
>   Darstellung auf der VM kontrollieren (nicht nur XML/DOM/RPC). Nach Doku/Commit/Push/PR/Merge die VM auf den finalen `main`-Stand
>   bringen und dort abschließend verifizieren. Prüfwerkzeug: `python scripts/vm_abnahme_check.py` (Rückgabewert 1 = VM-Abnahme offen).
>   Detail: `docs/arbeitsregel-vm-abnahme.md`.

## Status-Legende

| Status | Bedeutung |
|---|---|
| OFFEN | Noch zu testen (Abnahme läuft) |
| OK | Geprüft, entspricht Erwartung |
| BEHOBEN | Befund wurde korrigiert (mit Datum/Session dokumentiert) |
| KLÄRUNG NÖTIG | Fachliche Klärung erforderlich (keine Korrektur, Arbeit lief weiter) |
| FEHLER | Konkreter Befund, der vom Soll abweicht (nur dokumentiert, nicht behoben) |
| ANPASSUNG NÖTIG | Anpassung erforderlich (nach Freigabe) |
| NICHT RELEVANT | Für ITK-Fachabnahme nicht relevant (keine Nutzung/keine Daten) |

---

## 0. Modulinventar (Aufgabe 1) — Stand 01.09.2026

**Zahlensetzung:** Die 158 technisch installierten Module sind **nicht** „zu testende Module“. Sie zerfallen in:
- **40 Module aus unserem Repo** (`addons/`, davon 41 Verzeichnisse − 1 nicht installiert) → **die eigentlichen Kandidaten der Abnahme**:
  - 15 `itk_*`-Module (eigenentwickelt, fachlich zentral)
  - 6 OCA-/Helpdesk-Module
  - 19 weitere migrierte Drittanbieter-/Web-Module aus Odoo 11
- **118 Odoo-18-Standardmodule** aus dem `odoo:18`-Image (base, web, account, crm, sale, …). Davon sind nur **~12 fachlich genutzt** (Abschnitt 0.5); der Rest ist technische Basis (Installationsabhängigkeiten) und wird nicht fachlich abgenommen.
- **`geparkt/` (13 Verzeichnisse):** nicht installiert, kein Abnahmebedarf (außer Doku-Abgleich, s. Befund B10).
- **`addons/`-Verzeichnisse ohne Installation:** nur `web_tree_resize_column` (geparkt, JS/OWL-inkompatibel).

### 0.1 Installierte itk_*-Module (15) — technischer Name + sichtbare Bezeichnung

| Technischer Name | Sichtbare Bezeichnung (shortdesc) | Version DB | Version Repo | Daten | Zu testen |
|---|---|---|---|---|---|
| `itk_subscription` | ITK Abo-Management | 18.0.1.0.0 | 18.0.1.0.0 | 5 Abos, 3 Vorlagen | ✅ |
| `itk_crm` | `itk_crm` (nur techn. Name) | 18.0.1.5.0 | 18.0.1.5.0 | 1 Lead, 8 Stages, 4 Teams | ✅ |
| `itk_product` | `itk_product` | 18.0.1.0.0 | 18.0.1.0.0 | 6 Produkt-Typen | ✅ |
| `itk_projectcategory` | `itk_projectcategory` | **18.0.0.1** | **18.0.1.0.0** | Projektkategorien | ✅ (Upgrade offen) |
| `itk_sale_management` | `itk_sale_management` | 18.0.1.0.0 | 18.0.1.0.0 | Angebots-Layout | ✅ |
| `itk_valorisierung` | `itk_valorisierung` | 18.0.1.0.0 | 18.0.1.0.0 | 1 Valorisierung | ✅ |
| `itk_saleorder_lines` | `itk_saleorder_lines` | 18.0.1.0.0 | 18.0.1.0.0 | — | ✅ |
| `itk_multifactor` | `itk_multifactor` | 18.0.1.0.0 | 18.0.1.0.0 | — | ✅ |
| `itk_base_setup` | `itk_base_setup` | 18.0.1.0.0 | 18.0.1.0.0 | Grundeinstellungen | ✅ |
| `itk_third_party_setup` | `itk_third_party_setup` | 18.0.1.0.0 | 18.0.1.0.0 | — | ✅ |
| `itk_reports` | `itk_reports` | 18.0.1.0.0 | 18.0.1.0.0 | 4 Druckvorlagen | ✅ |
| `itk_automated_actions` | `itk_automated_actions` | 18.0.1.0.0 | 18.0.1.0.0 | Autom. Aktionen | ✅ |
| `itk_translation` | `itk_translation` | 18.0.1.0.0 | 18.0.1.0.0 | ITK-Menü/-Views | ✅ |
| `itk_helpdesk_category_user` | ITK Helpdesk Category User | 18.0.1.0.0 | 18.0.1.0.0 | Kategorie-Follower | ✅ |
| `itk_helpdesk_compat` | ITK Helpdesk Compatibility | 18.0.1.0.0 | 18.0.1.0.0 | Helpdesk-Oberfläche | ✅ |

### 0.2 Installierte OCA-/Helpdesk-Module (6)

| Technischer Name | Sichtbare Bezeichnung | Version | Zweck | Zu testen |
|---|---|---|---|---|
| `helpdesk_mgmt` | Helpdesk Management (en) | 18.0.1.17.1 | OCA-Ticketsystem (Ersatz für website_support) | ✅ |
| `helpdesk_mgmt_project` | Helpdesk Project (en) | 18.0.1.3.0 | Ticket↔Projekt-Verknüpfung | ✅ |
| `helpdesk_mgmt_sla` | Helpdesk Ticket SLA (en) | 18.0.2.1.0 | SLA-Management | ✅ |
| `helpdesk_mgmt_timesheet` | Helpdesk Ticket Timesheet (en) | 18.0.1.1.3 | Zeiterfassung auf Tickets | ✅ |
| `project_timesheet_time_control` | Project timesheet time control (en) | 18.0.1.0.7 | Zeiterfassungskontrolle | ✅ |
| `server_action_mass_edit` | Mass Editing (en) | 18.0.1.1.3 | Massenbearbeitung (ersetzt mass_editing) | ✅ |

### 0.3 Migrierte Drittanbieter-/Web-Module aus Odoo 11 (19, installiert)

`partner_firstname`, `hr_employee_firstname`, `partner_academic_title`, `partner_external_map`, `merge_sale_order`, `merge_purchase_order`, `purchase_order_line_number`, `account_invoice_line_number`, `account_invoice_line_report`, `sale_order_line_number`, `sale_merge_draft_invoice`, `mass_email_invoice`, `website_cookie_notice`, `website_odoo_debranding`, `web_environment_ribbon`, `web_no_bubble`, `web_sheet_full_width`, `web_group_expand` ⚠️ (als „geparkt“ dokumentiert, aber installiert — Doku-Inkonsistenz, s. Befund B10), `hr_holidays_public`.

### 0.4 Fachlich genutzte Odoo-18-Standardmodule (zu testen)

| Modul | Verwendung bei ITK | Daten (Ist) |
|---|---|---|
| `contacts` | Kontakte/Firmen/Ansprechpartner | 76 Partner (12 Firmen) |
| `crm` (+ `sales_team`, `crm_iap_*`, `crm_sms`) | CRM-Leads/Opportunities | 1 Lead, 8 Stages, 4 Teams |
| `sale` / `sale_management` | Angebote/Verkaufsaufträge | 16 Aufträge, 26 Positionen |
| `product` (+ `uom`) | Produkte/Preislisten | 23 Produkte, 2 Preislisten |
| `account` (+ `account_payment`, `l10n_at`, `l10n_din5008*`) | Rechnungsstellung/Fibu (soweit genutzt) | 22 Belege, 7 Journale, 7 Zahlungen |
| `project` (+ `project_account`, `project_purchase`, `project_todo`) | Projekte | 5 Projekte, 8 Aufgaben |
| `hr` (+ `hr_holidays`, `hr_timesheet`, `hr_attendance`) | Mitarbeiter/Abwesenheiten | 24 Mitarbeiter, 1 Abwesenheit |
| `sale_subscription` | Abo (Basis für itk_subscription) | 5 Abos, 6 Positionen, 3 Vorlagen |
| `mail` (Discuss) | Nachrichten/Aktivitäten | 456 Nachrichten, 0 Aktivitäten |
| `website` (+ `website_crm`, `website_mail`) | Webauftritt (Debranding/Cookie) | 1 Website |
| `base` / `web` | Basis/UI — kein fachlicher Test | — |
| `portal` | Kundenportal | nicht näher untersucht |

### 0.5 Installiert, aber NICHT RELEVANT für die Fachabnahme (0 Daten / keine ITK-Nutzung)

`survey`, `mass_mailing*`, `hr_attendance`, `project_milestone`, `gamification*`, `digest`, `spreadsheet*`, `snailmail`, `sms`, `social_media`, `auth_signup`/`auth_totp*`, `payment` (als technische Basis), `iap*`, `website_links`, `privacy_lookup`, `google_*` u. a. — Status **NICHT RELEVANT** (kein fachlicher Test nötig; Funktionalität ggf. später bewusst aktivieren).
**Nicht installiert:** `stock`, `mrp`, `pos`, `fleet`, `documents`, `lunch` (keine Tabellen vorhanden) — kein Testbedarf.

### 0.6 Addon-Verzeichnisse im Repo (nicht identisch mit „installiert“)

- `addons/`: 41 Verzeichnisse → 40 installiert, 1 nicht installiert (`web_tree_resize_column`, geparkt).
- `geparkt/`: 13 Verzeichnisse (inkl. Untergruppen `entfaellt/`, `initial_import_modules/`) → 0 installiert.
- 118 installierte Module ohne Repo-Verzeichnis = Odoo-18-Standard aus dem Image (inkl. `account_add_gln`).
- **Konsequenz:** „158 installiert“ ≠ „41 Addon-Verzeichnisse“ ≠ „zu testende Module“. Zu testen sind: 15 itk + 6 OCA/Helpdesk + 19 migrierte Drittanbieter + ~12 genutzte Standardmodule (Abschnitte 0.1–0.4).

---

## 1. A — Sprache / Deutsch

**Istzustand (read-only, aktualisiert 02.09.2026):**
- `res_lang`: 92 Einträge, **nur `de_DE` aktiv** (en_US vorhanden, aber inaktiv). → UI-Standardsprache ist Deutsch.
- Alle 14 aktiven Benutzer: `lang = de_DE`. System-Benutzer ebenfalls de_DE.
- Datums-/Zahlenformat de_DE: `%d.%m.%Y`, `%H:%M:%S`, Dezimaltrennzeichen `,`, Tausendertrennzeichen `.` (korrekt für Österreich).
- `web.base.url = https://k001959vsx.ipax.at` (korrekt).
- **RPC-Inventar 02.09.2026 (de_DE/en_US-Kontext, uid=2, gegen die VM):** sichtbare Texte der 15 itk_*- + 6 OCA-/Helpdesk-Module (Menüs, Actions, View-Namen, Feldlabels inkl. `fields_get`, Auswahlwerte, Modul-shortdesc) + 30 Fachmodelle systematisch erfasst. Befunde F14–F26; Gesamtinventar in `docs/abnahme_sprache_ui_abschnitt1.md`. Kern-Standardmodelle (res.partner, crm.lead, product.template, account.move, sale.order) zeigen in der UI-Sprachquelle `fields_get` **deutsche** Labels (Stichprobe OK). Keine Browser-Sichtprüfung (nächster Schritt, gemeinsam).

| Bereich | Funktion/Feld | Odoo-18-Istzustand | Status | Fehler/Abweichung | notwendige Anpassung | getestet |
|---|---|---|---|---|---|---|
| Menüs | Apps-Leiste (22 Top-Menüs) | Kern-Apps deutsch (Kundenverwaltung, Kontakte, Verkauf, Rechnungsstellung, Abonnements, …); Ausnahmen: „Helpdesk“ (OCA-Root), „ITK-Menu“ (itk_translation), „To-do“ | ANPASSUNG NÖTIG | „ITK-Menu“ = technischer Name als sichtbares App-Label (F14); „Helpdesk“/„To-do“ ohne de-Label (F21-Hinweis) | de-Labels/App-Namen festlegen (nach Freigabe) | teilweise (RPC-Inventar 02.09.; Browser offen) |
| Menüs | itk_translation-Untermenüs (ITK-Menu/Partner + /Reseller) | **8 Untermenüs englisch** (Actual/All/Former/Target customers, All Resellers, All Magnitudes, …) + 6 Actions englisch | **FEHLER** | sichtbare englische Menü-/Action-Namen (F14) | deutsche Bezeichnungen (nach Freigabe) | ja (RPC) |
| Menüs | Helpdesk-Baum (OCA + itk_helpdesk_compat) | größtenteils deutsch (Tickets, Meine Tickets, Kategorien, Stufen, Teams, Kanäle, Prioritäten, …) | ANPASSUNG NÖTIG | „All Tickets“, „Dashboard“, „Settings“ (unter Konfiguration), Action „Helpdesk Ticket“ (F21); itk_helpdesk_compat: „Support Tickets“ (F20); helpdesk_mgmt_sla: „SLA“, „SLA Report“ (F22); Zeiterfassung: „Start work“ (F24) | deutsche Bezeichnungen (nach Freigabe) | ja (RPC) |
| Feldbezeichnungen | Standard-Kernmodelle (Kontakt, CRM, Produkt, Angebot/Auftrag, Rechnung) | de_DE-Übersetzungen vorhanden (fields_get-Stichprobe: „Straße“, „Verkaufschance“, „Kunde“, „Gesamt“, „Verkaufspreis“ …) | OK (Stichprobe) | — | — | teilweise (RPC; Browser offen) |
| Feldbezeichnungen | Custom-Felder itk_crm auf res.partner/res.users | **~15 englische Labels** (Status of Community, Member of City Alliance, Title in Front/Back, Size of Population, Asset Partner, Sales as Final Customer, Reseller, Salutation, First/Last name …; s. F15) | **FEHLER** | englische Labels ohne de_DE-Text | de_DE-Labels (nach Freigabe) | ja (RPC) |
| Feldbezeichnungen | sale.subscription/-template (Abonnements) | **überwiegend englisch** (Start/End Date, Customer, Notice Period, Subscription Template, Created on/by …; ~70/~38 Kandidaten, s. F17) | **FEHLER** | Module-Übersetzung fehlt trotz de.po in itk_subscription (nur Menüs/Actions übersetzt) | de_DE-Übersetzung der Felder (nach Freigabe) | ja (RPC) |
| Feldbezeichnungen | itk_* auf Verkauf/Produkt/Rechnung/Abo (sale.order, product.template, account.move, sale.order.line, sale.subscription.line) | englische Zusatzfeld-Labels (Subscription Count/Management, Subscription Product/Template, Product-Type, To multiply by Factor(thsd)/(per 1000), Multiplication Factor/Thsd, Administrative/Technical/Sale/Final Customer, Valorisation Text, Project Category, Invoice Note, Benefit Period …; s. F18/F19) | **FEHLER** | englische Labels | de_DE-Labels (nach Freigabe) | ja (RPC) |
| Feldbezeichnungen | OCA Helpdesk-Zusatzmodule (sla/timesheet/project) + Kategorie-Follower | englische Labels (Assigned Users, Allow Timesheet, Planned/Remaining/Total Hours, Deadline, Expected Stage, Ignore Stages, Ticket Count, Number of tickets, Use Tickets as …; s. F22/F23) | **FEHLER** | Module ohne de.po bzw. de.po nicht geladen | de_DE-Übersetzung (nach Freigabe) | ja (RPC) |
| Buttons/Statuswerte | Stages/Kanban-Spalten CRM + Helpdesk | CRM-Stages deutsch (Neu … Verrechnet), Helpdesk-Stages deutsch (Offen …); Aktivitätstypen (12 aktiv) deutsch | ANPASSUNG NÖTIG | Stage „On-Hold“ (CRM) und „on Hold“ (Helpdesk) englisch (F25) | fachliche Namensentscheidung (nach Freigabe) | ja (RPC) |
| Auswahlwerte | x_-Felder crm.lead + Standard-Selection | Werte deutsch (x_Produktinteresse, x_lead_status „Bereits Kunde“ …, Standard-Selection-Labels deutsch) | ANPASSUNG NÖTIG | Feld-Labels x_lead_status „Lead Status“, x_Anrede_Lead „Anrede Lead“ (F16); Auswahlwert „On-Hold“; vereinzelte Mojibake-Auswahlwerte (F26) | de_DE-Labels (nach Freigabe) | ja (RPC) |
| Eigene itk_*-Felder | alle Custom-Felder (GKZ/Status/Community/Magnitude/…) | Felder vorhanden; Labels teils deutsch („Ist ein Kunde“, „zu Handen“, „Adresstyp“), teils englisch (s. oben) | ANPASSUNG NÖTIG | englische/fehlende de_DE-Labels (F15–F19) | de_DE-Labels (nach Freigabe) | ja (RPC) |
| Benutzerhinweise/Warnungen | Wizard-Texte, Fehlermeldungen | nicht geprüft (RPC nicht abgedeckt) | OFFEN | — | — | nein |
| Kanban-/Listen-/Formularansichten | CRM-Kanban, Aktivitäten-Kanban, Helpdesk-Views | Datenlabels (Stages/Typen/Kategorien) deutsch; View-Namen teils technisch | OFFEN | Browser-Sichtprüfung ausstehend (Kategorien-Duplikate/Tippfehler „Anynomisierungsportal“ s. F25) | — | nein |
| **Modulbezeichnungen (Apps-Liste)** | shortdesc der installierten Module | 12 von 15 itk-Modulen + alle 6 OCA-Module nur technischer/englischer Name (RPC bestätigt: de == en, z. B. „itk_crm“, „Helpdesk Management“, „Mass Editing“); itk_subscription „ITK Abo-Management“ OK; itk_helpdesk_compat/category_user nur engl. Zusatz | **ANPASSUNG NÖTIG** | Sichtbare Modulnamen in der deutschen Apps-Liste sind englisch/technisch (F6) | de_DE-shortdesc für die fachlich sichtbaren Module ergänzen (nach Freigabe) | ja (RPC) |
| **Modulbezeichnung `account_payment`** | shortdesc de_DE | „Zahlung ÔÇô Konto“ (CP850-Mojibake) — per RPC bestätigt | **FEHLER** | En-Dash „–“ als „ÔÇô“ fehlkodiert (F7) | Translation korrigieren (nach Freigabe) | ja (RPC) |

**Grundsatz:** Englische technische Begriffe nicht blind ersetzen. Unterscheiden: interner technischer Name (Modulname, Feldname, XML-ID) ≠ Benutzeroberfläche. Nur sichtbare UI-Texte sind zu prüfen; technische Namen bleiben unverändert.

---

## 2. B — Umlaute / Sonderzeichen / Encoding

**Testzeichen:** `ä ö ü Ä Ö Ü ß` sowie `€ & / - ' " ( )`

**Sinnvolle Testtexte (für Eingabe/Suche/Filter/PDF):**
1. `Marktgemeinde Groß-Enzersdorf`
2. `Straße & öffentliche Verwaltung`
3. `Änderung – Prüfung € 1.234,56`
4. Ergänzend: `Müller & Söhne`, `Halbjahres-Rechnung`, `10 % Rabatt`, `Öffnungszeiten`, `„Anführungszeichen“`

**Prüforte (Tabelle):**

| Bereich | Funktion/Feld | Odoo-18-Istzustand | Status | Fehler/Abweichung | notwendige Anpassung | getestet |
|---|---|---|---|---|---|---|
| Firmenname | res.partner (Firma) | Stichprobe OK (z. B. „Großhöflein“, „Städtebund Burgenland“, „Bundesministerium für Bildung, Wissenschaft und Forschung“) | OK (Stichprobe) | — | — | teilweise |
| Kontaktname | res.partner (Person) | Stichprobe OK („Würrer Florian“, „Michaela Müller“) | OK (Stichprobe) | — | — | teilweise |
| Straße/Adresse | res.partner.street | ├-Mojibake: 0 | OK (Muster-Check) | — | — | teilweise |
| Beschreibung/Textfelder | product/lead/ticket-Beschreibungen | ├-Mojibake: 0 | OK (Muster-Check) | — | — | teilweise |
| CRM | crm.lead.name/description | ├-Mojibake: 0 | OK (Muster-Check) | — | — | teilweise |
| Produkte | product.template.name/description | ├-Mojibake: 0 | OK (Muster-Check) | — | — | teilweise |
| Suche/Filtern | Universal-Suche, Filter nach Umlauten | nicht geprüft | OFFEN | — | — | nein |
| Anhänge/Dateinamen | ir.attachment (1260) | Dateinamen mit Umlauten nicht geprüft | OFFEN | — | — | nein |
| PDFs | Reports (itk_reports, Rechnung, Angebot) | gerendert (frühere Sessions), Umlaute nicht einzeln geprüft | OFFEN | — | — | nein |
| E-Mails | Versand (später) | SMTP noch nicht konfiguriert | OFFEN | — | — | nein |
| **res_currency.symbol** | Währungssymbole | EUR-Symbol = `€` (korrigiert 02.09.2026, Session 81; vorher `Ôé¼` CP850-Mojibake); USD `$` ok | **BEHOBEN** | F1: CP850-Schaden in der Symbolspalte | — (erledigt; weitere Symbole waren nicht betroffen: nur EUR/USD vorhanden) | ja (RPC/DB 02.09.) |
| **ir_module_module.shortdesc** | installierte Modul-Labels | `account_payment`: „Zahlung – Konto“ (korrigiert 02.09.2026, Session 81; vorher „Zahlung ÔÇô Konto“); 14 weitere (nicht installierte) l10n-/mrp-/pos-Module mit ÔÇô-Muster (nicht installiert → kein Eingriff) | **BEHOBEN** | F7: CP850-Mojibake „–“ → „ÔÇô“ | — (erledigt; nur installierte Module relevant) | ja (RPC 02.09.) |
| **de_DE-Übersetzungen (Feldlabels/Auswahlwerte)** | sichtbare UI-Übersetzungen | 3 Stellen korrigiert 02.09.2026 (F26): `account.move.status_in_payment` = „Status „In Zahlung““, `account.reconcile.model.line.show_force_tax_included` = „„Steuer inklusive erzwingen“ anzeigen“, `res.partner.peppol_eas`-Wert `0245` = „SK-Steueridentifikationsnummer (DIČ)“ | **BEHOBEN** | CP850-Mojibake (Anführungszeichen „…“, „Č“) — nicht Teil der Reparatur vom 13.08. | — (erledigt, gezielt; kein Ganz-DB-Lauf) | ja (RPC 02.09.) |

**Gesamtbild Encoding:** Die CP850-Reparatur vom 13.08.2026 ist in den fachlichen Tabellen bestätigt (0 ├-Zeilen in Partner/Produkt/Lead/Auftrag/Beleg/Nachricht/Ticket). Die dokumentierten Reststellen wurden am **02.09.2026 gezielt und freigegeben** korrigiert (F1 EUR-Symbol, F7 account_payment-shortdesc, F26 drei de_DE-Übersetzungsstellen) — jeweils punktuell per Slot-Korrektur, kein Ganz-DB-Lauf. Weitere Encoding-Eingriffe nur mit Freigabe.

---

## 3. C — Währung

**Istzustand (read-only):**
- Unternehmenswährung: **EUR (id 126)** — `res_company` IT-Kommunal GmbH, Land **AT** (id 12). ✅
- Österreich-Lokalisierung installiert: `l10n_at` 18.0.3.2.1 (+ `l10n_din5008*`). ✅
- Alle 7 Journale: `currency_id = NULL` (= Unternehmenswährung EUR). ✅
- 18 Belege EUR, aber **4 Belege USD** (ids 17, 20, 21, 19). ⚠️
- **USD (id 1) ist aktiv** (`active=true`) und trägt das Symbol `$` — Relikt aus der initialen DB-Erstellung (Odoo-Basiswährung vor l10n_at-Installation). ⚠️
- **14 Verkaufsaufträge in USD** (currency_id=1), alle über Preisliste 1 „Standard-Preisliste“ (USD), erstellt 01.07.–24.07.2026 (Testdaten-Zeitraum), inkl. `A-1900011`. ⚠️
- **Preislisten:** id 1 „Standard-Preisliste“ (USD, 0 Items) **inaktiv**; id 34 „Preisliste 2026 + Valorisierung“ (EUR, 2 Items) **seit 03.09.2026 aktiv** (Session 82) — Stand korrigiert am 10.09.2026 (Session 83). ⚠️
- **EUR-Symbol in `res_currency.symbol`:** auf **beiden** Instanzen korrekt `€` (VM seit Session 81, **lokal seit 11.09.2026, Session 85**) — Odoo-Formatter liefert `65,00 €` / `1.234,56 €`, gerenderte Rechnung/Auftrag ohne Mojibake. ✅

| Bereich | Funktion/Feld | Odoo-18-Istzustand | Status | Fehler/Abweichung | notwendige Anpassung | getestet |
|---|---|---|---|---|---|---|
| Unternehmenswährung | res_company | EUR (126), Land AT | OK | — | — | ja (DB) |
| Standardwährung | res_currency aktive Währungen | EUR aktiv ✅, **USD aktiv ⚠️** | **ANPASSUNG NÖTIG** | USD aktiv ohne fachliche Nutzung (Relikt) | prüfen, ob USD deaktiviert werden soll (nach Freigabe) | ja (DB) |
| Währungssymbol | res_currency.symbol (EUR) | **beide Instanzen: `€`** (VM seit Session 81, lokal seit 11.09.2026, Session 85) | **BEHOBEN** | — | keine offen — lokal per gezieltem Einzel-Write auf `res.currency` id 126 (keine globale Ersetzung) | ja (DB + gerenderte Belege, 11.09.2026) |
| Preislisten | product_pricelist | 3 Preislisten-Sätze: EUR-PL id 34 „Preisliste 2026 + Valorisierung" **aktiv** (seit 03.09., Session 82 — als Standard für die Abo-Anlage), USD-PL id 1 „Standard-Preisliste" **weiter inaktiv** | **TEILWEISE BEHOBEN** | keine aktive Preisliste war der Auslöser des Abo-Pflichtfeld-Fehlers; „Standard-Preisliste" ist USD und bleibt inaktiv | EUR-PL aktiviert (erledigt, Session 82); USD-PL-Thematik (F2–F4) separat nach Freigabe | ja (DB, 03.09.) |
| Produkte | product.template | 23 Produkte | OFFEN | Preis-/Währungsdarstellung prüfen | — | nein |
| Angebote/Aufträge | sale.order | **14 von 16 Aufträgen USD** (über inaktive USD-Preisliste) | **FEHLER** | USD-Belege (Testdaten) — Ursache: Belegwährung folgt der Preisliste; Standard-Preisliste war USD | Ursache klären, Belege/Währung bereinigen (nach Freigabe) | ja (DB) |
| Rechnungen | account.move | 18 EUR + **4 USD** (ids 17,20,21,19) | **FEHLER** | USD-Belege vorhanden | wie oben; erst Ursache prüfen, dann bereinigen (nach Freigabe) | ja (DB) |
| Journale | account_journal | 7 Journale, alle EUR | OK | — | — | ja (DB) |
| Reports/PDFs | Währungsdarstellung € | nicht geprüft (Symbol-Mojibake zu erwarten) | OFFEN | — | Symbol-Fix vorausgesetzt | nein |

**Grundsatz (wichtig):** Kein String-Replacement `$`→`€`. Für jeden USD-Befund gilt: **zuerst technisch klären, warum** (hier: Preislisten-Währung → Belegwährung), dann gezielt korrigieren. Die USD-Belege stammen aus der Testdatenerstellung (01.–24.07.2026), als die Basiswährung noch USD war bzw. die Standard-Preisliste USD-denominiert war — fachlich sind EUR/€ vorgesehen.

---

## 4. D — Allgemeine Odoo-Basiseinstellungen

| Bereich | Odoo-18-Istzustand | Status | Fehler/Abweichung | notwendige Anpassung | getestet |
|---|---|---|---|---|---|
| Unternehmen | IT-Kommunal GmbH (id 1), Partner: Land AT, is_company | OK | — | — | ja (DB) |
| Sprache | nur de_DE aktiv; alle Benutzer de_DE | OK | en_US vorhanden aber inaktiv (ungewöhnlich, aber funktional konsistent) | ggf. en_US-Aktivierung prüfen (kein Handlungsbedarf für Fachabnahme) | ja (DB) |
| Zeitzone | **14 von 14 aktiven internen Benutzern** mit `Europe/Vienna` (gesetzt am 11.09.2026, Session 86 — uid 13–24; uid 2/8 waren bereits korrekt) | **OK** | — | keine offen | ja (DB, VM **und** lokal, 11.09.2026) |
| Land | AT (Österreich) korrekt (Unternehmen + l10n_at) | OK | — | — | ja (DB) |
| Datumsformat | de_DE: `%d.%m.%Y` | OK | — | — | ja (DB) |
| Zahlen-/Dezimaldarstellung | de_DE: Dezimal `,` / Tausender `.` | OK | — | — | ja (DB) |
| Währung | EUR als Unternehmenswährung (Befunde s. Abschnitt 3) | siehe C | — | — | ja (DB) |
| Adressdarstellung | l10n_at/l10n_din5008 installiert; Darstellung nicht einzeln geprüft | OFFEN | — | — | nein |
| URL/Proxy | web.base.url = https://k001959vsx.ipax.at | OK | — | — | ja |

---

## 5. E — Fachliche Funktionsbereiche

**Datengrundlage (read-only, 01.09.2026):** Kontrollzahlen der Testumgebung.

| Bereich | Ist-Daten | Status | Fehler/Abweichung | notwendige Anpassung | getestet |
|---|---|---|---|---|---|
| CRM | 1 Lead, 8 Stages, 4 Teams | OFFEN | — | — | nein |
| Kontakte/Firmen/Ansprechpartner | 76 Partner (12 Firmen) | OFFEN | — | — | nein |
| Verkauf | 16 Aufträge, 26 Positionen | OFFEN | USD-Belege s. Abschnitt 3 | Währungsbereinigung (nach Freigabe) | nein |
| Produkte | 23 Produkte, 2 Preislisten | OFFEN | Preislisten inaktiv/USD s. C | — | nein |
| Rechnungs-/Finanzfunktionen (soweit genutzt) | 22 Belege, 7 Journale, 7 Zahlungen | OFFEN | 4 USD-Belege s. C | — | nein |
| Helpdesk | 1 Ticket, 16 Stages, 1 Team, 37 Kategorien, 1 SLA | OFFEN | — | — | nein |
| Aktivitäten | 0 Aktivitäten, 13 Typen | OFFEN | — | — | nein |
| Anhänge/Filestore | 1260 Anhänge (1249 + 11 Asset-Regeneration nach HTTPS-Umstellung); Filestore 1:1 | OK (Stand) | Altlasten bekannt (969 store_fname referenziert vs. 14 physisch) — vorbestehend, lokal identisch | kein Handlungsbedarf ohne Freigabe | teilweise |
| Suche/Filter/Gruppierungen | nicht geprüft | OFFEN | — | — | nein |
| Berechtigungen | 18 Benutzer (14 aktiv); Rollen nicht einzeln geprüft | OFFEN | Florian/Tina-Anlage offen (separate Freigabe) | — | nein |
| Reports/PDFs | 4 ITK-Vorlagen gerendert (frühere Sessions); Umlaute/€ offen | OFFEN | €-Symbol s. C | — | nein |
| E-Mail-Funktionen | SMTP **nicht konfiguriert** (bewusst offen) | OFFEN | — | SMTP in späterer Session (Freigabe) | nein |
| itk_subscription | 5 Abos, 6 Positionen, 3 Vorlagen | OFFEN | Abo-Anlage-Fix Session 82: `pricelist_id` (Pflichtfeld) — EUR-Standardpreisliste automatisch + tote O11-Gruppe im View korrigiert; lokal 18.0.1.1.0 getestet (8/8); **VM-Code-Deploy offen (SSH)** | — | teilweise (lokal 03.09.; Browser/VM offen) |
| itk_crm | Struktur persistiert (setup_runtime, post-migration) | OFFEN | — | — | nein |
| itk_product | 6 Produkt-Typen | OFFEN | — | — | nein |
| itk_projectcategory | Tabellen vorhanden | OFFEN | **Version DB 18.0.0.1 < Repo 18.0.1.0.0** (Upgrade offen, je Freigabe) | Einzel-Upgrade (nach Freigabe) | nein |
| itk_sale_management | Angebots-Layout | OFFEN | tree→list-Upgrade offen (Session 78) | Einzel-Upgrade (nach Freigabe) | nein |
| itk_valorisierung | 1 Valorisierung | OFFEN | — | — | nein |
| itk_saleorder_lines | installiert | OFFEN | — | — | nein |
| itk_multifactor | installiert | OFFEN | — | — | nein |
| itk_base_setup | installiert | OFFEN | — | — | nein |
| itk_third_party_setup | installiert | OFFEN | — | — | nein |
| itk_reports | 4 Druckvorlagen | OFFEN | tree→list-Upgrade offen (Session 78) | Einzel-Upgrade (nach Freigabe) | nein |
| itk_automated_actions | installiert | OFFEN | — | — | nein |
| itk_translation | ITK-Menü/-Views | OFFEN | tree→list-Upgrade offen (Session 78) | Einzel-Upgrade (nach Freigabe) | nein |
| itk_helpdesk_category_user | Kategorie-Follower (m2m) | OFFEN | — | — | nein |
| itk_helpdesk_compat | O11-Helpdesk-Oberfläche (9 Menüs, 2-stufige Kategorien, Prioritäten) | OFFEN | — | — | nein |
| helpdesk_mgmt (+project/sla/timesheet) | 1 Ticket, 16 Stages, 1 Team, 37 Kategorien, 1 SLA | OFFEN | — | — | nein |
| project_timesheet_time_control | installiert | OFFEN | — | — | nein |
| server_action_mass_edit | installiert (20 Aktionen aus O11 migriert) | OFFEN | — | — | nein |

---

## 6. Odoo 11 → Odoo 18 Mapping (in Bearbeitung — bereichsweise)

> **Referenz seit 15.09.2026 (Session 92):** produktives Odoo 11 mit **ausschließlich lesendem** Zugriff (`https://portal.it-kommunal.at`)
> sowie der lokale Produktiv-Dump `ITK_V1_a` (03.09.2026, `Desktop\Odoo_DB_Dump_2026_09_03`, identische Kopie in `Nextcloud`, PostgreSQL 10.23/Ubuntu 18.04).
> Der Feld-/Strukturvergleich läuft **bereichsweise**; dieser Abschnitt wird fortlaufend gefüllt.
>
> **Wichtig — nur Struktur, keine Daten:** In dieser Phase wird ausschließlich die **Odoo-18-Struktur** migrationsbereit gemacht.
> Es werden **keine** Odoo-11-Produktivdaten, **keine** Tags und **keine** Zuordnungen übernommen. Die Datenmigration folgt erst,
> wenn alle Bereiche in Odoo 18 angepasst und getestet sind.


**Erfassungsschema:**

| Odoo-11-Modell/Feld | Odoo-18-Zielfeld | Datentyp | Pflichtfeld | Auswahlwerte | Relation | Transformations-/Migrationsregel |
|---|---|---|---|---|---|---|
| *siehe 6.1 ff. (bereichsweise befüllt)* | | | | | | |

### 6.6 Kontakte → Kontaktformular → Tab „Interne Notizen“ — **ABGESCHLOSSEN** (VM-verifiziert), 15.09.2026 (Sessions 102/103/104)

**Umgesetzt (`itk_base_setup` 18.0.1.2.0):** Abschnittstitel „Alarmierung bei Auftrag“ (sale) und „Warnung beim Einkaufsauftrag“
(purchase) im Odoo-11-Wortlaut; Platzhalter des Notizfelds „Interner Hinweis ...“. Die Einkaufs-Warnung ist über die
Odoo-18-Einstellung `purchase.group_warning_purchase` („Warnungen“ im Einkauf) sichtbar gemacht — auf lokal und VM aktiviert.

**Feldlage:** `comment` (O18 HTML statt Text — moderne Technik bleibt), `sale_warn`, `invoice_warn`, `purchase_warn` vorhanden;
`picking_warn` (O11 „Warnung beim Kommissionieren“) **existiert in Odoo 18 nicht mehr** → kein Nachbau.
Auswahlwerte identisch (Keine Nachricht / Warnung / Blockierende Meldung).
**Verifikation:** VM-Browser, Kontakt 69, Tab „Interne Notizen“ (Screenshot `13_VM_InterneNotizen.png`), Werkzeug
`scripts/verify_s102_interne_notizen.py`; Modulversion 18.0.1.2.0 auf der VM; keine Datenänderung.
**picking_warn (Session 103, read-only in Odoo 11 Prod ausgewertet):** 5.842 Kontakte, davon **0** mit gesetztem Wert
(`picking_warn = 'no-message'` bei allen) und **0** mit individuellem Warntext → **keine Daten zu migrieren**. Auch
`sale_warn`/`invoice_warn`/`purchase_warn` sind in Odoo 11 bei 0 Kontakten aktiv. Odoo 18 hat diese drei Felder plus
linienbezogene Produktwarnungen; ein Partnerfeld für die Kommissionierung existiert nicht mehr.
**Empfehlung: kein eigenes Feld** (Entscheidung bei Anna).
**Einkaufs-Warnungen bleiben aktiv** (Anweisung Anna, `purchase.group_warning_purchase` auf lokal und VM).
**Dokument:** `docs/o11-o18-strukturvergleich-kontakt-interne-notizen.md`.

**Abschluss/Endstand (Session 104, verifiziert über HTTPS gegen die VM):**
- `itk_base_setup` **18.0.1.2.0** installiert, `latest_version` identisch → kein offenes Upgrade
- Einkaufs-Warn-Einstellung aktiv; gerenderter Arch: Platzhalter „Interner Hinweis ...“, Abschnitte „Alarmierung bei Auftrag“,
  „Warnung zu Rechnung“, „Warnung beim Einkaufsauftrag“ (Felder `comment`, `sale_warn`, `invoice_warn`, `purchase_warn`)
- Browser-Prüfung Tab „Interne Notizen“ auf der VM: alle drei Abschnitte sichtbar (`13_VM_InterneNotizen.png`)
- 0 von 41 Repo-Modulen mit Versionsabweichung; Kontrollzahlen unverändert (70 Kontakte), keine Datenänderung
- VM-Repo von Anna auf final main nachgezogen

**Empfehlung zu `picking_warn` offen bei Anna** (kein eigenes Feld nötig, da 0 Datensätze); Feld ist **nicht** als entfallen
festgeschrieben, sondern als „strukturell vorhanden, Datenbestand 0“ dokumentiert.

### 6.7 Kontakte → Kontaktformular → Tab „Verkauf & Einkauf“ — **ABGESCHLOSSEN, MIGRATIONSBEREIT**, 15.09.2026 (Sessions 105/106)

Feld-Mapping Odoo 11 → Odoo 18 vollständig dokumentiert in `docs/o11-o18-strukturvergleich-kontakt-verkauf-einkauf.md`
(23 Felder mit Bedeutung, Zielfeld, Typ, 1:1, Transformation, entfällt, neu).

**Kein optischer Rückbau** (Anweisung Anna): Odoo 18 ist im Tab vollständiger als Odoo 11 (Zahlungsbedingungen,
Zahlungsmethoden, Steuerposition, Käufer, Eingangserinnerung) — Tab unverändert gelassen.

**Bereits korrekt vorhanden:** `is_customer`/`is_supplier` als compute+inverse auf `customer_rank`/`supplier_rank`
(häkchengesteuerte Odoo-18-Logik, lokal + VM verifiziert). `multi_factor` und `ref` passen 1:1.

**Behobener GAP:** beide Odoo-18-Preislisten waren inaktiv → EUR-Preisliste „Preisliste 2026 + Valorisierung" auf
lokal und VM aktiviert (reversibel, keine Datensatzänderung).

**Offen (Datenentscheidungen, KLÄRUNG NÖTIG):** 1) Preislisten-Zuordnung (50 vs. 2; keine der verwendeten O11-Preislisten
existiert in O18; O18-Standard-Preisliste ist USD) · 2) 46 von 61 O11-Benutzern fehlen in O18 → 4.397 Verkäufer-Beziehungen
· 3) Steuerpositionen 5 vs. 4 Namen (1 Kontakt) · 4) `opt_out` 22 Kontakte → Marketing-Abos · 5) `ref`-Beschriftung.

**Nachweis:** `scripts/verify_s105_verkauf_einkauf.py` → lokal 50 OK / 0 FEHL, VM 50 OK / 0 FEHL.

**Abschluss Session 106 (Entscheidungen von Anna, verbindliche Vorgaben für die Datenmigration):**

- **Beschriftung umgesetzt:** `ref` heißt jetzt „Interne Referenz“ wie in Odoo 11 (Modellbeschriftung in
  `itk_base_setup` 18.0.1.2.1, Formular-XPath im Tab, deutsche Übersetzung in beiden Datenbanken). Feld und Inhalte unverändert;
  „GKZ“ im Kenndatenblock und in der Liste bleibt.
- **Preislisten:** jetzt nichts anlegen. Vor der Kontakt-/Verkaufsdatenmigration müssen die tatsächlich verwendeten
  Odoo-11-Preislisten (Public Pricelist 2.576, GSZ Kärnten 206, GemDat OÖ 165, GemDat NÖ 53) angelegt bzw. gemappt sein
  (Zuordnungstabelle O11-ID → O18-ID). Ohne Zuordnung darf `property_product_pricelist` nicht geschrieben werden.
  Die aktivierte EUR-Preisliste bleibt aktiv.
- **Benutzer/Verkäufer:** jetzt keine Benutzer anlegen. Strategie: vorhandene aktive Odoo-18-Benutzer 1:1 zuordnen;
  ausgeschiedene Odoo-11-Benutzer deaktiviert anlegen (`active = False`, ohne Passwort) und als historische Verkäuferbeziehung
  erhalten; fachlich unklare Benutzer später einzeln entscheiden. (4.397 Kontakte betroffen, 46 fehlende Benutzer.)
- **Steuerpositionen:** jetzt nichts anlegen. Vor der Migration die fünf Odoo-11-Steuerpositionen den Odoo-18-Positionen
  zuordnen bzw. fehlende Stammdaten vorbereiten; endgültige Zuordnung über die Buchhaltung bestätigen (1 Kontakt betroffen).
- **opt_out:** kein Nachbau. Vor der Migration die 22 Kontakte in die Odoo-18-Marketing-/Blacklist-Logik überführen
  (`mail.blacklist` bzw. `mailing.subscription.opt_out` mit `opt_out_datetime`).

**Nachweis final (Session 107, gegen die VM geprüft):** `scripts/verify_s105_verkauf_einkauf.py` → lokal 50 OK / 0 FEHL,
VM 50 OK / 0 FEHL; `itk_base_setup` 18.0.1.2.1 auf der VM installiert; gerenderter Arch zeigt im Tab „Interne Referenz“,
im Kenndatenblock/Kontaktliste weiterhin „GKZ“; Browser-Prüfung auf der VM bestätigt (kein alleinstehendes
„Referenz“); 70 Kontakte unverändert. **Bereich abgeschlossen.**

### 6.8 Kontakte → Kontaktformular → Tab „Abrechnung“ — **MIGRATIONSBEREIT (Struktur)**, 15.09.2026 (Session 108)

Feld-Mapping dokumentiert in `docs/o11-o18-strukturvergleich-kontakt-abrechnung.md` (23 Felder mit Bedeutung, Zielfeld,
Typ, Zuordnung; zusätzlich Liste der in andere Reiter verschobenen Felder).

**Kein optischer Rückbau** (Anweisung Anna): Der Odoo-18-Tab ist deutlich vollständiger als in Odoo 11 (Bankkonten
voll pflegbar, Rechnungsversand, E-Rechnungsformat, Peppol/VOKZ, Kreditlimits, Automatisierung der Rechnungsbuchung).
Tab unverändert gelassen; **keine strukturelle Lücke** gefunden.

**Verschobene Felder (kein Informationsverlust):** `property_payment_term_id`, `property_supplier_payment_term_id` und
`property_account_position_id` liegen in Odoo 18 im Reiter „Verkauf & Einkauf“ (in Odoo 11 „Abrechnung“);
`bank_ids` liegt in Odoo 18 im Reiter „Abrechnung“ (in Odoo 11 „Verkauf & Einkauf“, nur als Statistik-Knopf).
`property_stock_customer`/`property_stock_supplier` entfallen in Odoo 18 (Funktion über Lager/Routen).

**VOKZ geklärt:** VOKZ ist die österreichische Peppol-Kennung — in Odoo 18 `peppol_eas` = 9915 „VOKZ für Österreich“
mit dem Wert in `peppol_endpoint`. In Odoo 11 Prod existiert kein VOKZ-Feld (0 Treffer in Feldern, Beschreibungen,
Freitexten und Berichtsvorlagen) → nichts zu migrieren; Werte wären für den Peppol-Versand neu zu erheben.

**Offen (Stammdaten-/Verfahrensentscheidungen):** 1) Format der elektronischen Rechnung (Odoo 18 bietet UBL/CII-Formate
wie Peppol BIS 3; **kein ebInterface** im Standard — Entscheidung mit ITK) 2) Peppol-Registrierung/VOKZ-Erhebung
3) Zuordnung der fünf Odoo-11-Steuerpositionen 4) Bestätigung der Odoo-18-Kontenstandardwerte 5) Kreditlimits-Funktion
6) Standardwert für den Rechnungsversand.

**Nachweis:** `scripts/verify_s108_abrechnung.py` → lokal 44 OK / 0 FEHL, VM 44 OK / 0 FEHL; Browser-Prüfung des Reiters
auf der VM (Screenshot `16_VM_Abrechnung.png`).

### 6.9 Kontakte → Kontaktformular → Tab „Gemeinde-Information“ — **ABGESCHLOSSEN, MIGRATIONSBEREIT**, 15.09.2026 (Sessions 109/110)

Feld-Mapping dokumentiert in `docs/o11-o18-strukturvergleich-kontakt-gemeinde-information.md`.

**Feldbestand identisch:** In beiden Systemen dieselben fünf Felder im Reiter (`population` Einwohnerzahl,
`community_magnitude` Größenklasse, `population_update` Stand vom, `status_of_community` Organisationstyp,
`member_of_city_alliance` Städtebund-Mitglied), gleiche Gruppierung, gleiche Regel „nur Unternehmen“, keine Pflichtfelder,
gleiche Typen und Relationen. Nichts entfällt, nichts ist neu.

**Speicherung in Odoo 11 Prod:** normale Felder des Moduls `itk_crm` auf `res.partner` (keine x_-Felder, kein eigenes
Modell); `status_of_community` → many2one auf `itk_crm.statusofcommunity`; `community_magnitude` (char) und
`community_magnitude_id` (many2one) sind **berechnet** aus `population` und müssen nicht migriert werden.

**Behoben (Session 109, `itk_crm` 18.0.1.5.1):** Modellbeschriftungen standen in Odoo 18 englisch bzw. abweichend
(Magnitude, Status of Community, Member of City Alliance, Community Magnitude, Einwohnerzahl aktualisiert am,
Salutation of Community) → auf die Odoo-11-Wortlaute gesetzt (Größenklasse, Organisationstyp, Städtebund-Mitglied,
Einwohnerzahl, Stand vom, Organisationsbezeichnung). Wirkung auch in Suche, Filter und Export.

**Vorgabe für die Datenmigration:** Organisationstyp-Stammdaten in Odoo 18 unvollständig (nur „Marktgemeinde“);
die Odoo-11-Werte Marktgemeinde (768), Gemeinde (1.122), Stadtgemeinde (188), Magistrat (13), Magistrat der Stadt (2)
und Gemeindeverband bzw. „-“ (jeweils 0) sind vorher anzulegen bzw. zuzuordnen — sonst sind 2.093 Kontakte nicht zuordenbar.

**Nachweis:** `scripts/verify_s109_gemeinde_info.py` (read-only) prüft Felder, Beschriftungen, Reiter-Arch, is_company-Regel,
Stammdaten (inklusive Mapping über den Code) und die Größenklassen-Berechnung; lokal **45 OK / 0 FEHL**.
**Nachweis (Session 110/111, gegen die VM geprüft):** `itk_crm` 18.0.1.5.1 und `itk_base_setup` 18.0.1.2.2 auf der VM
installiert; alle 7 Modellbeschriftungen auf dem Odoo-11-Wortlaut; 6 Organisationstypen mit korrekten Codes (Mapping
geprüft); Browser-Messung im echten Chrome: Feld **256 px** statt 26 px, kein Abschneiden (längster Wert
„Magistrat der Stadt“ 119 px); Browser-Prüfung Kontakt 72 mit Screenshot; 70 Kontakte unverändert.
**Bereich abgeschlossen.**

**Session 110 — Organisationstypen als Ziel-Stammdaten vorbereitet (auf Anweisung von Anna):**
Read-only verifizierter Odoo-11-Bestand (7 Datensätze, 2.093 zugeordnete Kontakte). In Odoo 18 angelegt bzw. ergänzt,
idempotent auf lokal und VM, **ohne** Kontakte umzustellen und **ohne** Odoo-11-Zuordnungen zu übernehmen:
Marktgemeinde (Code M, vorhanden — Code ergänzt), Gemeinde (G), Stadtgemeinde (ST), Magistrat (SR),
Magistrat der Stadt (MAG), Gemeindeverband (GV). Der Platzhalter „-“ (0 Kontakte) wurde bewusst nicht angelegt.
Mapping-Schlüssel ist der **Code**, nicht die ID. Hinweis: „Magistrat“ (13 Kontakte) fehlte in der Aufstellung, wird aber
produktiv verwendet und wurde mit angelegt.

**Session 110 — Anzeige korrigiert:** Der Organisationstyp war im Browser abgeschnitten (Feldbreite 26 px bei 118 px
Textbedarf). Ursache: die Gruppe „Andere“ war doppelt verschachtelt und hatte nur ein Viertel der Reiterbreite.
Korrektur in `itk_base_setup` 18.0.1.2.2: `colspan="2"` auf der Gruppe „Andere“ und auf dem Feld
`status_of_community` — gezielt in dieser View, keine globale UI-Änderung. Nachher: Feldbreite 256 px, längster Wert
„Magistrat der Stadt“ (119 px) vollständig lesbar.

### 6.5 Kontakte → Adressblock / Adresstypen — MIGRATIONSBEREIT (abgeschlossen), 15.09.2026 (Session 101)

**Entscheidung von Anna: der Vergleich der Adressmaske passt funktional — kein Odoo-11-Nachbau.**

| Punkt | Entscheidung | Umsetzung |
|---|---|---|
| Lieferadresse (O18) vs. Zustellungsadresse (O11) | fachlich gleichwertig | keine |
| Privatadresse (O11) | nicht nachbauen (O11: 0 Datensätze; O18 hat eigene moderne Logik) | keine |
| „Adressart“/„Adresstyp“, „Verbundenes“/„Zugehöriges Unternehmen“ | funktional identisch | keine |
| übrige Adresstypen und Adressfelder | funktional vorhanden | keine |

**Status MIGRATIONSBEREIT.** Keine Code-Änderungen nötig. Dokument:
`docs/o11-o18-strukturvergleich-kontakte-personen-firmen.md` (Abschnitt 6).

### 6.4 Kontakte → Firmen/Personen-Logik und Ansprechpartner — UMGESETZT (Struktur), 15.09.2026 (Session 100)

Vergleich Odoo 11 Prod ↔ Odoo 18 (lokal + VM), Vergleichspaar Breitenbrunn (O11 5794 ↔ O18 72).

**Umgesetzt (`itk_base_setup` 18.0.1.1.0):** Im Tab „Kontakte & Adressen“ wird ein neu angelegter Ansprechpartner wieder
als **Kontakt** angelegt. Odoo 18 setzt im `child_ids`-Kontext `default_type: 'other'` (Andere Adresse), Odoo 11 setzt keinen
Typ → Feldstandard `contact`. Nachweis: `default_get(['type'])` mit Tab-Kontext → `contact` (lokal und VM).

**Gleich in beiden Systemen:** Firmen/Personen-Radio (`company_type`), `parent_id`-Domain (nur Unternehmen), Karten im Tab
(Name, Funktion, E-Mail, PLZ/Ort, Bundesland, Land, Telefon, Mobil).
**Kein Nachbau nötig:** Adresstyp „Privatadresse“ (Odoo 11: 0 Datensätze; Odoo 18 nutzt einen eigenen Datensatztyp).
**KLÄRUNG NÖTIG:** Wortlaute „Adressart“/„Adresstyp“, „Verbundenes“/„Zugehöriges Unternehmen“, „Zustellungsadresse“/„Lieferadresse“.
**Verifikation:** VM-Render des Tabs (`12_VM_Ansprechpartner_*`), Modulversion 18.0.1.1.0 auf der VM, keine Datenänderung.
**Dokument:** `docs/o11-o18-strukturvergleich-kontakte-personen-firmen.md`.

### 6.3 Kontakte → geöffnetes Kontaktformular / Detailansicht — UMGESETZT (Struktur), 15.09.2026 (Session 94)

Vergleich: 64 gemeinsame Formularfelder, 19 abweichende Beschriftungen; Kenndaten-Bereich, Tabs und Smart Buttons geprüft.

**Umgesetzt** (`itk_base_setup` 18.0.1.0.3, nur Ansichten/Übersetzungen):
- `title` → **„Titel“** (O18 „Anrede“, kollidierte mit `salutation`) · `street2` → **„Straße 2“** (O18-Tippfehler „Straße2“)
  · `child_ids` → **„Kontakte“** (O18 „Kontakt“) · `user_id` → **„Verkäufer“** in beiden Vorkommen (Tab „Verkauf & Einkauf“ zeigte „Vertriebsmitarbeiter“)
- `i18n/de.po` (dauerhafte Repo-Quelle) + gezielte Overwrite-Ladung auf beiden Instanzen für die Feld-Metadaten
- View-Prioritäten auf 90/91 angehoben, damit die Labels nach allen anderen Modul-Views greifen

**Bewusst Odoo-18-Technik beibehalten:** `customer_rank`/`is_customer`/„supplier_rank“ statt `customer`/`supplier`; `image_1920`;
`sale_warn` statt `picking_warn`; Konten in Gruppe „Buchungen“; `purchase_warn` über die O18-Einstellung; Archivieren statt `toggle_active`;
Tab „Rechnungsstellung“.

**Status:** lokal und VM verifiziert (`scripts/verify_s94_contact_form.py`: je **28/28 OK**), Kontrollzahlen unverändert. **Keine Daten übernommen.**

**Layout-Abgleich im echten Browser (Session 95, `itk_base_setup` 18.0.1.0.5):**
- Werkzeug `scripts/browser_form_layout.py` rendert die geöffnete Detailansicht (Chromium/Playwright) und liest sichtbare
  Labels mit Position, Tabs und Smart Buttons aus; Referenz-Vergleich Odoo 11 Prod Kontakt 5792 ↔ Odoo 18 Kontakt 69.
- Umgesetzt: **Tab-Reihenfolge** wie Odoo 11 (Interne Notizen 2.), **Kenndaten-Spalten** wie Odoo 11
  (links GKZ/Thsd/Lieferant/Kunde, rechts Verkäufer/zu Handen/Organisationsbezeichnung/Status), **Smart-Button-Reihenfolge**
  (Verkaufschancen, Verkauf, Meetings), `multi_factor`-Label repo-durable.
- Ergebnis: Browser-Render **lokal = VM** identisch, Screenshots `Desktop\Odoo18-Layoutvergleich-Session95\`,
  Doku `docs/o11-o18-kontaktformular-layoutvergleich.md`.
- Offen (KLÄRUNG): Kostenstellenkonten/Website-Veröffentlichung/Aktiv-Button (nicht migrierte O11-Module bzw. Odoo-18-Standardbedienung),
  zweiter "Abrechnung"-Tab (= Odoo-18-Seite `accounting_disabled` nur für Benutzer ohne Buchhaltungsrechte), `vat` "USt" vs. "UID".
**Session 98 — Nachbesserung (Bereich war zu früh als abgenommen bezeichnet):**
- `is_supplier`/`is_customer` hatten fälschlich `invisible="not is_company"` (Odoo 11 hat dort keine Bedingung) → behoben.
- Titel/akademische Titel stehen jetzt in einer eigenen Gruppe unterhalb des Adressblocks; die Gruppe ist bei Firmen
  selbst ausgeblendet.
- Ursache der fehlenden Felder bei Kontakt 79: der Datensatz war ein Personendatensatz (firmenbezogene Kenndaten sind bei
  Personen in beiden Systemen unsichtbar); auf der VM ist er seit 15.09. 12:07 als Unternehmen geführt.
- Auf der VM verifiziert (`browser_form_layout.py --instanz vm --partner 79`), Screenshots `10_VM_Kontakt79_FINAL_*`.
- Offen (KLÄRUNG): Sollen GKZ/Thsd/Organisationsbezeichnung auch bei Personen sichtbar sein?

**Session 96 — View-Kette und sichtbares Layout (nur so ist es wirklich erledigt):**
- Die Formular-View hing an der **Erweiterungs-View** `itk_crm` (prio 16) und wurde deshalb früh angewendet; spätere Views
  (akademische Titel 2340, Website 3598, Karte 3647, `view_partner_form` 3694, Multifactor 2285, Firstname 2329/2330) liefen danach
  darüber und deckten Änderungen zu → `inherit_id` jetzt **`base.view_partner_form`** (Wurzel) + `priority 90`.
- `position="move"`-Platzhalter: keine übersetzbaren Attribute als Selektor (`placeholder`, `string`, `title` …) → ParseError.
- Sichtbare Anordnung jetzt: Kenndaten links GKZ/Thsd/zu Handen/Organisationsbezeichnung, rechts Verkäufer/Lieferant/Kunde/Status;
  Adressblock links Adresse/UID/Stichwörter, rechts Telefon/Mobil/E-Mail/Website/Sprache; Titel/akademische Titel am Blockende.
- `vat`-Label „UID“ über `scripts/set_country_vat_label_de.py` (Basisdaten `res.country` AT; dokumentiert, `--revert` vorhanden).
- Verifikation im echten Browser: **lokal = VM identisch** (Tabs, Buttons, Feldreihenfolge mit Spaltenzuordnung);
  `verify_s94`: je 28/28 OK. Screenshots `Desktop\Odoo18-Layoutvergleich-Session95\5_/6_...`.

- **Regel für alle weiteren Bereiche: "vorhanden" ≠ "erledigt"** — je Punkt sichtbar? richtige Position? gleiche fachliche Funktion? gleiche Bedienlogik?
**KLÄRUNG NÖTIG:** `vat`-Label (O11 „UID“ vs. O18 „USt“, aus Basisdaten — Option: `res.country` AT `vat_label`);
`ref` „Referenz“ vs. „Interne Referenz“; Wortlaute (Einkäufe/Einkauf, Lieferantenrechnungen/Eingangsrechnungen, Zahlungstoken/Kreditkarte(n),
Bank/Bankkonten, Zahlungsbedingungen); Website-Veröffentlichung; `opt_out`; Buttons nicht migrierter O11-Module (Reklamation, Events,
Kostenstellenkonten). Details: PROJECT_KNOWLEDGE.md Session 94.
### 6.2 Kontakte → Kontaktformular / Kontaktliste — UMGESETZT (Struktur), 15.09.2026 (Session 93)

Vergleichsbasis: produktives Odoo 11 (Formular `fields_view_get`, Liste `res.partner.tree` + `itk_crm.view_partner_itk_tree`,
Suche `base.view_res_partner_filter` + Erweiterungen) gegen Odoo 18 lokal und VM.

**Umgesetzt** (Modul `itk_base_setup` 18.0.1.0.1, nur Ansichten — keine Daten):
- **Liste:** O11-Spalten ergänzt, die in O18 fehlten — `function`, `is_company`, `parent_id`, `salutation`, `active` (jeweils `optional="show"`);
  `category_id` (Stichwörter) wieder sichtbar; zweite Namensspalte `display_name` auf `optional="hide"` (O18 nutzt `complete_name`).
- **Suche:** Filter **„Meine Partner“** `[('user_id','=',uid)]` und **„Meine Aktivitäten“** `[('activity_ids.user_id','=',uid)]` aus Odoo 11 übernommen;
  alle O18-Filter/Gruppierungen unverändert.
- **Formular:** nichts zu ändern — die O11-Bestandteile sind in O18 vorhanden, nur teils moderner gelöst:
  Chatter via `<chatter/>`, `image_1920`/`avatar_128`, `customer_rank`/`is_customer`, `sale_warn` (ex `picking_warn`),
  `purchase_warn` (Gruppen-/Einstellungsgesteuert), Debitoren-/Kreditorenkonto in Gruppe „Buchungen“ (`account.group_account_readonly`).

**Status:** lokal und auf der VM umgesetzt und verifiziert (`scripts/verify_s93_contact_views.py`: **je 40/40 OK**;
Kontrollzahlen unverändert). **KLÄRUNG NÖTIG:** `opt_out`/Versandbereitschaft, Website-Veröffentlichung am Kontakt,
Wortlaute „Einkäufe“/„Lieferantenrechnungen“, Tab „Rechnungsstellung“, O11-Smart-Buttons ohne O18-Modul
(Reklamation, Events, Kostenstellenkonten, SLA, STP). Details: PROJECT_KNOWLEDGE.md Session 93.
### 6.1 Kontakte → Kontakt-Tags (`res.partner.category`) — STRUKTUR BEREIT (leer, lokal getestet)

Vollständiger Struktur-/Funktionsvergleich (Felder, Ansichten, Hierarchie, „Anzeigename"):
**`docs/o11-o18-strukturvergleich-kontakt-tags.md`**

| Odoo-11 (Prod) | Odoo-18-Ziel | Typ | Pflicht | Relation | Migrationsregel |
|---|---|---|---|---|---|
| `res.partner.category.name` | `name` | char (O18: `translate=True`/jsonb) | ja | – | Namen mit `lang=de_DE` schreiben (sonst falscher Sprachslot) |
| `parent_id` (Hierarchie) | `parent_id` | many2one | nein | res.partner.category | Eltern vor Kindern importieren |
| `parent_left`/`parent_right` (Nested-Set) | `parent_path` (Odoo 18 führt ihn selbst) | char | – | – | **nicht** migrieren |
| `x_tag_anzeigename2` („Tag Anzeigename", Studio) | `display_name` (berechnet: voller Pfad) | char, nicht gespeichert | – | – | **nicht** migrieren (redundant/fehlerhaft, z. B. „False" in id 152) |
| `color` | `color` | integer | nein | – | O11 durchgehend 0; O18-Default zufällig 1–11 |
| `active` | `active` | boolean | nein | – | 1:1 |
| `partner_ids` | `partner_ids` | many2many | nein | res.partner | Zuordnungen **erst** in der Datenmigration (O11: 5.307) |
| `res.partner.category_id` (am Kontakt) | `category_id` | many2many | nein | res.partner.category | unverändert — in O11/O18 identisch konfiguriert, Label „Stichwörter" |

**Umgesetzte Odoo-18-Struktur** (Modul `itk_partner_category` 18.0.1.0.0):

- **Liste:** Spalte „Anzeigename" (voller Hierarchiepfad), Spalte „ID", Spalte „Tag Anzeigename"; Kategorie und Farbe technisch erhalten, aber `optional="hide"`.
- **Formular:** Tag Anzeigename, Anzeigename (Pfad) **read-only**, Oberkategorie, untergeordnete Kategorien (Übersicht), Aktiv, Farbe.
- **Suche:** Hierarchiesuche über `parent_id` (`child_of`) sowie Filter Hauptkategorien / Unterkategorien / Verwendete Tags / Unverwendete Tags / Mit Unterkategorien / Ohne Unterkategorien.
- **Bewusst nicht gebaut:** `x_tag_anzeigename2`, `parent_left`/`parent_right`, jegliche Datenübernahme.

**Status:** lokal **und auf der VM** installiert und verifiziert (`scripts/verify_s92_partner_category.py` — je **36/36 OK**, inkl. Hierarchie-Test mit temporärem
Eltern-/Kind-Paar und anschließender Löschung; Tag-Anzahl unverändert 15 → 15). **Keine Daten übernommen.**
VM-Nachzug und Abschluss dokumentiert in PROJECT_KNOWLEDGE.md (Session 92); lokal = GitHub = VM auf `64e6203` (VM-Tag-Anzahl nach Test unverändert 15, VM-Log ohne modulbedingte Fehler).


---

## 7. Testreihenfolge (Aufgabe 4) — Vorschlag

Reihenfolge mit Priorität (fachlich motiviert: erst Darstellung/Sprache, dann Stammdaten, dann Geschäftsdaten, dann Ausgabe/Infrastruktur):

1. **Deutsch / Sprache** (Abschnitt 1) — Menü für Menü, Sicht je Benutzerrolle
2. **EUR / Währung** (Abschnitt 3) — nach Klärung der USD-Befunde
3. **Umlaute und Sonderzeichen** (Abschnitt 2) — inkl. Suche/Filter, Anhänge, PDFs
4. **Allgemeine Grundeinstellungen** (Abschnitt 4) — inkl. Zeitzone
5. **CRM** — Leads/Opportunities, Stages, Teams, Aktivitäten, „Neue Aktivität“-Wizard
6. **Kontakte** — Firmen/Personen, Ansprechpartner, Titel, GKZ/Status/Community (itk_translation/itk_crm-Felder)
7. **Verkauf / Produkte** — Angebote, Aufträge, Positionen, Preislisten (EUR!), Produkte, Valorisierung
8. **Helpdesk** — Tickets, Kategorien (2-stufig), Prioritäten, SLA, Zeiterfassung, Kategorie-Follower
9. **unsere itk_*-Module** — je Modul einzeln (Tabelle 0.1), inkl. Abos (itk_subscription), Druckvorlagen (itk_reports)
10. **relevante OCA-Module** — helpdesk_mgmt*, project_timesheet_time_control, server_action_mass_edit
11. **Anhänge / Filestore** — Upload/Download, Umlaute in Dateinamen, Bilder
12. **Reports / PDFs** — alle 4 ITK-Vorlagen + Standard (Angebot, Auftrag, Rechnung) mit Umlauten und €
13. **Berechtigungen** — Rollen je Benutzergruppe, Record Rules, Sichtbarkeit
14. **E-Mail-Konfiguration und E-Mail-Versand** — erst in einer späteren Phase (SMTP-Setup mit Freigabe)
15. **Abschließender Migration-Readiness-Check** — Zusammenfassung aller Statusfelder dieser Checkliste → Entscheidung „ready for O11-Migration“

**Vorgehen je Punkt:** Sollwert festlegen → testen (VM, https://k001959vsx.ipax.at) → Istwert + Befund dokumentieren → Status setzen. Nur dokumentieren, nichts eigenmächtig ändern.

---

## 8. Befundliste — erste Auffälligkeiten (01.09.2026, nur dokumentiert, nichts geändert)

| # | Bereich | Befund | Nachweis (read-only) | Status |
|---|---|---|---|---|
| F1 | C/Währung | EUR-Symbol in `res_currency.symbol` war `Ôé¼` statt `€` (CP850-Mojibake); weitere Symbole betroffen (nicht installiert/inaktiv) | res_currency id 126 auf **beiden** Instanzen | **BEHOBEN (vollständig)** — VM 02.09. (Session 81), **lokal 11.09.2026 (Session 85): `symbol = €`**; Odoo-Formatter liefert `65,00 €`/`1.234,56 €`, gerenderte Rechnung/Auftrag 0× Mojibake |
| F2 | C/Währung | USD (id 1) aktiv — Relikt aus initialer DB-Erstellung (Basiswährung vor l10n_at) | res_currency id 1 (auf beiden Instanzen `active=true`, Symbol `$`, rate 1.0 — bestätigt 10.09., Session 83) | ANPASSUNG NÖTIG (separate Währungs-Abnahme, unverändert) |
| F3 | C/Währung | 14 Verkaufsaufträge (inkl. A-1900011) in USD über inaktive USD-Preisliste 1 „Standard-Preisliste“ (Testdaten 01.–24.07.2026) | sale_order currency_id=1, pricelist_id=1 | FEHLER |
| F4 | C/Währung | 4 Rechnungen (account_move ids 17,20,21,19) in USD | account_move currency_id=1 | FEHLER |
| F5 | C/Währung | Beide Preislisten inaktiv (id 1 USD, id 34 EUR mit 2 Items); keine aktive Preisliste | product_pricelist | **TEILWEISE BEHOBEN** (03.09., Session 82: EUR-PL id 34 aktiviert — Standard für Abo-Anlage; USD-PL id 1 weiter inaktiv, Rest separat) |
| F6 | A/Sprache | 12 von 15 itk-Modulen + alle 6 OCA-Module ohne deutschen Namen in der Apps-Liste | ir_module_module.shortdesc | **BEHOBEN für die ITK-Module (lokal + VM)** — 14 Manifest-Namen deutsch (z. B. „ITK CRM-Erweiterung", „ITK Druckvorlagen", „ITK Helpdesk-Oberfläche"; `itk_subscription` war bereits „ITK Abo-Management") — **OCA-Modulnamen offen** (stammen aus OCA-Manifesten, Entscheidung Anna) |
| F7 | A/Sprache | `account_payment` de_DE-shortdesc „Zahlung ÔÇô Konto“ (CP850-Mojibake) — einziges betroffenes **installiertes** Modul; 14 weitere betroffene Module nicht installiert | ir_module_module.shortdesc | **BEHOBEN** (02.09., Session 81) |
| F8 | D/Basiseinstellungen | Zeitzone fehlte bei 12 von 14 aktiven internen Benutzern (nur uid 2, 8 hatten `Europe/Vienna`) | res_users/res_partner (11.09.2026, Session 86) | **BEHOBEN** — **alle 14 aktiven internen Benutzer** haben `Europe/Vienna` (**VM und lokal**); gesetzt für uid 13–24, uid 2/8 waren korrekt; technische Konten 1/3/4/5 unberührt; keine Löschung/Archivierung (Christiane Breit unverändert aktiv) |
| F9 | A/Sprache | Nur de_DE aktiv; en_US vorhanden aber inaktiv; 91 res_lang-Zeilen mit `active IS NULL` (Altlast) | res_lang | Hinweis |
| F10 | Inventar | `web_group_expand` installiert, obwohl als „geparkt“ dokumentiert (Doku-Inkonsistenz; Code funktioniert) | ir_module_module vs. README | Hinweis |
| F11 | Inventar | `itk_projectcategory`: installierte Version ist **18.0.1.0.0 = Repo-Version** auf beiden Instanzen; die DB-Spalte `latest_version` (18.0.0.1) ist nur ein **veralteter Cache-Wert** von vor dem Modul-Upgrade | ir.module.module (geprüft 10.09.2026, Session 83) vs. `__manifest__.py` | **GEPRÜFT/OK** — kein Upgrade offen |
| F12 | Inventar | Ausstehende Einzel-Upgrades (tree→list) — geprüft 10.09.2026 (Session 83): `itk_reports`, `itk_sale_management`, `itk_translation`, `hr_holidays_public` haben auf **beiden** Instanzen installierte Version = Repo-Version 18.0.1.0.0 | ir.module.module vs. `__manifest__.py` | **GEPRÜFT/OK** — bereits erfolgt |
| F13 | D/Anhänge | ir.attachment 1249 → 1260, mail_message 455 → 456 (Asset-Regeneration nach HTTPS/proxy_mode-Umstellung; erwartbar, kein Fehler) | Kontrollzahlen | Hinweis |
| F14 | A/Sprache (itk_translation) | ITK-Menü-Baum sichtbar englisch/technisch: Top-Menü „ITK-Menu“ (733); Untermenüs 734–741 „Partner“, „Actual customers“, „All customers“, „Former Customers“, „Target Customers“, „Reseller“, „All Resellers“, „All Magnitudes“; 6 Actions gleichlautend (ir.actions.act_window) | RPC VM (de_DE == en_US) | **BEHOBEN** (02.09.); Rest KLÄRUNG: Top-Menü 733 "ITK-Menu", Menü 741 "All Magnitudes" |
| F15 | A/Sprache (itk_crm) | Custom-Felder auf res.partner (+ Delegation res.users) ohne de_DE-Text, sichtbar englisch: `firstname`/`lastname` („First/Last name“, partner_firstname), `status_of_community` „Status of Community“, `population` „Size of Population“, `population_update`, `member_of_city_alliance` „Member of City Alliance“, `asset_partner` „Asset Partner“, `title_put_in_front`/`title_put_in_back` „Title in Front/Back“, `sales_as_final_customer_count` „# of Sales as Final Customer“, `reseller`, `salutation`, `austria_wiki_url`, `community_magnitude` „Magnitude“, `community_magnitude_id` „Community Magnitude“ | RPC VM fields_get/ir.model.fields de == en | **TEILWEISE BEHOBEN** (klare Labels); KLÄRUNG NÖTIG für Fachfelder (Status of Community, Population, Magnitude, Title in Front/Back, Member of City Alliance, Asset Partner u. a.) |
| F16 | A/Sprache (itk_crm, x_-Felder crm.lead) | 4 Custom-Selection-Felder: Labels `x_lead_status` „Lead Status“, `x_Anrede_Lead` „Anrede Lead“, `x_Lead_Quelle` „Lead Quelle“ (nicht einheitlich deutsch); Auswahlwerte deutsch (außer „On-Hold“); `x_Produktinteresse` OK | RPC VM de_DE | **KLÄRUNG NÖTIG** (x_-Labels bewusst nicht gesetzt; Werte bereits deutsch) |
| F17 | A/Sprache (itk_subscription/sale_subscription) | Felder sale.subscription (70 Kandidaten) und sale.subscription.template (38) sichtbar englisch, u. a. Kernfelder `partner_id` „Customer“, `date_start` „Start Date“, `date` „End Date“, `recurring_next_date` „Date of Next Invoice“, `template_id` „Subscription Template“, `create_date` „Created on“; Menüs/Actions des Moduls sind dagegen deutsch (de.po nur teilweise geladen bzw. ohne Feld-Terme) | RPC VM fields_get de == en | **BEHOBEN** (Kern- und Zusatzfelder, 304 Feld-Fixes gesamt); Rest-Liste (34, meist mail/system) im Session-81-Bericht. **WICHTIG — Rueckfall und dauerhafte Loesung (Session 87, 11.09.2026):** Die handgesetzten de_DE-Slots gingen beim Modul-Upgrade (Session 82/84) verloren. Ursache belegt: die `i18n/de.po` referenziert **Odoo-11-XML-IDs** (einfacher Unterstrich) statt `field_<model>__<feld>`, der PO-Import joint ueber `ir_model_data` und ignorierte sie stillschweigend. Repo-Korrektur: `scripts/fix_po_xmlids_de.py` (543 Referenzen in 15 Modulen, zusaetzlich `model:` → `model_terms:` fuer `arch_db` und `selection:`-Referenzen auf `ir.model.fields.selection`-XML-IDs) + gezielte Einzel-Upgrades → die deutschen Texte kommen jetzt **dauerhaft aus dem Repo** |
| F18 | A/Sprache (itk_multifactor) | Wizard-Action-Namen englisch („Set Pricelist for Subscriptions“, „Update Multifactor for Subscriptionlines“, „Update Population and Multifactor for Partners“); Felder „To multiply by Factor(per 1000)“ (product), „Multiplication Factor/Thsd“ (res.partner/-users, sale.order.line, sale.subscription.line) | RPC VM de == en | **BEHOBEN** (02.09.) |
| F19 | A/Sprache (weitere itk_*) | Englische sichtbare Labels: itk_product „Product-Type“, „To multiply by Factor(thsd)“; itk_sale_management 5 sale.order-Kontaktfelder („Administrative/Technical/Sale Contact“, „Final Customer“, „Product Category“); itk_valorisierung „Valorisation Text“ (account.move/-bank.line); itk_projectcategory „Project Category“ (account.move); itk_saleorder_lines Menü/Action „All Order Lines“/„Order Lines“; itk_helpdesk_category_user „Assigned Users“ (helpdesk.ticket.category); zzgl. Audit-Labels („Created on/by“, „Display Name“, „Last Updated on/by“) auf allen itk-eigenen Modellen | RPC VM de == en | **BEHOBEN** (02.09., klare Labels); Rest: Audit-Labels auf itk-eigenen Lookup-Modellen (minor, KLÄRUNG) |
| F20 | A/Sprache (itk_helpdesk_compat) | Menü + Action „Support Tickets“ (891) englisch; übrige Menüs/Actions/Felder deutsch (Positivbefund) | RPC VM | **BEHOBEN** (02.09.) |
| F21 | A/Sprache (helpdesk_mgmt) | Menüs teilweise englisch: „All Tickets“ (746), „Dashboard“ (743), „Settings“ (750, unter Konfiguration), Actions „Helpdesk Ticket“ (3×); Feldlücken englisch: duplicate_*/„Enable duplicate ticket tracking.“, „Commercial Partner“, „Followers (Partners)“, „SMS Delivery error“; Settings-Felder (res.company/res.config.settings) „Auto assign tickets“, „Select category/team in Helpdesk portal“, „Required Category/Team field in Helpdesk portal“, „Move duplicate tickets to this stage“ — de.po im Repo vorhanden (299 Terme), aber unvollständig/nicht vollständig geladen | RPC VM de vs en | **BEHOBEN** (02.09., dokumentierte Stellen); KLÄRUNG NÖTIG: Menü 750 "Settings" (mögliche Dublette zu itk-Menü 866), Root "Helpdesk"/"Dashboard" (Fachwörter, bewusst belassen) |
| F22 | A/Sprache (helpdesk_mgmt_sla) | Menüs „SLA“ (776), „SLA Report“ (775); helpdesk.sla- und helpdesk.ticket.sla-Felder überwiegend englisch (Days/Hours, Deadline, Expected Stage, Ignore Stages, Consumed time, Ticket Sla …; 76 moduleigene Felder, Großteil en) — kein de.po im Repo | RPC VM de == en | **BEHOBEN** (02.09., Kernfelder/Menüs) |
| F23 | A/Sprache (helpdesk_mgmt_timesheet/-project) | Menü/Action „Timesheets“ (757); Felder „Allow Timesheet“, „Planned/Remaining/Total Hours“, „Show Timesheet Portal“, „Last Timesheet Activity“ (ticket) sowie „Ticket Count“, „Number of tickets“, „Use Tickets as“, „Helpdesk Ticket Count“ (project/task/milestone), Actions „Helpdesk Tickets“ — kein de.po im Repo | RPC VM de == en | **BEHOBEN** (02.09., Kernfelder/Menüs) |
| F24 | A/Sprache (project_timesheet_time_control) | Menü + Action „Start work“ (756, unter Zeiterfassung); Felder „Start Time“/„End Time“ (date_time/date_time_end), „Show Time Control“, „Previous timer …“ — de.po im Repo vorhanden, aber nicht geladen/unvollständig | RPC VM de == en | **BEHOBEN** (02.09.) |
| F25 | A/Sprache + Datenqualität (Statuswerte/Kategorien) | CRM-Stage „On-Hold“, Helpdesk-Stage „on Hold“ (englisch); Helpdesk-Kategorien: deutsch, aber sichtbare Duplikate („Allgemeine Anfrage (Support)“ 5×, „Störung/Fehler melden“ 4×, „Angebot anfordern“ 3×, „allgemeiner Support“ 2×, „Zugangsdaten vergessen“ 2×) + Tippfehler „Anynomisierungsportal“; Aktivitätstypen (12 aktiv) und übrige CRM-Stages deutsch (Positiv) | RPC VM (Datensätze) | **KLÄRUNG NÖTIG** (Daten: Stages "On-Hold"/"on Hold", Kategorie-Duplikate, Tippfehler "Anynomisierungsportal"; Datenbereinigung separat) |
| F26 | B/Encoding (Übersetzungen) | 3 CP850-Artefakte in sichtbaren de_DE-Übersetzungen (nicht Teil der Reparatur vom 13.08.): `account.move.status_in_payment` „Status ÔÇ×In ZahlungÔÇ£“, `account.reconcile.model.line.show_force_tax_included` „ÔÇ×Steuer inklusive erzwingenÔÇ£ anzeigen“, `res.partner.peppol_eas`-Wert `0245` „SK-Steueridentifikationsnummer (DI─î)“ (auch res.users/res.company sichtbar) | RPC VM ir.model.fields/ir.model.fields.selection de_DE | **BEHOBEN** (02.09., 3 Stellen) |
| F27 | itk_subscription (Abo-Anlage) | Neues Abo speichern → „Ein Pflichtfeld ist nicht gesetzt — Pricelist (pricelist_id)": (1) `pricelist_id` required=True ohne Default (Feld-Default/default_get/create leer; `property_product_pricelist` bei allen Partnern leer), (2) Form-View blendet Feld per `groups="product.group_sale_pricelist"` aus — Gruppe existiert in Odoo 18 nicht (O11-Relikt; O18: `product.group_product_pricelist`), (3) keine aktive EUR-Preisliste (F5) | RPC/DB (03.09., Session 82), Reproduktion lokal | **BEHOBEN** (lokal 03.09.: itk_subscription 18.0.1.1.0 — EUR-Default via default_get/onchange/create + View-Gruppen korrigiert (`product.group_product_pricelist`, `uom.group_uom`); PL 34 EUR aktiv; Test 8/8 PASS); **AUF DER VM DEPLOYT UND GETESTET** (11.09.2026, Session 84: `git pull --ff-only` 7e9e9de→1d6c835, gezieltes Einzel-Upgrade itk_subscription → **18.0.1.1.0**, sauberer Neustart; Praxistest **6/6 grün** — Anlegen ohne `pricelist_id` erfolgreich, PL 34/EUR automatisch, Positionen 65,00/15,00, Wiedereröffnung stabil, 5 Bestandsabos datenidentisch unverändert). Browser-Klicktest durch Anna **nachweislich erfolgreich** (11.09.2026: Abo `NV-00204`, PL 34/EUR automatisch, gespeichert) — F27 damit **vollständig erfüllt** |
| F28 | D/Berechtigungen (Datenqualität) | **Doppelkonto:** uid 2 `anna.maierhofer@it-kommunal.at` (tz Europe/Vienna) **und** uid 16 `Anna.maierhofer@it-kommunal.at` (Groß-A, ohne tz) — beide aktiv, beide Nicht-Portal-Benutzer; auf beiden Instanzen identisch | res.users (RPC 10.09.2026, Session 83) | **KLÄRUNG NÖTIG** (Benutzerbereinigung — fachliche Entscheidung Anna) |
| F29 | B/Encoding (Odoo-Kern) | 6 Core-QWeb-Views mit CP850-Artefakten (`ÔÇ…`) in **beiden** Instanzen: id 1282 (`sale_management`-Auftrags-PDF, Zero-Width-Space → unsichtbar), 325 `mail.notification_preview`, 2451 `mass_mailing.digest_mail_main`, 3090 `website.s_key_images`, 3072 `website.s_opening_hours` („LetÔÇÖs get in touch"), 2895 `website.template_footer_centered` (**inaktiv**) | RPC `ir.ui.view.arch_db` + Rendering-Probe `/`, `/contactus`, `/web/login` (11.09.2026, Session 85) | **dokumentiert** — derzeit **nicht sichtbar** (Website rendert sauber); kein Fix beauftragt |
| F30 | Datenabgleich VM ↔ lokal | VM führt **mehr** Datensätze als lokal: **17 vs. 16** Verkaufsaufträge (zusätzlich id 200 `S00198`, draft, EUR, 01.09.2026 12:43), **6 vs. 5** Abos (zusätzlich `NV-00204` = Browser-Klicktest Anna), `mail.message` 423 vs. 421 | RPC `search_read`/`search_count` beider Instanzen (11.09.2026, Session 85) | Hinweis — Abweichung dokumentiert, **nichts angeglichen** |
| F31 | A/Sprache (Ursache aller Text-Lücken) | **PO-Referenzschema Odoo 11 vs. Odoo 18:** die `i18n/de.po` der migrierten Module verwiesen auf O11-XML-IDs (einfacher Unterstrich statt `field_<model>__<feld>`), benutzten `model:` statt `model_terms:` für `ir.ui.view.arch_db` und die in Odoo 18 nicht mehr unterstützte Form `selection:modell,feld:index`. Der PO-Import joint über `ir_model_data` → alle diese Einträge wurden **stillschweigend ignoriert**; Modul-Upgrades konnten dadurch handgesetzte DB-Slots sogar wieder entfernen (Rueckfall F17) | Container-Quellcode `odoo/tools/translate.py` (`TranslationImporter`, `PoFileReader`) und `base/models/ir_model.py` (`field_xmlid`, `selection_xmlid`); DB-Vergleich `ir.model.data` (11.09.2026, Session 87) | **BEHOBEN (lokal + VM, 14.09.2026)** — `scripts/fix_po_xmlids_de.py`: **543 Referenzen in 14 Modulen** korrigiert; Einzel-Upgrades auf **beiden** Instanzen ausgeführt (26 Module, kein `-u all`), Verifikation grün (Abo-Felder/Buttons/Status + Modulnamen deutsch, „Kundenverwaltung“ unverändert) |
| F32 | A/Sprache (Ursache, Fortsetzung von F31) | **Der PO-Reader mischt die `.pot`-Datei in die `.po`** (`PoFileReader.__init__` -> `pofile.merge(polib.pofile(pot_path))`): die XML-ID-Referenzen stammen damit aus dem `.pot`. O11-Referenzen dort machten auch die korrigierte `.po` wirkungslos (z. B. "Vorname/Nachname", "Karte/Routenplaner"). Zusaetzlich: Modul-Upgrades laden mit `overwrite=False` (`t.value \|\| m.feld` -> ein vorhandener falscher de_DE-Wert gewinnt) und Python-Label-Aenderungen brauchen einen Container-Neustart | Container-Quellcode `odoo/tools/translate.py` und `ir_module.py::_load_module_terms`; DB-Vergleich `ir_model_fields.field_description` (14.09.2026, Session 88) | **BEHOBEN** - `fix_po_xmlids_de.py` bearbeitet jetzt auch `.pot` (**625 weitere Referenzen in 10 Modulen**), `load_terms_de.py` fuer gezielte overwrite-Ladungen; lokal **17/17 verifiziert**, 0 Fehler im Log |
| F33 | Datenvollstaendigkeit (Dateien) | **Filestore unvollstaendig:** von 958 Anhaengen mit `store_fname` fehlen **895 Datensaetze = 513 verschiedene Dateien** (5,1 MB) - 432 Odoo-Standardgrafiken (payment/App-Icons/Gamification/Flaggen) und 81 Dateien mit Datenbezug (43 echte Kontakt-/Mitarbeiterfotos, 7 Beleg-PDFs, 4 Dashboards, 1 Logo, 1 CSS, 25 Mini-Platzhalter). Zusaetzlich liegen 19 (lokal) / 20 (VM) Dateien eine Ebene zu hoch und werden nicht gefunden. Betrifft beide Instanzen identisch | `scripts/f33_filestore_scan.py` (Vergleich Anhaenge <-> Filestore), VM-Log 48 h (210 `FileNotFoundError`), Abgleich aller lokalen Sicherungen per SHA-1; alter `dump.sql` mit 1.243 Anhangszeilen und **leerem `db_datas`** (14.09.2026, Session 88/90) | **UNTERSUCHT (Session 90) - vorbestehend, nicht durch unsere Sessions verursacht.** Lokal vorhanden: vollstaendiges **Odoo-11-Backup** (`Desktop` + `Nextcloud\Odoo_DB_Dump_2026_09_03`: `ITK_V1_a.pg_dump` 48 MB + `ITK_V1_a_filestore.tar.gz` 1,61 GB / 21.789 Dateien) - deckt aber nur **18 der 513** per Hash ab. 432 Modulgrafiken sind aus dem Odoo-Quellcode rekonstruierbar; ~25 Fotos semantisch ueber die O11-DB; **7 PDFs + 4 Dashboards nur ueber IPAX-Backup der Test-VM (vor 31.08.2026)**. Reparatur **noch nicht** ausgefuehrt. **Session 91 (15.09.2026, read-only):** Zugehoerigkeit, Struktur und Integritaet des O11-Backups bewiesen (21.789 Dateien, **100 %** `SHA-1(Inhalt) == Dateiname`, Mengen identisch mit den 21.789 `store_fname` des Dumps) => **502 von 513 Dateien ohne IPAX beschaffbar** (40 Bild-Datensaetze per Hash + 12 semantisch); definitiv offen nur **7 Beleg-PDFs + 4 Dashboards + 6 Bild-Datensaetze** (3 echte Personen, 12 Testkonten). Fuer die Testphase **bewusst offen haltbar**, Restposten namentlich dokumentiert. |

**Korrektur-Status Abschnitt 1 (Session 81, 02.09.2026 — ausgeführt mit Freigabe):**
- **Gezielte de_DE-Slot-Korrekturen auf der VM (Referenzumgebung):** 11 Menüs, 16 Actions, 304 Felder (inkl. sale.subscription/-template-Kernfelder, helpdesk.sla/ticket.sla, Projekt-/Timesheet-Zusatzfelder, itk-Labels auf Kontakt/Verkauf/Produkt/Rechnung). Methodik: ORM-write mit `lang=de_DE`-Kontext (jsonb-Slot), kuratierte Term-Liste + Übernahme korrekter de-Labels von Pendant-Feldern gleichen Feldnamens (keine globale Ersetzung). Verifikation per `fields_get` de_DE (Stichproben grün).
- **Encoding:** `res_currency` EUR-Symbol = `€` (F1); `account_payment`-shortdesc korrigiert (F7); 3 Übersetzungs-Mojibake-Stellen korrigiert (F26).
- **Reproduzierbar nach Restore:** `scripts/fix_ui_labels_de.py`, `scripts/fix_ui_menus_actions_de.py`, `scripts/fix_ui_encoding_de.py` (idempotent, HTTPS-RPC, Credentials aus lokaler `.env`).
- **Code-Angleichung itk_*-Module (für Neuinstallationen):** Menü-/Action-/Feld-Strings in 10 addons-Modulen auf Deutsch (Commits d0b357b/e6946e3, Branch hermes/abnahme-sprache-encoding; Deploy auf die VM nach git pull + gezielten Einzel-Upgrades — SSH-Port 22 war am 02.09. von hier blockiert).
- **KLÄRUNG NÖTIG (bewusst NICHT geändert, fachliche Entscheidung Anna):** itk_crm-Kontakt-Fachfelder („Status of Community“, „Population/Size of Population“, „Community Magnitude“, „Title in Front/Back“, „Member of City Alliance“, „Asset Partner“, „Reseller“); x_-Feld-Labels crm.lead („Lead Status“, „Anrede Lead“, „Lead Quelle“ — Werte bereits deutsch); Top-Menü 733 „ITK-Menu“ und 741 „All Magnitudes“; Menü 750 „Settings“ (Helpdesk, mögliche Dublette zu 866 „Einstellungen“); Stages „On-Hold“/„on Hold“ + Kategorien-Duplikate/Tippfehler „Anynomisierungsportal“ (Datenbereinigung); Audit-Labels auf itk-Lookup-Modellen (minor). Detail-Liste der offenen Felder: Session-81-Bericht in PROJECT_KNOWLEDGE.md.
- **Session-84-Abschluss (11.09.2026) — ABO-FIX AUF DER VM DEPLOYT UND GETESTET:** `itk_subscription` **18.0.1.1.0** per gezieltem Einzel-Upgrade auf der VM (`docker compose stop odoo` → one-shot `-u itk_subscription` → `start`); **neue Abos lassen sich wieder speichern** (Anlegen ohne `pricelist_id` erfolgreich, Praxistest 6/6 grün, Wiedereröffnung stabil). **Verwendete EUR-Preisliste: `product.pricelist` id 34 „Preisliste 2026 + Valorisierung" (EUR, aktiv) — Festpreise 65,00 / 15,00.** 5 Bestandsabos datenidentisch unverändert. **Umfangstreue: kein `-u all`, keine anderen Modul-Upgrades, keine DB-Migration, keine Systemänderung.** Details: PROJECT_KNOWLEDGE.md, Session 84.
- **Session-85-Abschluss (11.09.2026) — WÄHRUNG/EURO-ZEICHEN:** Analyse beider Instanzen (read-only) + **lokales EUR-Symbol korrigiert**: `res.currency` id 126 `symbol` von `Ôé¼` auf **`€`** (ein Feld, ein Datensatz, **keine** globale Ersetzung, **VM unverändert**). Verifikation: Odoo-Formatter `65,00 €`/`1.234,56 €`, **gerenderte Rechnung + Auftrag ohne Mojibake**, USD-Kontrollzahlen unverändert. USD-Währung/USD-Belege (F2/F3/F4) **bewusst unangetastet**. Details: PROJECT_KNOWLEDGE.md, Session 85.
- **Session-86-Abschluss (11.09.2026) — ZEITZONEN (F8):** `Europe/Vienna` für **alle 12** aktiven internen Benutzer ohne Zeitzone (uid 13–24, inkl. Doppelkonto uid 16 und Christiane Breit) — **auf VM und lokal**, je ein `write` auf `res.users`. uid 2/8 waren korrekt; die **4 inaktiven technischen/System-/Portal-Konten blieben unberührt**; **keine Löschung/Archivierung**; Kontrollzahlen vor == nach → historische Daten unverändert. Ergebnis: **14 von 14 aktiven internen Benutzern** mit `Europe/Vienna` auf beiden Instanzen.
- **Session-87-Abschluss (11.09.2026) — STUFE 1 „DAUERHAFTE DEUTSCHE TEXTE IM REPO":** Ursache aller Text-Lücken behoben (F31): die `i18n/de.po` der migrierten Module auf das **Odoo-18-Referenzschema** umgestellt (`scripts/fix_po_xmlids_de.py`, **543 Referenzen in 15 Modulen**: Feld-/Modell-IDs mit doppeltem Unterstrich, `model_terms:` für `arch_db`, `selection:`-Referenzen auf `ir.model.fields.selection`-IDs) und **14 ITK-Modulnamen** in den Manifesten deutsch gesetzt (F6). Danach **gezielte Einzel-Upgrades** (kein `-u all`), `update_list`, Neustart. **Verifikation lokal grün:** Abo-Feldlabels deutsch (`Kunde`, `Startdatum`, `Preisliste` …), Abo-Statuswerte **Neu/Laufend/Zu erneuern/Abgeschlossen/Abgebrochen**, Abo-Buttons deutsch, Apps-Liste deutsch, **„Kundenverwaltung" unverändert**, 0 Fehler nach den Upgrades. KLÄRUNG-Liste unangetastet. **VM-Deploy am 14.09.2026 nachgezogen** (SSH wieder offen): Pull `8f2a387`→`1f07d61`, Neustart, 26 Einzel-Upgrades, `update_list`, Verifikation auf der VM identisch grün → `lokal = GitHub = VM`.
- **Session-91-Abschluss (15.09.2026) - O11-FILESTORE-BACKUP GEPRUEFT (read-only):** `ITK_V1_a_filestore.tar.gz` gehoert **zweifelsfrei** zur O11-DB `ITK_V1_a` (Dump-Kopf `dbname: ITK_V1_a`, PostgreSQL 10.23/Ubuntu 18.04; die 21.789 `store_fname` der DB == die 21.789 Archivdateien, **mengenidentisch**) und ist **zu 100 % intakt** (`SHA-1(Inhalt) == Dateiname` fuer alle 21.789 Dateien, 0 Abweichungen, 0 leere Dateien, 1,89 GB, alle 256 Buckets belegt) => **vollstaendig, unversehrt, direkt verwendbar**. Foto-Zuordnung **pro Datensatz**: von **70** betroffenen Bild-Datensaetzen **40 per Hash** + **12 semantisch** ueber `ir_attachment.res_name` (Namensnormalisierung noetig, sonst nur 1 Treffer) + **18 lokal nicht vorhanden** (12 Test-/Demo-Konten, 6 Datensaetze von 3 echten Personen). **7 Beleg-PDFs** (0 Treffer auf S00188/S00189/P00015-P00018) und **4 Dashboards** (der Dump kennt keine `spreadsheet`-Tabellen) sind **definitiv nicht lokal vorhanden**. Ergebnis: **502 von 513 Dateien ohne IPAX beschaffbar**; F33 fuer die Testphase **bewusst offen haltbar**. Neues Werkzeug im Repo: `scripts/filestore_archive_verify.py` (Integritaet + Paarungsbeweis). **Nichts entpackt/kopiert/geaendert.**
- **Session-90-Abschluss (14.09.2026) - F33 UNTERSUCHT (read-only):** 895 Anhangsdatensaetze = **513 verschiedene fehlende Dateien** (432 Modulgrafiken + 81 Datendateien); keine davon in den lokalen Sicherungen (0 von 513) - der Anhangsdump enthaelt keine Dateien (`db_datas` leer). Neuer Fund: **vollstaendiges Odoo-11-Backup lokal** (`C:\Users\anna.maierhofer\Desktop\Odoo_DB_Dump_2026_09_03` und byte-identisch in `Nextcloud`): `ITK_V1_a.pg_dump` (48 MB, O11-Merkmale) + `ITK_V1_a_filestore.tar.gz` (1,61 GB, 21.789 Dateien) - deckt **18 der 513** per SHA-1 ab. Ohne IPAX moeglich: 432 Modulgrafiken (Quellcode) + 18 Fotos + voraussichtlich ~25 weitere Fotos (semantisch ueber die O11-DB); offen bleiben **7 Beleg-PDFs + 4 Dashboards**. Werkzeug im Repo: `scripts/f33_filestore_scan.py`. **Nichts kopiert/geaendert/geloescht.**
- **Session-89-Abschluss (14.09.2026) - PUNKTE 10, 13, 15, 16, 22, 26 + TEXTKORREKTUREN:** **Titel vorangestellt/nachgestellt** (itk_crm), **Projekte/Aufgaben/# Aufgaben** (Core-Felder, Eintraege in itk_base_setup), **SLA-Begriffe** (neue Datei `helpdesk_mgmt_sla/i18n/de.po`: SLA-Frist, SLA erfüllt, Team-SLA, Ticket-SLA, Gültige SLAs, SLA setzen), **Zeiterfassungs-Begriffe** (neue Datei `helpdesk_mgmt_timesheet/i18n/de.po`: Zeiterfassung erlauben, Letzte Zeiterfassung, Geplante Stunden, Fortschritt, Reststunden, Zeitsteuerung anzeigen, Zeiterfassung, Gesamtstunden, Arbeit starten/stoppen/fortsetzen), **Herrenlose Altfehler korrigiert:** "Erneuerungsabgebot" -> "Erneuerungsangebot", "Aboauftrag" -> "Abo-Auftrag"; Kategorie **"Anonymisierungsportal"** (Daten, beide Instanzen). Helpdesk-Grundbegriff und Feld Team **bewusst unveraendert**. **Verifikation lokal 36/36 OK** (`scripts/verify_s89_de.py`, inkl. 5 Gegenproben auf unveraenderte Begriffe), Log 0 Fehler nach 11:50. Zwischenfall: erste Upgrade-Runde brach ab, weil eine selbst formulierte `#.`-Kommentarzeile in einer `.po` nicht mit `#. module: <modul>` begann (`PoFileReader` ruft `match.groups()` ungeschuetzt auf) - behoben und dokumentiert. **VM-Deploy am 14.09.2026 durchgefuehrt** (Pull `73c3789`->`0f10547`, Neustart, 5 Einzel-Upgrades, gezielte Ladung, Neustart): **VM 36/36 OK**, Log 0 Fehler -> `lokal = GitHub = VM` auf `0f10547`.
- **Session-88-Abschluss (14.09.2026) - ZEHN EINDEUTIGE REPO-BEGRIFFE DEUTSCH:** Punkt 3, zweite Runde. Neue Ursache gefunden und behoben (F32): der PO-Reader mischt die **`.pot`-Referenzen** in die `.po` - dadurch blieben auch nach Session 87 deutsche Texte englisch. Umgesetzt: Abo-Button **"Rechnung manuell erstellen"**, **Vorname/Nachname**, **Einwohnerzahl**, **Einwohnerzahl aktualisiert am**, **Peppol-Endpunkt**, **Karte/Routenplaner**, Helpdesk-Duplikatbegriffe (**Anzahl Duplikate**, **Duplikat von**, **Duplikat-Tickets**, **Duplikat-Erkennung aktivieren.**, **Als Duplikat markieren**), Menues **ITK-Menü**, **SLAs**, **Helpdesk-Gruppen**; dazu 625 weitere `.pot`-Referenzen in 10 Modulen. Neue Werkzeuge: `load_terms_de.py`, `verify_s88_de.py`. Lokal **17/17 OK**, 0 Fehler im Log; "Kundenverwaltung" im Quelltext unveraendert. OCA-Modulnamen, Klärungs-Begriffe und DB-gepflegte Menues/Stages/Kategorien bleiben unangetastet. **VM-Deploy am 14.09.2026 durchgefuehrt** (Pull `6aaa5b9`->`e94b511`, Neustart, 8 Einzel-Upgrades, 2 gezielte Ueberschreib-Ladungen, Neustart): **VM 17/17 OK** -> `lokal = GitHub = VM` auf `e94b511`. Log-Gegenprobe 48 h: keine neuen Fehlerarten (F33 vorbestehend).

- **Offen:** Browser-Sichtprüfung der korrigierten UI (Chrome-„Allow remote debugging“-Popup nötig, wie in früheren Sessions) und der Browser-Klicktest der Abo-Anlage auf der VM; de.po-Nachladen funktioniert in dieser Umgebung NICHT (msgstr-Gerüste leer bzw. Import wirkungslos → dokumentierter Weg sind die Fix-Skripte).

---

## 9. Grenzen dieser Analyse

- Diese Checkliste basiert auf **read-only**-Auswertungen (SQL über die VM-DB, RPC-Textinventar de_DE/en_US 02.09.2026, Repo-Vergleich, frühere Sessions). **Keine** Browser-Sichtprüfung, keine PDF-Renderings, keine E-Mail-Tests in dieser Phase.
- Das RPC-Inventar (Abschnitt 1, Befunde F14–F26) erfasst, welche Texte das System für einen de_DE-Benutzer bereitstellt (Menüs, Actions, Feldlabels via `fields_get`, Auswahlwerte, Modul-shortdesc, Datensatznamen). Es ersetzt **nicht** die Sichtprüfung im Browser (Anordnung, Kanban-Darstellung, Hilfetexte, Fehlermeldungen zur Laufzeit).
- Die eigentliche Abnahme (Sichtprüfung, Bedienung, Datenqualität) erfolgt **gemeinsam Punkt für Punkt** über die Checkliste — begonnen mit Abschnitt 1 (Sprache): Browser-Durchgang zu den Befunden F14–F26 steht aus.
- **VM-Zugang (Stand 11.09.2026):** Die Test-VM wird über **VPN + Teleport** (`k001959vsv`, User `k001959`) administriert; ein direkter Zugriff auf Port 22 ist von außen VM-seitig gefiltert (Befund 10.09.2026, Session 83: 6/6 externe Nodes Timeout, 443 von denselben Nodes offen). Gearbeitet wird über Git + **gezielte Einzel-Upgrades** (`docker compose stop odoo` → one-shot `-u <modul> --stop-after-init` → `start`), niemals `-u all`; read-only-Analysen laufen über HTTPS-JSON-RPC. Die VM steht seit 11.09.2026 auf `main` = `1d6c835`. Die **lokale** Instanz hat weiterhin **nicht** den Fix-Stand der VM (EUR-Symbol F1, de_DE-Slots aus Session 81) — lokale Abweichungen werden getrennt ausgewiesen.
- Erst nach Abschluss der Abnahme und Entscheidung zur O11-Migration wird das Feldmapping (Abschnitt 6) erstellt und die Datenmigration geplant (`DATA_MIGRATION_CHECKLIST.md` bleibt dafür der operative Plan).