{
    'name': "itk_saleorder_lines",

    'summary': """
        Adds partner_id and salesperson_id fields to sale.order.line.
        """,

    'description': """
        Extends sale.order.line with:
        - partner_id (res.partner)
        - salesperson_id (res.users)
        
        Adds a menu entry "All Order Lines" under Sales.
    """,

    'author': "Alvarium Services, Andreas Väthröder, Fabian Väthröder",
    'website': "http://www.alvarium-services.de",

    'category': 'ITK - Specific Industry Applications',
    'version': '18.0.1.0.0',

    'license': 'LGPL-3',

    'depends': ['base', 'sale'],

    'data': [
        'views/views.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}