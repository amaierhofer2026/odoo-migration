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

### 6.10 Kontakte → Kontaktformular → Tab „Support Ticket“ — **MIGRATIONSBEREIT (Struktur)**, 15.09.2026 (Session 112)

Feld-Mapping und Umfang dokumentiert in `docs/o11-o18-strukturvergleich-kontakt-support-ticket.md`.

**Systemwechsel dokumentiert:** Odoo 11 nutzt `website_support` (Website Help Desk), Odoo 18 die OCA-Helpdesk-Funktion
`helpdesk_mgmt` (+ SLA, Projekt, Timesheet) sowie ITKs `itk_helpdesk_compat`.

**Odoo-11-Felder im Reiter:** `sla_id` (SLA je Kontakt) und `stp_ids` („Support Ticket Zugriffskonto“) — beide
**entfallen** in Odoo 18 (kein Gegenstück) und **ohne Datenbestand** (0 von 5.842 Kontakten).

**Smart-Button:** Odoo 11 „Support Tickets“ (`support_ticket_string`) → Odoo 18 `action_view_helpdesk_tickets` mit
`helpdesk_ticket_count`/‑active_count/‑count_string — Beschriftung in Session 112 auf „Support Tickets“ gesetzt.

**Behoben (Session 112, `itk_base_setup` 18.0.1.2.3):** Der Reiter enthielt nur einen Platzhaltertext und zeigt jetzt die
Odoo-18-Ticketliste des Kontakts (`helpdesk_ticket_ids`, nur lesend) mit Ticketnummer, Titel, Erstellt am, Stufe, Team,
Kategorie und Zugewiesenem Benutzer. Keine Daten migriert oder geändert.

**Eigener Migrationsbereich (dokumentiert, nicht bearbeitet):** 1.210 Odoo-11-Tickets (483 mit Kontakt) → `helpdesk.ticket`;
die sechs Odoo-11-Statusnamen entsprechen nahezu 1:1 den sechs Odoo-18-Stufen (nur „Open“ gegen „Offen“); 18 Odoo-11-Kategorien
gegen 37 Odoo-18-Kategorien (Zuordnungstabelle nötig); 1 SLA („Standard SLA Support ITK Produkte“) → SLA am Team.

**Ticket-Migration ist SELEKTIV (verbindliche Vorgabe Session 113):** Die 1.210 Odoo-11-Tickets werden **nicht automatisch**
migriert. Vor der Migration ist eine Auswahlregel zu definieren (Status, Alter/Erstell- bzw. Abschlussdatum, fachliche
Relevanz, ggf. Kategorie); **alte, abgeschlossene Tickets werden nicht automatisch übernommen**. Keine Entscheidung
darüber getroffen, welche Tickets migriert werden — offener Migrationspunkt. Zahlen als Grundlage: Geschlossen/Behoben 1.170,
Open 26, in Bearbeitung 12, on Hold 1, Verrechnung mit Kunde geklärt 1; 483 Tickets mit Kontaktbezug.

**Strukturelle Aufnahmefähigkeit geprüft (VM):** Kontaktbezug, Bearbeiter, Stufe, Kategorie, Team, Titel, Inhalte/Chatter und
Anhänge sind direkt beschreibbar. **Ticketnummer, Erstellzeitpunkt und Ersteller sind schreibgeschützt** → falls diese
Odoo-11-Werte erhalten bleiben sollen, ist ein technischer Importweg einzuplanen. **Status-Zuordnung nahezu 1:1** (nur
„Open“ gegen „Offen“); Kategorien brauchen eine Zuordnungstabelle (Odoo 11: 18).

**Nachweis (Session 113, gegen die VM geprüft):** `itk_base_setup` 18.0.1.2.3 auf der VM installiert;
`scripts/verify_s112_support_ticket.py` lokal 35 OK / 0 FEHL und **VM 35 OK / 0 FEHL**; Browser-Test des Reiters im echten Chrome
(alle 7 Spalten sichtbar, keine Bearbeiten-Buttons, Reiterfolge korrekt, Screenshot `21_VM_SupportTicket.png`);
70 Kontakte unverändert, keine Ticketdaten übernommen. **Bereich strukturell migrationsbereit.**

### 6.11 CRM → Verkaufschancen — **Struktur und Stammdaten MIGRATIONSBEREIT**, 15.09.2026 (Session 114)

Dokumentation: `docs/o11-o18-strukturvergleich-crm-verkaufschancen.md`.

**Zahlen-Korrektur:** Der bisher notierte Wert „6.966 Verkaufschancen“ war die Gesamtzahl aller `crm.lead`-Datensätze.
Live geprüft: **6.967** `crm.lead` gesamt = **6.608 Interessenten** (`lead`) + **359 Verkaufschancen** (`opportunity`).

**Stufen (9, wie Odoo 11):** Neu, Angebotsphase, On-Hold, **Angebot ausgesendet (neu angelegt, id 21, Position 4)**,
Positive Rückmeldung, Erfolgreich (is_won), Verloren, Zur Verrechnung bereit, Verrechnet. Die Reihenfolge entspricht jetzt
Odoo 11. Gepflegt im Repo (`itk_crm/data/crm_stages.xml`, `setup_runtime._STAGES`, Migration `18.0.1.5.2`), Modul **18.0.1.5.2**.

**Teams (7 tatsächlich verwendet):** Vertriebskanäle (Intern) 276 Chancen, Interne Weitergabe 74, Persönlicher Kontakt 3,
Webseite 2 (→ Odoo-18-Standardteam **Website**, aktiviert), Webinar 2, Newsletter 1, Telefon 1. Neu angelegt: Vertriebskanäle
(Intern), Interne Weitergabe, Persönlicher Kontakt, Webinar, Telefon; Teamleiter „Breit Christiane“ gesetzt, wo in Odoo 11
hinterlegt. **„Suche / Liste“ (0 Chancen) bewusst nicht angelegt.** Keine Verkaufschance zugeordnet.

**Verlustgründe:** Alle fünf Odoo-11-Namen existieren in Odoo 18 bereits — nichts anzulegen. Das Feld ist in Odoo 11 bei
**keiner** Chance gesetzt (auch nicht bei den 130 in Stufe „Verloren“). Feldname: `lost_reason` → **`lost_reason_id`**.

**Feld-Mapping (16 Felder dokumentiert):** u. a. `planned_revenue` → **`expected_revenue`** (float → monetary),
`lost_reason` → **`lost_reason_id`**, `tag_ids` von `crm.lead.tag` → **`crm.tag`**, `description` text → **html**;
`kanban_state` und `date_action_last` entfallen; `date_closed`/`date_open` in Odoo 18 schreibgeschützt (technischer Importweg).

**Keine Datenübernahme:** 0 der 359 Verkaufschancen und 0 der 6.608 Interessenten migriert.

**Offen (KLÄRUNG NÖTIG):** 1) Interessenten (6.608) — eigene Entscheidung 2) Auswahlregel für die Chancen-Migration
3) Stufe „Verrechnet“: `is_won`/`fold` fachlich klären (206 von 359 Chancen) 4) Gewinnwahrscheinlichkeit je Chance setzen?
5) Team-Mitgliedschaften 6) Wortlaute (Phase/Stufe, Vertriebsmitarbeiter/Verkäufer, Verkaufsteam/Vertriebskanal,
Verlustgrund/Ablehnugsgrund) 7) Tag-Mapping `crm.lead.tag` → `crm.tag` (117 Chancen) 8) Verlustgrund für die 130
Chancen in Stufe „Verloren“ (in Odoo 11 nicht gepflegt).

**Nachweis:** `scripts/verify_s114_crm_chancen.py` → lokal 52 OK / 0 FEHL; Browser-Prüfung auf der VM.

### 6.15 Verkauf (Menues, Module, Auftragsansichten) - **ABGESCHLOSSEN: VERKAUF VOLLSTAENDIG FUNKTIONSFAEHIG UND VOLLSTAENDIG MIGRATIONSVORBEREITET**, 29.09.2026 (Session 121, Teile 1-5)

Dokumente: `docs/o11-o18-vergleich-verkauf-teil1.md` bis `...teil5-luecken.md`,
`docs/o11-o18-verkauf-teil5-lageranbindung.md`, `docs/o11-o18-verkauf-teil5-block3-browserabnahme.md`,
Abschlussdokument **`docs/o11-o18-verkauf-abschluss.md`**.
Odoo 11 Prod `portal.it-kommunal.at` (DB `ITK_V1_a`) ausschliesslich read-only verwendet.

**Teil 1 (Grundstruktur, read-only):** Modulinventar beider Systeme, Menuebaum Odoo 11 (23 Menues
unter Wurzelmenue `Verkauf`, id 294) gegen Odoo 18 (37, spaeter 38 Menues mit dem neuen
Kanalbericht), Nutzungszahlen der Menueziele (sale.order 2.461, sale.order.line 4.007,
sale.report 3.984, product.pricelist 50, product.pricelist.item 1.872, crm.team 8,
report.all.channels.sales 3.772). Befunde: fehlender Bericht "Verkaufsauftraege aller Kanaele"
(in Teil 4 geloest), tote Menues (Reportlayout Kategorien, Reklamationen), abweichender
Default-Filter, 16 gespeicherte Filter (nicht uebernommen), fehlende Lageranbindung (in Teil 5
geschlossen).

**Teile 2 bis 5 - Kurzuebersicht und Nachweise:**

```
Teil 2  Feldinventar sale.order / sale.order.line
        verify_s121_verkauf_teil2.py ................. 111 OK / 0 FEHL
Teil 3  Formulare/Reiter .............................  64 OK / 0 FEHL
        Statuswechsel ................................  53 OK / 0 FEHL
        Suche/Filter/Gruppierungen ................... 199 OK / 0 FEHL
Teil 4  Ansichten (Liste/Kanban/Kalender/Pivot/Graph)  146 OK / 0 FEHL
        Auftrags-/Aktivitaetenkalender ...............  33 OK / 0 FEHL
        Bericht "Verkaufsauftraege aller Kanaele" ....  84 OK / 0 FEHL
        Druckberichte ................................  69 OK / 0 FEHL
Teil 5  Block 1 Regression (11 Laeufe, lokal+VM) ..... 886 OK / 0 FEHL
        Block 2 Lueckenanalyse ....................... 1 echte Luecke (Lageranbindung)
        Lueckenschluss Lageranbindung ................ lokal 26 OK, VM 26 OK (RPC)
                                                       lokal 14 OK, VM 14 OK (Browser)
        Stammdaten "30 Tage netto" ................... 113 OK / 0 FEHL, in Odoo 18 angelegt
        Block 3 Browser-Gesamtabnahme VM ............. 243 OK / 0 FEHL (11 Werkzeuge)
                                                       + 43 OK / 0 FEHL (15 Stationen)
        Block 4 Endstand ............................. keine offenen View-Fehler,
                                                       keine offenen Punkte
```

**Umgesetzt in Odoo 18:** `itk_sale_management` 18.0.1.6.0 (u. a. Bericht "Verkaufsauftraege aller
Kanaele" auf `sale.report` mit Aktion, Menuepunkt, Filter "Aktuelles Verkaufsjahr", Gruppierung
Vertriebskanal), `itk_product` 18.0.1.0.3 (`responsible_id` auf Odoo-18-Standard), Neuinstallation
`stock` 18.0.1.1 / `stock_account` 18.0.1.1 / `sale_stock` 18.0.1.0 (VM zusaetzlich `project_stock`,
`l10n_at` aktualisiert), Zahlungsbedingung "30 Tage netto" angelegt (ohne Zuordnung).

**Bewusste Abweichungen und bewusst nicht migrierte Punkte:** vollstaendig dokumentiert in
`docs/o11-o18-verkauf-abschluss.md` Abschnitt 3 und 4 (u. a. Bericht auf `sale.report` statt
`report.all.channels.sales`, Default-Filter "Meine Angebote" bleibt, keine Uebernahme der 16
Benutzerfilter, ITK-Proformavorlage als dokumentierte Altvorlage, Gruppe "Versand" heisst in
Odoo 18 "Lieferung", Sperre ueber Feld `locked`, tote Menues Reportlayout/Reklamationen,
Preislisten/Produkte als Datenmigrationsthema).

**Rahmenbedingungen eingehalten:** keine Datenmigration (alle Testdaten entfernt, Bestand nach
jedem Lauf unveraendert; VM 20 Auftraege / 29 Auftragszeilen / 13 Produkte / 0 Lagerbelege,
lokal 18 / 28 / 13 / 0), Odoo 11 ausschliesslich read-only, Odoo-18-Zusatzfunktionen unveraendert
erhalten (Standardfilter, Standardansichten, vier Druckberichte, Auftrags- und Aktivitaetenkalender,
Massenbearbeitung, Zusammenfuehren von Auftraegen, transaction_ids).

**View-Gesundheit (lokal und VM):** alle vorhandenen Ansichtstypen von `sale.order`,
`sale.order.line`, `stock.picking` (inklusive `project_stock`-Erweiterung), `product.template`,
`product.product`, `account.move`, `res.partner`, `account.payment.term`, `product.pricelist`,
`crm.team` laden fehlerfrei; Server-Logs ohne Meldungen zu ungueltigen Ansichten.

**Befund F55 (Session 121):** Odoo 18 haengt das Menue-Popover als `.o-popover o-dropdown--menu`
an das Ende des Body; Sichtbarkeitspruefungen ueber `offsetParent` schlagen dort fehl
(position: fixed) - `getClientRects()` verwenden.

**NACHTRAG 29.09.2026 (Entscheidung Anna): Abschlussmarkierung zurueckgestellt.** Der gezielte
Migrations-Check (Feldzuordnung mit Wertepruefung, Formularaufbau, Spalten - Dokument
`docs/o11-o18-verkauf-migrationscheck.md`) hat acht echte Migrationsrisiken ergeben (R1
Mengeneinheiten, R2 price_reduce, R3 Zustand `done`, R4 note text->html, R5 invoice_lines,
R6 tag_ids, R7 layout_category_id, R8 amt_invoiced/amt_to_invoice). Der Bereich Verkauf gilt
erst dann wieder als migrationsbereit, wenn diese Risiken technisch eindeutig vorbereitet sind.

**R1 Mengeneinheiten: ABGESCHLOSSEN (29.09.2026).** Odoo 18 fuehrt "GB" in der eigenen Kategorie
"Datenmenge" (keine Umrechnung zu Liter/Volumen); die sieben historischen Einheiten
"13/15/16/19/22/23/29 Gemeinden" bleiben bestehen und werden bei der Datenmigration 1:1 nach
Namen zugeordnet (nicht auf "Einheit(en)" zusammengefuehrt); Rundung "Einheit(en)" und
"ITK Einheit" 0,001; Dezimalgenauigkeit "Product Unit of Measure" 3. Nachweise: 64 OK / 0 FEHL,
Regression 886 OK / 0 FEHL, Browser auf der VM 43 OK / 0 FEHL.
Dokument: `docs/o11-o18-verkauf-r1-mengeneinheiten.md`.

**R2 price_reduce: ABGESCHLOSSEN (29.09.2026).** Odoo 18 kennt das Feld `price_reduce` nicht mehr;
die Nachfolgefelder `price_reduce_taxexcl` und `price_reduce_taxinc` sind vorhanden. Der Wert wird
bei der Datenmigration nicht direkt uebernommen, sondern aus `price_unit`, `discount`,
`product_uom_qty`, `tax_id` und `currency_id` durch die Odoo-18-Standardlogik neu berechnet.
Nachweis: Formel `price_reduce = price_unit * (1 - Rabatt/100)` trifft in allen 4.011 Zeilen zu;
3.960 von 3.960 Zeilen mit Menge > 0 stimmen innerhalb 0,01 mit dem Odoo-18-Wert ueberein (3.959
exakt); Sonderfaelle dokumentiert (1 Zeile mit 1-Cent-Eigenrundung, 51 leere Positionen).
Pruefung 9 OK / 0 FEHL je Instanz, keine Aenderung an Odoo 18 noetig.
Dokument: `docs/o11-o18-verkauf-r2-preis-reduziert.md`.

**R3 Status `done`: ABGESCHLOSSEN (29.09.2026).** Odoo 11 fuehrte die Auftragssperre als Zustand
`done` ("Gesperrt"); Buttons "Sperre"/"Entsperren", Feld `locked` gab es nicht. Bestand 0 Auftraege,
Nachverfolgung 1.727 Zustandsaenderungen mit 0 Wechseln nach "Gesperrt" - der Zustand war nie in
Verwendung. Odoo 18 bildet die Sperre ueber das Feld `locked` ab (Anzeige "Gesperrt", Buttons
"Sperren"/"Entsperren", gleicher Hilfetext, Feldschutz im Formular, `action_cancel` verweigert
gesperrte Auftraege). Transformationsregel: `done` -> `state='sale'` + `locked=True`; alle anderen
Zustaende 1:1; bei `sale` wird `locked` NICHT automatisch gesetzt (nur bei tatsaechlichem `done`).
Wortlaut: Odoo-18 "Storniert" bleibt bestehen. Keine Aenderung an Odoo 18 erforderlich.
Dokument: `docs/o11-o18-verkauf-r3-status-done.md`.

**R4 `note` (TEXT -> HTML): ABGESCHLOSSEN (29.09.2026).** Odoo 11 fuehrt `note` als Textfeld
("Geschaeftsbedingungen"), Odoo 18 als HTML-Feld (`sanitize`) mit dem Wortlaut "Allgemeine
Geschaeftsbedingungen" (Wortlaut bleibt bestehen, Abweichung dokumentiert). Transformationsregel:
Umwandlung mit der Odoo-18-Standardfunktion `odoo.tools.mail.plaintext2html` (HTML-Zeichen
maskieren, Zeilenumbrueche erhalten, URLs als Links, Inhalt unveraendert) - Nachweis: reiner Text
im HTML-Feld verliert den Zeilenumbruch, spitze Klammern werden als HTML gedeutet.
**Messkorrektur:** Nur 3 Auftraege tragen echten Text (A-1900897, A-1900947, A-2300151); die
frueher genannte Zahl 2.442 entstand aus der Domain `[('note','!=',False)]`, die auch leere Strings
zaehlt. Die Abweichung betrifft ausschliesslich `note`.
Dokument: `docs/o11-o18-verkauf-r4-note-html.md`.

**R5 `invoice_lines` / Modellwechsel `account.invoice.line` -> `account.move.line`:
ABGESCHLOSSEN (29.09.2026).** Beide Systeme nutzen die Verknuepfungstabelle
`sale_order_line_invoice_rel` (Spalten `order_line_id` / `invoice_line_id`); nur das Zielmodell der
Rechnungszeile hat gewechselt. Odoo 11: 1.863 von 4.011 Auftragszeilen verknuepft (= Zeilen mit
`qty_invoiced` > 0) aus 1.201 Rechnungen (1.194 Kundenrechnungen, 7 Gutschriften; Jahre 2019-2026),
1.198 Auftraege betroffen; `invoice_ids`/`invoice_count` sind in beiden Systemen berechnet.
Transformationsregel (Entscheidung Anna): keine Wertuebernahme - die Verknuepfung wird nach der
Migration beider Seiten ueber einen stabilen fachlichen Schluessel (Rechnungsnummer,
Position/Reihenfolge, ggf. Produkt/Auftragszeilenbezug) wiederhergestellt, niemals ueber Odoo-11-IDs;
Verbindung erst, wenn die Rechnungen in Odoo 18 vorhanden und eindeutig zuordenbar sind; werden
Rechnungen nicht migriert, wird keine historische Verknuepfung gesetzt. `qty_invoiced`,
`amount_invoiced` und `invoice_status` werden NICHT aus Odoo 11 uebernommen, sondern von Odoo 18
aus den Rechnungsdaten berechnet. Keine Aenderung an Odoo 18 erforderlich.
Dokument: `docs/o11-o18-verkauf-r5-invoice-lines.md`.

