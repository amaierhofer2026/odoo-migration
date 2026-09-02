# MIGRATION-READINESS-CHECKLIST — Odoo 18 Abnahme vor der Odoo-11-Datenmigration

> **Zweck:** Fachliche und technische Abnahme der Odoo-18-Testumgebung (ITK), **bevor** produktive Odoo-11-Daten migriert werden.
> **Referenzumgebung:** https://k001959vsx.ipax.at — DB `odoo18_test` (IPAX-Test-VM, Ubuntu 26.04, Docker odoo:18 + postgres:16)
> **Stand:** 02.09.2026 — Abschnitt 1 (A Sprache) read-only-RPC-Inventar ausgeführt (Session 80, de_DE/en_US-Kontext, uid=2, gegen VM); Befunde F14–F26 ergänzt, **nichts behoben**. Detail-Inventar: `docs/abnahme_sprache_ui_abschnitt1.md`.
> **Datengrundlage dieses Dokuments:** ausschließlich read-only-Analysen (SQL über die VM-DB, Repo-Vergleich). Keine Änderungen an DB, Modulen, Views, Konfiguration oder Daten.
>
> **WICHTIGE REGELN (fortgeschrieben):**
> - Keine Korrekturen ohne ausdrückliche Freigabe. Befunde werden hier dokumentiert, nicht behoben.
> - Kein Feld-für-Feld-Vergleich mit Odoo 11: Es existiert derzeit **keine laufende Odoo-11-Referenz** (alte VM am 31.08.2026 dekommissioniert). Das Mapping O11→O18 wird separat erstellt, sobald eine verlässliche Referenz verfügbar ist (gesicherte O11-Testumgebung, lesender Zugriff auf produktives O11, Exporte oder Dokumentation). Abschnitt 6 bleibt deshalb **OFFEN**.
> - Kein `-u all`, keine Modul-Upgrades, keine Datenmigration, keine Testdaten, kein E-Mail-Server-Setup in dieser Phase.

## Status-Legende

| Status | Bedeutung |
|---|---|
| OFFEN | Noch zu testen (Abnahme läuft) |
| OK | Geprüft, entspricht Erwartung |
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
| **res_currency.symbol** | Währungssymbole | EUR-Symbol = `Ôé¼` statt `€` (Bytes `\303\224\303\251\302\274`), weitere Symbole ebenfalls CP850-kodiert (GBP `┬ú`, CZK `K─ì`, PLN `z┼é` …) | **FEHLER** | CP850-Schaden in der Symbolspalte (nicht Teil der Reparatur vom 13.08.) | Symbolwerte korrigieren (nach Freigabe); s. auch Abschnitt 3 | nein |
| **ir_module_module.shortdesc** | installierte Modul-Labels | `account_payment`: „Zahlung ÔÇô Konto“; 14 weitere (nicht installierte) l10n-/mrp-/pos-Module mit ÔÇô-Muster | **FEHLER** | CP850-Mojibake „–“ → „ÔÇô“ | de_DE-Translations korrigieren (nach Freigabe) | nein |
| **de_DE-Übersetzungen (Feldlabels/Auswahlwerte)** | sichtbare UI-Übersetzungen | 3 Stellen mit CP850-Artefakten: `account.move.status_in_payment` = „Status ÔÇ×In ZahlungÔÇ£“; `account.reconcile.model.line.show_force_tax_included` = „ÔÇ×Steuer inklusive erzwingenÔÇ£ anzeigen“; `res.partner.peppol_eas`-Auswahlwert `0245` = „SK-Steueridentifikationsnummer (DI─î)“ (via Delegation auch res.users/res.company) | **FEHLER** | CP850-Mojibake (Anführungszeichen „…“, „Č“) — **nicht Teil der Reparatur vom 13.08.**, nur dokumentiert (F26) | Übersetzungen korrigieren (nach Freigabe; Encoding-Regel beachten) | ja (RPC 02.09.) |

