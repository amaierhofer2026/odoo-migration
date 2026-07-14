# Copyright 2015-2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import http


class CookieNotice(http.Controller):
    @http.route(
        "/website_cookie_notice/ok", auth="public", website=True, type='json',
        methods=['POST'])
    def accept_cookies(self):
        """Stop spamming with cookie banner."""
        http.request.session["accepted_cookies"] = True
        return {'result': 'ok'}
