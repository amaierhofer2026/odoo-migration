{
    "name": "ITK Events",
    "summary": "Odoo-11-Oberflaeche fuer Veranstaltungen im Odoo 18",
    "description": """ITK Events
=========

Gleicht den Bereich "Events" (Odoo 11) in Odoo 18 an den Odoo-11-Stand an:

* Menue im Odoo-11-Wortlaut: App "Events" mit "Events", "Berichtswesen"
  (neu: "Events" als Pivot/Graph) und "Konfiguration" ("Anlasskategorien").
* Status wie Odoo 11: die Odoo-18-Phasen tragen die Odoo-11-Bezeichnungen
  "Nicht bestaetigt", "Bestaetigt", "Erledigt", "Abgebrochen"; die Phase
  "Angekuendigt" bleibt als Odoo-18-Zusatz erhalten.
* Feld "Kategorie" (Odoo 11: event_type_id), Liste mit Kategorie und
  Mindestzahl, Formular mit Online-Kennzeichen und Mindestzahl.
* Odoo-11-Suchfilter "Nicht bestaetigt", "Bestaetigt", "Erledigt",
  "Abgebrochen".
* Lesbarer Block "Odoo-11-Angaben" mit der historischen Odoo-11-ID, dem
  Odoo-11-Status, der Anzahl der Odoo-11-Anmeldungen sowie den Odoo-11-IDs
  von Veranstalter und Ort (fuer die spaetere Nachverknuepfung nach der
  Kontaktmigration).
* Schutz: der Odoo-18-Cron "Event: Mail Scheduler" wird stillgelegt, damit
  uebernommene historische Mailplaner keine E-Mails ausloesen.

Die Odoo-18-Zusatzfunktionen (Phasen, Stichwoerter, Tickets, Registrierungs-
schalter, Fragen, Kanban, Website) bleiben unveraendert erhalten.

Vergleich und Begruendung: docs/o11-o18-events-vergleich.md
""",
    "version": "18.0.1.0.3",
    "license": "LGPL-3",
    "category": "ITK - Specific Industry Applications",
    "author": "IT-Kommunal GmbH",
    "website": "https://www.it-kommunal.at",
    "depends": [
        "event",
        "website_event"
    ],
    "data": [
        "data/itk_event_stages.xml",
        "data/itk_cron_schutz.xml",
        "views/event_event_views.xml",
        "views/event_type_views.xml",
        "views/menus.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
