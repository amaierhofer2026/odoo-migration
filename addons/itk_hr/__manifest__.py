{
    "name": "ITK Personal",
    "summary": "Personalbereich im Odoo-11-Wortlaut (Odoo 11 zu Odoo 18)",
    "description": """
ITK Personal
============
Gleicht den Personalbereich in Odoo 18 an den Odoo-11-Stand an:

* Gruppenueberschriften "Kontaktinformationen" und "Position" im Kopfbereich des
  Mitarbeiterformulars (wie Odoo 11).
* Feld "Notizen" mit der Bezeichnung "Weitere Informationen" am Ende des Reiters
  "Arbeitsinformationen" (in Odoo 18 vorhanden, aber in keiner Ansicht eingebaut).
* Feldbezeichnungen im Odoo-11-Wortlaut: "Position" statt "Stelle", "Ausbilder" statt "Coach".
* Gruppierung "Ausbilder" in der Mitarbeitersuche.
* Mitarbeiterliste ohne Aktivitaetsspalten (Odoo 11 kannte keine Aktivitaeten).
* Menuebenennung "Personal" wie in Odoo 11 (App, Untermenue, Aktion, Listentitel).
* Leserecht auf Mitarbeiter und Stellen fuer alle internen Benutzer (Odoo-11-Stand);
  Menue "Abteilungen" nur fuer Personalsachbearbeiter (Odoo-11-Stand).

Es werden KEINE Datensaetze angelegt oder uebernommen.

Vergleich und Begruendung: docs/o11-o18-strukturvergleich-personal.md
""",
    "version": "18.0.1.0.1",
    "license": "LGPL-3",
    "category": "ITK - Specific Industry Applications",
    "author": "IT-Kommunal GmbH",
    "website": "https://www.it-kommunal.at",
    "depends": [
        "hr",
    ],
    "data": [
        "security/personal_rechte.xml",
        "views/hr_employee_views.xml",
        "views/hr_menus.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