**R6 `tag_ids` / Modellwechsel `crm.lead.tag` -> `crm.tag`: ABGESCHLOSSEN (29.09.2026).** Die
Verknuepfungstabelle des Verkaufs heisst in Odoo 18 unveraendert `sale_order_tag_rel`
(`order_id` / `tag_id`); die Lead-Tabelle heisst jetzt `crm_tag_rel`. Verkauf: 1 von 2.464
Auftraegen mit Stichwort (A-1900710, Zustand Abgebrochen, "Up-Sell"); CRM: 6.155 von 6.968 Leads.
Odoo 18 (Testbestand) fuehrt 0 `crm.tag`-Datensaetze. Transformationsregel (Entscheidung Anna):
Zuordnung ausschliesslich ueber den Tag-Namen; fehlende Tags mit Name und Farbindex aus Odoo 11
anlegen; Verknuepfung anschliessend ueber `sale_order_tag_rel` bzw. `crm_tag_rel`; bei mehreren
gleichnamigen Tags keine automatische Zuordnung, sondern Konfliktmeldung.
Die 44 Odoo-11-Tags sind als migrationsrelevante Stammdaten vollstaendig dokumentiert (Name,
Farbindex, Nutzung; 13 davon ohne Verwendung) und werden spaeter in der Stammdatenmigration zentral
einmal angelegt, damit Verkauf und CRM dieselben Tags verwenden - jetzt wird nichts angelegt.
Dokument: `docs/o11-o18-verkauf-r6-tag-ids.md`.

**R7 `layout_category_id` / `layout_category_sequence`: ABGESCHLOSSEN (29.09.2026).** Beide Felder
werden bewusst NICHT migriert: Das Modell `sale.layout.category` ist in Odoo 11 nicht registriert
(Leseversuch und `fields_get` scheitern), die im Verkauf verwendete ITK-Druckvorlage gibt keine
Sektion aus (Abschnittsblock auskommentiert), `layout_category_sequence` ist immer 0, und Odoo 18
verwendet die Standardlogik mit Abschnitts-/Notizzeilen.
**Dokumentationskorrektur:** Nicht "alle 1.367 Werte 0", sondern genau 2 von 4.011 Auftragszeilen
mit `layout_category_id` = Sektion "Dienstleistungen" (Zeilen zu A-1900915 und A-1900906);
Korrektur in Lueckenanalyse, Abschlussdokument und dieser Checkliste eingetragen.
Entscheidung: fuer diese beiden Auftraege werden KEINE kuenstlichen Abschnittszeilen angelegt,
die Zuordnungen nur dokumentiert. Keine Aenderung an Odoo 18 erforderlich.
Dokument: `docs/o11-o18-verkauf-r7-layout-category.md`.

**R8 `amt_invoiced` / `amt_to_invoice`: ABGESCHLOSSEN (29.09.2026).** Odoo 11 fuehrt beide Werte
gespeichert und steuerinklusive; Odoo 18 fuehrt `amount_invoiced` / `amount_to_invoice` berechnet
und NICHT gespeichert (Import technisch unmoeglich). Berechnung: `amount_invoiced` = Summe
`price_total` der verknuepften, GEBUCHTEN Rechnungszeilen (Gutschriften negativ);
`amount_to_invoice` = (price_total / Menge) x (abzurechnende Menge - abgerechnete Menge).
End-to-End-Test: Entwurfsrechnung -> amount_invoiced 0,00 / amount_to_invoice 120,00; gebuchte
Rechnung -> 120,00 / 0,00.
Entscheidung: keine Wertuebernahme, Odoo 18 berechnet neu (Voraussetzungen: Rechnungen und
Rechnungszeilen migriert und gebucht, Verknuepfung nach R5). Ohne Rechnungsmigration gilt die
ausdruecklich dokumentierte Erwartung `amount_invoiced` 0, `amount_to_invoice` = offener Betrag,
`invoice_status` ggf. "to invoice" - nicht als Migrationsfehler zu deuten. Ziel bleibt, die
historischen Rechnungsbezuege zu erhalten, damit die Werte identisch zu Odoo 11 berechnet werden.
Dokument: `docs/o11-o18-verkauf-r8-invoiced-amounts.md`.

**ABSCHLUSSMARKIERUNG 29.09.2026 (Entscheidung Anna): VERKAUF FUNKTIONAL VOLLSTAENDIG UND
MIGRATIONSVORBEREITET.** Hinweis: Die Regeln R1 bis R8 sind ausschliesslich vorbereitete Regeln
fuer die spaetere Datenmigration und keine offenen Funktionsluecken im Odoo-18-Verkaufsmodul
(Gesamtstatus `docs/o11-o18-verkauf-gesamtstatus-r1-r8.md`, Abschlussdokument
`docs/o11-o18-verkauf-abschluss.md`).
Reihenfolge der spaeteren Datenmigration (dokumentiert, nicht ausgefuehrt): 1. Stammdaten zuerst
(Mengeneinheiten R1, Tags R6) - 2. Auftraege und Auftragszeilen - 3. Rechnungen/Rechnungszeilen im
Bereich Abrechnung - 4. Verknuepfung Auftragszeile <-> Rechnungszeile gemaess R5 - 5. berechnete
Felder wie amount_invoiced, amount_to_invoice und invoice_status durch Odoo 18 neu berechnen (R8).
Es wurden keine Odoo-11-Daten migriert; Odoo 11 ausschliesslich read-only. Teil 5 Block 3 und 4
wurden im echten Browser auf der Abnahmeumgebung abgenommen (243 OK / 0 FEHL als Aggregatlauf,
43 OK / 0 FEHL im Klickpfad).
Naechstes Modul noch nicht begonnen.


**Historie Teil 1 (24.09.2026):** Nachweise damals `scripts/verify_s121_verkauf_menue.py`
41 OK / 0 FEHL (ein Lauf: Odoo 11 read-only, Odoo 18 lokal und VM) und
`scripts/browser_verkauf_menue.py` lokal 43 OK / VM 43 OK; seit Block 3 fuehrt das Menuewerkzeug
42 OK, weil der Bericht "Verkaufsauftraege aller Kanaele" jetzt als sichtbarer Menuepunkt
geprueft wird.

**Nachtrag (Session 121, 24.09.2026):** Zur Klarstellung gegengeprueft - `confirmation_date`
("Bestätigung am", Odoo 11: 2.437 von 2.461 Auftraegen) ist in Odoo 18 vorhanden und in
`itk_sale_management` 18.0.1.1.0 umgesetzt, und die Mehrzustands-Browserpruefung auf der VM wurde
in Session 117 durchgefuehrt (`browser_auftraege_pruef.py` lokal 9 OK / VM 9 OK). Die
entsprechenden Hinweise in Abschnitt 6.13 sind damit veraltet.

**Entscheidungen von Anna (24.09.2026):**
1. "Verkaufsauftraege aller Kanaele" wird in Odoo 18 nachgebaut, Odoo-18-konform als Auswertung auf
   `sale.report` (Gruppierung Vertriebskanal, Filter aktuelles Verkaufsjahr) - kein Nachbau des
   Odoo-11-Modells `report.all.channels.sales`. Umgesetzt in Teil 4.
2. Default-Filter "Meine Angebote": siehe bewusste Abweichungen (Abschnitt 3 des Abschlussdokuments).
3. Die 15 benutzerspezifischen Filter werden nicht migriert; die 3 als Standard markierten Favoriten
   wurden read-only geprueft (0 systemweit, zwei nur Gruppierung, einer persoenliche Projektauswahl)
   - keine Migration, kein Nachbau.
4. Odoo-18-Zusatzfunktionen (Angebotsvorlagen, Kopf-/Fusszeilen und weitere) bleiben erhalten.

**Entscheidungen von Anna (24.09.2026):**
1. "Verkaufsauftraege aller Kanaele" wird in Odoo 18 nachgebaut, Odoo-18-konform als Auswertung auf
   `sale.report` (Gruppierung Vertriebskanal, Filter aktuelles Verkaufsjahr) - kein Nachbau des
   Odoo-11-Modells `report.all.channels.sales`. Einordnung: Teil 4.
2. Default-Filter "Meine Angebote" wird aus dem Menue Auftraege/Angebote entfernt; der Filter bleibt
   in der Suchleiste auswaehlbar. Einordnung: Teil 3 (mit Deploy und Browser-Abnahme auf der VM).
3. Die 15 benutzerspezifischen Filter werden nicht migriert. Die 3 als Standard markierten Favoriten
   wurden read-only geprueft: 0 systemweit, zwei nur Gruppierung (Status, Verkaeufer), einer
   persoenliche Projektauswahl (A-Tool/Comm-Unity). **Entschieden am 24.09.2026: keine Migration und
   kein Nachbau - die beiden Gruppierungen sind in Odoo 18 ueber "Gruppieren nach" verfuegbar, der
   dritte ist ein persoenlicher bzw. projektspezifischer Benutzerfilter.**
4. Odoo-18-Zusatzfunktionen (Angebotsvorlagen, Kopf-/Fusszeilen und weitere) bleiben erhalten.

**TEIL 1 ENDGUELTIG ABGESCHLOSSEN (24.09.2026): keine offenen Punkte.**
Offen im Bereich Verkauf nur noch die Teile 2 bis 5.

**Teil 2 - Feldinventar sale.order und sale.order.line (24.09.2026, Session 121): ANALYSIERT.**

Dokument: `docs/o11-o18-vergleich-verkauf-teil2.md`. Nur Analyse, keine Aenderung an Odoo 18,
keine Datenmigration, Odoo 11 read-only.

```
sale.order        Odoo 11 89 Felder | Odoo 18 110 | gemeinsam 58 | nur O11 31 | nur O18 52
sale.order.line   Odoo 11 53 Felder | Odoo 18  80 | gemeinsam 39 | nur O11 14 | nur O18 41
Typ-/Relationsabweichungen 5, alle Odoo-18-Umbenennungen (account.invoice -> account.move,
crm.lead.tag -> crm.tag, product.uom -> uom.uom, note text -> html, invoice_lines
account.invoice.line -> account.move.line)
ITK-Felder: 8 auf sale.order, 4 auf sale.order.line, alle mit gleichem Namen/Typ/Relation vorhanden
Uebersetzungs-/Feldbefunde: activity_state heisst in Odoo 11 auf Deutsch faelschlich "Bundesland";
tag_ids hat 1 von 2.461 Auftraegen belegt (Korrektur der Angabe aus Session 117)
Stammdaten vor der Migration: Zahlungsbedingungen (613 belegt; "30 Tage netto" mit 2 Auftraegen
fehlt in Odoo 18), Preisliste, Verkaeufer (31 verschiedene), Vertriebskanal (4 genutzt),
Stichwoerter (Odoo 18 derzeit 0 crm.tag)
```

Nachweise: `scripts/verify_s121_verkauf_teil2.py` -> 111 OK / 0 FEHL (Odoo 11 read-only,
Odoo 18 lokal und VM in einem Lauf); `scripts/analyse_verkauf_teil2_felder.py`,
`scripts/baue_verkauf_teil2_doku.py`. Gegenprobe: `ir.model.fields` und `fields_get` liefern
dieselben Feldmengen (je Modell und Instanz).

**Entscheidungen von Anna (24.09.2026) zu Teil 2:**
1. `note` (2.439 Auftraege): Inhalt vollstaendig uebernehmen, Zeilenumbrueche fuer das Odoo-18-HTML-Feld
   korrekt in HTML umsetzen.
2. Zahlungsbedingung "30 Tage netto" (2 Auftraege): keine Dublette anlegen, Zuordnung auf das
   vorhandene Odoo-18-"30 Tage" (id 4), fachlich identisch (100 % nach 30 Tagen ab Rechnungsdatum).
3. Stichwort "Up-Sell" (1 Auftrag A-1900710): nicht verlieren, als spaeterer Stammdaten-/
   Migrationsschritt vorbereitet (Odoo 18 hat derzeit 0 `crm.tag`).
4. Felder aus `sale_stock` und `sale_timesheet` duerfen entfallen (Module bewusst nicht installiert),
   kein Nachbau, weiterhin dokumentiert.
5. Preislisten: spaeterer Datenmigrationsschritt, Zuordnung vollstaendig vorbereitet - alle 25 in
   Odoo 11 verwendeten Preislisten (Summe 2.461 Auftraege) auf die Odoo-18-Preisliste id 34
   ("Preisliste 2026 + Valorisierung", EUR, aktiv). EUR bleibt verbindlich.

Verbindliche Regeln: `migration/verkauf_migrationsregeln.json` (Werkzeug
`scripts/baue_verkauf_migrationsregeln.py`, Zahlen read-only gemessen).

**Neuer Befund (KLAERUNG NOETIG):** Odoo 18 fuehrt die Zahlungsbedingung "14 Tage" (id 12) mit
`nb_days = 0` (Zahlung sofort), Odoo 11 mit 14 Tagen ab Rechnungsdatum. Betroffen sind 515 Auftraege.
Vor der Migration entscheiden: Odoo-18-Eintrag auf 14 Tage korrigieren (empfohlen) oder andere
Zuordnung waehlen. Bisher wurde nichts geaendert.

**TEIL 2 ABGESCHLOSSEN (24.09.2026, lokal und VM). Keine Aenderung an Odoo 18.**
Offen im Bereich Verkauf: Teile 3 bis 5 (Formulare/Reiter begonnen; Buttons, Filter, Ansichten,
Berichte, Abschluss).

**Teil 3, Schritt 1 - Formulare und Reiter (24.09.2026, Session 121): ANALYSIERT UND ABGENOMMEN.**

Dokument: `docs/o11-o18-vergleich-verkauf-teil3-formulare-reiter.md`. Nur Analyse, keine Aenderung
an Odoo 18, keine Datenmigration, Odoo 11 read-only. Buttons, Smart Buttons, Statuswechsel, Filter,
Gruppierungen und Suche sind ausdruecklich noch nicht bearbeitet.

```
Formularansichten sale.order       Odoo 11 12 | Odoo 18 8 (lokal = VM)
Formularansichten sale.order.line  Odoo 11  0 (eingebettet) | Odoo 18 1 (form.readonly)
Reiter Odoo 11 (2)   Auftragszeilen, Weitere Informationen
Reiter Odoo 18 (4)   Auftragspositionen, Optionale Produkte, Angebotsbauer, Weitere Informationen
  Sichtbarkeit: Optionale Produkte nur bei Status Angebot/gesendet; Angebotsbauer nur bei Kunde und
  is_pdf_quote_builder_available (im gesamten Testbestand False -> nicht sichtbar)
Gruppen "Weitere Informationen": Odoo 11 Lieferadresse, Information Umsatz, Abrechnung,
  Berichtswesen -> Odoo 18 Versand, Verkauf, Rechnungsstellung, Nachverfolgung
Hauptbereich: Odoo 11 25 Feldverweise -> Odoo 18 32; alle fachlichen Odoo-11-Bestandteile
  vorhanden, weggefallen nur Zaehler aus sale_stock/sale_timesheet/sale_payment/website_sale
ITK-Erweiterung (itk_sale_management "sale.order.form (itk)"): Kundenfeld ersetzt und ITK-Kontakte
  (Verkaufskontakt, Verwaltungskontakt, Technischer Kontakt, Produktkategorie) direkt danach;
  user_id und confirmation_date nach date_order
```

Nachweise: `scripts/verify_s121_verkauf_teil3_reiter.py` 64 OK / 0 FEHL (Odoo 11 read-only, lokal
und VM); `scripts/browser_verkauf_formular_reiter.py` VM 16 OK / 0 FEHL, lokal 16 OK / 0 FEHL mit
echten Klicks (Reiter sichtbar, Reiterwechsel, Gruppen VERKAUF/RECHNUNGSSTELLUNG/VERSAND/
NACHVERFOLGUNG, 0 JS-/RPC-Fehler; Screenshots `Desktop\Odoo18-Abnahme-Session121\03_Reiter_*`).

**Entscheidungen von Anna (24.09.2026) und Umsetzung (lokal; VM-Deploy offen):**
1. Reiter "Auftragspositionen" auf **"Auftragszeilen"** umbenannt (Odoo-11-Wortlaut). Umgesetzt in
   `itk_sale_management` **18.0.1.2.0**, eigene Ansicht an der Wurzel-View `sale.view_order_form`
   (priority 99, `xpath //page[@name='order_lines']`, `position="attributes"`). Lokal nach
   Modul-Upgrade geprueft: erster Reiter zeigt "Auftragszeilen"; Browser lokal 16 OK / 0 FEHL.
2. Odoo-11-Gruppe "Lieferadresse" wird **nicht nachgebaut** (Felder aus `sale_stock`).
3. Zahlungsbedingung **"14 Tage" korrigiert**: `nb_days` von 0 (Zahlung sofort) auf 14
   (14 Tage nach Rechnungsdatum). Werkzeug `scripts/apply_verkauf_stammdaten.py --instanz lokal|vm
   [--pruefen]`, idempotent; lokal 3 OK / 0 FEHL, Prueflauf 3 OK / 0 FEHL. "Sofortige Zahlung"
   (nb_days 0) und "30 Tage" (nb_days 30) unveraendert. Browser lokal 5 OK / 0 FEHL
   (Screenshot 05_Zahlungsbedingung_14_Tage_lokal.png).

**TEIL 3, SCHRITT 1 ABGENOMMEN (lokal und VM), Umsetzung auf der VM verifiziert.**
Offen in Teil 3: Statuswechsel, Filter, Gruppierungen, Suche.

**Teil 3, Schritt 2 - Buttons und Smart Buttons (24.09.2026, Session 121): ABGENOMMEN.**

Dokument: `docs/o11-o18-vergleich-verkauf-teil3-buttons.md`. Buttons und Smart Buttons vollstaendig
verglichen (Odoo 11 gegen Odoo 18), Klicktests mit echtem Browser lokal und auf der VM.

```
Kopf-Buttons  Odoo 11 10 verschiedene | Odoo 18 11 verschiedene
  zugeordnet: Bestaetigen, Stornieren, Auf Angebot setzen, Sperren (action_lock statt action_done),
  Entsperren, Drucken (Odoo 18 im Zahnrad), Rechnung erstellen (Aktion 428 statt 425, gleicher
  Assistent sale.advance.payment.inv), Per E-Mail versenden, Pro-forma-Rechnung senden
  entfaellt:   Wiederherstellungs-E-Mail senden (Website; in Odoo 11 0 Warenkoerbe)
  neu in O18:  Vorschau, Transaktion erfassen, Transaktion stornieren
Smart Buttons Odoo 11 7 | Odoo 18 3 (Abonnements, Rechnungen, Einkauf)
  entfaellt:   Warenauslieferung (sale_stock), Zeiterfassung/Projekte/Aufgaben (sale_timesheet),
               Zahlungen als Zaehler (Odoo 18 ueber transaction_ids)
Zeilenbereich Odoo 11 keine | Odoo 18 vier Zusatzbuttons (Katalog, Rabatt, Zum Auftrag, Steuern)
Druckberichte mit Bindung an sale.order: Odoo 18 PDF-Angebot, Angebot/Auftrag, ITK-Angebot/Auftrag,
  PRO-FORMA-Rechnung (im Klicktest alle erreichbar)
```

