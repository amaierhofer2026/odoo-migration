from odoo import models, api, _
from odoo.exceptions import UserError


class ResPartnerMultifactorUpdate(models.TransientModel):
    """
    This wizard will update the Multifactor from EWZ in all the selected contacts
    """

    _name = "res.partner.multifactor.update.confirm"
    _description = "Update the selected Partners for the Multifactor from EWZ"

    @api.multi
    def partner_update_population_and_multifactor(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['res.partner'].browse(active_ids):
            if record.is_company == False:
                raise UserError(_("Selected entry(ies) cannot be updated as they are no companies."))
            record._compute_populationthousandsfactor()
            record._compute_communitymagnitude()

        return {'type': 'ir.actions.act_window_close'}