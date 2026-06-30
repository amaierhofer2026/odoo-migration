from odoo import http

# class ItkProduct(http.Controller):
#     @http.route('/itk_product/itk_product/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/itk_product/itk_product/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('itk_product.listing', {
#             'root': '/itk_product/itk_product',
#             'objects': http.request.env['itk_product.itk_product'].search([]),
#         })

#     @http.route('/itk_product/itk_product/objects/<model("itk_product.itk_product"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('itk_product.object', {
#             'object': obj
#         })