Nachweise: Klicktest `scripts/browser_verkauf_buttons_klicktest.py` lokal 26 OK / 0 FEHL und
VM 26 OK / 0 FEHL (E-Mail-Assistent, Vorschau, Bestaetigen mit automatischer Sperre, Entsperren,
Smart-Button-Zaehler gegen 0 geprueft, Storno-Dialog mit "Verwerfen", "Auf Angebot setzen",
0 JS-/RPC-Fehler); Testauftrag jeweils angelegt und wieder geloescht. Inventar:
`scripts/analyse_verkauf_teil3_buttons.py`.

Regressionpruefung nach dem VM-Deploy: `verify_s121_verkauf_teil3_reiter.py` 64 OK,
`verify_s121_verkauf_teil2.py` 111 OK, `verify_s117_auftraege.py` 65 OK (lokal und VM),
`verify_s118_abo.py` 19 OK (VM), Browser Reiter 16 OK, Browser Zahlungsbedingung 5 OK,
`browser_auftraege_pruef.py` 7 OK / 1 FEHL (Testdatenmangel: kein Auftrag mit Rechnung vorhanden,
lokal identisch - kein Regressionsbefund).

**Befunde:** Odoo 18 storniert ueber den Assistenten `sale.order.cancel` (Bestaetigungsdialog mit
optionalem E-Mail-Versand) statt direkt. "Bestellungen automatisch sperren" ist in Odoo 18 aktiv,
ein bestaetigter Auftrag ist sofort gesperrt. Beides dokumentiert, keine Anpassung vorgeschlagen.

**Merke (F34 erneut bestaetigt):** Nach jedem Upgrade von `itk_sale_management` auf der VM muessen
die Feldbeschriftungen mit `scripts/apply_sale_labels.py --instanz vm` nachgezogen werden
(vorher 3 Abweichungen, danach 65 OK / 0 FEHL).

**TEIL 3, SCHRITT 2 ABGENOMMEN (lokal und VM).** Offen in Teil 3: Statuswechsel, Filter,
Gruppierungen, Suche. Danach Teil 4 (Ansichten und Berichte) und Teil 5 (Abschluss).

**Teil 3, Schritt 3 - Statuswechsel (24.09.2026, Session 121): ABGENOMMEN (lokal und VM).**

Dokument: `docs/o11-o18-vergleich-verkauf-teil3-statuswechsel.md`.

```
Zustaende Odoo 11: draft, sent, sale, done, cancel (5); Statusleiste draft,sent,sale
Zustaende Odoo 18: draft, sent, sale, cancel (4); Statusleiste draft,sent,sale
  Odoo 11 Sperre = Zustand done (nie benutzt, 0 Datensaetze)
  Odoo 18 Sperre = Feld locked (in der Testdatenbank ist "Bestellungen automatisch sperren" aktiv)
Bestand Odoo 11 (lesend): draft 5, sent 0, sale 2311, done 0, cancel 147, gesamt 2463
Uebergaenge Odoo 18: Bestätigen (draft/sent -> sale, danach automatisch gesperrt),
  Sperren/Entsperren (action_lock/action_unlock statt action_done),
  Stornieren (draft/sent/sale entsperrt -> cancel, ueber den Assistenten sale.order.cancel mit
  "Senden und stornieren"/"Stornieren"/"Verwerfen"; im gesperrten Auftrag nicht sichtbar),
  Auf Angebot setzen (cancel -> draft), sent wird ueber den E-Mail-Versand gesetzt
Klicktest echtes Browser: lokal 35 OK / 0 FEHL, VM 35 OK / 0 FEHL, je 0 JS-/RPC-Fehler
  Testauftrag angelegt und geloescht (lokal 18, VM 20 Auftraege wie vorher)
Prueflauf: scripts/verify_s121_verkauf_teil3_status.py 53 OK / 0 FEHL (Odoo 11 lesend, lokal, VM)
Mapping fuer die Datenmigration in migration/verkauf_migrationsregeln.json (Abschnitt statuswechsel)
```

**ENTSCHIEDEN (Anna, 28.09.2026): nur dokumentieren.** Bestaetigte Auftraege waren in Odoo 11
bearbeitbar, Odoo 18 nutzt zusaetzlich `locked`. Keine Importregel auf Produktivdaten, keine
Uebernahme oder Aenderung der 2311 Auftraege.

**Merke:** Odoo 18 storniert nur ueber Rueckfrage und nur bei entsperrtem Auftrag; ein Import mit
`state=sale` loest `action_confirm` nicht aus, `locked` muss ausdruecklich gesetzt werden.

**Nur dokumentiert (Entscheidung Anna, 28.09.2026):** Bestaetigte Verkaufsauftraege waren in
Odoo 11 bearbeitbar; Odoo 18 verwendet zusaetzlich das Feld `locked`. Keine Importregel auf
Produktivdaten anwenden, keine Auftraege uebernehmen oder veraendern - weiterhin
Funktions- und Migrationsvorbereitung.

**Teil 3, Schritt 4 - Suchfelder, Filter, Gruppierungen, Suche (28.09.2026, Session 121):
lokal umgesetzt und abgenommen, VM-Abnahme offen.**

Dokument: `docs/o11-o18-vergleich-verkauf-teil3-filter-suche.md`.

```
Verglichen je Menue (Angebote, Auftraege, Abzurechnende Auftraege, Upselling) aus dem Arch:
  Suchfelder, Filter, Gruppierungen, Default-Kontext; Odoo 11 nur lesend
Suchfelder: name/partner_id/user_id/team_id/final_customer_id/product_category_id in beiden gleich;
  Produkt ueber Auftragszeilen gleichwertig; analytic_account_id in Odoo 11 auf 0 Auftraegen belegt
  und in Odoo 18 nicht mehr vorhanden -> kein Nachbau; Odoo-18-Zusatz campaign_id bleibt
Filter: in Odoo 18 ergaenzt (Modul itk_sale_management 18.0.1.3.0, nur ergaenzt, nichts entfernt):
  "Ungelesene Nachrichten" (message_needaction), "Meine Aktivitaeten" (activity_ids.user_id = uid),
  "Angebote (Entwurf)" (state = draft), "Kostenvoranschlag gesendet" (state = sent)
Default-Filter: search_default_my_quotation aus sale.action_quotations und
  sale.action_quotations_with_onboarding entfernt (Odoo 11 oeffnete ohne Voreinstellung);
  Filter bleibt auswaehlbar (Entscheidung aus Teil 1 damit umgesetzt)
Gruppierungen: Verkaeufer, Kunde, Endkunde, Produktkategorie, Auftragsmonat alle vorhanden
  (Odoo-18-Label Vertriebsmitarbeiter/Auftragsdatum); Odoo-18-Zusatzgruppen bleiben
Bewusst nicht nachgebaut: "Von Website", "Zu sendende Wiederherstellungs-E-Mail" (Website nicht
  migriert), Odoo-11-Filter "Verkauf" mit ungueltigem Zustand progress (defekt), Bestaetigte
  Auftraege (durch Verkaufsauftraege abgedeckt)
Nachweise lokal: verify_s121_verkauf_teil3_filter.py 78 OK / 0 FEHL (Odoo 11 43 OK als Ausgangslage),
  browser_verkauf_filter_suche.py 19 OK / 0 FEHL, 0 JS-/RPC-Fehler
Nachweise VM (28.09.2026): Modul-Upgrade 18.0.1.3.0 ohne Fehler, Prueflauf 199 OK / 0 FEHL
  (Odoo 11 43 + lokal 78 + VM 78), Browserabnahme 19 OK / 0 FEHL, 0 JS-/RPC-Fehler
Keine Odoo-18-Funktion entfernt (Vorher/Nachher-Vergleich, nur Ergaenzungen); keine
  Schreibvorgaenge, keine Datenmigration
```

**Teil 4, Schritt 1 - Listen-, Kanban-, Pivot-, Graph- und Kalenderansichten (28.09.2026,
Session 121): lokal umgesetzt und abgenommen, VM-Abnahme offen.**

Dokument: `docs/o11-o18-vergleich-verkauf-teil4-ansichten.md`.

```
Verglichen je Menueaktion (Angebote, Auftraege, Pipeline, Abzurechnen, Upselling):
  Ansichtsarten, Listenspalten mit Reihenfolge und optional-Kennzeichnung, Kanban-Kartenfelder,
  Pivot- und Graph-Felder, Kalenderfelder, Default-Gruppierungen; Odoo 11 nur lesend
Odoo 11 (alle vier Menues): tree, kanban, form, calendar, pivot, graph; eine Listenansicht mit
  11 festen Spalten (u.a. name "Auftragsnummer", confirmation_date "Bestelldatum")
Odoo 18: list, kanban, form, calendar, pivot, graph, activity; 22 bzw. 24 Spalten mit
  optionalen Spalten; Kanban/Pivot/Graph gleichwertig; Aktivitaetenansicht als Odoo-18-Zusatz
Luecke: Spalte "Bestelldatum" (confirmation_date) fehlte in Odoo 18 -> ergaenzt
  (itk_sale_management 18.0.1.4.0, views/sale_order.xml, optional="show", Odoo-11-Wortlaut)
Unterschied: Odoo 11 hatte einen Monatskalender nach Auftragsdatum; Odoo 18 liefert den
  Aktivitaetenkalender (sale.view_sale_order_calendar, date_start=activity_date_deadline).
  Nichts geaendert; offene Entscheidung mit drei Optionen im Dokument (Abschnitt 7)
Nachweise lokal: Prueflauf Odoo 11 36 OK / 0 FEHL, lokal 55 OK / 0 FEHL;
  Browserabnahme 11 OK / 0 FEHL (Liste mit Bestelldatum, Spaltenauswahl, Kanban, Pivot, Graph,
  Kalender, 0 JS-/RPC-Fehler)
Offen: Entscheidung zur Kalenderansicht (Abschnitt 7)
VM-Abnahme 28.09.2026: Modul 18.0.1.4.0 auf der VM upgegradet, Prueflauf 146 OK / 0 FEHL
  (Odoo 11 36 + lokal 55 + VM 55), Browserabnahme VM 11 OK / 0 FEHL, keine Schreibvorgaenge
  (Bestand unveraendert 20 Auftraege / 29 Zeilen), Feldbeschriftungen per
  apply_sale_labels.py --instanz vm nachgezogen (verify_s117_auftraege VM 65 OK / 0 FEHL)
```

**Kalenderergaenzung Option A (Entscheidung Anna, 28.09.2026): Auftragskalender nach Auftragsdatum.**

```
itk_sale_management 18.0.1.5.0, views/sale_order_views_kalender.xml, nur ergaenzt:
  Kalenderansicht view_saleorder_kalender_itk (date_start=date_order, color=state, Monat)
  Aktion action_saleorder_kalender_itk (Auftragskalender, view_mode calendar,list,form,
    Zuordnung ueber view_ids; in Odoo 18 ist `views` nicht gespeichert)
  Menuepunkt menu_saleorder_kalender_itk unter Verkauf/Auftraege (Reihenfolge 25)
Odoo-18-Aktivitaetenkalender (sale.view_sale_order_calendar) unveraendert; Verkaufsmenues
  unveraendert (Ansichtsarten und Kontexte geprueft)
Browserabnahme lokal: 16 OK / 0 FEHL, 0 JS-/RPC-Fehler. Datumsbasis belegt: im Monat
  September 2026 zeigt der Kalender genau S00198 und S00200 (Auftragsdatum im Monat),
  Auftraege mit fruehrerem Auftragsdatum erscheinen nicht; der Aktivitaetenkalender zeigt
  einen anderen Ereignissatz.
Prueflauf: scripts/verify_s121_verkauf_kalender.py (Odoo 11 lesend + lokal + VM)
VM-Abnahme 28.09.2026: Modul 18.0.1.5.0 auf der VM upgegradet (ohne Fehler), Prueflauf
  33 OK / 0 FEHL (Odoo 11 + lokal + VM), Browserabnahme auf der VM 16 OK / 0 FEHL,
  0 JS-/RPC-Fehler; Menuepunkt Verkauf/Auftraege/Auftragskalender auf der VM vorhanden;
  Datumsbasis belegt (erwartet und angezeigt: S00198, S00199, S00201, S00203);
  Aktivitaetenkalender unveraendert; keine Schreibvorgaenge (20 Auftraege / 29 Zeilen);
  Feldbeschriftungen per apply_sale_labels.py --instanz vm nachgezogen
```

**Teil 4, Schritt 2 - Verkaufsberichte (28.09.2026, Session 121): UMGESETZT UND ABGENOMMEN
(lokal und VM).**

Dokument: `docs/o11-o18-vergleich-verkauf-teil4-berichte.md`.

```
UMGESETZT in itk_sale_management 18.0.1.6.0 (neue Datei views/sale_report_views_kanaele.xml):
  Aktion "Verkaufsaufträge aller Kanäle" auf sale.report, view_mode pivot,graph,list,
    Domain [('state','!=','cancel')] (nur nicht stornierte Auftraege),
    Kontext {'search_default_itk_current_year': 1, 'pivot_measures': ['price_total']},
    Ansichten ueber view_ids (eigene Pivot, sale.report.graph, sale.report.view.list)
  Pivotansicht: Zeile Auftragsreferenz (name), Spalte Vertriebskanal (team_id),
    Mass Total (price_total) - Anordnung wie Odoo 11
  Suchansicht (erbt sale.view_order_product_search, nur Ergaenzungen):
    Filter "Aktuelles Verkaufsjahr" (itk_current_year), Gruppierung "Vertriebskanal" (itk_channel)
  Menuepunkt Verkauf/Berichtswesen/Verkaufsaufträge aller Kanäle, Reihenfolge 15
  Modul nicht nachgebaut: report.all.channels.sales existiert in Odoo 18 weiterhin nicht
Befund: aktive Gruppenfilter-Facette macht in Odoo 18 den Kanal zur Zeile und verdraengt die
  Auftragsreferenz; deshalb liefert die Pivotansicht die Odoo-11-Anordnung ueber
  type="row"/type="col", der Filter "Vertriebskanal" bleibt zum Umschalten verfuegbar.
ABNAHME 28.09.2026:
  Prueflauf scripts/verify_s121_verkauf_teil4_bericht_kanaele.py: 84 OK / 0 FEHL
    (Odoo 11 lesend + Odoo 18 lokal + Odoo 18 VM)
  Browser scripts/browser_verkauf_bericht_kanaele.py: lokal 18 OK / 0 FEHL,
    VM 18 OK / 0 FEHL, 0 JavaScript-Fehler, 0 RPC-Fehler
  Belegwerte VM: Menuepunkt oeffnet, Facette "Aktuelles Verkaufsjahr" aktiv, Zeilen sind
    Auftragsreferenzen (S00007 ... S00203), Spalte "Verkauf" (Vertriebskanal), Mass "Gesamt"
    (price_total), Pivot-Summe 863,80 = Summe price_total nicht stornierter Positionen 2026
    (mit stornierten 1.055,80) -> stornierte ausgeschlossen; lokal 835,00 (mit stornierten 1.027,00)
  Erhalt: Odoo-18-Filter (Angebote, Verkaufsauftraege, Auftragsdatum, Abzurechnen, Komplett
    abgerechnet) und Gruppierungen (Vertriebsmitarbeiter, Verkaufsteam, Kunde, Kundenland,
    Kundenbranche, Produkt, Produktvariante, Produktkategorie, Status) unveraendert;
    Aktionen 416/417 der Verkaufsanalyse oeffnen unveraendert
  Bestand unveraendert: lokal 18 Auftraege / 28 Zeilen, VM 20 Auftraege / 29 Zeilen;
    verify_s117_auftraege.py VM 65 OK / 0 FEHL (nach apply_sale_labels.py --instanz vm)
Git: PR #116 -> main 98585b4 (lokal = GitHub = VM).
Noch keine Datenmigration; Odoo 11 wurde ausschliesslich lesend gelesen.
```

**Teil 4, Schritt 3 - Druckberichte (29.09.2026, Session 121): VERGLEICHEN UND ABGENOMMEN
(lokal und VM).**

**Teil 5, Block 1 und 2 (29.09.2026, Session 121): Regressionstest und Lueckenanalyse;
Luecke "Lageranbindung des Verkaufs" geschlossen.**

Dokumente: `docs/o11-o18-vergleich-verkauf-teil5-abschluss.md`,
`docs/o11-o18-vergleich-verkauf-teil5-luecken.md`, `docs/o11-o18-verkauf-teil5-lageranbindung.md`.

