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
| `itk_crm` | ✅ Migriert, installiert | 18.0.1.0.0 |
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

➕ **27 weitere Module** in `odoo11 module/` (Originalquellen) warten auf Migration.

## Struktur

```
odoo-migration/
├── addons/              → 29 Odoo-Addons (27 funktionsfähig + 2 geparkt)
├── config/              → Odoo-Konfiguration
├── odoo11 module/       → 33 Odoo-11-Originalquellen
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
