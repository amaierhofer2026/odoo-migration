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
    _logger.info("itk_crm: Menüstruktur Kundenverwaltung hergestellt")


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