```
Block 1 Regressionstest: scripts/abschluss_verkauf_regression.py, 11 Prueflaeufe ueber
  lokal und VM: 884 OK / 0 FEHL; nachgezogen: Menueumfang Odoo 18 37 -> 39 (Auftragskalender
  und Bericht "Verkaufsauftraege aller Kanaele"), Kanaele-Bericht gilt als vorhanden.
Block 2 Lueckenanalyse: Felder, Menueziele/Modelle, Automatismen, Server-Aktionen, Mailvorlagen,
  Stammdaten (Zahlungsbedingungen, Preislisten, Teams, UTM, Produkte, Steuern), Module und
  Nutzungsspuren (Lagerbelege, gelieferte Mengen, Zeiterfassungen, Zahlungstransaktionen).
  Ergebnis: genau eine echte strukturelle Luecke - Lageranbindung des Verkaufs.
  Odoo 11: stock/stock_account/sale_stock installiert, 2.463 Auftraege mit Lager,
  235 mit Lieferungen, 238 Lagerbelege mit Verkaufsbezug. Odoo 18: Module und Felder fehlten.
  Keine Luecke (dokumentiert): Feldumbenennungen (amt_invoiced -> amount_invoiced,
  amt_to_invoice -> amount_to_invoice, price_reduce -> price_reduce_taxexcl/taxinc),
  Reportlayout-Kategorien (korrigierte Messung 29.09.2026: 2 Auftragszeilen mit Sektion
  "Dienstleistungen", Sequenz immer 0; Modell in Odoo 11 nicht registriert),
  crm.claim (0 Datensaetze), crm.lead.tag -> crm.tag, crm.opportunity.report -> crm.lead,
  report.all.channels.sales (in Teil 4 ersetzt), Mailvorlagen ohne Nutzungsspur in Odoo 11
  (2.271 E-Mail-Nachrichten, aber 0 Anhaenge an Nachrichten), Stammdaten (Datenmigrationsthema),
  Zeiterfassung und Online-Zahlung (0 Verwendungen), uebrige Module gehoeren zu anderen Bereichen.
Schliessung der Luecke (Freigabe Anna): stock 18.0.1.1, stock_account 18.0.1.1 und sale_stock
  18.0.1.0 in Odoo 18 installiert (lokal und VM); delivery bleibt wie in Odoo 11 uninstalliert.
  Nebenschritte: itk_product 18.0.1.0.3 (product.template.responsible_id auf die
  Odoo-18-Standarddefinition company_dependent umgestellt; vorher Abbruch "cannot cast type
  integer to jsonb"), leere Spalte product_template.responsible_id in den Testdatenbanken
  entfernt, l10n_at auf der VM aktualisiert (fehlender Steuer-Tag +KZ 124 Bemessungsgrundlage),
  project_stock auf der VM installiert (Datenrest der Ansicht
  stock.picking.form.inherit.project_stock verursachte einen Client-Fehler in der Lieferansicht).
Nachweis: pruefe_verkauf_lieferung.py lokal 26 OK / 0 FEHL und VM 26 OK / 0 FEHL (Testprodukt und
  Testauftrag angelegt, bestaetigt, Lieferbeleg mit Position und Verkaufsbezug geprueft, danach
  alles geloescht; Bestand unveraendert); browser_verkauf_lieferung.py lokal 14 OK / 0 FEHL und
  VM 14 OK / 0 FEHL mit 0 JavaScript- und 0 RPC-Fehlern (Smart Button "1 Lieferung", Gruppe
  "Lieferung" mit Lagerhaus und Versandbedingungen, Lieferbeleg im Formular mit Referenzbeleg);
  Regressionstest Verkauf und Abonnements 886 OK / 0 FEHL.
Nachgezogene Prueferwartungen: verify_s121_verkauf_teil2.py (NEU_SEIT_TEIL5: picking_policy,
  warehouse_id, procurement_group_id, picking_ids, delivery_count, incoterm, move_ids, route_id),
  verify_s121_verkauf_teil3_reiter.py (Gruppe "Lieferadresse" heisst in Odoo 18 jetzt "Lieferung"),
  verify_s117_auftraege.py (SEIT_TEIL5_VORHANDEN: incoterm, warehouse_id, picking_ids),
  abschluss_verkauf_regression.py (Referenzwert s117 65 -> 67).
Keine Odoo-11-Daten uebernommen, Testdaten vollstaendig entfernt.
Nachtrag 29.09.2026 - Stammdaten "30 Tage netto" und View-Gesundheit:
  Odoo 11 (lesend): genau 4 Zahlungsbedingungen, alle firmenbezogen mit einer Zeile
    (value=balance, value_amount=0.0, option=day_after_invoice_date); "30 Tage netto" mit
    Hinweis "Zahlungsbedingungen: 30 Tage netto" und 30 Tagen, genutzt auf 2 Auftraegen,
    0 Kunden-Standardbedingung, 0 Rechnungen.
  Odoo 18 hatte 11 Zahlungsbedingungen ohne "30 Tage netto"; angelegt mit
    apply_verkauf_stammdaten.py (idempotent): eine Zeile percent/100 %, nb_days 30,
    delay_type days_after, Hinweis wie in Odoo 11; lokal id 16, VM id 14 -> je 12 Bedingungen.
    Feldnamen Odoo 11 -> Odoo 18: days -> nb_days, option -> delay_type; "balance" gibt es in
    Odoo 18 nicht mehr (Entsprechung percent 100 %). Keine Zuordnung, nichts entfernt.
  Pruefung verify_s121_verkauf_teil5_zahlungsbedingung_views.py: 113 OK / 0 FEHL
    (Zahlungsbedingung vollstaendig, 11 bisherige Bedingungen unveraendert, 0 Auftraege und
    0 Kunden umgestellt, View-Gesundheit ueber alle je Modell existierenden Ansichtstypen,
    project_stock-Erweiterung des Lagerbelegs gueltig, 0 Logmeldungen zu ungueltigen Ansichten).
Block 3 Browser-Gesamtabnahme auf der VM (29.09.2026): Aggregatlauf ueber 11 Browser-Werkzeuge
  243 OK / 0 FEHL, durchgehender Klickpfad 15 Stationen 43 OK / 0 FEHL, je 0 JavaScript- und
  0 RPC-Fehler, Bestand vor/nach dem Lauf unveraendert; Regression Verkauf + Abonnements
  886 OK / 0 FEHL. Werkzeuge: scripts/abschluss_verkauf_browser_gesamtabnahme.py,
  scripts/browser_verkauf_gesamtdurchgang.py; Doku docs/o11-o18-verkauf-teil5-block3-browserabnahme.md.

Offen: Block 4 (Abschlussmarkierung Verkauf).
```

**Teil 4 endgueltig abgeschlossen (29.09.2026).** Entscheidung Anna zur ITK-Proformavorlage:
kein zusaetzlicher Menueeintrag "ITK-Proformarechnung"; die bestehende Odoo-18-Funktion
"PRO-FORMA-Rechnung" (sale.report_saleorder_pro_forma) bleibt bestehen und wird verwendet; die
Vorlage itk_reports.report_itk_saleorder_proforma bleibt als dokumentierte Alt-/Zusatzvorlage ohne
Menuebindung im Modul, da sie fuer keinen tatsaechlich verwendeten Odoo-11-Prozess zwingend
benoetigt wird. Aenderung an Odoo 18: keine.

Dokument: `docs/o11-o18-vergleich-verkauf-teil4-druckberichte.md`.

```
Odoo 11 (lesend) - drei Report-Aktionen auf sale.order:
  Angebot/Auftrag (sale.report_itk_saleorder, gebunden), Angebot / Auftrag ORG
  (gleicher Reportname, NICHT gebunden -> Altlast), Proformarechnung
  (sale.report_itk_saleorder_proforma, gebunden). Formular: zwei Drucken-Knoepfe
  (print_quotation, states draft bzw. sent,sale).
  Dokumentvorlage sale.report_itk_saleorder_document: 24.198 Zeichen aktiv; Spaltenkoepfe
  Pos/Leistungsgegenstand/Menge/Einzelpreis/Rabatt/Gesamtpreis; Summenblock
  Nettosumme/Steuerzeilen (amount_by_group "20,00 % auf ...")/Gesamtsumme; Titel und
  Texte abhaengig von state. Nicht sichtbarer Code (alte Spalten "Steuern"/"Preis",
  Layoutkategorien) war in Odoo 11 auskommentiert.
Odoo 18 (unveraendert, vier gebundene Aktionen):
  Angebot/Auftrag (sale.report_saleorder_raw), ITK-Angebot/Auftrag
  (itk_reports.report_itk_saleorder), PDF-Angebot (sale.report_saleorder),
  PRO-FORMA-Rechnung (sale.report_saleorder_pro_forma)
  ITK-Vorlage 7.169 Zeichen aktiv, gleicher Aufbau; Summen ueber account.document_tax_totals,
  Firmenadresse ueber das externe Layout.
Befunde (nur dokumentiert, nichts geaendert):
  Summenbeschriftung "Nettobetrag"/"Gesamt" (Odoo-18-Standard) statt "Nettosumme"/"Gesamtsumme";
  Datum ohne Beschriftung; Proforma laeuft ueber den Odoo-18-Standardbericht, die
  ITK-Proformavorlage ist vorhanden, aber nicht gebunden (offene, nicht blockierende Entscheidung).
Abnahme 29.09.2026 im echten Browser (PDF-Download, Inhaltspruefung):
  scripts/browser_verkauf_druckberichte.py lokal 41 OK / 0 FEHL, VM 41 OK / 0 FEHL,
  0 JavaScript-Fehler, 0 RPC-Fehler
  VM: Menue Drucken (Zahnrad) zeigt Angebot/Auftrag, ITK-Angebot/Auftrag, PDF-Angebot,
  PRO-FORMA-Rechnung; Report-Aktion je Eintrag ueber die Server-Anfrage belegt; ITK-Auftrag
  S00203 -> "Auftrag S00203", Kunde/PLZ, Position Abo_Amtssignatur Test, Nettobetrag 24,00,
  20% 4,80, Gesamt 28,80, Datum 22.09.2026; S00189 (gesendet) -> "Angebot S00189", Gesamt 72,00;
  PRO-FORMA-Rechnung -> "Pro-forma-Rechnung", Gesamt 28,80
  Prueflauf scripts/verify_s121_verkauf_teil4_druckberichte.py: 69 OK / 0 FEHL
Keine Modulaenderung noetig (keine Odoo-11-Funktion fehlt); Odoo 11 nur lesend, keine Datenmigration.
```

Bestandsaufnahme Odoo 11 (lesend):
  Menue Verkauf/Berichtswesen: Verkauf (Aktion 423 sale.report), Verkaufsauftraege aller
    Kanaele (Aktion 424 report.all.channels.sales), Vertriebskaenale (Aktion 171 crm.team)
  report.all.channels.sales: SQL-Sicht, 18 Felder, Korn = Auftragszeile;
    3.775 Saetze = alle nicht stornierten Auftragszeilen (4.010 gesamt - 235 storniert);
    Zeitraum 2018-02 bis 2026-09; Kanaele: Vertriebskaene (Intern) 3.747, Interne Weitergabe 20,
    Persoenlicher Kontakt 5, Newsletter 3; 2026 = 406 Zeilen
    Pivot 1024 (name Zeile, price_total Mass, Vertriebskanal als Spalte),
    Suchansicht 1025 (Filter "Aktuelles Verkaufsjahr" [date_order >= Jahresanfang],
    Gruppierung "Vertriebskanal"), Default-Kontext
    {'search_default_team_id': 1, 'search_default_current_year': 1}
    analytic_account_id auf 0 Zeilen belegt -> nicht nachzubauen
  sale.report (O11): 31 Felder, 3.987 Saetze, Pivot 1016, Aktion 423 mit Default "Verkauf"
  Druckberichte (3): Angebot/Auftrag und Angebot / Auftrag ORG (sale.report_itk_saleorder),
    Proformarechnung (sale.report_itk_saleorder_proforma)
Bestandsaufnahme Odoo 18:
  Menue Verkauf/Berichtswesen: Verkauf (416), Kunden (419), Produkte (418),
    Vertriebsmitarbeiter (417) - alle sale.report; "Verkaufsauftraege aller Kanaele" fehlt,
    report.all.channels.sales existiert nicht
  sale.report: 41 Felder (date statt date_order, product_uom_qty statt product_qty,
    kein confirmation_date/analytic_account_id), Suchansicht 1206 mit Datumsfilter
    (name="year", default_period="year" = aktuelles Verkaufsjahr) und Gruppierung
    "Verkaufsteam" (team_id)
  Druckberichte (4): Angebot/Auftrag, PDF-Angebot, ITK-Angebot/Auftrag, PRO-FORMA-Rechnung
Mapping/Bewertung: sale.report uebernimmt die Funktion vollstaendig; Vorschlag eigener Aktion
  (Domain [('state','!=','cancel')], Kontext {'search_default_sales_channel': 1,
  'search_default_year': 1, 'pivot_measures': ['price_total']}), eigener Pivotansicht
  (name Zeile, price_total Mass) und Menuepunkt unter Verkauf/Berichtswesen.
Offene Entscheidungen: Label "Vertriebskanal" zusaetzlich anbieten, Vorgabemass/-zeile,
  Menueplatzierung, Beibehaltung der vier Odoo-18-Berichtsmenues
```

### 6.16 Abrechnung (Menues, Module, Datenmengen) - **BESTANDSAUFNAHME ABGESCHLOSSEN, BEREICH OFFEN**, 30.09.2026 (Session 122, Teil 1)

Dokument: `docs/o11-o18-vergleich-abrechnung-teil1.md`. Odoo 11 Prod `portal.it-kommunal.at`
(DB `ITK_V1_a`) ausschliesslich read-only verwendet (search_count/search_read/fields_get).
**In diesem Teil wurde an Odoo 18 nichts geaendert** (kein Upgrade, kein Neustart).

```
Module: installiert O11 130 | O18 171. Relevante Abweichungen:
  O11: account_invoicing, account_bank_statement_import, account_cash_basis_base_account,
       payment_transfer, l10n_de + l10n_de_skr03/04 (deutscher Kontenrahmen)
  O18: account_payment, account_invoice_line_report, sale_merge_draft_invoice, account_peppol,
       account_edi_ubl_cii, account_qr_code_sepa, snailmail_account, spreadsheet_account,
       l10n_at (oesterreichischer Kontenrahmen)
  Enterprise account_reports/accountant: in O18 nicht verfuegbar (uninstallable, OEEL-1)
Menuebaum: O11 App Abrechnung (Wurzel id 133) 70 Menues | O18 App Rechnungsstellung (id 193)
  63 Menues; lokal = VM (63 = 63, nur ein Wortlautunterschied "Ein Bankkonto hinzufuegen").
  Alle relevanten Modulversionen lokal = VM (account 18.0.1.3, account_payment 18.0.2.0,
  analytic 18.0.1.2, itk_valorisierung 18.0.1.0.0, l10n_at 18.0.3.2.1 u. a.).
Befund F56: ir.ui.menu.search_read filtert ohne context ir.ui.menu.full_list=True nach der
  Benutzersichtbarkeit - die App Abrechnung erschien dadurch mit nur 42 statt 70 Menues.
Nutzung Odoo 11 (read-only): 6.277 Rechnungen (6.040 Ausgangsrechnungen, 237 Kunden-Gutschriften,
  0 Eingangsrechnungen, 0 Lieferanten-Gutschriften; bezahlt 6.220 / offen 43 / Entwurf 14),
  10.031 Rechnungszeilen, 5.987 Zahlungen (5.877 Ein / 110 Aus, Journal BNK1, 5.985 mit
  Rechnungsbezug), 12.251 Buchungen, 12.634 Kostenstellenbuchungen (alle aus Projekten/Aufgaben),
  Valorisierungstexte auf 4.216 Rechnungen (10 Texte), 77 Steuern, 1.286 Konten, 8 Journale,
  4 Zahlungsbedingungen (alle value=balance), 0 Bankauszuege, 0 Online-Zahlungen,
  2.549 Rechnungen als per E-Mail versendet markiert (9.197 Anhaenge, 5.772 E-Mails im Chatter).
  Zeitraum 27.05.2019 bis 28.09.2026, Nummernkreis R-1900001 bis R-26989.
Testbestand Odoo 18: lokal 37, VM 57 Belege; Zahlungen je 7; 53 Steuern; 12 Zahlungsbedingungen;
  1 Valorisierungstext; 0 Anhaenge an Rechnungen.
FEHLENDE FUNKTIONEN (Odoo 18 Community hat die Odoo-11-Berichtsassistenten nicht mehr):
  acht Menues unter Berichtswesen/PDF Berichte (Audit Journale account.print.journal,
  Partner-Kontoauszug account.report.partner.ledger, Umsaetze nach Konten und Perioden
  account.report.general.ledger, Vorlaeufige Bilanz account.balance.report, Bilanz und
  Gewinn und Verlust accounting.report, alter Partner Saldo account.aged.trial.balance,
  Umsatzsteuerbericht account.tax.report), dazu account.financial.report (8 Finanzberichte),
  tax.adjustments.wizard (Steueranpassungen), account.analytic.tag (Kostenstellen Tags, 0 Werte),
  payment.icon (Zahlungssymbole, 10 Werte); account.account.type -> Auswahlfeld account_type.
  Ersatz nur ueber das Enterprise-Modul account_reports (nicht verfuegbar).
ANDERS AUFGEBAUT (kein Funktionsverlust): Gruppierung Verkauf/Einkauf gegen Kunden/Lieferanten;
  Zahlungsmenues ohne Domain (O11: partner_type customer/supplier); tree -> list; account.invoice ->
  account.move (move_type) und account.invoice.line -> account.move.line; Kontenrahmen l10n_de ->
  l10n_at; Berechtigungsgruppen Abrechnungsmanager/Zeige vollstaendige Finanzbuchhaltung ->
  Buchhaltungsfunktionen anzeigen/Kostenrechnung; Analytic-Modell (tag/account ->
  plan/distribution.model); payment.acquirer -> payment.provider/payment.method.
Odoo-18-ZUSATZFUNKTIONEN (bleiben erhalten): Abrechnungspositionen, Pruefpfad, Buchungen
  festschreiben, Mehrere Hauptbuecher, Steuergruppen, Abstimmungsmodelle, Incoterms,
  Kostenstellenplaene/Verteilungsschluessel, Zahlungsmethoden, Peppol/EDI, SEPA-QR-Code,
  Postversand, Spreadsheet, Sammelrechnung, Positionsbericht.
Offene Fachfragen (K1-K9 im Dokument): Kontenrahmen-Mapping, Nummernkreis, Nutzung der acht
  PDF-Berichte, Anlage der 10 Valorisierungstexte, Steuerzuordnung (Teil 2/3), Zahlungsmenu-Domain,
  SMTP/Rechnungsversand, Kostenstellen-Tags, USD/Preisliste F2-F5.
Browser-Spotcheck auf der VM (30.09.2026, read-only, scripts/browser_abrechnung_menue.py):
  App Rechnungsstellung im echten Browser geoeffnet, alle sechs Menuegruppen echt geklickt;
  Ergebnis 17 OK / 0 FEHL, 0 JavaScript- und 0 RPC-Fehler. Abgleich RPC-Sichtbarkeit gegen
  Browser: 38 sichtbare Menuepunkte, 37 im Browser gefunden, 1 dokumentierte Abweichung
  (Befund F57: Menue "Pruefpfad" id 245 per RPC sichtbar, im Web-Client nicht ausgeliefert).
  Gegenprobe: die sieben Odoo-11-Berichtsnamen sind im Browser nicht sichtbar.
  Screenshots Desktop\Odoo18-Abnahme-Session122\; Belegprobe "1-47 / 47" Ausgangsrechnungen.
Entscheidungen von Anna (30.09.2026, verbindlich): K1 Kontenrahmen l10n_at bleibt, Mapping-Tabelle
  O11-Konto -> O18-Konto fuer spaeter vorbereiten; K2 historische Rechnungsnummern muessen erhalten
  bzw. nachvollziehbar zugeordnet werden (Pruefung im Feldinventar, nichts umnummerieren);
  K3 die acht PDF-Berichte nicht nachbauen, erst Nutzung und Inhalt in der Berichtsanalyse
  feststellen; K4 die 10 Valorisierungstexte als migrationsrelevante Stammdaten erhalten
  (Mapping vorbereiten, jetzt nichts anlegen); K5 vollstaendiges Steuer-Mapping vorbereiten;
  K6 Odoo-18-Zahlungsmenues bleiben, Odoo-11-Navigation nur bei echter Funktionsluecke;
  K7 SMTP nur als offener Infrastrukturpunkt dokumentieren; K8 Kostenstellen-Tags nicht nachbauen;
  K9 USD-Waehrung/Preisliste als offener Pruefpunkt dokumentiert.
Teil 2 FELDINVENTAR (30.09.2026, nur Analyse, keine Aenderung an Odoo 18):
  Dokument docs/o11-o18-vergleich-abrechnung-teil2.md. account.invoice 87 Felder gegen
  account.move 189 (gemeinsam 50, nur O11 37, nur O18 139); account.invoice.line 37 gegen
  account.move.line 93 (gemeinsam 23, nur O11 14, nur O18 70). Vollstaendigkeitskontrolle:
  ir.model.fields gegen fields_get je Modell und Instanz ohne Abweichung.
  Jedes belegte Odoo-11-Feld hat ein Ziel; Pflichtfelder verschieben sich von fachlich
  (partner_id, account_id, reference_type) auf technisch (move_type, state, date, auto_post,
  display_type, move_id); Zustand: O11 draft/open/paid/cancel gegen O18 draft/posted/cancel
  plus payment_state; 2 bzw. 1 Typ-/Relationsabweichung; 24 bzw. 10 Beschriftungsunterschiede.
  ITK-Felder (valorisierung_id, projectcategory_id, notice, sale_order_*, subscription_id)
  in Odoo 18 vorhanden; entfallen nur Felder mit 0 Datensaetzen.
  K2 Rechnungsnummern technisch geprueft (read-only): Feld name beschreibbar; Odoo 18 hat den
  UNIQUE INDEX account_move_unique_name (name, journal_id) fuer gebuchte Belege (in Odoo 11
  war 'type' Teil des Schluessels) -> genau EINE Doppelnummer R-25001 (Rechnung id 9703 und
  Gutschrift id 11531, 2025) wuerde den Import abbrechen; Odoo 18 fuehrt die Zaehlung ab der
  hoechsten vorhandenen Nummer im gleichen Format fort (R-26990 ...). Regelung als K2a offen.
