# -*- coding: utf-8 -*-
{
    'name': "itk_initial_partner_nogkz_data_import",

    'summary': """
        Partner ohne GKZ""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",
    'category': 'ITK - Specific Industry Applications',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                #'itk_crm',

     # 'itk_data_setup',
                ],
    # always loaded
    'data': [
        'data/itk_customers_without_gkz.xml',
        'data/itk_gemdat_customers.xml',
        'data/communities_contacts_verrechnungsliste_nicht_help_amtsweg.xml',
        'data/itk_automated_actions.xml',
        'data/itk_set_community_display_name.xml',

    ],
    # only loaded in demonstration mode
    # 'demo': [
    #   'demo/demo.xml',
    # ],
    'installable': False,
}
