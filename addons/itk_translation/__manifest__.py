{
    'name': "itk_translation",

    'summary': """
        ITK-spezifische Begriffsuebersetzungen, Menues und Partner-Views.
       """,

    'description': """
       
    """,

    'author': "Alvarium Services, Andreas Vaethroeder, Fabian Vaethroeder",
    'website': "http://www.alvarium-services.de",

    'category': 'ITK - Specific Industry Applications',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',

    'depends': ['base', 'itk_crm'],

    'data': [
        'security/ir.model.access.csv',
        'views/itk_menus.xml',
        'views/res_partner.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
