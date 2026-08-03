"""Post-install hooks for itk_crm — sets up automated actions and runtime data."""
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Create the automated action 'Zur Verrechnung bereit' for CRM leads."""
    _logger.info("itk_crm post_init_hook: Setting up automated action...")

    # Find the "Zur Verrechnung bereit" stage
    Stage = env['crm.stage']
    stage = Stage.search([('name', '=', 'Zur Verrechnung bereit')], limit=1)
    if not stage:
        _logger.warning(
            "itk_crm: Stage 'Zur Verrechnung bereit' not found — "
            "skipping automated action creation. "
            "Run the CRM setup JSON-RPC script first."
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

    # Create the server action (ir.actions.server)
    ServerAction = env['ir.actions.server']
    server_action = ServerAction.create({
        'name': "Interessent 'zur Verrechnung bereit' — Benachrichtigung",
        'model_id': env.ref('crm.model_crm_lead').id,
        'state': 'code',
        'code': (
            "# Notify followers that the lead is ready for invoicing\n"
            "record.message_post(\n"
            "    body='Der Interessent wurde auf »Zur Verrechnung bereit« gesetzt.',\n"
            "    subtype_xmlid='mail.mt_comment',\n"
            ")\n"
        ),
        'usage': 'base_automation',
        'binding_model_id': env.ref('crm.model_crm_lead').id,
    })
    _logger.info("itk_crm: Created server action (id=%s)", server_action.id)

    # Create the automated action (base.automation)
    Automation.create({
        'name': "Interessent 'zur Verrechnung bereit'",
        'model_id': env.ref('crm.model_crm_lead').id,
        'trigger': 'on_write',
        'filter_pre_domain': "[['stage_id', '=', {}]]".format(stage.id),
        'action_server_id': server_action.id,
        'active': True,
    })
    _logger.info(
        "itk_crm: Created base.automation for lead → Zur Verrechnung bereit (stage_id=%s)",
        stage.id,
    )
