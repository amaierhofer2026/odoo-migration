"""Erzeugt addons/itk_project/i18n/de.po aus den englischen Feldbezeichnungen im Projektbereich.

Read-only gegenueber Odoo; schreibt nur die PO-Datei im Repo.
Aufruf: python scripts/gen_projekt_de_po.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _o11o18_client import o18  # noqa: E402

ZIEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "addons", "itk_project", "i18n", "de.po")

# Deutsche Bezeichnungen je (Modell, Feld). Odoo-11-Wortlaut wo direkt vorhanden.
DE = {
    ("project.project", "access_instruction_message"): "Hinweis zur Freigabe",
    ("project.project", "active"): "Aktiv",
    ("project.project", "activity_exception_icon"): "Symbol",
    ("project.project", "analytic_account_active"): "Aktive Kostenstelle",
    ("project.project", "can_mark_milestone_as_done"): "Meilenstein abschliessbar",
    ("project.project", "closed_task_count"): "Abgeschlossene Aufgaben",
    ("project.project", "collaborator_count"): "Anzahl Mitwirkende",
    ("project.project", "collaborator_ids"): "Mitwirkende",
    ("project.project", "color"): "Farbkennzeichnung",
    ("project.project", "currency_id"): "Währung",
    ("project.project", "display_sales_stat_buttons"): "Verkaufs-Kennzahlen anzeigen",
    ("project.project", "encode_uom_in_days"): "Zeiteinheit in Tagen",
    ("project.project", "favorite_user_ids"): "Mitglieder",
    ("project.project", "has_any_so_to_invoice"): "Auftrag mit offener Rechnung",
    ("project.project", "has_any_so_with_nothing_to_invoice"): "Auftrag ohne Rechnungsbedarf",
    ("project.project", "is_favorite"): "Projekt auf dem Dashboard anzeigen",
    ("project.project", "is_internal_project"): "Internes Projekt",
    ("project.project", "is_milestone_deadline_exceeded"): "Meilenstein-Frist überschritten",
    ("project.project", "is_milestone_exceeded"): "Meilenstein überschritten",
    ("project.project", "is_project_overtime"): "Projekt über Plan",
    ("project.project", "label_tickets"): "Tickets verwenden als",
    ("project.project", "last_update_color"): "Farbe Projektstatus",
    ("project.project", "last_update_id"): "Letzte Aktualisierung",
    ("project.project", "last_update_status"): "Projektstatus",
    ("project.project", "milestone_count"): "Anzahl Meilensteine",
    ("project.project", "milestone_count_reached"): "Erreichte Meilensteine",
    ("project.project", "milestone_ids"): "Meilensteine",
    ("project.project", "milestone_progress"): "Meilensteine erreicht",
    ("project.project", "next_milestone_id"): "Nächster Meilenstein",
    ("project.project", "open_task_count"): "Offene Aufgaben",
    ("project.project", "privacy_visibility_warning"): "Hinweis zur Sichtbarkeit",
    ("project.project", "purchase_orders_count"): "Anzahl Bestellungen",
    ("project.project", "rating_request_deadline"): "Frist Bewertungsanfrage",
    ("project.project", "resource_calendar_id"): "Arbeitszeit",
    ("project.project", "sale_line_employee_ids"): "Zuordnung Auftragsposition/Mitarbeiter",
    ("project.project", "sale_order_count"): "Verkaufsaufträge",
    ("project.project", "sale_order_id"): "Auftragsreferenz",
    ("project.project", "sale_order_line_count"): "Anzahl Auftragspositionen",
    ("project.project", "sequence"): "Nummernfolge",
    ("project.project", "show_time_control"): "Zeitsteuerung anzeigen",
    ("project.project", "task_completion_percentage"): "Aufgabenfortschritt (%)",
    ("project.project", "task_count"): "Aufgaben",
    ("project.project", "task_ids"): "Aufgaben",
    ("project.project", "ticket_count"): "Tickets",
    ("project.project", "ticket_ids"): "Tickets",
    ("project.project", "timesheet_encode_uom_id"): "Zeiteinheit der Zeiterfassung",
    ("project.project", "timesheet_ids"): "Zeiterfassung",
    ("project.project", "todo_ticket_count"): "Anzahl Tickets",
    ("project.project", "total_timesheet_time"): "Gesamtzeit (Projekteinheit, gerundet)",
    ("project.project", "type_ids"): "Aufgabenstufen",
    ("project.project", "update_count"): "Anzahl Aktualisierungen",
    ("project.project", "update_ids"): "Aktualisierungen",
    ("project.project", "warning_employee_rate"): "Warnung Mitarbeitersatz",
    ("project.task", "active"): "Aktiv",
    ("project.task", "activity_exception_icon"): "Symbol",
    ("project.task", "allow_milestones"): "Meilensteine",
    ("project.task", "allow_task_dependencies"): "Aufgabenabhängigkeiten",
    ("project.task", "allow_timesheets"): "Zeiterfassungen erlauben",
    ("project.task", "analytic_account_active"): "Aktive Kostenstelle",
    ("project.task", "attachment_ids"): "Hauptanhänge",
    ("project.task", "child_ids"): "Unteraufgaben",
    ("project.task", "closed_subtask_count"): "Abgeschlossene Unteraufgaben",
    ("project.task", "color"): "Farbkennzeichnung",
    ("project.task", "current_user_same_company_partner"): "Aktueller Benutzer aus derselben Firma",
    ("project.task", "dependent_ids"): "Blockiert",
    ("project.task", "dependent_tasks_count"): "Blockierte Aufgaben",
    ("project.task", "display_follow_button"): "Folgen-Knopf anzeigen",
    ("project.task", "display_in_project"): "In Projekt anzeigen",
    ("project.task", "display_parent_task_button"): "Knopf Übergeordnete Aufgabe anzeigen",
    ("project.task", "encode_uom_in_days"): "Zeiteinheit in Tagen",
    ("project.task", "has_late_and_unreached_milestone"): "Meilenstein überschritten und offen",
    ("project.task", "is_timeoff_task"): "Abwesenheitsaufgabe",
    ("project.task", "label_tickets"): "Tickets verwenden als",
    ("project.task", "link_preview_name"): "Linkvorschau",
    ("project.task", "personal_stage_type_ids"): "Persönliche Phasen",
    ("project.task", "portal_user_names"): "Portal-Benutzer",
    ("project.task", "remaining_hours_percentage"): "Verbleibende Zeit (%)",
    ("project.task", "sequence"): "Nummernfolge",
    ("project.task", "show_time_control"): "Zeitsteuerung anzeigen",
    ("project.task", "subtask_allocated_hours"): "Zugewiesene Zeit der Unteraufgaben",
    ("project.task", "subtask_completion_percentage"): "Unteraufgaben-Fortschritt (%)",
    ("project.task", "subtask_count"): "Anzahl Unteraufgaben",
    ("project.task", "ticket_count"): "Tickets",
    ("project.task", "ticket_ids"): "Tickets",
    ("project.task", "timesheet_ids"): "Zeiterfassung",
    ("project.task", "todo_ticket_count"): "Anzahl Tickets",
    ("project.task", "website_message_ids"): "Website-Nachrichten",
    ("project.task.type", "active"): "Aktiv",
    ("project.task.type", "disabled_rating_warning"): "Hinweis: Bewertung deaktiviert",
    ("project.tags", "project_ids"): "Projekte",
    ("project.tags", "task_ids"): "Aufgaben",
}


def main() -> int:
    cli = o18("lokal")
    zeilen = ['# German translation override - ITK Projekt (itk_project)',
              '# Setzt deutsche Bezeichnungen fuer Projekt-, Aufgaben-, Stufen- und Tag-Felder,',
              '# die Odoo 18 englisch ausliefert. Reine Uebersetzung, keine Datenmigration.',
              'msgid ""', 'msgstr ""',
              '"Project-Id-Version: itk_project 18.0.1.0.1\\n"',
              '"Language: de\\n"',
              '"Plural-Forms: nplurals=2; plural=(n != 1);\\n"', '']

    # Eintraege nach (msgid, msgstr) gruppieren, damit mehrere Felder je Text erfasst werden
    gruppen = {}
    offen = []
    for (modell, feld), deutsch in DE.items():
        r = cli.kw("ir.model.fields", "search_read", [[("model", "=", modell), ("name", "=", feld)]],
                   fields=["id", "field_description"], limit=1)
        if not r:
            offen.append("%s.%s" % (modell, feld))
            continue
        fid, englisch = r[0]["id"], r[0]["field_description"] or ""
        md = cli.kw("ir.model.data", "search_read",
                    [[("model", "=", "ir.model.fields"), ("res_id", "=", fid)]],
                    fields=["module", "name"], limit=1)
        if not md:
            offen.append("%s.%s (kein xmlid)" % (modell, feld))
            continue
        modul, name = md[0]["module"], md[0]["name"]
        ref = "model:ir.model.fields,field_description:%s.%s" % (modul, name)
        gruppen.setdefault((englisch, deutsch), []).append((modul, ref))

    for (englisch, deutsch), refs in gruppen.items():
        modul = refs[0][0]
        zeilen.append("#. module: %s" % modul)
        for _m, ref in refs:
            zeilen.append("#: %s" % ref)
        zeilen.append('msgid "%s"' % englisch.replace('"', '\\"'))
        zeilen.append('msgstr "%s"' % deutsch.replace('"', '\\"'))
        zeilen.append("")

    os.makedirs(os.path.dirname(ZIEL), exist_ok=True)

    # Zusaetzlich: Arch-Texte der Zeitsteuerungs-Knoepfe ("Start work"/"Stop") deutsch.
    # Diese Knoepfe stehen in mehreren Ansichten des Moduls project_timesheet_time_control;
    # die Uebersetzung wirkt unabhaengig von der View-Vererbungsreihenfolge.
    arch_views = ["project_invoice_form", "view_project_kanban_inherited", "view_project_tree",
                  "view_task_form2_inherited", "view_task_kanban", "view_task_tree2_inherited"]
    for englisch, deutsch in (("Start work", "Arbeit starten"), ("Stop", "Stopp")):
        zeilen.append("#. module: project_timesheet_time_control")
        for name in arch_views:
            zeilen.append("#: model_terms:ir.ui.view,arch_db:project_timesheet_time_control.%s" % name)
        zeilen.append('msgid "%s"' % englisch)
        zeilen.append('msgstr "%s"' % deutsch)
        zeilen.append("")

    with open(ZIEL, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(zeilen) + "\n")
    print("geschrieben: %s (%d Eintraege)" % (ZIEL, len(gruppen)))
    print("XMLIDS:", ",".join(sorted({ref.split(":", 2)[2] for refs in gruppen.values() for _m, ref in refs})))
    if offen:
        print("NICHT AUFLOESBAR:", offen)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
