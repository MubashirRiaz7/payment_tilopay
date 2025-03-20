# -*- coding: utf-8 -*-
#################################################################################
# Author      : ABL Solutions.
# Copyright(c): 2017-Present ABL Solutions.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################

import json
import logging
import requests

from odoo import fields, models, _
from odoo.http import request
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('tilopay', "Tilopay")], ondelete={'tilopay': 'set default'})
    tilopay_api_key = fields.Char("TiloPay API Key", help="The API Key of your Tilopay account", required_if_provider='tilopay')
    tilopay_api_user = fields.Char("Tilopay API User", required_if_provider='tilopay', groups='base.group_system')
    tilopay_api_password = fields.Char("Tilopay API Password", required_if_provider='tilopay', groups='base.group_system')

    def _tilopay_get_inline_form_values(self):
        """ Return a serialized JSON of the required values to render the inline form. """
        self.ensure_one()

        # Get Access Token from TiloPay
        payload = {
            "apiuser": self.tilopay_api_user,
            "password": self.tilopay_api_password,
            "key": self.tilopay_api_key,
        }
        
        headers = {'Content-Type': 'application/json'}
        url = "https://app.tilopay.com/api/v1/loginSdk"

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
            response.raise_for_status()
            response_data = response.json()
        except requests.RequestException as e:
            _logger.error("Tilopay API request failed: %s", e)
            raise UserError(_("Failed to connect to Tilopay API. Please check your credentials and network connection."))

        if 'access_token' not in response_data:
            _logger.error("Tilopay API response did not contain access token: %s", response_data)
            raise UserError(_("Failed to retrieve access token from Tilopay."))

        # Retrieve current sale order
        order = self.env['sale.order'].browse(request.session.get('sale_order_id'))
        if not order:
            raise UserError(_("No active sale order found in the session."))

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        # Prepare inline form values
        inline_form_values = {
            "token": response_data['access_token'],
            "currency": order.currency_id.name,
            "language": "es",
            "amount": order.amount_total,
            "billToFirstName": order.partner_id.first_name or order.partner_id.name,
            "billToLastName": order.partner_id.last_name or '',
            "billToAddress": order.partner_id.street or '',
            "billToCountry": order.partner_id.country_id.code or '',
            "billToEmail": order.partner_id.email,
            "orderNumber": order.name,
            "capture": 1,
            "redirect": f"{base_url}/payment/tilopay",
            "subscription": 0,
            "hashVersion": "V2",
        }

        return json.dumps(inline_form_values)

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes for Tilopay. """
        default_codes = super()._get_default_payment_method_codes()
        if self.provider == 'tilopay':
            return ['tilopay']
        return default_codes
