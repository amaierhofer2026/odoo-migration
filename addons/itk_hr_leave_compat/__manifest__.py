{
    "name": "ITK Urlaubsantraege und Anwesenheiten",
    "summary": "Odoo-11-Oberflaeche fuer Abwesenheiten und Anwesenheiten im Odoo 18",
    "description": """ITK Urlaubsantraege und Anwesenheiten
=====================================

Gleicht den Bereich "Anwesenheiten und Urlaubsantraege / Abwesenheiten" in
Odoo 18 an den Odoo-11-Stand an:

* Menue "Urlaubsantraege" mit den Odoo-11-Eintraegen "Mein Urlaubskonto"
  (Urlaubsantrag, Auswertung Urlaubskonto, Urlaubsanspruch anfragen),
  "Zu bestaetigender Urlaub" (Urlaubsantraege, Urlaubsanspruch) und
  "Berichtswesen" (Urlaubdetails, Urlaubsantraege, Urlaub nach Abteilung).
* Filter und Gruppierungen der Odoo-11-Suche: "Zur Genehmigung", "Aktive Typen",
  "Urlaube meiner Abteilung", "Mein Teamurlaub", Gruppen "Manager" und "Pruefer".
* Anwesenheiten: Spalte und Feld "Homeoffice" (Odoo-11-Feld x_homeoffice, das in
  Odoo 18 fehlt) in Liste und Formular.
* Abwesenheiten: schreibgeschuetztes Feld "Tage (Odoo 11)" mit der in Odoo 11
  gespeicherten Tagesanzahl (Odoo 18 rechnet die Dauer selbst neu).
* Gruppe "Anwesenheit manuell" (Odoo-11-Gruppe 34): eigene Anwesenheiten
  erfassen und korrigieren - in Odoo 18 duerfen interne Benutzer Anwesenheiten
  nur lesen.

Die Odoo-18-Zusatzfunktionen (Dashboard, Verwaltung, Konfiguration, Saldo,
Feiertage, Kioskmodus, Ueberstunden) bleiben unveraendert erhalten.

Vergleich und Begruendung: docs/o11-o18-anwesenheiten-urlaub-vergleich.md
""",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "category": "ITK - Specific Industry Applications",
    "author": "IT-Kommunal GmbH",
    "website": "https://www.it-kommunal.at",
    "depends": [
        "hr_holidays",
        "hr_attendance",
        "hr_holidays_public"
    ],
    "data": [
        "security/itk_anwesenheiten_rechte.xml",
        "views/hr_attendance_views.xml",
        "views/hr_leave_views.xml",
        "views/menus.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
