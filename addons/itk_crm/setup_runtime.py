"""ITK-CRM-Laufzeit-Setup (idempotent).

Alle Funktionen stellen den Odoo-11-kompatiblen CRM-Aufbau (Kundenverwaltung)
her und sind mehrfach ausfuehrbar. Aufgerufen von:
- hooks.py post_init_hook (Neuinstallation)
- migrations/<version>/post-migration.py (Upgrade — laeuft auch nach jedem
  Restore, weil die DB dann eine aeltere Modulversion hat)
"""
import json
import logging

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom-Felder auf crm.lead: char -> selection (x_Anrede_Lead ist Modelfeld)
# ---------------------------------------------------------------------------
_CUSTOM_FIELDS = {
    'x_Lead_Quelle': (
        'Lead Quelle',
        [
            'Excel Leads (230317)',
            'Versand Hinweis (230307)',
            'Webinar VKÖ/VÖWG (230306)',
            'Webinar OGD (230321)',
            'Versand Hinweis Intern (230411/230419/230502/230620)',
            'Versand Intrakommuna (2307)',
            'Versand Online Formulare (231206)',
            'IFG Webinare (2025-02-05/02-19/03-12/03-26/04-24/05-27/06-11/07-22/07-31)',
            'Recherchierte Adressen April 2025',
            'Anonym-Portal (2025-04-23/05-15)',
            'ITK & VÖWG Webinar (2025-06-24)',
        ],
    ),
    'x_Produktinteresse': (
        'Produktinteresse',
        [
            'OGD Publikationsservice', 'Hinweisportal', 'Acta Nova', 'Communex',
            'Online Formulare', 'Gemeindecloud', 'Sonstiges', 'Verwaltungsmanager',
            'IFG', 'Anonym-Portal',
        ],
    ),
    'x_lead_status': (
        'Lead Status',
        [
            'Lead angelegt', 'Lead aufbereitet', 'Lead kontaktiert',
            'Nicht erreicht / Rückruf', 'On-Hold', 'Lead verloren',
            'VK-Chance vorhanden', 'Event/Webinar angemeldet', 'Bereits Kunde',
            'Termin vereinbart', 'Event/Webinar teilgenommen',
            'Webinar teilgenommen bzw. angemeldet',
        ],
    ),
}

_STAGES = {
    'crm.stage_lead1': ('Neu', 1, False, False),
    'crm.stage_lead2': ('Angebotsphase', 2, False, False),
    'crm.stage_lead3': ('On-Hold', 3, False, False),
    'crm.stage_lead4': ('Erfolgreich', 5, False, True),
    'itk_crm.stage_positive_rueckmeldung': ('Positive Rückmeldung', 4, False, False),
    'itk_crm.stage_zur_verrechnung': ('Zur Verrechnung bereit', 6, False, False),
    'itk_crm.stage_verloren': ('Verloren', 7, True, False),
    'itk_crm.stage_verrechnet': ('Verrechnet', 8, True, False),
}


def setup_all(env):
    """Alle Struktur-/Laufzeit-Setups ausfuehren (idempotent)."""
    _logger.info("itk_crm setup_runtime: Struktur-Setup startet...")
    _setup_custom_fields(env)
    _setup_stage_labels(env)
    _setup_app_name(env)
    _setup_crm_menus(env)
    _setup_lost_reasons(env)
    _setup_automated_action(env)
    _setup_activity_kanban(env)
    _setup_activity_types(env)
    _setup_vertriebskanaele_labels(env)
    _logger.info("itk_crm setup_runtime: Struktur-Setup abgeschlossen")


def _setup_custom_fields(env):
    """crm.lead: x_Lead_Quelle/x_Produktinteresse/x_lead_status char->selection
    (idempotent). x_Anrede_Lead ist ein Modelfeld (models.py)."""
    cr = env.cr
    Field = env['ir.model.fields']
    for fname, (label, options) in _CUSTOM_FIELDS.items():
        field = Field.search([('model', '=', 'crm.lead'), ('name', '=', fname)], limit=1)
        if not field:
            continue
        cr.execute(
            "UPDATE ir_model_fields SET ttype='selection' WHERE id=%s", (field.id,))
        cr.execute("DELETE FROM ir_model_fields_selection WHERE field_id=%s", (field.id,))
        for seq, opt in enumerate(options, 1):
            cr.execute(
                "INSERT INTO ir_model_fields_selection (field_id, sequence, value, name) "
                "VALUES (%s, %s, %s, %s::jsonb)",
                (field.id, seq, opt, json.dumps({'en_US': opt, 'de_DE': opt})),
            )
        _logger.info("itk_crm: Custom field %s -> selection (%d Werte)", fname, len(options))