Naechster Schritt (Vorschlag): Teil 3 Formulare, Reiter, Buttons, Smart Buttons, Zustandswechsel,
  Zahlungs- und Abstimmungslogik, Rechnungsdruck und Versand (Browser lokal und VM); vorher
  Entscheidungen zu K1, K3, K4, K6 sowie K2a/K2b/K2c.
K2 VOLLSTAENDIG GEKLAERT (30.09.2026, read-only): eigenes Dokument
  docs/o11-o18-vergleich-abrechnung-k2-nummern.md.
  Messkorrektur: hoechste Rechnungsnummer 2026 ist R-261139 (nicht R-26989; die laufende Nummer
  wechselt bei Ueberschreitung von 999 in die Vierstelligkeit). Nachtrag in Teil 2, Abschnitt 12.
  K2a: Odoo 18 erlaubt gleiche Nummern nur je Journal (UNIQUE INDEX account_move_unique_name auf
  name+journal_id fuer gebuchte Belege); ein eigener Nummerkreis fuer Gutschriften
  (refund_sequence) loest den Fall NICHT, ein zweites Journal schon (aendert aber die
  Journalstruktur). Empfehlung Weg A: Rechnung behaelt R-25001, Gutschrift erhaelt eine neue
  Nummer, Originalnummer in einem eigenen Feld "Odoo-11-Rechnungsnummer" (Vorschlag, nichts
  angelegt). Gutschrift bleibt ueber reversed_entry_id/Ursprung R-25584 nachvollziehbar.
  K2b: ohne Zusatzkonfiguration erkennt Odoo 18 alle 6.263 Nummern als "fest" und wuerde bei
  R-1900003 weiterlaufen (Fortsetzung des 2019er Zaehlers); mit
  sequence_override_regex ^(?P<prefix1>R-)(?P<year>\d{2})(?P<seq>\d+)$ (deckt alle 6.263 ab)
  laeuft die Zaehlung je Jahr korrekt weiter: 2026 -> R-261140, 2027 -> R-2700001, kollisionsfrei.
  K2c: Journalfeld restrict_mode_hash_table ("Gebuchte Posten mit Hash festschreiben") schuetzt
  genau name, date, journal_id, company_id (Hash-Felder), ist nach dem ersten gesicherten Beleg
  nicht mehr abschaltbar und laesst sich per Assistent "Buchungen festschreiben" nachholen;
  zusaetzlich Loeschsperre fuer Kettenbelege, Schreibsperren fuer Journal/Datum/Nummer und
  Pruefpfad (res.company.check_account_audit_trail) zur Protokollierung.
  Offen: K2a (Weg A/B/C), K2a-2 (Einbauort des Feldes), K2b (Override ja/nein), K2c (Hash und
  Pruefpfad ja/nein).
ENTSCHEIDUNGEN VON ANNA (30.09.2026, verbindlich):
  K2a -> Weg A: Rechnung id 9703 behaelt R-25001; die Gutschrift id 11531 erhaelt bei der
     Migration eine neue, eindeutige Odoo-18-konforme Nummer; die urspruengliche Odoo-11-Nummer
     bleibt zusaetzlich nachvollziehbar erhalten; dafuer wird ein eigenes Feld
     "Odoo-11-Rechnungsnummer" vorgesehen; kein zweites Verkaufsjournal nur wegen dieser
     Kollision. Einordnung: Feldanlage und Migrationsregel in Teil 5.
  K2b -> jahresbezogene Nummerierung ueber sequence_override_regex wie vorgeschlagen; vorher in
     einer Testkopie pruefen, wie der erste Beleg eines neuen Jahres weitergezaehlt wird; jetzt
     keine produktive Nummerierung aendern. Einordnung: vor der ersten neuen Rechnung (Teil 5).
  K2c -> Hash-Sicherung und Pruefpfad erst NACH der echten Migration und nach erfolgreicher
     Kontrolle aktivieren; jetzt keine Aenderung. Einordnung: nach der Datenmigration.
  Unveraendert: keine Datenmigration, keine historischen Nummern aendern, Odoo 11 read-only,
     keine Odoo-18-Funktion entfernen.
```

TEIL 3 FORMULARE, BUTTONS, ZUSTANDSWECHSEL, ZAHLUNG, DRUCK, VERSAND (30.09.2026, nur Analyse,
keine Aenderung an Odoo 18). Dokument: `docs/o11-o18-vergleich-abrechnung-teil3.md`:
```
Reiter: O11 zwei (Rechnung, Andere Informationen) | O18 zwei im Browser (Rechnungszeilen,
  Weitere Informationen); der Arch enthaelt einen zweiten Abschnitt other_info als Erweiterung.
Kopf-Buttons: O11 vier (Bestaetigen, "Einzahlung erfassen" = act_window 178 auf account.payment,
  "Nach Gutschrift fragen" = act_window 241 auf account.invoice.refund, Auf Entwurf setzen)
  gegen O18 neunzehn Auspraegungen (Buchen/Bestaetigen, Senden, Drucken, Zahlen, Transaktion
  erfassen/stornieren, Vorschau, Stornobuchung, Gutschrift, Abbrechen, Auf Entwurf
  zuruecksetzen, Sperren, Stornierung anfordern, Als geprueft markieren, PEPPOL abbrechen),
  alle mit ihren Bedingungen im Dokument.
Smart Buttons: O11 keine (Zahlungen ueber payments_widget und outstanding_credits_debits_widget)
  gegen O18 acht (bei der Testrechnung war genau "1 Zahlungen" sichtbar).
Zustandswechsel: O11 Entwurf -> Offen -> Bezahlt, Storno -> Entwurf, Gutschrift ueber den
  Assistenten account.invoice.refund; O18 Entwurf -> Gebucht -> Zahlungszustand,
  "Auf Entwurf zuruecksetzen", Storno, Gutschrift ueber account.move.reversal, Sperren (K2c).
  Der Odoo-11-Zustand "Offen" (43 Belege) bleibt der einzige Wert ohne direkte Entsprechung.
Zahlung/Abstimmung: O11 5.987 Zahlungen (5.985 mit Rechnungsbezug), Sammelzahlungs-Assistent
  vorhanden aber 0 Belege, 6.123 Teil- und 6.081 Vollabstimmungen, 0 Bankauszuege; O18 Zahlungen
  ueber den Assistenten account.payment.register, Zahlungszustand als eigenes Feld, vier
  Abstimmungsmodelle (Zusatzfunktion). Das Abstimmungsmodell ist in O11 mit dem Lesekonto nicht
  lesbar (kein Leserecht) - Vorhandensein nur ueber ir.model belegt.
Druck: O11 vier Berichte auf account.invoice (537 "Rechnung" und 538 "Rechnung mit Zahlung"
  gebunden, 230/231 "ORG" ohne Bindung), kein Drucken-Knopf im Formular; O18 fuenf Berichte
  (323, 324, 325, 406, 1231 "ITK-Rechnung") und Knopf "Drucken" (action_print_pdf erzeugt direkt
  das PDF; Browser-Nachweis RE_2020_0001.pdf). attachment_use = False, es entstand kein Anhang.
Versand: O11 2.549 Rechnungen mit sent=True und 9 Mailvorlagen (inkl. 3 Mahnvorlagen, Modul
  mass_email_invoice); O18 Knopf "Senden" ueber account.move.send, 5 Standardvorlagen
  (englische Bezeichnungen), Massenversand im Aktionsmenue. Vorlagenangleichung offen (Befund B6).
Browser-Abnahme VM (read-only, scripts/browser_abrechnung_rechnung.py): 12 OK / 0 FEHL,
  0 JavaScript- und 0 RPC-Fehler; Beleg 28 RE/2020/0001 blieb unveraendert
  (write_date 2026-09-18 10:04:30, keine Anhaenge).
Befunde B1-B9 (jeder einzeln, nichts umgebaut) im Dokument, Abschnitt 10; Umsetzungsvorschlaege
  folgen erst nach Freigabe.
Naechster Schritt (Vorschlag): Teil 4 Ansichten/Listen/Filter/Massenaktionen, Teil 5
  Migrationsregeln/Feldabbildung (Offen-Regel, K2a-Umsetzung, K1, K5), Teil 6 Berichtsanalyse (K3)
  und Vorlagen (B6).
```

B2 GUTSCHRIFT (Befund aus Teil 3, 30.09.2026, nur Analyse, keine Aenderung an Odoo 18).
Dokument: `docs/o11-o18-vergleich-abrechnung-b2-gutschrift.md`:
```
Vergleich: Odoo 11 account.invoice.refund (Assistent, View 578, Modul account) gegen Odoo 18
  account.move.reversal (View 931).
Odoo 11 Assistent: Felder Rueckerstattungsmethode (Pflicht, 3 Werte), Grund (Pflicht),
  Gutschrift-Datum (Pflicht), Buchungsdatum; Buttons "Gutschrift hinzufuegen" und "Cancel";
  kein Referenzfeld. Quellcode-Fakten (_prepare_refund): Gutschrift im Entwurf, number=False,
  origin = Nummer der Rechnung, refund_invoice_id = Rechnung, name = Grund,
  date_invoice = date_due = Gutschrift-Datum, payment_term_id = False; die Rechnung erhaelt eine
  Chatter-Nachricht mit Betreff "Gutschrift" und dem Grund. Die drei Modi (Quellcode
  compute_refund): "refund" = Entwurf; "cancel" = buchen und ausgleichen (setzt die Rechnung
  NICHT auf Storno); "modify" = zusaetzlich neue Entwurfsrechnung.
Nutzung Odoo 11 (read-only): 237 Gutschriften, davon 222 bezahlt, 15 offen, 0 Entwurf/Storno;
  215 ueber den Assistenten (215 Chatter-Nachrichten "Gutschrift" auf 215 Belegen, genau die
  215 mit Ursprungsbezug und Begruendung); 22 ohne Assistent (davon 11 ohne Herkunft);
  0 Ausgangsrechnungen im Zustand Storno; 14 Entwuerfe, alle ohne Datum und mit Herkunft
  A-/NV-Nummern (kein Hinweis auf Modus "Modifizieren"); Feld reference in Odoo 11 nie benutzt (0);
  Feld name (Referenz/Beschreibung) in 1.418 Belegen belegt, davon 215 Gutschriften mit Grund.
Odoo 18 Assistent: Felder Begruendung auf Gutschrift angezeigt (reason), Journal (Pflicht,
  "?"-Markierung), Stornodatum (Vorbelegung heute); Buttons Stornieren (refund_moves),
  Stornieren und Rechnung erstellen (modify_moves), Verwerfen. Quellcode (_prepare_default_reversal):
  ref = "Stornierung von: <Nummer>, <Begruendung>", reversed_entry_id, date/invoice_date_due =
  Stornodatum, invoice_date = Stornodatum, journal_id, invoice_user_id, invoice_origin = Herkunft
  der Rechnung, auto_post = at_date bei Zukunftsdatum; Entwurf; Abstimmung nur bei
  "Stornieren und Rechnung erstellen" (cancel=True) plus neue Entwurfsrechnung. Journal
  Kundenrechnungen fuehrt refund_sequence = True (eigene Gutschriftenfolge, Grundlage K2a).
Browser-Nachweis VM (read-only, scripts/browser_b2_gutschrift.py, Beleg 28 RE/2020/0001):
  10 OK / 0 FEHL, Dialogtitel "Gutschrift", drei Felder wie oben, drei Buttons, mit "Verwerfen"
  geschlossen, kein Beleg angelegt (57 vorher, 57 nachher), 0 JavaScript- und 0 RPC-Fehler.
UNTERSCHIEDE (U1-U7, nichts umgebaut): U1 Sofort-Ausgleich des Odoo-11-Modus "Abbrechen" hat in
  Odoo 18 keinen eigenen Knopf (buchen + abstimmen, Ergebnis gleich, Vorschlag: nichts umbauen);
  U2 Zukunftsdatum bucht automatisch (Importregel auto_post = no vormerken);
  U3 Zielfeld fuer den Grund: Odoo 11 speichert ihn in name (in Odoo 18 die Belegnummer) - im
  Feldinventar Teil 2 ist fuer name kein Ziel definiert, Vorschlag: ref nach Odoo-18-Muster
  bilden und Grund zusaetzlich in der Chatter-Nachricht erhalten;
  U4 Herkunft: Odoo 11 origin = Nummer der Rechnung, Odoo 18 invoice_origin = Herkunft der
  Rechnung (Nummer nur im ref-Text), Vorschlag: reversed_entry_id setzen, Herkunft wie Odoo 18;
  U5 22 Gutschriften ohne Ursprungsbezug bleiben ohne Bezug (nichts rekonstruieren);
  U6 teilweise bezahlte Rechnungen: Odoo 18 ohne Einschraenkung (keine Luecke);
  U7 Mehrfachauswahl/Belegarten: Verhalten dokumentiert (keine Luecke).
ERGEBNIS: die in Odoo 11 verwendete Gutschrift-Funktion ist in Odoo 18 fachlich abgedeckt; offen
  sind nur Migrationspunkte (U2-U5), keine Funktionsluecke.
ENTSCHEIDUNGEN VON ANNA (30.09.2026, verbindlich): Arbeitsweise ab jetzt = Fertigstellung von
  Odoo 18 fuer die Migration (Befunde umsetzen statt einzeln vorlegen); Odoo 18 direkt anpassen,
  wenn die fachliche Loesung eindeutig ist; Stopp nur bei echten Entscheidungen mit mehreren
  sinnvollen Varianten. Fuer B2: Odoo-18-Standard account.move.reversal verwenden, keinen
  Odoo-11-Assistenten nachbauen, Verknuepfung ueber reversed_entry_id/reversal_move_ids,
  historischen Grund bei der Migration erhalten, Ursprung und alte Nummer nachvollziehbar halten,
  ungenutzte Odoo-11-Felder nicht rekonstruieren, Odoo-18-Workflow beibehalten; den alten
  Kurzbefehl "Abbrechen / sofort ausgleichen" NICHT nachbauen.
ABSCHLUSS B2: KEINE Aenderung an Odoo 18 erforderlich (Odoo-18-Standard ist fachlich
  ausreichend). Alle offenen Punkte sind Migrationsregeln fuer Teil 5: U2 auto_post = no,
  U3 Odoo-11-Feld name -> ref nach Odoo-18-Muster plus Chatter-Nachricht (Nachtrag Abschnitt 13
  im Feldinventar Teil 2), U4 Herkunftsregel, U5 22 Gutschriften ohne Bezug.
```

B3 ZAHLUNG (Befund aus Teil 3, 30.09.2026, umgesetzt und getestet). Dokument:
`docs/o11-o18-vergleich-abrechnung-b3-zahlung.md`:
```
Vergleich: Odoo 11 Aktion 178 "Register Payment" (Formular account.payment) gegen Odoo 18
  Assistent account.payment.register (Knopf "Zahlen").
Odoo 11 Nutzung (read-only): 5.987 Zahlungen, alle Zahlungsart "Manuell", Journal BNK1
  ("Bank fuer Tirol und Vorarlberg AG (EUR)"), 5.877 Eingang / 110 Ausgang, Partnerart Kunde,
  alle gebucht; Memo in 5.974 Faellen gefuellt (Wert = Rechnungsnummer); Abschreibungen 0,
  Zahlungsdifferenz immer 0,00; Sammelzahlungs-Assistent vorhanden aber 0 Belege; 0 Bankauszuege.
Odoo 18 Dialog (Browser, VM): Journal Bank, Zahlungsmethode, Betrag, Waehrung, Zahlungsdatum,
  Vermerk (Vorbelegung Rechnungsnummer); Knoepfe "Zahlung erstellen" und "Verwerfen"; zusaetzlich
  vorhanden (in Odoo 11 ungenutzt): Zahlungsdifferenz mit Behandlung, Differenzenkonto,
  Buchungstext, Zahlungen gruppieren, Bankkonto des Kunden.
Funktionstest lokal (scripts/test_b3_zahlung.py): Rechnung RE/2026/0001 -> Zahlung
  PBNK1/2026/00002 3,60, Memo RE/2026/0001, Buchungssatz 2803 Ausstehende Eingaenge / 2000
  Forderungen, Rechnung bezahlt (Rest 0,00), Zahlungen 7 -> 8, Teilabstimmungen 7 -> 8.
Browser-Abnahme VM (scripts/browser_b3_zahlung.py): 16 OK / 0 FEHL, Ablauf Entwurf -> Bestaetigen
  -> Zahlen -> Dialog -> "Zahlung erstellen" -> Anzeige "Bezahlt am 30.09.2026", Smart Button
  "1 Zahlungen", Zahlung PBNK1/2026/00005, Rechnung bezahlt, 0 JavaScript- und 0 RPC-Fehler.
Regression: 886 OK / 0 FEHL ueber 11 Prueflaeufe (Referenzniveau).
ERGEBNIS: kein funktionaler Unterschied; Anpassung an Odoo 18 nicht erforderlich.
OFFEN (keine Funktionseinbusse, dokumentiert): Z2 Beschriftung der Zahlungsmethodenzeile
  (Odoo 11 "Manuell", Odoo 18 "Manual Payment"; nicht uebersetzbar, Umbenennung waere moeglich -
  Entscheidung offen, Stammdaten), Z3 Journalname BNK1 (Stammdaten, Migration), Z4 Zahlungs-
  nummern CUST.IN/JJJJ/NNNN gegen PBNK1/JJJJ/NNNNN (Migrationsregel Teil 5).
TESTDATEN: lokal Zahlung id 8; VM Zahlungen id 9-11 und die dafuer gebuchten Rechnungen
  id 41, 45, 46 (Testdatenbank).
```

B6 MAILVORLAGEN (Befund aus Teil 3, 30.09.2026, UMGESETZT). Dokument:
`docs/o11-o18-vergleich-abrechnung-b6-mailvorlagen.md`:
```
Bestand Odoo 11: 9 Mailvorlagen auf der Rechnung, davon die verwendeten Wortlaute
  "Rechnungsstellung: Allgemeine Rechnung" (id 41, inhaltsgleich id 42) und
  "Rechnungsstellung: Ihr Abonnement fuer help-amtsweg.gv.at" (id 11); Mahn- und
  Erinnerungsvorlagen (58, 61, 71, 82, 83) sowie die Standardvorlage (38).
Bestand Odoo 18 vorher: 5 Standardvorlagen (de_DE uebersetzt), davon keine mit ITK-Wortlaut;
  der Knopf "Senden" nutzt fest die Standardvorlage (account_move.py, _get_mail_template).
