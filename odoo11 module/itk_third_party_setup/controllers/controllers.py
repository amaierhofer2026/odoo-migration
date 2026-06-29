# -*- coding: utf-8 -*-
from odoo import http

# class ItkThirdPartySetup(http.Controller):
#     @http.route('/itk_third_party_setup/itk_third_party_setup/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/itk_third_party_setup/itk_third_party_setup/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('itk_third_party_setup.listing', {
#             'root': '/itk_third_party_setup/itk_third_party_setup',
#             'objects': http.request.env['itk_third_party_setup.itk_third_party_setup'].search([]),
#         })

#     @http.route('/itk_third_party_setup/itk_third_party_setup/objects/<model("itk_third_party_setup.itk_third_party_setup"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('itk_third_party_setup.object', {
#             'object': obj
#         })