def _setup_stage_labels(env):
    """Stages: Namen (de_DE + en_US), Reihenfolge, fold/is_won (idempotent)."""
    for xmlid, (name, seq, fold, is_won) in _STAGES.items():
        try:
            stage = env.ref(xmlid)
        except ValueError:
            _logger.warning("itk_crm: Stage %s nicht gefunden (xmlid)", xmlid)
            continue
        stage.with_context(lang='de_DE').write({'name': name})
        stage.with_context(lang='en_US').write({'name': name})
        stage.write({'sequence': seq, 'fold': fold, 'is_won': is_won})
    _logger.info("itk_crm: 8 CRM-Stages (Kundenverwaltung) sichergestellt")


def _setup_app_name(env):
    """App-Kategorie 13: 'CRM' -> 'Kundenverwaltung'."""
    cat = env['ir.module.category'].sudo().browse(13)
    if cat.exists():
        cat.with_context(lang='de_DE').write({'name': 'Kundenverwaltung'})
        cat.with_context(lang='en_US').write({'name': 'Kundenverwaltung'})
        _logger.info("itk_crm: App-Name -> Kundenverwaltung")


def _setup_crm_menus(env):
    """Menüstruktur Kundenverwaltung (O11-kompatibel, idempotent).

    Aufbau:
    Kundenverwaltung (143)
    ├── Aktivitäten (unter 143, Action itk_crm.action_aktivitaeten)
    ├── Pipeline (144)
    │   ├── Pipeline (CRM: My Pipeline)
    │   ├── Interessenten (itk_crm.action_interessenten)
    │   ├── Angebote (sale.action_quotations)
    │   └── Teams (147, bleibt)
    ├── Kunden (148)
    ├── Berichtswesen (150)
    └── Konfiguration (155)
    """
    Menu = env['ir.ui.menu'].sudo()

    def _rename(menu_id, name):
        menu = Menu.browse(menu_id)
        if menu.exists():
            menu.with_context(lang='de_DE').write({'name': name})
            menu.with_context(lang='en_US').write({'name': name})

    def _ensure_menu(name, parent_id, action_ref, seq, old_xmlids=()):
        existing = Menu.with_context(lang='en_US').search(
            [('name', '=', name), ('parent_id', '=', parent_id)], limit=1)
        if existing:
            return existing
        for xmlid in old_xmlids:
            try:
                old = env.ref(xmlid)
            except ValueError:
                old = None
            if old and old.exists():
                old.unlink()
        return Menu.create({
            'name': name, 'parent_id': parent_id,
            'action': action_ref, 'sequence': seq,
        })

    _rename(143, 'Kundenverwaltung')
    _rename(144, 'Pipeline')
    Menu.browse(143).write({'sequence': 25})
    Menu.browse(144).write({'parent_id': 143, 'sequence': 1})
    _rename(148, 'Kunden')
    Menu.browse(148).write({'parent_id': 143, 'sequence': 5})
    _rename(150, 'Berichtswesen')
    Menu.browse(150).write({'sequence': 20})
    _rename(155, 'Konfiguration')
    Menu.browse(155).write({'sequence': 25})

    _ensure_menu(
        'Aktivitäten', 143,
        'ir.actions.act_window,%d' % env.ref('itk_crm.action_aktivitaeten').id,
        0, old_xmlids=('crm.crm_lead_menu_my_activities',),
    )
    _ensure_menu(
        'Pipeline', 144,
        'ir.actions.server,%d' % env.ref('crm.action_your_pipeline').id,
        1, old_xmlids=('crm.menu_crm_opportunities',),
    )
    _ensure_menu(
        'Interessenten', 144,
        'ir.actions.act_window,%d' % env.ref('itk_crm.action_interessenten').id,
        2, old_xmlids=('crm.crm_menu_leads',),
    )
    _ensure_menu(
        'Angebote', 144,
        'ir.actions.act_window,%d' % env.ref('sale.action_quotations').id,
        3, old_xmlids=('sale_crm.sale_order_menu_quotations_crm',),
    )
    _setup_neue_aktivitaet_menu(env)
    _logger.info("itk_crm: Menüstruktur Kundenverwaltung hergestellt")


