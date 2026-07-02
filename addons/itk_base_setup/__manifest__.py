{
    'name': "itk_base_setup",
    'summary': "ITK base setup. Installs all modules used by ITK.",
    'description': "ITK base setup. Installs all modules used by ITK and delivered with the Odoo system setup.",
    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",
    'category': 'ITK - Specific Industry Applications',
    'version': '18.0.1.0.0',
    'depends': [
        'base',
        'crm',
        'sale',
        'purchase',
        'hr',
        'hr_attendance',
        'hr_timesheet',
        'mass_mailing',
        'survey'
    ],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
