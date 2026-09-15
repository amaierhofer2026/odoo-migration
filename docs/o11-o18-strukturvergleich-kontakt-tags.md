# Odoo 11 Prod ↔ Odoo 18: Struktur-/Funktionsvergleich „Kontakte → Kontakt-Tags"

Stand: 15.09.2026 (Session 92) · Bereich: Kontakte → Kontakt-Tags (`res.partner.category`)
Grundlage: Odoo 11 Prod (`https://portal.it-kommunal.at`, **nur lesend**), Odoo-11-Produktiv-Dump `ITK_V1_a` (03.09.2026),
Odoo 18 lokal (`localhost:8069`) und Test-VM (`https://k001959vsx.ipax.at`).

> **Kein Datenimport.** Dieses Dokument und das zugehörige Modul `itk_partner_category` bereiten ausschließlich die
> **Struktur** vor. Es werden **keine** Odoo-11-Tags, **keine** der 5.307 Kontakt-Zuordnungen und **keine** sonstigen
> Produktionsinhalte übernommen.

---

## 1. Feldvergleich `res.partner.category`

| Feld | Odoo 11 Prod | Odoo 18 | Bewertung |
|---|---|---|---|
| `name` | char, **nicht** übersetzbar · Label „Tag Bezeichnung" | char, `translate=True` (**jsonb**) · Label „Name" | anders (übersetzbar) |
| `display_name` | char, nicht gespeichert · Inhalt = **voller Hierarchiepfad** · Label „Anzeigename" | char, nicht gespeichert · Inhalt = **voller Hierarchiepfad** (im Code berechnet) | **1:1 fachlich** |
| `x_tag_anzeigename2` | char, **gespeichert**, Studio-Feld · Label „Tag Anzeigename" | — kein Äquivalent — | entfällt (siehe §4) |
| `parent_id` | many2one · Label „Oberkategorie" | many2one · Label „Kategorie" | 1:1, Label abweichend |
| `parent_left` / `parent_right` | integer, Nested-Set (2 Felder) | — entfallen — | Technikwechsel |
| `parent_path` | — | char, „Übergeordneter Pfad", Inhalt = ID-Pfad (z. B. `13/`), indiziert | Technikwechsel |
| `child_ids` | one2many · Label „Untergeordnete Kategorien" | one2many · Label „Untergeordnete Stichwörter" | 1:1, Label abweichend |
| `color` | integer · Label „Farbkennzeichnung" (in Prod durchgehend `0`) | integer · Label „Farbe" · Default = **Zufallswert 1–11** | 1:1, neues Default-Verhalten |
| `active` | boolean · „Aktiv" | boolean · „Aktiv" | 1:1 |
| `partner_ids` | many2many · „Partner" | many2many · „Partner" | 1:1 |
| `create_date` / `create_uid` / `write_date` / `write_uid` | vorhanden | vorhanden | 1:1 |

**Kontaktseite (Feld am Kontakt):** in beiden Versionen identisch konfiguriert und benannt —
`category_id`, Widget `many2many_tags`, `options={'color_field': 'color', 'no_create_edit': True}`, Label **„Stichwörter"**
⇒ hier war keine Anpassung nötig.

## 2. Ansichten

| Ansicht | Odoo 11 Prod | Odoo 18 (Auslieferung) |
|---|---|---|
| Liste | `base.view_partner_category_list` (tree)<br>Spalten: `display_name`, `id`, `x_tag_anzeigename2` — read-only | `base.view_partner_category_list` (list)<br>Spalten: `name`, `parent_id`, `color` — inline editierbar (`editable="bottom"`, `multi_edit`, `sample`) |
| Formular | `base.view_partner_category_form`<br>`name`, `active`, `parent_id`, `create_date`, `x_tag_anzeigename2` (kein `color`) | `base.view_partner_category_form`<br>`name` (Platzhalter), `color` (Farbwähler), `parent_id`, `active` (Schalter) |
| Suche | keine eigene Suchansicht (Standard) | `base.res_partner_category_view_search`: `name`, `display_name`, Filter „Archiviert", Gruppieren nach Kategorie/Farbe |
| Aktion/Menü | „Kontakt Tags" (`base.action_partner_category_form`, `tree,form`) | „Kontakt-Stichwörter" (id 59, `list,form`) |
| Kontaktsuche | Feld `category_id`, `string="Tag"`, `filter_domain=[('category_id','ilike',self)]` | Feld `category_id`, `string="Stichwort"`, `operator="child_of"` (findet auch Kinder) |
| Kontaktliste | Spalte „Stichwörter" vorhanden | Spalte „Stichwörter" vorhanden |

Befund: In Odoo 11 Prod sind die **Standard-Views selbst verändert** — das Studio-Feld `x_tag_anzeigename2`
steckt direkt in `base.view_partner_category_list`/`_form` (die Original-Farbspalte fehlt dort).
Odoo 18 hat die unveränderten Standard-Views und **zusätzlich** eine Suchansicht, die Odoo 11 nicht hatte.

## 3. Hierarchie – Funktionsweise

