# -*- coding: utf-8 -*-
# Copyright 2015-2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': "Partner Academic Title",
    'summary': """Changed by Alvarium Services for odoo 11 ce. (Version set from 10.0.0.1 to 0.1 and dependency 
    from module 'partner_contact_configuration' removed
    
        Add possibility to define some academic title""",
    'author': 'ACSONE SA/NV,Odoo Community Association (OCA)',
    'website': "http://acsone.eu",
    'category': 'Other',
    'version': '0.01',
    'license': 'AGPL-3',
    'depends': [
        'hr',
        # 'partner_contact_configuration',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/partner_academic_title_data.xml',
        'views/partner_academic_title_view.xml',
        'views/res_partner_view.xml',
    ],
}
