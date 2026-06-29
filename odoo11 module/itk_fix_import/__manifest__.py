# -*- coding: utf-8 -*-
{
    'name': "!!! DO NOT INSTALL AGAIN !!! itk_fix_goo_ha_prices_import",

    'summary': """
     !!! DO NOT INSTALL AGAIN !!!
       Fix import mistakes""",

    'description': """
Fix import mistakes    """,

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'ITK - Specific Industry Applications',
    'version': '0.3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'itk_initial_data_import',

                ],

    'data': [

        #  importing to trigger setting of community-salutation
        'data/itk_new_application_for_leave.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #   'demo/demo.xml',
    # ],
    'installable': True,
}
