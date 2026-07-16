# -*- coding: utf-8 -*-
{
    'name': "itk_initial_data_ha_basis_verrechnung_import",

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


    # always loaded
    'data': [
        'data/habasis_gkz_strasse.xml',
        'data/habasis_set_invoice_contact_address.xml',
        'data/habasis_set_invoice_contact_email.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #   'demo/demo.xml',
    # ],
    'installable': False,
}
