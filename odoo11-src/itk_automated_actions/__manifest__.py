# -*- coding: utf-8 -*-
{
    'name': "itk_automated_actions",

    'summary': """
     This module imports ITK-specific automated actions.""",

    'description': """This module imports ITK-specific automated actions.""",

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",

    'website': "http://www.alvarium-services.de",

    'category': 'ITK - Specific Industry Applications',

    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'base_automation', 'hr', 'mail', 'contacts',
                ],

    'data': [
        'data/itk_new_application_for_leave.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #   'demo/demo.xml',
    # ],
    'installable': True,
}
