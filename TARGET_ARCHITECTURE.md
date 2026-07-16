# Odoo-18-Zielarchitektur

> Stand: 15.07.2026 — Modulanalyse abgeschlossen, Zielarchitektur festgelegt.

## Mapping: Odoo 11 → Odoo 18

### Bereits migrierte ITK-Module (in `addons/` installiert)

| Odoo 11 | Odoo 18 | Status |
|---|---|---|
| `itk_subscription` | `itk_subscription` v18.0.1.0.0 | ✅ Installiert |
| `itk_product` | `itk_product` v18.0.1.0.0 | ✅ Installiert |
| `itk_projectcategory` | `itk_projectcategory` v18.0.1.0.0 | ✅ Installiert |
| `itk_sale_management` | `itk_sale_management` v18.0.1.0.0 | ✅ Installiert |
| `itk_valorisierung` | `itk_valorisierung` v18.0.1.0.0 | ✅ Installiert |
| `itk_saleorder_lines` | `itk_saleorder_lines` v18.0.1.0.0 | ✅ Installiert |
| `itk_multifactor` | `itk_multifactor` v18.0.1.0.0 | ✅ Installiert |
| `itk_crm` | `itk_crm` v18.0.1.0.0 | ✅ Installiert |
| `itk_base_setup` | `itk_base_setup` v18.0.1.0.0 | ✅ Installiert |
| `itk_third_party_setup` | `itk_third_party_setup` v18.0.1.0.0 | ✅ Installiert |
| `itk_reports` | `itk_reports` v18.0.1.0.0 | ✅ Installiert |
| `itk_automated_actions` | `itk_automated_actions` v18.0.1.0.0 | ✅ Installiert |
| `itk_translation` | `itk_translation` v18.0.1.0.0 | ✅ Installiert |

### Odoo-18-Standard (bereits integriert, keine Migration nötig)

| Odoo 11 | Odoo 18 | Status |
|---|---|---|
| `account_invoice_line_number` | Odoo-18-Standard | ✅ Integriert |
| `sale_order_line_number` | Odoo-18-Standard | ✅ Integriert |

### Migrierte Drittanbieter-Module

| Odoo 11 | Odoo 18 | Status |
|---|---|---|
| `account_invoice_line_report` | Migriert | ✅ Installiert |
| `partner_firstname` | Migriert | ✅ Installiert |
| `hr_employee_firstname` | Migriert | ✅ Installiert |
| `partner_academic_title` | Migriert | ✅ Installiert |
| `purchase_order_line_number` | Migriert | ✅ Installiert |
| `merge_sale_order` | Migriert | ✅ Installiert |
| `merge_purchase_order` | Migriert | ✅ Installiert |
| `web_no_bubble` | Migriert | ✅ Installiert |
| `web_sheet_full_width` | Migriert | ✅ Installiert |
| `web_environment_ribbon` | Migriert | ✅ Installiert |
| `sale_merge_draft_invoice` | Migriert | ✅ Installiert |
| `website_odoo_debranding` | Migriert | ✅ Installiert |
| `partner_external_map` | Migriert | ✅ Installiert |
| `mass_email_invoice` | Migriert | ✅ Installiert |
| `website_cookie_notice` | Migriert | ✅ Installiert |
| `hr_holidays_public` | Migriert | ✅ Installiert |

### Durch OCA ersetzt

| Odoo 11 | Odoo 18 | Status |
|---|---|---|
| `mass_editing` | `server_action_mass_edit` (OCA/server-ux) | ✅ Installiert |

### Durch OCA zu ersetzen (noch nicht installiert)

| Odoo 11 | Odoo 18 | Status |
|---|---|---|
| `website_support` | `helpdesk_mgmt` (OCA/helpdesk) | 🔲 Geplant |
| `website_support_analytic_timesheets` | `helpdesk_mgmt_timesheet` (OCA/helpdesk) | 🔲 Geplant |
| `website_support_billing` | Odoo-18-Standard-Projektabrechnung | 🔲 Entfällt |

### Entfällt ersatzlos

