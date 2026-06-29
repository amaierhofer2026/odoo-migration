# -*- coding: utf-8 -*-
from odoo import http

# class ItkDataSetup(http.Controller):
#     @http.route('/itk_data_setup/itk_data_setup/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/itk_data_setup/itk_data_setup/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('itk_data_setup.listing', {
#             'root': '/itk_data_setup/itk_data_setup',
#             'objects': http.request.env['itk_data_setup.itk_data_setup'].search([]),
#         })

#     @http.route('/itk_data_setup/itk_data_setup/objects/<model("itk_data_setup.itk_data_setup"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('itk_data_setup.object', {
#             'object': obj
#         })