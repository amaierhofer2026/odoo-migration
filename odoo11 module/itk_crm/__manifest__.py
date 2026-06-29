# -*- coding: utf-8 -*-
{
    'name': "itk_crm",

    'summary': """
        Dieses Modul enhtält Anpassungen für das ITK-odoo.
       """,

    'description': """
       Dieses Modul enhtält Anpassungen für das ITK-odoo:
       Adds ResPartner Attributes:
        - status_of_community
        - population
        - population_update
        - member_of_city_alliance
        - status_of_community
        - population
        - population_updat
        - member_of_city_alliance
        - asset_partner
        - attention_of
        - salutation
        - title_put_in_front
        - title_put_in_back
        - sales_as_final_customer_count
        - community_magnitude_id
        - community_magnitude
        - community_salutation
        - official_email
        - austria_wiki_url
        - latitude
        - longitude
    
    Classes added - LookUps:
        - CommunityMagnitude
        - TitlePutInFront
        - TitlePutInBack
        - CommunityCode
        - StatusOfCommunity
        - StatusOfPartner
    
    """,

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'ITK - Specific Industry Applications',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_management', ],

    # always loaded
    'data': [
        'views/res_partner.xml',
        # 'views/itk_menus.xml',
        'security/itk_crm_security.xml',
        'security/ir.model.access.csv',
        'data/itk_status_of_partner.xml',
        # 'data/itk_status_of_community.xml',
        'data/itk_community_magnitude_classes.xml',

    ],
    # only loaded in demonstration mode
    # 'demo': [
    #    'demo/demo.xml',
    # ],
}
