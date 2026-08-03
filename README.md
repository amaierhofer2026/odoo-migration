# Odoo Migration – ITK

Migration aller Odoo-Module von **Version 11 nach Version 18** für ITK (IT Kommunal).
1:1-Spiegel des Entwicklungsverzeichnisses `C:\Odoo-Test\`.

## Ziel

- **Alle ~56 Odoo-11-Module** vollständig nach Odoo 18 migrieren
- Jedes Feature, jedes Feld, jede View muss exakt wie in Odoo 11 funktionieren
- Saubere Git-Historie, jeder Schritt nachvollziehbar
- Odoo 18 läuft in Docker (Windows, erreichbar unter `localhost:8069`)

## Migrations-Status

| Modul | Status | Version |
|---|---|---|
| `itk_subscription` (ITK Abo-Management) | ✅ Fertig getestet · 3 Abo-Vorlagen (J/M/Q) · Odoo-18-Fixes: Formular (Chatter/Archiv) + Portal-JS (publicWidget) | 18.0.1.0.0 |
| `account_invoice_line_number` | ✅ In Odoo 18 integriert · Live-Renummerierung im Formular gefixt (⟳ Docker-Neustart) | 18.0.1.0.0 |
| `itk_product` | ✅ Migriert, installiert | 18.0.1.0.0 |
| `itk_projectcategory` | ✅ Migriert, installiert | 18.0.1.0.0 |
| `itk_sale_management` | ✅ Migriert, installiert (Layout-Fix: Angebotsdatum) | 18.0.1.0.0 |
| `itk_valorisierung` | ✅ Migriert, installiert | 18.0.1.0.0 |
| `sale_order_line_number` | ✅ Fertig getestet · Live-Renummerierung im Formular gefixt (⟳ Docker-Neustart) | 18.0.1.0.0 |
| `itk_saleorder_lines` | ✅ Migriert, installiert | 18.0.1.0.0 |
| `itk_multifactor` | ✅ Fertig getestet (act_window + Wizard-ACL gefixt) | 18.0.1.0.0 |
| `itk_crm` | ✅ Migriert, installiert · Lost Reasons (O11-kompatibel), Automated Action, Aktivitäten-Kanban | 18.0.1.0.0 |
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
| Odoo 18 | http://localhost:8069 |
| Odoo 11 (Referenz) | https://93.189.28.204 (DB: ITK_V1_a, Login: anna.maierhofer@it-kommunal.at) |
| PostgreSQL | localhost:5432, User `odoo` |
| Docker-Stack | `docker compose up -d` im Projektverzeichnis |

## Betriebshinweise

**Nach jedem `docker compose down && docker compose up -d`** kann die Login-/Web-Oberfläche
ungestylt erscheinen (kein Odoo-Design, fehlende Login-Felder). Ursache sind veraltete
Asset-Bundles in der DB-Tabelle `ir.attachment` (URLs `/web/assets/*`), die auf tote Datei-Hashes
zeigen. **Fix:** diese Anhänge löschen (`ir.attachment` mit URL `/web/assets/%`) und die Seite neu
laden – Odoo regeneriert die CSS/JS-Bundles automatisch. Details siehe PROJECT_KNOWLEDGE.md
(Session 12 Nachtrag & Session 21).

## Lizenz

LGPL-3
