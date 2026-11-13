# -*- coding: utf-8 -*-
{
    "name": "ITK Migrationsschluessel",
    "summary": "Technische Odoo-11-IDs fuer idempotente Migrationen (keine Anzeige)",
    "description": """
ITK Migrationsschluessel
========================
Legt auf den Zielmodellen ein technisches Feld ``itk_o11_id`` an. Es haelt die ID des
Datensatzes aus der Odoo-11-Produktivdatenbank (``ITK_V1_a``).

Zweck: Migrationen erkennen bereits uebernommene Datensaetze eindeutig wieder und
erzeugen keine Dubletten. Das Feld ist nicht in Listen, Formularen oder Suchen sichtbar
und enthaelt keine personenbezogenen Daten - nur eine Zahl.

Betroffene Modelle: res.partner, res.partner.category, product.template,
product.product, product.category, product.pricelist, product.pricelist.item,
sale.order, sale.subscription.
""",
    "version": "18.0.1.0.0",
    "category": "ITK - Specific Industry Applications",
    "author": "ITK Migrationsprojekt (Freigabe Anna Maierhofer)",
    "license": "LGPL-3",
    "depends": ["base", "product", "sale", "itk_subscription"],
    "data": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
