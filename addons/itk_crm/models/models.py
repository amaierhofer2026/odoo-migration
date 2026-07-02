from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    firstname = fields.Char("First name", index=True)
    status_of_community = fields.Many2one('itk_crm.statusofcommunity', string='Status of Community')
    status_of_partner_id = fields.Many2one('itk_crm.statusofpartner', string='Status of Partner')
    population = fields.Integer('Size of Population')
    population_update = fields.Date('Population Update')
    member_of_city_alliance = fields.Boolean('Member of City Alliance')
    asset_partner = fields.Boolean('Asset Partner')
    attention_of = fields.Char("For the Attention of")
    salutation = fields.Char("Salutation")
    title_put_in_front = fields.Char(string='Title in Front')
    title_put_in_back = fields.Char(string='Title in Back')
    sales_as_final_customer_count = fields.Integer(
        compute='_sales_as_final_customer_count',
        string='# of Sales as Final Customer',
    )
    community_magnitude_id = fields.Many2one(
        'itk_crm.communitymagnitude',
        string='Community Magnitude',
        compute='_compute_communitymagnitude',
        store=True,
    )
    community_magnitude = fields.Char("Magnitude", compute='_compute_communitymagnitude')
    community_salutation = fields.Char("Salutation of Community")
    official_email = fields.Char("Official Email")
    austria_wiki_url = fields.Char("Austria Wiki URL")
    latitude = fields.Char("Latitude")
    longitude = fields.Char("Longitude")
    type = fields.Selection(selection_add=[('administrative', 'Administration'), ('technical', 'Technik')])
    reseller = fields.Boolean('Reseller')

    _sql_constraints = [('ref_unique', 'UNIQUE (ref)', 'The internal Reference has to be unique!')]

    def action_set_address_of_contact(self):
        self.ensure_one()
        self.street = self.parent_id.street
        self.street2 = self.parent_id.street2
        self.zip = self.parent_id.zip
        self.city = self.parent_id.street
        self.state_id = self.parent_id.state_id
        self.country_id = self.parent_id.country_id

    def _compute_communitymagnitude(self):
        for rec in self:
            rec._get_community_magnitude()

    @api.onchange('population')
    def compute_communitymagnitude(self):
        self._get_community_magnitude()

    def _get_community_magnitude(self):
        self.ensure_one()
        ppltn = self.population
        mgntd = self.env['itk_crm.communitymagnitude'].search(
            [('lower_limit', '<=', ppltn), ('upper_limit', '>', ppltn)])
        self.community_magnitude = mgntd.name
        self.community_magnitude_id = mgntd

    def act_show_sales_as_final_customer(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'name': "Saleorders as Final Customer",
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [["final_customer_id", "=", self.id], ["partner_id", "!=", self.id]],
        }

    def action_set_community_display_name(self):
        self.ensure_one()
        if self.is_company:
            self.display_name = '[' + (self.ref or '') + '] ' + (self.community_salutation or '')

    @api.onchange('status_of_community', 'name')
    def status_of_community_changed(self):
        if self.is_company and self.status_of_community.name:
            self.community_salutation = self.status_of_community.name + ' ' + self.name

    @api.onchange('name', 'ref', 'community_salutation')
    def ref_changed(self):
        self.action_set_community_display_name()

    @api.onchange('salutation', 'title', 'title_put_in_front', 'title_put_in_back', 'lastname', 'firstname')
    def attention_of_changed(self):
        if self.is_company:
            self.attention_of = ''
        else:
            ttl = self.title.name or ''
            sltt = self.salutation or ''
            tpif = self.title_put_in_front or ''
            tpib = self.title_put_in_back or ''
            fn = self.firstname or ''
            ln = self.lastname or ''
            self.attention_of = sltt + ' ' + tpif + ' ' + ttl + ' ' + fn + ' ' + ln + ' ' + tpib

    def _sales_as_final_customer_count(self):
        for partner in self:
            x = self.env['sale.order'].search([
                ('partner_id', '!=', partner.id),
                ('final_customer_id', '=', partner.id),
            ])
            partner.sales_as_final_customer_count = len(x)

    @api.depends('name', 'ref', 'status_of_community', 'type')
    def name_get(self):
        result = []
        for record in self:
            if record.is_company:
                result.append((record.id, "[%s] %s" % (record.ref, record.community_salutation)))
            else:
                selectionlist = dict(self.fields_get(allfields=['type']))
                aDict = selectionlist['type']
                selection_entries_list = aDict.get('selection')
                new_dict = {}
                for entry in selection_entries_list:
                    new_dict.update({entry[0]: entry[1]})
                selection = new_dict.get(record.type, '')
                x = record.parent_id.community_salutation if record.parent_id else ''
                result.append((record.id, "%s %s - [%s] %s" % (
                    record.name, selection, record.parent_id.ref if record.parent_id else '', x)))
        return result


class CommunityMagnitude(models.Model):
    _name = 'itk_crm.communitymagnitude'
    _description = 'Community Magnitude'
    _order = "seq asc"
    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    lower_limit = fields.Integer(string="Lower Limit")
    upper_limit = fields.Integer(string="Upper Limit")
    description = fields.Char(string="Description")
    seq = fields.Integer(string="Sequence")


class TitlePutInFront(models.Model):
    _name = 'itk_crm.titleputinfront'
    _description = 'Title put in Front'
    _order = "seq asc"
    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    seq = fields.Integer(string="Sequence")


class TitlePutInBack(models.Model):
    _name = 'itk_crm.titleputinback'
    _description = 'Title put in Back'
    _order = "seq asc"
    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    seq = fields.Integer(string="Sequence")


class CommunityCode(models.Model):
    _name = 'itk_crm.communitycode'
    _description = 'Community Code'
    _order = "seq asc"
    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    seq = fields.Integer(string="Sequence")


class StatusOfCommunity(models.Model):
    _name = 'itk_crm.statusofcommunity'
    _description = 'Status of Community'
    _order = "seq asc"
    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    display_name_new = fields.Char(string="Display Name New")
    display_name = fields.Char(string="Display Name")
    seq = fields.Integer(string="Sequence")


class StatusOfPartner(models.Model):
    _name = 'itk_crm.statusofpartner'
    _description = 'Status of Partner'
    _order = "seq asc"
    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    seq = fields.Integer(string="Sequence")
