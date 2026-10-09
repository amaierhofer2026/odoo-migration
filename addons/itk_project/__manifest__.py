{
    "name": "ITK Projekt",
    "summary": "Migrationsbereite Projektstruktur (Odoo 11 zu Odoo 18) - ohne Daten",
    "description": """
ITK Projekt
===========
Bereitet das Projektmodul in Odoo 18 so auf, dass ITK fachlich wie in Odoo 11
arbeiten kann: deutsche Bezeichnungen im Odoo-11-Wortlaut, Prioritaet Niedrig/Normal,
Startdatum auf der Aufgabe, deutsche Projektphasen. Es werden KEINE Datensaetze aus
Odoo 11 uebernommen.

Vergleich und Begruendung: docs/o11-o18-projekt-vergleich.md
""",
    "version": "18.0.1.0.1",
    "license": "LGPL-3",
    "category": "ITK - Specific Industry Applications",
    "author": "IT-Kommunal GmbH",
    "website": "https://www.it-kommunal.at",
    "depends": [
        "project",
        "hr_timesheet",
        "sale_project",
        "sale_timesheet",
    ],
    "data": [
        "data/project_project_stage.xml",
        "views/project_project_views.xml",
        "views/project_task_views.xml",
        "views/project_task_type_views.xml",
        "views/project_kanban_views.xml",
        "views/project_menus.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
