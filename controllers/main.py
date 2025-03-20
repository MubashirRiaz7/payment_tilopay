# -*- coding: utf-8 -*-
#################################################################################
# Author      : ABL Solutions.
# Copyright(c): 2017-Present ABL Solutions.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#################################################################################

import logging
import pprint

from werkzeug import urls
from odoo import _, http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from werkzeug.exceptions import Forbidden
from odoo.http import request

_logger = logging.getLogger(__name__)

class WebsiteSaleInherit(WebsiteSale):

    def _get_mandatory_billing_fields(self, country_id=False):
        """ Override to add custom mandatory fields for billing. """
        res = super(WebsiteSaleInherit, self)._get_mandatory_billing_fields(country_id=country_id)
        # Uncomment if you want to make these fields mandatory
        # res += ["first_name", "last_name", "surname"]
        return res

    def _get_mandatory_shipping_fields(self, country_id=False):
        """ Override to add custom mandatory fields for shipping. """
        res = super(WebsiteSaleInherit, self)._get_mandatory_shipping_fields(country_id=country_id)
        # Uncomment if you want to make these fields mandatory
        # res += ["first_name", "last_name", "surname"]
        return res

    def _checkout_form_save(self, order, mode, values):
        """ Override to save custom fields during checkout. """
        res = super(WebsiteSaleInherit, self)._checkout_form_save(order, mode, values)
        if order.partner_id:
            order.partner_id.sudo().write({
                key: values[key] for key in ['first_name', 'last_name', 'surname'] if key in values
            })
        return res


class TilopayController(http.Controller):

    @http.route('/payment/tilopay', type='http', auth='public', methods=['GET'], csrf=False)
    def tilopay_payment(self, **kwargs):
        """ Handle payment redirection from Tilopay. """
        _logger.info("Handling redirection from Tilopay with data:\n%s", pprint.pformat(kwargs))

        tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data('tilopay', kwargs)
        if not tx_sudo:
            _logger.error("Transaction not found for Tilopay data: %s", pprint.pformat(kwargs))
            return request.redirect('/payment/status')

        try:
            notification_data = self._parse_pdt_validation_response(kwargs, tx_sudo)
            tx_sudo._handle_notification_data('tilopay', notification_data)
        except Forbidden:
            _logger.exception("Could not verify the origin of the PDT; discarding it.")

        return request.redirect('/payment/status')

    @staticmethod
    def _parse_pdt_validation_response(response, tx_sudo):
        """ Parse the PDT validation request response and return the parsed notification data. """
        notification_data = {}
        for key, value in response.items():
            notification_data[key] = urls.url_unquote_plus(value)
        return notification_data
