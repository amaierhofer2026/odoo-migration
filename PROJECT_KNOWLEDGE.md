# Odoo Migration – Projekt-Knowledge-Base

## Über diese Datei (PROJECT_KNOWLEDGE.md)
Diese Datei ist das **zentrale Gedächtnis des Projekts**. Sie dokumentiert:
- Welche Schritte bereits durchgeführt wurden
- Welche Entscheidungen getroffen wurden
- Welche Fehler aufgetreten sind und wie sie gelöst wurden
- Wie der aktuelle Stand ist
- **Wie man frühere Versionen wiederherstellen kann**

Sie ist für Menschen lesbar (kein reiner Code), dient als "Long-Term Memory" für den KI-Assistenten und ersetzt das README.md für interne Projekt-Dokumentation.

---

## README.md – Wozu?
Die **README.md** ist die **Visitenkarte des Repos** für andere Menschen (oder dich selbst in 6 Monaten). Sie zeigt auf GitHub automatisch als Startseite an. Sie enthält nur:
- Projektname & Kurzbeschreibung
- Ordnerstruktur (Überblick)
- Lizenz

**PROJECT_KNOWLEDGE.md** ist dagegen der **detaillierte Projekt-Tagebuch** – alle technischen Details, Änderungen, Fehlerbehebungen und Entscheidungen.

---

## Repository
| Eigenschaft | Wert |
|---|---|
| Name | `odoo-migration` |
| URL | https://github.com/amaierhofer2026/odoo-migration |
| Ziel | Exakter Spiegel von `C:\Odoo-Test` |
| Haupt-Branch | `main` |

---

## Aktuelle Struktur

```
odoo-migration/
├── addons/                  → Odoo-Addons
│   ├── account_invoice_line_number/
│   ├── itk_product/
│   ├── itk_projectcategory/
│   ├── itk_sale_management/
│   ├── itk_subscription/    ✅ Migriert nach Odoo 18
│   ├── itk_valorisierung/
│   └── sale_order_line_number/
├── config/                  → Odoo-Konfiguration (leer)
├── odoo11 module/           → Odoo-11-Originalquellen (nur die, die NICHT in addons/ sind)
├── postgres/                → PostgreSQL-Datenbank
├── docker-compose.yml       → Docker-Stack (Odoo 18 + PostgreSQL 16)
├── .gitignore               → Ignoriert: __pycache__, *.pyc, *.mo, .idea/, *.swp
├── PROJECT_KNOWLEDGE.md     → Dieses Dokument (Projekt-Tagebuch)
└── README.md                → Kurz-Übersicht für GitHub
```

---

## Projekt-Chronik (Session-Log)

### Session 1: itk_subscription – Migration Odoo 11 → 18

**Datum:** 25.06.2026  
**Dauer:** Mehrere Stunden, iterativ mit Fehlerkorrektur  
**Modul:** `itk_subscription` (ITK Abo-Management)

#### Ausgangslage
- Odoo-11-Modul `itk_subscription` liegt in `C:\Odoo-Test\addons\itk_subscription\`
- Ziel: Installation in Odoo 18 (Docker-Container `odoo:18`)
- Testsystem: http://localhost:8069

#### Schritt-für-Schritt-Änderungen

**1. Manifest (`__manifest__.py`)**
- Version von `1.1` auf `18.0.1.0.0`
- `# -*- coding: utf-8 -*-` entfernt (Python 3 Default)
- `depends`: `sale_management` → `sale`, + `analytic` hinzugefügt
- `sale_subscription_wizard_views.xml` reaktiviert (war auskommentiert)
- `license`: `LGPL-3` hinzugefügt
- Assets: Aus XML in `'assets': {}`-Key im Manifest verschoben

**2. Python-Modelle (alle `.py`-Dateien)**
- Alle `# -*- coding: utf-8 -*-` entfernt
- `size=` auf Integer-Feldern entfernt (seit Odoo 13 deprecated)
- `_prepare_invoice_data()`: Komplett überarbeitet für Odoo-18-API
  - `'type': 'out_invoice'` → `'invoice_date'`
  - `'account_id'` entfernt, stattdessen `'partner_id'`
  - `'origin'` → `'invoice_origin'`
  - `'payment_term_id'` → `'invoice_payment_term_id'`
  - `'invoice_line_ids'` direkt in `_prepare_invoice_data()` integriert
- `_prepare_invoice_line()`: `account_analytic_id` → `analytic_distribution`
- `_do_payment()`: `acquirer_id` → `provider_id`, `s2s_do_transaction()` → `_send_payment_request()`
- `reconcile_pending_transaction()`: `action_invoice_open()` → `action_post()`
- Mail-Referenzen von `sale_subscription` auf `itk_subscription` korrigiert