def _setup_neue_aktivitaet_menu(env):
    """Menü 'Neue Aktivität' unter 'Aktivitäten' (B1, idempotent).

    Das Eltern-Menü 'Aktivitäten' wird hier per Action-Suche gefunden (nicht
    per fester ID), weil setup_runtime es per Delete+Recreate verwaltet und
    seine ID nach einem Restore nicht stabil ist. Das Kind-Menü öffnet den
    nativen Odoo-18-Wizard mail.activity.schedule (itk_crm.action_neue_aktivitaet).
    """
    Menu = env['ir.ui.menu'].sudo()
    Action = env['ir.actions.act_window'].sudo()
    parent_action = Action.search([
        ('name', '=', 'Aktivitäten'),
        ('res_model', '=', 'mail.activity'),
    ], limit=1)
    if not parent_action:
        _logger.warning("itk_crm: Aktivitäten-Action nicht gefunden — 'Neue Aktivität'-Menü uebersprungen")
        return
    parent = Menu.search([
        ('action', '=', 'ir.actions.act_window,%d' % parent_action.id),
    ], limit=1)
    if not parent:
        _logger.warning("itk_crm: Aktivitäten-Menü nicht gefunden — 'Neue Aktivität'-Menü uebersprungen")
        return
    action = env.ref('itk_crm.action_neue_aktivitaet', raise_if_not_found=False)
    if not action:
        _logger.warning("itk_crm: action_neue_aktivitaet fehlt — 'Neue Aktivität'-Menü uebersprungen")
        return
    existing = Menu.search([
        ('name', '=', 'Neue Aktivität'),
        ('parent_id', '=', parent.id),
    ], limit=1)
    if existing:
        _logger.info("itk_crm: 'Neue Aktivität'-Menü existiert bereits (id=%s)", existing.id)
        return
    Menu.create({
        'name': 'Neue Aktivität',
        'parent_id': parent.id,
        'action': 'ir.actions.act_window,%d' % action.id,
        'sequence': 99,
    })
    _logger.info("itk_crm: 'Neue Aktivität'-Menü unter Aktivitäten angelegt")


def _setup_lost_reasons(env):
    """Ensure Odoo-11-compatible Lost Reasons exist (idempotent)."""
    LostReason = env['crm.lost.reason']

    # ID 2: "We don't have people/skills" → "Im Moment keinen Bedarf"
    existing = LostReason.with_context(lang='en_US').search(
        [('name', '=', "We don't have people/skills")], limit=1)
    if existing:
        existing.write({'name': 'Im Moment keinen Bedarf'})
        _logger.info("itk_crm: Lost Reason 'Im Moment keinen Bedarf' renamed")
    else:
        _logger.info("itk_crm: Lost Reason 'We don't have people/skills' not found — may already be renamed")

    for name in ('Bedarf zu gering', 'Später kontaktieren', 'Mitbewerb'):
        if not LostReason.search([('name', '=', name)]):
            LostReason.create({'name': name})
            _logger.info("itk_crm: Created Lost Reason '%s'", name)