**Gesamtbild Encoding:** Die CP850-Reparatur vom 13.08.2026 ist in den fachlichen Tabellen bestätigt (0 ├-Zeilen in Partner/Produkt/Lead/Auftrag/Beleg/Nachricht/Ticket). **Aber:** Die Spalte `res_currency.symbol`, die de_DE-shortdesc-Translations **und einzelne de_DE-Feldlabel-/Auswahlwert-Übersetzungen** (F26) waren nicht Teil der Reparatur und enthalten weiterhin CP850-Muster. **Nichts eigenmächtig ändern** (Encoding gilt als „abgeschlossen“, jede Änderung nur mit Freigabe).

---

## 3. C — Währung

**Istzustand (read-only):**
- Unternehmenswährung: **EUR (id 126)** — `res_company` IT-Kommunal GmbH, Land **AT** (id 12). ✅
- Österreich-Lokalisierung installiert: `l10n_at` 18.0.3.2.1 (+ `l10n_din5008*`). ✅
- Alle 7 Journale: `currency_id = NULL` (= Unternehmenswährung EUR). ✅
- 18 Belege EUR, aber **4 Belege USD** (ids 17, 20, 21, 19). ⚠️
- **USD (id 1) ist aktiv** (`active=true`) und trägt das Symbol `$` — Relikt aus der initialen DB-Erstellung (Odoo-Basiswährung vor l10n_at-Installation). ⚠️
- **14 Verkaufsaufträge in USD** (currency_id=1), alle über Preisliste 1 „Standard-Preisliste“ (USD), erstellt 01.07.–24.07.2026 (Testdaten-Zeitraum), inkl. `A-1900011`. ⚠️
- **Beide Preislisten sind inaktiv:** id 1 „Standard-Preisliste“ (USD, 0 Items), id 34 „Preisliste 2026 + Valorisierung“ (EUR, 2 Items). ⚠️
- **EUR-Symbol in `res_currency.symbol` ist Mojibake `Ôé¼`** (siehe Abschnitt 2). Sichtbare Auswirkung in UI/PDF-Darstellung erwartet (Web-Client und QWeb-Formatierung nutzen dieses Feld) — im Abnahmetest bestätigen. ⚠️

| Bereich | Funktion/Feld | Odoo-18-Istzustand | Status | Fehler/Abweichung | notwendige Anpassung | getestet |
|---|---|---|---|---|---|---|
| Unternehmenswährung | res_company | EUR (126), Land AT | OK | — | — | ja (DB) |
| Standardwährung | res_currency aktive Währungen | EUR aktiv ✅, **USD aktiv ⚠️** | **ANPASSUNG NÖTIG** | USD aktiv ohne fachliche Nutzung (Relikt) | prüfen, ob USD deaktiviert werden soll (nach Freigabe) | ja (DB) |
| Währungssymbol | res_currency.symbol (EUR) | `Ôé¼` statt `€` | **FEHLER** | CP850-Mojibake | Symbol korrigieren (nach Freigabe) | ja (DB), UI offen |
| Preislisten | product_pricelist | 2 Preislisten, **beide inaktiv** | **ANPASSUNG NÖTIG** | keine aktive Preisliste; „Standard-Preisliste“ ist USD | aktivieren/neu anlegen (EUR), nach Freigabe | ja (DB) |
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
| Zeitzone | **nur 2 von 18 Benutzern** mit `Europe/Vienna` (uid 2, 8); restliche leer → UTC-Fallback | **ANPASSUNG NÖTIG** | Zeitzone fehlt bei 16 Benutzern | Zeitzone Europe/Vienna für aktive Benutzer setzen (nach Freigabe) | ja (DB) |
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
| itk_subscription | 5 Abos, 6 Positionen, 3 Vorlagen | OFFEN | — | — | nein |
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

## 6. Odoo 11 → Odoo 18 Mapping (späterer Abschnitt — VORLÄUFIG OFFEN)

> **Grund:** Keine laufende Odoo-11-Referenz vorhanden (O11-Test-VM am 31.08.2026 dekommissioniert). Ein Feld-für-Feld-Vergleich wäre ohne verlässliche Referenz Spekulation und wird **nicht** durchgeführt.
> **Verfügbare Referenzoptionen (sobald vorhanden):** gesicherte alte O11-Testumgebung (IPAX), produktives Odoo 11 mit ausschließlich lesendem Zugriff, Exporte, vorhandene Dokumentation (z. B. `Migration_Referenzen/`, `DATA_MIGRATION_CHECKLIST.md`).

