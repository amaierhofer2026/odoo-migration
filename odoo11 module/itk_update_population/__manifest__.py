# -*- coding: utf-8 -*-
{
    'name': "itk_update_population",
    'summary': """Update for Community Population Numbers""",
    'description': """Community Population Numbers are set to actual values. Community Magnitude and the Thsd-Multiplication-Factor are automatically updated.""",
    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",
    'category': 'ITK - Specific Industry Applications',
    'version': '1.0',
    'depends': ['base', 'crm', 'itk_multifactor', 'itk_initial_data_import', ],
    'data': ['data/itk_update_population_multifactor_community_magnitude_31102018.xml',],
    'installable': True,
}