**3. Controller/Portal (`controllers/portal.py`)**
- `payment.acquirer` → `payment.provider`
- `token_implemented` → `allow_tokenization`
- `tx.form_feedback()` → `tx._handle_notification_data()`
- Template-Variablen: `acquirers` → `providers`

**4. View-XML-Dateien**
- `<tree>` → `<list>` (Odoo 18: der View-Typ heißt `list`, nicht `tree`)
- `<record>`-Definitionen: weiterhin `<tree>` → `<list>` für Haupt-Views
- Inline-Edit-Listen innerhalb von `<field>`: `<tree>` → `<list>`
- `active_id` → `id` in Button-Kontexten (Odoo 18 validiert Felder strikter)
- `attrs="{'invisible': ...}"` → `invisible="..."`
- `analytic.model_account_analytic_account` → `account.model_account_analytic_account`

**5. Security**
- `ir.model.access.csv`: Alle `model_id:`-Referenzen vollqualifiziert (`itk_subscription.model_...`)
- `sale_subscription_security.xml`: `analytic.model_account_analytic_account` korrigiert

**6. Daten-Dateien**
- `numbercall` und `doall` aus Cron-Jobs entfernt (Odoo 18 `ir.cron`)
- `report_template` und `report_name` aus Mail-Template entfernt (Odoo 18 `mail.template`)

**7. Static/LESS**
- LESS-Mixins (`.o-flex-display()`, `.o-flex()`, etc.) durch reines CSS ersetzt

**8. Auskommentierte/nicht-kritische Views (für später)**
- `portal_my_home_menu_subscription` – XPath `o_portal_submenu` nicht mehr vorhanden
- `portal_my_home_subscription` – XPath `o_portal_docs` nicht mehr vorhanden
- `payment_views.xml` – `payment.transaction_form` XML-ID nicht gefunden
- `res_config_settings_views.xml` – XPath `//div[hasclass('settings')]` nicht mehr vorhanden
- `sale_order_views.xml` – Tiefer XPath `//field[@name='order_line']/form/group/group/...` entfernt

#### Fehler & Lösungen (chronologisch)
| # | Fehler | Ursache | Lösung |
|---|---|---|---|
| 1 | `Ungültiger Ansichtstyp: 'tree'` | `<tree>` in Odoo 18 nicht mehr gültig | Alle `<tree>` durch `<list>` ersetzen |
| 2 | `Unstimmigkeit bei Zugriffsrechten: active_id` | `active_id` kein Feld auf dem Model | `active_id` → `id` |
| 3 | `External ID not found: web.assets_backend` | Assets-Template mit `inherit_id` | Assets in Manifest verschieben |
| 4 | `Element "//ol[hasclass('o_portal_submenu')]" nicht lokalisiert` | Portal-Layout in Odoo 18 geändert | Portal-Templates auskommentiert |
| 5 | `Element "//div[hasclass('settings')]" nicht lokalisiert` | Settings-Layout in Odoo 18 geändert | Settings-View auskommentiert |
| 6 | `External ID not found: payment.transaction_form` | Payment-XML-ID in Odoo 18 geändert | Payment-View auskommentiert |
| 7 | `attrs wird nicht mehr verwendet` | `attrs=` ab Odoo 17 deprecated | `attrs=` → `invisible=` |
| 8 | `Invalid field 'numbercall' on 'ir.cron'` | `numbercall`/`doall` in Odoo 18 entfernt | Beide Felder aus Cron-Jobs entfernt |
| 9 | `Invalid field 'report_template' on 'mail.template'` | `report_template` in Odoo 18 entfernt | Aus Mail-Template entfernt |
| 10 | `Element "//field[@name='order_line']/form/...` | Order-Line-Form-Struktur geändert | XPath entfernt |

---

### Session 2: Repository-Struktur aufbauen

**Datum:** 29.06.2026

#### Schritte
1. Neues GitHub-Repo `odoo-migration` erstellt (API)
2. Initial-Commit mit `itk_subscription` (migrierte Version)
3. `.gitignore` hinzugefügt (__pycache__, *.pyc, *.mo, .idea/)
4. Odoo-11-Quellen aus `C:\Odoo-Test\odoo11 module\` ins Repo kopiert
5. `docker-compose.yml` hinzugefügt
6. `config/` und `postgres/` hinzugefügt
7. Doppelte Module aus `odoo11 module/` gelöscht (existieren bereits in `addons/`)

#### Aktueller Stand
- ✅ `itk_subscription` installiert & lauffähig in Odoo 18
- ✅ Repo spiegelt 1:1 die `C:\Odoo-Test`-Struktur
- 🔄 Restliche Module in `addons/` warten auf Migration
- 🔄 Auskommentierte Views müssen noch mit korrekten Odoo-18-XPath repariert werden

---

## Wie man frühere Versionen wiederherstellt

Das Git-Repository speichert **jeden Commit** – du kannst jederzeit zu einem früheren Stand zurück:

```bash
# Alle Commits anzeigen
git log --oneline

