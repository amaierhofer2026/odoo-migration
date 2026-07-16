# -*- coding: utf-8 -*-
{
    'name': "itk_data_setup",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'ITK - Specific Industry Applications',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale', ],
    # 'depends': ['base', 'account',],

    # always loaded
    'data': [
        # 'data/itk_company_base_data.xml',
        'data/itk_account_payment_terms.xml',
        'data/itk_res_country_states.xml',
        'data/itk_sale_layout_category.xml',

    ],
    # only loaded in demonstration mode
    # 'demo': [
    #   'demo/demo.xml',
    # ],
}
