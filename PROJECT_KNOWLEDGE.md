# Odoo Migration – Projekt-Knowledge-Base

## Repository
**Name:** Odoo Migration  
**URL:** https://github.com/amaierhofer2026/odoo-migration  
**Ziel:** Konsolidierung aller Odoo-Module aus verschiedenen Quell-Repos in einem einzigen Migrations-Repository.

## Module

### addons/ – Migriert nach Odoo 18

| Modul | Beschreibung | Status |
|---|---|---|
| `itk_subscription` | ITK Abo-Management (wiederkehrende Rechnungen) | ✅ Installiert in Odoo 18 |

### odoo11-src/ – Originale Odoo-11-Quellen (Migration ausstehend)

| Modul | Beschreibung | Status |
|---|---|---|
| `account_invoice_line_number` | Rechnungszeilen-Nummerierung | ❌ |
| `itk_product` | ITK Produkterweiterungen | ❌ |
| `itk_projectcategory` | ITK Projektkategorien | ❌ |
| `itk_sale_management` | ITK Verkaufsmanagement | ❌ |
| `itk_subscription` | ITK Abo-Management | ✅ Bereits migriert |
| `itk_valorisierung` | ITK Valorisierung | ❌ |
| `sale_order_line_number` | Auftragszeilen-Nummerierung | ❌ |
| Eigenschaft | Wert |
|---|---|
| Technischer Name | `itk_subscription` |
| Odoo Version | 18.0 |
| Original-Quelle | `odoo11-modules` (Odoo 11) |
| Pfad | `addons/itk_subscription/` |
| Abhängigkeiten | `sale`, `portal`, `account`, `analytic` |

#### Kernfunktionen
- Abos mit wiederkehrenden Rechnungen (täglich/wöchentlich/monatlich/jährlich)
- Kündigungsfristen (Notice Period) und Mindestvertragslaufzeit
- Abo-Vorlagen (subscription templates)
- Portal-Zugriff für Kunden
- Verkaufaufträge erzeugen automatisch Abos
- Automatische Rechnungserstellung per Cron-Job
- Automatische Zahlungsabwicklung (mit Payment-Tokens)

#### Bekannte Einschränkungen (Odoo 18)
- **XPath-Selektoren** in Portal-Templates (`o_portal_submenu`, `o_portal_docs`) und Settings (`//div[hasclass('settings')]`) sind noch nicht an Odoo 18 angepasst – aktuell auskommentiert
- **Payment-View-Inheritance** (`payment.transaction_form`) benötigt korrekten Odoo-18-XML-ID
- **Settings-View-Inheritance** braucht korrekten Odoo-18-XPath für das Settings-Layout
- **Order-Line-Form** im Sale-Order-View nutzt tief verschachteltes XPath, das in Odoo 18 anders ist

#### Änderungen für Odoo 18
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

## Nächste Schritte
- [ ] Portal-Templates mit korrektem Odoo-18-XPath wieder aktivieren
- [ ] Settings-View reparieren
- [ ] Payment-View-Inheritance reparieren
- [ ] Gründliche Funktionstests in Odoo 18
- [ ] Migration weiterer Module aus `odoo11-modules`

## Zugänge
**Odoo 18:** http://localhost:8069  
**Docker-Stack:** `C:\Odoo-Test\docker-compose.yml`  
**Addons-Pfad (Host):** `C:\Odoo-Test\addons\` → Container: `/mnt/extra-addons/`
