# Odoo Migration – Projekt-Knowledge-Base

## Repository
**Name:** Odoo Migration  
**URL:** https://github.com/amaierhofer2026/odoo-migration  
**Ziel:** Spiegel von `C:\Odoo-Test` – alle Odoo-Module & Docker-Konfiguration zentralisiert.

## Struktur (identisch zu C:\Odoo-Test)

```
odoo-migration/
├── addons/              → Odoo-18-Addons (als Docker-Volume eingebunden)
│   └── itk_subscription/
├── config/              → Odoo-Konfiguration
├── odoo11 module/       → Odoo-11-Originalquellen (57 Module)
├── docker-compose.yml   → Docker-Stack (Odoo 18 + PostgreSQL 16)
├── PROJECT_KNOWLEDGE.md → Dieses Dokument
└── README.md
```

**Hinweis:** `postgres/` (DB-Daten) und `*.zip`-Archive bleiben außerhalb des Git-Repositorys.

## Module

### addons/ – Migriert nach Odoo 18

| Modul | Beschreibung | Status |
|---|---|---|
| `itk_subscription` | ITK Abo-Management (wiederkehrende Rechnungen) | ✅ Installiert in Odoo 18 |

### odoo11 module/ – Odoo-11-Originale (Migration ausstehend)

**ITK-Kernmodule:**
`itk_base_setup`, `itk_contract`, `itk_crm`, `itk_misc`, `itk_multifactor`, `itk_product`, `itk_projectcategory`, `itk_reports`, `itk_sale_management`, `itk_saleorder_lines`, `itk_subscription`, `itk_support`, `itk_third_party_setup`, `itk_translation`, `itk_valorisierung`

**Import-Module:**
`itk_automated_actions`, `itk_data_setup`, `itk_fix_import`, `itk_initial_abo_import`, `itk_initial_data_habasis_gkz_strasse_import`, `itk_initial_data_habasis_gszk_import`, `itk_initial_data_import`, `itk_initial_partner_data_import`, `itk_initial_partner_emblem_import`, `itk_initial_partner_nogkz_data_import`, `itk_initial_product_import`, `itk_main_company_import`, `itk_update_population`

**Odoo-Erweiterungen (OCA/Community):**
`account_invoice_line_number`, `account_invoice_line_report`, `bi_crm_claim`, `hr_employee_firstname`, `hr_holiday_exclude_special_days`, `hr_holidays_public`, `mail_activity_board`, `mass_editing`, `mass_email_invoice`, `merge_purchase_order`, `merge_sale_order`, `partner_academic_title`, `partner_external_map`, `partner_firstname`, `purchase_order_line_number`, `sale_merge_draft_invoice`, `sale_order_line_number`, `web_environment_ribbon`, `web_group_expand`, `web_no_bubble`, `web_responsive`, `web_sheet_full_width`, `web_tree_resize_column`, `website_cookie_notice`, `website_odoo_debranding`, `website_support`, `website_support_analytic_timesheets`, `website_support_billing`

## itk_subscription – Migrationsdetails

| Eigenschaft | Wert |
|---|---|
| Technischer Name | `itk_subscription` |
| Odoo Version | 18.0 |
| Abhängigkeiten | `sale`, `portal`, `account`, `analytic` |

### Kernfunktionen
- Abos mit wiederkehrenden Rechnungen
- Kündigungsfristen und Mindestvertragslaufzeit
- Abo-Vorlagen
- Portal-Zugriff für Kunden
- Abos aus Verkaufsaufträgen
- Automatische Rechnungen per Cron
- Automatische Zahlungsabwicklung

### Änderungen für Odoo 18
- `# -*- coding: utf-8 -*-` entfernt
- Version, `depends`, Assets im Manifest aktualisiert
- `<list>` statt `<tree>`
- `active_id` → `id` in Button-Kontexten
- `attrs=` → `invisible=`
- `numbercall`, `doall` aus Cron entfernt
- `report_template` aus Mail-Template entfernt
- `payment.acquirer` → `payment.provider`
- `action_invoice_open()` → `action_post()`
- `size=` auf Integer-Feldern entfernt
- LESS-Mixins durch reines CSS

## Zugänge
**Odoo 18:** http://localhost:8069  
**Docker:** `docker compose up -d` in `C:\Odoo-Test\`  
**Addons-Pfad:** `C:\Odoo-Test\addons\` → Container `/mnt/extra-addons/`
