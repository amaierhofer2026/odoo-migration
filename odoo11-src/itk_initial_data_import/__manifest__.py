# -*- coding: utf-8 -*-
{
    'name': "itk_initial_data_import",

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
    'depends': ['base',
                ],
    # 'depends': ['base',],

    # always loaded
    'data': [
        'data/itk_status_of_community.xml',
        'data/itk_austrian_communities.xml',
        'data/itk_staedtebundmitglieder.xml',
        # 'data/itk_offizielle_email_adressen_ortsnameOLD.xml',
        'data/itk_offizielle_email_adressen_ortsname.xml',
        'data/itk_gkz_plz.xml',
        'data/communities_ewz_2016.xml',
        # 'data/itk_customers_without_gkz.xml',
        # 'data/itk_new_application_for_leave.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #   'demo/demo.xml',
    # ],
    'installable': False,
}
