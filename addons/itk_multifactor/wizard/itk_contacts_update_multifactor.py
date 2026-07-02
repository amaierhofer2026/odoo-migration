from odoo import models, _
from odoo.exceptions import UserError


class ResPartnerMultifactorUpdate(models.TransientModel):
    _name = "res.partner.multifactor.update.confirm"
    _description = "Update the selected Partners for the Multifactor from EWZ"

    def partner_update_population_and_multifactor(self):
        active_ids = self.env.context.get('active_ids', [])
        for record in self.env['res.partner'].browse(active_ids):
            if not record.is_company:
                raise UserError(_("Selected entry(ies) cannot be updated as they are no companies."))
            record._compute_populationthousandsfactor()
            if hasattr(record, '_compute_communitymagnitude'):
                record._compute_communitymagnitude()
        return {'type': 'ir.actions.act_window_close'}