| Odoo 11 | Grund | Status |
|---|---|---|
| `itk_contract` | 0 Datensätze, Felder in itk_subscription | ❌ Geparkt |
| `itk_support` | Leeres Modul, Menüs in itk_translation | ❌ Geparkt |
| `bi_crm_claim` | 0 Datensätze, nie genutzt | ❌ Geparkt |
| `itk_data_setup` | Datenimport → CSV-Migration | ❌ Geparkt |
| `itk_initial_abo_import` | Datenimport → CSV-Migration | ❌ Geparkt |
| `itk_initial_data_import` | Datenimport → CSV-Migration | ❌ Geparkt |
| `itk_initial_product_import` | Datenimport → CSV-Migration | ❌ Geparkt |
| `itk_initial_partner_data_import` | Datenimport → CSV-Migration | ❌ Geparkt |
| `itk_initial_partner_nogkz_data_import` | Datenimport → CSV-Migration | ❌ Geparkt |
| `itk_initial_partner_emblem_import` | Datenimport → CSV-Migration | ❌ Geparkt |
| `itk_initial_data_habasis_gkz_strasse` | Datenimport → CSV-Migration | ❌ Geparkt |
| `itk_initial_data_habasis_gszk` | Datenimport → CSV-Migration | ❌ Geparkt |
| `itk_misc` | Kein Modul → Referenzdokumentation | ❌ Geparkt |
| `web_tree_resize_column` | JS inkompatibel (OWL) | ❌ Geparkt |
| `web_group_expand` | JS inkompatibel (OWL) | ❌ Geparkt |

### Noch zu analysieren

| Odoo 11 | Status |
|---|---|
| `hr_holiday_exclude_special_days` | 🔲 Offen |
| `itk_fix_import` | 🔲 Offen |
| `itk_main_company_import` | 🔲 Offen |
| `itk_update_population` | 🔲 Offen |
| `mail_activity_board` | 🔲 Offen |
| `web_responsive` | 🔲 Offen |

---

## Migrationsphasenplan

### ✅ Abgeschlossen

| Phase | Inhalt |
|---|---|
| **Phase 1** — ITK-Kernmodule | `itk_subscription`, `itk_product`, `itk_crm`, `itk_sale_management`, `itk_valorisierung`, `itk_projectcategory`, `itk_multifactor`, `itk_saleorder_lines` |
| **Phase 2** — ITK-Ergänzungen | `itk_base_setup`, `itk_third_party_setup`, `itk_reports`, `itk_automated_actions`, `itk_translation` |
| **Phase 3** — Drittanbieter | `partner_firstname`, `hr_employee_firstname`, `partner_academic_title`, `merge_sale_order`, `merge_purchase_order`, `account_invoice_line_report`, uvm. |
| **Phase 4** — Web/UI | `web_no_bubble`, `web_sheet_full_width`, `web_environment_ribbon`, `website_cookie_notice`, `website_odoo_debranding` |
| **Phase 5** — OCA-Ersatz | `server_action_mass_edit` (ersetzt `mass_editing`) |

### 🔲 Geplant

| Phase | Inhalt | Odoo-18-Modul |
|---|---|---|
| **Phase 6** — OCA Helpdesk | `helpdesk_mgmt` installieren | OCA/helpdesk 18.0 |
| **Phase 7** — OCA SLA | `helpdesk_mgmt_sla` installieren | OCA/helpdesk 18.0 |
| **Phase 8** — OCA Timesheet | `helpdesk_mgmt_timesheet` installieren | OCA/helpdesk 18.0 |
| **Phase 9** — Restmodule | `hr_holiday_exclude_special_days`, `itk_update_population`, `mail_activity_board`, `web_responsive` | Analyse → Entscheidung |
| **Phase 10** — Datenimport | `itk_fix_import`, `itk_main_company_import` | Einmalige Ausführung |
| **Phase 11** — Nummernkreise | Sequenzen einrichten (R-%(y)s, A-%(y)s, E-%(y)s, NV-, ER-%(y)s) | Odoo-Konfiguration |
| **Phase 12** — Gesamtdatenmigration | Stammdaten → Geschäftsdaten (siehe `DATA_MIGRATION_CHECKLIST.md`) | CSV-Export/Import |

---

## Entscheidung: Support-Module

**Ticketmigration entfällt.** Der Odoo-18-Helpdesk startet leer.
Die 1.110 Tickets aus Odoo 11 werden nicht migriert. Das alte System bleibt
als Referenz in Odoo 11 lesbar, das neue System beginnt frisch.

**OCA-Module (zu installieren):**
- `helpdesk_mgmt` — Kern-Ticketsystem
- `helpdesk_mgmt_sla` — SLA-Management
- `helpdesk_mgmt_timesheet` — Zeiterfassung auf Tickets

**Nicht installieren:**
- `website_support_billing` → Odoo-18-Standard-Projektabrechnung
- `helpdesk_mgmt_rating` → Bei Bedarf später
