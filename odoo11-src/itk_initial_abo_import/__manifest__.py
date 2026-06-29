# -*- coding: utf-8 -*-
{
    'name': "itk_initial_abo_import",

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
    'depends': ['base',  'itk_initial_product_import', 'itk_initial_partner_nogkz_data_import',
                #'itk_crm',
                # 'itk_subscription',

     # 'itk_data_setup',
                ],
    # 'depends': ['base', ],

    # always loaded
    'data': [

        #  importing to trigger setting of community-salutation
        # 'data/itk_new_application_for_leave.xml',

        'data/abo_auftrag_ha.xml',
        'data/abo_vertrag_ha.xml',
        'data/connect_contracts_orders_ha.xml',

        'data/abo_auftrag_nha.xml',
        'data/abo_vertrag_nha.xml',
        'data/connect_contracts_orders_nha.xml',


        'data/abo_auftrag_ha_goo.xml',
        'data/abo_vertrag_ha_goo.xml',
        'data/connect_orders_ha_with_goo.xml',  # Zuweisung GOO als Verkäufer zu den Aufträgen
        'data/connect_contracts_orders_ha_goo.xml',

        'data/communities_contacts_dsgvo.xml',
        'data/abo_auftrag_dsgvo.xml',
        'data/habasis_gkz_strasse.xml',
        'data/connect_contracts_orders_dsgvo.xml',

        'data/abo_auftrag_blfs_no.xml',
        'data/abo_vertrag_blfs_no.xml',
        'data/connect_contracts_orders_blfs_no.xml',

        'data/abo_auftrag_heurigen_no.xml',
        'data/abo_vertrag_heurigen_no.xml',
        'data/connect_contracts_orders_heurigen_no.xml',

        'data/set_partner_id_of_subscription_line.xml',

    ],
    # only loaded in demonstration mode
    # 'demo': [
    #   'demo/demo.xml',
    # ],#
    'installable': False,
}
