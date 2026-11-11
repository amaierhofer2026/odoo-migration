# Copyright 2026 IT-Kommunal
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "ITK Website",
    "summary": "Odoo-18-Anpassungen fuer den ITK-Webauftritt (Wortlaute, Cookie-Hinweis, Fusszeile)",
    "version": "18.0.1.0.0",
    "author": "IT-Kommunal",
    "license": "LGPL-3",
    "category": "Website",
    "depends": ["website", "website_cookie_notice"],
    "data": [
        "views/website_templates.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
