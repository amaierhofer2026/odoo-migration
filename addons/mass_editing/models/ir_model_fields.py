# © 2016 Serpent Consulting Services Pvt. Ltd. (support@serpentcs.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    mass_editing_domain = fields.Char(
        string='Mass Editing Domain',
    )

    @api.model
    def search(self, args, offset=0, limit=None, order=None, **kwargs):
        # Odoo 18 removed 'count' from search() but some internal callers
        # still pass it. Accept **kwargs to avoid TypeError.
        model_domain = []
        for domain in args:
            if (len(domain) > 2 and domain[0] == 'mass_editing_domain' and
                    isinstance(domain[2], str) and
                    list(domain[2][1:-1])):
                model_domain += [('model_id', 'in',
                                  list(map(int, domain[2][1:-1].split(','))))]
            else:
                model_domain.append(domain)
        return super(IrModelFields, self).search(model_domain, offset=offset,
                                                 limit=limit, order=order)
