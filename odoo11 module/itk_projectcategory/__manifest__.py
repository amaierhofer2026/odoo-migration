# -*- coding: utf-8 -*-
{
    'name': "itk_projectcategory",

    'summary': """
        Project Category""",

    'description': """
        ITK Projekt Kategorien
    """,

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "alvarium-services.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'ITK - Specific Industry Applications',
    'version': '0.1',

    # any module necessary for this one to work correctly
    # 'depends': ['base', 'itk_crm', 'itk_data_setup', ],
    'depends': ['base', 'account'],  # 'itk_subscription',


    # always loaded
    'data': [
        # 'views/valorisierung_views.xml',
        'views/account_invoice_views.xml',
        'data/itk_projectcategory.xml',

    ],
    # only loaded in demonstration mode
    # 'demo': [
    #   'demo/demo.xml',
    # ],
}
