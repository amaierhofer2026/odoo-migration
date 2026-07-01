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

Nächster Schritt: Weitere ~49 Module aus `odoo11 module/` migrieren.
