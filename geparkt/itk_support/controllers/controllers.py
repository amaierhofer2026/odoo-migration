# -*- coding: utf-8 -*-
from odoo import http

# class ItkCrm(http.Controller):
#     @http.route('/itk_crm/itk_crm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/itk_crm/itk_crm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('itk_crm.listing', {
#             'root': '/itk_crm/itk_crm',
#             'objects': http.request.env['itk_crm.itk_crm'].search([]),
#         })

#     @http.route('/itk_crm/itk_crm/objects/<model("itk_crm.itk_crm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('itk_crm.object', {
#             'object': obj
#         })