UMSETZUNG in Odoo 18: neues Datenfile addons/itk_reports/data/mail_template_invoice.xml
  (Modul itk_reports 18.0.1.1.0) mit zwei Vorlagen auf account.move:
  itk_reports.mail_template_itk_invoice ("Rechnungsstellung: Allgemeine Rechnung") und
  itk_reports.mail_template_itk_invoice_abo ("Rechnungsstellung: Ihr Abonnement fuer
  help-amtsweg.gv.at"). Felder: Betreff "{{ object.company_id.name }} Rechnung (Ref
  {{ object.name or 'n/a' }})", Absender ITK-Office <office@it-kommunal.at>, Sprachlogik wie
  Odoo 11, Anhang ITK-Rechnung (action_report_itk_invoices), Briefkopf als Bild mit absoluter
  Adresse, Verkaeufersignatur, auto_delete wie Odoo 11. Platzhalter auf Odoo 18 umgestellt
  (object.number -> object.name, object.user_id -> object.invoice_user_id).
NICHT umgesetzt (bewusst): Mahn- und Erinnerungsvorlagen (Mahnwesen nicht installiert, Vorgabe
  K3/K7); keine Dublette fuer id 42 (inhaltsgleich mit id 41); Odoo-18-Standardvorlagen bleiben
  unveraendert und weiterhin Standard beim Knopf "Senden".
PRUEFUNGEN: lokal 31 OK / 0 FEHL, VM 31 OK / 0 FEHL (Rendern mit Betreff "IT-Kommunal GmbH
  Rechnung (Ref RE/2026/0005)" und ITK-Rechnung als PDF-Anhang), Browser-Abnahme VM
  10 OK / 0 FEHL (beide ITK-Vorlagen in der Vorlagenliste und im Massenversand-Dialog
  auswaehlbar, kein Versand ausgeloest), Regression 886 OK / 0 FEHL.
DEPLOY VM: Branch per Git, gezieltes Einzel-Upgrade itk_reports (docker compose stop/run/start),
  danach auf main synchronisiert.
```

TEIL 4 ANSICHTEN/LISTEN/FILTER/MASSENAKTIONEN (30.09.2026, UMGESETZT). Dokument:
`docs/o11-o18-vergleich-abrechnung-teil4-ansichten.md`:
```
Listenspalten: Odoo 11 zehn Spalten, Odoo 18 hat alle Spalten, aber "Zu bezahlen"
  (Faelliger Betrag), "Referenzbeleg" und "Referenz" waren optional="hide".
  UMGESETZT: neue Ansicht itk_reports.view_itk_invoice_list_spalten
  (addons/itk_reports/views/account_move_views.xml, itk_reports 18.0.1.2.0) setzt diese drei
  Spalten auf optional="show" -> Standardsichtbarkeit wie Odoo 11, weiterhin ausblendbar.
Suche: Odoo 11 neun Filter und sechs Gruppierungen, Odoo 18 achtzehn Filter und elf
  Gruppierungen; inhaltlich vollstaendig (Odoo-11-"Offen" entspricht Odoo-18-"Zu zahlen"/
  "In Zahlung"; Gruppierungen Verkaeufer/Vertriebsmitarbeiter, Partner/Kunde,
  Vertriebskanal/Verkaufsteam).
Massenaktionen: Odoo 11 hatte fuenf Massenbearbeitungsobjekte auf der Rechnung
  (Valorisierungstext, Zahlungsbedingungen, Rechnungsdatum, Leistungszeitraum,
  Projektkategorie). In Odoo 18 existieren genau diese fuenf als Server-Aktionen des Typs
  mass_edit (id 1313, 1314, 1315, 1317, 1318; angelegt 15.07.2026 im Projekt) - kein Nachbau
  noetig, nichts entfernt.
PRUEFUNGEN: Browser-Abnahme VM 19 OK / 0 FEHL (zehn Spalten inklusive der drei angeglichenen,
  Filter Ueberfaellig/Zu zahlen/Meine Rechnungen, Gruppierungen Kunde/Vertriebsmitarbeiter/
  Verkaufsteam/Status, Aktionsmenue mit allen fuenf ITK-Massenaktionen, Massenbearbeitungs-
  Dialog geoeffnet und verworfen), Regression 886 OK / 0 FEHL.
DEPLOY VM: Branch per Git, Einzel-Upgrade itk_reports (docker compose stop/run/start), danach
  auf main synchronisiert.
Offen dokumentiert: Odoo-11-Zustand "Offen" ohne Gegenstueck (Teil 5); Beschriftungen
  (Verkaeufer/Vertriebsmitarbeiter, Vertriebskanal/Verkaufsteam, Zu bezahlen/Faelliger Betrag).
```

LABEL-REGEL ABRECHNUNG (Anna, 30.09.2026, verbindlich fuer alle Module; rueckwirkend auf
Teil 1-4 angewendet). Dokumente: `docs/o11-o18-abrechnung-labelmapping.md` (Feldmapping) und
`docs/o11-o18-abrechnung-viewlabels.md` (View-Bezeichnungen):
```
Regel: Hat ein Feld in Odoo 18 fachlich dieselbe Bedeutung wie in Odoo 11, zeigt Odoo 18 die
  sichtbare deutsche Bezeichnung aus Odoo 11. Technische Odoo-18-Feldnamen bleiben unveraendert.
  Keine Angleichung bei fachlich unterschiedlicher Bedeutung; Odoo-18-Zusatzfelder bleiben.
Pruefung (automatisiert):
  scripts/check_abrechnung_labels.py     Feldbeschreibungen (de_DE), 57 Feldpaare,
    schreibt docs/o11-o18-abrechnung-labelmapping.md
    (Odoo-11-Feld -> Odoo-18-Zielfeld -> Odoo-11-Bezeichnung -> Odoo-18-Bezeichnung -> Zustand)
  scripts/check_abrechnung_viewlabels.py View-Bezeichnungen (Spalten, Reiter, Gruppen, Filter,
    Gruppierungen, Knoepfe), schreibt docs/o11-o18-abrechnung-viewlabels.md
  scripts/apply_abrechnung_labels.py     setzt 33 Feldbeschreibungen auf den Odoo-11-Wortlaut
    (nach jedem Modul-Upgrade erneut auszufuehren, lokal und VM)
Umgesetzt: 33 Feldbeschreibungen (lokal und VM je 33 gesetzt) und 3 View-Spalten
  (itk_reports 18.0.1.3.0, views/account_move_labels.xml: Total, Zu Bezahlen, Verkaeufer).
  Beispiele: Verkaeufer, Vertriebskanal, Rechnungsdatum, Faelligkeit, Buchungsdatum,
  Referenzbeleg, Weitere Informationen, Steuerzuordnung, Bankkonto, Total, Preis pro ME,
  Mengeneinheit, Beschreibung, Kostenstelle, Project Category, Valorisation Text.
Stand nach der Anpassung: 3 Feld-Abweichungen und 1 View-Abweichung, alle begruendet:
  account.move.ref (Odoo-11-Feld reference nie belegt, Odoo 18 nutzt ref fuer Stornierungstexte),
  account.move.payment_reference (in Odoo 11 nicht vorhanden), account.move.name (in Odoo 11
  Begruendung/Beschreibung, keine 1:1-Zuordnung), Spalte Kunde/Lieferant (Odoo 11 beschriftete
  die Kundenspalte irrefuehrend "Lieferant"; Odoo 18 trennt nach Belegart und bleibt).
Browser-Nachweis VM (Liste): Spalten Nummer, Kunde, Rechnungsdatum, Faelligkeit, Referenzbeleg,
  Referenz, Exklusive Steuern, Total, Zu Bezahlen, Status -> 19 OK / 0 FEHL.
```

UPGRADE-VERFAHREN MIT AUTOMATISCHEM LABEL-ABGLEICH (30.09.2026, UMGESETZT):
```
scripts/upgrade_modules.py fuehrt nach jedem Modul-Upgrade automatisch aus:
  1) scripts/apply_abrechnung_labels.py --instanz <lokal|vm>   (Odoo-11-Bezeichnungen setzen)
  2) scripts/check_abrechnung_labels.py --instanz <...>        (Feldbeschriftungen pruefen)
  3) scripts/check_abrechnung_viewlabels.py --instanz <...>    (View-Bezeichnungen pruefen)
Eine unbegruendete Abweichung oder ein fehlendes Feld markiert den Lauf als Fehler
  (Rueckgabewert ungleich 0). Die drei bewusst dokumentierten Ausnahmen (account.move.ref,
  account.move.payment_reference, account.move.name) und die begruendete Spalte Kunde/Lieferant
  sind in den Pruefskripten hinterlegt und zaehlen nicht als Abweichung.
Abschaltbar mit --ohne-labels.
Pruefung lokal: Upgrade itk_reports -> apply "0 gesetzt, 0 Abweichungen", beide Checks OK,
  Rueckgabewert 0. Pruefung VM: Upgrade itk_reports -> apply "20 gesetzt" (Upgrade hatte die
  deutschen Beschriftungen zurueckgesetzt), beide Checks OK, Rueckgabewert 0.
Verbindlich: nach jedem Upgrade der Odoo-18-Module laeuft dieser Abgleich mit; im Fehlerfall
  ist der Lauf zu wiederholen bzw. die Ursache zu klaeren.
```

TEIL 5 FELDABBILDUNG UND MIGRATIONSREGELN (30.09.2026). Dokument:
`docs/o11-o18-vergleich-abrechnung-teil5-feldabbildung.md` (erzeugt von
`scripts/baue_abrechnung_teil5_doku.py`, 53 Feldpaare):
```
Je tatsaechlich relevantem Odoo-11-Feld sind festgehalten: Odoo-11-Modell und Feld,
  Odoo-11-Bezeichnung, Odoo-18-Zielmodell und Feld, Odoo-18-Bezeichnung (nach Label-Abgleich),
  Zuordnung bzw. Transformationsregel, benoetigte Stammdaten/Modulabhaengigkeit, gespeichert oder
  berechnet in beiden Systemen, migriert oder neu berechnet und die Validierungsregel.
Regeln ohne Feldbezug: K2a (Weg A, Feld "Odoo-11-Rechnungsnummer"), K2b (sequence_override_regex
  vor der ersten neuen Rechnung, vorher Testkopie), K2c (Hash und Pruefpfad erst nach der
  Migration), Gutschriften B2 (reversed_entry_id, Gutschriftsgrund aus dem Odoo-11-Feld name in
  ref und Chatter, auto_post = no), Zahlungen B3 (Abstimmung, Journal BNK1, Memo =
  Rechnungsnummer), K1 Kontenrahmen-Mapping (1.286 -> l10n_at), K5 Steuermapping (77 -> 53),
  K4 Valorisierungstexte (10 Stammdatensaetze), K7 SMTP offen.
Kernpunkte je Feld: Belegnummer 1:1 (Kontrolle K2a), Zustand Offen -> gebucht + Zahlungszustand,
  Restbetrag neu berechnet, Kostenstelle -> analytic_distribution 100 %, Erloeskonto ueber
  K1-Mapping, Steuern ueber K5-Mapping, Valorisierungstext und Projektkategorie ueber Stammdaten.
Es wurde nichts migriert und nichts in Odoo 18 geaendert.
```

ENTSCHEIDUNGEN UND UMSETZUNG 30.09.2026 (Teil 6 / Label-Regel):
```
1) Kein Enterprise-Berichtsmodul: Odoo 18 Community bleibt; fehlende Odoo-11-Berichte werden bei
   tatsaechlichem Bedarf mit Community-/ITK-Mitteln nachgebaut (nicht pauschal).
2) Zahlungsart des Bankjournals sichtbar "Manuelle Zahlung (Bank)" (statt "Manual Payment"),
   gesetzt ueber scripts/apply_abrechnung_labels.py (Zeile 1 und 2 des Journals BNK1).
3) Journal BNK1 sichtbar "Bank fuer Tirol und Vorarlberg AG (EUR)", technischer Code BNK1
   unveraendert - ebenfalls ueber den Apply-Lauf.
4) Bericht "ITK-Rechnung mit Zahlung" (Odoo 11: Bericht 538 "Rechnung mit Zahlung") als
   Community-/ITK-Bericht nachgebaut: itk_reports 18.0.1.4.0,
   Vorlage report_itk_invoice_document_with_payments mit Zahlungsblock ("Bezahlt am <Datum>" +
   Betrag, danach offener Betrag), Aktion action_report_itk_invoices_with_payments gebunden an
   account.move. Nachweis lokal (HTML/PDF mit Zahlungsblock, Vergleich gegen die Variante ohne
   Zahlungen) und VM (Drucken-Menue zeigt vier Berichte, Klick erzeugt PDF; 4 OK / 0 FEHL).
5) Die uebrigen alten Odoo-11-Berichte werden nicht pauschal nachgebaut.
Der Apply-Lauf setzt die Punkte 2 und 3 nach jedem Upgrade erneut und prueft sie.
```

ABRECHNUNG: IN ARBEIT (01.10.2026) - visuelle Abnahme der fuenf Belegarten erfolgt, Anna kontrolliert manuell im Browser:
Pruefliste: docs/o11-o18-abrechnung-pruefliste-manuell.md; bis zur Kontrolle keine Umbauten, kein neues Modul.
```
Vollstaendigkeitscheck ohne Lese-Limit (scripts/pruefe_teil5_abdeckung.py, Odoo 11 read-only):
Konten: 34.492 Buchungszeilen gesamt = 5.989 (1201 Bank) + 12.252 (1410 Forderungen)
        + 6.241 (1776 Umsatzsteuer 19%) + 10.010 (8400 Erloese 19% USt); 0 Zeilen ohne Konto
        -> Abdeckung 100 %; Zielkonten Odoo 18: 2801, 2000, 3500, 4000 (alle vorhanden).
Steuern: einzige belegte Steuer Odoo 11 ID 18 "20% Umsatzsteuer" (20 %, percent, sale, exklusiv)
        -> Odoo 18 ID 15 "20% Ust"; belegt in 9.988 Buchungszeilen, 6.241 Steuerzeilen,
        10.029 Rechnungszeilen und 6.275 Rechnungsteuerzeilen -> Abdeckung 100 %.
        22 Rechnungszeilen sind in Odoo 11 ohne Steuer gefuehrt (Anzahlungen, Reisekosten)
        und werden steuerfrei uebernommen (keine Mapping-Luecke).
Journale: nur "Ausgangsrechnungen (EUR)" und "Bank fuer Tirol und Vorarlberg AG (EUR)".
Offen und eingeplant, ohne Blockade der Vorbereitung: sequence_override_regex (K2b, Test an
        Kopie) und Hash-Sicherung/Pruefpfad (K2c) erst mit bzw. nach der echten Migration.
Keine Datenmigration gestartet; kein Testdatensatz migriert.
Erledigt (01.10.2026): kompletter Browser-Menuewalk ueber alle Menuepunkte der App
        (Steuern, Journale, Waehrungen, Steuerzuordnung, Zahlungsbedingungen, Kostenrechnung,
        Bankkonten, Zahlungen, Verwaltung, Einstellungen) lokal und VM, Formulare fuer Rechnung,
        Gutschrift und Zahlung, Listen/Spalten, Filter, Gruppierungen, Suchfelder,
        Assistenten/Dialoge; Testgutschrift in Odoo 18 erzeugt, geprueft und restlos entfernt
        (Bestand vorher = nachher); Regression 0 Fehler; lokal = GitHub = VM.
        Siehe docs/o11-o18-abrechnung-abschlussmatrix.md (Abschnitte 8 bis 11).
```

UMSETZUNG TEIL 5 (30.09.2026) - Stammdaten und Zuordnungen vorbereitet:
```
1) Neues Modul addons/itk_account_migration (18.0.1.0.0): Feld account.move.itk_o11_invoice_number
   "Odoo-11-Rechnungsnummer" (read-only in Formular/Liste/Suche, nur Rechnungen/Gutschriften) und
   account.payment.itk_o11_payment_number "Odoo-11-Zahlungsnummer". Kein Ueberschreiben der
   Odoo-18-Nummern, keine Sequenzaenderung. Mapping: account.invoice.number -> itk_o11_invoice_number.
2) Valorisierungstexte: 10 tatsaechlich verwendete Odoo-11-Texte in
   addons/itk_valorisierung/data/valorisierungstexte_o11.xml (noupdate=1, XML-ID
   valorisierung_o11_<O11-ID>); Odoo 18 hat jetzt 11 Texte, keine Dubletten.
3) Konten-Mapping (read-only gezaehlt, 34.488 Buchungszeilen): O11 1201 Bank -> O18 2801 Bank;
   O11 1410 Forderungen -> O18 2000 Forderungen aus Lieferungen und Leistungen Inland;
   O11 1776 Umsatzsteuer 19% -> O18 3500 Umsatzsteuer 20%;
   O11 8400 Erloese 19% USt -> O18 4000 Brutto-Umsatzerloese im Inland (20%).
   Kein Zielkonto musste neu angelegt werden.
4) Steuer-Mapping: einzige tatsaechlich verwendete O11-Steuer (ID 18 "20% Umsatzsteuer",
   20 %, percent, sale, exklusiv) -> O18 ID 15 "20% Ust" (identisch) = 1:1, keine Neuanlage.
5) Zahlungsnummern-Regel: O11 CUST.IN/<Jahr>/<4-stellig> bzw. CUST.OUT/<Jahr>/<4-stellig>
   (CUST.IN/2019/0001 ... CUST.IN/2026/1061) wird in itk_o11_payment_number erhalten;
   laufende Nummerierung bleibt die unveraenderte Odoo-18-Sequenz; keine Rueckschreibung
   historischer Nummern in die Sequenz; Memo bleibt Rechnungsnummer.
Doku: docs/o11-o18-vergleich-abrechnung-teil5-umsetzung.md, Rohdaten scripts/erhebe_teil5_rohdaten.py
Nachweise lokal (Felder char/gespeichert, 11 Valorisierungstexte, Installation fehlerfrei),
VM gleichartig, Regression 886 OK / 0 FEHL.
Kein Blocker fuer eine spaetere Testmigration eines einzelnen Rechnungsdatensatzes.
```

### 6.14 Abonnements / Subscriptions - **ABGESCHLOSSEN: ABONNEMENTS VOLLSTAENDIG FUNKTIONSFAEHIG UND VOLLSTAENDIG MIGRATIONSVORBEREITET** (Teile 1-15: Modulstatus, Feldinventar, Zustandslogik, Mapping, Stammdaten, Zusatzverkaeufe/EUR, Rechnungserzeugung, Smart Buttons, manueller Rechnungsweg, Reiterbeschriftung, Abonnement Produkte, Produktformular), erste Abnahme 18.09.2026 (Session 118), Teil 14 am 22.09.2026 (Session 119), Teil 15 am 24.09.2026 (Session 120) auf der VM im Browser abgenommen

Dokument: `docs/o11-o18-vergleich-abo-teil1.md`; Teil 14: `docs/o11-o18-vergleich-abo-teil14.md`; Teil 15: `docs/o11-o18-vergleich-abo-teil15-produktformular.md`; Uebergabe und Vollstaendigkeitsbestaetigung: `docs/uebergabe-session-120-abonnements.md` (24.09.2026: jedes in Odoo 11 verwendete Feld, Reiter, Button, Smart Button, Statuswechsel, Filter, Gruppierung und jeder Geschaeftsprozess ist gleich vorhanden, funktional gleichwertig an anderer Stelle vorhanden oder bewusst dokumentiert; keine offene funktionale Abweichung).

**STATUS (24.09.2026, Session 120): ABONNEMENTS = VOLLSTAENDIG FUNKTIONSFAEHIG UND MIGRATIONSVORBEREITET (Teile 1-15).**
Der Unterbereich "Abonnement Produkte" wurde in Teil 15 vollstaendig gegengeprueft (alle Reiter,
Felder, Bezeichnungen, Typen/Relationen, Sichtbarkeitsregeln, Buttons, Pflichtfelder,
funktionale Zusammenhaenge; Odoo 11 Prod read-only) und danach auf der VM abgenommen.

Umgesetzt und auf der VM ausgerollt (`itk_product` 18.0.1.0.2; VM: git pull auf f41b2c6,
Container-Neustart, Modul-Upgrade, Browser-Abnahme am 24.09.2026):

```
1. "Verantwortlich" (responsible_id, many2one res.users) neu im Modul - gleicher Feldname und
   gleiche Relation wie Odoo 11, daher 1:1 migrierbar. In Odoo 11 stand das Feld im Reiter
   "Lager" (bei Dienstleistungen ausgeblendet), in Odoo 18 in eigener Gruppe im ersten Reiter.
   Anlass: das Feld ist in Odoo 11 auf allen 649 Produkten gepflegt, Odoo 17/18 hat es entfernt.
