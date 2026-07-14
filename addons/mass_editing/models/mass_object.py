# © 2016 Serpent Consulting Services Pvt. Ltd. (support@serpentcs.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class MassObject(models.Model):
    _name = "mass.object"
    _description = "Mass Editing Object"

    name = fields.Char('Name', required=True, index=1)
    model_id = fields.Many2one('ir.model', 'Model', required=True,
                               ondelete="cascade",
                               help="Model is used for Selecting Fields. "
                                    "This is editable until Sidebar menu "
                                    "is not created.")
    field_ids = fields.Many2many('ir.model.fields', 'mass_field_rel',
                                 'mass_id', 'field_id', 'Fields')
    ref_ir_act_window_id = fields.Many2one('ir.actions.act_window',
                                           'Sidebar action',
                                           readonly=True,
                                           help="Sidebar action to make this "
                                                "template available on "
                                                "records of the related "
                                                "document model.")
    model_list = fields.Char('Model List')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Name must be unique!'),
    ]

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.field_ids = [(6, 0, [])]
        model_list = []
        if self.model_id:
            model_obj = self.env['ir.model']
            model_list = [self.model_id.id]
            active_model_obj = self.env[self.model_id.model]
            if active_model_obj._inherits:
                keys = list(active_model_obj._inherits.keys())
                inherits_model_list = model_obj.search([('model', 'in', keys)])
                model_list.extend((inherits_model_list and
                                   inherits_model_list.ids or []))
        self.model_list = model_list

    def create_action(self):
        self.ensure_one()
        action_obj = self.env['ir.actions.act_window']
        server_obj = self.env['ir.actions.server']
        src_obj = self.model_id.model
        button_name = _('Mass Editing (%s)') % self.name

        # Create window action (the actual wizard opener, no binding)
        window_action_id = action_obj.create({
            'name': button_name,
            'type': 'ir.actions.act_window',
            'res_model': 'mass.editing.wizard',
            'context': "{'mass_editing_object' : %d}" % (self.id),
            'view_mode': 'form',
            'target': 'new',
        }).id

        # Create server action that binds to the model (Odoo 18 requires
        # ir.actions.server for dynamically created actions to appear in UI)
        server_action_id = server_obj.create({
            'name': button_name,
            'model_id': self.model_id.id,
            'binding_model_id': self.model_id.id,
            'binding_type': 'action',
            'binding_view_types': 'list',
            'state': 'code',
            'code': (
                "action = env['ir.actions.act_window'].browse(%d).read()[0]\n"
                "action['context'] = {\n"
                "    'mass_editing_object': %d,\n"
                "    'active_model': context.get('active_model'),\n"
                "    'active_ids': context.get('active_ids'),\n"
                "}\n"
            ) % (window_action_id, self.id),
        }).id

        # Register both in ir.model.data
        self.env['ir.model.data'].create({
            'module': 'mass_editing',
            'name': 'action_window_mass_editing_%d' % self.id,
            'model': 'ir.actions.act_window',
            'res_id': window_action_id,
            'noupdate': True,
        })
        self.env['ir.model.data'].create({
            'module': 'mass_editing',
            'name': 'action_server_mass_editing_%d' % self.id,
            'model': 'ir.actions.server',
            'res_id': server_action_id,
            'noupdate': True,
        })

        # Store the window action ID (used by unlink_action)
        self.write({'ref_ir_act_window_id': window_action_id})
        # Also need to track the server action for cleanup
        self.env['ir.model.data'].create({
            'module': 'mass_editing',
            'name': 'action_server_ref_%d' % self.id,
            'model': 'ir.actions.server',
            'res_id': server_action_id,
            'noupdate': True,
        })
        return True

    def unlink_action(self):
        self.mapped('ref_ir_act_window_id').unlink()
        return True

    def unlink(self):
        self.unlink_action()
        return super(MassObject, self).unlink()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if default is None:
            default = {}
        default.update({'name': _("%s (copy)" % self.name), 'field_ids': []})
        return super(MassObject, self).copy(default)
