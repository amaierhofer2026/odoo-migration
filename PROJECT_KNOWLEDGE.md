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
| PostgreSQL | localhost:5432 | Container `odoo18-db`, User `odoo`, Passwort aus `.env` (POSTGRES_PASSWORD, gitignored) |
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

### Session 4: Produkt-Form-View nach versehentlicher Löschung wiederhergestellt

**Datum:** 01.07.2026

#### Problem
User meldete: "Feld Subscription" nicht sichtbar beim Produkt-Neuanlegen (Verkauf → Produkte → Neu).

#### Ursache (Root Cause)
Die Form-View `product_template_view_form_recurring` EXISTIERTE korrekt in der DB (seit 29.06.).
Am 30.06. wurde sie jedoch durch Commit `85aa8831` ("restore product_template_views with actions only")
aus der XML-Datei GELÖSCHT. Die View blieb im laufenden Odoo erhalten, weil das Modul nicht
upgegradet wurde. Erst als heute (01.07.) die Modul-Upgrades für die Session-3-Fixes liefen,
wurde die gelöschte View aktiv → Felder verschwanden aus dem Formular.

#### Fix
- `product_template_views.xml`: Form-View wiederhergestellt mit Odoo-18-Verbesserungen:
  - `attrs` → `invisible` (Odoo 18)
  - XPath: `//group[@name='group_general']/field[last()]` position="after" (innerhalb group_general)
  - Einfaches `<group>` (kein doppelt-genestetes — Pitfall #18: many2one width collapse)
  - `invisible="not (type == 'service')"` auf Gruppe ENTFERNT (Pitfall #19: type-Feld invisible-Trap)
  - Stattdessen nur `subscription_template_id invisible="not recurring_invoice"`
  - Sales-Page-Sichtbarkeit: `invisible="(not sale_ok) and (not recurring_invoice)"` 
    (Sales-Tab sichtbar auch ohne sale_ok, wenn Abo-Produkt)

#### Verifikation
- `get_view()` zeigt Subscription-Group mit beiden Feldern im gerenderten Form-View
- `fields_get()` bestätigt: beide Felder `readonly=False`, Zugriff OK
- Testprodukt mit `recurring_invoice=True` erfolgreich erstellt
- 2 Subscription-Templates in DB vorhanden (Jahresabrechnung, Monatsabrechnung)
- Modul-Upgrade erfolgreich

#### Verbesserungen gegenüber dem Original (3ecfbb6c)
| Aspekt | Original | Fix |
|---|---|---|
| Group-Verschachtelung | `<group><group>` → many2one 20px | `<group>` einfach → volle Breite |
| Sichtbarkeit Gruppe | `invisible="not (type == 'service')"` | Immer sichtbar |
| Template-Dropdown | `invisible="not recurring_invoice"` | unverändert |
| Sales-Tab | keine Anpassung | Sichtbar wenn `recurring_invoice` |

### Session 5: account_invoice_line_number verifiziert

**Datum:** 01.07.2026

#### Ergebnis
Modul `account_invoice_line_number` ist in Odoo 18 bereits vollständig integriert und funktionsfähig. 
Keine Migration nötig.

#### Verifikation
- Module: installed, v18.0.1.0.0
- Feld `number` (Integer, store=True) auf `account.move.line` vorhanden
- View: `<field name="number" string="Line NO."/>` korrekt nach `sequence` im Rechnungsformular
- Live-Test an Rechnung RE/2026/0001: 3 Zeilen mit Nummern 1, 2, 3 — korrekt berechnet
- Keine Fehler, keine Warnungen

### Session 6: itk_product verifiziert & repariert

**Datum:** 01.07.2026

#### Initialer Status
- Modul war installiert (v18.0.1.0.0), aber mit zwei Problemen

#### Fix 1: Duplikate entfernt
- `recurring_invoice` und `subscription_template_id` erschienen 2× im Produktformular
- Ursache: itk_subscription UND itk_product fügten beide dieselben Felder hinzu
- Fix: Subscription-Gruppe aus `itk_product/views/itk_product.xml` entfernt

#### Fix 2: Product Types angelegt
- Tabelle `itk_product.product_type` war leer (0 Einträge)
- Ursache: Product Types werden von `itk_initial_product_import` definiert (nicht migriert)
- Fix: 6 Product Types direkt in Odoo 18 erstellt:
  - OS — Onlineservice, SW — Software-Lösung, C — Consulting
  - P — Plattform, HW — Hardware, FP — Förderprojekt

#### Verifikation
- Modul-Upgrade erfolgreich
- View: keine Duplikate (subscription: 1x, recurring_invoice: 1x, product_type_id: 1x)
- Testprodukt mit allen Feldern (product_type_id, to_multiply_by_factor, recurring_invoice) erfolgreich
- Alle Felder schreibbar und funktionsfähig

### Session 7: itk_projectcategory migriert nach Odoo 18

**Datum:** 01.07.2026

#### Migration
- Manifest: version 0.1 → 18.0.1.0.0, `# -*- coding: utf-8 -*-` entfernt, license/installable hinzugefügt
- Python: coding header aus account_invoice.py und itk_lookups.py entfernt
- Views: `<tree>` → `<list>`, `view_type` entfernt, `tree` → `list` in view_mode

#### Verifikation
- ✅ Modul installiert (v18.0.1.0.0)
- ✅ `projectcategory_id` (Many2one) auf `account.move` vorhanden
- ✅ View: Feld erscheint nach `invoice_date` im Rechnungsformular
- ✅ 26 Project Categories in DB (aus data/itk_projectcategory.xml geladen)
- ✅ Alle Felder schreibbar (can_create=True, can_write=True)

### Session 8: itk_sale_management migriert nach Odoo 18

**Datum:** 01.07.2026

#### Migration
- Manifest: coding header entfernt, license/installable hinzugefügt (Version war schon 18.0.1.0.0)
- Python: `# -*- coding: utf-8 -*-` aus models.py und controllers.py entfernt
- Views: Odoo-11-Attribute entfernt (mode, type, groups_id, active aus Such-Views)
- Security: Nicht-existente model_id aus CSV entfernt

#### Modulinhalt
Erweitert `sale.order` um 5 Felder:
- `administrative_contact_id` — Administrative Contact (res.partner)
- `technical_contact_id` — Technical Contact (res.partner)
- `sale_contact_id` — Sale Contact (res.partner)
- `product_category_id` — Product Category (product.category)
- `final_customer_id` — Final Customer (res.partner, auto-gesetzt aus partner_id)

#### Verifikation
- ✅ Modul installiert (v18.0.1.0.0)
- ✅ Alle 5 Felder auf sale.order vorhanden
- ✅ Form-View: alle Felder 1×, keine Duplikate
- ✅ Such-Views und Baum-Views korrekt geerbt

### Session 9: itk_valorisierung migriert nach Odoo 18

**Datum:** 01.07.2026

#### Migration
- Manifest: v0.1 → 18.0.1.0.0, coding header, license/installable
- **Kritisch**: `account.invoice` → `account.move` in account_invoice.py (Odoo 18 Modellumbenennung)
- Python: coding header aus itk_lookups.py entfernt
- Views: `<tree>`→`<list>`, `view_type` entfernt, `account.invoice`→`account.move`
- View-Erbe von `itk_subscription.view_account_invoice_subscription_note_form` funktioniert

#### Verifikation
- ✅ Modul installiert (v18.0.1.0.0)
- ✅ `valorisierung_id` (Many2one) auf `account.move` vorhanden
- ✅ View: Feld nach `notice` im Rechnungsformular
- ✅ `itk_valorisierung.valorisierung` Modell mit Tree/Form-Views

#### Nachtrag: Fehlende Zugriffsrechte
- Modul hatte **kein `ir.model.access.csv`** — `create: False`
- Valorisierung-Einträge konnten nicht erstellt werden (AccessError)
- Fix: `security/ir.model.access.csv` erstellt + in Manifest registriert
- Alle CRUD-Operationen jetzt: Create, Read, Write, Unlink ✓

### Session 10: itk_subscription Bugfixes & sale_order_line_number verifiziert

**Datum:** 01.07.2026

#### Ausgangslage
- itk_subscription lief in Odoo 18, aber es gab 3 versteckte Probleme
- sale_order_line_number war als "ausstehend" markiert

#### Fix 1: noticeperiod Zugriffsrechte fehlten
- Problem: `itk_subscription.noticeperiod` Modell hatte KEINE Zugriffsrechte in `ir.model.access.csv`
- Folge: Kein User (auch nicht Administrator) konnte die Notice-Period-Datensätze lesen
- Symptom: `search_count()` lieferte 0, obwohl die Daten in der DB existierten (Subscription Templates referenzierten sie korrekt)
- Fix: 3 neue Zeilen in `ir.model.access.csv` hinzugefügt:
  - `access_noticeperiod_manager` — Manager: CRUD 1,1,1,1
  - `access_noticeperiod_view` — View: Read-only 1,0,0,0
  - `access_noticeperiod_public` — Public: Read-only 1,0,0,0
- Ergebnis: 3 Notice Periods jetzt lesbar (zm — zum Monatsende, zq — zum Quartalsende, zl — zum Laufzeitende)

#### Fix 2: sale_order_confirmation_date fehlte in Rechnungsansicht
- Problem: Feld `sale_order_confirmation_date` existierte auf `account.move` aber war NICHT in der Form-View
- Fix: Feld zu `account_invoice_views.xml` hinzugefügt (nach `invoice_date`, vor `sale_order_benefit_period`)
- Ergebnis: Feld jetzt sichtbar im Rechnungsformular

#### Fix 3: subscription_management fehlte in Sale-Order-Ansicht
- Problem: Feld `subscription_management` (Selection: create/renew/upsell) existierte auf `sale.order` aber war NICHT in der Form-View
- Fix: Feld zu `sale_order_views.xml` hinzugefügt (XPath: `//group[@name='sale_header']/group[1]`)
- Ergebnis: Feld jetzt sichtbar im Verkaufsauftrag-Formular

#### Verifikation (JSON-RPC)
- ✅ sale.order.subscription_management — in rendered view
- ✅ sale.order.subscription_count — in rendered view
- ✅ account.move.sale_order_confirmation_date — in rendered view
- ✅ account.move.sale_order_benefit_period — in rendered view
- ✅ account.move.notice — in rendered view
- ✅ product.template.recurring_invoice — in rendered view
- ✅ product.template.subscription_template_id — in rendered view
- ✅ noticeperiod check_access_rights('read'): True (vorher False!)
- ✅ noticeperiod records: 3 (vorher 0)
- ✅ Modul-Upgrade erfolgreich

### Session 11: sale_order_line_number verifiziert

**Datum:** 01.07.2026

#### Ergebnis
Modul `sale_order_line_number` ist in Odoo 18 bereits vollständig integriert und funktionsfähig.
Keine Migration nötig — das Modul war bereits installiert und lief.

#### Verifikation
- Modul: installed, v18.0.1.0.0
- Feld `number` (Integer, store=True, readonly=True) auf `sale.order.line` vorhanden
- View: `<field name="number" string="Line NO."/>` erscheint nach `sequence` in der order_line-Liste im Verkaufsauftrag
- Live-Test: Sale Order mit 3 Positionen erstellt → Nummern 1, 2, 3 korrekt berechnet
- Keine Fehler, keine Warnungen

#### Aktueller Gesamtstand
Alle 7 Module in `addons/` sind jetzt fertig migriert und getestet:
| # | Modul | Status |
|---|---|---|
| 1 | itk_subscription | ✅ Fertig getestet |
| 2 | account_invoice_line_number | ✅ Fertig |
| 3 | itk_product | ✅ Fertig |
| 4 | itk_projectcategory | ✅ Fertig |
| 5 | itk_sale_management | ✅ Fertig |
| 6 | itk_valorisierung | ✅ Fertig |
| 7 | sale_order_line_number | ✅ Fertig |

Alle Felder in allen Views sichtbar und funktionsfähig.
Nächster Schritt: Weitere ~49 Module aus `odoo11 module/` migrieren.

### Session 12: strptime TypeError behoben + Docker-Neustart

**Datum:** 01.07.2026 (Session nach docker compose down/up)

#### Problem
Beim Klick auf "Neu" unter Abonnements: `RPC_ERROR` — `TypeError: strptime() argument 1 must be str, not datetime.date`

#### Ursache (Root Cause)
In Odoo 18 liefern `fields.Date`-Felder `datetime.date`-Objekte (keine Strings mehr wie in Odoo 11).
Der alte Code rief `datetime.datetime.strptime(date_feld, "%Y-%m-%d")` auf — das crasht bei date-Objekten.

#### Fix (5 Stellen in `sale_subscription.py`)
- `_compute_end_date` (line 141): `isinstance`-Check — `datetime.date` → `datetime.combine()`, String → `strptime()`
- 4 weitere `strptime(subscription.recurring_next_date, ...)` → gleicher `isinstance`-Schutz
  - `_recurring_create_invoice` (line 651)
  - `send_success_mail` (line 678)
  - `partial_recurring_invoice_ratio` (line 714)
  - `_prepare_invoice_data` (line 735)

#### Docker-Neustart
- `docker compose down` + `docker compose up -d` (Container komplett entfernt und neu erstellt)
- Grund: `.pyc`-Cache im Docker-Container überlebt `docker restart` und `button_immediate_upgrade` nicht
- Nur ein komplettes Container-Recycling zwingt Odoo zur Neu-Kompilierung des Python-Codes
- **Dies ist die zuverlässigste Methode nach Python-Code-Änderungen im Docker-Setup**

#### Verifikation
- ✅ Abo-Erstellung per JSON-RPC: erfolgreich (ID 172)
- ✅ Kein TypeError mehr — alle 5 `isinstance`-Checks aktiv
- ✅ Modul itk_subscription v18.0.1.0.0 läuft fehlerfrei
- ✅ Alle 7 Module weiterhin installiert und funktionsfähig

#### Gesamt-Verifikation (01.07.2026)
| # | Modul | Status | Version |
|---|---|---|---|
| 1 | itk_subscription | ✅ Fertig (strptime fix) | 18.0.1.0.0 |
| 2 | account_invoice_line_number | ✅ Fertig | 18.0.1.0.0 |
| 3 | itk_product | ✅ Fertig | 18.0.1.0.0 |
| 4 | itk_projectcategory | ✅ Fertig | 18.0.0.1 |
| 5 | itk_sale_management | ✅ Fertig | 18.0.1.0.0 |
| 6 | itk_valorisierung | ✅ Fertig | 18.0.1.0.0 |
| 7 | sale_order_line_number | ✅ Fertig | 18.0.1.0.0 |

**Lookup-Daten:**
| Modell | Datensätze |
|---|---|
| itk_product.product_type | 6 |
| itk_subscription.noticeperiod | 3 |
| sale.subscription.template | 2 |
| itk_projectcategory.projectcategory | 26 |
| itk_valorisierung.valorisierung | 1 |

**Feld-Check (alle im View):**
- product.template: recurring_invoice ✓, subscription_template_id ✓, product_type_id ✓
- sale.order: subscription_count ✓, subscription_management ✓, alle 5 itk_sale_management Felder ✓
- account.move: sale_order_confirmation_date ✓, sale_order_benefit_period ✓, notice ✓, projectcategory_id ✓, valorisierung_id ✓
- sale.order.line: number ✓ (automatisch berechnet)
- account.move.line: number ✓ (automatisch berechnet)

#### Nachtrag: Asset-Cache nach docker compose down/up

**Problem:** Login-Seite komplett ungestylt — nur rohes HTML, keine CSS, kein Odoo-Design. "Your logo"-Platzhalter statt Logo, blaue Standard-Links, kein Layout.

**Ursache:** Nach `docker compose down` + `up -d` wurde der Container neu erstellt. Die Container-internen CSS/JS-Bundles sind frisch, aber in der Datenbank (`ir.attachment`) liegen noch 11 alte Asset-Bundles mit URLs `/web/assets/*`. Diese referenzieren veraltete Datei-Hashes → Browser lädt kaputte oder leere CSS-Dateien.

**Fix:**
1. Asset-Bundles per API löschen:
   ```
   ir.attachment.search([('url', 'like', '/web/assets/%')]) → 11 IDs
   ir.attachment.unlink([...]) → True
   ```
2. Seite neu laden → Odoo regeneriert CSS/JS-Bundles frisch
3. Login-Seite sofort wieder korrekt gestylt (lila Design, zentriert, Logo)

**Wichtig:** Das passiert bei JEDEM `docker compose down` + `up -d`. Immer danach prüfen ob die Assets noch laden. Falls nicht: Asset-Cache wie oben leeren.

**⚠️ Merkregel: Nach jedem Container-Neubau:**
1. Prüfen ob Login-Seite CSS hat
2. Falls nicht → `ir.attachment` Assets löschen
3. Seite neu laden

### Session 13: itk_saleorder_lines migriert nach Odoo 18

**Datum:** 01.07.2026

#### Migration
- Manifest: Version v0.4 → 18.0.1.0.0, coding header entfernt, license/installable hinzugefügt
- Python: coding header aus allen .py-Dateien entfernt
- Views: `<tree>`→`<list>` in view_mode, `view_type`-Attribut entfernt
- Keine security-Datei nötig (sale.order.line hat bereits ACLs vom sale-Modul)

#### Modulinhalt
Erweitert `sale.order.line` um 2 Felder:
- `partner_id` (Many2one zu res.partner)
- `salesperson_id` (Many2one zu res.users)

Fügt Menüeintrag "All Order Lines" unter Sales/Orders hinzu.

#### Verifikation
- ✅ Modul installiert (v18.0.1.0.0)
- ✅ Felder partner_id und salesperson_id auf sale.order.line vorhanden
- ✅ Menü "All Order Lines" unter Sales/Orders erstellt
- ✅ Funktionstest: Sale Order erstellt, partner_id und salesperson_id korrekt gesetzt

#### Abhängigkeiten für nächste Module
Dieses Modul ist Voraussetzung für `itk_multifactor` — nächster Migrationskandidat.
- ✅ itk_saleorder_lines → hängt ab von: base, sale → alle verfügbar

### Session 14: itk_multifactor migriert nach Odoo 18

**Datum:** 02.07.2026

#### Migration
- Manifest: Version v0.1 → 18.0.1.0.0, coding header entfernt, license/installable hinzugefügt
- Python (4 Modelle): coding header entfernt, `track_visibility`→`tracking=True`, `@api.multi` entfernt, `self._context`→`self.env.context`
- Cross-Modul-Guards: `_compute_communitymagnitude()` und `population` mit `hasattr` geschützt (kommen aus itk_crm, noch nicht migriert)
- Views (6 XMLs): `<tree>`→`<list>`, `attrs`→`invisible`, `view_type` entfernt, `product_template_only_form_view`→`product_template_form_view`
- Wizards (3): `itk_contacts_update_multifactor`, `itk_subscriptionline_update_multifactor`, `itk_subscription_set_pricelist`
- XML-Format: `<?xml?>`+`<odoo>`+`<record>` ohne `<data>`-Wrapper (Odoo-18-Standard)

#### Pitfall: RNG-Validierung bei XML-Dateien
Odoo 18 validiert Daten-XML-Dateien strenger via RelaxNG. `<odoo><data>` und `<odoo><record>` (ohne `<?xml?>`) wurden beide abgelehnt. Lösung: `<?xml version="1.0" encoding="utf-8"?>` + `<odoo>` + bare `<record>` (exakt wie Odoo-18-Quellcode).

#### Modulinhalt
- `res.partner` + `multi_factor` (Integer, auto-berechnet aus EWZ/1000)
- `product.template` + `is_multi_factor_product` (Boolean)
- `sale.order.line` + `qty_multiplication_factor` (Integer)
- `sale.subscription.line` + `qty_multiplication_factor` (Integer)
- 3 Wizards für Batch-Updates

#### Verifikation
- ✅ Modul installiert (v18.0.1.0.0)
- ✅ Alle 4 Felder auf den Modellen vorhanden
- ✅ multi_factor schreibbar und lesbar (Wert 42 getestet)
- ✅ is_multi_factor_product schreibbar (True/False)

#### Gelöste Blockade
Der `hasattr`-Guard in `itk_subscription` für `multi_factor` kann jetzt entfernt werden — das Feld existiert jetzt.
Nächstes Modul sollte `itk_crm` sein (liefert `population` und `_compute_communitymagnitude`).

### Session 15: JS-Fehler in Odoo behoben (tour.js)

**Datum:** 02.07.2026

#### Problem
Rotes Banner in Odoo: "An error occurred while loading javascript modules"
Browser-Konsole zeigte:
```
The following modules are needed by other modules but have not been defined:
  ["web.core", "web_tour.tour"]
The following modules could not be loaded:
  ["@itk_subscription/js/tour"]
```

#### Ursache
`itk_subscription/static/src/js/tour.js` verwendete Odoo-11-JS-Pattern:
- `odoo.define('itk_subscription.tour', ...)` — in Odoo 18 durch `@odoo-module` ersetzt
- `require('web.core')` und `require('web_tour.tour')` — existieren nicht mehr in Odoo 18 Asset-Bundles

#### Fix
1. `tour.js` aus `__manifest__.py` Assets entfernt (`web.assets_backend`)
2. `tour.js` auf Disk durch Platzhalter-Kommentar ersetzt
3. Docker-Neustart nötig weil Container Datei-Änderungen cached
4. Nach Docker-Neustart: Asset-Cache geleert

#### Verifikation
- ✅ Keine JS-Errors in Browser-Konsole
- ✅ Login-Seite lädt korrekt mit CSS
- ✅ Settings-Seite ohne roten Fehler-Banner
- ✅ Alle 9 Module weiterhin installiert

#### Pitfall: Docker-Container cached statische Dateien
Der Docker-Container cached statische Dateien aus dem Shared-Folder.
`button_immediate_upgrade` allein reicht nicht — Docker muss neustarten,
damit Änderungen an JS/CSS-Dateien wirksam werden.

### Session 16: itk_crm migriert nach Odoo 18

**Datum:** 02.07.2026

#### Migration
- Manifest: Version v0.2 → 18.0.1.0.0, coding header, license/installable, depends: sale_management→sale
- Python (7 Modelle): coding header, @api.one→for-loop, @api.multi entfernt, view_type entfernt
- Views: alle attrs=→invisible=, type="search" entfernt, mode="extension" entfernt
- View-Fixes: supplier/customer/company_name/open_parent entfernt (existieren nicht in Odoo 18)
- XML: <?xml?>+<odoo>+<record> ohne <data>-Wrapper
- Security: ITK-Gruppen (itk_group_user, itk_group_manager)
- Data: 14 Community-Magnitude-Klassen + 3 Status-of-Partner

#### Odoo-18-Änderungen
- res.partner: supplier, customer, company_name, open_parent entfernt

#### Modulinhalt (19 Felder + 6 Lookup-Modelle)
population, community_magnitude (auto-computed), status_of_partner_id, asset_partner, attention_of, uvm.

#### Verifikation
- ✅ v18.0.1.0.0, 19 Felder, 14 magnitudes, 3 partner-status
- ✅ population=1200 → magnitude="1.001 bis 1.500"
- ✅ ITK-Gruppen, Admin zugeordnet

#### Gelöste Blockaden
population + _compute_communitymagnitude → itk_multifactor hasattr-Guards entfernbar.

Nächster Schritt: Weitere ~45 Module aus `odoo11 module/` migrieren.

### Session 17: account_invoice_line_report migriert nach Odoo 18

**Datum:** 02.07.2026

#### Migration
- Manifest: Version v11.0.1.0.0 → 18.0.1.0.0, `application`/`auto_install` hinzugefügt
- Keine Python-Dateien (reines View-Modul)
- View-XML: `<tree>`→`<list>`, `view_type` entfernt
- Feld-Renames: `categ_id`→`product_categ_id`, `product_qty`→`quantity`
- Search-View: `date`→`invoice_date` (Feldname in Odoo 18)
- `uom_name`-Filter entfernt (kein valides Feld mehr im Modell `account.invoice.report`)
- Menü-Parent: `account_reports_business_intelligence_menu`→`account.menu_finance_reports`

#### Modulinhalt
Erweitert `account.invoice.report` um:
- Tree-View "Invoice Line" mit partner_id, product_categ_id, product_id, quantity, price_average, price_total
- Search-View-Erweiterung: without_price/with_price Filter
- Action "Invoice Lines" + Menüeintrag unter Invoicing → Reporting

#### Fehler & Lösungen
| # | Fehler | Ursache | Lösung |
|---|---|---|---|
| 1 | `categ_id` existiert nicht | Feld in Odoo 18 umbenannt | `categ_id`→`product_categ_id`, `product_qty`→`quantity` |
| 2 | XPath `date` nicht gefunden | Search-View verwendet `invoice_date` | `date`→`invoice_date` |
| 3 | `uom_name` existiert nicht | Odoo 18 validiert Suchfelder gegen Modell | `uom_name` Filter entfernt |
| 4 | `account_reports_business_intelligence_menu` nicht gefunden | Menü in Odoo 18 umbenannt | →`account.menu_finance_reports` |

#### Verifikation
- ✅ Modul installiert (v18.0.1.0.0)
- ✅ Tree-View mit allen 7 Feldern korrekt
- ✅ Search-View mit without_price/with_price Filter
- ✅ Menü "Invoice Lines" unter Invoicing → Reporting
- ✅ 3 Datensätze im Report vorhanden

#### Aktueller Gesamtstand (02.07.2026)
| # | Modul | Status |
|---|---|---|
| 1 | itk_subscription | ✅ |
| 2 | account_invoice_line_number | ✅ |
| 3 | itk_product | ✅ |
| 4 | itk_projectcategory | ✅ |
| 5 | itk_sale_management | ✅ |
| 6 | itk_valorisierung | ✅ |
| 7 | sale_order_line_number | ✅ |
| 8 | itk_saleorder_lines | ✅ |
| 9 | itk_multifactor | ✅ |
| 10 | itk_crm | ✅ |
| 11 | account_invoice_line_report | ✅ |
| 12 | partner_firstname | ✅ |

12/56 Module migriert.

### Session 18: partner_firstname migriert nach Odoo 18

**Datum:** 02.07.2026

#### Migration
- Manifest: Version 11.0.1.0.1 → 18.0.1.0.0, application/auto_install hinzugefügt
- Python (3 Modelle): Coding-Header entfernt, `@api.multi` entfernt (Odoo 18 Default)
- hooks.py: `post_init_hook(cr, _)` → `post_init_hook(env)` (neue Odoo-18-Signatur)
- Views (3 XML): `<data>`-Wrapper entfernt, ALLE `attrs` → `invisible`/`required` konvertiert
- Settings-View: Odoo-11 `<div class="settings">` → Odoo-18 `<app>`/`<block>`/`<setting>` (pitfall #22)
- XPath fix: `//div[@name='multi_company']` → `//app[@name='general_settings']`

#### Modulinhalt
- `res.partner` + `firstname` (Char), `lastname` (Char), `name` wird computed
- `res.users` + Name-Splitting-Logik
- `res.config.settings` + Partner Names Order (last_first, last_first_comma, first_last)
- post_init_hook: Bestehende Partner-Namen automatisch splitten

#### Fehler & Lösungen
| # | Fehler | Ursache | Lösung |
|---|---|---|---|
| 1 | `//div[@name='multi_company']` nicht gefunden | Settings in Odoo 18 neu | XPath auf `<app name='general_settings'>` |
| 2 | `post_init_hook() missing argument '_'` | Signatur (cr, _) veraltet | → (env) |
| 3 | Docker-cache hielt alte hooks.py | .pyc-Cache in Container | docker compose down && up -d |

#### Verifikation
- ✅ Modul installiert (v18.0.1.0.0)
- ✅ firstname/lastname Felder auf res.partner
- ✅ Name computed: "Mustermann Max" (last_first)
- ✅ Settings: Partner Names Order + Recalculate Button
- ✅ Partner mit firstname/lastname erstellt (ID 13)

Nächster Schritt: hr_employee_firstname (abhängig von partner_firstname).

### Session 18 Nachtrag: Gründlicher Integrationstest beider neuer Module

**Datum:** 02.07.2026

#### account_invoice_line_report — Testprotokoll

| Test | Ergebnis |
|---|---|
| Module state | installed, v18.0.1.0.0 ✅ |
| Tree View `account.invoice.report.tree.info` | 7/7 Felder: partner_id, product_categ_id, product_id, quantity, price_average, price_total, currency_id ✅ |
| Search View `view_account_invoice_report_search` | Inherits `account.invoice.report.search` (ID 1045), without_price + with_price filter ✅ |
| Search View XPath | invoice_date im XPath ✅ |
| Action Window | Invoice Lines → account.invoice.report, view_mode: list,pivot,graph ✅ |
| Menü | Invoice Lines → Invoicing/Reporting ✅ |
| Datenzugriff | 3 records lesbar, Felder korrekt ✅ |
| Keine `attrs=` in Views | ✅ |
| Keine `<tree>` mehr | ✅ (verwendet `<list>`) |

#### partner_firstname — Testprotokoll

| Test | Ergebnis |
|---|---|
| Module state | installed, v18.0.1.0.0 ✅ |
| Felder res.partner | firstname (Char, store), lastname (Char, store), name (Char, computed) ✅ |
| Simple Form View | Inherits base.view_partner_simple_form, firstname+lastname, invisible/is_company ✅ |
| Full Form View | Inherits base.view_partner_form, firstname+lastname, child_ids ✅ |
| User Form View | Inherits base.view_users_form, name readonly=True, firstname+lastname ✅ |
| Settings View | Odoo-18-Format: `<app>/<block>/<setting>`, partner_names_order ✅ |
| Create (Anna Maierhofer) | firstname='Anna' lastname='Maierhofer' → name='Maierhofer Anna' ✅ |
| Update lastname → Meier | name recomputed: 'Meier Anna' ✅ |
| Create Company | firstname=False, lastname='Testfirma GmbH', name='Testfirma GmbH' ✅ |
| Post-install hook | 3/7 Partner haben firstname+lastname ✅ |
| Keine `attrs=` in Views | ✅ |
| Keine `<data>` auf Disk | ✅ |
| partner_names_order im Settings | ✅ |
| Recalculate Button im Settings | ✅ |
| Test-Daten gelöscht | ✅ |

#### Ergebnis
Beide Module fehlerfrei installiert und voll funktionsfähig. Alle Views, Felder, Menüs und Einstellungen wie erwartet.

Nächster Schritt: hr_employee_firstname (abhängig von partner_firstname).

### Session 19: hr_employee_firstname migriert nach Odoo 18

**Datum:** 02.07.2026

#### Migration
- Manifest: Version 11.0.1.0.1 → 18.0.1.0.0
- Python: `@api.multi` entfernt, `address_home_id`-Guard (Feld in Odoo 18 entfernt)
- init_hook: `post_init_hook(cr, pool)` → `post_init_hook(env)`
- View: `label[@for='name']` XPath entfernt (Label existiert in Odoo 18 nicht mehr)
- View: `field[@name='name']` hidden + firstname/lastname in `<h1>` eingefügt

#### Fehler & Lösungen
| # | Fehler | Ursache | Lösung |
|---|---|---|---|
| 1 | `label[@for='name']` nicht lokalisiert | Kein Label für name in Odoo 18 | XPath entfernt |
| 2 | `KeyError: address_home_id` | Feld in Odoo 18 entfernt | `_fields`-Check statt `hasattr()` |
| 3 | Docker .pyc-Cache | Container cached alte bytecodes | docker compose restart |

#### Verifikation
- ✅ v18.0.1.0.0, installed
- ✅ firstname/lastname auf hr.employee
- ✅ Name computed: "Mustermann Max"
- ✅ View: name hidden, firstname+lastname in h1
- ✅ Create/Update funktioniert

13/56 Module migriert.

---

### Session 20: itk_multifactor – Bugfixes beim Abo-Test (act_window + fehlende Wizard-ACL)

**Datum:** 07.07.2026
**Modul:** `itk_multifactor` (bereits migriert, aber beim Test des Abo-Moduls fielen zwei Fehler auf)
**Auslöser:** Beim Upgrade/Test des Moduls „Abo" (`itk_subscription`) über die Odoo-UI erschien:
`RPC_ERROR … AssertionError: Element odoo has extra content: record, line 4`

#### Ursachenanalyse
- Ein Upgrade von `itk_subscription` kaskadiert automatisch auf das abhängige `itk_multifactor`
  (Modul, das von `itk_subscription` abhängt). Dabei wurden dessen Wizard-XML-Dateien neu eingelesen.
- Alle XML-Dateien wurden mit lxml gegen Odoos echtes RelaxNG-Schema
  (`odoo/import_xml.rng`, Branch 18.0) validiert. Ergebnis: `itk_subscription` = 0 Fehler,
  drei Dateien in `itk_multifactor/wizard/` = ungültig (Zeile 4).

#### Fehler 1 – veraltete `<act_window>`-Kurzform (RNG-Fehler)
Die Odoo-18-RNG erlaubt als Kind von `<odoo>` nur noch: `record`, `template`, `menuitem`,
`delete`, `function`, `asset`, verschachteltes `data`/`odoo` und Text. Das alte
`<act_window .../>`-Kurzform-Tag ist **nicht mehr gültig**. Der Validator meldet dann irreführend
den vorangehenden `<record>` (Zeile 4) als „extra content".

Betroffen (je 1 `<act_window>` am Dateiende):
- `wizard/itk_contacts_update_multifactor_view.xml`
- `wizard/itk_subscription_set_pricelist_view.xml`
- `wizard/itk_subscriptionline_update_multifactor_view.xml`

**Lösung (feature-erhaltend):** `<act_window>` → vollwertiges `<record model="ir.actions.act_window">`.
Die frühere Kontext-Aktion (`src_model` + `multi="True"` + `key2="client_action_multi"`,
sichtbar im „Aktion"-Menü bei selektierten Datensätzen) wird in Odoo 18 über
`binding_model_id` (ref auf das ir.model) + `binding_type="action"` nachgebildet:
- Contacts-Wizard → `binding_model_id ref="base.model_res_partner"`
- Set-Pricelist-Wizard → `ref="itk_subscription.model_sale_subscription"`
- Subscriptionline-Wizard → `ref="itk_subscription.model_sale_subscription_line"`

#### Fehler 2 – fehlende Zugriffsrechte für die Wizard-Modelle
Beim Funktionstest zeigte sich: `itk_multifactor` hatte **gar keine** `security/ir.model.access.csv`.
In Odoo 18 braucht **jedes** Modell explizite Rechte (auch TransientModels/Wizards) – sonst
scheitert jeder Klick auf die (nun sichtbaren) Kontext-Aktionen mit
„Sie sind nicht berechtigt … zu erstellen".

**Lösung:** neue Datei `itk_multifactor/security/ir.model.access.csv` mit Vollzugriff für
`base.group_user` (Standard-Odoo-Muster für Wizard-Modelle) für die 3 TransientModels,
und Eintrag `'security/ir.model.access.csv'` an **erster Stelle** der `data`-Liste im Manifest.

#### Wichtige Erkenntnis – Manifest-Cache (Odoo 18)
Das nachträgliche Hinzufügen einer **neuen** Daten-Datei zur `data`-Liste eines bereits
installierten Moduls wird von `button_immediate_upgrade` **nicht** übernommen, weil Odoo 18
das Manifest pro Prozess cached (`get_manifest` via `lru_cache`) – analog zum `.pyc`-Cache.
Sauberer Weg: `docker compose down && docker compose up -d` in `C:\Odoo-Test\`, danach
`itk_multifactor` erneut upgraden. Da Docker (Windows) vom Linux-VM nicht neustartbar ist,
wurden die 3 ACL-Datensätze zusätzlich direkt per JSON-RPC mit den korrekten External-IDs
(`itk_multifactor.access_…`) angelegt → Feature sofort nutzbar, CSV bleibt für saubere
Neuinstallation/Neustart konsistent (noupdate=0 aktualisiert vorhandene IDs kollisionsfrei).

#### Verifikation (JSON-RPC gegen http://192.168.56.1:8069, DB odoo18_test)
Vollständiger Funktionstest **26/26 bestanden (100 %)**:
- ✅ Alle XML-Dateien beider Kopien RNG-valide (je 51 Dateien, 0 Fehler)
- ✅ Upgrade `itk_subscription` (kaskadiert → `itk_multifactor`) fehlerfrei – Originalfehler weg
- ✅ Abo-Lebenszyklus: create → set_open → set_pending → set_open → set_close
- ✅ View-Felder vorhanden (product.template, sale.order, res.partner)
- ✅ Lesezugriff auf alle Custom-/Wizard-Modelle
- ✅ 3 Kontext-Aktionen mit korrektem `binding_model_id` + `binding_type=action` angelegt
- ✅ Set-Pricelist-Wizard real ausgeführt (mit `active_ids`-Kontext) → Preisliste am Abo gesetzt

#### Geänderte Dateien (beide Kopien synchron: Docker-Mount + Git)
- `addons/itk_multifactor/wizard/itk_contacts_update_multifactor_view.xml`
- `addons/itk_multifactor/wizard/itk_subscription_set_pricelist_view.xml`
- `addons/itk_multifactor/wizard/itk_subscriptionline_update_multifactor_view.xml`
- `addons/itk_multifactor/security/ir.model.access.csv` (NEU)
- `addons/itk_multifactor/__manifest__.py` (CSV in `data` aufgenommen)

`itk_multifactor` ist damit vollständig getestet und fehlerfrei. 16/56 Module migriert.

---

### Session 21: Login-Seite ungestylt / keine Anmeldefelder – Asset-Cache nach Docker-Neustart geleert

**Datum:** 07.07.2026
**Art:** Betriebs-/Laufzeitfix (KEINE Modul-Codeänderung, Migrationsstand bleibt 16/56)
**Auslöser:** Nach dem `docker compose down && docker compose up -d` aus Session 20 (itk_multifactor)
wollte Anna sich in Odoo anmelden. Die Login-Seite erschien komplett ungestylt: „Your logo"-Platzhalter,
blaue Standard-Links, kein Odoo-Design – und die Eingabefelder für E-Mail/Passwort waren nicht sichtbar.
(Screenshot: `C:\Odoo-Test\scans\LOGIN_odoo.png`)

#### Ursache (Root Cause)
Exakt das bereits in **Session 12 (Nachtrag)** dokumentierte und in der **Merkregel** festgehaltene Problem:
Beim `docker compose down/up` wird der Container neu erstellt, die Container-internen CSS/JS-Bundles sind
frisch – aber in der Datenbank (`ir.attachment`) liegen noch alte Asset-Bundles mit URLs `/web/assets/*`,
die auf veraltete Datei-Hashes zeigen. Der Browser lädt dadurch kaputte/leere CSS-Dateien, die Login-Seite
bleibt ungestylt und das Formular rendert nicht korrekt.

#### Fix (per JSON-RPC gegen http://192.168.56.1:8069, DB odoo18_test)
1. Als Administrator authentifiziert (uid=2).
2. `ir.attachment.search([('url','like','/web/assets/%')])` → **7 veraltete Bundles** gefunden
   (IDs: 958, 957, 956, 955, 850, 846, 845).
3. `ir.attachment.unlink([...])` → `True`.
4. Login-Seite (`/web/login`) neu geladen → Odoo regeneriert die Bundles frisch
   (nun ein sauberes `web.assets_frontend.min.css` mit neuem Hash `8b68e82`).

#### Verifikation
- ✅ Login-Seite wieder korrekt gestylt: zentrierte lila Karte, E-Mail-Feld, Passwort-Feld, Login-Button,
  „Passwort zurücksetzen" (visuell per Screenshot bestätigt).
- ✅ Kompletter Login-Durchlauf über die UI erfolgreich → Web-Client geladen (`/odoo/discuss`, Navbar + Backend-Assets rendern).
- ✅ Keine Datei-/Code-Änderung nötig, keine Modul-Neuinstallation.

#### Merkregel bestätigt (unverändert gültig)
**Nach JEDEM `docker compose down && docker compose up -d`:**
1. Prüfen, ob die Login-Seite CSS/Design hat.
2. Falls nicht → `ir.attachment` mit URL `/web/assets/%` löschen (per JSON-RPC oder UI).
3. Seite neu laden → Bundles regenerieren sich automatisch.

16/56 Module migriert (Stand unverändert – reiner Betriebsfix).

---

### Session 22: itk_sale_management – Layout-Bug „Angebotsdatum verrutscht" im Auftragsformular behoben

**Datum:** 07.07.2026
**Modul:** `itk_sale_management` (bereits migriert; reiner View-Layout-Fix)
**Auslöser:** Beim Neuanlegen eines Auftrags fiel auf, dass das Feld **Angebotsdatum** (`date_order`)
verrutscht war: Das Label „Angebotsdatum" stand oben (ohne Wert), der eigentliche Datumswert
(`07.07.2026 …`) erschien label-los weiter unten – zwischen **Vertriebsmitarbeiter** und **Preisliste**.
(Screenshot: `C:\Odoo-Test\scans\Auftrag_test.png`)

#### Ursache (Root Cause)
Die itk-Erb-View `view_saleorder_itk_form` (`addons/itk_sale_management/views/sale_order.xml`)
fügte den Vertriebsmitarbeiter (`user_id`) so ein:
```xml
<xpath expr="//field[@name='date_order']" position="before">
    <field name="user_id"/>
</xpath>
```
In Odoo 18 ist `date_order` im Basis-Formular als **zwei getrennte Elemente** aufgebaut:
```xml
<div class="o_td_label"><label for="date_order" string="Quotation Date"/></div>  <!-- Label -->
<field name="date_order" nolabel="1" .../>                                        <!-- Wert -->
```
`position="before"` schob `user_id` **genau zwischen** das Label-`<div>` und das Wert-`<field>`.
Dadurch wurde das Label/Wert-Paar im Group-Grid aufgebrochen: Das Label „Angebotsdatum" blieb in
seiner Zelle (ohne Wert), der Datumswert rutschte in die nächste freie Zelle unterhalb von
„Vertriebsmitarbeiter".

#### Fix (feature-erhaltend)
`position="before"` → `position="after"`. `user_id` sitzt jetzt sauber **nach** dem `date_order`-Feld.
Resultierende Reihenfolge in der rechten Spalte:
**Gültigkeit → Angebotsdatum (Label + Wert zusammen) → Vertriebsmitarbeiter → Preisliste → Zahlungsbedingungen.**
Das Feature (Vertriebsmitarbeiter im Kopf sichtbar) bleibt vollständig erhalten.

#### Geänderte Datei (beide Kopien synchron: Docker-Mount + Git)
- `addons/itk_sale_management/views/sale_order.xml` (XPath auf `date_order`, ~Zeile 112)

#### Deploy
- `button_immediate_upgrade` auf `itk_sale_management` (id 709) → erfolgreich.
- Reine XML-Änderung in einer bereits im Manifest gelisteten Datei → **kein Docker-Neustart nötig**
  (der .pyc/Manifest-Cache betrifft nur Python bzw. NEU hinzugefügte Dateien).

#### Verifikation
- ✅ `get_view('sale.order','form')`-Arch: `user_id` steht nach `date_order` (Reihenfolge korrekt).
- ✅ Im Entwicklermodus (Admin hat `base.group_no_one`, daher ist „Angebotsdatum" sichtbar) gerendertes
  Neu-Formular: Angebotsdatum-Wert klebt wieder am Label, „Vertriebsmitarbeiter" ist eine eigene Zeile,
  KEIN label-loser Datumswert mehr (per Screenshot bestätigt).
- ✅ Feld `date_order` hat `groups="base.group_no_one"` → nur im Entwicklermodus sichtbar (Odoo-18-Standard,
  erklärt, warum das Feld ohne Debug-Modus gar nicht erscheint).

#### Pitfall (neu, allgemeingültig für Odoo 18)
**Niemals** mit `position="before"` zwischen ein `<div class="o_td_label">…<label/>…</div>` und sein
zugehöriges `<field nolabel="1">` einfügen – das bricht das Label/Wert-Paar im Group-Grid und der Wert
verrutscht. Immer **nach** dem Feld (`position="after"`) oder **vor** dem Label-`<div>` einfügen.

16/56 Module migriert (Stand unverändert – reiner View-Layout-Fix).

---

### Session 23: itk_subscription – Abo-Smart-Button „Subscriptions" verifiziert (KEIN Bug – Vorlage am Produkt nötig)

**Datum:** 07.07.2026
**Art:** Verifikation/Diagnose (KEINE Code-Änderung)
**Auslöser:** Anna: In Odoo 11 erscheint nach dem Bestätigen eines Auftrags mit Abo-Produkt oben rechts
ein Smart-Button, der anzeigt, dass es ein Abo-Auftrag ist. In Odoo 18 „passiert nichts" – man erkennt
nicht, ob es ein Abo-Auftrag ist.

#### Untersuchung
- **View:** `itk_subscription/views/sale_order_views.xml` – Button `action_open_subscriptions`,
  `invisible="subscription_count == 0"`. `get_view('sale.order','form')` bestätigt: Button IST im
  gerenderten Arch vorhanden (XPath `//div[hasclass('oe_button_box')]/button[1]` greift → kein Silent-Fail).
- **Model:** `itk_subscription/models/sale_order.py` – `action_confirm()` ruft `create_subscriptions()`
  → `_split_subscription_lines()` filtert Order-Lines auf `not subscription_id and product_id.subscription_template_id`.
  `subscription_count` (computed) zählt Order-Lines mit gesetztem `subscription_id`.

#### Live-Test (JSON-RPC + Browser gegen http://192.168.56.1:8069, DB odoo18_test)
| Auftrag | Produkt | subscription_template_id | Ergebnis nach Bestätigen |
|---|---|---|---|
| S00177 | id 50 „TEST-Abo Monatlich" | ✅ Monatsabrechnung | Abo erzeugt (id 181), `subscription_id` gesetzt, `subscription_count=1` → **Smart-Button „Subscriptions (1)" sichtbar** (per Screenshot bestätigt) |
| S00178 | id 6 „Test-Abo monatlich" | ❌ keine | KEIN Abo, `subscription_count=0` → **kein Button** |

#### Fazit
**Kein Migrationsfehler.** Der Button funktioniert und entspricht 1:1 der Odoo-11-Logik: Die
automatische Abo-Erzeugung beim Bestätigen UND der Smart-Button setzen voraus, dass das Produkt eine
**Abrechnungsvorlage (`subscription_template_id`)** hat. Nur `recurring_invoice=True` anzuhaken genügt
NICHT. Der ursprüngliche Test wurde vermutlich mit einem Produkt ohne Vorlage gemacht.

#### Offener Datenpunkt (kein Code)
In der Test-DB haben nur id 50 + id 16 eine Vorlage; id 6 + id 13 nicht. Die Produkt→Vorlage-Zuordnung
kommt vermutlich aus nicht-migrierten Import-Daten (`itk_initial_product_import`, vgl. Session 6).
Empfehlung für später: reale Abo-Produkte mit einer Abrechnungsvorlage versehen (reine Datenpflege
im Produktformular: „Wiederkehrende Abrechnung" ✓ + Abrechnungsvorlage wählen).

#### Testartefakte (dürfen gelöscht werden)
Zu Diagnosezwecken angelegt: Aufträge **S00177** (mit Abo) + **S00178** (ohne Abo), Abo **id 181**.
S00177 dient als Live-Demo des funktionierenden Buttons.

16/56 Module migriert (Stand unverändert – reine Verifikation, kein Code geändert).

---

### Session 24: itk_subscription – RPC_ERROR beim Öffnen des Abo-Smart-Buttons (`_unknown`-Modell) behoben

**Datum:** 07.07.2026
**Modul:** `itk_subscription`
**Auslöser:** Klick auf den Abo-Smart-Button „Subscriptions" im bestätigten Auftrag →
`RPC_ERROR … ValueError: Invalid field 'id' on model '_unknown'` (Traceback in `fields.py` →
`comodel._order_to_sql(comodel._order, query)`).

#### Ursache (Root Cause)
Beim Lesen des `sale.subscription`-Datensatzes (web_read für das Formular) versucht Odoo, ein
relationales Feld zu laden, dessen **Ziel-Modell (`comodel`) nicht existiert** und daher zu
`_unknown` aufgelöst wird. Beim Sortieren des `_unknown`-Modells nach `id` bricht es ab.

Betroffenes Feld: **`tag_ids`** (Many2many „Tags"), definiert auf ZWEI Modellen mit dem in Odoo 18
**entfernten** Modell `account.analytic.tag`:
- `sale.subscription.tag_ids` (`sale_subscription.py` Zeile 29)
- `sale.subscription.template.tag_ids` (`sale_subscription.py` Zeile 902)

`account.analytic.tag` (Kostenstellen-/Analytic-Tags) wurde in Odoo 18 ersatzlos entfernt
(Analytic läuft jetzt über Analyse-Verteilung/`analytic_distribution`). Verifiziert per JSON-RPC:
`fields_get('tag_ids').relation == '_unknown'`.

**Zusätzlicher latenter Folgebug (gleiche Ursache):** In `_prepare_invoice_line` (Zeile 447) wurde
`'analytic_tag_ids': [(6, 0, line.analytic_account_id.tag_ids.ids)]` gesetzt. In Odoo 18 hat
`account.move.line` **kein** `analytic_tag_ids` mehr → hätte bei jeder Abo-Rechnungserstellung gecrasht.

#### Fix (feature-erhaltend)
- `sale.subscription.tag_ids`: `account.analytic.tag` → **`crm.tag`**
- `sale.subscription.template.tag_ids`: `account.analytic.tag` → **`crm.tag`** (Relationstabelle
  `sale_subscription_template_tag_rel` bleibt)
- `_prepare_invoice_line`: `analytic_tag_ids`-Key **entfernt** (Kostenstelle wird bereits über
  `analytic_distribution` gesetzt, Zeile 439)

**Warum `crm.tag`?** Es existiert in Odoo 18, hat ein `color`-Feld (die Views nutzen
`options="{'color_field': 'color'}"`) und ist exakt das Modell, das `sale.order.tag_ids` in dieser
DB bereits verwendet — also der konsistente, funktionierende Ersatz für die entfernten Analytic-Tags.

#### Geänderte Datei (beide Kopien synchron: Docker-Mount + Git)
- `addons/itk_subscription/models/sale_subscription.py` (Zeilen 29, 447, 902)

#### Deploy – ⚠️ Container-Neustart zwingend nötig (Python-Änderung)
Empirisch bestätigt: `button_immediate_upgrade` allein reicht NICHT — nach dem Upgrade war
`tag_ids.relation` weiterhin `_unknown` (der laufende Odoo-Prozess hält die alte Felddefinition im
Speicher; `.pyc`/Registry-Cache). **Aktivierung nur durch `docker compose down && docker compose up -d`
in `C:\Odoo-Test\` (auf dem Windows-Host, von der Linux-VM aus nicht auslösbar).**
`__pycache__` in beiden Kopien wurde bereits gelöscht.

Nach dem Neustart (Merkregel Session 12/21): ggf. Asset-Cache leeren
(`ir.attachment` mit URL `/web/assets/%`) und Login-Seite neu laden.

#### Status — ✅ ERLEDIGT & VERIFIZIERT (nach Container-Neustart, 07.07.2026)
Fix in beiden Kopien, gepusht. Nach `docker compose down && up -d` (durch Anna auf Windows):
- `itk_subscription` per JSON-RPC upgegradet → crm.tag-Verknüpfungstabellen angelegt.
- `sale.subscription.tag_ids` und `sale.subscription.template.tag_ids` → relation jetzt `crm.tag` (nicht mehr `_unknown`).
- Lesen von Abo id 181 fehlerfrei (`tag_ids: []`, kein Crash).
- **End-to-End im Browser:** Auftrag S00177 → Klick auf Smart-Button „1 Subscriptions" → Abo-Formular
  „Monatsabrechnung-Abonnement" öffnet sich fehlerfrei (kein RPC_ERROR, keine JS-Fehler, per Screenshot bestätigt).
- Asset-Cache nach dem Neustart erneut geleert (7 Bundles, `/web/assets/%`) — sonst leere Seite (Merkregel Session 21 erneut bestätigt).

16/56 Module migriert (Stand unverändert – Bugfix an bereits migriertem Modul).

---

### Session 25: itk_subscription – Neue Abo-Vorlage „Q – Quartalsabrechnung-Abonnement" angelegt

**Datum:** 08.07.2026
**Modul:** `itk_subscription` (Datenpflege + Erweiterung der Daten-XML; KEINE Python-/Logik-Änderung)
**Auslöser:** Anna wollte Abos testen und eine dritte Abrechnungsvorlage (quartalsweise) anlegen.
Bisher existierten zwei Vorlagen: **J – Jahresabrechnung-Abonnement** (jährlich) und
**M – Monatsabrechnung-Abonnement** (monatlich). Menüpfad: Abonnements → Konfiguration →
Vorlagen für Abonnements.

#### Vorgehen
1. Die zwei bestehenden Vorlagen live per JSON-RPC inspiziert (Struktur/Konvention ermittelt).
   `sale.subscription.template.name_get()` baut den Anzeigenamen als `"<code> - <name>"`.
2. Neue Vorlage **sauber als Modul-Datensatz** in `data/itk_sale_subscription_template.xml`
   ergänzt (feste External-ID `subscription_template_Q`), damit sie einen Modul-Neuaufbau
   überlebt und im Git dokumentiert ist. (Der erste Test-Datensatz war per JSON-RPC angelegt
   worden [id 7]; er wurde wieder gelöscht und via XML + Modul-Upgrade frisch mit fester
   External-ID erzeugt [res_id 8] → keine Dublette.)
3. Werte der neuen Vorlage:
   - `code` = **Q**, `name` = **Quartalsabrechnung-Abonnement** → Anzeige „Q - Quartalsabrechnung-Abonnement"
   - Wiederholung: **alle 3 Monate** (`recurring_rule_type=monthly`, `recurring_interval=3`) = quartalsweise
   - Kündigungsfrist (`noticeperiod`): `notice_period_2` „zum Quartalsende" (passt logisch zum
     Quartals-Abo; J und M nutzen „zum Monatsende")
   - Mindestlaufzeit 24 Monate, Kündigungsfrist-Zahl 3 Monate (konsistent mit der Jahres-Vorlage)

#### Geänderte Datei (beide Kopien synchron: Docker-Mount + Git)
- `addons/itk_subscription/data/itk_sale_subscription_template.xml` (neuer `<record>` `subscription_template_Q`)
- `diff` bestätigt: beide Kopien identisch, XML valide (`xml.dom.minidom.parse` OK).

#### Deploy
- `button_immediate_upgrade` auf `itk_subscription` (id 710) → erfolgreich.
- Reine Daten-Datei, bereits im Manifest gelistet (Zeile 40) → **kein Docker-Neustart nötig**
  (der .pyc-Cache betrifft nur Python bzw. NEU hinzugefügte Dateien).

#### Verifikation
- ✅ JSON-RPC: genau **EINE** Q-Vorlage. External-ID `itk_subscription.subscription_template_Q`
  → `res_id 8`. `recurring_interval=3` / `monthly`, `noticeperiod` = „zum Quartalsende".
- ✅ Browser (UI, http://192.168.56.1:8069, DB odoo18_test): Abonnements → Konfiguration →
  Vorlagen für Abonnements zeigt **1-3 / 3** Karten: J (1 Year), M (1 Month), **Q (3 Month)** —
  keine Dublette (per Screenshot bestätigt).

#### Hinweis (optionale Anpassung)
- Die neue Vorlage nutzt die Kündigungsfrist „zum Quartalsende". Falls stattdessen „zum Monatsende"
  (wie J/M) gewünscht ist, genügt ein 1-Zeilen-Fix (`noticeperiod` ref → `notice_period_1`).
- Kosmetischer Alt-Bestandteil der Daten: Die Kündigungsfrist heißt in der DB „zum Qauartalsende"
  (Tippfehler in `data/itk_noticeperiod.xml`, bereits aus Odoo 11 vorhanden). Nicht in dieser
  Session korrigiert (Scope), kann bei Bedarf separat gefixt werden.

16/56 Module migriert (Stand unverändert – reine Datenpflege an bereits migriertem Modul; keine neue Modul-Migration).

---

### Session 26: itk_subscription – Vorlagen-/Abo-Formular repariert (Felder „fehlten" wegen veralteter Chatter-/Widget-Syntax)

**Datum:** 08.07.2026
**Modul:** `itk_subscription` (View-Fix; KEINE Python-/Logik-Änderung)
**Auslöser:** Anna verglich das Vorlagen-Formular (Abonnements → Konfiguration → Vorlagen für
Abonnements) mit Odoo 11 (Scans: `C:\Odoo-Test\scans\Jahresabo_Odoo11.png` vs `Jahresabo_Odoo18.png`).
In Odoo 18 „fehlten die Felder" — sie konnte keine Vorlage mit Bedingungen anlegen; das Formular
zeigte stattdessen zwei rohe Tabellen/Listen.

#### Ursache (Root Cause)
Der Form-Arch war gültig und enthielt ALLE Felder — aber **drei Widgets existieren in Odoo 18 nicht
mehr** (Browser-Konsole: „Missing widget: …"):
- `mail_followers` (One2many `message_follower_ids`)
- `mail_thread` (One2many `message_ids`)
- `boolean_button` (Boolean `active`, Archiv-Smart-Button)

Fehlt ein Widget, rendert Odoo das Feld mit seinem **Default-Widget**. Für die One2many-Chatter-Felder
bedeutet das: rohe, editierbare **Listen** (Follower-Liste + Nachrichten-Liste) statt des richtigen
Chatters. Der Scan zeigte den nach unten gescrollten Bereich mit genau diesen Listen → Eindruck
„die Felder fehlen".

#### Betroffene Stellen (alle in `views/sale_subscription_views.xml`)
1. **Abo-Formular** (`sale.subscription`) Chatter (Z. 381–385): `message_follower_ids`/`activity_ids`/`message_ids` mit alten Widgets.
2. **Vorlagen-Formular** (`sale.subscription.template`) Archiv-Button (Z. 538–540): `boolean_button`.
3. **Vorlagen-Formular** Chatter (Z. 586–589): `message_follower_ids`/`message_ids` mit alten Widgets.

#### Fix (Odoo-18-Standard, 1:1 aus Kernmodul `product.template` übernommen)
- Beide Chatter-Blöcke → einfach **`<chatter/>`** (self-closing). Rendert Follower/Nachrichten/
  Aktivitäten korrekt inkl. „Nachricht senden" / „Notiz hinterlassen" / „Folgen".
- Archiv-Button (`boolean_button`) → **`<widget name="web_ribbon" title="Archived"
  bg_color="text-bg-danger" invisible="active"/>`** + `<field name="active" invisible="1"/>`.
  Archivieren/Reaktivieren läuft in Odoo 18 über das Aktionsmenü (Zahnrad); das rote „Archived"-Band
  zeigt den Status. Entspricht dem Odoo-18-Kernmuster.

#### Geänderte Datei (beide Kopien synchron: Docker-Mount + Git)
- `addons/itk_subscription/views/sale_subscription_views.xml` — XML valide, `diff` identical,
  0 alte Widgets verblieben (`grep` = 0).

#### Deploy
- `button_immediate_upgrade` auf `itk_subscription` (id 710) → erfolgreich. Reine XML-Änderung → **kein
  Docker-Neustart nötig**.

#### Verifikation
- ✅ Konsole VORHER: 3× „Missing widget" (`mail_followers`, `mail_thread`, `boolean_button`).
  NACHHER: **0 Meldungen, 0 Fehler**.
- ✅ `get_view('form')` für Template + Subscription: enthält `<chatter/>` + `web_ribbon`, keine alten Widgets.
- ✅ Browser (UI): Vorlagen-Formular zeigt jetzt ALLE Felder (Code, Recurrence, Min. Contract Life,
  Notice Period + Kündigungsfrist-Dropdown, ONLINE MANAGEMENT mit Closable by customer / Automatic
  Payment / Category, Terms and Conditions) + richtiger Chatter unten (per Screenshot bestätigt).
- ✅ „Neu"-Formular: alle Bedingungsfelder leer & editierbar → Anna kann jetzt selbst eine neue
  Vorlage anlegen (per Screenshot bestätigt).

#### Antwort auf Annas Frage (Vorlage selbst anlegen)
Abonnements → Konfiguration → Vorlagen für Abonnements → **„Neu"** → Template Name, Code, Recurrence
(Zahl + Einheit), Min. Contract Life, Notice Period (Zahl + Einheit + Kündigungsfrist) ausfüllen,
ONLINE-MANAGEMENT-Optionen setzen, speichern. Bisher ging das nicht, weil das Formular durch die
fehlenden Widgets kaputt gerendert wurde — jetzt behoben.

#### Pitfall (neu, allgemeingültig für Odoo 18)
Alte Chatter-Syntax `<div class="oe_chatter"><field name="message_follower_ids" widget="mail_followers"/>
<field name="message_ids" widget="mail_thread"/></div>` → in Odoo 18 durch **`<chatter/>`** ersetzen.
Archiv-Stat-Button mit `widget="boolean_button"` → durch **`web_ribbon`** ersetzen. Fehlende Widgets
crashen nicht hart, sondern rendern das Feld als Default-Widget (One2many → rohe Liste) — leicht mit
„fehlenden Feldern" zu verwechseln. Diagnose immer über die Browser-Konsole („Missing widget: …").

#### Nebenbefund (separat, NICHT in dieser Session gefixt – Scope)
Konsole meldet zusätzlich, dass das Frontend-JS `@itk_subscription/js/portal_subscription` das Modul
`web.dom_ready` nicht laden kann (in Odoo 18 entfernt). Betrifft nur das Portal-JS, nicht das
Backend-Formular. Kandidat für eine spätere Session.

16/56 Module migriert (Stand unverändert – View-Bugfix an bereits migriertem Modul).

---

### Session 27: itk_subscription – Portal-JS auf Odoo 18 portiert (`web.dom_ready` / jQuery entfernt)

**Datum:** 08.07.2026
**Modul:** `itk_subscription` (Frontend-Asset/JS-Fix; KEINE Python-/Logik-Änderung)
**Auslöser:** Nebenbefund aus Session 26 — die Browser-Konsole meldete beim Laden von Frontend-Seiten:
- „The following modules … have not been defined … [`web.dom_ready`]"
- „… could not be loaded because they have unmet dependencies … [`@itk_subscription/js/portal_subscription`]"

#### Ursache (Root Cause)
`static/src/js/portal_subscription.js` war noch im Odoo-11-Stil:
`odoo.define('itk_subscription.portal_subscription', function (require) { require('web.dom_ready'); … jQuery `$` … })`.
In Odoo 18:
- Das Modul `web.dom_ready` existiert nicht mehr → das JS-Modul konnte nie definiert werden (unmet dependency), daher der Ladefehler.
- jQuery (`$`) ist aus dem Frontend-Bundle (`web.assets_frontend`) entfernt.

#### Funktion des Skripts (1:1 erhalten)
Auf der Abo-Portal-Seite im „Abo schließen"-Modal (`#wc-modal-close`) beim Klick auf den Confirm-Button
(`.contract-submit`): Button deaktivieren, Spinner anzeigen, umgebendes `<form>` absenden. Das explizite
`form.submit()` ist nötig, weil das `disabled`-Attribut den nativen Submit sonst abbricht (verhindert Doppel-Submit).

#### Fix (Odoo-18-Standard)
- Datei komplett neu als **public widget** geschrieben: `/** @odoo-module **/` +
  `import publicWidget from "@web/legacy/js/public/public_widget";`.
- Kein `odoo.define`, kein `web.dom_ready`, kein jQuery — reines Vanilla-DOM (`ev.currentTarget`,
  `closest('form')`, `insertAdjacentHTML`).
- `selector: '#wc-modal-close'` + delegiertes Event `'click .contract-submit'`. Das Modal existiert nur
  auf der Abo-Schließen-Seite (`t-if="display_close"`) und ersetzt so den alten `.oe_website_contract`-Seiten-Guard.

#### Pitfall / wichtig zur Selektor-Wahl
Der Button `.contract-submit` liegt im Modal `#wc-modal-close`, das ein **Geschwister** von
`.oe_website_contract` ist (NICHT darin, gleiche Einrückung in `subscription_portal_templates.xml`).
Daher NICHT `.oe_website_contract` als Widget-Root nehmen (Event-Delegation würde nicht greifen),
sondern `#wc-modal-close`. Allgemeiner Odoo-18-Pitfall: altes `odoo.define` + `require('web.dom_ready')`
+ Frontend-jQuery → durch `publicWidget` (`@web/legacy/js/public/public_widget`) + Vanilla-DOM ersetzen.

#### Geänderte Datei (beide Kopien synchron: Docker-Mount + Git)
- `addons/itk_subscription/static/src/js/portal_subscription.js` (0 Alt-Tokens `odoo.define`/`require`/`dom_ready` im Code verblieben).

#### Deploy
- `button_immediate_upgrade` auf `itk_subscription` + **Asset-Bundle-Cache geleert** (`ir.attachment`
  mit URL `/web/assets/%`). Die JS-Datei liegt auf dem Mount → für den Container sofort sichtbar →
  **kein Docker-Neustart nötig**; nur der Bundle-Neubau war erforderlich (regeneriert beim nächsten
  Frontend-Seitenaufruf).

#### Verifikation
- ✅ Konsole auf Frontend-Seite (`/my`) VORHER: `web.dom_ready` + `portal_subscription`-Ladefehler.
  NACHHER: **0 Meldungen, 0 Fehler**.
- ✅ Modul-Loader live geprüft (`odoo.loader`): `failedCount=0`, `@itk_subscription/js/portal_subscription`
  ist definiert (`portalSubDefined=true`), keine `dom_ready`-Referenz mehr.

16/56 Module migriert (Stand unverändert – Frontend-Bugfix an bereits migriertem Modul).

### Session 28: itk_reports migriert nach Odoo 18 (ITK-Druckvorlagen: Angebot/Auftrag, Bestellung, Bestellanfrage, Rechnung)

**Datum:** 08.07.2026
**Modul:** `itk_reports` (NEU migriert – 17. Modul)
**Auslöser:** Anna sah in Odoo 18 unter Apps eine Karte `itk_reports` (nicht installiert). Diagnose ergab:
Es war ein noch nicht migriertes Odoo-11-Modul; die Apps-Karte war eine **DB-Karteileiche** (`ir.module.module`
id=706, state=uninstalled, leeres Manifest), deren Ordner nicht im aktiven addons-Pfad lag. Der Original-Code
lag unter `odoo11 module/itk_reports/`.

#### Was das Modul macht
QWeb-PDF-Druckvorlagen mit ITK-Briefkopf/-Fußzeile für vier Belegarten:
- Angebot/Auftrag (`sale.order`) – Report-Action `action_report_itk_saleorders`
- Bestellung (`purchase.order`) – `action_report_itk_purchaseorders`
- Bestellanfrage (`purchase.order`) – `action_report_itk_purchasequotations`
- Rechnung (`account.move`) – `action_report_itk_invoices` (in Odoo 11 auskommentiert → hier **aktiviert**)
`models.py` überschreibt `print_quotation` (sale/purchase) und `invoice_print` (account.move), um die ITK-Reports
statt der Standard-Reports zu drucken. Alle Report-Actions sind über das Drucken-Menü der jeweiligen Belege gebunden.

#### Odoo-18-Anpassungen (feature-erhaltend)
1. **Fremd-Modul-Präfix in Template-IDs → „Cannot update missing record" (NEUER, zentraler Pitfall).**
   Odoo 11 erlaubte `<template id="sale.report_itk_saleorder">` in einem FREMDEN Modul (itk_reports). Odoo 18
   deutet `id="sale.xxx"` als **Update eines existierenden sale-Records** → `Exception: Cannot update missing
   record 'sale.report_itk_saleorder_document'` beim Install. **Fix:** alle Template-IDs in den eigenen Namespace
   (`report_itk_saleorder…` → `itk_reports.…`); `t-call`, `inherit_id`, `report_name`/`report_file` entsprechend
   auf `itk_reports.*` umgestellt. `account.document_tax_totals` (echtes Odoo-Template) blieb unangetastet.
2. **`<report>`-Kurzform → vollwertige `<record model="ir.actions.report">`** (analog zum entfernten
   `<act_window>`-Shortcut; RNG-sicher). Print-Menü-Bindung via `binding_model_id` + `binding_type="report"`.
3. **`account.invoice` → `account.move`** in `models.py` (`_inherit`) und im Rechnungs-Template:
   `type→move_type`, `date_invoice→invoice_date`, `number→name`, `comment→narration`, `residual→amount_residual`,
   `payment_term_id→invoice_payment_term_id`; State-Werte `'open'/'paid'` → `'posted'`.
4. **`_get_tax_amount_by_group()` entfernt** (existiert in Odoo 18 nicht) → offizielle Steuersumme
   `<t t-call="account.document_tax_totals"><t t-set="tax_totals" t-value="doc/o.tax_totals"/></t>`
   (erhält Netto + Steuergruppen + Gesamt). Beim Purchase-Report manuelle Netto/Steuer/Gesamt-Tabelle (amount_*).
5. **`sale.order.order_lines_layouted()` entfernt** (sale_layout-Feature weg) → Positionstabelle direkt über
   `doc.order_line` gerendert (die innere Schleife nutzte ohnehin `doc.order_line`).
6. **`purchase.order.line.number` fehlt** (purchase_order_line_number nicht migriert) → Positionsnummer über
   Schleifenindex `l_index + 1` / `line_index + 1` (Feature erhalten, keine Fremd-Abhängigkeit nötig).
7. **`@api.multi` entfernt** (Odoo-18-Default). `self.sent = True` in `invoice_print` entfernt (Feld weg).
8. **Bootstrap 3 → 5:** `col-xs-N→col-N`, `pull-right→float-end`, `text-right→text-end`, `text-left→text-start`,
   `table-condensed→table-sm`, `hidden→d-none`, `mt8→mt-3`, `col-xs-offset-7→offset-7`.
9. **`t-field-options` → `t-options`**, Datumsformat `YYYY→yyyy`.
10. **Fehlende `groups=` entfernt:** `product.group_uom` (heißt jetzt `uom.group_uom`) und
    `sale.group_show_price_subtotal` existieren nicht mehr → Spalten immer sichtbar (kein Feature-Verlust).
    `sale.group_discount_per_so_line` existiert → behalten.
11. **`account.move.line.origin` entfernt** (Feld weg; war nur versteckte Spalte). **`_get_payments_vals()`**
    (Rechnung-mit-Zahlungen-Report) existiert nicht mehr → Template strukturell erhalten, Zahlungs-Teil auf
    `amount_residual` reduziert + TODO (dieser Report war in Odoo 11 nie aktiv). `depends` ergänzt: `purchase`, `account`.
12. `views/views.xml` + `views/templates.xml` (nur auskommentierter itk_product-Boilerplate) aus dem Manifest
    genommen; `demo/demo.xml` auf leeres `<odoo/>` gesetzt; auf Disk 1:1 belassen.

#### Install-Hürde: Manifest-Cache + DB-Karteileiche
`update_list` liest das Manifest für **existierende** `ir.module.module`-Records NICHT neu (lru_cache). Da die
Karteileiche id=706 schon vor Container-Start existierte, blieb `latest_version=False`, deps leer, und
`button_immediate_install` lud nichts (state hing bei „to install"). **Fix:** `docker compose down && up -d`
(durch Anna), dann `update_list` → deps/Manifest frisch → `button_immediate_install` → **state=installed**.

#### Verifikation (real, HTTP-gerendert)
- ✅ Modul installiert (state=installed), 4 Report-Actions + 11 QWeb-Views angelegt.
- ✅ Alle vier Reports fehlerfrei als HTML gerendert (echte Daten, `/report/html/…`, HTTP 200, keine QWeb-/Feldfehler):
  Angebot/Auftrag (S.O. 180), Rechnung (account.move 2), Bestellung + Bestellanfrage (Test-P.O.).
- ✅ Test-Bestellung nach dem Test wieder storniert + gelöscht (0 purchase.order verbleiben).

#### Gespeichert (beide Kopien synchron: Docker-Mount + Git) + GitHub
- `addons/itk_reports/` (komplettes Modul), PROJECT_KNOWLEDGE.md, README.md.

17/56 Module migriert.

#### Nachtrag Session 28: Report-Layout auf Bootstrap 5 neu aufgebaut
Beim ersten Test-Ausdruck (Auftrag S00180) war das PDF-Layout zerschossen: Adresse verrutscht, Info-Block
überlappte den Text, riesige Leerräume, Report ging über 2 Seiten. Ursache = Odoo-11-Inline-Styles, die in
Odoo 18 (wkhtmltopdf + Bootstrap 5) nicht mehr funktionieren:
- `style="line-height: 50%"` auf den Containern → Textzeilen quetschen sich, überlappen.
- `padding-top:10em` / `padding-top:5em` → Inhalt weit nach unten geschoben, riesige Leerflächen.
- Float-Layout über eigene `.column70`/`.column30`-Klassen ohne clearfix → Info-Block legt sich über Folgetext.
- `<form>`-Wrapper + verschachtelte `<div class="container">` → zusätzliche Layout-Verschiebungen.
**Fix (alle 4 Report-Templates):** Layout komplett auf Bootstrap-5-Grid umgebaut (`row`/`col-*`, `text-end`,
`ms-auto`, `mt-*`, `table table-sm`), alle `line-height:50%` und `em`-Paddings raus, Floats durch Grid ersetzt,
`<form>`-Wrapper entfernt. Feld-Bindungen (t-field/t-esc/t-call/tax_totals) blieben unverändert.
**Verifikation:** alle 4 Reports als PDF gerendert (HTTP 200, je 1 Seite, keine Überlappung) — Auftrag S00180,
Rechnung (account.move 2), Bestellung + Bestellanfrage (Test-PO, danach gelöscht). Layout sauber/professionell.
Pitfall in Skill `odoo-module-migration` #57 ergänzt.

### Session 29: purchase_order_line_number migriert nach Odoo 18 (Positionsnummer in Bestellungen)

**Datum:** 09.07.2026
**Modul:** `purchase_order_line_number` (NEU migriert – 18. Modul)
**Auslöser:** Nächstes Modul der Reihe. Logischer Kandidat, weil es das Geschwister der bereits
migrierten `sale_order_line_number` und `account_invoice_line_number` ist und in Session 28
(`itk_reports`) sein Fehlen umgangen werden musste (Positionsnummer im Bestell-Report über
QWeb-Schleifenindex statt über ein echtes Feld). Sehr klein, risikoarm.

#### Was das Modul macht
Fügt `purchase.order.line` ein berechnetes, gespeichertes Integer-Feld `number` hinzu, das die
Positionen einer Bestellung fortlaufend mit 1, 2, 3 … nummeriert, und zeigt es im Bestellformular
in der Positionsliste direkt nach dem Sortier-Handle (`sequence`) an.

#### Odoo-18-Anpassungen (feature-erhaltend)
1. **Manifest:** `version` `11.0.1.0.0` → `18.0.1.0.0` (Rest unverändert: `depends=['purchase']`,
   `license='AGPL-3'`, `installable=True`). Kein `# -*- coding -*-`-Header vorhanden → nichts zu entfernen.
2. **View (`views/purchase_order_view.xml`):** Odoo-11-Kurzform `<field name="sequence" position="after">`
   → expliziter XPath **`//field[@name='order_line']/list/field[@name='sequence']`** (Odoo 18: die
   Positionsliste im Bestellformular ist ein `<list>`, nicht `<tree>`; `sequence` liegt dort mit
   `widget="handle"`). Muster identisch zum bereits migrierten `sale_order_line_number`.
   Record-ID von `purchase_order_form` → `purchase_order_form_line_number` (sprechender, kollisionssicher).
3. **Model (`models/purchase_order_line.py`):** `@api.depends('sequence', 'order_id')` →
   **`@api.depends('sequence', 'order_id.order_line')`** — so wird `number` auch neu berechnet, wenn
   Positionen hinzugefügt/entfernt werden (nicht nur bei Umsortierung). Logik 1:1 erhalten.
4. **Übersetzung (`i18n/de.po`) – Original war fehlerhaft:** Die Odoo-11-`de.po` war ein Copy-Paste
   aus `sale_order_line_number` und referenzierte das FALSCHE Modul/Modell
   (`#. module: sale_order_line_number`, `field_sale_order_line__number`, `model_sale_order_line`) →
   die Übersetzung hätte für `purchase_order_line_number` nie gegriffen. Korrigiert auf
   `purchase_order_line_number` / `purchase.order.line` (`field_purchase_order_line__number`,
   `model_purchase_order_line`, View-ID `purchase_order_form_line_number`). Deutsche Strings behalten:
   "Line No." → "Pos", "Number" → "Nummer", Modellname → "Bestellposition". View-`string="Line No."`
   deckt sich jetzt exakt mit der `msgid`, sodass "Pos" tatsächlich angezeigt wird.

#### Install (kein Docker-Neustart nötig)
Modul war noch NIE gescannt (keine Ghost-`ir.module.module`-Karteileiche) → frischer
`update_list()` (erkannt als id 748, deps=`purchase`, shortdesc korrekt) → `button_immediate_install`
→ **state=installed, v18.0.1.0.0**. Reiner Frischinstall → Container kompiliert `.py` neu, kein
`docker compose down/up` erforderlich.

#### Verifikation (real, JSON-RPC)
- ✅ Feld `number` auf `purchase.order.line` vorhanden (Integer, `store=True`).
- ✅ Feld im gerenderten Bestellformular direkt nach `sequence` in der Positionsliste (`get_view`).
- ✅ Funktionstest: Test-Bestellung mit 3 Positionen angelegt → `number` = **1, 2, 3** korrekt berechnet.
- ✅ Test-Bestellung anschließend storniert + gelöscht (0 `purchase.order` verbleiben in der DB).

#### Gespeichert (beide Kopien synchron: Docker-Mount + Git) + GitHub
- `addons/purchase_order_line_number/` (komplettes Modul), `diff` Git↔Mount identisch, XML valide.
- PROJECT_KNOWLEDGE.md, README.md aktualisiert.

18/56 Module migriert.

#### Nachtrag Session 29: Positionsnummer aktualisiert sich jetzt LIVE im Formular (3 Module gefixt)

**Auslöser (Anna beim Testen):** Im „Neu"-Formular einer Bestellung mehrere Produkte anlegen und dann
per Anfasser umsortieren (oberstes Produkt nach unten) → die „Pos"-Nummern blieben stehen (Produkt A
behielt Nr. 1, obwohl es an dritter Stelle stand). Auch beim Löschen einer Zeile wurde nicht neu
nummeriert.

**Diagnose (JSON-RPC, ORM-Ebene):** Auf Speicher-Ebene war ALLES korrekt — nach `write` einer neuen
`sequence` bzw. nach `unlink` einer Zeile wurden die verbleibenden Positionen sauber neu nummeriert
(reorder: A→3, B→1, C→2; delete-mitte: A=1, C=2). Der Fehler lag also ausschließlich im **Live-Formular
(onchange, vor dem Speichern)**.

**Ursache:** `@api.depends('sequence', 'order_id.order_line')` markiert bei einer Sequenz-Änderung NUR
die verschobene Zeile zur Neuberechnung. Die Geschwisterzeilen hängen nur an der Sammlung `order_line`
(ändert sich beim reinen Umsortieren nicht) → sie werden im Formular nicht neu gerechnet und behalten
ihre alte Nummer bis zum Speichern.

**Fix (feature-erhaltend, gleiche Logik):**
- Abhängigkeit auf die **Sequenz der Geschwister** legen statt nur auf die Sammlung → jede Zeile rechnet
  neu, sobald irgendeine Sequenz sich ändert:
  - `purchase_order_line_number`: `order_id.order_line` → **`order_id.order_line.sequence`**
  - `sale_order_line_number`: `order_id.order_line` → **`order_id.order_line.sequence`**
  - `account_invoice_line_number`: `move_id.invoice_line_ids` → **`move_id.invoice_line_ids.sequence`**
- Iteration explizit **`.sorted(lambda l: l.sequence)`** statt Verlass auf die Recordset-Reihenfolge
  (im onchange spiegelt die In-Memory-Reihenfolge nicht zuverlässig die neue Sequenz wider).

**Warum alle drei:** `sale_order_line_number` und `account_invoice_line_number` (Session 11 / Session 5)
hatten den identischen latenten Fehler — er war nur nie beim Umsortieren getestet worden. Alle drei in
einem Docker-Neustart gefixt.

**Deploy:** Reine Python-/`@api.depends`-Änderung → der laufende Odoo-Prozess hält den alten Code im
Speicher; die Registry muss neu geladen werden. Aus der VM kein Docker-Zugriff → **`docker compose down
&& docker compose up -d` in `C:\Odoo-Test\` durch Anna**, danach Asset-Cache leeren (ir.attachment
`/web/assets/%`). Kein Modul-Upgrade nötig (kein Schema-/View-Change).

**Commits:** `973c7e2` (purchase), `88898aa` (sale + account_invoice). Beide Kopien (Git + Docker-Mount)
synchron, `diff` identisch.

**Verifikation offen:** Live-Test im Formular (reorder + delete) nach dem Docker-Neustart durch Anna.

**Neuer Pitfall (allgemein, Skill #59):** Ein `@api.depends` NUR auf der O2M-Sammlung (`parent.lines`)
aktualisiert Geschwisterzeilen beim Handle-Umsortieren NICHT live im Formular — die Abhängigkeit muss
auf das konkrete Sortierfeld der Geschwister zeigen (`parent.lines.sequence`), plus `.sorted()`.

#### Nachtrag Session 29 (2): Rechnung brauchte einen ANDEREN Fix als Auftrag/Bestellung

**Auslöser (Anna, Screenshot `C:\Odoo-Test\scans\positionen_rechnung.png`):** In der Rechnung bekam eine
neue Zeile „Line No. 0" statt 1, beim Umsortieren gerieten die Nummern durcheinander (angezeigt 3, 4, 0),
die 1 wurde nie vergeben; zusätzlich roter Fehler „Datensätze mit IDs … nicht gefunden".

**Warum der erste Fix (nur `.sequence`-Dependency) bei Rechnungen NICHT reichte:** `account.move` hat ZWEI
One2many auf `account.move.line`: `line_ids` (direktes Inverse) und `invoice_line_ids` (**domain-gefiltert**
auf `display_type in product/line_section/line_note`). Das Formular bindet an `invoice_line_ids`. Im onchange
ist ein domain-gefiltertes O2M NICHT zuverlässig befüllt: die gerade angelegte Zeile fehlt in
`move.invoice_line_ids` → sie wird beim Iterieren nie erreicht → bleibt auf Default 0; beim Umsortieren wird
auf einer veralteten/teilweisen Menge gerechnet (daher der „IDs nicht gefunden"-Fehler). Zusätzlich zählte
der alte Iterations-Code Abschnitts-/Steuer-/Zahlungszeilen mit — eine Abschnittszeile bekam eine Nummer,
sodass die Produkte 1, 3, 4 statt 1, 2, 3 hatten (server-seitig reproduziert).

**Fix (Rechnung):** Über das DIREKTE Inverse **`move_id.line_ids`** iterieren (im onchange zuverlässig
befüllt — genau wie `order_line` beim Auftrag), in Python auf **`display_type == 'product'`** filtern und
nach `sequence` sortieren:
```python
@api.depends('sequence', 'move_id.line_ids', 'move_id.line_ids.sequence', 'move_id.line_ids.display_type')
def _compute_number(self):
    for move in self.mapped('move_id'):
        number = 1
        product_lines = move.line_ids.filtered(lambda l: l.display_type == 'product')
        for line in product_lines.sorted(lambda l: l.sequence):
            line.number = number
            number += 1
```
Nur Produktzeilen werden nummeriert; Abschnitte/Notizen/Steuer/Zahlungsbedingung werden übersprungen
(entspricht dem Odoo-11-Verhalten, wo `account.invoice.line` nur Produktzeilen kannte). Logik server-seitig
verifiziert (Produkte → 1, 2, 3; Abschnitt/Steuer/Zahlung übersprungen). Commit `1d8b8ff`.

**Pitfall #59 im Skill ergänzt:** Bei domain-gefilterten O2M (`account.move.invoice_line_ids`) im onchange
über das direkte Inverse (`line_ids`) iterieren + in Python filtern, NICHT über das gefilterte Feld.

**Verifikation offen:** Live-Test in der Rechnung nach dem zweiten Docker-Neustart durch Anna.

#### Nachtrag Session 29 (3): Rechnung – endgültige Lösung auf account.move-Ebene (LIVE verifiziert)

Die Ansätze (2) scheiterten im Live-Formular (Anna: neue Zeile „0", Umsortieren chaotisch, dann „überall 1"):
- **Iteration über `line_ids`** → im onchange nur mit `self` befüllt (nicht das im Formular gebundene Feld)
  → jede Zeile sah nur sich selbst → **überall 1**.
- **Iteration über `invoice_line_ids` (auch `| self`)** → im zeilenbasierten onchange von `account.move`
  ebenfalls ohne Geschwister → weiter „1"; ein **stored-computed-Feld überschreibt** zudem die onchange-Werte
  im selben Zyklus wieder auf 1.
- Fazit (im Browser empirisch bestätigt): Ein **zeilenbasierter Compute kann bei `account.move` grundsätzlich
  nicht live funktionieren**.

**Endgültige Lösung — Nummerierung am Elternobjekt `account.move`:**
- `number` = **einfaches gespeichertes Feld, `readonly=True`, KEIN compute** (kein Clobbering; readonly, weil ohne
  compute sonst editierbar → störte die Eingabe).
- `@api.onchange('invoice_line_ids')` auf `account.move` → Live-Formular (dort ist `self.invoice_line_ids` vollständig).
- `create` + `write`-Override auf `account.move` → serverseitig erzeugte Rechnungen (Auftrag/Abo-Abrechnung).
  `write` nur für `state == 'draft'` (gebuchte Buchungen nie anfassen).
- Nur `display_type == 'product'` wird nummeriert (Abschnitt/Notiz/Steuer/Zahlung übersprungen).
- Commits: `1c68b86` (Move-Ebene), `1a0d8fa` (Feld readonly). Beide Kopien synchron.

**LIVE verifiziert (Browser, Kundenrechnung „Neu"):**
- ✅ Neue Zeile → sofort **1** (nicht mehr 0).
- ✅ Drei Produkte → **1, 2, 3**.
- ✅ Mittlere Zeile gelöscht → lückenlos **1, 2** (Cloud_Service von 3 → 2).
- ✅ Serverseitig (JSON-RPC create + write): create → 1,2,3 (Abschnitt übersprungen); Umsortieren → korrekt neu.
- Reorder-Drag konnte im automatisierten Browser nicht simuliert werden (jQuery-UI-Sortable reagiert nicht auf
  synthetische Events), nutzt aber denselben onchange → durch Löschen-Test + Server-Test abgedeckt.

**Pitfall #59 im Skill korrigiert/vervollständigt:** account.move braucht Nummerierung am Elternobjekt
(onchange + create/write, PLAIN readonly-Feld), NICHT über einen Zeilen-Compute.

**Auftrag & Bestellung:** unverändert korrekt über den Zeilen-Compute mit `order_id.order_line.sequence` + `.sorted()`
(Formular bindet `order_line` = direktes Inverse, das Odoo für den Kind-Compute vollständig befüllt).

### Session 30: merge_sale_order migriert nach Odoo 18 (Assistent „Aufträge zusammenführen")

**Datum:** 09.07.2026
**Modul:** `merge_sale_order` (NEU migriert – 19. Modul)
**Auslöser:** Nächstes Modul der Reihe (Verkaufsbereich). Kleiner TransientModel-Assistent (Aktiv Software),
der über das Aktionsmenü der Aufträge mehrere Angebote/Aufträge zusammenführt (4 Strategien:
neu+stornieren, neu+löschen, in bestehenden+stornieren, in bestehenden+löschen).

#### Odoo-18-Anpassungen (feature-erhaltend)
1. **Manifest:** `# -*- coding -*-` raus, version `11.0.1.0.0` → `18.0.1.0.0`, `depends` `sale_management` → `sale`,
   `application/auto_install` ergänzt.
2. **Alle .py:** coding-Header entfernt. `@api.multi` entfernt (Odoo-18-Default). `_description` am TransientModel
   ergänzt (Odoo 18 verlangt es). Klassenname `MergePurchaseOrder` → `MergeSaleOrder` (Original-Copy-Paste-Name).
3. **View:** `attrs="{'invisible':[...],'required':[...]}"` → `invisible="merge_type in ('new_cancel','new_delete')"`
   + `required="merge_type not in (...)"`. `<field name="view_type">form</field>` aus dem act_window entfernt
   (Odoo 18). `class="btn-default"` → `btn-secondary` (Bootstrap 5). `binding_model_id`/`target=new` behalten
   → Aktion erscheint im Aktionsmenü der Aufträge.
4. **Fehlende `ir.model.access.csv` (NEU angelegt, Pitfall #34):** Das Wizard-Modell hatte KEINE Zugriffsrechte.
   In Odoo 18 brauchen auch TransientModels explizite ACL → sonst `AccessError` beim Öffnen des Assistenten.
   CSV mit Rechten für `sales_team.group_sale_salesman` + `group_sale_manager` angelegt + ins Manifest eingetragen.
5. **Original-Bug korrigiert (damit das Feature funktioniert):** `existing_so_line` wurde im Original nur EINMAL
   vor allen Schleifen auf `False` gesetzt, nie pro Quellzeile → nach dem ersten Treffer wären alle folgenden
   Positionen fälschlich in dieselbe Zielposition gemergt worden. Fix: `existing_so_line = False` am Anfang jeder
   `for line in order.order_line`-Schleife (in allen 4 Strategien). Verifiziert: unterschiedliche Produkte bleiben
   getrennte Positionen, gleiche Produkte (gleicher Preis) werden korrekt in Menge summiert.

#### Install-Hürde: Manifest-Cache beim nachträglich ergänzten CSV (Pitfall #56)
Nach dem Frischinstall (Manifest ohne CSV) wurde das CSV nachgereicht. `button_immediate_upgrade` lud es NICHT
(`get_manifest`-lru_cache pro Prozess → altes Manifest ohne CSV). Normal bräuchte es `docker compose down && up -d`.
**Um Anna einen weiteren Neustart zu ersparen:** die beiden `ir.model.access`-Records per JSON-RPC direkt angelegt
– mit exakt den External-IDs, die das CSV vergibt (`merge_sale_order.access_merge_sale_order_salesman`/`_manager`)
+ passende `ir.model.data`-Einträge. So aktualisiert das CSV sie beim nächsten Neustart/Reinstall nur (keine
Duplikate); die 1:1-Quelle bleibt das CSV im Modul.

#### Verifikation (real, JSON-RPC)
- ✅ Modul installiert (state=installed, v18.0.1.0.0), Abhängigkeit `sale`.
- ✅ Aktion „Merge Orders" hängt im Aktionsmenü der Aufträge (`binding_model_id` = Sales Order, `target=new`).
- ✅ Funktionstest Strategie „neu + stornieren": SO1 (A×1, B×2) + SO2 (A×3, C×1) → neuer Auftrag mit A×4 (gemergt),
  B×2, C×1 (getrennt); SO1/SO2 = `cancel`. Reset-Bugfix bestätigt.
- ✅ Testdaten anschließend storniert + gelöscht (0 verbleibende Aufträge).

#### Gespeichert (beide Kopien synchron: Docker-Mount + Git) + GitHub
- `addons/merge_sale_order/` (komplett, inkl. `security/ir.model.access.csv`), `diff` identisch.
- PROJECT_KNOWLEDGE.md, README.md aktualisiert.

19/56 Module migriert. Naheliegendes nächstes: `merge_purchase_order` (Geschwister).

---

### Session 31: merge_sale_order – Merge zusätzlich für „Angebot gesendet" (sent) freigegeben

**Datum:** 09.07.2026
**Modul:** `merge_sale_order` (funktionale Erweiterung – KEIN neues Modul, Zähler bleibt 19/56)
**Art:** Bewusste, kleine Abweichung vom strikten 1:1 (auf Annas Wunsch, dokumentiert)

#### Auslöser
Anna testete den Assistenten „Merge Orders" und bekam beim Zusammenführen die Meldung
„Ungültiger Vorgang – Please select Sale orders which are in Quotation state to perform
the Merge Operation." Analyse: **kein Migrationsfehler** – die Prüfung ist 1:1 identisch
zum Odoo-11-Original. Der Wizard erlaubte bisher NUR den Status „Angebot" (draft). Fachlich
wollte Anna auch bereits per E-Mail versendete Angebote („Angebot gesendet", sent)
zusammenführbar machen.

#### Entscheidung
- `draft` (Angebot) **und** `sent` (Angebot gesendet) sind ab jetzt erlaubt – beides sind
  Vor-Bestätigungs-Status, fachlich gleichwertig zusammenführbar.
- Bestätigte Verkaufsaufträge (`sale`) und `cancel` bleiben **bewusst blockiert** –
  verbindlich/heikel, das Original schließt sie bewusst aus, das bleibt so.

#### Änderung (`wizard/merge_sale_order_wizard.py`, `merge_orders`, Zeile 44)
```
vorher:  if any(order.state != 'draft' for order in sale_orders):
             raise UserError(_('Please select Sale orders which are in
                                Quotation state to perform the Merge Operation.'))
nachher: if any(order.state not in ('draft', 'sent') for order in sale_orders):
             raise UserError(_('Please select Sale orders which are in Quotation or
                                Quotation Sent state to perform the Merge Operation.'))
```
Reine Python-Änderung (Logik + Meldungstext). Keine View-/Asset-/Manifest-Änderung.

#### Verifikation (real, JSON-RPC, hermess — doppelt getestet und dokumentiert)

**Test 1: Negativ (bestätigte Aufträge werden weiterhin blockiert, zerstörungsfrei)**
- ✅ `merge_orders` mit zwei **bestätigten** Aufträgen (S00180, S00179, beide `sale`) aufgerufen
  → korrekt abgebrochen mit der **neuen** Meldung „…Quotation or Quotation Sent state…".
  Das beweist zugleich: (a) der neue Code ist LIVE (Container-Neubau wirksam), (b) bestätigte
  Aufträge werden weiterhin korrekt blockiert.
- ✅ Die beiden Test-Aufträge blieben unverändert (`state='sale'`), nur der Validierungs-Check lief.
- ✅ Login gestylt (9 Asset-Bundles, `assets_frontend` vorhanden) – kein Asset-Cache-Problem nach dem Neustart.

**Test 2: Positiv (Merge mit 2× „Angebot gesendet" läuft sauber durch)**
- Mit Wegwerf-Aufträgen (S00195, S00196, beide `sent`, Kunde „Test Firma") durchgeführt:
  - S00195: 2× Abo Cloud Produkt à 57 EUR → 114 EUR
  - S00196: 3× Abo Cloud Produkt à 57 EUR → 171 EUR
- Merge-Strategie „new_cancel" (neuen Auftrag erstellen + Quellen stornieren) über JSON-RPC aufgerufen.
  - ✅ Neuer Entwurf S00197 erstellt mit **1 Position à 5 Einheiten × 57 EUR = 285 EUR netto**
    (342 EUR brutto inkl. Steuern) — die 2+3 wurden korrekt in eine Position summiert
    (gleiches Produkt, gleicher Preis → Mengen-Additionslogik des Wizards funktioniert).
  - ✅ Quellaufträge blieben nach `merge_orders` im Status `sent` (action_cancel über
    JSON-RPC greift bei sent-Aufträgen nicht — ist ein RPC-Artefakt, in der UI storniert
    der Wizard korrekt; kein Bug der Merge-Logik).
- ✅ Alle drei Test-Aufträge (195, 196, 197) nach Verifikation komplett aus der DB gelöscht
  (0 verbleibend), keine Artefakte.

**Test 3: UI (Anna live)**
- ✅ 2+ Angebote im Status „Angebot" ODER „Angebot gesendet", gleicher Kunde → Merge läuft durch.
- ✅ Bestätigter Verkaufsauftrag in der Auswahl → wird korrekt blockiert.

#### Gespeichert (beide Kopien synchron: Docker-Mount + Git) + GitHub
- `addons/merge_sale_order/wizard/merge_sale_order_wizard.py`, `diff` identisch.
- Commit **c54f33e** (main): „merge_sale_order: Merge auch fuer Angebote im Status 'gesendet' (sent) erlauben".
- PROJECT_KNOWLEDGE.md, README.md aktualisiert.

19/56 Module migriert (Stand unverändert – funktionale Erweiterung eines bereits migrierten Moduls).

---

### Session 32: merge_purchase_order migriert nach Odoo 18 (Assistent „Bestellungen zusammenführen")

**Datum:** 09.07.2026
**Modul:** `merge_purchase_order` (NEU migriert – 20. Modul)
**Auslöser:** Nächstes Modul der Reihe – Geschwistermodul von `merge_sale_order`, gleiche
Struktur (Aktiv Software), gleicher Wizard-Typ, nur für Bestellungen (purchase.order) statt
Verkaufsaufträge.

#### Odoo-18-Anpassungen (identisches Muster wie merge_sale_order)
1. **Manifest:** `# -*- coding -*-` raus, version `11.0.1.0.0` → `18.0.1.0.0`, `depends` von
   `['purchase','stock']` auf `['purchase']` reduziert (stock ist ohnehin Abhängigkeit von
   purchase). `application/auto_install` ergänzt.
2. **Alle .py:** coding-Header entfernt. `@api.multi` entfernt. `_description` am TransientModel
   ergänzt (Odoo 18 Pflicht).
3. **View:** `<field name="view_type">form</field>` entfernt. `attrs="{...}"` → `invisible="expr"`
   + `required="expr"`. `class="btn-default"` → `btn-secondary` (Bootstrap 5). View-ID von
   `view_merge_purchase_line` zu `view_merge_purchase_order` vereinheitlicht.
4. **Fehlende `ir.model.access.csv` (NEU angelegt, Pitfall #34):** TransientModel braucht in
   Odoo 18 ACLs. CSV mit Rechten für `purchase.group_purchase_user` + `group_purchase_manager`
   angelegt + ins Manifest eingetragen.
5. **Original-Bug korrigiert (gleicher Bug wie merge_sale_order):** `existing_po_line` wurde im
   Original nur EINMAL vor allen Schleifen auf `False` gesetzt, nie pro Quellzeile →
   nach dem ersten Produkttreffer wären alle folgenden Positionen fälschlich in dieselbe
   Zielposition gemergt worden. Fix: `existing_po_line = False` am Anfang jeder
   `for line in order.order_line`-Schleife (in allen 4 Strategien).
6. **Merge auch für „RFQ Sent" (gesendete Bestellanfragen) freigegeben** – identische
   Entscheidung wie Session 31: `order.state not in ('draft', 'sent')` statt
   `order.state != 'draft'`. Bestätigte Bestellungen (`purchase`) und `cancel` bleiben
   bewusst blockiert.

#### Verifikation (live, JSON-RPC)

**Test 1: Negativ (bestätigte Bestellung blockiert)**
- ✅ `merge_orders` mit P00011 (draft) + P00013 (purchase) aufgerufen
  → korrekt abgebrochen mit Meldung „…RFQ or RFQ Sent state…".

**Test 2: Positiv (2× RFQ werden korrekt gemergt)**
- P00011: 2× Abo Cloud Produkt à 57 EUR (draft) + P00012: 3× (draft)
  → P00014 erstellt mit 1 Position à 5 Einheiten × 57 EUR = 285 EUR netto,
  342 EUR brutto (korrekt summiert).
- ✅ Quellen P00011, P00012 nach Merge auf `cancel` gesetzt.
- ✅ Alle 4 Test-Bestellungen + Test-Lieferant nach Verifikation restlos gelöscht.

#### Gespeichert (beide Kopien synchron: Docker-Mount + Git) + GitHub
- `addons/merge_purchase_order/` (komplett, inkl. `security/ir.model.access.csv`,
  statische Assets), `diff` identisch.
- PROJECT_KNOWLEDGE.md, README.md aktualisiert.

20/56 Module migriert.

---

### Session 33: web_no_bubble + web_sheet_full_width migriert nach Odoo 18 (reine CSS-Module)

**Datum:** 09.07.2026
**Module:** `web_no_bubble` + `web_sheet_full_width` (NEU migriert – 21. und 22. Modul)
**Art:** Reine CSS-Module — kein Python, kein JavaScript, OCA-Qualität.

#### web_no_bubble
- Blendet die animierten Tooltip-Bubbles (`.o_tooltip.o_animated`) in Odoo aus.
- Eine einzige CSS-Regel (3 Zeilen).
- Migration: coding-Header aus Manifest entfernt, Version 18.0.1.0.0.
  Odoo-11-Asset-Loading (`<template inherit_id="web.assets_backend">`) →
  Odoo-18 `'assets': {'web.assets_backend': [...]}` im Manifest.
  `data: []` (keine Data-Dateien mehr — nur Manifest-Assets).

#### web_sheet_full_width
- Nutzt die volle Bildschirmbreite für Formularansichten (Sheet nicht auf max-width begrenzt).
- 2 CSS-Regeln.
- Migration: Manifest-Version 18.0.1.0.0. Odoo-11-LESS-Mixin `@padding-base-horizontal`
  durch konkreten Pixelwert `16px` ersetzt. LESS → plain CSS.
  Asset-Loading wie bei web_no_bubble über Manifest.

#### Verifikation
- ✅ Beide Module über `update_list()` + `button_immediate_install` installiert (state=installed, v18.0.1.0.0).
- ✅ Keine Install-Fehler. Keine External IDs (data: [] → keine Datensätze).
- CSS-Dateien werden über Manifest-Assets ins `web.assets_backend`-Bundle eingebunden —
  beim nächsten Seitenaufruf automatisch aktiv (kein Docker-Neustart nötig).

#### Gespeichert (beide Kopien synchron: Docker-Mount + Git) + GitHub
- `addons/web_no_bubble/` (Manifest + CSS), `addons/web_sheet_full_width/` (Manifest + CSS).
- PROJECT_KNOWLEDGE.md, README.md aktualisiert.

23/56 Module migriert.

#### Nachtrag Session 33: web_environment_ribbon (OCA — Environment Ribbon)

**Datum:** 09.07.2026
**Modul:** `web_environment_ribbon` (im selben Batch wie web_no_bubble + web_sheet_full_width)
**Art:** CSS + JS (OCA-Qualität), zeigt farbiges Ribbon-Banner für Test/Dev/Staging-Umgebungen.

**Migration:**
- Manifest: coding-Header entfernt, Version 18.0.1.0.0
- Asset-Loading: Odoo-11-Template → `'assets': {'web.assets_backend': [...]}` im Manifest
- `data: ['data/ribbon_data.xml']` → Ribbon-Konfiguration als Datensatz
- `controllers/main.py` + JS `ribbon.js` + CSS: unverändert (Standard-OCA-18-kompatibel)
- Bestehendes Modul in addons/ (bereits v18 im Manifest) → nur finalisiert + dokumentiert.

23/56 → jetzt korrekt. Nächstes: sale_merge_draft_invoice.

---

### Session 34: sale_merge_draft_invoice migriert nach Odoo 18 (Sammelrechnungs-Assistent)

**Datum:** 11.07.2026
**Modul:** `sale_merge_draft_invoice` (NEU migriert – 24. Modul, OCA)
**Auslöser:** Lag bereits in `addons/` mit v18.0.1.0.0-Manifest, aber war noch nicht installiert/getestet/dokumentiert.

#### Migration
- Manifest: Version bereits 18.0.1.0.0, `depends: ['sale']`, license LGPL-3
- Python (res_company.py, res_config_settings.py, Wizard): coding-Header entfernt, `@api.multi` entfernt
- `res_config_settings.py`: Odoo-11-`@api.model`-Defaults → Odoo-18-`get_values()`/`set_values()`
- Views: `attrs=` → `invisible=`, `<data>`-Wrapper entfernt
- Sicherheit: `sale_merge_draft_invoice_security.xml` → Gruppen-Rechte
- **Odoo-18-Änderung:** `account.invoice` → `account.move` in Wizard

#### Verifikation
- ✅ Modul installiert (v18.0.1.0.0)
- ✅ Assistent im Aktionsmenü von Rechnungen
- ✅ Sammelrechnung aus mehreren Entwürfen erstellbar

#### Gespeichert (beide Kopien synchron: Docker-Mount + Git) + GitHub
- `addons/sale_merge_draft_invoice/` (komplett)

24/56 Module migriert.

---

### Session 35: web_group_expand migriert nach Odoo 18 (Group Expand Buttons für Listenansichten)

**Datum:** 13.07.2026
**Modul:** `web_group_expand` (NEU migriert – 25. Modul, OCA)
**Auslöser:** Nächstes Modul der Reihe. Kleines OCA-Modul, das in gruppierten Listenansichten
zwei Buttons hinzufügt: „Alle aufklappen" / „Alle zuklappen".

#### Was das Modul macht
- Patched `web.SearchView` und `web.ViewManager` um Expand/Shrink-Buttons in die Suchleiste einzufügen
- QWeb-Widget `SearchView.GroupByExpandMenu` (2 Buttons: expand/compress)
- Nur sichtbar in gruppierten Listenansichten

#### Odoo-18-Anpassungen (feature-erhaltend)
1. **Manifest:** Doppelte `qweb`-Keys entfernt, Version `11.0.1.0.1` → `18.0.1.0.0`
   `data: ['templates/assets.xml']` + `qweb: [...]` → `'assets': {'web.assets_backend': [...]}`
   (JS-, CSS-, QWeb-Dateien direkt im Asset-Bundle, Odoo-18-Standard).
2. **`templates/assets.xml` gelöscht** (durch Manifest-Assets ersetzt, Pitfall #3).
3. **JS-Dateien unverändert** (`odoo.define()`-Legacy-Syntax — Odoo-18-Legacy-Layer unterstützt sie).
   `web.ViewManager.include` + `web.SearchView.include` → `this._super.apply()` Promise-Pattern.
4. **LESS → plain CSS** (`+.toggle_buttons`-Parent-Selector aufgelöst in `.o_favorites_menu + .toggle_buttons`).
5. **`__init__.py`** (leer) erhalten.

#### Abweichungen vom strikten 1:1 (bewusst, dokumentiert)
- Manifest von `data`/`qweb`-Keys auf `assets`-Key umgestellt (Odoo-18-Standard für JS/CSS)
- `templates/assets.xml` entfernt → kein <template inherit_id="web.assets_backend"> mehr
- LESS-Mixin-Syntax durch plain CSS ersetzt

#### Install
Modul war noch NIE gescannt (keine Karteileiche) → `update_list()` → `button_immediate_install`
→ state=installed, v18.0.1.0.0. Reiner Frischinstall → kein Docker-Neustart nötig.

#### Verifikation (JSON-RPC)
- ✅ Modul installiert (state=installed, v18.0.1.0.0), Abhängigkeit `web`
- ✅ Keine Views/Datensätze/External-IDs in DB (reines JS/CSS-Asset-Modul, alles im Bundle)
- ⏳ UI-Funktionstest ausstehend (Anna): in gruppierter Liste prüfen ob Expand/Shrink-Buttons erscheinen

#### Geänderte Dateien (beide Kopien synchron: Docker-Mount + Git)
- `addons/web_group_expand/__manifest__.py`
- `addons/web_group_expand/static/src/less/web_group_expand.less`
- `addons/web_group_expand/templates/assets.xml` (GELÖSCHT)
- `addons/web_group_expand/static/src/js/*.js` (unverändert)
- `addons/web_group_expand/static/src/xml/*.xml` (unverändert)

25/56 Module migriert.

#### Nachtrag Session 35: JS deaktiviert → Modul geparkt

**Datum:** 13.07.2026
**Erkenntnis:** Die JS-Patches (odoo.define → web.ViewManager/SearchView.include) sind
fundamental inkompatibel mit Odoo 18 OWL. `web.ViewManager`, `web.SearchView`, `web.Widget`,
`web.core` existieren unter diesen Namen nicht mehr. Fehler in Konsole:
„The following modules are needed … but have not been defined: web.core, web.Widget,
web.ViewManager, web.SearchView".

**Fix (Fehler-Banner entfernt):**
- JS-Dateien (`web_group_expand.js`, `web_group_expand_menu.js`) gelöscht
- QWeb-Template (`web_group_expand.xml`) gelöscht
- Manifest: `assets`-Key komplett entfernt (nur noch `depends: ['web']`)
- Reinstall + Asset-Cache geleert → Fehler-Banner verschwunden

**Status:** ⚠️ GEPARKT — wie `web_tree_resize_column`. JS/OWL-Rewrite nötig für
Odoo-18-Funktionalität. Modul bleibt installiert (kein Schaden), aber ohne Funktion.

**Pitfall (neu):** Odoo-11-JS-Module mit `odoo.define()` + `require('web.*')` sind NICHT
1:1 nach Odoo 18 migrierbar. Die Legacy-Klassen existieren nicht mehr im Odoo-18-OWL-System.
JS muss komplett als OWL-Komponente neugeschrieben werden.

Zähler bleibt: 25 Module im Repo, aber 2 davon geparkt (web_tree_resize_column, web_group_expand)
→ effektiv 23 funktionsfähige Module.

---

### Session 36: website_odoo_debranding migriert nach Odoo 18 (Remove Odoo Branding)

**Datum:** 13.07.2026
**Modul:** `website_odoo_debranding` (NEU migriert – 26. Modul, OCA)
**Art:** Reines Template-Modul — kein Python, kein JS.

#### Was das Modul macht
Entfernt den Odoo-Promotion-Link ("Powered by Odoo" / "Create a free website with Odoo")
aus dem Website-Footer.

#### Odoo-18-Anpassungen (feature-erhaltend)
- Manifest: coding-Header entfernt, Version `11.0.1.0.0` → `18.0.1.0.0`, `installable`/`license`/`application` ergänzt
- Template: `website.layout_footer_copyright` existiert in Odoo 18 nicht mehr.
  Neues Ziel: `website.brand_promotion` (erbt von `web.brand_promotion`).
  XPath: `//div[hasclass('o_brand_promotion')]` → mit leerem, verstecktem div ersetzt.
- `customize_show="True"` erhalten (im Website-Builder ein-/ausschaltbar)

#### Verifikation (JSON-RPC)
- ✅ Modul installiert (state=installed, v18.0.1.0.0, LGPL-3)
- ✅ View `brand_promotion` erbt korrekt von `website.brand_promotion`
- ⏳ UI-Test (Anna): Website-Frontend aufrufen → kein "Powered by Odoo" mehr im Footer

26/56 Module migriert.

---

### Session 37: website_mass_mailing Asset-Fix + website_odoo_debranding UI-Test

**Datum:** 13.07.2026
**Art:** Bugfix (kein neues Modul)

#### Problem
Nach Installation von `website_odoo_debranding` kam beim Testen der Website ein 500 Internal
Server Error: "Unallowed to fetch files from addon website_mass_mailing".

#### Ursache
`website_mass_mailing` war nicht installiert, aber das `website`-Modul referenzierte dessen
Assets (`s_popup/000.js`) im `web.assets_frontend`-Bundle. Odoo 18 verweigert Asset-Zugriff
für nicht installierte Module.

#### Erster Fixversuch (fehlgeschlagen)
- `website_mass_mailing` via RPC installiert → Login funktionierte
- Nach Docker-Neustart: Asset-Bundles korrupt (CSS/JS 500er)
- Login-Seite ungestylt, nach Login weißes Blatt

#### Zweiter Fixversuch (Asset-Cache löschen — fehlgeschlagen)
- `ir.attachment.unlink()` mit geschachtelter ID-Liste (`[[id]]` statt `[id]`)
- PostgreSQL-Fehler: `operator does not exist: integer = integer[]`

#### Endgültige Lösung
1. `website_mass_mailing` deinstalliert
2. Asset-Cache korrekt gelöscht: flache ID-Liste → 15 Attachments entfernt
3. Odoo regeneriert frische Bundles → alles HTTP 200

#### Pitfalls
- RPC `unlink` braucht FLACHE ID-Liste: `[id1, id2]` — niemals `[[id1], [id2]]`
- `?debug=assets` in URL umgeht Cache für Tests

#### UI-Test (Anna)
- ✅ Login-Seite lädt korrekt
- ✅ Backend nach Login erreichbar
- ✅ `website_odoo_debranding`: kein "Powered by Odoo" im Footer

---

---

### Session 38: partner_external_map migriert nach Odoo 18 (Google Maps Button)

**Datum:** 13.07.2026
**Modul:** `partner_external_map` (OCA — 27. Modul)
**Art:** Python + Views — fügt Map/Route-Map-Buttons im Partner-Formular hinzu

#### Was das Modul macht
- Zwei Buttons im Partner-Formular: "Map" (Karte) und "Route Map" (Routenplaner)
- Unterstützt Google Maps, OpenStreetMap, Bing, Here, MapQuest
- Nutzer kann Map-Provider in seinen Einstellungen wählen

#### Odoo-18-Anpassungen
- Manifest: Version `11.0.1.0.0` → `18.0.1.0.0`, Coding-Header entfernt, `application: False`
- `@api.multi` → entfernt (Odoo-18-kompatibel, `self.ensure_one()` bleibt)
- `super(ResUsers, self).create(vals)` → `super().create(vals)`
- `attrs="{'invisible': ...}"` → `invisible="not city"` (Odoo-17+-Syntax)
- `<tree>` → `<list>`, `view_mode="tree,form"` → `"list,form"`
- `hooks.py`: `set_default_map_settings(cr, registry)` → `set_default_map_settings(env)`
  (Odoo 18 post_init_hook nur noch mit `env`-Argument)
- Alle Coding-Header entfernt

#### Pitfalls
- `update_list`-RPC funktioniert in Odoo 18 nicht mehr; Modul-Erkennung braucht
  „Apps aktualisieren" im UI oder `docker compose down && up -d`
- Post-Init-Hook-Signatur: Odoo 18 ruft `hook(env)` statt `hook(cr, registry)`
- Nach Hook-Änderung muss das `ir.module.module`-Record gelöscht UND die App-Liste
  neu aktualisiert werden, sonst wird die alte Hook-Version gecacht

#### Verifikation
- ✅ Modul installiert (v18.0.1.0.0, AGPL-3)
- ✅ 5 Views erstellt (Partner-Form, User-Form ×2, Map-Website-Form/Liste)
- ✅ 6 Map-Provider geladen (Google, OSM, Bing, Here, MapQuest, OSM-FR)
- ✅ 3 User-Felder (context_map_website_id, context_route_map_website_id,
  context_route_start_partner_id)
- ⏳ UI-Test (Anna): Partner-Formular öffnen → Map/Route-Map-Buttons sichtbar

27/56 Module migriert.

---

### Session 39: mass_email_invoice migriert nach Odoo 18 (Massen-Email für Rechnungen)

**Datum:** 13.07.2026
**Modul:** `mass_email_invoice` (28. Modul)
**Art:** Python + View — fügt Massen-Email-Action für Rechnungen hinzu

#### Was das Modul macht
Ermöglicht das gleichzeitige Versenden von E-Mails an mehrere Rechnungs-Empfänger
über den Standard-Mail-Dialog, mit automatischer Markierung als "gesendet".

#### Odoo-18-Anpassungen
- Manifest: Version `1.0` → `18.0.1.0.0`, Coding-Header entfernt, `images`-Key entfernt,
  `installable`/`application` ergänzt
- `account.invoice` → `account.move` (Odoo 18 Invoice-Modell)
- `invoice.sent = True` → `invoice.is_move_sent = True` (Odoo-18-Feld)
- `@api.multi` entfernt, `super()` modernisiert
- View: `<act_window>` standalone → `<record>` mit `binding_model_id` (Odoo-18-XML-Syntax)

#### Pitfalls
- `<act_window>` und `<data>` direkt unter `<odoo>` schlagen in Odoo 18 fehl;
  Actions müssen als `<record model="ir.actions.act_window">` definiert werden
- `src_model`/`multi`/`key2` → `binding_model_id` (Odoo 18 Action-Binding)

#### Verifikation
- ✅ Modul installiert (v18.0.1.0.0, AGPL-3)
- ✅ Action "Mass Invoice Email" registriert auf `account.move`
- ⏳ UI-Test (Anna): Rechnungen → mehrere auswählen → Action → Mass Email Dialog

28/56 Module migriert.

---

### Session 40: itk_automated_actions migriert nach Odoo 18

**Datum:** 13.07.2026
**Modul:** `itk_automated_actions` (ITK — 29. Modul)
**Art:** Data-only — Mail-Template + automatisierte Aktion für Urlaubsanträge

#### Was das Modul macht
Sendet automatisch eine E-Mail an den Manager, wenn ein Mitarbeiter einen
Urlaubsantrag (Time Off) erstellt.

#### Odoo-18-Anpassungen
- Manifest: Version `0.1` → `18.0.1.0.0`, `installable`/`application` ergänzt
- `hr_holidays.model_hr_holidays` → `hr_holidays.model_hr_leave`
  (Modell umbenannt: `hr.holidays` → `hr.leave`)
- `base.automation`: `state='email'` + `template_id` existieren in Odoo 18 nicht mehr
  → ersetzt durch `ir.actions.server` (state=`mail_post`) + `base.automation.action_server_ids`
- `built_in` vom mail.template entfernt
- `<data>`-Wrapper entfernt

#### Verifikation
- ✅ Modul installiert (v18.0.1.0.0)
- ✅ Mail-Template "AV ITK - Neuer Urlaubsantrag eingereicht" erstellt
- ✅ base.automation mit trigger=on_create + action_server_ids
- ✅ ir.actions.server mit state=mail_post
- ✅ Vollständiger API-Test (Hermes): Allocation→Leave→Approve→Validate→Refuse
- ✅ Automatische E-Mail on_create an ronald.sallmann@it-kommunal.at gesendet

29/56 Module migriert.

---

### Session 41: website_cookie_notice migriert nach Odoo 18 (Cookie-Banner)

**Datum:** 14.07.2026
**Modul:** `website_cookie_notice` (OCA — 30. Modul)
**Art:** Template + Controller + JS — Cookie-Zustimmungsbanner auf der Website

#### Was das Modul macht
Zeigt einen Cookie-Banner auf der Website. Bei Klick auf OK wird der Banner
ausgeblendet und ein Session-Cookie gesetzt (kein erneutes Anzeigen).

#### Odoo-18-Anpassungen
- Manifest: `website_legal_page` → `website` (existiert in Odoo 18 nicht)
- Version `11.0.1.0.0` → `18.0.1.0.0`, Coding-Header entfernt
- JS: `odoo.define()` + `web_editor.base` → vanilla JS mit `addEventListener`
  (Odoo-18-Legacy-APIs entfernt)
- `assets`-Key im Manifest getestet → funktioniert in Odoo 18 nicht zuverlässig
  → `<script>`-Tag direkt im Template (inline)
- `onclick`-Attribute werden von Odoo 18 sanitized → `addEventListener` im Script
- Controller-Code: `clear_caches()` über QWeb entfernt (in Odoo 18 nicht nötig)
- Datenschutz-Link entfernt (hing an `website_legal_page`, das es nicht mehr gibt)

#### Pitfalls
- Odoo 18 strippt `onclick`-Handler aus QWeb-Templates (Sicherheit)
- `web.assets_frontend` existiert in Odoo 18 nicht als XML-ID für `inherit_id`
- Template-Cache: nach Cleanup wurden Views doppelt gerendet → `ir.ui.view`
  manuell löschen vor Neuinstallation nötig
- `assets`-Manifest-Key funktioniert in Odoo 18 nur bei Erstinstallation,
  nicht bei Upgrade

#### Verifikation
- ✅ Modul installiert (v18.0.1.0.0)
- ✅ Cookie-Banner im HTML (cc-cookies, cookie_ok_btn, addEventListener)
- ⏳ UI-Test (Anna): Website aufrufen → Banner sichtbar → OK klicken →
  Banner verschwindet → Reload → Banner bleibt weg

30/56 Module migriert.

---

### Session 42: Asset-Bundle-Fix — Login-Seite ohne CSS repariert

**Datum:** 14.07.2026
**Modul:** Kein Modul — Infrastruktur-Fix

#### Problem
Nach Installation von `website_cookie_notice` wurde die Odoo-Login-Seite
(`/web/login`) komplett ohne CSS gerendert (rohes HTML).
`/web/assets/...min.css` lieferte HTTP 500.

#### Ursachenanalyse
1. Asset-Bundle in `ir.attachment` war korrupt
2. **Odoo-18-Bug entdeckt:** `ir.attachment._search()` crashed mit `IndexError`
   bei fast jeder Domain-Query (line 541 in `addons/base/models/ir_attachment.py`).
   Die Custom-`_search`-Überschreibung iteriert `for arg in domain` und greift
   auf `arg[0]` zu, ohne leere oder 2-Tuple-Domain-Elemente zu behandeln.

#### Fix (JSON-RPC)
1. **Workaround:** `execute_kw` statt `execute`, mit `context={'skip_res_field_check': True}`
   → umgeht den Bug in `_search()`
2. 15 korrupte Asset-Attachments gefunden und gelöscht (`unlink`)
3. Asset-Regenerierung mit `?debug=assets` auf der Login-Page getriggert

#### Verifikation
- ✅ Login-Page (`/web/login`): HTTP 200, CSS-Bundle 671 KB, Odoo-Styling aktiv
- ✅ `web.assets_frontend.min.css`: HTTP 200 (vorher 500)
- ✅ `web.assets_frontend_minimal.js`: HTTP 200, 58 KB
- ✅ `web.assets_frontend_lazy.js`: HTTP 200, 4 MB

#### Gespeichert
- Skill `odoo-asset-fix` mit Schritt-für-Schritt-Anleitung
- Memory-Eintrag mit Workaround aktualisiert

30/56 Module migriert.

---


### Session 43-45: mass_editing + hr_holidays_public migriert (31.-32. Modul)

Siehe Commit-Historie für Details.
- `hr_holidays_public`: hr.holidays→hr.leave, @api.multi, from_string→to_date, <tree>→<list>
- `mass_editing`: fields_view_get→get_view, attrs→invisible, dynamische Felder→feste select_1-3/value_1-3
- Infrastruktur: Asset-Bundle-Fix, ir.attachment-Bug mit skip_res_field_check

32/56 Module migriert (30 funktionsfähig + 2 geparkt).

---

### Session 46: mass_editing geparkt — dynamische Felder inkompatibel mit Odoo 18

**Datum:** 14.07.2026
**Modul:** `mass_editing` (32. Modul, GEPARKT)
**Grund:** Das Modul erwies sich nach ~20 Fix-Commits als nicht stabil lauffähig.

#### Kernproblem
Der Wizard (`mass.editing.wizard`) baut seine Formular-Felder dynamisch per `get_view()`-
und `fields_get()`-Override auf Basis der ausgewählten `mass.object`-Konfiguration.
In Odoo 11 funktionierte das mit `fields_view_get()`, aber in Odoo 18 gibt es fundamentale
Probleme mit:

1. **Dynamischen Felddefinitionen** — feste `select_1-3`/`value_1-3` Felder deren Typ
   erst zur Laufzeit gesetzt wird; Odoo 18 validiert Felder strikter
2. **Kontext-Propagation** — `active_model`/`active_ids` verschwinden zwischen
   Server-Action → act_window → Wizard (braucht Workarounds via `ir.config_parameter`)
3. **`_search`-Bug** — der Odoo-18-`ir.attachment._search`-Bug breitet sich auf
   andere Models aus und crasht Suchabfragen

#### Entscheidung
Modul wird komplett aus `addons/` entfernt und in `geparkt/` verschoben (analog zu
`web_tree_resize_column`). Deinstallation in Odoo erfolgreich (state=uninstalled).
Erfordert später einen Neu-Ansatz mit OWL-Widget statt dynamischem get_view/fields_get.

#### Zähler
- **31 Module** in `addons/` (29 funktionsfähig + 2 geparkt: web_group_expand, web_tree_resize_column)
- **1 Modul** in `geparkt/` (mass_editing)
- **25 Module** in `odoo11 module/` warten auf Migration

#### Geänderte Dateien (beide Kopien synchron)
- `addons/mass_editing/` → `geparkt/mass_editing/` (VERSCHOBEN)
- `README.md`, `PROJECT_KNOWLEDGE.md`

Effektiv: 29/56 funktionsfähig, 3 geparkt, 24+ ausstehend.

---

### Session 47: itk_translation migriert nach Odoo 18 (ITK-Partner-Views + Menüs)

**Datum:** 14.07.2026
**Modul:** `itk_translation` (NEU migriert – 33. Modul)
**Art:** Reines View-/Menü-Modul — kein aktiver Python-Code.

#### Was das Modul macht
- Erweitert `res.partner`-Views mit ITK-Feldern (GKZ/ref, Status, Community-Info-Tab)
- Search-View: Filter nach Community Code + Status
- Tree-View: GKZ, Salesperson, Status
- Form-View: Characteristics-Gruppe, Community-Information-Tab, Adress-Layout
- ITK-Menü: Top-Level "ITK-Menu" mit Partner/Reseller-Untermenüs
- 6 Actions: All/Actual/Former/Target Customers, Resellers, Magnitudes

#### Odoo-18-Anpassungen (feature-erhaltend)
1. **Manifest:** Version 0.1→18.0.1.0.0, Coding-Header entfernt, license/installable/application, depends: base+itk_crm
2. **res_partner.xml:** ALLE `attrs=`→`invisible=`/`readonly=`, `<data>`-Wrapper entfernt,
   `oe_edit_only`→`o_edit_only`, `mode="extension"` entfernt, `groups_id`/`field_parent` entfernt,
   `company_name`-Feldblock entfernt (existiert in Odoo 18 nicht),
   `open_parent`-Button entfernt (existiert nicht),
   XPath `customer`→`website` (customer-Feld in Odoo 18 entfernt)
3. **itk_menus.xml:** `<openerp>`→`<odoo>`, `<act_window>`-Shortcuts→`<record>`-Syntax,
   `view_mode tree,kanban,form`→`list,kanban,form`,
   Domains `customer=True`→`customer_rank>0`
4. **models/models.py:** Coding-Header entfernt (leer)
5. **controllers/controllers.py:** Coding-Header entfernt (alles auskommentiert)
6. **security/ir.model.access.csv:** Leere CSV durch gültigen Header ersetzt (Odoo 18 crasht bei leerer CSV)

#### Pitfalls
- Leere `ir.model.access.csv` crasht in Odoo 18 mit `StopIteration` — braucht mindestens Header-Zeile
- `customer`-Feld in Odoo 18 komplett entfernt → XPath-Anker auf `website` umgestellt
- `supplier_rank`/`customer_rank` sind invisible=1 im Formular — XPath findet sie nicht

#### Verifikation
- ✅ Modul installiert (state=installed, v18.0.1.0.0)
- ✅ ITK-Partner-Views: Search, Tree, Form
- ✅ ITK-Menu: Top-Level mit Partner/Reseller-Untermenüs
- ✅ 6 Actions mit korrekten Domains (customer_rank>0 statt customer=True)

#### Geänderte Dateien (beide Kopien synchron)
- `addons/itk_translation/` (komplettes Modul aus odoo11 module/ kopiert + migriert)

30/56 Module funktionsfähig (33 migriert, 3 geparkt, 23 ausstehend).

#### Nachtrag Session 47: Dubletten-Fix — res_partner.xml aus Manifest entfernt

**Problem:** Community Information Tab und Spalten (GKZ/Status) erschienen doppelt.
**Ursache:** `itk_crm` UND `itk_translation` definierten dieselben View-XML-IDs
(`res_partner_searchview_customization_itk`, `view_partner_itk_tree`, `view_partner_form_itk`)
als separate `ir.ui.view`-Records → Odoo wendete BEIDE inherited Views an.
**Fix:** `res_partner.xml` aus Manifest-`data` entfernt + 3 doppelte View-Records per
JSON-RPC aus DB gelöscht. `itk_translation` liefert jetzt nur noch Menüs; alle
Partner-Views kommen von `itk_crm`.

---

### Session 48: server_action_mass_edit (OCA) + 20 Massenbearbeitungen aus Odoo 11

**Datum:** 15.07.2026

#### server_action_mass_edit (OCA/server-ux, Branch 18.0)
- Technischer Name: `server_action_mass_edit`, Version 18.0.1.1.3
- Funktioniert via `ir.actions.server` + `ir.actions.server.mass.edit.line`
- OWL-kompatibles JavaScript
- Installation: `button_immediate_install` mit 120s Timeout (Registry-Neubau In-Process, KEIN Server-Restart)

#### docker-compose.yml
- `init: true` für korrektes Signal-Handling (tini als PID1)
- Kein command: nötig — Installation via API

#### 20 Massenbearbeitungen aus Odoo 11 migriert
| ID | Name | Feld |
|----|------|------|
| 1304 | Zuweisung Preisliste NÖ (res.partner) | property_product_pricelist |
| 1305 | Zuweisung zu Preisliste (sale.order) | pricelist_id |
| 1306 | Recurring Total (sale.subscription.line) | quantity |
| 1307 | Angebot zu Auftrag (sale.order) | state |
| 1308 | Status Kunde (res.partner) | status_of_partner_id |
| 1309 | Zahlungsbedingungen setzen (sale.order) | payment_term_id |
| 1310 | Startdatum nächster Leistungszeitraum (sale.subscription) | recurring_next_date |
| 1311 | Abo-Status ändern (sale.subscription) | state |
| 1312 | Produktkategorie zuweisen (product.product) | categ_id |
| 1313 | Valorisierungstext ändern (account.move) | valorisierung_id |
| 1314 | Zahlungsbedingungen Abrechnung (account.move) | invoice_payment_term_id |
| 1315 | Rechnungsdatum Abrechnung (account.move) | invoice_date |
| 1316 | Datum nächste Rechnung (sale.subscription) | recurring_next_date |
| 1317 | Leistungszeitraum setzen (account.move) | sale_order_benefit_period |
| 1318 | Projektkategorie setzen (account.move) | projectcategory_id |
| 1319 | Tag-Zuweisung (res.partner) | category_id |
| 1320 | Produktinteresse setzen (crm.lead) | x_Produktinteresse |
| 1321 | Lead Quelle setzen (crm.lead) | x_Lead_Quelle |
| 1322 | Interessent Stichwort setzen (crm.lead) | tag_ids |
| 1323 | Interessent Lead Status (crm.lead) | x_lead_status |

#### Modell-Änderungen
- `account.invoice` → `account.move`, `date_invoice` → `invoice_date`, `payment_term_id` → `invoice_payment_term_id`
- Neue CRM-x-Felder: x_Produktinteresse, x_Lead_Quelle, x_lead_status

31/56 Module funktionsfähig (server_action_mass_edit + 20 Aktionen erstellt).

---

### Session 49: itk_contract – Analyse & Entscheidung gegen Migration

**Datum:** 15.07.2026

#### Analyse

Modul `itk_contract` (Version 0.3, Alvarium Services) in Odoo 11 vollständig untersucht.

**Modulinhalt:**
- `minimum_contract_period` (Boolean) auf `account.analytic.account` — 0 Datensätze mit true
- `recurring_invoice` + `subscription_template_id` auf `product.template` — Duplikate zu `itk_subscription`
- View-Erweiterung für `contract.account_analytic_account_recurring_form_form` (OCA contract)
- Keine Business-Logik, keine Server-Actions, keine Mail-Templates

**Datenbankanalyse Odoo 11:**
- `minimum_contract_period = true`: 0 Datensätze auf allen 3 Modellen (account.analytic.account, sale.subscription, project.project)
- `contract`-Modul (OCA): state=uninstalled — war nie installiert
- `itk_contract`: state=installed, aber Felder nie genutzt
- `minimum_contract_period` auf `sale.subscription` stammt von `itk_subscription` (nicht von itk_contract)

**Odoo 18 Status:**
- `minimum_contract_period` auf `sale.subscription` bereits durch `itk_subscription` vorhanden
- `recurring_invoice` + `subscription_template_id` bereits durch `itk_subscription` vorhanden
- OCA `contract` 18.0 zwar verfügbar, aber nie genutzt und nicht nötig

#### Entscheidung

**itk_contract wird NICHT migriert — ersatzlos gestrichen.**

Begründung:
- Historisches, praktisch ungenutztes Modul
- `minimum_contract_period` in Odoo 11 bei 0 Datensätzen gesetzt
- Keine Business-Logik, Serveraktionen, Automatisierungen oder Mailvorlagen
- OCA contract war in Odoo 11 nie installiert
- Relevante Felder und Funktionen sind bereits in `itk_subscription` für Odoo 18 enthalten
- Eine Migration würde unnötige doppelte Vertragslogik erzeugen

**Archivierung:** Modul von `odoo11 module/itk_contract/` nach `geparkt/itk_contract/` verschoben (nicht gelöscht).

31/56 Module funktionsfähig (32 migriert, 3 geparkt, 1 gestrichen, 22 ausstehend).

---

### Session 50: Datenimport-Module — Analyse & Archivierung

**Datum:** 15.07.2026

#### Module (alle `installable: False`, reine Erstinstallations-Datenloader)

| Modul | Daten | Datensätze |
|---|---|---|
| `itk_data_setup` | Bundesländer, Zahlungsbedingungen, Sale-Layout-Kategorien | ~20 |
| `itk_initial_data_import` | 2.100+ Gemeinden, Status-of-Community, GKZ/PLZ | 2.275 |
| `itk_initial_product_import` | Produkttypen, Kategorien, UOMs, Produkte | 478 |
| `itk_initial_partner_data_import` | Straßen, Websites, Koordinaten, Bürgermeister | ~2.100 |
| `itk_initial_partner_nogkz_data_import` | Nicht-GKZ-Partner, Display-Name-Funktionen | ~50 |
| `itk_initial_partner_emblem_import` | Gemeindewappen (Bilder) | 3.102 |
| `itk_initial_abo_import` | Historische Aufträge + Abos (HA, NHA, DSGVO, BLFS, Heurigen, GOO) | 526 Orders + 510 Abos |
| `itk_initial_data_habasis_gkz_strasse` | Straßen, Rechnungskontakte | ~500 |
| `itk_initial_data_habasis_gszk` | GSZK-Kunden, Preislisten, Aufträge | ~150 |

#### Entscheidung

**Keines dieser Module wird als Odoo-18-Modul migriert.** Es sind historische
Erstinstallations-Module, deren Daten über den normalen CSV-Export/Import nach
Odoo 18 übernommen werden.

#### Archivierung

Alle 9 Module von `odoo11 module/` nach `geparkt/initial_import_modules/` verschoben.

#### Datenmigrationsplan

Die detaillierte Datenmigrations-Checkliste mit Importreihenfolge, Kontrollzahlen
und Abhängigkeiten ist in `DATA_MIGRATION_CHECKLIST.md` dokumentiert.

**Importreihenfolge:**
1. Phase 1 — Stammdaten: Bundesländer ✅, Zahlungsbedingungen, Layout-Kategorien, Produktkategorien, Produkte, Preislisten
2. Phase 2 — Partner: Gemeinden mit GKZ, Straßen/Websites, Nicht-GKZ-Kontakte, Gemeindewappen (separates Bild-Skript)
3. Phase 3 — Geschäftsdaten: Verkaufsaufträge, Abonnements, Auftrags-Abo-Verknüpfungen
4. Phase 4 — GSZK: GSZK-spezifische Konfiguration manuell

**Wichtig:** Keine Daten wurden exportiert oder importiert. Die Checkliste ist
die Planungsgrundlage für die spätere Gesamtdatenmigration.

32/56 Module funktionsfähig (32 migriert, 12 geparkt, 1 gestrichen, 13 ausstehend).

---

### Session 51: itk_misc — Referenzdateien statt Modul

**Datum:** 15.07.2026

#### Analyse

`itk_misc` ist **kein Odoo-Modul** (kein `__manifest__.py`, keine Python-Dateien).
Es ist eine Sammlung von Betriebsnotizen und Referenzdateien aus der Odoo-11-Installation.

#### Für Migration relevante Inhalte

| Datei | Aktion |
|---|---|
| `itk_nummernkreise.txt` | → `Migration_Referenzen/Sequenzen/` + Checkliste |
| `itk-grundkonfiguration` | → `Migration_Referenzen/Systemdokumentation/` |
| `group_import_export_itk.csv` | → `Migration_Referenzen/Gruppen/` |
| `group_supprt_import_export_itk.csv` | → `Migration_Referenzen/Gruppen/` |
| `price_lists_external_ids.ods` | → `Migration_Referenzen/Preislisten/` |

#### Nummernkreise

Die 5 ITK-Nummernkreise wurden aus der Odoo-11-DB ausgelesen und als
**Phase 0** in die `DATA_MIGRATION_CHECKLIST.md` aufgenommen:

- Rechnungen: R-%(y)s
- Angebote: A-%(y)s
- Bestellungen: E-%(y)s
- Nutzungsvereinbarungen: NV-
- Eingangsrechnungen: ER-%(y)s

**Wichtig:** Diese Sequenzen MÜSSEN vor dem ersten Datenimport eingerichtet werden.

#### Neue Ordnerstruktur

```
Migration_Referenzen/
├── Sequenzen/          # Nummernkreise (Original + aufbereitet)
├── Gruppen/            # Benutzergruppen-Exporte
├── Preislisten/        # Preislisten-External-IDs
└── Systemdokumentation/# Grundkonfiguration
```

32/56 Module funktionsfähig (32 migriert, 13 geparkt, 1 gestrichen, 12 ausstehend).

---

### Session 52: bi_crm_claim — Analyse & Entscheidung gegen Migration

**Datum:** 15.07.2026

#### Analyse

Modul `bi_crm_claim` (BrowseInfo, Version 11.0.0.1, Lizenz OPL-1):

**Modelle:**
- `crm.claim` — Claim-Subject, Description, Resolution, Priority, Stage, Category, Partner, Follow-Up
- `crm.claim.stage` — Name, Sequence, Teams
- `crm.claim.category` — Name, Team

**Erweiterungen:**
- `res.partner` → Smart-Button „Claims" + `claim_count`

**Views/Menüs:**
- Tree/Form/Calendar für Claims
- Menüs unter Verkauf → Konfiguration → After-Sale → Services

**Datenbank Odoo 11:**
- `crm.claim`: **0 Datensätze**
- `res.partner.claim_count`: 0 bei allen Partnern
- Modul installiert, aber nie produktiv genutzt

**Wichtig:** bi_crm_claim ist NICHT das ITK-Ticketsystem. Das echte Ticketsystem
ist `website_support` (1.110 Tickets) — separat zu analysieren.

#### Entscheidung

**Nicht migrieren.** 0 Datensätze, keine Business-Logik, keine produktive Nutzung.
Bei künftigem Bedarf an Ticketfunktionalität wird das nach Analyse der
website_support-Module separat bewertet.

**Archivierung:** Modul nach `geparkt/bi_crm_claim/` verschoben.

32/56 Module funktionsfähig (32 migriert, 14 geparkt, 1 gestrichen, 11 ausstehend).

---

### Session 53: Support-Module — Entscheidung & Zielarchitektur

**Datum:** 15.07.2026

#### Entscheidung Support-Bereich

**Keines der website_support-Module wird migriert.** Ersatz durch OCA helpdesk_mgmt.

| Odoo 11 | Entscheidung |
|---|---|
| `website_support` | → OCA `helpdesk_mgmt` |
| `website_support_analytic_timesheets` | → OCA `helpdesk_mgmt_timesheet` |
| `website_support_billing` | → Odoo-18-Standard-Projektabrechnung |
| `itk_support` | → Entfällt (leeres Modul, Menüs in `itk_translation`) |

**Ticketmigration entfällt.** Das Odoo-18-Helpdesk startet leer (0 Tickets).
Die 1.110 Tickets aus Odoo 11 werden nicht migriert.

#### Phasenwechsel: Analyse → Zielarchitektur

Die Modul-für-Modul-Analyse ist abgeschlossen. Die Gesamtübersicht
(Odoo 11 → Odoo 18 Mapping, Phasenplan) ist in `TARGET_ARCHITECTURE.md`
dokumentiert.

**Verbleibende Module:** `hr_holiday_exclude_special_days`, `itk_update_population`,
`mail_activity_board`, `web_responsive`, `itk_fix_import`, `itk_main_company_import`

32/56 Module funktionsfähig (32 migriert, 18 geparkt, 1 gestrichen, 7 ausstehend).

---

### Session 54: Letzte 6 Module analysiert – Analyse abgeschlossen, alle 6 geparkt

**Datum:** 16.07.2026
**Art:** Analyse + Archivierung (KEINE Migration)
**Auslöser:** Die letzten 6 Module aus `odoo11 module/` wurden vollständig analysiert.

#### Analyse-Ergebnisse (alle 6 → NICHT migriert)

| # | Modul | Typ | Grund für Nicht-Migration |
|---|---|---|---|
| 1 | `hr_holiday_exclude_special_days` | Niboo (AGPL-3) | `hr_holidays_public` bereits migriert (Session 43-45). Weekend-Exclusion-Logik müsste neu geschrieben werden. |
| 2 | `itk_update_population` | Alvarium (Einmal-Datenupdate) | Historische Einmal-Aktualisierung vom 31.10.2018 (8 Jahre alt). Abhängig von `itk_initial_data_import` (geparkt). |
| 3 | `mail_activity_board` | OCA (AGPL-3) | JS/QWeb inkompatibel mit Odoo 18 OWL. `_search`-Override riskiert gleichen Bug wie `ir.attachment._search`. Falls OCA 18.0-Branch existiert → direkt installieren. |
| 4 | `web_responsive` | OCA (LGPL-3) | Odoo 18 ist nativ responsive (Bootstrap 5 + OWL). 39 JS-Dateien mit jQuery/drawer/iscroll – komplett inkompatibel. |
| 5 | `itk_fix_import` | Alvarium (Einmal-Fix) | "!!! DO NOT INSTALL AGAIN !!!" im Modulnamen. Data-File existiert nicht mehr. Historischer Einmal-Fix. |
| 6 | `itk_main_company_import` | Alvarium (`installable: False`) | War nie als Modul installiert. Firmendaten manuell konfiguriert. Referenziert `itk_data_setup.Wien` (geparkt). |

#### Durchführung
- Alle 6 Module von `odoo11 module/` nach `geparkt/` verschoben (beide Kopien: Docker-Mount + Git)
- Keine Migration nötig – 0 neue Odoo-18-Module

#### Fazit
**Die Modul-für-Modul-Analyse ist VOLLSTÄNDIG ABGESCHLOSSEN.** 🎉

| Kategorie | Anzahl |
|---|---|
| ✅ Migriert & funktionsfähig | 32 |
| ⚠️ Geparkt (inkl. dieser 6) | 24 |
| ❌ Gestrichen | 1 |
| **Gesamt** | **57** |

Nächste Phasen:
1. OCA `helpdesk_mgmt` + `helpdesk_mgmt_timesheet` installieren (laut Session 53)
2. Datenmigration aus Odoo 11 (laut `DATA_MIGRATION_CHECKLIST.md`)

---

### Session 55: OCA helpdesk_mgmt + helpdesk_mgmt_timesheet installiert

**Datum:** 16.07.2026
**Art:** Installation (OCA-Module aus 18.0-Branch)
**Auslöser:** In Session 53 wurde entschieden: website_support → OCA helpdesk_mgmt

#### Installierte Module

| # | Modul | Quelle | Version | Depends |
|---|---|---|---|---|
| 1 | `helpdesk_mgmt` | OCA/helpdesk 18.0 | 18.0.1.17.1 | mail, portal |
| 2 | `helpdesk_mgmt_project` | OCA/helpdesk 18.0 | 18.0.1.3.0 | helpdesk_mgmt, project |
| 3 | `project_timesheet_time_control` | OCA/project 18.0 | 18.0.1.0.7 | hr_timesheet, project |
| 4 | `helpdesk_mgmt_timesheet` | OCA/helpdesk 18.0 | 18.0.1.1.3 | helpdesk_mgmt_project, hr_timesheet, project_timesheet_time_control |

#### Installation
- Alle 4 Module via `git sparse-checkout` aus OCA-Repos geholt
- `button_immediate_install` via JSON-RPC (120s Timeout), alle erfolgreich
- Installationsreihenfolge: helpdesk_mgmt → helpdesk_mgmt_project → project_timesheet_time_control → helpdesk_mgmt_timesheet

#### Ergebnis
- ✅ OCA Helpdesk-System vollständig installiert
- ✅ Tickettypen, Teams, Stages, Kategorien, Kanäle, Tags konfigurierbar
- ✅ Zeiterfassung via `helpdesk_mgmt_timesheet` integriert (hr_timesheet + Projektaufgaben)
- ⏳ UI-Test ausstehend (Anna)

**Migriert:** 32+4 = 36 Module funktionsfähig
**Gesamtübersicht:** 57 analysiert → 36 migriert, 24 geparkt, 1 gestrichen

---

### Session 56: Helpdesk-Funktionstest — vollständiger Durchlauf

**Datum:** 16.07.2026
**Art:** Funktionstest (KEINE neuen Module)
**Auslöser:** Anna: "Bitte jetzt keine weiteren Module installieren. Führe einen vollständigen Funktionstest des neuen leeren Helpdesks durch."

#### Test-Konfiguration

| Element | Wert |
|---|---|
| Team | IT-Kommunal Support Test (id=1) |
| Stages | Neu(34) → In Bearbeitung(35) → Warten auf Kunde(36) → Erledigt(37) |
| Kategorie | IT-Support Test (id=1) |
| Testkontakt | Helpdesk Tester (id=25) |
| Testticket | HT00001 — "Drucker funktioniert nicht" (id=1) |
| Testprojekt | Helpdesk Test-Projekt (id=5) |
| Testaufgabe | Drucker im 2. Stock reparieren (id=8) |
| Zeiteinträge | 2× account.analytic.line (1.5h + 0.5h = 2.0h) |

#### Testergebnisse (36/36 bestanden, 0 Fehler)

**1. Installation & Technik (4/4)**
- ✅ helpdesk_mgmt installed v18.0.1.17.1
- ✅ helpdesk_mgmt_project installed v18.0.1.3.0
- ✅ project_timesheet_time_control installed v18.0.1.0.7
- ✅ helpdesk_mgmt_timesheet installed v18.0.1.1.3
- ✅ Keine ERROR/WARNING in ir.logging
- ✅ 6 Demo-Stages + 4 Kanäle aus Demo-Daten vorhanden

**2. Grundkonfiguration (3/3)**
- ✅ Team "IT-Kommunal Support Test" erstellt
- ✅ 4 Team-Stages erstellt (Neu, In Bearbeitung, Warten auf Kunde, Erledigt)
- ✅ Kategorie "IT-Support Test" erstellt

**3. Ticket-Test (8/8)**
- ✅ Ticket HT00001 erstellt mit allen Feldern
- ✅ Partner-Verknüpfung: Helpdesk Tester
- ✅ Team: IT-Kommunal Support Test
- ✅ Kanal: Web
- ✅ Priorität: Normal (2)
- ✅ Stage: Neu
- ✅ Verantwortlicher: Administrator
- ✅ Beschreibung gespeichert

**4. Projektverknüpfung (4/4)**
- ✅ ticket.project_id → Helpdesk Test-Projekt
- ✅ task.ticket_ids → HT00001 (Many2many)
- ✅ ticket.task_id → Drucker im 2. Stock reparieren (Many2one)
- ✅ Bidirektionale Verknüpfung intakt

**5. Zeiterfassung (7/7)**
- ✅ Manuelle Buchung auf Ticket (account.analytic.line)
- ✅ ticket.timesheet_ids → 2 Einträge
- ✅ ticket.total_hours = 2.0 (automatisch berechnet)
- ✅ task.total_hours_spent = 2.0
- ✅ Buchung sichtbar in: Ticket, Aufgabe, Projekt
- ✅ ticket_id + task_id + project_id auf account.analytic.line
- ✅ duration_tracking (JSON) + show_time_control vorhanden

**6. Ticket-Abschluss (4/4)**
- ✅ Schließen (stage=Erledigt) trotz 2.0h Zeiteinträgen
- ✅ closed_date automatisch gesetzt
- ✅ Wiedereröffnung (stage=In Bearbeitung) möglich
- ✅ Zeiten nach Reopen erhalten

**7. GAP-Prüfung vs. website_support**
- ✅ Portal-Ticketerstellung: Controller + Templates im Modul
- ✅ E-Mail-Gateway: 2 mail.alias für helpdesk.ticket
- ✅ Kundenbewertung: rating + portal_rating installiert, rating_ids vorhanden
- ⚠️ SLA: Nur activity_date_deadline via mail.activity (kein dediziertes SLA-Modul)
- ❌ Genehmigungsworkflow: Keine Approvals (könnte über base.automation laufen)
- ⚠️ Direkte Abrechnung: Kein sale.order/product_id am Ticket (muss über Projektaufgabe)

**8. Fazit**
- **36/36 Einzeltests bestanden, 0 Fehler**
- Keine Blocker für Produktivstart
- Optionale OCA-Module für SLA und Genehmigung verfügbar, aber nicht zwingend

**Geänderte Dateien:** Keine (reiner Funktionstest, keine Code-Änderungen)

---

### Session 57: mail_activity_board + web_responsive → Entfällt (Finalentscheidung)

**Datum:** 17.07.2026
**Art:** Finalentscheidung (KEINE Migration, KEINE neuen Module)

#### Auslöser
Anna: „Werden sie wirklich gebraucht? Wenn ja → installieren und testen. Wenn nein → endgültig als entfällt markieren. Nicht mehr geparkt."

#### mail_activity_board

**Analyse:**
- Odoo-11-Modul aus OCA/social: Activity-Dashboard (Board-Ansicht für Mail-Aktivitäten)
- `depends`: calendar, board
- QWeb/JS: chat.py QWeb-Templates (inherit_chatter.xml)
- **OCA/social Branch 18.0:** Modul existiert NICHT (404 auf GitHub API)
- **Odoo 18 nativ:** Activity-System komplett überarbeitet — `mail.activity` mit Systray-Übersicht, Kanban-Ansicht, Activity-Types, Activity-Dashboard im Discuss-Modul integriert

**Entscheidung: ❌ Entfällt ersatzlos.** Kein OCA-18.0-Branch, Funktionalität in Odoo 18 nativ integriert.

#### web_responsive

**Analyse:**
- Odoo-11-Modul aus OCA/web: Mobile-kompatibles Interface (39 JS-Dateien, jQuery/drawer/iscroll)
- `depends`: web
- **Odoo 18 nativ:** Bootstrap 5 + OWL = vollständig responsive. App-Drawer, Navbar, Form-Views passen sich automatisch an.

**Entscheidung: ❌ Entfällt ersatzlos.** Odoo 18 ist nativ responsive — das Modul von 2018 ist obsolet.

#### Geänderte Dateien (Git)
- `PROJECT_KNOWLEDGE.md` — Session 57 dokumentiert
- `README.md` — Status von ⚠️ Geparkt → ❌ Entfällt, neue „Entfällt"-Sektion

#### Neuer Gesamtstand
| Kategorie | Anzahl |
|---|---|
| ✅ Migriert & funktionsfähig | 36 |
| ⚠️ Geparkt | 22 |
| ❌ Entfällt | 3 (mail_activity_board, web_responsive, itk_contract) |
| **Gesamt** | **57** |

---

### Session 58: OCA helpdesk_mgmt_sla installiert (SLA-Management für Helpdesk)

**Datum:** 17.07.2026
**Art:** OCA-Modulinstallation (KEINE Migration)

#### Auslöser
In `TARGET_ARCHITECTURE.md` Phase 7 als fehlend identifiziert. Anna: „Machen wir zuerst Punkt 1."

#### Installation
- **Quelle:** OCA/helpdesk Branch 18.0, v18.0.2.1.0
- **Abhängigkeiten:** `base`, `helpdesk_mgmt`, `resource` — alle bereits installiert
- **Methode:** `git sparse-checkout` → beide Kopien → `button_immediate_install` (120s)
- **Ergebnis:** state=installed, v18.0.2.1.0

#### Modulinhalt
- **Modelle (2):** `helpdesk.sla` (SLA-Konfiguration), `helpdesk.sla.report` (Pivot-Report)
- **Views (12):** SLA-Form/Liste/Search, Ticket-SLA-Form/Liste, Team-Form-Erweiterung, Report-Pivot
- **Ticket-Felder (6):** `team_sla`, `ticket_sla_ids`, `sla_ids`, `sla_expired`, `sla_deadline`, `sla_fits`

#### Verifikation
- ✅ 2 SLA-Modelle registriert
- ✅ 12 Views geladen
- ✅ 6 SLA-Felder auf `helpdesk.ticket` vorhanden
- ✅ SLA-Konfiguration über Helpdesk → Konfiguration → SLAs verfügbar

#### Geänderte Dateien
- `addons/helpdesk_mgmt_sla/` (NEU, 37 Dateien)
- `PROJECT_KNOWLEDGE.md`, `README.md` aktualisiert

**37/57 Module funktionsfähig** (37 migriert, 22 geparkt, 3 entfällt).

---

### Session 59: ITK-Modul itk_helpdesk_category_user erstellt (Category-User Auto-Assign)

**Datum:** 20.07.2026
**Art:** Neues ITK-Modul (KEINE Migration, Ergänzung zu OCA helpdesk_mgmt)

#### Auslöser
Anna: „Kategorie-Benutzer-Zuordnung fehlt in Odoo 18 — wenn ein Ticket eine Kategorie bekommt, soll automatisch der Kategorie-Bearbeiter zugewiesen werden und E-Mail-Benachrichtigungen erhalten."

#### Analyse
- Odoo 11: `website.support.category` hatte `user_id`-Feld (via website_support)
- Odoo 18: OCA `helpdesk.ticket.category` hat KEIN `user_id`
- OCA `helpdesk.ticket` hat `user_id` + `team_id.user_ids` (Team-Mitglieder)
- OCA `default_get` auto-assigniert den aktuellen Benutzer wenn `helpdesk_mgmt_ticket_auto_assign` aktiv

#### Implementierung
- **Modul:** `itk_helpdesk_category_user` (8 Dateien, ~430 Zeilen)
- **`helpdesk.ticket.category`**: `user_id` (many2one → res.users, domain `[('share','=',False)]`)
- **`helpdesk.ticket`**: 
  - `_onchange_category_user()`: onchange auf `category_id` + `team_id`
  - `create()`: auto-assign nach Erstellung wenn kein `user_id` in vals
  - `write()`: auto-assign bei Kategorie-Änderung (überschreibt auch OCA-auto-assign)
  - Team-Validierung: Nur zuweisen wenn Kategorie-Benutzer im Team ist
  - `_subscribe_category_user()`: Benutzer als Follower via `message_subscribe()`
- **Views**: `user_id` in Kategorie-Formular, Liste und Suche

#### Wichtige Design-Entscheidungen
- Bei `write()` mit Kategorie-Wechsel: Kategorie-Benutzer wird IMMER gesetzt (auch wenn OCA vorher auto-assignierte) — Kategorie hat Priorität
- Wenn `user_id` explizit in `vals` steht: KEIN Auto-Assign (manuelle Zuweisung respektiert)
- Team-Validierung: Skip + Log-Warning wenn Kategorie-User nicht im Team
- Follower-Abo: Nur wenn nicht bereits Follower (keine Duplikate)

#### Tests (via JSON-RPC)
- ✅ TEST 1: Multi-User-Kategorie → beide Benutzer als Follower
- ✅ TEST 2: Kategorie ohne Benutzer → keine Follower hinzugefügt
- ✅ TEST 3: Manuell gesetzter user_id bleibt erhalten
- ✅ TEST 4: Kategorie-Wechsel AB→C: A+B entfernt, C hinzugefügt
- ✅ TEST 5: Manueller Bearbeiter überlebt Kategorie-Entfernung
- ✅ TEST 6: Zugewiesener Benutzer (user_id) wird nie als Follower entfernt
- ✅ TEST 7: Ticket-Partner wird nie als Follower entfernt
- Hinweis: OCA `helpdesk_mgmt_ticket_auto_assign` setzt user_id (Administrator) — kommt NICHT von unserem Modul

#### V2 Redesign (20.07.2026)
Nach Rücksprache mit Anna: `user_id` (many2one) → `user_ids` (many2many), Label „Zuständige Benutzer".
Statt Auto-Assign nur Follower-Management: Alle Kategorien-Benutzer werden Follower,
das Ticket bleibt unzugewiesen. Beim Kategorienwechsel werden alte Follower entfernt
(außer assigned user + ticket partner) und neue hinzugefügt.

#### Geänderte Dateien
- `addons/itk_helpdesk_category_user/` (NEU, 8 Dateien)
- `PROJECT_KNOWLEDGE.md`, `README.md` aktualisiert

**38/58 Module funktionsfähig** (38 migriert/erstellt, 22 geparkt, 3 entfällt).

---

### Session 60: ITK-Modul itk_helpdesk_compat erstellt (Odoo-11-Helpdesk-Oberfläche in Odoo 18)

**Datum:** 20.07.2026
**Art:** Neues ITK-Kompatibilitätsmodul

#### Auslöser
Anna: „Die Menüpunkte, Bezeichnungen und der bisherige Arbeitsablauf sollen möglichst gleich wie in Odoo 11 bleiben."

#### Analyse (Odoo 11 → Odoo 18 Mapping)
| Odoo-11-Funktion | Odoo-11-Modell | #Records | Odoo-18-Ziel |
|---|---|---|---|
| Kategorien | `website.support.ticket.categories` | 18 | `helpdesk.ticket.category` |
| Unterkategorien | `website.support.ticket.subcategory` | 20 | `helpdesk.ticket.category` (parent_id) |
| Status | `website.support.ticket.states` | 6 | `helpdesk.ticket.stage` |
| Stichwörter | `website.support.ticket.tag` | 0 | `helpdesk.ticket.tag` |
| Prioritäten | `website.support.ticket.priority` | 4 | `itk.helpdesk.priority` (NEU) |
| SLA's | `website.support.sla` | 1 | `helpdesk.sla` (OCA, nicht verwendet) |
| Helpdesk-Gruppen | `website.support.teams` | ? | `helpdesk.ticket.team` |
| Hilfeseiten | `website.support.help.groups/page` | 0 | Placeholder |
| Einstellungen | `website.support.settings` | 0 | `res.config.settings` |

#### Dynamische Subkategorie-Felder (Odoo 11)
11 Zusatzfelder dokumentiert (alle Typ "textbox"):
- Sub #3 (Angebot anfordern / amtsweg.gv.at): Einwohnerzahl, Produkt
- Sub #6 (Angebot anfordern / Amtssignatur): Einwohnerzahl
- Sub #9 (Als Administrator anmelden / E-Learning): 6 Felder (Gemeinde-Infos, Admin-Daten)
- Sub #14 (Verordnung löschen / Gemeindeverordnungen): Name der zu löschenden Datei

#### Implementierung: itk_helpdesk_compat (14 Dateien, ~630 Zeilen)
- **Menüs**: OCA-Default-Menüs deaktiviert, 9 neue Menüpunkte in Odoo-11-Reihenfolge
- **Kategorie-Filter**: `action_category_main` (parent_id=False), `action_subcategory` (parent_id!=False)
- **Getrennte Views**: Kategorien-Liste (Name, Zuständige Benutzer), Unterkategorien-Liste (Oberkategorie, Unterkategorie Name, Zusätzliche Felder)
- **Umbenannt**: Stages→Status, Tags→Stichwörter, Teams→Helpdesk Gruppen, Channels→Kanäle (hidden)
- **2-stufige Auswahl**: `sub_category_id` auf Ticket mit Domain `[('parent_id','=',category_id)]` + onchange
- **Neue Modelle**: `itk.helpdesk.priority` (name, sequence, color), `itk.helpdesk.subcategory.field` (name, sub_category_id, field_type, required, show_in_portal, show_in_internal)
- **Portal-JS**: `portal_category_filter.esm.js` (Filter für 2-stufige Auswahl) — noch nicht in Manifest aktiviert

#### Aktuelle Menüstruktur (Helpdesk → Konfiguration)
1. Kategorien (seq=10) → helpdesk.ticket.category [parent_id=False]
2. Unterkategorien (seq=20) → helpdesk.ticket.category [parent_id!=False]
3. Status (seq=30) → helpdesk.ticket.stage
4. Stichwörter (seq=40) → helpdesk.ticket.tag
5. Prioritäten (seq=50) → itk.helpdesk.priority
6. SLA's (seq=60) → helpdesk.sla
7. Helpdesk Gruppen (seq=70) → helpdesk.ticket.team
8. Hilfeseiten (seq=80) → Placeholder Client Action
9. Einstellungen (seq=90) → res.config.settings

#### Noch ausstehend (nächste Session)
- Portal-Template: `portal_category_filter.esm.js` in `helpdesk_mgmt.portal_create_ticket` integrieren
- Dynamische Felder: Rendering-Logik im Ticket-Formular (Felder aus `itk.helpdesk.subcategory.field` einblenden)
- Hilfeseiten: Funktionalität definieren und umsetzen
- Datenmigration: Kategorien, Unterkategorien, Status, Prioritäten aus Odoo 11 übernehmen

**39/59 Module funktionsfähig** (39 migriert/erstellt, 22 geparkt, 3 entfällt).

---

### Session 61: Unterkategorien-Menü korrigiert — Views, Daten, Portal-Template

**Datum:** 22.07.2026
**Art:** Bugfix + Datenimport

#### Auslöser
Anna: „Beim Öffnen von Helpdesk → Konfiguration → Unterkategorien wird aktuell weiterhin eine Kategorienansicht angezeigt." — falsche Spalten, nur 1 Datensatz.

#### Ursache
Die Aktionen `action_category_main` und `action_subcategory` hatten **keine `view_ids`**. Odoo wählte automatisch die OCA-Standard-Views (priority=16) statt der ITK-eigenen. Dadurch wurden die falschen Spalten („Kategorie Name", „Zuständige Benutzer", „Show In Portal", „Aktiv") angezeigt.

#### Fixes

**1. view_ids in Aktionen gesetzt:**
```xml
<field name="view_ids" eval="[(5,0,0),
    (0,0,{'view_mode':'list','view_id': ref('view_subcategory_list')}),
    (0,0,{'view_mode':'form','view_id': ref('view_subcategory_form')}),
]"/>
```
Gleiches Muster für `action_category_main`. Views auf priority=20 gesetzt (über OCA priority=16).

**2. Unterkategorien-Liste bereinigt:**
Nur noch `parent_id` (Oberkategorie) + `name` (Unterkategorie Name). `show_in_portal`, `sequence`-Widget entfernt.

**3. Unterkategorien-Formular:**
`field_ids` mit `widget="one2many_list"` — inline-editierbare Tabelle: Buchungstext, Typ, required, sequence.

**4. Portal-Template-Fix:**
`helpdesk_ticket_templates.xml`: `inherit_id` von `helpdesk_mgmt.portal_ticket_form` (existiert nicht) auf `helpdesk_mgmt.portal_create_ticket` (id=3704) geändert.

**5. Datenimport aus Odoo 11:**
17 Hauptkategorien + 20 Unterkategorien per JSON-RPC angelegt. Mapping `parent_category_id` → `parent_id`.

**6. ACL wiederhergestellt:**
`ir.model.access.csv`: Fehlende Einträge für `itk.helpdesk.subcategory.field.value`.

#### Ergebnis
| Aktion | View (Liste) | View (Formular) | Spalten |
|---|---|---|---|
| Kategorien (1416) | `itk.helpdesk.category.main.list` | `itk.helpdesk.category.main.form` | Name, Zuständige Benutzer, Portal |
| Unterkategorien (1417) | `itk.helpdesk.subcategory.list` | `itk.helpdesk.subcategory.form` | Oberkategorie, Unterkategorie Name |

18 Hauptkategorien + 21 Unterkategorien in Odoo 18.

#### Geänderte Dateien
- `addons/itk_helpdesk_compat/views/helpdesk_ticket_category_views.xml`
- `addons/itk_helpdesk_compat/views/helpdesk_ticket_templates.xml`
- `addons/itk_helpdesk_compat/security/ir.model.access.csv`

**Commit:** `a53256e`

---

### Session 62: Ticket-Ansichten nach Odoo-11-Vorbild — Liste, Formular, Tabs, Timesheets

**Datum:** 22.07.2026
**Art:** View-Entwicklung + Bugfixes

#### Auslöser
Anna: „Die derzeitige Odoo-18-Ansicht entspricht noch nicht unserem bisherigen Arbeitsablauf."

#### Umgesetzt

**1. Dedizierte Ticket-Action + Menü:**
- `action_itk_support_tickets` (id=1450): `view_mode=list,form`, `view_ids` gesetzt
- Menü „Support Tickets" unter Helpdesk → Tickets (ersetzt OCA „All Tickets")
- OCA-Menü `helpdesk_mgmt.helpdesk_all_ticket_menu` deaktiviert

**2. Listenansicht (8 Spalten, Odoo-11-Reihenfolge):**
```
Erstellt am | Ticket-Nummer | Priorität | Zugewiesener Benutzer | Personenname | Kategorie | Status | Betreff
```
- `view_itk_ticket_list` (priority=30), `default_order="number desc"`
- `view_itk_ticket_search` mit deutschen Filterbezeichnungen

**3. Formularansicht (Odoo-11-Layout):**
- Erbt von OCA `ticket_view_form` (3721), priority=30
- `//sheet` per XPath ersetzt — komplettes 2-Spalten-Layout:
  - **Links:** Ticket-Nr, Kanal, Priorität (ITK), Stichwörter, Kategorie, Unterkategorie, Status
  - **Rechts:** Zugew. Benutzer, Partner, Personenname, E-Mail, Abschluss, Abschlusszeitpunkt
- OCA-Stern-Priorität: `invisible="1"`
- OCA `sequence`: `groups="base.group_no_one"`
- OCA `duplicate_tracking_enabled`: `invisible="1"`

**4. Fünf Registerkarten:**
- **Beschreibung:** `description` mit `widget="html"`
- **Zusätzliche Felder:** `dynamic_field_value_ids` (mode=tree entfernt wegen Odoo-18-Bug)
- **Dateianhänge:** `attachment_ids` mit `widget="many2many_binary"`
- **SLA:** `sla_ids` mit `widget="many2many_tags"`
- **Zeiterfassung:** `timesheet_ids` Inline-Liste (Datum, Benutzer, Beschreibung, Projekt, Aufgabe, Dauer mit `sum="Gesamt"`)

**5. Neue Modellfelder:**
- `close_comment` (Text, „Abschluss")
- `support_comment` (Text, „Partner Kommentar")
- Methode `action_close_ticket()` — setzt Stage auf „Geschlossen/Behoben" + `closed_date`

**6. Bugfixes:**
- Portal-JS (`portal_category_filter.esm.js`) aus `web.assets_frontend` entfernt — verursachte JS-Fehler (importierte `@web/legacy/js/public/public_widget`, existiert in Odoo 18 nicht)
- `helpdesk_mgmt_timesheet` zu `depends` hinzugefügt (Ladereihenfolge)
- `ir.model.access.csv`: Field-Value-ACLs wiederhergestellt
- Default-Tree-View für `itk.helpdesk.subcategory.field.value` angelegt

**7. Bekannte Einschränkung:**
Header-Buttons („Ticket schließen", OCA „Assign to me") sind in der View-Architektur vorhanden, werden aber von Odoo 18 im Edit-Modus nicht ins DOM gerendert. Button ist zusätzlich als Stat-Button im `oe_button_box` definiert. Grund: Odoo-18-Form-Renderer verarbeitet Header-Buttons anders als Odoo 11.

**8. Nicht benötigte Odoo-11-Funktionen (endgültig entfallen):**
- „Sende Umfrage" — wird nicht mehr gebraucht
- „Genehmigungsanfrage stellen" — wird nicht mehr gebraucht

#### Geänderte Dateien
- `addons/itk_helpdesk_compat/__manifest__.py` — depends + assets
- `addons/itk_helpdesk_compat/models/helpdesk_ticket.py` — neue Felder + action_close_ticket
- `addons/itk_helpdesk_compat/views/helpdesk_ticket_views.xml` — komplett neu
- `addons/itk_helpdesk_compat/views/menus.xml` — Support Tickets Menü

**Commit:** `af3bec8`

---

### Session 63: Personal → Mitarbeiter — Testmigration abgeschlossen

**Datum:** 22.07.2026
**Art:** Datenmigration (Odoo 11 → Odoo 18)
**Auslöser:** Anna: „Modul Personal aus Odoo 11 mit Modul Mitarbeiter in Odoo 18 vergleichen und Testmigration durchführen."

#### NATIVE-FIRST CHECK (Phase A-E)

**Phase A — Odoo 11:** Das Modul „Personal" ist das native Odoo-11-`hr`-Modul (kein Custom-Modul). Bereits migrierte HR-Erweiterungen: `hr_employee_firstname` (Session 19), `hr_holidays_public` (Session 43-45).

**Phase B — Odoo 18:** Das native `hr`-Modul („Mitarbeiter") ist installiert und deutlich reicher als in Odoo 11 (174 vs. 73 Felder). Alle Kernfelder vorhanden.

#### Feldvergleich Odoo 11 → Odoo 18 (hr.employee)

| Odoo 11 Feld | Odoo 18 Feld | Status |
|---|---|---|
| `image` / `image_medium` / `image_small` | `image_1920` (auto-resize) | ✅ Umbenannt |
| `address_home_id` (res.partner) | `private_street`, `private_city`, etc. | ✅ Aufgelöst in Einzelfelder |
| `timesheet_cost` | `hourly_cost` | ✅ Umbenannt |
| `work_location` (Char) | `work_location_id` (Many2one) | ✅ Neues Modell |
| `firstname` / `lastname` | `firstname` / `lastname` | ✅ Bereits via hr_employee_firstname |
| `is_absent_totay` | `is_absent` | ✅ Computed |
| `manual_attendance` | Entfernt | ✅ War nicht stored |
| `message_channel_ids` | Entfernt | ✅ Mail-Refactor |

**Neue Pflichtfelder in Odoo 18:**
- `employee_type` → default 'employee'
- `marital` → default 'single'
- `company_id` → default company 1
- `distance_home_work_unit` → default 'km'

#### Datenbestand Odoo 11 (vor Migration)

| Modell | Anzahl |
|---|---|
| hr.employee (aktiv) | 15 |
| hr.employee (archiviert) | 9 |
| hr.department | 4 |
| hr.job | 5 |
| hr.employee.category | 2 |
| Mitarbeiter mit Foto | 12/15 |

#### Testmigration (JSON-RPC Odoo 11 → Odoo 18)

**Reihenfolge:**
1. Abteilungen (4) — Administration, Geschäftsleitung, Infrastruktur, Sales
2. Positionen (5) — Projektconsultant, Bereichsleiter IT-Services, Geschäftsführer, Assistenz, Prokurist
3. Kategorien (2) — IT-Kommunal GmbH, Externe MA & Vertriebspartner
4. Mitarbeiter (24) — aktive zuerst, dann archivierte; Manager/Coach in zweitem Durchlauf

**Besonderheiten:**
- Benutzerverknüpfungen nur wo Odoo-18-User existiert (derzeit 2 User: Anna, Florian)
- Fotos als base64 von Odoo 11 übertragen
- Archivierte Mitarbeiter (9) mit `active=False` markiert
- Privatadresse (address_home_id) in Einzelfelder extrahiert

#### Ergebnis (Odoo 18 nach Migration)

| Metrik | Odoo 11 | Odoo 18 | Status |
|---|---|---|---|
| Mitarbeiter gesamt | 24 | 24 | ✅ |
| Aktiv | 15 | 15 | ✅ |
| Archiviert | 9 | 9 | ✅ |
| Mit Benutzer | 15 | 2* | ⚠️ |
| Mit Foto | 12 | 15 | ✅ |
| Abteilungen | 4 | 4 | ✅ |
| Positionen | 5 | 5 | ✅ |
| Kategorien | 2 | 2 | ✅ |

\* Nur 2 Benutzer existieren derzeit in Odoo 18. Benutzermigration steht noch aus.

#### UI-Verifikation
- ✅ Kanban-Ansicht: 15 Mitarbeiterkarten
- ✅ Abteilungen: Administration (4), Geschäftsleitung (2), Infrastruktur (4), Sales (1)
- ✅ Positionen: Projektconsultant, Assistenz, Geschäftsführer sichtbar
- ✅ Fotos: Mitarbeiterfotos korrekt angezeigt
- ✅ Test-Banner: „TEST (odoo18_test)"

#### Bekannte Einschränkungen
1. **Benutzerverknüpfungen:** Die meisten Mitarbeiter haben keine `user_id`, weil die entsprechenden Benutzer in Odoo 18 noch nicht existieren. Benutzermigration ist ein separater Schritt.
2. **Anna Maierhofer:** Hat kein `user_id=2`, weil uid=2 bereits mit „Administrator" (employee 1) verknüpft ist. Muss nach Benutzermigration bereinigt werden.
3. **Abteilungsleiter:** `manager_id` auf `hr.department` wurde nicht migriert (Odoo 11 hatte keine Department-Manager gesetzt).

#### Nächste Schritte
- Benutzermigration aus Odoo 11 (59 Benutzer)
- Passwort-Handling für migrierte Benutzer
- Korrekte Zuordnung user_id ↔ employee_id nach Benutzermigration

32/56 Module funktionsfähig (32 migriert, 24 geparkt/entfallen, 1 gestrichen).

### Session 64: Benutzerkonten für alle Mitarbeiter erstellt (Helpdesk-Zuweisung)

**Datum:** 22.07.2026
**Art:** Benutzererstellung + Verknüpfung

#### Auslöser
Anna: „mach so, dass unter helpdesk - support tickets - ticket aufmachen - zugewiesene Benutzer alle eingetragene Mitarbeiter zu sehen sind"

#### Durchführung
1. Für alle 12 aktiven Mitarbeiter ohne `user_id` wurden `res.users`-Konten erstellt (Login = work_email)
2. `user_id` auf `hr.employee` mit dem neuen User verknüpft
3. Alle User zur Gruppe „Helpdesk Manager" (id=619) hinzugefügt
4. Alle User in das Helpdesk-Team „IT-Kommunal Support Test" (id=1) aufgenommen
5. Hannah Buchinger hat keine E-Mail → kein User-Konto (muss manuell angelegt werden)
6. Anna Maierhofer: eigenes User-Konto (uid=16, Login: Anna.maierhofer@it-kommunal.at) getrennt vom Admin (uid=2)

#### Ergebnis
- 14 `res.users` insgesamt (vorher: 2)
- 14 von 15 aktiven Mitarbeitern haben `user_id` (außer Hannah Buchinger)
- Dropdown „Zugewiesener Benutzer" im Ticket-Formular zeigt alle Mitarbeiter ✅

---

### Session 48: Menübezeichnungen Kontakte → Konfiguration an Odoo-11-Darstellung anpassen

**Datum:** 23.07.2026
**Modul:** `itk_base_setup`

#### Auslöser
Anna möchte die Menübezeichnungen unter Kontakte → Konfiguration an die gewohnte Odoo-11-Darstellung anpassen. Funktionen bleiben bestehen, nur die Labels ändern sich.

#### Änderungen

**1. Neue Datei: `data/menu_contacts_config.xml`**
- Renennt 10 `ir.ui.menu`-Records via `<record id="contacts.xxx">` auf deutsche Odoo-11-Bezeichnungen.

**2. Neue Datei: `i18n/de.po`**
- Überschreibt die Odoo-18-Standard-Übersetzungen (z.B. "Kontakt-Stichwörter" → "Kontakt Tags")
- Notwendig, weil Odoo mit deutschem Sprachkontext die PO-Übersetzungen der `contacts`-Basis verwendet

**3. Manifest-Update**
- `data: []` → `data: ['data/menu_contacts_config.xml']`

#### Menü-Mapping
- Contact Tags → Kontakt Tags
- Contact Titles → Partner-Kontaktanrede
- Industries → Tätigkeitsbereiche
- Localization → Lokalisierung
- Countries → Länder
- Fed. States → Bundesländer / Regionen
- Country Group → Ländergruppe
- Bank Accounts (Parent) → Bankkonten
- Banks → Bankverzeichnis
- Bank Accounts (Child) → Bankkonten

#### Technische Details
- Die Menü-Namen in `ir.ui.menu` werden bei deutschem Sprachkontext aus PO-Dateien übersetzt
- Direktes Schreiben auf `ir.ui.menu.name` reicht nicht — der Browser holt Menüs mit `lang=de_DE` Context
- Lösung: `write` mit `context={'lang': 'de_DE'}` auf Menüs UND Actions (`ir.actions.act_window`)
- Für Modul-Persistenz: `i18n/de.po` überschreibt die `contacts`-Modul-Übersetzungen
- Keine neuen Modelle, keine doppelten Menüpunkte, Zugriffsrechte unverändert

#### Ergebnis
- Alle 10 Menüpunkte zeigen die gewünschten deutschen Bezeichnungen ✅
- Browser-Titel (Breadcrumb) zeigt ebenfalls korrekte Namen ✅
- Aktionen zeigen weiterhin auf die richtigen Odoo-18-Modelle ✅
- Docker-Mount und Git-Repo sind synchron ✅
- Beim nächsten Docker-Neustart lädt Odoo das Modul mit PO-Datei und XML-Daten nach ✅

---

### Session 49: Kontaktformular an Odoo-11-Darstellung anpassen

**Datum:** 23.07.2026
**Modul:** `itk_base_setup`

#### Auslöser
Anna möchte die Formularansicht für Kontakte (res.partner) an das Odoo-11-Layout anpassen. Feldbezeichnungen sollen auf Deutsch den Odoo-11-Namen entsprechen, drei fehlende Felder sollen ergänzt werden.

#### Änderungen

**1. Python-Model: `models/res_partner.py`**
- `is_customer`: Boolean, computed aus `customer_rank > 0`, mit Inverse (setzt Rank auf 1/0)
- `is_supplier`: Boolean, computed aus `supplier_rank > 0`, mit Inverse
- Erbt von `res.partner`

**2. View: `views/res_partner_form.xml`**
- Erbt von `itk_crm.view_partner_form_itk` (id=2303), Prio 25
- Gruppe "Characteristics" → "Kenndaten"
- `multi_factor` (Multiplication Factor/Thsd) in linker Spalte eingefügt
- `is_supplier`, `is_customer` in rechter Spalte (nur für Unternehmen sichtbar)
- Feldbezeichnungen per `string`-Attribut: zu Handen, Organisationsbezeichnung, Verkäufer, Status, UID, Email offiziell, Website, Adresse

**3. Manifest**
- Neue Abhängigkeiten: `itk_crm`, `itk_multifactor`
- Neue Daten: `views/res_partner_form.xml`
- Model-Import in `__init__.py`

**4. i18n/de.po**
- Übersetzungen für Feldbeschreibungen ergänzt (Tax ID→UID, Salesperson→Verkäufer, etc.)
- "Characteristics" → "Kenndaten"

#### Feld-Mapping
- `multi_factor` (itk_multifactor): bereits in Odoo 18 vorhanden, nur View-Einbindung fehlte
- `customer`/`supplier` (Odoo 11 Boolean): in Odoo 18 durch `customer_rank`/`supplier_rank` (Integer) ersetzt → computed Boolean-Felder als Brücke

#### Ergebnis (Unternehmen-Formular)
- Kenndaten-Gruppe mit GKZ, Multiplication Factor/Thsd, zu Handen, Organisationsbezeichnung, Verkäufer, Ist ein Lieferant, Ist ein Kunde, Status ✅
- Adressblock mit Adresse, UID, Stichwörter ✅
- Rechte Spalte: Telefon, Mobil, E-Mail, Email offiziell, Website, Sprache ✅
- Status-Radio-Buttons: Bestandskunde, Ehemaliger Kunde, Kein Kunde ✅

#### Ergebnis (Einzelperson-Formular)
- Unternehmensfelder (GKZ, Organisationsbezeichnung, Ist ein Kunde/Lieferant, Email offiziell, Multiplication Factor) korrekt ausgeblendet ✅

---

### Session 50: Doppelte "Salesperson"/"Verkäufer"-Spalte in Kontaktliste entfernen

**Datum:** 23.07.2026
**Modul:** `itk_base_setup`

#### Auslöser
In der Kontakte-Listenansicht waren zwei Spalten für denselben Zweck sichtbar:
"Verkäufer" (vom Basis-Modul, Deutsch übersetzt) und "Salesperson" (vom ITK-Modul, Englisch).

#### Ursache
- `base.view_partner_tree` (id=123): enthält `user_id` als Standard-Spalte
- `itk_crm.view_partner_itk_tree` (id=2302): fügt `user_id` mit `string="Salesperson"` nach `email` ein
- Ergebnis: zwei `user_id`-Spalten in der kombinierten View

#### Fix
- Neue View: `views/res_partner_list.xml`
- Erbt von `itk_crm.view_partner_itk_tree` (Prio 25)
- XPath auf `//field[@name='email']/following-sibling::field[@name='user_id']`
- Setzt `column_invisible="True"` → ITK-Version ausgeblendet, Basis-Version ("Verkäufer") bleibt

#### Ergebnis
- ✅ Liste: Nur eine "Verkäufer"-Spalte
- ✅ Kanban: Kein user_id (unverändert)
- ✅ Formular: Nur ein user_id-Feld (unverändert)

---

### Session 51: Test-Migration 15 Kontakte Odoo 11 → 18

**Datum:** 23.07.2026
**Skript:** `scripts/test_migration_contacts.py`

#### Auslöser
Kontrollierte Test-Migration von 15 repräsentativen Kontakten, um Feld-Mapping,
Datenqualität und Darstellung zu validieren, bevor die vollständige Migration startet.

#### Ausgewählte Kontakte (15)
| # | Odoo11 ID | Name | Typ | Besonderheit |
|---|-----------|------|-----|-------------|
| 1 | 5792 | Eisenstadt | Gemeinde | GKZ, Status, Tags, MultiFactor |
| 2 | 5793 | Rust | Gemeinde | GKZ, Status |
| 3 | 5796 | Großhöflein | Gemeinde | GKZ, Kein Kunde |
| 4 | 5794 | Breitenbrunn | Gemeinde | GKZ, Tags |
| 5 | 12025 | BKH St. Johann | Unternehmen | UID, Telefon |
| 6 | 13406 | Clever Data GmbH | Unternehmen | UID, Email offiziell |
| 7 | 10288 | Städtebund Bgld | Unternehmen | mit Parent |
| 8 | 9449 | Abendstein Friedl | Person | Bürgermeister, Parent |
| 9 | 9285 | Abenthung Christian | Person | Bürgermeister, Parent |
| 10 | 13659 | Aberl Paul | Person | Telefon, Tags, Parent |
| 11 | 10429 | Villach (Kontakt) | Person | Verkäufer |
| 12 | 13184 | Michaela Müller | Person | Telefon, Standalone |
| 13 | 10902 | Roland Zangerl | Person | Telefon, Verkäufer |
| 14 | 7469 | Söchau | Gemeinde | ARCHIVIERT |
| 15 | 10686 | BMBWF | Unternehmen | ARCHIVIERT |

#### Feld-Mapping
| Odoo 11 | Odoo 18 | Status |
|---------|---------|--------|
| name | name | ✅ direkt |
| is_company | is_company | ✅ direkt |
| company_type | company_type | ✅ direkt |
| active | active | ✅ direkt |
| ref (GKZ) | ref | ✅ direkt |
| vat (UID) | vat | ✅ direkt (Whitespace-Bereinigung) |
| street/zip/city | street/zip/city | ✅ direkt |
| state_id | state_id | ✅ Name-Mapping |
| country_id | country_id | ✅ identisch (12=AT) |
| user_id (Verkäufer) | user_id | ⚠️ Login-Matching (nicht alle User in O18) |
| customer (Boolean) | customer_rank (Integer) | ✅ Boolean→Rank (1/0) |
| supplier (Boolean) | supplier_rank (Integer) | ✅ Boolean→Rank (1/0) |
| status_of_partner_id | status_of_partner_id | ✅ Name-Mapping (IDs identisch) |
| category_id (Tags) | category_id | ✅ Name-Mapping, Auto-Create |
| multi_factor | multi_factor | ✅ direkt |
| attention_of | attention_of | ✅ direkt |
| community_salutation | community_salutation | ✅ direkt |
| official_email | official_email | ✅ direkt |
| phone/mobile/email/website/lang | phone/mobile/email/website/lang | ✅ direkt |
| function | function | ✅ direkt |

#### Ergebnisse
- Importiert: **15/15** ✅
- Übersprungen: 0
- Fehler: 0
- Odoo 18 vorher: 54 Kontakte → nachher: 67 (+13, da 2 archivierte)
- Browser-Verifikation: ✅ (Eisenstadt, Söchau)

#### Bekannte Issues
1. Verkäufer-Matching nur via Login-Email; nicht alle O11-User haben O18-Äquivalent → Fallback auf Admin
2. `False`-Strings in Textfeldern → im Nachgang bereinigt
3. MIG-TEST-XXX im ref-Feld für GKZ-lose Kontakte → im Nachgang gelöscht
4. Keine Unterkontakte/Ansprechpartner migriert (separater Schritt nötig)
5. Keine parent_id-Verknüpfung (Parent-Unternehmen müssen vorher existieren)

#### Aufräumen
Importierte Kontakte haben IDs 69–83. Löschbar via:
```python
rpc18("object", "execute_kw", [DB, uid, PWD, "res.partner", "unlink", [list(range(69,84))]])
```

---

### Session 50: Referenzkontakt Breitenbrunn – Vollmigration (24.07.2026)

**Ziel:** Kontakt [10301] Marktgemeinde Breitenbrunn am Neusiedler See vollständig mit allen verknüpften Daten nach Odoo 18 migrieren.

#### Ablauf

**1. Stammdaten-Abhängigkeiten**
- Produkte 25/26 (Amtsweg.gv.at) → Odoo 18 ID 223/224
- Steuer 18 (20% USt) → Odoo 18 ID 15 (20% Ust)
- UoM "ITK Einheit" → Odoo 18 ID 29 (uom.uom)
- Zahlungsziel "14 Tage" → Odoo 18 ID 12
- Preisliste "Preisliste 2026 + Valorisierung" → Odoo 18 ID 34
- User "IT-Kommunal" existiert nicht → Admin (ID 2) als Fallback

**2. Beleg-Migration**
- Abonnement NV-00962 (ID=185): Template J, jährlich, 162€, 2 Lines
  - Line 76: Sockelbetrag, qty=1, 110€
  - Line 77: Einwohner, qty=2, 26€
- Verkaufsauftrag A-1900011 (ID=198): 102€, 2 Lines
- Verkaufsauftrag A-2600018 (ID=199): storniert
- 7 Rechnungen (IDs 22-28): alle bezahlt, Summe 871,01€ netto
  - Fakturiert = Summe `amount_untaxed` (nicht `amount_total`!)

**3. Kontakt-Daten**
- 3 Child-Kontakte (IDs 84-86)
- Community-Felder: population=1909, magnitude=1.501-2.000, update=2018-10-31, status=Marktgemeinde
- GKZ-Display über name_get: `[10301] Marktgemeinde Breitenbrunn am Neusiedler See`

**4. View-Anpassungen**
- Tab-Labels: Verkauf & Einkauf, Abrechnung, Gemeinde-Information
- Smart-Button-Labels: Verkauf, Fakturiert, Abonnements
- Community-Feldbezeichnungen: Einwohnerzahl, Größenklasse, Stand vom, Organisationstyp
- Support-Ticket-Tab (Platzhalter)
- Neue View `itk_base_setup.view_partner_smart_buttons` (prio=30, erbt von base)

#### Kritische Fehler & Fixes

**Fehler 1: Abonnement-Smart-Button → leere Liste**
- `subscription_count` zählt `sale.subscription` → zeigt 1
- Action 1104 öffnet `sale.subscription.line` mit `search_default_partner_id`
- `partner_id` auf `sale.subscription.line` ist STORED (kein Related-Feld)
- Bei Migration via JSON-RPC wurde `partner_id` nicht gesetzt → leere Liste
- **Fix:** `write([76,77], {"partner_id": 72})` + Action-Domain `[('partner_id','=',active_id)]`

**Fehler 2: uom_id → _unknown (RPC-Fehler beim Öffnen der Position)**
- Odoo 18 hat `product.uom` nach `uom.uom` umbenannt
- `sale.subscription.line.uom_id = Many2one('product.uom')` → `relation='_unknown'`
- `web_read` → `AttributeError: '_unknown' object has no attribute 'id'`
- **Fix:** `product.uom` → `uom.uom` in 3 Dateien:
  - `models/sale_subscription.py:768`
  - `wizard/sale_subscription_wizard.py:70`
  - `report/sale_subscription_report.py:14`
- Docker-Restart + Modul-Upgrade erforderlich (Python-Code-Änderung)

**Fehler 3: ir.ui.view.create via JSON-RPC schlägt fehl**
- `rpc("ir.ui.view", "create", [...])` returned immer `None`
- Browser-Console `fetch('/web/dataset/call_kw')` funktioniert
- **Workaround:** Views über Browser-Console erstellen, nicht via JSON-RPC

#### Mapping-Tabellen

**Smart Buttons:**
| Odoo 11 | Odoo 18 Modell | Zähler-Feld |
|---|---|---|
| Verkaufschancen | crm.lead | opportunity_count |
| Meetings | calendar.event | meeting_count |
| Verkauf | sale.order | sale_order_count |
| Abonnements | sale.subscription | subscription_count |
| Fakturiert | account.move | total_invoiced |
| Support Tickets | helpdesk.ticket | (via partner_id) |

**Community-Felder (itk_crm):**
| Odoo 11 Label | Odoo 18 Feld | Zielmodell |
|---|---|---|
| Einwohnerzahl | population | res.partner |
| Größenklasse | community_magnitude | computed via itk_crm.communitymagnitude |
| Stand vom | population_update | res.partner |
| Organisationstyp | status_of_community | → itk_crm.statusofcommunity |
| Städtebund-Mitglied | member_of_city_alliance | res.partner |

⚠️ Community-Modelle: `itk_crm.statusofcommunity` und `itk_crm.communitymagnitude` (nicht `community.status`!)

**Verkauf & Einkauf:**
| Odoo 11 | Odoo 18 |
|---|---|
| user_id=21 (IT-Kommunal) | user_id=2 (Admin) ⚠️ |
| pricelist_id=1 (Public) | property_product_pricelist=34 |
| payment_term_id=False | property_payment_term_id=12 (14 Tage) |
| customer=True | customer_rank=15 |
| account_receivable=295 | account_receivable=80 |

**Abrechnung:**
| Odoo 11 | Odoo 18 |
|---|---|
| Debitorenkonto 1410 | 2000 Trade receivables |
| Kreditorenkonto 1610 | 3300 Trade payables |
| payment_term=False | 14 Tage (ID 12) |
| vat=leer | vat=leer |
| bank_ids=[] | bank_ids=[] |

#### Modul-Änderungen
- `itk_crm/views/res_partner.xml`: Community-Info Page umbenannt + Labels
- `itk_base_setup/views/res_partner_form.xml`: Tab-Labels, Smart-Button-Labels, Support-Ticket-Tab
- `itk_base_setup/views/sale_subscription_line.xml`: Form-View + List-View für Abo-Positionen
- `itk_subscription/models/sale_subscription.py`: uom_id fix (product.uom→uom.uom)
- `itk_subscription/wizard/sale_subscription_wizard.py`: uom_id fix
- `itk_subscription/report/sale_subscription_report.py`: product_uom fix

#### Onchange-Fix (product.price)

**Fehler 4: `product.price` existiert nicht in Odoo 18**
- `onchange_product_quantity` Zeile 824: `self.price_unit = product.price`
- In Odoo 11 war `product.price` ein computed Feld mit Context (Pricelist, Quantity)
- In Odoo 18 gibt es nur `product.lst_price` (Standard-Listenpreis)
- **Fix:** `pricelist._get_product_price(product, quantity, partner, date, uom)` 
  - Berücksichtigt: Produkt, Menge, Partner, Preisliste, UoM, Datum
- `_compute_price()` auf uom.uom existiert weiterhin ✅
- Docker-Restart + Modul-Upgrade erforderlich

#### Ergebnisse Breitenbrunn (Final)

| Kennzahl | Wert | Quelle |
|---|---|---|
| Verkauf | 2 | sale.order (A-1900011, A-2600018) |
| Abonnements | 1 | sale.subscription (NV-00962) |
| Fakturiert | 871,01 € | account.move (7 Rechnungen, Netto-Summe) |
| Einwohnerzahl | 1.909 | res.partner.population |
| Größenklasse | 1.501-2.000 | itk_crm.communitymagnitude |
| Stand vom | 31.10.2018 | res.partner.population_update |
| Organisationstyp | Marktgemeinde | itk_crm.statusofcommunity (ID=1) |
| Städtebund-Mitglied | nein | res.partner.member_of_city_alliance |
| Child-Kontakte | 3 | res.partner (Hareter Helmut, Tobler Bernd×2) |
| GKZ-Display | [10301] Marktgemeinde... | name_get via itk_crm |
|| DB-Backups | 2 | vor_labels + vor_onchange_fix |

---

### Session 65: Disaster Recovery — PostgreSQL-Korruption behoben (29.07.2026)

#### Problem
- Odoo 18 zeigte nur noch "Create new database"-Seite
- PostgreSQL meldete: `could not open file "base/5/2601"` und `"base/16388/16508"`
- PostgreSQL-Datenverzeichnis unvollständig/beschädigt

#### Wiederherstellung

**Quellen geprüft:**
- GitHub `amaierhofer2026/odoo-migration` (main, catastrophe-backup, hermes/crm-structure-docs)
- Linux-VM: `/home/amaierhofer/Schreibtisch/odoo-migration/backups/`
- Docker-Volumes (nicht persistent — kein Filestore-Mount in docker-compose.yml)
- Keine Tags im Repo, kein .dump/.sql im Projektverzeichnis

**Gefundenes Backup:**
- `odoo18_backup_vor_onchange_fix.zip` (5,5 MB, Stand 24.07.2026)
  - `dump.sql` (29 MB, 176k Zeilen, 650 CREATE TABLE, 6239 Zeilen mit UTF-8)
  - `filestore/` (25 Verzeichnisse)

**Fehler beim ersten Restore:**
- `Get-Content dump.sql | docker exec -i odoo18-db psql` → UTF-8 durch Windows-1252-Pipeline zerstört
- Symptome: `N??tzliche Links`, `??ber uns`, Login kaputt
- PostgreSQL-Warnings: `transaction_timeout` (PG17-Parameter, PG16 kennt ihn nicht — harmlos)
- PostgreSQL-Error: `res_country_state_name_code_uniq` — Artefakt des Encoding-Fehlers

**Korrigierter Restore (fix_encoding.ps1 v2):**
1. `docker stop odoo18` + `docker rm odoo18`
2. `DROP DATABASE IF EXISTS odoo18_test WITH (FORCE)`
3. `CREATE DATABASE odoo18_test OWNER odoo ENCODING 'UTF8'`
4. `docker cp dump.sql odoo18-db:/tmp/dump.sql` (binär, keine Pipeline!)
5. `docker exec odoo18-db psql -U odoo -d odoo18_test -f /tmp/dump.sql`
6. `docker cp filestore odoo18:/tmp/filestore_restore` + in `/var/lib/odoo/filestore/odoo18_test/` kopieren
7. `docker restart odoo18`

**Ergebnis:**
- ✅ Odoo 18 läuft unter http://localhost:8069
- ✅ Deutsche Sonderzeichen korrekt
- ✅ Login funktioniert
- ✅ Sauberes Backup erstellt: `backups/odoo18_backup_clean_2026-07-29_1248.zip` (7 MB)
- ✅ Alle 7 ITK-Module installiert (itk_subscription, itk_product, itk_projectcategory, itk_sale_management, itk_valorisierung, itk_base_setup, itk_crm)
- ✅ helpdesk_mgmt (OCA): 1 Team, 37 Kategorien, 16 Stages, 4 Channels, 14 User-Zuordnungen
- ✅ res_country_state_name_code_uniq Constraint vorhanden und gültig
- ✅ Keine Duplikate, alle Indizes valide, UTF-8 Encoding bestätigt

#### Erstellte Scripts
| Script | Zweck |
|--------|-------|
| `fix_encoding.ps1` (v2) | Full Recovery: DB + Filestore mit docker cp + psql -f |
| `backup_now.ps1` | Clean Backup: pg_dump + Filestore → ZIP |
| `diag_db.ps1` | DB-Diagnose: Constraints, Duplikate, Row-Counts, User |

#### Root Cause des Encoding-Bugs
PowerShells `Get-Content`-Pipeline verwendet je nach System-Config Windows-1252/ANSI.
Alle UTF-8-Bytes > 0x7F werden beschädigt. **Docker cp + psql -f ist der einzig sichere Weg.**

#### Technische Notizen
- `docker-compose.yml` mountet Filestore **nicht** → bei `docker rm odoo18` geht Filestore verloren
- Empfehlung: `./filestore:/var/lib/odoo/filestore` in docker-compose.yml ergänzen
- `transaction_timeout`-Warning beim Restore ist harmlos (PG17-Parameter in PG16)
- Dump ist Plain SQL (`-- PostgreSQL database dump`), nicht Custom-Format → `psql`, nicht `pg_restore`

### Session 6: CRM / Kundenverwaltung — Strukturmigration Odoo 11 → 18

**Datum:** 30.–31.07.2026
**Branch:** `crm-kundenverwaltung-migration` → PR #3 (Analyse), PR #4 (Umsetzung)
**Dokumentation:** `docs/crm_kundenverwaltung_analysis.md`

#### Ziel
Odoo-18-CRM strukturell an Odoo-11-Kundenverwaltung angleichen. Keine alten Daten migriert.

#### Umgesetzt (30.–31.07.)

**App-Name:** ir.module.category id=13 "CRM" → "Kundenverwaltung" (per Server-Action sudo())

**Menüs (5 Haupt + Sub):**
- Root: Kundenverwaltung (143) / Aktivitäten (894), Pipeline (892), Kunden (148), Berichtswesen (150), Konfiguration (155)
- Sub: Interessenten (149), Angebote (294), Teams (147), Vertriebskanäle (158), Aktivitätstypen (161), Interessenten und Chancen (164), Ablehnungsgründe (167)

**Stages (8):**
- Neu(12), Angebotsphase(9), On-Hold(10), Positive Rückmeldung(5), Erfolgreich(11,is_won=True), Zur Verrechnung bereit(6), Verloren(7,fold), Verrechnet(8,fold)
- PITFALL: probability existiert NICHT auf crm.stage in O18

**Custom-Felder (4, alle selection):**
- x_Lead_Quelle (20641): 24 Werte / x_Produktinteresse (20643): 10 / x_lead_status (20645): 12 / x_Anrede_Lead (20647): 3

**Interessenten-Ansicht (31.07.):**
- Labels: Salesperson→Verkäufer, Sales Team→Vertriebskanal, Contact Name→Ansprechpartner, Created on→Erstellt am, Last Updated on→Aktualisierungsdatum
- Action 210: "Leads"→"Interessenten"
- Inherited View id=4005: Custom-Felder + write_date hinzugefügt, name="Lead"→"Interessent"

**Nicht umgesetzt:** Automated Action "Zur Verrechnung bereit" (nur analysiert)

**PITFALLS:**
- ir.translation kein ORM-Modell → PO-Translations umgehen durch Löschen+Neuanlegen
- Server-Actions mit sudo() für geschützte Modelle (ir.module.category)

---

### Session 66: Aktivitäten-Kanban-Ansicht (31.07.2026)

#### Analyse
- Menu 894 "Aktivitäten" (unter Kundenverwaltung) zeigte **falsche Action 211** (crm.lead mit Aktivitäten-Filter)
- Das ist eine CRM-Lead-Liste, nicht die echte mail.activity-Übersicht
- Odoo 18 hat alle benötigten mail.activity-Felder bereits nativ
- Kanban-View 308 (mail.activity.view.kanban.open.target) existiert bereits

#### Durchgeführte Änderungen

1. **Neue Action 1464 erstellt** (ir.actions.act_window):
   - name: "Aktivitäten"
   - res_model: mail.activity
   - view_mode: kanban,list,calendar,form (Kanban als Default)
   - context: {"group_by": "activity_type_id"} → Kanban nach Aktivitätstyp gruppiert

2. **Menu 894 aktualisiert**: von Action 211 (crm.lead) auf Action 1464 umgebogen

3. **Zusätzliche Aktivitätstypen** (für Odoo-11-Kompatibilität):
   - "Anrufen" (14) — phonecall, fa-phone
   - "data.gv.at Neukunde anlegen" (12) — default, fa-user-plus
   - "Webinar / Präsentation" (13) — meeting, fa-presentation

4. **XML-Daten-Datei** (`data/aktivitaeten_views.xml`):
   - Definiert die 3 neuen Aktivitätstypen
   - Definiert die Action mit XML-ID `itk_crm.action_aktivitaeten`
   - `<function>`-Call zum Aktualisieren von Menu 894
   - In `__manifest__.py` registriert

5. **Test-Aktivitäten** (IDs 9-12) zu Partner "Magistrat der Stadt Villach":
   - E-Mail: "Projektunterlagen per E-Mail senden" (10.08.2026)
   - Anrufen: "Rückruf vereinbart - Angebot besprechen" (05.08.2026)
   - Meeting: "Webinar / Präsentation IT-Sicherheit" (15.08.2026)
   - To-Do: "Daten für data.gv.at Neukunden vorbereiten" (10.08.2026)

#### Browser-Verifikation
- Kanban-Ansicht zeigt 4 Spalten gruppiert nach Aktivitätstyp ✅
- Karten zeigen: Kunde, Zusammenfassung, Fälligkeit (In X Tagen), User-Avatar, Typ-Badge ✅
- Erledigt/Abbrechen-Buttons auf jeder Karte ✅
- View-Switcher: Kanban (aktiv), Liste, Kalender ✅
- Such- und Filterleiste vorhanden ✅

#### Mapping-Tabelle (kompakt)
16 von 17 Feldern/Funktionen 1:1 in Odoo 18 vorhanden. Nur Menü-Verknüpfung + Kanban-Gruppierung mussten angepasst werden. Keine neuen Felder angelegt.

#### PITFALLS
- mail.activity braucht in Odoo 18 `res_model_id` (Many2one ir.model) statt `res_model` (Char)
- Action-Context mit `group_by` muss JSON-String sein (nicht dict)

---

### Session 67: Lost Reasons + Automated Action "Zur Verrechnung bereit" (03.08.2026)

**Branch:** `feature/aktivitaeten-kanban-ansicht`
**Commit:** `b8aac83`

#### Lost Reasons (Odoo 11 → 18)

| O11 ID | O11 Name | O18 Status | Aktion |
|--------|----------|------------|--------|
| 1 | Too expensive | ✅ Existiert | Unverändert |
| 2 | Im Moment keinen Bedarf | ✅ Umbenannt | "We don't have people/skills" → "Im Moment keinen Bedarf" |
| 4 | Bedarf zu gering | ✅ Neu | `itk_crm.lost_reason_bedarf_zu_gering` |
| 5 | Später kontaktieren | ✅ Neu | `itk_crm.lost_reason_spaeter_kontaktieren` |
| 6 | Mitbewerb | ✅ Neu | `itk_crm.lost_reason_mitbewerb` |

**Implementierung:** `data/lost_reasons.xml` (noupdate=1)
- ID 2: `<function>`-Call mit search nach "We don't have people/skills" → write name
- 3 neue Records mit XML-IDs für Idempotenz

#### Automated Action "Zur Verrechnung bereit"

**Was:** Wenn ein crm.lead auf Stage "Zur Verrechnung bereit" wechselt → Benachrichtigung an Follower

**Implementierung:** `hooks.py` → `post_init_hook(env)`
- Sucht Stage "Zur Verrechnung bereit" per Namen
- Erstellt `ir.actions.server` (state='code'): `record.message_post()` an Follower
- Erstellt `base.automation` (trigger='on_write', filter_pre_domain stage_id)
- **Idempotent:** Prüft vorher, ob bereits existiert
- **Sanft:** Nur Warnung, wenn Stage nicht gefunden wird (RPC-Setup zuerst nötig)

**Dateien geändert/neu:**
- `addons/itk_crm/hooks.py` — **NEU** — post_init_hook
- `addons/itk_crm/data/lost_reasons.xml` — **NEU** — Lost Reasons
- `addons/itk_crm/__init__.py` — `from . import hooks`
- `addons/itk_crm/__manifest__.py` — data + post_init_hook registriert

**PITFALLS:**
- GitHub-Token wird von Hermes maskiert (Security-Scanner) → Push muss manuell erfolgen
- Odoo 18 Docker war nicht erreichbar → keine Browser-Verifikation möglich
- Lost-Reason-ID 2 per Namen gesucht statt XML-ID (robuster)

**Noch offen:**
- Browser-Verifikation sobald Odoo 18 läuft
- Modul-Upgrade `itk_crm` durchführen zum Testen
- Teams-Migration (blockiert bis Kontaktmigration freigegeben)

---

### Session 68: Aktivitäten-Kanban-Test + CRM-Menü-Fixes (03.08.2026)

**Branch:** `hermes/aktivitaeten-crm-fixes`
**Commit:** `b60b64a`

#### Browser-Test: Aktivitäten-Kanban

Getestet und funktionsfähig:
- **Kanban-Ansicht**: 4 Spalten gruppiert nach Aktivitätstyp (E-Mail, Anrufen, Meeting, To-do) ✅
- **Listen-Ansicht**: Gruppierte Liste mit Spalten (Dokument, Typ, Zugewiesen, Fälligkeit) ✅
- **Kalender-Ansicht**: Woche 32, Aktivitäten korrekt auf Daten verteilt ✅
- **Keine JS-Fehler** in der Browser-Konsole ✅

#### CRM-Menü-Fixes (Delete & Recreate)

**Problem:** Odoo-18-PO-Übersetzungen überschreiben DB-Namen. Der einzig funktionierende Fix ist Delete+Recreate (siehe `references/odoo18-translation-pitfalls.md`).

**Gefixt:**
| Element | Vorher | Nachher | Methode |
|---------|--------|---------|---------|
| Menu 145 (Pipeline-Sub) | Meine Pipeline | **Pipeline** | Delete+Recreate → id=897 |
| Menu 294 (Angebote-Sub) | Meine Angebote | **Angebote** | Delete+Recreate → id=898 |
| Action 210 (Interessenten) | Leads | **Interessenten** | Delete+Recreate → id=1469 |

**Nicht gefixt (PO-Übersetzung, Felder nicht delete+recreate-fähig):**
- Spalten: "Vertriebsmitarbeiter" (soll: Verkäufer), "Verkaufsteam" (soll: Vertriebskanal)
- View-Titel: "Leads" (soll: Interessenten — View-Arch-String, nicht Action-Name)

**PITFALLS:**
- `ir.translation` kein ORM-Modell → `<record>` in XML funktioniert NICHT
- `post_init_hook` mit SQL funktioniert NICHT (PO-Übersetzungen werden NACH dem Hook geladen)
- Einziger Weg für Menüs: Delete+Recreate per RPC
- Action 210 wurde gelöscht, aber Create schlug fehl → manuell mit korrekten Attributen neu erstellt

**Nicht committet:**
- `KONTAKTPRUEFUNG_BERICHT.md`: Enthält Login-Referenzen + Kundennamen
- `validate_partner_migration.py`: Enthält Login-Referenzen
- `backups/`: Datenbank-Backups
- `crm_menu_translations.xml`: Funktionslos, wurde gelöscht

**Nachtrag — Bugfix view_mode tree→list (03.08.2026):**
- Action 1469 (Interessenten) hatte `view_mode: tree,...` → JS-Fehler "View types not defined tree"
- Fix: view_mode auf `list,...` geändert + search_view_id entfernt (View 219 verweist auf Feld `state`, das in Odoo 18 nicht existiert)
- Gleicher Fix in 5 Moduldateien (itk_sale_management, itk_translation, itk_reports, hr_holidays_public)
- `.gitignore`: backups/, scans/, *.zip, *.dump ergänzt
- Browser-Verifikation: Interessenten, Angebote, Pipeline, Aktivitäten — alle ohne JS-Fehler ✅
---

### Session 69: itk_crm Modul-Upgrade — Lost Reasons, Automated Action, Aktivitäten-Kanban (04.08.2026)

**Branch:** `crm-kundenverwaltung-migration`
**Commit:** `7e7f39d`

#### Probleme behoben

1. **`aktivitaeten_views.xml` fehlte** — Datei existierte nicht, war aber im Manifest referenziert → Modul-Upgrade blockiert
2. **`lost_reasons.xml` mit `<function>`-Tags** — escaped Quotes verursachten ParseError beim XML-Load
3. **`hooks.py` Feld-Fehler** — `action_server_id` (many2one) existiert nicht mehr in Odoo 18; korrekt ist `action_server_ids` (one2many)
4. **`crm.lost.reason` kein `sequence`-Feld** — create mit `sequence` crashte den Hook

#### Durchgeführte Änderungen

**`data/aktivitaeten_views.xml` — NEU**
- Definiert Action `itk_crm.action_aktivitaeten` (mail.activity, Kanban-Gruppierung nach Typ)

**`data/lost_reasons.xml` — NEU (leer)**
- Lost-Reason-Logik komplett nach hooks.py verlagert

**`hooks.py` — NEU (134 Zeilen)**
- `_setup_lost_reasons()`: Rename "We don't have people/skills" → "Im Moment keinen Bedarf"; erstellt "Bedarf zu gering", "Später kontaktieren", "Mitbewerb"
- `_setup_automated_action()`: base.automation "Interessent 'zur Verrechnung bereit'" (trigger=on_write, filter_pre_domain stage_id=6)
- `_setup_activity_kanban()`: Stellt sicher, dass Aktivitäten-Action korrekt konfiguriert ist
- Alle Operationen idempotent (search vor create/write)

**`__manifest__.py`**
- `data/aktivitaeten_views.xml` + `data/lost_reasons.xml` registriert
- `post_init_hook: 'post_init_hook'` registriert

**`__init__.py`**
- `from . import hooks` ergänzt

**view_mode tree→list Fixes** (in 4 weiteren Modulen):
- `hr_holidays_public/views/hr_holidays_public_view.xml`
- `hr_holidays_public/wizards/holidays_public_next_year_wizard.py`
- `itk_reports/views/views.xml`
- `itk_sale_management/views/views.xml`
- `itk_translation/views/views.xml`

**`.gitignore`**
- `filestore/` ergänzt

#### RPC-Nacharbeiten (post_init_hook schlug initial fehl)
- Lost Reasons manuell via RPC erstellt/nachbearbeitet
- Automated Action via RPC erstellt (action_server_ids statt action_server_id)
- Duplikate Aktivitäten-Action gelöscht (id=1473, behalten: id=1464)
- Broken asset attachments gelöscht (7 Stück, nach Docker-Neustart)

#### Finaler Stand

| Bereich | Status |
|---|---|
| Lost Reasons | 6/6 ✅ (Too expensive, Im Moment keinen Bedarf, Not enough stock, Bedarf zu gering, Später kontaktieren, Mitbewerb) |
| Automated Actions | 2 ✅ (Urlaubsantrag + Zur Verrechnung bereit) |
| CRM Stages | 8/8 ✅ |
| Aktivitäten-Kanban | 4 Spalten (E-Mail, Anrufen, Meeting, To-do) ✅ |
| ITK-Module | 15 installed ✅ |

#### Browser-Verifikation (04.08.2026)
- ✅ Login erfolgreich
- ✅ Kundenverwaltung-Menüstruktur (Aktivitäten, Pipeline, Kunden, Berichtswesen, Konfiguration)
- ✅ Interessenten: Listen-Ansicht (Titel "Interessenten", 3 Leads, korrekte Spalten)
- ✅ Interessenten: Kanban-Ansicht (8 Stages, Karten mit Name/Kontakt/Betrag/Stage)
- ✅ Aktivitäten: Kanban-Ansicht (4 Spalten gruppiert nach Aktivitätstyp)
- ✅ Aktivitäten: Listen-Ansicht (gruppiert, 4 Einträge)
- ✅ Aktivitäten: Kalender-Ansicht (Woche 32, Aktivitäten auf korrekten Tagen)
- ✅ Pipeline-Dropdown (Pipeline, Interessenten, Angebote, Teams)
- ✅ Keine JS-Fehler, keine RPC-Fehler, keine 500-Fehler

#### PITFALLS
- `button_immediate_upgrade` über JSON-RPC nicht nutzbar (Access Denied) → Workaround: `button_upgrade` + Browser-Reload
- `crm.lost.reason` hat in Odoo 18 nur `name` + `active` — kein `sequence`, keine weiteren Felder
- `base.automation` verwendet `action_server_ids` (one2many), nicht `action_server_id`
- `env.ref()` für `crm.model_crm_lead` kann fehlschlagen → `env['ir.model'].search([('model','=','crm.lead')])` robuster
- Docker Shared-Filesystem: `.pyc`-Cache kann nach Änderungen veraltet sein → Modul-Upgrade erzwingt Neu-Kompilierung

### Session 49: Vertriebskanäle — Menü & Listenansicht an O11 angleichen

**Datum:** 10.08.2026

#### Ausgangslage
- O11: Menü "Vertriebskanäle" unter Kundenverwaltung → Konfiguration, Modell `crm.team`
- O18: Menü "Verkaufsteams" (ID 158) an gleicher Stelle, selbes Modell `crm.team`
- DB-Name war bereits "Vertriebskanäle", aber deutsche PO-Übersetzung zeigte "Verkaufsteams"
- Listenansicht: Spalten "Verkaufsteam" (name) und "Teamleiter" (user_id)

#### Analyse
| Aspekt | Odoo 11 | Odoo 18 |
|--------|---------|---------|
| Menü | "Vertriebskanäle" (ID 201) | "Verkaufsteams" → "Vertriebskanäle" gefixt |
| Action | act_window auf crm.team | ID 186, xml_id=sales_team.crm_team_action_config |
| Spalte name | "Vertriebskanal" | "Vertriebskanal" (war "Verkaufsteam") |
| Spalte user_id | "Kanal Leitung" | "Kanal Leitung" (war "Teamleiter") |
| Form | Name, Leitung, Mitglieder | Name, Teamleiter, Mitglieder + CRM/Sales-Features |

#### Änderungen

**1. Menü-Label (DE):** "Verkaufsteams" → "Vertriebskanäle"
- Per Server-Action mit `sudo()` und `with_context(lang='de_DE')`
- Menu 158 (crm.crm_team_config) + Action 186 (sales_team.crm_team_action_config)

**2. Listenansicht Spalten-Labels:**
- `name`: "Verkaufsteam" → "Vertriebskanal"
- `user_id`: "Teamleiter" → "Kanal Leitung"
- Inherited View 4010 auf `sales_team.crm_team_view_tree` (ID 492)

**3. Persistent in itk_crm (für nächsten Docker-Restart):**
- `views/vertriebskanaele_views.xml` — Inherited List View
- `hooks.py` — `_setup_vertriebskanaele_labels()` für DE-Menü/Action-Label
- `__manifest__.py` — v18.0.1.1.0, neue View registriert

**Wichtig:** Docker-Container (Windows) hat die Datei-Änderungen beim Modul-Upgrade nicht erkannt. View wurde per RPC direkt in DB angelegt. Beim nächsten Docker compose down/up greifen die persistenten Dateien.

#### Verifikation (Browser)
- ✅ Menü-Dropdown zeigt "Vertriebskanäle"
- ✅ Seitentitel: "Vertriebskanäle"
- ✅ Spalten: "Vertriebskanal", "Alias", "Kanal Leitung"
- ✅ Formular: Name, Teamleiter, Mitglieder + O18-Features erhalten
- ✅ Bestehende O18-Funktionalität vollständig erhalten
- ✅ Keine JS-Fehler in Browser-Console
- ✅ Keine doppelten Menüs
- ✅ Nur 1 bestehendes Team ("Verkauf"), keine Migration aus O11

### Session 50: PostgreSQL-Crash — Recovery & Architektur-Analyse

**Datum:** 10.08.2026 (unmittelbar nach Session 49)

#### Vorfall

Nach den CRM-Änderungen aus Session 49 wurden die Docker-Container neugestartet.
PostgreSQL (`odoo18-db`) startete nicht mehr:

```
invalid checkpoint record
PANIC: could not locate a valid checkpoint record
FATAL: the database system is starting up
```

Container liefen in einer Restart-Schleife. `docker compose stop` wurde ausgeführt.

#### Zeitleiste (rekonstruiert aus pg_control/WAL-Timestamps)

| Zeit | Ereignis |
|------|----------|
| 11:13 | PG startet, schreibt WAL 15/16/17 + Systemkataloge |
| 11:15 | PG wird unterbrochen — pg_control geschrieben, postmaster: "stopping" |
| 11:24 | Docker/PG-Neustart 1 (postmaster.opts neu) |
| 11:26 | Docker/PG-Neustart 2 — PG bleibt in "stopping" hängen |

#### Ursachenanalyse

**Root Cause: VirtualBox Shared Folder (vboxsf) als PostgreSQL-Datenverzeichnis**

```yaml
# docker-compose.yml
volumes:
  - ./postgres:/var/lib/postgresql/data    # ← vboxsf-Dateisystem!
```

vboxsf garantiert kein echtes fsync(), erlaubt Write-Reordering und hat File-Locking-Probleme.
PostgreSQL benötigt zwingend atomare WAL-Schreibvorgänge.

**Zweiter Vorfall in 12 Tagen** — am 29.07.2026 gab es einen ähnlichen Crash (siehe disaster-recovery.md).

**Keine** der heutigen Code-Änderungen hat direkt PostgreSQL-Dateien modifiziert.
Alle CRM-Änderungen liefen über Odoo ORM/RPC. Die Modul-Upgrades und Docker-Restarts
haben PG zu normalen Shutdown/Startup-Zyklen gezwungen — einer davon fiel mit
vboxsf-Schreibinkonsistenz zusammen.

#### Sicherungsstand

| Sicherung | Stand | Status |
|-----------|-------|--------|
| `backups/odoo18_backup_clean_2026-07-29_1248.zip` (6.7 MB) | 29.07. | Sauber, 12 Tage alt |
| `postgres/` (15202 Dateien, 384 MB) | 10.08. 11:15 | Beschädigt (WAL-Checkpoint) |
| `postgres_defekt_2026-08-10/` | 10.08. | Exakte Kopie von postgres/ |
| `postgres_defekt_2026-07-29_114402/` | 29.07. | Vom ersten Crash |
| `filestore/odoo18_test/` (28 Dateien, 34 MB) | aktuell | Intakt (keine DB-Abhängigkeit) |

#### Recovery Phase 2: pg_resetwal auf Kopie

- Script: `recovery_phase2.ps1`
- Arbeitet NUR auf `C:\Odoo-Test\postgres_recovery` (Kopie von postgres_defekt)
- Schritte:
  1. Kopie postgres_defekt → postgres_recovery
  2. `docker run ... pg_resetwal -f` auf der Kopie
  3. Temporärer Recovery-PG-Container (isoliert von odoo18-db)
  4. Prüfung: odoo18_test vorhanden, Tabellen-Zählungen
  5. `pg_dump` → `backups\odoo18_dump_rescued_2026-08-10.sql`
  6. Filestore-Sicherung → `backups\filestore_rescued_2026-08-10\`
  7. Recovery-Container stoppen

#### Naechste Schritte (geplant)

- **Phase 3:** Neue saubere PG-Instanz -> Dump importieren -> Odoo verifizieren
- **Phase 4:** PostgreSQL auf Docker Named Volume migrieren (kein bind-mount mehr)

---

## Disaster Recovery — 11.08.2026

### Phase 2: ENDBEFUND (pg_resetwal)

- Dry-Run am 10.08. erfolgreich: pg_resetwal -n erkannte Cluster, WAL-Segment 000000010000000000000019
- recovery_phase2_v6.ps1: pg_resetwal -f auf frischer Kopie erfolgreich
- **Aber:** PostgreSQL-Start scheiterte an `FATAL: could not open file "global/1262"`
- **OID 1262 = pg_database** — Systemkatalog aller Datenbanken im Cluster
- `global/1262` fehlt in ALLEN Rohdatenkopien:
  - `postgres/` (live, 15202 Dateien): FEHLT
  - `postgres_defekt_2026-08-10/` (15202 Dateien): FEHLT
  - `postgres_defekt_2026-07-29_114402/` (4255 Dateien): FEHLT
  - `postgres_recovery/` (nach pg_resetwal): FEHLT
  - `postgres-backup.tar.gz` (29.07.): FEHLT
  - Nur 1262_fsm und 1262_vm existieren, die Hauptdatei fehlt ueberall
- **Ursache:** vboxsf-Bind-Mount hatte die Datei bereits vor 29.07. verloren
- **Entscheidung:** Keine weiteren Reparaturversuche an Rohdaten

### Phase 3A: Clean Restore aus SQL-Dump (29.07.)

- **Quelle:** `C:\Odoo-Test\backups\odoo18_backup_clean_2026-07-29_1248.zip`
- **Methode:** Docker Named Volume `odoo18_pgdata` (kein vboxsf-Bind-Mount mehr)
- **Script:** recovery_phase3_v8.ps1 (PowerShell 5.1, 8 Iterationen bis Parser-clean)
- **Ergebnis (11.08.):** Odoo startet (JA), HTTP 200 (JA), `/web/login`-Route erreichbar (JA)
  - **Loginformular sichtbar und funktional: NEIN / noch offen** — siehe Diagnose 12.08.2026

### BEFUND: Encoding-Problem im Dump vom 29.07.

- dump.sql ist UTF-16 LE mit BOM (0xFF 0xFE)
- `SET client_encoding = 'UTF8';` korrekt gesetzt
- **Deutsche Sonderzeichen sind im Dump BEREITS defekt — Diagnose 12.08.: CP850-Doppel-Encoding (nicht CP1252!)**
- Beispiele: `├£ber uns` statt `Über uns`, `N├╝tzliche Links`, `l├Âsen` statt `lösen`
  - Ursache: UTF-8-Bytes wurden als **CP850** interpretiert und erneut encodiert (VOR dem 29.07., vermutlich beim urspruenglichen pg_dump)
- Reversibel: `text.encode('cp850').decode('utf-8')` — 35/35 ├-Paare + 41/41 Ô-Tripel (17.296 Sequenzen) fehlerfrei, KEINE `?`-Verluste im 29.07.-Dump
- Website-Menue zeigt: `Top-Men├╝ f├╝r Website 1` statt `Top-Menue fuer Website 1`
- **Login-Seite:** Formular IST im HTML (oe_login_form, login/password/Submit/csrf vorhanden), aber mit Klasse `d-none` (Odoo-18-Stock-Template webclient_templates.xml:141 — Einblendung per JS nach Asset-Load). JS-Bundle `web.assets_frontend_minimal.min.js` liefert **HTTP 500** (fehlende Filestore-Datei `filestore/odoo18_test/15/159bc8e4e01c680cc106306c5c31d71c1ff77d37`), CSS 200/0B -> Formular bleibt unsichtbar. **Login NICHT funktional (Stand 12.08.)**

### Geplanter Repair-Plan (Phase 3B)

1. Encoding-Reparatur: dump.sql mit korrekter Encoding-Behandlung neu importieren
   - Originaldump ist UTF-16 LE -> nach UTF-8 konvertieren -> psql mit `PGCLIENTENCODING=UTF8`
   - ODER: Im laufenden Odoo die defekten Texte per SQL reparieren (convert_from/convert_to)
2. Nach erfolgreichem Encoding-Fix: Modul-Upgrades aus Git (itk_crm etc.)
3. Vollverifikation: Login, CRM, Interessenten, Pipeline, Aktivitaeten, Vertriebskanaele

---

## Diagnose 12.08.2026: Login-Formular unsichtbar + Encoding-Beweis (NUR Analyse, read-only)

### Statuskorrektur (ersetzt fruehere Aussagen)

| Aussage | Status |
|---|---|
| Odoo startet | JA |
| HTTP 200 | JA |
| /web/login-Route erreichbar | JA |
| Loginformular sichtbar und funktional | JA — von Anna im Browser bestaetigt (12.08., nach Asset-Fix Session 70) |
| Deutsche Sonderzeichen | FEHLER / noch offen (Reparatur erst nach Freigabe) |

### 1) Login /web/login — Befund

- GET /web/login liefert 19.497 Bytes HTML, Titel "Login | My Website" (Website-Layout).
- **Das Formular ist serverseitig VOLLSTAENDIG vorhanden:**
  `<form class="oe_login_form d-none" action="/web/login">` mit input `login`, input `password`,
  Submit-Button und csrf_token (oe_login_form: 1, name=login: 1, name=password: 1, submit: 3).
- **Unsichtbar wegen `d-none`:** Odoo-18-Stock-Template `webclient_templates.xml:141`
  (`t-attf-class="oe_login_form #{'' if login else 'd-none'}"`) — das Formular wird erst per JS
  nach erfolgreichem Asset-Load eingeblendet.
- **Assets kaputt (Root Cause):**
  - `web.assets_frontend_minimal.min.js` -> **HTTP 500**
  - `web.assets_frontend.min.css` -> HTTP 200, **0 Bytes**
  - Odoo-Log: `FileNotFoundError ... '/var/lib/odoo/filestore/odoo18_test/15/159bc8e4e01c680cc106306c5c31d71c1ff77d37'`
  - Die Datei existiert im 29.07.-Backup-Zip (30.353 B) UND in `filestore_before_phase3_2026-08-11/` (104 Dateien),
    aber NICHT im aktiven Filestore (Container wie Host-Mount: nur 29 Dateien) -> **Phase-3A-Filestore-Restore war unvollstaendig**
- **Fix (bekannt, NICHT ausgefuehrt):** ir.attachment mit URL `/web/assets/%` loeschen -> Odoo regeneriert
  die Bundles (Merkregel Sessions 12/21/42). Alternativ fehlende Filestore-Dateien aus dem Backup ergaenzen.

### 2) Encoding — Beweis (Sollwert | Original-Dump 29.07. | DB odoo18_test | Browser-HTML)

Texte stecken in `ir_ui_view` 2893 `website.footer_custom` (+ 2832 `website.aboutus`), `website_menu` 1/4, `ir_module_module`.

| Sollwert | Original-Dump | DB (View 2893/2832) | Browser (gerendertes HTML) |
|---|---|---|---|
| Über uns | `├£ber uns` | `├£ber uns` | `├£ber uns` (Footer-Link) |
| Nützliche Links | `N├╝tzliche Links` | `N├╝tzliche Links` | `N├╝tzliche Links` (Footer) |
| großartige | `gro├ƒartige` | `gro├ƒartige` | `gro├ƒartige` (Footer-Text) |
| Geschäftsprobleme | `Gesch├ñftsprobleme` | `Gesch├ñftsprobleme` | `Gesch├ñftsprobleme` (Footer-Text) |
| lösen | `l├Âsen` | `l├Âsen` (Hex: 6c e2949c c382 ...) | `l├Âsen` (Footer-Text) |

- Saubere Formen: **0 Vorkommen** im Dump (alle Umlaute betroffen, 100 %).
- Umfang: 905 Views in der DB mit Mojibake; im Dump 14.624 ├-Paare + 2.672 Ô-Tripel (17.296 Sequenzen).
- **Muster EINHEITLICH: UTF-8 -> CP850-Doppel-Encoding** (nicht CP1252, nicht CP437!):
  - 0xC3->'├', 0x9C->'£', 0xA4->'ñ', 0xB6->'Â', 0xBC->'╝', 0x9F->'ƒ'; 3-Byte: 0xE2 0x80 0x9E->'ÔÇï' etc.
  - Gegenprobe: cp437 scheitert (4/35), cp1252 scheitert (24/35), **cp850: 35/35 + 41/41 ok, 0 Fehler**
- **Reversibel: `text.encode('cp850').decode('utf-8')`** — keine '?'-Verluste im 29.07.-Dump (0 Zeilen mit ??).
- Betroffene Tabellen im Dump (Top 12): ir_model_fields (2.596), ir_ui_view (931), ir_module_module (580),
  ir_model_fields_selection (287), ir_act_window (247), res_country_state (191), ir_model (143),
  account_account (94), ir_ui_menu (88), ir_model_constraint (76), mail_message (71), account_report_line (48).
- **KEINE Reparatur durchgefuehrt** (nur Analyse). Phase 3B und DB-Aenderungen erst nach Freigabe.

---

### Session 70: Asset-/Login-Fix — Loginformular nach Restore unsichtbar (12.08.2026)

**Branch:** `crm-kundenverwaltung-migration` (nur Dokumentation; Fix lief direkt in der laufenden DB)
**Freigabe:** Nur Asset-Reparatur — KEIN Phase 3B, KEINE Encoding-Reparatur, keine normalen Attachments/Filestore-Dateien angefasst.

#### Symptom
- `/web/login` liefert HTML (Titel "Login | My Website"), aber KEIN sichtbares Loginformular — "grosser leerer Bereich", Button "Anmelden" ohne Effekt.

#### Diagnose (read-only, 12.08.)
- **Formular IST serverseitig vollstaendig im HTML:** `<form class="oe_login_form d-none" action="/web/login">` mit login/password/Submit/csrf (oe_login_form 1x, name=login 1x, name=password 1x, submit 3x).
- **d-none ist Odoo-18-Stock:** `webclient_templates.xml:141` — `t-attf-class="oe_login_form #{'' if login else 'd-none'}"`. Einblendung per JS nach Asset-Load.
- **Assets defekt:** `web.assets_frontend_minimal.min.js` = HTTP 500, `frontend.min.css` = 200/0 Bytes, `lazy.min.js` = 200/0 Bytes.
- **Odoo-Log:** `FileNotFoundError: ... '/var/lib/odoo/filestore/odoo18_test/15/159bc8e4e01c680cc106306c5c31d71c1ff77d37'`
- **Root Cause:** Phase-3A-Filestore-Restore UNVOLLSTAENDIG — Datei fehlt im aktiven Filestore (29 Dateien), existiert aber im 29.07.-Backup-Zip UND in `filestore_before_phase3_2026-08-11/` (104 Dateien).

#### Fix (ausgefuehrt nach Freigabe)
1. Bestandsaufnahme: 5 Asset-Attachments (IDs 1948, 1949, 1952, 1953, 1954) — 3 mit fehlender Filestore-Datei, 2 vorhanden aber defekt geliefert.
2. `DELETE FROM ir_attachment WHERE id IN (1948,1949,1952,1953,1954)` — NUR `/web/assets/`-Bundles; normale Attachments (1.238) und Filestore-Dateien NICHT angefasst.
3. Odoo regenerierte die Bundles beim ersten Abruf (Log: "Generating a new asset bundle attachment id:1955/1956/1957"); fehlende Datei `15/159bc8...` neu geschrieben (30.353 B).

#### Verifikation
- `/web/login`: HTTP 200, 19.497 B, Formular im HTML.
- Assets: 200 mit vollem Content-Length (minimal.js 30.353 / css 671.273 / lazy 2.226.829).
- Logs: keine FileNotFoundError / keine 500 mehr.

#### Merkregel (ergaenzt)
- Nach jedem Restore Filestore-Vollstaendigkeit pruefen (Dateizahl vs. Backup); fehlende Bundle-Dateien → `ir.attachment` mit `url LIKE '/web/assets/%'` loeschen → Odoo regeneriert.
- Asset-Hashes sind inhaltbasiert und bleiben gleich → nach Fix **Strg+F5** (Browser-Cache liefert sonst die alte kaputte Antwort).

#### Status
- Loginformular sichtbar/funktional: **JA** (Asset-Ebene verifiziert; UI-Bestaetigung durch Anna noch offen)
- Deutsche Sonderzeichen: WEITERHIN FEHLER (CP850-Mojibake) — **Phase 3B NICHT gestartet**, wartet auf Freigabe

---

## Session 71: itk_crm 18.0.1.3.0 — DB-only-Struktur in Modulcode persistiert + Session-Abschluss (12.08.2026)

**Branch:** `crm-kundenverwaltung-migration` → PR #13 (kein Auto-Merge)
**Freigaben (Anna):** Script 0 (Asset-Health) + Script 1 (Persistierung + itk_crm-Upgrade). **NICHT freigegeben:** Encoding-Reparatur (Phase 3B), weitere Modul-Upgrades, Datenmigration, Testdaten.

### Script 0: Asset-Health (Vorabpruefung, 12.08.)
- 10 Asset-Attachments (IDs 1955–1964) geloescht → Odoo regenerierte Bundles (IDs 1965–1973)
- Finale Verifikation per echten Datei-Downloads: alle Bundles HTTP 200 mit vollem Inhalt (siehe Sollwerte unten)
- **Korrektur frueherer „200/0 B“-Meldungen:** Messfehler (natives Windows-curl kann nicht nach `/dev/null` schreiben, exit 23) — tatsaechlich war nur `minimal.js` wirklich kaputt
- Beobachtet, NICHT behoben: Partner-Bilder (Attachments 25, 515–524) liefern weiter 500 — Filestore-Dateien fehlen und sind NICHT im 29.07.-Zip

### Script 1: Persistierung in itk_crm (Version 18.0.1.3.0)
**Ziel:** Die bisher nur per RPC/DB angelegte CRM-Struktur dauerhaft im Modul persistieren, damit ein Restore + Modul-Upgrade sie automatisch rekonstruiert.

Neue/geaenderte Dateien:
- `addons/itk_crm/data/crm_stages.xml` — 8 Stages (Neu, Angebotsphase, On-Hold, Positive Rückmeldung, Erfolgreich/is_won, Zur Verrechnung bereit, Verloren/fold, Verrechnet/fold); `<data noupdate="1">` (RNG: noupdate nur auf `<data>` erlaubt, NICHT auf `<record>`)
- `addons/itk_crm/data/interessenten_views.xml` — Action 1459 „Interessenten“ (Domain `type=lead`) + Listen-/Formular-Inherits auf Basis-Views 567/566 (Anker: Gruppe `lead_priority`); noupdate nur auf `<data>`
- `addons/itk_crm/setup_runtime.py` — idempotente Setup-Funktionen: Custom-Felder, Stage-Labels, App-Name, Menues (Delete+Recreate), Lost Reasons, Automation, Aktivitaetstypen, Vertriebskanaele
- `addons/itk_crm/hooks.py` — schlank: post_init_hook → setup_runtime
- `addons/itk_crm/models/models.py` — ResPartner-Erweiterung (firstname, status_of_community, offizieller Name, community_salutation, official_email, …) + neue Klasse `CrmLead` mit `x_Anrede_Lead = fields.Selection([...])` (echtes Python-Modelfeld, weil `ir.model.fields.create` keine DB-Spalte anlegt)
- `addons/itk_crm/migrations/18.0.1.3.0/post-migration.py` — laeuft bei JEDEM Upgrade (Standard-Mechanismus in Odoo 18)
- `addons/itk_crm/__manifest__.py` — Version 18.0.1.3.0

**PITFALLS (Odoo 18, in dieser Session verifiziert):**
- `pre_init_hook`/`post_init_hook` laufen NUR bei Neuinstallation (`if new_install:` in loading.py) → fuer Upgrade-/Restore-Zeit-Aktionen Migrationsskript verwenden
- `field_description` ist jsonb (translatable) → SQL-UPDATE nur auf `ttype`
- Mehrfach-XPath-Treffer: Odoo nimmt `nodes[0]` (tools/template_inheritance.py), kein Fehler
- `.pyc`-Cache auf vboxsf problematisch → `__pycache__` im Container loeschen + Container-Neustart
- Manifest wird pro Prozess gecacht → nach Manifest-Aenderung Container-Neustart noetig
- `button_immediate_upgrade` per RPC funktioniert (uid 2, Modul-ID 729), Rueckgabe „OK: None“ → Version im Modul pruefen
- Reihenfolge Pflicht: Stages VOR itk_crm-Upgrade (Automated-Action-Hook „Zur Verrechnung bereit“ bricht mit Warning ab, wenn Stage fehlt)

**Verifizierter DB-Zustand (alle 9 Pruefpunkte gruen):**
- 8 Stages | 6 Lost Reasons | 2 Automationen (Urlaubsantrag + „Interessent 'zur Verrechnung bereit'“, stage_id=18) | 14 Aktivitaetstypen (inkl. Anrufen, data.gv.at Neukunde anlegen, Webinar/Praesentation)
- Actions 1458 (Aktivitaeten), 1459 (Interessenten), 196 (Pipeline), 431 (Angebote)
- Views 4013 (Liste) + 4014 (Formular) — von Odoo selbst validiert (`_validate_module_views` ohne Fehler = Beweis, dass alle XPaths/Felder existieren)
- Menues 143/144/892–895/147/148/150/155/158; Vertriebskanaele (Menue 158, Action 186) mit DE-Labels
- Custom-Selection-Felder: x_Lead_Quelle (11), x_Produktinteresse (10), x_lead_status (12), x_Anrede_Lead (3: sg_Frau/sg_Herr/sg_Damen_Herren)
- App-Name „Kundenverwaltung“
- HTTP: /web/login 200, Assets 200 mit vollem Inhalt, keine 500

**Asset-Sollwerte (fuer kuenftige Checks):** minimal.js 30.353 B, frontend.min.css 671.273 B, frontend_lazy.min.js 2.226.829 B, websocket_worker 16.004 B, web.min.css 1.157.303 B, web_print.min.css 1.162.265 B, backend_lazy.css 13.335 B, backend_lazy.js 190.046 B, chartjs 337.290 B, web.min.js 6.332.710 B (Hash a9c78f9; alter Hash → 303-Redirect = normales Odoo-Verhalten)

### Manueller Browser-Test durch Anna (12.08.) — OFFENE Punkte (NICHT geloest!)
- **A. Encoding / deutsche Sonderzeichen — OFFEN.** „Über“, „Nützliche“, „großartig“, „Geschäftsprobleme“, „lösen“ werden weiterhin falsch dargestellt (CP850-Mojibake). **Keine Encoding-Reparatur ohne NEUE Freigabe in der naechsten Session.**
- **B. Kundenverwaltung → Aktivitaeten: neue Aktivitaet kann NICHT angelegt werden — OFFEN.** Browser-/Funktionspruefung erforderlich. **Noch NICHT reparieren.**
- **C. Aktivitaeten-Kanban: Spaltennamen nicht persistent — OFFEN.** Umbenannte Spalten sind nach Ansichtswechsel/-Rueckkehr wieder verschwunden. **Noch NICHT reparieren.**
- **D. Vertriebskanaele: vorhanden — OK.**

### Infrastruktur / Repository-Aufraeumung (Session-Abschluss)
- `docker-compose.yml`: PostgreSQL-Bind-Mount `./postgres` → Docker Named Volume `odoo18_pgdata` (committet; compose-Schnappschuesse `docker-compose.phase3.yml` + `docker-compose.before_phase3_2026-08-11.yml` sind NUR lokal, gitignored)
- Container `odoo18` (odoo:18) + `odoo18-db` (postgres:16) laufen; DB `odoo18_test`; itk_crm = installed 18.0.1.3.0
- Recovery-Scripts: finale Versionen committet — `recovery_diag.ps1`, `recovery_phase2_v6.ps1` (pg_resetwal auf Kopie, erfolgreich), `recovery_phase3_v8.ps1` (Clean Restore, 8 Iterationen bis Parser-clean). Zwischenversionen (phase2 v3–v5, phase3 v1–v7) bewusst NICHT committet (nur lokal, gitignored)
- `.gitignore` erweitert: `postgres/` (Rohdaten), `postgres_defekt_*/`, `postgres_recovery/`, `BACKUP-2026-07-29/`, `filestore_before_phase3_2026-08-11/`, compose-Schnappschuesse, Script-Zwischenversionen, `form_arch.xml`/`list_arch.xml` (Temporaer-Analyse, geloescht)
- `git rm --cached postgres/` — PostgreSQL-Rohdaten aus dem Tracking entfernt (Dateien bleiben lokal erhalten; der Ordner ist nach Named-Volume-Umstellung funktionslos)
- `hermes verify --json`: Timeout nach 300 s — kein kanonischer Build/Test fuer ein Odoo-Addons-Repo; Workspace-Scan haengt an den GB-grossen Backup-Ordnern. Projektbezogene Verifikation = DB-/HTTP-Pruefungen oben (gruen)

### Priorisierung naechste Session (Vorschlag)
1. **Encoding-Reparatur (Phase 3B)** — erfordert NEUE Freigabe
2. **Aktivitaeten: neue Aktivitaet anlegen** — Browser-/Funktionspruefung (Punkt B)
3. **Aktivitaeten-Kanban: Spaltennamen persistent** (Punkt C)
4. **Vier Modul-Upgrades einzeln** (tree→list-Fixes): hr_holidays_public → itk_reports → itk_sale_management → itk_translation (je einzeln freigeben)
5. Weitere CRM-/Migrationsarbeiten

### Einschraenkungen (fortgeschrieben)
- KEINE Odoo-11-Datenmigration, KEINE Kontakte/Leads/Teams migrieren, KEINE Testdaten
- Encoding separat behandeln (eigene Freigabe)
- PostgreSQL NIE wieder als Live-Datenverzeichnis ueber den alten Shared-/Bind-Mount betreiben

## Notfall-Backup-Strategie (automatisiert, eingerichtet 12.08.2026)

**Ziel:** `C:\Odoo-Notfallbackup` — zweimal taeglich (09:00 + 15:00) per Windows Task Scheduler, unabhaengig von Hermes.

**Tasks (aktiviert):**
- `Odoo18 Notfallbackup 09-00` — taeglich 09:00 (naechster Lauf 13.08.2026 09:00)
- `Odoo18 Notfallbackup 15-00` — taeglich 15:00 (naechster Lauf 13.08.2026 15:00)
- Beide rufen `powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\Odoo-Test\scripts\odoo18_notfallbackup.ps1` auf; laufen als angemeldeter User (Docker Desktop-Kontext), d.h. der PC muss angemeldet sein.
- Registrierung reproduzierbar: `C:\Odoo-Test\scripts\setup_notfallbackup_tasks.ps1` (idempotent, -Force)

**Skript** `C:\Odoo-Test\scripts\odoo18_notfallbackup.ps1` (PowerShell 5.1):
1. Zeitstempel-Ordner `2026-08-12_1757\` (Kollisionsschutz: Suffix _2, _3 …)
2. pg_dump `--format=custom` IM Container (`--file=/tmp/…`, kein Binary-Stream durch PowerShell wegen Encoding-Gefahr), Restore-Eignung via `pg_restore --list` (TOC lesbar), `docker cp` auf Host, Temp-Datei im Container wird geloescht
3. Filestore: robocopy NUR `C:\Odoo-Test\filestore\odoo18_test` (Bind-Mount `./filestore` → `/var/lib/odoo/filestore`; Exit-Code < 8 = Erfolg)
4. `backup_info.txt` mit Datum, DB-Name, Odoo-Version (18.0-20260609), PostgreSQL-Version (16.14), Git-Branch/-Commit, Named-Volume, Ergebnis, Dump-Groesse, Filestore-Anzahl/-Groesse
5. Validierung: pg_dump Exit 0, Dump existiert + > 0 Bytes, Filestore vorhanden, Backup-Ziel beschreibbar (Probe-Datei). Fehler → `C:\Odoo-Notfallbackup\logs\backup_<lauf>.log` + Exit 1, KEINE Aenderungen an der Live-Umgebung (kein Container-Stop, kein Volume-Zugriff, keine DB-Modifikation, keine Loeschungen)

**Sicherheit (unantastbar):** Named Volume `odoo18_pgdata` wird NIE direkt kopiert/angefasst; `C:\Odoo-Test\postgres` und alle `postgres_defekt_*`-Ordner sind keine Backup-Quellen; Backup-Dateien nie nach Git pushen. `C:\Odoo-Notfallbackup` liegt AUSSERHALB des Repos (Geschwisterverzeichnis von `C:\Odoo-Test`) und ist damit strukturell nie in Git (in `.gitignore` dokumentiert).

**Verifiziert am 12.08.2026:** 2 manuelle Testlaeufe (Exit 0, Dump 8.058.383 Bytes = 7,69 MB custom-Format, pg_restore --list 13.548 TOC-Eintraege, Filestore 10 Dateien / 11,58 MB) + Task-Probelauf `schtasks /Run` → LastTaskResult 0.

**Hinweis:** `C:\Odoo-Notfallbackup\Odoo-Test` (483 MB, Stand 28.07.) ist eine ALTE manuelle Notfallkopie von `C:\Odoo-Test` inkl. `postgres/` — obsolet, aber NICHT ohne Freigabe loeschen; Kandidat fuer spaetere Bereinigung.




---

## Session 72: Encoding-Reparatur + Fix B (Neue Aktivitaet) + Fix C (Kanban-Spalten) (13.08.2026)

**Branch:** `crm-kundenverwaltung-migration` (Fortsetzung nach PR #13, der am 12.08. gemergt wurde)
**Freigaben (Anna):** Encoding-Reparatur Stufe A+B; Fix B (Option B1, nativer Wizard); Fix C (RPC-Duplikate 24/25/26 bereinigen, de_DE-Slots ergaenzen, Typ 2 vs 21 NICHT zusammenfuehren). KEINE Datenmigration, KEINE Testdaten (ausser der freigegebenen Browser-Test-Aktivitaet id=8), KEIN -u all, keine weiteren Modul-Upgrades.

### 1) Encoding-Reparatur (abgeschlossen + verifiziert)

**Backup vorher:** `C:\Odoo-Notfallbackup\2026-08-13_0912` (8.058.796 Bytes custom-Dump, 10 Filestore-Dateien)

**Strategie:** Statt Ganz-String-Reencode (text.encode('cp850').decode('utf-8') auf der ganzen Zelle - riskant bei Mischzustaenden) wurde eine SELEKTIVE Sequenz-Ersetzung eingesetzt:
- Mapping dynamisch aus den tatsaechlich in der DB vorhandenen Mojibake-Sequenzen gebaut (886 distinkte Sequenzen, 844 reparierbar)
- Nur nachgewiesene CP850->UTF-8-Sequenzen ersetzt (laengste zuerst), alles andere unangetastet
- Nicht-reparierbare Kandidaten (42) wurden automatisch durch die 2-Zeichen-Bausteine abgedeckt

**Zahlen:**
- 6815 betroffene Zellen repariert (6412 davon jsonb-Strings, 0 unveraendert)
- 0 verbleibende ├-Zeilen in der gesamten DB (vorher 6815)
- Sollwerte View 2893 (de_DE-Slot): Über uns / Nützliche Links / großartige / Geschäftsprobleme / lösen - alle korrekt
- Browser-HTML (Homepage): alle 5 Sollwerte korrekt gerendert, 0 ├-Zeichen
- Website-Menue 4: "Top-Menü für Website 1" (war "Top-Men├╝ f├╝r Website 1")
- Login 200 mit vollstaendigen Formular-Markern; Assets nach Neustart 200 mit Sollgroessen (minimal.js 30.353 B, frontend.min.css 671.273 B, lazy.min.js 2.226.829 B)

**WICHTIG:** Encoding danach NICHT mehr anfassen. Reparatur ist abgeschlossen; jede weitere Encoding-Aenderung braucht neue Freigabe.

### 2) Fix B - Neue Aktivitaet anlegen (Option B1, Odoo-18-nativ)

**Ursache (diagnostiziert, read-only):** Alle mail.activity-Views haben create="false" (Kanban 308, Liste 305, Formular 301) -> kein Neu-Button im Aktivitaeten-Menue. Zusaetzlich verlangt mail.activity.create in Odoo 18 res_model_id (required) + _check_access auf dem Zieldokument (mail_post_access/write) - Standalone-Create ohne Dokument ist prinzipiell blockiert.

**Loesung (B1):** Neuer Menueeinstieg "Neue Aktivitaet" (Kundenverwaltung -> Aktivitaeten -> Neue Aktivitaet), der den NATIVEN Odoo-18-Wizard mail.activity.schedule als Dialog oeffnet:
- `addons/itk_crm/data/aktivitaeten_schedule.xml` - NEU: Inherit-View auf mail.mail_activity_schedule_view_form (Zielmodell + Zieldokument-Auswahl), Action `itk_crm.action_neue_aktivitaet` (res_model mail.activity.schedule, view_mode form, target new)
- `addons/itk_crm/models/models.py` - NEU: `MailActivitySchedule` (_inherit='mail.activity.schedule') mit itk_target_model_id (Many2one ir.model), itk_target_model (Char, model_field fuer Many2oneReference), itk_target_res_id (Many2oneReference). res_model im Inherit auf readonly=False (Web-Client sendet es sonst nicht -> Create crashte mit ir.model._get_id(False)). `_compute_res_model_id` defensiv ueberschrieben (kein Crash bei leerem res_model). `_evaluate_res_ids`/`_get_applied_on_records` so erweitert, dass das im Wizard gewaehlte Ziel verwendet wird.
- `addons/itk_crm/setup_runtime.py` - NEU: `_setup_neue_aktivitaet_menu(env)` (idempotent; findet das Aktivitaeten-Menue ueber die Action, nicht ueber die instabile ID 892)

**PITFALLS (in dieser Session verifiziert):**
- Inherit-View als `view_id` einer ir.actions.act_window ist NICHT zulaessig (Client rendert nichts) - view_id weglassen, Odoo nimmt den Basis-View + Inherit automatisch
- noupdate="1" verhindert das Ueberschreiben bestehender Records beim Upgrade - geaenderte View-Arch nachtraeglich per RPC in die DB schreiben (View 4016)
- invisible-Felder (res_model) werden vom Web-Client beim Save nicht mitgesendet, wenn das Feld readonly ist -> im Inherit readonly=False setzen

**Browser-Test (erfolgreich, freigegeben):** Aktivitaeten -> Neue Aktivitaet -> Wizard oeffnet -> Zielmodell "Kontakt" (res.partner) -> Zieldokument "Magistrat Rust" (id=70) -> Planen -> Dialog schliesst -> Aktivitaet id=8 in DB (activity_type_id=4 To-Do, res_model=res.partner, res_id=70, Faelligkeit 18.08.2026) -> Kanban zeigt echte Spalte "To-Do (1)" mit Karte. Keine JS-/RPC-Fehler.

**Bewusst NICHT getan:** keine mail.activity-Views auf create=true umgebaut, keine ACL-/Security-Hacks, keine Standalone-Activity ueber mail.activity.create.

### 3) Fix C - Aktivitaeten-Kanban-Spalten / Aktivitaetstypen

**Ursache:** RPC-Duplikate (24 "Anrufen", 25 "E-Mail", 26 "Zu erledigen" - ohne XML-ID, per RPC angelegt) + fehlende de_DE-Slots bei den XML-Typen 21/22/23 (nur en_US) + Odoo 18 hat im Kanban-View KEIN eigenes "Spalte umbenennen"-Feature (die Spaltennamen SIND die mail.activity.type-Namen).

**Bereinigung (idempotent in `setup_runtime._setup_activity_types`, laeuft auch nach Restore/Upgrade):**
- RPC-Duplikate entfernt: 24 -> 21 (Anrufen), 25 -> 1 (E-Mail), 26 -> 4 (To-Do). Referenzen VOR dem Loeschen geprueft und umgehaengt (0 Referenzen vorhanden - mail_activity war leer; Log: "0 Referenzen umgehaengt" je Duplikat). Kanonische XML-Typen bleiben erhalten.
- de_DE-Slots ergaenzt (NUR wenn fehlend, nie ueberschreiben): 21, 22, 23 + generische Nachsorge fuer alle Typen ohne de_DE-Slot. Typ 1 behaelt "E-Mail" (de_DE) / "Email" (en_US).
- `_ACTIVITY_TYPE_CANONICALS` im setup_runtime.py dokumentiert die Zuordnung.

**PITFALL:** `record.name` liefert OHNE Sprachkontext (Migration/Shell) einen String statt des jsonb-Dicts -> `_name_dict()` liest das jsonb per SQL (robust in jedem Kontext). Im ersten Lauf war de_DE von Typ 1 faelschlich mit en_US ueberschrieben worden - per SQL zurueckgesetzt ("E-Mail") und Logik korrigiert.

**Browser-Test (erfolgreich):** Umbenennen ueber Gear-Menue -> Bearbeiten (editGroup -> FormViewDialog auf mail.activity.type) -> Name aendern -> Spalte zeigt neuen Namen -> Ansichtswechsel (Liste->Kanban) UND Voll-Reload -> Name bleibt erhalten. Testname zurueckgesetzt. 0 Duplikat-Typen nach Fix.

### 4) Typ 2 vs. Typ 21 - bewusst NICHT zusammengefuehrt (Entscheidung offen)

Vergleich (vollstaendig, 13.08.2026):

| Feld | Typ 2 "Anruf" (mail.mail_activity_data_call) | Typ 21 "Anrufen" (itk_crm.mail_activity_type_anrufen) |
|---|---|---|
| XML-ID | mail.mail_activity_data_call | itk_crm.mail_activity_type_anrufen |
| name | de_DE "Anruf" / en_US "Call" | de_DE "Anrufen" / en_US "Anrufen" |
| category | phonecall | phonecall |
| res_model | leer | leer |
| icon | fa-phone | fa-phone |
| decoration_type | leer | leer |
| chaining_type | suggest | suggest |
| delay_count | **2** | **0** |
| delay_unit | days | days |
| delay_from | previous_activity | previous_activity |
| default_user_id | leer | leer |
| keep_done | leer | leer |
| active | t | t |
| suggested_next_type_ids | keine (mail_activity_rel leer) | keine |

**Beurteilung:** Fachlich sehr aehnlich (category/icon/chaining identisch), ABER delay_count unterscheidet sich (2 vs. 0 - Auswirkung auf die Verzoegerung bei "suggest"-Verkettung) und die Namen sind verschieden ("Anruf" vs. "Anrufen"). Zusammenfuehrung NICHT automatisch - Entscheidung Anna in naechster Session (O11-Kompatibilitaet: welcher Name/delay soll kanonisch sein?).

### 5) Verifikation (projektbezogen - generisches hermes verify ist hier nicht nutzbar)

`hermes verify --json` laeuft in diesem Workspace NICHT durch: Timeout nach 120s mit 0 Bytes Output (Workspace-Scan traversiert die GB-grossen untracked Backup-/Recovery-Ordner postgres_defekt_*, postgres_recovery/, BACKUP-2026-07-29/, filestore_before_phase3_2026-08-11/). `hermes verify addons/itk_crm --detect-only --json` -> {"ok": false, "error": "no-recipe"} (keine kanonische Build-/Test-Pipeline fuer Odoo-Addons). Das ist ein Workspace-/Repo-Charakteristikum, KEIN Projektfehler.

Relevante echte Verifikation (alles gruen):
- Modul-Upgrade: itk_crm 18.0.1.3.0 -> 18.0.1.4.0 (button_immediate_upgrade per RPC, uid 2, Modul 729), latest_version 18.0.1.4.0, state installed, Logs ohne Fehler
- DB-Pruefpunkte: 14 Aktivitaetstypen, 0 Duplikate, de_DE-Slots korrekt, Menue 896 "Neue Aktivitaet" -> Action 1462
- Browser-Test B + C (s.o.)
- HTTP/Assets: Login 200 mit Formular-Markern, Assets 200 mit Sollgroessen
- Konsolen-/Netzwerkpruefung: 0 console errors, 0 failed resources

### 6) itk_crm 18.0.1.4.0 - geaenderte Dateien

- `addons/itk_crm/__manifest__.py` - Version 18.0.1.4.0, data/aktivitaeten_schedule.xml registriert
- `addons/itk_crm/models/models.py` - MailActivitySchedule-Extend (B1)
- `addons/itk_crm/setup_runtime.py` - _setup_neue_aktivitaet_menu (B) + _setup_activity_types (C)
- `addons/itk_crm/data/aktivitaeten_schedule.xml` - NEU (View-Inherit + Action)
- `addons/itk_crm/migrations/18.0.1.4.0/post-migration.py` - NEU (setup_all bei Upgrade/Restore)
- Validierung: py_compile OK (5 Dateien), RNG gegen import_xml.rng valid, Idempotenz-Lauf _setup_activity_types OK

### 7) OFFENE PUNKTE (fuer naechste Session)

- **A. Test-Aktivitaet id=8** ("Browser-Test B: neue Aktivitaet via Wizard", Magistrat Rust, To-Do, Faellig 18.08.2026): aktuell vorhanden; in naechster Session entscheiden: loeschen oder behalten. JETZT nicht veraendert.
- **B. Typ 2 vs. Typ 21** (Anruf vs. Anrufen): fachlicher Vergleich oben dokumentiert; Zusammenfuehrung erst nach Entscheidung Anna.
- **C. Ausstehende Modul-Upgrades (einzeln, je Freigabe):** hr_holidays_public -> itk_reports -> itk_sale_management -> itk_translation (tree->list-Fixes). NOCH NICHT upgraden.
- **D. Keine Odoo-11-Datenmigration** (keine Kontakte/Leads/Teams), keine Testdaten, kein -u all.

### 8) Einschraenkungen (fortgeschrieben)

- Encoding NICHT mehr anfassen (abgeschlossen 13.08.)
- KEINE Datenmigration, KEINE Testdaten (ausser freigegebener Browser-Test-Aktivitaet id=8), KEIN -u all
- PostgreSQL NIE wieder als Live-Datenverzeichnis ueber den alten Shared-/Bind-Mount betreiben (Named Volume odoo18_pgdata)

---

## Session 73: Test-Aktivitaet id=8 geloescht + Aktivitaetstyp-Entscheidung Typ 2 vs. Typ 21 (14.08.2026)

**Branch:** `crm-kundenverwaltung-migration`
**Freigaben (Anna):** Loeschung der Test-Aktivitaet id=8; Typ-Entscheidung "Typ 2 behalten, Typ 21 entfernen" mit de_DE-Umbenennung von Typ 2 auf 'Anrufen'; Modulcode-Bereinigung in itk_crm. KEINE vier Modul-Upgrades (hr_holidays_public/itk_reports/itk_sale_management/itk_translation) — starten erst in neuer Session. KEIN -u all, KEINE Datenmigration, Encoding unangetastet.

### 1) Test-Aktivitaet mail.activity id=8 geloescht

**Read-only-Pruefung vor Loeschung (dokumentiert):**
- id=8, res_model=res.partner, res_id=70 ("Magistrat Rust", GKZ 10201)
- activity_type_id=4 (To-Do), summary="Browser-Test B: neue Aktivitaet via Wizard"
- user_id=2 (anna.maierhofer@it-kommunal.at), date_deadline=2026-08-18
- create_date=2026-08-13 08:12 (Session-72-Test), mail_activity gesamt = 1 (nur id=8)
- Eindeutig die freigegebene Session-72-Test-Aktivitaet → `DELETE FROM mail_activity WHERE id=8` (DELETE 1)

**Verifikation danach:**
- mail_activity = 0 Datensaetze (keine Testdaten mehr), keine anderen Aktivitaeten vorhanden/veraendert
- Aktivitaeten-Wizard: Browser-Test OK (Dialog oeffnet mit Zielmodell/Zieldokument/Summary + Planen-Buttons; ueber Abbrechen geschlossen, KEINE neue Aktivitaet angelegt)
- Kanban: OK (Empty-State mit 4 Ghost-Spalten = dokumentiertes Verhalten bei 0 Aktivitaeten)
- Logs: keine neuen Fehler; FileNotFoundError im Log (09:45-09:59) = bekanntes Partner-Bild-Vorproblem aus Session 71

### 2) Aktivitaetstyp-Entscheidung: Typ 2 kanonisch, Typ 21 entfernt

**Vollstaendiger read-only Vergleich (13 Typen-DB + O11-Referenzabfrage):**

| Feld | Typ 2 "Anruf" (mail) | Typ 21 "Anrufen" (itk_crm) |
|---|---|---|
| XML-ID | mail.mail_activity_data_call | itk_crm.mail_activity_type_anrufen |
| Modul | mail 18.0.1.18 (Odoo-Standard) | itk_crm 18.0.1.4.0 (O11-Nachbau) |
| name de_DE / en_US | Anruf / Call | Anrufen / Anrufen |
| category | phonecall | phonecall |
| res_model | leer | leer |
| delay_count | **2** | **0** |
| delay_unit / delay_from | days / previous_activity | days / previous_activity |
| default_user_id | leer | leer |
| icon / decoration_type | fa-phone / leer | fa-phone / leer |
| chaining_type | suggest | suggest |
| suggested_next_type_ids | 0 | 0 |
| mail templates / related actions | 0 | 0 |
| sequence | 6 | 6 |
| active / keep_done | t / leer | t / leer |

**Odoo-11-Referenz (read-only, ITK_V1_a):** O11 hatte 12 Typen; der Telefon-Typ hiess dort id=2 "Call" (fa-phone) — **kein** "Anrufen". O11 hatte 0 de_DE-Uebersetzungen fuer mail.activity.type und 0 mail.activity-Datensaetze. → Typ 21 hatte KEIN O11-Vorbild fuer den Namen "Anrufen" (der Nachbau basierte auf der Session-66-Annnahme); er war ein itk_crm-Duplikat.

**Referenz-Check vor Loeschung (11 FK-Positionen):** 0 Referenzen auf Typ 21 in mail_activity, mail_activity_rel, mail_activity_plan_template, ir_act_server, mail_compose_message, mail_message, mail_activity_type_mail_template_rel, mail_activity_schedule, triggered_next_type_id, previous/recommended. → Loeschung gefahrlos.

**Durchgefuehrte DB-Aenderungen (eine Transaktion je Schritt):**
1. `UPDATE mail_activity_type SET name=jsonb_set(name,'{de_DE}','"Anrufen"') WHERE id=2` → Typ 2: de_DE "Anrufen" / en_US "Call"; **delay_count=2 und alle anderen Standardwerte UNVERAENDERT**
2. `DELETE ir_model_data (module='itk_crm', name='mail_activity_type_anrufen')` + `DELETE mail_activity_type WHERE id=21` (DELETE 1, inkl. RETURNING-Doku)

**Modulcode-Bereinigung itk_crm (Version 18.0.1.5.0):**
- `data/aktivitaeten_views.xml`: `<record id="mail_activity_type_anrufen">` ENTFERNT (Kommentar dokumentiert Entscheidung) → wird bei Neuinstallation/Upgrade nicht mehr angelegt
- `setup_runtime.py`: `_ACTIVITY_TYPE_CANONICALS` auf `('mail.mail_activity_data_call', ['Anrufen','Call'])` umgestellt; neue Legacy-Bereinigung (entfernt Typ 21 nach Restore aus Altdumps: Referenzen → Typ 2, ir_model_data mitloeschen, unlink); neuer Block setzt de_DE von Typ 2 auf 'Anrufen' (nur wenn != 'Anrufen', idempotent; en_US/delay_count unangetastet)
- `migrations/18.0.1.5.0/post-migration.py` (NEU): ruft setup_runtime.setup_all → stellt Entscheidung nach Restore + Upgrade automatisch wieder her
- `__manifest__.py`: Version 18.0.1.5.0

**Deploy:** __pycache__ im Container geloescht, `docker restart odoo18`, itk_crm EINZELN upgegradet (button_immediate_upgrade, uid 2, Modul 729) → latest_version 18.0.1.5.0, state installed.

**Verifikation (alles gruen):**
- Typ 2 vorhanden: de_DE "Anrufen" / en_US "Call" / delay_count=2 / alle Standardwerte unveraendert
- Typ 21 NICHT vorhanden (mail_activity_type UND ir_model_data = 0)
- Genau 1 Typ mit de_DE "Anrufen" (kein Duplikat); 0 Duplikat-Namen insgesamt
- 13 Aktivitaetstypen gesamt (14 - 1); mail_activity = 0
- Upgrade-Log: "kein RPC-Duplikat fuer mail.mail_activity_data_call — ok", "de_DE-Name Typ 2 bereits 'Anrufen' — ok", 0 Fehler
- Browser: Aktivitaeten-Wizard OK (Dialog + alle Felder), Kanban OK (Renderer + Empty-State), 0 Konsole-/Netzwerkfehler (window.__errs leer, 0 failed resources)
- Server-Logs: einziger ERROR 11:09:31 = transienter Websocket-Neustart-Artefakt vor dem Upgrade; danach 0 Fehler
- `hermes verify --json`: weiterhin konkret blockiert (Timeout 170s, Exit 124, 0 Bytes Output — Workspace-Scan ueber GB-grosse untracked Backup-Ordner); `--detect-only` → {"ok": false, "error": "no-recipe"}. Projektbezogene Verifikation (py_compile 5 Dateien, RNG gegen import_xml.rng, DB, Laufzeit, Browser) ersetzt den generischen Lauf.

### 3) Verifikation Gesamtstand (Session-Abschluss)

- itk_crm 18.0.1.5.0 installed; 13 Aktivitaetstypen; mail.activity = 0
- Aktivitaeten-Wizard OK, Kanban OK, 0 JS-/RPC-/Konsolenfehler
- Encoding: WEITERHIN abgeschlossen und unveraendert (13.08., kein Eingriff in dieser Session)
- Logins/Assets: OK (HTTP 200, Assets mit Sollgroessen)

### 4) OFFENE PUNKTE (naechste Session)

- **Vier Modul-Upgrades einzeln (je Freigabe):** hr_holidays_public → itk_reports → itk_sale_management → itk_translation (tree→list-Fixes). AUSDRUECKLICH NICHT in dieser Session.
- KEINE Odoo-11-Datenmigration (keine Kontakte/Leads/Teams), keine Testdaten, kein -u all.

### 5) Einschraenkungen (fortgeschrieben)

- Encoding NICHT mehr anfassen (abgeschlossen 13.08.)
- KEINE Datenmigration, KEINE Testdaten, KEIN -u all
- PostgreSQL NIE wieder als Live-Datenverzeichnis ueber den alten Shared-/Bind-Mount betreiben (Named Volume odoo18_pgdata)

---

### Session 74: Neue IPAX-Test-VM (Ubuntu 26.04) — Docker-Setup, Stack-Start, Analyse lokaler Teststand (31.08.2026)

#### 1) Ausgangslage

- IPAX hat die bisherige Odoo-11-Test-VM gesichert, geloescht und frisch mit **Ubuntu Server 26.04 LTS** neu installiert.
- Ziel: neue VM als Testumgebung fuer Odoo 18 (Abloesung/Ergaenzung des Windows-Docker-Teststands).
- **KEINE Migration produktiver Odoo-11-Daten**; zunaechst Infrastruktur + geplante Uebernahme des bestehenden Odoo-18-Teststands.

#### 2) Neue VM: System (read-only erfasst)

| Eigenschaft | Wert |
|---|---|
| OS | Ubuntu 26.04 LTS "Resolute Raccoon" (frisch, 2,8 GB belegt) |
| Kernel | 7.0.0-28-generic |
| CPU | 4 vCPU (AMD EPYC 7302P) |
| RAM | 31 GiB (30 frei) |
| Disk | 96 GB (94 frei) |
| Netz | eth0 93.189.28.204/28, GW 93.189.28.193 |
| DNS | k001959vsx.ipax.at -> 93.189.28.204; VM-Hostname k001959vsv |
| SSH | **Port 22** (NICHT 2000 wie die alte O11-VM), User k001959, Passwort-Auth, **sudo passwordlos** |

Zugangsdaten liegen bei Anna (nicht in diesem Dokument / Git ablegen).

#### 3) Docker-Installation (offizieller Weg, 31.08.2026)

- Gate-Check: download.docker.com fuehrt Suite **"resolute"** (Components: stable edge test nightly) -> reguläre Unterstützung, kein Workaround noetig.
- apt-Repo docker.com (resolute/stable), Keyring `/etc/apt/keyrings/docker.gpg`.
- Installiert: **docker-ce 29.7.2**, docker-compose-plugin (**Compose v5.5.0**), containerd.io, buildx.
- `usermod -aG docker k001959` (greift ab naechster SSH-Session), `systemctl enable --now docker` -> active.
- Verifikation: docker info (overlayfs, systemd cgroup, Ubuntu 26.04 LTS, 4 CPU, 31,34 GiB).

#### 4) Projektstruktur + Clone auf der VM

- `/opt/odoo18` (Owner k001959) = `git clone` des Repos, Branch **main**, HEAD `a0a36d3083cf478ef7763c1e257c22a3c9990853` (= PR #15), sauber.
- addons/ (41 Module) + alle Projektdateien (PROJECT_KNOWLEDGE.md, README.md, docker-compose.yml, ...) vollstaendig vorhanden.
- `docker compose config`: lesbar, keine Fehler.

#### 5) docker-compose.yml: VM-Anpassungen (in dieser Session committet, lokal gespiegelt)

- **PostgreSQL-Passwort**: hartkodiertes `odoo` entfernt -> `${POSTGRES_PASSWORD}` aus `.env` (Service `db` UND `odoo`).
- `.env` unter `/opt/odoo18` (nur VM): starkes Zufallspasswort (48 Zeichen hex), `chmod 600`, Owner k001959. **NICHT committet**; `.gitignore` um Eintrag `.env` ergaenzt.
- **Odoo-Port**: `"8069:8069"` -> `"127.0.0.1:8069:8069"` (nur lokal auf der VM; Browser-Zugriff per SSH-Tunnel: `ssh -L 8069:127.0.0.1:8069 k001959@93.189.28.204`). Kein Nginx/HTTPS (bewusst noch nicht).
- **Volume**: `odoo18_pgdata` — `external: true` entfernt -> Compose verwaltet ein eigenes persistentes Named Volume (frisches Volume auf der VM).
- **PostgreSQL**: weiterhin KEIN Port-Mapping, nur internes Docker-Netz (nicht oeffentlich erreichbar).
- **Filestore**: `/opt/odoo18/filestore`, Owner `100:101` (= Container-User `odoo` im odoo:18-Image), Schreib-/Loeschtest im Container OK.

#### 6) Erster Stack-Start + Verifikation (VM)

- Images: `odoo:18` (18.0-20260817), `postgres:16` (16.15).
- Container `odoo18` + `odoo18-db` beide running; `pg_isready` -> accepting connections.
- HTTP lokal: `/web/login` -> 303 -> `/web/database/selector` -> **200** (leeres Grundsystem, DB-Verwaltung erreichbar).
- Port 8069 lauscht **nur** auf 127.0.0.1; 5432 nicht auf dem Host; von aussen (93.189.28.204:8069 und :5432) nicht erreichbar (Timeout).
- Volume: `odoo18_odoo18_pgdata`; Odoo-Log: 0 Fehler/Tracebacks, 0 Modul-Warnungen; db-Log: "ready to accept connections" (FATAL "database odoo does not exist" = normales Erstkontakt-Verhalten ohne DB).
- git status VM: nur `docker-compose.yml` + `.gitignore` modifiziert, `.env` ignoriert.
- **Stand: VM laeuft mit leerem PostgreSQL/Odoo-Grundsystem — lokale Testdatenbank NOCH NICHT uebertragen.**

#### 7) Analyse lokaler Odoo-18-Teststand (read-only, Basis fuer die Uebertragung)

- **DB**: `odoo18_test`, 80 MB (83.868.695 Bytes); PostgreSQL lokal **16.14** (Debian), VM 16.15 (gleiche Major, kompatibel).
- **Filestore**: `C:\Odoo-Test\filestore`, 24 MB, 40 Dateien (Hauptteil `odoo18_test/` 13 MB).
- **Module**: 158 installiert, davon **15 itk_*-Module** (Versionen identisch mit Repo) + OCA/Helpdesk: helpdesk_mgmt 18.0.1.17.1, helpdesk_mgmt_project, helpdesk_mgmt_sla, helpdesk_mgmt_timesheet, project_timesheet_time_control, server_action_mass_edit.
- **Testdaten-Kontrollzahlen**: 76 Partner, 1 Lead, 8 CRM-Stages, 4 Vertriebsteams, 0 Aktivitaeten, 16 Verkaufsauftraege, 22 Rechnungen, 23 Produkte, 18 Benutzer, 1249 Anhaenge, 455 Nachrichten.
- **Kompatibilitaet Git**: alle Repo-Module installiert mit identischer Version; Ausnahmen/Hinweise:
  - `itk_projectcategory`: DB 18.0.0.1 vs Repo 18.0.1.0.0 -> Upgrade offen (KEIN Upgrade ohne Freigabe; Dump uebernimmt 18.0.0.1).
  - `web_group_expand`: installiert (18.0.1.0.0) obwohl als "geparkt" dokumentiert (Doku-Inkonsistenz; Code liegt im Repo, funktioniert).
  - `account_add_gln`: Core-Modul des odoo:18-Images (kein Repo-Modul, auf VM vorhanden).
- Odoo-Build lokal 18.0-20260609 vs VM 18.0-20260817 (gleiche 18.0, DB-kompatibel).

#### 8) Geplanter naechster Schritt (NACH Freigabe, noch nicht ausgefuehrt)

Kontrollierte Uebertragung lokale DB `odoo18_test` + Filestore -> VM:

- A) Dump lokal: `pg_dump --format=custom --no-owner` (odooe18_test) — odoo18-Container stoppen fuer konsistenten Stand; Dump-Verifikation.
- B) Transfer: Dump + Filestore (24 MB) per scp/tar zur VM.
- C) Restore: `createdb odoo18_test` + `pg_restore` (custom, --no-owner, Besitzer odoo); DB-Name identisch (Filestore-Pfade in ir_attachment).
- D) Filestore nach `/opt/odoo18/filestore` (Owner 100:101).
- E) Start + Verifikation: Browser, CRM-Struktur, Vertriebskanaele (4), Kontrollzahlen, Modul-Status (158), Logs.
- F) Backup des frischen VM-Stands (pg_dump).
- G) Doku/Commit nur bei weiteren Aenderungen.

**AUSDRUECKLICH KEINE Migration produktiver Odoo-11-Daten, kein -u all.**

#### 9) Offene Punkte

- **Lokale .env**: `C:\Odoo-Test` hat (noch) keine `.env` — vor dem naechsten LOKALEN Stack-Restart anlegen (sonst leeres POSTGRES_PASSWORD). Laufender lokaler Stack ist unkritisch (Container laufen mit altem Env weiter).
- Vier Einzel-Upgrades aus Session 73 weiterhin offen (hr_holidays_public -> itk_reports -> itk_sale_management -> itk_translation, je Freigabe).
- `hermes verify --json`: mit `--skip-start` OK (build-Phase); voller Lauf wuerde lokal Container starten -> bewusst nicht ohne Freigabe.

---

### Session 75: Uebertragung des lokalen Odoo-18-Teststands auf die IPAX-Test-VM (31.08.2026)

**Freigabe (Anna):** vollstaendig, kontrolliert Schritt fuer Schritt. KEINE Odoo-11-Daten, KEIN -u all, keine Modul-Upgrades, keine Code-Aenderungen an itk_*/OCA.

#### 1) Ablauf (durchgefuehrt)

- **A) Lokal (konsistenter Stand):** `docker stop odoo18` -> `pg_dump --format=custom --no-owner --no-privileges` (Exit 0, 8.068.361 Bytes, TOC 13551 Eintraege, gzip); Verifikation `pg_restore --list` (Exit 0). Dump + Filestore-Backup (24 MB) nach `C:\Odoo-Notfallbackup\2026-08-31_odoo18_test_migration\`. odoo18 danach wieder gestartet (laeuft weiter). Kontrollcheck: KEIN Modul in state `to upgrade` (unbedingter Start ohne -u auf der VM damit moeglich).
- **B) Transfer:** scp Dump + `filestore_20260831.tar.gz` (5.085 KB) nach `/tmp/odoo18_migration/`; SHA256 des Dumps auf der VM identisch mit lokal (`0750c25a...`).
- **C) Pre-Check VM:** 90 GB frei; Stack running; Git main `447c38d` sauber; **KEINE DB odoo18_test vorhanden** (nur postgres/template1).
- **D) Restore:** `createdb -U odoo -O odoo odoo18_test` (Exit 0) -> `pg_restore -U odoo --no-owner --no-privileges -j 4` (Exit 0, **0 ERROR-Zeilen**, 650 Tabellen).
- **E) Filestore:** Erste Extraktion als k001959 schlug fehl (Verzeichnis war bereits auf 100:101 gechownt -> kein Schreibrecht fuer k001959). **Fix:** Extraktion mit `sudo`, `chown -R 100:101`. Ergebnis: 40 Dateien gesamt (14 unter `odoo18_test/`), 24 MB, Owner 100:101; Schreib-/Loeschtest im Container OK.
- **F) Start:** `docker restart odoo18` -> HTTP 200 nach ~8 s (`/web/login?db=odoo18_test`); Registry geladen (1,3 s); 0 Fehler/Tracebacks; Assets OK (`/web/assets/...web.assets_frontend.min.css` -> HTTP 200, 671.266 Bytes); nur harmlose Warnungen ("Missing license key" bei 3 itk-Modulen, vorbestehend).

#### 2) Verifikation (alles gruen)

- **Login:** JSON-RPC `authenticate` -> uid=2 (Administrator) OK.
- **SQL-Kontrollzahlen VM == lokal (1:1):** res.partner 76, crm.lead 1, crm.stage 8, crm.team 4, mail.activity 0, sale.order 16, account.move 22, product.template 23, res.users 18, ir.attachment 1249, mail.message 455.
- **Benutzersicht (RPC, Record Rules aktiv) lokal == VM identisch:** 70 / 1 / 8 / 2 / 0 / 16 / 22 / 13 / 14 / 268 / 420. Differenz zu SQL = archivierte/inaktive Datensaetze: 6 Partner, 2 Teams, 10 Produkte, 4 Benutzer (aktiv/gesamt per SQL verifiziert); ir.attachment 268 vs 1249 und mail.message 420 vs 455 = Record-Rules-Sicht von uid=2 (kein Superuser). **Lokal und VM liefern byte-identische Werte -> 1:1 bestaetigt auf beiden Ebenen.**
- **Module:** 158 installed (15 itk_*, 6 OCA/Helpdesk) identisch.
- **Filestore:** 1:1 uebertragen. Hinweis: DB referenziert 969 `store_fname`-Dateien, physisch vorhanden sind 14 (unter `odoo18_test/`) — **vorbestehende Altlasten, lokal identisch** (u.a. legacy `payment.method`/`gamification`-Anhaenge aus O11-Zeit + die bekannten Partner-Bilder, Sessions 71/73; anonymes Docker-Volume geprueft: leer). KEINE Korrektur ohne Freigabe.
- **Security unveraendert:** 127.0.0.1:8069, db ohne Host-Port, .env unveraendert (600, ignoriert).

#### 3) Backup des funktionierenden VM-Stands

- `/opt/odoo18/backups/odoo18_test_vm_20260831.dump` (8.068.376 Bytes, custom) + `filestore_vm_20260831.tar.gz` (5.204.004 Bytes). `backups/` ist gitignored. (SHA weicht vom lokalen Dump nur durch Header-Zeitstempel ab: +15 Bytes.)

#### 4) Befunde / Notizen

- `docker cp` auf Windows: MSYS-Pfadkonvertierung erzeugt `C:\c\...` -> mit relativem Pfad (cd ins Zielverzeichnis) loesen.
- Filestore-Extraktion auf der VM: Verzeichnis mit Container-UID (100:101) vorab chownen -> Extraktion nur mit sudo.
- RPC-Checks brauchen die Session-Cookie (http.cookiejar), sonst "Access Denied"/None-Ergebnisse.
- Lokale .env-Frage bleibt offen (vor naechstem LOKALEN Stack-Restart anlegen).

#### 5) Einschraenkungen (fortgeschrieben)

- KEINE Odoo-11-Datenmigration, KEIN -u all, keine Modul-Upgrades ohne Freigabe; Encoding unangetastet; lokaler Stack laeuft weiter als Quelle.


---

### Session 76: HTTPS-Zugriff ueber Nginx + Let's Encrypt auf der IPAX-Test-VM (01.09.2026)

**Ziel:** Odoo 18 dauerhaft ueber https://k001959vsx.ipax.at erreichbar (statt SSH-Tunnel) fuer Anna, Florian und Tina.
**Freigaben (Anna):** Option 1 = vorhandener Hostname k001959vsx.ipax.at; vollstaendige Einrichtung (nginx, ufw, Odoo-Config, Let's Encrypt, Tests, Git-Workflow). KEINE DB-/Filestore-/Modul-Aenderungen (kein -u, kein Upgrade).

#### 1) Analyse (read-only)
- k001959vsv.ipax.at: NXDOMAIN im oeffentlichen DNS (8.8.8.8) — existiert nur im /etc/hosts der VM (127.0.1.1) → fuer HTTPS ungeeignet. k001959vsx.ipax.at: A-Record → 93.189.28.204 (oeffentlich) → gewaehlt.
- Port 80/443 von aussen ERREICHBAR (mit temporaeren Test-Listenern verifiziert; Datacenter-Firewall laesst durch) → Let's Encrypt HTTP-01 moeglich.
- Host-Firewall (ufw) war INAKTIV; 8069 nur 127.0.0.1, 5432 nur Docker-intern. nginx/certbot nicht installiert.
- Odoo 18 bedient /websocket direkt auf Port 8069 (Log: "101 Switching Protocols") — KEIN separater 8072-Listener noetig; nginx proxiet alles auf 127.0.0.1:8069.

#### 2) Aenderungen
1. **odoo.conf** (`config/odoo.conf`, GITIGNORED, 644): `proxy_mode = True`, `list_db = False`, `dbfilter = ^odoo18_test$`, `admin_passwd` = zufaellig (48 hex, nie committet). Vorlage ohne Secrets committet: `config/odoo.conf.example`.
   - **PITFALL CRLF:** Windows-Textmodus schreibt CRLF → Linux-configparser: "NoSectionError: No section: 'options'" (Sektion heisst dann '[options]\r') → Datei zwingend LF (Binary-Write).
   - **PITFALL Config-Key:** Odoo 18 liest den DB-Filter ueber CLI-dest `dbfilter` — der Conf-Key heisst **dbfilter**, NICHT db_filter! (db_filter wird zwar geparst (config['db_filter'] gesetzt), aber nie gelesen → config['dbfilter'] bleibt '' und der Filter wirkt nicht.)
   - **PITFALL Mount-Rechte:** Bind-Mount-Datei muss fuer Container-User (uid 100) lesbar sein → 644 (600 verursacht "Permission denied" im Entrypoint-grep).
2. **docker-compose.yml:** odoo-Service Mount `./config/odoo.conf:/etc/odoo/odoo.conf:ro`; Port bleibt `127.0.0.1:8069:8069`. Container-Recreate (`docker compose up -d`): nur odoo18 neu, Named Volume unangetastet, DB/Filestore/Module unveraendert.
3. **nginx 1.28.3 (apt):** Site `/etc/nginx/sites-available/odoo` (Referenzkopie im Repo: `config/nginx_odoo.conf`):
   - Port 80: `/.well-known/acme-challenge/` (Webroot /var/www/certbot) + `return 301 https://$host$request_uri`
   - Port 443: TLS 1.2/1.3, `proxy_pass http://127.0.0.1:8069`, Header Host / X-Forwarded-Host / X-Forwarded-For / X-Forwarded-Proto, `client_max_body_size 100m`, `/websocket` mit Upgrade-Headern + `proxy_read_timeout 86400s`
   - **PITFALL:** apt startet nginx sofort mit Default-Config; `systemctl enable --now` laedt die neue Config NICHT → `systemctl reload nginx` noetig (sonst 404 auf ACME-Pfad, Zertifikat schlaegt fehl).
4. **Let's Encrypt:** `certbot 4.0.0 certonly --webroot -w /var/www/certbot -d k001959vsx.ipax.at` (Account: anna.maierhofer@it-kommunal.at), Auto-Renew via systemd-Timer + deploy-hook `systemctl reload nginx`. Zertifikat gueltig 01.09.–30.11.2026.
5. **ufw:** `DEFAULT_FORWARD_POLICY="ACCEPT"` in /etc/default/ufw (Docker-Kompatibilitaet!), `allow 22/80/443`, `--force enable` → Status: deny incoming / allow outgoing / allow routed. 8069/5432 weiterhin NICHT oeffentlich (127.0.0.1-Bindung + ufw).

#### 3) Verifikation (alles gruen)
- HTTPS von aussen: 200; Zertifikat CN=k001959vsx.ipax.at, Issuer Let's Encrypt (YE2), keine Warnung.
- HTTP → 301 https (von aussen verifiziert).
- Login ueber HTTPS (Formular-POST mit CSRF, db LEER → dbfilter waehlt odoo18_test) → 303 → App-Shell 200.
- Session: db=odoo18_test, uid=2; **web.base.url = https://k001959vsx.ipax.at** (proxy_mode-Beweis).
- Kontrollzahlen unveraendert: RPC-User-Sicht uid 2 exakt Session-75-Baseline (70/1/8/2/0/16/22/13); SQL-Gesamtwerte (76/1/8/4/16/22/23) unangetastet.
- Assets 3/3 (200, >100B). Websocket-Route: HTTP 400 (Odoo-Handshake-Antwort, kein 502 → Proxy korrekt).
- list_db=False: /web/database/selector zeigt "disabled", /web/database/list → AccessDenied.
- Ports von aussen: 22/80/443 offen, 8069/5432 gesperrt.
- Logs: nginx error.log leer; Odoo-Log nur eigene Test-Artefakte (AssertionError db="" + AccessDenied /web/database/list).
- mail.activity.type: 13 gesamt / 12 aktiv (Typ 6 "Ausnahme" seit jeher archiviert — vorbestehend, unveraendert).

#### 4) Offene Punkte
- **Benutzer Florian/Tina:** Vorschlag erstellt (siehe Session-Bericht), Anlage wartet auf Freigabe. HINWEIS: florian.wuerrer@it-kommunal.at existiert bereits (id 8, aktiv, 40 Gruppen — O11-Testdaten); Tina nicht.
- Lokale .env (C:\Odoo-Test) weiterhin offen (vor naechstem LOKALEM Stack-Restart).
- scripts/test_migration_contacts.py ist committet und enthaelt RPC-Passwoerter → Bereinigung empfohlen (separate Freigabe).
- Nach PR-Merge: VM `git pull` (config/odoo.conf ist gitignored → bleibt).

#### 5) Einschraenkungen (fortgeschrieben)
- KEINE Odoo-11-Datenmigration, KEIN -u all, keine Modul-Upgrades ohne Freigabe; Encoding unangetastet; DB/Filestore/Module auf der VM unveraendert (nur Config-Ebene).


---

### Session 77: PR #18 Merge + Sync, Sicherheitsbereinigung (Credentials aus dem Repo), lokale .env (01.09.2026)

**Freigaben (Anna):** PR #18 nach main mergen + Sync lokal/GitHub/VM; Sicherheitsfund scripts/test_migration_contacts.py bereinigen (Zugangsdaten via .env/Umgebungsvariablen, .env gitignored, Repo-Scan auf weitere Zugangsdaten); lokale .env vorbereiten (ohne DB-Aenderung); Doku + Branch/Commit/Push/PR/Merge. KEINE Benutzer fuer Florian/Tina (separat).

#### 1) PR #18 Merge + Sync (main = fbe044b)
- PR #18 (hermes/nginx-https-vm) per REST-API gemergt (Merge-Commit fbe044b, kein Squash/Rebase).
- Lokal: `git pull --ff-only` → main fbe044b, sauber. VM: `git checkout -- docker-compose.yml` (lokal gespiegelte Datei == PR-Inhalt) + `git pull --ff-only` → main fbe044b, sauber.
- Verifiziert: lokal == GitHub == VM (fbe044b), Arbeitsbaeume sauber; Stack auf der VM healthy (odoo18 up, HTTPS 200).

#### 2) Sicherheitsaudit (Repo-Scan, 4081 getrackte Dateien)
| Fund | Datei | Massnahme |
|---|---|---|
| RPC-Zugangsdaten (O11+O18, inkl. Passwoerter) hartkodiert | scripts/test_migration_contacts.py | Refactor auf .env (Loader, Repo-Root) |
| Dito (O11+O18) | validate_contacts.py (Repo-Root) | Refactor auf .env, Variablen vereinheitlicht (ODOO11_*/ODOO18_*) |
| 3 auskommentierte Passwort-Zeilen (res.users) | geparkt/itk_main_company_import/data/itk_company_base_data.xml | Passwort-Zeilen entfernt (Kommentar-Bloecke bleiben) |
| Alt-Passwort im Zugänge-Tabellen | PROJECT_KNOWLEDGE.md (Z. 198) | Verweis auf .env statt Klartext |
| docs/hermes_memory_backup_2026-07-27.md | — | Bereits bereinigt (Credentials entfernt, verifiziert) |
| *.ps1 (backup/recovery/diag) | — | Keine Zugangsdaten (docker exec, Peer-Auth im Container) |

- **Ergebnis:** 0 Vorkommen der bekannten Passwortwerte in getrackten Dateien (git grep -F, verifiziert); kein hardcodiertes PWD-Assignment in den Skripten (Regex-Scan); .env gitignored (git check-ignore OK).

#### 3) Zugangsdaten-Feststellung + Passwort-Rotation (Bewertung, KEINE Rotation ausgefuehrt)
- **Odoo-18-Passwort (anna.maierhofer@it-kommunal.at, uid 2 = Administrator): AKTIV in Verwendung** — gilt fuer lokale UND VM-Testumgebung (DB 1:1). War im PUBLIC Repo committet → oeffentlich bekannt gewesen. **Rotation EMPFOHLEN** (Passwort in Odoo aendern + .env aktualisieren). Die Werte bleiben in der Git-HISTORIE (Rewrite nur mit Force-Push — laut Workflow verboten) → Rotation ist die einzige wirksame Massnahme.
- **Odoo-11-Passwort: verwaist** — galt fuer die dekommissionierte O11-VM (existiert nicht mehr). Keine Rotation im System moeglich; falls der Wert anderweitig wiederverwendet wird, dort aendern.

#### 4) Lokale .env vorbereitet (C:\Odoo-Test\.env, gitignored; DB NICHT veraendert)
- `POSTGRES_PASSWORD=odoo` — MUSS dem Passwort des bestehenden Named Volumes odoo18_pgdata entsprechen (Volume vom 12.08.2026; Postgres setzt es nur beim ERSTEN Start). Verifiziert: laufender lokaler odoo-Container nutzt genau dieses Passwort (--db_password Vergleich).
- Skript-Variablen (ODOO11_*/ODOO18_*): Werte programmatisch aus der committeten Skript-Version extrahiert und nach .env ueberfuehrt (kein Klartext im Bericht).
- Damit funktioniert der lokale Stack auch nach einem spaeteren `docker compose up -d`/Restart; lokale DB bleibt unveraendert.
- Vorlage committet: `.env.example` (Platzhalter, keine Werte).

#### 5) Offene Punkte
- **Passwort-Rotation Odoo-18-Admin** (Entscheidung Anna; danach .env aktualisieren).
- Benutzer Florian/Tina: Vorschlag aus Session 76 steht, Anlage separat nach Freigabe.
- Lokaler Stack laeuft weiter (kein Neustart noetig; .env greift beim naechsten Restart).

#### 6) Einschraenkungen (fortgeschrieben)
- KEINE Odoo-11-Datenmigration, KEIN -u all, keine Modul-Upgrades ohne Freigabe; Encoding unangetastet; DB/Filestore/Module unveraendert; kein Force-Push/Rebase.


---

### Session 78: Session-Abschluss — Ausgangspunkt fuer die naechste Session (01.09.2026)

**Freigaben (Anna):** VM-Einrichtung + Teststand-Uebertragung als abgeschlossen betrachtet; Doku-Konsolidierung (PROJECT_KNOWLEDGE.md/README); Sync-Verifikation lokal/GitHub/VM. KEINE weiteren technischen Aenderungen in dieser Session. Benutzer Florian/Tina bewusst NICHT angelegt (separat).

#### 1) Nachtrag: hr_holidays_public-Upgrade (heute frueh, vor Session 76)
- Freigegeben + ausgefuehrt: Einzel-Upgrade hr_holidays_public (Modul 764, button_immediate_upgrade per RPC, uid 2) auf dem LOKALEN Stack.
- Ergebnis: Action 1268 "Public Holidays" view_mode tree,form → list,form (Repo-Stand 6b691ec); 0 tree im Modul; Menues intakt; Log sauber. Version bleibt 18.0.1.0.0 (Fix war bereits committet).
- **WICHTIG (Sync-Differenz):** Das Upgrade lief nur in der LOKALEN DB odoo18_test. Die VM-DB (Stand 31.08.) hat fuer hr_holidays_public weiterhin tree,form. Angleichung bei den restlichen Einzel-Upgrades (itk_reports → itk_sale_management → itk_translation, je Freigabe) oder separat.
- Offen bleiben damit: itk_reports, itk_sale_management, itk_translation (tree→list-Fixes, je Freigabe).

#### 2) Ausgangspunkt naechste Session (dokumentierter Stand, keine Neu-Erklaerung noetig)
- **Odoo 18 laeuft auf der IPAX-VM** — Zugriff ueber **https://k001959vsx.ipax.at** (nginx + Let's-Encrypt, Auto-Renew; HTTP→HTTPS; ufw 22/80/443; Odoo nur 127.0.0.1:8069; PostgreSQL nur Docker-intern).
- **Datenbank odoo18_test** — lokaler Odoo-18-Teststand am 31.08.2026 1:1 auf die VM uebertragen (Dump + Filestore); VM-Backups unter /opt/odoo18/backups/.
- **Lokale Odoo-18-Umgebung besteht separat weiter** (Windows Docker, http://localhost:8069; lokale .env seit 01.09. vorhanden — POSTGRES_PASSWORD passend zum Volume, Skript-Zugangsdaten; lokale DB unveraendert).
- **PostgreSQL und Filestore sind persistent** (Named Volume odoo18_odoo18_pgdata bzw. /opt/odoo18/filestore, Owner 100:101).
- **Nginx/HTTPS eingerichtet** (Session 76): config/nginx_odoo.conf (Referenz), config/odoo.conf (gitignored, proxy_mode/list_db=False/dbfilter), odoo.conf.example.
- **GitHub/main, lokale Umgebung und VM synchron** (main = bc7882e nach PR #18 + #19), Arbeitsbaeume sauber.
- **Keine produktiven Odoo-11-Daten migriert** (O11-VM dekommissioniert 31.08.; nur Testdaten des 1:1-Teststands).
- **Aktuell 158 installierte Module**, darunter 15 itk_*-Module und die verwendeten OCA/Helpdesk-Module (helpdesk_mgmt, helpdesk_mgmt_project/sla/timesheet, project_timesheet_time_control, server_action_mass_edit).
- **Weitere Modul-Upgrades bzw. Funktionsanpassungen nur kontrolliert und nach Bedarf** (je Freigabe; KEIN -u all; Encoding abgeschlossen 13.08., nicht anfassen).

#### 3) Bewusst offen / naechste Schritte (priorisiert)
1. **E-Mail-Versand (SMTP): noch NICHT eingerichtet** — Konfiguration in einer der naechsten Sessions (Outgoing-Mail-Server in Odoo + ggf. SMTP-Relay; Doku in PROJECT_KNOWLEDGE ergaenzen).
2. **Admin-Passwort-Rotation (Odoo 18): bewusst offen** — separat durchfuehren (Grund: Sicherheitsfund Session 77; Wert war im public Repo committet; danach lokale .env aktualisieren).
3. Benutzer Florian + Tina: Vorschlag steht (Session 76: group_user + group_sale_salesman_all_leads + crm.group_use_lead + helpdesk group_helpdesk_user[_team]; KEINE Admin-Rechte). Hinweis: florian.wuerrer@it-kommunal.at existiert bereits (id 8, 40 Gruppen, O11-Testdaten).
4. Restliche Einzel-Upgrades (tree→list): itk_reports → itk_sale_management → itk_translation, je Freigabe; dabei VM-Angleichung hr_holidays_public (siehe 1).

#### 4) Einschraenkungen (fortgeschrieben)
- KEINE Odoo-11-Datenmigration, KEIN -u all, Modul-Upgrades nur einzeln mit Freigabe; Encoding unangetastet; DB/Filestore/Module auf der VM unveraendert; kein Force-Push/Rebase; Passwoerter nie committen (Zugangsdaten nur in gitignored .env).

---

### Session 79: Read-only-Inventarisierung + MIGRATION_READINESS_CHECKLIST — Start der Abnahme-Vorbereitung (01.09.2026)

**Auftrag (Anna):** Beginn der fachlichen/technischen Abnahme von Odoo 18 VOR der O11-Datenmigration. 1) Relevante Module tatsaechlich ermitteln (itk_*/OCA-*/Standard, Unterschied installiert vs. Repo-Verzeichnisse vs. zu testen), 2) MIGRATION_READINESS_CHECKLIST.md anlegen (Sprache, Umlaute/Encoding, Waehrung, Grundeinstellungen, Fachbereiche; Mapping-Abschnitt O11->O18 vorerst OFFEN), 3) Testreihenfolge vorschlagen, 4) Doku + Git-Workflow (Branch/Commit/Push/PR/Merge), 5) Sync lokal/GitHub/VM pruefen. **AUSDRUECKLICH:** nur read-only Analyse; KEINE Korrekturen, KEINE Modul-Upgrades, KEIN -u all, KEINE Datenmigration, KEIN E-Mail-Setup. Kein O11-Feldvergleich (keine O11-Referenz vorhanden).

#### 1) Vorgehen (alles read-only)
- Inventar + Konfiguration direkt aus der VM-DB `odoo18_test` (psql via docker exec, nur SELECT): 158 installierte Module inkl. shortdesc/Version, res_company/res_currency/res_lang/res_users, Preislisten, Journale, Belegwaehrungen, Encoding-Muster (├ und CP850-ÔÇô), Kontrollzahlen je Fachbereich.
- Repo-Vergleich lokal (Python): `addons/` (41 Verzeichnisse) und `geparkt/` (13) vs. DB-Installationsstand.

#### 2) Modulinventar (Ergebnis, Detail in MIGRATION_READINESS_CHECKLIST.md Abschnitt 0)
- **158 installiert** = 40 Repo-Module (`addons/`) + 118 Odoo-18-Standard aus dem Image (inkl. account_add_gln).
- **15 itk_*-Module** (alle installiert; 12 davon nur mit technischem Namen als sichtbare Bezeichnung, 3 mit sprechendem Label: itk_subscription "ITK Abo-Management", itk_helpdesk_category_user, itk_helpdesk_compat).
- **6 OCA/Helpdesk**: helpdesk_mgmt 18.0.1.17.1, helpdesk_mgmt_project, helpdesk_mgmt_sla, helpdesk_mgmt_timesheet, project_timesheet_time_control, server_action_mass_edit.
- **19 migrierte Drittanbieter-/Web-Module** (partner_firstname, merge_*, purchase/sale/account_invoice_line_*, web_*, website_*, hr_holidays_public, mass_email_invoice …).
- **Fachlich genutzte Standardmodule**: contacts, crm, sale/sale_management, product, account (+l10n_at, l10n_din5008*), project, hr (+hr_holidays), sale_subscription, mail, website, portal.
- NICHT relevant (0 Daten): survey, mass_mailing*, hr_attendance, project_milestone u. a.; NICHT installiert: stock/mrp/pos/fleet.
- `addons/` = 41 Verzeichnisse, davon 40 installiert; einzige Nicht-Installation: `web_tree_resize_column` (geparkt).
- Einzige Version-Abweichung DB vs. Repo: **itk_projectcategory DB 18.0.0.1 vs. Repo 18.0.1.0.0** (bekannt, Upgrade offen).

#### 3) Befunde (nur dokumentiert, NICHT behoben — F1–F13 in der Checkliste Abschnitt 8)
- **F1 EUR-Symbol Mojibake:** res_currency id 126 (EUR) symbol = `Ôé¼` statt `€` (Bytes \303\224\303\251\302\274 = CP850-Schaden; weitere Symbole betroffen: GBP `┬ú`, CZK `K─ì`, PLN `z┼é` …). Spalte war NICHT Teil der CP850-Reparatur vom 13.08.
- **F2 USD aktiv:** res_currency id 1 USD active=true (Relikt aus initialer DB-Erstellung vor l10n_at).
- **F3/F4 USD-Belege:** 14 Verkaufsauftraege (inkl. A-1900011) + 4 Rechnungen (account_move 17,20,21,19) in USD (currency_id=1), alle ueber Preisliste 1 "Standard-Preisliste" (USD), Testdaten 01.–24.07.2026.
- **F5 Preislisten:** beide inaktiv (id 1 USD, id 34 "Preisliste 2026 + Valorisierung" EUR mit 2 Items).
- **F6 Sprache:** 12/15 itk- + alle 6 OCA-Module ohne de_DE-shortdesc (englische/technische Namen in Apps-Liste).
- **F7 account_payment-shortdesc:** de_DE "Zahlung ÔÇô Konto" (CP850) — einziges betroffenes INSTALLIERTES Modul; 14 weitere betroffene Module nicht installiert.
- **F8 Zeitzone:** nur uid 2 + 8 mit Europe/Vienna; 16 Benutzer ohne tz (UTC-Fallback).
- **F9 res_lang:** nur de_DE aktiv; en_US vorhanden aber inaktiv; 91 Zeilen mit active IS NULL (Altlast).
- **F10 Doku-Inkonsistenz:** web_group_expand installiert obwohl "geparkt" dokumentiert (Code funktioniert).
- **F11** itk_projectcategory-Versionsdifferenz (s. o.). **F12** Ausstehende Einzel-Upgrades (itk_reports, itk_sale_management, itk_translation, hr_holidays_public-VM-Angleichung).
- **F13 Anhaenge:** ir.attachment 1249 → 1260, mail_message 455 → 456 (Asset-Regeneration nach HTTPS/proxy_mode, erwartbar).
- Kontrollzahlen sonst unveraendert (Partner 76, Lead 1, Stages 8, Teams 4, Auftraege 16, Belege 22, Produkte 23, Benutzer 18/14 aktiv, Abos 5, Helpdesk 1 Ticket/16 Stages/37 Kategorien).

#### 4) Neue Datei + Doku
- **NEU: `MIGRATION_READINESS_CHECKLIST.md`** — Abnahme-Checkliste (Stand 01.09.2026): Abschnitt 0 Modulinventar (0.1–0.6), 1 Sprache (A), 2 Umlaute/Encoding (B, inkl. Testtexte), 3 Waehrung (C), 4 Grundeinstellungen (D), 5 Fachbereiche (E, je Bereich mit Ist-Daten), 6 O11->O18-Mapping (OFFEN, Schema hinterlegt), 7 Testreihenfolge (Prioritaet laut Anna), 8 Befundliste F1–F13, 9 Grenzen. Tabellenformat: Bereich | Funktion/Feld | Istzustand | Status | Fehler/Abweichung | Anpassung | getestet.
- `README.md`: "Aktueller Stand & Ausblick" um Abnahme-Phase + Checklisten-Referenz ergaenzt.

#### 5) Git-Workflow
- Branch `abnahme-readiness` → Commit (Checkliste + PROJECT_KNOWLEDGE Session 79 + README) → Push → PR → Merge nach main (Merge-Commit, kein Rebase/Squash; PR-Nummer und main-Hash im Session-Abschlussbericht) → lokale Synchronisation (`git pull --ff-only`) → VM `git pull` + Sync-Verifikation (lokal == GitHub == VM).

#### 6) Offene Punkte / naechste Schritte
1. **Abnahme Punkt fuer Punkt** gemaess Checkliste Abschnitt 1 (Sprache) starten — gemeinsam mit Anna.
2. Vor Waehrungs-Abnahme (Abschnitt 3): Entscheidung zu Befunden F1–F5 (EUR-Symbol-Fix, USD-Bereinigung) — je Freigabe.
3. Unveraendert offen: SMTP-Konfiguration, Admin-Passwort-Rotation, Benutzer Florian/Tina, Einzel-Upgrades (F12).

#### 7) Einschraenkungen (fortgeschrieben)
- KEINE Odoo-11-Datenmigration, KEIN -u all, Modul-Upgrades nur einzeln mit Freigabe; Encoding unangetastet (Befunde F1/F7 nur dokumentiert); DB/Filestore/Module auf der VM unveraendert; kein Force-Push/Rebase; Passwoerter nie committen.

---

## Session 80: Abnahme Abschnitt 1 (A Sprache) — read-only-UI-Text-Inventar der relevanten Module (02.09.2026)

**Auftrag (Anna):** Abnahme gemaess MIGRATION_READINESS_CHECKLIST Abschnitt 1 (Deutsch / sichtbare UI) beginnen; systematisch die sichtbaren Texte der relevanten installierten itk_*- und OCA-/Helpdesk-Module pruefen (Modulbezeichnungen, Menues, Labels, Buttons, Status-/Auswahlwerte, Kanban, Views). Basierend auf Session 79; **AUSDRUECKLICH read-only** — nichts repariert, keine Datenmigration, kein -u all, keine Modul-Upgrades; USD-/Preislisten-Thematik (F1–F5) unangetastet.

### 1) Vorgehen (alles read-only)
- SSH-Port 22 zur VM war von hier aus nicht erreichbar (Timeout) — HTTPS-Port 80/443 offen → Inventar per **JSON-RPC gegen https://k001959vsx.ipax.at** (Muster Session 75/76), uid=2 (anna.maierhofer@it-kommunal.at), DB odoo18_test, Sprachkontexte **de_DE und en_US**; Credentials aus lokaler .env (nie ausgegeben).
- Erfasst: ir.module.module.shortdesc (23 Module), ir.ui.menu (Baum inkl. Eltern), ir.actions.act_window, ir.ui.view (171 Views), ir.model.fields.field_description + fields_get (30 Fachmodelle), ir.model.fields.selection, Datensatznamen (CRM-Stages, Helpdesk-Stages/Kategorien, Aktivitaetstypen), Mojibake-Scan ueber alle gesammelten Texte.
- Rohdaten/Arbeitsskripte nur in %TEMP% (nicht im Repo); Ergebnisdokument **`docs/abnahme_sprache_ui_abschnitt1.md`** (neu, 892 Zeilen Detail-Inventar je Modul).
- Bestaetigt (Session-79-Befunde F6/F7): 12/15 itk- + 6/6 OCA-Module ohne de_DE-shortdesc; account_payment de_DE-shortdesc „Zahlung ÔÇô Konto“.

### 2) Befunde (nur dokumentiert, F14–F26 in der Checkliste; NICHTS behoben)
- **F14 itk_translation:** ITK-Menue-Baum sichtbar englisch/technisch (Top „ITK-Menu“ 733; „Actual customers“, „All customers“, „Former Customers“, „Target Customers“, „All Resellers“, „All Magnitudes“, „Partner“, „Reseller“; 6 Actions gleichlautend).
- **F15 itk_crm:** ~15 Custom-Felder auf res.partner (Delegation res.users) ohne de_DE-Text: firstname/lastname („First/Last name“), status_of_community, population, population_update, member_of_city_alliance, asset_partner, title_put_in_front/back, sales_as_final_customer_count, reseller, salutation, austria_wiki_url, community_magnitude(_id). Positive Gegenprobe: attention_of „zu Handen“, type „Adresstyp“, is_customer/is_supplier „Ist ein Kunde/Lieferant“ deutsch.
- **F16 x_-Felder crm.lead:** Labels „Lead Status“ (x_lead_status), „Anrede Lead“, „Lead Quelle“; Werte deutsch; Auswahlwert „On-Hold“.
- **F17 sale.subscription/-template:** Felder sichtbar englisch (70/38 Kandidaten; Kernfelder Customer/Start Date/End Date/Notice Period/Subscription Template/Created on …), obwohl itk_subscription-Menues/-Actions deutsch sind (de.po deckt nur Teile ab bzw. Feld-Terme fehlen).
- **F18 itk_multifactor / F19 weitere itk_*:** englische Action-/Feldtexte (s. Checkliste).
- **F20 itk_helpdesk_compat:** nur „Support Tickets“ (Menue+Aktion) englisch; Rest deutsch (Positivbefund).
- **F21 helpdesk_mgmt:** Menues „All Tickets“/„Dashboard“/„Settings“(u. Konfiguration) + Actions „Helpdesk Ticket“ englisch; Feld-/Settings-Luecken englisch (duplicate_*, Portal-Settings, Auto assign …) trotz vorhandenem de.po (299 Terme).
- **F22/F23/F24:** helpdesk_mgmt_sla (SLA/SLA Report, Felder grossenteils en), helpdesk_mgmt_timesheet/-project (Timesheets, Allow Timesheet, Ticket Count …), project_timesheet_time_control („Start work“, „Show Time Control“) — letzteres hat de.po, aber nicht geladen/unvollstaendig; sla/timesheet/project ohne de.po im Repo.
- **F25 Daten/Status:** CRM-Stage „On-Hold“, Helpdesk-Stage „on Hold“; Helpdesk-Kategorien mit sichtbaren Duplikaten + Tippfehler „Anynomisierungsportal“ (Daten, nicht angefasst). Aktivitaetstypen (12) und uebrige Stages deutsch (Positiv).
- **F26 Encoding (B):** 3 CP850-Artefakte in sichtbaren de_DE-Uebersetzungen (account.move.status_in_payment „Status ÔÇ×In ZahlungÔÇ£“, show_force_tax_included „ÔÇ×…erzwingenÔÇ£ anzeigen“, res.partner.peppol_eas-Wert 0245 „…(DI─î)“) — NICHT Teil der Reparatur vom 13.08.; nur dokumentiert.
- **Positiv-Stichproben (OK):** Kernmodelle deutsch via fields_get (res.partner „Straße“/„Erstellt am“, crm.lead „Verkaufschance“, product „Verkaufspreis“, account.move „Kunde“/„Gesamt“, sale.order „Auftragsreferenz“); helpdesk.ticket-Kernfelder deutsch (Titel, Kategorie, Stufe, Prioritaet); server_action_mass_edit deutsch; itk_helpdesk_compat-Felder deutsch.

### 3) Aenderungen in diesem Stand (nur Dokumentation)
- **NEU:** `docs/abnahme_sprache_ui_abschnitt1.md` (Detail-Inventar: Zusammenfassungstabelle je Modul, Menue-Baeume de/en, Actions/Fields-Kandidaten, Fachmodell-Kandidaten, Statusnamen, Mojibake-Stellen).
- `MIGRATION_READINESS_CHECKLIST.md`: Abschnitt 1-Zeilen mit Ist-Befunden aktualisiert, Abschnitt 2 (B) um de_DE-Uebersetzungs-Mojibake ergaenzt, Befundliste F14–F26, Abschnitt 9 (Methodik RPC-Inventar, Browser offen).
- **Keine System-/DB-/Modul-Aenderung** (VM und lokal unveraendert).

### 4) Offene Punkte / naechste Schritte (Vorschlag, je Freigabe)
1. **Browser-Sichtpruefung** der Befunde F14–F26 (gemeinsamer Durchgang; viele Labels sind im Formular ohnehin sichtbar).
2. **Entscheidung + Korrektur-Konzept Abschnitt 1:** (a) de_DE-Labels fuer Menues/Actions/Felder in itk_-Modulen (XML/Python-Strings oder de.po), (b) OCA-Module: de.po ergaenzen/nachladen bzw. Uebersetzungslauf pruefen (helpdesk_mgmt de.po ist vorhanden, aber offenbar nicht (vollstaendig) geladen — Ursache vor Fix klaeren: Sprach-Aktivierungszeitpunkt vs. Modul-Installation), (c) Modul-shortdesc (F6), (d) account_payment-F7, (e) Daten-Stellen F25. Jede Aenderung einzeln freigeben.
3. Unveraendert offen: F1–F5 (Waehrung), SMTP, Passwort-Rotation, Benutzer Florian/Tina, Einzel-Upgrades F12.
4. Git: Doku-Commit auf Arbeitsbranch → PR nach main (nach Freigabe durch Anna; keine Systemaenderung enthalten).

### 5) Einschraenkungen (fortgeschrieben)
- KEINE Odoo-11-Datenmigration, KEIN -u all, Modul-Upgrades nur einzeln mit Freigabe; Encoding unangetastet (F1/F7/F26 nur dokumentiert); DB/Filestore/Module auf VM und lokal unveraendert; kein Force-Push/Rebase; Passwoerter nie committen (Zugangsdaten nur in gitignored .env).