**Erfassungsschema für das spätere Mapping:**

| Odoo-11-Modell/Feld | Odoo-18-Zielfeld | Datentyp | Pflichtfeld | Auswahlwerte | Relation | Transformations-/Migrationsregel |
|---|---|---|---|---|---|---|
| (OFFEN) | (OFFEN) | (OFFEN) | (OFFEN) | (OFFEN) | (OFFEN) | (OFFEN) |

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
| F1 | C/Währung | EUR-Symbol in `res_currency.symbol` = `Ôé¼` statt `€` (CP850-Mojibake, Bytes `\303\224\303\251\302\274`); weitere Symbole betroffen (GBP `┬ú`, CZK `K─ì`, PLN `z┼é`, …) | VM-DB res_currency id 126 | FEHLER |
| F2 | C/Währung | USD (id 1) aktiv — Relikt aus initialer DB-Erstellung (Basiswährung vor l10n_at) | res_currency id 1 | ANPASSUNG NÖTIG |
| F3 | C/Währung | 14 Verkaufsaufträge (inkl. A-1900011) in USD über inaktive USD-Preisliste 1 „Standard-Preisliste“ (Testdaten 01.–24.07.2026) | sale_order currency_id=1, pricelist_id=1 | FEHLER |
| F4 | C/Währung | 4 Rechnungen (account_move ids 17,20,21,19) in USD | account_move currency_id=1 | FEHLER |
| F5 | C/Währung | Beide Preislisten inaktiv (id 1 USD, id 34 EUR mit 2 Items); keine aktive Preisliste | product_pricelist | ANPASSUNG NÖTIG |
| F6 | A/Sprache | 12 von 15 itk-Modulen + alle 6 OCA-Module ohne de_DE-shortdesc → englische/technische Namen in der Apps-Liste | ir_module_module.shortdesc | ANPASSUNG NÖTIG |
| F7 | A/Sprache | `account_payment` de_DE-shortdesc „Zahlung ÔÇô Konto“ (CP850-Mojibake) — einziges betroffenes **installiertes** Modul; 14 weitere betroffene Module nicht installiert | ir_module_module.shortdesc | FEHLER |
| F8 | D/Basiseinstellungen | Zeitzone nur bei 2 von 18 Benutzern gesetzt (Europe/Vienna); 16 Benutzer ohne tz (UTC-Fallback) | res_users/res_partner | ANPASSUNG NÖTIG |
| F9 | A/Sprache | Nur de_DE aktiv; en_US vorhanden aber inaktiv; 91 res_lang-Zeilen mit `active IS NULL` (Altlast) | res_lang | Hinweis |
| F10 | Inventar | `web_group_expand` installiert, obwohl als „geparkt“ dokumentiert (Doku-Inkonsistenz; Code funktioniert) | ir_module_module vs. README | Hinweis |
| F11 | Inventar | `itk_projectcategory`: DB 18.0.0.1 vs. Repo 18.0.1.0.0 (Upgrade offen, bekannt seit Session 74) | ir_module_module vs. __manifest__ | OFFEN |
| F12 | Inventar | Ausstehende Einzel-Upgrades (tree→list): itk_reports, itk_sale_management, itk_translation (+ VM-Angleichung hr_holidays_public) — je Freigabe | Session 78 | OFFEN |
| F13 | D/Anhänge | ir.attachment 1249 → 1260, mail_message 455 → 456 (Asset-Regeneration nach HTTPS/proxy_mode-Umstellung; erwartbar, kein Fehler) | Kontrollzahlen | Hinweis |
| F14 | A/Sprache (itk_translation) | ITK-Menü-Baum sichtbar englisch/technisch: Top-Menü „ITK-Menu“ (733); Untermenüs 734–741 „Partner“, „Actual customers“, „All customers“, „Former Customers“, „Target Customers“, „Reseller“, „All Resellers“, „All Magnitudes“; 6 Actions gleichlautend (ir.actions.act_window) | RPC VM (de_DE == en_US) | FEHLER |
| F15 | A/Sprache (itk_crm) | Custom-Felder auf res.partner (+ Delegation res.users) ohne de_DE-Text, sichtbar englisch: `firstname`/`lastname` („First/Last name“, partner_firstname), `status_of_community` „Status of Community“, `population` „Size of Population“, `population_update`, `member_of_city_alliance` „Member of City Alliance“, `asset_partner` „Asset Partner“, `title_put_in_front`/`title_put_in_back` „Title in Front/Back“, `sales_as_final_customer_count` „# of Sales as Final Customer“, `reseller`, `salutation`, `austria_wiki_url`, `community_magnitude` „Magnitude“, `community_magnitude_id` „Community Magnitude“ | RPC VM fields_get/ir.model.fields de == en | FEHLER |
| F16 | A/Sprache (itk_crm, x_-Felder crm.lead) | 4 Custom-Selection-Felder: Labels `x_lead_status` „Lead Status“, `x_Anrede_Lead` „Anrede Lead“, `x_Lead_Quelle` „Lead Quelle“ (nicht einheitlich deutsch); Auswahlwerte deutsch (außer „On-Hold“); `x_Produktinteresse` OK | RPC VM de_DE | ANPASSUNG NÖTIG |
| F17 | A/Sprache (itk_subscription/sale_subscription) | Felder sale.subscription (70 Kandidaten) und sale.subscription.template (38) sichtbar englisch, u. a. Kernfelder `partner_id` „Customer“, `date_start` „Start Date“, `date` „End Date“, `recurring_next_date` „Date of Next Invoice“, `template_id` „Subscription Template“, `create_date` „Created on“; Menüs/Actions des Moduls sind dagegen deutsch (de.po nur teilweise geladen bzw. ohne Feld-Terme) | RPC VM fields_get de == en | FEHLER |
| F18 | A/Sprache (itk_multifactor) | Wizard-Action-Namen englisch („Set Pricelist for Subscriptions“, „Update Multifactor for Subscriptionlines“, „Update Population and Multifactor for Partners“); Felder „To multiply by Factor(per 1000)“ (product), „Multiplication Factor/Thsd“ (res.partner/-users, sale.order.line, sale.subscription.line) | RPC VM de == en | FEHLER |
| F19 | A/Sprache (weitere itk_*) | Englische sichtbare Labels: itk_product „Product-Type“, „To multiply by Factor(thsd)“; itk_sale_management 5 sale.order-Kontaktfelder („Administrative/Technical/Sale Contact“, „Final Customer“, „Product Category“); itk_valorisierung „Valorisation Text“ (account.move/-bank.line); itk_projectcategory „Project Category“ (account.move); itk_saleorder_lines Menü/Action „All Order Lines“/„Order Lines“; itk_helpdesk_category_user „Assigned Users“ (helpdesk.ticket.category); zzgl. Audit-Labels („Created on/by“, „Display Name“, „Last Updated on/by“) auf allen itk-eigenen Modellen | RPC VM de == en | FEHLER |
| F20 | A/Sprache (itk_helpdesk_compat) | Menü + Action „Support Tickets“ (891) englisch; übrige Menüs/Actions/Felder deutsch (Positivbefund) | RPC VM | ANPASSUNG NÖTIG |
| F21 | A/Sprache (helpdesk_mgmt) | Menüs teilweise englisch: „All Tickets“ (746), „Dashboard“ (743), „Settings“ (750, unter Konfiguration), Actions „Helpdesk Ticket“ (3×); Feldlücken englisch: duplicate_*/„Enable duplicate ticket tracking.“, „Commercial Partner“, „Followers (Partners)“, „SMS Delivery error“; Settings-Felder (res.company/res.config.settings) „Auto assign tickets“, „Select category/team in Helpdesk portal“, „Required Category/Team field in Helpdesk portal“, „Move duplicate tickets to this stage“ — de.po im Repo vorhanden (299 Terme), aber unvollständig/nicht vollständig geladen | RPC VM de vs en | FEHLER |
| F22 | A/Sprache (helpdesk_mgmt_sla) | Menüs „SLA“ (776), „SLA Report“ (775); helpdesk.sla- und helpdesk.ticket.sla-Felder überwiegend englisch (Days/Hours, Deadline, Expected Stage, Ignore Stages, Consumed time, Ticket Sla …; 76 moduleigene Felder, Großteil en) — kein de.po im Repo | RPC VM de == en | FEHLER |
| F23 | A/Sprache (helpdesk_mgmt_timesheet/-project) | Menü/Action „Timesheets“ (757); Felder „Allow Timesheet“, „Planned/Remaining/Total Hours“, „Show Timesheet Portal“, „Last Timesheet Activity“ (ticket) sowie „Ticket Count“, „Number of tickets“, „Use Tickets as“, „Helpdesk Ticket Count“ (project/task/milestone), Actions „Helpdesk Tickets“ — kein de.po im Repo | RPC VM de == en | FEHLER |
| F24 | A/Sprache (project_timesheet_time_control) | Menü + Action „Start work“ (756, unter Zeiterfassung); Felder „Start Time“/„End Time“ (date_time/date_time_end), „Show Time Control“, „Previous timer …“ — de.po im Repo vorhanden, aber nicht geladen/unvollständig | RPC VM de == en | FEHLER |
| F25 | A/Sprache + Datenqualität (Statuswerte/Kategorien) | CRM-Stage „On-Hold“, Helpdesk-Stage „on Hold“ (englisch); Helpdesk-Kategorien: deutsch, aber sichtbare Duplikate („Allgemeine Anfrage (Support)“ 5×, „Störung/Fehler melden“ 4×, „Angebot anfordern“ 3×, „allgemeiner Support“ 2×, „Zugangsdaten vergessen“ 2×) + Tippfehler „Anynomisierungsportal“; Aktivitätstypen (12 aktiv) und übrige CRM-Stages deutsch (Positiv) | RPC VM (Datensätze) | Hinweis/ANPASSUNG NÖTIG |
| F26 | B/Encoding (Übersetzungen) | 3 CP850-Artefakte in sichtbaren de_DE-Übersetzungen (nicht Teil der Reparatur vom 13.08.): `account.move.status_in_payment` „Status ÔÇ×In ZahlungÔÇ£“, `account.reconcile.model.line.show_force_tax_included` „ÔÇ×Steuer inklusive erzwingenÔÇ£ anzeigen“, `res.partner.peppol_eas`-Wert `0245` „SK-Steueridentifikationsnummer (DI─î)“ (auch res.users/res.company sichtbar) | RPC VM ir.model.fields/ir.model.fields.selection de_DE | FEHLER |