2. Gruppe "Interne Notizen" heisst sichtbar wieder "Notizen" (Odoo-11-Wortlaut), Inhalt
   unveraendert, Odoo-18-Zusatzfunktionen bleiben erhalten.
3. Reiter "Buchhaltung": KEINE Aenderung. In Odoo 11 waren die Kontofelder dieses Reiters selbst
   ausgeblendet (invisible="1") und 0 von 649 Produkten hatte ein eigenes Konto; der Reiter
   zeigte nur Steuern, Dienstleistungslogik und Kontrollrichtlinie. Diese sind in Odoo 18 alle
   an anderer Stelle erreichbar. Keine Gruppenaufnahme, keine zusaetzlichen Rechte, keine
   Ersatzseite (Entscheidung Anna, 24.09.2026).
4. Zeiterfassung: sale_timesheet bleibt uninstalliert. Festlegung: service_type wird NICHT
   uebernommen (51 Produkte, 40 in Abos; 0 Stundenzettelzeilen dieser Produkte von 12.601
   Zeilen gesamt, 246 Auftragszeilen, 0 mit gelieferter Menge). In Odoo 18 normale
   Dienstleistung mit manueller Menge, keine Aufgaben und keine Projekte.
5. Reiter "Bilder": kein Nachbau (product_image_ids in Odoo 11 mit 0 Datensaetzen belegt;
   in Odoo 18 Hauptbild, Dokumente-Smart-Button, Chatter).
```

Nachweise lokal und VM (jeweils 0 FEHL):

```
                                    lokal              VM
