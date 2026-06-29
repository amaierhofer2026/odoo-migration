# -*- coding: utf-8 -*-
{
    'name': "itk_multifactor",

    'summary': """
        Dieses Modul enhtält Anpassungen für das ITK-odoo. EWZ je Tsd. Multiplikationsfaktor
       """,

    'description': """
       
    """,

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'ITK - Specific Industry Applications',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'sale', 'itk_saleorder_lines', 'itk_subscription'],

    # always loaded
    'data': [
                'views/res_partner.xml',
                'views/itk_product.xml',
                'views/itk_subscription_line.xml',
                'wizard/itk_contacts_update_multifactor_view.xml',
                'wizard/itk_subscriptionline_update_multifactor_view.xml',
                'wizard/itk_subscription_set_pricelist_view.xml',

    ],
    # only loaded in demonstration mode
    # 'demo': [
    #    'demo/demo.xml',
    # ],
}
