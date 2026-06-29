# -*- coding: utf-8 -*-
from odoo import http

# class ItkSaleManagement(http.Controller):
#     @http.route('/itk_sale_management/itk_sale_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/itk_sale_management/itk_sale_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('itk_sale_management.listing', {
#             'root': '/itk_sale_management/itk_sale_management',
#             'objects': http.request.env['itk_sale_management.itk_sale_management'].search([]),
#         })

#     @http.route('/itk_sale_management/itk_sale_management/objects/<model("itk_sale_management.itk_sale_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('itk_sale_management.object', {
#             'object': obj
#         })