# Beispiel-Ausgabe:
# 4dfa9d4 Remove duplicate modules from odoo11 module/
# 937fb0b Mirror exact C:\Odoo-Test structure
# d56964b Restructure repo to mirror C:\Odoo-Test exactly
# c4138d9 Add all 57 Odoo 11 source modules to odoo11-src/
# b05c4e1 Add all Odoo 11 source modules to odoo11-src/
# f675f2d Add .gitignore, remove pycache and compiled files
# 36f416e Initial commit: itk_subscription migrated to Odoo 18

# Temporär zu einem früheren Stand wechseln (z. B. vor dem Löschen der Duplikate):
git checkout 937fb0b

# Oder einen neuen Branch von einem früheren Commit erstellen:
git checkout -b vor-dem-loeschen 937fb0b

# Dauerhaft zurücksetzen (VORSICHT: nur wenn du sicher bist!):
git reset --hard 937fb0b
git push --force
```

---

## Zugänge
| Dienst | URL | Details |
|---|---|---|
| Odoo 18 | http://localhost:8069 | Docker-Container `odoo18` |
| PostgreSQL | localhost:5432 | Container `odoo18-db`, User `odoo`, Passwort `odoo` |
| Docker-Stack | `C:\Odoo-Test\` | `docker compose up -d` |
| Addons-Pfad (Host) | `C:\Odoo-Test\addons\` | → Container `/mnt/extra-addons/` |
| GitHub | https://github.com/amaierhofer2026/odoo-migration | |

### Session 3: Auskommentierte Views reparieren (Settings, Payment, Portal)

**Datum:** 01.07.2026

#### Ausgangslage
- itk_subscription läuft in Odoo 18, aber 3 View-Dateien waren deaktiviert:
  - `res_config_settings_views.xml` - komplett leer (Settings-Layout Odoo 18 geändert)
  - `payment_views.xml` - komplett leer (payment.transaction_form XML-ID nicht gefunden)
  - `subscription_portal_templates.xml` - Portal-Menü-Einträge auskommentiert

#### Fixes

**1. payment_views.xml**
- Ursprünglicher Inhalt: `invoice_id` Feld nach `reference` in `payment.transaction` Form
- Problem: XML-ID `payment.transaction_form` existiert nicht in Odoo 18
- Lösung: Korrekte XML-ID ist `payment.payment_transaction_form` (Odoo 18 fügt Präfix hinzu)
- View komplett wiederhergestellt

**2. res_config_settings_views.xml**
- Ursprünglicher Inhalt: Settings-Block mit Dashboard- und Deferred-Revenue-Toggles
- Problem: `//div[hasclass('settings')]` existiert nicht mehr in Odoo 18
- Lösung: Odoo 18 verwendet `<app>`/`<block>`/`<setting>` Struktur.
  - inherit_id von `account.res_config_settings_view_form` → `base.res_config_settings_view_form`
  - Neuer `<app data-string="Subscriptions">` Block mit `<setting>` Elementen

**3. subscription_portal_templates.xml**
- Portal-Menü-Einträge waren auskommentiert
- Problem 1: XPath `//ol[hasclass('o_portal_submenu')]` in `portal.portal_layout` nicht auflösbar
  → `portal_breadcrumbs` ist in Odoo 18 ein separates Template
- Lösung 1: inherit_id von `portal.portal_layout` → `portal.portal_breadcrumbs`
- Problem 2: `//ul[hasclass('o_portal_docs')]` in Odoo 18 → `<div>` statt `<ul>`
- Lösung 2: Odoo-18-Portal-Muster mit `portal.portal_docs_entry` verwendet
  - Kategorien über `t-set` Variablen aktivieren (`portal_client_category_enable`)
  - Subscription-Karte in `#portal_client_category` einfügen

#### Ergebnis
- ✅ Modul-Upgrade erfolgreich (button_immediate_upgrade)
- ✅ itk_subscription v18.0.1.0.0 → installed
- ✅ Alle 3 Views aktiv und fehlerfrei
- ✅ Keine Parse-Fehler beim Modul-Upgrade

#### Technische Notizen
- Odoo 18 Settings: `base.res_config_settings_view_form` mit `<app>`/`<block>`/`<setting>` Struktur
- Odoo 18 Portal: `portal.portal_breadcrumbs` enthält das Breadcrumb-OL (nicht `portal.portal_layout`)
- Odoo 18 Payment: XML-IDs verwenden `payment.payment_transaction_form` (nicht `payment.transaction_form`)
- Odoo 18 Portal Home: `portal.portal_docs_entry` Template mit `#portal_client_category` / `#portal_alert_category`
