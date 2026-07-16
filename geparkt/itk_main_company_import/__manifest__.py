# -*- coding: utf-8 -*-
{
    'name': "itk_main_company_import",

    'summary': """
        Setting up IT-Kommunal as base.main_company with company informations""",

    'description': """
        Settin up IT-Kommunal as base.main_company with company informations
    """,

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'ITK - Specific Industry Applications',
    'version': '0.1',

    # any module necessary for this one to work correctly

    # 'depends': ['base', 'itk_initial_data_import'],
    'depends': ['base', ],

    # always loaded
    'data': [
        'data/itk_company_base_data.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #   'demo/demo.xml',
    # ],
    'installable': False,
}
