# Odoo Migration – Projekt-Knowledge-Base

## Repository
**Name:** Odoo Migration  
**URL:** https://github.com/amaierhofer2026/odoo-migration  
**Ziel:** Exakter Spiegel von `C:\Odoo-Test`

## Struktur

```
odoo-migration/
├── addons/              → Alle Odoo-Addons
│   ├── account_invoice_line_number/
│   ├── itk_product/
│   ├── itk_projectcategory/
│   ├── itk_sale_management/
│   ├── itk_subscription/   ✅ Migriert nach Odoo 18
│   ├── itk_valorisierung/
│   └── sale_order_line_number/
├── config/              → Odoo-Konfiguration
├── odoo11 module/       → Odoo-11-Originalquellen (57 Module + Archive)
├── postgres/            → PostgreSQL-Datenbank
├── docker-compose.yml   → Docker-Stack (Odoo 18 + PostgreSQL 16)
└── README.md
```

## itk_subscription – Migrationsdetails

| Eigenschaft | Wert |
|---|---|
| Technischer Name | `itk_subscription` |
| Odoo Version | 18.0 |
| Abhängigkeiten | `sale`, `portal`, `account`, `analytic` |
| Status | ✅ Installiert in Odoo 18 |

### Bekannte Einschränkungen (Odoo 18)
- Portal-Templates (`o_portal_submenu`, `o_portal_docs`) – XPath angepasst
- Settings-View-Inheritance – XPath angepasst
- Payment-View-Inheritance – XML-ID angepasst

### Wichtigste Änderungen für Odoo 18
- `<list>` statt `<tree>`, `attrs=` → `invisible=`, `active_id` → `id`
- `numbercall`, `doall` aus Cron entfernt, `report_template` aus Mail-Template
- `payment.acquirer` → `payment.provider`, `action_invoice_open()` → `action_post()`
- `size=` auf Integer-Feldern entfernt, LESS-Mixins durch reines CSS

## Zugänge
**Odoo 18:** http://localhost:8069  
**Docker:** `docker compose up -d` in `C:\Odoo-Test\`  
**PostgreSQL:** Container `odoo18-db`, User `odoo`, Passwort `odoo`
