{
    "name": "ITK Zeiterfassung",
    "summary": "Zeiterfassung in Odoo 18 im Odoo-11-Wortlaut (Ansichten, Suche, Menues, Berichte)",
    "description": """
ITK Zeiterfassung
=================
Bringt die Zeiterfassung in Odoo 18 auf den fachlichen und sichtbaren Stand von
Odoo 11, ohne Odoo-18-Funktionen zu entfernen:

* Liste und Formular: Spalte "Zeit (Stunden)" mit Summe "Gesamtdauer",
  Beschreibung als Pflichtfeld, Datum im Formular sichtbar,
  Startzeit/Endzeit (Odoo 18) als optionale Spalten.
* Suche: Filter "Meine Stundenzettel", "Abrechenbare Stunden",
  "Projekte mit Festpreis", "Nicht abrechenbare Stunden", "Mit Ticket",
  neuer Filter "Dieser Monat" (Odoo 11), Gruppierung "Monatliche Zeiterfassung".
* Menues im Odoo-11-Wortlaut: "Meine Stundenzettel", "Nach Abrechnungsrate",
  "Anwesenheit"; neues Berichtsmenue "Kosten und Erloese" (Odoo 11).
* Favorit "Abrechnungsrate" (Odoo 11) wieder vorhanden.
* Spalte "Referenz" (optional) und Formularfeld fuer die historische Odoo-11-
  Ticketnummer/Aufgabe/Kostenstelle, Filter "Mit historischer Referenz".

Reine Ansichts-/Anzeigeanpassung, keine Datenmigration.
Vergleich: docs/o11-o18-zeiterfassung-vergleich.md
""",
    "version": "18.0.1.0.6",
    "license": "LGPL-3",
    "category": "ITK - Specific Industry Applications",
    "author": "IT-Kommunal GmbH",
    "website": "https://www.it-kommunal.at",
    "depends": [
        "hr_timesheet",
        "sale_timesheet",
        "project_timesheet_time_control",
        "helpdesk_mgmt_timesheet",
    ],
    "data": [
        "views/timesheet_views.xml",
        "views/timesheet_search.xml",
        "views/timesheet_report.xml",
        "data/ir_filters.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
