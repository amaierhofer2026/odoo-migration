# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    """Adds
        - status_of_community
        - population
        - population_update
        - member_of_city_alliance
        - status_of_community
        - population
        - population_updat
        - member_of_city_alliance
        - asset_partner
        - attention_of
        - salutation
        - title_put_in_front
        - title_put_in_back
        - sales_as_final_customer_count
        - community_magnitude_id
        - community_magnitude
        - community_salutation
        - official_email
        - austria_wiki_url
        - latitude
        - longitude

        - population_thousands_factor
        """
    _inherit = 'res.partner'

    firstname = fields.Char(
        "First name",
        index=True,
    )

    status_of_community = fields.Many2one('itk_crm.statusofcommunity', string='Status of Community')
    status_of_partner_id = fields.Many2one('itk_crm.statusofpartner', string='Status of Partner')
    population = fields.Integer('Size of Population')
    population_update = fields.Date('Population Update')
    member_of_city_alliance = fields.Boolean('Member of City Alliance')
    asset_partner = fields.Boolean('Asset Partner')
    attention_of = fields.Char("For the Attention of", )
    salutation = fields.Char("Salutation")
    # title_put_in_front = fields.Many2one('itk_crm.titleputinfront', string='Title in Front')
    title_put_in_front = fields.Char(string='Title in Front')
    # title_put_in_back = fields.Many2one('itk_crm.titleputinback', string='Title in Back')
    title_put_in_back = fields.Char(string='Title in Back')
    sales_as_final_customer_count = fields.Integer(compute='_sales_as_final_customer_count',
                                                   string='# of Sales as Final Customer')
    community_magnitude_id = fields.Many2one('itk_crm.communitymagnitude',
                                             string='Community Magnitude',
                                             compute='_compute_communitymagnitude',
                                             store=True)
    community_magnitude = fields.Char("Magnitude", compute='_compute_communitymagnitude')
    # community_salutation = fields.Char("Salutation of Community", compute='_get_salutation_for_community')
    community_salutation = fields.Char("Salutation of Community", )
    official_email = fields.Char("Official Email")
    austria_wiki_url = fields.Char("Austria Wiki URL")
    latitude = fields.Char("Latitude")
    longitude = fields.Char("Longitude")
    type = fields.Selection(selection_add=[('administrative', 'Administration'), ('technical', 'Technik')])
    reseller = fields.Boolean('Reseller')
    # population_1000s_factor = fields.Integer(string='Population Thousands Factor',
    #                                          #compute='_compute_populationthousandsfactor',
    #                                          store=True)

    _sql_constraints = [('ref_unique', 'UNIQUE (ref)', 'The internal Reference has to be unique!')]

    @api.multi
    def action_set_address_of_contact(self):
        # Action called by function call in xml-import for setting addressdata of a contact
        self.street = self.parent_id.street
        self.street2 = self.parent_id.street2
        self.zip = self.parent_id.zip
        self.city = self.parent_id.street
        self.state_id = self.parent_id.state_id
        self.country_id = self.parent_id.country_id

#==============================
    # @api.one
    # def _compute_populationthousandsfactor(self):
    #     self._get_populationthousandsfactor()
    #
    # @api.onchange('population')
    # def _compute_populationthousandsfactor(self):
    #     self._get_populationthousandsfactor()
    #
    # def _get_populationthousandsfactor(self):
    #     ppltn = self.population
    #     ptf = -(-ppltn // 1000)
    #     self.population_thousands_factor = ptf


#==============================


    @api.one
    def _compute_communitymagnitude(self):
        self._get_community_magnitude()

    @api.onchange('population')
    def compute_communitymagnitude(self):
        self._get_community_magnitude()

    def _get_community_magnitude(self):
        ppltn = self.population
        mgntd = self.env['itk_crm.communitymagnitude'].search(
            [('lower_limit', '<=', ppltn), ('upper_limit', '>', ppltn)])
        self.community_magnitude = mgntd.name

    @api.multi
    def act_show_sales_as_final_customer(self):
        self.ensure_one()
        partner_id = self.id
        domain = [["final_customer_id", "=", partner_id], ["partner_id", "!=", partner_id]]
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'name': "Saleorders as Final Customer",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': domain
        }


    # @api.multi
    # def action_set_community_salutation_and_display_name(self):  # called via function by XML-import to set community_salutation
    #     self.action_set_community_display_name()
    #     self.action_set_community_salutation()
    #     self.name_get()


    # @api.multi
    # def action_set_community_salutation(self):  # called via function by XML-import to set community_salutation
    #     if self.is_company:
    #         if self.status_of_community.name == False:
    #             x = ''
    #         else:
    #             x = self.status_of_community.name
    #         self.community_salutation = x + ' ' + self.name
    #     else:
    #         1 + 1


    @api.multi
    def action_set_community_display_name(self):  # called via function by XML-import to set community display_name
        if self.display_name == False:
                self.display_name = ''
        if self.ref == False:
                self.ref = ''
        if self.community_salutation == False:
                self.community_salutation = ''


        if self.is_company:
            if self.display_name == False:
                self.display_name = ''
            else:
                self.display_name = '[' + self.ref + '] ' + self.community_salutation
        else:
            1 + 1

    @api.onchange('status_of_community', 'name')
    def status_of_community_changed(self):
        if self.is_company:
            if self.status_of_community.name == False:
                x = ''
            else:
                x = self.status_of_community.name
                self.community_salutation = x + ' ' + self.name
        else:
            1 + 1

    @api.onchange('name', 'ref', 'community_salutation')
    def ref_changed(self):
        self.action_set_community_display_name()
        self.name_get()

    @api.onchange('salutation', 'title', 'title_put_in_front', 'title_put_in_back', 'lastname', 'firstname')
    def attention_of_changed(self):
    #     self.attention_of_get()
    #
    # def attention_of_get(self):
        if self.is_company:
            self.attention_of = ''
        else:
            1+1
            if self.title.name == False:
                ttl = ''
            else:
                ttl = self.title.name

            if self.salutation == False:
                sltt = ''
            else:
                sltt = self.salutation

            if self.title_put_in_front == False:
                t_p_i_f = ''
            else:
                t_p_i_f = self.title_put_in_front
            if self.title_put_in_back == False:
                t_p_i_b = ''
            else:
                t_p_i_b = self.title_put_in_back
            if self.firstname == False:
                fn = ''
            else:
                fn = self.firstname
            if self.lastname == False:
                ln = ''
            else:
                ln = self.lastname
            self.attention_of = sltt + ' ' + t_p_i_f + ' ' + ttl + ' ' + fn + ' ' + ln + ' ' + t_p_i_b


    def _sales_as_final_customer_count(self):
        for partner in self:
            x = self.env['sale.order'].search([('partner_id', '!=', partner.id),
                                               ('final_customer_id', '=', partner.id)])
            x_size = len(x)
            partner.sales_as_final_customer_count = x_size

    @api.depends('name', 'ref', 'status_of_community', 'type')
    def name_get(self):
        result = []
        for record in self:
            if record.is_company:
                # result.append((record.id, u"[%s] %s" % (record.ref, record.name)))

                result.append((record.id, u"[%s] %s" % (record.ref, record.community_salutation)))
            else:
                selectionlist = dict(self.fields_get(allfields=['type']))
                aDict = selectionlist['type']
                selection_entries_list = aDict.get('selection')
                new_dict = {}
                for entry in selection_entries_list:
                    key = entry[0]
                    value = entry[1]
                    new_dict.update({key: value})
                selection = new_dict.get(record.type)
                x = record.parent_id.community_salutation
                if x:
                    result.append((record.id, u"%s %s - [%s] %s" % (
                        record.name, selection, record.parent_id.ref, x)))
                else:
                    x = ''
                    result.append((record.id, u"%s - %s - [%s] %s" % (
                        record.name, selection, record.parent_id.ref, x)))
        return result


class CommunityMagnitude(models.Model):
    _name = 'itk_crm.communitymagnitude'
    _description = 'Community Magnitude'
    _order = "seq asc"
    code = fields.Char(string="Code", )
    name = fields.Char(string="Name", )
    lower_limit = fields.Integer(string="Lower Limit", required=False, )
    upper_limit = fields.Integer(string="Upper Limit", required=False, )
    description = fields.Char(string="Description", )
    seq = fields.Integer(string="Sequence", required=False, )


class TitlePutInFront(models.Model):
    _name = 'itk_crm.titleputinfront'
    _description = 'Title put in Front'
    _order = "seq asc"
    code = fields.Char(string="Code", )
    name = fields.Char(string="Name", )
    seq = fields.Integer(string="Sequence", required=False, )


class TitlePutInBack(models.Model):
    _name = 'itk_crm.titleputinback'
    _description = 'Title put in Back'
    _order = "seq asc"
    code = fields.Char(string="Code", )
    name = fields.Char(string="Name", )
    seq = fields.Integer(string="Sequence", required=False, )


class CommunityCode(models.Model):
    _name = 'itk_crm.communitycode'
    _description = 'Community Code'
    _order = "seq asc"
    code = fields.Char(string="Code", )
    name = fields.Char(string="Name", )
    seq = fields.Integer(string="Sequence", required=False, )


class StatusOfCommunity(models.Model):
    _name = 'itk_crm.statusofcommunity'
    _description = 'Status of Community'
    _order = "seq asc"
    code = fields.Char(string="Code", )
    name = fields.Char(string="Name", )
    display_name_new = fields.Char(string="Display Name New", )
    display_name = fields.Char(string="Display Name", )
    seq = fields.Integer(string="Sequence", required=False, )


class StatusOfPartner(models.Model):
    _name = 'itk_crm.statusofpartner'
    _description = 'Status of Partner'
    _order = "seq asc"
    code = fields.Char(string="Code", )
    name = fields.Char(string="Name", )
    seq = fields.Integer(string="Sequence", required=False, )
