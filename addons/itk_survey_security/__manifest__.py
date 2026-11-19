# -*- coding: utf-8 -*-
{
    "name": "ITK Umfragen - Sichtbarkeit der Antworten",
    "summary": "Normale Umfrage-Benutzer sehen nur ihre eigenen Teilnahmen (wie Odoo 11)",
    "description": """
ITK Umfragen - Sichtbarkeit der Antworten
=========================================

Odoo 11 hat normale Umfrage-Benutzer auf die **eigenen** Teilnahmen und Antworten
beschraenkt (Record Rule ``create_uid = user`` bzw. ``partner_id = user.partner_id``).
Odoo 18 laesst die Gruppe "Umfragen / Benutzer" dagegen **alle** Antworten sehen.

Dieses Modul stellt das Odoo-11-Prinzip wieder her, ohne Odoo 18 zurueckzubauen:

- Die beiden Gruppenregeln des Moduls ``survey`` fuer ``survey.user_input`` und
  ``survey.user_input.line`` werden mit derselben XML-ID ueberschrieben. Sie sind im
  Modul ``survey`` unter ``noupdate="1"`` abgelegt, ein Upgrade von ``survey`` setzt sie
  also nicht zurueck.
- Die Einschraenkung auf "normale" Umfragetypen bleibt erhalten.
- Die Manager-Regeln des Moduls ``survey`` bleiben unveraendert. Odoo kombiniert
  Gruppenregeln mit ODER: Ein Benutzer, der zusaetzlich in "Umfragen / Administrator"
  ist, sieht weiterhin alle Antworten. Das Administratorkonto ist unberuehrt.
- Oeffentliche Umfragen (Ausfuellen ohne Anmeldung) laufen ueber den Controller mit
  erhoehten Rechten und sind nicht betroffen.

Keine neuen Felder, keine Datenmigration: reine Rechtekonfiguration im Repository.
""",
    "version": "18.0.1.0.0",
    "category": "ITK - Specific Industry Applications",
    "author": "IT-Kommunal GmbH",
    "license": "LGPL-3",
    "depends": ["survey"],
    "data": [
        "security/survey_security.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