def _setup_automated_action(env):
    """Create the automated action 'Zur Verrechnung bereit' for CRM leads."""
    _logger.info("itk_crm: Setting up automated action...")

    Stage = env['crm.stage']
    stage = Stage.with_context(lang='en_US').search(
        [('name', '=', 'Zur Verrechnung bereit')], limit=1)
    if not stage:
        _logger.warning("itk_crm: Stage 'Zur Verrechnung bereit' not found — skipping automation")
        return

    Automation = env['base.automation']
    if Automation.search([
        ('name', '=', "Interessent 'zur Verrechnung bereit'"),
        ('model_id.model', '=', 'crm.lead'),
    ], limit=1):
        _logger.info("itk_crm: Automated action already exists — skipping.")
        return

    lead_model = env['ir.model'].search([('model', '=', 'crm.lead')], limit=1)
    if not lead_model:
        _logger.error("itk_crm: crm.lead model not found in ir.model!")
        return

    ServerAction = env['ir.actions.server']
    server_action = ServerAction.create({
        'name': "Interessent 'zur Verrechnung bereit' — Benachrichtigung",
        'model_id': lead_model.id,
        'state': 'code',
        'code': (
            "# Notify followers that the lead is ready for invoicing\n"
            "record.message_post(\n"
            "    body='Der Interessent wurde auf »Zur Verrechnung bereit« gesetzt.',\n"
            "    subtype_xmlid='mail.mt_comment',\n"
            ")\n"
        ),
        'usage': 'base_automation',
        'binding_model_id': lead_model.id,
    })
    Automation.create({
        'name': "Interessent 'zur Verrechnung bereit'",
        'model_id': lead_model.id,
        'trigger': 'on_write',
        'filter_pre_domain': f"[['stage_id', '=', {stage.id}]]",
        'action_server_ids': [(6, 0, [server_action.id])],
        'on_change_field_ids': [(6, 0, [])],
        'active': True,
    })
    _logger.info("itk_crm: Created base.automation for lead → Zur Verrechnung bereit (stage_id=%s)", stage.id)


def _setup_activity_kanban(env):
    """Ensure the Aktivitäten-Action exists (idempotent)."""
    Action = env['ir.actions.act_window']
    existing = Action.search([
        ('name', '=', 'Aktivitäten'),
        ('res_model', '=', 'mail.activity'),
    ], limit=1)
    vals = {
        'view_mode': 'kanban,list,calendar,form',
        'context': "{'group_by': 'activity_type_id'}",
        'help': 'Übersicht aller geplanten Aktivitäten (Anrufe, E-Mails, Meetings, To-dos)',
    }
    if existing:
        existing.write(vals)
        _logger.info("itk_crm: Updated Aktivitäten action (id=%s)", existing.id)
    else:
        action = Action.create(dict(vals, name='Aktivitäten', res_model='mail.activity'))
        _logger.info("itk_crm: Created Aktivitäten action (id=%s)", action.id)


def _setup_vertriebskanaele_labels(env):
    """Fix German labels: 'Sales Teams' → 'Vertriebskanäle' (idempotent)."""
    _logger.info("itk_crm: Setting up Vertriebskanäle German labels...")
    Menu = env['ir.ui.menu'].sudo()
    Action = env['ir.actions.act_window'].sudo()

    menu = Menu.browse(158)
    if menu.exists():
        menu.with_context(lang='de_DE').write({'name': 'Vertriebskanäle'})
        _logger.info("itk_crm: Menu 158 DE label → 'Vertriebskanäle'")

    action = Action.browse(186)
    if action.exists():
        action.with_context(lang='de_DE').write({'name': 'Vertriebskanäle'})
        _logger.info("itk_crm: Action 186 DE label → 'Vertriebskanäle'")


# ---------------------------------------------------------------------------
# Aktivitaetstypen: RPC-Duplikate bereinigen + de_DE-Slots sicherstellen (C)
# ---------------------------------------------------------------------------
# Kanonische Typen (XML-ID im Modul) -> Namen, an denen RPC-Duplikate erkannt werden.
# Entscheidung Anna 14.08.2026: Odoo-Standard mail.mail_activity_data_call
# (Typ 2) ist KANONISCH fuer Telefon-Aktivitaeten; sein de_DE-Name wird auf
# 'Anrufen' gesetzt (passt zur Kundenverwaltung). Der itk_crm-Nachbau
# mail_activity_type_anrufen (Typ 21) wurde entfernt — Record aus der XML
# geloescht; nach Restore aus Altdumps entfernt ihn die Legacy-Bereinigung
# unten (Referenzen -> Typ 2). delay_count und alle Standardwerte von Typ 2
# bleiben unangetastet.
_ACTIVITY_TYPE_CANONICALS = [
    # (XML-ID des kanonischen Typs, [Duplikat-Namen en_US])
    ('mail.mail_activity_data_call', ['Anrufen', 'Call']),
    ('mail.mail_activity_data_email', ['E-Mail', 'Email']),
    ('mail.mail_activity_data_todo', ['Zu erledigen', 'To-Do', 'To-do']),
]