---

## 9. Grenzen dieser Analyse

- Diese Checkliste basiert auf **read-only**-Auswertungen (SQL über die VM-DB, RPC-Textinventar de_DE/en_US 02.09.2026, Repo-Vergleich, frühere Sessions). **Keine** Browser-Sichtprüfung, keine PDF-Renderings, keine E-Mail-Tests in dieser Phase.
- Das RPC-Inventar (Abschnitt 1, Befunde F14–F26) erfasst, welche Texte das System für einen de_DE-Benutzer bereitstellt (Menüs, Actions, Feldlabels via `fields_get`, Auswahlwerte, Modul-shortdesc, Datensatznamen). Es ersetzt **nicht** die Sichtprüfung im Browser (Anordnung, Kanban-Darstellung, Hilfetexte, Fehlermeldungen zur Laufzeit).
- Die eigentliche Abnahme (Sichtprüfung, Bedienung, Datenqualität) erfolgt **gemeinsam Punkt für Punkt** über die Checkliste — begonnen mit Abschnitt 1 (Sprache): Browser-Durchgang zu den Befunden F14–F26 steht aus.
- Erst nach Abschluss der Abnahme und Entscheidung zur O11-Migration wird das Feldmapping (Abschnitt 6) erstellt und die Datenmigration geplant (`DATA_MIGRATION_CHECKLIST.md` bleibt dafür der operative Plan).