* **Odoo 11 Prod:** `parent_id` / `child_ids` mit `_parent_store=True` über **`parent_left`/`parent_right`** (Nested-Set).
  Wirkung: die Liste wird hierarchisch verschachtelt sortiert. In den Produktivdaten bis **6 Ebenen** tief,
  123 Knoten, 13 Namen mehrfach belegt (z. B. „Region", „AWS", „GemDAT OÖ").
* **Odoo 18:** `parent_id` / `child_ids` mit `_parent_store=True` über **`parent_path`** (Pfad der IDs, indiziert).
  `_order = 'name'` ⇒ die Liste ist **alphabetisch flach**; die Hierarchie ist über die Spalte „Kategorie"
  bzw. über Gruppieren und die Suche sichtbar. Zyklus-Schutz per Constraint
  (`You can not create recursive tags.`). `display_name` wird aus der `parent_id`-Kette berechnet,
  `_search_display_name` sucht bei „like" per `child_of` ⇒ **Hierarchiesuche ist vorhanden**.

**Kernaussage:** Die Hierarchie ist in Odoo 18 voll funktionsfähig (beliebige Tiefe, Eltern/Kind, ebenenübergreifende
Suche). Unterschiede zur O11-Bedienung: flache Sortierung und keine Einrückung der Ebenen in der Liste.

## 4. „Anzeigename" bzw. „Tag Anzeigename"

* **Odoo 11 `display_name`** (nicht gespeichert) liefert den **vollen Pfad** — belegt an 6 Produktionsdatensätzen,
  z. B. `AFS / amtsweg.gv.at STANDARD / Region / GVA Baden`.
* **Odoo 11 `x_tag_anzeigename2`** („Tag Anzeigename") ist ein **manuell gepflegtes Studio-Feld** (char, gespeichert,
  ohne Hilfe-Text, ohne XML-ID) und dupliziert diesen Pfad — **und ist inkonsistent**:
  * Datensatz id 32: Feld = „FSW / amtsweg.gv.at Light / Österreich", tatsächlicher Pfad = „FSW / amtsweg.gv.at LIGHT / Basis-Paket: Österreich"
  * Datensatz id 152: Feld enthält den Text **„False"**
* **Odoo-18-Äquivalent = `display_name`** (Quellcode-Beleg `base/models/res_partner.py`):

  ```python
  @api.depends('parent_id')
  def _compute_display_name(self):
      """ Return the categories' display name, including their direct
          parent by default. """
      # Kette über parent_id, verbunden mit ' / '  ->  "A / B / C"
  ```

  ⇒ **gleiche fachliche Funktion, aber automatisch und immer korrekt.**
  `parent_path` („Übergeordneter Pfad") ist dagegen der interne ID-Pfad und **kein** Anzeigename.

**Entscheidung:** `x_tag_anzeigename2` wird **nicht** nachgebaut (redundant und fehlerhaft);
`parent_left`/`parent_right` werden **nicht** nachgebaut (Odoo 18 nutzt `parent_path`).

## 5. Umgesetzte Anpassung in Odoo 18 (Modul `itk_partner_category`)

Leere, aber migrationsbereite Struktur — **keine Datensätze**:

| Anforderung | Umsetzung |
|---|---|
| Liste: Spalte **Anzeigename** | `display_name` (voller Hierarchiepfad), neue erste Spalte |
| Liste: Spalte **ID** | `id` |
| Liste: Spalte **Tag Anzeigename** | `name` (Label in der Liste: „Tag Anzeigename") |
| Liste: Kategorie + Farbe technisch erhalten, aber optional | `parent_id` und `color` mit `optional="hide"` (über die Spaltenauswahl weiter zuschaltbar) |
| Formular: **Tag Anzeigename** | `name` mit Label „Tag Anzeigename" |
| Formular: **übergeordnete Kategorie** | `parent_id` mit Label „Oberkategorie" |
| Formular: **untergeordnete Kategorien** | `child_ids` als read-only-Übersicht (Anzeigename + Aktiv), kein Anlegen/Löschen aus dem Formular |
| Formular: **Aktiv** / **Farbe** | wie in Odoo 18 vorhanden (Farbe als Farbwähler erhalten) |
| Formular: **voller Pfad read-only** | `display_name`, read-only, direkt unter dem Tag-Namen |
| Suche: **Filter Hauptkategorien** | Filter „Hauptkategorien (oberste Ebene)" = `[('parent_id','=',False)]` |
| Suche: **Filter verwendete Tags** | Filter „Verwendete Tags" = `[('partner_ids','!=',False)]` (plus Gegenstück „Unverwendete Tags") |
| Suche: **Vor-/Nachkontrolle der Hierarchie** | Filter „Unterkategorien (mit Oberkategorie)", „Mit Unterkategorien", „Ohne Unterkategorien (Blätter)" |
| Suche: **child_of / Hierarchiesuche erhalten** | zusätzliches Suchfeld `parent_id` mit `operator="child_of"`; `display_name`/`name`-Suche (child_of bei „like") unverändert |

**Ausdrücklich nicht umgesetzt:** Datenübernahme aller Art, `x_tag_anzeigename2`, `parent_left`/`parent_right`,
Änderungen am Kontaktformular oder an der Kontaktsuche (dort war nichts anzupassen).

## 6. Hinweise für die spätere Datenmigration (noch nicht ausgeführt)

1. `name` ist in Odoo 18 `translate=True` (jsonb) ⇒ Tag-Namen mit `lang=de_DE` schreiben, sonst landet der Wert im falschen Sprachslot.
2. Die Hierarchie kommt ausschließlich über `parent_id`; der O11-Pfad steckt in `display_name` (nicht als Feld speichern).
3. `color` bekommt in Odoo 18 neue Werte zufällig (1–11) — Odoo 11 Prod hatte durchgehend `0` ⇒ beim Import ggf. explizit `color = 0` setzen.
4. Reihenfolge für den späteren Import: erst Eltern, dann Kinder (oder zweiter Durchlauf zum Setzen von `parent_id`).
5. 13 Tag-Namen sind in O11 mehrfach belegt und nur über den Pfad unterscheidbar ⇒ beim Import ohne Hierarchie droht stilles Zusammenführen (siehe F33-unabhängige Analyse in PROJECT_KNOWLEDGE.md, Session 92).
6. Modul `itk_partner_category` gehört mit in das Produktiv-Deployment (leere Struktur, keine Daten).
