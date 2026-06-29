# -*- coding: utf-8 -*-
from odoo import http

# class ItkBaseSetup(http.Controller):
#     @http.route('/itk_base_setup/itk_base_setup/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/itk_base_setup/itk_base_setup/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('itk_base_setup.listing', {
#             'root': '/itk_base_setup/itk_base_setup',
#             'objects': http.request.env['itk_base_setup.itk_base_setup'].search([]),
#         })

#     @http.route('/itk_base_setup/itk_base_setup/objects/<model("itk_base_setup.itk_base_setup"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('itk_base_setup.object', {
#             'object': obj
#         })