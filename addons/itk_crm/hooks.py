"""Post-install hooks for itk_crm — sets up automated actions, lost reasons, and other runtime data."""
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Create runtime data: lost reasons, automated action, activity kanban action."""
    _logger.info("itk_crm post_init_hook: Setting up runtime data...")

    _setup_lost_reasons(env)
    _setup_automated_action(env)
    _setup_activity_kanban(env)


def _setup_lost_reasons(env):
    """Ensure Odoo-11-compatible Lost Reasons exist (idempotent).

    Odoo-18 crm.lost.reason hat KEIN sequence-Feld — nur name + active.
    """
    LostReason = env['crm.lost.reason']

    # ID 2: "We don't have people/skills" → "Im Moment keinen Bedarf"
    existing = LostReason.search([('name', '=', "We don't have people/skills")], limit=1)
    if existing:
        existing.write({'name': 'Im Moment keinen Bedarf'})
        _logger.info("itk_crm: Lost Reason 'Im Moment keinen Bedarf' renamed (was: We don't have...)")
    else:
        _logger.info("itk_crm: Lost Reason 'We don't have people/skills' not found — may already be renamed")

    # ID 4: "Bedarf zu gering" (NEW)
    if not LostReason.search([('name', '=', 'Bedarf zu gering')]):
        LostReason.create({'name': 'Bedarf zu gering'})
        _logger.info("itk_crm: Created Lost Reason 'Bedarf zu gering'")

    # ID 5: "Später kontaktieren" (NEW)
    if not LostReason.search([('name', '=', 'Später kontaktieren')]):
        LostReason.create({'name': 'Später kontaktieren'})
        _logger.info("itk_crm: Created Lost Reason 'Später kontaktieren'")

    # ID 6: "Mitbewerb" (NEW)
    if not LostReason.search([('name', '=', 'Mitbewerb')]):
        LostReason.create({'name': 'Mitbewerb'})
        _logger.info("itk_crm: Created Lost Reason 'Mitbewerb'")


def _setup_automated_action(env):
    """Create the automated action 'Zur Verrechnung bereit' for CRM leads."""
    Stage = env['crm.stage']
    stage = Stage.search([('name', '=', 'Zur Verrechnung bereit')], limit=1)
    if not stage:
        _logger.warning(
            "itk_crm: Stage 'Zur Verrechnung bereit' not found — "
            "skipping automated action creation."
        )
        return

    _logger.info("itk_crm: Found stage 'Zur Verrechnung bereit' (id=%s)", stage.id)

    # Check if automated action already exists (idempotent)
    Automation = env['base.automation']
    existing = Automation.search([
        ('name', '=', "Interessent 'zur Verrechnung bereit'"),
        ('model_id.model', '=', 'crm.lead'),
    ], limit=1)
    if existing:
        _logger.info("itk_crm: Automated action already exists — skipping.")
        return

    # Find crm.lead model ref
    lead_model = env['ir.model'].search([('model', '=', 'crm.lead')], limit=1)
    if not lead_model:
        _logger.error("itk_crm: crm.lead model not found in ir.model!")
        return

    # Create the server action (ir.actions.server)
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
    _logger.info("itk_crm: Created server action (id=%s)", server_action.id)

    # Create the automated action (base.automation)
    # NOTE: Odoo 18 uses action_server_ids (one2many), not action_server_id (many2one)
    Automation.create({
        'name': "Interessent 'zur Verrechnung bereit'",
        'model_id': lead_model.id,
        'trigger': 'on_write',
        'filter_pre_domain': f"[['stage_id', '=', {stage.id}]]",
        'action_server_ids': [(6, 0, [server_action.id])],
        'on_change_field_ids': [(6, 0, [])],  # Trigger on any field change
        'active': True,
    })
    _logger.info(
        "itk_crm: Created base.automation for lead → Zur Verrechnung bereit (stage_id=%s)",
        stage.id,
    )


def _setup_activity_kanban(env):
    """Ensure the Aktivitäten-Action exists (idempotent)."""
    Action = env['ir.actions.act_window']
    existing = Action.search([
        ('name', '=', 'Aktivitäten'),
        ('res_model', '=', 'mail.activity'),
    ], limit=1)

    if existing:
        existing.write({
            'view_mode': 'kanban,list,calendar,form',
            'context': "{'group_by': 'activity_type_id'}",
            'help': 'Übersicht aller geplanten Aktivitäten (Anrufe, E-Mails, Meetings, To-dos)',
        })
        _logger.info("itk_crm: Updated Aktivitäten action (id=%s)", existing.id)
    else:
        action = Action.create({
            'name': 'Aktivitäten',
            'res_model': 'mail.activity',
            'view_mode': 'kanban,list,calendar,form',
            'context': "{'group_by': 'activity_type_id'}",
            'help': 'Übersicht aller geplanten Aktivitäten (Anrufe, E-Mails, Meetings, To-dos)',
        })
        _logger.info("itk_crm: Created Aktivitäten action (id=%s)", action.id)
