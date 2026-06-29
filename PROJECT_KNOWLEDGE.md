# Odoo Migration – Projekt-Knowledge-Base

## Repository
**Name:** Odoo Migration  
**URL:** https://github.com/amaierhofer2026/odoo-migration  
**Ziel:** Konsolidierung aller Odoo-Module aus verschiedenen Quell-Repos in einem einzigen Migrations-Repository.

## Struktur

```
odoo-migration/
├── addons/          → Fertig migrierte Odoo-18-Module
└── odoo11-src/      → Originale Odoo-11-Quellen (zur Migration)
```

## Module

### addons/ – Migriert nach Odoo 18

| Modul | Beschreibung | Status |
|---|---|---|
| `itk_subscription` | ITK Abo-Management (wiederkehrende Rechnungen) | ✅ Installiert in Odoo 18 |

### odoo11-src/ – Odoo-11-Originale (Migration ausstehend)

**ITK-Kernmodule:**
| Modul | Beschreibung |
|---|---|
| `itk_base_setup` | ITK Basis-Setup |
| `itk_contract` | ITK Verträge |
| `itk_crm` | ITK CRM-Erweiterungen |
| `itk_misc` | ITK Verschiedenes |
| `itk_multifactor` | ITK Multiplikatorfaktor |
| `itk_product` | ITK Produkterweiterungen |
| `itk_projectcategory` | ITK Projektkategorien |
| `itk_reports` | ITK Berichte |
| `itk_sale_management` | ITK Verkaufsmanagement |
| `itk_saleorder_lines` | ITK Auftragszeilen |
| `itk_subscription` | ITK Abo-Management |
| `itk_support` | ITK Support |
| `itk_third_party_setup` | ITK Drittanbieter-Setup |
| `itk_translation` | ITK Übersetzungen |
| `itk_valorisierung` | ITK Valorisierung |

**Import-Module:**
| Modul | Beschreibung |
|---|---|
| `itk_automated_actions` | Automatisierte Aktionen |
| `itk_data_setup` | Daten-Setup |
| `itk_fix_import` | Fix-Import |
| `itk_initial_abo_import` | Initialer Abo-Import |
| `itk_initial_data_habasis_gkz_strasse_import` | Initialdaten-Import Habasis GKZ Strasse |
| `itk_initial_data_habasis_gszk_import` | Initialdaten-Import Habasis GSZK |
| `itk_initial_data_import` | Initialdaten-Import |
| `itk_initial_partner_data_import` | Initialer Partnerdaten-Import |
| `itk_initial_partner_emblem_import` | Initialer Partner-Emblem-Import |
| `itk_initial_partner_nogkz_data_import` | Partner NOGKZ-Daten-Import |
| `itk_initial_product_import` | Initialer Produkt-Import |
| `itk_main_company_import` | Hauptfirmen-Import |
| `itk_update_population` | Update Population |

**Odoo-Erweiterungen von Drittanbietern:**
| Modul | Beschreibung |
|---|---|
| `account_invoice_line_number` | Rechnungszeilen-Nummerierung |
| `account_invoice_line_report` | Rechnungszeilen-Report |
| `bi_crm_claim` | CRM Claim |
| `hr_employee_firstname` | Mitarbeiter Vorname |
| `hr_holiday_exclude_special_days` | Urlaub: besondere Tage ausschließen |
| `hr_holidays_public` | Gesetzliche Feiertage |
| `mail_activity_board` | Mail Activity Board |
| `mass_editing` | Massenbearbeitung |
| `mass_email_invoice` | Massen-E-Mail Rechnung |
| `merge_purchase_order` | Bestellungen zusammenführen |
| `merge_sale_order` | Verkaufsaufträge zusammenführen |
| `partner_academic_title` | Partner akademischer Titel |
| `partner_external_map` | Partner externe Karte |
| `partner_firstname` | Partner Vorname |
| `purchase_order_line_number` | Bestellzeilen-Nummerierung |
| `sale_merge_draft_invoice` | Entwurfsrechnungen zusammenführen |
| `sale_order_line_number` | Auftragszeilen-Nummerierung |
| `web_environment_ribbon` | Umgebungs-Badge |
| `web_group_expand` | Group Expand |
| `web_no_bubble` | Keine Bubble |
| `web_responsive` | Responsive Backend |
| `web_sheet_full_width` | Vollbreite Sheets |
| `website_cookie_notice` | Cookie-Hinweis |
| `website_odoo_debranding` | Odoo-Branding entfernen |
| `website_support` | Website Support |
| `website_support_analytic_timesheets` | Support-Zeiterfassung |
| `website_support_billing` | Support-Abrechnung |
| `web_tree_resize_column` | Spaltenbreite anpassen |

## itk_subscription – Migrationsdetails

| Eigenschaft | Wert |
|---|---|
| Technischer Name | `itk_subscription` |
| Odoo Version | 18.0 |
| Original-Quelle | `odoo11-src/itk_subscription` (Odoo 11) |
| Ziel | `addons/itk_subscription` |
| Abhängigkeiten | `sale`, `portal`, `account`, `analytic` |

### Kernfunktionen
- Abos mit wiederkehrenden Rechnungen (täglich/wöchentlich/monatlich/jährlich)
- Kündigungsfristen (Notice Period) und Mindestvertragslaufzeit
- Abo-Vorlagen (subscription templates)
- Portal-Zugriff für Kunden
- Verkaufaufträge erzeugen automatisch Abos
- Automatische Rechnungserstellung per Cron-Job
- Automatische Zahlungsabwicklung (mit Payment-Tokens)

### Bekannte Einschränkungen (Odoo 18)
- **XPath-Selektoren** in Portal-Templates (`o_portal_submenu`, `o_portal_docs`) und Settings (`//div[hasclass('settings')]`) sind noch nicht an Odoo 18 angepasst – aktuell auskommentiert
- **Payment-View-Inheritance** (`payment.transaction_form`) benötigt korrekten Odoo-18-XML-ID
- **Settings-View-Inheritance** braucht korrekten Odoo-18-XPath für das Settings-Layout
- **Order-Line-Form** im Sale-Order-View nutzt tief verschachteltes XPath, das in Odoo 18 anders ist

### Änderungen für Odoo 18
- `# -*- coding: utf-8 -*-` aus allen Python-Dateien entfernt
- `__manifest__.py`: Version, `depends`, Assets über `'assets': {}`-Key
- `<list>` statt `<tree>` (Odoo 18 hat View-Typ geändert)
- `active_id` → `id` in Button-Kontexten (Odoo 18 validiert strenger)
- `attrs=` → `invisible=` (ab Odoo 17 deprecated)
- `numbercall`, `doall` aus Cron-Jobs entfernt
- `report_template` aus Mail-Template entfernt (Odoo 18 `mail.template`)
- Payment: `payment.acquirer` → `payment.provider`
- Zahlung: `action_invoice_open()` → `action_post()`
- `size=` auf Integer-Feldern entfernt
- LESS: Odoo-Bootstrap-Mixins durch reines CSS ersetzt

## Zugänge
**Odoo 18:** http://localhost:8069  
**Docker-Stack:** `C:\Odoo-Test\docker-compose.yml`  
**Addons-Pfad (Host):** `C:\Odoo-Test\addons\` → Container: `/mnt/extra-addons/`
