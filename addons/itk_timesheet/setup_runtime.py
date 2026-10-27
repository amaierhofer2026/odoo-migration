"""Laufzeit-Setup itk_timesheet: Menue-Wortlaute im Odoo-11-Wortlaut.

Hintergrund (Lehre aus Session 114/115): Menue-/Aktionsnamen sind Moduldaten mit
`noupdate` - ein Modul-Upgrade setzt nur die QUELLE zurueck, die alte de_DE-
Uebersetzung bleibt in der Datenbank stehen und ueberdeckt die Quelle in der
Oberflaeche. Deshalb werden Quelle UND beide Sprachen geschrieben, und zwar bei
jeder Installation (post_init) und jedem Upgrade (post-migration).
"""
import logging

_logger = logging.getLogger(__name__)

# xmlid -> sichtbarer Name (Odoo-11-Wortlaut)
MENUE_WORTLAUTE = {
    "hr_timesheet.timesheet_menu_activity_mine": "Meine Stundenzettel",
    # Odoo 11: die obere Menuezeile hiess ebenfalls "Meine Stundenzettel"
    "hr_timesheet.timesheet_menu_activity_user": "Meine Stundenzettel",
    "sale_timesheet.menu_timesheet_billing_analysis": "Nach Abrechnungsrate",
    "hr_timesheet_attendance.menu_hr_timesheet_attendance_report": "Anwesenheit",
}


def setze_menue_wortlaute(env):
    """Setzt die Menue-Namen in Quelle, de_DE und en_US (idempotent)."""
    for xmlid, name in MENUE_WORTLAUTE.items():
        menu = env.ref(xmlid, raise_if_not_found=False)
        if not menu:
            _logger.warning("itk_timesheet: Menue %s nicht gefunden", xmlid)
            continue
        menu.write({"name": name})
        menu.with_context(lang="de_DE").write({"name": name})
        menu.with_context(lang="en_US").write({"name": name})
        _logger.info("itk_timesheet: Menue %s -> %s", xmlid, name)


# Aktionen mit sichtbarem Namen (Breadcrumb/Titel), die den Odoo-11-Wortlaut tragen
AKTION_WORTLAUTE = {
    "hr_timesheet.act_hr_timesheet_line": "Meine Stundenzettel",
}


def setze_aktions_wortlaute(env):
    """Aktionsnamen in Quelle, de_DE und en_US setzen (idempotent)."""
    for xmlid, name in AKTION_WORTLAUTE.items():
        akt = env.ref(xmlid, raise_if_not_found=False)
        if not akt:
            _logger.warning("itk_timesheet: Aktion %s nicht gefunden", xmlid)
            continue
        akt.write({"name": name})
        akt.with_context(lang="de_DE").write({"name": name})
        akt.with_context(lang="en_US").write({"name": name})


def setup_all(env):
    setze_aktions_wortlaute(env)
    setze_menue_wortlaute(env)
    _logger.info("itk_timesheet setup_runtime: Wortlaute gesetzt")
