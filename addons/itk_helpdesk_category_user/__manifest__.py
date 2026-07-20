# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "ITK Helpdesk Category User",
    "summary": "Auto-assign helpdesk tickets based on category user and subscribe them as followers",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "category": "Helpdesk",
    "author": "IT-Kommunal GmbH",
    "website": "https://www.it-kommunal.at",
    "depends": ["helpdesk_mgmt"],
    "data": [
        "views/helpdesk_ticket_category_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
