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
