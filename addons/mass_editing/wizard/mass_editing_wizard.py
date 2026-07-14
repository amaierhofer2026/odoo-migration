from lxml import etree

import odoo.tools as tools
from odoo import api, fields, models


class MassEditingWizard(models.TransientModel):
    _name = 'mass.editing.wizard'

    mass_editing_object_id = fields.Many2one(
        'mass.object', 'Mass Editing Template',
        default=lambda self: self.env.context.get('mass_editing_object'))

    # Fixed generic fields — labels/types overridden via get_view + fields_get
    select_1 = fields.Selection([], string='Op 1')
    value_1 = fields.Char(string='Val 1')
    select_2 = fields.Selection([], string='Op 2')
    value_2 = fields.Char(string='Val 2')
    select_3 = fields.Selection([], string='Op 3')
    value_3 = fields.Char(string='Val 3')

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        result = super().get_view(view_id=view_id, view_type=view_type, **options)
        mass_obj_id = self.env.context.get('mass_editing_object')
        if not mass_obj_id:
            mass_obj_id = int(self.env['ir.config_parameter'].sudo().get_param(
                'mass_editing_last_id', '0'))
        if not mass_obj_id:
            return result

        mass_obj = self.env['mass.object'].browse([mass_obj_id])
        model_obj = self.env[mass_obj.model_id.model]
        field_info = model_obj.fields_get()
        fields_out = {}
        xml_form = etree.Element('form', {'string': tools.ustr(mass_obj.name)})
        xml_form.append(etree.Element('sheet'))
        xml_group = etree.SubElement(xml_form[0], 'group', {'colspan': '2'})

        for i, fld in enumerate(mass_obj.field_ids[:3]):
            idx = i + 1
            sel_name = 'select_%d' % idx
            val_name = 'value_%d' % idx

            if fld.ttype == 'many2many':
                fields_out[sel_name] = {
                    'type': 'selection', 'string': field_info[fld.name]['string'],
                    'selection': [('set', 'Set'), ('remove_m2m', 'Remove'), ('add', 'Add')],
                }
                fields_out[val_name] = {
                    'type': 'many2many', 'string': fld.field_description,
                    'relation': fld.relation,
                }
                sep = etree.SubElement(xml_group, 'separator', {
                    'string': field_info[fld.name]['string'], 'colspan': '2',
                })
                etree.SubElement(xml_group, 'field', {
                    'name': sel_name, 'nolabel': '1',
                })
                etree.SubElement(xml_group, 'field', {
                    'name': val_name, 'nolabel': '1',
                    'invisible': "%s == 'remove_m2m'" % sel_name,
                })
            elif fld.ttype in ('one2many', 'many2one'):
                fields_out[sel_name] = {
                    'type': 'selection', 'string': field_info[fld.name]['string'],
                    'selection': [('set', 'Set'), ('remove', 'Remove')],
                }
                fields_out[val_name] = {
                    'type': 'many2one', 'string': fld.field_description,
                    'relation': fld.relation,
                }
                etree.SubElement(xml_group, 'field', {'name': sel_name})
                etree.SubElement(xml_group, 'field', {
                    'name': val_name, 'nolabel': '1',
                    'invisible': "%s == 'remove'" % sel_name,
                })
            else:
                fields_out[sel_name] = {
                    'type': 'selection', 'string': field_info[fld.name]['string'],
                    'selection': [('set', 'Set'), ('remove', 'Remove')],
                }
                if fld.ttype == 'selection':
                    fields_out[val_name] = {
                        'type': 'selection', 'string': fld.field_description,
                        'selection': field_info[fld.name]['selection'],
                    }
                elif fld.ttype == 'text':
                    fields_out[val_name] = {
                        'type': 'text', 'string': fld.field_description,
                    }
                else:
                    fields_out[val_name] = {
                        'type': fld.ttype, 'string': fld.field_description,
                    }
                etree.SubElement(xml_group, 'field', {'name': sel_name})
                etree.SubElement(xml_group, 'field', {
                    'name': val_name, 'nolabel': '1',
                    'invisible': "%s == 'remove'" % sel_name,
                })

        for f in fields_out.values():
            f.setdefault("views", {})

        xml_footer = etree.SubElement(xml_form[0], 'footer', {})
        etree.SubElement(xml_footer, 'button', {
            'string': 'Apply', 'class': 'btn-primary',
            'type': 'object', 'name': 'action_apply',
        })
        etree.SubElement(xml_footer, 'button', {
            'string': 'Close', 'class': 'btn-default', 'special': 'cancel',
        })

        result['arch'] = etree.tostring(xml_form.getroottree())
        result['fields'] = fields_out
        return result

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields=allfields, attributes=attributes)
        mass_obj_id = self.env.context.get('mass_editing_object')
        if not mass_obj_id:
            mass_obj_id = int(self.env['ir.config_parameter'].sudo().get_param(
                'mass_editing_last_id', '0'))
        if not mass_obj_id:
            return res

        mass_obj = self.env['mass.object'].browse([mass_obj_id])
        model_obj = self.env[mass_obj.model_id.model]
        field_info = model_obj.fields_get()

        for i, fld in enumerate(mass_obj.field_ids[:3]):
            idx = i + 1
            sel_name = 'select_%d' % idx
            val_name = 'value_%d' % idx

            if fld.ttype == 'many2many':
                res[sel_name] = {
                    'type': 'selection', 'string': field_info[fld.name]['string'],
                    'selection': [('set', 'Set'), ('remove_m2m', 'Remove'), ('add', 'Add')],
                }
                res[val_name] = {
                    'type': 'many2many', 'string': fld.field_description,
                    'relation': fld.relation,
                }
            elif fld.ttype in ('one2many', 'many2one'):
                res[sel_name] = {
                    'type': 'selection', 'string': field_info[fld.name]['string'],
                    'selection': [('set', 'Set'), ('remove', 'Remove')],
                }
                res[val_name] = {
                    'type': 'many2one', 'string': fld.field_description,
                    'relation': fld.relation,
                }
            else:
                res[sel_name] = {
                    'type': 'selection', 'string': field_info[fld.name]['string'],
                    'selection': [('set', 'Set'), ('remove', 'Remove')],
                }
                if fld.ttype == 'selection':
                    res[val_name] = {
                        'type': 'selection', 'string': fld.field_description,
                        'selection': field_info[fld.name]['selection'],
                    }
                elif fld.ttype == 'text':
                    res[val_name] = {'type': 'text', 'string': fld.field_description}
                else:
                    res[val_name] = {'type': fld.ttype, 'string': fld.field_description}
        return res

    @api.model
    def create(self, vals):
        if (self.env.context.get('active_model') and self.env.context.get('active_ids')):
            model_obj = self.env[self.env.context.get('active_model')]
            mass_obj_id = self.env.context.get('mass_editing_object')
            if not mass_obj_id:
                mass_obj_id = int(self.env['ir.config_parameter'].sudo().get_param(
                    'mass_editing_last_id', '0'))
            mass_obj = self.env['mass.object'].browse([mass_obj_id])

            values = {}
            for i, fld in enumerate(mass_obj.field_ids[:3]):
                idx = i + 1
                sel_key = 'select_%d' % idx
                val_key = 'value_%d' % idx
                sel_val = vals.get(sel_key)
                val_val = vals.get(val_key)

                if not sel_val:
                    continue

                if sel_val == 'set':
                    values[fld.name] = val_val
                elif sel_val == 'remove':
                    values[fld.name] = False
                elif sel_val == 'remove_m2m':
                    if val_val and isinstance(val_val, list):
                        values[fld.name] = [(3, mid) for mid in val_val]
                    else:
                        values[fld.name] = [(5, 0, [])]
                elif sel_val == 'add':
                    if val_val and isinstance(val_val, list):
                        values[fld.name] = [(4, mid) for mid in val_val]

            if values:
                model_obj.browse(self.env.context.get('active_ids')).write(values)
        return super().create({})

    def action_apply(self):
        return {'type': 'ir.actions.act_window_close'}
