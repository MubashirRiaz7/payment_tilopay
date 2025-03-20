# -*- coding: utf-8 -*-
#################################################################################
# Author      : ABL Solutions.
# Copyright(c): 2017-Present ABL Solutions.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################

{
    'name': 'Tilopay Payment Gateway',
    'version': '14.0.0.1',  # Adjusted for Odoo 14 compatibility
    'summary': "Integrate Tilopay Payment Gateway with Odoo E-commerce.",
    'description': 'This module integrates the Tilopay SDK with Odoo for handling Credit Card and Debit Card payments.',
    'category': 'Accounting/Payment Acquirers',
    'author': 'ABL Solutions',
    'license': 'OPL-1',  # Using Odoo Proprietary License (change if needed)
    'price': 35.0,
    'currency': 'USD',
    'support': 'infoablsolutions24@gmail.com',
    'depends': ['payment', 'website_sale'],
    'data': [
        'views/payment_provider_views.xml',
        'views/payment_tilopay_templates.xml',
        'views/payment_template.xml',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_tilopay/static/src/js/payment_form.js',
        ],
    },
    'images': ['static/description/Banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