verify_produktformular.py          27 OK / 0 FEHL     27 OK / 0 FEHL
verify_abo_produkte.py             34 OK / 0 FEHL     34 OK / 0 FEHL
test_abo_smartbuttons.py           11 OK / 0 FEHL     11 OK / 0 FEHL
browser_produktformular.py         20 OK / 0 FEHL     20 OK / 0 FEHL (echte Klicks, Screenshots)
pruefe_view_render.py               8 OK / 0 FEHL      8 OK / 0 FEHL
verify_s118_abo.py                      -             19 OK / 0 FEHL
pruefe_abo_xmlids.py                    -              0 fehlende XML-IDs
```

Modul-Upgrade `itk_product` 18.0.1.0.1 -> 18.0.1.0.2 (lokal und VM) ohne Fehler, Odoo-Log
fehlerfrei, `/web/login` auf der VM HTTP 200. Browser-Abnahme auf der VM am 24.09.2026:
Klick auf ein Abo-Produkt, Feld "Verantwortlich" gesetzt und gespeichert (danach per RPC gelesen:
[2, 'Administrator']), Gruppe "Notizen" sichtbar, Reiter Verkauf/Einkauf funktionsfaehig, Filter
"Mit Faktor multipliziert" wirkt, keine JavaScript- und keine RPC-Fehler. Der Testwert wurde
danach wieder entfernt (Feld steht auf dem Testprodukt leer). Screenshots:
`Desktop\Odoo18-Abnahme-Session120\01..06_*.png`.

**Offen bleiben nur die Datenschritte der Migration** (keine Funktion dieses Bereichs):
F42 Datenmigration "Verantwortlich" (Wert liegt in Odoo 11 auf 649 Produkten, Feld und Ziel stehen
in Odoo 18 bereit), F43 Zeiterfassung (Festlegung oben: nicht uebernehmen), F48 Bestandsmenge /
Preislistenpositionen als Datenpaket, 8 USD-Testauftraege, NV-Nummern, Cron vor der Migration
pausieren. Werkzeugbefunde dieser Session: F49 (`pruefe_view_render.py`, korrigiert),
F51 (Format der de.po-Datei), F52 (Testfall in `test_abo_smartbuttons.py`, korrigiert),
F53 (Sprachkontext bei Suchen auf uebersetzten Feldern).

> Hinweis (Session 119): Die in den Teilen 7-13 genannten Fassungen `itk_subscription`
> 18.0.1.2.3 bis 18.0.1.2.6 sind im Repo nicht belegt. Die Git-Historie und die Datenbank
> stehen auf **18.0.1.2.1** (1.0.0 -> 1.1.0 -> 1.2.0 -> 1.2.1); die Code-Aenderungen der Teile
> 10-13 sind vorhanden, nur die Versionsnummer wurde nie hochgesetzt.

**Teil 14 erledigt (Abonnement Produkte) - 22.09.2026 (Session 119):** `docs/o11-o18-vergleich-abo-teil14.md`.
Listenansicht: `categ_id` als "Interne Kategorie" und `is_multi_factor_product` als sichtbare
Spalten in der Spaltenauswahl (`itk_multifactor` 18.0.1.1.1, Modul haengt jetzt von `itk_product`
ab). Neue Suchansicht `product.template.search.abo.produkte` mit den Filtern
"Mit Faktor multipliziert" und "Aktive Abonnement Produkte" sowie den Gruppierungen
"Status" (`product_type_id`) und "Mit Faktor multipliziert"; die Odoo-18-Filter und
-Gruppierungen bleiben erhalten. Die Odoo-11-Filter "Service Type ..." wurden bewusst nicht
nachgebaut - sie hatten dort Einzelwerte der ITK-Produktart fest verdrahtet, in Odoo 18 leistet
das die Gruppierung nach `product_type_id`. `to_multiply_by_factor` ist aus dem Produktformular
entfernt (`itk_product` 18.0.1.0.1; Feld bleibt in der DB) - es existiert in Odoo 11 nicht und ist
eine Dublette zu `is_multi_factor_product`. **Lager:** `stock` wird NICHT installiert; read-only
belegt (0 erledigte Lagerbewegungen, 0 Bestandszeilen, 0 Produkte mit Bestand, 0 Lagerartikel,
1 Standard-Lagerhaus, 0 Bestellvorschlaege), daher entfallen Bestandsmenge und Geplante
Bestandsmenge begruendet. Nachweise VM: `verify_abo_produkte.py` 34 OK / 0 FEHL,
`browser_abo_produkte.py` 47 OK / 0 FEHL (Screenshots 60-66), dazu die Gegenpruefung des
Gesamtbereichs `verify_s118_abo` 19 OK / 0 FEHL, `pruefe_abo_xmlids` 0 fehlende XML-IDs,
`test_abo_rechnungslauf` 13 OK / 0 FEHL, `test_abo_manuelle_rechnung` 16 OK / 0 FEHL,
`test_abo_smartbuttons` 11 OK / 0 FEHL.
**STATUS (Stand zum jeweiligen Teil-Abschluss): ABONNEMENTS WAREN VOLLSTAENDIG FUNKTIONSFAEHIG UND VOLLSTAENDIG MIGRATIONSVORBEREITET - massgeblich ist der Status am Abschnittsanfang (zuletzt Session 120: Teile 1-15 abgeschlossen).**

**Modulstatus:** `sale_subscription` ist ein Katalogeintrag von Odoo Enterprise (OEEL-1) ohne Quellcode
-> Zustand `uninstallable`, kein Traeger der Funktion und kein Blocker. Traeger ist das ITK-eigene Modul
**`itk_subscription` 18.0.1.1.0** (installiert, LGPL-3), zusaetzlich `itk_multifactor`. In Odoo 11 Prod ist
genau dasselbe ITK-Modul im Einsatz (11.0.1.1). Modelle, Aktionen, Menues und 2 aktive Cronjobs aufgenommen;
5 Test-Abos in Odoo 18 technisch konsistent (3 mit Verkaufsauftrag verknuepft).

**Odoo 11 Prod (read-only):** 1.764 Abos (draft 3, open 1.482, close 48, cancel 231), 2.434 Zeilen,
1.722 mit Verkaufsauftrag verknuepft, 5 Vorlagen (Jahres-, Monats-, Quartalsabrechnung, 5-Jahresabo,
Jahresabo mit 12 Monaten Mindestlaufzeit). Feldnutzung gezaehlt (recurring_rule_type/interval/next_date/total,
partner_id, template_id, pricelist_id, date_start je 1.764; close_reason_id 291; tag_ids 0).

**Vorlaeufiger Feldvergleich (18 Felder):** durchgehend 1:1 abbildbar; ohne Odoo-11-Quelle sind
payment_term_id, in_progress (berechnet) und team_id. Keine Migration, keine Aenderung in Odoo 11.

**Teil 2 erledigt:** `docs/o11-o18-vergleich-abo-teil2.md` - vollstaendiges Feldinventar beider Modelle
(`sale.subscription`: 40 Felder, `sale.subscription.line`: 11 Felder) mit Typ/Relation/required/readonly/
store-compute, Nutzung in Odoo 11 und Ziel in Odoo 18. Ergebnis: **Feldnamen, Typen, Relationen und
Selection-Werte sind identisch**; kein Feld ohne Ziel, keine Transformation. Ohne Odoo-11-Nutzung:
analytic_account_id, industry_id, minimum_contract_period, noticeperiod, payment_mandatory, payment_token_id,
tag_ids. Nur in Odoo 18: `has_message`; obsolet: `__last_update`. Einziger Labelunterschied:
`recurring_next_date` (Odoo 11 "Start-Datum des nächsten Leistungszeitraums" / Odoo 18 "Datum der nächsten
Rechnung"). Status- und Intervallwerte identisch. 42 Abos ohne Verkaufsauftrag = Altbestand 2013/2014
(open 24, cancel 16, close 2; yearly 39, monthly 3) -> Auswahlregel offen. Zeilenmodell: 2.434 Zeilen,
alle mit Produkt/Menge/Preis/ME und Multiplikationsfaktor (`qty_multiplication_factor`, ITK);
Zeile->Abo ueber `analytic_account_id` ("Aboauftrag") in beiden Systemen.

**Teil 3 erledigt:** `docs/o11-o18-vergleich-abo-teil3.md`. View-Vergleich: 37 gegen 36 Felder in gleicher
Reihenfolge, gleiche Reiter, gleiche Statusleiste, gleiche Listenspalten, gleiche Suchfilter, gleiche
Aktions- und Smart Buttons mit **identischen Sichtbarkeitsregeln**. Browser-Pruefung (Odoo 11 nur lesend,
Odoo 18 VM): Zustaende Neu und Laufend sowie Abo ohne Auftrag. Smart Buttons/Zaehler arbeiten (1 Rechnungen,
1 Verkauf bzw. 0/0). **Abos ohne Verkaufsauftrag laufen in Odoo 18 vollstaendig** (Abo 172 und 185 auf der VM).
Einziger Unterschied: Odoo 11 hatte den Button "Abonnement-Zusatzverkäufe", Odoo 18 fuehrt dies ueber den
Assistenten "Optionen hinzufügen" - funktional vorhanden. Beschriftung `recurring_next_date` bleibt
(Entscheidung Anna). 42 Alt-Abos: keine Regel festgelegt, nur funktional geprueft.

**Teil 13 erledigt (Reiterbeschriftung):** `docs/o11-o18-vergleich-abo-teil13.md`. Erster Reiter im
Abo-Formular heisst wie in Odoo 11 "Wiederkehrende Buchungen" (vorher "Abonnement-Einträge").
Gesetzt im Modul selbst (views/sale_subscription_views.xml, <page string=...>) plus de.po-Eintrag,
damit ein Modul-Upgrade die Beschriftung nicht zuruecksetzt. itk_subscription 18.0.1.2.6.
Browser auf der VM: normales Abo und Zu erneuernde Abonnements je mit dem Reiter
"Wiederkehrende Buchungen" bestaetigt (3 OK / 0 FEHL, Screenshots 54/55).

**Teil 12 erledigt (manueller Rechnungsweg + Finanzposition):** `docs/o11-o18-vergleich-abo-teil12.md`.
Ursache: Odoo 11 liefert IDs, Odoo 18 Recordsets; der Nachbau map_account/map_tax fuehrte zu
psycopg2.ProgrammingError: can't adapt type 'account.fiscal.position'. Behoben durch die Odoo-18-native
Loesung: Finanzposition nur noch als ID am Beleg, Konten-/Steuerzuordnung macht Odoo selbst.
itk_subscription 18.0.1.2.5. Nachweise: Cron-Weg 13 OK / 0 FEHL, manueller Weg 16 OK / 0 FEHL
(lokal und VM), Browser-Klick auf der VM 4 OK / 0 FEHL (genau eine neue Rechnung).

**Neue Abnahmeregel:** Ein Button gilt erst als funktionsfaehig, wenn er auf der VM im echten Browser
geklickt wurde und der Vorgang ohne RPC-/Serverfehler durchlaeuft.

**STATUS (Stand zum jeweiligen Teil-Abschluss): ABONNEMENTS WAREN VOLLSTAENDIG FUNKTIONSFAEHIG UND VOLLSTAENDIG MIGRATIONSVORBEREITET - massgeblich ist der Status am Abschnittsanfang (zuletzt Session 120: Teile 1-15 abgeschlossen).**

**Teil 11 erledigt (Smart Button Rechnungen):** `docs/o11-o18-vergleich-abo-teil11.md`.
account.action_invoice_tree1 (Odoo-11-XML-ID) durch account.action_move_out_invoice_type ersetzt,
views im vom Client erwarteten Listenformat. Alle 38 XML-IDs des Moduls geprueft (scripts/pruefe_abo_xmlids.py):
keine fehlende ID mehr. Funktionstest scripts/test_abo_smartbuttons.py lokal und VM 11 OK / 0 FEHL
(0 / 1 / mehrere Rechnungen, Gegenprobe fremde Rechnung, Verkauf-Button). Browsertest VM 54 OK / 1 FEHL,
der letzte Nachweis manuell durch Anna erbracht: Abo 183 oeffnet die zugehoerigen Rechnungen,
Abo 172 blendet den Button bei 0 Rechnungen aus.
**STATUS (Stand zum jeweiligen Teil-Abschluss): ABONNEMENTS WAREN VOLLSTAENDIG FUNKTIONSFAEHIG UND VOLLSTAENDIG MIGRATIONSVORBEREITET - massgeblich ist der Status am Abschnittsanfang (zuletzt Session 120: Teile 1-15 abgeschlossen).**
Keine offenen fachlichen oder technischen Grundsatzentscheidungen fuer dieses Modul.

**Teil 10 erledigt (Abschluss Rechnungserzeugung):** `docs/o11-o18-vergleich-abo-teil10.md`.
Vier Odoo-11-Kompatibilitaetsreste in itk_subscription behoben (get_fiscal_position,
map_tax-Signatur, message_post_with_view, fehlendes move_type am account.move).
Ohne move_type entstand ein Buchungssatz statt einer Kundenrechnung - daher 0,00 Euro.
itk_subscription 18.0.1.2.3. Nachweis `scripts/test_abo_rechnungslauf.py`:
**lokal 13 OK / 0 FEHL, VM 13 OK / 0 FEHL** (Rechnung 65,00 netto + 13,00 Steuer = 78,00 EUR,
recurring_next_date fortgeschrieben, kein Duplikat, Verknuepfung ueber invoice_origin).
**Status: ABONNEMENTS = VOLLSTAENDIG FUNKTIONSFAEHIG UND VOLLSTAENDIG MIGRATIONSVORBEREITET.**

**Teil 7 erledigt (Endabnahme):** `docs/o11-o18-vergleich-abo-teil7.md`. Fehlende Zugriffsregeln der drei
Assistenten-Modelle ergaenzt (itk_subscription 18.0.1.2.1) - der Button "Abonnement-Zusatzverkäufe" wirft
jetzt keinen Zugriffsfehler mehr. USD-Testrechnungen geloescht, EUR-Testdaten fuer alle fuenf Zustaende
angelegt, neue Belege erhalten EUR. Browser-Abschlusspruefung auf der VM **48 OK / 0 FEHL**.
**Status: ABONNEMENTS = VOLLSTAENDIG FUNKTIONSFAEHIG, EUR-KONSISTENT UND MIGRATIONSBEREIT.**
Restposten: 8 bestaetigte USD-Testauftraege aus frueheren Sessions (Odoo sperrt Aenderung und Loeschen).

**Teil 6 erledigt (Abschluss Zusatzverkaeufe + EUR):** `docs/o11-o18-vergleich-abo-teil6.md`.
Button "Abonnement-Zusatzverkäufe" im Abo-Formular ergaenzt (Odoo 11: Aktion 513 = derselbe Assistent
`sale.subscription.wizard`; Odoo 18: Aktion 1101 `itk_subscription.wizard_action`) - Modulversion
18.0.1.2.0, Odoo-18-Aktion bleibt erhalten. Waehrung: `scripts/fix_currency_eur.py` (Partner, Abos,
Angebote auf die EUR-Preisliste; 0 USD-Abos). Offen: 8 bestaetigte Testauftraege + 4 Testrechnungen
tragen noch USD (Odoo sperrt Waehrungsaenderungen bei bestaetigten Belegen) - Entscheidung Anna.
Falle: neue Addon-Dateien erst nach `docker restart odoo18` sichtbar.

**Teil 5 erledigt (Abschluss):** `docs/o11-o18-vergleich-abo-teil5.md`. Die in Odoo 11 referenzierten
Stammdaten sind angelegt: 1 fehlende Vorlage ("J- Jahresabrechnungsabo-Mindestvertragsdauer 12 Monate",
Odoo 11: 1 Abo) und 26 fehlende Beendigungsgruende (Odoo 11: 170 Verwendungen). Nicht angelegt: Vorlage
"5-Jahresabo" (0 Referenzen) und 2 Gruende ohne Verwendung. Werkzeug `scripts/apply_abo_stammdaten.py`
(lokal + VM ausgefuehrt). Abschlusspruefung `scripts/verify_s118_abo.py`:
**lokal 19 OK / 0 FEHL, VM 19 OK / 0 FEHL**. Damit hat jedes in Odoo 11 verwendete Feld, jede verwendete
Vorlage und jeder verwendete Beendigungsgrund ein eindeutiges Ziel in Odoo 18.
**Status: ABONNEMENTS = VOLLSTAENDIG FUNKTIONSFAEHIG UND MIGRATIONSBEREIT** (ohne Datenmigration).
Offen nur noch Datenschritte: Auswahlregel, Reihenfolge Auftraege-vor-Abos, Multiplikationsfaktor-Freigabe,
Rechnungsstellung nach der Migration, Uebernahme der NV-Nummern.

**Teil 4 erledigt:** `docs/o11-o18-vergleich-abo-teil4.md` mit vollstaendiger Migrations-Mapping-Tabelle
(Abo-Kopf, Abo-Zeilen) und Abschlusspruefung. Ergebnis: **keine strukturellen oder funktionalen Luecken**
-> Bereich strukturell und funktional **MIGRATIONSVORBEREITET** (ohne Datenmigration).
Reiter in beiden Systemen gleich (O18 zeigt Positionen zusaetzlich inline); Vorlagen-Felder, Menues,
Cronjobs (2, identisch), Rechte (ITK-Abonnements Manager/User + Portal) und Rechnungsmechanik gleich.
**Stammdaten-Luecken vor der Migration:** 2 Vorlagen fehlen in Odoo 18 (5-Jahresabo, Jahresabo mit
12 Monaten Mindestlaufzeit) und 28 von 33 Beendigungsgruenden (Odoo 11: 33, in Odoo 18 5).
Offen (Abschnitt 7 des Dokuments): Auswahlregel der Abos, Reihenfolge Auftraege vor Abos,
Multiplikationsfaktor-Freigabe, Rechnungsstellung nach der Migration, Uebernahme der NV-Nummern.
Migrationsvorbereitung (Reihenfolge Auftraege vor Abos, Feldzuordnung 1:1 aus Teil 2).
Wortlautentscheidung `recurring_next_date`, Auswahlregel fuer die 42 Alt-Abos - erst danach Anpassungen.
Formulare/Smart Buttons/Zustandslogik im Browser, Zeilenmodell - erst danach Anpassungen.


### 6.13 Angebote / Verkaufsauftraege (sale.order) - **ABGESCHLOSSEN, MIGRATIONSVORBEREITET**, 18.09.2026 (Session 117)

Dokument: `docs/o11-o18-strukturvergleich-angebote-auftraege.md`.

**Odoo 11 Prod (read-only):** 2.460 Auftraege (draft 5, sent 0, sale 2.308, done 0, cancel 147),
1.764 Abonnements (open 1.482, cancel 231, close 48, draft 3). Zustands-Browserpruefung nutzt damit
Angebot, bestaetigter Auftrag und storniert; "Angebot gesendet" und "Abgeschlossen" sind in Odoo 11 unbenutzt.

**Feldvergleich:** Alle in Odoo 11 verwendeten Felder haben ein Odoo-18-Ziel. Die ITK-Kontaktfelder
(Verkaufskontakt, Verwaltungskontakt, Technischer Kontakt, Endkunde, Produktkategorie) sind im Modul
`itk_sale_management` vorhanden und im Formular eingebunden. Entfallen: `incoterm` (O11: 0 Nutzungen),
`analytic_account_id` (Kostenstelle, O11: 0 -> Odoo 18 `sale.order.line.analytic_distribution`),
`payment_tx_id/-ids` (O11: 0 -> `transaction_ids`). `confirmation_date` (O11: 2.436 Nutzungen) hat in
Odoo 18 kein Feld -> KLAERUNG NOETIG.

**Statusumwandlung:** Odoo 11 `draft/sent/sale/cancel` = 1:1; `done` (0 Datensaetze) entfaellt in Odoo 18
und ist dort `state=sale` + `locked=True` (Feld und Buttons action_lock/action_unlock geprueft).

**Beschriftungen angeglichen (apply_sale_labels.py):** team_id -> Vertriebskanal,
administrative_contact_id -> Verwaltungskontakt, opportunity_id -> Chance, source_id -> Referenz.
Bewusst Odoo-18-Wortlaut: Auftragsdatum, Gueltigkeit, Rechnungsstatus, Auftragspositionen.

**Browser-Test (mehrere Zustaende):** `scripts/browser_auftraege_pruef.py` - Angebot, Angebot gesendet,
bestaetigter Auftrag, storniert, Auftrag mit Rechnung, Auftrag mit Abonnement. Smart Buttons und Zaehler
geprueft, Klicks oeffnen Rechnungs- und Abo-Ansicht. Lokal 9 OK / 0 FEHL.

**Nachweis:** `scripts/verify_s117_auftraege.py` -> lokal 58 OK / 0 FEHL, VM 58 OK / 0 FEHL.
Offen: Mehrzustands-Browserpruefung auf der VM, Abo-Modul `sale_subscription` (lokal `uninstallable`),
Zielregel fuer `confirmation_date` (KLAERUNG). Keine Auftrags-/Rechnungs-/Abodaten uebernommen
(Odoo 18 Teststand 16 Auftraege, 5 Abos).


### 6.12 Kundenverwaltung / CRM (Menue, Ansichten, Suche, Konfiguration, Funktionen, Berechtigungen) - **ABGESCHLOSSEN, VM-ABGENOMMEN**, 17.09.2026 (Session 115)

Dokumentation: `docs/o11-o18-strukturvergleich-kundenverwaltung-crm.md` (ergaenzt 6.11).

**Auftrag:** vollstaendiger Funktions- und UI-Abgleich Odoo 11 Kundenverwaltung gegen Odoo 18 CRM. Weiterhin keine
Datenmigration: 0 der 359 Verkaufschancen und 0 der 6.608 Interessenten uebernommen; Odoo 11 Prod ausschliesslich read-only.

**Angepasst (itk_crm 18.0.1.5.4):**
1. Sichtbarer App-Name "CRM" -> **"Kundenverwaltung"** (Menue `crm.crm_menu_root`, Quelle + de_DE + en_US). Ursache:
   Moduldaten mit `noupdate=0` - ein Upgrade des Moduls `crm` setzte die Quelle zurueck, die alte de_DE-Uebersetzung "CRM" blieb stehen.
2. Konfigurationsgruppe "Pipeline" -> **"Interessenten und Chancen"** (Menue `crm.menu_crm_config_lead`, Wortlaut aus Odoo 11).
3. Beide Namen werden bei jedem itk_crm-Upgrade erneut gesetzt (`setup_runtime.setup_all`, Migration 18.0.1.5.4).

**Menuevergleich:** Hauptmenues Aktivitaeten, Pipeline, Kunden, Berichtswesen, Konfiguration (Reihenfolge = Odoo 11);
Pipeline-Untermenues Pipeline, Interessenten, Angebote, Teams; Konfiguration: Einstellungen, Vertriebskanaele, Aktivitaeten
-> Aktivitaetstypen/Aktivitaetsplaene, Wiederkehrende Plaene, Interessenten und Chancen -> Stichwoerter, Verlustgruende,
Lead-Generierung. Wurzelmenue-Gruppen: Sales/Administrator + Sales/User (Odoo 11: Manager + User) - gleichwertig.

**Bewusst Odoo-18-standardmaessig:** Klassifizierung, Prognose, Wiederkehrende Plaene, Aktivitaetsplaene, Lead-Generierung,
Berichte aus `crm.lead` statt `crm.opportunity.report`, Smart Buttons.

**Ansichten und Suche:** Die ITK-Felder (`x_Anrede_Lead`, `x_Lead_Quelle`, `x_Produktinteresse`, `x_lead_status`) stehen in
Odoo 18 an denselben Stellen wie in Odoo 11 (Liste der Interessenten + Formular, nicht in der Liste der Verkaufschancen).
Filter und Gruppierungen sind in Odoo 18 eine Obermenge; entfallen: Filter "Archiviert" (ueber Gewonnen/Verloren abgedeckt)
und "Opt Out exkludieren" (Odoo 18 hat kein `opt_out` mehr); die Gruppierung "Kunde" (`partner_id`) fehlt.

**Wortlaute (Nachtrag, itk_crm 18.0.1.5.5):** auf die in Odoo 11 sichtbaren Begriffe umgestellt - Stufe
(statt Phase), Verkaeufer (statt Vertriebsmitarbeiter), Vertriebskanal (statt Verkaufsteam), Ablehnungsgrund
(statt Verlustgrund; Odoo 11 Prod schreibt dort "Ablehnugsgrund" mit Schreibfehler), Erwartetes Abschlussdatum;
Konfigurationsmenues "Lead Tags" (statt Stichwoerter) und "Ablehnungsgruende" (statt Verlustgruende),
Stufenliste heisst "Stufen" (statt "Phasen"). Nur Oberflaeche, technische Namen unveraendert.

**Gruppierung "Kunde":** in Odoo 11 vorhanden, in Odoo 18 ergaenzt - in beiden Suchansichten (Chancen und
Interessenten) als Filter `groupby_partner` mit `context={'group_by': 'partner_id'}`. Keine Datenänderung.

**Berichtswesen/Vertriebskanaele:** In Odoo 11 war das die Team-Kanbanansicht (Aktion "Sales Channels"), kein
Auswertungsbericht. Odoo 18 hat dieselbe Ansicht; der Menuepunkt "Vertriebskanaele" wurde unter Berichtswesen
(Sequenz 10) auf die vorhandene Odoo-18-Aktion gelegt. Kein Bericht nachgebaut.

**Berechtigungen:** Die Odoo-11-Gruppe "Manager (edit)" (24 Regeln auf ITK-Stammdaten) wurde read-only
analysiert und auf Odoo-18-Rollen gemappt - kein Nachbau. Einziger fachlicher Unterschied: Loeschrecht auf
`crm.lead` (Odoo 11: 13 Benutzer, Odoo 18: nur Sales/Administrator) -> KLAERUNG NOETIG.

**Favoriten:** 17 gespeicherte Suchen in Odoo 11 analysiert (2 geteilt, 15 benutzerindividuell, 2 als Standard
je Benutzer). Keine Uebernahme; kein systemweit wichtiger Standardfilter festgestellt.

**Berechtigungen (Entscheidung Anna, umgesetzt):** Die Odoo-11-Gruppen existieren in Odoo 18 bereits als
ITK-Gruppen (`itk_crm.itk_group_user`, `itk_crm.itk_group_manager`). Ergaenzt wurde genau ein Recht:
`access_itk_crm_lead_manager` = Loeschen (nur `perm_unlink=1`) auf `crm.lead` fuer "Manager (edit)" -
keine Sales-Administratorrechte. **Keine Benutzerzuordnung** (nur Administrator, wie vom Modul angelegt).
Modulstand **18.0.1.5.7** (18.0.1.5.6 Berechtigung, 18.0.1.5.7 Aktionsnamen).

**Favoriten:** bewusst nicht uebernommen (Entscheidung Anna); 15 von 17 waren benutzerspezifisch.
**Filterbezeichnungen:** Odoo-18-Standardfilter bleiben unveraendert (u. a. "Meine Pipeline"),
Abweichungen dokumentiert.

**Browser-Abnahme auf der VM (31 OK / 0 FEHL):** App-Name Kundenverwaltung, Haupt- und Untermenues,
Pipeline mit 9 Stufen, Interessenten, Angebote, Kunden, Berichtswesen inkl. Vertriebskanaele,
Konfiguration (Stufen 9, Vertriebskanaele 7, Ablehnungsgruende 5, Lead Tags 10), Suche/Filter/Gruppieren
inkl. Kunde, Formular mit Beschriftungen. Screenshots 31-42 (`_VM_`).

**Browser-Abnahme VM (34 OK / 0 FEHL):** App-Name, Haupt- und Untermenues, Pipeline mit 9 Stufen, Interessenten
(ITK-Spalten), Angebote, Kunden (76 Karten), Berichtswesen/Vertriebskanaele (13 Team-Karten), Konfiguration
(Stufen 9 mit Aktionsname "Stufen", Vertriebskanaele 7, Ablehnungsgruende mit Aktionsname, Lead Tags 10 mit
Aktionsname), Suche/Filter/Gruppieren inkl. Kunde, Formular. Screenshots 31-42.

**Befund und Dauerloesung (F34):** Auf der VM setzt ein itk_crm-Upgrade die deutschen Feldbeschriftungen auf
die Quelltexte zurueck (Odoo 18 gleicht `ir.model.fields` nach dem Modul-Setup ab; lokal nicht reproduzierbar,
kein VM-Logzugang). Deshalb: neues Werkzeug `scripts/apply_crm_labels.py` (setzt die Beschriftungen idempotent,
lokal + VM, `--pruefen` nur lesend) - **verbindlich nach jedem itk_crm-Upgrade auf der VM** - sowie
`addons/itk_crm/i18n/de.po` als Moduluebersetzung. Modulstand final **18.0.1.5.7**.

**Bundeslaender bereinigt (F35, Session 116):** In Odoo 18 waren 357 `res.country.state`-Namen als
Mojibake gespeichert (UTF-8-Bytes als CP437 gelesen; China, Japan, Thailand, Lettland, Mongolei, Rumaenien,
Tuerkei, Vietnam, Suedkorea, Litauen, Russland) - identisch lokal und auf der VM, in Odoo 11 Prod nicht
vorhanden. Bereinigt mit `scripts/repair_state_names.py` (Sollwerte aus der Odoo-Moduldatei) - nur
State-Stammdaten, keine Kontakte/Interessenten. Danach 0 Abweichungen, 0 verdaechtige Zeichen.
Wichtig fuer die Migration: Odoo 11 fuehrt eigene AT-Codes (Bgld./Ktn./NOe/...), Odoo 18 die Codes 1-9 ->
Mapping ueber Name und Land, nicht ueber Code. Werkzeug `scripts/verify_s115_kundenverwaltung.py`
Abschnitt 11 prueft beschaedigte Zeichen, leere Namen, doppelte Land/Code-Kombinationen und Oesterreich.

**Nachweis:** `scripts/verify_s115_kundenverwaltung.py` -> lokal 41 OK / 0 FEHL, VM 41 OK / 0 FEHL;
Browser VM 38 OK / 0 FEHL (inkl. Bundesland-Suche 'Buc' -> București, '北' -> 北京市, Gegenprobe Mojibake).
`scripts/browser_kundenverwaltung_pruef.py` -> lokal 27 OK / 0 FEHL (18.0.1.5.5), VM 22 OK mit den 5 erwarteten
Wortlaut-Abweichungen vor dem Deploy von 18.0.1.5.5. Screenshots 31-38 im Desktop-Ordner.

**Offen (KLAERUNG NOETIG):** 1) 17 Odoo-11-Favoriten (2 Standard) - uebernehmen, neu aufbauen oder verwerfen 2) Gruppierung
"Kunde" ergaenzen? 3) ITK-Zugriffsregel `access_itk_crm_lead_manager` (Gruppe "Manager (edit)", 13 aktive Benutzer in Prod)
4) Odoo-11-Berichtsmenue "Vertriebskanaele" nachbauen? 5) Wortlaute (wie 6.11) 6) Datenmigration (Auswahlregel, Zeitpunkt).

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

## Verbindlicher Arbeitsstandard: Abschlussdurchgang je Modul (ab 01.10.2026)

Gilt fuer Abrechnung, Verkauf, Abonnements und alle weiteren Module. Ein Bereich gilt erst als
migrationsbereit, wenn ALLE Punkte belegt sind - Skriptausgabe oder "View laedt fehlerfrei" genuegt nie.

1. Sichtbarer Browserabgleich (lokal UND VM, echte Menuepunkte, echte Datensaetze, Screenshots angesehen)
   - Menuepunkte, Listenansichten, alle Spalten, Formularansichten, Kopfbereich, alle Reiter, alle Gruppen
   - Buttons, Smart Buttons, Statusleiste, Aktionen, Assistenten/Dialoge, Druck-/Versandfunktionen
   - Suchfelder, Filter, Gruppierungen
2. Sichtbare Angleichung an Odoo 11, wo technisch sauber machbar
   - gleiche fachliche Bedeutung = gleicher sichtbarer Wortlaut
   - Position, Reihenfolge und Gruppierung an Odoo 11
   - keine Doppelanzeigen, keine verwaisten Beschriftungen, keine leeren Bloecke, keine Layoutreste
   - Odoo-18-Zusatzfelder und -funktionen bleiben vollstaendig erhalten
   - technische Feldnamen/Modelle werden nie umbenannt; Pflichtfeldlogik nicht aus Optik aendern
3. Feldmapping vollstaendig: Odoo-11-Modell/Feld -> Odoo-18-Modell/Feld mit Kennzeichnung
   1:1 / Transformation / Neuberechnung / bewusst nicht migrieren, nur fuer tatsaechlich belegte Felder
4. Beziehungen getrennt pruefen (many2one, many2many, one2many); niemals IDs blind uebernehmen,
   sondern fachliche Schluessel definieren (z. B. Rechnungsnummer, Partnername, Kontocode)
5. Stammdaten vollstaendig: Konten, Steuern, Journale, Zahlungsbedingungen, Einheiten, Tags,
   Projektkategorien, Valorisierungstexte, Zahlungsarten
6. Statuswerte und Zustaende abgleichen (Entwurf/Gebucht/Bezahlt, Abo-Zustaende, Zahlungsstatus)
7. Verknuepfungen pruefen: Rechnung <-> Zahlung <-> Gutschrift <-> Auftrag <-> Abo
8. Berechnete Felder nur migrieren, wo Odoo 18 sie nicht selbst korrekt neu berechnet
9. Pflichtfelder, Constraints, Unique-Constraints von Odoo 18 beruecksichtigen
10. Migrationsreihenfolge dokumentieren (Stammdaten -> Beziehungen -> Belege -> Verknuepfungen)
11. Erst danach Testmigration mit wenigen repraesentativen Datensaetzen - nie produktiv ohne Freigabe

Hilfsmittel: `scripts/browser_abrechnung_vollstaendig.py` (Browserdurchgang, Protokoll in
`docs/_abrechnung_durchgang.json`), `scripts/_dom_waehrung.py` (DOM-Herkunft sichtbarer Elemente),
`scripts/apply_abrechnung_labels.py --instanz vm`.

Lehre aus dem Rechnungsformular (01.10.2026): Der Odoo-18-Kopfbereich besteht aus expliziten
label-Elementen und nolabel-Feldern. Wird ein Feld daraus verschoben, MUSS auch seine Beschriftung
entfernt werden, sonst bleibt eine verwaiste Beschriftung sichtbar ("Waehrung" ohne Wert).

### Pruefprotokoll je Modul (ausfuellen)

| Modul | Browserabgleich lokal | Browserabgleich VM | Feldmapping | Beziehungen | Stammdaten | Statuswerte | Verknuepfungen | Constraints | Reihenfolge | Screenshots | Stand |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Abrechnung | vorhanden | vorhanden | 273 belegte Felder, 0 Luecken | vorhanden | vorhanden | vorhanden | vorhanden | vorhanden | vorhanden | vorhanden | IN ARBEIT (offen: Produktfilter-Entscheidung, Testmigration, Restansichten) |
| Verkauf | vorhanden | vorhanden | Teil 5 vorhanden | vorhanden | vorhanden | vorhanden | vorhanden | vorhanden | vorhanden | vorhanden | abgeschlossen (R1-R8) |
| Abonnements | vorhanden (02.10.) | vorhanden (02.10.) | Feldbestand verglichen (57/64 Felder, 0 echte Luecken); siehe docs/o11-o18-abonnement-abgleich.md | nicht betroffen | Cron/Fristen geprueft | Zustaende 1:1 plus O18-Zusatz pending | 1:1 | nicht betroffen | vorhanden | vorhanden | abgeglichen (PR #184/#185), Abweichungen dokumentiert |
