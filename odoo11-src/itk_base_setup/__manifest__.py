# -*- coding: utf-8 -*-
{
    'name': "itk_base_setup",

    'summary': """
        ITK base setup. Installs all modules used by ITK and delivered with the odoo 11 system setup.
        """,

    'description': """
         ITK base setup. Installs all modules used by ITK and delivered with the odoo 11 system setup.
         
         Modules ar located in the main-addon-directory

    """,

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'ITK - Specific Industry Applications',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'crm',
        'sale_management',
        'purchase',
        'hr',
        'hr_attendance',
        'hr_timesheet',
        'mass_mailing',
        'survey'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        #    'demo/demo.xml',
    ],
    'installable': False,
}
