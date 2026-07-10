from odoo import http
from odoo.http import request


class WebEnvironmentRibbon(http.Controller):

    @http.route('/web/environment/ribbon', type='json', auth='user')
    def get_environment_ribbon(self):
        return request.env['web.environment.ribbon.backend'].get_environment_ribbon()