def _setup_activity_types(env):
    """Aktivitaetstypen bereinigen (idempotent, C).

    1. RPC-Duplikate (keine XML-ID, gleicher Name) auf den kanonischen Typ
       zusammenfuehren: Referenzen umhaengen, dann loeschen.
    2. Fehlende de_DE-Slots fuer die kanonischen Typen ergaenzen (jsonb),
       damit die deutsche Anzeige nie auf den en_US-Slot zurueckfaellt.
    """
    _logger.info("itk_crm: Aktivitaetstypen-Setup (Duplikat-Bereinigung + de_DE-Slots)...")
    ActivityType = env['mail.activity.type']

    def _find_dup(canonical, dup_names):
        """RPC-Duplikat finden: gleicher Name, aber KEINE XML-ID (ir_model_data)."""
        for name in dup_names:
            candidates = ActivityType.with_context(lang='en_US').search(
                [('name', '=', name)])
            for cand in candidates:
                if cand.id == canonical.id:
                    continue
                # Nur bereinigen, wenn der Kandidat wirklich RPC-angelegt ist
                # (kein ir_model_data-Eintrag -> kein Modul besitzt ihn).
                xmlid = env['ir.model.data'].search([
                    ('model', '=', 'mail.activity.type'),
                    ('res_id', '=', cand.id),
                ], limit=1)
                if not xmlid:
                    return cand
        return False

    # Referenz-Spalten (FK auf mail.activity.type), die umgehaengt werden muessen
    _FK_COLUMNS = [
        ('mail_activity', 'activity_type_id'),
        ('mail_activity', 'previous_activity_type_id'),
        ('mail_activity', 'recommended_activity_type_id'),
        ('mail_activity_plan_template', 'activity_type_id'),
        ('ir_act_server', 'activity_type_id'),
        ('mail_compose_message', 'mail_activity_type_id'),
        ('mail_message', 'mail_activity_type_id'),
        ('mail_activity_type_mail_template_rel', 'mail_activity_type_id'),
        ('mail_activity_type', 'triggered_next_type_id'),
    ]

    def _repoint_refs(cr, dup_id, canonical_id):
        """Alle Referenzen von dup auf canonical umhaengen; Anzahl loggen."""
        moved = 0
        for table, column in _FK_COLUMNS:
            cr.execute(
                'SELECT count(*) FROM "%s" WHERE "%s" = %%s' % (table, column),
                (dup_id,))
            cnt = cr.fetchone()[0]
            if cnt:
                cr.execute(
                    'UPDATE "%s" SET "%s" = %%s WHERE "%s" = %%s' % (table, column, column),
                    (canonical_id, dup_id))
                moved += cnt
                _logger.info("itk_crm:   %s.%s: %s Referenz(en) umgehaengt %s -> %s",
                             table, column, cnt, dup_id, canonical_id)
        return moved

    def _name_dict(record):
        """jsonb-Dict von mail.activity.type.name lesen (robust in jedem Kontext).

        record.name liefert OHNE Sprachkontext (Migration, Shell) einen String
        (en_US-Slot) statt des jsonb-Dicts — daher per SQL lesen.
        """
        env.cr.execute(
            "SELECT name FROM mail_activity_type WHERE id=%s", (record.id,))
        row = env.cr.fetchone()
        return row[0] if row and isinstance(row[0], dict) else {}

    for xmlid, dup_names in _ACTIVITY_TYPE_CANONICALS:
        canonical = env.ref(xmlid, raise_if_not_found=False)
        if not canonical or not canonical.exists():
            _logger.warning("itk_crm: kanonischer Typ %s nicht gefunden — uebersprungen", xmlid)
            continue
        dup = _find_dup(canonical, dup_names)
        if dup:
            moved = _repoint_refs(env.cr, dup.id, canonical.id)
            env['mail.activity.type'].browse(dup.id).unlink()
            _logger.info("itk_crm: RPC-Duplikat %s (%s) entfernt, %s Referenzen umgehaengt",
                         dup.id, dup_names, moved)
        else:
            _logger.info("itk_crm: kein RPC-Duplikat fuer %s — ok", xmlid)
        # de_DE-Slot NUR ergaenzen, wenn er fehlt (nie ueberschreiben):
        # name ist jsonb {lang: value}; existiert 'de_DE' bereits (z.B. die
        # deutsche Uebersetzung 'E-Mail' bei mail_activity_data_email),
        # bleibt sie unangetastet.
        name_dict = _name_dict(canonical)
        if 'de_DE' not in name_dict and name_dict.get('en_US'):
            canonical.write({'name': dict(name_dict, de_DE=name_dict['en_US'])})
            _logger.info("itk_crm: de_DE-Slot fuer %s ergaenzt: %s",
                         xmlid, name_dict['en_US'])
        else:
            _logger.info("itk_crm: de_DE-Slot fuer %s bereits vorhanden: %s",
                         xmlid, name_dict.get('de_DE'))

    # Generische Nachsorge: ALLE Aktivitaetstypen ohne de_DE-Slot ergaenzen
    # (deckt die weiteren itk_crm-XML-Typen 22/23 und kuenftige Faelle ab).
    for activity_type in ActivityType.search([]):
        name_dict = _name_dict(activity_type)
        if 'de_DE' not in name_dict and name_dict.get('en_US'):
            activity_type.write({'name': dict(name_dict, de_DE=name_dict['en_US'])})
            _logger.info("itk_crm: de_DE-Slot fuer Typ %s ergaenzt: %s",
                         activity_type.id, name_dict['en_US'])

    # --- Legacy-Bereinigung: itk_crm.mail_activity_type_anrufen (Typ 21) ---
    # Entscheidung Anna 14.08.2026: Odoo-Standard mail.mail_activity_data_call
    # (Typ 2) ist kanonisch; der O11-Nachbau 'Anrufen' (Typ 21) entfaellt.
    # Nach einem Restore aus einem Altdump koennte Typ 21 inkl. XML-ID wieder
    # existieren -> hier gezielt entfernen (Referenzen auf Typ 2 umhaengen,
    # ir_model_data-Eintrag mitloeschen, dann unlink).
    legacy_anrufen = env.ref('itk_crm.mail_activity_type_anrufen',
                             raise_if_not_found=False)
    call_type = env.ref('mail.mail_activity_data_call', raise_if_not_found=False)
    if legacy_anrufen and legacy_anrufen.exists():
        if call_type and call_type.exists():
            moved = _repoint_refs(env.cr, legacy_anrufen.id, call_type.id)
            env.cr.execute(
                "DELETE FROM ir_model_data WHERE model='mail.activity.type' "
                "AND module='itk_crm' AND name='mail_activity_type_anrufen'")
            legacy_anrufen.unlink()
            _logger.info(
                "itk_crm: Legacy-Typ %s (mail_activity_type_anrufen) entfernt, "
                "%s Referenzen -> Typ %s", legacy_anrufen.id, moved, call_type.id)
        else:
            _logger.warning(
                "itk_crm: Legacy-Typ %s vorhanden, aber kanonischer Typ "
                "mail.mail_activity_data_call fehlt — nicht entfernt",
                legacy_anrufen.id)

    # --- Kanonischer Name von Typ 2: de_DE -> 'Anrufen' ---
    # Entscheidung Anna 14.08.2026: NUR der de_DE-Slot von
    # mail.mail_activity_data_call wird auf 'Anrufen' gesetzt (passt zur
    # Kundenverwaltung). en_US 'Call', delay_count=2 und alle uebrigen
    # Standardwerte bleiben unangetastet. Idempotent: schreibt nur, wenn de_DE
    # noch nicht 'Anrufen' ist.
    if call_type and call_type.exists():
        call_dict = _name_dict(call_type)
        if call_dict.get('de_DE') != 'Anrufen':
            call_type.write({'name': dict(call_dict, de_DE='Anrufen')})
            _logger.info("itk_crm: de_DE-Name Typ %s -> 'Anrufen'", call_type.id)
        else:
            _logger.info("itk_crm: de_DE-Name Typ %s bereits 'Anrufen' — ok",
                         call_type.id)

    _logger.info("itk_crm: Aktivitaetstypen-Setup abgeschlossen")
