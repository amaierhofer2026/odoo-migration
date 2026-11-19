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
# Zeitstempel erhalten (bewusste Whitelist). Der zweite Wert nennt zusaetzliche
# Spalten, die nur dort existieren (crm.lead fuehrt z. B. date_open).
ERLAUBTE_MODELLE = {
    "crm.lead": ("crm_lead", ("date_open",)),
    "survey.survey": ("survey_survey", ()),
    "survey.question": ("survey_question", ()),
    "survey.question.answer": ("survey_question_answer", ()),
    "survey.user_input": ("survey_user_input", ()),
    "survey.user_input.line": ("survey_user_input_line", ()),
    "itk_valorisierung.valorisierung": ("itk_valorisierung_valorisierung", ()),
}


class ItkMigrationZeitstempel(models.TransientModel):
    _name = "itk.migration.zeitstempel"
    _description = "Technischer Importweg fuer Log-Access-Felder"

    @api.model
    def setze_zeitstempel(self, modell, zeilen, spalte="itk_o11_id"):
        """Setzt Zeitstempel und Benutzer je Datensatz.

        :param modell: Zielmodell (nur Modelle aus ERLAUBTE_MODELLE)
        :param zeilen: Liste von [schluessel, create_date, write_date,
                       date_open, create_uid, write_uid]
        :param spalte: ``itk_o11_id`` (Standard) oder ``id``. ``id`` ist noetig,
                       wenn sich Quell-IDs ueberlappen (Odoo-11-Seite 1 und
                       -Frage 1 liegen beide in survey.question).
        :return: Anzahl geschriebener Zeilen
        """
        eintrag = ERLAUBTE_MODELLE.get(modell)
        if not eintrag:
            raise ValueError("Modell nicht freigegeben: %s" % modell)
        if spalte not in ("itk_o11_id", "id"):
            raise ValueError("Schluesselspalte nicht erlaubt: %s" % spalte)
        tabelle, zusatz = eintrag
        # date_open nur schreiben, wenn die Tabelle die Spalte fuehrt; sonst
        # bricht das UPDATE fuer Modelle ohne diese Odoo-11-Sonderspalte ab.
        setzliste = ("create_date=%s, write_date=%s, "
                     "create_uid=COALESCE(%s::integer, create_uid), "
                     "write_uid=COALESCE(%s::integer, write_uid)")
        geschrieben = 0
        for zeile in zeilen or []:
            werte = [zeile[1], zeile[2], zeile[4], zeile[5]]
            sql = 'UPDATE "%s" SET %s' % (tabelle, setzliste)
            if "date_open" in zusatz:
                sql += ", date_open=%s"
                werte.append(zeile[3])
            sql += " WHERE %s=%%s" % spalte
            werte.append(zeile[0])
            self.env.cr.execute(sql, tuple(werte))
            geschrieben += self.env.cr.rowcount
        return geschrieben
