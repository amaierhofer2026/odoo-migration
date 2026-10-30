{
    "name": "ITK E-Mail-Marketing",
    "summary": "Mailingkampagnen mit Stufen aus Odoo 11 und historische Kennzahlen",
    "description": """ITK E-Mail-Marketing
====================

Ergaenzt das Odoo-18-Modul `mass_mailing` um die Teile des Odoo-11-Bereichs
E-Mail-Marketing, die Odoo 18 nicht mehr kennt:

* Mailingkampagnen als eigenes Modell (`itk.mailing.campaign`) mit Stufen
  (`itk.mailing.campaign.stage`: Ausfuehrungsplan, Design, Gesendet) und
  Kampagnen-Tags - die Odoo-11-Kampagnenlogik bleibt damit erhalten.
* Historische Odoo-11-Kennzahlen je Kampagne und je Mailing (gesendet,
  zugestellt, geoeffnet, geantwortet, Bounces, fehlgeschlagen, Quoten).
  Sie stehen bewusst in eigenen Feldern (Praefix `x_o11_`) und sind damit
  klar von den Kennzahlen getrennt, die Odoo 18 kuenftig aus
  `mailing.trace` selbst berechnet.
* Odoo-11-Bezeichnung des Mailings (`x_o11_name`), historisches geplantes
  Sendedatum (`x_o11_schedule_date`, nur Information) und die
  Odoo-11-Datensatz-ID (`x_o11_id`) fuer Idempotenz und Nachverknuepfung.
* **Versandsperre:** Uebernommene historische Mailings (`x_o11_id` gesetzt)
  koennen nicht gesendet, nicht in die Warteschlange gelegt und nicht auf
  "Im Versand" gesetzt werden. Ein erneuter Versand alter Mailings ist damit
  technisch ausgeschlossen.

Nicht enthalten und bewusst nicht uebernommen: Kontakte, Personen, Partner,
E-Mail-Adressen, Mailinglisten-Mitglieder, Empfaenger, `mailing.trace`-
Datensaetze sowie Blacklist-/Opt-out-Adressen. Diese folgen mit der
Kontakt- und Personendatenmigration.

Vergleich und Begruendung: docs/o11-o18-email-marketing-vergleich.md
""",
    "version": "18.0.1.1.0",
    "license": "LGPL-3",
    "category": "ITK - Specific Industry Applications",
    "author": "IT-Kommunal GmbH",
    "website": "https://www.it-kommunal.at",
    "depends": [
        "mass_mailing"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/mailing_views.xml",
        "views/campaign_views.xml",
        "views/menus.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}
