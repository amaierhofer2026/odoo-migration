from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # type = fields.Selection(selection_add=[('license', 'Lizenz')])
    type = fields.Selection(selection=[('consu', 'Verbrauchsgüter'),
                                       ('service', 'Service'),
                                       ('general', 'Allgemein'),
                                       ('onlineservice', 'Onlineservice'),
                                       ('sw', 'Software-Lösung'),
                                       ('consulting', 'Consulting'),
                                       ('platform', 'Plattform'),
                                       ('hw', 'Hardware'),
                                       ('project', 'Förderprojekt'),
                                       ])


    product_type_id = fields.Many2one('itk_product.product_type', string='Produkttyp')
    to_multiply_by_factor = fields.Boolean(string="Mit Faktor multiplizieren (pro 1.000)", default=False)

    # 06.10.2026 (Reiter "Verkauf"): Odoo 11 fuehrte die Preislistenregeln direkt im Produktformular
    # (Feld item_ids, Beschriftung "Preislisten-Positionen", one2many auf product.pricelist.item
    # ueber product_tmpl_id). Odoo 18 hat das Feld aus dem Formular entfernt - Preislistenregeln
    # werden dort ueber den Smart Button "Regeln Preislisten" erreicht. Fuer den Odoo-11-Nachbau
    # und die Migration wird das Feld mit demselben Namen und derselben Relation neu angelegt.
    # Belegung Odoo 11 (read-only gemessen): 321 der 653 Vorlagen tragen Regeln, 1.469 Regeln mit
    # Produktbezug (compute_price formula 1003, fixed 460, percentage 6).
    item_ids = fields.One2many('product.pricelist.item', 'product_tmpl_id',
                               string='Preislisten-Positionen')

    # 24.09.2026 (Session 120, Teil 15): Odoo 11 hatte am Produkt ein Feld "Verantwortlich"
    # (responsible_id -> res.users). Odoo 17/18 hat es ersatzlos entfernt, in Odoo 11 ist es
    # aber auf allen 649 Produkten gepflegt (Administrator 394, Waiss Martina 252,
    # Breiteneder Lorenz 3). Es wird hier mit demselben Feldnamen und derselben Relation
    # neu angelegt, damit der Wert bei der Migration 1:1 uebernommen werden kann.
    # 29.09.2026 (Session 121, Teil 5 Block 2): Das Modul stock (Odoo 18) definiert dasselbe
    # Feld ebenfalls, dort unternehmensabhaengig (company_dependent=True, jsonb-Speicherung).
    # Zwei unterschiedliche Speicherarten fuehrten beim Installieren von sale_stock zu
    # "cannot cast type integer to jsonb". Das Feld wird daher identisch zum Odoo-18-Standard
    # definiert; die Beschriftung "Verantwortlich" bleibt erhalten.
    responsible_id = fields.Many2one('res.users', string='Verantwortlich',
                                     company_dependent=True, check_company=True)


class ProductType(models.Model):
    _name = 'itk_product.product_type'
    _description = 'Product-Type'
    _order = "seq asc"
    code = fields.Char(string="Code", )
    name = fields.Char(string="Name", )
    seq = fields.Integer(string="Sequence", required=False, )