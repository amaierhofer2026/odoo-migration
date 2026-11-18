# -*- coding: utf-8 -*-
"""Technischer Importweg fuer Log-Access-Felder (create_date, write_date, ...).

Odoo 18 entfernt ``create_uid``/``create_date``/``write_uid``/``write_date`` in
``models._sanitize_vals`` aus jedem ``create``/``write`` - auch fuer den
Administrator. Fuer die Migration muessen diese Werte aber den Odoo-11-Stand
tragen (Erstellungsdatum, letzte Bearbeitung, Ersteller).

Diese TransientModel-Methode fuehrt deshalb ein gezieltes SQL-Update aus. Sie ist
bewusst auf bekannte Modelle mit ``itk_o11_id`` beschraenkt und enthaelt keine
Fachlogik - reine Migrationsinfrastruktur.
"""
from odoo import api, models

# Modell -> Tabelle; nur diese Modelle duerfen ueber den technischen Weg
# Zeitstempel erhalten (bewusste Whitelist).
ERLAUBTE_MODELLE = {
    "crm.lead": "crm_lead",
}


class ItkMigrationZeitstempel(models.TransientModel):
    _name = "itk.migration.zeitstempel"
    _description = "Technischer Importweg fuer Log-Access-Felder"

    @api.model
    def setze_zeitstempel(self, modell, zeilen):
        """Setzt Zeitstempel und Benutzer je Odoo-11-ID.

        :param modell: Zielmodell (nur Modelle aus ERLAUBTE_MODELLE)
        :param zeilen: Liste von [itk_o11_id, create_date, write_date,
                       date_open, create_uid, write_uid]
        :return: Anzahl geschriebener Zeilen
        """
        tabelle = ERLAUBTE_MODELLE.get(modell)
        if not tabelle:
            raise ValueError("Modell nicht freigegeben: %s" % modell)
        geschrieben = 0
        for zeile in zeilen or []:
            self.env.cr.execute(
                'UPDATE "%s" SET create_date=%%s, write_date=%%s, date_open=%%s, '
                'create_uid=COALESCE(%%s::integer, create_uid), '
                'write_uid=COALESCE(%%s::integer, write_uid) '
                'WHERE itk_o11_id=%%s' % tabelle,
                (zeile[1], zeile[2], zeile[3], zeile[4], zeile[5], zeile[0]),
            )
            geschrieben += self.env.cr.rowcount
        return geschrieben
