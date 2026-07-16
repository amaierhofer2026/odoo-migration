# -*- coding: utf-8 -*-
{
    'name': "itk_initial_partner_data_import",

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

     # 'itk_data_setup',
                ],
    # 'depends': ['base', ],

    # always loaded
    'data': [
        'data/communities_city_data_niederoesterreich_m_z.xml',
        'data/communities_city_data_burgenland.xml',
        'data/communities_city_data_kaernten.xml',
        'data/communities_city_data_niederoesterreich_a_l.xml',
        'data/communities_city_data_oberoesterreich.xml',
        'data/communities_city_data_salzburg_land.xml',
        'data/communities_city_data_salzburg_stadtregion.xml',
        'data/communities_city_data_steiermark.xml',
        'data/communities_city_data_tirol.xml',
        'data/communities_city_data_wien_neustadt.xml',
        'data/communities_city_data_wien_stadtregion.xml',
        'data/communities_majors_burgenland.xml',
        'data/communities_majors_kaernten.xml',
        'data/communities_majors_niederoesterreich_a_l.xml',
        'data/communities_majors_niederoesterreich_m_z.xml',
        'data/communities_majors_oberoesterreich.xml',
        'data/communities_majors_salzburg_land.xml',
        'data/communities_majors_salzburg_stadtregion.xml',
        'data/communities_majors_steiermark.xml',
        'data/communities_majors_tirol.xml',
        'data/communities_majors_wien_neustadt.xml',
        'data/communities_majors_wien_stadtregion.xml',
        'data/communities_contacts_verrechnungsliste.xml',
        'data/communities_set_to_kk.xml',
        'data/itk_bestandskunden.xml',
        'data/communities_set_to_ek.xml',

    ],
    # only loaded in demonstration mode
    # 'demo': [
    #   'demo/demo.xml',
    # ],
    'installable': False,
}
