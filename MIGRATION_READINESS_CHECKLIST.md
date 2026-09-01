# MIGRATION-READINESS-CHECKLIST — Odoo 18 Abnahme vor der Odoo-11-Datenmigration

> **Zweck:** Fachliche und technische Abnahme der Odoo-18-Testumgebung (ITK), **bevor** produktive Odoo-11-Daten migriert werden.
> **Referenzumgebung:** https://k001959vsx.ipax.at — DB `odoo18_test` (IPAX-Test-VM, Ubuntu 26.04, Docker odoo:18 + postgres:16)
> **Stand:** 01.09.2026, nach Session 78 (Git main = `08e96d2`, lokal/GitHub/VM synchron)
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

**Istzustand (read-only):**
- `res_lang`: 92 Einträge, **nur `de_DE` aktiv** (en_US vorhanden, aber inaktiv). → UI-Standardsprache ist Deutsch.
- Alle 14 aktiven Benutzer: `lang = de_DE`. System-Benutzer ebenfalls de_DE.
- Datums-/Zahlenformat de_DE: `%d.%m.%Y`, `%H:%M:%S`, Dezimaltrennzeichen `,`, Tausendertrennzeichen `.` (korrekt für Österreich).
- `web.base.url = https://k001959vsx.ipax.at` (korrekt).

| Bereich | Funktion/Feld | Odoo-18-Istzustand | Status | Fehler/Abweichung | notwendige Anpassung | getestet |
|---|---|---|---|---|---|---|
| Menüs | alle sichtbaren Menüs (CRM, Kontakte, Verkauf, Helpdesk, ITK-Menü) | Menüs vorhanden (nicht einzeln geprüft) | OFFEN | — | — | nein |
| Feldbezeichnungen | Standard-Views + itk_crm-Custom-Felder | nicht einzeln geprüft | OFFEN | — | — | nein |
| Buttons/Statuswerte | Stages, Buttons, Aktivitäten-Wizard | nicht einzeln geprüft | OFFEN | — | — | nein |
| Auswahlwerte | Selection-Felder (itk_*, CRM, Helpdesk-Prioritäten) | nicht einzeln geprüft | OFFEN | — | — | nein |
| Eigene itk_*-Felder | alle Custom-Felder (GKZ, Status, Community, Magnitude, Subkategorie-Felder …) | Felder/Tabellen vorhanden | OFFEN | — | — | nein |
| Benutzerhinweise/Warnungen | Wizard-Texte, Fehlermeldungen | nicht einzeln geprüft | OFFEN | — | — | nein |
| Kanban-/Listen-/Formularansichten | CRM-Kanban, Aktivitäten-Kanban, Helpdesk-Views | teilweise geprüft (frühere Sessions) | OFFEN | — | — | nein |
| **Modulbezeichnungen (Apps-Liste)** | shortdesc der installierten Module | 12 von 15 itk-Modulen + alle 6 OCA-Module nur mit technischem/englischem Namen (kein de_DE-Label) | **ANPASSUNG NÖTIG** | Sichtbare Modulnamen in der deutschen Apps-Liste sind englisch/technisch, z. B. „itk_crm“, „Helpdesk Management“, „Mass Editing“ | de_DE-shortdesc für die fachlich sichtbaren Module ergänzen (nach Freigabe) | nein |
| **Modulbezeichnung `account_payment`** | shortdesc de_DE | „Zahlung ÔÇô Konto“ (CP850-Mojibake, s. B) | **FEHLER** | En-Dash „–“ als „ÔÇô“ fehlkodiert | Translation korrigieren (nach Freigabe) | nein |

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

**Gesamtbild Encoding:** Die CP850-Reparatur vom 13.08.2026 ist in den fachlichen Tabellen bestätigt (0 ├-Zeilen in Partner/Produkt/Lead/Auftrag/Beleg/Nachricht/Ticket). **Aber:** Die Spalte `res_currency.symbol` und die de_DE-shortdesc-Translations waren nicht Teil der Reparatur und enthalten weiterhin CP850-Muster. **Nichts eigenmächtig ändern** (Encoding gilt als „abgeschlossen“, jede Änderung nur mit Freigabe).

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

---

## 9. Grenzen dieser Analyse

- Diese Checkliste basiert auf **read-only**-Auswertungen (SQL über VM-DB, Repo-Vergleich, frühere Sessions). **Keine** UI-Tests, keine PDF-Renderings, keine E-Mail-Tests in dieser Phase.
- Die eigentliche Abnahme (Sichtprüfung, Bedienung, Datenqualität) erfolgt **gemeinsam Punkt für Punkt** über die Checkliste, beginnend mit Abschnitt 1 (Sprache).
- Erst nach Abschluss der Abnahme und Entscheidung zur O11-Migration wird das Feldmapping (Abschnitt 6) erstellt und die Datenmigration geplant (`DATA_MIGRATION_CHECKLIST.md` bleibt dafür der operative Plan).
