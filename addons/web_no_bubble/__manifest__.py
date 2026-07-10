{
    'name': 'Web No Bubble',
    'version': '18.0.1.0.0',
    'author': 'Savoir-faire Linux, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/web',
    'license': 'AGPL-3',
    'category': 'Web',
    'summary': 'Remove the bubbles from the web interface',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'web_no_bubble/static/src/css/web_no_bubble.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
