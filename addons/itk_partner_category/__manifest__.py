{
    "name": "ITK Kontakt-Tags",
    "summary": "Migrationsbereite Struktur der Kontakt-Tags (Odoo 11 Prod) - ohne Daten",
    "description": """
ITK Kontakt-Tags
================
Bereitet die Kontakt-Tags (res.partner.category) in Odoo 18 so auf, dass die
Bedienung der Odoo-11-Produktivumgebung entspricht:

* Liste: Spalte "Anzeigename" (voller Hierarchiepfad), Spalte "ID",
  Spalte "Tag Anzeigename" (der eigentliche Tag-Name);
  "Kategorie" und "Farbe" bleiben technisch erhalten, sind aber optional.
* Formular: "Tag Anzeigename", "Oberkategorie", "Untergeordnete Kategorien",
  "Aktiv", "Farbe" sowie der vollstaendige Pfad read-only.
* Suche: Filter nach Hauptkategorien, verwendeten Tags und zur
  Hierarchie-Kontrolle; Hierarchiesuche (child_of) bleibt erhalten.

Es werden KEINE Datensaetze angelegt oder aus Odoo 11 uebernommen.
Das O11-Studio-Feld x_tag_anzeigename2 wird bewusst nicht nachgebaut
(redundant und fehlerhaft) - der Pfad kommt aus display_name, die Hierarchie
aus parent_id/parent_path.

Vergleich und Begruendung: docs/o11-o18-strukturvergleich-kontakt-tags.md
""",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "category": "ITK - Specific Industry Applications",
    "author": "IT-Kommunal GmbH",
    "website": "https://www.it-kommunal.at",
    "depends": [
        "base",
    ],
    "data": [
        "views/res_partner_category_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
